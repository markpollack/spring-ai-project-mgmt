#!/usr/bin/env python3
"""
Complete PR Review Workflow - Python Implementation

This replaces the problematic shell scripts with a robust Python implementation.
Handles the entire workflow: checkout PR -> compile -> squash -> rebase -> review
"""

import os
import sys
import subprocess
import argparse
import json
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# Import our conflict analyzer and compilation error resolver
from conflict_analyzer import ConflictAnalyzer, ConflictAnalysis
from compilation_error_resolver import CompilationErrorResolver


@dataclass
class WorkflowConfig:
    """Configuration for the PR workflow"""
    script_dir: Path
    spring_ai_repo: str = "spring-projects/spring-ai"
    upstream_remote: str = "upstream"
    main_branch: str = "main"
    
    @property
    def spring_ai_dir(self) -> Path:
        return self.script_dir / "spring-ai"
    
    @property
    def plans_dir(self) -> Path:
        return self.script_dir / "plans"
    
    @property
    def reports_dir(self) -> Path:
        return self.script_dir / "reports"
    
    @property
    def prompt_file(self) -> Path:
        return self.script_dir / "prompt-pr-review.md"


class Colors:
    """ANSI color codes for console output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


class Logger:
    """Logging utilities with color support"""
    
    @staticmethod
    def info(message: str):
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")
    
    @staticmethod
    def warn(message: str):
        print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}")
    
    @staticmethod
    def error(message: str):
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")
    
    @staticmethod
    def success(message: str):
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")


class GitHelper:
    """Git operations helper"""
    
    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir
    
    def run_git(self, args: List[str], check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess:
        """Run git command in the repository directory"""
        cmd = ["git"] + args
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_dir,
                capture_output=capture_output,
                text=True,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            Logger.error(f"Git command failed: {' '.join(cmd)}")
            Logger.error(f"Error: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            raise
    
    def get_conflicted_files(self) -> List[str]:
        """Get list of conflicted files"""
        result = self.run_git(["status", "--porcelain"], capture_output=True)
        conflicted = []
        for line in result.stdout.strip().split('\n'):
            if line and (line.startswith('UU ') or line.startswith('AA ') or line.startswith('DD ')):
                conflicted.append(line[3:].strip())
        return conflicted
    
    def has_conflicts(self) -> bool:
        """Check if repository has conflicts"""
        return len(self.get_conflicted_files()) > 0
    
    def get_current_branch(self) -> str:
        """Get current branch name, handling special git states"""
        try:
            # First try the standard approach
            result = self.run_git(["branch", "--show-current"], capture_output=True)
            branch_name = result.stdout.strip()
            
            if branch_name:
                return branch_name
            
            # If empty, we might be in a detached HEAD state (e.g., during rebase)
            # Try to get the branch name from git status
            status_result = self.run_git(["status", "--porcelain=v1", "-b"], capture_output=True)
            status_lines = status_result.stdout.strip().split('\n')
            
            if status_lines and status_lines[0].startswith('##'):
                # Parse the branch info from status
                branch_info = status_lines[0][3:]  # Remove '## '
                
                if 'HEAD (no branch)' in branch_info:
                    return "detached-HEAD"
                elif 'rebase' in branch_info.lower():
                    # Extract original branch from rebase info
                    if 'rebase ' in branch_info:
                        parts = branch_info.split()
                        for i, part in enumerate(parts):
                            if part == 'rebase' and i + 1 < len(parts):
                                return f"{parts[i+1]}-rebasing"
                    return "rebasing"
                else:
                    # Extract branch name before any tracking info
                    branch_name = branch_info.split('...')[0].split()[0]
                    return branch_name
            
            return "unknown"
            
        except subprocess.CalledProcessError as e:
            # If we can't determine the branch, at least try to give some context
            try:
                # Check if we're even in a git repository
                self.run_git(["rev-parse", "--git-dir"], capture_output=True)
                return "git-error"
            except subprocess.CalledProcessError:
                return "not-git-repo"
    
    def get_commits_ahead(self, base_branch: str) -> int:
        """Get number of commits ahead of base branch"""
        try:
            result = self.run_git(["rev-list", "--count", f"{base_branch}..HEAD"], capture_output=True)
            return int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            return 0


class BuildCache:
    """Build caching system"""
    
    def __init__(self, script_dir: Path, spring_ai_dir: Path):
        self.script_dir = script_dir
        self.spring_ai_dir = spring_ai_dir
    
    def get_cache_file(self, pr_number: str) -> Path:
        return self.script_dir / f".build_cache_pr_{pr_number}"
    
    def is_build_needed(self, pr_number: str) -> bool:
        """Check if build is needed based on code changes"""
        cache_file = self.get_cache_file(pr_number)
        
        if not cache_file.exists():
            Logger.info("📝 No build cache found - build required")
            return True
        
        try:
            # Get current commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.spring_ai_dir,
                capture_output=True,
                text=True,
                check=True
            )
            current_commit = result.stdout.strip()
            
            # Read cached commit
            with open(cache_file, 'r') as f:
                cached_commit = f.readline().strip()
            
            if current_commit == cached_commit:
                Logger.info("✅ Build cache hit - no code changes detected since last successful build")
                return False
            else:
                Logger.info("📝 Code changes detected - build required")
                return True
                
        except Exception as e:
            Logger.warn(f"Error checking build cache: {e}")
            return True
    
    def save_build_success(self, pr_number: str):
        """Save successful build state"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.spring_ai_dir,
                capture_output=True,
                text=True,
                check=True
            )
            current_commit = result.stdout.strip()
            
            cache_file = self.get_cache_file(pr_number)
            with open(cache_file, 'w') as f:
                f.write(f"{current_commit}\n")
                f.write(f"{datetime.now().isoformat()}\n")
            
            Logger.info(f"💾 Build cache updated for PR #{pr_number}")
            
        except Exception as e:
            Logger.warn(f"Error saving build cache: {e}")


class PRAnalyzer:
    """PR analysis and report generation"""
    
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.git = GitHelper(config.spring_ai_dir)
    
    def check_claude_available(self) -> bool:
        """Check if Claude Code CLI is available"""
        return shutil.which("claude") is not None
    
    def check_gh_auth(self) -> bool:
        """Check if GitHub CLI is authenticated"""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def generate_report(self, pr_number: str, dry_run: bool = False) -> Optional[Path]:
        """Generate PR analysis report using Python-based analyzer"""
        
        # Check GitHub CLI authentication
        if not self.check_gh_auth():
            Logger.error("GitHub CLI not authenticated. Please run: gh auth login")
            return None
        
        report_file = self.config.reports_dir / f"review-pr-{pr_number}.md"
        
        if dry_run:
            Logger.info(f"[DRY RUN] Would generate PR analysis report")
            Logger.info(f"[DRY RUN] Report file: {report_file}")
            return report_file
        
        Logger.info(f"🔍 Generating PR analysis report for PR #{pr_number}...")
        Logger.info("Using Python-based analysis...")
        
        try:
            # Use the Python report generator
            python_generator = self.config.script_dir / "python_report_generator.py"
            
            if not python_generator.exists():
                Logger.error(f"Python report generator not found: {python_generator}")
                return None
            
            # Execute Python report generator
            Logger.info("Running Python-based PR analysis...")
            result = subprocess.run(
                ["python3", str(python_generator), pr_number, str(report_file)],
                cwd=self.config.spring_ai_dir,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode == 0:
                Logger.success(f"📋 PR analysis report generated: {report_file}")
                
                # Show report stats
                if report_file.exists():
                    with open(report_file, 'r') as f:
                        line_count = sum(1 for _ in f)
                    Logger.info(f"Report contains {line_count} lines")
                    
                    # Show preview
                    Logger.info("Report preview:")
                    print("=" * 50)
                    with open(report_file, 'r') as f:
                        preview_lines = f.readlines()[10:25]  # Skip header, show next 15 lines
                        for line in preview_lines:
                            print(line.rstrip())
                    print("=" * 50)
                    Logger.info(f"Full report: {report_file}")
                
                return report_file
            else:
                Logger.error("Python PR analysis failed")
                Logger.error(f"Error: {result.stderr}")
                if result.stdout:
                    Logger.error(f"Output: {result.stdout}")
                return None
                
        except subprocess.TimeoutExpired:
            Logger.error("Python PR analysis timed out (2 minutes)")
            return None
        except Exception as e:
            Logger.error(f"Error generating report: {e}")
            return None


class PRWorkflow:
    """Main PR workflow implementation"""
    
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.git = GitHelper(config.spring_ai_dir)
        self.build_cache = BuildCache(config.script_dir, config.spring_ai_dir)
        self.conflict_analyzer = ConflictAnalyzer(str(config.script_dir))
        self.pr_analyzer = PRAnalyzer(config)
        self.compilation_resolver = CompilationErrorResolver(config.spring_ai_dir)
        
        # Ensure directories exist
        config.plans_dir.mkdir(exist_ok=True)
        config.reports_dir.mkdir(exist_ok=True)
    
    def run_command(self, cmd: List[str], description: str, cwd: Optional[Path] = None, dry_run: bool = False) -> bool:
        """Run a command with logging"""
        if dry_run:
            Logger.info(f"[DRY RUN] Would execute: {description}")
            Logger.info(f"[DRY RUN] Command: {' '.join(cmd)}")
            return True
        
        Logger.info(f"Executing: {description}")
        try:
            subprocess.run(cmd, cwd=cwd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Command failed: {' '.join(cmd)}")
            return False
    
    def setup_repository(self, dry_run: bool = False) -> bool:
        """Setup and update the Spring AI repository"""
        Logger.info("Setting up Spring AI repository...")
        
        if not self.config.spring_ai_dir.exists():
            Logger.warn(f"Spring AI repository not found at {self.config.spring_ai_dir}")
            Logger.info("Cloning Spring AI repository...")
            
            clone_cmd = [
                "git", "clone", 
                f"https://github.com/{self.config.spring_ai_repo}.git",
                str(self.config.spring_ai_dir)
            ]
            
            if not self.run_command(clone_cmd, "Clone Spring AI repository", dry_run=dry_run):
                return False
        
        if dry_run:
            Logger.info("[DRY RUN] Would navigate to repository and update")
            return True
        
        # Verify it's a git repository
        if not (self.config.spring_ai_dir / ".git").exists():
            Logger.error(f"Directory {self.config.spring_ai_dir} exists but is not a git repository")
            return False
        
        # Ensure upstream remote exists
        try:
            self.git.run_git(["remote", "get-url", self.config.upstream_remote], capture_output=True)
        except subprocess.CalledProcessError:
            Logger.info("Adding upstream remote...")
            self.git.run_git([
                "remote", "add", self.config.upstream_remote,
                f"https://github.com/{self.config.spring_ai_repo}.git"
            ])
        
        # Fetch latest changes
        Logger.info("Fetching latest changes from upstream...")
        self.git.run_git(["fetch", self.config.upstream_remote])
        
        # Switch to main branch and update
        Logger.info(f"Switching to {self.config.main_branch} branch...")
        self.git.run_git(["checkout", self.config.main_branch])
        self.git.run_git(["pull", self.config.upstream_remote, self.config.main_branch])
        
        return True
    
    def checkout_pr(self, pr_number: str, force: bool = False, dry_run: bool = False) -> bool:
        """Checkout the PR"""
        Logger.info(f"Checking out PR #{pr_number}...")
        
        pr_branch = f"pr-{pr_number}"
        
        if dry_run:
            Logger.info(f"[DRY RUN] Would checkout PR #{pr_number} into branch {pr_branch}")
            return True
        
        # Check if PR branch already exists
        try:
            self.git.run_git(["show-ref", "--verify", "--quiet", f"refs/heads/{pr_branch}"])
            if force:
                Logger.warn(f"Branch {pr_branch} already exists, deleting due to --force flag")
                self.git.run_git(["branch", "-D", pr_branch])
            else:
                Logger.error(f"Branch {pr_branch} already exists. Use --force to overwrite or delete manually.")
                return False
        except subprocess.CalledProcessError:
            # Branch doesn't exist, which is good
            pass
        
        # Checkout the PR using GitHub CLI
        gh_cmd = ["gh", "pr", "checkout", pr_number]
        if not self.run_command(gh_cmd, f"Checkout PR #{pr_number}", cwd=self.config.spring_ai_dir):
            return False
        
        # Rename branch to our convention if gh created a different name
        current_branch = self.git.get_current_branch()
        if current_branch != pr_branch:
            self.git.run_git(["branch", "-m", current_branch, pr_branch])
        
        return True
    def apply_java_formatter(self, dry_run: bool = False) -> bool:
        """Apply Spring Java formatter to fix code formatting violations"""
        Logger.info("🎨 Applying Spring Java formatter...")
        
        if dry_run:
            Logger.info("[DRY RUN] Would apply Spring Java formatter")
            return True
        
        # Try different formatter commands in order of preference
        formatter_commands = [
            (["mvnd", "spring-javaformat:apply"], "Apply formatter with mvnd"),
            (["./mvnw", "spring-javaformat:apply"], "Apply formatter with mvnw"),
            (["mvn", "spring-javaformat:apply"], "Apply formatter with system mvn")
        ]
        
        for cmd, description in formatter_commands:
            if cmd[0] == "./mvnw":
                # Check if mvnw exists
                if not (self.config.spring_ai_dir / "mvnw").exists():
                    continue
            elif cmd[0] in ["mvnd", "mvn"]:
                # Check if command exists
                if not shutil.which(cmd[0]):
                    continue
            
            Logger.info(f"Using {cmd[0]} for formatting...")
            if self.run_command(cmd, description, cwd=self.config.spring_ai_dir):
                Logger.success("✅ Java formatting applied successfully")
                return True
            else:
                Logger.warn(f"Formatting with {cmd[0]} failed, trying next option...")
        
        Logger.error("All formatting options failed")
        return False
    
    def _handle_compilation_errors(self, dry_run: bool = False) -> bool:
        """Detect and automatically resolve compilation errors"""
        if dry_run:
            Logger.info("[DRY RUN] Would detect and resolve compilation errors")
            return True
        
        Logger.info("🔍 Checking for compilation errors...")
        
        # Detect compilation errors
        errors = self.compilation_resolver.detect_compilation_errors()
        
        if not errors:
            Logger.success("✅ No compilation errors detected")
            return True
        
        Logger.warn(f"Found {len(errors)} compilation error(s)")
        
        # Show error details
        auto_fixable = [e for e in errors if e.auto_fixable]
        manual_review = [e for e in errors if not e.auto_fixable]
        
        if auto_fixable:
            Logger.info(f"🔧 {len(auto_fixable)} error(s) can be auto-resolved")
            resolved_count, resolution_log = self.compilation_resolver.auto_resolve_errors(errors)
            
            if resolved_count > 0:
                Logger.success(f"✅ Auto-resolved {resolved_count} compilation error(s)")
                
                # Re-apply formatter after fixes
                if not self.apply_java_formatter():
                    Logger.warn("⚠️  Java formatter failed after compilation fixes")
        
        if manual_review:
            Logger.error(f"❌ {len(manual_review)} error(s) require manual review:")
            for error in manual_review:
                Logger.error(f"  - {error.file_path}:{error.line_number} - {error.message}")
            return False
        
        # Final compilation check
        final_errors = self.compilation_resolver.detect_compilation_errors()
        if final_errors:
            Logger.error(f"❌ {len(final_errors)} compilation error(s) still remain")
            return False
        
        return True
    
    def generate_enhanced_plan(self, pr_number: str, pr_context: Optional[Dict] = None) -> Path:
        """Generate enhanced plan with progress tracking and automation details"""
        plan_file = self.config.plans_dir / f"enhanced-plan-pr-{pr_number}.md"
        
        Logger.info(f"📋 Generating enhanced workflow plan for PR #{pr_number}...")
        
        # Get current status
        current_branch = self._get_current_branch()
        
        # Check for compilation errors
        errors = self.compilation_resolver.detect_compilation_errors()
        compilation_errors_section = self._format_compilation_errors(errors)
        
        # Check for conflicts
        conflicts = self.git.get_conflicted_files()
        conflicts_section = self._format_conflicts(conflicts)
        
        # Prepare template data
        template_data = {
            'pr_number': pr_number,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'repository': 'spring-projects/spring-ai',
            'branch': current_branch,
            'author': pr_context.get('author', 'Unknown') if pr_context else 'Unknown',
            'title': pr_context.get('title', 'Unknown') if pr_context else 'Unknown',
            'compilation_errors_section': compilation_errors_section,
            'conflicts_section': conflicts_section,
            'test_failures_section': '*(Run tests to populate)*',
            'manual_intervention_section': self._get_manual_intervention_section(errors, conflicts),
            'completed_count': 0,  # Will be updated as workflow progresses
            'total_count': 20,     # Total number of workflow steps
            'current_phase': 'Phase 1: Repository Setup',
            'estimated_time': '15-30 minutes',
            'blocker_count': len([e for e in errors if not e.auto_fixable]) + len(conflicts)
        }
        
        # Load and populate template
        template_path = self.config.script_dir / "templates" / "enhanced-plan-template.md"
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Simple template substitution
            plan_content = template_content.format(**template_data)
            
            with open(plan_file, 'w', encoding='utf-8') as f:
                f.write(plan_content)
            
            Logger.success(f"📋 Enhanced plan generated: {plan_file}")
            return plan_file
            
        except Exception as e:
            Logger.error(f"Error generating enhanced plan: {e}")
            return None
    
    def _get_current_branch(self) -> str:
        """Get current git branch name"""
        try:
            result = self.git.run_git(["rev-parse", "--abbrev-ref", "HEAD"], capture_output=True)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def _format_compilation_errors(self, errors) -> str:
        """Format compilation errors for plan display"""
        if not errors:
            return "✅ No compilation errors detected"
        
        auto_fixable = [e for e in errors if e.auto_fixable]
        manual_review = [e for e in errors if not e.auto_fixable]
        
        section = f"Found {len(errors)} compilation error(s):\n"
        
        if auto_fixable:
            section += f"\n**Auto-fixable ({len(auto_fixable)}):**\n"
            for error in auto_fixable[:5]:  # Show first 5
                section += f"- ✅ `{error.file_path}:{error.line_number}` - {error.fix_description}\n"
            if len(auto_fixable) > 5:
                section += f"- ... and {len(auto_fixable) - 5} more\n"
        
        if manual_review:
            section += f"\n**Require Manual Review ({len(manual_review)}):**\n"
            for error in manual_review[:5]:  # Show first 5
                section += f"- ❌ `{error.file_path}:{error.line_number}` - {error.message}\n"
            if len(manual_review) > 5:
                section += f"- ... and {len(manual_review) - 5} more\n"
        
        return section
    
    def _format_conflicts(self, conflicts) -> str:
        """Format merge conflicts for plan display"""
        if not conflicts:
            return "✅ No merge conflicts detected"
        
        section = f"Found {len(conflicts)} conflicted file(s):\n"
        for conflict in conflicts[:10]:  # Show first 10
            section += f"- 🔀 `{conflict}`\n"
        if len(conflicts) > 10:
            section += f"- ... and {len(conflicts) - 10} more\n"
        
        return section
    
    def _get_manual_intervention_section(self, errors, conflicts) -> str:
        """Generate manual intervention section"""
        issues = []
        
        # Add compilation errors that need manual review
        manual_errors = [e for e in errors if not e.auto_fixable]
        if manual_errors:
            issues.append(f"**Compilation Errors**: {len(manual_errors)} error(s) need manual code review")
        
        # Add complex conflicts
        if conflicts:
            issues.append(f"**Merge Conflicts**: {len(conflicts)} file(s) have merge conflicts")
        
        if not issues:
            return "✅ No manual intervention required at this time"
        
        return "\n".join(f"- {issue}" for issue in issues)
    
    def run_build_check(self, pr_number: str, skip_compile: bool = False, dry_run: bool = False) -> bool:
        """Run compilation check with caching"""
        if skip_compile:
            Logger.info("Skipping compilation check as requested")
            return True
        
        # Check if build is needed
        if not self.build_cache.is_build_needed(pr_number):
            Logger.success("⏭️  Skipping build - no changes since last successful build")
            return True
        
        Logger.info("🔨 Running compilation check...")
        
        if dry_run:
            Logger.info("[DRY RUN] Would run compilation check")
            return True
        
        # Apply Java formatter first to fix any formatting violations
        if not self.apply_java_formatter(dry_run):
            Logger.error("❌ Java formatter failed - code will not pass CI tests")
            return False
        
        # Detect and auto-resolve compilation errors
        if not self._handle_compilation_errors(dry_run):
            Logger.error("❌ Compilation errors could not be resolved")
            return False
        
        # Try different build tools in order of preference
        build_commands = [
            (["fb"], "Run compilation check with fb alias"),
            (["mvnd", "clean", "package", "-Dmaven.javadoc.skip=true", "-DskipTests"], "Run Maven build with mvnd"),
            (["./mvnw", "clean", "package", "-Dmaven.javadoc.skip=true", "-DskipTests"], "Run Maven build with mvnw"),
            (["mvn", "clean", "package", "-Dmaven.javadoc.skip=true", "-DskipTests"], "Run Maven build with system mvn")
        ]
        
        for cmd, description in build_commands:
            if cmd[0] == "fb":
                # Check if fb alias exists
                if not shutil.which("fb"):
                    continue
            elif cmd[0] == "./mvnw":
                # Check if mvnw exists
                if not (self.config.spring_ai_dir / "mvnw").exists():
                    continue
            elif cmd[0] in ["mvnd", "mvn"]:
                # Check if command exists
                if not shutil.which(cmd[0]):
                    continue
            
            Logger.info(f"Using {cmd[0]} for build...")
            if self.run_command(cmd, description, cwd=self.config.spring_ai_dir):
                self.build_cache.save_build_success(pr_number)
                return True
            else:
                Logger.warn(f"Build with {cmd[0]} failed, trying next option...")
        
        Logger.error("All build options failed")
        return False
    
    def squash_commits(self, pr_number: str, skip_squash: bool = False, dry_run: bool = False) -> bool:
        """Squash commits in the PR"""
        if skip_squash:
            Logger.info("Skipping commit squashing as requested")
            return True
        
        Logger.info("Squashing commits...")
        
        if dry_run:
            Logger.info("[DRY RUN] Would squash commits if there are multiple commits ahead of main")
            return True
        
        # Count commits ahead of main
        commits_ahead = self.git.get_commits_ahead(f"{self.config.upstream_remote}/{self.config.main_branch}")
        
        if commits_ahead <= 1:
            Logger.info(f"Only {commits_ahead} commit(s) ahead of main, no squashing needed")
            return True
        
        Logger.info(f"Found {commits_ahead} commits ahead of main, squashing automatically...")
        
        # Create automatic squash script
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write('#!/bin/bash\n')
            f.write("# Automatic squash: keep first as pick, change rest to squash\n")
            f.write("sed -i '1!s/^pick/squash/' \"$1\"\n")
            f.flush()
            
            os.chmod(f.name, 0o755)
            
            try:
                # Perform automatic rebase with squashing
                Logger.info("Performing automatic squash rebase...")
                env = os.environ.copy()
                env['GIT_SEQUENCE_EDITOR'] = f.name
                
                subprocess.run([
                    "git", "rebase", "-i", f"HEAD~{commits_ahead}"
                ], cwd=self.config.spring_ai_dir, env=env, check=True)
                
                Logger.success("Commits squashed successfully")
                return True
                
            except subprocess.CalledProcessError:
                Logger.warn("Squash rebase encountered conflicts")
                # For now, we'll return False and let the caller handle conflicts
                return False
            finally:
                os.unlink(f.name)
    
    def rebase_against_upstream(self, pr_number: str, auto_resolve: bool = False, dry_run: bool = False) -> bool:
        """Rebase against upstream main"""
        Logger.info(f"Rebasing against {self.config.upstream_remote}/{self.config.main_branch}...")
        
        if dry_run:
            Logger.info(f"[DRY RUN] Would rebase against {self.config.upstream_remote}/{self.config.main_branch}")
            return True
        
        # Fetch latest upstream changes
        self.git.run_git(["fetch", self.config.upstream_remote])
        
        # Rebase against upstream main
        try:
            self.git.run_git(["rebase", f"{self.config.upstream_remote}/{self.config.main_branch}"])
            Logger.success("Rebase completed successfully with no conflicts")
            return True
        except subprocess.CalledProcessError:
            Logger.warn(f"Rebase conflicts detected for PR #{pr_number}")
            
            # Analyze conflicts using our Python analyzer
            analysis = self.conflict_analyzer.analyze_conflicts(pr_number)
            
            if analysis.total_conflicts == 0:
                Logger.success("Rebase completed successfully with no conflicts")
                return True
            
            Logger.warn(f"Found {analysis.total_conflicts} conflicted files:")
            Logger.warn(f"   🟡 Simple: {analysis.simple_conflicts}")
            Logger.warn(f"   🔴 Complex: {analysis.complex_conflicts}")
            
            plan_file = self.conflict_analyzer.generate_plan(analysis)
            Logger.info(f"📋 Conflict resolution plan generated: {plan_file}")
            
            if auto_resolve:
                Logger.info("Attempting automatic conflict resolution...")
                # Try to auto-resolve conflicts using the legacy shell logic
                if self.attempt_auto_resolution(pr_number):
                    Logger.info("Some conflicts were auto-resolved, attempting to continue rebase...")
                    try:
                        self.git.run_git(["rebase", "--continue"])
                        Logger.success("Rebase completed successfully after auto-resolution")
                        return True
                    except subprocess.CalledProcessError:
                        Logger.warn("Auto-resolution helped but rebase still has issues")
                else:
                    Logger.warn("Automatic conflict resolution was unsuccessful")
            
            # Provide guidance
            Logger.error("Rebase conflicts detected. Resolution options:")
            Logger.info("  1. Resolve conflicts manually and run: git add . && git rebase --continue")
            Logger.info(f"  2. Review plan file: {plan_file}")
            Logger.info("  3. Use Claude Code for AI assistance")
            
            return False
    
    def attempt_auto_resolution(self, pr_number: str) -> bool:
        """Attempt automatic conflict resolution using smart strategies"""
        Logger.info("Analyzing conflicts for auto-resolution...")
        
        # Get conflicted files
        conflicted_files = self.git.get_conflicted_files()
        if not conflicted_files:
            return True  # No conflicts to resolve
        
        resolved_count = 0
        
        for file_path in conflicted_files:
            full_path = self.config.spring_ai_dir / file_path
            if not full_path.exists():
                continue
                
            Logger.info(f"Attempting to resolve conflicts in: {file_path}")
            
            try:
                # Read the conflicted file
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Try different resolution strategies
                resolved_content = None
                
                # Strategy 1: Simple author attribution conflicts
                if self.resolve_author_conflicts(content, file_path):
                    resolved_content = self.resolve_author_conflicts(content, file_path)
                
                # Strategy 2: Version/Docker image conflicts  
                elif self.resolve_version_conflicts(content, file_path):
                    resolved_content = self.resolve_version_conflicts(content, file_path)
                
                # Strategy 3: Simple property/config conflicts
                elif self.resolve_simple_conflicts(content, file_path):
                    resolved_content = self.resolve_simple_conflicts(content, file_path)
                
                if resolved_content:
                    # Write resolved content back
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(resolved_content)
                    
                    # Stage the resolved file
                    self.git.run_git(["add", file_path])
                    resolved_count += 1
                    Logger.success(f"Auto-resolved conflicts in: {file_path}")
                else:
                    Logger.warn(f"Could not auto-resolve conflicts in: {file_path}")
                    
            except Exception as e:
                Logger.warn(f"Error processing {file_path}: {e}")
        
        if resolved_count > 0:
            Logger.success(f"Auto-resolved conflicts in {resolved_count} file(s)")
            
            # Apply Java formatter after resolving conflicts to fix any formatting issues
            Logger.info("🎨 Applying Java formatter after conflict resolution...")
            if not self.apply_java_formatter():
                Logger.error("❌ Java formatter failed after conflict resolution - code will not pass CI")
                return False
            
            return True
        else:
            Logger.warn("No conflicts could be auto-resolved")
            return False
    
    def resolve_author_conflicts(self, content: str, file_path: str) -> str:
        """Resolve simple author attribution conflicts"""
        if not ('<<<<<<< HEAD' in content and '>>>>>>> ' in content):
            return None
        
        # Check if this looks like an author conflict
        if '@author' not in content:
            return None
        
        # Strategy: Keep both authors, merge them
        lines = content.split('\n')
        resolved_lines = []
        in_conflict = False
        conflict_lines = []
        
        for line in lines:
            if line.startswith('<<<<<<< HEAD'):
                in_conflict = True
                conflict_lines = []
            elif line.startswith('>>>>>>> '):
                in_conflict = False
                # Process the collected conflict lines
                authors = []
                other_lines = []
                
                for conflict_line in conflict_lines:
                    if conflict_line.strip().startswith('* @author'):
                        author = conflict_line.strip()
                        if author not in authors:
                            authors.append(author)
                    elif conflict_line.strip() != '=======' and conflict_line.strip():
                        other_lines.append(conflict_line)
                
                # Add all unique authors
                resolved_lines.extend(authors)
                resolved_lines.extend(other_lines)
                
            elif line.startswith('======='):
                continue  # Skip conflict separator
            elif in_conflict:
                conflict_lines.append(line)
            else:
                resolved_lines.append(line)
        
        return '\n'.join(resolved_lines)
    
    def resolve_version_conflicts(self, content: str, file_path: str) -> str:
        """Resolve version number and Docker image conflicts"""
        if not ('<<<<<<< HEAD' in content and '>>>>>>> ' in content):
            return None
        
        # Check if this looks like a version conflict
        if not any(keyword in content for keyword in ['version', 'VERSION', 'parse(', 'docker', 'image']):
            return None
        
        # Strategy: Take the newer/higher version
        lines = content.split('\n')
        resolved_lines = []
        in_conflict = False
        head_lines = []
        branch_lines = []
        
        for line in lines:
            if line.startswith('<<<<<<< HEAD'):
                in_conflict = True
                head_lines = []
                branch_lines = []
                in_head_section = True
            elif line.startswith('======='):
                in_head_section = False
            elif line.startswith('>>>>>>> '):
                in_conflict = False
                
                # Choose the better version (prefer branch changes for newer versions)
                chosen_lines = branch_lines if branch_lines else head_lines
                resolved_lines.extend(chosen_lines)
                
            elif in_conflict:
                if hasattr(locals(), 'in_head_section') and locals().get('in_head_section', True):
                    head_lines.append(line)
                else:
                    branch_lines.append(line)
            else:
                resolved_lines.append(line)
        
        return '\n'.join(resolved_lines)
    
    def resolve_simple_conflicts(self, content: str, file_path: str) -> str:
        """Resolve other simple conflicts by taking branch version"""
        if not ('<<<<<<< HEAD' in content and '>>>>>>> ' in content):
            return None
        
        # For simple conflicts, prefer the branch version (incoming changes)
        lines = content.split('\n')
        resolved_lines = []
        in_conflict = False
        in_head_section = True
        
        for line in lines:
            if line.startswith('<<<<<<< HEAD'):
                in_conflict = True
                in_head_section = True
            elif line.startswith('======='):
                in_head_section = False
            elif line.startswith('>>>>>>> '):
                in_conflict = False
            elif in_conflict and not in_head_section:
                # Take the branch version (after =======)
                resolved_lines.append(line)
            elif not in_conflict:
                resolved_lines.append(line)
        
        return '\n'.join(resolved_lines)
    
    def run_complete_workflow(self, pr_number: str, skip_squash: bool = False, skip_compile: bool = False, 
                            auto_resolve: bool = False, force: bool = False, generate_report: bool = True, dry_run: bool = False) -> bool:
        """Run the complete PR workflow"""
        Logger.info(f"🚀 Starting complete PR review workflow for PR #{pr_number}")
        
        if dry_run:
            Logger.warn("DRY RUN MODE - No actual changes will be made")
        
        # Phase 1: Setup repository
        if not self.setup_repository(dry_run):
            Logger.error("❌ Repository setup failed")
            return False
        
        # Phase 2: Checkout PR
        if not self.checkout_pr(pr_number, force, dry_run):
            Logger.error("❌ PR checkout failed")
            return False
        
        # Phase 3: Build check
        if not self.run_build_check(pr_number, skip_compile, dry_run):
            Logger.error("❌ Build check failed")
            return False
        
        # Phase 4: Squash commits
        if not self.squash_commits(pr_number, skip_squash, dry_run):
            Logger.warn("⚠️  Squash encountered issues, continuing...")
        
        # Phase 5: Rebase against upstream
        if not self.rebase_against_upstream(pr_number, auto_resolve, dry_run):
            Logger.error("❌ Rebase failed with conflicts")
            Logger.info("Resolve conflicts and run the workflow again")
            return False
        
        # Phase 6: Generate PR Analysis Report (if requested)
        report_file = None
        if generate_report:
            Logger.info("📊 Generating PR analysis report...")
            report_file = self.pr_analyzer.generate_report(pr_number, dry_run)
            if report_file is None and not dry_run:
                Logger.warn("⚠️  Report generation failed, but PR preparation was successful")
        
        # Phase 7: Run tests for changed test files
        if not skip_compile and not dry_run:
            self.run_changed_tests(pr_number)
        
        # Success
        Logger.success(f"🎉 Complete PR workflow finished for PR #{pr_number}!")
        
        if not dry_run:
            Logger.info("📁 PR is ready for review")
            Logger.info(f"Repository: {self.config.spring_ai_dir}")
            Logger.info(f"Current branch: {self.git.get_current_branch()}")
            commits_ahead = self.git.get_commits_ahead(f"{self.config.upstream_remote}/{self.config.main_branch}")
            Logger.info(f"Commits ahead of {self.config.upstream_remote}/{self.config.main_branch}: {commits_ahead}")
            
            if report_file:
                Logger.info(f"📋 Review report: {report_file}")
        
        return True
    
    def run_report_only(self, pr_number: str, dry_run: bool = False) -> bool:
        """Generate only the PR analysis report (assumes PR is already prepared)"""
        Logger.info(f"📊 Generating PR analysis report for PR #{pr_number}")
        
        if dry_run:
            Logger.warn("DRY RUN MODE - No actual report will be generated")
        
        # Validate that we're in the right state
        if not self.config.spring_ai_dir.exists():
            Logger.error(f"Spring AI repository not found: {self.config.spring_ai_dir}")
            Logger.error("Please run the full workflow first to prepare the PR")
            return False
        
        # Check if we're on the expected PR branch
        current_branch = self.git.get_current_branch()
        expected_branch = f"pr-{pr_number}"
        
        if current_branch != expected_branch:
            Logger.warn(f"Current branch is '{current_branch}', expected '{expected_branch}'")
            Logger.warn("You may be generating a report for the wrong PR")
        
        # Generate the report
        report_file = self.pr_analyzer.generate_report(pr_number, dry_run)
        
        if report_file:
            Logger.success(f"📋 PR analysis report generated: {report_file}")
            return True
        else:
            Logger.error("❌ Report generation failed")
            return False
    
    def run_test_only(self, pr_number: str, dry_run: bool = False) -> bool:
        """Run only the changed tests (assumes PR is already prepared)"""
        Logger.info(f"🧪 Running tests for changed files in PR #{pr_number}")
        
        if dry_run:
            Logger.info("[DRY RUN] Would run tests for changed test files")
            return True
        
        # Ensure we're in the Spring AI directory
        if not self.config.spring_ai_dir.exists():
            Logger.error(f"Spring AI directory not found: {self.config.spring_ai_dir}")
            return False
        
        # Change to the repository directory
        os.chdir(self.config.spring_ai_dir)
        
        # Run the tests
        success = self.run_changed_tests(pr_number)
        
        if success:
            Logger.success("🎉 All changed tests passed!")
        else:
            Logger.error("💥 Some tests failed")
        
        return success
    
    def get_changed_test_files(self) -> List[str]:
        """Get list of changed test files from the PR"""
        try:
            result = self.git.run_git([
                "diff", "--name-only", f"{self.config.upstream_remote}/{self.config.main_branch}"
            ], capture_output=True)
            
            changed_files = result.stdout.strip().split('\n')
            test_files = []
            
            for file in changed_files:
                if file and self._is_test_file(file):
                    test_files.append(file)
            
            return test_files
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to get changed test files: {e}")
            return []
    
    def _is_test_file(self, filepath: str) -> bool:
        """Check if a file is a test file"""
        if not '/test/' in filepath:
            return False
        
        # Check if it's actually a test class (not just utility classes in test directory)
        return (
            filepath.endswith('Test.java') or 
            filepath.endswith('Tests.java') or
            filepath.endswith('IT.java')
        )
    
    def _get_test_class_name(self, test_file: str) -> Optional[str]:
        """Extract the fully qualified test class name from file path"""
        if not test_file.endswith('.java'):
            return None
        
        # Convert file path to class name
        # e.g., models/spring-ai-ollama/src/test/java/org/springframework/ai/ollama/OllamaApiIT.java
        # -> org.springframework.ai.ollama.OllamaApiIT
        
        # Find the java source path
        java_path_parts = test_file.split('/src/test/java/')
        if len(java_path_parts) != 2:
            return None
        
        class_path = java_path_parts[1]
        class_name = class_path.replace('/', '.').replace('.java', '')
        
        return class_name
    
    def _get_module_path(self, test_file: str) -> Optional[Path]:
        """Get the Maven module path for a test file"""
        # Find the module directory (contains pom.xml)
        file_path = self.config.spring_ai_dir / test_file
        current_dir = file_path.parent
        
        while current_dir != self.config.spring_ai_dir:
            pom_file = current_dir / "pom.xml"
            if pom_file.exists():
                return current_dir
            current_dir = current_dir.parent
        
        return None
    
    def run_changed_tests(self, pr_number: str) -> bool:
        """Run tests for files that changed in the PR"""
        Logger.info("🧪 Running tests for changed test files...")
        
        test_files = self.get_changed_test_files()
        if not test_files:
            Logger.info("✅ No test files changed in this PR")
            return True
        
        Logger.info(f"Found {len(test_files)} changed test files:")
        for test_file in test_files:
            Logger.info(f"  - {test_file}")
        
        # Create test logs directory
        test_logs_dir = self.config.reports_dir / f"test-logs-pr-{pr_number}"
        test_logs_dir.mkdir(exist_ok=True)
        
        # Group test files by module
        modules_to_test = {}
        
        for test_file in test_files:
            module_path = self._get_module_path(test_file)
            class_name = self._get_test_class_name(test_file)
            
            if module_path and class_name:
                if module_path not in modules_to_test:
                    modules_to_test[module_path] = []
                modules_to_test[module_path].append(class_name)
            else:
                Logger.warn(f"Could not determine module/class for: {test_file}")
        
        # Check Docker availability for Testcontainers
        self._check_docker_availability()
        
        # Apply Java formatter before running tests to ensure code compliance
        Logger.info("🎨 Applying Java formatter before running tests...")
        if not self.apply_java_formatter():
            Logger.error("❌ Java formatter failed before tests - code will not pass CI")
            return False
        
        # Run tests by module
        success = True
        test_results = []
        
        for module_path, test_classes in modules_to_test.items():
            Logger.info(f"🔬 Running tests in module: {module_path.name}")
            
            for test_class in test_classes:
                Logger.info(f"  Testing: {test_class}")
                
                # Create log file for this test
                log_file = test_logs_dir / f"{test_class.replace('.', '_')}.log"
                
                # Run single test class using mvnd with full output
                cmd = [
                    "mvnd", "test", 
                    f"-Dtest={test_class}",
                    "-Dmaven.javadoc.skip=true",
                    "-X"  # Debug output for more details
                ]
                
                try:
                    result = subprocess.run(
                        cmd,
                        cwd=module_path,
                        capture_output=True,
                        text=True,
                        timeout=600  # 10 minute timeout for integration tests
                    )
                    
                    # Save full test output to log file
                    with open(log_file, 'w') as f:
                        f.write(f"Test Command: {' '.join(cmd)}\n")
                        f.write(f"Working Directory: {module_path}\n")
                        f.write(f"Return Code: {result.returncode}\n")
                        f.write("=" * 80 + "\n")
                        f.write("STDOUT:\n")
                        f.write(result.stdout)
                        f.write("\n" + "=" * 80 + "\n")
                        f.write("STDERR:\n")
                        f.write(result.stderr)
                    
                    if result.returncode == 0:
                        Logger.success(f"✅ {test_class} - PASSED")
                        test_results.append((test_class, "PASSED", str(log_file)))
                    else:
                        Logger.error(f"❌ {test_class} - FAILED")
                        Logger.error(f"Full test log saved to: {log_file}")
                        # Show last few lines of error for immediate feedback
                        error_lines = result.stderr.split('\n')[-10:]
                        Logger.error("Last few error lines:")
                        for line in error_lines:
                            if line.strip():
                                Logger.error(f"  {line}")
                        test_results.append((test_class, "FAILED", str(log_file)))
                        success = False
                        
                except subprocess.TimeoutExpired:
                    Logger.error(f"❌ {test_class} - TIMEOUT (10 minutes)")
                    with open(log_file, 'w') as f:
                        f.write(f"Test Command: {' '.join(cmd)}\n")
                        f.write(f"Working Directory: {module_path}\n")
                        f.write("STATUS: TIMEOUT after 10 minutes\n")
                    test_results.append((test_class, "TIMEOUT", str(log_file)))
                    success = False
                except Exception as e:
                    Logger.error(f"❌ {test_class} - ERROR: {e}")
                    with open(log_file, 'w') as f:
                        f.write(f"Test Command: {' '.join(cmd)}\n")
                        f.write(f"Working Directory: {module_path}\n")
                        f.write(f"ERROR: {e}\n")
                    test_results.append((test_class, "ERROR", str(log_file)))
                    success = False
        
        # Create test summary report
        self._create_test_summary_report(pr_number, test_results, test_logs_dir)
        
        if success:
            Logger.success("🎉 All changed tests passed!")
        else:
            Logger.error("💥 Some tests failed - review needed")
            Logger.info(f"📋 Test logs available in: {test_logs_dir}")
        
        return success
    
    def _check_docker_availability(self):
        """Check if Docker is available for Testcontainers"""
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                Logger.info("✅ Docker is available for Testcontainers")
            else:
                Logger.warn("⚠️  Docker may not be properly configured")
                Logger.warn("Integration tests might fail without Docker")
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            Logger.warn("⚠️  Docker not found - integration tests will likely fail")
            Logger.warn("Install Docker to run Testcontainers-based tests")
    
    def _create_test_summary_report(self, pr_number: str, test_results: List[Tuple[str, str, str]], logs_dir: Path):
        """Create a summary report of test execution"""
        summary_file = logs_dir / "test-summary.md"
        
        with open(summary_file, 'w') as f:
            f.write(f"# Test Execution Summary - PR #{pr_number}\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            passed = [r for r in test_results if r[1] == "PASSED"]
            failed = [r for r in test_results if r[1] in ["FAILED", "TIMEOUT", "ERROR"]]
            
            f.write(f"## Summary\n\n")
            f.write(f"- **Total Tests**: {len(test_results)}\n")
            f.write(f"- **Passed**: {len(passed)}\n")
            f.write(f"- **Failed**: {len(failed)}\n")
            f.write(f"- **Success Rate**: {len(passed)/len(test_results)*100:.1f}%\n\n")
            
            if passed:
                f.write("## ✅ Passed Tests\n\n")
                for test_class, status, log_file in passed:
                    f.write(f"- `{test_class}` - [Log]({Path(log_file).name})\n")
                f.write("\n")
            
            if failed:
                f.write("## ❌ Failed Tests\n\n")
                for test_class, status, log_file in failed:
                    f.write(f"- `{test_class}` - **{status}** - [Log]({Path(log_file).name})\n")
                f.write("\n")
        
        Logger.info(f"📋 Test summary report: {summary_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Complete PR Review Workflow for Spring AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 pr_workflow.py 3386                      # Full workflow for PR #3386
  python3 pr_workflow.py --auto-resolve 3386       # Include automatic conflict resolution
  python3 pr_workflow.py --skip-squash 3386        # Skip commit squashing
  python3 pr_workflow.py --skip-report 3386        # Skip report generation (prep only)
  python3 pr_workflow.py --report-only 3386        # Generate only the analysis report
  python3 pr_workflow.py --test-only 3386          # Run only the changed tests
  python3 pr_workflow.py --plan-only 3386          # Generate enhanced workflow plan
  python3 pr_workflow.py --dry-run 3386            # Preview the workflow
        """
    )
    
    parser.add_argument('pr_number', help='GitHub PR number to process')
    parser.add_argument('--skip-squash', action='store_true', help='Skip commit squashing')
    parser.add_argument('--skip-compile', action='store_true', help='Skip compilation check')
    parser.add_argument('--auto-resolve', action='store_true', help='Attempt automatic conflict resolution')
    parser.add_argument('--force', action='store_true', help='Force operations (overwrite existing branches)')
    parser.add_argument('--skip-report', action='store_true', help='Skip PR analysis report generation')
    parser.add_argument('--report-only', action='store_true', help='Generate only the analysis report (assumes PR already prepared)')
    parser.add_argument('--test-only', action='store_true', help='Run only the changed tests (assumes PR already prepared)')
    parser.add_argument('--plan-only', action='store_true', help='Generate enhanced workflow plan with progress tracking')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    # Validate PR number
    if not args.pr_number.isdigit():
        Logger.error(f"PR number must be a positive integer: {args.pr_number}")
        sys.exit(1)
    
    # Setup configuration
    script_dir = Path(__file__).parent.absolute()
    config = WorkflowConfig(script_dir)
    
    # Create workflow instance
    workflow = PRWorkflow(config)
    
    # Check for mutually exclusive options
    exclusive_options = [args.skip_report, args.report_only, args.test_only, args.plan_only]
    if sum(exclusive_options) > 1:
        Logger.error("Cannot use multiple exclusive options: --skip-report, --report-only, --test-only, --plan-only")
        sys.exit(1)
    
    # Run the appropriate workflow
    if args.report_only:
        success = workflow.run_report_only(
            pr_number=args.pr_number,
            dry_run=args.dry_run
        )
    elif args.test_only:
        success = workflow.run_test_only(
            pr_number=args.pr_number,
            dry_run=args.dry_run
        )
    elif args.plan_only:
        plan_file = workflow.generate_enhanced_plan(args.pr_number)
        success = plan_file is not None
        if success:
            Logger.success(f"📋 Enhanced plan generated successfully: {plan_file}")
        else:
            Logger.error("❌ Failed to generate enhanced plan")
    else:
        success = workflow.run_complete_workflow(
            pr_number=args.pr_number,
            skip_squash=args.skip_squash,
            skip_compile=args.skip_compile,
            auto_resolve=args.auto_resolve,
            force=args.force,
            generate_report=not args.skip_report,
            dry_run=args.dry_run
        )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
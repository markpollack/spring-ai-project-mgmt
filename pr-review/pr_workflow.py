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
# Import GitHub utilities for branch management
from github_utils import GitHubUtils
from claude_code_wrapper import ClaudeCodeWrapper
from commit_message_generator import CommitMessageGenerator


@dataclass
class WorkflowConfig:
    """Configuration for the PR workflow"""
    script_dir: Path
    spring_ai_repo: str = "spring-projects/spring-ai"
    mcp_sdk_repo: str = "modelcontextprotocol/java-sdk"
    upstream_remote: str = "origin"
    main_branch: str = "main"
    
    @property
    def spring_ai_dir(self) -> Path:
        return self.script_dir / "spring-ai"
    
    @property
    def mcp_sdk_dir(self) -> Path:
        return self.script_dir / "mcp-java-sdk"
    
    @property
    def plans_dir(self) -> Path:
        return self.script_dir / "plans"
    
    @property
    def reports_dir(self) -> Path:
        return self.script_dir / "reports"
    
    @property
    def prompt_file(self) -> Path:
        return self.script_dir / "prompt-pr-review.md"
    
    @property
    def context_dir(self) -> Path:
        return self.script_dir / "context"
    
    @property
    def logs_dir(self) -> Path:
        return self.script_dir / "logs"


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
        """Run git command in the repository directory with non-interactive environment"""
        cmd = ["git"] + args
        try:
            # Global environment to prevent any git editor popups
            env = os.environ.copy()
            env['GIT_EDITOR'] = 'true'  # Use 'true' command that always succeeds
            env['EDITOR'] = 'true'
            env['VISUAL'] = 'true'
            env['GIT_SEQUENCE_EDITOR'] = 'true'
            env['GIT_MERGE_AUTOEDIT'] = 'no'
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_dir,
                capture_output=capture_output,
                text=True,
                check=check,
                env=env
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
    
    def generate_report(self, pr_number: str, dry_run: bool = False, force_fresh: bool = False, skip_backport: bool = False) -> Optional[Path]:
        """Generate enhanced PR analysis report using context collection and AI-powered analysis"""
        
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
        Logger.info("Using enhanced analysis with context collection...")
        
        try:
            # Verify context data exists (should have been collected in earlier phase)
            context_dir = self.config.context_dir / f"pr-{pr_number}"
            if not context_dir.exists():
                Logger.warn("⚠️  Context data not found, collecting now...")
                if not self.collect_pr_context(pr_number):
                    raise RuntimeError(f"Context collection failed for PR #{pr_number}")
            else:
                context_files = list(context_dir.glob("*.json"))
                Logger.info(f"✅ Using existing context data: {len(context_files)} files")
            
            # Then generate enhanced report
            enhanced_generator = self.config.script_dir / "enhanced_report_generator.py"
            
            if not enhanced_generator.exists():
                Logger.error(f"Enhanced report generator not found: {enhanced_generator}")
                return None
            
            # Execute enhanced report generator
            Logger.info("Generating enhanced PR analysis report...")
            # Run without capturing output so we can see real-time progress
            
            # Add --force-fresh flag for report-only mode to regenerate AI assessments
            cmd = ["python3", str(enhanced_generator), pr_number]
            
            Logger.info(f"🔍 DEBUG: force_fresh parameter: {force_fresh}")
            
            if force_fresh:
                cmd.append("--force-fresh")
                Logger.info("🔄 Forcing fresh AI analysis (report-only mode)")
            
            if skip_backport:
                cmd.append("--skip-backport")
                Logger.info("⏭️  Skipping backport assessment")
            
            # Pass the context directory to the enhanced report generator
            cmd.extend(["--context-dir", str(self.config.context_dir)])
            
            # Pass reports and logs directories for batch processing
            cmd.extend(["--reports-dir", str(self.config.reports_dir)])
            cmd.extend(["--logs-dir", str(self.config.logs_dir)])
            Logger.info(f"🔍 Using context directory: {self.config.context_dir}")
            
            Logger.info(f"🔍 DEBUG: Command being executed: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, 
                cwd=self.config.script_dir, 
                timeout=600  # Increase to 10 minutes for debugging
            )
            
            if result.returncode == 0:
                # Check if report was actually created with real content
                if not report_file.exists():
                    Logger.error(f"❌ Enhanced report file was not created: {report_file}")
                    return None
                
                # Verify report has real data (not just placeholder content)
                with open(report_file, 'r') as f:
                    content = f.read()
                    
                # Check for placeholder/empty data indicators
                placeholder_indicators = [
                    "Analysis not available",
                    "Assessment not available", 
                    "N/A/10 ⭐",
                    "Problem Being Solved**: Analysis not available"
                ]
                
                has_placeholder_data = any(indicator in content for indicator in placeholder_indicators)
                
                if has_placeholder_data:
                    Logger.error("❌ Enhanced report contains placeholder data - AI analysis failed")
                    Logger.error("❌ Context data was not properly processed by the enhanced report generator")
                    Logger.error("❌ Cannot continue with incomplete AI analysis")
                    return None
                
                Logger.success(f"📋 Enhanced PR analysis report generated: {report_file}")
                
                # Show report stats
                line_count = len(content.splitlines())
                Logger.info(f"Enhanced report contains {line_count} lines")
                
                # Show preview
                Logger.info("Enhanced report preview:")
                print("=" * 50)
                preview_lines = content.splitlines()[10:25]  # Skip header, show next 15 lines
                for line in preview_lines:
                    print(line)
                print("=" * 50)
                Logger.info(f"Full enhanced report: {report_file}")
                
                return report_file
            else:
                Logger.error("Enhanced PR analysis failed")
                Logger.error(f"Enhanced report generation return code: {result.returncode}")
                return None
                
        except subprocess.TimeoutExpired:
            Logger.error("Enhanced PR analysis timed out (10 minutes)")
            return None
        except Exception as e:
            Logger.error(f"Error generating report: {e}")
            return None


class PRWorkflow:
    """Main PR workflow implementation"""
    
    def __init__(self, config: WorkflowConfig):
        # Log startup timestamp for debugging correlation
        startup_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        Logger.info(f"🚀 PRWorkflow starting at {startup_time}")
        
        self.config = config
        self.git = GitHelper(config.spring_ai_dir)
        self.build_cache = BuildCache(config.script_dir, config.spring_ai_dir)
        self.conflict_analyzer = ConflictAnalyzer(str(config.script_dir))
        self.pr_analyzer = PRAnalyzer(config)
        self.compilation_resolver = CompilationErrorResolver(config.spring_ai_dir, config.mcp_sdk_dir)
        self.github_utils = GitHubUtils(config.script_dir, config.spring_ai_repo)
        
        # Ensure directories exist
        config.plans_dir.mkdir(exist_ok=True)
        config.reports_dir.mkdir(exist_ok=True)
    
    def run_command(self, cmd: List[str], description: str, cwd: Optional[Path] = None, dry_run: bool = False, 
                   suppress_output: bool = False, log_file: Optional[Path] = None) -> bool:
        """Run a command with logging
        
        Args:
            cmd: Command to run
            description: Description for logging
            cwd: Working directory
            dry_run: Whether to actually run the command
            suppress_output: Whether to suppress stdout/stderr from terminal
            log_file: Optional file to write output to
        """
        if dry_run:
            Logger.info(f"[DRY RUN] Would execute: {description}")
            Logger.info(f"[DRY RUN] Command: {' '.join(cmd)}")
            return True
        
        Logger.info(f"Executing: {description}")
        try:
            if suppress_output:
                # Enhanced mvnd output suppression using your colleague's solution
                if cmd[0] == 'mvnd':
                    # Add mvnd-specific suppression flags
                    enhanced_cmd = cmd + [
                        '-q',                        # Quiet mode  
                        '-Dmvnd.rollingWindowSize=0' # Disable rolling window display
                    ]
                    
                    # Set environment variables for complete suppression
                    env = os.environ.copy()
                    env.update({
                        'TERM': 'dumb',
                        'NO_COLOR': '1',
                        'CI': 'true',                           # Many tools detect CI and disable fancy output
                        'MAVEN_OPTS': '-Djansi.force=false',
                        'MVND_TERMINAL': 'false'                # Disable mvnd terminal features
                    })
                else:
                    enhanced_cmd = cmd
                    env = None
                
                # Create logs directory if it doesn't exist
                if log_file:
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(log_file, 'w') as f:
                        f.write(f"Command: {' '.join(enhanced_cmd)}\n")
                        f.write(f"Working directory: {cwd or 'current'}\n")
                        f.write(f"Description: {description}\n")
                        f.write("-" * 50 + "\n")
                        f.flush()
                        
                        result = subprocess.run(
                            enhanced_cmd, 
                            cwd=cwd, 
                            check=True, 
                            stdout=f, 
                            stderr=f,
                            stdin=subprocess.DEVNULL,
                            start_new_session=True,
                            env=env,
                            text=True
                        )
                else:
                    # Suppress output completely
                    result = subprocess.run(
                        enhanced_cmd, 
                        cwd=cwd, 
                        check=True, 
                        capture_output=True, 
                        stdin=subprocess.DEVNULL,
                        start_new_session=True,
                        env=env,
                        text=True
                    )
                return True
            else:
                # Standard behavior - output goes to terminal
                subprocess.run(cmd, cwd=cwd, check=True)
                return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Command failed: {' '.join(cmd)}")
            if suppress_output and log_file and log_file.exists():
                Logger.error(f"Check log file for details: {log_file}")
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
        
        # Fetch latest changes from origin
        Logger.info("Fetching latest changes from origin...")
        self.git.run_git(["fetch", self.config.upstream_remote])
        
        # Switch to main branch and update
        Logger.info(f"Switching to {self.config.main_branch} branch...")
        self.git.run_git(["checkout", self.config.main_branch])
        self.git.run_git(["pull", self.config.upstream_remote, self.config.main_branch])
        
        return True
    
    def setup_mcp_sdk_repository(self, dry_run: bool = False) -> bool:
        """Setup and update the MCP Java SDK repository"""
        Logger.info("Setting up MCP Java SDK repository...")
        
        if not self.config.mcp_sdk_dir.exists():
            Logger.warn(f"MCP SDK repository not found at {self.config.mcp_sdk_dir}")
            Logger.info("Cloning MCP Java SDK repository...")
            
            clone_cmd = [
                "git", "clone", 
                f"https://github.com/{self.config.mcp_sdk_repo}.git",
                str(self.config.mcp_sdk_dir)
            ]
            
            if not self.run_command(clone_cmd, "Clone MCP Java SDK repository", dry_run=dry_run):
                return False
        
        if dry_run:
            Logger.info("[DRY RUN] Would navigate to MCP SDK repository and update")
            return True
        
        # Verify it's a git repository
        if not (self.config.mcp_sdk_dir / ".git").exists():
            Logger.error(f"Directory {self.config.mcp_sdk_dir} exists but is not a git repository")
            return False
        
        # Create a temporary GitHelper for the MCP SDK repository
        mcp_git = GitHelper(self.config.mcp_sdk_dir)
        
        # Fetch latest changes from origin
        Logger.info("Fetching latest changes from MCP SDK origin...")
        mcp_git.run_git(["fetch", self.config.upstream_remote])
        
        # Switch to main branch and update
        Logger.info(f"Switching to {self.config.main_branch} branch...")
        mcp_git.run_git(["checkout", self.config.main_branch])
        mcp_git.run_git(["pull", self.config.upstream_remote, self.config.main_branch])
        
        return True
    
    def checkout_pr(self, pr_number: str, force: bool = False, dry_run: bool = False) -> bool:
        """Checkout the PR using smart branch switching"""
        Logger.info(f"Checking out PR #{pr_number}...")
        
        if dry_run:
            Logger.info(f"[DRY RUN] Would checkout PR #{pr_number}")
            return True
        
        # Get the expected branch name for this PR
        expected_branch = self.github_utils.get_pr_branch_name(pr_number)
        if not expected_branch:
            Logger.error(f"Could not determine branch name for PR #{pr_number}")
            return False
        
        # Check if we already have this branch locally
        try:
            result = self.git.run_git(["show-ref", "--verify", "--quiet", f"refs/heads/{expected_branch}"], 
                                    check=False, capture_output=True)
            branch_exists_locally = (result.returncode == 0)
        except:
            branch_exists_locally = False
        
        if branch_exists_locally and not force:
            # Branch exists locally - just switch to it (preserves local changes/squashes)
            Logger.info(f"🔄 Branch {expected_branch} exists locally, switching to it")
            if not self.github_utils.switch_to_branch(self.config.spring_ai_dir, expected_branch):
                return False
        else:
            # Branch doesn't exist locally or force requested - use gh pr checkout
            if force and branch_exists_locally:
                Logger.info(f"🔄 Force checkout requested - will overwrite local branch {expected_branch}")
            
            Logger.info(f"📥 Checking out PR #{pr_number} from GitHub")
            gh_cmd = ["gh", "pr", "checkout", pr_number]
            if not self.run_command(gh_cmd, f"Checkout PR #{pr_number}", cwd=self.config.spring_ai_dir):
                return False
            
            # Store the branch mapping for future use
            actual_branch = self.git.run_git(["rev-parse", "--abbrev-ref", "HEAD"], capture_output=True).stdout.strip()
            self.github_utils.store_pr_branch_mapping(pr_number, actual_branch)
        
        # Verify we're on the correct branch
        current_branch = self.git.run_git(["rev-parse", "--abbrev-ref", "HEAD"], capture_output=True).stdout.strip()
        Logger.success(f"✅ Now on branch: {current_branch}")
        
        # Store the actual branch name for cleanup purposes
        self.current_pr_branch = current_branch
        
        return True
    def apply_java_formatter(self, dry_run: bool = False) -> bool:
        """Apply Spring Java formatter to fix code formatting violations"""
        Logger.info("🎨 Applying Spring Java formatter...")
        
        if dry_run:
            Logger.info("[DRY RUN] Would apply Spring Java formatter")
            return True
        
        # Create log file for formatter output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.config.logs_dir / f"java-formatter-{timestamp}.log"
        
        # Use mvnd for fastest formatting
        formatter_commands = [
            (["mvnd", "spring-javaformat:apply"], "Apply formatter with mvnd")
        ]
        
        for cmd, description in formatter_commands:
            if cmd[0] == "mvnd":
                # Check if mvnd exists
                if not shutil.which("mvnd"):
                    Logger.error("mvnd not found - please install Maven Daemon for fastest formatting")
                    return False
            
            Logger.info(f"Using {cmd[0]} for formatting (output logged to {log_file.name})...")
            if self.run_command(cmd, description, cwd=self.config.spring_ai_dir, 
                              suppress_output=True, log_file=log_file):
                Logger.success("✅ Java formatting applied successfully")
                return True
            else:
                Logger.warn(f"Formatting with {cmd[0]} failed, trying next option...")
        
        Logger.error("All formatting options failed")
        return False
    
    def _handle_compilation_errors(self, pr_number: str = None, dry_run: bool = False) -> bool:
        """Detect and automatically resolve compilation errors"""
        if dry_run:
            Logger.info("[DRY RUN] Would detect and resolve compilation errors")
            return True
        
        Logger.info("🔍 Checking for compilation errors...")
        
        # Detect compilation errors (first and only initial check)
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
            
            # Single-shot fixing with human intervention fallback
            max_attempts = 1
            total_resolved = 0
            
            for attempt in range(1, max_attempts + 1):
                Logger.info(f"🔄 Compilation fix attempt {attempt}/{max_attempts}")
                
                # Use existing errors list instead of re-detecting
                if attempt == 1:
                    current_errors = errors
                else:
                    # Only re-detect on subsequent attempts
                    current_errors = self.compilation_resolver.detect_compilation_errors()
                
                if not current_errors:
                    Logger.success("✅ All compilation errors resolved!")
                    break
                    
                auto_fixable_current = [e for e in current_errors if e.auto_fixable]
                if not auto_fixable_current:
                    Logger.info("No more auto-fixable errors remaining")
                    break
                
                # Attempt to resolve current batch of errors
                attempted_count, resolution_log = self.compilation_resolver.auto_resolve_errors(auto_fixable_current)
                
                if attempted_count > 0:
                    Logger.info(f"🔧 Applied fixes to {attempted_count} error(s) in attempt {attempt} - validating...")
                    
                    # Re-apply formatter after fixes
                    if not self.apply_java_formatter():
                        Logger.warn("⚠️  Java formatter failed after compilation fixes")
                    
                    # Critical: Check if all errors are actually resolved after this attempt
                    verification_errors = self.compilation_resolver.detect_compilation_errors()
                    if not verification_errors:
                        Logger.success("✅ Validation successful: All compilation errors resolved!")
                        # Count actually resolved errors = initial errors - remaining errors
                        errors_resolved_this_attempt = len(current_errors) - len(verification_errors)
                        total_resolved += errors_resolved_this_attempt
                        break
                    else:
                        Logger.info(f"📋 After attempt {attempt}: {len(verification_errors)} error(s) still remain")
                        # Count partially resolved errors = reduction in error count
                        errors_resolved_this_attempt = len(current_errors) - len(verification_errors)
                        if errors_resolved_this_attempt > 0:
                            total_resolved += errors_resolved_this_attempt
                            Logger.info(f"🎯 Actually resolved {errors_resolved_this_attempt} error(s) in this attempt")
                        if attempt < max_attempts:
                            Logger.info("Continuing to next attempt...")
                else:
                    Logger.warn(f"⚠️  No fix attempts made in attempt {attempt}")
                    break
            
            Logger.info(f"🎯 Total compilation errors resolved: {total_resolved}")
            
            # Commit compilation fixes immediately to prevent losing them
            if total_resolved > 0:
                try:
                    status_result = self.git.run_git(["status", "--porcelain"], capture_output=True)
                    if status_result.stdout.strip():
                        Logger.info("💾 Committing compilation fixes...")
                        self.git.run_git(["add", "."])
                        self.git.run_git(["commit", "-m", f"Auto-fix compilation errors\n\n🤖 Automatically resolved {total_resolved} compilation errors using Claude Code"])
                        Logger.success("✅ Compilation fixes committed")
                    else:
                        Logger.debug("No uncommitted changes to commit")
                except Exception as e:
                    Logger.warn(f"Error committing compilation fixes: {e}")
        
        if manual_review:
            Logger.error(f"❌ {len(manual_review)} error(s) require manual review:")
            for error in manual_review:
                Logger.error(f"  - {error.file_path}:{error.line_number} - {error.message}")
            return False
        
        # Final verification step - ensure all errors are actually resolved
        Logger.info("🔍 Final verification: checking if all compilation errors are resolved...")
        final_errors = self.compilation_resolver.detect_compilation_errors()
        
        if final_errors:
            Logger.error(f"❌ {len(final_errors)} compilation error(s) still remain after resolution attempts:")
            for error in final_errors:
                Logger.error(f"  - {error.file_path}:{error.line_number} - {error.message}")
            Logger.error("")
            Logger.error("🔧 HUMAN INTERVENTION NEEDED")
            Logger.error("Please manually fix the compilation errors above, then resume with:")
            Logger.error(f"   python3 pr_workflow.py --resume-after-compile {pr_number or '<PR_NUMBER>'}")
            Logger.error("")
            Logger.error("💡 The compilation errors are in the working directory:")
            Logger.error(f"   {self.config.spring_ai_dir}")
            return False
        
        Logger.success("✅ All compilation errors successfully resolved and verified!")
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
    
    def _delete_pr_branch(self, branch_name: str, pr_number: str = None) -> bool:
        """Delete a PR branch for cleaner workspace state"""
        if not branch_name or branch_name == self.config.main_branch:
            return False
            
        try:
            # Check if branch exists
            branches_result = self.git.run_git(["branch", "--list", branch_name], capture_output=True)
            if not branches_result.stdout.strip():
                Logger.debug(f"Branch {branch_name} doesn't exist, nothing to delete")
                return True
            
            Logger.info(f"🗑️  Deleting PR branch: {branch_name}")
            self.git.run_git(["branch", "-D", branch_name])
            Logger.info(f"✅ Deleted PR branch: {branch_name}")
            
            # Also try to get and delete the PR branch from GitHub mapping as fallback
            if pr_number:
                expected_branch = self.github_utils.get_pr_branch_name(pr_number)
                if expected_branch and expected_branch != branch_name and expected_branch != self.config.main_branch:
                    try:
                        branches_result = self.git.run_git(["branch", "--list", expected_branch], capture_output=True)
                        if branches_result.stdout.strip():
                            Logger.info(f"🗑️  Also deleting expected PR branch: {expected_branch}")
                            self.git.run_git(["branch", "-D", expected_branch])
                            Logger.info(f"✅ Deleted expected PR branch: {expected_branch}")
                    except Exception as e:
                        Logger.debug(f"Could not delete expected branch {expected_branch}: {e}")
            
            return True
            
        except Exception as e:
            Logger.warn(f"Failed to delete PR branch {branch_name}: {e}")
            return False
    
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
    
    def cleanup_pr_workspace(self, pr_number: str, cleanup_mode: str = 'light', dry_run: bool = False, preserve_context: bool = False, force_ai_refresh: bool = False) -> bool:
        """Clean up PR workspace and generated files
        
        Args:
            pr_number: PR number to clean up
            cleanup_mode: 'full' (remove everything), 'light' (keep spring-ai repo), 'reports' (reports only), 'ai-cache' (AI cache only)
            dry_run: Show what would be done without executing
            preserve_context: Skip cleaning context data (for batch processing)
            force_ai_refresh: Force removal of AI assessment cache for fresh analysis
        """
        Logger.info(f"🧹 Cleaning up PR #{pr_number} workspace ({cleanup_mode} mode)...")
        
        # Core generated files that are always cleaned
        cleanup_items = [
            # Build cache files
            self.config.script_dir / f".build_cache_pr_{pr_number}",
            # Generated reports
            self.config.reports_dir / f"review-pr-{pr_number}.md",
            self.config.reports_dir / f"enhanced-review-pr-{pr_number}.md",
            self.config.reports_dir / f"test-logs-pr-{pr_number}",
            # Generated plans
            self.config.plans_dir / f"plan-pr-{pr_number}.md",
            self.config.plans_dir / f"enhanced-plan-pr-{pr_number}.md",
        ]
        
        # Add context cleanup only if not preserving context for batch processing
        if not preserve_context:
            cleanup_items.append(self.config.context_dir / f"pr-{pr_number}")
            # Also preserve logs directory during batch processing
            cleanup_items.append(self.config.logs_dir)
        
        # Add spring-ai repo only for full cleanup
        if cleanup_mode == 'full':
            cleanup_items.append(self.config.spring_ai_dir)
        
        success = True
        cleaned_count = 0
        
        if dry_run:
            Logger.info("[DRY RUN] Would clean the following items:")
            for item in cleanup_items:
                if isinstance(item, str):
                    Logger.info(f"[DRY RUN]   - Git branch: {item}")
                else:
                    Logger.info(f"[DRY RUN]   - File/Directory: {item}")
            return True
        
        # Handle git branch cleanup based on cleanup mode
        if cleanup_mode == 'light' and self.config.spring_ai_dir.exists():
            # For light cleanup, just ensure we're on main branch
            try:
                current_branch = self.git.run_git(["rev-parse", "--abbrev-ref", "HEAD"], capture_output=True).stdout.strip()
                if current_branch != self.config.main_branch:
                    Logger.info(f"🔄 Switching from {current_branch} to main branch...")
                    
                    # Check for uncommitted changes before switching
                    try:
                        status_result = self.git.run_git(["status", "--porcelain"], capture_output=True)
                        if status_result.stdout.strip():
                            Logger.info("🔄 Found uncommitted changes - discarding them...")
                            self.git.run_git(["reset", "--hard", "HEAD"])
                            self.git.run_git(["clean", "-fd"])
                    except Exception as reset_error:
                        Logger.warn(f"Error resetting changes: {reset_error}")
                    
                    self.git.run_git(["checkout", self.config.main_branch])
                    Logger.info("✅ Switched to main branch (keeping repository)")
                    
                    # Delete the PR branch for cleaner state
                    self._delete_pr_branch(current_branch, pr_number)
            except Exception as e:
                Logger.warn(f"Error switching to main branch: {e}")
                # Still try to delete PR branch if we know what it was
                if hasattr(self, 'current_pr_branch') and self.current_pr_branch:
                    self._delete_pr_branch(self.current_pr_branch, pr_number)
        elif cleanup_mode == 'full':
            # For full cleanup, the entire spring-ai directory will be removed
            Logger.info("📁 Spring AI directory will be completely removed (full cleanup)")
        else:
            Logger.info("📁 Spring AI directory doesn't exist (already clean)")
        
        # Clean up files and directories
        for item in cleanup_items:
            try:
                if item.exists():
                    if item.is_file():
                        Logger.info(f"Removing file: {item}")
                        item.unlink()
                    elif item.is_dir():
                        Logger.info(f"Removing directory: {item}")
                        shutil.rmtree(item)
                    cleaned_count += 1
                else:
                    # Item doesn't exist, which is fine (already clean)
                    pass
                    
            except Exception as e:
                Logger.warn(f"Error cleaning {item}: {e}")
                success = False
        
        # Clean up Python cache files
        try:
            cache_dir = self.config.script_dir / "__pycache__"
            if cache_dir.exists():
                Logger.info("Removing Python cache files...")
                shutil.rmtree(cache_dir)
                cleaned_count += 1
        except Exception as e:
            Logger.warn(f"Error cleaning Python cache: {e}")
        
        if success:
            Logger.success(f"✅ Cleaned {cleaned_count} items for PR #{pr_number}")
            Logger.info("🧹 Workspace is now clean and ready for fresh testing")
        else:
            Logger.warn(f"⚠️  Partially cleaned workspace - some items couldn't be removed")
        
        return success
    
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
        if not self._handle_compilation_errors(pr_number, dry_run):
            Logger.error("❌ Compilation errors could not be resolved")
            return False
        
        # Run full Maven build (this also serves as final compilation verification)
        # Use mvnd for fastest builds (with fb as backup)
        build_commands = [
            (["fb"], "Run compilation check with fb alias"),
            (["mvnd", "clean", "install", "-Dmaven.javadoc.skip=true", "-DskipTests"], "Run Maven build with mvnd")
        ]
        
        for cmd, description in build_commands:
            if cmd[0] == "fb":
                # Check if fb alias exists
                if not shutil.which("fb"):
                    continue
            elif cmd[0] == "mvnd":
                # Check if mvnd exists
                if not shutil.which("mvnd"):
                    Logger.error("mvnd not found - please install Maven Daemon for fastest builds")
                    continue
            
            Logger.info(f"Using {cmd[0]} for build...")
            
            # Create timestamped log file for build output
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            build_log_file = self.config.logs_dir / f"build-check-{timestamp}.log"
            
            if self.run_command(cmd, description, cwd=self.config.spring_ai_dir, 
                               suppress_output=True, log_file=build_log_file):
                Logger.success(f"✅ Build with {cmd[0]} completed successfully")
                Logger.info(f"Build output logged to: {build_log_file}")
                self.build_cache.save_build_success(pr_number)
                return True
            else:
                Logger.error(f"❌ Build with {cmd[0]} failed!")
                Logger.error(f"Check build log for details: {build_log_file}")
                
                # Show last few lines of build log for immediate debugging
                if build_log_file.exists():
                    try:
                        with open(build_log_file, 'r') as f:
                            lines = f.readlines()
                            if lines:
                                Logger.error("Last 10 lines from build log:")
                                for line in lines[-10:]:
                                    Logger.error(f"  {line.rstrip()}")
                    except Exception as e:
                        Logger.error(f"Could not read build log: {e}")
                
                Logger.warn(f"Trying next build option...")
        
        Logger.error("All build options failed")
        return False
    
    def run_antora_docs_build(self, pr_number: str, skip_docs: bool = False, dry_run: bool = False) -> bool:
        """Run Antora documentation build for PRs containing .adoc files"""
        if skip_docs:
            Logger.info("📚 Skipping documentation build as requested")
            return True
        
        # Check if PR contains .adoc files
        if not self._has_adoc_files(pr_number):
            Logger.info("📚 No .adoc files found - skipping documentation build")
            return True
        
        Logger.info("📚 Running Antora documentation build...")
        
        if dry_run:
            Logger.info("[DRY RUN] Would run: ./mvnw -pl spring-ai-docs antora")
            return True
        
        # Create timestamped log file for documentation build output
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        docs_log_file = self.config.logs_dir / f"antora-docs-{timestamp}.log"
        
        # Ensure logs directory exists
        docs_log_file.parent.mkdir(exist_ok=True)
        
        # Run Antora documentation build
        cmd = ["./mvnw", "-pl", "spring-ai-docs", "antora"]
        description = "Build Antora documentation"
        
        Logger.info(f"Running documentation build: {' '.join(cmd)}")
        
        success = self.run_command(
            cmd, 
            description, 
            cwd=self.config.spring_ai_dir,
            suppress_output=True,
            log_file=docs_log_file
        )
        
        if success:
            Logger.success("✅ Antora documentation build completed successfully")
            Logger.info(f"Documentation build output logged to: {docs_log_file}")
            return True
        else:
            Logger.error("❌ Antora documentation build failed!")
            Logger.error(f"Check documentation build log for details: {docs_log_file}")
            
            # Show last few lines of documentation build log for immediate debugging
            if docs_log_file.exists():
                try:
                    with open(docs_log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            Logger.error("Last 10 lines from documentation build log:")
                            for line in lines[-10:]:
                                Logger.error(f"  {line.rstrip()}")
                except Exception as e:
                    Logger.error(f"Could not read documentation build log: {e}")
            
            return False
    
    def squash_commits(self, pr_number: str, skip_squash: bool = False, dry_run: bool = False) -> bool:
        """Squash commits using intelligent squash script"""
        if skip_squash:
            Logger.info("Skipping commit squashing as requested")
            return True
        
        Logger.info("Using intelligent squash script...")
        
        # Use the new intelligent squash script
        squash_script = self.config.script_dir / "intelligent_squash.py"
        
        if not squash_script.exists():
            Logger.error(f"Intelligent squash script not found: {squash_script}")
            return False
        
        try:
            cmd = ["python3", str(squash_script), pr_number]
            if dry_run:
                cmd.append("--dry-run")
            
            Logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=self.config.script_dir,
                capture_output=False,  # Let output show directly
                text=True,
                check=True
            )
            
            Logger.success("✅ Intelligent squash completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"❌ Intelligent squash failed with exit code {e.returncode}")
            return False
        except Exception as e:
            Logger.error(f"❌ Error running intelligent squash: {e}")
            return False
    
    def generate_commit_message(self, pr_number: str, skip_commit_message: bool = False, 
                              dry_run: bool = False) -> Optional[str]:
        """Generate comprehensive commit message using AI"""
        if skip_commit_message:
            Logger.info("Skipping AI commit message generation as requested")
            return None
        
        if dry_run:
            Logger.info("🎭 DRY RUN: Would generate AI-powered commit message")
            return None
        
        try:
            Logger.info(f"🤖 Generating comprehensive commit message for PR #{pr_number}")
            
            # Get PR context directory
            pr_context_dir = self.config.context_dir / f"pr-{pr_number}"
            
            # Validate that context directory exists and has required data
            if not pr_context_dir.exists():
                error_msg = f"❌ CRITICAL ERROR: Context directory not found for PR #{pr_number}"
                Logger.error(error_msg)
                Logger.error(f"Expected: {pr_context_dir}")
                Logger.error("Context collection must run successfully before commit message generation")
                raise RuntimeError(f"Context directory not found: {pr_context_dir}")
            
            # Check for essential context files
            required_files = ["pr-data.json"]
            missing_files = []
            for file_name in required_files:
                if not (pr_context_dir / file_name).exists():
                    missing_files.append(file_name)
            
            if missing_files:
                error_msg = f"❌ CRITICAL ERROR: Missing context files for PR #{pr_number}: {missing_files}"
                Logger.error(error_msg)
                Logger.error(f"Context directory: {pr_context_dir}")
                Logger.error("All required context files must be present for commit message generation")
                raise RuntimeError(f"Missing required context files: {missing_files}")
            
            Logger.info(f"✅ Context validation passed for PR #{pr_number}")
            
            # Initialize commit message generator
            generator = CommitMessageGenerator(self.config.script_dir, logs_dir=self.config.logs_dir)
            
            # Generate the commit message (now error-raising, no fallback)
            result = generator.generate_commit_message(
                pr_number=pr_number,
                pr_context_dir=pr_context_dir,
                fallback_title=None  # No longer needed since no fallback
            )
            
            # The generator now always raises on error, so result.success should always be True
            Logger.success(f"✅ Generated AI-powered commit message ({result.processing_time:.1f}s)")
            return result.message
                
        except Exception as e:
            Logger.error(f"❌ CRITICAL ERROR: Commit message generation failed for PR #{pr_number}: {e}")
            Logger.error("This indicates a problem with context collection, Claude Code availability, or template files")
            raise  # Re-raise instead of falling back
    
    def collect_pr_context(self, pr_number: str, dry_run: bool = False) -> bool:
        """Collect PR context data for AI analysis"""
        if dry_run:
            Logger.info("🎭 DRY RUN: Would collect PR context data")
            return True
        
        try:
            # Collect context data
            context_collector = self.config.script_dir / "pr_context_collector.py"
            Logger.info("📋 Collecting context data for AI analysis...")
            context_result = subprocess.run(
                ["python3", str(context_collector), pr_number, "--context-dir", str(self.config.context_dir)], 
                cwd=self.config.script_dir,
                capture_output=True, 
                text=True, 
                timeout=120
            )

            # Debug: Log context collection output
            Logger.info(f"🔍 Context collection return code: {context_result.returncode}")
            if context_result.stdout:
                Logger.info(f"🔍 Context collection stdout: {context_result.stdout.strip()}")
            if context_result.stderr:
                Logger.warn(f"🔍 Context collection stderr: {context_result.stderr.strip()}")

            if context_result.returncode != 0:
                error_msg = f"❌ CRITICAL ERROR: Context collection failed for PR #{pr_number}"
                Logger.error(error_msg)
                Logger.error(f"Return code: {context_result.returncode}")
                Logger.error(f"Command: python3 pr_context_collector.py {pr_number} --context-dir {self.config.context_dir}")
                Logger.error(f"Error output: {context_result.stderr}")
                Logger.error(f"Standard output: {context_result.stdout}")
                Logger.error("Context collection must succeed before any downstream AI analysis")
                return False
            
            # Verify context data was actually created
            context_dir = self.config.context_dir / f"pr-{pr_number}"
            if not context_dir.exists():
                error_msg = f"❌ CRITICAL ERROR: Context directory not created for PR #{pr_number}"
                Logger.error(error_msg)
                Logger.error(f"Expected directory: {context_dir}")
                Logger.error(f"Context collection completed with return code 0 but directory is missing")
                Logger.error("This indicates an issue with the pr_context_collector.py script")
                return False
            
            context_files = list(context_dir.glob("*.json"))
            Logger.info(f"🔍 Context files created: {len(context_files)} files")
            for file in context_files:
                Logger.info(f"   - {file.name}")
            
            Logger.success("✅ Context data collection completed")
            return True
            
        except Exception as e:
            Logger.error(f"❌ Error during context collection for PR #{pr_number}: {e}")
            return False
    
    def rebase_against_upstream(self, pr_number: str, auto_resolve: bool = False, dry_run: bool = False) -> bool:
        """Rebase against upstream main"""
        Logger.info(f"Rebasing against {self.config.upstream_remote}/{self.config.main_branch}...")
        
        if dry_run:
            Logger.info(f"[DRY RUN] Would rebase against {self.config.upstream_remote}/{self.config.main_branch}")
            return True
        
        # Check for uncommitted changes (e.g., from CompilationErrorResolver auto-fixes)
        try:
            status_result = self.git.run_git(["status", "--porcelain"], capture_output=True)
            if status_result.stdout.strip():
                Logger.info("🔧 Found uncommitted changes from auto-fixes - committing them...")
                self.git.run_git(["add", "."])
                self.git.run_git(["commit", "-m", f"Auto-fix compilation errors in PR #{pr_number}\n\n🤖 Automatically resolved compilation errors using Claude Code"])
                Logger.success("✅ Committed auto-fix changes")
        except Exception as e:
            Logger.warn(f"Error checking/committing auto-fixes: {e}")
        
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
                    
                    # Ensure all resolved files are staged before continuing
                    try:
                        Logger.info("Staging all resolved files...")
                        self.git.run_git(["add", "."])
                        
                        Logger.info("Continuing rebase...")
                        self.git.run_git(["rebase", "--continue"])
                        Logger.success("Rebase completed successfully after auto-resolution")
                        return True
                    except subprocess.CalledProcessError as e:
                        # Check if rebase is actually complete
                        try:
                            # Check if we're still in rebase state
                            result = subprocess.run(
                                ["git", "status", "--porcelain"],
                                cwd=self.config.spring_ai_dir,
                                capture_output=True,
                                text=True
                            )
                            
                            # If no uncommitted changes and not in rebase, we're done
                            if not result.stdout.strip():
                                rebase_status = subprocess.run(
                                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                    cwd=self.config.spring_ai_dir,
                                    capture_output=True,
                                    text=True
                                )
                                if "HEAD" not in rebase_status.stdout:
                                    Logger.success("Rebase completed successfully (all conflicts resolved)")
                                    return True
                            
                            Logger.warn("Auto-resolution helped but rebase still has issues")
                            Logger.warn(f"Git error: {e}")
                        except Exception:
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
        """Attempt automatic conflict resolution using Claude Code AI only"""
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
                
            Logger.info(f"🤖 Attempting Claude Code AI resolution for: {file_path}")
            
            try:
                if self.resolve_with_claude_code(full_path):
                    # Stage the resolved file
                    self.git.run_git(["add", file_path])
                    resolved_count += 1
                    Logger.success(f"✅ Claude Code AI resolved conflicts in: {file_path}")
                else:
                    Logger.warn(f"❌ Could not auto-resolve conflicts in: {file_path}")
                    
            except Exception as e:
                Logger.warn(f"Error processing {file_path}: {e}")
        
        total_conflicts = len(conflicted_files)
        
        if resolved_count == total_conflicts:
            Logger.success(f"✅ All {total_conflicts} conflicts successfully resolved!")
            
            # Apply Java formatter after resolving conflicts to fix any formatting issues
            Logger.info("🎨 Applying Java formatter after conflict resolution...")
            if not self.apply_java_formatter():
                Logger.error("❌ Java formatter failed after conflict resolution - code will not pass CI")
                return False
            
            return True
        else:
            if resolved_count > 0:
                unresolved_count = total_conflicts - resolved_count
                Logger.warn(f"❌ Only resolved {resolved_count}/{total_conflicts} conflicts")
                Logger.warn(f"❌ {unresolved_count} conflicts still remain unresolved")
            else:
                Logger.warn("❌ No conflicts could be auto-resolved")
            
            Logger.warn("❌ Cannot continue - script must resolve ALL conflicts to proceed")
            return False
    
    def resolve_with_claude_code(self, file_path: Path) -> bool:
        """Resolve merge conflicts using Claude Code AI"""
        import subprocess
        import tempfile
        import os
        
        try:
            # Check if Claude Code CLI is available
            claude_path = '/home/mark/.nvm/versions/node/v22.15.0/bin/claude'
            try:
                subprocess.run([claude_path, '--version'], capture_output=True, check=True, timeout=5)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                Logger.warn("Claude Code CLI not available for AI conflict resolution")
                return False
            
            # Check if file actually has conflicts
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not any(marker in content for marker in ['<<<<<<<', '>>>>>>>', '=======']):
                return False  # No conflicts to resolve
            
            Logger.info(f"🤖 Using Claude Code AI to resolve conflicts in: {file_path.name}")
            
            # Save conflicted file for debugging
            debug_file = self.config.logs_dir / f"conflict-debug-{file_path.name}"
            debug_file.parent.mkdir(exist_ok=True)
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(content)
            Logger.info(f"🔍 Saved conflicted file for debugging: {debug_file}")
            
            # Create prompt for Claude Code
            claude_prompt = """Please resolve this Git merge conflict intelligently.

IMPORTANT: Output ONLY the clean file content - no explanations, no markdown code blocks, no comments.

The file contains Git conflict markers (<<<<<<< HEAD, =======, >>>>>>> branch).
Analyze the conflicting changes and resolve them appropriately:
- If both changes are compatible, merge them
- If they conflict, choose the better/newer version
- Remove all conflict markers

File content with conflicts:"""
            
            # Log the prompt being sent to Claude Code
            full_prompt = claude_prompt + '\n\n' + content
            Logger.info(f"🔍 Claude Code prompt length: {len(full_prompt)} chars")
            Logger.info(f"🔍 Conflict markers in file: {content.count('<<<<<<<')} conflicts detected")
            Logger.info(f"🔍 File size: {len(content)} chars, {len(content.split(chr(10)))} lines")
            
            # Save full prompt sent to Claude Code for debugging
            prompt_debug_file = self.config.logs_dir / f"claude-prompt-{file_path.name}.txt"
            with open(prompt_debug_file, 'w', encoding='utf-8') as f:
                f.write(claude_prompt + '\n\n')
                f.write(content)
            Logger.info(f"🔍 Saved Claude Code prompt for debugging: {prompt_debug_file}")
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as input_file:
                input_file.write(claude_prompt + '\n\n')
                input_file.write(content)
                input_file_path = input_file.name
            
            try:
                # Use full path to Claude Code to ensure correct version
                claude_path = '/home/mark/.nvm/versions/node/v22.15.0/bin/claude'
                
                # Debug: Check what version is being called
                version_check = subprocess.run([claude_path, '--version'], capture_output=True, text=True, check=False)
                Logger.info(f"🔍 Claude Code version being called: {version_check.stdout.strip() if version_check.stdout else 'No stdout'}")
                Logger.info(f"🔍 Claude Code version stderr: {version_check.stderr.strip() if version_check.stderr else 'No stderr'}")
                
                # Use ClaudeCodeWrapper with permissions skip for temp files
                logs_dir = self.config.logs_dir
                logs_dir.mkdir(exist_ok=True)
                claude = ClaudeCodeWrapper(logs_dir=logs_dir)
                
                if not claude.is_available():
                    Logger.error("❌ Claude Code is not available")
                    return None
                
                # Use wrapper to analyze from file (conflict resolution doesn't need JSON output)
                logs_dir = self.config.logs_dir
                logs_dir.mkdir(exist_ok=True)
                debug_response_file = logs_dir / f"claude-response-conflict-resolution-{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                result = claude.analyze_from_file(str(input_file_path), str(debug_response_file), timeout=300, use_json_output=False, system_debug_mode=True)
                
                # Debug: Log Claude Code execution details
                Logger.info(f"🔍 Claude Code execution - Success: {result['success']}")
                if result['success']:
                    Logger.info(f"🔍 Claude Code stdout length: {len(result['response']) if result['response'] else 0} chars")
                else:
                    Logger.error(f"🔍 Claude Code error: {result['error']}")
                    Logger.info(f"🔍 Claude Code stderr: {result['stderr'] if result['stderr'] else 'None'}")
                
                # Response is already saved to debug_response_file by the wrapper
                Logger.info(f"🔍 Saved Claude Code response for debugging: {debug_response_file}")
                
                if result['success'] and result['response'] and result['response'].strip():
                    resolved_content = result['response'].strip()
                    Logger.info(f"🔍 Claude Code response preview: {resolved_content[:100]}...")
                    
                    # Strip markdown code fences if present
                    lines = resolved_content.split('\n')
                    if lines and lines[0].startswith('```'):
                        lines = lines[1:]
                        Logger.info("🔍 Stripped opening code fence")
                    if lines and lines[-1].startswith('```'):
                        lines = lines[:-1]
                        Logger.info("🔍 Stripped closing code fence")
                    resolved_content = '\n'.join(lines)
                    
                    # Verify the result doesn't still have conflict markers
                    conflict_markers = ['<<<<<<<', '>>>>>>>', '=======']
                    remaining_markers = [marker for marker in conflict_markers if marker in resolved_content]
                    
                    if not remaining_markers:
                        # Verify the file is not empty and seems reasonable
                        original_lines = len(content.split('\n'))
                        resolved_lines = len(resolved_content.split('\n'))
                        
                        Logger.info(f"🔍 Line count: {original_lines} → {resolved_lines}")
                        Logger.info(f"🔍 Content length: {len(content)} → {len(resolved_content)} chars")
                        
                        if resolved_content.strip() and resolved_lines > original_lines // 2:
                            # Write resolved content back to original file
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(resolved_content)
                            
                            Logger.success(f"✅ Claude Code successfully resolved conflicts in: {file_path.name}")
                            return True
                        else:
                            Logger.warn(f"❌ Claude Code resolution failed - suspicious output for: {file_path.name}")
                            Logger.warn(f"   Content empty: {not resolved_content.strip()}")
                            Logger.warn(f"   Lines too few: {resolved_lines} <= {original_lines // 2}")
                            return False
                    else:
                        Logger.warn(f"❌ Claude Code output still contains conflict markers for: {file_path.name}")
                        Logger.warn(f"   Remaining markers: {remaining_markers}")
                        Logger.info(f"🔍 Problematic content preview: {resolved_content[:200]}...")
                        return False
                else:
                    Logger.warn(f"❌ Claude Code failed to process: {file_path.name}")
                    Logger.warn(f"   Success: {result['success']}")
                    if result.get('error'):
                        Logger.warn(f"   Error: {result['error']}")
                    if result.get('response'):
                        Logger.warn(f"   Response preview: {result['response'][:200]}...")
                    if result.get('stderr'):
                        Logger.warn(f"   Stderr: {result['stderr'].strip()}")
                    return False
                
            finally:
                # Clean up temporary files
                try:
                    os.unlink(input_file_path)
                except OSError:
                    pass
            
            return False
            
        except Exception as e:
            Logger.warn(f"⚠️  Claude Code resolution failed for {file_path.name}: {e}")
            return False
    
    
    
    
    def run_complete_workflow(self, pr_number: str, skip_squash: bool = False, skip_compile: bool = False, 
                            skip_tests: bool = False, skip_docs: bool = False, auto_resolve: bool = False, force: bool = False, generate_report: bool = True, skip_commit_message: bool = False, resume_after_compile: bool = False, dry_run: bool = False) -> bool:
        """Run the complete PR workflow"""
        Logger.info(f"🚀 Starting complete PR review workflow for PR #{pr_number}")
        
        if dry_run:
            Logger.warn("DRY RUN MODE - No actual changes will be made")
        
        # Phase 1: Setup repository (skip when resuming after manual fixes)
        if not resume_after_compile:
            if not self.setup_repository(dry_run):
                Logger.error("❌ Repository setup failed")
                return False
            
            # Phase 1b: Setup MCP SDK repository
            if not self.setup_mcp_sdk_repository(dry_run):
                Logger.error("❌ MCP SDK repository setup failed")
                return False
            
            # Phase 2: Checkout PR
            if not self.checkout_pr(pr_number, force, dry_run):
                Logger.error("❌ PR checkout failed")
                return False
        else:
            Logger.info("🔄 Resuming after manual compilation fixes - preserving current git state")
            Logger.info(f"💡 Working in current branch with manual fixes intact")
        
        # Phase 3: Build check
        # Skip compilation when resuming after manual fixes
        effective_skip_compile = skip_compile or resume_after_compile
        if resume_after_compile:
            Logger.info("🔄 Resuming after manual compilation fixes - skipping compilation check")
        if not self.run_build_check(pr_number, effective_skip_compile, dry_run):
            Logger.error("❌ Build check failed")
            return False
        
        # Phase 4: Squash commits (mandatory for multi-commit PRs)
        # Skip squash when resuming to preserve manual fix commits
        effective_skip_squash = skip_squash or resume_after_compile
        if resume_after_compile:
            Logger.info("🔄 Skipping squash to preserve manual compilation fix commits")
        if not self.squash_commits(pr_number, effective_skip_squash, dry_run):
            Logger.error("❌ Squash commits failed - cannot proceed with multi-commit rebase")
            return False
        
        # Phase 4.5: Collect PR context for AI analysis
        if not skip_commit_message or generate_report:
            Logger.info("📋 Collecting PR context for AI analysis...")
            if not self.collect_pr_context(pr_number, dry_run):
                Logger.error("❌ Context collection failed")
                return False
        
        # Phase 4.6: Generate comprehensive commit message (DISABLED)
        # TODO: Fix commit message generation before re-enabling
        # commit_message = self.generate_commit_message(pr_number, skip_commit_message, dry_run)
        # if commit_message and not dry_run:
        #     # Update the commit message if we generated one
        #     Logger.info("📝 Updating commit with AI-generated message")
        #     try:
        #         # Amend the commit with the new message
        #         result = subprocess.run(
        #             ["git", "commit", "--amend", "-m", commit_message],
        #             cwd=self.config.spring_ai_dir,
        #             capture_output=True,
        #             text=True,
        #             check=True
        #         )
        #         Logger.success("✅ Updated commit with comprehensive message")
        #     except subprocess.CalledProcessError as e:
        #         Logger.warn(f"⚠️  Could not update commit message: {e}")
        Logger.info("📝 Skipping commit message rewrite (disabled)")
        Logger.warn("Proceeding with existing commit message")
        
        # Phase 5: Rebase against upstream
        if not self.rebase_against_upstream(pr_number, auto_resolve, dry_run):
            Logger.error("❌ Rebase failed with conflicts")
            Logger.info("Resolve conflicts and run the workflow again")
            return False
        
        # Phase 5.5: Build documentation if PR contains .adoc files
        # This happens after rebase/conflict resolution and compilation
        if not self.run_antora_docs_build(pr_number, skip_docs=skip_docs, dry_run=dry_run):
            Logger.error("❌ Documentation build failed")
            return False
        
        # Phase 6: Generate PR Analysis Report (if requested)
        report_file = None
        if generate_report:
            Logger.info("📊 Generating PR analysis report...")
            report_file = self.pr_analyzer.generate_report(pr_number, dry_run)
            if report_file is None and not dry_run:
                Logger.warn("⚠️  Report generation failed, but PR preparation was successful")
        
        # Phase 7: Run tests for changed test files
        if not skip_compile and not skip_tests and not dry_run:
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
                
                # Show both HTML and Markdown report locations
                if str(report_file).endswith('.md'):
                    # Markdown report exists, check for HTML version
                    html_report = str(report_file).replace('.md', '.html')
                    if Path(html_report).exists():
                        Logger.info(f"🌐 HTML report: {html_report}")
                        Logger.info(f"📄 Markdown report: {report_file}")
                elif str(report_file).endswith('.html'):
                    # HTML report exists, check for Markdown version  
                    md_report = str(report_file).replace('.html', '.md')
                    if Path(md_report).exists():
                        Logger.info(f"🌐 HTML report: {report_file}")
                        Logger.info(f"📄 Markdown report: {md_report}")
                
                # Show how to open HTML report
                html_path = str(report_file).replace('.md', '.html') if str(report_file).endswith('.md') else str(report_file)
                if Path(html_path).exists():
                    Logger.info(f"💻 Open in browser: file://{Path(html_path).absolute()}")
        
        return True
    
    def run_report_only(self, pr_number: str, dry_run: bool = False, skip_backport: bool = False, force_fresh: bool = False, 
                       no_html: bool = False, html_only: bool = False, open_browser: bool = False) -> bool:
        """Generate enhanced PR analysis report with AI-powered analysis (assumes PR is already prepared)"""
        Logger.info(f"📊 Generating PR analysis report for PR #{pr_number}")
        
        # Report-only mode will force fresh AI analysis
        
        if dry_run:
            Logger.warn("DRY RUN MODE - No actual report will be generated")
        
        # Validate that we're in the right state
        if not self.config.spring_ai_dir.exists():
            Logger.error(f"Spring AI repository not found: {self.config.spring_ai_dir}")
            Logger.error("Please run the full workflow first to prepare the PR")
            return False
        
        # Ensure we're on the correct branch for this PR
        if not self.github_utils.ensure_correct_branch(pr_number, self.config.spring_ai_dir):
            Logger.error(f"Failed to switch to correct branch for PR #{pr_number}")
            return False
        
        # Validate we're working with the correct PR by checking GitHub
        current_branch = self.git.get_current_branch()
        
        try:
            # Get the actual PR branch name from GitHub
            result = subprocess.run([
                "gh", "pr", "view", pr_number, "--repo", self.config.spring_ai_repo,
                "--json", "headRefName"
            ], cwd=self.config.spring_ai_dir, capture_output=True, text=True, check=True)
            
            pr_data = json.loads(result.stdout)
            actual_pr_branch = pr_data.get("headRefName")
            
            if actual_pr_branch and current_branch != actual_pr_branch:
                Logger.warn(f"Current branch is '{current_branch}', but PR #{pr_number} is from branch '{actual_pr_branch}'")
                Logger.warn("You may be generating a report for the wrong PR or branch")
                Logger.info(f"Consider running: gh pr checkout {pr_number}")
                
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            Logger.warn(f"Could not validate PR branch from GitHub: {e}")
            Logger.info(f"Current branch: '{current_branch}' - ensure this matches PR #{pr_number}")
        
        # Generate reports based on options
        report_file = None
        html_report_file = None
        
        # Generate markdown report unless html-only mode
        if not html_only:
            report_file = self.pr_analyzer.generate_report(pr_number, dry_run, force_fresh=force_fresh, skip_backport=skip_backport)
            if report_file:
                Logger.success(f"📋 Markdown report generated: {report_file}")
            else:
                Logger.error("❌ Markdown report generation failed")
                if not html_only:  # If this was the only report type requested, fail
                    return False
        
        # Generate HTML report unless no-html mode or if markdown failed and we're not in html-only mode
        if not no_html and not dry_run and (report_file or html_only):
            try:
                from single_pr_html_generator import SinglePRHTMLGenerator
                
                html_generator = SinglePRHTMLGenerator(
                    working_dir=self.config.script_dir,
                    context_dir=self.config.context_dir,
                    reports_dir=self.config.reports_dir,
                    logs_dir=self.config.logs_dir
                )
                
                html_report_file = html_generator.generate_html_report(pr_number)
                
                if html_report_file:
                    Logger.success(f"🎨 HTML report generated: {html_report_file}")
                    
                    # Open browser if requested
                    if open_browser:
                        try:
                            import webbrowser
                            file_url = f"file://{html_report_file.absolute()}"
                            webbrowser.open(file_url)
                            Logger.info(f"🌐 Opened HTML report in browser: {file_url}")
                        except Exception as e:
                            Logger.warn(f"⚠️  Could not open browser: {e}")
                            Logger.info(f"🔗 Manual URL: file://{html_report_file.absolute()}")
                else:
                    Logger.warn("⚠️  HTML report generation failed")
                    if html_only:  # If this was the only report type requested, fail
                        return False
                    
            except Exception as e:
                Logger.warn(f"⚠️  HTML report generation failed: {e}")
                if html_only:  # If this was the only report type requested, fail
                    Logger.error("❌ HTML-only mode failed")
                    return False
                Logger.info("📋 Markdown report is still available")
        
        # Summary of what was generated
        if report_file and html_report_file:
            Logger.info(f"📊 Dual output generated:")
            Logger.info(f"   📄 Markdown: {report_file}")
            Logger.info(f"   🌐 HTML: {html_report_file}")
            Logger.info(f"   🔗 Open HTML: file://{html_report_file.absolute()}")
        elif report_file:
            Logger.info(f"📄 Markdown report: {report_file}")
        elif html_report_file:
            Logger.info(f"🌐 HTML report: {html_report_file}")
            Logger.info(f"🔗 Open HTML: file://{html_report_file.absolute()}")
        else:
            Logger.error("❌ No reports were generated successfully")
            return False
            
        return True
    
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
    
    def get_changed_test_files(self, pr_number: str) -> List[str]:
        """Get list of changed test files from the original PR (not post-rebase diff)"""
        changed_files = self._get_changed_files(pr_number)
        test_files = [file for file in changed_files if self._is_test_file(file)]
        
        Logger.info(f"Original PR files: {len(changed_files)} total, {len(test_files)} test files")
        return test_files
    
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
    
    def _get_changed_files(self, pr_number: str) -> List[str]:
        """Get list of all changed files from the original PR (not post-rebase diff)"""
        try:
            # Get original files from the PR using GitHub CLI
            result = subprocess.run([
                "gh", "pr", "view", pr_number, "--repo", self.config.spring_ai_repo,
                "--json", "files", "--jq", ".files[].path"
            ], cwd=self.config.spring_ai_dir, capture_output=True, text=True, check=True)
            
            changed_files = result.stdout.strip().split('\n')
            # Filter out empty strings
            return [file for file in changed_files if file]
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to get original PR files: {e}")
            Logger.warn("Falling back to git diff method...")
            
            # Fallback to git diff method
            try:
                result = self.git.run_git([
                    "diff", "--name-only", f"{self.config.upstream_remote}/{self.config.main_branch}"
                ], capture_output=True)
                
                if result.returncode == 0:
                    return [file for file in result.stdout.strip().split('\n') if file]
                else:
                    Logger.error("Git diff fallback also failed")
                    return []
                    
            except Exception as fallback_error:
                Logger.error(f"Git diff fallback failed: {fallback_error}")
                return []
    
    def _has_adoc_files(self, pr_number: str) -> bool:
        """Check if PR contains any .adoc documentation files"""
        changed_files = self._get_changed_files(pr_number)
        adoc_files = [file for file in changed_files if file.endswith('.adoc')]
        
        if adoc_files:
            Logger.info(f"📚 Found {len(adoc_files)} .adoc documentation files in PR #{pr_number}")
            for file in adoc_files:
                Logger.info(f"   - {file}")
            return True
        else:
            Logger.info(f"📚 No .adoc documentation files found in PR #{pr_number}")
            return False
    
    def get_changed_adoc_files(self, pr_number: str) -> List[str]:
        """Get list of changed .adoc documentation files from the original PR"""
        changed_files = self._get_changed_files(pr_number)
        adoc_files = [file for file in changed_files if file.endswith('.adoc')]
        
        Logger.info(f"📚 Documentation files: {len(adoc_files)} .adoc files")
        return adoc_files
    
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
        
        test_files = self.get_changed_test_files(pr_number)
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
        
        # First do a complete build to ensure all dependencies are available
        Logger.info("🔨 Performing complete build to ensure all dependencies are available...")
        
        # Create timestamped log file for build output
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        build_log_file = self.config.logs_dir / f"full-build-{timestamp}.log"
        build_log_file.parent.mkdir(exist_ok=True)
        
        full_build_cmd = [
            "mvnd", "install", 
            "-B",  # Batch mode - disable fancy output
            "-U",  # Force update snapshots - ignore cached dependency failures
            "--no-transfer-progress",  # Disable transfer progress
            "-Dmaven.javadoc.skip=true",
            "-DskipTests",  # Skip tests in dependency build - we'll run them separately
            "-Djansi.force=false",  # Disable ANSI escape sequences
            "-Dorg.slf4j.simpleLogger.log.org.apache.maven.cli.transfer.Slf4jMavenTransferListener=warn"  # Suppress download progress
        ]
        
        try:
            # Set environment variables to disable terminal features
            env = os.environ.copy()
            env.update({
                'TERM': 'dumb',           # Disable terminal capabilities
                'NO_COLOR': '1',          # Disable color output
                'MAVEN_OPTS': '-Djansi.force=false -Dorg.slf4j.simpleLogger.showDateTime=true'
            })
            
            # Comprehensive mvnd output suppression
            with open(build_log_file, 'w') as log_f:
                log_f.write(f"Build Command: {' '.join(full_build_cmd)}\n")
                log_f.write(f"Working Directory: {self.config.spring_ai_dir}\n")
                log_f.write("=" * 80 + "\n")
                log_f.flush()
                
                build_result = subprocess.run(
                    full_build_cmd,
                    cwd=self.config.spring_ai_dir,
                    stdout=log_f,              # Redirect stdout to log file
                    stderr=log_f,              # Redirect stderr to log file  
                    stdin=subprocess.DEVNULL,   # Close stdin
                    start_new_session=True,     # Detach from terminal session
                    env=env,                   # Use modified environment
                    timeout=600  # 10 minutes for full build
                )
                
                log_f.write(f"\n{'=' * 80}\n")
                log_f.write(f"Return Code: {build_result.returncode}\n")
            
            if build_result.returncode != 0:
                Logger.error("❌ Full build failed - cannot run tests")
                Logger.error(f"Build output saved to: {build_log_file}")
                
                # Show last few lines of build log for immediate debugging
                try:
                    with open(build_log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            Logger.error("Last 10 lines from full build log:")
                            for line in lines[-10:]:
                                Logger.error(f"  {line.rstrip()}")
                except Exception as e:
                    Logger.error(f"Could not read full build log: {e}")
                
                return False
            else:
                Logger.success("✅ Full build completed successfully")
                Logger.info(f"Build output logged to: {build_log_file}")
                
        except subprocess.TimeoutExpired:
            Logger.error("❌ Full build timed out")
            return False
        except Exception as e:
            Logger.error(f"❌ Full build failed with exception: {e}")
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
                
                # Run single test class using mvnd from project root (dependencies already built)
                # Get relative module path from project root
                relative_module = module_path.relative_to(self.config.spring_ai_dir)
                
                # Run the specific test in the target module (dependencies already compiled)
                test_cmd = [
                    "mvnd", "test", 
                    f"-pl", str(relative_module),
                    "-U",  # Force update snapshots - ignore cached dependency failures
                    f"-Dtest={test_class}",
                    "-Dmaven.javadoc.skip=true"
                ]
                
                try:
                    result = subprocess.run(
                        test_cmd,
                        cwd=self.config.spring_ai_dir,  # Run from project root
                        capture_output=True,
                        text=True,
                        timeout=600  # 10 minute timeout for integration tests
                    )
                    
                    # Save full test output to log file
                    with open(log_file, 'w') as f:
                        f.write(f"Test Command: {' '.join(test_cmd)}\n")
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
                        f.write(f"Test Command: {' '.join(test_cmd)}\n")
                        f.write(f"Working Directory: {module_path}\n")
                        f.write("STATUS: TIMEOUT after 10 minutes\n")
                    test_results.append((test_class, "TIMEOUT", str(log_file)))
                    success = False
                except Exception as e:
                    Logger.error(f"❌ {test_class} - ERROR: {e}")
                    with open(log_file, 'w') as f:
                        f.write(f"Test Command: {' '.join(test_cmd)}\n")
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
  python3 pr_workflow.py 3386                      # Full workflow for PR #3386 (with auto-resolve)
  python3 pr_workflow.py --no-auto-resolve 3386    # Disable automatic conflict resolution
  python3 pr_workflow.py --skip-squash 3386        # Skip commit squashing
  python3 pr_workflow.py --skip-commit-message 3386 # Skip AI commit message generation
  python3 pr_workflow.py --skip-report 3386        # Skip report generation (prep only)
  python3 pr_workflow.py --report-only 3386        # Generate only the analysis report
  python3 pr_workflow.py --test-only 3386          # Run only the changed tests
  python3 pr_workflow.py --plan-only 3386          # Generate enhanced workflow plan
  python3 pr_workflow.py --cleanup 3386            # Clean up PR workspace (light mode - keeps spring-ai repo)
  python3 pr_workflow.py --cleanup 3386 --cleanup-mode full  # Full cleanup (removes everything)
  python3 pr_workflow.py --dry-run 3386            # Preview the workflow
  python3 pr_workflow.py --resume-after-compile 3386 # Resume after manually fixing compilation errors
        """
    )
    
    parser.add_argument('pr_number', help='GitHub PR number to process')
    parser.add_argument('--skip-squash', action='store_true', help='Skip commit squashing')
    parser.add_argument('--skip-compile', action='store_true', help='Skip compilation check')
    parser.add_argument('--skip-tests', action='store_true', help='Skip test execution')
    parser.add_argument('--skip-docs', action='store_true', help='Skip Antora documentation build')
    parser.add_argument('--skip-commit-message', action='store_true', help='Skip AI-powered commit message generation')
    parser.add_argument('--no-auto-resolve', action='store_true', help='Disable automatic conflict resolution (auto-resolve is enabled by default)')
    parser.add_argument('--force', action='store_true', help='Force operations (overwrite existing branches)')
    parser.add_argument('--skip-report', action='store_true', help='Skip PR analysis report generation')
    parser.add_argument('--report-only', action='store_true', help='Generate only the analysis report (assumes PR already prepared)')
    parser.add_argument('--skip-backport', action='store_true', help='Skip backport assessment in report generation')
    parser.add_argument('--force-fresh', action='store_true', help='Force fresh AI analysis (ignore cached assessments)')
    parser.add_argument('--no-html', action='store_true', help='Skip HTML report generation (generate only markdown)')
    parser.add_argument('--html-only', action='store_true', help='Generate only HTML report (skip markdown)')
    parser.add_argument('--open-browser', action='store_true', help='Automatically open HTML report in browser')
    parser.add_argument('--test-only', action='store_true', help='Run only the changed tests (assumes PR already prepared)')
    parser.add_argument('--plan-only', action='store_true', help='Generate enhanced workflow plan with progress tracking')
    parser.add_argument('--cleanup', action='store_true', help='Clean up PR workspace and generated files')
    parser.add_argument('--cleanup-mode', choices=['full', 'light'], default='light', 
                       help='Cleanup mode: full (remove everything including spring-ai repo) or light (keep spring-ai repo, remove generated files only)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--resume-after-compile', action='store_true', help='Resume workflow after manual compilation fixes (skips compilation check)')
    
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
    exclusive_options = [args.skip_report, args.report_only, args.test_only, args.plan_only, args.cleanup]
    if sum(exclusive_options) > 1:
        Logger.error("Cannot use multiple exclusive options: --skip-report, --report-only, --test-only, --plan-only, --cleanup")
        sys.exit(1)
    
    # Run the appropriate workflow
    if args.report_only:
        success = workflow.run_report_only(
            pr_number=args.pr_number,
            dry_run=args.dry_run,
            skip_backport=args.skip_backport,
            force_fresh=args.force_fresh,
            no_html=args.no_html,
            html_only=args.html_only,
            open_browser=args.open_browser
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
    elif args.cleanup:
        success = workflow.cleanup_pr_workspace(args.pr_number, cleanup_mode=args.cleanup_mode, dry_run=args.dry_run)
        if success:
            Logger.success(f"🧹 PR #{args.pr_number} workspace cleaned successfully")
        else:
            Logger.error("❌ Failed to clean up PR workspace")
    else:
        success = workflow.run_complete_workflow(
            pr_number=args.pr_number,
            skip_squash=args.skip_squash,
            skip_compile=args.skip_compile,
            skip_tests=args.skip_tests,
            skip_docs=args.skip_docs,
            auto_resolve=not args.no_auto_resolve,  # Auto-resolve by default unless disabled
            force=args.force,
            generate_report=not args.skip_report,
            skip_commit_message=args.skip_commit_message,
            resume_after_compile=args.resume_after_compile,
            dry_run=args.dry_run
        )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
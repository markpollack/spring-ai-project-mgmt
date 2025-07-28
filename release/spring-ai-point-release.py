#!/usr/bin/env python3
"""
Spring AI Point Release Script - 1.0.x Branch Automation

Automates point releases for Spring AI 1.0.x branch with enhanced safety and interactivity.
Based on proven patterns from pr-review scripts.

Usage:
    python3 spring-ai-point-release.py 1.0.1 --branch 1.0.x --dry-run
"""

import os
import sys
import subprocess
import argparse
import json
import shutil
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReleaseConfig:
    """Configuration for the point release workflow"""
    script_dir: Path
    target_version: str
    branch: str = "1.0.x"
    spring_ai_repo: str = "spring-projects/spring-ai"
    upstream_remote: str = "origin"
    dry_run: bool = False
    post_maven_central: bool = False
    skip_to: Optional[str] = None
    cleanup: bool = False
    
    @property
    def spring_ai_dir(self) -> Path:
        return self.script_dir / "spring-ai-release"
    
    @property
    def state_dir(self) -> Path:
        return self.script_dir / "state"
    
    @property
    def release_state_file(self) -> Path:
        return self.state_dir / f"release-{self.target_version}.json"
    
    @property
    def release_branch(self) -> str:
        """Get the release branch name (same as target version)"""
        return self.target_version
    
    @property
    def next_dev_version(self) -> str:
        """Calculate next development version from target version"""
        # Parse version like 1.0.1 -> 1.0.2-SNAPSHOT
        parts = self.target_version.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {self.target_version}. Expected X.Y.Z")
        
        major, minor, patch = parts
        next_patch = str(int(patch) + 1)
        return f"{major}.{minor}.{next_patch}-SNAPSHOT"
    
    @property
    def tag_name(self) -> str:
        return f"v{self.target_version}"
    
    def validate_version(self) -> bool:
        """Validate version format matches expected pattern"""
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, self.target_version))


class Colors:
    """ANSI color codes for console output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
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
    
    @staticmethod
    def step(message: str):
        print(f"{Colors.CYAN}[STEP]{Colors.NC} {message}")
    
    @staticmethod
    def bold(message: str):
        print(f"{Colors.BOLD}{message}{Colors.NC}")


class ReleaseGitHelper:
    """Git operations helper for release workflow"""
    
    def __init__(self, repo_dir: Path, config: ReleaseConfig):
        self.repo_dir = repo_dir
        self.config = config
    
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
            
            Logger.info(f"Running: {' '.join(cmd)} (in {self.repo_dir})")
            
            if self.config.dry_run:
                Logger.warn("DRY RUN: Would execute git command")
                # Return a mock successful result for dry run
                return subprocess.CompletedProcess(cmd, 0, '', '')
            
            result = subprocess.run(cmd, cwd=self.repo_dir, env=env, 
                                  capture_output=capture_output, text=True, check=check)
            return result
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Git command failed: {' '.join(cmd)}")
            Logger.error(f"Exit code: {e.returncode}")
            if e.stdout:
                Logger.error(f"Stdout: {e.stdout}")
            if e.stderr:
                Logger.error(f"Stderr: {e.stderr}")
            raise
    
    def clone_repository(self) -> bool:
        """Clone the Spring AI repository"""
        try:
            if self.config.spring_ai_dir.exists():
                Logger.info(f"Removing existing directory: {self.config.spring_ai_dir}")
                if not self.config.dry_run:
                    shutil.rmtree(self.config.spring_ai_dir)
            
            clone_url = f"https://github.com/{self.config.spring_ai_repo}.git"
            cmd = ["git", "clone", clone_url, str(self.config.spring_ai_dir)]
            
            Logger.info(f"Cloning repository: {clone_url}")
            
            if self.config.dry_run:
                Logger.warn("DRY RUN: Would clone repository")
                return True
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            Logger.success("Repository cloned successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to clone repository: {e}")
            return False
    
    def checkout_branch(self) -> bool:
        """Checkout the target branch"""
        try:
            Logger.info(f"Checking out branch: {self.config.branch}")
            self.run_git(["checkout", self.config.branch])
            
            # Ensure we're up to date
            Logger.info("Pulling latest changes")
            self.run_git(["pull", self.config.upstream_remote, self.config.branch])
            
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_current_version(self) -> Optional[str]:
        """Get current version from main POM"""
        # In dry-run mode, repository isn't cloned so POM won't exist
        if self.config.dry_run:
            Logger.info("DRY RUN: Would read current version from pom.xml")
            return "X.Y.Z-SNAPSHOT (dry-run placeholder)"
        
        try:
            pom_path = self.repo_dir / "pom.xml"
            if not pom_path.exists():
                Logger.error("pom.xml not found")
                return None
            
            # Simple regex to extract version from POM
            with open(pom_path, 'r') as f:
                content = f.read()
                # Look for <version>X.Y.Z-SNAPSHOT</version> near the top
                match = re.search(r'<version>([^<]+)</version>', content)
                if match:
                    return match.group(1)
            
            return None
        except Exception as e:
            Logger.error(f"Failed to get current version: {e}")
            return None
    
    def commit_changes(self, message: str) -> bool:
        """Commit all changes with the given message"""
        try:
            self.run_git(["add", "-A"])
            self.run_git(["commit", "-m", message])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def create_tag(self, tag_name: str, message: str) -> bool:
        """Create an annotated tag"""
        try:
            self.run_git(["tag", "-a", tag_name, "-m", message])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def create_release_branch(self, branch_name: str, from_tag: str) -> bool:
        """Create a new release branch from a tag"""
        try:
            Logger.info(f"Creating release branch {branch_name} from tag {from_tag}")
            self.run_git(["checkout", "-b", branch_name, from_tag])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def push_changes(self) -> bool:
        """Push changes and tags to remote (legacy method)"""
        try:
            Logger.info(f"Pushing changes to {self.config.upstream_remote} {self.config.branch}")
            self.run_git(["push", self.config.upstream_remote, self.config.branch])
            
            Logger.info(f"Pushing tag {self.config.tag_name}")
            self.run_git(["push", self.config.upstream_remote, self.config.tag_name])
            
            return True
        except subprocess.CalledProcessError:
            return False
    
    def push_tag_only(self) -> bool:
        """Push only the release tag to remote (not the branch commits)"""
        try:
            Logger.info(f"Pushing tag {self.config.tag_name}")
            self.run_git(["push", self.config.upstream_remote, self.config.tag_name])
            
            Logger.info("ℹ️  Release commit stays local until Maven Central deployment succeeds")
            return True
        except subprocess.CalledProcessError:
            return False
    
    def push_branch_only(self) -> bool:
        """Push branch commits to remote (not tags)"""
        try:
            Logger.info(f"Pushing release commit to {self.config.upstream_remote} {self.config.branch}")
            self.run_git(["push", self.config.upstream_remote, self.config.branch])
            
            return True
        except subprocess.CalledProcessError:
            return False
    
    def push_tag_and_release_branch(self) -> bool:
        """Push tag and release branch to remote (not maintenance branch)"""
        try:
            Logger.info(f"Pushing tag {self.config.tag_name}")
            self.run_git(["push", self.config.upstream_remote, self.config.tag_name])
            
            Logger.info(f"Pushing release branch {self.config.release_branch}")
            self.run_git(["push", self.config.upstream_remote, self.config.release_branch])
            
            Logger.info(f"ℹ️  Maintenance branch {self.config.branch} stays local (not pushed)")
            return True
        except subprocess.CalledProcessError:
            return False


class MavenHelper:
    """Maven operations helper"""
    
    def __init__(self, repo_dir: Path, config: ReleaseConfig):
        self.repo_dir = repo_dir
        self.config = config
    
    def run_command(self, cmd: List[str], description: str, suppress_output: bool = False, 
                   log_file: Optional[Path] = None) -> bool:
        """Run a command with logging (adapted from pr_workflow.py)
        
        Args:
            cmd: Command to run  
            description: Description for logging
            suppress_output: Whether to suppress stdout/stderr from terminal
            log_file: Optional file to write output to
        """
        if self.config.dry_run:
            Logger.warn(f"DRY RUN: Would execute: {description}")
            Logger.info(f"DRY RUN: Command: {' '.join(cmd)}")
            return True
        
        Logger.info(f"Executing: {description}")
        try:
            if suppress_output:
                # Enhanced mvnd output suppression using proven solution
                if cmd[0] == 'mvnd':
                    # When logging to file, don't use -q so we get full output in the log
                    if log_file:
                        enhanced_cmd = cmd + ['-Dmvnd.rollingWindowSize=0']  # Still disable rolling window
                    else:
                        enhanced_cmd = cmd + ['-q', '-Dmvnd.rollingWindowSize=0']  # Full quiet mode
                    
                    # Set environment variables for complete suppression
                    env = os.environ.copy()
                    env.update({
                        'TERM': 'dumb',
                        'NO_COLOR': '1',
                        'CI': 'true',                           # Many tools detect CI and disable fancy output
                        'MAVEN_OPTS': '-Djansi.force=false',
                        'MVND_TERMINAL': 'false'                # Disable mvnd terminal features
                    })
                elif cmd[0] == './mvnw':
                    # When logging to file, don't use -q so we get full output in the log
                    if log_file:
                        enhanced_cmd = cmd  # No quiet flags for full logging
                    else:
                        enhanced_cmd = cmd + ['-q']  # Quiet mode when no logging
                    
                    env = os.environ.copy()
                    env.update({
                        'TERM': 'dumb',
                        'NO_COLOR': '1',
                        'CI': 'true',
                        'MAVEN_OPTS': '-Djansi.force=false'
                    })
                else:
                    enhanced_cmd = cmd
                    env = None
                
                # Create logs directory if it doesn't exist
                if log_file:
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(log_file, 'w') as f:
                        f.write(f"Command: {' '.join(enhanced_cmd)}\n")
                        f.write(f"Working directory: {self.repo_dir}\n")
                        f.write(f"Description: {description}\n")
                        f.write("-" * 50 + "\n")
                        f.flush()
                        
                        result = subprocess.run(
                            enhanced_cmd, 
                            cwd=self.repo_dir, 
                            check=True, 
                            stdout=f, 
                            stderr=subprocess.STDOUT,  # Redirect stderr to stdout so it goes to the log file
                            stdin=subprocess.DEVNULL,
                            start_new_session=True,
                            env=env,
                            text=True
                        )
                else:
                    # Suppress output completely (no log file)
                    result = subprocess.run(
                        enhanced_cmd, 
                        cwd=self.repo_dir, 
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
                subprocess.run(cmd, cwd=self.repo_dir, check=True)
                return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Command failed: {' '.join(cmd)}")
            if suppress_output and log_file and log_file.exists():
                Logger.error(f"Check log file for details: {log_file}")
                # Show last few lines of log for immediate debugging
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            Logger.error("Last 10 lines from log:")
                            for line in lines[-10:]:
                                Logger.error(f"  {line.rstrip()}")
                except Exception:
                    pass
            return False
    
    def run_maven(self, goals: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run Maven command (legacy method for compatibility)"""
        # Use mvnd if available, otherwise fall back to ./mvnw
        mvnd_available = shutil.which('mvnd') is not None
        cmd = ['mvnd'] if mvnd_available else ['./mvnw']
        cmd.extend(goals)
        
        Logger.info(f"Running Maven: {' '.join(cmd)}")
        
        if self.config.dry_run:
            Logger.warn("DRY RUN: Would execute Maven command")
            return subprocess.CompletedProcess(cmd, 0, '', '')
        
        try:
            result = subprocess.run(cmd, cwd=self.repo_dir, check=check, 
                                  capture_output=True, text=True)
            return result
        except subprocess.CalledProcessError as e:
            Logger.error(f"Maven command failed: {' '.join(cmd)}")
            Logger.error(f"Exit code: {e.returncode}")
            if e.stdout:
                Logger.error(f"Stdout: {e.stdout}")
            if e.stderr:
                Logger.error(f"Stderr: {e.stderr}")
            raise
    
    def set_version(self, version: str) -> bool:
        """Set version using Maven versions plugin"""
        try:
            Logger.info(f"Setting main project version to: {version}")
            self.run_maven([
                "versions:set",
                f"-DnewVersion={version}",
                "-DgenerateBackupPoms=false"
            ])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def set_bom_version(self, version: str) -> bool:
        """Set version in spring-ai-bom module specifically"""
        try:
            Logger.info(f"Setting BOM version to: {version}")
            self.run_maven([
                "versions:set",
                f"-DnewVersion={version}",
                "-DgenerateBackupPoms=false",
                "-pl", "spring-ai-bom"
            ])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def fast_build(self) -> bool:
        """Run fast build without tests and javadoc"""
        # Use mvnd if available, otherwise fall back to ./mvnw
        mvnd_available = shutil.which('mvnd') is not None
        cmd = ['mvnd'] if mvnd_available else ['./mvnw']
        cmd.extend([
            "clean", "package",
            "-Dmaven.javadoc.skip=true",
            "-DskipTests"
        ])
        
        # Create timestamped log file for build output
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        build_log_file = self.config.script_dir / "logs" / f"fast-build-{timestamp}.log"
        
        description = f"Fast build with {cmd[0]} (no tests, no javadoc)"
        success = self.run_command(cmd, description, suppress_output=True, log_file=build_log_file)
        
        if success:
            Logger.success(f"✅ Fast build with {cmd[0]} completed successfully")
            Logger.info(f"Build output logged to: {build_log_file}")
        else:
            Logger.error(f"❌ Fast build with {cmd[0]} failed!")
            Logger.error(f"Check build log for details: {build_log_file}")
        
        return success
    
    def verify_docs(self) -> bool:
        """Verify documentation build"""
        # Use ./mvnw specifically for docs (antora requires ./mvnw)
        cmd = ["./mvnw", "-pl", "spring-ai-docs", "antora"]
        
        # Create timestamped log file for documentation build output
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        docs_log_file = self.config.script_dir / "logs" / f"docs-build-{timestamp}.log"
        
        description = "Verify Antora documentation build"
        success = self.run_command(cmd, description, suppress_output=True, log_file=docs_log_file)
        
        if success:
            Logger.success("✅ Antora documentation build completed successfully")
            Logger.info(f"Documentation build output logged to: {docs_log_file}")
        else:
            Logger.error("❌ Antora documentation build failed!")
            Logger.error(f"Check documentation build log for details: {docs_log_file}")
        
        return success
    
    def verify_pom_version(self, pom_path: Path, expected_version: str) -> bool:
        """Verify a specific POM file has the expected version"""
        if self.config.dry_run:
            Logger.info(f"DRY RUN: Would verify {pom_path.name} has version {expected_version}")
            return True
        
        try:
            if not pom_path.exists():
                Logger.error(f"POM file not found: {pom_path}")
                return False
            
            with open(pom_path, 'r') as f:
                content = f.read()
                # Look for <version>X.Y.Z</version> near the top (before dependencies)
                lines = content.split('\n')
                for i, line in enumerate(lines[:50]):  # Check first 50 lines
                    if '<version>' in line and '</version>' in line:
                        # Extract version between tags
                        start = line.find('<version>') + 9
                        end = line.find('</version>')
                        if start > 8 and end > start:
                            version = line[start:end].strip()
                            if version == expected_version:
                                Logger.info(f"✓ {pom_path.name} has correct version: {version}")
                                return True
                            else:
                                Logger.error(f"✗ {pom_path.name} has incorrect version: {version} (expected: {expected_version})")
                                return False
                
                Logger.error(f"✗ Could not find version in {pom_path.name}")
                return False
                
        except Exception as e:
            Logger.error(f"Failed to verify {pom_path.name}: {e}")
            return False
    
    def check_for_snapshots(self) -> bool:
        """Check for any remaining SNAPSHOT versions in POM files"""
        if self.config.dry_run:
            Logger.info("DRY RUN: Would check for SNAPSHOT versions in all POM files")
            return True
        
        try:
            # Use grep to find SNAPSHOT in all pom.xml files
            cmd = ["grep", "-r", "--include=pom.xml", "-n", "SNAPSHOT", "."]
            result = subprocess.run(cmd, cwd=self.repo_dir, capture_output=True, text=True)
            
            if result.returncode == 0:  # Found SNAPSHOT references
                Logger.error("✗ Found SNAPSHOT references in POM files:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        Logger.error(f"  {line}")
                return False
            else:
                Logger.info("✓ No SNAPSHOT versions found in POM files")
                return True
                
        except Exception as e:
            Logger.error(f"Failed to check for SNAPSHOT versions: {e}")
            return False
    
    def verify_release_versions(self, release_version: str) -> bool:
        """Comprehensive version verification after setting release version"""
        Logger.info("Verifying all POM files have correct release version...")
        
        success = True
        
        # Check root POM
        root_pom = self.repo_dir / "pom.xml"
        if not self.verify_pom_version(root_pom, release_version):
            success = False
        
        # Check BOM POM
        bom_pom = self.repo_dir / "spring-ai-bom" / "pom.xml"
        if not self.verify_pom_version(bom_pom, release_version):
            success = False
        
        # Check for any remaining SNAPSHOT versions
        if not self.check_for_snapshots():
            success = False
        
        if success:
            Logger.success("✓ All version verifications passed")
        else:
            Logger.error("✗ Version verification failed")
        
        return success


class GitHubActionsHelper:
    """GitHub Actions workflow trigger helper"""
    
    def __init__(self, config: ReleaseConfig):
        self.config = config
        self.repo = config.spring_ai_repo
    
    def is_gh_available(self) -> bool:
        """Check if GitHub CLI is available and authenticated"""
        try:
            result = subprocess.run(['gh', 'auth', 'status'], 
                                  capture_output=True, text=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def run_gh_workflow(self, workflow_file: str, inputs: Dict[str, str] = None, use_release_branch: bool = False) -> bool:
        """Run GitHub workflow with optional inputs on specified branch"""
        try:
            # Use release branch for release workflows, maintenance branch for others
            branch = self.config.release_branch if use_release_branch else self.config.branch
            cmd = ['gh', 'workflow', 'run', workflow_file, '--repo', self.repo, '--ref', branch]
            
            # Add input parameters if provided
            if inputs:
                for key, value in inputs.items():
                    cmd.extend(['-f', f'{key}={value}'])
            
            Logger.info(f"Running GitHub workflow: {' '.join(cmd)}")
            
            if self.config.dry_run:
                Logger.warn("DRY RUN: Would trigger GitHub workflow")
                return True
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            Logger.success(f"GitHub workflow '{workflow_file}' triggered successfully on branch {branch}")
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to trigger GitHub workflow '{workflow_file}'")
            Logger.error(f"Exit code: {e.returncode}")
            if e.stdout:
                Logger.error(f"Stdout: {e.stdout}")
            if e.stderr:
                Logger.error(f"Stderr: {e.stderr}")
            return False
    
    def trigger_deploy_docs(self) -> bool:
        """Trigger documentation deployment workflow"""
        Logger.info(f"Triggering documentation deployment on release branch {self.config.release_branch}")
        return self.run_gh_workflow('deploy-docs.yml', use_release_branch=True)
    
    def trigger_documentation_upload(self) -> bool:
        """Trigger javadoc upload with version parameter"""
        Logger.info(f"Triggering javadoc upload for version {self.config.target_version} on release branch {self.config.release_branch}")
        inputs = {'releaseVersion': self.config.target_version}
        return self.run_gh_workflow('documentation-upload.yml', inputs, use_release_branch=True)
    
    def trigger_maven_central_release(self) -> bool:
        """Trigger Maven Central artifact upload"""
        Logger.info(f"Triggering Maven Central release on release branch {self.config.release_branch}")
        return self.run_gh_workflow('new-maven-central-release.yml', use_release_branch=True)


class ReleaseWorkflow:
    """Main workflow orchestrator"""
    
    def __init__(self, config: ReleaseConfig):
        self.config = config
        self.git_helper = None
        self.maven_helper = None
        self.github_helper = None
        self._ensure_state_dir()
    
    def _ensure_state_dir(self):
        """Ensure state directory exists"""
        self.config.state_dir.mkdir(exist_ok=True)
    
    def cleanup_workspace_and_state(self) -> bool:
        """Clean up workspace directory and state files for fresh start"""
        Logger.info("🧹 Cleaning up workspace and state files...")
        
        cleanup_items = [
            (self.config.spring_ai_dir, "workspace directory"),
            (self.config.release_state_file, "release state file"),
        ]
        
        success = True
        cleaned_count = 0
        
        for item_path, description in cleanup_items:
            try:
                if item_path.exists():
                    if self.config.dry_run:
                        Logger.info(f"DRY RUN: Would remove {description}: {item_path}")
                        cleaned_count += 1
                    else:
                        if item_path.is_dir():
                            import shutil
                            shutil.rmtree(item_path)
                            Logger.success(f"✅ Removed {description}: {item_path}")
                        else:
                            item_path.unlink()
                            Logger.success(f"✅ Removed {description}: {item_path}")
                        cleaned_count += 1
                else:
                    Logger.info(f"ℹ️  {description} not found: {item_path}")
            except Exception as e:
                Logger.error(f"❌ Failed to remove {description} {item_path}: {e}")
                success = False
        
        if success:
            if cleaned_count > 0:
                action = "Would clean" if self.config.dry_run else "Cleaned"
                Logger.success(f"🎉 {action} {cleaned_count} items successfully!")
            else:
                Logger.info("ℹ️  No cleanup needed - workspace already clean")
        else:
            Logger.error("❌ Some cleanup operations failed")
        
        return success
    
    def save_release_state(self, phase: str, completed_steps: List[str]):
        """Save current release state to file"""
        state = {
            "version": self.config.target_version,
            "branch": self.config.branch,
            "phase": phase,
            "completed_steps": completed_steps,
            "timestamp": datetime.now().isoformat(),
            "next_dev_version": self.config.next_dev_version
        }
        
        if not self.config.dry_run:
            with open(self.config.release_state_file, 'w') as f:
                json.dump(state, f, indent=2)
            Logger.info(f"Release state saved to {self.config.release_state_file}")
        else:
            Logger.info("DRY RUN: Would save release state")
    
    def load_release_state(self) -> Optional[Dict[str, Any]]:
        """Load release state from file"""
        if not self.config.release_state_file.exists():
            return None
        
        try:
            with open(self.config.release_state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            Logger.error(f"Failed to load release state: {e}")
            return None
    
    def get_step_commands(self, step_name: str) -> List[str]:
        """Get detailed command summary for a step"""
        commands = []
        
        if step_name == "Setup workspace":
            commands = [
                f"git clone https://github.com/{self.config.spring_ai_repo}.git {self.config.spring_ai_dir}",
                f"cd {self.config.spring_ai_dir}",
                f"git checkout {self.config.branch}",
                f"git pull origin {self.config.branch}",
                "Initialize Maven and GitHub helpers"
            ]
        elif step_name == "Set release version":
            commands = [
                f"mvnd versions:set -DnewVersion={self.config.target_version} -DgenerateBackupPoms=false",
                f"mvnd versions:set -DnewVersion={self.config.target_version} -DgenerateBackupPoms=false -pl spring-ai-bom",
                f"Verify pom.xml has version {self.config.target_version}",
                f"Verify spring-ai-bom/pom.xml has version {self.config.target_version}",
                "Check all POM files for SNAPSHOT versions (should find none)"
            ]
        elif step_name == "Build and verify":
            commands = [
                "mvnd clean package -Dmaven.javadoc.skip=true -DskipTests",
                "./mvnw -pl spring-ai-docs antora"
            ]
        elif step_name == "Commit release version":
            commands = [
                "git add -A",
                f"git commit -m 'Release version {self.config.target_version}'"
            ]
        elif step_name == "Create release tag":
            commands = [
                f"git tag -a {self.config.tag_name} -m 'Release version {self.config.target_version}'"
            ]
        elif step_name == "Set next development version":
            commands = [
                f"mvnd versions:set -DnewVersion={self.config.next_dev_version} -DgenerateBackupPoms=false",
                f"mvnd versions:set -DnewVersion={self.config.next_dev_version} -DgenerateBackupPoms=false -pl spring-ai-bom"
            ]
        elif step_name == "Commit development version":
            commands = [
                "git add -A",
                f"git commit -m 'Next development version {self.config.next_dev_version}'"
            ]
        elif step_name == "Push release tag":
            commands = [
                f"git push origin {self.config.tag_name}",
                "# Release commit stays local until Maven Central deployment succeeds"
            ]
        elif step_name == "Push release commit":
            commands = [
                f"git push origin {self.config.branch}",
                "# Pushes the release commit after Maven Central deployment succeeds"
            ]
        elif step_name == "Push development version":
            commands = [
                f"git push origin {self.config.branch}"
            ]
        elif step_name == "Trigger documentation deployment":
            commands = [
                f"gh workflow run deploy-docs.yml --repo {self.config.spring_ai_repo} --ref {self.config.release_branch}"
            ]
        elif step_name == "Trigger javadoc upload":
            commands = [
                f"gh workflow run documentation-upload.yml --repo {self.config.spring_ai_repo} --ref {self.config.release_branch} -f releaseVersion={self.config.target_version}"
            ]
        elif step_name == "Trigger Maven Central release":
            commands = [
                f"gh workflow run new-maven-central-release.yml --repo {self.config.spring_ai_repo} --ref {self.config.release_branch}"
            ]
        
        return commands
    
    def confirm_step(self, message: str) -> bool:
        """Ask user for confirmation before proceeding with a step"""
        Logger.step(message)
        
        # Show detailed command summary
        step_name = message.replace("Execute: ", "")
        commands = self.get_step_commands(step_name)
        
        if commands:
            mode_prefix = "DRY RUN - " if self.config.dry_run else ""
            Logger.info(f"{mode_prefix}Commands that will be executed:")
            for i, cmd in enumerate(commands, 1):
                print(f"  {Colors.CYAN}{i}.{Colors.NC} {cmd}")
            print()  # Add blank line for readability
        
        if self.config.dry_run:
            Logger.warn(f"DRY RUN: {message}")
            return True
            
        response = input(f"{Colors.YELLOW}Proceed? (Y/n): {Colors.NC}").strip().lower()
        return response in ['', 'y', 'yes']
    
    def display_summary(self):
        """Display release summary"""
        Logger.bold("\n" + "="*60)
        Logger.bold("SPRING AI POINT RELEASE SUMMARY")
        Logger.bold("="*60)
        Logger.info(f"Target Version: {self.config.target_version}")
        Logger.info(f"Next Dev Version: {self.config.next_dev_version}")
        Logger.info(f"Branch: {self.config.branch}")
        Logger.info(f"Tag: {self.config.tag_name}")
        Logger.info(f"Workspace: {self.config.spring_ai_dir}")
        Logger.info(f"Dry Run: {self.config.dry_run}")
        Logger.bold("="*60 + "\n")
    
    def setup_workspace(self) -> bool:
        """Set up the workspace with fresh checkout"""
        Logger.step("Setting up workspace")
        
        self.git_helper = ReleaseGitHelper(self.config.spring_ai_dir, self.config)
        
        if not self.git_helper.clone_repository():
            return False
        
        if not self.git_helper.checkout_branch():
            return False
        
        self.maven_helper = MavenHelper(self.config.spring_ai_dir, self.config)
        self.github_helper = GitHubActionsHelper(self.config)
        
        # Check GitHub CLI availability
        if not self.github_helper.is_gh_available():
            Logger.warn("GitHub CLI not available or not authenticated - GitHub Actions will be skipped")
        
        # Display current version
        current_version = self.git_helper.get_current_version()
        if current_version:
            Logger.info(f"Current version: {current_version}")
        
        return True
    
    def execute_release(self) -> bool:
        """Execute the main release workflow (stops at Maven Central trigger)"""
        Logger.bold("\nStarting main release workflow...\n")
        
        # Map skip-to names to step names
        skip_to_mapping = {
            'setup': 'Setup workspace',
            'set-version': 'Set release version', 
            'build': 'Build and verify',
            'commit-release': 'Commit release version',
            'tag': 'Create release tag',
            'branch': 'Create release branch',
            'push': 'Push changes',
            'docs': 'Trigger documentation deployment',
            'javadoc': 'Trigger javadoc upload',
            'maven-central': 'Trigger Maven Central release'
        }
        
        steps = [
            ("Setup workspace", self.setup_workspace),
            ("Set release version", self._set_release_version),
            ("Build and verify", self._build_and_verify),
            ("Commit release version", self._commit_release_version),
            ("Create release tag", self._create_release_tag),
            ("Create release branch", self._create_release_branch),
            ("Push changes", self._push_changes),
            ("Trigger documentation deployment", self._trigger_deploy_docs),
            ("Trigger javadoc upload", self._trigger_documentation_upload),
            ("Trigger Maven Central release", self._trigger_maven_central_release),
        ]
        
        # Find starting step index based on skip-to parameter
        start_index = 0
        if self.config.skip_to:
            target_step = skip_to_mapping.get(self.config.skip_to)
            if target_step:
                for i, (step_name, _) in enumerate(steps):
                    if step_name == target_step:
                        start_index = i
                        break
                Logger.info(f"🚀 Skipping to step: {target_step}")
                Logger.info(f"📝 Note: Make sure previous steps were completed successfully!")
                
                # If we're skipping setup, we still need to initialize helpers
                if start_index > 0:
                    Logger.info("🔧 Initializing helpers for skipped workflow...")
                    # Minimal setup for skipped workflows - just initialize the helpers
                    self.git_helper = ReleaseGitHelper(self.config.spring_ai_dir, self.config)
                    self.maven_helper = MavenHelper(self.config.spring_ai_dir, self.config)
                    self.github_helper = GitHubActionsHelper(self.config)
        
        completed_steps = []
        
        for i, (step_name, step_func) in enumerate(steps):
            # Skip steps before the target step
            if i < start_index:
                Logger.info(f"⏭️  Skipping: {step_name}")
                completed_steps.append(step_name)  # Mark as completed for state tracking
                continue
                
            if not self.confirm_step(f"Execute: {step_name}"):
                Logger.warn("Step cancelled by user")
                return False
            
            try:
                if not step_func():
                    Logger.error(f"Step failed: {step_name}")
                    return False
                Logger.success(f"Step completed: {step_name}")
                completed_steps.append(step_name)
            except Exception as e:
                Logger.error(f"Step failed with exception: {step_name} - {e}")
                return False
        
        # Save state after Maven Central trigger
        self.save_release_state("maven_central_triggered", completed_steps)
        
        Logger.bold(f"\n🎯 Main release workflow completed!")
        Logger.bold(f"Maven Central release has been triggered.")
        Logger.bold(f"\nAfter Maven Central deployment succeeds, run:")
        Logger.bold(f"python3 spring-ai-point-release.py {self.config.target_version} --post-maven-central")
        
        return True
    
    def execute_post_maven_central(self) -> bool:
        """Execute post-Maven Central steps (development version setup)"""
        Logger.bold("\nStarting post-Maven Central workflow...\n")
        
        # Load and validate state
        state = self.load_release_state()
        if not state:
            Logger.error("No release state found. Run the main release workflow first.")
            return False
        
        if state["phase"] != "maven_central_triggered":
            Logger.error(f"Invalid release phase: {state['phase']}. Expected 'maven_central_triggered'")
            return False
        
        Logger.info(f"Resuming release {state['version']} from Maven Central trigger phase")
        
        # Setup workspace (repository should already exist from main workflow)
        if not self.setup_workspace():
            return False
        
        steps = [
            ("Push release commit", self._push_release_commit),
            ("Set next development version", self._set_next_dev_version),
            ("Commit development version", self._commit_dev_version),
            ("Push development version", self._push_dev_changes),
        ]
        
        completed_steps = state["completed_steps"].copy()
        
        for step_name, step_func in steps:
            if not self.confirm_step(f"Execute: {step_name}"):
                Logger.warn("Step cancelled by user")
                return False
            
            try:
                if not step_func():
                    Logger.error(f"Step failed: {step_name}")
                    return False
                Logger.success(f"Step completed: {step_name}")
                completed_steps.append(step_name)
            except Exception as e:
                Logger.error(f"Step failed with exception: {step_name} - {e}")
                return False
        
        # Save final state
        self.save_release_state("completed", completed_steps)
        
        Logger.bold(f"\n🎉 Complete release workflow finished!")
        Logger.bold(f"Released version: {self.config.target_version}")
        Logger.bold(f"Development version: {self.config.next_dev_version}")
        
        return True
    
    def _set_release_version(self) -> bool:
        """Set the release version and verify it was applied correctly"""
        if not self.maven_helper.set_version(self.config.target_version):
            return False
        if not self.maven_helper.set_bom_version(self.config.target_version):
            return False
        # Verify versions were set correctly
        return self.maven_helper.verify_release_versions(self.config.target_version)
    
    def _build_and_verify(self) -> bool:
        """Build and verify the release"""
        if not self.maven_helper.fast_build():
            return False
        return self.maven_helper.verify_docs()
    
    def _commit_release_version(self) -> bool:
        """Commit the release version"""
        message = f"Release version {self.config.target_version}"
        return self.git_helper.commit_changes(message)
    
    def _create_release_tag(self) -> bool:
        """Create the release tag"""
        message = f"Release version {self.config.target_version}"
        return self.git_helper.create_tag(self.config.tag_name, message)
    
    def _create_release_branch(self) -> bool:
        """Create the release branch from the tag"""
        return self.git_helper.create_release_branch(self.config.release_branch, self.config.tag_name)
    
    def _set_next_dev_version(self) -> bool:
        """Set the next development version"""
        if not self.maven_helper.set_version(self.config.next_dev_version):
            return False
        return self.maven_helper.set_bom_version(self.config.next_dev_version)
    
    def _commit_dev_version(self) -> bool:
        """Commit the development version"""
        message = f"Next development version {self.config.next_dev_version}"
        return self.git_helper.commit_changes(message)
    
    def _push_changes(self) -> bool:
        """Push tag and release branch (not maintenance branch)"""
        return self.git_helper.push_tag_and_release_branch()
    
    def _push_release_commit(self) -> bool:
        """Push the release commit to the branch (after Maven Central success)"""
        return self.git_helper.push_branch_only()
    
    def _push_dev_changes(self) -> bool:
        """Push development version changes (no tags)"""
        try:
            Logger.info(f"Pushing development version changes to {self.config.upstream_remote} {self.config.branch}")
            self.git_helper.run_git(["push", self.config.upstream_remote, self.config.branch])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _trigger_deploy_docs(self) -> bool:
        """Trigger documentation deployment on target branch"""
        if not self.github_helper.is_gh_available():
            Logger.warn("GitHub CLI not available - skipping documentation deployment")
            return True
        return self.github_helper.trigger_deploy_docs()
    
    def _trigger_documentation_upload(self) -> bool:
        """Trigger javadoc upload with version parameter on target branch"""
        if not self.github_helper.is_gh_available():
            Logger.warn("GitHub CLI not available - skipping javadoc upload")
            return True
        return self.github_helper.trigger_documentation_upload()
    
    def _trigger_maven_central_release(self) -> bool:
        """Trigger Maven Central artifact upload on target branch"""
        if not self.github_helper.is_gh_available():
            Logger.warn("GitHub CLI not available - skipping Maven Central release")
            return True
        return self.github_helper.trigger_maven_central_release()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Spring AI Point Release Script for 1.0.x branch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Main release workflow (stops at Maven Central trigger)
  python3 spring-ai-point-release.py 1.0.1 --dry-run
  python3 spring-ai-point-release.py 1.0.1 --branch 1.0.x
  
  # Skip to specific step (useful for resuming interrupted releases)
  python3 spring-ai-point-release.py 1.0.1 --skip-to build
  python3 spring-ai-point-release.py 1.0.1 --skip-to commit-release
  
  # Clean up workspace and state for fresh start
  python3 spring-ai-point-release.py 1.0.1 --cleanup
  python3 spring-ai-point-release.py 1.0.1 --cleanup --dry-run
  
  # Post-Maven Central workflow (after deployment succeeds)
  python3 spring-ai-point-release.py 1.0.1 --post-maven-central

Skip-to options: setup, set-version, build, commit-release, tag, push, docs, javadoc, maven-central
        """
    )
    
    parser.add_argument('version', help='Target release version (e.g., 1.0.1)')
    parser.add_argument('--branch', default='1.0.x', help='Branch to release from (default: 1.0.x)')
    parser.add_argument('--dry-run', action='store_true', help='Preview commands without executing')
    parser.add_argument('--workspace', type=Path, help='Override workspace directory')
    parser.add_argument('--post-maven-central', action='store_true', 
                       help='Complete development version setup after Maven Central success')
    parser.add_argument('--skip-to', choices=[
        'setup', 'set-version', 'build', 'commit-release', 'tag', 'branch', 'push', 
        'docs', 'javadoc', 'maven-central'
    ], help='Skip to specific workflow step (useful for resuming interrupted releases)')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up state files and workspace directory before starting (fresh start)')
    
    args = parser.parse_args()
    
    # Setup configuration
    script_dir = Path(__file__).parent.absolute()
    if args.workspace:
        script_dir = args.workspace
    
    config = ReleaseConfig(
        script_dir=script_dir,
        target_version=args.version,
        branch=args.branch,
        dry_run=args.dry_run,
        post_maven_central=args.post_maven_central,
        skip_to=args.skip_to,
        cleanup=args.cleanup
    )
    
    # Validate version format
    if not config.validate_version():
        Logger.error(f"Invalid version format: {args.version}")
        Logger.error("Expected format: X.Y.Z (e.g., 1.0.1)")
        sys.exit(1)
    
    # Create workflow and execute
    workflow = ReleaseWorkflow(config)
    
    # Handle cleanup if requested
    if config.cleanup:
        Logger.bold("\n🧹 CLEANUP MODE")
        Logger.bold("=" * 30)
        
        if not workflow.confirm_step("Clean up workspace and state files"):
            Logger.info("Cleanup cancelled by user")
            sys.exit(0)
        
        try:
            success = workflow.cleanup_workspace_and_state()
            if not success:
                Logger.error("\nCleanup failed!")
                sys.exit(1)
            else:
                Logger.success("\n✅ Cleanup completed successfully!")
                Logger.info("You can now run the release from a clean state.")
                sys.exit(0)
        except Exception as e:
            Logger.error(f"\nUnexpected error during cleanup: {e}")
            sys.exit(1)
    
    if config.post_maven_central:
        # Post-Maven Central workflow
        Logger.bold("\nPost-Maven Central Development Version Setup")
        Logger.bold("="*50)
        
        if not workflow.confirm_step("Start post-Maven Central workflow"):
            Logger.info("Post-Maven Central workflow cancelled by user")
            sys.exit(0)
        
        try:
            success = workflow.execute_post_maven_central()
            if success:
                Logger.success("\nPost-Maven Central workflow completed successfully!")
            else:
                Logger.error("\nPost-Maven Central workflow failed!")
                sys.exit(1)
        except KeyboardInterrupt:
            Logger.warn("\nPost-Maven Central workflow interrupted by user")
            sys.exit(1)
        except Exception as e:
            Logger.error(f"\nUnexpected error: {e}")
            sys.exit(1)
    else:
        # Main release workflow
        workflow.display_summary()
        
        if not workflow.confirm_step("Start main release workflow"):
            Logger.info("Release cancelled by user")
            sys.exit(0)
        
        try:
            success = workflow.execute_release()
            if not success:
                Logger.error("\nMain release workflow failed!")
                sys.exit(1)
        except KeyboardInterrupt:
            Logger.warn("\nRelease workflow interrupted by user")
            sys.exit(1)
        except Exception as e:
            Logger.error(f"\nUnexpected error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
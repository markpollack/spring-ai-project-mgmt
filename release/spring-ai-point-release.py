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
    
    @property
    def spring_ai_dir(self) -> Path:
        return self.script_dir / "spring-ai-release"
    
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
    
    def push_changes(self) -> bool:
        """Push changes and tags to remote"""
        try:
            Logger.info(f"Pushing changes to {self.config.upstream_remote} {self.config.branch}")
            self.run_git(["push", self.config.upstream_remote, self.config.branch])
            
            Logger.info(f"Pushing tag {self.config.tag_name}")
            self.run_git(["push", self.config.upstream_remote, self.config.tag_name])
            
            return True
        except subprocess.CalledProcessError:
            return False


class MavenHelper:
    """Maven operations helper"""
    
    def __init__(self, repo_dir: Path, config: ReleaseConfig):
        self.repo_dir = repo_dir
        self.config = config
    
    def run_maven(self, goals: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run Maven command"""
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
        try:
            Logger.info("Running fast build (no tests, no javadoc)")
            self.run_maven([
                "clean", "package",
                "-Dmaven.javadoc.skip=true",
                "-DskipTests"
            ])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def verify_docs(self) -> bool:
        """Verify documentation build"""
        try:
            Logger.info("Verifying documentation build")
            # Use ./mvnw specifically for docs
            cmd = ["./mvnw", "-pl", "spring-ai-docs", "antora"]
            
            if self.config.dry_run:
                Logger.warn("DRY RUN: Would verify docs build")
                return True
            
            result = subprocess.run(cmd, cwd=self.repo_dir, check=True,
                                  capture_output=True, text=True)
            Logger.success("Documentation build verified")
            return True
        except subprocess.CalledProcessError as e:
            Logger.error("Documentation build failed")
            return False


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
    
    def run_gh_workflow(self, workflow_file: str, inputs: Dict[str, str] = None) -> bool:
        """Run GitHub workflow with optional inputs on specified branch"""
        try:
            cmd = ['gh', 'workflow', 'run', workflow_file, '--repo', self.repo, '--ref', self.config.branch]
            
            # Add input parameters if provided
            if inputs:
                for key, value in inputs.items():
                    cmd.extend(['-f', f'{key}={value}'])
            
            Logger.info(f"Running GitHub workflow: {' '.join(cmd)}")
            
            if self.config.dry_run:
                Logger.warn("DRY RUN: Would trigger GitHub workflow")
                return True
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            Logger.success(f"GitHub workflow '{workflow_file}' triggered successfully on branch {self.config.branch}")
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
        Logger.info(f"Triggering documentation deployment on branch {self.config.branch}")
        return self.run_gh_workflow('deploy-docs.yml')
    
    def trigger_documentation_upload(self) -> bool:
        """Trigger javadoc upload with version parameter"""
        Logger.info(f"Triggering javadoc upload for version {self.config.target_version} on branch {self.config.branch}")
        inputs = {'releaseVersion': self.config.target_version}
        return self.run_gh_workflow('documentation-upload.yml', inputs)
    
    def trigger_maven_central_release(self) -> bool:
        """Trigger Maven Central artifact upload"""
        Logger.info(f"Triggering Maven Central release on branch {self.config.branch}")
        return self.run_gh_workflow('new-maven-central-release.yml')


class ReleaseWorkflow:
    """Main workflow orchestrator"""
    
    def __init__(self, config: ReleaseConfig):
        self.config = config
        self.git_helper = None
        self.maven_helper = None
        self.github_helper = None
    
    def confirm_step(self, message: str) -> bool:
        """Ask user for confirmation before proceeding with a step"""
        if self.config.dry_run:
            Logger.warn(f"DRY RUN: {message}")
            return True
        
        Logger.step(message)
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
        """Execute the release workflow"""
        Logger.bold("\nStarting release workflow...\n")
        
        steps = [
            ("Setup workspace", self.setup_workspace),
            ("Set release version", self._set_release_version),
            ("Build and verify", self._build_and_verify),
            ("Commit release version", self._commit_release_version),
            ("Create release tag", self._create_release_tag),
            ("Set next development version", self._set_next_dev_version),
            ("Commit development version", self._commit_dev_version),
            ("Push changes", self._push_changes),
            ("Trigger documentation deployment", self._trigger_deploy_docs),
            ("Trigger javadoc upload", self._trigger_documentation_upload),
            ("Trigger Maven Central release", self._trigger_maven_central_release),
        ]
        
        for step_name, step_func in steps:
            if not self.confirm_step(f"Execute: {step_name}"):
                Logger.warn("Step cancelled by user")
                return False
            
            try:
                if not step_func():
                    Logger.error(f"Step failed: {step_name}")
                    return False
                Logger.success(f"Step completed: {step_name}")
            except Exception as e:
                Logger.error(f"Step failed with exception: {step_name} - {e}")
                return False
        
        return True
    
    def _set_release_version(self) -> bool:
        """Set the release version"""
        if not self.maven_helper.set_version(self.config.target_version):
            return False
        return self.maven_helper.set_bom_version(self.config.target_version)
    
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
        """Push changes and tags"""
        return self.git_helper.push_changes()
    
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
  python3 spring-ai-point-release.py 1.0.1 --dry-run
  python3 spring-ai-point-release.py 1.0.2 --branch 1.0.x
        """
    )
    
    parser.add_argument('version', help='Target release version (e.g., 1.0.1)')
    parser.add_argument('--branch', default='1.0.x', help='Branch to release from (default: 1.0.x)')
    parser.add_argument('--dry-run', action='store_true', help='Preview commands without executing')
    parser.add_argument('--workspace', type=Path, help='Override workspace directory')
    
    args = parser.parse_args()
    
    # Setup configuration
    script_dir = Path(__file__).parent.absolute()
    if args.workspace:
        script_dir = args.workspace
    
    config = ReleaseConfig(
        script_dir=script_dir,
        target_version=args.version,
        branch=args.branch,
        dry_run=args.dry_run
    )
    
    # Validate version format
    if not config.validate_version():
        Logger.error(f"Invalid version format: {args.version}")
        Logger.error("Expected format: X.Y.Z (e.g., 1.0.1)")
        sys.exit(1)
    
    # Create workflow and execute
    workflow = ReleaseWorkflow(config)
    workflow.display_summary()
    
    if not workflow.confirm_step("Start release workflow"):
        Logger.info("Release cancelled by user")
        sys.exit(0)
    
    try:
        success = workflow.execute_release()
        if success:
            Logger.success("\nRelease workflow completed successfully!")
            Logger.bold(f"Released version: {config.target_version}")
            Logger.bold(f"Tag created: {config.tag_name}")
        else:
            Logger.error("\nRelease workflow failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        Logger.warn("\nRelease workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        Logger.error(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
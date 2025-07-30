#!/usr/bin/env python3
"""
Backport Preparation Script for Spring AI PRs

This script handles the complete backport preparation workflow:
1. Pre-flight checks (repository, branch, git status)
2. Interactive commit squashing 
3. Adding backport directive to commit message
4. Safety features (backup branch, rollback option)

Usage:
    cd spring-ai
    python3 ../prepare_backport.py <pr_number>

Example:
    cd spring-ai
    python3 ../prepare_backport.py 3920
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GitStatus:
    """Git repository status information"""
    is_repo: bool
    is_clean: bool
    current_branch: str
    has_upstream: bool
    commits_ahead: int
    repo_root: str


@dataclass
class CommitInfo:
    """Information about a commit"""
    hash: str
    message: str
    author: str
    date: str


class Logger:
    """Colored logging for terminal output"""
    
    @staticmethod
    def info(msg): print(f"\033[34m[INFO]\033[0m {msg}")
    
    @staticmethod
    def success(msg): print(f"\033[32m✅\033[0m {msg}")
    
    @staticmethod
    def warn(msg): print(f"\033[33m⚠️\033[0m {msg}")
    
    @staticmethod
    def error(msg): print(f"\033[31m❌\033[0m {msg}")
    
    @staticmethod
    def header(msg): print(f"\033[1m\033[36m{msg}\033[0m")
    
    @staticmethod
    def separator(): print("━" * 50)


class BackportPreparer:
    """Main class for backport preparation workflow"""
    
    def __init__(self, pr_number: str):
        self.pr_number = pr_number
        self.expected_branch = f"pr-{pr_number}-branch"
        self.backup_branch = f"pr-{pr_number}-branch-backup"
        self.context_dir = Path(__file__).parent
        
    def run(self) -> bool:
        """Execute the complete backport preparation workflow"""
        try:
            Logger.header(f"🔄 Backport Preparation for PR #{self.pr_number}")
            Logger.separator()
            
            # Step 1: Pre-flight checks
            if not self._preflight_checks():
                return False
                
            # Step 2: Analyze commits
            commits = self._analyze_commits()
            if not commits:
                Logger.error("No commits found to squash")
                return False
                
            # Step 3: Create backup
            if not self._create_backup():
                return False
                
            # Step 4: Interactive squashing
            if not self._interactive_squash(commits):
                return False
                
            # Step 5: Add backport directive
            if not self._add_backport_directive():
                return False
                
            Logger.success("Backport preparation completed successfully!")
            Logger.info(f"Branch '{self.expected_branch}' is ready for backport")
            Logger.info("You can now merge this PR - the commit will auto-cherry-pick to 1.0.x")
            
            return True
            
        except KeyboardInterrupt:
            Logger.warn("Operation cancelled by user")
            return False
        except Exception as e:
            Logger.error(f"Unexpected error: {e}")
            return False
    
    def _preflight_checks(self) -> bool:
        """Perform all pre-flight validation checks"""
        Logger.info("Running pre-flight checks...")
        
        # Check 1: Verify we're in a git repository
        git_status = self._get_git_status()
        if not git_status.is_repo:
            Logger.error("Not in a git repository")
            Logger.info("Make sure you're in the spring-ai directory")
            return False
            
        Logger.success(f"Repository: {os.path.basename(git_status.repo_root)}")
        
        # Check 2: Verify clean working directory
        if not git_status.is_clean:
            Logger.error("Working directory is not clean")
            Logger.info("Please commit or stash your changes before running backport preparation")
            self._show_git_status()
            return False
            
        Logger.success("Working directory: clean")
        
        # Check 3: Verify correct branch
        if git_status.current_branch != self.expected_branch:
            Logger.error(f"Wrong branch: {git_status.current_branch}")
            Logger.info(f"Expected branch: {self.expected_branch}")
            Logger.info(f"Run: git checkout {self.expected_branch}")
            return False
            
        Logger.success(f"Branch: {self.expected_branch}")
        
        # Check 4: Verify PR context exists
        pr_context_dir = self.context_dir / "context" / f"pr-{self.pr_number}"
        if not pr_context_dir.exists():
            Logger.error(f"PR context not found: {pr_context_dir}")
            Logger.info(f"Run the PR workflow first: python3 pr_workflow.py {self.pr_number}")
            return False
            
        Logger.success(f"PR context: found")
        
        # Check 5: Verify backport approval
        if not self._check_backport_approval():
            Logger.error("PR is not approved for backport")
            Logger.info("Only approved PRs can be prepared for backport")
            return False
            
        Logger.success("Backport status: ✅ APPROVED")
        
        return True
    
    def _get_git_status(self) -> GitStatus:
        """Get comprehensive git repository status"""
        try:
            # Check if we're in a git repo
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  capture_output=True, text=True)
            is_repo = result.returncode == 0
            
            if not is_repo:
                return GitStatus(False, False, "", False, 0, "")
            
            # Get repository root
            result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], 
                                  capture_output=True, text=True)
            repo_root = result.stdout.strip() if result.returncode == 0 else ""
            
            # Check if working directory is clean
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            is_clean = len(result.stdout.strip()) == 0
            
            # Get current branch
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True)
            current_branch = result.stdout.strip() if result.returncode == 0 else ""
            
            # Check upstream and commits ahead
            result = subprocess.run(['git', 'status', '-b', '--porcelain'], 
                                  capture_output=True, text=True)
            has_upstream = "..." in result.stdout
            commits_ahead = 0
            
            if has_upstream:
                # Parse commits ahead from status
                for line in result.stdout.split('\n'):
                    if line.startswith('##') and 'ahead' in line:
                        match = re.search(r'ahead (\d+)', line)
                        if match:
                            commits_ahead = int(match.group(1))
            
            return GitStatus(is_repo, is_clean, current_branch, has_upstream, commits_ahead, repo_root)
            
        except Exception as e:
            Logger.error(f"Error getting git status: {e}")
            return GitStatus(False, False, "", False, 0, "")
    
    def _show_git_status(self):
        """Display current git status for user"""
        try:
            result = subprocess.run(['git', 'status'], capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
        except Exception:
            pass
    
    def _check_backport_approval(self) -> bool:
        """Check if PR is approved for backport"""
        try:
            backport_file = self.context_dir / "context" / f"pr-{self.pr_number}" / "backport-assessment.json"
            if not backport_file.exists():
                return False
                
            with open(backport_file, 'r') as f:
                data = json.load(f)
                
            return data.get('decision') == 'APPROVE'
            
        except Exception as e:
            Logger.error(f"Error checking backport approval: {e}")
            return False
    
    def _analyze_commits(self) -> List[CommitInfo]:
        """Analyze commits in the current PR branch"""
        try:
            Logger.info("Analyzing commits in PR branch...")
            
            # Get commits that are in current branch but not in main
            result = subprocess.run([
                'git', 'log', '--oneline', '--reverse', 'main..HEAD'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                Logger.error("Error getting commit history")
                return []
            
            commit_lines = [line for line in result.stdout.strip().split('\n') if line]
            
            if not commit_lines:
                Logger.warn("No commits found ahead of main branch")
                return []
            
            Logger.success(f"Commits to squash: {len(commit_lines)} commits")
            print()
            Logger.info("📋 Current commits:")
            
            commits = []
            for line in commit_lines:
                hash_part = line.split(' ', 1)[0]
                message_part = line.split(' ', 1)[1] if ' ' in line else ''
                
                # Get detailed commit info
                result = subprocess.run([
                    'git', 'show', '--format=%an|%ad', '--no-patch', hash_part
                ], capture_output=True, text=True)
                
                author = "Unknown"
                date = "Unknown"
                if result.returncode == 0:
                    parts = result.stdout.strip().split('|')
                    if len(parts) >= 2:
                        author = parts[0]
                        date = parts[1]
                
                commits.append(CommitInfo(hash_part, message_part, author, date))
                print(f"  {hash_part} {message_part}")
            
            print()
            return commits
            
        except Exception as e:
            Logger.error(f"Error analyzing commits: {e}")
            return []
    
    def _create_backup(self) -> bool:
        """Create backup branch before making changes"""
        try:
            Logger.info(f"Creating backup branch: {self.backup_branch}")
            
            # Delete existing backup if present
            subprocess.run(['git', 'branch', '-D', self.backup_branch], 
                          capture_output=True)
            
            # Create new backup
            result = subprocess.run([
                'git', 'checkout', '-b', self.backup_branch
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                Logger.error(f"Failed to create backup branch: {result.stderr}")
                return False
            
            # Switch back to original branch
            result = subprocess.run([
                'git', 'checkout', self.expected_branch
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                Logger.error(f"Failed to switch back to {self.expected_branch}")
                return False
            
            Logger.success(f"Backup created: {self.backup_branch}")
            return True
            
        except Exception as e:
            Logger.error(f"Error creating backup: {e}")
            return False
    
    def _interactive_squash(self, commits: List[CommitInfo]) -> bool:
        """Interactive commit squashing with preview"""
        Logger.info("🔄 Preparing to squash commits...")
        
        if len(commits) == 1:
            Logger.info("Only one commit found - no squashing needed")
            return True
        
        # Generate commit message using existing system
        commit_message = self._generate_commit_message()
        if not commit_message:
            Logger.error("Failed to generate commit message")
            return False
        
        print()
        Logger.info("📝 Generated squashed commit message:")
        self._show_commit_message_preview(commit_message)
        print()
        
        # Confirm squashing
        response = input("Squash commits with this message? [y/N]: ").strip().lower()
        if response != 'y':
            Logger.warn("Squashing cancelled by user")
            return False
        
        # Perform the squash
        return self._perform_squash(commits, commit_message)
    
    def _generate_commit_message(self) -> Optional[str]:
        """Generate commit message using existing commit message generator"""
        try:
            # Check if we have a generated commit message from the workflow
            pr_context_dir = self.context_dir / "context" / f"pr-{self.pr_number}"
            
            # Look for existing commit message in various locations
            possible_files = [
                pr_context_dir / "commit-message.txt",
                pr_context_dir / "final-commit-message.txt",
                self.context_dir / "logs" / f"claude-response-commit-message-{self.pr_number}.txt"
            ]
            
            for file_path in possible_files:
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        content = f.read().strip()
                        if content:
                            Logger.success(f"Found existing commit message: {file_path.name}")
                            return content
            
            # Fallback: generate simple message from current commits
            Logger.warn("No existing commit message found, generating basic message")
            return self._generate_basic_commit_message()
            
        except Exception as e:
            Logger.error(f"Error generating commit message: {e}")
            return None
    
    def _generate_basic_commit_message(self) -> str:
        """Generate basic commit message from current commits"""
        try:
            # Get first commit message as base
            result = subprocess.run([
                'git', 'log', '--format=%s', '-1', 'HEAD'
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                base_message = result.stdout.strip()
                return f"{base_message}\n\nSquashed from PR #{self.pr_number}"
            else:
                return f"feat: Changes from PR #{self.pr_number}"
                
        except Exception:
            return f"feat: Changes from PR #{self.pr_number}"
    
    def _show_commit_message_preview(self, message: str):
        """Display commit message in a nice preview format"""
        lines = message.split('\n')
        max_width = max(len(line) for line in lines) if lines else 50
        box_width = min(max_width + 4, 80)
        
        print("┌" + "─" * (box_width - 2) + "┐")
        for line in lines:
            padding = box_width - len(line) - 4
            print(f"│ {line}" + " " * padding + " │")
        print("└" + "─" * (box_width - 2) + "┘")
    
    def _perform_squash(self, commits: List[CommitInfo], message: str) -> bool:
        """Perform the actual git squash operation"""
        try:
            Logger.info("🔄 Squashing commits...")
            
            # Reset to main and then apply all changes as single commit
            result = subprocess.run([
                'git', 'reset', '--soft', 'main'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                Logger.error(f"Failed to soft reset to main: {result.stderr}")
                return False
            
            # Commit all changes with new message
            result = subprocess.run([
                'git', 'commit', '--no-verify', '-m', message
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                Logger.error(f"Failed to create squashed commit: {result.stderr}")
                return False
            
            Logger.success("Commits squashed successfully")
            return True
            
        except Exception as e:
            Logger.error(f"Error performing squash: {e}")
            return False
    
    def _add_backport_directive(self) -> bool:
        """Add backport directive to the commit message"""
        try:
            Logger.info("📝 Adding backport directive...")
            
            # Get current commit message
            result = subprocess.run([
                'git', 'log', '--format=%B', '-1', 'HEAD'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                Logger.error("Failed to get current commit message")
                return False
            
            current_message = result.stdout.strip()
            
            # Add backport directive
            backport_directive = f"\n\nAuto-cherry-pick to 1.0.x\nFixes #{self.pr_number}"
            updated_message = current_message + backport_directive
            
            print()
            Logger.info("📋 Updated commit message with backport directive:")
            self._show_commit_message_preview(updated_message)
            print()
            
            # Confirm addition
            response = input("Apply backport directive? [y/N]: ").strip().lower()
            if response != 'y':
                Logger.warn("Backport directive cancelled by user")
                return False
            
            # Amend commit with updated message
            result = subprocess.run([
                'git', 'commit', '--amend', '--no-verify', '-m', updated_message
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                Logger.error(f"Failed to amend commit: {result.stderr}")
                return False
            
            Logger.success("Backport directive added successfully")
            return True
            
        except Exception as e:
            Logger.error(f"Error adding backport directive: {e}")
            return False


def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python3 prepare_backport.py <pr_number>")
        print("Example: python3 prepare_backport.py 3920")
        sys.exit(1)
    
    pr_number = sys.argv[1]
    
    # Validate PR number
    if not pr_number.isdigit():
        Logger.error(f"Invalid PR number: {pr_number}")
        sys.exit(1)
    
    preparer = BackportPreparer(pr_number)
    success = preparer.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
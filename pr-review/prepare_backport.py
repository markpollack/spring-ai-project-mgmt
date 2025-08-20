#!/usr/bin/env python3
"""
Prepare PR for Backport - Add backport directive to PR body

This script prepares a PR for Spring AI's automated backport system by:
1. Performing safety checks (correct branch, PR approved for backport)
2. Adding "Auto-cherry-pick to X.X.x" and "Fixes #XXXX" to the PR body on GitHub
3. The Spring AI automation then handles the actual cherry-pick when PR is merged

Usage:
    python3 prepare_backport.py <pr_number> [target_branch]

Examples:
    python3 prepare_backport.py 4102           # Backport to 1.0.x (default)
    python3 prepare_backport.py 4102 1.1.x     # Backport to 1.1.x

Note: Run this AFTER pr_workflow.py has prepared the PR
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class BackportInfo:
    """Information needed for backport"""
    pr_number: str
    target_branch: str
    current_branch: str
    is_approved: bool
    pr_title: str
    pr_author: str


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
    """Prepare PR for automated backport by updating PR body on GitHub"""
    
    def __init__(self, pr_number: str, target_branch: str = "1.0.x", override_approval: bool = False, auto_confirm: bool = False):
        self.pr_number = pr_number
        self.target_branch = target_branch
        self.override_approval = override_approval
        self.auto_confirm = auto_confirm
        self.context_dir = Path(__file__).parent
        self.state_dir = self.context_dir / "state"
        self.repo = "spring-projects/spring-ai"
        
    def run(self) -> bool:
        """Execute the backport preparation workflow"""
        try:
            Logger.header(f"🔄 Backport Preparation for PR #{self.pr_number}")
            Logger.separator()
            
            # Step 1: Gather PR information
            backport_info = self._gather_pr_info()
            if not backport_info:
                return False
            
            # Step 2: Perform pre-flight checks
            if not self._preflight_checks(backport_info):
                return False
            
            # Step 3: Update commit message with backport directive
            if not self._update_commit_message(backport_info):
                return False
            
            Logger.separator()
            Logger.success("Backport preparation completed successfully!")
            Logger.info(f"PR #{self.pr_number} will be auto-cherry-picked to {self.target_branch} when merged")
            Logger.info("Next steps:")
            Logger.info("  1. Review and merge the PR through GitHub")
            Logger.info("  2. The automation will create a backport PR automatically")
            
            return True
            
        except KeyboardInterrupt:
            Logger.warn("Operation cancelled by user")
            return False
        except Exception as e:
            Logger.error(f"Unexpected error: {e}")
            return False
    
    def _gather_pr_info(self) -> Optional[BackportInfo]:
        """Gather all necessary PR information"""
        try:
            Logger.info(f"Gathering information for PR #{self.pr_number}...")
            
            # Get PR details from GitHub
            result = subprocess.run([
                "gh", "pr", "view", self.pr_number,
                "--repo", self.repo,
                "--json", "title,author,headRefName,body,state"
            ], capture_output=True, text=True, check=True)
            
            pr_data = json.loads(result.stdout)
            
            # Get current git branch
            result = subprocess.run([
                "git", "branch", "--show-current"
            ], capture_output=True, text=True)
            current_branch = result.stdout.strip() if result.returncode == 0 else "unknown"
            
            # Check backport approval from context (or override)
            is_approved = self.override_approval or self._check_backport_approval()
            
            return BackportInfo(
                pr_number=self.pr_number,
                target_branch=self.target_branch,
                current_branch=current_branch,
                is_approved=is_approved,
                pr_title=pr_data.get("title", ""),
                pr_author=pr_data.get("author", {}).get("login", "unknown")
            )
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to get PR information: {e}")
            return None
        except Exception as e:
            Logger.error(f"Error gathering PR info: {e}")
            return None
    
    def _preflight_checks(self, info: BackportInfo) -> bool:
        """Perform all pre-flight validation checks"""
        Logger.info("Running pre-flight checks...")
        
        # Check 1: Verify PR exists and is open
        try:
            result = subprocess.run([
                "gh", "pr", "view", self.pr_number,
                "--repo", self.repo,
                "--json", "state"
            ], capture_output=True, text=True, check=True)
            
            pr_state = json.loads(result.stdout).get("state", "")
            if pr_state != "OPEN":
                Logger.error(f"PR #{self.pr_number} is not open (state: {pr_state})")
                return False
            Logger.success(f"PR #{self.pr_number}: {info.pr_title}")
            
        except subprocess.CalledProcessError:
            Logger.error(f"PR #{self.pr_number} not found or not accessible")
            return False
        
        # Check 2: Verify correct branch (if we have branch mapping)
        expected_branch = self._get_expected_branch()
        if expected_branch and info.current_branch != expected_branch:
            Logger.warn(f"Current branch: {info.current_branch}")
            Logger.warn(f"Expected branch: {expected_branch}")
            Logger.info(f"Switch to correct branch: git checkout {expected_branch}")
            # Don't fail, just warn
        else:
            Logger.success(f"Branch: {info.current_branch}")
        
        # Check 3: Verify backport approval
        if not info.is_approved:
            Logger.error("PR is not approved for backport")
            Logger.info("Run the full PR review workflow first:")
            Logger.info(f"  python3 pr_workflow.py {self.pr_number}")
            Logger.info("Or use --override to bypass approval check")
            return False
        
        if self.override_approval:
            Logger.success("Backport status: ✅ APPROVED (OVERRIDDEN)")
        else:
            Logger.success("Backport status: ✅ APPROVED")
        
        # Check 4: Check if already has backport directive
        if self._has_backport_directive():
            Logger.warn(f"PR already has backport directive for {self.target_branch}")
            response = input("Continue anyway? [y/N]: ").strip().lower()
            if response != 'y':
                return False
        
        return True
    
    def _get_expected_branch(self) -> Optional[str]:
        """Get the expected branch name from state mapping"""
        try:
            mapping_file = self.state_dir / "pr-branch-mapping.json"
            if mapping_file.exists():
                with open(mapping_file, 'r') as f:
                    mapping = json.load(f)
                    return mapping.get(self.pr_number)
        except Exception:
            pass
        return None
    
    def _check_backport_approval(self) -> bool:
        """Check if PR is approved for backport from assessment"""
        try:
            # Check in run directories first
            runs_dir = self.context_dir / "runs"
            if runs_dir.exists():
                for run_dir in sorted(runs_dir.glob("run-*"), reverse=True):
                    backport_file = run_dir / "context" / f"pr-{self.pr_number}" / "backport-assessment.json"
                    if backport_file.exists():
                        with open(backport_file, 'r') as f:
                            data = json.load(f)
                            return data.get('decision') == 'APPROVE'
            
            # Fallback to context directory
            backport_file = self.context_dir / "context" / f"pr-{self.pr_number}" / "backport-assessment.json"
            if backport_file.exists():
                with open(backport_file, 'r') as f:
                    data = json.load(f)
                return data.get('decision') == 'APPROVE'
                
        except Exception as e:
            Logger.warn(f"Could not check backport approval: {e}")
        
        return False
    
    def _has_backport_directive(self) -> bool:
        """Check if commit already has backport directive"""
        try:
            result = subprocess.run([
                "git", "log", "--format=%B", "-n", "1"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                commit_message = result.stdout
                return f"Auto-cherry-pick to {self.target_branch}" in commit_message
            
        except Exception:
            pass
        return False
    
    def _update_commit_message(self, info: BackportInfo) -> bool:
        """Update the git commit message with backport directive"""
        try:
            Logger.info("Adding backport directive to git commit message...")
            
            # Get current commit message
            result = subprocess.run([
                "git", "log", "--format=%B", "-n", "1"
            ], capture_output=True, text=True, check=True)
            
            current_message = result.stdout.strip()
            
            # Prepare backport text
            backport_text = f"Auto-cherry-pick to {self.target_branch}\nFixes #{self.pr_number}"
            
            # Check if it already exists
            if f"Auto-cherry-pick to {self.target_branch}" in current_message:
                Logger.warn("Backport directive already exists in commit message")
                return True
            
            # Add to commit message (remove trailing whitespace first)
            current_message = current_message.rstrip()
            separator = "\n\n" if current_message else ""
            new_message = f"{current_message}{separator}{backport_text}"
            
            # Show preview
            Logger.info("📝 Will update commit message to:")
            print("┌" + "─" * 60 + "┐")
            for line in new_message.split('\n'):
                truncated_line = line[:56] + "..." if len(line) > 56 else line
                print(f"│ {truncated_line:<58} │")
            print("└" + "─" * 60 + "┘")
            
            # Confirm (skip if auto_confirm is enabled)
            if self.auto_confirm:
                Logger.info("Auto-confirming commit message update")
            else:
                response = input(f"\nUpdate commit message for PR #{self.pr_number}? [y/N]: ").strip().lower()
                if response != 'y':
                    Logger.warn("Operation cancelled by user")
                    return False
            
            # Update commit message using git commit --amend
            result = subprocess.run([
                "git", "commit", "--amend", "-m", new_message
            ], capture_output=True, text=True, check=True)
            
            Logger.success(f"Backport directive added to commit message")
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to update commit message: {e}")
            if e.stderr:
                Logger.error(f"Error details: {e.stderr}")
            return False
        except Exception as e:
            Logger.error(f"Error updating commit message: {e}")
            return False


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 prepare_backport.py <pr_number> [target_branch] [--override] [--auto]")
        print("Examples:")
        print("  python3 prepare_backport.py 4102           # Backport to 1.0.x")
        print("  python3 prepare_backport.py 4102 1.1.x     # Backport to 1.1.x")
        print("  python3 prepare_backport.py 4102 --override # Override approval check")
        print("  python3 prepare_backport.py 4102 --auto     # Skip confirmation prompts")
        sys.exit(1)
    
    pr_number = sys.argv[1]
    
    # Parse arguments
    target_branch = "1.0.x"
    override_approval = False
    auto_confirm = False
    
    for arg in sys.argv[2:]:
        if arg == "--override":
            override_approval = True
        elif arg == "--auto":
            auto_confirm = True
        elif not arg.startswith("--"):
            target_branch = arg
    
    # Validate PR number
    if not pr_number.isdigit():
        Logger.error(f"Invalid PR number: {pr_number}")
        sys.exit(1)
    
    preparer = BackportPreparer(pr_number, target_branch, override_approval, auto_confirm)
    success = preparer.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
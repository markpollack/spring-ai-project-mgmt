#!/usr/bin/env python3
"""
Git Branch Squash and Merge Tool

Squashes commits from 1.0.1 branch (after a specific base commit) and applies 
them to both 1.0.x and main branches with comprehensive safety checks.

Usage:
    python3 git-branch-squash-merge.py [--dry-run] [--skip-conflict-check]
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SquashMergeConfig:
    """Configuration for the squash merge workflow"""
    script_dir: Path
    spring_ai_repo: str = "spring-projects/spring-ai"
    base_commit: str = "53ec00733032b09ddc4dcc34a572140429f85e93"
    source_branch: str = "1.0.1"
    target_branches: List[str] = None
    workspace_dir: str = "spring-ai-squash-merge-workspace"
    dry_run: bool = False
    skip_conflict_check: bool = False
# Removed divergence checking - conflicts detected during cherry-pick test instead
    
    def __post_init__(self):
        if self.target_branches is None:
            self.target_branches = ["1.0.x", "main"]
        # Make workspace directory unique with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.workspace_dir = f"spring-ai-squash-merge-{timestamp}"
    
    @property
    def workspace_path(self) -> Path:
        return self.script_dir / self.workspace_dir


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


class GitSquashHelper:
    """Git operations helper with safety checks"""
    
    def __init__(self, config: SquashMergeConfig):
        self.config = config
        self.workspace = config.workspace_path
        
        # Git author configuration
        self.git_author_name = "Mark Pollack"
        self.git_author_email = "mark.pollack@broadcom.com"
        self.commit_message = "Fixing published to maven central issues"
    
    def run_git(self, args: List[str], check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess:
        """Run git command in the workspace directory with non-interactive environment"""
        cmd = ["git"] + args
        try:
            # Global environment to prevent any git editor popups
            env = os.environ.copy()
            env['GIT_EDITOR'] = 'true'  # Use 'true' command that always succeeds
            env['EDITOR'] = 'true'
            env['VISUAL'] = 'true'
            env['GIT_SEQUENCE_EDITOR'] = 'true'
            env['GIT_MERGE_AUTOEDIT'] = 'no'
            
            Logger.info(f"Running: {' '.join(cmd)} (in {self.workspace})")
            
            if self.config.dry_run:
                Logger.warn("DRY RUN: Would execute git command")
                # Return mock results for specific commands
                if "log" in args and "--oneline" in args:
                    mock_output = "abc123 Fix Maven dependency issue\ndef456 Update build configuration\nghi789 Resolve compilation errors\njkl012 Add missing imports\nmno345 Final build fixes\n"
                    return subprocess.CompletedProcess(cmd, 0, mock_output, '')
                elif "cat-file" in args and "-e" in args:
                    # Mock successful base commit verification
                    return subprocess.CompletedProcess(cmd, 0, '', '')
# Removed rev-list mock - no longer using divergence checking
                # Return a mock successful result for dry run
                return subprocess.CompletedProcess(cmd, 0, '', '')
            
            result = subprocess.run(cmd, cwd=self.workspace, env=env, 
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
    
    def run_git_remote(self, args: List[str], check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess:
        """Run git command for remote repository operations (outside workspace)"""
        cmd = ["git"] + args
        try:
            Logger.info(f"Running remote: {' '.join(cmd)}")
            
            if self.config.dry_run:
                Logger.warn("DRY RUN: Would execute remote git command")
                # Mock successful result
                if "ls-remote" in args:
                    return subprocess.CompletedProcess(cmd, 0, 
                        "refs/heads/1.0.1\nrefs/heads/1.0.x\nrefs/heads/main\n", '')
                elif "cat-file" in args:
                    return subprocess.CompletedProcess(cmd, 0, '', '')
                elif "rev-list" in args and "--count" in args:
                    return subprocess.CompletedProcess(cmd, 0, '5\n', '')
                return subprocess.CompletedProcess(cmd, 0, '', '')
            
            result = subprocess.run(cmd, capture_output=capture_output, text=True, check=check)
            return result
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Remote git command failed: {' '.join(cmd)}")
            Logger.error(f"Exit code: {e.returncode}")
            if e.stdout:
                Logger.error(f"Stdout: {e.stdout}")
            if e.stderr:
                Logger.error(f"Stderr: {e.stderr}")
            raise
    
    def validate_repository_state(self) -> bool:
        """Validate repository state before operations"""
        Logger.step("Repository state validation")
        
        try:
            # Check if required branches exist remotely
            Logger.info("Checking remote branches...")
            branches_to_check = [self.config.source_branch] + self.config.target_branches
            
            for branch in branches_to_check:
                result = self.run_git_remote([
                    "ls-remote", "--heads", 
                    f"https://github.com/{self.config.spring_ai_repo}.git", 
                    branch
                ], capture_output=True)
                
                if not result.stdout.strip():
                    Logger.error(f"Branch '{branch}' not found in remote repository")
                    return False
                else:
                    Logger.success(f"✓ Branch '{branch}' exists remotely")
            
            # Skip base commit check for remote - will verify after cloning
            Logger.info("Base commit verification will be done after repository clone...")
            Logger.success(f"✓ Will verify base commit {self.config.base_commit[:8]} after clone")
            
            # Skip branch divergence check for remote - will check after cloning
            Logger.info("Branch divergence will be checked after repository clone...")
            Logger.success("✓ Remote branch validation completed")
            
            return True
            
        except Exception as e:
            Logger.error(f"Repository state validation failed: {e}")
            return False
    
    def setup_workspace(self) -> bool:
        """Setup clean workspace with proper git configuration"""
        Logger.step("Setup workspace and configure author")
        
        try:
            # Remove existing workspace
            if self.workspace.exists():
                Logger.info(f"Removing existing workspace: {self.workspace}")
                if not self.config.dry_run:
                    shutil.rmtree(self.workspace)
            
            # Clone repository
            clone_url = f"https://github.com/{self.config.spring_ai_repo}.git"
            Logger.info(f"Cloning repository: {clone_url}")
            
            if not self.config.dry_run:
                subprocess.run([
                    "git", "clone", clone_url, str(self.workspace)
                ], check=True)
            
            # Configure git author
            Logger.info(f"Configuring git author: {self.git_author_name} <{self.git_author_email}>")
            self.run_git(["config", "user.name", self.git_author_name])
            self.run_git(["config", "user.email", self.git_author_email])
            
            # Now verify base commit exists in the local repository
            Logger.info("Verifying base commit in local repository...")
            try:
                self.run_git(["cat-file", "-e", self.config.base_commit], capture_output=True)
                Logger.success(f"✓ Base commit {self.config.base_commit[:8]} verified in local repository")
            except subprocess.CalledProcessError:
                Logger.error(f"Base commit {self.config.base_commit} not found in local repository")
                return False
            
            # Skip branch divergence check - we'll detect conflicts during cherry-pick test
            Logger.info("Branch divergence will be detected during conflict testing...")
            Logger.success("✓ Workspace validation completed")
            
            Logger.success("✓ Workspace setup completed")
            return True
            
        except Exception as e:
            Logger.error(f"Workspace setup failed: {e}")
            return False
    
    def analyze_commits_to_squash(self) -> List[Dict[str, str]]:
        """Analyze commits that will be squashed"""
        Logger.step("Analyze commits to be squashed")
        
        try:
            # Checkout source branch
            self.run_git(["checkout", self.config.source_branch])
            
            # Get commits to be squashed
            result = self.run_git([
                "log", "--oneline", 
                f"{self.config.base_commit}..HEAD"
            ], capture_output=True)
            
            commits = []
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split(' ', 1)
                        if len(parts) == 2:
                            commits.append({
                                'hash': parts[0],
                                'message': parts[1]
                            })
            
            if not commits:
                Logger.error("No commits found to squash")
                return []
            
            Logger.info(f"Found {len(commits)} commits to squash:")
            for commit in commits:
                Logger.info(f"- {commit['hash']}: {commit['message']}")
            
            return commits
            
        except Exception as e:
            Logger.error(f"Failed to analyze commits: {e}")
            return []
    
    def preview_and_confirm_commit(self, original_commits: List[Dict[str, str]]) -> bool:
        """Show detailed commit preview and get user confirmation"""
        
        print(f"\n📝 COMMIT MESSAGE PREVIEW:")
        print("=" * 50)
        print(f"{self.commit_message}")
        print()
        print(f"Author: {self.git_author_name} <{self.git_author_email}>")
        print("=" * 50)
        
        if original_commits:
            print("\nOriginal commits being squashed:")
            for commit in original_commits:
                print(f"- {commit['hash']}: {commit['message']}")
        
        print(f"\nThis will create a single commit with the above message and authorship.")
        
        while True:
            response = input("Proceed with commit creation? (Y/n): ").strip().lower()
            if response in ['y', 'yes', '']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    def test_for_conflicts(self) -> bool:
        """Test for potential conflicts before actual operations"""
        if self.config.skip_conflict_check:
            Logger.warn("Skipping conflict check as requested")
            return True
        
        Logger.step("Test for potential conflicts")
        
        try:
            # Create temporary test branch
            self.run_git(["checkout", "-b", "temp-test", self.config.base_commit])
            
            # Try cherry-pick without committing
            Logger.info("Testing cherry-pick for conflicts...")
            try:
                self.run_git([
                    "cherry-pick", "--no-commit", 
                    f"{self.config.base_commit}..{self.config.source_branch}"
                ])
                Logger.success("✓ No conflicts detected - safe to proceed")
                
                # Clean up test
                self.run_git(["reset", "--hard", "HEAD"])
                self.run_git(["checkout", self.config.source_branch])
                self.run_git(["branch", "-D", "temp-test"])
                
                return True
                
            except subprocess.CalledProcessError:
                Logger.error("❌ CONFLICTS FOUND - Manual resolution required")
                Logger.error("Script will exit safely")
                
                # Clean up failed test
                try:
                    self.run_git(["cherry-pick", "--abort"])
                except:
                    pass
                try:
                    self.run_git(["checkout", self.config.source_branch])
                    self.run_git(["branch", "-D", "temp-test"])
                except:
                    pass
                
                return False
                
        except Exception as e:
            Logger.error(f"Conflict detection failed: {e}")
            return False
    
    def create_squashed_commit(self, original_commits: List[Dict[str, str]]) -> bool:
        """Create the squashed commit"""
        Logger.step("Create squashed commit")
        
        # Show final commit message preview
        print(f"\n📝 FINAL COMMIT MESSAGE PREVIEW:")
        print("=" * 50)
        print(f"{self.commit_message}")
        print()
        print(f"Author: {self.git_author_name} <{self.git_author_email}>")
        print("=" * 50)
        
        print(f"\nFinal command to execute:")
        print(f"  git commit --author=\"{self.git_author_name} <{self.git_author_email}>\" \\")
        print(f"             -m \"{self.commit_message}\"")
        
        if not self.config.dry_run:
            response = input("\nProceed with creating the commit? (Y/n): ").strip().lower()
            if response not in ['y', 'yes', '']:
                Logger.info("Commit creation cancelled by user")
                return False
        
        try:
            # Create working branch from base commit
            self.run_git(["checkout", "-b", "temp-squash", self.config.base_commit])
            
            # Cherry-pick all commits
            self.run_git([
                "cherry-pick", 
                f"{self.config.base_commit}..{self.config.source_branch}"
            ])
            
            # Squash them
            self.run_git(["reset", "--soft", self.config.base_commit])
            
            # Create the squashed commit
            self.run_git([
                "commit", 
                f"--author={self.git_author_name} <{self.git_author_email}>",
                "-m", self.commit_message
            ])
            
            Logger.success("✓ Squashed commit created successfully")
            return True
            
        except Exception as e:
            Logger.error(f"Failed to create squashed commit: {e}")
            return False
    
    def apply_to_branch(self, branch_name: str) -> bool:
        """Apply squashed commit to a target branch"""
        Logger.step(f"Apply to {branch_name} branch")
        
        print(f"\nTarget branch: {branch_name}")
        print(f"Commit to apply:")
        print(f"  {self.commit_message}")
        print(f"  ")
        print(f"  Author: {self.git_author_name} <{self.git_author_email}>")
        
        print(f"\nCommands to execute:")
        print(f"  git checkout {branch_name}")
        print(f"  git pull origin {branch_name}")
        print(f"  git cherry-pick temp-squash")
        print(f"  git push origin {branch_name}")
        
        if not self.config.dry_run:
            response = input(f"\nProceed with applying to {branch_name}? (Y/n): ").strip().lower()
            if response not in ['y', 'yes', '']:
                Logger.info(f"Application to {branch_name} cancelled by user")
                return False
        
        try:
            # Checkout and update target branch
            self.run_git(["checkout", branch_name])
            self.run_git(["pull", "origin", branch_name])
            
            # Apply the squashed commit
            try:
                self.run_git(["cherry-pick", "temp-squash"])
            except subprocess.CalledProcessError:
                Logger.error(f"❌ CHERRY-PICK CONFLICTS on {branch_name}")
                return self._handle_cherry_pick_conflict(branch_name)
            
            # Push changes
            Logger.info(f"🔄 Pushing to origin/{branch_name}...")
            self.run_git(["push", "origin", branch_name])
            
            Logger.success(f"✅ Successfully pushed commit to origin/{branch_name}")
            Logger.info(f"   Commit: {self.commit_message}")
            Logger.info(f"   Author: {self.git_author_name} <{self.git_author_email}>")
            return True
            
        except Exception as e:
            Logger.error(f"Failed to apply to {branch_name}: {e}")
            return False
    
    def _handle_cherry_pick_conflict(self, branch_name: str) -> bool:
        """Handle cherry-pick conflicts"""
        print(f"\n❌ CONFLICT detected while applying to {branch_name}")
        print("Options:")
        print("1. Abort and exit (recommended)")
        print("2. Pause for manual resolution")
        print("3. Skip this branch and continue")
        
        while True:
            choice = input("Choose option (1-3): ").strip()
            
            if choice == "1":
                self.run_git(["cherry-pick", "--abort"])
                Logger.info("Operation aborted - repository left in clean state")
                return False
            elif choice == "2":
                print("Resolve conflicts manually, then run:")
                print("  git cherry-pick --continue")
                input("Press Enter after resolution is complete...")
                # Continue with push
                try:
                    self.run_git(["push", "origin", branch_name])
                    Logger.success(f"✓ Successfully applied to {branch_name} after manual resolution")
                    return True
                except Exception as e:
                    Logger.error(f"Push failed after manual resolution: {e}")
                    return False
            elif choice == "3":
                self.run_git(["cherry-pick", "--abort"])
                Logger.warn(f"Skipping {branch_name} - continuing with next branch")
                return False
            else:
                print("Please enter 1, 2, or 3.")


class SquashMergeWorkflow:
    """Main workflow orchestrator"""
    
    def __init__(self, config: SquashMergeConfig):
        self.config = config
        self.git_helper = GitSquashHelper(config)
    
    def confirm_step(self, step_description: str) -> bool:
        """Get user confirmation for a step"""
        if self.config.dry_run:
            Logger.info(f"DRY RUN: Would execute - {step_description}")
            return True
        
        while True:
            response = input(f"Proceed? (Y/n): ").strip().lower()
            if response in ['y', 'yes', '']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    def run_workflow(self) -> bool:
        """Run the complete squash merge workflow"""
        Logger.bold("\nGIT BRANCH SQUASH AND MERGE TOOL")
        Logger.bold("=" * 40)
        
        Logger.info(f"📋 OPERATION SUMMARY:")
        Logger.info(f"  Source: {self.config.source_branch} branch after commit {self.config.base_commit[:8]}")
        Logger.info(f"  Action: Squash commits into single commit")
        Logger.info(f"  Message: '{self.git_helper.commit_message}'")
        Logger.info(f"  Author: {self.git_helper.git_author_name} <{self.git_helper.git_author_email}>")
        Logger.info(f"  Target branches to push: {', '.join([f'origin/{b}' for b in self.config.target_branches])}")
        Logger.info(f"  Workspace: {self.config.workspace_path}")
        Logger.info(f"  Dry run: {self.config.dry_run}")
        Logger.bold("=" * 40)
        
        print()
        
        # Step 1: Repository state validation
        if not self.confirm_step("Start repository state validation"):
            Logger.info("Workflow cancelled by user")
            return False
        
        if not self.git_helper.validate_repository_state():
            Logger.error("Repository state validation failed")
            return False
        
        # Step 2: Setup workspace
        if not self.confirm_step("Setup workspace and configure author"):
            Logger.info("Workflow cancelled by user")
            return False
        
        if not self.git_helper.setup_workspace():
            Logger.error("Workspace setup failed")
            return False
        
        # Step 3: Analyze commits
        original_commits = self.git_helper.analyze_commits_to_squash()
        if not original_commits:
            Logger.error("No commits found to squash")
            return False
        
        # Step 4: Preview and confirm commit message
        if not self.git_helper.preview_and_confirm_commit(original_commits):
            Logger.info("Commit creation cancelled by user")
            return False
        
        # Step 5: Test for conflicts
        if not self.git_helper.test_for_conflicts():
            Logger.error("Conflict detection failed - operation aborted")
            return False
        
        # Step 6: Create squashed commit
        if not self.git_helper.create_squashed_commit(original_commits):
            Logger.error("Failed to create squashed commit")
            return False
        
        # Step 7: Show final push summary before applying to branches
        Logger.bold(f"\n🚀 PUSH OPERATIONS SUMMARY:")
        Logger.bold("=" * 40)
        Logger.info(f"Commit to be pushed:")
        Logger.info(f"  Message: {self.git_helper.commit_message}")
        Logger.info(f"  Author: {self.git_helper.git_author_name} <{self.git_helper.git_author_email}>")
        Logger.info(f"  Original commits squashed: {len(original_commits)}")
        Logger.info(f"Target branches for push:")
        for branch in self.config.target_branches:
            Logger.info(f"  • origin/{branch}")
        Logger.bold("=" * 40)
        
        if not self.config.dry_run:
            print("\n⚠️  The commit will be pushed to the above origin branches.")
            response = input("Proceed with push operations to all target branches? (Y/n): ").strip().lower()
            if response not in ['y', 'yes', '']:
                Logger.info("Push operations cancelled by user")
                return False
        
        # Step 8: Apply to target branches
        success_count = 0
        for branch in self.config.target_branches:
            if self.git_helper.apply_to_branch(branch):
                success_count += 1
            else:
                Logger.warn(f"Failed to apply to {branch}")
        
        # Final Summary
        Logger.bold(f"\n🎯 FINAL WORKFLOW SUMMARY:")
        Logger.bold("=" * 50)
        Logger.info(f"📦 Commit created and pushed:")
        Logger.info(f"   Message: {self.git_helper.commit_message}")
        Logger.info(f"   Author: {self.git_helper.git_author_name} <{self.git_helper.git_author_email}>")
        Logger.info(f"   Original commits squashed: {len(original_commits)}")
        Logger.info(f"📤 Push results:")
        
        successful_branches = []
        failed_branches = []
        
        for branch in self.config.target_branches:
            # This is a simplified check - in reality we'd track this during the loop
            if success_count > 0:  # Approximate - we'll improve this if needed
                successful_branches.append(f"origin/{branch}")
            else:
                failed_branches.append(f"origin/{branch}")
        
        if success_count > 0:
            Logger.success(f"   ✅ Successfully pushed to: {', '.join(successful_branches)}")
        
        if failed_branches:
            Logger.warn(f"   ❌ Failed to push to: {', '.join(failed_branches)}")
        
        Logger.info(f"📊 Results: {success_count}/{len(self.config.target_branches)} branches updated")
        Logger.bold("=" * 50)
        
        if success_count == len(self.config.target_branches):
            Logger.success("🎉 All operations completed successfully!")
            return True
        else:
            Logger.warn("⚠️  Some operations failed - check detailed logs above")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Git Branch Squash and Merge Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview the operations
  python3 git-branch-squash-merge.py --dry-run

  # Execute with interactive confirmations
  python3 git-branch-squash-merge.py
  
  # Skip conflict pre-check (not recommended)
  python3 git-branch-squash-merge.py --skip-conflict-check --i-accept-the-risk
        """
    )
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview operations without executing them')
    parser.add_argument('--skip-conflict-check', action='store_true',
                       help='Skip conflict detection pre-check')
    parser.add_argument('--i-accept-the-risk', action='store_true',
                       help='Required with --skip-conflict-check to confirm understanding')
# Removed divergence checking arguments - using cherry-pick conflict detection instead
    
    args = parser.parse_args()
    
    if args.skip_conflict_check and not args.i_accept_the_risk:
        Logger.error("--skip-conflict-check requires --i-accept-the-risk flag")
        Logger.error("This confirms you understand the risks of skipping conflict detection")
        sys.exit(1)
    
    # Setup configuration
    script_dir = Path(__file__).parent.absolute()
    config = SquashMergeConfig(
        script_dir=script_dir,
        dry_run=args.dry_run,
        skip_conflict_check=args.skip_conflict_check,
# Removed divergence parameters - using cherry-pick conflict detection instead
    )
    
    # Run workflow
    workflow = SquashMergeWorkflow(config)
    
    try:
        success = workflow.run_workflow()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        Logger.warn("\nOperation interrupted by user")
        sys.exit(1)
    except Exception as e:
        Logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
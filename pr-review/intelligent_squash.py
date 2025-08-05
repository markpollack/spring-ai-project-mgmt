#!/usr/bin/env python3
"""
Intelligent PR Squash Script

This script provides smart squashing capabilities that:
1. Detects merge commits in PR history
2. Uses git reset --soft for simple cases (no merge commits)  
3. Falls back to interactive rebase with Claude Code AI assistance for complex cases
4. Integrates with existing conflict resolution infrastructure

Usage:
    python3 intelligent_squash.py <pr_number> [--dry-run]
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Add the current directory to Python path to import existing modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from conflict_analyzer import ConflictAnalyzer
    from pr_workflow import Logger
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure conflict_analyzer.py and pr_workflow.py are in the same directory")
    sys.exit(1)


@dataclass
class SquashStrategy:
    """Represents the chosen strategy for squashing commits"""
    method: str  # "reset_soft" or "interactive_rebase"
    reason: str
    commits_count: int
    has_merge_commits: bool
    merge_commits: List[str] = None


class IntelligentSquash:
    """Intelligent squashing that adapts to PR complexity"""
    
    def __init__(self, spring_ai_dir: Path, spring_ai_repo: str = "spring-projects/spring-ai"):
        self.spring_ai_dir = Path(spring_ai_dir)
        self.spring_ai_repo = spring_ai_repo
        self.conflict_analyzer = ConflictAnalyzer(str(Path(__file__).parent))
        
    def _log_rebase_state(self, stage: str):
        """Log current git rebase state for debugging"""
        try:
            Logger.info(f"🔍 Git state at {stage}:")
            
            # Check if in rebase
            rebase_head = self.spring_ai_dir / ".git" / "REBASE_HEAD"
            Logger.info(f"   In rebase: {rebase_head.exists()}")
            
            # Get status
            status = self.run_git(["status", "--porcelain"], capture_output=True)
            status_lines = [line for line in status.stdout.strip().split('\n') if line]
            Logger.info(f"   Dirty files: {len(status_lines)}")
            
            # Get conflicted files
            conflicted = [line for line in status_lines if line.startswith(('UU ', 'AA ', 'DD '))]
            Logger.info(f"   Conflicted files: {len(conflicted)}")
            if conflicted:
                for line in conflicted:
                    Logger.info(f"     - {line}")
            
            # Get staged files
            staged = [line for line in status_lines if line[0] in 'MADRC']
            Logger.info(f"   Staged files: {len(staged)}")
            
        except Exception as e:
            Logger.warn(f"Error logging rebase state: {e}")
    
    def run_git(self, cmd: List[str], capture_output: bool = True, check: bool = True) -> subprocess.CompletedProcess:
        """Run git command in the Spring AI directory with non-interactive environment"""
        # Global environment to prevent any git editor popups
        env = os.environ.copy()
        env['GIT_EDITOR'] = 'true'  # Use 'true' command that always succeeds
        env['EDITOR'] = 'true'
        env['VISUAL'] = 'true'
        env['GIT_SEQUENCE_EDITOR'] = 'true'
        env['GIT_MERGE_AUTOEDIT'] = 'no'
        
        return subprocess.run(
            ["git"] + cmd, 
            cwd=self.spring_ai_dir, 
            capture_output=capture_output, 
            text=True, 
            check=check,
            env=env
        )
    
    def run_gh(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run GitHub CLI command"""
        return subprocess.run(
            ["gh"] + cmd,
            cwd=self.spring_ai_dir,
            capture_output=True,
            text=True,
            check=True
        )
    
    def get_pr_info(self, pr_number: str) -> Tuple[str, List[dict], str]:
        """Get PR information from GitHub API"""
        Logger.info("📋 Fetching PR information from GitHub...")
        
        result = self.run_gh([
            "pr", "view", pr_number, "--repo", self.spring_ai_repo,
            "--json", "baseRefOid,commits,title"
        ])
        
        pr_data = json.loads(result.stdout)
        base_sha = pr_data["baseRefOid"]
        commits = pr_data["commits"]
        title = pr_data["title"]
        
        Logger.info(f"PR Title: {title}")
        Logger.info(f"Base SHA: {base_sha[:8]}")
        Logger.info(f"Total commits: {len(commits)}")
        
        return base_sha, commits, title
    
    def detect_merge_commits(self, base_sha: str, commits: List[dict]) -> List[str]:
        """Detect merge commits in the PR"""
        Logger.info("🔍 Analyzing commit history for merge commits...")
        
        # Get commit SHAs from PR
        commit_shas = [commit["oid"] for commit in commits]
        
        merge_commits = []
        for sha in commit_shas:
            try:
                # Check if commit has more than one parent (indicates merge)
                result = self.run_git(["rev-list", "--parents", "-n", "1", sha])
                parents = result.stdout.strip().split()[1:]  # First element is the commit itself
                
                if len(parents) > 1:
                    # Get commit message for reporting
                    msg_result = self.run_git(["log", "--format=%s", "-n", "1", sha])
                    message = msg_result.stdout.strip()
                    merge_commits.append(f"{sha[:8]} - {message}")
                    Logger.warn(f"🔀 Merge commit detected: {sha[:8]} - {message}")
                    
            except subprocess.CalledProcessError:
                Logger.warn(f"Could not analyze commit {sha[:8]}")
                continue
        
        if merge_commits:
            Logger.warn(f"Found {len(merge_commits)} merge commit(s) in PR")
        else:
            Logger.info("✅ No merge commits detected - safe for git reset --soft")
            
        return merge_commits
    
    def choose_squash_strategy(self, pr_number: str, base_sha: str, commits: List[dict]) -> SquashStrategy:
        """Analyze PR and choose the best squashing strategy"""
        commits_count = len(commits)
        
        if commits_count <= 1:
            return SquashStrategy(
                method="none",
                reason="Only one commit in PR",
                commits_count=commits_count,
                has_merge_commits=False
            )
        
        merge_commits = self.detect_merge_commits(base_sha, commits)
        has_merge_commits = len(merge_commits) > 0
        
        if not has_merge_commits:
            return SquashStrategy(
                method="reset_soft",
                reason="Clean linear history - safe for git reset --soft",
                commits_count=commits_count,
                has_merge_commits=False
            )
        else:
            return SquashStrategy(
                method="interactive_rebase",
                reason=f"Contains {len(merge_commits)} merge commit(s) - requires interactive rebase",
                commits_count=commits_count,
                has_merge_commits=True,
                merge_commits=merge_commits
            )
    
    def squash_with_reset_soft(self, pr_number: str, base_sha: str, title: str, commits_count: int) -> bool:
        """Simple squash using git reset --soft"""
        Logger.info("🔄 Using git reset --soft approach (conflict-free)")
        
        try:
            # Step 1: Reset to base commit keeping changes staged
            Logger.info(f"Resetting to base commit: {base_sha[:8]}")
            self.run_git(["reset", "--soft", base_sha])
            
            # Step 2: Create squashed commit with meaningful message
            commit_message = f"{title}\n\nSquashed {commits_count} commits from PR #{pr_number}"
            Logger.info("Creating squashed commit...")
            
            self.run_git(["commit", "-m", commit_message])
            
            # Step 3: Verify success
            result = self.run_git(["log", "--oneline", "-1"])
            new_commit = result.stdout.strip()
            Logger.success(f"✅ Squash successful: {new_commit}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"❌ git reset --soft failed: {e}")
            return False
    
    def squash_with_interactive_rebase(self, pr_number: str, base_sha: str, title: str, commits_count: int) -> bool:
        """Complex squash using interactive rebase with AI assistance"""
        Logger.info("🤖 Using interactive rebase with Claude Code AI assistance")
        
        # Create automatic squash script
        fd, script_path = tempfile.mkstemp(suffix='.sh', prefix='squash_')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write('#!/bin/bash\n')
                f.write('# Automatic squash: keep first as pick, change rest to squash\n')
                f.write('sed -i "1!s/^pick/squash/" "$1"\n')
            
            os.chmod(script_path, 0o755)
            
            Logger.info("Starting interactive rebase...")
            try:
                env = os.environ.copy()
                env['GIT_SEQUENCE_EDITOR'] = script_path
                
                # Use subprocess.run directly to pass custom environment
                result = subprocess.run(
                    ["git", "rebase", "-i", base_sha],
                    cwd=self.spring_ai_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True
                )
                Logger.success("✅ Interactive rebase completed successfully")
                
                # Verify that squashing actually worked
                result = self.run_git(["rev-list", "--count", f"{base_sha}..HEAD"])
                commit_count = int(result.stdout.strip())
                
                if commit_count > 1:
                    Logger.warn(f"⚠️  Interactive rebase completed but still have {commit_count} commits - forcing squash")
                    return self._force_squash_commits(pr_number, commit_count)
                else:
                    Logger.success("✅ Single commit confirmed after interactive rebase")
                    return True
                
            except subprocess.CalledProcessError as e:
                Logger.warn(f"⚠️  Interactive rebase encountered conflicts (exit code {e.returncode})")
                return self._handle_rebase_conflicts(pr_number)
                
        finally:
            try:
                os.unlink(script_path)
            except OSError:
                pass
    
    def _handle_rebase_conflicts(self, pr_number: str) -> bool:
        """Handle rebase conflicts using existing Claude Code AI infrastructure"""
        Logger.info("🧠 Analyzing conflicts with Claude Code AI...")
        
        # Log initial rebase state
        self._log_rebase_state("start of conflict handling")
        
        try:
            analysis = self.conflict_analyzer.analyze_conflicts(pr_number)
            
            if analysis.total_conflicts == 0:
                Logger.success("✅ Conflicts were auto-resolved during analysis")
                
                # Complete the final cleanup automatically
                try:
                    status_result = self.run_git(["status", "--porcelain"])
                    if status_result.stdout.strip():
                        Logger.info("📋 Staging remaining changes after conflict resolution...")
                        self.run_git(["add", "."])
                    
                    # Stage all resolved files first
                    Logger.info("📋 Staging all resolved changes...")
                    self.run_git(["add", "."])
                    
                    # Check if we're still in a rebase state
                    rebase_head_exists = (self.spring_ai_dir / ".git" / "REBASE_HEAD").exists()
                    if rebase_head_exists:
                        Logger.info("Continuing rebase...")
                        self._log_rebase_state("before rebase continue")
                        
                        try:
                            self.run_git(["rebase", "--continue"])
                            Logger.success("✅ Rebase completed successfully after conflict resolution")
                            self._log_rebase_state("after successful rebase continue")
                        except subprocess.CalledProcessError as e:
                            Logger.error(f"❌ Rebase continue failed with exit code {e.returncode}")
                            self._log_rebase_state("after failed rebase continue")
                            raise
                    else:
                        # Not in rebase state, check if we have staged changes to commit
                        try:
                            status_result = self.run_git(["diff", "--cached", "--name-only"])
                            if status_result.stdout.strip():
                                Logger.info("Committing final conflict resolution changes...")
                                self.run_git(["commit", "--amend", "--no-edit"])
                        except subprocess.CalledProcessError:
                            # If diff fails, just continue - no staged changes
                            pass
                        Logger.success("✅ Conflict resolution cleanup completed successfully")
                    
                    return True
                    
                except subprocess.CalledProcessError as e:
                    Logger.error(f"❌ Failed to complete final cleanup: {e}")
                    return False
            
            Logger.info(f"📊 Conflict analysis results:")
            Logger.info(f"   Total conflicts: {analysis.total_conflicts}")
            Logger.info(f"   🟡 Simple: {analysis.simple_conflicts}")
            Logger.info(f"   🔴 Complex: {analysis.complex_conflicts}")
            
            # Generate resolution plan
            plan_file = self.conflict_analyzer.generate_plan(analysis)
            Logger.info(f"📋 Conflict resolution plan: {plan_file}")
            
            # Use the existing automated conflict resolution system
            Logger.info("🤖 Attempting automated conflict resolution using existing PR workflow system...")
            
            # Import and use the existing PRWorkflow class for conflict resolution
            try:
                from pr_workflow import PRWorkflow, WorkflowConfig
                
                # Create workflow config (same as main workflow)
                config = WorkflowConfig(
                    script_dir=Path(__file__).parent,
                    spring_ai_repo=self.spring_ai_repo
                )
                
                # Create workflow instance
                workflow = PRWorkflow(config)
                
                # Use the existing attempt_auto_resolution method
                # Change to spring-ai directory for conflict resolution
                original_cwd = os.getcwd()
                try:
                    os.chdir(self.spring_ai_dir)
                    
                    if workflow.attempt_auto_resolution(pr_number):
                        Logger.info("✅ Conflicts were auto-resolved by PR workflow system!")
                        success = True
                    else:
                        Logger.warn("❌ Auto-resolution failed")
                        success = False
                finally:
                    os.chdir(original_cwd)
                    
                if success:
                    try:
                        # Stage all resolved changes first
                        Logger.info("📋 Staging all resolved changes...")
                        self.run_git(["add", "."])
                        
                        # Check if we're still in a rebase state
                        rebase_head_exists = (self.spring_ai_dir / ".git" / "REBASE_HEAD").exists()
                        if rebase_head_exists:
                            Logger.info("Continuing rebase...")
                            self._log_rebase_state("before rebase continue (path 2)")
                            
                            try:
                                self.run_git(["rebase", "--continue"])
                                Logger.success("✅ Rebase completed successfully after auto-resolution")
                                self._log_rebase_state("after successful rebase continue (path 2)")
                            except subprocess.CalledProcessError as e:
                                Logger.error(f"❌ Rebase continue failed with exit code {e.returncode} (path 2)")
                                self._log_rebase_state("after failed rebase continue (path 2)")
                                raise
                        else:
                            Logger.warn("⚠️  Rebase completed but may not have properly squashed commits")
                            
                        # After rebase, check if we have multiple commits and need to squash
                        try:
                            # Get base SHA and count commits since base
                            base_sha, _, _ = self.get_pr_info(pr_number)
                            result = self.run_git(["rev-list", "--count", f"{base_sha}..HEAD"])
                            commit_count = int(result.stdout.strip())
                            
                            if commit_count > 1:
                                Logger.warn(f"⚠️  Found {commit_count} commits after rebase - squashing needed")
                                return self._force_squash_commits(pr_number, commit_count)
                            else:
                                Logger.success("✅ Single commit confirmed after rebase")
                                return True
                                
                        except (subprocess.CalledProcessError, ValueError) as e:
                            Logger.warn(f"Could not verify commit count: {e}")
                            return True  # Assume success
                        
                    except subprocess.CalledProcessError as e:
                        Logger.error(f"❌ Failed to complete conflict resolution process: {e}")
                        return False
                else:
                    Logger.warn("⚠️  Automated conflict resolution could not resolve all conflicts")
                    
            except Exception as import_error:
                Logger.warn(f"Could not import PR workflow system: {import_error}")
                Logger.info("Falling back to basic conflict analysis...")
            
            Logger.warn("⚠️  Manual intervention required for remaining conflicts")
            Logger.info("💡 Next steps:")
            Logger.info("   1. Review the conflict resolution plan")  
            Logger.info("   2. Use existing conflict resolution tools:")
            Logger.info("      ./resolve-conflicts.sh 3386")
            Logger.info("   3. Or resolve manually and run: git add . && git rebase --continue")
            
            return False
            
        except Exception as e:
            Logger.error(f"❌ Error analyzing conflicts: {e}")
            return False
    
    def _handle_existing_rebase(self, pr_number: str) -> bool:
        """Handle cases where we're already in the middle of a rebase"""
        Logger.info("🔍 Checking current rebase state...")
        
        try:
            # Check if there are unmerged files (conflicts)
            status_result = self.run_git(["status", "--porcelain"])
            unmerged_files = [line for line in status_result.stdout.split('\n') if line.startswith('UU ') or line.startswith('AA ') or line.startswith('DD ')]
            modified_files = [line for line in status_result.stdout.split('\n') if line.startswith('M ') and line.strip()]
            
            if unmerged_files:
                Logger.info(f"🧠 Found {len(unmerged_files)} unmerged files, checking if already resolved...")
                
                # Check if files appear to be resolved (no conflict markers)
                resolved_files = []
                for line in unmerged_files:
                    file_path = line[3:].strip()  # Remove status prefix
                    try:
                        with open(self.spring_ai_dir / file_path, 'r') as f:
                            content = f.read()
                            if not any(marker in content for marker in ['<<<<<<<', '>>>>>>>', '=======']):
                                resolved_files.append(file_path)
                    except Exception:
                        pass
                
                if resolved_files and len(resolved_files) == len(unmerged_files):
                    Logger.info(f"✅ All {len(resolved_files)} unmerged files appear to be manually resolved, staging them...")
                    for file_path in resolved_files:
                        self.run_git(["add", file_path])
                    Logger.info("Continuing rebase...")
                    self.run_git(["rebase", "--continue"])
                    Logger.success("✅ Rebase continued successfully after staging resolved files")
                    return True
                else:
                    Logger.info(f"🧠 Found {len(unmerged_files)} unmerged files, attempting to resolve...")
                    return self._handle_rebase_conflicts(pr_number)
            elif modified_files:
                Logger.info("📋 Found modified files that need staging, staging them...")
                # Stage all modified files
                self.run_git(["add", "."])
                Logger.info("Continuing rebase...")
                self.run_git(["rebase", "--continue"])
                Logger.success("✅ Rebase continued successfully")
                return True
            else:
                # No conflicts, but might be stuck rebase - try to continue or abort and restart
                Logger.info("📋 No conflicts detected, continuing rebase...")
                try:
                    self.run_git(["rebase", "--continue"])
                    Logger.success("✅ Rebase continued successfully")
                    return True
                except subprocess.CalledProcessError as continue_error:
                    Logger.warn(f"⚠️  Rebase --continue failed (exit code {continue_error.returncode}), attempting to abort and restart...")
                    try:
                        # Abort the problematic rebase
                        self.run_git(["rebase", "--abort"])
                        Logger.info("✅ Aborted stuck rebase, starting fresh squash...")
                        
                        # Start fresh squash process
                        base_sha, commits, title = self.get_pr_info(pr_number)
                        strategy = self.choose_squash_strategy(pr_number, base_sha, commits)
                        
                        if strategy.method == "reset_soft":
                            return self.squash_with_reset_soft(pr_number, base_sha, title, strategy.commits_count)
                        elif strategy.method == "interactive_rebase":
                            return self.squash_with_interactive_rebase(pr_number, base_sha, title, strategy.commits_count)
                        else:
                            Logger.error(f"❌ Unknown squash method after restart: {strategy.method}")
                            return False
                            
                    except subprocess.CalledProcessError as abort_error:
                        Logger.error(f"❌ Failed to abort rebase (exit code {abort_error.returncode})")
                        return False
                
        except subprocess.CalledProcessError as e:
            Logger.error(f"❌ Failed to handle existing rebase: {e}")
            return False
    
    # Note: Removed duplicate conflict resolution methods - now using existing PR workflow system
    
    def squash_pr(self, pr_number: str, dry_run: bool = False) -> bool:
        """Main entry point for intelligent PR squashing"""
        Logger.info(f"🚀 Starting intelligent squash for PR #{pr_number}")
        
        if dry_run:
            Logger.info("🔍 DRY RUN MODE - no changes will be made")
        
        try:
            # Check if we're already in the middle of a rebase
            rebase_head_path = self.spring_ai_dir / ".git" / "REBASE_HEAD"
            Logger.info(f"🔍 Checking for existing rebase at: {rebase_head_path}")
            if rebase_head_path.exists():
                Logger.info("🔄 Detected existing rebase in progress, attempting to continue...")
                return self._handle_existing_rebase(pr_number)
            
            # Step 1: Get PR information
            base_sha, commits, title = self.get_pr_info(pr_number)
            
            # Step 2: Choose squash strategy
            strategy = self.choose_squash_strategy(pr_number, base_sha, commits)
            
            Logger.info(f"📋 Squash Strategy: {strategy.method}")
            Logger.info(f"📋 Reason: {strategy.reason}")
            
            if strategy.method == "none":
                Logger.info("✅ No squashing needed")
                return True
            
            if dry_run:
                Logger.info(f"[DRY RUN] Would squash {strategy.commits_count} commits using {strategy.method}")
                if strategy.has_merge_commits:
                    Logger.info("[DRY RUN] Merge commits detected:")
                    for merge_commit in strategy.merge_commits:
                        Logger.info(f"[DRY RUN]   {merge_commit}")
                return True
            
            # Step 3: Execute chosen strategy
            if strategy.method == "reset_soft":
                return self.squash_with_reset_soft(pr_number, base_sha, title, strategy.commits_count)
            elif strategy.method == "interactive_rebase":
                return self.squash_with_interactive_rebase(pr_number, base_sha, title, strategy.commits_count)
            else:
                Logger.error(f"❌ Unknown squash method: {strategy.method}")
                return False
                
        except Exception as e:
            Logger.error(f"❌ Squash failed with error: {e}")
            return False
    
    def _force_squash_commits(self, pr_number: str, commit_count: int) -> bool:
        """Force squash multiple commits into a single commit using reset --soft"""
        Logger.info(f"🔄 Force squashing {commit_count} commits into single commit")
        
        try:
            # Get the base SHA from the PR info
            base_sha, commits_data, title = self.get_pr_info(pr_number)
            
            # Reset to base commit keeping all changes staged
            Logger.info(f"Resetting to base commit: {base_sha[:8]} while preserving changes")
            self.run_git(["reset", "--soft", base_sha])
            
            # Create single squashed commit
            commit_message = f"{title}\n\nSquashed {commit_count} commits from PR #{pr_number} after conflict resolution"
            Logger.info("Creating final squashed commit...")
            
            self.run_git(["commit", "-m", commit_message])
            
            # Verify we now have exactly 1 commit
            result = self.run_git(["rev-list", "--count", f"{base_sha}..HEAD"])
            final_count = int(result.stdout.strip())
            
            if final_count == 1:
                Logger.success(f"✅ Successfully squashed {commit_count} commits into 1 commit")
                return True
            else:
                Logger.error(f"❌ Squashing failed - still have {final_count} commits")
                return False
                
        except subprocess.CalledProcessError as e:
            Logger.error(f"❌ Force squash failed: {e}")
            return False


def main():
    """Command line interface"""
    if len(sys.argv) < 2:
        print("Usage: python3 intelligent_squash.py <pr_number> [--dry-run]")
        sys.exit(1)
    
    pr_number = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    
    # Determine Spring AI directory (same as pr_workflow.py)
    script_dir = Path(__file__).parent
    spring_ai_dir = script_dir / "spring-ai"
    
    if not spring_ai_dir.exists():
        Logger.error(f"Spring AI directory not found: {spring_ai_dir}")
        Logger.error("Please ensure the Spring AI repository is cloned")
        sys.exit(1)
    
    squasher = IntelligentSquash(spring_ai_dir)
    success = squasher.squash_pr(pr_number, dry_run)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
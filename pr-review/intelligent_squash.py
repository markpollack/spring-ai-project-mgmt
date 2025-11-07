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
    
    def get_pr_info(self, pr_number: str) -> Tuple[str, str, List[dict], str]:
        """Get PR information from GitHub API

        Returns:
            Tuple of (github_base_sha, github_head_sha, commits, title)
        """
        Logger.info("📋 Fetching PR information from GitHub...")

        result = self.run_gh([
            "pr", "view", pr_number, "--repo", self.spring_ai_repo,
            "--json", "baseRefOid,headRefOid,commits,title"
        ])

        pr_data = json.loads(result.stdout)
        github_base_sha = pr_data["baseRefOid"]
        github_head_sha = pr_data["headRefOid"]
        commits = pr_data["commits"]
        title = pr_data["title"]

        Logger.info(f"PR Title: {title}")
        Logger.info(f"GitHub base (current target branch): {github_base_sha[:8]}")
        Logger.info(f"GitHub head (PR branch tip): {github_head_sha[:8]}")
        Logger.info(f"Total commits in PR: {len(commits)}")

        return github_base_sha, github_head_sha, commits, title
    
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
    
    def extract_dco_signatures(self, base_sha: str) -> str:
        """Extract all unique Signed-off-by lines from commits being squashed"""
        try:
            # Get all commit messages from base to HEAD
            result = self.run_git(["log", "--format=%B", f"{base_sha}..HEAD"])
            commit_messages = result.stdout
            
            signed_off_lines = set()
            for line in commit_messages.split('\n'):
                line = line.strip()
                if line.startswith('Signed-off-by:'):
                    signed_off_lines.add(line)
            
            if signed_off_lines:
                Logger.info(f"🔏 Found {len(signed_off_lines)} DCO signature(s) to preserve")
                for sig in signed_off_lines:
                    Logger.info(f"   {sig}")
                return '\n'.join(sorted(signed_off_lines))
            else:
                Logger.info("ℹ️  No DCO signatures found in commits")
                return ""
                
        except subprocess.CalledProcessError as e:
            Logger.warn(f"⚠️  Could not extract DCO signatures: {e}")
            return ""

    def build_squash_commit_message(self, pr_number: str, title: str, commits: List[dict]) -> str:
        """Build comprehensive commit message with all PR commit details"""
        commit_count = len(commits)

        # Start with PR title
        message_lines = [title, ""]

        # Add commit details if there are multiple commits
        if commit_count > 1:
            message_lines.append(f"Squashed {commit_count} commits from PR #{pr_number}:")
            message_lines.append("")

            # Add each commit's message
            for commit in commits:
                oid_short = commit['oid'][:8]
                headline = commit.get('messageHeadline', '(no message)')
                message_lines.append(f"- {oid_short}: {headline}")

                # Add commit body if present and not empty
                body = commit.get('messageBody', '').strip()
                if body:
                    # Indent body lines
                    for line in body.split('\n'):
                        if line.strip():
                            message_lines.append(f"  {line}")

            message_lines.append("")
        else:
            message_lines.append(f"From PR #{pr_number}")
            message_lines.append("")

        # Extract and add DCO signatures
        try:
            dco_signatures = set()
            for commit in commits:
                message_body = commit.get('messageBody', '')
                for line in message_body.split('\n'):
                    line = line.strip()
                    if line.startswith('Signed-off-by:'):
                        dco_signatures.add(line)

            if dco_signatures:
                for sig in sorted(dco_signatures):
                    message_lines.append(sig)
        except Exception as e:
            Logger.warn(f"⚠️  Could not extract DCO signatures from commit messages: {e}")

        return '\n'.join(message_lines)

    def squash_with_patch(self, pr_number: str, github_base_sha: str, github_head_sha: str,
                          title: str, commits: List[dict]) -> bool:
        """Create clean squashed commit using patch from GitHub base to head

        This approach:
        1. Creates a patch of ONLY the PR's actual changes (GitHub base -> head)
        2. Resets to current origin/main
        3. Applies the patch
        4. Creates a single commit with comprehensive message including all commit details

        Benefits:
        - No conflicts during squash (we're applying a clean patch)
        - Fast (single patch operation, no multi-commit rebase)
        - Gets only PR changes, not old file versions from outdated branch
        - Preserves full commit history in message
        """
        Logger.info("🔄 Using patch-based squash (conflict-free)")
        Logger.info(f"📊 Extracting changes from {len(commits)} commits")

        try:
            # Step 1: Fetch the actual PR head commit from GitHub
            Logger.info(f"📥 Fetching PR head commit: {github_head_sha[:8]}")
            self.run_git(["fetch", "origin", github_head_sha])

            # Step 2: Create a patch of ONLY the PR's changes
            Logger.info(f"📄 Creating patch: {github_base_sha[:8]}..{github_head_sha[:8]}")
            patch_result = self.run_git([
                "diff", f"{github_base_sha}..{github_head_sha}"
            ])
            patch_content = patch_result.stdout

            if not patch_content.strip():
                Logger.warn("⚠️  Patch is empty - no changes to apply")
                return False

            # Log patch stats
            lines = patch_content.split('\n')
            files_changed = len([l for l in lines if l.startswith('diff --git')])
            Logger.info(f"📋 Patch affects {files_changed} file(s)")

            # Step 3: Reset to current origin/main
            Logger.info("🔄 Resetting to current origin/main")
            self.run_git(["fetch", "origin", "main:refs/remotes/origin/main"])
            self.run_git(["reset", "--hard", "origin/main"])

            # Step 4: Apply the patch
            Logger.info("📝 Applying PR changes...")

            # Write patch to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
                patch_file = f.name
                f.write(patch_content)

            try:
                # Apply patch
                self.run_git(["apply", "--index", patch_file])
                Logger.success("✅ Patch applied successfully")
            finally:
                # Clean up temp file
                os.unlink(patch_file)

            # Step 5: Create comprehensive commit message
            commit_message = self.build_squash_commit_message(pr_number, title, commits)

            # Step 6: Commit the changes
            Logger.info("📝 Creating squashed commit...")

            # Write commit message to temp file for proper multi-line handling
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                msg_file = f.name
                f.write(commit_message)

            try:
                self.run_git(["commit", "-F", msg_file])
                Logger.success(f"✅ Created squashed commit with {len(commits)} commit details")
            finally:
                os.unlink(msg_file)

            # Step 7: Verify the result
            result = self.run_git(["rev-list", "--count", "origin/main..HEAD"])
            commit_count = int(result.stdout.strip())

            if commit_count == 1:
                Logger.success("✅ Squash validation passed: exactly 1 commit created")

                # Show the commit
                self.run_git(["log", "-1", "--stat"])
                return True
            else:
                Logger.error(f"❌ Squash validation failed: expected 1 commit, found {commit_count}")
                return False

        except subprocess.CalledProcessError as e:
            Logger.error(f"❌ Patch-based squash failed: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                Logger.error(f"Error details: {e.stderr}")
            return False

    def choose_squash_strategy(self, pr_number: str, base_sha: str, commits: List[dict]) -> SquashStrategy:
        """Analyze PR and choose the best squashing strategy

        Strategy: Always use git reset --soft for squashing, regardless of merge commits.

        Rationale:
        - We're creating a single squashed commit, so merge history is irrelevant
        - reset --soft is instant and never causes conflicts during the squash operation
        - Conflicts will be resolved once during the subsequent rebase against main
        - This is 16x faster than interactive rebase for PRs with many commits
        """
        commits_count = len(commits)

        if commits_count <= 1:
            return SquashStrategy(
                method="none",
                reason="Only one commit in PR",
                commits_count=commits_count,
                has_merge_commits=False
            )

        # Always use reset_soft for squashing - it's fast and conflict-free
        # Conflicts will be resolved during the subsequent rebase against main
        merge_commits = self.detect_merge_commits(base_sha, commits)
        has_merge_commits = len(merge_commits) > 0

        if has_merge_commits:
            Logger.info(f"Found {len(merge_commits)} merge commit(s) - will be flattened during squash")

        return SquashStrategy(
            method="reset_soft",
            reason=f"Using git reset --soft for instant squash of {commits_count} commits",
            commits_count=commits_count,
            has_merge_commits=has_merge_commits,
            merge_commits=merge_commits if has_merge_commits else None
        )
    
    def squash_with_reset_soft(self, pr_number: str, base_sha: str, title: str, commits_count: int) -> bool:
        """Simple squash using git reset --soft"""
        Logger.info("🔄 Using git reset --soft approach (conflict-free)")
        Logger.info(f"📊 Squashing {commits_count} commits into 1")

        try:
            # Step 1: Verify commit count before squashing
            result = self.run_git(["rev-list", "--count", f"{base_sha}..HEAD"])
            before_count = int(result.stdout.strip())
            Logger.info(f"📋 Commits before squash: {before_count}")

            if before_count != commits_count:
                Logger.warn(f"⚠️  Warning: Expected {commits_count} commits, found {before_count}")

            # Step 2: Extract DCO signatures before reset
            dco_signatures = self.extract_dco_signatures(base_sha)

            # Step 3: Reset to base commit keeping changes staged
            Logger.info(f"Resetting to base commit: {base_sha[:8]}")
            self.run_git(["reset", "--soft", base_sha])

            # Step 4: Create squashed commit with meaningful message and preserve DCO
            commit_message = f"{title}\n\nSquashed {commits_count} commits from PR #{pr_number}"
            if dco_signatures:
                commit_message += f"\n\n{dco_signatures}"

            Logger.info("Creating squashed commit...")
            self.run_git(["commit", "-m", commit_message])

            # Step 5: Verify exactly 1 commit exists after squashing
            result = self.run_git(["rev-list", "--count", f"{base_sha}..HEAD"])
            after_count = int(result.stdout.strip())

            if after_count != 1:
                Logger.error(f"❌ Squash validation failed: expected 1 commit, found {after_count}")
                return False

            # Step 6: Log success with commit details
            result = self.run_git(["log", "--oneline", "-1"])
            new_commit = result.stdout.strip()
            Logger.success(f"✅ Squash successful: {before_count} → 1 commit")
            Logger.success(f"   {new_commit}")

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
    
    def _handle_rebase_conflicts(self, pr_number: str, max_iterations: int = 5) -> bool:
        """Handle rebase conflicts using existing Claude Code AI infrastructure

        Args:
            pr_number: The PR number being processed
            max_iterations: Maximum number of conflict resolution iterations (default: 5)
                           Reduced from 10 since we now squash before rebasing, so conflicts
                           only appear during the final rebase, not during squashing.

        Returns:
            bool: True if all conflicts resolved successfully, False otherwise
        """
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            Logger.info(f"🧠 Conflict resolution iteration {iteration}/{max_iterations}")

            # Log initial rebase state
            self._log_rebase_state(f"iteration {iteration} - start")

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
                                return True  # Successfully completed rebase
                            except subprocess.CalledProcessError as e:
                                Logger.warn(f"⚠️  Rebase continue encountered issues (exit code {e.returncode})")
                                self._log_rebase_state("after failed rebase continue")

                                # Check if there are new conflicts in the next commit
                                status_result = self.run_git(["status", "--porcelain"], check=False)
                                conflicted_files = [line for line in status_result.stdout.split('\n')
                                                    if line.startswith(('UU ', 'AA ', 'DD '))]

                                if conflicted_files:
                                    Logger.info(f"🔄 Found {len(conflicted_files)} new conflicts in next commit - continuing resolution loop...")
                                    continue  # Loop back to resolve new conflicts
                                else:
                                    Logger.error(f"❌ Rebase continue failed without new conflicts - unknown error")
                                    return False
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

                                    # After rebase, check if we have multiple commits and need to squash
                                    try:
                                        # Get base SHA and count commits since base
                                        base_sha, _, _, _ = self.get_pr_info(pr_number)
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
                                    Logger.warn(f"⚠️  Rebase continue encountered issues (exit code {e.returncode}) (path 2)")
                                    self._log_rebase_state("after failed rebase continue (path 2)")

                                    # Check if there are new conflicts in the next commit
                                    status_result = self.run_git(["status", "--porcelain"], check=False)
                                    conflicted_files = [line for line in status_result.stdout.split('\n')
                                                        if line.startswith(('UU ', 'AA ', 'DD '))]

                                    if conflicted_files:
                                        Logger.info(f"🔄 Found {len(conflicted_files)} new conflicts in next commit - continuing resolution loop...")
                                        continue  # Loop back to resolve new conflicts
                                    else:
                                        Logger.error(f"❌ Rebase continue failed without new conflicts - unknown error")
                                        return False
                            else:
                                Logger.warn("⚠️  Rebase completed but may not have properly squashed commits")

                                # After rebase, check if we have multiple commits and need to squash
                                try:
                                    # Get base SHA and count commits since base
                                    base_sha, _, _, _ = self.get_pr_info(pr_number)
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
                        # Will exit loop and show manual intervention message

                except Exception as import_error:
                    Logger.warn(f"Could not import PR workflow system: {import_error}")
                    Logger.info("Falling back to basic conflict analysis...")

                # If we reach here in this iteration, resolution failed
                Logger.warn(f"⚠️  Iteration {iteration}/{max_iterations}: Manual intervention may be required")

                # Check if we should continue trying
                if iteration < max_iterations:
                    # Check if we still have conflicts to resolve
                    status_result = self.run_git(["status", "--porcelain"], check=False)
                    conflicted_files = [line for line in status_result.stdout.split('\n')
                                        if line.startswith(('UU ', 'AA ', 'DD '))]
                    if conflicted_files:
                        Logger.info(f"Still have {len(conflicted_files)} conflicts - will retry in next iteration")
                        continue

                # No more conflicts or max iterations reached - exit loop
                break

            except Exception as e:
                Logger.error(f"❌ Error analyzing conflicts in iteration {iteration}: {e}")
                # Continue to next iteration unless we've exhausted attempts
                if iteration < max_iterations:
                    Logger.info(f"Will retry in next iteration ({iteration + 1}/{max_iterations})")
                    continue
                else:
                    break

        # If we exit the loop without returning, show manual intervention message
        Logger.warn("⚠️  Manual intervention required for remaining conflicts")
        Logger.info("💡 Next steps:")
        Logger.info("   1. Review the conflict resolution plan")
        Logger.info("   2. Use existing conflict resolution tools:")
        Logger.info("      ./resolve-conflicts.sh 3386")
        Logger.info("   3. Or resolve manually and run: git add . && git rebase --continue")

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
                
                # Debug: Check what git thinks about the current state
                try:
                    self._debug_git_state()
                except Exception as debug_error:
                    Logger.warn(f"Debug state check failed: {debug_error}")
                
                try:
                    self.run_git(["rebase", "--continue"])
                    Logger.success("✅ Rebase continued successfully")
                    return True
                except subprocess.CalledProcessError as continue_error:
                    Logger.warn(f"⚠️  Rebase --continue failed (exit code {continue_error.returncode}) - will try abort and restart")
                    try:
                        # Abort the problematic rebase
                        self.run_git(["rebase", "--abort"])
                        Logger.info("✅ Aborted stuck rebase, starting fresh squash...")
                        
                        # Start fresh squash process
                        base_sha, _, commits, title = self.get_pr_info(pr_number)
                        strategy = self.choose_squash_strategy(pr_number, base_sha, commits)
                        
                        if strategy.method == "reset_soft":
                            return self.squash_with_reset_soft(pr_number, base_sha, title, strategy.commits_count)
                        elif strategy.method == "interactive_rebase":
                            return self.squash_with_interactive_rebase(pr_number, base_sha, title, strategy.commits_count)
                        else:
                            Logger.error(f"❌ Unknown squash method after restart: {strategy.method}")
                            return False
                            
                    except subprocess.CalledProcessError as abort_error:
                        Logger.warn(f"⚠️  Standard rebase abort failed (exit code {abort_error.returncode}) - trying emergency cleanup")
                        Logger.info("🧹 Attempting alternative cleanup methods...")
                        if self._emergency_cleanup():
                            Logger.info("✅ Emergency cleanup successful, starting fresh squash...")
                            # Try to start fresh after cleanup
                            base_sha, _, commits, title = self.get_pr_info(pr_number)
                            strategy = self.choose_squash_strategy(pr_number, base_sha, commits)
                            
                            if strategy.method == "reset_soft":
                                return self.squash_with_reset_soft(pr_number, base_sha, title, strategy.commits_count)
                            elif strategy.method == "interactive_rebase":
                                return self.squash_with_interactive_rebase(pr_number, base_sha, title, strategy.commits_count)
                            else:
                                Logger.error(f"❌ Unknown squash method after cleanup: {strategy.method}")
                                return False
                        else:
                            Logger.error("❌ CRITICAL: All cleanup attempts failed - manual intervention required")
                            Logger.error("❌ Repository may be in an inconsistent state - check git status manually")
                            return False
                
        except subprocess.CalledProcessError as e:
            Logger.error(f"❌ Failed to handle existing rebase: {e}")
            return False
    
    def _debug_git_state(self):
        """Debug git state to understand rebase issues"""
        Logger.info("🔍 DEBUG: Current git state analysis:")
        
        try:
            # Check current branch/HEAD
            branch_result = self.run_git(["rev-parse", "--abbrev-ref", "HEAD"])
            Logger.info(f"   Current branch/HEAD: {branch_result.stdout.strip()}")
        except Exception as e:
            Logger.info(f"   Branch check failed: {e}")
        
        try:
            # Check if REBASE_HEAD exists and what commit it points to
            rebase_head = self.spring_ai_dir / ".git" / "REBASE_HEAD"
            if rebase_head.exists():
                with open(rebase_head, 'r') as f:
                    rebase_commit = f.read().strip()
                Logger.info(f"   REBASE_HEAD: {rebase_commit[:8]}")
            else:
                Logger.info("   REBASE_HEAD: not found")
        except Exception as e:
            Logger.info(f"   REBASE_HEAD check failed: {e}")
        
        try:
            # Check rebase state directories
            rebase_merge = self.spring_ai_dir / ".git" / "rebase-merge"
            rebase_apply = self.spring_ai_dir / ".git" / "rebase-apply"
            Logger.info(f"   rebase-merge exists: {rebase_merge.exists()}")
            Logger.info(f"   rebase-apply exists: {rebase_apply.exists()}")
        except Exception as e:
            Logger.info(f"   Rebase directory check failed: {e}")
        
        try:
            # Check index status
            status_result = self.run_git(["status", "--porcelain=v1"])
            status_lines = [line for line in status_result.stdout.strip().split('\n') if line]
            Logger.info(f"   Working directory status: {len(status_lines)} items")
            if status_lines and len(status_lines) <= 5:  # Show a few items
                for line in status_lines[:5]:
                    Logger.info(f"     {line}")
        except Exception as e:
            Logger.info(f"   Status check failed: {e}")
    
    def _emergency_cleanup(self) -> bool:
        """Emergency cleanup when standard git rebase --abort fails"""
        Logger.info("🚨 Performing emergency git state cleanup...")
        
        try:
            # Method 1: Try to reset HEAD to remove rebase state
            Logger.info("🔧 Attempting to reset HEAD to clear rebase state...")
            try:
                self.run_git(["reset", "--hard", "HEAD"])
                Logger.info("✅ HEAD reset successful")
            except subprocess.CalledProcessError:
                Logger.warn("⚠️  HEAD reset failed, trying alternative methods...")
            
            # Method 2: Remove rebase-related files manually
            Logger.info("🗑️  Removing rebase state files...")
            rebase_files = [
                self.spring_ai_dir / ".git" / "REBASE_HEAD",
                self.spring_ai_dir / ".git" / "rebase-merge",
                self.spring_ai_dir / ".git" / "rebase-apply"
            ]
            
            for file_path in rebase_files:
                try:
                    if file_path.exists():
                        if file_path.is_file():
                            file_path.unlink()
                            Logger.info(f"✅ Removed {file_path.name}")
                        elif file_path.is_dir():
                            import shutil
                            shutil.rmtree(file_path)
                            Logger.info(f"✅ Removed directory {file_path.name}")
                except Exception as e:
                    Logger.warn(f"Could not remove {file_path.name}: {e}")
            
            # Method 3: Verify we're back to a clean state
            try:
                status_result = self.run_git(["status", "--porcelain"])
                if not status_result.stdout.strip():
                    Logger.success("✅ Repository is now in a clean state")
                    return True
                else:
                    Logger.warn("⚠️  Repository still has uncommitted changes after cleanup")
                    # Try to clean working directory
                    self.run_git(["reset", "--hard"])
                    self.run_git(["clean", "-fd"])
                    Logger.info("✅ Performed hard reset and clean")
                    return True
            except subprocess.CalledProcessError as e:
                Logger.error(f"❌ Could not verify clean state: {e}")
                return False
            
        except Exception as e:
            Logger.error(f"❌ Emergency cleanup failed: {e}")
            return False
    
    # Note: Removed duplicate conflict resolution methods - now using existing PR workflow system
    
    def squash_pr(self, pr_number: str, dry_run: bool = False) -> bool:
        """Main entry point for intelligent PR squashing"""
        Logger.info(f"🚀 Starting intelligent squash for PR #{pr_number}")
        
        if dry_run:
            Logger.info("🔍 DRY RUN MODE - no changes will be made")
        
        try:
            # Critical: Validate we're on the correct PR branch before proceeding
            current_branch = self.run_git(["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
            if current_branch == "main" or current_branch == "master":
                Logger.error("❌ CRITICAL: Cannot run squash on main/master branch!")
                Logger.error("❌ Please checkout the PR branch first using the main workflow")
                Logger.error("❌ Use: python3 pr_workflow.py --cleanup 3914 && python3 pr_workflow.py 3914")
                return False
            
            Logger.info(f"📋 Operating on branch: {current_branch}")
            
            # Check if we're already in the middle of a rebase
            rebase_head_path = self.spring_ai_dir / ".git" / "REBASE_HEAD"
            Logger.info(f"🔍 Checking for existing rebase at: {rebase_head_path}")
            if rebase_head_path.exists():
                Logger.info("🔄 Detected existing rebase in progress, attempting to continue...")
                return self._handle_existing_rebase(pr_number)
            
            # Step 1: Get PR information from GitHub
            github_base_sha, github_head_sha, commits, title = self.get_pr_info(pr_number)

            # Check if squashing is needed
            if len(commits) <= 1:
                Logger.info("✅ Only one commit in PR - no squashing needed")
                return True

            if dry_run:
                Logger.info(f"[DRY RUN] Would squash {len(commits)} commits using patch-based approach")
                Logger.info(f"[DRY RUN] Patch: {github_base_sha[:8]}..{github_head_sha[:8]}")
                return True

            # Step 2: Use patch-based squash (fast, conflict-free, preserves commit history)
            return self.squash_with_patch(pr_number, github_base_sha, github_head_sha, title, commits)
                
        except Exception as e:
            Logger.error(f"❌ Squash failed with error: {e}")
            return False
    
    def _force_squash_commits(self, pr_number: str, commit_count: int) -> bool:
        """Force squash multiple commits into a single commit using reset --soft"""
        Logger.info(f"🔄 Force squashing {commit_count} commits into single commit")
        
        try:
            # Get the base SHA from the PR info
            base_sha, _, commits_data, title = self.get_pr_info(pr_number)
            
            # Extract DCO signatures before reset
            dco_signatures = self.extract_dco_signatures(base_sha)
            
            # Reset to base commit keeping all changes staged
            Logger.info(f"Resetting to base commit: {base_sha[:8]} while preserving changes")
            self.run_git(["reset", "--soft", base_sha])
            
            # Create single squashed commit with DCO preservation
            commit_message = f"{title}\n\nSquashed {commit_count} commits from PR #{pr_number} after conflict resolution"
            if dco_signatures:
                commit_message += f"\n\n{dco_signatures}"
            
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
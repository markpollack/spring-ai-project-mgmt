#!/usr/bin/env python3
"""
Spring AI start.spring.io Update Script

Standalone script for updating start.spring.io (Spring Initializr) with new Spring AI releases.
This script handles step 14 of the Spring AI patch release process.

Usage:
    python3 update-start-spring-io.py 1.0.1 --dry-run
    python3 update-start-spring-io.py 1.0.1 --cleanup
"""

import os
import sys
import subprocess
import argparse
import shutil
import re
from pathlib import Path
from typing import Optional, Tuple


class Colors:
    """ANSI color codes"""
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


class StartSpringIOUpdater:
    """Update start.spring.io with new Spring AI releases"""
    
    def __init__(self, version: str, dry_run: bool = False):
        self.version = version
        self.dry_run = dry_run
        self.script_dir = Path(__file__).parent
        self.upstream_repo = "spring-io/start.spring.io"
        self.fork_repo = "markpollack/start.spring.io"  # Your fork
        self.fork_url = f"https://github.com/{self.fork_repo}.git"
        self.repo_dir = self.script_dir / "start-spring-io"
        self.application_yml = self.repo_dir / "start-site" / "src" / "main" / "resources" / "application.yml"
        self.branch_name = f"update-spring-ai-{version}"
    
    def validate_version(self) -> bool:
        """Validate version format"""
        if not re.match(r'^\d+\.\d+\.\d+$', self.version):
            Logger.error(f"Invalid version format: {self.version}. Expected X.Y.Z format.")
            return False
        return True
    
    def check_github_cli(self) -> bool:
        """Check if GitHub CLI is available and authenticated"""
        try:
            result = subprocess.run(["gh", "auth", "status"], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                Logger.info("✅ GitHub CLI is available and authenticated")
                return True
            else:
                Logger.error("❌ GitHub CLI authentication required. Run: gh auth login")
                return False
        except FileNotFoundError:
            Logger.error("❌ GitHub CLI not found. Please install gh CLI")
            return False
    
    def show_spring_ai_section(self) -> bool:
        """Show the spring-ai section for debugging purposes"""
        try:
            if self.dry_run:
                Logger.warn("DRY RUN: Would show spring-ai section")
                return True
                
            with open(self.application_yml, 'r') as f:
                lines = f.readlines()
            
            # Find the spring-ai section
            start_idx = -1
            for i, line in enumerate(lines):
                if 'spring-ai:' in line and not line.strip().startswith('#'):
                    start_idx = i
                    break
            
            if start_idx == -1:
                Logger.error("Could not find spring-ai section")
                return False
            
            # Show context around spring-ai section
            Logger.info(f"Spring AI section found at line {start_idx + 1}:")
            start = max(0, start_idx - 2)
            end = min(len(lines), start_idx + 15)  # Show ~15 lines after spring-ai
            
            for i in range(start, end):
                prefix = ">>>" if i == start_idx else "   "
                Logger.info(f"{prefix} {i+1:3d}: {lines[i].rstrip()}")
            
            return True
        except Exception as e:
            Logger.error(f"Error showing spring-ai section: {e}")
            return False
    
    def cleanup_repository(self) -> bool:
        """Remove the cloned repository"""
        try:
            if self.repo_dir.exists():
                Logger.info(f"🧹 Cleaning up repository: {self.repo_dir}")
                if not self.dry_run:
                    shutil.rmtree(self.repo_dir)
                Logger.success("Cleanup completed")
            else:
                Logger.info("No repository directory to clean up")
            return True
        except Exception as e:
            Logger.error(f"Error cleaning up repository: {e}")
            return False
    
    def confirm_action(self, message: str) -> bool:
        """Ask for user confirmation"""
        if self.dry_run:
            Logger.warn(f"DRY RUN: Would ask - {message}")
            return True
        
        response = input(f"\n{Colors.YELLOW}{message} (Y/n): {Colors.NC}").strip().lower()
        return response in ['', 'y', 'yes']
    
    def clone_repository(self) -> bool:
        """Clone fork and set up upstream remote"""
        try:
            # Remove existing directory if it exists
            if self.repo_dir.exists():
                Logger.info(f"Removing existing directory: {self.repo_dir}")
                if not self.dry_run:
                    shutil.rmtree(self.repo_dir)
            
            Logger.step(f"Cloning fork {self.fork_repo} to {self.repo_dir}")
            
            if not self.confirm_action("Proceed with cloning fork?"):
                Logger.info("Repository clone cancelled by user")
                return False
            
            if self.dry_run:
                Logger.warn("DRY RUN: Would clone fork and set up upstream")
                return True
            
            # Clone your fork
            subprocess.run([
                "git", "clone", self.fork_url, str(self.repo_dir)
            ], check=True, capture_output=True, text=True)
            
            # Add upstream remote
            subprocess.run([
                "git", "-C", str(self.repo_dir), "remote", "add", "upstream", 
                f"https://github.com/{self.upstream_repo}.git"
            ], check=True, capture_output=True, text=True)
            
            Logger.success("Fork cloned and upstream remote added")
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to clone repository: {e}")
            return False
    
    def sync_fork_with_upstream(self) -> bool:
        """Sync fork with latest upstream changes"""
        try:
            Logger.step("Syncing fork with upstream changes")
            
            if not self.confirm_action("Fetch and sync with upstream main branch?"):
                Logger.info("Fork sync cancelled by user")
                return False
            
            if self.dry_run:
                Logger.warn("DRY RUN: Would sync fork with upstream")
                return True
            
            # Fetch upstream changes
            subprocess.run([
                "git", "-C", str(self.repo_dir), "fetch", "upstream"
            ], check=True, capture_output=True, text=True)
            
            # Checkout main and merge upstream changes
            subprocess.run([
                "git", "-C", str(self.repo_dir), "checkout", "main"
            ], check=True, capture_output=True, text=True)
            
            subprocess.run([
                "git", "-C", str(self.repo_dir), "merge", "upstream/main"
            ], check=True, capture_output=True, text=True)
            
            # Push updated main to your fork
            subprocess.run([
                "git", "-C", str(self.repo_dir), "push", "origin", "main"
            ], check=True, capture_output=True, text=True)
            
            Logger.success("Fork synced with upstream successfully")
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to sync fork with upstream: {e}")
            return False
    
    def create_feature_branch(self) -> bool:
        """Create feature branch for the update"""
        try:
            Logger.step(f"Creating feature branch: {self.branch_name}")
            
            if not self.confirm_action(f"Create feature branch '{self.branch_name}'?"):
                Logger.info("Feature branch creation cancelled by user")
                return False
            
            if self.dry_run:
                Logger.warn("DRY RUN: Would create feature branch")
                return True
            
            subprocess.run([
                "git", "-C", str(self.repo_dir), "checkout", "-b", self.branch_name
            ], check=True, capture_output=True, text=True)
            
            Logger.success("Feature branch created successfully")
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to create feature branch: {e}")
            return False
    
    def find_current_version(self) -> str:
        """Find current Spring AI version in BOM mappings section of application.yml"""
        try:
            if self.dry_run:
                Logger.warn("DRY RUN: Would read current version from application.yml")
                return "1.0.0"  # Mock version for dry run
            
            with open(self.application_yml, 'r') as f:
                content = f.read()
            
            # Look for spring-ai BOM section with specific mappings structure
            # More flexible pattern for whitespace variations
            pattern = r'spring-ai:\s*\r?\n\s*groupId:\s*org\.springframework\.ai\s*\r?\n\s*artifactId:\s*spring-ai-bom.*?mappings:\s*\r?\n\s*-\s*compatibilityRange:.*?\r?\n\s*version:\s*([0-9]+\.[0-9]+\.[0-9]+)'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                version = match.group(1)
                Logger.info(f"Found current Spring AI BOM version: {version}")
                return version
            else:
                Logger.error("Could not find Spring AI BOM version in mappings section of application.yml")
                Logger.info("Searching for the spring-ai section in the file...")
                
                # Fallback: show what we can find for debugging
                fallback_pattern = r'spring-ai:'
                if re.search(fallback_pattern, content):
                    Logger.info("Found spring-ai section but couldn't locate BOM version mapping")
                else:
                    Logger.error("spring-ai section not found in file")
                return ""
        except Exception as e:
            Logger.error(f"Error reading application.yml: {e}")
            return ""
    
    def update_spring_ai_version(self) -> Tuple[bool, str]:
        """Update Spring AI version in application.yml"""
        try:
            current_version = self.find_current_version()
            if not current_version:
                return False, ""
            
            if current_version == self.version:
                Logger.warn(f"Version {self.version} is already set in application.yml")
                return False, current_version
            
            Logger.step(f"Updating Spring AI version: {current_version} → {self.version}")
            
            if not self.confirm_action(f"Update version from {current_version} to {self.version}?"):
                Logger.info("Version update cancelled by user")
                return False, current_version
            
            if self.dry_run:
                Logger.warn("DRY RUN: Would update version in application.yml")
                return True, current_version
            
            with open(self.application_yml, 'r') as f:
                content = f.read()
            
            # Replace the version in spring-ai BOM mappings section specifically
            # More flexible pattern for whitespace variations
            pattern = r'(spring-ai:\s*\r?\n\s*groupId:\s*org\.springframework\.ai\s*\r?\n\s*artifactId:\s*spring-ai-bom.*?mappings:\s*\r?\n\s*-\s*compatibilityRange:.*?\r?\n\s*version:\s*)([0-9]+\.[0-9]+\.[0-9]+)'
            new_content = re.sub(pattern, f'\\g<1>{self.version}', content, flags=re.DOTALL)
            
            if content == new_content:
                Logger.error("Version replacement failed - no changes made to spring-ai BOM mapping")
                Logger.info("This could indicate the pattern didn't match the expected structure")
                return False, current_version
            
            with open(self.application_yml, 'w') as f:
                f.write(new_content)
            
            Logger.success("Version updated successfully")
            return True, current_version
        except Exception as e:
            Logger.error(f"Error updating application.yml: {e}")
            return False, ""
    
    def show_changes_preview(self, old_version: str) -> bool:
        """Show diff of changes for user review"""
        try:
            Logger.bold("\n" + "="*60)
            Logger.bold("📋 CHANGES PREVIEW")
            Logger.bold("="*60)
            
            if self.dry_run:
                Logger.warn("DRY RUN: Would show git diff")
                print(f"{Colors.CYAN}File: application.yml{Colors.NC}")
                print(f"{Colors.GREEN}+            version: {self.version}{Colors.NC}")
                print(f"{Colors.RED}-            version: {old_version}{Colors.NC}")
            else:
                # Show git diff
                result = subprocess.run([
                    "git", "-C", str(self.repo_dir), "diff", "start-site/src/main/resources/application.yml"
                ], capture_output=True, text=True)
                
                if result.stdout:
                    print(f"{Colors.CYAN}File: application.yml{Colors.NC}")
                    print(result.stdout)
            
            # Show commit and PR details
            commit_msg = f"Update Spring AI to {self.version}"
            pr_title = f"Update Spring AI to {self.version}"
            pr_body = f"""Updates Spring AI BOM version to {self.version} for compatibility with latest patch release.

- Updated spring-ai version mapping from {old_version} to {self.version}
- Maintains compatibility range [3.4.0,4.0.0-M1)

This change makes Spring AI {self.version} available in Spring Initializr for new projects."""
            
            print(f"\n{Colors.GREEN}🔍 Full Commit Message (with DCO sign-off):{Colors.NC}")
            print(f"{Colors.CYAN}{commit_msg}{Colors.NC}")
            print(f"{Colors.YELLOW}Signed-off-by: Mark Pollack <mark.pollack@broadcom.com>{Colors.NC}")
            
            print(f"\n{Colors.GREEN}🎯 PR Title:{Colors.NC}")
            print(f"{Colors.CYAN}{pr_title}{Colors.NC}")
            
            print(f"\n{Colors.GREEN}📝 PR Body:{Colors.NC}")
            print(f"{Colors.CYAN}{pr_body}{Colors.NC}")
            
            Logger.bold("="*60)
            
            return True
        except Exception as e:
            Logger.error(f"Error showing changes preview: {e}")
            return False
    
    def commit_changes(self) -> bool:
        """Commit the version update with DCO sign-off"""
        try:
            commit_msg = f"Update Spring AI to {self.version}"
            
            Logger.step(f"Committing changes with DCO sign-off: {commit_msg}")
            
            if not self.confirm_action("Commit the changes (with DCO sign-off)?"):
                Logger.info("Commit cancelled by user")
                return False
            
            if self.dry_run:
                Logger.warn("DRY RUN: Would commit changes with DCO sign-off")
                return True
            
            # Ensure git user is configured for DCO
            subprocess.run([
                "git", "-C", str(self.repo_dir), "config", "user.name", "Mark Pollack"
            ], check=True, capture_output=True, text=True)
            
            subprocess.run([
                "git", "-C", str(self.repo_dir), "config", "user.email", "mark.pollack@broadcom.com"
            ], check=True, capture_output=True, text=True)
            
            subprocess.run([
                "git", "-C", str(self.repo_dir), "add", "start-site/src/main/resources/application.yml"
            ], check=True, capture_output=True, text=True)
            
            # Commit with DCO sign-off (-s flag)
            subprocess.run([
                "git", "-C", str(self.repo_dir), "commit", "-s", "-m", commit_msg
            ], check=True, capture_output=True, text=True)
            
            Logger.success("Changes committed successfully with DCO sign-off")
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to commit changes: {e}")
            return False
    
    def create_pull_request(self, old_version: str) -> bool:
        """Create pull request using GitHub CLI"""
        try:
            pr_title = f"Update Spring AI to {self.version}"
            pr_body = f"""Updates Spring AI BOM version to {self.version} for compatibility with latest patch release.

- Updated spring-ai version mapping from {old_version} to {self.version}
- Maintains compatibility range [3.4.0,4.0.0-M1)

This change makes Spring AI {self.version} available in Spring Initializr for new projects.

---
✅ **DCO Compliance**: All commits in this PR include the required `Signed-off-by` trailer for Developer Certificate of Origin compliance."""
            
            Logger.step("Creating pull request...")
            Logger.info(f"Title: {pr_title}")
            
            if not self.confirm_action("⚠️ FINAL CONFIRMATION: Create pull request on GitHub?"):
                Logger.info("Pull request creation cancelled by user")
                return False
            
            if self.dry_run:
                Logger.warn("DRY RUN: Would create pull request")
                Logger.info("DRY RUN: Would push branch and create PR")
                return True
            
            # Push branch first
            Logger.info(f"Pushing branch '{self.branch_name}' to origin...")
            subprocess.run([
                "git", "-C", str(self.repo_dir), "push", "-u", "origin", self.branch_name
            ], check=True, capture_output=True, text=True)
            
            # Create PR from your fork to upstream
            Logger.info("Creating pull request from fork to upstream...")
            result = subprocess.run([
                "gh", "pr", "create",
                "--repo", self.upstream_repo,
                "--title", pr_title,
                "--body", pr_body,
                "--head", f"{self.fork_repo.split('/')[0]}:{self.branch_name}",  # markpollack:update-spring-ai-1.0.1
                "--base", "main"
            ], cwd=str(self.repo_dir), check=True, capture_output=True, text=True)
            
            if result.stdout:
                Logger.success("Pull request created successfully!")
                Logger.info(f"PR URL: {result.stdout.strip()}")
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to create pull request: {e}")
            if e.stderr:
                Logger.error(f"Error details: {e.stderr}")
            return False
    
    def run_update(self) -> bool:
        """Run the complete update workflow"""
        try:
            Logger.bold("\n" + "="*60)
            Logger.bold("🚀 SPRING AI START.SPRING.IO UPDATE")
            Logger.bold("="*60)
            Logger.info(f"Target Version: {self.version}")
            Logger.info(f"Fork: {self.fork_repo}")
            Logger.info(f"Upstream: {self.upstream_repo}")
            Logger.info(f"Dry Run: {self.dry_run}")
            Logger.bold("="*60)
            
            # Validation
            if not self.validate_version():
                return False
            
            if not self.dry_run and not self.check_github_cli():
                return False
            
            # Clone repository
            if not self.clone_repository():
                return False
            
            # Sync fork with upstream
            if not self.sync_fork_with_upstream():
                return False
            
            # Create feature branch
            if not self.create_feature_branch():
                return False
            
            # Update version and get old version
            success, old_version = self.update_spring_ai_version()
            if not success:
                if old_version == self.version:
                    Logger.info("Version already up to date - no changes needed")
                    return True
                    
                # Show debugging info when version update fails
                Logger.warn("Version update failed. Showing spring-ai section for debugging:")
                self.show_spring_ai_section()
                return False
            
            # Show changes preview
            if not self.show_changes_preview(old_version):
                return False
            
            if not self.confirm_action("Proceed with the changes shown above?"):
                Logger.info("Update process cancelled by user")
                return False
            
            # Commit changes
            if not self.commit_changes():
                return False
            
            # Create pull request
            if not self.create_pull_request(old_version):
                return False
            
            Logger.bold("\n🎉 start.spring.io update completed successfully!")
            Logger.info("The pull request has been created and is ready for review.")
            
            return True
            
        except KeyboardInterrupt:
            Logger.warn("\nOperation cancelled by user (Ctrl+C)")
            return False
        except Exception as e:
            Logger.error(f"Unexpected error during update: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Update start.spring.io with new Spring AI release",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 update-start-spring-io.py 1.0.1 --dry-run
  python3 update-start-spring-io.py 1.0.1
  python3 update-start-spring-io.py 1.0.1 --cleanup
        """
    )
    
    parser.add_argument('version', help='Spring AI version to update to (e.g., 1.0.1)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without making them')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up repository directory and exit')
    parser.add_argument('--test-pattern', action='store_true',
                       help='Test the regex pattern against existing repository (debug mode)')
    parser.add_argument('--fresh-start', action='store_true',
                       help='Clean up and start completely fresh (cleanup + full run)')
    
    args = parser.parse_args()
    
    updater = StartSpringIOUpdater(args.version, args.dry_run)
    
    if args.cleanup:
        Logger.info("Cleaning up repository...")
        success = updater.cleanup_repository()
        sys.exit(0 if success else 1)
    
    if args.test_pattern:
        Logger.info("Testing regex pattern against existing repository...")
        # Clone repository if needed
        if not updater.repo_dir.exists():
            if not updater.clone_repository():
                sys.exit(1)
        
        # Test pattern
        current_version = updater.find_current_version()
        if current_version:
            Logger.success(f"✅ Pattern test successful! Found version: {current_version}")
            updater.show_spring_ai_section()
        else:
            Logger.error("❌ Pattern test failed!")
            updater.show_spring_ai_section()
        
        sys.exit(0 if current_version else 1)
    
    if args.fresh_start:
        Logger.info("🔄 Fresh start requested - cleaning up and running full update...")
        # Clean up first
        updater.cleanup_repository()
        Logger.success("Cleanup completed, starting fresh update...")
    
    # Run the update
    success = updater.run_update()
    
    # Always cleanup on completion
    updater.cleanup_repository()
    
    if success:
        Logger.bold("\n✅ Update completed successfully!")
        sys.exit(0)
    else:
        Logger.bold("\n❌ Update failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
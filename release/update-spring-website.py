#!/usr/bin/env python3
"""
Spring AI spring-website-content Update Script

Standalone script for updating spring-website-content with new Spring AI documentation.
This script handles step 15 of the Spring AI patch release process.

Usage:
    python3 update-spring-website.py 1.0.1 --dry-run
    python3 update-spring-website.py 1.0.1 --cleanup
"""

import os
import sys
import subprocess
import argparse
import shutil
import re
import json
from pathlib import Path
from typing import Optional


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


class SpringWebsiteUpdater:
    """Update spring-website-content with new Spring AI documentation"""
    
    def __init__(self, version: str, dry_run: bool = False):
        self.version = version
        self.dry_run = dry_run
        self.script_dir = Path(__file__).parent
        self.repo_url = "https://github.com/spring-io/spring-website-content.git"
        self.repo_dir = self.script_dir / "spring-website-content"
        self.branch_name = f"update-spring-ai-{version}"
        self.doc_file = self.repo_dir / "project" / "spring-ai" / "documentation.json"
    
    def validate_version(self) -> bool:
        """Validate version format - supports both patch (X.Y.Z) and milestone (X.Y.Z-M1) versions"""
        # Accept patch versions (1.0.1) and milestone versions (1.1.0-M1, 1.1.0-RC1)
        patch_pattern = r'^\d+\.\d+\.\d+$'
        milestone_pattern = r'^\d+\.\d+\.\d+-(M\d+|RC\d+|SNAPSHOT)$'
        
        if re.match(patch_pattern, self.version) or re.match(milestone_pattern, self.version):
            return True
        else:
            Logger.error(f"Invalid version format: {self.version}. Expected X.Y.Z or X.Y.Z-M1/RC1 format.")
            return False
    
    def is_milestone_release(self) -> bool:
        """Check if this is a milestone/prerelease version"""
        return re.match(r'^\d+\.\d+\.\d+-(M\d+|RC\d+|SNAPSHOT)$', self.version) is not None
    
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
        """Clone spring-website-content repository"""
        try:
            # Remove existing directory if it exists
            if self.repo_dir.exists():
                Logger.info(f"Removing existing directory: {self.repo_dir}")
                if not self.dry_run:
                    shutil.rmtree(self.repo_dir)
            
            Logger.step(f"Cloning spring-website-content repository to {self.repo_dir}")
            
            if not self.confirm_action("Proceed with cloning repository?"):
                Logger.info("Repository clone cancelled by user")
                return False
            
            if self.dry_run:
                Logger.warn("DRY RUN: Would clone repository")
                return True
            
            subprocess.run([
                "git", "clone", self.repo_url, str(self.repo_dir)
            ], check=True, capture_output=True, text=True)
            
            Logger.success("Repository cloned successfully")
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to clone repository: {e}")
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
    
    def _dry_run_clone_for_version(self) -> bool:
        """Temporary clone in dry-run mode just to read current version"""
        try:
            # Quick clone just to read the file
            subprocess.run([
                "git", "clone", "--depth", "1", self.repo_url, str(self.repo_dir)
            ], check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def update_documentation_json(self) -> tuple[bool, str]:
        """Update documentation.json array for patch or milestone release"""
        try:
            if not self.doc_file.exists():
                if self.dry_run:
                    Logger.warn("DRY RUN: Cloning repository temporarily to read current version")
                    if not self._dry_run_clone_for_version():
                        Logger.warn("DRY RUN: Failed to clone, using mock version 1.0.0")
                        return True, "1.0.0"  # Mock old version for dry run
                else:
                    Logger.error(f"Documentation file not found: {self.doc_file}")
                    return False, ""
            
            Logger.step("Reading documentation.json array...")
            
            if self.dry_run:
                Logger.warn("DRY RUN: Reading actual current version from documentation.json")
                # Even in dry run, read the actual current version for accuracy
                if not self.doc_file.exists():
                    Logger.warn("DRY RUN: documentation.json not found, using mock version 1.0.1")
                    old_version = "1.0.1"  # Mock current GA version if file doesn't exist
                else:
                    # Read actual version from file
                    with open(self.doc_file, 'r') as f:
                        data = json.load(f)
                    
                    # Find current GA version
                    old_version = "1.0.1"  # Fallback
                    for entry in data:
                        if entry.get("status") == "GENERAL_AVAILABILITY" and entry.get("current") == True:
                            old_version = entry["version"]
                            break
                if self.is_milestone_release():
                    Logger.info(f"DRY RUN: Current GA version: {old_version} (unchanged)")
                    Logger.info(f"DRY RUN: Adding milestone version: {self.version}")
                    Logger.info("DRY RUN: Would add new PRERELEASE entry without changing GA entry")
                    print(f"{Colors.CYAN}DRY RUN: New entry would be added:{Colors.NC}")
                    print(f'{Colors.GREEN}+  {{{Colors.NC}')
                    print(f'{Colors.GREEN}+    "version": "{self.version}",{Colors.NC}')
                    print(f'{Colors.GREEN}+    "antora": false,{Colors.NC}')
                    print(f'{Colors.GREEN}+    "api": "https://docs.spring.io/spring-ai/docs/{self.version}/api/",{Colors.NC}')
                    print(f'{Colors.GREEN}+    "ref": "https://docs.spring.io/spring-ai/reference/{self.version}/index.html",{Colors.NC}')
                    print(f'{Colors.GREEN}+    "status": "PRERELEASE",{Colors.NC}')
                    print(f'{Colors.GREEN}+    "current": false{Colors.NC}')
                    print(f'{Colors.GREEN}+  }},{Colors.NC}')
                else:
                    Logger.info(f"DRY RUN: Current GA version: {old_version}")
                    Logger.info(f"DRY RUN: Target version: {self.version}")
                return True, old_version
            
            # Read current content - should be an array of version objects
            with open(self.doc_file, 'r') as f:
                doc_array = json.load(f)
            
            if not isinstance(doc_array, list):
                Logger.error("Documentation.json should contain an array of version objects")
                return False, ""
            
            if self.is_milestone_release():
                # For milestone releases: add new PRERELEASE entry
                return self._handle_milestone_release(doc_array)
            else:
                # For patch releases: update existing GA entry
                return self._handle_patch_release(doc_array)
                
        except json.JSONDecodeError as e:
            Logger.error(f"Invalid JSON in documentation.json: {e}")
            return False, ""
        except Exception as e:
            Logger.error(f"Error updating documentation.json: {e}")
            return False, ""
    
    def _handle_milestone_release(self, doc_array: list) -> tuple[bool, str]:
        """Handle milestone release by adding new PRERELEASE entry"""
        try:
            # Check if milestone version already exists
            for entry in doc_array:
                if entry.get('version') == self.version:
                    Logger.warn(f"Version {self.version} already exists in documentation.json")
                    return False, ""
            
            # Get current GA entry for reference
            ga_entry = None
            for entry in doc_array:
                if entry.get('status') == 'GENERAL_AVAILABILITY' and entry.get('current', False):
                    ga_entry = entry
                    break
            
            if not ga_entry:
                Logger.error("Could not find GENERAL_AVAILABILITY entry to use as reference")
                return False, ""
            
            old_version = ga_entry.get('version', '')
            Logger.info(f"Current GA version: {old_version}")
            Logger.info(f"Adding milestone version: {self.version}")
            
            # Create new PRERELEASE entry based on Spring Boot pattern
            # Extract major.minor for reference URL (1.1.0-M1 -> 1.1)
            version_parts = self.version.split('.')
            major_minor = f"{version_parts[0]}.{version_parts[1]}"
            
            milestone_entry = {
                "version": self.version,
                "antora": True,  # Spring AI uses Antora documentation
                "api": f"https://docs.spring.io/spring-ai/docs/{self.version}/api/",
                "ref": f"https://docs.spring.io/spring-ai/reference/{major_minor}/index.html",
                "status": "PRERELEASE", 
                "current": False
            }
            
            # Insert milestone entry after GA entry (following Spring Boot pattern)
            ga_index = -1
            for i, entry in enumerate(doc_array):
                if entry.get('status') == 'GENERAL_AVAILABILITY' and entry.get('current', False):
                    ga_index = i
                    break
            
            if ga_index == -1:
                Logger.error("Could not find GA entry index for insertion")
                return False, ""
            
            # Insert after GA entry
            doc_array.insert(ga_index + 1, milestone_entry)
            
            # Show preview
            Logger.bold("\n" + "="*60)
            Logger.bold("📋 SPRING WEBSITE CHANGES PREVIEW")
            Logger.bold("="*60)
            Logger.info(f"File: {self.doc_file.relative_to(self.repo_dir)}")
            Logger.info(f"Adding new PRERELEASE entry:")
            Logger.info(f"  version: {self.version}")
            Logger.info(f"  antora: true (Spring AI uses Antora documentation)")
            Logger.info(f"  status: PRERELEASE")
            Logger.info(f"  api: {milestone_entry['api']}")
            Logger.info(f"  ref: {milestone_entry['ref']} (using major.minor: {major_minor})")
            Logger.info(f"  current: false")
            Logger.info(f"  position: after GA entry (index {ga_index + 1})")
            Logger.bold("="*60)
            
            if not self.confirm_action("Proceed with adding PRERELEASE entry?"):
                Logger.info("Milestone release update cancelled by user")
                return False, old_version
            
            # Write updated content
            with open(self.doc_file, 'w') as f:
                json.dump(doc_array, f, indent=2, ensure_ascii=False)
                f.write('\n')  # Add trailing newline
            
            Logger.success(f"PRERELEASE entry for {self.version} added successfully")
            return True, old_version
            
        except Exception as e:
            Logger.error(f"Error handling milestone release: {e}")
            return False, ""
    
    def _handle_patch_release(self, doc_array: list) -> tuple[bool, str]:
        """Handle patch release by updating existing GA entry"""
        try:
            # Find the GENERAL_AVAILABILITY entry (current stable release)
            ga_entry = None
            ga_index = -1
            for i, entry in enumerate(doc_array):
                if entry.get('status') == 'GENERAL_AVAILABILITY' and entry.get('current', False):
                    ga_entry = entry
                    ga_index = i
                    break
            
            if not ga_entry:
                Logger.error("Could not find GENERAL_AVAILABILITY entry with current=true")
                return False, ""
            
            old_version = ga_entry.get('version', '')
            Logger.info(f"Current GA version: {old_version}")
            Logger.info(f"Target version: {self.version}")
            
            # Check if already updated
            if old_version == self.version:
                Logger.warn(f"Documentation already shows version {self.version}")
                return False, old_version
            
            # Update the GA entry
            old_api_url = ga_entry.get('api', '')
            old_ref_url = ga_entry.get('ref', '')
            
            # Update version
            doc_array[ga_index]['version'] = self.version
            
            # Update API URL (patch release specific)
            if old_api_url:
                new_api_url = old_api_url.replace(f"/{old_version}/", f"/{self.version}/")
                doc_array[ga_index]['api'] = new_api_url
                Logger.info(f"API URL updated: {old_api_url} → {new_api_url}")
            
            # Show preview
            Logger.bold("\n" + "="*60)
            Logger.bold("📋 SPRING WEBSITE CHANGES PREVIEW")
            Logger.bold("="*60)
            Logger.info(f"File: {self.doc_file.relative_to(self.repo_dir)}")
            Logger.info(f"Updating GENERAL_AVAILABILITY entry (index {ga_index}):")
            Logger.info(f"  version: {old_version} → {self.version}")
            if old_api_url:
                Logger.info(f"  api: {old_api_url} → {doc_array[ga_index]['api']}")
            if old_ref_url:
                Logger.info(f"  ref: {old_ref_url} (unchanged - stays at major.minor level)")
            Logger.bold("="*60)
            
            if not self.confirm_action("Proceed with GENERAL_AVAILABILITY update?"):
                Logger.info("Patch release update cancelled by user")
                return False, old_version
            
            # Write updated content
            with open(self.doc_file, 'w') as f:
                json.dump(doc_array, f, indent=2, ensure_ascii=False)
                f.write('\n')  # Add trailing newline
            
            Logger.success("GENERAL_AVAILABILITY entry updated successfully")
            return True, old_version
            
        except Exception as e:
            Logger.error(f"Error handling patch release: {e}")
            return False, ""
    
    def _show_json_diff(self, original_content: str, updated_content: str) -> None:
        """Show a visual diff of JSON changes"""
        try:
            print(f"{Colors.CYAN}File: project/spring-ai/documentation.json{Colors.NC}")
            
            # Split into lines for comparison
            original_lines = original_content.splitlines()
            updated_lines = updated_content.splitlines()
            
            # Find all differences and collect them
            changes = []
            for i, (orig_line, new_line) in enumerate(zip(original_lines, updated_lines)):
                if orig_line != new_line:
                    changes.append(i)
            
            if not changes:
                Logger.warn("No differences found in JSON content")
                return
            
            # Show a unified diff-style view with context
            print(f"{Colors.CYAN}@@ Showing all changes with context @@{Colors.NC}")
            
            # Find the range that covers all changes with context
            if changes:
                first_change = changes[0]
                last_change = changes[-1]
                start_idx = max(0, first_change - 3)
                end_idx = min(len(original_lines), last_change + 4)
                
                for i in range(start_idx, end_idx):
                    if i < len(original_lines):
                        if i in changes:
                            # Show the actual change
                            print(f"{Colors.RED}-{original_lines[i]}{Colors.NC}")
                            if i < len(updated_lines):
                                print(f"{Colors.GREEN}+{updated_lines[i]}{Colors.NC}")
                        else:
                            # Show context line
                            print(f" {original_lines[i]}")
            
            print()  # Empty line after diff
            Logger.success(f"Found {len(changes)} line(s) changed")
                
        except Exception as e:
            Logger.error(f"Error showing JSON diff: {e}")
    
    def show_git_diff(self) -> bool:
        """Show git diff of changes with 10 lines of context around each change"""
        try:
            if self.dry_run:
                Logger.warn("DRY RUN: Would show git diff with 10 lines context")
                print(f"{Colors.CYAN}File: project/spring-ai/documentation.json{Colors.NC}")
                
                if self.is_milestone_release():
                    # Show correct milestone behavior: ADD new PRERELEASE entry
                    # Extract major.minor for reference URL (1.1.0-M1 -> 1.1)
                    version_parts = self.version.split('.')
                    major_minor = f"{version_parts[0]}.{version_parts[1]}"
                    
                    print(f"{Colors.CYAN}@@ -17,4 +17,11 @@{Colors.NC}")
                    print(f"     \"status\": \"GENERAL_AVAILABILITY\",")
                    print(f"     \"current\": true")
                    print(f"   }},")
                    print(f"{Colors.GREEN}+  {{{Colors.NC}")
                    print(f"{Colors.GREEN}+    \"version\": \"{self.version}\",{Colors.NC}")
                    print(f"{Colors.GREEN}+    \"antora\": true,{Colors.NC}")
                    print(f"{Colors.GREEN}+    \"api\": \"https://docs.spring.io/spring-ai/docs/{self.version}/api/\",{Colors.NC}")
                    print(f"{Colors.GREEN}+    \"ref\": \"https://docs.spring.io/spring-ai/reference/{major_minor}/index.html\",{Colors.NC}")
                    print(f"{Colors.GREEN}+    \"status\": \"PRERELEASE\",{Colors.NC}")
                    print(f"{Colors.GREEN}+    \"current\": false{Colors.NC}")
                    print(f"{Colors.GREEN}+  }}{Colors.NC}")
                    print(f" ]")
                else:
                    # Show patch release behavior: UPDATE existing GA entry
                    print(f"{Colors.CYAN}@@ -8,10 +8,10 @@{Colors.NC}")
                    print(f"   {{")
                    print(f"     \"version\": \"1.1.0-SNAPSHOT\",")
                    print(f"     \"antora\": false,")
                    print(f"     \"api\": \"https://docs.spring.io/spring-ai/docs/1.1.0-SNAPSHOT/api/\",")
                    print(f"     \"ref\": \"https://docs.spring.io/spring-ai/reference/1.1-SNAPSHOT/index.html\",")
                    print(f"     \"status\": \"SNAPSHOT\",")
                    print(f"     \"current\": false")
                    print(f"   }},")
                    print(f"   {{")
                    print(f"{Colors.RED}-    \"version\": \"1.0.1\",{Colors.NC}")
                    print(f"{Colors.GREEN}+    \"version\": \"{self.version}\",{Colors.NC}")
                    print(f"     \"antora\": false,")
                    print(f"{Colors.RED}-    \"api\": \"https://docs.spring.io/spring-ai/docs/1.0.1/api/\",{Colors.NC}")
                    print(f"{Colors.GREEN}+    \"api\": \"https://docs.spring.io/spring-ai/docs/{self.version}/api/\",{Colors.NC}")
                    print(f"     \"ref\": \"https://docs.spring.io/spring-ai/reference/1.0/index.html\",")
                    print(f"     \"status\" : \"GENERAL_AVAILABILITY\",")
                    print(f"     \"current\" : true")
                    print(f"   }}")
                    print(f" ]")
                return True
            
            # Show git diff with 10 lines of context
            result = subprocess.run([
                "git", "-C", str(self.repo_dir), "diff", "-C", "10", "project/spring-ai/documentation.json"
            ], capture_output=True, text=True)
            
            if result.stdout:
                Logger.info("\n📋 GIT DIFF (with 10 lines context):")
                print(f"{Colors.CYAN}File: project/spring-ai/documentation.json{Colors.NC}")
                print(result.stdout)
            
            return True
        except Exception as e:
            Logger.error(f"Error showing git diff: {e}")
            return False
    
    def commit_changes(self) -> bool:
        """Commit the documentation changes with DCO sign-off"""
        try:
            commit_msg = f"Update Spring AI documentation to {self.version}"
            
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
                "git", "-C", str(self.repo_dir), "add", "project/spring-ai/documentation.json"
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
            pr_title = f"Update Spring AI documentation to {self.version}"
            pr_body = f"""Updates Spring AI project documentation for patch release {self.version}.

**Changes:**
- Updated version field from {old_version} to {self.version}
- Updated API documentation URL to reference {self.version}
- Reference documentation URL unchanged (stays at major.minor level)

This change ensures the Spring AI project page reflects the latest patch release information.

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
            
            # Create PR
            Logger.info("Creating pull request on GitHub...")
            result = subprocess.run([
                "gh", "pr", "create",
                "--repo", "spring-io/spring-website-content",
                "--title", pr_title,
                "--body", pr_body,
                "--head", self.branch_name,
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
            Logger.bold("🌐 SPRING WEBSITE DOCUMENTATION UPDATE")
            Logger.bold("="*60)
            Logger.info(f"Target Version: {self.version}")
            Logger.info(f"Repository: {self.repo_url}")
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
            
            # Create feature branch
            if not self.create_feature_branch():
                return False
            
            # Update documentation.json and get old version
            success, old_version = self.update_documentation_json()
            if not success:
                if old_version == self.version:
                    Logger.info("Documentation already up to date - no changes needed")
                    return True
                return False
            
            # Show git diff with full context
            if not self.show_git_diff():
                return False
            
            if not self.confirm_action("Proceed with committing the changes shown above?"):
                Logger.info("Update process cancelled by user")
                return False
            
            # Commit changes
            if not self.commit_changes():
                return False
            
            # Create pull request
            if not self.create_pull_request(old_version):
                return False
            
            Logger.bold("\n🎉 spring-website-content update completed successfully!")
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
        description="Update spring-website-content with new Spring AI documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 update-spring-website.py 1.0.1 --dry-run
  python3 update-spring-website.py 1.0.1
  python3 update-spring-website.py 1.0.1 --cleanup
        """
    )
    
    parser.add_argument('version', help='Spring AI version to update to (e.g., 1.0.1)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without making them')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up repository directory and exit')
    parser.add_argument('--fresh-start', action='store_true',
                       help='Clean up and start completely fresh (cleanup + full run)')
    parser.add_argument('--test-json', action='store_true',
                       help='Test JSON parsing against existing repository (debug mode)')
    
    args = parser.parse_args()
    
    updater = SpringWebsiteUpdater(args.version, args.dry_run)
    
    if args.cleanup:
        Logger.info("Cleaning up repository...")
        success = updater.cleanup_repository()
        sys.exit(0 if success else 1)
    
    if args.test_json:
        Logger.info("Testing JSON parsing against existing repository...")
        # Clone repository if needed
        if not updater.repo_dir.exists():
            if not updater.clone_repository():
                sys.exit(1)
        
        # Test JSON parsing
        if updater.doc_file.exists():
            try:
                with open(updater.doc_file, 'r') as f:
                    doc_array = json.load(f)
                
                if not isinstance(doc_array, list):
                    Logger.error("❌ JSON should be an array of version objects")
                    sys.exit(1)
                
                Logger.success(f"✅ JSON parsing successful! Found {len(doc_array)} version entries:")
                
                for i, entry in enumerate(doc_array):
                    version = entry.get('version', 'NO_VERSION')
                    status = entry.get('status', 'NO_STATUS')
                    current = entry.get('current', False)
                    api_url = entry.get('api', 'NO_API')
                    ref_url = entry.get('ref', 'NO_REF')
                    
                    status_marker = "🟢" if current else "⚪"
                    Logger.info(f"  {status_marker} [{i}] {version} ({status}) current={current}")
                    Logger.info(f"      api: {api_url}")
                    Logger.info(f"      ref: {ref_url}")
                
                # Find GA entry
                ga_entry = None
                for entry in doc_array:
                    if entry.get('status') == 'GENERAL_AVAILABILITY' and entry.get('current', False):
                        ga_entry = entry
                        break
                
                if ga_entry:
                    Logger.success(f"✅ Found GENERAL_AVAILABILITY entry with version: {ga_entry.get('version')}")
                else:
                    Logger.warn("⚠️ No GENERAL_AVAILABILITY entry with current=true found")
                    
            except json.JSONDecodeError as e:
                Logger.error(f"❌ JSON parsing failed: {e}")
                sys.exit(1)
        else:
            Logger.error(f"❌ Documentation file not found: {updater.doc_file}")
            sys.exit(1)
        
        sys.exit(0)
    
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
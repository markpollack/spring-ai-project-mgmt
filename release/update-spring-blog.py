#!/usr/bin/env python3
"""
Spring AI Blog Post Publishing Script

Standalone script for publishing Spring AI release blog posts to spring.io blog.
Follows the same DRY architecture as update-spring-website.py with fresh clone workflow.

Usage:
    python3 update-spring-blog.py 1.1.0-M1 blog-iteration/spring-ai-1-1-0-M1-available-now.md --dry-run
    python3 update-spring-blog.py 1.0.2 /path/to/blog-post.md
    python3 update-spring-blog.py 1.1.0-RC1 ../release-candidate-blog.md --cleanup
"""

import os
import sys
import subprocess
import argparse
import shutil
import re
import yaml
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime


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
        print(f"\n{Colors.CYAN}[STEP]{Colors.NC} {message}")
    
    @staticmethod
    def bold(message: str):
        print(f"{Colors.BOLD}{message}{Colors.NC}")


class SpringBlogUpdater:
    """Spring AI blog post publisher with fresh clone workflow"""
    
    def __init__(self, version: str, blog_file_path: str, dry_run: bool = False):
        self.version = version
        self.blog_file_path = Path(blog_file_path).resolve()
        self.dry_run = dry_run
        
        # Repository configuration
        self.repo_url = "https://github.com/spring-io/spring-website-content.git"
        self.repo_dir = Path("./repos/spring-website-content-blog")
        self.branch_name = f"spring-ai-{version}-blog"
        
        # Blog post configuration
        self.blog_metadata = None
        self.target_blog_path = None
    
    def validate_version(self) -> bool:
        """Validate version format"""
        version_pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-(M\d+|RC\d+|SNAPSHOT))?$'
        if not re.match(version_pattern, self.version):
            Logger.error(f"Invalid version format: {self.version}")
            Logger.info("Expected formats: 1.0.1, 1.1.0-M1, 1.1.0-RC1")
            return False
        return True
    
    def validate_blog_file(self) -> bool:
        """Validate blog file exists and has proper frontmatter"""
        try:
            if not self.blog_file_path.exists():
                Logger.error(f"Blog file not found: {self.blog_file_path}")
                return False
            
            Logger.step(f"Validating blog file: {self.blog_file_path}")
            
            # Read and parse frontmatter
            with open(self.blog_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.startswith('---'):
                Logger.error("Blog file must start with YAML frontmatter (---)")
                return False
            
            # Extract frontmatter
            parts = content.split('---', 2)
            if len(parts) < 3:
                Logger.error("Invalid frontmatter format")
                return False
            
            try:
                self.blog_metadata = yaml.safe_load(parts[1])
            except yaml.YAMLError as e:
                Logger.error(f"Invalid YAML frontmatter: {e}")
                return False
            
            # Validate required fields
            required_fields = ['title', 'category', 'publishedAt', 'author']
            for field in required_fields:
                if field not in self.blog_metadata:
                    Logger.error(f"Missing required frontmatter field: {field}")
                    return False
            
            Logger.success("Blog file validation passed")
            Logger.info(f"Title: {self.blog_metadata['title']}")
            Logger.info(f"Published: {self.blog_metadata['publishedAt']}")
            Logger.info(f"Author: {self.blog_metadata['author']}")
            
            return True
            
        except Exception as e:
            Logger.error(f"Error validating blog file: {e}")
            return False
    
    def determine_target_path(self) -> bool:
        """Determine target blog path based on publishedAt date"""
        try:
            published_date = self.blog_metadata['publishedAt']
            
            # Handle different date formats
            if isinstance(published_date, str):
                date_obj = datetime.strptime(published_date, '%Y-%m-%d')
            else:
                date_obj = published_date
            
            year = date_obj.strftime('%Y')
            month = date_obj.strftime('%m')
            filename = self.blog_file_path.name
            
            self.target_blog_path = Path(f"blog/{year}/{month}/{filename}")
            
            Logger.info(f"Target path: {self.target_blog_path}")
            return True
            
        except Exception as e:
            Logger.error(f"Error determining target path: {e}")
            return False
    
    def check_github_cli(self) -> bool:
        """Check if GitHub CLI is available and authenticated"""
        try:
            result = subprocess.run(['gh', 'auth', 'status'], 
                                  capture_output=True, text=True, check=True)
            # gh auth status returns 0 if authenticated, non-zero if not
            # The output goes to stderr by design
            if result.returncode == 0:
                Logger.success("GitHub CLI authenticated")
                return True
            else:
                Logger.error("❌ GitHub CLI authentication required. Run: gh auth login")
                return False
        except FileNotFoundError:
            Logger.error("❌ GitHub CLI not found. Please install gh CLI")
            return False
        except subprocess.CalledProcessError:
            Logger.error("❌ GitHub CLI authentication required. Run: gh auth login")
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
        """Create feature branch for the blog post"""
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
    
    def copy_blog_post(self) -> bool:
        """Copy blog post to target directory"""
        try:
            target_full_path = self.repo_dir / self.target_blog_path
            target_dir = target_full_path.parent
            
            Logger.step(f"Copying blog post to {self.target_blog_path}")
            
            if not self.confirm_action(f"Copy blog post to {self.target_blog_path}?"):
                Logger.info("Blog post copy cancelled by user")
                return False
            
            if self.dry_run:
                Logger.warn("DRY RUN: Would copy blog post and create directories")
                return True
            
            # Create target directory if it doesn't exist
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy blog post
            shutil.copy2(self.blog_file_path, target_full_path)
            
            Logger.success("Blog post copied successfully")
            Logger.info(f"Source: {self.blog_file_path}")
            Logger.info(f"Target: {target_full_path}")
            
            return True
        except Exception as e:
            Logger.error(f"Failed to copy blog post: {e}")
            return False
    
    def commit_changes(self) -> bool:
        """Commit the blog post with DCO sign-off"""
        try:
            commit_msg = f"Add Spring AI {self.version} release blog post"
            
            Logger.step(f"Committing changes with DCO sign-off: {commit_msg}")
            
            if not self.confirm_action("Commit the blog post (with DCO sign-off)?"):
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
                "git", "-C", str(self.repo_dir), "add", str(self.target_blog_path)
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
    
    def create_pull_request(self) -> bool:
        """Create pull request using GitHub CLI"""
        try:
            pr_title = f"Add Spring AI {self.version} release blog post"
            pr_body = f"""Spring AI {self.version} release announcement blog post.

**Blog Post Details:**
- **Title**: {self.blog_metadata['title']}
- **Category**: {self.blog_metadata['category']}
- **Published Date**: {self.blog_metadata['publishedAt']}
- **Author**: {self.blog_metadata['author']}
- **File**: {self.target_blog_path}

This blog post announces the Spring AI {self.version} release with key highlights and improvements for the Spring AI community.

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
        """Run the complete blog publishing workflow"""
        try:
            Logger.bold("\n" + "="*60)
            Logger.bold("📝 SPRING AI BLOG POST PUBLISHER")
            Logger.bold("="*60)
            Logger.info(f"Version: {self.version}")
            Logger.info(f"Blog File: {self.blog_file_path}")
            Logger.info(f"Repository: {self.repo_url}")
            Logger.info(f"Dry Run: {self.dry_run}")
            Logger.bold("="*60)
            
            # Validation
            if not self.validate_version():
                return False
            
            if not self.validate_blog_file():
                return False
            
            if not self.determine_target_path():
                return False
            
            if not self.dry_run and not self.check_github_cli():
                return False
            
            # Clone repository
            if not self.clone_repository():
                return False
            
            # Create feature branch
            if not self.create_feature_branch():
                return False
            
            # Copy blog post
            if not self.copy_blog_post():
                return False
            
            # Commit changes
            if not self.commit_changes():
                return False
            
            # Create pull request
            if not self.create_pull_request():
                return False
            
            Logger.bold("\n" + "="*60)
            Logger.success("✅ BLOG POST PUBLISHING COMPLETED SUCCESSFULLY!")
            Logger.bold("="*60)
            Logger.info("Pull request is ready for review and merge.")
            Logger.info("")
            Logger.info("📝 Next Steps:")
            Logger.info("1. Review and merge the pull request")
            Logger.info("2. Watch the blog publish action at:")
            Logger.info("   https://github.com/spring-io/spring-website/actions")
            Logger.info("3. Blog will be live on https://spring.io/blog after GitHub Action completes")
            Logger.info("   (typically 5-10 minutes after PR merge)")

            return True
            
        except Exception as e:
            Logger.error(f"Unexpected error in blog publishing workflow: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Publish Spring AI release blog posts to spring.io blog',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 update-spring-blog.py 1.1.0-M1 blog-iteration/spring-ai-1-1-0-M1-available-now.md --dry-run
  python3 update-spring-blog.py 1.0.2 /path/to/patch-release-blog.md
  python3 update-spring-blog.py 1.1.0-RC1 ../release-candidate-blog.md --cleanup
        """
    )
    
    parser.add_argument('version', 
                       help='Release version (1.0.1, 1.1.0-M1, 1.1.0-RC1, etc.)')
    parser.add_argument('blog_file', 
                       help='Path to blog markdown file (relative or absolute)')
    parser.add_argument('--dry-run', 
                       action='store_true',
                       help='Preview changes without executing them')
    parser.add_argument('--cleanup', 
                       action='store_true',
                       help='Clean up repository directory and exit')
    
    args = parser.parse_args()
    
    updater = SpringBlogUpdater(args.version, args.blog_file, args.dry_run)
    
    # Handle cleanup mode
    if args.cleanup:
        Logger.info("Running in cleanup mode...")
        success = updater.cleanup_repository()
        sys.exit(0 if success else 1)
    
    # Run the blog publishing workflow
    success = updater.run_update()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
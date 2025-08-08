#!/usr/bin/env python3
"""
GitHub Release Creator for Spring AI

This script creates GitHub releases using existing release notes files.
It handles draft/prerelease creation with automatic tag validation.

Usage:
    python3 create-github-release.py v1.0.1 --draft
    python3 create-github-release.py v1.0.2 --notes-file RELEASE_NOTES_1.0.2.md
    python3 create-github-release.py v1.0.1 --dry-run

Examples:
    # Create draft release using existing RELEASE_NOTES.md
    python3 create-github-release.py v1.0.1 --draft --dry-run
    
    # Create actual release with custom title
    python3 create-github-release.py v1.0.1 --title "Spring AI 1.0.1 - Bug Fixes"
    
    # Create prerelease
    python3 create-github-release.py v1.1.0-M1 --prerelease
"""

import os
import sys
import subprocess
import argparse
import requests
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

# Color logging utility
class Logger:
    @staticmethod
    def info(msg): print(f"\033[34m[INFO]\033[0m {msg}")
    @staticmethod
    def success(msg): print(f"\033[32m[SUCCESS]\033[0m {msg}")
    @staticmethod
    def warn(msg): print(f"\033[33m[WARN]\033[0m {msg}")
    @staticmethod
    def error(msg): print(f"\033[31m[ERROR]\033[0m {msg}")
    @staticmethod
    def debug(msg): print(f"\033[36m[DEBUG]\033[0m {msg}")
    @staticmethod
    def bold(msg): print(f"\033[1m{msg}\033[0m")

@dataclass
class ReleaseConfig:
    """Configuration for GitHub release creation"""
    tag_name: str
    title: Optional[str] = None
    notes_file: str = "RELEASE_NOTES.md"
    repo: str = "spring-projects/spring-ai"
    draft: bool = False
    prerelease: bool = False
    target_commitish: str = None  # Will be set to tag_name by default
    use_tag_date: bool = True
    github_token: Optional[str] = None
    dry_run: bool = False
    
    def __post_init__(self):
        # Auto-generate title if not provided
        if not self.title:
            self.title = f"Spring AI {self.tag_name.lstrip('v')}"
        
        # Target should point to the tag itself, not a branch
        if not self.target_commitish:
            self.target_commitish = self.tag_name
        
        # Auto-detect prerelease based on version
        if not self.prerelease:
            version = self.tag_name.lstrip('v').lower()
            self.prerelease = any(marker in version for marker in ['m', 'rc', 'alpha', 'beta', 'snapshot'])
        
        # Get GitHub token from environment
        if not self.github_token:
            self.github_token = os.environ.get('GITHUB_TOKEN')

class GitHubReleaseCreator:
    """Create GitHub releases with proper date handling"""
    
    def __init__(self, config: ReleaseConfig, repo_path: Path = None):
        self.config = config
        self.repo_path = repo_path or Path("/home/mark/projects/spring-ai")
    
    def create_release(self) -> bool:
        """Create the GitHub release"""
        Logger.bold("🚀 GITHUB RELEASE CREATOR")
        Logger.bold("=" * 40)
        
        # Validate prerequisites
        if not self._validate_prerequisites():
            return False
        
        # Load release notes
        notes_content = self._load_release_notes()
        if not notes_content:
            return False
        
        # Always use GitHub CLI (more reliable than REST API)
        return self._create_release_with_cli(notes_content)
    
    def _validate_prerequisites(self) -> bool:
        """Validate all prerequisites for release creation"""
        Logger.info("🔍 Validating prerequisites...")
        
        # Check GitHub token
        if not self.config.github_token:
            Logger.error("❌ GitHub token required (set GITHUB_TOKEN environment variable)")
            return False
        
        # Check GitHub CLI availability
        try:
            subprocess.run(['gh', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            Logger.error("❌ GitHub CLI not available - install with: brew install gh")
            return False
        
        # Check if tag exists
        if not self._tag_exists():
            Logger.error(f"❌ Tag {self.config.tag_name} does not exist")
            Logger.error("Create the tag first or check the tag name")
            return False
        
        # Check if release already exists
        if self._release_exists():
            Logger.warn(f"⚠️ Release {self.config.tag_name} already exists - will update it")
        
        # Check target commitish exists (should be the tag itself)
        if not self._commitish_exists():
            Logger.error(f"❌ Target commitish {self.config.target_commitish} does not exist")
            return False
        
        Logger.success("✅ All prerequisites validated")
        return True
    
    def _load_release_notes(self) -> Optional[str]:
        """Load release notes from file"""
        notes_path = Path(self.config.notes_file)
        if not notes_path.exists():
            Logger.error(f"❌ Release notes file not found: {notes_path}")
            Logger.error("Run generate-release-notes.py first to create the release notes")
            return None
        
        try:
            with open(notes_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            Logger.info(f"📝 Loaded release notes: {len(content)} characters from {notes_path}")
            return content
            
        except Exception as e:
            Logger.error(f"❌ Failed to read release notes file: {e}")
            return None
    
    def _get_tag_date(self) -> Optional[str]:
        """Get the creation date of the git tag"""
        try:
            cmd = ['git', 'log', '-1', '--format=%aI', self.config.tag_name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=self.repo_path)
            tag_date = result.stdout.strip()
            Logger.debug(f"Tag {self.config.tag_name} creation date: {tag_date}")
            return tag_date
        except subprocess.CalledProcessError as e:
            Logger.debug(f"Failed to get tag date: {e}")
            return None
    
    def _tag_exists(self) -> bool:
        """Check if the git tag exists"""
        try:
            cmd = ['git', 'tag', '-l', self.config.tag_name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=self.repo_path)
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False
    
    def _release_exists(self) -> bool:
        """Check if GitHub release already exists"""
        try:
            cmd = ['gh', 'release', 'view', self.config.tag_name, '--repo', self.config.repo]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _commitish_exists(self) -> bool:
        """Check if target commitish (tag/commit/branch) exists"""
        try:
            # Check if it's a valid commit-ish (tag, commit SHA, or branch)
            cmd = ['git', 'rev-parse', '--verify', f'{self.config.target_commitish}^{{commit}}']
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
            if result.returncode == 0:
                Logger.debug(f"Found commitish: {self.config.target_commitish}")
                return True
                
            return False
        except subprocess.CalledProcessError:
            return False
    
    def _create_release_with_api(self, notes_content: str, published_at: str) -> bool:
        """Create release using GitHub REST API (supports custom date)"""
        Logger.info("🔧 Creating release via GitHub REST API...")
        
        if self.config.dry_run:
            Logger.info("🧪 DRY RUN - Would create release with:")
            Logger.info(f"  📝 Title: {self.config.title}")
            Logger.info(f"  🏷️ Tag: {self.config.tag_name}")
            Logger.info("  📅 Date: Current time (GitHub default)")
            Logger.info(f"  🎯 Target: {self.config.target_commitish}")
            Logger.info(f"  📋 Draft: {self.config.draft}")
            Logger.info(f"  🚀 Prerelease: {self.config.prerelease}")
            Logger.info(f"  📄 Notes: {len(notes_content)} characters")
            
            # Prepare the actual release data that would be sent
            release_data = {
                "tag_name": self.config.tag_name,
                "target_commitish": self.config.target_commitish,
                "name": self.config.title,
                "body": notes_content,
                "draft": self.config.draft,
                "prerelease": self.config.prerelease,
            }
            
            # Show exact API call details
            Logger.bold("\n🔧 EXACT API CALL DETAILS:")
            Logger.info(f"📡 URL: https://api.github.com/repos/{self.config.repo}/releases")
            Logger.info("📋 Method: POST")
            Logger.info("📄 Headers:")
            Logger.info("   Authorization: token [GITHUB_TOKEN]")
            Logger.info("   Accept: application/vnd.github+json")
            Logger.info("   X-GitHub-Api-Version: 2022-11-28")
            Logger.info("   Content-Type: application/json")
            
            Logger.bold("\n📦 JSON PAYLOAD:")
            # Pretty print the JSON payload (truncated body for readability)
            display_data = release_data.copy()
            if len(display_data["body"]) > 200:
                display_data["body"] = display_data["body"][:200] + "...[truncated]"
            
            import json
            Logger.info(json.dumps(display_data, indent=2))
            
            # Show what the URL would be
            expected_url = f"https://github.com/{self.config.repo}/releases/tag/{self.config.tag_name}"
            Logger.bold("\n🎯 EXPECTED RESULT:")
            Logger.info(f"🔗 Release URL: {expected_url}")
            Logger.info("👆 Remove --dry-run to create the actual release")
            return True
        
        # Prepare release data (without unsupported published_at field)
        release_data = {
            "tag_name": self.config.tag_name,
            "target_commitish": self.config.target_commitish,
            "name": self.config.title,
            "body": notes_content,
            "draft": self.config.draft,
            "prerelease": self.config.prerelease
        }
        
        try:
            url = f"https://api.github.com/repos/{self.config.repo}/releases"
            headers = {
                "Authorization": f"token {self.config.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=release_data, headers=headers)
            response.raise_for_status()
            
            release_info = response.json()
            Logger.success(f"✅ GitHub release {self.config.tag_name} created successfully!")
            
            # Prominent URL display
            Logger.bold("\n" + "="*60)
            Logger.bold("🎯 REVIEW YOUR GITHUB RELEASE")
            Logger.bold("="*60)
            Logger.info(f"🔗 Release URL: {release_info['html_url']}")
            Logger.info(f"📅 Published at: {release_info['published_at']}")
            Logger.info(f"📋 Draft: {release_info['draft']}")
            Logger.info(f"🚀 Prerelease: {release_info['prerelease']}")
            
            if release_info['draft']:
                Logger.bold("\n📝 DRAFT RELEASE CREATED:")
                Logger.info("   • Review the content and formatting")
                Logger.info("   • Check contributor acknowledgments") 
                Logger.info("   • Verify categorization accuracy")
                Logger.info("   • Click 'Publish release' when ready")
            else:
                Logger.bold("\n🚀 RELEASE PUBLISHED:")
                Logger.info("   • Release is now live and public")
                Logger.info("   • Users will be notified of the new release")
            
            Logger.bold(f"\n👆 Click the URL above to review: {release_info['html_url']}")
            Logger.bold("="*60)
            
            return True
            
        except requests.exceptions.RequestException as e:
            Logger.error(f"❌ Failed to create release via API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    Logger.error(f"API Error: {error_data}")
                except:
                    Logger.error(f"Response: {e.response.text}")
            return False
    
    def _create_release_with_cli(self, notes_content: str) -> bool:
        """Create release using GitHub CLI (standard flow)"""
        
        # Check if release already exists to determine command
        release_exists = self._release_exists()
        action = "edit" if release_exists else "create"
        
        Logger.info(f"🔧 {'Updating' if release_exists else 'Creating'} release via GitHub CLI...")
        
        # Build command
        cmd = ['gh', 'release', action, self.config.tag_name]
        cmd.extend(['--title', self.config.title])
        
        # Only add target for create (not edit) and only if tag doesn't exist
        if not release_exists and not self._tag_exists():
            cmd.extend(['--target', self.config.target_commitish])
        
        cmd.extend(['--repo', self.config.repo])
        
        # Handle draft flag differently for create vs edit
        if action == "create":
            # For create: use --draft (boolean flag)
            if self.config.draft:
                cmd.append('--draft')
        else:
            # For edit: use --draft=true/false (with equals)
            if self.config.draft:
                cmd.append('--draft=true')
            else:
                cmd.append('--draft=false')
        
        if self.config.prerelease:
            cmd.append('--prerelease')
        
        # Write notes to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(notes_content)
            temp_notes = f.name
        
        try:
            cmd.extend(['--notes-file', temp_notes])
            
            if self.config.dry_run:
                Logger.info("🧪 DRY RUN - Would execute command:")
                Logger.info(f"  {' '.join(cmd)}")
                return True
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            Logger.success(f"✅ GitHub release {self.config.tag_name} {'updated' if release_exists else 'created'} successfully!")
            
            # Get the correct URL using gh release view
            try:
                url_cmd = ['gh', 'release', 'view', self.config.tag_name, '--repo', self.config.repo, '--json', 'url', '-q', '.url']
                url_result = subprocess.run(url_cmd, capture_output=True, text=True, check=True)
                release_url = url_result.stdout.strip()
            except subprocess.CalledProcessError:
                # Fallback to constructed URL if view fails
                release_url = f"https://github.com/{self.config.repo}/releases/tag/{self.config.tag_name}"
            
            Logger.bold("\n" + "="*60)
            Logger.bold("🎯 REVIEW YOUR GITHUB RELEASE")
            Logger.bold("="*60)
            Logger.info(f"🔗 Release URL: {release_url}")
            
            if self.config.draft:
                Logger.bold("\n📝 DRAFT RELEASE CREATED:")
                Logger.info("   • Review the content and formatting")
                Logger.info("   • Check contributor acknowledgments") 
                Logger.info("   • Verify categorization accuracy")
                Logger.info("   • Click 'Publish release' when ready")
            else:
                Logger.bold("\n🚀 RELEASE PUBLISHED:")
                Logger.info("   • Release is now live and public")
                Logger.info("   • Users will be notified of the new release")
            
            Logger.bold(f"\n👆 Click the URL above to review: {release_url}")
            Logger.bold("="*60)
            
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"❌ Failed to create release: {e}")
            Logger.error(f"Command output: {e.stdout}")
            Logger.error(f"Command error: {e.stderr}")
            return False
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_notes)
            except:
                pass

def main():
    parser = argparse.ArgumentParser(
        description="Create GitHub releases for Spring AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('tag_name', 
                       help='Git tag name for the release (e.g., v1.0.1)')
    parser.add_argument('--title',
                       help='Custom release title (default: auto-generated from tag)')
    parser.add_argument('--notes-file',
                       default='RELEASE_NOTES.md',
                       help='Release notes file (default: RELEASE_NOTES.md)')
    parser.add_argument('--repo',
                       default='spring-projects/spring-ai',
                       help='GitHub repository (default: spring-projects/spring-ai)')
    parser.add_argument('--draft',
                       action='store_true',
                       help='Create as draft release')
    parser.add_argument('--prerelease',
                       action='store_true', 
                       help='Mark as prerelease (auto-detected from version)')
    parser.add_argument('--target',
                       help='Target commitish (tag/commit/branch) for release (default: same as tag_name)')
    parser.add_argument('--no-tag-date',
                       action='store_true',
                       help='Do not use tag creation date (use current time)')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Show what would be done without creating release')
    parser.add_argument('--verbose',
                       action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Enable debug logging if verbose
    if args.verbose:
        os.environ['DEBUG'] = '1'
    
    # Create release configuration
    config = ReleaseConfig(
        tag_name=args.tag_name,
        title=args.title,
        notes_file=args.notes_file,
        repo=args.repo,
        draft=args.draft,
        prerelease=args.prerelease,
        target_commitish=args.target,
        use_tag_date=not args.no_tag_date,
        dry_run=args.dry_run
    )
    
    # Create and execute release
    creator = GitHubReleaseCreator(config)
    success = creator.create_release()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
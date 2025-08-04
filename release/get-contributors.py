#!/usr/bin/env python3
"""
Spring AI Contributors Collection Script

Collects and formats contributor information between releases using GitHub API.
Automatically detects the previous release date or accepts manual date input.

Usage:
    python3 get-contributors.py                      # Auto-detect since last release
    python3 get-contributors.py --since-version 1.0.0  # Since specific version
    python3 get-contributors.py --since 2024-04-01     # Since specific date
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class ContributorConfig:
    """Configuration for contributor collection"""
    script_dir: Path
    spring_ai_repo: str = "spring-projects/spring-ai"
    repo_path: Path = Path("/home/mark/projects/spring-ai")
    output_dir: Path = None
    since_date: Optional[str] = None
    since_version: Optional[str] = None
    dry_run: bool = False
    show_commits: bool = False
    format: str = "markdown"  # markdown, json
    
    def __post_init__(self):
        if self.output_dir is None:
            self.output_dir = self.script_dir / "contributors-output"
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class Contributor:
    """Represents a contributor with their information"""
    name: str
    username: str
    email: Optional[str] = None
    commits: List[str] = field(default_factory=list)
    is_bot: bool = False
    
    @property
    def github_url(self) -> str:
        return f"https://github.com/{self.username}"
    
    @property
    def markdown_entry(self) -> str:
        return f"- [{self.name} ({self.username})]({self.github_url})"


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
    def debug(message: str):
        if os.environ.get('DEBUG'):
            print(f"{Colors.CYAN}[DEBUG]{Colors.NC} {message}")


class GitHubAPIHelper:
    """Helper for GitHub API operations"""
    
    def __init__(self, repo: str):
        self.repo = repo
    
    def is_gh_available(self) -> bool:
        """Check if GitHub CLI is available and authenticated"""
        try:
            result = subprocess.run(['gh', 'auth', 'status'], 
                                  capture_output=True, text=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_latest_release(self) -> Optional[Dict]:
        """Get the latest release information"""
        try:
            cmd = ['gh', 'api', f'/repos/{self.repo}/releases/latest']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to get latest release: {e}")
            return None
    
    def get_release_by_tag(self, tag: str) -> Optional[Dict]:
        """Get release information by tag name"""
        try:
            # Try with 'v' prefix first
            if not tag.startswith('v'):
                tag = f'v{tag}'
            
            cmd = ['gh', 'api', f'/repos/{self.repo}/releases/tags/{tag}']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError:
            # Try without 'v' prefix
            if tag.startswith('v'):
                tag = tag[1:]
                cmd = ['gh', 'api', f'/repos/{self.repo}/releases/tags/{tag}']
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    return json.loads(result.stdout)
                except subprocess.CalledProcessError as e:
                    Logger.debug(f"No GitHub release found for tag, will check git tags")
                    return None
    
    def get_tag_date(self, tag: str, repo_path: Path) -> Optional[str]:
        """Get the date of a git tag"""
        try:
            # Ensure tag has 'v' prefix
            if not tag.startswith('v'):
                tag = f'v{tag}'
            
            original_dir = os.getcwd()
            os.chdir(repo_path)
            
            # Get the commit date for the tag
            cmd = ['git', 'log', '-1', '--format=%aI', tag]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                # Convert ISO format to simple date
                date = datetime.fromisoformat(result.stdout.strip())
                return date.strftime('%Y-%m-%d')
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to get tag date for {tag}: {e}")
        finally:
            os.chdir(original_dir)
        
        return None
    
    def get_commit_author(self, commit_sha: str) -> Optional[Dict]:
        """Get detailed author information for a commit"""
        try:
            cmd = ['gh', 'api', f'/repos/{self.repo}/commits/{commit_sha}']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            author_info = {
                'name': data['commit']['author']['name'],
                'email': data['commit']['author']['email'],
                'username': None,
                'is_bot': False
            }
            
            # Get GitHub username if available
            if data.get('author'):
                author_info['username'] = data['author']['login']
                author_info['is_bot'] = data['author'].get('type', '').lower() == 'bot'
            
            return author_info
        except subprocess.CalledProcessError as e:
            Logger.debug(f"Failed to get commit author for {commit_sha}: {e}")
            return None


class ContributorCollector:
    """Main collector for contributor information"""
    
    def __init__(self, config: ContributorConfig):
        self.config = config
        self.github = GitHubAPIHelper(config.spring_ai_repo)
        self.contributors: Dict[str, Contributor] = {}
    
    def determine_since_date(self) -> Optional[str]:
        """Determine the since date based on configuration"""
        if self.config.since_date:
            return self.config.since_date
        
        if self.config.since_version:
            Logger.info(f"Looking up release date for version {self.config.since_version}")
            release = self.github.get_release_by_tag(self.config.since_version)
            if release:
                published_at = release['published_at']
                # Convert ISO format to simple date
                date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                return date.strftime('%Y-%m-%d')
            else:
                # Try to get date from git tag
                Logger.info(f"No GitHub release found, checking git tag {self.config.since_version}")
                tag_date = self.github.get_tag_date(self.config.since_version, self.config.repo_path)
                if tag_date:
                    Logger.info(f"Found tag date: {tag_date}")
                    return tag_date
                else:
                    Logger.error(f"Could not find release or tag {self.config.since_version}")
                    return None
        
        # Default: try to get the latest release
        Logger.info("No date specified, checking latest release")
        release = self.github.get_latest_release()
        if release:
            published_at = release['published_at']
            tag = release['tag_name']
            date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            Logger.info(f"Using date from latest release {tag}: {date.strftime('%Y-%m-%d')}")
            return date.strftime('%Y-%m-%d')
        
        # Try to get the latest version tag from git
        Logger.info("No GitHub releases found, checking git tags")
        latest_tag = self._get_latest_version_tag()
        if latest_tag:
            tag_date = self.github.get_tag_date(latest_tag, self.config.repo_path)
            if tag_date:
                Logger.info(f"Using date from latest tag {latest_tag}: {tag_date}")
                return tag_date
        
        Logger.warn("Could not determine date automatically")
        return None
    
    def _get_latest_version_tag(self) -> Optional[str]:
        """Get the latest version tag from git"""
        try:
            original_dir = os.getcwd()
            os.chdir(self.config.repo_path)
            
            # Get all version tags sorted by version
            cmd = ['git', 'tag', '-l', 'v*.*.*']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                tags = result.stdout.strip().split('\n')
                # Sort tags by version number (assumes semantic versioning)
                tags.sort(key=lambda t: [int(x) for x in t.lstrip('v').split('.')])
                return tags[-1]  # Return the latest tag
            
        except subprocess.CalledProcessError as e:
            Logger.debug(f"Failed to get latest tag: {e}")
        finally:
            os.chdir(original_dir)
        
        return None
    
    def collect_contributors(self) -> bool:
        """Collect contributor information from git log"""
        since_date = self.determine_since_date()
        if not since_date:
            Logger.error("No date specified and could not determine automatically")
            return False
        
        Logger.info(f"Collecting contributors since {since_date}")
        
        # Change to repository directory
        original_dir = os.getcwd()
        try:
            os.chdir(self.config.repo_path)
            
            # Get commits since date
            cmd = ['git', 'log', f'--since={since_date}', '--format=%H|%aN|%aE']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            commits = result.stdout.strip().split('\n')
            if not commits or commits == ['']:
                Logger.warn("No commits found in the specified date range")
                return True
            
            Logger.info(f"Processing {len(commits)} commits...")
            
            # Process each commit
            for i, commit_line in enumerate(commits):
                if not commit_line:
                    continue
                
                parts = commit_line.split('|')
                if len(parts) != 3:
                    continue
                
                commit_sha, author_name, author_email = parts
                
                # Show progress
                if (i + 1) % 10 == 0:
                    Logger.info(f"Progress: {i + 1}/{len(commits)} commits processed")
                
                # Get detailed author info from GitHub
                author_info = self.github.get_commit_author(commit_sha)
                
                if author_info:
                    username = author_info['username'] or self._extract_username_from_email(author_email)
                    
                    # Skip bot accounts if configured
                    if author_info['is_bot']:
                        Logger.debug(f"Skipping bot account: {username}")
                        continue
                    
                    # Create or update contributor
                    key = username.lower()
                    if key not in self.contributors:
                        self.contributors[key] = Contributor(
                            name=author_name,
                            username=username,
                            email=author_email,
                            is_bot=author_info['is_bot']
                        )
                    
                    self.contributors[key].commits.append(commit_sha[:7])
                else:
                    # Fallback to email-based username extraction
                    username = self._extract_username_from_email(author_email)
                    key = username.lower()
                    
                    if key not in self.contributors:
                        self.contributors[key] = Contributor(
                            name=author_name,
                            username=username,
                            email=author_email
                        )
                    
                    self.contributors[key].commits.append(commit_sha[:7])
            
            Logger.success(f"Collected {len(self.contributors)} unique contributors")
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Git command failed: {e}")
            return False
        finally:
            os.chdir(original_dir)
    
    def _extract_username_from_email(self, email: str) -> str:
        """Extract username from email address"""
        if '@' in email:
            # Handle noreply emails like: username@users.noreply.github.com
            if 'noreply.github.com' in email:
                username = email.split('@')[0]
                # Remove numeric prefix if present (e.g., "12345+username")
                if '+' in username:
                    username = username.split('+')[1]
                return username
            else:
                # Regular email, use the part before @
                return email.split('@')[0]
        return email


class ContributorFormatter:
    """Format contributors for output"""
    
    def __init__(self, contributors: Dict[str, Contributor], config: ContributorConfig):
        self.contributors = contributors
        self.config = config
    
    def generate_markdown(self) -> str:
        """Generate markdown formatted contributor list"""
        lines = ["## Contributors", ""]
        lines.append("There were other refactoring, bug fixing, documentation enhancements across the board by a wide range of contributors. If we haven't gotten to your PR yet, we will, please be patient. Thanks to")
        lines.append("")
        
        # Sort contributors alphabetically by name
        sorted_contributors = sorted(self.contributors.values(), key=lambda c: c.name.lower())
        
        for contributor in sorted_contributors:
            lines.append(contributor.markdown_entry)
        
        return '\n'.join(lines)
    
    def generate_json(self) -> str:
        """Generate JSON formatted contributor list"""
        data = []
        for contributor in self.contributors.values():
            data.append({
                'name': contributor.name,
                'username': contributor.username,
                'github_url': contributor.github_url,
                'commits': len(contributor.commits),
                'is_bot': contributor.is_bot
            })
        
        # Sort by name
        data.sort(key=lambda c: c['name'].lower())
        
        return json.dumps(data, indent=2)
    
    def save_output(self) -> bool:
        """Save formatted output to files"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if self.config.format == 'markdown' or self.config.format == 'both':
                md_content = self.generate_markdown()
                md_file = self.config.output_dir / f'contributors_{timestamp}.md'
                md_file.write_text(md_content)
                Logger.success(f"Markdown output saved to: {md_file}")
                
                # Also save a latest version
                latest_md = self.config.output_dir / 'contributors_latest.md'
                latest_md.write_text(md_content)
            
            if self.config.format == 'json' or self.config.format == 'both':
                json_content = self.generate_json()
                json_file = self.config.output_dir / f'contributors_{timestamp}.json'
                json_file.write_text(json_content)
                Logger.success(f"JSON output saved to: {json_file}")
                
                # Also save a latest version
                latest_json = self.config.output_dir / 'contributors_latest.json'
                latest_json.write_text(json_content)
            
            # Save raw data with commits if requested
            if self.config.show_commits:
                raw_data = []
                for contributor in self.contributors.values():
                    raw_data.append({
                        'name': contributor.name,
                        'username': contributor.username,
                        'email': contributor.email,
                        'commits': contributor.commits,
                        'commit_count': len(contributor.commits)
                    })
                
                raw_file = self.config.output_dir / f'contributors_raw_{timestamp}.json'
                raw_file.write_text(json.dumps(raw_data, indent=2))
                Logger.info(f"Raw data saved to: {raw_file}")
            
            return True
            
        except Exception as e:
            Logger.error(f"Failed to save output: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Collect and format Spring AI contributors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect since last release
  python3 get-contributors.py

  # Since specific version
  python3 get-contributors.py --since-version 1.0.0

  # Since specific date
  python3 get-contributors.py --since 2024-04-01

  # Custom output directory and format
  python3 get-contributors.py --output-dir ./output --format json
        """
    )
    
    parser.add_argument('--since', 
                       help='Date to collect contributors since (YYYY-MM-DD)')
    parser.add_argument('--since-version', 
                       help='Version to collect contributors since (e.g., 1.0.0)')
    parser.add_argument('--repo-path', 
                       default='/home/mark/projects/spring-ai',
                       help='Path to Spring AI repository')
    parser.add_argument('--output-dir',
                       help='Output directory for results')
    parser.add_argument('--format',
                       choices=['markdown', 'json', 'both'],
                       default='markdown',
                       help='Output format')
    parser.add_argument('--show-commits',
                       action='store_true',
                       help='Include commit SHAs in output')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    # Create configuration
    script_dir = Path(__file__).parent.resolve()
    config = ContributorConfig(
        script_dir=script_dir,
        repo_path=Path(args.repo_path),
        since_date=args.since,
        since_version=args.since_version,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        format=args.format,
        show_commits=args.show_commits,
        dry_run=args.dry_run
    )
    
    # Check GitHub CLI availability
    github = GitHubAPIHelper(config.spring_ai_repo)
    if not github.is_gh_available():
        Logger.error("GitHub CLI not available or not authenticated")
        Logger.info("Please run: gh auth login")
        return 1
    
    # Check repository exists
    if not config.repo_path.exists():
        Logger.error(f"Repository path does not exist: {config.repo_path}")
        return 1
    
    # Collect contributors
    collector = ContributorCollector(config)
    if not collector.collect_contributors():
        return 1
    
    if not collector.contributors:
        Logger.warn("No contributors found")
        return 0
    
    # Format and save output
    formatter = ContributorFormatter(collector.contributors, config)
    if config.dry_run:
        Logger.info("DRY RUN: Would generate the following output:")
        if config.format == 'json':
            print("\n" + formatter.generate_json())
        elif config.format == 'both':
            print("\n=== MARKDOWN ===")
            print(formatter.generate_markdown())
            print("\n=== JSON ===")
            print(formatter.generate_json())
        else:
            print("\n" + formatter.generate_markdown())
    else:
        if not formatter.save_output():
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Spring AI Release Notes Generator

Automatically generates comprehensive GitHub-ready release notes by analyzing commits,
pull requests, and issues since the last release. Uses Claude Code CLI for intelligent
categorization and Spring AI specific analysis.

Features:
- Automatic commit discovery since last release
- GitHub GraphQL integration for PR/issue enrichment  
- AI-powered categorization using Claude Code CLI
- Professional markdown output with proper linking
- Contributor acknowledgments and statistics
- Spring AI project-specific considerations

Usage:
    python3 generate-release-notes.py --since-version 1.0.0    # Since specific version tag
    python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1   # Tag-to-tag range
    python3 generate-release-notes.py --since-version 1.0.0 --limit 5 --verbose      # Test with limited commits
"""

import os
import sys
import subprocess
import argparse
import json
import requests
import re
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict

# Import Claude Code wrapper from pr-review directory
sys.path.insert(0, str(Path(__file__).parent.parent / "pr-review"))
from claude_code_wrapper import ClaudeCodeWrapper


class CostTracker:
    """Track and report AI analysis costs"""
    
    def __init__(self):
        self.operations = []
        self.total_cost = 0.0
    
    def add_operation(self, operation_name: str, cost: float, commit_count: int = 0):
        """Add a cost operation"""
        self.operations.append({
            'operation': operation_name,
            'cost': cost,
            'commit_count': commit_count,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        self.total_cost += cost
    
    def get_summary(self) -> str:
        """Get cost summary"""
        if not self.operations:
            return "💰 No AI operations performed - Total cost: $0.00"
        
        summary = [f"💰 AI ANALYSIS COST SUMMARY"]
        summary.append("=" * 40)
        
        for op in self.operations:
            commits_info = f" ({op['commit_count']} commits)" if op['commit_count'] > 0 else ""
            summary.append(f"• {op['operation']}{commits_info}: ${op['cost']:.4f}")
        
        summary.append("-" * 40)
        summary.append(f"🎯 TOTAL COST: ${self.total_cost:.4f}")
        
        return "\n".join(summary)
    
    def save_to_file(self, filepath: Path):
        """Save cost tracking to file"""
        with open(filepath, 'w') as f:
            f.write(self.get_summary())
            f.write("\n\nDetailed Operations:\n")
            for op in self.operations:
                f.write(f"{op['timestamp']}: {op['operation']} - ${op['cost']:.4f}\n")


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
    
    @staticmethod
    def bold(message: str):
        print(f"{Colors.BOLD}{message}{Colors.NC}")


# Core Data Structures
@dataclass
class CommitData:
    """Basic commit information from git log"""
    sha: str
    message: str
    author: str
    email: str
    date: str
    
    @property
    def short_sha(self) -> str:
        return self.sha[:7]
    
    @property
    def commit_url(self) -> str:
        """Generate GitHub commit URL"""
        return f"https://github.com/spring-projects/spring-ai/commit/{self.sha}"


@dataclass
class PullRequest:
    """Pull request information from GitHub API"""
    number: int
    title: str
    url: str
    state: str
    labels: List[str] = field(default_factory=list)
    closing_issues: List[int] = field(default_factory=list)
    merged_at: Optional[str] = None
    author: Optional[str] = None
    
    @property
    def is_merged(self) -> bool:
        return self.state == "MERGED" and self.merged_at is not None


@dataclass
class Issue:
    """GitHub issue information"""
    number: int
    title: str
    url: str
    state: str
    labels: List[str] = field(default_factory=list)


@dataclass
class EnrichedCommit:
    """Commit enhanced with GitHub PR and issue information"""
    commit: CommitData
    prs: List[PullRequest] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    category_hints: List[str] = field(default_factory=list)
    
    @property
    def primary_link(self) -> str:
        """Get the primary link (PR preferred, commit fallback)"""
        if self.prs:
            # Prefer merged PRs
            merged_prs = [pr for pr in self.prs if pr.is_merged]
            if merged_prs:
                return merged_prs[0].url
            # Fallback to any PR
            return self.prs[0].url
        return self.commit.commit_url
    
    @property
    def link_text(self) -> str:
        """Generate link text like '(#123 via #456, #789)'"""
        if not self.prs:
            return f"({self.commit.short_sha})"
        
        pr_links = []
        issue_links = []
        
        for pr in self.prs:
            pr_links.append(f"#{pr.number}")
            for issue_num in pr.closing_issues:
                if issue_num not in [i.number for i in self.issues]:
                    issue_links.append(f"#{issue_num}")
        
        # Add direct issues
        for issue in self.issues:
            if f"#{issue.number}" not in issue_links:
                issue_links.append(f"#{issue.number}")
        
        if issue_links:
            return f"({', '.join(pr_links)} via {', '.join(issue_links)})"
        else:
            return f"({', '.join(pr_links)})"


@dataclass
class CategorizedChange:
    """A categorized change for release notes"""
    title: str
    description: str
    link_text: str
    category: str
    breaking: bool = False
    impact: str = "normal"
    commit: EnrichedCommit = None
    
    def to_markdown_line(self) -> str:
        """Convert to markdown list item"""
        return f"- {self.description} {self.link_text}"


@dataclass
class ReleaseNotesConfig:
    """Configuration for release notes generation"""
    # Repository settings
    repo_owner: str = "spring-projects"
    repo_name: str = "spring-ai"
    repo_path: Path = Path("/home/mark/projects/spring-ai")
    branch: str = "1.0.x"
    
    # Version settings (tag-based only)
    since_version: Optional[str] = None
    target_version: Optional[str] = None
    
    # AI analysis settings
    ai_model: str = "sonnet"  # Cost control
    ai_timeout: int = 300
    claude_logs_dir: Path = Path("./logs")
    use_ai: bool = True
    
    # Output settings
    output_file: Path = Path("RELEASE_NOTES.md")
    include_stats: bool = True
    include_contributors: bool = True
    group_related_changes: bool = True
    include_debug_data: bool = False
    dry_run: bool = False
    verbose: bool = False
    
    # Testing/development settings
    limit: Optional[int] = None
    sample: Optional[int] = None
    skip_github: bool = False
    save_ai_input: bool = False
    logs_dir: Path = Path("./logs/release-notes")
    
    # GitHub settings
    github_token: Optional[str] = None
    rate_limit_delay: float = 1.0
    
    def __post_init__(self):
        self.repo_path = Path(self.repo_path)
        self.output_file = Path(self.output_file)
        self.claude_logs_dir = Path(self.claude_logs_dir)
        self.claude_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Get GitHub token from environment if not provided
        if not self.github_token:
            self.github_token = os.environ.get('GITHUB_TOKEN')


@dataclass
class AnalysisResult:
    """Result of AI analysis"""
    highlights: str = ""
    breaking_changes: List[CategorizedChange] = field(default_factory=list)
    features: List[CategorizedChange] = field(default_factory=list)
    bug_fixes: List[CategorizedChange] = field(default_factory=list)
    documentation: List[CategorizedChange] = field(default_factory=list)
    performance: List[CategorizedChange] = field(default_factory=list)
    internal: List[CategorizedChange] = field(default_factory=list)
    security: List[CategorizedChange] = field(default_factory=list)
    accessibility: List[CategorizedChange] = field(default_factory=list)
    other: List[CategorizedChange] = field(default_factory=list)


class ReleaseNotesError(Exception):
    """Custom exception for release notes generation"""
    pass


class GitHubAPIHelper:
    """Enhanced GitHub API helper with GraphQL support"""
    
    def __init__(self, repo: str, token: Optional[str] = None):
        self.repo = repo
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.graphql_url = 'https://api.github.com/graphql'
        self.rest_url = 'https://api.github.com'
        
        if not self.token:
            Logger.warn("No GitHub token found - some features may be limited")
    
    @property
    def headers(self) -> Dict[str, str]:
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
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
                    Logger.debug(f"No GitHub release found for tag {tag}")
                    return None
    
    def get_tag_date(self, tag: str, repo_path: Path) -> Optional[str]:
        """Get the date of a git tag"""
        try:
            # Ensure tag has 'v' prefix for consistency
            if not tag.startswith('v'):
                tag = f'v{tag}'
            
            original_dir = os.getcwd()
            os.chdir(repo_path)
            
            # Get the commit date for the tag
            cmd = ['git', 'log', '-1', '--format=%aI', tag]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                # Convert ISO format to simple date
                date = datetime.fromisoformat(result.stdout.strip().replace('Z', '+00:00'))
                return date.strftime('%Y-%m-%d')
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to get tag date for {tag}: {e}")
        finally:
            os.chdir(original_dir)
        
        return None
    
    def get_commit_pr_associations(self, commit_shas: List[str]) -> Dict[str, List[PullRequest]]:
        """Get PR associations for multiple commits using GraphQL"""
        if not self.token:
            Logger.warn("No GitHub token - cannot fetch PR associations")
            return {}
        
        associations = {}
        
        # Process commits in batches to avoid GraphQL query size limits
        batch_size = 10
        for i in range(0, len(commit_shas), batch_size):
            batch = commit_shas[i:i + batch_size]
            batch_associations = self._fetch_pr_associations_batch(batch)
            associations.update(batch_associations)
            
            # Rate limiting
            if len(commit_shas) > batch_size:
                import time
                time.sleep(0.5)
        
        return associations
    
    def _fetch_pr_associations_batch(self, commit_shas: List[str]) -> Dict[str, List[PullRequest]]:
        """Fetch PR associations for a batch of commits"""
        Logger.debug(f"Fetching PR associations for {len(commit_shas)} commits: {[sha[:8] for sha in commit_shas]}")
        
        # Build GraphQL query for multiple commits
        repo_parts = self.repo.split('/')
        owner, name = repo_parts[0], repo_parts[1]
        
        Logger.debug(f"Repository: {owner}/{name}")
        
        commit_queries = []
        for i, sha in enumerate(commit_shas):
            commit_queries.append(f'''
            commit{i}: object(oid: "{sha}") {{
                ... on Commit {{
                    oid
                    associatedPullRequests(first: 5) {{
                        nodes {{
                            number
                            title
                            url
                            state
                            mergedAt
                            author {{
                                login
                            }}
                            labels(first: 10) {{
                                nodes {{
                                    name
                                }}
                            }}
                            closingIssuesReferences(first: 10) {{
                                nodes {{
                                    number
                                }}
                            }}
                        }}
                    }}
                }}
            }}
            ''')
        
        query = f'''
        query {{
            repository(owner: "{owner}", name: "{name}") {{
                {' '.join(commit_queries)}
            }}
        }}
        '''
        
        # Log GraphQL query for debugging (only if --debug-github is enabled)
        if os.environ.get('DEBUG_GITHUB'):
            Logger.debug("GraphQL query:")
            for line in query.split('\n'):
                if line.strip():
                    Logger.debug(f"  {line}")
        
        try:
            response = requests.post(
                self.graphql_url,
                json={'query': query},
                headers=self.headers,
                timeout=30
            )
            
            Logger.debug(f"GraphQL response status: {response.status_code}")
            response.raise_for_status()
            
            data = response.json()
            
            # Only show full response with --debug-github flag  
            if os.environ.get('DEBUG_GITHUB'):
                Logger.debug(f"Raw GraphQL response: {json.dumps(data, indent=2)}")
            else:
                Logger.debug(f"GraphQL response received with {len(data.get('data', {}).get('repository', {}))} repository fields")
            
            if 'errors' in data:
                Logger.warn(f"GraphQL errors: {data['errors']}")
                return {}
            
            # Parse response
            associations = {}
            repo_data = data.get('data', {}).get('repository', {})
            
            Logger.debug(f"Repository data keys: {list(repo_data.keys()) if repo_data else 'None'}")
            
            for i, sha in enumerate(commit_shas):
                commit_key = f'commit{i}'
                commit_data = repo_data.get(commit_key)
                
                Logger.debug(f"Commit {sha[:8]} ({commit_key}): {commit_data is not None}")
                
                if not commit_data:
                    Logger.debug(f"  No data found for commit {sha[:8]}")
                    continue
                
                prs = []
                pr_data = commit_data.get('associatedPullRequests', {})
                pr_nodes = pr_data.get('nodes', [])
                
                Logger.debug(f"  Found {len(pr_nodes)} associated PRs")
                
                for pr_node in pr_nodes:
                    Logger.debug(f"    PR #{pr_node.get('number')}: {pr_node.get('title')}")
                    
                    labels = [label['name'] for label in pr_node.get('labels', {}).get('nodes', [])]
                    closing_issues = [issue['number'] for issue in pr_node.get('closingIssuesReferences', {}).get('nodes', [])]
                    
                    pr = PullRequest(
                        number=pr_node['number'],
                        title=pr_node['title'],
                        url=pr_node['url'],
                        state=pr_node['state'],
                        labels=labels,
                        closing_issues=closing_issues,
                        merged_at=pr_node.get('mergedAt'),
                        author=pr_node.get('author', {}).get('login') if pr_node.get('author') else None
                    )
                    prs.append(pr)
                
                if prs:
                    associations[sha] = prs
                    Logger.debug(f"  Added {len(prs)} PRs for commit {sha[:8]}")
                else:
                    Logger.debug(f"  No PRs found for commit {sha[:8]}")
            
            Logger.debug(f"Total PR associations found: {len(associations)} commits with PRs")
            return associations
            
        except Exception as e:
            Logger.error(f"Failed to fetch PR associations: {e}")
            Logger.debug(f"Exception details: {type(e).__name__}: {str(e)}")
            return {}


class GitCommitCollector:
    """Collect commits and basic metadata from git repository"""
    
    def __init__(self, config: ReleaseNotesConfig):
        self.config = config
        self.github = GitHubAPIHelper(f"{config.repo_owner}/{config.repo_name}", config.github_token)
    
    def determine_since_tag(self) -> Optional[str]:
        """Determine the since tag for tag-to-tag collection - simpler and more accurate"""
        if self.config.since_version:
            # Try different tag formats
            possible_tags = [
                f"v{self.config.since_version}",  # e.g., "v1.0.0" (most common)
                self.config.since_version,  # e.g., "1.0.0"
                f"release-{self.config.since_version}",  # e.g., "release-1.0.0"
            ]
            
            # Change to repository directory to check tags
            original_dir = os.getcwd()
            try:
                os.chdir(self.config.repo_path)
                
                for tag in possible_tags:
                    try:
                        # Check if tag exists
                        cmd = ['git', 'rev-parse', '--verify', f'refs/tags/{tag}']
                        subprocess.run(cmd, capture_output=True, text=True, check=True)
                        Logger.info(f"Found since tag: {tag}")
                        return tag
                    except subprocess.CalledProcessError:
                        Logger.debug(f"Tag {tag} not found")
                        continue
                
                Logger.error(f"Could not find any tag for version {self.config.since_version}")
                return None
                
            finally:
                os.chdir(original_dir)
        
        # Default: try to get the latest version tag from git directly
        Logger.info("No version specified, finding latest version tag from git")
        latest_tag = self._get_latest_version_tag()
        if latest_tag:
            Logger.info(f"Using latest version tag: {latest_tag}")
            return latest_tag
        else:
            Logger.error("No version tags found and no version specified")
            return None

    def _get_latest_version_tag(self) -> Optional[str]:
        """Get the latest version tag from git - reused from get-contributors.py pattern"""
        try:
            original_dir = os.getcwd()
            os.chdir(self.config.repo_path)
            
            # Get all version tags sorted by version
            cmd = ['git', 'tag', '-l', 'v*.*.*']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if not result.stdout.strip():
                return None
            
            tags = result.stdout.strip().split('\n')
            if not tags:
                return None
            
            # Sort tags by semantic version
            sorted_tags = sorted(tags, key=self._parse_version_tag, reverse=True)
            latest_tag = sorted_tags[0]
            
            Logger.info(f"Found latest version tag: {latest_tag}")
            return latest_tag
            
        except subprocess.CalledProcessError as e:
            Logger.debug(f"Failed to get version tags: {e}")
            return None
        finally:
            os.chdir(original_dir)

    def determine_target_tag(self) -> Optional[str]:
        """Determine the target tag for tag-to-tag collection"""
        if self.config.target_version:
            # Try different tag formats for target version
            possible_tags = [
                f"v{self.config.target_version}",  # e.g., "v1.0.1"
                self.config.target_version,  # e.g., "1.0.1"
                f"release-{self.config.target_version}",  # e.g., "release-1.0.1"
            ]
            
            # Change to repository directory to check tags
            original_dir = os.getcwd()
            try:
                os.chdir(self.config.repo_path)
                
                for tag in possible_tags:
                    try:
                        # Check if tag exists
                        cmd = ['git', 'rev-parse', '--verify', f'refs/tags/{tag}']
                        subprocess.run(cmd, capture_output=True, text=True, check=True)
                        Logger.info(f"Found target tag: {tag}")
                        return tag
                    except subprocess.CalledProcessError:
                        Logger.debug(f"Tag {tag} not found")
                        continue
                
                Logger.error(f"Could not find any tag for target version {self.config.target_version}")
                return None
                
            finally:
                os.chdir(original_dir)
        
        # Default: use the latest version tag
        Logger.info("No target version specified, finding latest version tag")
        latest_tag = self._get_latest_version_tag()
        if latest_tag:
            Logger.info(f"Using latest version tag as target: {latest_tag}")
            return latest_tag
        else:
            Logger.warn("No version tags found, using HEAD")
            return "HEAD"

    
    def _get_latest_version_tag(self) -> Optional[str]:
        """Get the latest version tag from git with proper semantic version parsing"""
        try:
            original_dir = os.getcwd()
            os.chdir(self.config.repo_path)
            
            # Get all version tags sorted by version
            cmd = ['git', 'tag', '-l', 'v*.*.*']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                tags = result.stdout.strip().split('\n')
                # Sort tags by semantic version with proper pre-release handling
                tags.sort(key=self._parse_semantic_version)
                return tags[-1]  # Return the latest tag
            
        except subprocess.CalledProcessError as e:
            Logger.debug(f"Failed to get latest tag: {e}")
        finally:
            os.chdir(original_dir)
        
        return None
    
    def _parse_semantic_version(self, tag: str) -> Tuple[int, int, int, int, str]:
        """
        Parse semantic version for sorting, handling pre-release identifiers
        
        Returns tuple: (major, minor, patch, pre_release_order, pre_release_version)
        Pre-release order: 0=M (milestone), 1=RC, 2=GA (no suffix)
        """
        try:
            # Remove 'v' prefix
            version = tag.lstrip('v')
            
            # Split on first dash to separate version from pre-release
            if '-' in version:
                base_version, pre_release = version.split('-', 1)
            else:
                base_version = version
                pre_release = ''
            
            # Parse base version (major.minor.patch)
            parts = base_version.split('.')
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            
            # Parse pre-release identifier
            if not pre_release:
                # GA release - highest priority
                pre_release_order = 2
                pre_release_version = ''
            elif pre_release.startswith('M'):
                # Milestone release - lowest priority
                pre_release_order = 0
                pre_release_version = pre_release
            elif pre_release.startswith('RC'):
                # Release candidate - middle priority
                pre_release_order = 1
                pre_release_version = pre_release
            else:
                # Unknown pre-release type - treat as milestone
                pre_release_order = 0
                pre_release_version = pre_release
            
            return (major, minor, patch, pre_release_order, pre_release_version)
            
        except (ValueError, IndexError) as e:
            Logger.debug(f"Failed to parse version tag {tag}: {e}")
            # Return a very low priority tuple for unparseable tags
            return (0, 0, 0, -1, tag)
    
    def collect_commits_with_metadata(self) -> List[CommitData]:
        """Collect commits with basic metadata using tag-to-tag collection"""
        # Use tag-to-tag collection - the only reliable method
        since_tag = self.determine_since_tag()
        target_tag = self.determine_target_tag()
        
        if not since_tag:
            raise ReleaseNotesError("No since version specified and could not determine from tags. Please specify --since-version.")
        
        # Change to repository directory
        original_dir = os.getcwd()
        try:
            os.chdir(self.config.repo_path)
            
            # Fetch latest tags
            Logger.info("Fetching latest tags from origin")
            fetch_cmd = ['git', 'fetch', '--tags', 'origin']
            subprocess.run(fetch_cmd, capture_output=True, text=True, check=True)
            
            # Build the commit range
            if target_tag and target_tag != "HEAD":
                commit_range = f"{since_tag}..{target_tag}"
                Logger.info(f"Collecting commits from {since_tag} to {target_tag}")
            else:
                commit_range = f"{since_tag}..HEAD"
                Logger.info(f"Collecting commits from {since_tag} to HEAD")
            
            # Get expected count for verification
            count_cmd = ['git', 'rev-list', '--count', commit_range]
            count_result = subprocess.run(count_cmd, capture_output=True, text=True, check=True)
            expected_count = int(count_result.stdout.strip())
            Logger.info(f"Expected commit count: {expected_count}")
            
            # Get commits with detailed format
            cmd = ['git', 'log', commit_range, '--format=%H|%s|%aN|%aE|%aI']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            commit_lines = result.stdout.strip().split('\n')
            if not commit_lines or commit_lines == ['']:
                Logger.warn("No commits found in the specified range")
                return []
            
            actual_count = len(commit_lines)
            if actual_count == expected_count:
                Logger.info(f"✅ Found {actual_count} commits (matches expected count)")
            else:
                Logger.warn(f"⚠️  Found {actual_count} commits but expected {expected_count}")
            
            commits = []
            for line in commit_lines:
                if not line:
                    continue
                
                parts = line.split('|')
                if len(parts) != 5:
                    Logger.debug(f"Skipping malformed commit line: {line}")
                    continue
                
                sha, message, author, email, date = parts
                commit = CommitData(
                    sha=sha,
                    message=message,
                    author=author,
                    email=email,
                    date=date
                )
                commits.append(commit)
            
            Logger.success(f"Collected {len(commits)} commits with metadata using tag-to-tag method")
            return commits
            
        except subprocess.CalledProcessError as e:
            raise ReleaseNotesError(f"Git command failed: {e}")
        finally:
            os.chdir(original_dir)

class GitHubDataEnricher:
    """Enrich commits with GitHub PR and issue information using GraphQL"""
    
    def __init__(self, config: ReleaseNotesConfig):
        self.config = config
        self.github = GitHubAPIHelper(f"{config.repo_owner}/{config.repo_name}", config.github_token)
    
    def enrich_commits_with_prs_and_issues(self, commits: List[CommitData]) -> List[EnrichedCommit]:
        """Enrich commits with PR and issue associations"""
        if not commits:
            return []
        
        Logger.info(f"Enriching {len(commits)} commits with GitHub data...")
        
        # Extract commit SHAs
        commit_shas = [commit.sha for commit in commits]
        Logger.info(f"Processing commits: {[sha[:8] for sha in commit_shas]}")
        
        # Get PR associations using GraphQL
        Logger.info("Fetching PR associations via GitHub GraphQL API...")
        Logger.debug(f"GitHub token available: {'Yes' if self.config.github_token else 'No'}")
        
        pr_associations = self.github.get_commit_pr_associations(commit_shas)
        
        Logger.info(f"Found PR associations for {len(pr_associations) if pr_associations else 0} commits")
        if not pr_associations:
            Logger.warn("❌ No PR associations found - this will limit AI analysis quality")
            Logger.warn("   Check: 1) GitHub token permissions 2) Commits are from PRs 3) API access")
        else:
            for commit_sha, prs in pr_associations.items():
                Logger.info(f"  Commit {commit_sha[:8]}: {len(prs)} PR(s) - {[pr.get('number', 'unknown') for pr in prs]}")
        
        # Create enriched commits
        enriched_commits = []
        
        for commit in commits:
            # Get PRs for this commit
            prs = pr_associations.get(commit.sha, [])
            
            # Collect issues from PR closing references
            issues = []
            category_hints = []
            
            for pr in prs:
                # Add labels as category hints
                category_hints.extend(pr.labels)
                
                # Convert closing issue numbers to Issue objects
                for issue_num in pr.closing_issues:
                    # Create basic issue object (we could enrich this further with another GraphQL call)
                    issue = Issue(
                        number=issue_num,
                        title=f"Issue #{issue_num}",  # Placeholder - could fetch real title
                        url=f"https://github.com/{self.config.repo_owner}/{self.config.repo_name}/issues/{issue_num}",
                        state="UNKNOWN",
                        labels=[]
                    )
                    issues.append(issue)
            
            # Create enriched commit
            enriched_commit = EnrichedCommit(
                commit=commit,
                prs=prs,
                issues=issues,
                category_hints=list(set(category_hints))  # Remove duplicates
            )
            
            enriched_commits.append(enriched_commit)
        
        return enriched_commits
    
    def categorize_by_labels(self, enriched_commits: List[EnrichedCommit]) -> Dict[str, List[EnrichedCommit]]:
        """Simple rule-based categorization using PR labels as fallback"""
        categories = defaultdict(list)
        
        for commit in enriched_commits:
            commit_categories = set()
            
            # Check PR labels for category hints
            for hint in commit.category_hints:
                hint_lower = hint.lower()
                if any(word in hint_lower for word in ['bug', 'fix']):
                    commit_categories.add('bug_fixes')
                elif any(word in hint_lower for word in ['feature', 'enhancement']):
                    commit_categories.add('features')
                elif any(word in hint_lower for word in ['doc', 'documentation']):
                    commit_categories.add('documentation')
                elif any(word in hint_lower for word in ['security']):
                    commit_categories.add('security')
                elif any(word in hint_lower for word in ['performance', 'perf']):
                    commit_categories.add('performance')
                elif any(word in hint_lower for word in ['breaking', 'break']):
                    commit_categories.add('breaking_changes')
            
            # Check commit message for category hints if no labels
            if not commit_categories:
                message_lower = commit.commit.message.lower()
                if any(word in message_lower for word in ['fix', 'bug', 'resolve']):
                    commit_categories.add('bug_fixes')
                elif any(word in message_lower for word in ['add', 'feature', 'implement']):
                    commit_categories.add('features')
                elif any(word in message_lower for word in ['doc', 'documentation', 'readme']):
                    commit_categories.add('documentation')
                elif any(word in message_lower for word in ['refactor', 'cleanup', 'improve']):
                    commit_categories.add('internal')
                else:
                    commit_categories.add('other')
            
            # Add to categories
            for category in commit_categories:
                categories[category].append(commit)
        
        return dict(categories)


class ReleaseNotesAIAnalyzer:
    """AI-powered analysis using Claude Code CLI for intelligent categorization"""
    
    def __init__(self, config: ReleaseNotesConfig):
        self.config = config
        self.claude = ClaudeCodeWrapper(logs_dir=config.claude_logs_dir)
    
    def analyze_changes(self, enriched_commits: List[EnrichedCommit], cost_tracker: CostTracker = None) -> AnalysisResult:
        """Analyze enriched commits using Claude Code for categorization"""
        if not enriched_commits:
            return AnalysisResult()
        
        Logger.info(f"Analyzing {len(enriched_commits)} commits with Claude Code...")
        
        # Check Claude Code availability
        if not self.claude.is_available():
            Logger.warn("Claude Code not available - falling back to rule-based categorization")
            return self._fallback_analysis(enriched_commits)
        
        try:
            # Generate comprehensive prompt
            prompt_content = self._generate_analysis_prompt(enriched_commits)
            prompt_file = self._create_prompt_file(prompt_content)
            
            # Save AI input for debugging if requested
            if self.config.save_ai_input:
                debug_input_file = self.config.logs_dir / f"ai_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(debug_input_file, 'w') as f:
                    f.write(prompt_content)
                Logger.info(f"💾 Saved AI input to: {debug_input_file}")
            
            # Analyze with Claude Code
            Logger.info(f"🤖 Sending {len(enriched_commits)} commits to Claude Code for analysis...")
            result = self.claude.analyze_from_file_with_json(
                prompt_file_path=str(prompt_file),
                timeout=self.config.ai_timeout,
                model=self.config.ai_model,
                show_progress=True
            )
            
            # Extract cost information from result
            cost = self._extract_cost_from_result(result)
            if cost_tracker and cost > 0:
                cost_tracker.add_operation("AI Categorization", cost, len(enriched_commits))
                Logger.info(f"💰 AI Analysis cost: ${cost:.4f}")
            
            if result['success'] and result.get('json_extraction_success'):
                return self._parse_analysis_result(result['json_data'], enriched_commits)
            else:
                Logger.warn(f"AI analysis failed: {result.get('error', 'Unknown error')}")
                return self._fallback_analysis(enriched_commits)
                
        except Exception as e:
            Logger.error(f"AI analysis error: {e}")
            return self._fallback_analysis(enriched_commits)

    def _extract_cost_from_result(self, result: Dict[str, Any]) -> float:
        """Extract cost information from Claude Code result"""
        try:
            # Claude Code wrapper might return cost in various formats
            if 'cost' in result:
                return float(result['cost'])
            elif 'usage' in result and 'cost' in result['usage']:
                return float(result['usage']['cost'])
            elif 'metadata' in result and 'cost' in result['metadata']:
                return float(result['metadata']['cost'])
            else:
                # Try to parse from stdout/stderr for cost information
                output = result.get('stdout', '') + result.get('stderr', '')
                # Look for cost patterns like "$0.1234" or "Cost: $0.1234"
                import re
                cost_patterns = [
                    r'\$(\d+\.\d+)',
                    r'cost[:\s]+\$(\d+\.\d+)',
                    r'(\d+\.\d+)\s*cents'
                ]
                
                for pattern in cost_patterns:
                    matches = re.findall(pattern, output, re.IGNORECASE)
                    if matches:
                        cost = float(matches[-1])  # Take the last match
                        if 'cents' in pattern:
                            cost = cost / 100  # Convert cents to dollars
                        return cost
                
                return 0.0
        except Exception as e:
            Logger.debug(f"Could not extract cost: {e}")
            return 0.0
    
    def _generate_analysis_prompt(self, enriched_commits: List[EnrichedCommit]) -> str:
        """Generate comprehensive analysis prompt for Claude Code"""
        
        # Prepare commit data for analysis
        commits_data = []
        for commit in enriched_commits:
            commit_info = {
                "sha": commit.commit.short_sha,
                "message": commit.commit.message,
                "author": commit.commit.author,
                "prs": [{"number": pr.number, "title": pr.title, "labels": pr.labels} for pr in commit.prs],
                "issues": [{"number": issue.number} for issue in commit.issues],
                "category_hints": commit.category_hints
            }
            commits_data.append(commit_info)
        
        prompt = f"""# Spring AI Release Notes Analysis

## Context
I need you to analyze commits from the Spring AI project to generate professional release notes. You have data for {len(enriched_commits)} commits with associated pull requests and issues.

## Data
```json
{json.dumps(commits_data, indent=2)}
```

## Analysis Task
Analyze this data and categorize changes into Spring AI appropriate categories. For each change:

1. **Categorize** into one of these categories:
   - ✨ **New Features**: New functionality, integrations, model providers
   - 🐛 **Bug Fixes**: Bug fixes, error corrections, stability improvements
   - 💥 **Breaking Changes**: API changes, configuration changes, breaking updates
   - 📚 **Documentation**: Documentation improvements, examples, guides
   - ⚡ **Performance**: Performance improvements, optimizations
   - 🔧 **Internal Changes**: Refactoring, build improvements, dependency updates
   - 🔐 **Security**: Security-related fixes and improvements

2. **Prefer PR titles** over commit messages when available (they're usually better formatted)
3. **Group related changes** when multiple commits/PRs address the same feature
4. **Identify breaking changes** from labels, titles, or descriptions
5. **Create proper linking** in format: (#PR via #issue1, #issue2) or just (#PR) or (commit-sha)

## Spring AI Specific Considerations
- Highlight new model providers (OpenAI, Anthropic, Azure, etc.)
- Note vector database integrations (Chroma, Pinecone, Redis, etc.)
- Call out configuration property changes
- Identify new starters or auto-configurations
- Note function calling and tool integration changes

## Required Output Format
Return ONLY valid JSON in this exact format:

```json
{{
  "highlights": "2-3 sentence summary of most significant changes in this release",
  "breaking_changes": [
    {{
      "title": "Change title",
      "description": "User-facing description",
      "link_text": "(#123 via #456)"
    }}
  ],
  "features": [
    {{
      "title": "Feature title", 
      "description": "User-facing description",
      "link_text": "(#123)"
    }}
  ],
  "bug_fixes": [
    {{
      "title": "Fix title",
      "description": "User-facing description", 
      "link_text": "(#123 via #456)"
    }}
  ],
  "documentation": [
    {{
      "title": "Doc change title",
      "description": "Description",
      "link_text": "(#123)"
    }}
  ],
  "performance": [],
  "internal": [],
  "security": []
}}
```

Focus on changes that affect end users. Group minor related fixes. Make descriptions clear and user-focused.
"""
        
        return prompt
    
    def _create_prompt_file(self, prompt_content: str) -> Path:
        """Create prompt file for Claude Code analysis"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        prompt_file = self.config.claude_logs_dir / f"release-notes-analysis-{timestamp}.md"
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        
        Logger.debug(f"Created analysis prompt file: {prompt_file}")
        return prompt_file
    
    def _parse_analysis_result(self, json_data: Dict[str, Any], enriched_commits: List[EnrichedCommit]) -> AnalysisResult:
        """Parse JSON analysis result into AnalysisResult object"""
        if not json_data:
            Logger.warn("No JSON data from AI analysis")
            return self._fallback_analysis(enriched_commits)
        
        def create_categorized_changes(changes_list: List[Dict]) -> List[CategorizedChange]:
            categorized_changes = []
            for change_data in changes_list:
                if isinstance(change_data, dict):
                    change = CategorizedChange(
                        title=change_data.get('title', ''),
                        description=change_data.get('description', ''),
                        link_text=change_data.get('link_text', ''),
                        category=change_data.get('category', 'other'),
                        breaking=change_data.get('breaking', False)
                    )
                    categorized_changes.append(change)
            return categorized_changes
        
        return AnalysisResult(
            highlights=json_data.get('highlights', ''),
            breaking_changes=create_categorized_changes(json_data.get('breaking_changes', [])),
            features=create_categorized_changes(json_data.get('features', [])),
            bug_fixes=create_categorized_changes(json_data.get('bug_fixes', [])),
            documentation=create_categorized_changes(json_data.get('documentation', [])),
            performance=create_categorized_changes(json_data.get('performance', [])),
            internal=create_categorized_changes(json_data.get('internal', [])),
            security=create_categorized_changes(json_data.get('security', []))
        )
    
    def _fallback_analysis(self, enriched_commits: List[EnrichedCommit]) -> AnalysisResult:
        """Fallback rule-based analysis when AI is not available"""
        Logger.info("Using rule-based analysis as fallback...")
        
        # Simple categorization logic
        features = []
        bug_fixes = []
        documentation = []
        internal = []
        
        for commit in enriched_commits:
            # Create basic categorized change
            if commit.prs:
                title = commit.prs[0].title
                link_text = commit.link_text
            else:
                title = commit.commit.message.split('\n')[0]  # First line
                link_text = f"({commit.commit.short_sha})"
            
            change = CategorizedChange(
                title=title,
                description=title,
                link_text=link_text,
                category="other",
                commit=commit
            )
            
            # Simple categorization
            message_lower = commit.commit.message.lower()
            if any(word in message_lower for word in ['fix', 'bug', 'resolve', 'correct']):
                bug_fixes.append(change)
            elif any(word in message_lower for word in ['add', 'feature', 'implement', 'support']):
                features.append(change)
            elif any(word in message_lower for word in ['doc', 'documentation', 'readme']):
                documentation.append(change)
            else:
                internal.append(change)
        
        return AnalysisResult(
            highlights=f"This release includes {len(features)} new features, {len(bug_fixes)} bug fixes, and {len(documentation)} documentation improvements.",
            features=features,
            bug_fixes=bug_fixes,
            documentation=documentation,
            internal=internal
        )


@dataclass
class Contributor:
    """Contributor information for acknowledgments"""
    name: str
    username: str
    email: Optional[str] = None
    commits_count: int = 0
    
    @property
    def github_url(self) -> str:
        return f"https://github.com/{self.username}"
    
    @property
    def markdown_entry(self) -> str:
        return f"- [{self.name} (@{self.username})]({self.github_url})"


class ReleaseNotesGenerator:
    """Generate markdown release notes from analysis results"""
    
    def __init__(self, config: ReleaseNotesConfig):
        self.config = config
    
    def extract_contributors(self, enriched_commits: List[EnrichedCommit]) -> List[Contributor]:
        """Extract unique contributors from commits"""
        contributors_map = {}
        
        for commit in enriched_commits:
            author = commit.commit.author
            email = commit.commit.email
            
            # Extract username from email if it's a GitHub noreply email
            username = self._extract_username_from_email(email)
            
            key = username.lower()
            if key not in contributors_map:
                contributors_map[key] = Contributor(
                    name=author,
                    username=username,
                    email=email,
                    commits_count=0
                )
            
            contributors_map[key].commits_count += 1
        
        # Sort contributors by name
        contributors = list(contributors_map.values())
        contributors.sort(key=lambda c: c.name.lower())
        
        return contributors
    
    def _extract_username_from_email(self, email: str) -> str:
        """Extract username from email address - reused from get-contributors.py logic"""
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
    
    def generate_markdown(self, analysis_result: AnalysisResult, contributors: List[Contributor], 
                         enriched_commits: List[EnrichedCommit]) -> str:
        """Generate complete markdown release notes"""
        lines = []
        
        # Title (use target version if specified)
        version = self.config.target_version or "Next Release"
        lines.append(f"# Spring AI {version} Release Notes")
        lines.append("")
        
        # Highlights section
        if analysis_result.highlights:
            lines.append("## 🎯 Highlights")
            lines.append(analysis_result.highlights)
            lines.append("")
        
        # Breaking changes (most important - show first)
        if analysis_result.breaking_changes:
            lines.append("## 💥 Breaking Changes")
            for change in analysis_result.breaking_changes:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # New features
        if analysis_result.features:
            lines.append("## ✨ New Features")
            for change in analysis_result.features:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Bug fixes
        if analysis_result.bug_fixes:
            lines.append("## 🐛 Bug Fixes")
            for change in analysis_result.bug_fixes:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Documentation
        if analysis_result.documentation:
            lines.append("## 📚 Documentation")
            for change in analysis_result.documentation:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Performance improvements
        if analysis_result.performance:
            lines.append("## ⚡ Performance")
            for change in analysis_result.performance:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Security improvements
        if analysis_result.security:
            lines.append("## 🔐 Security")
            for change in analysis_result.security:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Internal changes
        if analysis_result.internal:
            lines.append("## 🔧 Internal Changes")
            for change in analysis_result.internal:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Contributors section
        if self.config.include_contributors and contributors:
            lines.append("## 🙏 Contributors")
            lines.append("")
            lines.append("Thanks to all contributors who made this release possible:")
            lines.append("")
            for contributor in contributors:
                lines.append(contributor.markdown_entry)
            lines.append("")
        
        # Statistics section
        if self.config.include_stats:
            lines.append("## 📈 Statistics")
            
            # Calculate stats
            total_prs = sum(len(commit.prs) for commit in enriched_commits)
            total_issues = sum(len(commit.issues) for commit in enriched_commits)
            commits_with_prs = len([c for c in enriched_commits if c.prs])
            
            lines.append(f"- {len(enriched_commits)} commits from {len(contributors)} contributors")
            lines.append(f"- {total_prs} pull requests merged")
            lines.append(f"- {total_issues} issues resolved")
            lines.append(f"- {commits_with_prs} commits associated with pull requests")
            lines.append("")
        
        # Debug data section (if requested)
        if self.config.include_debug_data:
            lines.append("## 🔍 Debug Information")
            lines.append("")
            lines.append("<details>")
            lines.append("<summary>Click to expand debug data</summary>")
            lines.append("")
            lines.append("### Generation Details")
            lines.append(f"- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"- AI Analysis: {'Enabled' if self.config.use_ai else 'Disabled'}")
            lines.append(f"- Repository: {self.config.repo_owner}/{self.config.repo_name}")
            lines.append(f"- Since version: {self.config.since_version}")
            lines.append(f"- Since date: {self.config.since_date}")
            lines.append("")
            
            # Show categorization breakdown
            total_categorized = (len(analysis_result.features) + len(analysis_result.bug_fixes) + 
                               len(analysis_result.breaking_changes) + len(analysis_result.documentation))
            
            lines.append("### Categorization Breakdown")
            lines.append(f"- Features: {len(analysis_result.features)}")
            lines.append(f"- Bug Fixes: {len(analysis_result.bug_fixes)}")
            lines.append(f"- Breaking Changes: {len(analysis_result.breaking_changes)}")
            lines.append(f"- Documentation: {len(analysis_result.documentation)}")
            lines.append(f"- Performance: {len(analysis_result.performance)}")
            lines.append(f"- Internal: {len(analysis_result.internal)}")
            lines.append(f"- Security: {len(analysis_result.security)}")
            lines.append(f"- Total Categorized: {total_categorized}")
            lines.append("")
            lines.append("</details>")
            lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*Generated automatically by [generate-release-notes.py](https://github.com/spring-projects/spring-ai-project-mgmt) on {datetime.now().strftime('%Y-%m-%d')}*")
        
        return '\n'.join(lines)
    
    def write_markdown_file(self, markdown_content: str) -> None:
        """Write markdown content to output file"""
        # Ensure output directory exists
        self.config.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        with open(self.config.output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        Logger.info(f"Release notes written to: {self.config.output_file}")
        Logger.info(f"File size: {len(markdown_content)} characters")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate Spring AI release notes with AI-powered categorization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Tag-to-latest commits (requires --since-version)
  python3 generate-release-notes.py --since-version 1.0.0

  # Specific tag-to-tag range
  python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1

  # Testing with limited commits
  python3 generate-release-notes.py --since-version 1.0.0 --limit 5 --verbose

  # Skip AI analysis (rule-based only)
  python3 generate-release-notes.py --no-ai

  # Include debug data
  python3 generate-release-notes.py --include-debug-data
        """
    )
    
    parser.add_argument('--since-version', 
                       help='Version tag to collect changes since (e.g., 1.0.0)')
    parser.add_argument('--target-version', 
                       help='Target version for this release (e.g., 1.0.1)')
    parser.add_argument('--repo-path', 
                       default='/home/mark/projects/spring-ai',
                       help='Path to Spring AI repository')
    parser.add_argument('--branch',
                       default='1.0.x',
                       help='Branch to analyze (default: 1.0.x)')
    parser.add_argument('--output', '-o',
                       default='RELEASE_NOTES.md',
                       help='Output file for release notes')
    parser.add_argument('--no-ai',
                       action='store_true',
                       help='Skip AI analysis, use rule-based categorization only')
    parser.add_argument('--ai-model',
                       default='sonnet',
                       help='AI model to use (default: sonnet for cost control)')
    parser.add_argument('--ai-timeout',
                       type=int,
                       default=300,
                       help='AI analysis timeout in seconds (default: 300)')
    parser.add_argument('--no-contributors',
                       action='store_true',
                       help='Skip contributor acknowledgments')
    parser.add_argument('--no-stats',
                       action='store_true',
                       help='Skip statistics section')
    parser.add_argument('--include-debug-data',
                       action='store_true',
                       help='Include debug data in output')
    parser.add_argument('--count-only',
                       action='store_true',
                       help='Only count commits without generating release notes')
    parser.add_argument('--limit',
                       type=int,
                       help='Limit to first N commits for testing (e.g., --limit 10)')
    parser.add_argument('--sample',
                       type=int,
                       help='Randomly sample N commits for testing (e.g., --sample 5)')
    parser.add_argument('--skip-github',
                       action='store_true',
                       help='Skip GitHub API enrichment to test AI categorization only')
    parser.add_argument('--save-ai-input',
                       action='store_true',
                       help='Save AI prompt input to logs for debugging')
    parser.add_argument('--logs-dir',
                       default='./logs/release-notes',
                       help='Directory for debug logs (default: ./logs/release-notes)')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Preview changes without writing output file')
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--debug-github',
                       action='store_true',
                       help='Enable detailed GitHub API debugging (shows queries and responses)')
    
    args = parser.parse_args()
    
    # Set debug mode
    if args.verbose or args.debug_github:
        os.environ['DEBUG'] = '1'
    
    if args.debug_github:
        os.environ['DEBUG_GITHUB'] = '1'
    
    # Create configuration
    script_dir = Path(__file__).parent.resolve()
    config = ReleaseNotesConfig(
        repo_path=Path(args.repo_path),
        branch=args.branch,
        since_version=args.since_version,
        target_version=args.target_version,
        output_file=Path(args.output),
        use_ai=not args.no_ai,
        ai_model=args.ai_model,
        ai_timeout=args.ai_timeout,
        include_contributors=not args.no_contributors,
        include_stats=not args.no_stats,
        include_debug_data=args.include_debug_data,
        dry_run=args.dry_run,
        verbose=args.verbose,
        limit=args.limit,
        sample=args.sample,
        skip_github=args.skip_github,
        save_ai_input=args.save_ai_input,
        logs_dir=Path(args.logs_dir),
        claude_logs_dir=Path(args.logs_dir) / "claude"
    )
    
    try:
        # Setup logging directory
        config.logs_dir.mkdir(parents=True, exist_ok=True)
        config.claude_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize cost tracker
        cost_tracker = CostTracker()
        
        Logger.bold("🚀 SPRING AI RELEASE NOTES GENERATOR")
        Logger.bold("="*50)
        
        if config.verbose:
            Logger.info(f"Repository: {config.repo_owner}/{config.repo_name}")
            Logger.info(f"Repository Path: {config.repo_path}")
            Logger.info(f"Output File: {config.output_file}")
            Logger.info(f"AI Analysis: {'Enabled' if config.use_ai else 'Disabled'}")
            Logger.info(f"Dry Run: {config.dry_run}")
        
        # Check repository exists
        if not config.repo_path.exists():
            raise ReleaseNotesError(f"Repository path does not exist: {config.repo_path}")
        
        # Phase 1: Collect commits
        Logger.info("Phase 1: Collecting commits...")
        collector = GitCommitCollector(config)
        commits = collector.collect_commits_with_metadata()
        
        if not commits:
            Logger.warn("No commits found - nothing to analyze")
            return 0
        
        Logger.success(f"Collected {len(commits)} commits")
        
        # Check for count-only mode
        if args.count_only:
            Logger.bold("🎯 COUNT-ONLY MODE")
            Logger.success(f"Total commits found: {len(commits)}")
            Logger.info("Skipping release notes generation as requested")
            return 0
        
        # Apply testing filters (limit/sample)
        original_count = len(commits)
        if config.limit:
            commits = commits[:config.limit]
            Logger.warn(f"🧪 TESTING: Limited to first {len(commits)} commits (out of {original_count})")
        elif config.sample:
            import random
            if config.sample < len(commits):
                commits = random.sample(commits, config.sample)
                Logger.warn(f"🧪 TESTING: Randomly sampled {len(commits)} commits (out of {original_count})")
            else:
                Logger.info(f"Sample size ({config.sample}) >= total commits ({len(commits)}), using all")
        
        if config.skip_github:
            Logger.warn("🧪 TESTING: Skipping GitHub API enrichment as requested")
        
        # Phase 2: Enrich with GitHub data (or skip for testing)
        if config.skip_github:
            Logger.info("Phase 2: Skipping GitHub enrichment for testing...")
            # Create minimal enriched commits without API calls
            enriched_commits = [
                EnrichedCommit(
                    commit=commit,
                    prs=[],
                    primary_link=f"https://github.com/{config.repo_owner}/{config.repo_name}/commit/{commit.sha}",
                    category_hints=[]
                ) for commit in commits
            ]
        else:
            Logger.info("Phase 2: Enriching commits with GitHub PR/issue data...")
            enricher = GitHubDataEnricher(config)
            enriched_commits = enricher.enrich_commits_with_prs_and_issues(commits)
        
        Logger.success(f"Enriched {len(enriched_commits)} commits with GitHub data")
        
        # Show enrichment statistics
        pr_count = sum(len(commit.prs) for commit in enriched_commits)
        issue_count = sum(len(commit.issues) for commit in enriched_commits)
        commits_with_prs = len([c for c in enriched_commits if c.prs])
        
        Logger.info(f"Found {pr_count} PRs associated with {commits_with_prs} commits")
        Logger.info(f"Found {issue_count} issues referenced by PRs")
        
        if config.verbose:
            # Show sample of enriched commits
            Logger.info("Sample enriched commits:")
            for i, commit in enumerate(enriched_commits[:3]):
                pr_info = f"{len(commit.prs)} PRs" if commit.prs else "no PRs"
                Logger.info(f"  {commit.commit.short_sha}: {commit.commit.message[:50]}... ({pr_info})")
        
        # Phase 3: AI analysis (if enabled)
        if config.use_ai:
            Logger.info("Phase 3: AI-powered categorization and analysis...")
            analyzer = ReleaseNotesAIAnalyzer(config)
            analysis_result = analyzer.analyze_changes(enriched_commits, cost_tracker)
            Logger.success("AI analysis completed")
        else:
            Logger.info("Phase 3: Rule-based categorization (AI disabled)...")
            # Fallback to rule-based categorization
            categories = enricher.categorize_by_labels(enriched_commits)
            analysis_result = AnalysisResult(
                highlights="Release notes generated using rule-based categorization",
                features=[],
                bug_fixes=[],
                # TODO: Convert categories to CategorizedChange objects
            )
            Logger.success("Rule-based categorization completed")
        
        # Phase 4: Generate markdown
        Logger.info("Phase 4: Generating markdown release notes...")
        generator = ReleaseNotesGenerator(config)
        
        # Generate contributor acknowledgments if requested
        contributors = []
        if config.include_contributors:
            Logger.info("Generating contributor acknowledgments...")
            contributors = generator.extract_contributors(enriched_commits)
            Logger.info(f"Found {len(contributors)} unique contributors")
        
        # Generate markdown
        markdown_content = generator.generate_markdown(analysis_result, contributors, enriched_commits)
        
        if config.dry_run:
            Logger.info("DRY RUN: Generated release notes preview:")
            Logger.bold("="*60)
            # Show first 1000 characters of generated markdown
            preview = markdown_content[:1000] + "..." if len(markdown_content) > 1000 else markdown_content
            print(preview)
            Logger.bold("="*60)
            Logger.info(f"Full markdown length: {len(markdown_content)} characters")
        else:
            # Write to output file
            generator.write_markdown_file(markdown_content)
            Logger.success(f"Release notes written to: {config.output_file}")
        
        Logger.bold("🎉 Release notes generation completed!")
        
        # Show summary statistics
        total_changes = (len(analysis_result.features) + len(analysis_result.bug_fixes) + 
                        len(analysis_result.breaking_changes) + len(analysis_result.documentation) + 
                        len(analysis_result.performance) + len(analysis_result.internal) + 
                        len(analysis_result.security))
        
        Logger.info(f"📊 Summary:")
        Logger.info(f"  • {len(enriched_commits)} commits analyzed")
        Logger.info(f"  • {pr_count} PRs processed")
        Logger.info(f"  • {issue_count} issues referenced")
        Logger.info(f"  • {total_changes} categorized changes")
        Logger.info(f"  • {len(contributors)} contributors")
        
        # Display cost summary
        Logger.bold("\n" + cost_tracker.get_summary())
        
        # Save cost tracking to file
        cost_file = config.logs_dir / f"costs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        cost_tracker.save_to_file(cost_file)
        Logger.info(f"💾 Cost tracking saved to: {cost_file}")
        
        return 0
        
    except ReleaseNotesError as e:
        Logger.error(str(e))
        return 1
    except KeyboardInterrupt:
        Logger.warn("Operation cancelled by user")
        return 1
    except Exception as e:
        Logger.error(f"Unexpected error: {e}")
        if config.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
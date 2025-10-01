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
- Cross-branch backport analysis for proper PR attribution

Backport Analysis:
Spring AI uses a backport workflow where PRs are merged to main branch with labels like 
"for: backport-to-1.0.x", then manually backported to release branches as direct commits.
This script automatically:
- Extracts PR references from backport commit messages using regex patterns
- Verifies original PRs have backport labels on main branch
- Links backported commits to their original PRs for proper attribution
- Generates release notes with original PR links instead of just commit hashes

Usage:
    python3 generate-release-notes.py --since-version 1.0.0    # Since specific version tag
    python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1   # Tag-to-tag range
    python3 generate-release-notes.py --since-version 1.0.0 --limit 5 --verbose      # Test with limited commits
    
    # GitHub Release Automation:
    python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1 --create-github-release
    python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1 --create-github-release --release-draft
    python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1 --create-github-release --dry-run
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

# Import centralized git tag utilities
from git_tag_utils import get_latest_version_tag, parse_semantic_version


@dataclass 
class TokenUsage:
    """Detailed token usage information"""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    
    def total_input_tokens(self) -> int:
        """Total input tokens including cache operations"""
        return self.input_tokens + self.cache_creation_input_tokens + self.cache_read_input_tokens
    
    def calculate_cost_sonnet4(self) -> float:
        """Calculate cost based on Claude Sonnet 4 pricing"""
        # Claude Sonnet 4 pricing (per million tokens)
        INPUT_COST_PER_MTOK = 3.00  # $3.00 per million tokens
        OUTPUT_COST_PER_MTOK = 15.00  # $15.00 per million tokens  
        CACHE_WRITE_COST_PER_MTOK = 3.75  # $3.75 per million tokens
        CACHE_READ_COST_PER_MTOK = 0.30  # $0.30 per million tokens
        
        # Calculate costs (convert to millions)
        input_cost = (self.input_tokens / 1_000_000) * INPUT_COST_PER_MTOK
        output_cost = (self.output_tokens / 1_000_000) * OUTPUT_COST_PER_MTOK
        cache_write_cost = (self.cache_creation_input_tokens / 1_000_000) * CACHE_WRITE_COST_PER_MTOK
        cache_read_cost = (self.cache_read_input_tokens / 1_000_000) * CACHE_READ_COST_PER_MTOK
        
        return input_cost + output_cost + cache_write_cost + cache_read_cost

class CostTracker:
    """Track and report AI analysis costs with detailed token breakdown"""
    
    def __init__(self):
        self.operations = []
        self.total_cost = 0.0
        self.total_tokens = TokenUsage()
    
    def add_operation(self, operation_name: str, cost: float, commit_count: int = 0, token_usage: TokenUsage = None):
        """Add a cost operation with detailed token information"""
        operation = {
            'operation': operation_name,
            'cost': cost,
            'commit_count': commit_count,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'token_usage': token_usage
        }
        self.operations.append(operation)
        self.total_cost += cost
        
        # Add to total token usage
        if token_usage:
            self.total_tokens.input_tokens += token_usage.input_tokens
            self.total_tokens.output_tokens += token_usage.output_tokens
            self.total_tokens.cache_creation_input_tokens += token_usage.cache_creation_input_tokens
            self.total_tokens.cache_read_input_tokens += token_usage.cache_read_input_tokens
    
    def get_summary(self) -> str:
        """Get detailed cost and token usage summary"""
        if not self.operations:
            return "💰 No AI operations performed - Total cost: $0.00"
        
        summary = [f"💰 AI ANALYSIS COST SUMMARY"]
        summary.append("=" * 40)
        
        # Show per-operation breakdown
        for op in self.operations:
            commits_info = f" ({op['commit_count']} commits)" if op['commit_count'] > 0 else ""
            summary.append(f"• {op['operation']}{commits_info}: ${op['cost']:.4f}")
            
            # Show token usage if available
            if op.get('token_usage'):
                usage = op['token_usage']
                summary.append(f"  └─ Tokens: {usage.input_tokens:,} in, {usage.output_tokens:,} out")
                if usage.cache_creation_input_tokens > 0:
                    summary.append(f"  └─ Cache: {usage.cache_creation_input_tokens:,} write, {usage.cache_read_input_tokens:,} read")
        
        # Show total summary
        summary.append("-" * 40)
        total_input = self.total_tokens.total_input_tokens()
        summary.append(f"📊 TOTAL TOKENS: {total_input:,} input, {self.total_tokens.output_tokens:,} output")
        if self.total_tokens.cache_creation_input_tokens > 0 or self.total_tokens.cache_read_input_tokens > 0:
            summary.append(f"📊 CACHE TOKENS: {self.total_tokens.cache_creation_input_tokens:,} write, {self.total_tokens.cache_read_input_tokens:,} read")
        
        summary.append("-" * 40)
        summary.append(f"🎯 TOTAL COST: ${self.total_cost:.4f}")
        
        return "\n".join(summary)
    
    def save_to_file(self, filepath: Path):
        """Save cost tracking to file with detailed token breakdown"""
        with open(filepath, 'w') as f:
            f.write(self.get_summary())
            f.write("\n\nDetailed Operations:\n")
            f.write("=" * 60 + "\n")
            
            for op in self.operations:
                f.write(f"{op['timestamp']}: {op['operation']}\n")
                f.write(f"  Cost: ${op['cost']:.4f}\n")
                f.write(f"  Commits: {op['commit_count']}\n")
                
                if op.get('token_usage'):
                    usage = op['token_usage']
                    f.write(f"  Tokens - Input: {usage.input_tokens:,}, Output: {usage.output_tokens:,}\n")
                    if usage.cache_creation_input_tokens > 0 or usage.cache_read_input_tokens > 0:
                        f.write(f"  Cache - Write: {usage.cache_creation_input_tokens:,}, Read: {usage.cache_read_input_tokens:,}\n")
                    f.write(f"  Rate - Input: ${usage.input_tokens * 3.0 / 1_000_000:.6f}, Output: ${usage.output_tokens * 15.0 / 1_000_000:.6f}\n")
                
                f.write("-" * 40 + "\n")


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
        """Generate markdown hyperlinks like '[#123](url) via [#456](url)'"""
        if not self.prs:
            # Return commit link: [2082a59](https://github.com/spring-projects/spring-ai/commit/sha)
            return f"[{self.commit.short_sha}]({self.commit.commit_url})"
        
        pr_links = []
        issue_links = []
        
        for pr in self.prs:
            # Generate PR markdown link: [#123](https://github.com/spring-projects/spring-ai/pull/123)
            pr_url = f"https://github.com/spring-projects/spring-ai/pull/{pr.number}"
            pr_links.append(f"[#{pr.number}]({pr_url})")
            
            for issue_num in pr.closing_issues:
                if issue_num not in [i.number for i in self.issues]:
                    # Generate issue markdown link: [#456](https://github.com/spring-projects/spring-ai/issues/456)
                    issue_url = f"https://github.com/spring-projects/spring-ai/issues/{issue_num}"
                    issue_links.append(f"[#{issue_num}]({issue_url})")
        
        # Add direct issues
        for issue in self.issues:
            issue_link = f"[#{issue.number}]({issue.url})"
            if issue_link not in issue_links:
                issue_links.append(issue_link)
        
        if issue_links:
            return f"{', '.join(pr_links)} via {', '.join(issue_links)}"
        else:
            return f"{', '.join(pr_links)}"


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
    repo_path: Path = Path("./spring-ai-release")
    branch: str = "1.0.x"
    
    # Version settings (tag-based only)
    since_version: Optional[str] = None
    target_version: Optional[str] = None
    
    # AI analysis settings
    ai_model: str = "sonnet"  # Cost control
    ai_timeout: int = 300
    claude_logs_dir: Path = Path("./logs")
    use_ai: bool = True
    ai_batch_size: int = 10  # Maximum commits per AI analysis batch
    
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
class GitHubReleaseConfig:
    """Configuration for GitHub release creation"""
    version: str
    release_notes_file: str = "RELEASE_NOTES.md"
    repo: str = "spring-projects/spring-ai"
    title: Optional[str] = None  # Auto-generate from version if None
    draft: bool = False
    prerelease: bool = False
    generate_notes: bool = True  # Auto-generate if notes file missing
    target_commitish: str = "1.0.x"  # Branch or SHA for release
    tag_name: Optional[str] = None  # Auto-generate from version if None
    discussion_category: Optional[str] = None  # Enable discussions
    latest: bool = True  # Mark as latest release
    published_at: Optional[str] = None  # Custom release date (ISO 8601 format: 2024-12-15T10:30:00Z)
    use_tag_date: bool = True  # Automatically use the tag's creation date for the release
    
    def __post_init__(self):
        # Auto-generate title if not provided
        if not self.title:
            self.title = f"Spring AI {self.version}"
        
        # Auto-generate tag name if not provided
        if not self.tag_name:
            self.tag_name = f"v{self.version}" if not self.version.startswith('v') else self.version
    
    @property
    def is_patch_release(self) -> bool:
        """Check if this is a patch release (x.y.z)"""
        version = self.version.replace('v', '')
        parts = version.split('.')
        return len(parts) >= 3 and parts[2].isdigit()
    
    @property
    def is_prerelease_version(self) -> bool:
        """Check if version indicates prerelease (M1, M2, RC, etc.)"""
        return any(marker in self.version.upper() for marker in ['M1', 'M2', 'M3', 'RC', 'SNAPSHOT', 'ALPHA', 'BETA'])


@dataclass
class AnalysisResult:
    """Result of AI analysis - aligned with Spring ecosystem standards"""
    highlights: str = ""
    breaking_changes: List[CategorizedChange] = field(default_factory=list)
    features: List[CategorizedChange] = field(default_factory=list)
    bug_fixes: List[CategorizedChange] = field(default_factory=list)
    documentation: List[CategorizedChange] = field(default_factory=list)
    dependency_upgrades: List[CategorizedChange] = field(default_factory=list)
    performance: List[CategorizedChange] = field(default_factory=list)
    build_updates: List[CategorizedChange] = field(default_factory=list)
    security: List[CategorizedChange] = field(default_factory=list)
    noteworthy: List[CategorizedChange] = field(default_factory=list)
    upgrading_notes: List[CategorizedChange] = field(default_factory=list)
    other: List[CategorizedChange] = field(default_factory=list)
    
    # Deprecated - map to new categories for backward compatibility
    internal: List[CategorizedChange] = field(default_factory=list)  # Maps to build_updates
    accessibility: List[CategorizedChange] = field(default_factory=list)  # Maps to other


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
            
            # Get the commit date for the tag
            cmd = ['git', 'log', '-1', '--format=%aI', tag]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=repo_path)
            
            if result.stdout.strip():
                # Convert ISO format to simple date
                date = datetime.fromisoformat(result.stdout.strip().replace('Z', '+00:00'))
                return date.strftime('%Y-%m-%d')
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to get tag date for {tag}: {e}")
        
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


class GitHubReleaseAutomator:
    """Handle GitHub release creation and management"""
    
    def __init__(self, config: ReleaseNotesConfig):
        self.config = config
        self.github = GitHubAPIHelper(f"{config.repo_owner}/{config.repo_name}", config.github_token)
    
    def create_github_release(self, release_config: GitHubReleaseConfig, release_notes_content: str) -> bool:
        """Create a GitHub release using the generated release notes"""
        Logger.info(f"🚀 Creating GitHub release {release_config.tag_name}...")
        
        # Validate prerequisites  
        if not self.validate_release_prerequisites(release_config):
            return False
        
        # Write release notes to file if needed
        notes_file = Path(release_config.release_notes_file)
        if not notes_file.exists() or release_config.generate_notes:
            Logger.info(f"Writing release notes to {notes_file}")
            with open(notes_file, 'w') as f:
                f.write(release_notes_content)
        
        # Get tag date if requested and not explicitly provided
        if release_config.use_tag_date and not release_config.published_at:
            tag_date = self.get_tag_date(release_config.tag_name)
            if tag_date:
                release_config.published_at = tag_date
                Logger.info(f"📅 Using tag creation date for release: {tag_date}")
            else:
                Logger.warn(f"⚠️ Could not determine date for tag {release_config.tag_name}, using current time")
        
        # Use REST API if custom published_at date is specified (GitHub CLI doesn't support this)
        if release_config.published_at:
            Logger.info(f"📅 Creating release with custom date: {release_config.published_at}")
            return self.create_release_with_api(release_config, release_notes_content)
        else:
            # Use GitHub CLI for standard release creation
            return self.create_release_with_gh_cli(release_config, notes_file)
    
    def get_tag_date(self, tag_name: str) -> Optional[str]:
        """Get the creation date of a git tag in ISO 8601 format"""
        try:
            # Get tag date using git command
            # Use git log to get the date of the commit that the tag points to
            cmd = ['git', 'log', '-1', '--format=%aI', tag_name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=self.config.repo_path)
            tag_date = result.stdout.strip()
            
            Logger.debug(f"Tag {tag_name} creation date: {tag_date}")
            return tag_date
            
        except subprocess.CalledProcessError as e:
            Logger.debug(f"Failed to get tag date for {tag_name}: {e}")
            return None
    
    def create_release_with_api(self, release_config: GitHubReleaseConfig, release_notes_content: str) -> bool:
        """Create a GitHub release using REST API (supports custom published_at date)"""
        if not self.config.github_token:
            Logger.error("❌ GitHub token required for API-based release creation")
            Logger.error("Set GITHUB_TOKEN environment variable or provide token in config")
            return False
        
        # Prepare release data
        release_data = {
            "tag_name": release_config.tag_name,
            "target_commitish": release_config.target_commitish,
            "name": release_config.title,
            "body": release_notes_content,
            "draft": release_config.draft,
            "prerelease": release_config.prerelease or release_config.is_prerelease_version,
            "published_at": release_config.published_at
        }
        
        if release_config.discussion_category:
            release_data["discussion_category_name"] = release_config.discussion_category
        
        Logger.info("Creating GitHub release via REST API...")
        Logger.debug(f"Release data: tag={release_config.tag_name}, date={release_config.published_at}")
        
        try:
            # Create release via GitHub API
            url = f"https://api.github.com/repos/{release_config.repo}/releases"
            headers = {
                "Authorization": f"token {self.config.github_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=release_data, headers=headers)
            response.raise_for_status()
            
            release_info = response.json()
            Logger.success(f"✅ GitHub release {release_config.tag_name} created successfully with tag date!")
            Logger.info(f"🔗 Release URL: {release_info['html_url']}")
            Logger.info(f"📅 Published at: {release_info['published_at']}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            Logger.error(f"❌ Failed to create GitHub release via API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    Logger.error(f"API Error: {error_data}")
                except:
                    Logger.error(f"Response: {e.response.text}")
            return False
    
    def create_release_with_gh_cli(self, release_config: GitHubReleaseConfig, notes_file: Path) -> bool:
        """Create a GitHub release using GitHub CLI (standard flow)"""
        # Build GitHub CLI command
        cmd = self.build_release_command(release_config, notes_file)
        
        if self.config.dry_run:
            Logger.info("🧪 DRY RUN - Would execute command:")
            Logger.info(f"  {' '.join(cmd)}")
            return True
        
        # Execute release creation
        try:
            Logger.info("Creating GitHub release...")
            Logger.debug(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.stdout:
                Logger.info(f"✅ Release created successfully!")
                Logger.info(f"Release URL: {result.stdout.strip()}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"❌ Failed to create GitHub release: {e}")
            Logger.error(f"Command output: {e.stdout}")
            Logger.error(f"Command error: {e.stderr}")
            return False
    
    def validate_release_prerequisites(self, release_config: GitHubReleaseConfig) -> bool:
        """Validate prerequisites for creating a GitHub release"""
        Logger.info("Validating release prerequisites...")
        
        # Check GitHub CLI availability
        if not self.github.is_gh_available():
            Logger.error("❌ GitHub CLI is not available or not authenticated")
            Logger.error("Please run: gh auth login")
            return False
        
        # Check if tag already exists
        if self.tag_exists(release_config.tag_name):
            # Check if release already exists
            if self.release_exists(release_config.tag_name):
                Logger.warn(f"⚠️  Release {release_config.tag_name} already exists")
                return self.confirm_release_update(release_config)
            else:
                Logger.info(f"✅ Tag {release_config.tag_name} exists but no release found")
        else:
            Logger.info(f"✅ Tag {release_config.tag_name} will be created")
        
        # Validate target branch/commit
        if not self.validate_target_commitish(release_config.target_commitish):
            Logger.error(f"❌ Invalid target commitish: {release_config.target_commitish}")
            return False
        
        Logger.info("✅ All prerequisites validated")
        return True
    
    def tag_exists(self, tag_name: str) -> bool:
        """Check if a git tag exists"""
        try:
            cmd = ['gh', 'api', f'/repos/{self.config.repo_owner}/{self.config.repo_name}/git/refs/tags/{tag_name}']
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def release_exists(self, tag_name: str) -> bool:
        """Check if a GitHub release exists for the tag"""
        try:
            cmd = ['gh', 'api', f'/repos/{self.config.repo_owner}/{self.config.repo_name}/releases/tags/{tag_name}']
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def validate_target_commitish(self, target_commitish: str) -> bool:
        """Validate that target_commitish exists (branch or SHA)"""
        try:
            # Check if it's a branch
            cmd = ['gh', 'api', f'/repos/{self.config.repo_owner}/{self.config.repo_name}/branches/{target_commitish}']
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                Logger.debug(f"Found branch: {target_commitish}")
                return True
            
            # Check if it's a valid commit SHA
            if len(target_commitish) >= 7:  # Minimum SHA length
                cmd = ['gh', 'api', f'/repos/{self.config.repo_owner}/{self.config.repo_name}/commits/{target_commitish}']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    Logger.debug(f"Found commit: {target_commitish}")
                    return True
            
            return False
        except Exception as e:
            Logger.debug(f"Error validating target_commitish: {e}")
            return False
    
    def confirm_release_update(self, release_config: GitHubReleaseConfig) -> bool:
        """Confirm if user wants to update existing release"""
        if self.config.dry_run:
            Logger.info("🧪 DRY RUN - Would prompt to update existing release")
            return True
        
        response = input(f"Release {release_config.tag_name} already exists. Update it with new release notes? (y/N): ")
        return response.lower().startswith('y')
    
    def build_release_command(self, release_config: GitHubReleaseConfig, notes_file: Path) -> List[str]:
        """Build the GitHub CLI command for release creation"""
        # Determine if this should be an update or create
        cmd = ['gh', 'release']
        
        if self.release_exists(release_config.tag_name):
            # Update existing release
            cmd.extend(['edit', release_config.tag_name])
            cmd.extend(['--notes-file', str(notes_file)])
        else:
            # Create new release
            cmd.extend(['create', release_config.tag_name])
            cmd.extend(['--title', release_config.title])
            cmd.extend(['--notes-file', str(notes_file)])
            cmd.extend(['--target', release_config.target_commitish])
            
            # Add flags based on config
            if release_config.draft:
                cmd.append('--draft')
            
            if release_config.prerelease or release_config.is_prerelease_version:
                cmd.append('--prerelease')
                
            if not release_config.latest and release_config.is_patch_release:
                # For patch releases, usually don't mark as latest if it's not the main branch
                pass  # GitHub will handle this automatically
            
            if release_config.discussion_category:
                cmd.extend(['--discussion-category', release_config.discussion_category])
        
        # Add repo specification
        cmd.extend(['--repo', release_config.repo])
        
        return cmd
    
    def get_release_url(self, tag_name: str) -> Optional[str]:
        """Get the URL of a created release"""
        try:
            cmd = ['gh', 'api', f'/repos/{self.config.repo_owner}/{self.config.repo_name}/releases/tags/{tag_name}', '--jq', '.html_url']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None


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
            for tag in possible_tags:
                try:
                    # Check if tag exists
                    cmd = ['git', 'rev-parse', '--verify', f'refs/tags/{tag}']
                    subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=self.config.repo_path)
                    Logger.info(f"Found since tag: {tag}")
                    return tag
                except subprocess.CalledProcessError:
                    Logger.debug(f"Tag {tag} not found")
                    continue
            
            Logger.error(f"Could not find any tag for version {self.config.since_version}")
            return None
        
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
            # Get all version tags sorted by version
            cmd = ['git', 'tag', '-l', 'v*.*.*']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=self.config.repo_path)
            
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

    def determine_target_tag(self) -> Optional[str]:
        """Determine the target tag for tag-to-tag collection"""
        if self.config.target_version:
            # Try different tag formats for target version
            possible_tags = [
                f"v{self.config.target_version}",  # e.g., "v1.0.1"
                self.config.target_version,  # e.g., "1.0.1"
                f"release-{self.config.target_version}",  # e.g., "release-1.0.1"
            ]
            
            for tag in possible_tags:
                try:
                    # Check if tag exists
                    cmd = ['git', 'rev-parse', '--verify', f'refs/tags/{tag}']
                    subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=self.config.repo_path)
                    Logger.info(f"Found target tag: {tag}")
                    return tag
                except subprocess.CalledProcessError:
                    Logger.debug(f"Tag {tag} not found")
                    continue
            
            Logger.info(f"No existing tag found for target version {self.config.target_version} (expected for unreleased versions)")
            return None
        
        # Default: use HEAD for unreleased changes (common case for milestones)
        Logger.info("No target version specified, defaulting to HEAD")
        return "HEAD"

    
    def _get_latest_version_tag(self) -> Optional[str]:
        """Get the latest version tag from git with proper semantic version parsing"""
        # Use centralized utility function with branch-specific detection
        return get_latest_version_tag(self.config.repo_path, branch_specific=True)
    
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
    
    def setup_repository(self) -> None:
        """Setup repository with fresh clone and proper branch checkout"""
        import shutil
        
        # Remove existing directory if it exists
        if self.config.repo_path.exists():
            Logger.info(f"Removing existing directory: {self.config.repo_path}")
            shutil.rmtree(self.config.repo_path)
        
        # Clone repository
        Logger.info(f"Cloning spring-projects/spring-ai repository to {self.config.repo_path}")
        clone_cmd = [
            'git', 'clone', 
            f'https://github.com/{self.config.repo_owner}/{self.config.repo_name}.git',
            str(self.config.repo_path)
        ]
        subprocess.run(clone_cmd, capture_output=True, text=True, check=True)
        
        # DON'T change working directory - run all git commands with cwd parameter
        
        # Fetch latest updates
        Logger.info("Fetching latest tags and branches from origin")
        fetch_cmd = ['git', 'fetch', '--tags', 'origin']
        subprocess.run(fetch_cmd, capture_output=True, text=True, check=True, cwd=self.config.repo_path)
        
        # Fetch all branches
        fetch_branches_cmd = ['git', 'fetch', 'origin', '+refs/heads/*:refs/remotes/origin/*']
        subprocess.run(fetch_branches_cmd, capture_output=True, text=True, check=True, cwd=self.config.repo_path)
        
        # Checkout the correct branch
        Logger.info(f"Checking out branch: {self.config.branch}")
        checkout_cmd = ['git', 'checkout', f'origin/{self.config.branch}']
        result = subprocess.run(checkout_cmd, capture_output=True, text=True, cwd=self.config.repo_path)
        if result.returncode != 0:
            Logger.warn(f"Could not checkout {self.config.branch}: {result.stderr.strip()}")
            Logger.info("Falling back to main branch")
            subprocess.run(['git', 'checkout', 'origin/main'], capture_output=True, text=True, check=True, cwd=self.config.repo_path)
        else:
            Logger.info(f"Successfully checked out {self.config.branch}")

    def collect_commits_with_metadata(self) -> List[CommitData]:
        """Collect commits with basic metadata using tag-to-tag collection"""
        # Setup repository with fresh clone and correct branch FIRST
        try:
            self.setup_repository()
            
            # Now determine tags after repository is available
            since_tag = self.determine_since_tag()
            target_tag = self.determine_target_tag()
            
            if not since_tag:
                raise ReleaseNotesError("No since version specified and could not determine from tags. Please specify --since-version.")
            
            # Repository is already on correct branch from setup_repository()
            
            # Build the commit range
            if target_tag and target_tag != "HEAD":
                commit_range = f"{since_tag}..{target_tag}"
                Logger.info(f"Collecting commits from {since_tag} to {target_tag}")
            else:
                commit_range = f"{since_tag}..HEAD"
                Logger.info(f"Collecting commits from {since_tag} to HEAD")
            
            # Get expected count for verification
            count_cmd = ['git', 'rev-list', '--count', commit_range]
            count_result = subprocess.run(count_cmd, capture_output=True, text=True, check=True, cwd=self.config.repo_path)
            expected_count = int(count_result.stdout.strip())
            Logger.info(f"Expected commit count: {expected_count}")
            
            # Get commits with detailed format
            cmd = ['git', 'log', commit_range, '--format=%H|%s|%aN|%aE|%aI']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=self.config.repo_path)
            
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

class GitHubDataEnricher:
    """Enrich commits with GitHub PR and issue information using GraphQL"""
    
    def __init__(self, config: ReleaseNotesConfig):
        self.config = config
        self.github = GitHubAPIHelper(f"{config.repo_owner}/{config.repo_name}", config.github_token)
    
    def enrich_commits_with_prs_and_issues(self, commits: List[CommitData]) -> List[EnrichedCommit]:
        """Enrich commits with PR and issue associations, including backport analysis"""
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
                Logger.info(f"  Commit {commit_sha[:8]}: {len(prs)} PR(s) - {[pr.number for pr in prs]}")
        
        # Analyze backport commits to find original PRs
        Logger.info("Analyzing backport commits for cross-branch PR linking...")
        backport_pr_associations = self.analyze_backport_commits(commits, pr_associations)
        
        if backport_pr_associations:
            Logger.info(f"Found {len(backport_pr_associations)} backport PR associations")
            for commit_sha, prs in backport_pr_associations.items():
                Logger.info(f"  Backport {commit_sha[:8]}: linked to PR(s) {[pr.number for pr in prs]}")
        
        # Create enriched commits
        enriched_commits = []
        
        for commit in commits:
            # Get PRs for this commit (direct associations)
            prs = pr_associations.get(commit.sha, [])
            
            # Add backport PR associations if available
            backport_prs = backport_pr_associations.get(commit.sha, [])
            if backport_prs:
                prs.extend(backport_prs)
                Logger.debug(f"  Commit {commit.sha[:8]}: added {len(backport_prs)} backport PR(s)")
            
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
    
    def analyze_backport_commits(self, commits: List[CommitData], existing_pr_associations: Dict[str, List]) -> Dict[str, List]:
        """
        Analyze commits to find backport PRs on main branch
        
        Spring AI uses a backport workflow where:
        1. PRs are merged to main branch with label "for: backport-to-1.0.x"
        2. Changes are manually backported to 1.0.x as direct commits
        3. These backport commits often reference the original PR in commit message
        
        This method attempts to link backport commits to their original PRs.
        """
        Logger.debug("Starting backport analysis...")
        backport_associations = {}
        
        # Find commits without direct PR associations (likely backports)
        backport_candidates = []
        for commit in commits:
            if commit.sha not in existing_pr_associations or not existing_pr_associations[commit.sha]:
                backport_candidates.append(commit)
        
        if not backport_candidates:
            Logger.debug("No backport candidates found (all commits have direct PR associations)")
            return backport_associations
        
        Logger.info(f"Analyzing {len(backport_candidates)} potential backport commits")
        
        # Extract PR numbers from commit messages
        pr_numbers_from_messages = self.extract_pr_numbers_from_messages(backport_candidates)
        
        if pr_numbers_from_messages:
            Logger.info(f"Found PR references in {len(pr_numbers_from_messages)} commit messages")
            
            # Directly fetch the referenced PRs to check for backport labels
            all_referenced_prs = set()
            for pr_numbers in pr_numbers_from_messages.values():
                all_referenced_prs.update(pr_numbers)
            
            Logger.info(f"Checking {len(all_referenced_prs)} PRs for backport labels...")
            verified_backport_prs = self.verify_backport_prs(list(all_referenced_prs))
            
            if verified_backport_prs:
                Logger.info(f"Found {len(verified_backport_prs)} PRs with backport labels")
                
                # Match commits to verified backport PRs
                for commit_sha, pr_numbers in pr_numbers_from_messages.items():
                    matched_prs = []
                    
                    for pr_number in pr_numbers:
                        # Find the PR in our verified backport PRs
                        matching_pr = next((pr for pr in verified_backport_prs if pr.number == pr_number), None)
                        if matching_pr:
                            matched_prs.append(matching_pr)
                            Logger.debug(f"  Linked commit {commit_sha[:8]} to backport PR #{pr_number}")
                    
                    if matched_prs:
                        backport_associations[commit_sha] = matched_prs
        
        Logger.debug(f"Backport analysis complete: found {len(backport_associations)} associations")
        return backport_associations
    
    def extract_pr_numbers_from_messages(self, commits: List[CommitData]) -> Dict[str, List[int]]:
        """Extract PR numbers from commit messages using regex patterns"""
        import re
        
        pr_patterns = [
            r'#(\d+)',  # Standard GitHub PR reference: #123
            r'\(#(\d+)\)',  # PR number in parentheses: (#123)
            r'PR\s*#?(\d+)',  # PR 123 or PR #123
            r'pull\s+request\s*#?(\d+)',  # pull request 123
            r'backport.*#(\d+)',  # backport of #123
            r'cherry.*pick.*#(\d+)'  # cherry pick from #123
        ]
        
        commit_pr_refs = {}
        
        for commit in commits:
            pr_numbers = set()
            message_lower = commit.message.lower()
            
            for pattern in pr_patterns:
                matches = re.findall(pattern, message_lower, re.IGNORECASE)
                for match in matches:
                    try:
                        pr_number = int(match)
                        if 1 <= pr_number <= 99999:  # Reasonable PR number range
                            pr_numbers.add(pr_number)
                    except ValueError:
                        continue
            
            if pr_numbers:
                commit_pr_refs[commit.sha] = list(pr_numbers)
                Logger.debug(f"  Commit {commit.sha[:8]}: found PR refs {list(pr_numbers)} in '{commit.message[:50]}...'")
        
        return commit_pr_refs
    
    def verify_backport_prs(self, pr_numbers: List[int]) -> List[PullRequest]:
        """Verify if specific PRs have backport labels by fetching them individually"""
        Logger.debug(f"Verifying {len(pr_numbers)} PRs for backport labels...")
        
        backport_labels = [
            "for: backport-to-1.0.x",
            "backport",
            "1.0.x",
            "backport-candidate"
        ]
        
        verified_prs = []
        
        for pr_number in pr_numbers:
            try:
                Logger.debug(f"  Checking PR #{pr_number}...")
                
                cmd = [
                    'gh', 'pr', 'view', str(pr_number),
                    '--repo', f"{self.config.repo_owner}/{self.config.repo_name}",
                    '--json', 'number,title,url,mergedAt,state,baseRefName,labels'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
                pr = json.loads(result.stdout)
                
                # Check if PR has backport labels and was merged to main
                pr_labels = [label['name'] for label in pr.get('labels', [])]
                has_backport_label = any(label in pr_labels for label in backport_labels)
                is_main_branch = pr.get('baseRefName') == 'main'
                is_merged = pr.get('state') == 'MERGED'
                
                if has_backport_label and is_main_branch and is_merged:
                    Logger.debug(f"    ✅ PR #{pr_number} has backport labels: {[l for l in pr_labels if l in backport_labels]}")
                    
                    # Convert to PullRequest object
                    pr_obj = PullRequest(
                        number=pr['number'],
                        title=pr['title'],
                        url=pr['url'],
                        state='MERGED',
                        labels=pr_labels,
                        closing_issues=[],  # Would need separate API call to get this
                        merged_at=pr.get('mergedAt'),
                        author=None  # Not available from this API call
                    )
                    
                    verified_prs.append(pr_obj)
                else:
                    Logger.debug(f"    ❌ PR #{pr_number}: backport={has_backport_label}, main={is_main_branch}, merged={is_merged}")
                    
            except subprocess.CalledProcessError as e:
                Logger.warn(f"Failed to fetch PR #{pr_number}: {e}")
                continue
            except Exception as e:
                Logger.warn(f"Error processing PR #{pr_number}: {e}")
                continue
        
        Logger.debug(f"Found {len(verified_prs)} PRs with backport labels out of {len(pr_numbers)} checked")
        return verified_prs
    
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
                elif any(word in hint_lower for word in ['dependencies', 'dependency', 'upgrade', 'bump']):
                    commit_categories.add('dependency_upgrades')
                elif any(word in hint_lower for word in ['security']):
                    commit_categories.add('security')
                elif any(word in hint_lower for word in ['performance', 'perf']):
                    commit_categories.add('performance')
                elif any(word in hint_lower for word in ['build', 'ci', 'cd', 'gradle', 'maven']):
                    commit_categories.add('build_updates')
                elif any(word in hint_lower for word in ['breaking', 'break']):
                    commit_categories.add('breaking_changes')
                elif any(word in hint_lower for word in ['deprecat', 'important', 'notice']):
                    commit_categories.add('noteworthy')
            
            # Check commit message for category hints if no labels
            if not commit_categories:
                message_lower = commit.commit.message.lower()
                if any(word in message_lower for word in ['fix', 'bug', 'resolve']):
                    commit_categories.add('bug_fixes')
                elif any(word in message_lower for word in ['add', 'feature', 'implement']):
                    commit_categories.add('features')
                elif any(word in message_lower for word in ['doc', 'documentation', 'readme']):
                    commit_categories.add('documentation')
                elif any(word in message_lower for word in ['upgrade', 'bump', 'update.*version', 'dependency']):
                    commit_categories.add('dependency_upgrades')
                elif any(word in message_lower for word in ['build', 'gradle', 'maven', 'ci', 'workflow']):
                    commit_categories.add('build_updates')
                elif any(word in message_lower for word in ['deprecat', 'important', 'breaking']):
                    commit_categories.add('noteworthy')
                elif any(word in message_lower for word in ['refactor', 'cleanup', 'improve']):
                    commit_categories.add('build_updates')  # Map old internal to build_updates
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
        """Analyze enriched commits using Claude Code for categorization with automatic batching"""
        if not enriched_commits:
            return AnalysisResult()
        
        total_commits = len(enriched_commits)
        Logger.info(f"Analyzing {total_commits} commits with Claude Code...")
        
        # Check Claude Code availability
        if not self.claude.is_available():
            Logger.warn("Claude Code not available - falling back to rule-based categorization")
            return self._fallback_analysis(enriched_commits)
        
        # Determine if batching is needed
        batch_size = self.config.ai_batch_size
        if total_commits <= batch_size:
            Logger.info(f"Processing all {total_commits} commits in single batch")
            return self._analyze_single_batch(enriched_commits, cost_tracker)
        
        # Process in batches
        Logger.info(f"Processing {total_commits} commits in batches of {batch_size}")
        batch_results = []
        
        for i in range(0, total_commits, batch_size):
            batch_end = min(i + batch_size, total_commits)
            batch_commits = enriched_commits[i:batch_end]
            batch_num = (i // batch_size) + 1
            total_batches = (total_commits + batch_size - 1) // batch_size
            
            Logger.info(f"📦 Processing batch {batch_num}/{total_batches}: commits {i+1}-{batch_end}")
            
            batch_result = self._analyze_single_batch(batch_commits, cost_tracker, batch_num)
            batch_results.append(batch_result)
            
            # Brief pause between batches to avoid overwhelming Claude Code
            if i + batch_size < total_commits:
                import time
                time.sleep(1.0)
        
        # Merge all batch results
        Logger.info(f"🔄 Merging results from {len(batch_results)} batches...")
        merged_result = self._merge_batch_results(batch_results)
        Logger.success(f"✅ Completed AI analysis of {total_commits} commits in {len(batch_results)} batches")
        
        return merged_result
    
    def _analyze_single_batch(self, enriched_commits: List[EnrichedCommit], cost_tracker: CostTracker = None, batch_num: int = None) -> AnalysisResult:
        """Analyze a single batch of commits"""
        
        try:
            # Generate comprehensive prompt
            prompt_content = self._generate_analysis_prompt(enriched_commits)
            
            # Add batch information to filename if this is part of a multi-batch operation
            if batch_num:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                prompt_file = self.config.claude_logs_dir / "release-notes" / "claude" / f"release-notes-analysis-batch{batch_num}-{timestamp}.md"
            else:
                prompt_file = self._create_prompt_file(prompt_content)
            
            # Create the file
            if batch_num:
                prompt_file.parent.mkdir(parents=True, exist_ok=True)
                with open(prompt_file, 'w') as f:
                    f.write(prompt_content)
            
            # Save AI input for debugging if requested
            if self.config.save_ai_input:
                suffix = f"_batch{batch_num}" if batch_num else ""
                debug_input_file = self.config.logs_dir / f"ai_input{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(debug_input_file, 'w') as f:
                    f.write(prompt_content)
                Logger.info(f"💾 Saved AI input to: {debug_input_file}")
            
            # Analyze with Claude Code
            batch_info = f" (batch {batch_num})" if batch_num else ""
            Logger.info(f"🤖 Sending {len(enriched_commits)} commits to Claude Code for analysis{batch_info}...")
            result = self.claude.analyze_from_file_with_json(
                prompt_file_path=str(prompt_file),
                timeout=self.config.ai_timeout,
                model=self.config.ai_model,
                show_progress=True
            )
            
            # Extract cost and token usage information from result
            cost, token_usage = self._extract_cost_from_result(result)
            if cost_tracker and cost > 0:
                operation_name = f"AI Categorization{batch_info}" if batch_num else "AI Categorization"
                cost_tracker.add_operation(operation_name, cost, len(enriched_commits), token_usage)
                
                # Show detailed cost breakdown
                Logger.info(f"💰 AI Analysis cost{batch_info}: ${cost:.4f}")
                Logger.info(f"📊 Token usage: {token_usage.total_input_tokens():,} input, {token_usage.output_tokens:,} output")
                if token_usage.cache_creation_input_tokens > 0 or token_usage.cache_read_input_tokens > 0:
                    Logger.info(f"📊 Cache usage: {token_usage.cache_creation_input_tokens:,} write, {token_usage.cache_read_input_tokens:,} read")
            
            if result['success'] and result.get('json_extraction_success'):
                return self._parse_analysis_result(result['json_data'], enriched_commits)
            else:
                # Force failure instead of fallback - AI analysis is required
                error_msg = result.get('error', 'JSON extraction failed')
                Logger.error(f"AI analysis failed{batch_info}: {error_msg}")
                Logger.error("❌ Refusing to use rule-based fallback - AI analysis is required")
                raise Exception(f"AI analysis failed{batch_info}: {error_msg}. Please check Claude Code integration and JSON output format.")
                
        except Exception as e:
            Logger.error(f"AI analysis error{batch_info if batch_num else ''}: {e}")
            Logger.error("❌ AI analysis failed - no fallback available")
            raise
    
    def _merge_batch_results(self, batch_results: List[AnalysisResult]) -> AnalysisResult:
        """Merge multiple AnalysisResult objects from batched analysis"""
        if not batch_results:
            return AnalysisResult()
        
        if len(batch_results) == 1:
            return batch_results[0]
        
        # Initialize merged result with first batch
        merged = AnalysisResult()
        
        # Collect all highlights and create a master summary
        all_highlights = []
        total_features = 0
        total_bug_fixes = 0
        total_docs = 0
        total_other = 0
        
        # Merge all categories from all batches
        for batch_result in batch_results:
            merged.breaking_changes.extend(batch_result.breaking_changes)
            merged.features.extend(batch_result.features)
            merged.bug_fixes.extend(batch_result.bug_fixes)
            merged.documentation.extend(batch_result.documentation)
            merged.dependency_upgrades.extend(batch_result.dependency_upgrades)
            merged.performance.extend(batch_result.performance)
            merged.build_updates.extend(batch_result.build_updates)
            merged.security.extend(batch_result.security)
            merged.noteworthy.extend(batch_result.noteworthy)
            merged.upgrading_notes.extend(batch_result.upgrading_notes)
            merged.other.extend(batch_result.other)
            
            # Handle deprecated categories for backward compatibility
            merged.internal.extend(batch_result.internal)
            merged.accessibility.extend(batch_result.accessibility)
            
            # Collect statistics for master highlights
            total_features += len(batch_result.features)
            total_bug_fixes += len(batch_result.bug_fixes)
            total_docs += len(batch_result.documentation)
            total_other += (len(batch_result.dependency_upgrades) + len(batch_result.performance) + 
                          len(batch_result.build_updates) + len(batch_result.security) + 
                          len(batch_result.noteworthy) + len(batch_result.upgrading_notes) + 
                          len(batch_result.other))
            
            # Collect individual highlights
            if batch_result.highlights:
                all_highlights.append(batch_result.highlights)
        
        # Create master highlights
        highlight_parts = []
        if total_features > 0:
            highlight_parts.append(f"{total_features} new features")
        if total_bug_fixes > 0:
            highlight_parts.append(f"{total_bug_fixes} bug fixes")
        if total_docs > 0:
            highlight_parts.append(f"{total_docs} documentation improvements")
        if total_other > 0:
            highlight_parts.append(f"{total_other} other improvements")
        
        if highlight_parts:
            merged.highlights = f"This release includes {', '.join(highlight_parts)}."
        
        Logger.debug(f"Merged {len(batch_results)} batch results:")
        Logger.debug(f"  ⭐ Features: {len(merged.features)}")
        Logger.debug(f"  🪲 Bug fixes: {len(merged.bug_fixes)}")  
        Logger.debug(f"  📚 Documentation: {len(merged.documentation)}")
        Logger.debug(f"  🔨 Dependency upgrades: {len(merged.dependency_upgrades)}")
        Logger.debug(f"  ⚡ Performance: {len(merged.performance)}")
        Logger.debug(f"  🔩 Build updates: {len(merged.build_updates)}")
        Logger.debug(f"  🔐 Security: {len(merged.security)}")
        Logger.debug(f"  📢 Noteworthy: {len(merged.noteworthy)}")
        Logger.debug(f"  ⚠️ Upgrading notes: {len(merged.upgrading_notes)}")
        Logger.debug(f"  ⏪ Breaking changes: {len(merged.breaking_changes)}")
        Logger.debug(f"  🔧 Other: {len(merged.other)}")
        
        return merged

    def _extract_token_usage_from_result(self, result: Dict[str, Any]) -> TokenUsage:
        """Extract detailed token usage from Claude Code result"""
        usage = TokenUsage()
        
        try:
            # ClaudeCodeWrapper directly provides token usage information in the result
            if 'token_usage' in result and result['token_usage']:
                token_data = result['token_usage']
                
                # Extract token counts from ClaudeCodeWrapper format
                usage.input_tokens = token_data.get('input_tokens', 0)
                usage.output_tokens = token_data.get('output_tokens', 0)
                usage.cache_creation_input_tokens = token_data.get('cache_creation_input_tokens', 0)
                usage.cache_read_input_tokens = token_data.get('cache_read_input_tokens', 0)
                
                Logger.debug(f"Extracted token usage: {usage.input_tokens} input, {usage.output_tokens} output, {usage.cache_creation_input_tokens} cache write, {usage.cache_read_input_tokens} cache read")
            else:
                Logger.debug("No token_usage found in result, returning empty usage")
                
        except Exception as e:
            Logger.debug(f"Failed to extract token usage from result: {e}")
            # Return empty usage object as fallback
        
        return usage

    def _extract_cost_from_result(self, result: Dict[str, Any]) -> Tuple[float, TokenUsage]:
        """Extract cost information and token usage from Claude Code result"""
        # First extract token usage
        token_usage = self._extract_token_usage_from_result(result)
        
        # Try to get cost directly from ClaudeCodeWrapper result first
        try:
            # ClaudeCodeWrapper provides cost_info directly
            if 'cost_info' in result and result['cost_info']:
                direct_cost = float(result['cost_info'])
                Logger.debug(f"Using direct cost from ClaudeCodeWrapper: ${direct_cost:.6f}")
                return direct_cost, token_usage
        except (ValueError, TypeError) as e:
            Logger.debug(f"Could not extract direct cost: {e}")
        
        # Fallback: Calculate cost based on token usage
        calculated_cost = token_usage.calculate_cost_sonnet4()
        Logger.debug(f"Using calculated cost from token usage: ${calculated_cost:.6f}")
        
        return calculated_cost, token_usage
    
    def _generate_analysis_prompt(self, enriched_commits: List[EnrichedCommit]) -> str:
        """Generate comprehensive analysis prompt for Claude Code"""
        
        # Prepare commit data for analysis
        commits_data = []
        for commit in enriched_commits:
            commit_info = {
                "sha": commit.commit.sha,  # Full SHA for proper commit URLs
                "short_sha": commit.commit.short_sha,  # Short SHA for display
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

1. **Categorize** into one of these categories (aligned with Spring ecosystem standards):
   - ⭐ **New Features**: New functionality, integrations, model providers
   - 🪲 **Bug Fixes**: Bug fixes, error corrections, stability improvements
   - ⏪ **Breaking Changes**: API changes, configuration changes, breaking updates
   - 📓 **Documentation**: Documentation improvements, examples, guides
   - 🔨 **Dependency Upgrades**: Library updates, Spring Boot upgrades, model provider updates
   - ⚡ **Performance**: Performance improvements, optimizations
   - 🔩 **Build Updates**: Build system changes, Maven/Gradle updates, CI/CD improvements
   - 🔐 **Security**: Security-related fixes and improvements
   - 📢 **Noteworthy**: Major announcements, important notices, deprecations
   - ⚠️ **Upgrading Notes**: Migration guidance, breaking change instructions

2. **Prefer PR titles** over commit messages when available (they're usually better formatted)
3. **Group related changes** when multiple commits/PRs address the same feature
4. **Identify breaking changes** from labels, titles, or descriptions
5. **Create proper markdown hyperlinks** (IMPORTANT - always use full URLs):
   - For PRs: [#123](https://github.com/spring-projects/spring-ai/pull/123)  
   - For issues: [#456](https://github.com/spring-projects/spring-ai/issues/456)
   - For commits (when no PR): [short_sha](https://github.com/spring-projects/spring-ai/commit/full-sha)
   - Combined: [#123](https://github.com/spring-projects/spring-ai/pull/123) via [#456](https://github.com/spring-projects/spring-ai/issues/456)
   - **Never use plain text like (abc1234) or (#123) - always use markdown links**
   - **For commits: Use short_sha for display text but full sha for URL**

## Spring AI Specific Considerations
- Highlight new model providers (OpenAI, Anthropic, Azure, etc.)
- Note vector database integrations (Chroma, Pinecone, Redis, etc.)
- Call out configuration property changes
- Identify new starters or auto-configurations
- Note function calling and tool integration changes

## Required Output Format
**CRITICAL**: You MUST return ONLY raw JSON data with no additional text, explanations, or markdown formatting. 
Do NOT include any conversational text before or after the JSON.
Do NOT wrap the JSON in markdown code blocks.
Your response must start with {{ and end with }} - nothing else.

Return ONLY the raw JSON object in this exact format:

{{
  "highlights": "2-3 sentence summary of most significant changes in this release",
  "breaking_changes": [
    {{
      "title": "Change title",
      "description": "User-facing description",
      "link_text": "[#123](https://github.com/spring-projects/spring-ai/pull/123) via [#456](https://github.com/spring-projects/spring-ai/issues/456)"
    }}
  ],
  "features": [
    {{
      "title": "Feature title", 
      "description": "User-facing description",
      "link_text": "[#123](https://github.com/spring-projects/spring-ai/pull/123)"
    }}
  ],
  "bug_fixes": [
    {{
      "title": "Fix title",
      "description": "User-facing description", 
      "link_text": "[#123](https://github.com/spring-projects/spring-ai/pull/123) via [#456](https://github.com/spring-projects/spring-ai/issues/456)"
    }}
  ],
  "documentation": [
    {{
      "title": "Doc change title",
      "description": "Description",
      "link_text": "[#123](https://github.com/spring-projects/spring-ai/pull/123)"
    }}
  ],
  "dependency_upgrades": [
    {{
      "title": "Dependency update title",
      "description": "Library or framework update",
      "link_text": "[#123](https://github.com/spring-projects/spring-ai/pull/123)"
    }}
  ],
  "performance": [],
  "build_updates": [
    {{
      "title": "Build change title",
      "description": "Build system or CI/CD update",
      "link_text": "[abc1234](https://github.com/spring-projects/spring-ai/commit/abc1234full-40-char-sha-here)"
    }}
  ],
  "security": [],
  "noteworthy": [
    {{
      "title": "Important notice title",
      "description": "Major announcement or deprecation",
      "link_text": "[#123](https://github.com/spring-projects/spring-ai/pull/123)"
    }}
  ],
  "upgrading_notes": [
    {{
      "title": "Migration instruction title", 
      "description": "How to handle breaking changes",
      "link_text": "[#123](https://github.com/spring-projects/spring-ai/pull/123)"
    }}
  ]
}}

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
        
        # Parse all Spring ecosystem categories
        result = AnalysisResult(
            highlights=json_data.get('highlights', ''),
            breaking_changes=create_categorized_changes(json_data.get('breaking_changes', [])),
            features=create_categorized_changes(json_data.get('features', [])),
            bug_fixes=create_categorized_changes(json_data.get('bug_fixes', [])),
            documentation=create_categorized_changes(json_data.get('documentation', [])),
            dependency_upgrades=create_categorized_changes(json_data.get('dependency_upgrades', [])),
            performance=create_categorized_changes(json_data.get('performance', [])),
            build_updates=create_categorized_changes(json_data.get('build_updates', [])),
            security=create_categorized_changes(json_data.get('security', [])),
            noteworthy=create_categorized_changes(json_data.get('noteworthy', [])),
            upgrading_notes=create_categorized_changes(json_data.get('upgrading_notes', [])),
            other=create_categorized_changes(json_data.get('other', [])),
            # Deprecated categories for backward compatibility
            internal=create_categorized_changes(json_data.get('internal', [])),
            accessibility=create_categorized_changes(json_data.get('accessibility', []))
        )
        
        # Debug log all categories
        Logger.debug(f"Parsed analysis result categories:")
        Logger.debug(f"  ⭐ Features: {len(result.features)}")
        Logger.debug(f"  🪲 Bug fixes: {len(result.bug_fixes)}")  
        Logger.debug(f"  📚 Documentation: {len(result.documentation)}")
        Logger.debug(f"  🔨 Dependency upgrades: {len(result.dependency_upgrades)}")
        Logger.debug(f"  ⚡ Performance: {len(result.performance)}")
        Logger.debug(f"  🔩 Build updates: {len(result.build_updates)}")
        Logger.debug(f"  🔐 Security: {len(result.security)}")
        Logger.debug(f"  📢 Noteworthy: {len(result.noteworthy)}")
        Logger.debug(f"  ⚠️ Upgrading notes: {len(result.upgrading_notes)}")
        Logger.debug(f"  ⏪ Breaking changes: {len(result.breaking_changes)}")
        Logger.debug(f"  🔧 Other: {len(result.other)}")
        if result.internal or result.accessibility:
            Logger.debug(f"  📦 Internal (deprecated): {len(result.internal)}")
            Logger.debug(f"  ♿ Accessibility (deprecated): {len(result.accessibility)}")
        
        return result
    
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
        """Extract unique contributors from commits with smart name-based deduplication"""
        contributors_by_name = {}
        
        for commit in enriched_commits:
            author = commit.commit.author
            email = commit.commit.email
            
            # Extract username from email if it's a GitHub noreply email
            username = self._extract_username_from_email(email)
            is_github_username = 'noreply.github.com' in email
            
            # Use normalized author name as primary key for deduplication
            name_key = self._normalize_contributor_name(author)
            
            if name_key not in contributors_by_name:
                contributors_by_name[name_key] = Contributor(
                    name=author,
                    username=username,
                    email=email,
                    commits_count=1
                )
            else:
                existing = contributors_by_name[name_key]
                existing.commits_count += 1
                
                # Update with "better" username using smart preference rules
                new_username = self._choose_better_username(
                    existing.username, username, existing.email, email
                )
                if new_username != existing.username:
                    Logger.debug(f"Contributor '{author}': combined commits, using username '{new_username}' (total: {existing.commits_count})")
                existing.username = new_username
                
                # Update email if the new one is a GitHub email and old one isn't
                if is_github_username and 'noreply.github.com' not in existing.email:
                    existing.email = email
        
        # Sort contributors by name
        contributors = list(contributors_by_name.values())
        contributors.sort(key=lambda c: c.name.lower())
        
        Logger.debug(f"Deduplicated contributors: {len(contributors)} unique names from {len(enriched_commits)} commits")
        
        return contributors
    
    def _normalize_contributor_name(self, name: str) -> str:
        """Normalize contributor name for deduplication"""
        # Basic normalization - remove extra whitespace and convert to lowercase
        normalized = ' '.join(name.strip().split()).lower()
        
        # Handle common name variations
        # Remove middle initials/names for better matching (e.g., "John D. Smith" -> "john smith")
        # This helps catch cases where the same person appears with and without middle names
        parts = normalized.split()
        if len(parts) >= 3:
            # If middle part is just an initial (single letter + optional period), remove it
            middle_parts = parts[1:-1]  # Everything except first and last
            filtered_parts = [parts[0]]  # Keep first name
            
            for part in middle_parts:
                # Keep middle part if it's more than just an initial
                if len(part.replace('.', '')) > 1:
                    filtered_parts.append(part)
            
            filtered_parts.append(parts[-1])  # Keep last name
            normalized = ' '.join(filtered_parts)
        
        return normalized
    
    def _choose_better_username(self, existing_username: str, new_username: str, 
                              existing_email: str, new_email: str) -> str:
        """Choose the better username when deduplicating contributors by name"""
        
        # Preference rules (in order of priority):
        # 1. Prefer GitHub usernames over email-derived usernames
        existing_is_github = 'noreply.github.com' in existing_email
        new_is_github = 'noreply.github.com' in new_email
        
        if new_is_github and not existing_is_github:
            Logger.debug(f"Username upgrade: {existing_username} -> {new_username} (GitHub username preferred)")
            return new_username
        elif existing_is_github and not new_is_github:
            return existing_username
        
        # 2. If both are GitHub usernames, prefer the shorter one (usually cleaner)
        if existing_is_github and new_is_github:
            if len(new_username) < len(existing_username):
                Logger.debug(f"Username upgrade: {existing_username} -> {new_username} (shorter GitHub username)")
                return new_username
            elif len(existing_username) < len(new_username):
                return existing_username
        
        # 3. Prefer usernames without dots/special characters (cleaner GitHub handles)
        existing_has_dots = '.' in existing_username
        new_has_dots = '.' in new_username
        
        if not new_has_dots and existing_has_dots:
            Logger.debug(f"Username upgrade: {existing_username} -> {new_username} (no dots preferred)")
            return new_username
        elif not existing_has_dots and new_has_dots:
            return existing_username
        
        # 4. If all else is equal, keep the existing username (first wins)
        return existing_username
    
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
            lines.append("## ⏪ Breaking Changes")
            for change in analysis_result.breaking_changes:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Upgrading notes (if any breaking changes need guidance)
        if analysis_result.upgrading_notes:
            lines.append("## ⚠️ Upgrading Notes") 
            for change in analysis_result.upgrading_notes:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Noteworthy changes (major announcements)
        if analysis_result.noteworthy:
            lines.append("## 📢 Noteworthy")
            for change in analysis_result.noteworthy:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # New features
        if analysis_result.features:
            lines.append("## ⭐ New Features")
            for change in analysis_result.features:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Bug fixes
        if analysis_result.bug_fixes:
            lines.append("## 🪲 Bug Fixes")
            for change in analysis_result.bug_fixes:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Documentation
        if analysis_result.documentation:
            lines.append("## 📓 Documentation")
            for change in analysis_result.documentation:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Dependency upgrades
        if analysis_result.dependency_upgrades:
            lines.append("## 🔨 Dependency Upgrades")
            for change in analysis_result.dependency_upgrades:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Performance improvements
        if analysis_result.performance:
            lines.append("## ⚡ Performance")
            for change in analysis_result.performance:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Build updates
        if analysis_result.build_updates:
            lines.append("## 🔩 Build Updates")
            for change in analysis_result.build_updates:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Security improvements
        if analysis_result.security:
            lines.append("## 🔐 Security")
            for change in analysis_result.security:
                lines.append(change.to_markdown_line())
            lines.append("")
        
        # Internal changes (deprecated - map to build_updates)
        if analysis_result.internal:
            lines.append("## 🔩 Internal Changes")
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
        
        # No footer - clean release notes output
        
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
                       default='./spring-ai-release',
                       help='Path to Spring AI repository (will be created with fresh clone)')
    parser.add_argument('--branch',
                       default='auto',
                       help='Branch to analyze (default: auto-detect based on version)')
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
    parser.add_argument('--ai-batch-size',
                       type=int,
                       default=10,
                       help='Maximum commits per AI analysis batch (default: 10)')
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
    
    # GitHub Release Automation
    parser.add_argument('--create-github-release',
                       action='store_true',
                       help='Create a GitHub release using the generated release notes')
    parser.add_argument('--release-draft',
                       action='store_true',
                       help='Create release as a draft (requires --create-github-release)')
    parser.add_argument('--release-prerelease',
                       action='store_true',
                       help='Mark release as prerelease (requires --create-github-release)')
    parser.add_argument('--release-target',
                       default='1.0.x',
                       help='Target branch or commit for release (default: 1.0.x)')
    parser.add_argument('--release-title',
                       help='Custom title for GitHub release (default: auto-generated)')
    parser.add_argument('--release-discussion',
                       help='Discussion category to enable for release (e.g., "General")')
    parser.add_argument('--no-tag-date',
                       action='store_true',
                       help='Do not use tag creation date for GitHub release (use current time instead)')
    parser.add_argument('--skip-generation',
                       action='store_true',
                       help='Skip release notes generation and use existing RELEASE_NOTES.md (for GitHub release only)')
    
    args = parser.parse_args()
    
    # Set debug mode
    if args.verbose or args.debug_github:
        os.environ['DEBUG'] = '1'
    
    if args.debug_github:
        os.environ['DEBUG_GITHUB'] = '1'
    
    # Auto-determine branch based on version if not explicitly set
    def determine_branch(since_version: str, target_version: str, explicit_branch: str) -> str:
        """Determine the correct branch based on version patterns"""
        # If user explicitly set branch (not auto), use it
        if explicit_branch != 'auto':
            return explicit_branch
            
        # For milestone releases (M1, M2, RC, etc.), use main branch
        if (target_version and ('M' in target_version or 'RC' in target_version)) or \
           (since_version and ('M' in since_version or 'RC' in since_version)):
            return 'main'
            
        # For patch releases within 1.0.x series, use 1.0.x branch
        if target_version and target_version.startswith('1.0.'):
            return '1.0.x'
            
        # For patch releases within 1.1.x series, use 1.1.x branch (future)
        if target_version and target_version.startswith('1.1.'):
            return '1.1.x'
            
        # Default fallback
        return explicit_branch
    
    # Determine the correct branch
    determined_branch = determine_branch(args.since_version, args.target_version, args.branch)
    
    # Create configuration
    script_dir = Path(__file__).parent.resolve()
    config = ReleaseNotesConfig(
        repo_path=Path(args.repo_path),
        branch=determined_branch,
        since_version=args.since_version,
        target_version=args.target_version,
        output_file=Path(args.output),
        use_ai=not args.no_ai,
        ai_model=args.ai_model,
        ai_timeout=args.ai_timeout,
        ai_batch_size=args.ai_batch_size,
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
        
        # Show branch selection logic
        if determined_branch != args.branch:
            Logger.info(f"🔀 Auto-selected branch: {determined_branch} (was default: {args.branch})")
        else:
            Logger.info(f"🌿 Using branch: {determined_branch}")
        
        if config.verbose:
            Logger.info(f"Repository: {config.repo_owner}/{config.repo_name}")
            Logger.info(f"Repository Path: {config.repo_path}")
            Logger.info(f"Output File: {config.output_file}")
            Logger.info(f"AI Analysis: {'Enabled' if config.use_ai else 'Disabled'}")
            Logger.info(f"Dry Run: {config.dry_run}")
        
        # Repository will be created by setup_repository() method if needed
        Logger.info(f"Repository will be cloned to: {config.repo_path}")
        
        # Check if we should skip generation and go straight to GitHub release
        if args.skip_generation and args.create_github_release:
            if not config.output_file.exists():
                Logger.error(f"❌ Cannot skip generation: {config.output_file} does not exist")
                Logger.error("Run without --skip-generation first to create the release notes file")
                return 1
            
            Logger.info(f"📄 Using existing release notes file: {config.output_file}")
            Logger.info("⚡ Skipping analysis phases - going directly to GitHub release creation")
            
            # Read existing release notes for GitHub release creation
            with open(config.output_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
                
            # Jump to GitHub release creation
        else:
            # Normal generation flow
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
        
        # Phase 2: Enrich with GitHub data (or skip for testing/dry-run)
        enricher = GitHubDataEnricher(config)  # Create enricher for both paths
        
        if config.skip_github or config.dry_run:
            reason = "dry-run mode" if config.dry_run else "testing"
            Logger.info(f"Phase 2: Skipping GitHub enrichment for {reason}...")
            # Create minimal enriched commits without API calls
            enriched_commits = [
                EnrichedCommit(
                    commit=commit,
                    prs=[],
                    issues=[],
                    category_hints=[]
                ) for commit in commits
            ]
        else:
            Logger.info("Phase 2: Enriching commits with GitHub PR/issue data...")
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
        
        # Phase 3: AI analysis (if enabled and not dry-run)
        if config.use_ai and not config.dry_run:
            Logger.info("Phase 3: AI-powered categorization and analysis...")
            analyzer = ReleaseNotesAIAnalyzer(config)
            analysis_result = analyzer.analyze_changes(enriched_commits, cost_tracker)
            Logger.success("AI analysis completed")
        else:
            reason = "dry-run mode" if config.dry_run else "AI disabled"
            Logger.info(f"Phase 3: Rule-based categorization ({reason})...")
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
            Logger.success("🧪 DRY RUN COMPLETED - No files written, no costs incurred")
            Logger.info("Generated release notes preview (first 1000 chars):")
            Logger.bold("="*60)
            # Show first 1000 characters of generated markdown
            preview = markdown_content[:1000] + "..." if len(markdown_content) > 1000 else markdown_content
            print(preview)
            Logger.bold("="*60)
            Logger.info(f"Full markdown length: {len(markdown_content)} characters")
            Logger.info(f"Would write to: {config.output_file}")
        else:
            # Write to output file
            generator.write_markdown_file(markdown_content)
            Logger.success(f"Release notes written to: {config.output_file}")
        
        Logger.bold("🎉 Release notes generation completed!")
        
        # GitHub Release Creation (if requested)
        if args.create_github_release:
            Logger.info("\n" + "="*50)
            Logger.info("📦 GITHUB RELEASE CREATION")
            Logger.info("="*50)
            
            # Determine version for release
            release_version = args.target_version or config.target_version
            if not release_version:
                Logger.error("❌ Cannot create GitHub release: no target version specified")
                Logger.error("Please specify --target-version for GitHub release creation")
                return 1
            
            # Create GitHub release configuration
            release_config = GitHubReleaseConfig(
                version=release_version,
                release_notes_file=str(config.output_file),
                repo=f"{config.repo_owner}/{config.repo_name}",
                title=args.release_title,
                draft=args.release_draft,
                prerelease=args.release_prerelease,
                target_commitish=args.release_target,
                discussion_category=args.release_discussion,
                use_tag_date=not args.no_tag_date,  # Use tag date unless disabled
                generate_notes=True  # We just generated the notes
            )
            
            # Create the release
            release_automator = GitHubReleaseAutomator(config)
            success = release_automator.create_github_release(release_config, markdown_content)
            
            if success:
                Logger.success(f"🎉 GitHub release {release_config.tag_name} created successfully!")
                release_url = release_automator.get_release_url(release_config.tag_name)
                if release_url:
                    Logger.info(f"🔗 Release URL: {release_url}")
            else:
                Logger.error(f"❌ Failed to create GitHub release {release_config.tag_name}")
                return 1
        
        # Show summary statistics  
        total_changes = (len(analysis_result.features) + len(analysis_result.bug_fixes) + 
                        len(analysis_result.breaking_changes) + len(analysis_result.documentation) + 
                        len(analysis_result.dependency_upgrades) + len(analysis_result.performance) + 
                        len(analysis_result.build_updates) + len(analysis_result.security) +
                        len(analysis_result.noteworthy) + len(analysis_result.upgrading_notes) +
                        len(analysis_result.other) +
                        len(analysis_result.internal) + len(analysis_result.accessibility))  # Deprecated categories
        
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
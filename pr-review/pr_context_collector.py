#!/usr/bin/env python3
"""
PR Context Collector - Foundation for Enhanced PR Analysis

Collects comprehensive GitHub issue and PR data for analysis including:
- Issue descriptions, comments, labels, assignees
- PR descriptions, comments, reviews, linked issues  
- File changes and commit messages
- Structured JSON storage for downstream analysis

This is Iteration 1 of the Enhanced PR Analysis implementation.
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import re

# Simple logger to avoid circular imports
class Logger:
    @staticmethod
    def info(msg): print(f"\033[34m[INFO]\033[0m {msg}")
    @staticmethod
    def success(msg): print(f"\033[32m[SUCCESS]\033[0m {msg}")
    @staticmethod
    def warn(msg): print(f"\033[33m[WARN]\033[0m {msg}")
    @staticmethod
    def error(msg): print(f"\033[31m[ERROR]\033[0m {msg}")


@dataclass
class IssueData:
    """GitHub Issue information"""
    number: int
    title: str
    body: str
    state: str
    labels: List[str]
    assignees: List[str]
    created_at: str
    updated_at: str
    author: str
    url: str
    comments_count: int
    comments: List[Dict[str, Any]]


@dataclass
class PRData:
    """GitHub Pull Request information"""
    number: int
    title: str
    body: str
    state: str
    draft: bool
    labels: List[str]
    assignees: List[str]
    reviewers: List[str]
    created_at: str
    updated_at: str
    author: str
    url: str
    base_branch: str
    head_branch: str
    commits_count: int
    changed_files: int
    additions: int
    deletions: int
    linked_issues: List[int]
    comments: List[Dict[str, Any]]
    reviews: List[Dict[str, Any]]


@dataclass
class FileChange:
    """File change information"""
    filename: str
    status: str  # added, modified, deleted, renamed
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None


@dataclass
class CommitData:
    """Commit information"""
    sha: str
    message: str
    author: str
    date: str
    url: str


@dataclass
class ConversationEntry:
    """Unified conversation entry from issues/PRs"""
    type: str  # 'issue_comment', 'pr_comment', 'review', 'commit'
    author: str
    created_at: str
    body: str
    url: str
    metadata: Dict[str, Any]  # Additional context-specific data


class PRContextCollector:
    """Collects comprehensive PR and related issue context from GitHub"""
    
    def __init__(self, working_dir: Path, repository: str = "spring-projects/spring-ai", context_dir: Optional[Path] = None):
        self.working_dir = working_dir
        self.repository = repository
        self.context_dir = context_dir if context_dir else working_dir / "context"
        self.context_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting and caching
        self.request_count = 0
        self.last_request_time = 0
        self.cache_duration = 3600  # 1 hour cache
    
    def collect_all_context(self, pr_number: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Collect all context data for a PR"""
        Logger.info(f"🔍 Collecting comprehensive context for PR #{pr_number}")
        
        pr_context_dir = self.context_dir / f"pr-{pr_number}"
        pr_context_dir.mkdir(exist_ok=True)
        
        # Check if we have recent cached data
        if not force_refresh and self._has_recent_cache(pr_context_dir):
            Logger.info("📋 Using cached context data")
            return self._load_cached_context(pr_context_dir)
        
        try:
            # 1. Collect PR data
            Logger.info("📥 Collecting PR information...")
            pr_data = self._collect_pr_data(pr_number)
            
            # 2. Collect linked issues data
            Logger.info("🔗 Collecting linked issues...")
            issues_data = self._collect_linked_issues(pr_data.linked_issues)
            
            # 3. Collect file changes
            Logger.info("📁 Collecting file changes...")
            file_changes = self._collect_file_changes(pr_number)
            
            # 4. Collect commit data
            Logger.info("📝 Collecting commit information...")
            commits_data = self._collect_commits_data(pr_number)
            
            # 5. Build unified conversation
            Logger.info("💬 Building unified conversation...")
            conversation = self._build_unified_conversation(pr_data, issues_data)
            
            # 6. Save all data
            context_data = {
                'pr_data': asdict(pr_data),
                'issues_data': [asdict(issue) for issue in issues_data],
                'file_changes': [asdict(change) for change in file_changes],
                'commits_data': [asdict(commit) for commit in commits_data],
                'conversation': [asdict(entry) for entry in conversation],
                'collection_timestamp': datetime.now().isoformat(),
                'repository': self.repository
            }
            
            self._save_context_data(pr_context_dir, context_data)
            
            Logger.success(f"✅ Context collection completed for PR #{pr_number}")
            Logger.info(f"   - PR data: {pr_data.title}")
            Logger.info(f"   - Linked issues: {len(issues_data)}")
            Logger.info(f"   - File changes: {len(file_changes)}")
            Logger.info(f"   - Commits: {len(commits_data)}")
            Logger.info(f"   - Conversation entries: {len(conversation)}")
            
            return context_data
            
        except Exception as e:
            Logger.error(f"❌ Failed to collect context for PR #{pr_number}: {e}")
            return {}
    
    def _collect_pr_data(self, pr_number: str) -> PRData:
        """Collect PR information from GitHub"""
        # Get basic PR info
        pr_info = self._gh_api_call([
            "pr", "view", pr_number, "--json",
            "number,title,body,state,isDraft,labels,assignees,reviewRequests,createdAt,updatedAt,author,url,baseRefName,headRefName,commits,changedFiles,additions,deletions"
        ])
        
        # Get PR comments
        pr_comments = self._gh_api_call([
            "pr", "view", pr_number, "--json", "comments"
        ]).get("comments", [])
        
        # Get PR reviews
        pr_reviews = self._gh_api_call([
            "api", f"repos/{self.repository}/pulls/{pr_number}/reviews"
        ])
        
        # Extract linked issues from PR body and comments
        linked_issues = self._extract_linked_issues(pr_info.get("body", ""))
        for comment in pr_comments:
            linked_issues.extend(self._extract_linked_issues(comment.get("body", "")))
        
        return PRData(
            number=int(pr_number),
            title=pr_info.get("title", ""),
            body=pr_info.get("body", ""),
            state=pr_info.get("state", ""),
            draft=pr_info.get("isDraft", False),
            labels=[label.get("name", "") for label in pr_info.get("labels", [])],
            assignees=[assignee.get("login", "") for assignee in pr_info.get("assignees", [])],
            reviewers=[req.get("login", "") for req in pr_info.get("reviewRequests", [])],
            created_at=pr_info.get("createdAt", ""),
            updated_at=pr_info.get("updatedAt", ""),
            author=pr_info.get("author", {}).get("login", ""),
            url=pr_info.get("url", ""),
            base_branch=pr_info.get("baseRefName", ""),
            head_branch=pr_info.get("headRefName", ""),
            commits_count=len(pr_info.get("commits", [])),
            changed_files=pr_info.get("changedFiles", 0),
            additions=pr_info.get("additions", 0),
            deletions=pr_info.get("deletions", 0),
            linked_issues=list(set(linked_issues)),  # Remove duplicates
            comments=pr_comments,
            reviews=pr_reviews if isinstance(pr_reviews, list) else []
        )
    
    def _collect_linked_issues(self, issue_numbers: List[int]) -> List[IssueData]:
        """Collect data for linked issues"""
        issues_data = []
        
        for issue_num in issue_numbers:
            try:
                Logger.info(f"  📋 Collecting issue #{issue_num}")
                
                # Get issue info
                issue_info = self._gh_api_call([
                    "issue", "view", str(issue_num), "--json",
                    "number,title,body,state,labels,assignees,createdAt,updatedAt,author,url,comments"
                ])
                
                # Get issue comments
                issue_comments = issue_info.get("comments", [])
                
                issues_data.append(IssueData(
                    number=issue_num,
                    title=issue_info.get("title", ""),
                    body=issue_info.get("body", ""),
                    state=issue_info.get("state", ""),
                    labels=[label.get("name", "") for label in issue_info.get("labels", [])],
                    assignees=[assignee.get("login", "") for assignee in issue_info.get("assignees", [])],
                    created_at=issue_info.get("createdAt", ""),
                    updated_at=issue_info.get("updatedAt", ""),
                    author=issue_info.get("author", {}).get("login", ""),
                    url=issue_info.get("url", ""),
                    comments_count=len(issue_comments),
                    comments=issue_comments
                ))
                
            except Exception as e:
                Logger.warn(f"⚠️  Could not collect issue #{issue_num}: {e}")
        
        return issues_data
    
    def _collect_file_changes(self, pr_number: str) -> List[FileChange]:
        """Collect file change information"""
        try:
            # Get PR file changes
            files_data = self._gh_api_call([
                "api", f"repos/{self.repository}/pulls/{pr_number}/files"
            ])
            
            file_changes = []
            for file_info in files_data:
                file_changes.append(FileChange(
                    filename=file_info.get("filename", ""),
                    status=file_info.get("status", ""),
                    additions=file_info.get("additions", 0),
                    deletions=file_info.get("deletions", 0),
                    changes=file_info.get("changes", 0),
                    patch=file_info.get("patch", "")
                ))
            
            return file_changes
            
        except Exception as e:
            Logger.warn(f"⚠️  Could not collect file changes: {e}")
            return []
    
    def _collect_commits_data(self, pr_number: str) -> List[CommitData]:
        """Collect commit information"""
        try:
            # Get PR commits
            commits_data = self._gh_api_call([
                "api", f"repos/{self.repository}/pulls/{pr_number}/commits"
            ])
            
            commits = []
            for commit_info in commits_data:
                commits.append(CommitData(
                    sha=commit_info.get("sha", ""),
                    message=commit_info.get("commit", {}).get("message", ""),
                    author=commit_info.get("commit", {}).get("author", {}).get("name", ""),
                    date=commit_info.get("commit", {}).get("author", {}).get("date", ""),
                    url=commit_info.get("html_url", "")
                ))
            
            return commits
            
        except Exception as e:
            Logger.warn(f"⚠️  Could not collect commits: {e}")
            return []
    
    def _build_unified_conversation(self, pr_data: PRData, issues_data: List[IssueData]) -> List[ConversationEntry]:
        """Build chronological conversation from issues and PR"""
        conversation = []
        
        # Add issue comments
        for issue in issues_data:
            for comment in issue.comments:
                conversation.append(ConversationEntry(
                    type="issue_comment",
                    author=comment.get("author", {}).get("login", ""),
                    created_at=comment.get("createdAt", ""),
                    body=comment.get("body", ""),
                    url=comment.get("url", ""),
                    metadata={"issue_number": issue.number}
                ))
        
        # Add PR comments
        for comment in pr_data.comments:
            conversation.append(ConversationEntry(
                type="pr_comment",
                author=comment.get("author", {}).get("login", ""),
                created_at=comment.get("createdAt", ""),
                body=comment.get("body", ""),
                url=comment.get("url", ""),
                metadata={"pr_number": pr_data.number}
            ))
        
        # Add PR reviews
        for review in pr_data.reviews:
            if review.get("body"):  # Only include reviews with content
                conversation.append(ConversationEntry(
                    type="review",
                    author=review.get("user", {}).get("login", ""),
                    created_at=review.get("submitted_at", ""),
                    body=review.get("body", ""),
                    url=review.get("html_url", ""),
                    metadata={
                        "pr_number": pr_data.number,
                        "review_state": review.get("state", "")
                    }
                ))
        
        # Sort chronologically
        conversation.sort(key=lambda x: x.created_at)
        
        return conversation
    
    def _extract_linked_issues(self, text: str) -> List[int]:
        """Extract linked issue numbers from text"""
        # Common patterns for linking issues
        patterns = [
            r'[Ff]ixes?\s+#(\d+)',
            r'[Cc]loses?\s+#(\d+)',
            r'[Rr]esolves?\s+#(\d+)',
            r'[Rr]elated\s+to\s+#(\d+)',
            r'[Ss]ee\s+#(\d+)',
            r'#(\d+)'
        ]
        
        issue_numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            issue_numbers.extend([int(num) for num in matches])
        
        return list(set(issue_numbers))  # Remove duplicates
    
    def _gh_api_call(self, args: List[str]) -> Any:
        """Make GitHub CLI API call with rate limiting"""
        self._rate_limit()
        
        try:
            # Handle different GitHub CLI commands
            if args[0] in ["pr", "issue"]:
                # For pr and issue commands, use --repo flag
                full_args = ["gh", "--repo", self.repository] + args
            else:
                # For api commands, just use gh api directly
                full_args = ["gh"] + args
            
            result = subprocess.run(
                full_args,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                return json.loads(result.stdout)
            return {}
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"GitHub API call failed: {' '.join(args)}\nError: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse GitHub API response: {e}")
    
    def _rate_limit(self, delay: float = 0.1):
        """Simple rate limiting for GitHub API calls"""
        current_time = time.time()
        if current_time - self.last_request_time < delay:
            time.sleep(delay)
        self.last_request_time = current_time
        self.request_count += 1
    
    def _has_recent_cache(self, pr_context_dir: Path) -> bool:
        """Check if we have recent cached data"""
        cache_file = pr_context_dir / "analysis-cache.json"
        if not cache_file.exists():
            return False
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cache_data.get("collection_timestamp", ""))
            age_seconds = (datetime.now() - cache_time).total_seconds()
            
            return age_seconds < self.cache_duration
            
        except Exception:
            return False
    
    def _load_cached_context(self, pr_context_dir: Path) -> Dict[str, Any]:
        """Load cached context data"""
        cache_file = pr_context_dir / "analysis-cache.json"
        with open(cache_file, 'r') as f:
            return json.load(f)
    
    def _save_context_data(self, pr_context_dir: Path, context_data: Dict[str, Any]):
        """Save context data to structured JSON files"""
        # Save individual data files
        files_to_save = [
            ("issue-data.json", context_data["issues_data"]),
            ("pr-data.json", context_data["pr_data"]),
            ("file-changes.json", context_data["file_changes"]),
            ("conversation.json", context_data["conversation"]),
            ("analysis-cache.json", context_data)  # Full cache
        ]
        
        for filename, data in files_to_save:
            file_path = pr_context_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        Logger.info(f"📁 Context data saved to {pr_context_dir}")


def main():
    """Command-line interface for PR context collection"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 pr_context_collector.py <pr_number> [--force-refresh] [--context-dir <path>]")
        print("\nExamples:")
        print("  python3 pr_context_collector.py 3386")
        print("  python3 pr_context_collector.py 3386 --force-refresh")
        print("  python3 pr_context_collector.py 3386 --context-dir /path/to/context")
        sys.exit(1)
    
    pr_number = sys.argv[1]
    force_refresh = "--force-refresh" in sys.argv
    
    # Parse context directory argument
    context_dir = None
    if "--context-dir" in sys.argv:
        try:
            idx = sys.argv.index("--context-dir")
            if idx + 1 < len(sys.argv):
                context_dir = Path(sys.argv[idx + 1])
            else:
                print("Error: --context-dir requires a path argument")
                sys.exit(1)
        except ValueError:
            pass
    
    # Use script directory for context collection (robust regardless of where script is called from)
    working_dir = Path(__file__).parent.absolute()
    collector = PRContextCollector(working_dir, context_dir=context_dir)
    
    # Collect context data
    context_data = collector.collect_all_context(pr_number, force_refresh)
    
    if context_data:
        print(f"\n✅ Successfully collected context for PR #{pr_number}")
        print(f"📊 Data collected:")
        print(f"   - Issues: {len(context_data.get('issues_data', []))}")
        print(f"   - File changes: {len(context_data.get('file_changes', []))}")
        print(f"   - Conversation entries: {len(context_data.get('conversation', []))}")
        sys.exit(0)
    else:
        print(f"\n❌ Failed to collect context for PR #{pr_number}")
        sys.exit(1)


if __name__ == "__main__":
    main()
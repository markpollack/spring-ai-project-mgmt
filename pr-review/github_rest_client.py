#!/usr/bin/env python3
"""
GitHub REST API Client - Drop-in replacement for gh CLI calls.

Uses urllib (no external deps) to call GitHub REST API directly,
bypassing SAML SSO issues with gh CLI OAuth tokens.

Supports optional GITHUB_TOKEN env var for higher rate limits (5000/hr vs 60/hr).
"""

import json
import os
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional


class GitHubRestClient:
    """Direct GitHub REST API client that replaces gh CLI calls."""

    BASE_URL = "https://api.github.com"

    def __init__(self, repository: str = "spring-projects/spring-ai"):
        self.repository = repository
        self.token = os.environ.get("GITHUB_TOKEN")
        self._last_request_time = 0
        self._min_interval = 0.1  # 100ms between requests

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "spring-ai-pr-review",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def _rate_limit(self):
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _get(self, path: str, paginate: bool = False) -> Any:
        """Make GET request to GitHub API."""
        self._rate_limit()
        url = f"{self.BASE_URL}/{path.lstrip('/')}"

        if not paginate:
            req = urllib.request.Request(url, headers=self._headers())
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as e:
                body = e.read().decode() if e.fp else ""
                raise Exception(f"GitHub API error {e.code}: {body}")

        # Paginated request
        all_results = []
        page = 1
        while True:
            sep = "&" if "?" in url else "?"
            page_url = f"{url}{sep}per_page=100&page={page}"
            req = urllib.request.Request(page_url, headers=self._headers())
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode())
                    if not data or not isinstance(data, list):
                        if isinstance(data, list):
                            break
                        all_results = data  # Single object, not a list
                        break
                    all_results.extend(data)
                    if len(data) < 100:
                        break
                    page += 1
            except urllib.error.HTTPError as e:
                body = e.read().decode() if e.fp else ""
                raise Exception(f"GitHub API error {e.code}: {body}")

        return all_results

    # === PR Operations ===

    def get_pr(self, pr_number: str) -> Dict[str, Any]:
        """Get full PR data. Replaces: gh pr view <num> --json ..."""
        return self._get(f"repos/{self.repository}/pulls/{pr_number}")

    def get_pr_files(self, pr_number: str) -> List[Dict[str, Any]]:
        """Get PR changed files. Replaces: gh api repos/.../pulls/<num>/files"""
        return self._get(f"repos/{self.repository}/pulls/{pr_number}/files", paginate=True)

    def get_pr_commits(self, pr_number: str) -> List[Dict[str, Any]]:
        """Get PR commits. Replaces: gh api repos/.../pulls/<num>/commits"""
        return self._get(f"repos/{self.repository}/pulls/{pr_number}/commits", paginate=True)

    def get_pr_reviews(self, pr_number: str) -> List[Dict[str, Any]]:
        """Get PR reviews. Replaces: gh api repos/.../pulls/<num>/reviews"""
        return self._get(f"repos/{self.repository}/pulls/{pr_number}/reviews")

    def get_pr_comments(self, pr_number: str) -> List[Dict[str, Any]]:
        """Get PR issue comments (not review comments)."""
        return self._get(f"repos/{self.repository}/issues/{pr_number}/comments", paginate=True)

    def list_prs(self, limit: int = 1) -> List[Dict[str, Any]]:
        """List open PRs. Replaces: gh pr list --limit N"""
        return self._get(f"repos/{self.repository}/pulls?state=open&per_page={limit}")

    # === Issue Operations ===

    def get_issue(self, issue_number: int) -> Dict[str, Any]:
        """Get issue data. Replaces: gh issue view <num> --json ..."""
        return self._get(f"repos/{self.repository}/issues/{issue_number}")

    def get_issue_comments(self, issue_number: int) -> List[Dict[str, Any]]:
        """Get issue comments."""
        return self._get(f"repos/{self.repository}/issues/{issue_number}/comments", paginate=True)

    # === Repository Operations ===

    def get_repo(self) -> Dict[str, Any]:
        """Get repo info. Replaces: gh repo view --json name"""
        return self._get(f"repos/{self.repository}")

    def check_access(self) -> bool:
        """Check if API access works (replaces gh auth status for our purposes)."""
        try:
            self.get_repo()
            return True
        except Exception:
            return False

    # === Convenience: gh CLI compatible data extraction ===

    def get_pr_branch_info(self, pr_number: str) -> Dict[str, Any]:
        """Get PR branch info in gh-compatible format.

        Returns dict with: headRefName, headRepository, baseRefName, headRepositoryOwner
        """
        pr = self.get_pr(pr_number)
        head = pr.get("head", {})
        base = pr.get("base", {})
        head_repo = head.get("repo") or {}
        head_owner = head_repo.get("owner", {}) if head_repo else {}

        return {
            "headRefName": head.get("ref", ""),
            "headRepository": {"name": head_repo.get("name", "")} if head_repo else None,
            "baseRefName": base.get("ref", ""),
            "headRepositoryOwner": {"login": head_owner.get("login", "")} if head_owner else None,
        }

    def get_pr_basic_info(self, pr_number: str) -> Dict[str, Any]:
        """Get basic PR info in gh-compatible format.

        Returns dict with: number, title, author, headRefName, state, createdAt
        """
        pr = self.get_pr(pr_number)
        return {
            "number": pr.get("number"),
            "title": pr.get("title", ""),
            "author": {"login": pr.get("user", {}).get("login", "")},
            "headRefName": pr.get("head", {}).get("ref", ""),
            "state": pr.get("state", ""),
            "createdAt": pr.get("created_at", ""),
        }

    def get_pr_squash_info(self, pr_number: str) -> Dict[str, Any]:
        """Get PR info for squashing in gh-compatible format.

        Returns dict with: baseRefOid, headRefOid, commits, title
        """
        pr = self.get_pr(pr_number)
        commits_raw = self.get_pr_commits(pr_number)

        commits = []
        for c in commits_raw:
            commits.append({
                "oid": c.get("sha", ""),
                "messageHeadline": c.get("commit", {}).get("message", "").split("\n")[0],
                "messageBody": c.get("commit", {}).get("message", ""),
                "authors": [{"name": c.get("commit", {}).get("author", {}).get("name", ""),
                            "email": c.get("commit", {}).get("author", {}).get("email", "")}],
            })

        return {
            "baseRefOid": pr.get("base", {}).get("sha", ""),
            "headRefOid": pr.get("head", {}).get("sha", ""),
            "commits": commits,
            "title": pr.get("title", ""),
        }

    def get_pr_view_full(self, pr_number: str) -> Dict[str, Any]:
        """Get comprehensive PR data in gh-compatible format.

        Returns dict matching: gh pr view <num> --json number,title,body,...
        """
        pr = self.get_pr(pr_number)
        comments = self.get_pr_comments(pr_number)

        # Map REST API labels format to gh format
        labels = [{"name": l.get("name", "")} for l in pr.get("labels", [])]
        assignees = [{"login": a.get("login", "")} for a in pr.get("assignees", [])]
        review_requests = [{"login": r.get("login", "")} for r in pr.get("requested_reviewers", [])]

        # Get commits for count
        commits_raw = self.get_pr_commits(pr_number)
        commits_gh = []
        for c in commits_raw:
            commits_gh.append({
                "oid": c.get("sha", ""),
                "messageHeadline": c.get("commit", {}).get("message", "").split("\n")[0],
            })

        return {
            "number": pr.get("number"),
            "title": pr.get("title", ""),
            "body": pr.get("body", ""),
            "state": pr.get("state", "").upper(),
            "isDraft": pr.get("draft", False),
            "labels": labels,
            "assignees": assignees,
            "reviewRequests": review_requests,
            "createdAt": pr.get("created_at", ""),
            "updatedAt": pr.get("updated_at", ""),
            "author": {"login": pr.get("user", {}).get("login", "")},
            "url": pr.get("html_url", ""),
            "baseRefName": pr.get("base", {}).get("ref", ""),
            "headRefName": pr.get("head", {}).get("ref", ""),
            "commits": commits_gh,
            "changedFiles": pr.get("changed_files", 0),
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "comments": [{
                "author": {"login": c.get("user", {}).get("login", "")},
                "body": c.get("body", ""),
                "createdAt": c.get("created_at", ""),
                "url": c.get("html_url", ""),
            } for c in comments],
        }

    def get_issue_full(self, issue_number: int) -> Dict[str, Any]:
        """Get issue data in gh-compatible format."""
        issue = self.get_issue(issue_number)
        comments = self.get_issue_comments(issue_number)

        return {
            "number": issue.get("number"),
            "title": issue.get("title", ""),
            "body": issue.get("body", ""),
            "state": issue.get("state", "").upper(),
            "labels": [{"name": l.get("name", "")} for l in issue.get("labels", [])],
            "assignees": [{"login": a.get("login", "")} for a in issue.get("assignees", [])],
            "createdAt": issue.get("created_at", ""),
            "updatedAt": issue.get("updated_at", ""),
            "author": {"login": issue.get("user", {}).get("login", "")},
            "url": issue.get("html_url", ""),
            "comments": [{
                "author": {"login": c.get("user", {}).get("login", "")},
                "body": c.get("body", ""),
                "createdAt": c.get("created_at", ""),
                "url": c.get("html_url", ""),
            } for c in comments],
        }

    def get_pr_file_paths(self, pr_number: str) -> List[str]:
        """Get just file paths from PR. Replaces: gh pr view --json files --jq .files[].path"""
        files = self.get_pr_files(pr_number)
        return [f.get("filename", "") for f in files if f.get("filename")]


# Singleton for easy import
_default_client = None

def get_client(repository: str = "spring-projects/spring-ai") -> GitHubRestClient:
    """Get or create a GitHubRestClient singleton."""
    global _default_client
    if _default_client is None or _default_client.repository != repository:
        _default_client = GitHubRestClient(repository)
    return _default_client

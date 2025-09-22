#!/usr/bin/env python3
"""
Git Analysis for Blog Generation

Lightweight git analysis specifically for Spring AI blog generation.
Extracts the essential git analysis logic from generate-release-notes.py
without the complexity of full release note generation.

Usage:
    from git_analysis_for_blog import BlogGitAnalyzer, GitCommitData
    
    analyzer = BlogGitAnalyzer("/path/to/spring-ai", "1.0.1", "1.1.0-M1")
    commits = analyzer.collect_commits()
    analysis = analyzer.analyze_commits(commits)
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict


# Simple logging for this module
class Logger:
    @staticmethod
    def info(msg): print(f"\033[34m[INFO]\033[0m {msg}")
    @staticmethod
    def warn(msg): print(f"\033[33m[WARN]\033[0m {msg}")
    @staticmethod
    def error(msg): print(f"\033[31m[ERROR]\033[0m {msg}")
    @staticmethod
    def debug(msg): 
        if os.environ.get('DEBUG'): 
            print(f"\033[36m[DEBUG]\033[0m {msg}")


@dataclass
class GitCommitData:
    """Basic commit information from git log"""
    sha: str
    message: str
    author: str
    email: str
    date: str
    
    @property
    def short_sha(self) -> str:
        return self.sha[:7]


@dataclass
class BlogCommitAnalysis:
    """Analysis results for blog generation"""
    total_commits: int = 0
    bug_fixes: int = 0
    new_features: int = 0
    documentation: int = 0
    dependency_upgrades: int = 0
    other_improvements: int = 0
    contributors: List[str] = None
    
    def __post_init__(self):
        if self.contributors is None:
            self.contributors = []


class BlogGitAnalyzer:
    """Lightweight git analyzer for blog generation"""
    
    def __init__(self, repo_path: str, since_version: str, target_version: str = None):
        self.repo_path = Path(repo_path)
        self.since_version = since_version
        self.target_version = target_version
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
    
    def collect_commits(self) -> List[GitCommitData]:
        """Collect commits using tag-to-tag analysis"""
        Logger.info(f"🔍 Collecting commits from {self.since_version} to {self.target_version or 'HEAD'}")
        
        original_dir = os.getcwd()
        try:
            os.chdir(self.repo_path)
            
            # Fetch latest tags
            Logger.debug("Fetching latest tags from origin")
            fetch_cmd = ['git', 'fetch', '--tags', 'origin']
            subprocess.run(fetch_cmd, capture_output=True, text=True, check=True)
            
            # Determine since tag
            since_tag = self._resolve_tag(self.since_version)
            if not since_tag:
                raise ValueError(f"Could not resolve since tag: {self.since_version}")
            
            # Build commit range
            if self.target_version:
                target_tag = self._resolve_tag(self.target_version)
                if target_tag:
                    commit_range = f"{since_tag}..{target_tag}"
                    Logger.info(f"Using range: {since_tag} to {target_tag}")
                else:
                    commit_range = f"{since_tag}..HEAD"
                    Logger.info(f"Using range: {since_tag} to HEAD (target tag not found)")
            else:
                commit_range = f"{since_tag}..HEAD"
                Logger.info(f"Using range: {since_tag} to HEAD")
            
            # Get expected count
            count_cmd = ['git', 'rev-list', '--count', commit_range]
            count_result = subprocess.run(count_cmd, capture_output=True, text=True, check=True)
            expected_count = int(count_result.stdout.strip())
            Logger.info(f"Expected commits: {expected_count}")
            
            if expected_count == 0:
                Logger.warn("No commits found in range")
                return []
            
            # Get commits with metadata
            cmd = ['git', 'log', commit_range, '--format=%H|%s|%aN|%aE|%aI']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            commit_lines = result.stdout.strip().split('\n')
            if not commit_lines or commit_lines == ['']:
                Logger.warn("No commit data found")
                return []
            
            commits = []
            for line in commit_lines:
                if not line:
                    continue
                
                parts = line.split('|', 4)
                if len(parts) != 5:
                    Logger.debug(f"Skipping malformed commit line: {line}")
                    continue
                
                commits.append(GitCommitData(
                    sha=parts[0],
                    message=parts[1],
                    author=parts[2],
                    email=parts[3],
                    date=parts[4]
                ))
            
            Logger.info(f"✅ Collected {len(commits)} commits")
            return commits
            
        finally:
            os.chdir(original_dir)
    
    def _resolve_tag(self, version: str) -> Optional[str]:
        """Resolve version to actual git tag"""
        candidates = [
            f"v{version}",
            version,
            f"refs/tags/v{version}",
            f"refs/tags/{version}"
        ]
        
        for candidate in candidates:
            try:
                cmd = ['git', 'rev-parse', '--verify', f"{candidate}^{{tag}}"]
                result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)
                if result.returncode == 0:
                    Logger.debug(f"Resolved {version} to tag: {candidate}")
                    return candidate
            except subprocess.CalledProcessError:
                continue
        
        # Try without ^{tag} for commits
        for candidate in candidates:
            try:
                cmd = ['git', 'rev-parse', '--verify', candidate]
                result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)
                if result.returncode == 0:
                    Logger.debug(f"Resolved {version} to ref: {candidate}")
                    return candidate
            except subprocess.CalledProcessError:
                continue
        
        Logger.error(f"Could not resolve version tag: {version}")
        return None
    
    def analyze_commits(self, commits: List[GitCommitData]) -> BlogCommitAnalysis:
        """Analyze commits for blog metrics"""
        Logger.info(f"📊 Analyzing {len(commits)} commits for blog metrics")
        
        analysis = BlogCommitAnalysis()
        analysis.total_commits = len(commits)
        
        # Extract unique contributors
        contributors = set()
        
        # Categorize commits based on message patterns
        for commit in commits:
            msg = commit.message.lower()
            contributors.add(commit.author)
            
            # Simple pattern-based categorization
            if any(pattern in msg for pattern in ['fix:', 'fix(', 'bug', 'issue', 'error', 'exception']):
                analysis.bug_fixes += 1
            elif any(pattern in msg for pattern in ['feat:', 'feat(', 'add', 'implement', 'new ']):
                analysis.new_features += 1
            elif any(pattern in msg for pattern in ['docs:', 'docs(', 'doc:', 'readme', 'documentation']):
                analysis.documentation += 1
            elif any(pattern in msg for pattern in ['bump', 'upgrade', 'update.*version', 'dependency', 'deps']):
                analysis.dependency_upgrades += 1
            elif any(pattern in msg for pattern in ['refactor', 'improve', 'enhance', 'optimize', 'cleanup']):
                analysis.other_improvements += 1
            else:
                # Default to other improvements for uncategorized commits
                analysis.other_improvements += 1
        
        analysis.contributors = sorted(list(contributors))
        
        Logger.info(f"📈 Analysis complete:")
        Logger.info(f"  - Total commits: {analysis.total_commits}")
        Logger.info(f"  - New features: {analysis.new_features}")
        Logger.info(f"  - Bug fixes: {analysis.bug_fixes}")
        Logger.info(f"  - Documentation: {analysis.documentation}")
        Logger.info(f"  - Dependency upgrades: {analysis.dependency_upgrades}")
        Logger.info(f"  - Other improvements: {analysis.other_improvements}")
        
        return analysis
    
    def get_contributors_details(self, commits: List[GitCommitData]) -> List[Dict[str, Any]]:
        """Get detailed contributor information"""
        contributor_stats = defaultdict(lambda: {
            'name': '',
            'email': '',
            'commits': 0,
            'first_commit': None,
            'last_commit': None
        })
        
        for commit in commits:
            stats = contributor_stats[commit.email]
            stats['name'] = commit.author
            stats['email'] = commit.email
            stats['commits'] += 1
            
            if not stats['first_commit'] or commit.date < stats['first_commit']:
                stats['first_commit'] = commit.date
            if not stats['last_commit'] or commit.date > stats['last_commit']:
                stats['last_commit'] = commit.date
        
        # Sort by commit count descending
        return sorted(contributor_stats.values(), key=lambda x: x['commits'], reverse=True)
    
    def generate_summary(self, analysis: BlogCommitAnalysis) -> str:
        """Generate a text summary for debugging"""
        lines = [
            f"Git Analysis Summary for {self.since_version} → {self.target_version or 'HEAD'}",
            "=" * 60,
            f"Total Commits: {analysis.total_commits}",
            f"New Features: {analysis.new_features}",
            f"Bug Fixes: {analysis.bug_fixes}",
            f"Documentation: {analysis.documentation}",
            f"Dependency Upgrades: {analysis.dependency_upgrades}",
            f"Other Improvements: {analysis.other_improvements}",
            f"Contributors: {len(analysis.contributors)}",
            "",
            "Top Contributors:",
        ]
        
        for i, contributor in enumerate(analysis.contributors[:10]):
            lines.append(f"  {i+1}. {contributor}")
        
        return "\n".join(lines)


def main():
    """CLI interface for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Git analysis for Spring AI blog generation")
    parser.add_argument('--repo-path', default='/home/mark/projects/spring-ai', help='Path to Spring AI repository')
    parser.add_argument('--since-version', default='1.0.1', help='Since version')
    parser.add_argument('--target-version', help='Target version (default: HEAD)')
    parser.add_argument('--verbose', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        os.environ['DEBUG'] = '1'
    
    analyzer = BlogGitAnalyzer(args.repo_path, args.since_version, args.target_version)
    
    # Collect commits
    commits = analyzer.collect_commits()
    
    # Analyze commits
    analysis = analyzer.analyze_commits(commits)
    
    # Print summary
    print("\n" + analyzer.generate_summary(analysis))
    
    # Show contributor details if verbose
    if args.verbose:
        print("\nDetailed Contributors:")
        contributors = analyzer.get_contributors_details(commits)
        for contrib in contributors[:10]:
            print(f"  {contrib['name']} ({contrib['email']}): {contrib['commits']} commits")


if __name__ == "__main__":
    main()
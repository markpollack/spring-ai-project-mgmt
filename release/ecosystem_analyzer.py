#!/usr/bin/env python3
"""
Spring AI Ecosystem Repository Analyzer

Analyzes external Spring AI ecosystem repositories for release blog metrics:
- spring-projects/spring-ai-examples
- spring-ai-community/awesome-spring-ai

Since these repositories don't use semantic versioning tags, analysis is based on
date ranges derived from the main Spring AI release dates.

Usage:
    from ecosystem_analyzer import EcosystemAnalyzer
    
    analyzer = EcosystemAnalyzer()
    metrics = analyzer.analyze_since_date("2024-01-15")  # Since 1.0.1 release
    
Features:
- Repository cloning with caching
- Date-based commit analysis
- Community contribution metrics
- Example/tutorial discovery
- Blog post and resource curation tracking
"""

import os
import sys
import subprocess
import json
import re
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict

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
    def debug(msg): 
        if os.environ.get('DEBUG'): 
            print(f"\033[36m[DEBUG]\033[0m {msg}")
    @staticmethod
    def bold(msg): print(f"\033[1m{msg}\033[0m")


@dataclass
class RepositoryConfig:
    """Configuration for a repository to analyze"""
    name: str
    url: str
    local_path: Path
    analysis_patterns: Dict[str, List[str]] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.analysis_patterns:
            # Default patterns for different repo types
            if 'examples' in self.name.lower():
                self.analysis_patterns = {
                    'new_examples': ['README.md', 'pom.xml', 'build.gradle'],  # New project creation indicators
                    'mcp_features': ['mcp', 'MCP'],  # Direct MCP-related content
                    'ai_tests': ['Test.java', 'IT.java']  # Test files
                }
            elif 'awesome' in self.name.lower():
                self.analysis_patterns = {
                    'blog_posts': ['blog', 'article'],  # Look for blog-related content in commit messages
                    'tutorials': ['tutorial', 'guide', 'how-to'],   # Tutorial-related keywords
                    'resources': ['resource', 'link', 'tool']    # Resource additions
                }


@dataclass
class CommitAnalysis:
    """Analysis result for a single commit"""
    sha: str
    message: str
    author: str
    date: str
    files_changed: List[str] = field(default_factory=list)
    categories: Set[str] = field(default_factory=set)


@dataclass 
class EcosystemMetrics:
    """Comprehensive ecosystem metrics"""
    # Community momentum
    total_contributors: int = 0
    new_contributors: int = 0
    returning_contributors: int = 0
    
    # Contribution activity  
    total_commits: int = 0
    merged_prs: int = 0
    
    # Ecosystem growth
    new_examples: int = 0
    mcp_features: int = 0
    ai_tests: int = 0
    blog_posts: int = 0
    tutorials: int = 0
    resources_added: int = 0
    
    # Detailed data
    contributor_details: List[Dict] = field(default_factory=list)
    commit_analysis: List[CommitAnalysis] = field(default_factory=list)
    repository_metrics: Dict[str, Dict] = field(default_factory=dict)


class EcosystemAnalyzer:
    """Analyzes Spring AI ecosystem repositories for release metrics"""
    
    def __init__(self, cache_dir: Path = None, refresh_cache: bool = False):
        self.script_dir = Path(__file__).parent
        self.cache_dir = cache_dir or (self.script_dir / ".ecosystem_cache")
        self.refresh_cache = refresh_cache
        self.cache_dir.mkdir(exist_ok=True)
        
        # Define repositories to analyze
        self.repositories = [
            RepositoryConfig(
                name="spring-ai-examples",
                url="https://github.com/spring-projects/spring-ai-examples.git",
                local_path=self.cache_dir / "spring-ai-examples"
            ),
            RepositoryConfig(
                name="awesome-spring-ai", 
                url="https://github.com/spring-ai-community/awesome-spring-ai.git",
                local_path=self.cache_dir / "awesome-spring-ai"
            )
        ]
    
    def analyze_since_date(self, since_date: str) -> EcosystemMetrics:
        """Analyze ecosystem repositories since a specific date"""
        Logger.bold(f"🌟 SPRING AI ECOSYSTEM ANALYSIS")
        Logger.bold(f"Analysis Date Range: {since_date} → present")
        Logger.bold("=" * 50)
        
        metrics = EcosystemMetrics()
        
        for repo_config in self.repositories:
            Logger.info(f"📊 Analyzing repository: {repo_config.name}")
            
            # Ensure repository is available
            if not self._ensure_repository(repo_config):
                Logger.error(f"Failed to prepare repository: {repo_config.name}")
                continue
            
            # Analyze repository
            repo_metrics = self._analyze_repository(repo_config, since_date)
            
            # Merge into overall metrics
            self._merge_metrics(metrics, repo_metrics, repo_config.name)
            
            Logger.success(f"✅ Completed analysis for {repo_config.name}")
        
        # Calculate derived metrics
        self._calculate_derived_metrics(metrics)
        
        Logger.bold("=" * 50)
        Logger.success(f"🎯 Analysis complete: {metrics.total_commits} commits, {metrics.total_contributors} contributors")
        
        return metrics
    
    def _ensure_repository(self, config: RepositoryConfig) -> bool:
        """Ensure repository is cloned and up to date"""
        try:
            if config.local_path.exists() and not self.refresh_cache:
                Logger.debug(f"Using cached repository: {config.local_path}")
                # Just fetch latest changes
                result = subprocess.run([
                    'git', 'fetch', 'origin'
                ], cwd=config.local_path, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    return True
                else:
                    Logger.warn(f"Git fetch failed, will re-clone: {result.stderr}")
            
            # Remove existing directory if refresh requested or if fetch failed
            if config.local_path.exists():
                Logger.info(f"Removing cached repository for refresh: {config.local_path}")
                shutil.rmtree(config.local_path)
            
            # Clone repository
            Logger.info(f"Cloning repository: {config.url}")
            result = subprocess.run([
                'git', 'clone', config.url, str(config.local_path)
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                Logger.error(f"Git clone failed: {result.stderr}")
                return False
            
            Logger.success(f"Repository cloned successfully: {config.name}")
            return True
            
        except Exception as e:
            Logger.error(f"Error preparing repository {config.name}: {e}")
            return False
    
    def _analyze_repository(self, config: RepositoryConfig, since_date: str) -> Dict[str, Any]:
        """Analyze a single repository for metrics"""
        try:
            # Get commits since date
            commits = self._get_commits_since_date(config, since_date)
            Logger.info(f"Found {len(commits)} commits since {since_date}")
            
            # Analyze commits for patterns
            analyzed_commits = []
            for commit in commits:
                analysis = self._analyze_commit(config, commit)
                if analysis:
                    analyzed_commits.append(analysis)
            
            # Extract contributors
            contributors = self._extract_contributors(commits)
            
            # Calculate category metrics
            category_metrics = self._calculate_category_metrics(analyzed_commits, config)
            
            return {
                'commits': analyzed_commits,
                'contributors': contributors,
                'metrics': category_metrics,
                'total_commits': len(commits)
            }
            
        except Exception as e:
            Logger.error(f"Error analyzing repository {config.name}: {e}")
            return {'commits': [], 'contributors': [], 'metrics': {}, 'total_commits': 0}
    
    def _get_commits_since_date(self, config: RepositoryConfig, since_date: str) -> List[Dict]:
        """Get commits from repository since specified date"""
        try:
            cmd = [
                'git', 'log', f'--since={since_date}', 
                '--format=%H|%aN|%aE|%aI|%s'
            ]
            
            result = subprocess.run(
                cmd, cwd=config.local_path,
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                Logger.warn(f"Git log failed for {config.name}: {result.stderr}")
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.strip().split('|', 4)
                    if len(parts) == 5:
                        commits.append({
                            'sha': parts[0],
                            'author': parts[1],
                            'email': parts[2], 
                            'date': parts[3],
                            'message': parts[4]
                        })
            
            return commits
            
        except Exception as e:
            Logger.error(f"Error getting commits for {config.name}: {e}")
            return []
    
    def _analyze_commit(self, config: RepositoryConfig, commit: Dict) -> Optional[CommitAnalysis]:
        """Analyze a single commit for patterns"""
        try:
            # Get files changed in this commit
            result = subprocess.run([
                'git', 'show', '--name-only', '--format=', commit['sha']
            ], cwd=config.local_path, capture_output=True, text=True, timeout=10)
            
            files_changed = []
            if result.returncode == 0:
                files_changed = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            
            # Categorize commit based on patterns
            categories = set()
            message_lower = commit['message'].lower()
            
            # Analyze against repository patterns
            for category, patterns in config.analysis_patterns.items():
                for pattern in patterns:
                    # Extract meaningful keywords from pattern (not splitting on '*')
                    pattern_keywords = []
                    if '**/' in pattern:
                        # Extract the meaningful part after the glob
                        meaningful_part = pattern.split('**/')[1] if '**/' in pattern else pattern
                        if meaningful_part and meaningful_part != '*':
                            pattern_keywords.append(meaningful_part.lower())
                    elif '*' not in pattern:
                        # Direct file pattern
                        pattern_keywords.append(pattern.lower())
                    else:
                        # Other patterns - extract non-wildcard parts
                        parts = [p for p in pattern.split('*') if p and len(p) > 1]
                        pattern_keywords.extend(p.lower() for p in parts)
                    
                    # Check message content for meaningful keywords only
                    if pattern_keywords and any(keyword in message_lower for keyword in pattern_keywords):
                        categories.add(category)
                    
                    # Check changed files
                    if any(self._matches_pattern(f, pattern) for f in files_changed):
                        categories.add(category)
            
            # Additional semantic analysis
            if any(keyword in message_lower for keyword in ['feat:', 'add', 'new', 'implement']):
                categories.add('feature')
            if any(keyword in message_lower for keyword in ['fix:', 'bug', 'issue']):
                categories.add('bugfix')
            if any(keyword in message_lower for keyword in ['doc:', 'docs', 'readme']):
                categories.add('documentation')
            
            return CommitAnalysis(
                sha=commit['sha'],
                message=commit['message'],
                author=commit['author'],
                date=commit['date'],
                files_changed=files_changed,
                categories=categories
            )
            
        except Exception as e:
            Logger.debug(f"Error analyzing commit {commit['sha']}: {e}")
            return None
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches a glob-like pattern"""
        import fnmatch
        return fnmatch.fnmatch(filename.lower(), pattern.lower())
    
    def _extract_contributors(self, commits: List[Dict]) -> List[Dict]:
        """Extract unique contributor information"""
        contributors = {}
        
        for commit in commits:
            author = commit['author']
            email = commit['email']
            
            if author not in contributors:
                contributors[author] = {
                    'name': author,
                    'email': email,
                    'commits': 0,
                    'first_commit_date': commit['date'],
                    'last_commit_date': commit['date']
                }
            
            contributors[author]['commits'] += 1
            if commit['date'] < contributors[author]['first_commit_date']:
                contributors[author]['first_commit_date'] = commit['date']
            if commit['date'] > contributors[author]['last_commit_date']:
                contributors[author]['last_commit_date'] = commit['date']
        
        return list(contributors.values())
    
    def _calculate_category_metrics(self, commits: List[CommitAnalysis], config: RepositoryConfig) -> Dict[str, int]:
        """Calculate metrics by category"""
        metrics = defaultdict(int)
        
        for commit in commits:
            for category in commit.categories:
                metrics[category] += 1
        
        return dict(metrics)
    
    def _merge_metrics(self, overall: EcosystemMetrics, repo_metrics: Dict, repo_name: str) -> None:
        """Merge repository metrics into overall metrics"""
        overall.total_commits += repo_metrics['total_commits']
        overall.repository_metrics[repo_name] = repo_metrics['metrics']
        
        # Merge commit analysis
        overall.commit_analysis.extend(repo_metrics['commits'])
        
        # Merge contributors
        overall.contributor_details.extend([
            {'repository': repo_name, **contrib} 
            for contrib in repo_metrics['contributors']
        ])
        
        # Update category-specific metrics
        metrics = repo_metrics['metrics']
        overall.new_examples += metrics.get('new_examples', 0)
        overall.mcp_features += metrics.get('mcp_features', 0)
        overall.ai_tests += metrics.get('ai_tests', 0)
        overall.blog_posts += metrics.get('blog_posts', 0)
        overall.tutorials += metrics.get('tutorials', 0)
        overall.resources_added += metrics.get('resources', 0)
    
    def _calculate_derived_metrics(self, metrics: EcosystemMetrics) -> None:
        """Calculate derived metrics like unique contributors"""
        # Count unique contributors across all repositories
        unique_contributors = set()
        for contrib in metrics.contributor_details:
            unique_contributors.add(contrib['email'])  # Use email as unique identifier
        
        metrics.total_contributors = len(unique_contributors)
        
        # For now, consider all as new contributors since we don't have historical data
        # In a real implementation, you'd compare against a previous baseline
        metrics.new_contributors = metrics.total_contributors
        metrics.returning_contributors = 0
    
    def generate_summary_report(self, metrics: EcosystemMetrics) -> str:
        """Generate a summary report of ecosystem metrics"""
        lines = [
            "# Spring AI Ecosystem Analysis Report",
            "",
            "## Community Momentum",
            f"- **Total Contributors**: {metrics.total_contributors}",
            f"- **New Contributors**: {metrics.new_contributors}",
            f"- **Returning Contributors**: {metrics.returning_contributors}",
            "",
            "## Contribution Activity",
            f"- **Total Commits**: {metrics.total_commits}",
            "",
            "## Ecosystem Growth",
            f"- **New Examples**: {metrics.new_examples}",
            f"- **MCP Features**: {metrics.mcp_features}",
            f"- **AI Tests**: {metrics.ai_tests}",
            f"- **Blog Posts**: {metrics.blog_posts}",
            f"- **Tutorials**: {metrics.tutorials}",
            f"- **Resources Added**: {metrics.resources_added}",
            "",
            "## Repository Breakdown"
        ]
        
        for repo_name, repo_metrics in metrics.repository_metrics.items():
            lines.append(f"### {repo_name}")
            for category, count in repo_metrics.items():
                lines.append(f"- {category}: {count}")
            lines.append("")
        
        return "\n".join(lines)
    
    def save_metrics(self, metrics: EcosystemMetrics, output_file: Path) -> bool:
        """Save metrics to JSON file"""
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(asdict(metrics), f, indent=2, default=str)
            
            Logger.success(f"Metrics saved to: {output_file}")
            return True
            
        except Exception as e:
            Logger.error(f"Error saving metrics: {e}")
            return False
    
    def cleanup_cache(self) -> None:
        """Remove cached repositories"""
        try:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                Logger.success("Cache cleaned up")
        except Exception as e:
            Logger.error(f"Error cleaning cache: {e}")


def main():
    """CLI interface for ecosystem analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze Spring AI ecosystem repositories")
    parser.add_argument('--since-date', required=True, help='Start date for analysis (YYYY-MM-DD)')
    parser.add_argument('--output-dir', help='Output directory for results')
    parser.add_argument('--refresh-cache', action='store_true', help='Refresh cached repositories')
    parser.add_argument('--cleanup', action='store_true', help='Clean up cached repositories')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be analyzed')
    
    args = parser.parse_args()
    
    if args.cleanup:
        analyzer = EcosystemAnalyzer()
        analyzer.cleanup_cache()
        return
    
    if args.dry_run:
        Logger.info(f"DRY RUN: Would analyze ecosystem since {args.since_date}")
        analyzer = EcosystemAnalyzer()
        for repo in analyzer.repositories:
            Logger.info(f"  - {repo.name}: {repo.url}")
        return
    
    # Run analysis
    analyzer = EcosystemAnalyzer(refresh_cache=args.refresh_cache)
    metrics = analyzer.analyze_since_date(args.since_date)
    
    # Generate report
    report = analyzer.generate_summary_report(metrics)
    print("\n" + report)
    
    # Save results if output directory specified
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON metrics
        metrics_file = output_dir / 'ecosystem_metrics.json'
        analyzer.save_metrics(metrics, metrics_file)
        
        # Save report
        report_file = output_dir / 'ecosystem_report.md'
        with open(report_file, 'w') as f:
            f.write(report)
        Logger.success(f"Report saved to: {report_file}")


if __name__ == "__main__":
    main()
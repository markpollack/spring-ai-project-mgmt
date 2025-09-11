#!/usr/bin/env python3
"""
Spring AI Blog Post Generator

Generates blog posts for Spring AI releases following established patterns
from markpollack's previous posts and Spring ecosystem conventions.

Features:
- Smart version baseline logic (1.1.0-M1 baselines from latest 1.0.x patch)
- Multi-repository ecosystem analysis (spring-ai-examples, awesome-spring-ai)
- Community metrics (contributors, examples, blog posts, tutorials)
- MCP annotation examples and AI-powered test tracking
- Repository caching for faster repeated runs

Usage:
    python3 generate-blog-post.py 1.0.1 --dry-run
    python3 generate-blog-post.py 1.0.2 --output-file my-blog-post.md
    python3 generate-blog-post.py 1.1.0-M1 --analyze-ecosystem

Examples:
    # Generate blog post for 1.0.1 with dry run
    python3 generate-blog-post.py 1.0.1 --dry-run
    
    # Generate with contributor analysis
    python3 generate-blog-post.py 1.0.1 --include-contributors --since-version 1.0.0
    
    # Generate milestone release with ecosystem analysis
    python3 generate-blog-post.py 1.1.0-M1 --analyze-ecosystem --include-contributors
    
    # Custom output location with ecosystem cache refresh
    python3 generate-blog-post.py 1.0.1 --output-file /path/to/blog-post.md --analyze-ecosystem --refresh-ecosystem-cache
"""

import os
import sys
import subprocess
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Import the dedicated Claude Code wrapper
try:
    sys.path.append(str(Path(__file__).parent.parent / "pr-review"))
    from claude_code_wrapper import ClaudeCodeWrapper
    CLAUDE_WRAPPER_AVAILABLE = True
except ImportError as e:
    CLAUDE_WRAPPER_AVAILABLE = False

# Import documentation-based feature extractor (imported later after Logger is defined)

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

# Import documentation-based feature extractor  
try:
    import sys
    sys.path.append(str(Path(__file__).parent))
    from doc_based_feature_extractor import DocBasedFeatureExtractor, Feature
    DocBasedFeatureExtractor_available = True
except ImportError as e:
    DocBasedFeatureExtractor = None
    DocBasedFeatureExtractor_available = False

# Import ecosystem analyzer
try:
    from ecosystem_analyzer import EcosystemAnalyzer, EcosystemMetrics
    EcosystemAnalyzer_available = True
except ImportError as e:
    EcosystemAnalyzer = None
    EcosystemAnalyzer_available = False

# Import git analysis for blog
try:
    from git_analysis_for_blog import BlogGitAnalyzer, BlogCommitAnalysis
    BlogGitAnalyzer_available = True
except ImportError as e:
    BlogGitAnalyzer = None
    BlogGitAnalyzer_available = False

@dataclass
class ReleaseData:
    """Data structure for Spring AI release information"""
    version: str
    publish_date: str
    total_commits: int = 0
    bug_fixes: int = 0
    new_features: int = 0
    documentation: int = 0
    dependency_upgrades: int = 0
    other_improvements: int = 0
    contributors: List[str] = None
    key_highlights: List[str] = None
    github_release_url: str = ""
    previous_version: str = ""
    
    # Ecosystem metrics
    ecosystem_metrics: Optional[Any] = None  # EcosystemMetrics object
    ecosystem_contributors: int = 0
    ecosystem_examples: int = 0
    ecosystem_blog_posts: int = 0
    ecosystem_tutorials: int = 0
    mcp_features: int = 0
    ai_tests: int = 0
    
    def __post_init__(self):
        if self.contributors is None:
            self.contributors = []
        if self.key_highlights is None:
            self.key_highlights = []

class SpringAIBlogGenerator:
    """Generate Spring AI blog posts following established patterns"""
    
    def __init__(self, version: str, config: dict = None):
        self.version = version
        self.config = config or {}
        self.script_dir = Path(__file__).parent
        self.spring_ai_repo = Path("/home/mark/projects/spring-ai")
        self.website_content_repo = self.script_dir / "repos" / "spring-website-content"
        self.output_file = self.config.get('output_file') or f'spring-ai-{version.replace(".", "-")}-available-now.md'
        self.use_doc_based_features = self.config.get('use_doc_based_features', False)
        self.blog_seed_content = self._load_blog_seed_file()
        self.synthesis_data = self._load_synthesis_file()
        
    def generate_blog_post(self) -> bool:
        """Generate the complete blog post"""
        Logger.bold("🚀 SPRING AI BLOG POST GENERATOR")
        Logger.bold("=" * 50)
        Logger.info(f"Target Version: {self.version}")
        Logger.info(f"Output File: {self.output_file}")
        Logger.bold("=" * 50)
        
        # Gather release data
        release_data = self._gather_release_data()
        if not release_data:
            Logger.error("Failed to gather release data")
            return False
        
        # Generate blog content
        blog_content = self._generate_blog_content(release_data)
        if not blog_content:
            Logger.error("Failed to generate blog content")
            return False
        
        # Write blog post
        if self.config.get('dry_run'):
            Logger.info("🧪 DRY RUN - Generated blog post content:")
            Logger.bold("\n" + "=" * 60)
            print(blog_content)
            Logger.bold("=" * 60)
            Logger.info("👆 Remove --dry-run to write the actual file")
            return True
        else:
            return self._write_blog_post(blog_content)
    
    def _load_blog_seed_file(self) -> Optional[str]:
        """Load content from blog seed file if provided"""
        seed_file = self.config.get('blog_seed_file')
        if not seed_file:
            return None
            
        try:
            seed_path = Path(seed_file)
            if seed_path.exists():
                with open(seed_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    Logger.info(f"📝 Loaded blog seed from: {seed_file}")
                    return content
            else:
                Logger.warn(f"Blog seed file not found: {seed_file}")
                return None
        except Exception as e:
            Logger.warn(f"Failed to load blog seed file: {e}")
            return None
    
    def _load_synthesis_file(self) -> Optional[dict]:
        """Load AI synthesis data from file"""
        synthesis_file = self.config.get('synthesis_file')
        if not synthesis_file:
            # Try auto-detect based on version
            auto_file = self.script_dir / f".synthesis-{self.version}.json"
            if auto_file.exists():
                synthesis_file = str(auto_file)
            else:
                return None
        
        try:
            with open(synthesis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                Logger.info(f"📊 Loaded synthesis data from: {synthesis_file}")
                return data
        except Exception as e:
            Logger.warn(f"Failed to load synthesis file: {e}")
            return None
    
    def _extract_seed_highlights(self) -> Optional[str]:
        """Extract highlights section from blog seed file"""
        if not self.blog_seed_content:
            return None
            
        # Look for highlights section markers
        patterns = [
            r'## Key Highlights?\s*\n(.*?)(?=\n##|\Z)',
            r'# Highlights?\s*\n(.*?)(?=\n#|\Z)',
            r'HIGHLIGHTS?\s*[:\n](.*?)(?=\n[A-Z]{2,}|\Z)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.blog_seed_content, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if content:
                    Logger.info("📝 Using seed content for highlights section")
                    return content
        
        return None
    
    def _extract_seed_whats_next(self) -> Optional[str]:
        """Extract what's next section from blog seed file"""
        if not self.blog_seed_content:
            return None
            
        # Look for future/roadmap section markers
        patterns = [
            r'## What\'?s Next\s*\n(.*?)(?=\n##|\Z)',
            r'# Future\s*\n(.*?)(?=\n#|\Z)',
            r'# Roadmap\s*\n(.*?)(?=\n#|\Z)',
            r'FUTURE\s*[:\n](.*?)(?=\n[A-Z]{2,}|\Z)',
            r'ROADMAP\s*[:\n](.*?)(?=\n[A-Z]{2,}|\Z)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.blog_seed_content, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if content:
                    Logger.info("📝 Using seed content for what's next section")
                    return content
        
        return None
    
    def _generate_synthesis_highlights(self) -> Optional[str]:
        """Generate highlights from AI synthesis data"""
        if not self.synthesis_data:
            return None
        
        themes_data = self.synthesis_data.get('themes', {})
        if not themes_data:
            return None
        
        highlights_sections = []
        
        for theme_name, theme_data in themes_data.items():
            synthesized_content = theme_data.get('synthesized_content')
            commit_count = theme_data.get('commit_count', 0)
            
            if commit_count == 0:
                continue
                
            if synthesized_content:
                # Parse the synthesized content to extract highlights
                highlights = self._extract_highlights_from_synthesis(synthesized_content)
                if highlights:
                    highlights_sections.append(f"### {theme_name}")
                    highlights_sections.extend(highlights[:3])  # Top 3 highlights per theme
            else:
                # Fallback to raw commit data
                raw_commits = theme_data.get('raw_commits', [])
                if raw_commits:
                    highlights_sections.append(f"### {theme_name}")
                    highlights_sections.extend([f"- {commit}" for commit in raw_commits[:3]])
        
        if highlights_sections:
            Logger.info("✨ Using AI synthesis data for Key Highlights")
            return '\n'.join(highlights_sections)
        
        return None
    
    def _extract_highlights_from_synthesis(self, synthesis_content: str) -> list:
        """Extract bullet points from synthesis content"""
        highlights = []
        lines = synthesis_content.split('\n')
        in_highlights = False
        
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith('HIGHLIGHTS:') or line_stripped.startswith('**HIGHLIGHTS:**'):
                in_highlights = True
                continue
            elif in_highlights and line_stripped.startswith('-'):
                highlights.append(line_stripped)
            elif in_highlights and not line_stripped:
                break  # End of highlights section
        
        return highlights
    
    def _generate_doc_based_highlights(self) -> Optional[str]:
        """Generate highlights using documentation-based feature extraction"""
        if not DocBasedFeatureExtractor_available:
            Logger.warn("DocBasedFeatureExtractor not available - check if doc-based-feature-extractor.py exists")
            return None
            
        try:
            # Determine since version for milestone vs patch releases
            since_version = self._determine_since_version()
            
            extractor = DocBasedFeatureExtractor()
            categorized_features = extractor.extract_features(self.version, since_version)
            
            if not categorized_features:
                Logger.warn("No features found using documentation-based extraction")
                return None
            
            highlights_sections = []
            
            # Limit to most important categories and top features to keep blog concise
            priority_categories = [
                "Model Support", "Model Context Protocol (MCP)", 
                "Vector Store Enhancements", "Chat Client Improvements",
                "API Enhancements"
            ]
            
            for category in priority_categories:
                features = categorized_features.get(category, [])
                if not features:
                    continue
                
                highlights_sections.append(f"### {category}")
                
                # Show top 3-5 most significant features per category
                for i, feature in enumerate(features[:5]):
                    # Clean up feature title and make it more blog-friendly
                    clean_title = self._clean_feature_title(feature.title)
                    highlights_sections.append(f"- **{clean_title}**: Enhanced capabilities and improved functionality")
                    
                    if i >= 4:  # Limit to 5 per category
                        break
            
            return "\n".join(highlights_sections) if highlights_sections else None
            
        except Exception as e:
            Logger.error(f"Error generating documentation-based highlights: {e}")
            return None
    
    def _clean_feature_title(self, title: str) -> str:
        """Clean up feature title for blog presentation"""
        # Remove technical prefixes and clean up title
        clean_title = re.sub(r'^(feat|fix|add|GH-\d+):\s*', '', title, flags=re.IGNORECASE)
        clean_title = re.sub(r'\s*\(#\d+\)\s*$', '', clean_title)
        clean_title = re.sub(r'^\w+\s*:\s*', '', clean_title)  # Remove prefixes like "feat:", "docs:"
        
        # Capitalize first letter
        if clean_title:
            clean_title = clean_title[0].upper() + clean_title[1:]
        
        return clean_title.strip()
    
    def _determine_since_version(self) -> str:
        """Determine since version based on release type with tag-date awareness"""
        # For milestone releases like 1.1.0-M1, baseline from latest patch in previous minor series
        if re.match(r'^\d+\.\d+\.\d+-M\d+$', self.version):
            parts = self.version.split('-')[0].split('.')
            major, minor = int(parts[0]), int(parts[1])
            
            # Find latest patch release in previous minor series (e.g., for 1.1.0-M1, find latest 1.0.x)
            prev_minor_base = f"{major}.{minor-1}" if minor > 0 else f"{major-1}.0" if major > 1 else "1.0"
            
            # Get latest patch release with tag-date awareness
            latest_patch = self._get_latest_patch_release(prev_minor_base)
            if latest_patch:
                Logger.info(f"Using baseline version: {latest_patch} (latest patch in {prev_minor_base}.x series)")
                return latest_patch
            else:
                # Fallback to .0 if no patches exist
                fallback = f"{prev_minor_base}.0"
                Logger.warn(f"No patches found in {prev_minor_base}.x series, using fallback: {fallback}")
                return fallback
        
        # For patch releases like 1.0.2, compare since previous patch
        if re.match(r'^\d+\.\d+\.\d+$', self.version):
            parts = self.version.split('.')
            prev_patch = max(0, int(parts[2]) - 1)
            return f"{parts[0]}.{parts[1]}.{prev_patch}"
            
        # Default fallback
        return "1.0.0"
    
    def _get_latest_patch_release(self, minor_series: str) -> Optional[str]:
        """Get the latest patch release in a minor series with tag-date awareness"""
        try:
            # Get current version's tag date for comparison (if it exists)
            current_tag_date = self._get_tag_date(self.version)
            
            # Get all tags matching the pattern (e.g., 1.0.*)
            result = subprocess.run([
                'git', 'tag', '-l', f'v{minor_series}.*'
            ], cwd=self.spring_ai_repo, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                Logger.debug(f"Git tag command failed: {result.stderr}")
                return None
            
            tags = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # Filter to only GA releases (no -M, -RC suffixes)
            ga_tags = []
            for tag in tags:
                clean_tag = tag.replace('v', '')
                if re.match(r'^\d+\.\d+\.\d+$', clean_tag):  # Only X.Y.Z format
                    ga_tags.append(clean_tag)
            
            if not ga_tags:
                return None
            
            # Sort by semantic version and get candidates
            ga_tags.sort(key=lambda t: [int(x) for x in t.split('.')])
            
            # If we have current tag date, filter by date
            if current_tag_date:
                valid_tags = []
                for tag in ga_tags:
                    tag_date = self._get_tag_date(tag)
                    if tag_date and tag_date <= current_tag_date:
                        valid_tags.append(tag)
                ga_tags = valid_tags
            
            # Return the latest valid tag
            return ga_tags[-1] if ga_tags else None
            
        except Exception as e:
            Logger.debug(f"Error getting latest patch release for {minor_series}: {e}")
            return None
    
    def _get_tag_date(self, version: str) -> Optional[str]:
        """Get the date of a git tag"""
        try:
            tag_name = version if version.startswith('v') else f'v{version}'
            
            result = subprocess.run([
                'git', 'log', '-1', '--format=%aI', tag_name
            ], cwd=self.spring_ai_repo, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                # Convert ISO format to simple date for comparison
                from datetime import datetime
                date = datetime.fromisoformat(result.stdout.strip().replace('Z', '+00:00'))
                return date.strftime('%Y-%m-%d')
            
        except Exception as e:
            Logger.debug(f"Could not get tag date for {version}: {e}")
        
        return None
    
    def _gather_release_data(self) -> Optional[ReleaseData]:
        """Gather data about the release from various sources"""
        Logger.info("📊 Gathering release data...")
        
        try:
            # Create release data object
            release_data = ReleaseData(
                version=self.version,
                publish_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            # Get GitHub release information
            github_url, commit_count = self._get_github_release_info()
            release_data.github_release_url = github_url
            release_data.total_commits = commit_count
            
            # Analyze commit types from RELEASE_NOTES.md
            commit_analysis = self._analyze_commits()
            release_data.bug_fixes = commit_analysis.get('bug_fixes', 0)
            release_data.new_features = commit_analysis.get('new_features', 0)
            release_data.documentation = commit_analysis.get('documentation', 0)
            release_data.dependency_upgrades = commit_analysis.get('dependency_upgrades', 0)
            release_data.other_improvements = commit_analysis.get('other_improvements', 0)
            
            # Get contributors if requested
            if self.config.get('include_contributors'):
                release_data.contributors = self._get_contributors()
            
            # Generate key highlights
            release_data.key_highlights = self._generate_key_highlights(release_data)
            
            # Determine previous version
            release_data.previous_version = self._get_previous_version()
            
            # Analyze ecosystem repositories if enabled
            if self.config.get('analyze_ecosystem', False):
                ecosystem_metrics = self._analyze_ecosystem_repositories(release_data.previous_version)
                if ecosystem_metrics:
                    release_data.ecosystem_metrics = ecosystem_metrics
                    release_data.ecosystem_contributors = ecosystem_metrics.total_contributors
                    release_data.ecosystem_examples = ecosystem_metrics.new_examples
                    release_data.ecosystem_blog_posts = ecosystem_metrics.blog_posts
                    release_data.ecosystem_tutorials = ecosystem_metrics.tutorials
                    release_data.mcp_features = ecosystem_metrics.mcp_features
                    release_data.ai_tests = ecosystem_metrics.ai_tests
            
            Logger.success(f"✅ Release data gathered: {commit_count} commits, {len(release_data.contributors)} contributors")
            if release_data.ecosystem_metrics:
                Logger.success(f"   🌟 Ecosystem: {release_data.ecosystem_contributors} contributors, {release_data.ecosystem_examples} examples")
            return release_data
            
        except Exception as e:
            Logger.error(f"Error gathering release data: {e}")
            return None
    
    def _analyze_ecosystem_repositories(self, since_version: str) -> Optional[Any]:
        """Analyze ecosystem repositories for community metrics"""
        if not EcosystemAnalyzer_available:
            Logger.warn("EcosystemAnalyzer not available - skipping ecosystem analysis")
            return None
        
        try:
            Logger.info("🌟 Analyzing Spring AI ecosystem repositories...")
            
            # Get the baseline date from the previous version tag
            baseline_date = self._get_tag_date(since_version)
            if not baseline_date:
                Logger.warn(f"Could not determine date for version {since_version}, skipping ecosystem analysis")
                return None
            
            Logger.info(f"Using baseline date: {baseline_date} (from {since_version} tag)")
            
            # Initialize analyzer with caching
            cache_dir = Path(self.config.get('ecosystem_cache_dir')) if self.config.get('ecosystem_cache_dir') else (self.script_dir / ".ecosystem_cache")
            analyzer = EcosystemAnalyzer(
                cache_dir=cache_dir,
                refresh_cache=self.config.get('refresh_ecosystem_cache', False)
            )
            
            # Analyze ecosystem since baseline date
            metrics = analyzer.analyze_since_date(baseline_date)
            
            Logger.success(f"✅ Ecosystem analysis complete")
            return metrics
            
        except Exception as e:
            Logger.error(f"Error analyzing ecosystem repositories: {e}")
            return None
    
    def _get_github_release_info(self) -> tuple[str, int]:
        """Get GitHub release URL and commit count"""
        try:
            # Check if release exists on GitHub
            result = subprocess.run([
                'gh', 'release', 'view', f'v{self.version}', 
                '--repo', 'spring-projects/spring-ai',
                '--json', 'url'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                release_info = json.loads(result.stdout)
                github_url = release_info['url']
            else:
                # Construct expected URL if release doesn't exist yet
                github_url = f"https://github.com/spring-projects/spring-ai/releases/tag/v{self.version}"
            
            # Get commit count (simplified - could integrate with release notes generator)
            commit_count = self._estimate_commit_count()
            
            return github_url, commit_count
            
        except Exception as e:
            Logger.warn(f"Could not get GitHub release info: {e}")
            return f"https://github.com/spring-projects/spring-ai/releases/tag/v{self.version}", 0
    
    def _estimate_commit_count(self) -> int:
        """Get total commit count using fresh git analysis"""
        if not BlogGitAnalyzer_available:
            Logger.warn("BlogGitAnalyzer not available, using default estimate")
            return 25
        
        try:
            since_version = self._determine_since_version()
            target_version = self.version if not self.version.endswith('-M1') else None  # Use HEAD for milestones
            
            analyzer = BlogGitAnalyzer(
                repo_path=str(self.spring_ai_repo),
                since_version=since_version,
                target_version=target_version
            )
            
            commits = analyzer.collect_commits()
            total_count = len(commits)
            
            Logger.info(f"Fresh git analysis found {total_count} total commits")
            return total_count
            
        except Exception as e:
            Logger.warn(f"Could not get fresh commit count: {e}, using default")
            return 25
    
    def _analyze_commits(self) -> Dict[str, int]:
        """Analyze commit types using direct git analysis"""
        if not BlogGitAnalyzer_available:
            Logger.warn("BlogGitAnalyzer not available, using defaults")
            return {
                'new_features': 8,
                'bug_fixes': 15,
                'documentation': 5,
                'dependency_upgrades': 2,
                'other_improvements': 10
            }
        
        try:
            Logger.info("🔍 Performing fresh git analysis for commit categorization")
            
            # Determine version range
            since_version = self._determine_since_version()
            target_version = self.version if not self.version.endswith('-M1') else None  # Use HEAD for milestones
            
            # Initialize analyzer
            analyzer = BlogGitAnalyzer(
                repo_path=str(self.spring_ai_repo),
                since_version=since_version,
                target_version=target_version
            )
            
            # Collect and analyze commits
            commits = analyzer.collect_commits()
            analysis = analyzer.analyze_commits(commits)
            
            Logger.info(f"✅ Fresh git analysis complete: {analysis.total_commits} commits analyzed")
            
            return {
                'new_features': analysis.new_features,
                'bug_fixes': analysis.bug_fixes,
                'documentation': analysis.documentation,
                'dependency_upgrades': analysis.dependency_upgrades,
                'other_improvements': analysis.other_improvements
            }
            
        except Exception as e:
            Logger.error(f"Fresh git analysis failed: {e}, using defaults")
            return {
                'new_features': 8,
                'bug_fixes': 15,
                'documentation': 5,
                'dependency_upgrades': 2,
                'other_improvements': 10
            }
    
    def _get_contributors(self) -> List[str]:
        """Get list of contributors using the proper contributor script"""
        try:
            Logger.info("🔍 Extracting contributors using get-contributors.py logic")
            
            # Use the existing get-contributors.py approach
            since_version = self._determine_since_version()
            
            # Run the contributor script to get proper GitHub username resolution
            result = subprocess.run([
                'python3', 'get-contributors.py', 
                '--since-version', since_version,
                '--dry-run'
            ], capture_output=True, text=True, cwd=self.script_dir)
            
            if result.returncode == 0:
                # Extract contributor count from output
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Collected' in line and 'unique contributors' in line:
                        import re
                        matches = re.findall(r'(\d+) unique contributors', line)
                        if matches:
                            contributor_count = int(matches[0])
                            Logger.info(f"✅ Found {contributor_count} contributors using proper GitHub resolution")
                            
                            # Extract ALL contributors with full GitHub username format for full section
                            contributors = []
                            for line in lines:
                                if line.strip().startswith('- [') and '(' in line and ')' in line:
                                    # Extract format: Name (username) from - [Name (username)](url)
                                    start = line.find('[') + 1
                                    end = line.find(']')
                                    if end > start:
                                        contributor_with_username = line[start:end].strip()
                                        contributors.append(contributor_with_username)
                            
                            # Return ALL contributors for full section - no limiting for blog post
                            return contributors
                
                Logger.warn("Could not parse contributor count from get-contributors.py output")
            else:
                Logger.warn(f"get-contributors.py failed: {result.stderr}")
            
            # Fallback to simple git analysis
            return self._get_contributors_fallback()
            
        except Exception as e:
            Logger.warn(f"Could not use get-contributors.py: {e}")
            return self._get_contributors_fallback()
    
    def _get_contributors_fallback(self) -> List[str]:
        """Fallback contributor extraction using simple git analysis"""
        if not BlogGitAnalyzer_available:
            return []
        
        try:
            since_version = self._determine_since_version()
            target_version = self.version if not self.version.endswith('-M1') else None  # Use HEAD for milestones
            
            analyzer = BlogGitAnalyzer(
                repo_path=str(self.spring_ai_repo),
                since_version=since_version,
                target_version=target_version
            )
            
            commits = analyzer.collect_commits()
            analysis = analyzer.analyze_commits(commits)
            
            return analysis.contributors[:10] if len(analysis.contributors) > 10 else analysis.contributors
            
        except Exception as e:
            Logger.debug(f"Fallback contributor extraction failed: {e}")
            return []
    
    def _generate_key_highlights(self, release_data: ReleaseData) -> List[str]:
        """Generate key highlights for the release"""
        highlights = []
        
        # Combine new features and other improvements for patch release messaging
        total_improvements = release_data.new_features + release_data.other_improvements
        
        # Add highlights based on commit analysis
        if total_improvements > 20:
            highlights.append(f"Significant functionality enhancements with {total_improvements} improvements")
        elif total_improvements > 10:
            highlights.append(f"Enhanced functionality with {total_improvements} improvements")
        
        if release_data.bug_fixes > 10:
            highlights.append(f"Major stability improvements with {release_data.bug_fixes} bug fixes")
        
        if release_data.documentation > 20:
            highlights.append(f"Comprehensive documentation updates with {release_data.documentation} improvements")
            
        if release_data.dependency_upgrades > 0:
            highlights.append(f"Updated dependencies for better security and performance")
        
        # Default highlight if none generated
        if not highlights:
            highlights.append("Improved stability and performance")
        
        return highlights
    
    def _get_previous_version(self) -> str:
        """Determine the previous version"""
        # Handle milestone, RC, and patch releases
        if '-M' in self.version or '-RC' in self.version:
            # For milestones/RCs, previous version is typically the base GA
            base_version = self.version.split('-')[0]
            version_parts = base_version.split('.')
            if len(version_parts) == 3:
                major, minor, patch = version_parts
                if int(patch) == 0:
                    # X.Y.0-M1 -> previous is typically (X.Y-1).0 or X.0.0
                    if int(minor) > 0:
                        return f"{major}.{int(minor)-1}.0"
                    else:
                        return f"{int(major)-1}.0.0" if int(major) > 0 else "1.0.0"
                else:
                    return f"{major}.{minor}.{int(patch)-1}"
            return "1.0.0"
        else:
            # Standard patch release logic
            version_parts = self.version.split('.')
            if len(version_parts) == 3:
                major, minor, patch = version_parts
                prev_patch = max(0, int(patch) - 1)
                return f"{major}.{minor}.{prev_patch}"
            return "1.0.0"  # Default fallback
    
    def _generate_blog_content(self, release_data: ReleaseData) -> Optional[str]:
        """Generate the blog post content following Spring AI patterns"""
        Logger.info("✍️ Generating blog post content...")
        
        try:
            # Generate each section
            frontmatter = self._generate_frontmatter(release_data)
            opening = self._generate_opening(release_data)
            release_summary = self._generate_release_summary(release_data)
            key_highlights = self._generate_highlights_section(release_data)
            functional_themes = self._generate_functional_themes_section(release_data)
            community = self._generate_community_section(release_data)
            whats_next = self._generate_whats_next(release_data)
            resources = self._generate_resources_section(release_data)
            
            # Add full contributors section if we have contributors
            full_contributors = self._generate_full_contributors_section(release_data)
            
            # Combine all sections (filter out empty ones)
            sections = [s for s in [
                frontmatter,
                opening,
                release_summary,
                key_highlights,
                functional_themes,
                community,
                whats_next,
                resources,
                full_contributors
            ] if s.strip()]
            
            blog_content = "\n".join(sections)
            
            return blog_content
            
        except Exception as e:
            Logger.error(f"Error generating blog content: {e}")
            return None
    
    def _generate_frontmatter(self, release_data: ReleaseData) -> str:
        """Generate YAML frontmatter"""
        return f'''---
title: "Spring AI {self.version} Available Now"
category: Releases
publishedAt: {release_data.publish_date}
author: markpollack
---'''
    
    def _generate_opening(self, release_data: ReleaseData) -> str:
        """Generate opening announcement section"""
        return f'''
On behalf of the Spring AI engineering team and everyone who has contributed, I'm happy to announce that Spring AI `{self.version}` has been released and is now available from Maven Central.

This patch release delivers important stability improvements and bug fixes.'''
    
    
    def _generate_release_summary(self, release_data: ReleaseData) -> str:
        """Generate release summary section"""
        total_changes = release_data.bug_fixes + release_data.new_features + release_data.documentation + release_data.dependency_upgrades + release_data.other_improvements
        
        # Combine new features with other improvements for patch release messaging
        total_improvements = release_data.new_features + release_data.other_improvements
        
        summary_bullets = []
        
        if total_improvements > 0:
            summary_bullets.append(f"- **Improvements**: {total_improvements} enhancements to expand capabilities and functionality")
        
        if release_data.bug_fixes > 0:
            summary_bullets.append(f"- **Stability**: {release_data.bug_fixes} bug fixes addressing community-reported issues")
        
        if release_data.documentation > 0:
            summary_bullets.append(f"- **Documentation**: {release_data.documentation} improvements to help developers")
        
        if release_data.dependency_upgrades > 0:
            summary_bullets.append(f"- **Security**: {release_data.dependency_upgrades} dependency upgrades for enhanced security")
        
        bullets_text = "\n".join(summary_bullets)
        
        return f'''
## Release Summary

This release includes [{total_changes} improvements, bug fixes, and documentation updates]({release_data.github_release_url}). The focus of this patch release is on:

{bullets_text}

Thanks to all those who have contributed with issue reports and pull requests.'''
    
    def _generate_highlights_section(self, release_data: ReleaseData) -> str:
        """Generate key highlights section"""
        
        # Check if user requested documentation-based features
        if hasattr(self, 'use_doc_based_features') and self.use_doc_based_features:
            doc_highlights = self._generate_doc_based_highlights()
            if doc_highlights:
                Logger.info("✨ Using documentation-based feature extraction for Key Highlights")
                return f'''
## Key Highlights

{doc_highlights}

These improvements ensure that Spring AI continues to provide a robust and reliable foundation for building production-ready AI applications.'''
        
        # Try to use synthesis data first (commit-based facts)
        synthesis_highlights = self._generate_synthesis_highlights()
        if synthesis_highlights:
            Logger.info("✨ Using AI synthesis data for Key Highlights")
            return f'''
## Key Highlights

{synthesis_highlights}

These improvements ensure that Spring AI continues to provide a robust and reliable foundation for building production-ready AI applications.'''
        
        # Fallback to seed content
        seed_highlights = self._extract_seed_highlights()
        if seed_highlights:
            return f'''
## Key Highlights

{seed_highlights}

These improvements ensure that Spring AI continues to provide a robust and reliable foundation for building production-ready AI applications.'''
        
        # Final fallback to generic highlights
        if not release_data.key_highlights:
            return ""
        
        highlights_text = "\n".join([f"- {highlight}" for highlight in release_data.key_highlights])
        
        return f'''
## Key Highlights

{highlights_text}

These improvements ensure that Spring AI continues to provide a robust and reliable foundation for building production-ready AI applications.'''
    
    
    def _generate_community_section(self, release_data: ReleaseData) -> str:
        """Generate community appreciation section"""
        contributor_text = ""
        if release_data.contributors:
            contributor_list = ", ".join(release_data.contributors[:10])  # Limit for readability
            if len(release_data.contributors) > 10:
                contributor_list += f" and {len(release_data.contributors) - 10} others"
            contributor_text = f" Special thanks to our contributors: {contributor_list}."
        
        return f'''
## Community

The Spring AI community continues to grow and contribute in meaningful ways. This release includes contributions from community members who reported issues, submitted fixes, and provided valuable feedback.{contributor_text}

Thanks to all those who have contributed with issue reports and pull requests.

### How can you help?

If you're interested in contributing, check out the ["ideal for contribution" tag](https://github.com/spring-projects/spring-ai/labels/ideal-for-contribution) in our issue repository. For general questions, please ask on [Stack Overflow](https://stackoverflow.com) using the [`spring-ai` tag](https://stackoverflow.com/tags/spring-ai).'''
    
    def _generate_functional_themes_section(self, release_data: ReleaseData) -> str:
        """Generate functional themes section from AI-analyzed release notes"""
        functional_themes = self._extract_functional_themes_from_release_notes()
        
        if not functional_themes:
            return ""
        
        sections = []
        sections.append("## Key Functional Areas Enhanced")
        sections.append("")
        sections.append("This release brings significant improvements across major functional areas of Spring AI:")
        sections.append("")
        
        for theme in functional_themes:
            sections.append(f"- {theme}")
        
        sections.append("")
        sections.append("These enhancements strengthen Spring AI's capabilities across the entire AI application development lifecycle.")
        
        return "\n".join(sections)
    
    def _extract_functional_themes_from_release_notes(self) -> List[str]:
        """Extract compelling functional themes using AI analysis of RELEASE_NOTES.md"""
        try:
            # Read the AI-generated release notes
            release_notes_path = self.script_dir / "RELEASE_NOTES.md"
            if not release_notes_path.exists():
                Logger.warn("RELEASE_NOTES.md not found - using basic themes")
                return self._get_fallback_themes()
            
            Logger.debug("🤖 Using AI-powered theme extraction from RELEASE_NOTES.md")
            
            # Use Claude Code CLI to extract compelling themes
            themes = self._extract_themes_with_ai_analysis(release_notes_path)
            
            if themes:
                return themes[:6]  # Limit to top 6 themes
            else:
                Logger.warn("AI theme extraction failed - using fallback")
                return self._get_fallback_themes()
            
        except Exception as e:
            Logger.debug(f"Error extracting themes from release notes: {e}")
            return self._get_fallback_themes()
    
    def _extract_themes_with_ai_analysis(self, release_notes_path: Path) -> List[str]:
        """Use Claude Code CLI via ClaudeCodeWrapper to extract compelling themes from release notes"""
        if not CLAUDE_WRAPPER_AVAILABLE:
            Logger.warn("ClaudeCodeWrapper not available - using fallback themes")
            return []
        
        try:
            # Create Claude Code wrapper with logs in current directory
            logs_dir = self.script_dir / "logs"
            claude = ClaudeCodeWrapper(logs_dir=logs_dir)
            
            # Read the release notes content to include in the prompt
            with open(release_notes_path, 'r', encoding='utf-8') as f:
                release_notes_content = f.read()
            
            # Create analysis prompt with the actual release notes content
            analysis_prompt = f"""Analyze the following Spring AI release notes and extract 5-6 compelling, specific functional themes for a blog post.

Requirements:
1. Each theme should be **bold** with a descriptive title
2. Follow with a dash and specific details about what changed
3. Focus on major functional areas, not generic improvements
4. Use compelling language that highlights significance
5. Be specific about technologies, models, and capabilities mentioned
6. Avoid generic phrases like "enhanced" or "improved" - be specific

Example format:
- **Model Context Protocol Revolution** - complete MCP integration with annotation-based configuration, enabling seamless tool execution across HTTP, stdio, and SSE protocols
- **Next-Generation AI Model Arsenal** - native support for GPT-5, Claude Opus-4, Google GenAI SDK, and ElevenLabs text-to-speech bringing cutting-edge capabilities directly to Spring Boot

Focus on functional areas like:
- Specific AI model integrations (name the models)
- Vector store and RAG capabilities (specific improvements)
- Tool calling and MCP protocol support (what's new)
- Multimodal capabilities (audio, image, PDF processing)
- Developer experience improvements (specific tooling)
- Chat and memory management (what's enhanced)

Return only the bullet points, no other text.

RELEASE NOTES TO ANALYZE:
{release_notes_content}"""

            Logger.debug("🤖 Running AI theme analysis using ClaudeCodeWrapper")
            
            # Create temporary prompt file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as prompt_file:
                prompt_file.write(analysis_prompt)
                prompt_file_path = prompt_file.name
            
            try:
                # Run analysis using the proper ClaudeCodeWrapper method
                result = claude.analyze_from_file(
                    prompt_file_path=prompt_file_path,
                    timeout=120,  # 2 minute timeout
                    model="sonnet"  # Cost-effective model
                )
            finally:
                # Clean up temporary file
                try:
                    os.unlink(prompt_file_path)
                except:
                    pass
            
            # Parse the ClaudeCodeWrapper response structure
            if result.get('success', False):
                # Extract the actual content from the complex response structure
                ai_response = None
                
                # Based on logs, the structure has a 'response' key with the actual content
                if 'response' in result and result['response']:
                    ai_response = result['response']
                
                # Fallback: try to get the content from the result key
                if not ai_response and 'result' in result and result['result']:
                    if isinstance(result['result'], str):
                        ai_response = result['result']
                    elif isinstance(result['result'], dict) and 'content' in result['result']:
                        ai_response = result['result']['content']
                
                # Fallback: check if there's an 'analysis' key (older format)  
                if not ai_response and 'analysis' in result:
                    ai_response = result['analysis']
                
                # Fallback: check if the entire result is the response
                if not ai_response and isinstance(result, str):
                    ai_response = result
                
                if ai_response:
                    ai_response = ai_response.strip()
                    Logger.debug(f"AI analysis response length: {len(ai_response)} chars")
                    
                    # Extract bullet points from AI response
                    themes = []
                    for line in ai_response.split('\n'):
                        line = line.strip()
                        if line.startswith('-') or line.startswith('•'):
                            # Clean up the bullet point
                            theme = line[1:].strip()  # Remove bullet
                            if theme and '**' in theme:  # Must have bold formatting
                                themes.append(theme)
                    
                    if themes:
                        Logger.success(f"AI extracted {len(themes)} compelling functional themes")
                        return themes
                    else:
                        Logger.warn("AI response didn't contain properly formatted themes")
                        Logger.debug(f"AI response sample: {ai_response[:200]}...")
                        return []
                else:
                    Logger.warn("Could not extract content from AI response")
                    Logger.debug(f"Response structure: {list(result.keys())}")
                    return []
            else:
                error_msg = result.get('error', 'Unknown error')
                Logger.warn(f"AI analysis failed: {error_msg}")
                return []
                
        except Exception as e:
            Logger.debug(f"Error in AI theme extraction: {e}")
            return []
    
    def _load_spring_ai_labels_mapping(self) -> Optional[List[Dict]]:
        """Load the Spring AI functional areas metadata for blog generation"""
        try:
            labels_file = self.script_dir / "spring-ai-functional-areas.json"
            if not labels_file.exists():
                Logger.debug("Spring AI functional areas file not found")
                return None
            
            with open(labels_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            Logger.debug(f"Error loading functional areas: {e}")
            return None
    
    def _analyze_content_with_label_metadata(self, content: str, labels_mapping: List[Dict]) -> List[str]:
        """Analyze release notes content using rich Spring AI label metadata"""
        content_lower = content.lower()
        theme_matches = {}
        
        # Group labels into major functional categories based on their metadata
        functional_categories = {
            'model_providers': {
                'theme_name': '**AI Model Provider Ecosystem**',
                'labels': ['anthropic', 'azure', 'bedrock', 'claude', 'deepseek', 'gemini', 'huggingface', 
                          'minimax', 'mistral', 'moonshot', 'ollama', 'openai', 'vertex', 'zhipu', 'gcp'],
                'description': 'enhanced integrations and new model support',
                'matches': []
            },
            'multimodal_ai': {
                'theme_name': '**Multimodal AI Capabilities**',
                'labels': ['audio', 'image models', 'multimodality', 'speech', 'transcription models'],
                'description': 'expanded audio, image, and cross-modal processing',
                'matches': []
            },
            'vector_rag': {
                'theme_name': '**Vector Stores & RAG Pipeline**',
                'labels': ['vector store', 'rag', 'embedding', 'cassandra', 'chromadb', 'milvus', 'neo4j', 
                          'pgvector', 'pinecone', 'qdrant', 'redis', 'weaviate', 'elastic search', 'opensearch'],
                'description': 'improved retrieval, storage, and metadata handling',
                'matches': []
            },
            'conversation_memory': {
                'theme_name': '**Conversational AI & Memory**',
                'labels': ['chat client', 'chat memory', 'chat options', 'advisors', 'messages'],
                'description': 'enhanced chat capabilities and memory management',
                'matches': []
            },
            'tool_integration': {
                'theme_name': '**Tool Integration & Function Calling**',
                'labels': ['tool/function calling', 'mcp', 'structured output'],
                'description': 'improved annotations, execution, and protocol support',
                'matches': []
            },
            'developer_experience': {
                'theme_name': '**Developer Experience & Configuration**',
                'labels': ['configuration', 'observability', 'testing', 'integration testing', 'documentation', 
                          'getting started experience', 'usability', 'AOT/Native'],
                'description': 'enhanced tooling, testing, and development workflow',
                'matches': []
            }
        }
        
        # Analyze content for each functional category
        for category, category_info in functional_categories.items():
            for label_name in category_info['labels']:
                # Find the label definition
                label_def = next((l for l in labels_mapping if l['label'].lower() == label_name.lower()), None)
                if not label_def:
                    continue
                
                # Check for matches using rich metadata
                matches = []
                
                # Check key classes mentioned in content
                for key_class in label_def.get('key_classes', []):
                    if key_class.lower() in content_lower:
                        matches.append(f"class:{key_class}")
                
                # Check relevant modules mentioned
                for module in label_def.get('relevant_modules', []):
                    if any(mod_part in content_lower for mod_part in module.lower().split('-')):
                        matches.append(f"module:{module}")
                
                # Check config keys mentioned
                for config_key in label_def.get('config_keys', []):
                    if config_key.lower() in content_lower:
                        matches.append(f"config:{config_key}")
                
                # Check developer touchpoints
                for touchpoint in label_def.get('developer_touchpoints', []):
                    if touchpoint.lower() in content_lower:
                        matches.append(f"touchpoint:{touchpoint}")
                
                # Simple label name check as fallback
                if label_name.lower().replace(' ', '') in content_lower.replace(' ', ''):
                    matches.append(f"label:{label_name}")
                
                if matches:
                    category_info['matches'].extend(matches)
        
        # Generate themes based on matches
        themes = []
        for category, category_info in functional_categories.items():
            if category_info['matches']:
                themes.append(f"{category_info['theme_name']} - {category_info['description']}")
        
        # If we don't have enough themes, add some based on generic analysis
        if len(themes) < 3:
            themes.extend(self._extract_themes_simple_approach(content))
        
        return list(set(themes))  # Remove duplicates
    
    def _extract_themes_simple_approach(self, content: str) -> List[str]:
        """Fallback to simple content analysis if labels mapping isn't available"""
        themes = []
        content_lower = content.lower()
        
        # Model Context Protocol
        if 'model context protocol' in content_lower or 'mcp' in content_lower:
            themes.append("**Model Context Protocol (MCP) Integration** - annotation-based configuration and tool execution")
        
        # Model providers
        providers = []
        if 'google genai' in content_lower: providers.append("Google GenAI")
        if 'gpt-5' in content_lower: providers.append("GPT-5")
        if 'claude opus-4' in content_lower or 'sonnet-4' in content_lower: providers.append("Claude models")
        if 'elevenlabs' in content_lower: providers.append("ElevenLabs")
        
        if providers:
            themes.append(f"**AI Model Provider Expansions** - new support for {', '.join(providers[:3])}")
        
        # Vector stores
        if 'vectorstore' in content_lower or 'vector store' in content_lower:
            themes.append("**Vector Store & Retrieval Enhancements** - improved metadata and interfaces")
        
        # Chat capabilities
        if 'chatclient' in content_lower or 'chat memory' in content_lower:
            themes.append("**Conversational AI Capabilities** - enhanced chat and memory management")
        
        # Tool calling
        if '@tool' in content_lower or 'tool call' in content_lower:
            themes.append("**Tool Integration & Function Calling** - improved annotations and execution")
        
        # Multimodal
        multimodal = []
        if 'audio transcription' in content_lower: multimodal.append("audio transcription")
        if 'text-to-speech' in content_lower: multimodal.append("text-to-speech")
        if 'pdf files' in content_lower: multimodal.append("PDF processing")
        
        if multimodal:
            themes.append(f"**Multimodal AI Capabilities** - expanded {', '.join(multimodal)}")
        
        return themes
    
    def _get_fallback_themes(self) -> List[str]:
        """Fallback themes when analysis fails"""
        return [
            "**AI Model Provider Integration** - enhanced support for multiple AI platforms",
            "**Developer Experience Improvements** - better APIs and configuration options", 
            "**Core Platform Stability** - bug fixes and performance optimizations"
        ]
    
    def _generate_full_contributors_section(self, release_data: ReleaseData) -> str:
        """Generate full contributors appreciation section with all contributors listed"""
        if not release_data.contributors:
            return ""
            
        # Format contributors with proper markdown links
        contributors_formatted = []
        for contributor in release_data.contributors:
            # Extract username from "Name (username)" format
            if '(' in contributor and ')' in contributor:
                # Format: Name (username) -> [Name (username)](https://github.com/username)
                start_paren = contributor.rfind('(')
                end_paren = contributor.rfind(')')
                if start_paren > 0 and end_paren > start_paren:
                    username = contributor[start_paren+1:end_paren]
                    github_link = f"[{contributor}](https://github.com/{username})"
                    contributors_formatted.append(github_link)
                else:
                    # Fallback for malformed entries
                    contributors_formatted.append(contributor)
            else:
                # Fallback for entries without username format
                contributors_formatted.append(contributor)
        
        contributors_text = "\n".join(contributors_formatted)
        
        return f'''
🙏 Contributors
Thanks to all contributors who made this release possible:

{contributors_text}
'''.strip()
    
    def _generate_whats_next(self, release_data: ReleaseData) -> str:
        """Generate what's next section"""
        # Check for seed content override
        seed_whats_next = self._extract_seed_whats_next()
        if seed_whats_next:
            return f'''
## Looking Ahead: Spring AI 1.1 and Beyond

{seed_whats_next}'''
        
        # Simple, clean what's next section
        return f'''
## What's Next

The Spring AI team continues to focus on improving AI application development with Spring Boot. Based on the momentum from {self.version}, upcoming releases will build on these foundations with enhanced capabilities and developer experience improvements.

For the latest updates and to contribute to the project, visit our [GitHub repository](https://github.com/spring-projects/spring-ai) or join the discussion in our community channels.'''
    
    def _generate_resources_section(self, release_data: ReleaseData) -> str:
        """Generate resources section"""
        return f'''
## Resources

[Project Page](https://spring.io/projects/spring-ai/) | [GitHub](https://github.com/spring-projects/spring-ai) | [Issues](https://github.com/spring-projects/spring-ai/issues) | [Documentation](https://docs.spring.io/spring-ai/docs/{self.version}/reference/html) | [Stack Overflow](https://stackoverflow.com/questions/tagged/spring-ai)'''
    
    def _write_blog_post(self, content: str) -> bool:
        """Write the blog post to file"""
        try:
            output_path = Path(self.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            Logger.success(f"✅ Blog post written to: {output_path}")
            Logger.info(f"📄 Content length: {len(content)} characters")
            
            # Show next steps
            Logger.bold("\n" + "=" * 60)
            Logger.bold("📝 BLOG POST GENERATION COMPLETE")
            Logger.bold("=" * 60)
            Logger.info(f"📍 File location: {output_path.absolute()}")
            Logger.info("\n🔍 Next steps:")
            Logger.info("   1. Review the generated content for accuracy")
            Logger.info("   2. Verify all links and version numbers")
            Logger.info("   3. Add any project-specific highlights")
            Logger.info("   4. Submit for review and publication")
            Logger.bold("=" * 60)
            
            return True
            
        except Exception as e:
            Logger.error(f"Error writing blog post: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(
        description="Generate Spring AI blog posts for patch releases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('version', 
                       help='Spring AI version (e.g., 1.0.1, 1.0.2)')
    parser.add_argument('--output-file',
                       help='Output file path (default: auto-generated)')
    parser.add_argument('--include-contributors',
                       action='store_true',
                       help='Include contributor analysis')
    parser.add_argument('--since-version',
                       help='Previous version for contributor analysis (default: auto-detect)')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Show generated content without writing file')
    parser.add_argument('--verbose',
                       action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--blog-seed-file',
                       help='Path to blog seed file containing themes and focus areas for the blog post')
    parser.add_argument('--synthesis-file',
                       help='Path to AI synthesis file with commit-based theme analysis')
    parser.add_argument('--use-doc-based-features',
                       action='store_true',
                       help='Use documentation-based feature extraction instead of AI synthesis')
    parser.add_argument('--analyze-ecosystem',
                       action='store_true',
                       help='Enable ecosystem repository analysis (spring-ai-examples, awesome-spring-ai)')
    parser.add_argument('--refresh-ecosystem-cache',
                       action='store_true',
                       help='Force refresh of cached ecosystem repositories')
    parser.add_argument('--ecosystem-cache-dir',
                       help='Custom directory for ecosystem repository cache')
    
    args = parser.parse_args()
    
    # Validate version format - support X.Y.Z, X.Y.Z-MN, X.Y.Z-RCN
    if not re.match(r'^\d+\.\d+\.\d+(-M\d+|-RC\d+)?$', args.version):
        Logger.error(f"Invalid version format: {args.version}. Expected X.Y.Z, X.Y.Z-MN, or X.Y.Z-RCN format.")
        sys.exit(1)
    
    # Enable debug logging if verbose
    if args.verbose:
        os.environ['DEBUG'] = '1'
    
    # Create configuration
    config = {
        'output_file': args.output_file,
        'include_contributors': args.include_contributors,
        'since_version': args.since_version,
        'dry_run': args.dry_run,
        'verbose': args.verbose,
        'blog_seed_file': args.blog_seed_file,
        'synthesis_file': args.synthesis_file,
        'use_doc_based_features': args.use_doc_based_features,
        'analyze_ecosystem': args.analyze_ecosystem,
        'refresh_ecosystem_cache': args.refresh_ecosystem_cache,
        'ecosystem_cache_dir': args.ecosystem_cache_dir
    }
    
    # Generate blog post
    generator = SpringAIBlogGenerator(args.version, config)
    success = generator.generate_blog_post()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Spring AI Blog Post Generator

Generates blog posts for Spring AI patch releases following established patterns
from markpollack's previous posts and Spring ecosystem conventions.

Usage:
    python3 generate-blog-post.py 1.0.1 --dry-run
    python3 generate-blog-post.py 1.0.2 --output-file my-blog-post.md
    python3 generate-blog-post.py 1.0.1 --include-contributors

Examples:
    # Generate blog post for 1.0.1 with dry run
    python3 generate-blog-post.py 1.0.1 --dry-run
    
    # Generate with contributor analysis
    python3 generate-blog-post.py 1.0.1 --include-contributors --since-version 1.0.0
    
    # Custom output location
    python3 generate-blog-post.py 1.0.1 --output-file /path/to/blog-post.md
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
        """Determine since version based on release type"""
        # For milestone releases like 1.1.0-M1, compare since last major (1.0.0)
        if re.match(r'^\d+\.\d+\.\d+-M\d+$', self.version):
            parts = self.version.split('-')[0].split('.')
            return f"{parts[0]}.0.0"
        
        # For patch releases like 1.0.2, compare since previous patch
        if re.match(r'^\d+\.\d+\.\d+$', self.version):
            parts = self.version.split('.')
            prev_patch = max(0, int(parts[2]) - 1)
            return f"{parts[0]}.{parts[1]}.{prev_patch}"
            
        # Default fallback
        return "1.0.0"
    
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
            
            Logger.success(f"✅ Release data gathered: {commit_count} commits, {len(release_data.contributors)} contributors")
            return release_data
            
        except Exception as e:
            Logger.error(f"Error gathering release data: {e}")
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
        """Get total commit count from RELEASE_NOTES.md"""
        try:
            release_notes_path = Path("RELEASE_NOTES.md")
            if not release_notes_path.exists():
                return 25  # Default estimate
            
            with open(release_notes_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract total from highlights line
            for line in content.split('\n'):
                if 'new features' in line and 'bug fixes' in line:
                    import re
                    numbers = re.findall(r'(\d+)', line)
                    if numbers:
                        # Sum all the numbers: new features + bug fixes + doc improvements + other improvements
                        total = sum(int(n) for n in numbers)
                        Logger.info(f"Extracted total changes from RELEASE_NOTES.md: {total}")
                        return total
            
            return 25  # Fallback
        except Exception as e:
            Logger.warn(f"Could not extract commit count: {e}")
            return 25
    
    def _analyze_commits(self) -> Dict[str, int]:
        """Analyze commit types from RELEASE_NOTES.md"""
        try:
            release_notes_path = Path("RELEASE_NOTES.md")
            if not release_notes_path.exists():
                Logger.warn("RELEASE_NOTES.md not found, using defaults")
                return {
                    'new_features': 8,
                    'bug_fixes': 15,
                    'documentation': 5,
                    'dependency_upgrades': 2
                }
            
            with open(release_notes_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract numbers from the highlights section
            bug_fixes = 0
            new_features = 0
            documentation = 0
            other_improvements = 0
            dependency_upgrades = 0
            
            # Look for the highlights line with numbers
            for line in content.split('\n'):
                if 'new features' in line and 'bug fixes' in line:
                    # Parse: "This release includes 24 new features, 50 bug fixes, 45 documentation improvements, 32 other improvements."
                    import re
                    numbers = re.findall(r'(\d+)\s+(\w+(?:\s+\w+)*)', line)
                    for count, desc in numbers:
                        count = int(count)
                        if 'new features' in desc:
                            new_features = count
                        elif 'bug fixes' in desc:
                            bug_fixes = count
                        elif 'documentation improvements' in desc:
                            documentation = count
                        elif 'other improvements' in desc:
                            other_improvements = count
                    break
            
            # Scan for dependency upgrades in the content
            dependency_section_found = False
            for line in content.split('\n'):
                if '## 🔄 Dependency Upgrades' in line or '## Dependency Upgrades' in line:
                    dependency_section_found = True
                elif dependency_section_found and line.startswith('##'):
                    break
                elif dependency_section_found and line.startswith('-'):
                    dependency_upgrades += 1
            
            Logger.info(f"Extracted: {new_features} new features, {bug_fixes} bug fixes, {documentation} documentation, {dependency_upgrades} dependency upgrades")
            
            return {
                'new_features': new_features,
                'bug_fixes': bug_fixes,
                'documentation': documentation,
                'dependency_upgrades': dependency_upgrades,
                'other_improvements': other_improvements
            }
            
        except Exception as e:
            Logger.warn(f"Could not parse RELEASE_NOTES.md: {e}, using defaults")
            return {
                'new_features': 8,
                'bug_fixes': 15,
                'documentation': 5,
                'dependency_upgrades': 2
            }
    
    def _get_contributors(self) -> List[str]:
        """Get list of contributors from RELEASE_NOTES.md"""
        try:
            release_notes_path = Path("RELEASE_NOTES.md")
            if not release_notes_path.exists():
                Logger.warn("RELEASE_NOTES.md not found, skipping contributor extraction")
                return []
            
            with open(release_notes_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract contributors from the Contributors section
            contributors = []
            lines = content.split('\n')
            in_contributors_section = False
            
            for line in lines:
                if "🙏 Contributors" in line and line.startswith('##'):
                    in_contributors_section = True
                    if self.config.get('verbose'): Logger.debug(f"Found contributors section: {line}")
                    continue
                elif in_contributors_section and (line.startswith('##') or line.startswith('#')):
                    # End of contributors section
                    if self.config.get('verbose'): Logger.debug(f"End of contributors section at: {line}")
                    break
                elif in_contributors_section and line.strip():
                    # Extract contributor name from various formats
                    if line.startswith('- ['):
                        # Format: - [Name (@username)](https://github.com/username)
                        # Extract name between [ and (@
                        try:
                            start_idx = line.find('[') + 1
                            end_idx = line.find(' (@')
                            if end_idx == -1:  # Fallback if no @ symbol
                                end_idx = line.find(']')
                            contributor = line[start_idx:end_idx].strip()
                            if contributor:
                                contributors.append(contributor)
                                if self.config.get('verbose'): Logger.debug(f"Added contributor: {contributor}")
                        except Exception as e:
                            if self.config.get('verbose'): Logger.debug(f"Error parsing contributor line: {line} - {e}")
                    elif line.startswith('- '):
                        # Format: - Name (username)
                        contributor = line[2:].split('(')[0].strip()
                        if contributor and '[' not in contributor:  # Skip markdown links
                            contributors.append(contributor)
                    elif line.startswith('*'):
                        # Format: * Name
                        contributor = line[1:].split('(')[0].strip()
                        if contributor:
                            contributors.append(contributor)
            
            Logger.info(f"Extracted {len(contributors)} contributors from RELEASE_NOTES.md")
            return contributors
            
        except Exception as e:
            Logger.warn(f"Could not extract contributors from RELEASE_NOTES.md: {e}")
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
            community = self._generate_community_section(release_data)
            whats_next = self._generate_whats_next(release_data)
            resources = self._generate_resources_section(release_data)
            
            # Combine all sections
            blog_content = "\n".join([
                frontmatter,
                opening,
                release_summary,
                key_highlights,
                community,
                whats_next,
                resources
            ])
            
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
        'use_doc_based_features': args.use_doc_based_features
    }
    
    # Generate blog post
    generator = SpringAIBlogGenerator(args.version, config)
    success = generator.generate_blog_post()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
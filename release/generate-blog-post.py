#!/usr/bin/env python3
"""
Spring AI Blog Post Generator

Generates blog posts for Spring AI point releases following established patterns
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
        
        # Combine new features and other improvements for point release messaging
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
        # Simple logic for point releases
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

This point release delivers important stability improvements and bug fixes.'''
    
    
    def _generate_release_summary(self, release_data: ReleaseData) -> str:
        """Generate release summary section"""
        total_changes = release_data.bug_fixes + release_data.new_features + release_data.documentation + release_data.dependency_upgrades + release_data.other_improvements
        
        # Combine new features with other improvements for point release messaging
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

This release includes [{total_changes} improvements, bug fixes, and documentation updates]({release_data.github_release_url}). The focus of this point release is on:

{bullets_text}

Thanks to all those who have contributed with issue reports and pull requests.'''
    
    def _generate_highlights_section(self, release_data: ReleaseData) -> str:
        """Generate key highlights section"""
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
        return f'''
## Looking Ahead: Spring AI 1.1 and Beyond

While version {self.version} focused on stability and bug fixes, the Spring AI team is working on new capabilities for version 1.1. However, with a rapidly evolving AI landscape and over 150 open pull requests to manage, we're being thoughtful about prioritization and would value community input on what matters most.

Our [2025 roadmap diagram](https://claude.ai/public/artifacts/e211dc9e-249d-425d-abd6-9425b8a2bf16) provides key dates and shows our planning focus on Spring AI 2.0 with new Spring Boot 4 foundations. The roadmap is primarily date-driven to help the community understand timing, while indicating the major architectural changes we're preparing for the next generation of Spring AI.

**Current Focus Areas for Spring AI 1.1:**

Our roadmap includes a broad range of potential feature areas. Rather than overpromise, we want to share the full "menu" of what we're considering so the community can help us prioritize:

**Core Infrastructure & Maintenance:**
- Spring Boot 4 support and compatibility
- CI/CD improvements (Google Vertex, Amazon testing gaps)
- Issue triage and community PR integration
- Kotlin null-safety improvements

**AI Model Provider Enhancements:**
- Chat vendor SDK updates (Azure OpenAI, Google Vertex migrations)
- Enhanced chat vendor features (prompt caching, message batching, "thinking" models)
- Non-chat API breadth (Responses API, Image API, Text-to-Speech, Realtime API)
- Native JSON mode and structured output improvements

**Advanced Capabilities:**
- Model Context Protocol (MCP) integration and streaming support
- Vector store improvements and hybrid search (beyond similarity search)
- Enterprise guardrails and security features
- Enhanced observability and monitoring
- Chat memory enhancements and MemGPT-style implementations

**Developer Experience:**
- Evaluators and testing frameworks for AI applications
- Agent frameworks and workflow helpers
- Multi-client configuration improvements
- API key rotation and supplier patterns

**Emerging Areas:**
- Agent-to-agent protocols and communication
- Commercial MCP proxy solutions
- GraphRAG and advanced retrieval patterns

**Community Guidance Needed:**

We can't tackle everything simultaneously, so community feedback on prioritization is invaluable. If any of these areas are critical to your use cases, please engage with us on [GitHub Issues](https://github.com/spring-projects/spring-ai/issues) or contribute pull requests.

The team is also investing in AI-powered tooling to help manage our growing backlog more efficiently, but your input remains essential for steering the project's direction.

Follow our progress on [GitHub](https://github.com/spring-projects/spring-ai) and join the conversation in our community channels.'''
    
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
        description="Generate Spring AI blog posts for point releases",
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
    
    args = parser.parse_args()
    
    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+$', args.version):
        Logger.error(f"Invalid version format: {args.version}. Expected X.Y.Z format.")
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
        'verbose': args.verbose
    }
    
    # Generate blog post
    generator = SpringAIBlogGenerator(args.version, config)
    success = generator.generate_blog_post()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
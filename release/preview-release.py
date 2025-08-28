#!/usr/bin/env python3
"""
Spring AI Release Preview Script

Quick preview of release notes and blog posts before making any commits or tags.
This script runs in read-only mode and doesn't modify any repositories.

Usage:
    python3 preview-release.py 1.1.0-M1 --since-version 1.0.0
    python3 preview-release.py 1.0.2 --since-version 1.0.1
    python3 preview-release.py 1.1.0-M1 --since-version 1.0.0 --blog-seed-file my-seed.txt
    python3 preview-release.py 1.1.0-M1 --since-version 1.0.0 --release-notes-only
    python3 preview-release.py 1.1.0-M1 --since-version 1.0.0 --blog-only

Examples:
    # Preview everything for milestone release (all commits since 1.0.0)
    python3 preview-release.py 1.1.0-M1 --since-version 1.0.0
    
    # Preview patch release (commits since previous patch)
    python3 preview-release.py 1.0.2 --since-version 1.0.1
    
    # Preview with blog seed file
    python3 preview-release.py 1.1.0-M1 --since-version 1.0.0 --blog-seed-file blog-seed-example.txt
    
    # Preview only release notes
    python3 preview-release.py 1.1.0-M1 --since-version 1.0.0 --release-notes-only
    
    # Preview only blog post
    python3 preview-release.py 1.1.0-M1 --since-version 1.0.0 --blog-only
"""

import os
import sys
import subprocess
import argparse
import re
import json
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

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

def get_release_type(version: str) -> str:
    """Determine release type from version string"""
    if '-M' in version:
        return 'milestone'
    elif '-RC' in version:
        return 'rc'
    elif version.count('.') == 2:
        parts = version.split('.')
        if len(parts) == 3 and parts[2] == '0':
            return 'minor'  # X.Y.0 is a minor release
        else:
            return 'patch'  # X.Y.Z where Z > 0
    return 'unknown'

def validate_since_version(version: str, since_version: str) -> bool:
    """Validate that since_version makes sense for the target version"""
    try:
        # Parse target version
        target_base = version.split('-')[0] if '-' in version else version
        target_parts = [int(x) for x in target_base.split('.')]
        
        # Parse since version  
        since_parts = [int(x) for x in since_version.split('.')]
        
        # Since version should be less than target version
        if since_parts >= target_parts:
            Logger.error(f"Since version {since_version} should be less than target version {target_base}")
            return False
            
        return True
        
    except (ValueError, IndexError):
        Logger.error(f"Invalid version format in since-version: {since_version}")
        return False

def get_cache_key(since_version: str) -> str:
    """Generate cache key for commits since version"""
    return hashlib.md5(f"commits_since_v{since_version}".encode()).hexdigest()[:8]

def get_cache_path(since_version: str) -> Path:
    """Get cache file path for commits"""
    cache_dir = Path(__file__).parent / '.cache'
    cache_dir.mkdir(exist_ok=True)
    cache_key = get_cache_key(since_version)
    return cache_dir / f"commits_{cache_key}.json"

def load_cached_commits(since_version: str) -> tuple[bool, list[dict]]:
    """Load commits from cache if available and fresh"""
    cache_path = get_cache_path(since_version)
    
    if not cache_path.exists():
        return False, []
    
    try:
        # Check cache age (expire after 1 hour)
        cache_age = datetime.now().timestamp() - cache_path.stat().st_mtime
        if cache_age > 3600:  # 1 hour
            Logger.debug("Cache expired, will refresh")
            return False, []
        
        with open(cache_path, 'r') as f:
            data = json.load(f)
            commits = data.get('commits', [])
            Logger.info(f"📦 Using cached commits ({len(commits)} commits)")
            return True, commits
            
    except Exception as e:
        Logger.debug(f"Cache load failed: {e}")
        return False, []

def save_cached_commits(since_version: str, commits: list[dict]) -> None:
    """Save commits to cache"""
    try:
        cache_path = get_cache_path(since_version)
        data = {
            'since_version': since_version,
            'cached_at': datetime.now().isoformat(),
            'commits': commits
        }
        
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        Logger.debug(f"Cached {len(commits)} commits")
        
    except Exception as e:
        Logger.debug(f"Cache save failed: {e}")

def get_commits_since_version(since_version: str) -> tuple[bool, list[dict]]:
    """Get raw commits since the specified version"""
    try:
        # Try cache first
        success, cached_commits = load_cached_commits(since_version)
        if success:
            return True, cached_commits
        
        Logger.info(f"📦 Fetching commits since v{since_version}...")
        
        # Get commits using git log with full message and file changes
        cmd = [
            'git', 'log', 
            f'v{since_version}..HEAD',
            '--pretty=format:%H|%an|%ae|%ad|%s|%b',
            '--date=short',
            '--no-merges',
            '--stat=120,120'  # Include file change statistics
        ]
        
        # Try to run from Spring AI repo if it exists
        spring_ai_repo = Path("/home/mark/projects/spring-ai")
        if spring_ai_repo.exists():
            result = subprocess.run(cmd, cwd=spring_ai_repo, capture_output=True, text=True, timeout=30)
        else:
            # Fallback to current directory
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            Logger.error(f"Git log failed: {result.stderr}")
            return False, []
        
        commits = []
        current_commit = None
        
        for line in result.stdout.strip().split('\n'):
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            # Check if this is a new commit line (has the pipe delimiters)
            if '|' in line and line.count('|') >= 5:
                # Save previous commit if exists
                if current_commit:
                    commits.append(current_commit)
                
                # Parse new commit
                parts = line.split('|', 5)  # Split into max 6 parts
                if len(parts) == 6:
                    current_commit = {
                        'hash': parts[0][:8],  # Short hash
                        'author': parts[1],
                        'email': parts[2], 
                        'date': parts[3],
                        'subject': parts[4],
                        'body': parts[5].strip(),
                        'files_changed': []
                    }
            elif current_commit and ('|' in line or line.endswith('(+)') or line.endswith('(-)')):
                # This is a file change line
                current_commit['files_changed'].append(line_stripped)
        
        # Don't forget the last commit
        if current_commit:
            commits.append(current_commit)
        
        Logger.success(f"✅ Found {len(commits)} commits since v{since_version}")
        
        # Cache the results
        save_cached_commits(since_version, commits)
        
        return True, commits
        
    except Exception as e:
        Logger.error(f"Failed to get commits: {e}")
        return False, []

def extract_themes_with_ai(seed_content: str) -> List[Dict[str, str]]:
    """Use AI to extract themes from seed content"""
    if not seed_content:
        return []
    
    Logger.info("🤖 Using AI to extract themes from seed content...")
    
    # Create prompt for theme extraction
    prompt = f"""
Please analyze this blog seed content and extract all the main themes or topics discussed.
For each theme, provide:
1. A concise theme name (2-6 words)
2. Key technical terms and aliases that relate to this theme
3. A brief description

Blog seed content:
```
{seed_content}
```

Please respond with a JSON array of themes in this format:
[
  {{
    "name": "Model Context Protocol Integration",
    "aliases": ["MCP", "model context protocol", "mcp server", "protocol integration"],
    "description": "Integration and enhancement of Model Context Protocol capabilities"
  }},
  {{
    "name": "Core AI Classes Enhancement", 
    "aliases": ["OpenAIApi", "AnthropicApi", "AzureOpenAI", "ChatModel", "core api"],
    "description": "Updates to fundamental AI model interfaces and implementations"
  }}
]
"""

    try:
        # Call Claude Code CLI with prompt via stdin
        cmd = [
            '/home/mark/.nvm/versions/node/v22.15.0/bin/claude', '--print', '--dangerously-skip-permissions'
        ]
        
        result = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Extract JSON from response
            output = result.stdout
            Logger.debug(f"AI response length: {len(output)} chars")
            # Find JSON array in the output
            import re
            json_match = re.search(r'\[[\s\S]*\]', output)
            if json_match:
                themes_json = json_match.group(0)
                themes = json.loads(themes_json)
                Logger.success(f"✅ AI extracted {len(themes)} themes from seed content")
                return themes
            else:
                Logger.warn("No JSON found in AI response, falling back to regex")
                Logger.debug(f"AI response: {output[:500]}...")
        else:
            Logger.warn(f"AI call failed (code {result.returncode}), falling back to regex")
            Logger.debug(f"Error: {result.stderr[:200]}")
                
    except subprocess.TimeoutExpired:
        Logger.warn("AI theme extraction timed out, falling back to regex")
    except Exception as e:
        Logger.warn(f"AI theme extraction failed: {e}, falling back to regex")

    # Fallback to regex-based extraction
    return extract_themes_with_regex(seed_content)

def extract_themes_with_regex(seed_content: str) -> List[Dict[str, str]]:
    """Fallback regex-based theme extraction"""
    themes = []
    
    # Look for bullet points or structured content
    for line in seed_content.split('\n'):
        line = line.strip()
        if line.startswith('- **') and line.endswith('**:'):
            # Extract theme from "- **Theme Name**:"
            theme_name = line[3:-3]  # Remove "- **" and "**:"
            # Create simple aliases for the theme
            aliases = [
                theme_name.lower(),
                theme_name.lower().replace(' ', ''),
                *theme_name.lower().split()
            ]
            # Add specific aliases for known themes
            if 'mcp' in theme_name.lower():
                aliases.extend(['mcp', 'model context protocol', 'model-context-protocol'])
            if 'vector' in theme_name.lower():
                aliases.extend(['vector', 'vectorstore', 'similarity'])
            if 'api' in theme_name.lower():
                aliases.extend(['api', 'openai', 'anthropic', 'azure'])
            if 'test' in theme_name.lower():
                aliases.extend(['test', 'testing', 'coverage'])
            
            themes.append({
                'name': theme_name,
                'aliases': list(set(aliases)),  # Remove duplicates
                'description': f"Theme extracted from: {line}"
            })
        elif line.startswith('- ') and ':' in line:
            # Extract theme from "- Theme: description"
            theme_name = line[2:].split(':')[0].strip()
            aliases = [theme_name.lower(), *theme_name.lower().split()]
            themes.append({
                'name': theme_name,
                'aliases': list(set(aliases)),
                'description': f"Theme extracted from: {line}"
            })
    
    return themes

def analyze_commits_for_seed_themes(commits: list[dict], seed_content: str) -> dict:
    """Use AI to analyze which commits relate to seed file themes"""
    if not seed_content or not commits:
        return {}
    
    Logger.info(f"🤖 Analyzing {len(commits)} commits for seed theme relevance...")
    
    # Extract themes using AI
    themes = extract_themes_with_ai(seed_content)
    
    if not themes:
        Logger.warn("No themes found in seed content")
        return {}
    
    theme_names = [theme['name'] for theme in themes]
    Logger.info(f"📋 Found {len(themes)} themes in seed file: {', '.join(theme_names)}")
    
    # Enhanced keyword-based matching using AI-extracted aliases
    theme_matches = {}
    for theme in themes:
        theme_name = theme['name']
        theme_matches[theme_name] = []
        
        # Use AI-provided aliases (which already includes theme name)
        search_terms = theme.get('aliases', [theme_name.lower()])
        
        Logger.debug(f"Theme '{theme_name}' search terms: {search_terms}")
        
        for commit in commits:
            subject_lower = commit['subject'].lower()
            
            # Check if any aliases appear in commit subject
            for alias in search_terms:
                alias_lower = alias.lower()
                # Enhanced matching: exact word boundaries and substring matching
                if (alias_lower in subject_lower or 
                    any(word.startswith(alias_lower) for word in subject_lower.split()) or
                    any(alias_lower in word for word in subject_lower.split())):
                    
                    theme_matches[theme_name].append({
                        'hash': commit['hash'],
                        'subject': commit['subject'],
                        'author': commit['author'],
                        'date': commit['date'],
                        'matched_term': alias
                    })
                    break  # Don't add the same commit multiple times for one theme
        
        Logger.debug(f"Theme '{theme_name}' found {len(theme_matches[theme_name])} matches")
    
    return theme_matches

def synthesize_theme_content_with_ai(theme_name: str, commits: List[Dict], theme_description: str = "") -> Optional[str]:
    """Use AI to synthesize commit details into user-friendly narrative"""
    if not commits:
        return None
    
    Logger.info(f"🤖 Synthesizing {len(commits)} commits for theme '{theme_name}'...")
    
    # Batch large commit sets to avoid timeouts
    max_commits_per_batch = 15
    if len(commits) > max_commits_per_batch:
        Logger.info(f"Batching {len(commits)} commits into groups of {max_commits_per_batch}")
        
        batch_results = []
        for i in range(0, len(commits), max_commits_per_batch):
            batch = commits[i:i + max_commits_per_batch]
            batch_result = synthesize_commit_batch(theme_name, batch, theme_description, i // max_commits_per_batch + 1)
            if batch_result and "Execution error" not in batch_result:
                batch_results.append(batch_result)
        
        # Combine batch results
        if batch_results:
            return combine_batch_results(theme_name, batch_results)
        else:
            return None
    
    # Single batch processing
    return synthesize_commit_batch(theme_name, commits, theme_description)

def synthesize_commit_batch(theme_name: str, commits: List[Dict], theme_description: str = "", batch_num: int = None) -> Optional[str]:
    """Synthesize a single batch of commits"""
    # Prepare commit details for AI
    commit_details = []
    for commit in commits:
        # Limit file changes to avoid token bloat
        files_summary = f" (files: {', '.join(commit.get('files_changed', [])[:2])})" if commit.get('files_changed') else ""
        commit_details.append(
            f"- {commit['subject']}\n"
            f"  Author: {commit['author']}, Hash: {commit['hash']}{files_summary}"
        )
        # Limit body to prevent token overflow
        if commit.get('body') and len(commit['body']) > 50:
            commit_details.append(f"  Details: {commit['body'][:150]}...")
    
    commits_text = '\n'.join(commit_details)
    
    batch_suffix = f" (batch {batch_num})" if batch_num else ""
    
    prompt = f"""
Please analyze these commits for the theme "{theme_name}" and create a concise, user-friendly summary of the actual improvements made.

Theme Context: {theme_description}

Commits ({len(commits)} total){batch_suffix}:
```
{commits_text}
```

Please provide:
1. A brief paragraph summarizing the key improvements
2. 3-5 specific bullet points highlighting the most important changes
3. Focus on user benefits and technical improvements, not internal refactoring

Format your response as:
SUMMARY: [paragraph]
HIGHLIGHTS:
- [specific improvement 1]
- [specific improvement 2]
- [etc.]
"""

    try:
        # Call Claude Code CLI with more generous timeout and retries
        timeout = 60 if batch_num else 90
        cmd = ['/home/mark/.nvm/versions/node/v22.15.0/bin/claude', '--print', '--dangerously-skip-permissions']
        
        # Try the AI call with retry logic
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                result = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout)
                break
            except subprocess.TimeoutExpired as e:
                if attempt == max_retries:
                    raise e
                Logger.warn(f"AI call timed out for '{theme_name}', retrying (attempt {attempt + 1}/{max_retries + 1})")
                timeout = min(timeout + 15, 120)  # Increase timeout for retry
        
        if result.returncode == 0:
            response = result.stdout.strip()
            batch_info = f" batch {batch_num}" if batch_num else ""
            
            # Check for execution errors in the response
            if "Execution error" in response:
                Logger.warn(f"AI returned execution error for '{theme_name}'{batch_suffix}")
                Logger.debug(f"Response with error: {response[:300]}")
                # Return None to trigger fallback
                return None
            
            Logger.success(f"✅ AI synthesized{batch_info} content for '{theme_name}'")
            return response
        else:
            Logger.warn(f"AI synthesis failed for '{theme_name}'{batch_suffix} (code {result.returncode})")
            Logger.debug(f"Error: {result.stderr[:200]}")
            
    except subprocess.TimeoutExpired:
        Logger.warn(f"AI synthesis timed out for '{theme_name}'{batch_suffix}")
    except Exception as e:
        Logger.warn(f"AI synthesis error for '{theme_name}'{batch_suffix}: {e}")
    
    # Fallback to simple summary
    return f"SUMMARY: {len(commits)} improvements made to {theme_name.lower()}\nHIGHLIGHTS:\n" + \
           '\n'.join([f"- {commit['subject']}" for commit in commits[:5]])

def combine_batch_results(theme_name: str, batch_results: List[str]) -> str:
    """Combine multiple batch results into a cohesive summary"""
    Logger.info(f"🔄 Combining {len(batch_results)} batch results for '{theme_name}'")
    
    # Extract summaries and highlights from each batch
    all_highlights = []
    all_summaries = []
    
    for i, result in enumerate(batch_results):
        Logger.debug(f"Processing batch {i+1} result: {result[:200]}...")
        
        lines = result.split('\n')
        summary_line = None
        in_highlights = False
        
        for line in lines:
            line_stripped = line.strip()
            # Handle both SUMMARY: and **SUMMARY:** formats
            if (line_stripped.startswith('SUMMARY:') or 
                line_stripped.startswith('**SUMMARY:**')):
                if line_stripped.startswith('**SUMMARY:**'):
                    summary_line = line_stripped[12:].strip()  # Remove **SUMMARY:**
                else:
                    summary_line = line_stripped[8:].strip()   # Remove SUMMARY:
                if summary_line:  # Only add non-empty summaries
                    all_summaries.append(summary_line)
                    Logger.debug(f"Found summary: {summary_line[:100]}...")
            # Handle both HIGHLIGHTS: and **HIGHLIGHTS:** formats
            elif (line_stripped.startswith('HIGHLIGHTS:') or 
                  line_stripped.startswith('**HIGHLIGHTS:**')):
                in_highlights = True
                Logger.debug("Found HIGHLIGHTS section")
            elif in_highlights and line_stripped.startswith('-'):
                all_highlights.append(line_stripped)
                Logger.debug(f"Found highlight: {line_stripped[:100]}...")
            elif in_highlights and line_stripped.startswith('•'):
                # Handle bullet points that might use • instead of -
                all_highlights.append(f"- {line_stripped[1:].strip()}")
                Logger.debug(f"Found bullet highlight: {line_stripped[:100]}...")
    
    Logger.debug(f"Found {len(all_summaries)} summaries and {len(all_highlights)} highlights")
    
    # Create combined result
    if all_summaries:
        # Combine the first 2 summaries intelligently
        combined_summary = all_summaries[0]
        if len(all_summaries) > 1:
            # Add additional context from second summary
            second_summary = all_summaries[1]
            if not combined_summary.endswith('.'):
                combined_summary += '.'
            combined_summary += f" {second_summary}"
    else:
        combined_summary = f"This release includes {len(batch_results)} major improvement areas for {theme_name.lower()}."
    
    # Take top highlights (max 6)
    top_highlights = all_highlights[:6]
    
    if not top_highlights:
        Logger.warn(f"No highlights found for {theme_name} - using fallback")
        return f"SUMMARY: {combined_summary}\nHIGHLIGHTS:\n- Multiple improvements made across {len(batch_results)} batches"
    
    return f"SUMMARY: {combined_summary}\nHIGHLIGHTS:\n" + '\n'.join(top_highlights)

def preview_commit_analysis(version: str, since_version: str, seed_content: str = None) -> bool:
    """Preview commits and their mapping to seed themes"""
    Logger.bold("🔍 COMMIT THEME ANALYSIS")
    Logger.bold("=" * 50)
    
    success, commits = get_commits_since_version(since_version)
    if not success:
        return False
    
    if not commits:
        Logger.warn("No commits found in the specified range")
        return True
    
    Logger.info(f"📊 Found {len(commits)} total commits since v{since_version}")
    
    synthesis_data = {}  # Store synthesis results for blog generator
    
    if seed_content:
        # Extract themes first to get descriptions
        themes = extract_themes_with_ai(seed_content)
        
        # Analyze commits for seed themes
        theme_matches = analyze_commits_for_seed_themes(commits, seed_content)
        
        if theme_matches:
            print("\n🎯 **SEED THEME ANALYSIS WITH AI SYNTHESIS**:")
            print("=" * 60)
            
            for theme, matches in theme_matches.items():
                if matches:
                    print(f"\n📌 **{theme}** ({len(matches)} related commits):")
                    
                    # Get theme description from original themes data
                    theme_description = ""
                    for original_theme in themes:
                        if original_theme['name'] == theme:
                            theme_description = original_theme.get('description', '')
                            break
                    
                    # Use AI to synthesize the commits into user-friendly content
                    synthesized = synthesize_theme_content_with_ai(theme, matches, theme_description)
                    if synthesized:
                        print(f"\n{synthesized}")
                        # Store synthesis for blog generator
                        synthesis_data[theme] = {
                            'commit_count': len(matches),
                            'synthesized_content': synthesized,
                            'description': theme_description
                        }
                    else:
                        # Fallback to showing raw commits
                        for match in matches[:5]:
                            matched_term = match.get('matched_term', 'unknown')
                            print(f"   • {match['hash']} {match['subject']} ({match['author']}) [matched: {matched_term}]")
                        if len(matches) > 5:
                            print(f"   ... and {len(matches) - 5} more commits")
                        # Store fallback data
                        synthesis_data[theme] = {
                            'commit_count': len(matches),
                            'synthesized_content': None,
                            'raw_commits': [f"{match['hash']} {match['subject']}" for match in matches[:5]]
                        }
                else:
                    print(f"\n📌 **{theme}**: No directly related commits found")
                    synthesis_data[theme] = {
                        'commit_count': 0,
                        'synthesized_content': None
                    }
        else:
            print("\n⚠️  No theme analysis available - check seed file format")
    else:
        print("\n📝 No seed file provided - skipping theme analysis")
    
    print("\n" + "=" * 60)
    Logger.success("✅ Commit analysis completed")
    
    # Save synthesis data for blog generator
    if synthesis_data:
        save_synthesis_for_blog_generator(synthesis_data, version, since_version)
    
    return True

def save_synthesis_for_blog_generator(synthesis_data: dict, version: str, since_version: str):
    """Save synthesis data to file for blog generator to use"""
    try:
        synthesis_file = Path(__file__).parent / f".synthesis-{version}.json"
        
        # Create complete synthesis package
        synthesis_package = {
            'version': version,
            'since_version': since_version,
            'generated_at': datetime.now().isoformat(),
            'themes': synthesis_data
        }
        
        with open(synthesis_file, 'w', encoding='utf-8') as f:
            json.dump(synthesis_package, f, indent=2, ensure_ascii=False)
        
        Logger.info(f"💾 Saved synthesis data to {synthesis_file}")
        
    except Exception as e:
        Logger.warn(f"Failed to save synthesis data: {e}")

def preview_release_notes(version: str, since_version: str) -> bool:
    """Preview release notes generation"""
    Logger.bold("📋 RELEASE NOTES PREVIEW")
    Logger.bold("=" * 50)
    Logger.info(f"Version: {version}")
    Logger.info(f"Since Version: {since_version}")
    Logger.info(f"Release Type: {get_release_type(version)}")
    Logger.bold("=" * 50)
    
    # Build command for release notes generator
    cmd = [
        'python3', 'generate-release-notes.py',
        '--target-version', version,
        '--since-version', since_version,
        '--dry-run'
    ]
    
    try:
        Logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=Path(__file__).parent, 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(result.stdout)
            Logger.success("✅ Release notes preview completed successfully")
            return True
        else:
            Logger.error("❌ Release notes preview failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        Logger.error("❌ Release notes generation timed out")
        return False
    except FileNotFoundError:
        Logger.error("❌ generate-release-notes.py not found")
        Logger.info("Make sure you're running this from the release directory")
        return False
    except Exception as e:
        Logger.error(f"❌ Error running release notes preview: {e}")
        return False

def preview_blog_post(version: str, blog_seed_file: Optional[str] = None) -> bool:
    """Preview blog post generation"""
    Logger.bold("📝 BLOG POST PREVIEW")
    Logger.bold("=" * 50)
    Logger.info(f"Version: {version}")
    Logger.info(f"Release Type: {get_release_type(version)}")
    if blog_seed_file:
        Logger.info(f"Blog Seed File: {blog_seed_file}")
    Logger.bold("=" * 50)
    
    # Build command for blog generator
    cmd = [
        'python3', 'generate-blog-post.py',
        version,
        '--dry-run'
    ]
    
    # Add synthesis file if available
    synthesis_file = Path(__file__).parent / f".synthesis-{version}.json"
    if synthesis_file.exists():
        cmd.extend(['--synthesis-file', str(synthesis_file)])
    
    if blog_seed_file:
        cmd.extend(['--blog-seed-file', blog_seed_file])
    
    try:
        Logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=Path(__file__).parent, 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(result.stdout)
            Logger.success("✅ Blog post preview completed successfully")
            return True
        else:
            Logger.error("❌ Blog post preview failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        Logger.error("❌ Blog post generation timed out")
        return False
    except FileNotFoundError:
        Logger.error("❌ generate-blog-post.py not found")
        Logger.info("Make sure you're running this from the release directory")
        return False
    except Exception as e:
        Logger.error(f"❌ Error running blog post preview: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Preview Spring AI release notes and blog posts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('version', 
                       help='Spring AI version (e.g., 1.0.1, 1.1.0-M1, 1.1.0-RC1)')
    parser.add_argument('--since-version',
                       required=True,
                       help='Previous version for changelog (e.g., 1.0.0, 1.0.1)')
    parser.add_argument('--blog-seed-file',
                       help='Path to blog seed file for focused blog generation')
    parser.add_argument('--release-notes-only',
                       action='store_true',
                       help='Preview only release notes')
    parser.add_argument('--blog-only',
                       action='store_true',
                       help='Preview only blog post')
    parser.add_argument('--clear-cache',
                       action='store_true',
                       help='Clear commit cache before running')
    parser.add_argument('--verbose',
                       action='store_true',
                       help='Enable verbose debug output')
    
    args = parser.parse_args()
    
    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+(-M\d+|-RC\d+)?$', args.version):
        Logger.error(f"Invalid version format: {args.version}. Expected X.Y.Z, X.Y.Z-MN, or X.Y.Z-RCN format.")
        sys.exit(1)
    
    # Validate blog seed file if provided
    if args.blog_seed_file and not Path(args.blog_seed_file).exists():
        Logger.error(f"Blog seed file not found: {args.blog_seed_file}")
        sys.exit(1)
    
    # Enable debug logging if verbose
    if args.verbose:
        import os
        os.environ['DEBUG'] = '1'
    
    # Clear cache if requested
    if args.clear_cache:
        cache_dir = Path(__file__).parent / '.cache'
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
            Logger.info("🧹 Cache cleared")
    
    # Validate since version
    if not validate_since_version(args.version, args.since_version):
        sys.exit(1)
    
    Logger.bold("🚀 SPRING AI RELEASE PREVIEW")
    Logger.bold("=" * 60)
    Logger.info(f"Target Version: {args.version}")
    Logger.info(f"Release Type: {get_release_type(args.version)}")
    Logger.info(f"Since Version: {args.since_version}")
    if args.blog_seed_file:
        Logger.info(f"Blog Seed File: {args.blog_seed_file}")
    Logger.info(f"Preview Mode: {'Release Notes Only' if args.release_notes_only else 'Blog Only' if args.blog_only else 'Both'}")
    Logger.bold("=" * 60)
    
    success = True
    
    # First, do commit analysis if we have a seed file
    seed_content = None
    if args.blog_seed_file:
        try:
            with open(args.blog_seed_file, 'r', encoding='utf-8') as f:
                seed_content = f.read().strip()
        except Exception as e:
            Logger.error(f"Failed to read seed file: {e}")
    
    if seed_content and not args.release_notes_only:
        Logger.info("\\n" + "=" * 60)
        if not preview_commit_analysis(args.version, args.since_version, seed_content):
            success = False
    
    # Preview release notes unless blog-only
    if not args.blog_only:
        Logger.info("\\n" + "=" * 60)
        if not preview_release_notes(args.version, args.since_version):
            success = False
    
    # Preview blog post unless release-notes-only  
    if not args.release_notes_only:
        Logger.info("\\n" + "=" * 60)
        if not preview_blog_post(args.version, args.blog_seed_file):
            success = False
    
    Logger.info("\\n" + "=" * 60)
    if success:
        Logger.success("🎉 All previews completed successfully!")
        Logger.info("\\n📋 Quick Commands for Your Reference:")
        Logger.info(f"   Release Notes: python3 generate-release-notes.py --target-version {args.version} --since-version {args.since_version}")
        Logger.info(f"   Blog Post: python3 generate-blog-post.py {args.version}" + 
                   (f" --blog-seed-file {args.blog_seed_file}" if args.blog_seed_file else ""))
        Logger.info("\\n🏃‍♂️ Ready to proceed with actual release when satisfied with previews!")
    else:
        Logger.error("❌ Some previews failed - check output above")
        sys.exit(1)

if __name__ == '__main__':
    main()
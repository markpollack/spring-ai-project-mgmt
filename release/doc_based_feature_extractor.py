#!/usr/bin/env python3
"""
Documentation-Based Feature Extractor for Spring AI
====================================================

Alternative approach to AI synthesis - analyzes documentation changes and 
feature commits to identify new capabilities for release blog posts.

This script complements the AI-based approach by focusing on:
1. Explicit feature commits (feat: prefix)
2. Documentation file changes that indicate new features
3. Major API additions and enhancements

Usage:
    python3 doc-based-feature-extractor.py 1.1.0-M1 --since-version 1.0.0
"""

import os
import sys
import subprocess
import argparse
import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Feature:
    title: str
    description: str
    commit_hash: str
    commit_message: str
    doc_files: List[str] = None

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
    def bold(msg): print(f"\033[1m{msg}\033[0m")

class DocBasedFeatureExtractor:
    def __init__(self, spring_ai_path: str = "/home/mark/projects/spring-ai"):
        self.spring_ai_path = Path(spring_ai_path)
        
    def extract_features(self, target_version: str, since_version: str) -> Dict[str, List[Feature]]:
        """Extract features by analyzing commits and documentation changes"""
        Logger.info(f"🔍 Extracting features from {since_version} to {target_version}")
        
        # Get all feature commits
        feature_commits = self._get_feature_commits(since_version)
        Logger.info(f"📋 Found {len(feature_commits)} explicit feature commits")
        
        # Get major documentation changes
        doc_changes = self._get_major_doc_changes(since_version)
        Logger.info(f"📚 Found {len(doc_changes)} major documentation changes")
        
        # Organize features by category
        categorized_features = self._categorize_features(feature_commits, doc_changes)
        
        return categorized_features
    
    def _get_feature_commits(self, since_version: str) -> List[Dict]:
        """Get commits with 'feat:' prefix"""
        try:
            cmd = [
                'git', 'log', f'v{since_version}..HEAD', 
                '--oneline', '--grep=feat:', '--grep=add', '--grep=Add'
            ]
            
            result = subprocess.run(
                cmd, cwd=self.spring_ai_path, 
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                Logger.warn(f"Git log failed: {result.stderr}")
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.strip().split(' ', 1)
                    if len(parts) == 2:
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1]
                        })
            
            return commits
            
        except Exception as e:
            Logger.error(f"Error getting feature commits: {e}")
            return []
    
    def _get_major_doc_changes(self, since_version: str) -> List[Dict]:
        """Get documentation files with significant changes"""
        try:
            # Get changed doc files with line counts
            cmd = [
                'git', 'diff', f'v{since_version}..HEAD', '--stat',
                '--', '*.adoc', '*.md'
            ]
            
            result = subprocess.run(
                cmd, cwd=self.spring_ai_path,
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                return []
            
            doc_changes = []
            for line in result.stdout.strip().split('\n'):
                if line.strip() and ('|' in line):
                    # Parse git diff --stat format
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        file_path = parts[0].strip()
                        changes = parts[1].strip().split()[0]
                        
                        # Only include significant changes (>10 lines)
                        try:
                            change_count = int(changes)
                            if change_count > 10:
                                doc_changes.append({
                                    'file': file_path,
                                    'changes': change_count
                                })
                        except (ValueError, IndexError):
                            continue
            
            return doc_changes
            
        except Exception as e:
            Logger.error(f"Error getting doc changes: {e}")
            return []
    
    def _categorize_features(self, feature_commits: List[Dict], doc_changes: List[Dict]) -> Dict[str, List[Feature]]:
        """Categorize features by theme"""
        
        categories = {
            "Model Support": [],
            "Model Context Protocol (MCP)": [],
            "Vector Store Enhancements": [],
            "Chat Client Improvements": [],
            "API Enhancements": [],
            "Developer Experience": [],
            "Other Features": []
        }
        
        # Analyze feature commits
        for commit in feature_commits:
            feature = self._analyze_commit_for_feature(commit)
            if feature:
                category = self._determine_category(feature)
                categories[category].append(feature)
        
        # Filter out empty categories
        return {k: v for k, v in categories.items() if v}
    
    def _analyze_commit_for_feature(self, commit: Dict) -> Optional[Feature]:
        """Convert commit to Feature object"""
        message = commit['message']
        
        # Skip CI/build related commits
        if any(skip in message.lower() for skip in ['ci:', 'build:', 'chore:', 'test:']):
            return None
        
        # Extract meaningful title and description
        title = self._extract_feature_title(message)
        description = self._extract_feature_description(message, commit['hash'])
        
        if title and description:
            return Feature(
                title=title,
                description=description,
                commit_hash=commit['hash'],
                commit_message=message
            )
        
        return None
    
    def _extract_feature_title(self, message: str) -> str:
        """Extract a clean title from commit message"""
        # Remove feat: prefix and PR numbers
        title = re.sub(r'^feat:\s*', '', message, flags=re.IGNORECASE)
        title = re.sub(r'\s*\(#\d+\)\s*$', '', title)
        title = re.sub(r'\s*#\d+\s*$', '', title)
        
        return title.strip()
    
    def _extract_feature_description(self, message: str, commit_hash: str) -> str:
        """Generate description from commit message"""
        # For now, use the commit message as description
        # Could be enhanced to look at commit body or related docs
        return f"Added in commit {commit_hash[:8]}: {message}"
    
    def _determine_category(self, feature: Feature) -> str:
        """Determine which category a feature belongs to"""
        message_lower = feature.commit_message.lower()
        
        if any(term in message_lower for term in ['gpt-5', 'model', 'anthropic', 'openai', 'azure']):
            return "Model Support"
        elif any(term in message_lower for term in ['mcp', 'context protocol']):
            return "Model Context Protocol (MCP)"
        elif any(term in message_lower for term in ['vector', 'embedding', 'similarity']):
            return "Vector Store Enhancements"  
        elif any(term in message_lower for term in ['chatclient', 'chat client']):
            return "Chat Client Improvements"
        elif any(term in message_lower for term in ['api', 'endpoint', 'configuration']):
            return "API Enhancements"
        elif any(term in message_lower for term in ['debug', 'workflow', 'ci', 'build']):
            return "Developer Experience"
        else:
            return "Other Features"
    
    def generate_highlights(self, categorized_features: Dict[str, List[Feature]]) -> str:
        """Generate markdown highlights from categorized features"""
        
        if not categorized_features:
            return "## Key Highlights\n\nNo major new features identified through documentation analysis."
        
        highlights = ["## Key Highlights", ""]
        
        for category, features in categorized_features.items():
            if not features:
                continue
                
            highlights.append(f"### {category}")
            highlights.append("")
            
            for feature in features:
                highlights.append(f"- **{feature.title}**: {feature.description}")
            
            highlights.append("")
        
        return "\n".join(highlights)

def main():
    parser = argparse.ArgumentParser(description="Extract features from Spring AI documentation and commits")
    parser.add_argument('version', help='Target version (e.g., 1.1.0-M1)')
    parser.add_argument('--since-version', required=True, help='Since version (e.g., 1.0.0)')
    parser.add_argument('--spring-ai-path', default='/home/mark/projects/spring-ai', 
                       help='Path to Spring AI repository')
    parser.add_argument('--output-file', help='Output file for highlights markdown')
    
    args = parser.parse_args()
    
    Logger.bold(f"📚 DOCUMENTATION-BASED FEATURE EXTRACTION")
    Logger.bold(f"Target Version: {args.version}")
    Logger.bold(f"Since Version: {args.since_version}")
    Logger.bold("=" * 60)
    
    extractor = DocBasedFeatureExtractor(args.spring_ai_path)
    
    try:
        # Extract features
        categorized_features = extractor.extract_features(args.version, args.since_version)
        
        # Generate highlights
        highlights_md = extractor.generate_highlights(categorized_features)
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                f.write(highlights_md)
            Logger.success(f"✅ Highlights saved to {args.output_file}")
        else:
            print("\n" + highlights_md)
        
        Logger.success("✅ Documentation-based feature extraction completed")
        
    except Exception as e:
        Logger.error(f"❌ Feature extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
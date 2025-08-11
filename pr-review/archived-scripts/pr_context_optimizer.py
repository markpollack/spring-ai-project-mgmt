#!/usr/bin/env python3
"""
PR Context Optimizer

Handles intelligent context size management for AI analysis of PRs.
Adapts context inclusion strategy based on PR size to avoid timeouts
while preserving critical information for security and risk assessment.

Usage:
    from pr_context_optimizer import PRContextOptimizer
    
    optimizer = PRContextOptimizer()
    optimized_context = optimizer.optimize_file_changes(file_changes)
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class PRSize(Enum):
    """PR size categories for context optimization"""
    SMALL = "small"      # ≤10 files
    MEDIUM = "medium"    # 11-20 files  
    LARGE = "large"      # 21-50 files
    HUGE = "huge"        # >50 files


@dataclass
class ContextLimits:
    """Context limits for different PR sizes"""
    max_files: int
    max_patch_lines_per_file: int
    include_full_patches: bool
    prioritize_security: bool
    include_deletions: bool


class PRContextOptimizer:
    """Optimizes PR context for AI analysis based on PR size"""
    
    def __init__(self):
        # Define limits for different PR sizes
        self.size_limits = {
            PRSize.SMALL: ContextLimits(
                max_files=15,
                max_patch_lines_per_file=25,
                include_full_patches=True,
                prioritize_security=False,
                include_deletions=True
            ),
            PRSize.MEDIUM: ContextLimits(
                max_files=12,
                max_patch_lines_per_file=18,
                include_full_patches=True,
                prioritize_security=True,
                include_deletions=False
            ),
            PRSize.LARGE: ContextLimits(
                max_files=10,
                max_patch_lines_per_file=12,
                include_full_patches=False,
                prioritize_security=True,
                include_deletions=False
            ),
            PRSize.HUGE: ContextLimits(
                max_files=8,
                max_patch_lines_per_file=8,
                include_full_patches=False,
                prioritize_security=True,
                include_deletions=False
            )
        }
        
        # Security-relevant keywords for patch filtering
        self.security_keywords = [
            'password', 'secret', 'key', 'token', 'credential', 'auth',
            'system.getenv', 'system.getproperty', 'base64', 'encrypt',
            'decrypt', 'hash', 'security', 'permission', 'authorize'
        ]
    
    def classify_pr_size(self, file_count: int) -> PRSize:
        """Classify PR size based on file count"""
        if file_count <= 10:
            return PRSize.SMALL
        elif file_count <= 20:
            return PRSize.MEDIUM
        elif file_count <= 50:
            return PRSize.LARGE
        else:
            return PRSize.HUGE
    
    def calculate_context_estimate(self, file_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate estimated context size for the PR"""
        total_files = len(file_changes)
        total_patch_chars = sum(len(f.get('patch', '')) for f in file_changes)
        total_additions = sum(f.get('additions', 0) for f in file_changes)
        total_deletions = sum(f.get('deletions', 0) for f in file_changes)
        
        # Categorize files
        java_files = [f for f in file_changes if f.get('filename', '').endswith('.java')]
        test_files = [f for f in java_files if '/test/' in f.get('filename', '')]
        config_files = [f for f in file_changes if self._is_config_file(f.get('filename', ''))]
        
        return {
            'total_files': total_files,
            'total_patch_chars': total_patch_chars,
            'total_additions': total_additions,
            'total_deletions': total_deletions,
            'java_files': len(java_files),
            'test_files': len(test_files),
            'config_files': len(config_files),
            'pr_size': self.classify_pr_size(total_files),
            'estimated_kb': total_patch_chars / 1024
        }
    
    def prioritize_files(self, file_changes: List[Dict[str, Any]], limits: ContextLimits) -> List[Dict[str, Any]]:
        """Prioritize files for inclusion based on importance"""
        
        # Score each file by importance
        scored_files = []
        for file_change in file_changes:
            filename = file_change.get('filename', '')
            score = self._calculate_file_importance_score(file_change)
            scored_files.append((score, file_change))
        
        # Sort by score (highest first) and take top files
        scored_files.sort(key=lambda x: x[0], reverse=True)
        return [f[1] for f in scored_files[:limits.max_files]]
    
    def _calculate_file_importance_score(self, file_change: Dict[str, Any]) -> int:
        """Calculate importance score for file prioritization"""
        filename = file_change.get('filename', '')
        additions = file_change.get('additions', 0)
        patch = file_change.get('patch', '')
        
        score = 0
        
        # File type importance
        if filename.endswith('.java'):
            if '/test/' not in filename:
                score += 100  # Main implementation files are highest priority
            else:
                score += 60   # Test files are medium priority
        elif self._is_config_file(filename):
            score += 40       # Config files are lower priority
        else:
            score += 20       # Documentation, etc. are lowest priority
        
        # Size bonus (larger changes are more important)
        score += min(additions, 50)  # Cap at 50 to avoid skewing too much
        
        # Security content bonus
        if any(keyword in patch.lower() for keyword in self.security_keywords):
            score += 30
        
        # New file bonus (additions are more important than modifications)
        if file_change.get('status') == 'added':
            score += 25
        
        return score
    
    def _is_config_file(self, filename: str) -> bool:
        """Check if file is a configuration file"""
        config_extensions = ['.xml', '.properties', '.yml', '.yaml', '.json', '.md', '.imports', '.txt']
        return any(filename.endswith(ext) for ext in config_extensions)
    
    def optimize_patch_content(self, patch: str, limits: ContextLimits) -> str:
        """Optimize patch content based on context limits"""
        if not patch:
            return ""
        
        if limits.include_full_patches and len(patch) < 2000:
            # Small patches can be included fully
            return patch
        
        # Extract meaningful lines from patch
        patch_lines = patch.split('\n')
        optimized_lines = []
        added_lines = 0
        
        for line in patch_lines:
            # Always include diff headers
            if line.startswith(('@@', '+++', '---', 'diff --git')):
                optimized_lines.append(line)
                continue
            
            # Skip if we've hit our line limit
            if added_lines >= limits.max_patch_lines_per_file:
                break
            
            # Handle addition/deletion filtering
            if line.startswith('-') and not limits.include_deletions:
                continue
            
            # Include line if it's relevant
            if self._is_patch_line_relevant(line, limits):
                optimized_lines.append(line[:120])  # Truncate very long lines
                added_lines += 1
        
        # Add truncation notice if we cut content
        if added_lines >= limits.max_patch_lines_per_file and len(patch_lines) > added_lines + 5:
            optimized_lines.append("... [patch truncated for context size] ...")
        
        return '\n'.join(optimized_lines)
    
    def _is_patch_line_relevant(self, line: str, limits: ContextLimits) -> bool:
        """Determine if a patch line should be included"""
        line_lower = line.lower()
        
        # Always include additions and modifications
        if line.startswith(('+', '-', ' ')):
            
            # If prioritizing security, filter by keywords
            if limits.prioritize_security:
                return (any(keyword in line_lower for keyword in self.security_keywords) or
                        'import' in line_lower or
                        'class ' in line_lower or
                        'public ' in line_lower or
                        '@' in line)  # Annotations
            else:
                return True  # Include all code lines for small PRs
        
        return False
    
    def build_optimized_file_changes_summary(self, file_changes: List[Dict[str, Any]]) -> str:
        """Build optimized file changes summary for AI prompts"""
        if not file_changes:
            return "*No file changes data available*"
        
        # Calculate context stats
        context_stats = self.calculate_context_estimate(file_changes)
        pr_size = context_stats['pr_size']
        limits = self.size_limits[pr_size]
        
        # Build summary header
        summary = []
        summary.append(f"**PR Size**: {pr_size.value.title()} ({context_stats['total_files']} files, ~{context_stats['estimated_kb']:.1f}KB)")
        summary.append(f"**File Types**: {context_stats['java_files']} Java files ({context_stats['test_files']} tests), {context_stats['config_files']} config files")
        summary.append(f"**Changes**: +{context_stats['total_additions']}/-{context_stats['total_deletions']} lines")
        summary.append("")
        
        # Add optimization notice for large PRs
        if pr_size in [PRSize.LARGE, PRSize.HUGE]:
            summary.append(f"*Context optimized for {pr_size.value} PR: showing top {limits.max_files} files with security-focused filtering*")
            summary.append("")
        
        # Prioritize and optimize files
        prioritized_files = self.prioritize_files(file_changes, limits)
        
        # Generate file details
        for file_change in prioritized_files:
            filename = file_change.get('filename', 'Unknown')
            status = file_change.get('status', 'unknown')
            additions = file_change.get('additions', 0)
            deletions = file_change.get('deletions', 0)
            patch = file_change.get('patch', '')
            
            summary.append(f"**{filename}** ({status})")
            summary.append(f"  - +{additions}/-{deletions} lines")
            
            # Include optimized patch content
            optimized_patch = self.optimize_patch_content(patch, limits)
            if optimized_patch and limits.max_patch_lines_per_file > 0:
                patch_lines = [line for line in optimized_patch.split('\n') 
                              if line.strip() and not line.startswith(('@@', '+++', '---', 'diff --git'))]
                if patch_lines:
                    summary.append("  - Key changes:")
                    for line in patch_lines[:8]:  # Max 8 lines per file in summary
                        summary.append(f"    {line}")
            
            summary.append("")
        
        # Add footer for omitted files
        omitted_count = len(file_changes) - len(prioritized_files)
        if omitted_count > 0:
            summary.append(f"*{omitted_count} additional files omitted for context optimization*")
        
        return '\n'.join(summary)
    
    def get_optimization_stats(self, file_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the optimization applied"""
        context_stats = self.calculate_context_estimate(file_changes)
        pr_size = context_stats['pr_size']
        limits = self.size_limits[pr_size]
        prioritized_files = self.prioritize_files(file_changes, limits)
        
        return {
            'original_file_count': len(file_changes),
            'optimized_file_count': len(prioritized_files),
            'pr_size_category': pr_size.value,
            'context_limits_applied': {
                'max_files': limits.max_files,
                'max_patch_lines': limits.max_patch_lines_per_file,
                'security_prioritized': limits.prioritize_security,
                'full_patches': limits.include_full_patches
            },
            'estimated_original_size_kb': context_stats['estimated_kb'],
            'optimization_ratio': len(prioritized_files) / len(file_changes) if file_changes else 1.0
        }


def main():
    """Command-line interface for testing context optimization"""
    import sys
    import json
    from pathlib import Path
    
    if len(sys.argv) < 2:
        print("Usage: python3 pr_context_optimizer.py <pr_number>")
        print("  Tests context optimization on a PR's file changes")
        sys.exit(1)
    
    pr_number = sys.argv[1]
    
    # Load file changes data
    context_dir = Path(__file__).parent / "context" / f"pr-{pr_number}"
    file_changes_file = context_dir / "file-changes.json"
    
    if not file_changes_file.exists():
        print(f"No file changes data found for PR #{pr_number}")
        sys.exit(1)
    
    with open(file_changes_file, 'r') as f:
        file_changes = json.load(f)
    
    # Test optimization
    optimizer = PRContextOptimizer()
    
    print("=== PR Context Optimization Test ===")
    print()
    
    stats = optimizer.get_optimization_stats(file_changes)
    print("Optimization Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    optimized_summary = optimizer.build_optimized_file_changes_summary(file_changes)
    print("Optimized Summary:")
    print(optimized_summary)


if __name__ == "__main__":
    main()
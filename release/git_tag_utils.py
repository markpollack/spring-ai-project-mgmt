"""
Shared Git Tag Utilities

Centralized git tag detection and version parsing logic to maintain DRY principles.
Used by multiple release automation scripts to ensure consistent behavior.
"""

import subprocess
from pathlib import Path
from typing import Optional, Tuple, List
import re


def get_latest_version_tag(repo_path: Path, branch_specific: bool = True) -> Optional[str]:
    """
    Get the latest version tag from git repository.

    Args:
        repo_path: Path to the git repository
        branch_specific: If True, only returns tags reachable from current branch (default: True)
                        If False, returns latest tag across all branches

    Returns:
        Latest version tag (e.g., 'v1.0.2') or None if no tags found

    Examples:
        # On 1.0.x branch with branch_specific=True
        >>> get_latest_version_tag(Path('.'), branch_specific=True)
        'v1.0.2'  # Returns latest 1.0.x tag, not milestone tags from main

        # With branch_specific=False
        >>> get_latest_version_tag(Path('.'), branch_specific=False)
        'v1.1.0-M2'  # Returns latest tag across all branches
    """
    try:
        if branch_specific:
            # Get only tags reachable from current branch (--merged HEAD)
            # This ensures we only get tags from the current branch (e.g., 1.0.x)
            # and not from other branches (e.g., main with milestone tags)
            cmd = ['git', 'tag', '--merged', 'HEAD', '-l', 'v*.*.*']
        else:
            # Get all version tags across all branches
            cmd = ['git', 'tag', '-l', 'v*.*.*']

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_path
        )

        if result.stdout.strip():
            tags = result.stdout.strip().split('\n')
            # Sort tags by semantic version with proper pre-release handling
            tags.sort(key=parse_semantic_version)
            return tags[-1]  # Return the latest tag

    except subprocess.CalledProcessError:
        pass

    return None


def parse_semantic_version(tag: str) -> Tuple[int, int, int, int, str]:
    """
    Parse semantic version for sorting, handling pre-release identifiers.

    Returns tuple: (major, minor, patch, pre_release_order, pre_release_version)
    Pre-release order: 0=M (milestone), 1=RC, 2=GA (no suffix)

    Examples:
        >>> parse_semantic_version('v1.0.1')
        (1, 0, 1, 2, '')
        >>> parse_semantic_version('v1.1.0-M1')
        (1, 1, 0, 0, '1')
        >>> parse_semantic_version('v1.1.0-RC1')
        (1, 1, 0, 1, '1')
    """
    # Remove 'v' prefix
    version = tag.lstrip('v')

    # Split on first dash to separate version from pre-release
    parts = version.split('-', 1)
    base_version = parts[0]
    pre_release = parts[1] if len(parts) > 1 else ''

    # Parse base version (major.minor.patch)
    version_parts = base_version.split('.')
    major = int(version_parts[0]) if len(version_parts) > 0 else 0
    minor = int(version_parts[1]) if len(version_parts) > 1 else 0
    patch = int(version_parts[2]) if len(version_parts) > 2 else 0

    # Determine pre-release order and version
    if not pre_release:
        # GA release (highest priority)
        pre_release_order = 2
        pre_release_version = ''
    elif pre_release.startswith('M'):
        # Milestone (lowest priority)
        pre_release_order = 0
        pre_release_version = pre_release[1:]  # Remove 'M' prefix
    elif pre_release.startswith('RC'):
        # Release Candidate (middle priority)
        pre_release_order = 1
        pre_release_version = pre_release[2:]  # Remove 'RC' prefix
    else:
        # Unknown pre-release type (treat as lower than GA)
        pre_release_order = 0
        pre_release_version = pre_release

    return (major, minor, patch, pre_release_order, pre_release_version)


def get_tags_for_branch(repo_path: Path, pattern: str = 'v*.*.*') -> List[str]:
    """
    Get all tags matching pattern that are reachable from current branch.

    Args:
        repo_path: Path to the git repository
        pattern: Git tag pattern to match (default: 'v*.*.*')

    Returns:
        List of tags sorted by semantic version
    """
    try:
        cmd = ['git', 'tag', '--merged', 'HEAD', '-l', pattern]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_path
        )

        if result.stdout.strip():
            tags = result.stdout.strip().split('\n')
            tags.sort(key=parse_semantic_version)
            return tags

    except subprocess.CalledProcessError:
        pass

    return []


def tag_exists(repo_path: Path, tag: str) -> bool:
    """
    Check if a git tag exists in the repository.

    Args:
        repo_path: Path to the git repository
        tag: Tag name to check (with or without 'v' prefix)

    Returns:
        True if tag exists, False otherwise
    """
    # Ensure tag has 'v' prefix
    if not tag.startswith('v'):
        tag = f'v{tag}'

    try:
        cmd = ['git', 'rev-parse', '--verify', f'refs/tags/{tag}']
        subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=repo_path)
        return True
    except subprocess.CalledProcessError:
        return False

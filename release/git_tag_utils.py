"""
Shared Git Tag Utilities

Centralized git tag detection and version parsing logic to maintain DRY principles.
Used by multiple release automation scripts to ensure consistent behavior.
"""

import subprocess
from pathlib import Path
from typing import Optional, Tuple, List
import re


def get_latest_version_tag(repo_path: Path, branch_specific: bool = True, branch_name: Optional[str] = None) -> Optional[str]:
    """
    Get the latest version tag from git repository.

    Args:
        repo_path: Path to the git repository
        branch_specific: If True, filters tags by branch version pattern (default: True)
        branch_name: Branch name to derive version pattern from (e.g., '1.0.x', 'main')
                    If None, attempts to detect from current branch

    Returns:
        Latest version tag (e.g., 'v1.0.2') or None if no tags found

    Examples:
        # On 1.0.x branch with branch_specific=True
        >>> get_latest_version_tag(Path('.'), branch_specific=True, branch_name='1.0.x')
        'v1.0.2'  # Returns latest 1.0.* tag (GA releases only)

        # With branch_specific=False
        >>> get_latest_version_tag(Path('.'), branch_specific=False)
        'v1.1.0-M2'  # Returns latest tag across all branches
    """
    try:
        # Get all version tags
        cmd = ['git', 'tag', '-l', 'v*.*.*']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_path
        )

        if not result.stdout.strip():
            return None

        tags = result.stdout.strip().split('\n')

        if branch_specific:
            # Detect branch name if not provided
            if branch_name is None:
                branch_cmd = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
                branch_result = subprocess.run(
                    branch_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=repo_path
                )
                branch_name = branch_result.stdout.strip()

                # Handle detached HEAD state
                if branch_name == 'HEAD':
                    # Try to get branch from reflog or remote tracking
                    symbolic_cmd = ['git', 'symbolic-ref', 'HEAD']
                    symbolic_result = subprocess.run(
                        symbolic_cmd,
                        capture_output=True,
                        text=True,
                        cwd=repo_path
                    )
                    if symbolic_result.returncode == 0:
                        # Extract branch name from refs/heads/...
                        branch_name = symbolic_result.stdout.strip().split('/')[-1]

            # Filter tags by branch version pattern
            # For 1.0.x branch, only include v1.0.* GA tags (no milestones/RCs)
            # For main branch, include all tags
            if branch_name and branch_name != 'main' and branch_name != 'HEAD':
                # Extract version prefix from branch name (e.g., '1.0.x' -> '1.0')
                version_match = re.match(r'(\d+\.\d+)\.x', branch_name)
                if version_match:
                    version_prefix = version_match.group(1)
                    # Filter for tags matching version pattern without pre-release suffixes
                    # e.g., v1.0.0, v1.0.1, v1.0.2 (but not v1.0.0-M1, v1.1.0-M1)
                    tags = [
                        tag for tag in tags
                        if tag.startswith(f'v{version_prefix}.')
                        and '-' not in tag  # Exclude pre-release tags (M1, RC1, etc.)
                    ]

        # Sort tags by semantic version with proper pre-release handling
        tags.sort(key=parse_semantic_version)
        return tags[-1] if tags else None

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

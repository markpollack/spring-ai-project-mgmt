#!/usr/bin/env python3

import subprocess
import re
from pathlib import Path
from typing import Set, List

def get_git_authors(repo_path: Path, since_tag: str = "v1.0.1") -> Set[str]:
    """Get unique authors from git log since specified tag on current branch"""
    cmd = [
        'git', 'log', f'{since_tag}..HEAD',
        '--pretty=format:%aN',
        '--no-merges'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_path, check=True)
    authors = set()
    
    for line in result.stdout.strip().split('\n'):
        if line.strip():
            authors.add(line.strip())
    
    return authors

def extract_contributors_from_release_notes(release_notes_path: Path) -> Set[str]:
    """Extract contributor names from RELEASE_NOTES.md"""
    if not release_notes_path.exists():
        print(f"Release notes file not found: {release_notes_path}")
        return set()
    
    content = release_notes_path.read_text()
    contributors = set()
    
    # Look for contributors section
    contributors_section = False
    for line in content.split('\n'):
        if 'Contributors' in line and '##' in line:
            contributors_section = True
            continue
        elif contributors_section and line.startswith('##'):
            break
        elif contributors_section and line.strip() and line.startswith('- '):
            # Extract name from format: - [Real Name (@username)](url)
            # Pattern: - [Real Name (@username)](url)
            match = re.search(r'- \[([^(@]+)', line)
            if match:
                name = match.group(1).strip()
                contributors.add(name)
    
    return contributors

def main():
    repo_path = Path('./spring-ai-release')
    release_notes_path = Path('./RELEASE_NOTES.md')
    
    print("🔍 Verifying contributor list accuracy...")
    print()
    
    if not repo_path.exists():
        print(f"❌ Repository not found at {repo_path}")
        return
    
    if not release_notes_path.exists():
        print(f"❌ Release notes not found at {release_notes_path}")
        return
    
    # Get actual git authors
    print("📊 Extracting authors from git log...")
    git_authors = get_git_authors(repo_path)
    print(f"   Found {len(git_authors)} unique authors in git log")
    
    # Get contributors from release notes
    print("📋 Extracting contributors from release notes...")
    release_contributors = extract_contributors_from_release_notes(release_notes_path)
    print(f"   Found {len(release_contributors)} contributors in release notes")
    
    print()
    print("=" * 60)
    
    # Compare the sets
    missing_from_release = git_authors - release_contributors
    extra_in_release = release_contributors - git_authors
    
    print(f"✅ Git Authors: {len(git_authors)}")
    print(f"✅ Release Contributors: {len(release_contributors)}")
    print()
    
    if not missing_from_release and not extra_in_release:
        print("🎉 Perfect match! All contributors are correctly listed.")
    else:
        if missing_from_release:
            print(f"⚠️  Missing from release notes ({len(missing_from_release)}):")
            for author in sorted(missing_from_release):
                print(f"   - {author}")
            print()
        
        if extra_in_release:
            print(f"⚠️  Extra in release notes ({len(extra_in_release)}):")
            for contributor in sorted(extra_in_release):
                print(f"   - {contributor}")
            print()
    
    print("=" * 60)
    print()
    print("📝 All Git Authors (for reference):")
    for author in sorted(git_authors):
        print(f"   - {author}")

if __name__ == '__main__':
    main()
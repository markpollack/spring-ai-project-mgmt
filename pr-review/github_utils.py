#!/usr/bin/env python3
"""
GitHub Utilities for Spring AI PR Management

Shared utilities for GitHub operations including PR branch management,
API interactions, and state management across all PR review scripts.

Usage:
    from github_utils import ensure_correct_branch, get_pr_branch_name
    
    # Ensure we're on the right branch before analysis
    ensure_correct_branch("3386", spring_ai_dir)
    
    # Get PR branch name (cached or from API)
    branch_name = get_pr_branch_name("3386")
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass

# Add the current directory to Python path to import existing modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from pr_workflow import Logger
except ImportError:
    # Simple logger fallback if pr_workflow is not available
    class Logger:
        @staticmethod
        def info(msg): print(f"\033[34m[INFO]\033[0m {msg}")
        @staticmethod
        def success(msg): print(f"\033[32m[SUCCESS]\033[0m {msg}")
        @staticmethod
        def warn(msg): print(f"\033[33m[WARN]\033[0m {msg}")
        @staticmethod
        def error(msg): print(f"\033[31m[ERROR]\033[0m {msg}")


@dataclass
class PRInfo:
    """Basic PR information"""
    number: str
    title: str
    author: str
    branch_name: str
    state: str
    created_at: str


class GitHubUtils:
    """Shared GitHub utilities for PR management"""
    
    def __init__(self, working_dir: Path, spring_ai_repo: str = "spring-projects/spring-ai"):
        self.working_dir = working_dir
        self.spring_ai_repo = spring_ai_repo
        self.state_dir = working_dir / "state"
        self.branch_mapping_file = self.state_dir / "pr-branch-mapping.json"
        
        # Ensure state directory exists
        self.state_dir.mkdir(exist_ok=True)
    
    def load_pr_branch_mapping(self) -> Dict[str, str]:
        """Load PR number to branch name mapping from state file"""
        try:
            if self.branch_mapping_file.exists():
                with open(self.branch_mapping_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            Logger.warn(f"Error loading branch mapping: {e}")
            return {}
    
    def store_pr_branch_mapping(self, pr_number: str, branch_name: str):
        """Store PR number to branch name mapping"""
        try:
            mapping = self.load_pr_branch_mapping()
            mapping[pr_number] = branch_name
            
            with open(self.branch_mapping_file, 'w') as f:
                json.dump(mapping, f, indent=2)
            
            Logger.info(f"💾 Stored branch mapping: PR #{pr_number} → {branch_name}")
            
        except Exception as e:
            Logger.error(f"Error storing branch mapping: {e}")
    
    def get_pr_branch_name(self, pr_number: str) -> Optional[str]:
        """Get PR branch name from cache or GitHub API"""
        
        # First check cache
        mapping = self.load_pr_branch_mapping()
        if pr_number in mapping:
            branch_name = mapping[pr_number]
            Logger.info(f"📋 Using cached branch: PR #{pr_number} → {branch_name}")
            return branch_name
        
        # Fetch from GitHub API
        try:
            Logger.info(f"🔍 Fetching branch name for PR #{pr_number} from GitHub...")
            
            result = subprocess.run([
                "gh", "pr", "view", pr_number,
                "--repo", self.spring_ai_repo,
                "--json", "headRefName"
            ], capture_output=True, text=True, check=True, timeout=30)
            
            pr_data = json.loads(result.stdout)
            branch_name = pr_data.get("headRefName")
            
            if branch_name:
                Logger.success(f"✅ Found branch: PR #{pr_number} → {branch_name}")
                # Cache the result
                self.store_pr_branch_mapping(pr_number, branch_name)
                return branch_name
            else:
                Logger.error(f"No branch name found in PR #{pr_number} data")
                return None
                
        except subprocess.CalledProcessError as e:
            Logger.error(f"GitHub CLI error getting PR #{pr_number} branch: {e}")
            if e.stderr:
                Logger.error(f"Error details: {e.stderr.strip()}")
            return None
        except Exception as e:
            Logger.error(f"Error getting PR branch name: {e}")
            return None
    
    def get_pr_basic_info(self, pr_number: str) -> Optional[PRInfo]:
        """Get basic PR information from GitHub API"""
        try:
            Logger.info(f"🔍 Fetching PR #{pr_number} info from GitHub...")
            
            result = subprocess.run([
                "gh", "pr", "view", pr_number,
                "--repo", self.spring_ai_repo,
                "--json", "number,title,author,headRefName,state,createdAt"
            ], capture_output=True, text=True, check=True, timeout=30)
            
            pr_data = json.loads(result.stdout)
            
            pr_info = PRInfo(
                number=str(pr_data.get("number", pr_number)),
                title=pr_data.get("title", "Unknown"),
                author=pr_data.get("author", {}).get("login", "Unknown"),
                branch_name=pr_data.get("headRefName", ""),
                state=pr_data.get("state", "unknown"),
                created_at=pr_data.get("createdAt", "")
            )
            
            Logger.success(f"✅ Got PR info: {pr_info.title} by {pr_info.author}")
            
            # Cache the branch name
            if pr_info.branch_name:
                self.store_pr_branch_mapping(pr_number, pr_info.branch_name)
            
            return pr_info
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"GitHub CLI error getting PR #{pr_number} info: {e}")
            return None
        except Exception as e:
            Logger.error(f"Error getting PR info: {e}")
            return None
    
    def get_current_branch(self, spring_ai_dir: Path) -> Optional[str]:
        """Get current branch in the Spring AI repository"""
        try:
            result = subprocess.run([
                "git", "rev-parse", "--abbrev-ref", "HEAD"
            ], cwd=spring_ai_dir, capture_output=True, text=True, check=True)
            
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Error getting current branch: {e}")
            return None
    
    def switch_to_branch(self, spring_ai_dir: Path, branch_name: str) -> bool:
        """Switch to the specified branch in the Spring AI repository"""
        try:
            Logger.info(f"🔄 Switching to branch: {branch_name}")
            
            # First, fetch to make sure we have the latest branch info
            subprocess.run([
                "git", "fetch", "origin"
            ], cwd=spring_ai_dir, capture_output=True, check=True)
            
            # Switch to the branch
            result = subprocess.run([
                "git", "checkout", branch_name
            ], cwd=spring_ai_dir, capture_output=True, text=True, check=True)
            
            Logger.success(f"✅ Switched to branch: {branch_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"Error switching to branch {branch_name}: {e}")
            if e.stderr:
                Logger.error(f"Git error: {e.stderr.strip()}")
            return False
    
    def ensure_correct_branch(self, pr_number: str, spring_ai_dir: Path) -> bool:
        """Ensure we're on the correct branch for the given PR"""
        
        # Get the expected branch name for this PR
        expected_branch = self.get_pr_branch_name(pr_number)
        if not expected_branch:
            Logger.error(f"Could not determine branch for PR #{pr_number}")
            return False
        
        # Check current branch
        current_branch = self.get_current_branch(spring_ai_dir)
        if not current_branch:
            Logger.error("Could not determine current branch")
            return False
        
        # If we're already on the right branch, we're good
        if current_branch == expected_branch:
            Logger.info(f"✅ Already on correct branch: {current_branch}")
            return True
        
        # Need to switch branches
        Logger.info(f"🔄 Need to switch: {current_branch} → {expected_branch}")
        return self.switch_to_branch(spring_ai_dir, expected_branch)


# Global utility functions for easy import
def get_github_utils(working_dir: Path = None) -> GitHubUtils:
    """Get GitHubUtils instance with default working directory"""
    if working_dir is None:
        working_dir = Path(__file__).parent
    return GitHubUtils(working_dir)


def ensure_correct_branch(pr_number: str, spring_ai_dir: Path, working_dir: Path = None) -> bool:
    """Convenience function to ensure correct branch"""
    utils = get_github_utils(working_dir)
    return utils.ensure_correct_branch(pr_number, spring_ai_dir)


def get_pr_branch_name(pr_number: str, working_dir: Path = None) -> Optional[str]:
    """Convenience function to get PR branch name"""
    utils = get_github_utils(working_dir)
    return utils.get_pr_branch_name(pr_number)


def get_pr_basic_info(pr_number: str, working_dir: Path = None) -> Optional[PRInfo]:
    """Convenience function to get PR basic info"""
    utils = get_github_utils(working_dir)
    return utils.get_pr_basic_info(pr_number)


def main():
    """Command-line interface for testing GitHub utilities"""
    if len(sys.argv) < 2:
        print("Usage: python3 github_utils.py <pr_number>")
        print("  Tests GitHub utilities with the given PR number")
        sys.exit(1)
    
    pr_number = sys.argv[1]
    working_dir = Path(__file__).parent
    spring_ai_dir = working_dir / "spring-ai"
    
    print(f"=== Testing GitHub Utils for PR #{pr_number} ===")
    
    utils = GitHubUtils(working_dir)
    
    # Test getting PR info
    pr_info = utils.get_pr_basic_info(pr_number)
    if pr_info:
        print(f"PR Info: {pr_info}")
    
    # Test branch management
    if spring_ai_dir.exists():
        current_branch = utils.get_current_branch(spring_ai_dir)
        print(f"Current branch: {current_branch}")
        
        success = utils.ensure_correct_branch(pr_number, spring_ai_dir)
        print(f"Branch switch successful: {success}")
    else:
        print(f"Spring AI directory not found: {spring_ai_dir}")


if __name__ == "__main__":
    main()
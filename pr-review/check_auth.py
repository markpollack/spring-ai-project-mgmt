#!/usr/bin/env python3
"""
Check authentication and permissions for GitHub and Git operations

This module provides utilities to verify that:
1. GitHub CLI (gh) is authenticated
2. Git has proper access to the Spring AI repository
3. Required permissions are available
"""

import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional

class Logger:
    @staticmethod
    def info(msg): print(f"\033[34m[INFO]\033[0m {msg}")
    @staticmethod
    def success(msg): print(f"\033[32m[SUCCESS]\033[0m {msg}")
    @staticmethod
    def warn(msg): print(f"\033[33m[WARN]\033[0m {msg}")
    @staticmethod
    def error(msg): print(f"\033[31m[ERROR]\033[0m {msg}")


class AuthChecker:
    """Check authentication status for GitHub and Git operations"""
    
    SPRING_AI_REPO = "spring-projects/spring-ai"
    
    def check_gh_auth(self) -> Tuple[bool, str]:
        """Check if GitHub CLI is authenticated"""
        try:
            # Check auth status
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Extract logged in user
                for line in result.stdout.split('\n'):
                    if 'Logged in to github.com as' in line:
                        user = line.split('as')[-1].strip().split()[0]
                        return True, f"Authenticated as {user}"
                return True, "Authenticated"
            else:
                return False, "Not authenticated with GitHub CLI"
                
        except subprocess.TimeoutExpired:
            return False, "GitHub CLI auth check timed out"
        except FileNotFoundError:
            return False, "GitHub CLI (gh) not found. Please install it first."
        except Exception as e:
            return False, f"Error checking GitHub CLI auth: {e}"
    
    def check_gh_repo_access(self) -> Tuple[bool, str]:
        """Check if we can access the Spring AI repository via gh"""
        try:
            # Try to fetch repo info
            result = subprocess.run(
                ["gh", "repo", "view", self.SPRING_AI_REPO, "--json", "name"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, f"Can access {self.SPRING_AI_REPO}"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                if "HTTP 404" in error_msg:
                    return False, f"Repository {self.SPRING_AI_REPO} not found or no access"
                elif "HTTP 401" in error_msg:
                    return False, "Authentication required - run: gh auth login"
                else:
                    return False, f"Cannot access repository: {error_msg}"
                    
        except subprocess.TimeoutExpired:
            return False, "Repository access check timed out - network issues?"
        except Exception as e:
            return False, f"Error checking repository access: {e}"
    
    def check_git_remote_access(self, repo_dir: Optional[Path] = None) -> Tuple[bool, str]:
        """Check if git can fetch from the Spring AI repository"""
        if repo_dir and repo_dir.exists():
            cwd = repo_dir
        else:
            # Try to find the spring-ai directory
            script_dir = Path(__file__).parent
            spring_ai_dir = script_dir / "spring-ai"
            if spring_ai_dir.exists():
                cwd = spring_ai_dir
            else:
                return True, "Spring AI repo not cloned yet (will be cloned during workflow)"
        
        try:
            # Try to fetch with --dry-run to test access
            result = subprocess.run(
                ["git", "ls-remote", "https://github.com/spring-projects/spring-ai.git", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=cwd
            )
            
            if result.returncode == 0:
                return True, "Git can access Spring AI repository"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                if "Authentication failed" in error_msg:
                    return False, "Git authentication failed - may need to configure credentials"
                elif "Could not resolve host" in error_msg:
                    return False, "Network error - cannot reach github.com"
                else:
                    return False, f"Git access error: {error_msg}"
                    
        except subprocess.TimeoutExpired:
            return False, "Git remote access check timed out"
        except Exception as e:
            return False, f"Error checking git access: {e}"
    
    def check_pr_api_access(self) -> Tuple[bool, str]:
        """Check if we can list PRs via the API"""
        try:
            result = subprocess.run(
                ["gh", "pr", "list", "--repo", self.SPRING_AI_REPO, "--limit", "1", "--json", "number"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, "Can access PR API"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return False, f"Cannot access PR API: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "PR API access check timed out"
        except Exception as e:
            return False, f"Error checking PR API access: {e}"
    
    def run_all_checks(self, repo_dir: Optional[Path] = None) -> bool:
        """Run all authentication checks and report results"""
        Logger.info("🔐 Checking authentication and permissions...")
        Logger.info("=" * 50)
        
        all_passed = True
        
        # Check GitHub CLI auth
        success, message = self.check_gh_auth()
        if success:
            Logger.success(f"✅ GitHub CLI: {message}")
        else:
            Logger.error(f"❌ GitHub CLI: {message}")
            all_passed = False
            
        # Check repo access via gh
        if success:  # Only check if gh is authenticated
            success, message = self.check_gh_repo_access()
            if success:
                Logger.success(f"✅ Repository access: {message}")
            else:
                Logger.error(f"❌ Repository access: {message}")
                all_passed = False
                
            # Check PR API access
            success, message = self.check_pr_api_access()
            if success:
                Logger.success(f"✅ PR API: {message}")
            else:
                Logger.error(f"❌ PR API: {message}")
                all_passed = False
        
        # Check git access
        success, message = self.check_git_remote_access(repo_dir)
        if success:
            Logger.success(f"✅ Git access: {message}")
        else:
            Logger.warn(f"⚠️  Git access: {message}")
            # Don't fail for git access as gh might be sufficient
        
        Logger.info("=" * 50)
        
        if not all_passed:
            Logger.error("\n❌ Authentication check failed!")
            Logger.info("\n📝 To fix authentication issues:")
            Logger.info("  1. For GitHub CLI: Run 'gh auth login'")
            Logger.info("  2. For Git: Configure credentials or SSH keys")
            Logger.info("  3. Ensure you have access to spring-projects/spring-ai")
            Logger.info("\n💡 Test with: gh repo view spring-projects/spring-ai")
            return False
        else:
            Logger.success("\n✅ All authentication checks passed!")
            return True


def main():
    """Run authentication checks as a standalone script"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check authentication for Spring AI repository access"
    )
    parser.add_argument(
        "--repo-dir",
        type=Path,
        help="Path to the spring-ai repository directory"
    )
    
    args = parser.parse_args()
    
    checker = AuthChecker()
    if checker.run_all_checks(args.repo_dir):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
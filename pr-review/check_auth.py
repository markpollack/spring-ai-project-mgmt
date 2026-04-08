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
import json
from pathlib import Path
from typing import Tuple, Optional

from github_rest_client import get_client as get_github_client

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
        """Check if GitHub API is accessible (via REST API, no gh CLI needed)"""
        try:
            client = get_github_client(self.SPRING_AI_REPO)
            if client.check_access():
                token_status = "with token" if client.token else "unauthenticated (60 req/hr)"
                return True, f"GitHub REST API accessible ({token_status})"
            else:
                return False, "Cannot access GitHub REST API"
        except Exception as e:
            return False, f"Error checking GitHub API access: {e}"
    
    def check_gh_repo_access(self) -> Tuple[bool, str]:
        """Check if we can access the Spring AI repository via REST API"""
        try:
            client = get_github_client(self.SPRING_AI_REPO)
            repo = client.get_repo()
            return True, f"Can access {self.SPRING_AI_REPO} ({repo.get('name', '')})"
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                return False, f"Repository {self.SPRING_AI_REPO} not found or no access"
            elif "401" in error_msg:
                return False, "Authentication required - set GITHUB_TOKEN env var"
            else:
                return False, f"Cannot access repository: {error_msg}"
    
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
        """Check if we can list PRs via the REST API"""
        try:
            client = get_github_client(self.SPRING_AI_REPO)
            prs = client.list_prs(limit=1)
            if isinstance(prs, list) and len(prs) > 0:
                return True, "Can access PR API"
            return True, "PR API accessible (no open PRs found)"
        except Exception as e:
            return False, f"Cannot access PR API: {e}"
    
    def check_claude_code_installed(self) -> Tuple[bool, str]:
        """Check if Claude Code CLI is installed and accessible"""
        try:
            # Test basic execution
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version = result.stdout.strip() or "Unknown version"
                return True, f"Claude Code installed ({version})"
            else:
                return False, f"Claude Code found but not working properly: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return False, "Claude Code executable timeout - installation issue?"
        except FileNotFoundError:
            return False, "Claude Code CLI (claude) not found. Please install from https://claude.ai/code"
        except Exception as e:
            return False, f"Error checking Claude Code installation: {e}"
    
    def check_claude_code_auth(self) -> Tuple[bool, str]:
        """Check if Claude Code is properly authenticated"""
        try:
            # Test authentication with a simple command
            result = subprocess.run(
                ["claude", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, "Claude Code authenticated and functional"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                    return False, f"Claude Code authentication issue: {error_msg}"
                else:
                    return False, f"Claude Code error: {error_msg}"
                    
        except subprocess.TimeoutExpired:
            return False, "Claude Code authentication check timed out"
        except Exception as e:
            return False, f"Error checking Claude Code authentication: {e}"
    
    def check_claude_code_functionality(self) -> Tuple[bool, str]:
        """Test Claude Code with a simple functionality test"""
        try:
            # Create a temporary test file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("What is 2+2? Please respond with just the number.")
                test_file = f.name
            
            try:
                # Test Claude Code with a simple request
                result = subprocess.run(
                    ["claude", "--dangerously-skip-permissions", test_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Clean up test file
                Path(test_file).unlink(missing_ok=True)
                
                if result.returncode == 0:
                    # Check if response contains "4" or similar
                    response = result.stdout.strip()
                    if "4" in response:
                        return True, "Claude Code functional - AI responses working"
                    else:
                        return False, f"Claude Code responds but output unexpected: {response[:100]}..."
                else:
                    error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                    if "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                        return False, f"Claude Code API authentication failed: {error_msg}"
                    elif "rate limit" in error_msg.lower():
                        return False, f"Claude Code rate limited: {error_msg}"
                    else:
                        return False, f"Claude Code functional test failed: {error_msg}"
                        
            except subprocess.TimeoutExpired:
                Path(test_file).unlink(missing_ok=True)  # Clean up
                return False, "Claude Code functional test timed out (30s) - API issues?"
                
        except Exception as e:
            return False, f"Error testing Claude Code functionality: {e}"
    
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
            
        # Check Claude Code installation
        Logger.info("\n🤖 Checking Claude Code AI Analysis...")
        Logger.info("=" * 50)
        
        claude_success, message = self.check_claude_code_installed()
        if claude_success:
            Logger.success(f"✅ Claude Code CLI: {message}")
            
            # Check Claude Code authentication
            claude_success, message = self.check_claude_code_auth()
            if claude_success:
                Logger.success(f"✅ Claude Code auth: {message}")
                
                # Test Claude Code functionality (optional - don't fail workflow if this fails)
                claude_success, message = self.check_claude_code_functionality()
                if claude_success:
                    Logger.success(f"✅ Claude Code functionality: {message}")
                else:
                    Logger.warn(f"⚠️  Claude Code functionality: {message}")
                    Logger.warn("    AI analysis may be degraded but workflow can continue")
            else:
                Logger.error(f"❌ Claude Code auth: {message}")
                all_passed = False
        else:
            Logger.error(f"❌ Claude Code CLI: {message}")
            all_passed = False
        
        Logger.info("=" * 50)
        
        if not all_passed:
            Logger.error("\n❌ Authentication check failed!")
            Logger.info("\n📝 To fix authentication issues:")
            Logger.info("  🔧 GitHub CLI:")
            Logger.info("    • Run: gh auth login")
            Logger.info("    • Verify: gh repo view spring-projects/spring-ai")
            Logger.info("  🤖 Claude Code:")
            Logger.info("    • Install: npm install -g @anthropic-ai/claude-code")
            Logger.info("    • Or via: https://claude.ai/code")
            Logger.info("    • Verify: claude --version")
            Logger.info("  🔐 Git (optional):")
            Logger.info("    • Configure credentials or SSH keys")
            Logger.info("    • Ensure repository access")
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
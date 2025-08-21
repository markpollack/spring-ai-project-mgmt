#!/usr/bin/env python3
"""
Automated PR Merge Workflow for Spring AI

This script automates the complete merge process for Spring AI PRs including:
- Checking out PR branch
- Rebasing on latest main
- Running backport preparation if approved
- Merging into main
- Pushing to origin

Usage:
    python3 merge_pr.py <pr_number> <branch_name>           # Interactive mode
    python3 merge_pr.py <pr_number> <branch_name> --auto    # Automatic mode
    python3 merge_pr.py <pr_number> <branch_name> --backport # Force backport (overrides approval)
    python3 merge_pr.py <pr_number> <branch_name> --dry-run # Show commands only

Examples:
    python3 merge_pr.py 4174 feature/document-comprehensive-tests
    python3 merge_pr.py 4174 feature/document-comprehensive-tests --auto
    python3 merge_pr.py 4174 feature/document-comprehensive-tests --backport --dry-run
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
from typing import Optional, Tuple

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(step_num: int, total: int, description: str):
    """Print a colorized step header"""
    print(f"{Colors.CYAN}[Step {step_num}/{total}]{Colors.END} {Colors.BOLD}{description}{Colors.END}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def run_command(cmd: str, dry_run: bool = False, confirm: bool = True, cwd: Optional[str] = None) -> Tuple[bool, str]:
    """
    Run a command with optional confirmation and dry-run mode
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    if dry_run:
        print(f"{Colors.WHITE}[DRY RUN] Would execute: {cmd}{Colors.END}")
        return True, "dry-run"
    
    if confirm:
        response = input(f"{Colors.YELLOW}Execute: {cmd}\n{Colors.WHITE}Continue? (Y/n): {Colors.END}")
        if response.lower() in ['n', 'no']:
            print("❌ Skipped by user")
            return False, "skipped"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        if result.returncode == 0:
            if result.stdout.strip():
                print(f"{Colors.WHITE}{result.stdout.strip()}{Colors.END}")
            return True, result.stdout
        else:
            print_error(f"Command failed with return code {result.returncode}")
            if result.stderr:
                print_error(f"Error: {result.stderr.strip()}")
            return False, result.stderr
    except Exception as e:
        print_error(f"Exception running command: {e}")
        return False, str(e)

def check_backport_status(pr_number: str) -> bool:
    """Check if PR is approved for backport by looking at assessment file"""
    try:
        # Look for backport assessment in context directory relative to script location
        script_dir = Path(__file__).resolve().parent
        context_dirs = list(script_dir.glob("runs/*/context/pr-" + pr_number))
        if not context_dirs:
            context_dirs = list(script_dir.glob("context/pr-" + pr_number))
        
        # Debug: print search paths if no context dirs found
        if not context_dirs:
            print_warning(f"No context directories found in {script_dir}/runs/*/context/pr-{pr_number}")
            print_warning(f"Also checked {script_dir}/context/pr-{pr_number}")
        
        for context_dir in context_dirs:
            backport_file = context_dir / "backport-assessment.json"
            if backport_file.exists():
                with open(backport_file, 'r') as f:
                    data = json.load(f)
                    decision = data.get('decision', '').upper()
                    return decision == 'APPROVE'
        
        print_warning(f"No backport assessment found for PR #{pr_number}")
        return False
        
    except Exception as e:
        print_warning(f"Could not check backport status: {e}")
        return False

def merge_workflow(pr_number: str, branch_name: str, auto: bool = False, 
                  force_backport: bool = False, dry_run: bool = False) -> bool:
    """
    Execute the complete merge workflow
    
    Returns:
        bool: True if successful, False otherwise
    """
    spring_ai_dir = Path(__file__).parent / "spring-ai"
    
    if not spring_ai_dir.exists():
        print_error(f"Spring AI directory not found: {spring_ai_dir}")
        print_info("Expected: /home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/spring-ai")
        return False
    
    # Check backport status
    should_backport = force_backport or check_backport_status(pr_number)
    if should_backport:
        print_success(f"PR #{pr_number} is approved for backport")
    
    total_steps = 9 if should_backport else 8
    confirm = not auto
    
    print(f"\n{Colors.BOLD}🚀 Starting merge workflow for PR #{pr_number}{Colors.END}")
    print(f"Branch: {branch_name}")
    print(f"Mode: {'Auto' if auto else 'Interactive'}")
    print(f"Backport: {'Yes' if should_backport else 'No'}")
    print(f"Dry run: {'Yes' if dry_run else 'No'}")
    print()
    
    # Step 1: Navigate to Spring AI repository (already handled by cwd parameter)
    print_step(1, total_steps, "Navigate to Spring AI repository")
    print_info(f"Working in: {spring_ai_dir}")
    
    # Step 2: Checkout PR branch
    print_step(2, total_steps, f"Checkout PR branch: {branch_name}")
    success, output = run_command(f"git checkout {branch_name}", dry_run, confirm, str(spring_ai_dir))
    if not success:
        print_error("Failed to checkout PR branch")
        return False
    
    # Step 3: Update main branch without switching
    print_step(3, total_steps, "Update main branch without leaving current branch")
    success, output = run_command("git fetch origin", dry_run, confirm, str(spring_ai_dir))
    if success:
        success, output = run_command("git branch -f main origin/main", dry_run, confirm, str(spring_ai_dir))
    if not success:
        print_error("Failed to update main branch")
        return False
    
    # Step 4: Rebase PR branch on main
    print_step(4, total_steps, "Rebase PR branch on latest main")
    success, output = run_command("git rebase main", dry_run, confirm, str(spring_ai_dir))
    if not success:
        print_error("Rebase failed - you may need to resolve conflicts manually")
        print_info("After resolving conflicts:")
        print_info("1. Fix conflicts in files")
        print_info("2. git add <fixed-files>")
        print_info("3. git rebase --continue")
        print_info("4. Re-run this script")
        return False
    
    current_step = 5
    
    # Step 5: Backport preparation (if approved)
    if should_backport:
        print_step(current_step, total_steps, "Add backport directive to PR")
        backport_script = Path(__file__).parent / "prepare_backport.py"
        # When --backport is used, pass both --override and --auto to make it "just work"
        # Otherwise, only pass --auto to prevent hanging
        if force_backport:
            flags = "--override --auto"
        else:
            flags = "--auto"
        success, output = run_command(f"python3 {backport_script} {pr_number} {flags}".strip(), dry_run, confirm, str(spring_ai_dir))
        if not success:
            print_error("Backport preparation failed")
            return False
        current_step += 1
    
    # Step 6: Switch to main branch
    print_step(current_step, total_steps, "Switch to main branch")
    success, output = run_command("git checkout main", dry_run, confirm, str(spring_ai_dir))
    if not success:
        print_error("Failed to checkout main branch")
        return False
    current_step += 1
    
    # Step 7: Merge PR branch into main
    print_step(current_step, total_steps, f"Merge PR branch: {branch_name}")
    success, output = run_command(f"git merge {branch_name}", dry_run, confirm, str(spring_ai_dir))
    if not success:
        print_error("Merge failed")
        return False
    current_step += 1
    
    # Step 8: Push to origin
    print_step(current_step, total_steps, "Push merged changes to origin")
    success, output = run_command("git push origin main", dry_run, confirm, str(spring_ai_dir))
    if not success:
        print_error("Push failed - main branch may have new commits")
        print_info("You may need to:")
        print_info("1. git pull --rebase origin main")
        print_info("2. git push origin main")
        return False
    current_step += 1
    
    # Step 9: Reminder
    print_step(current_step, total_steps, "Final reminders")
    print_success("🎉 Merge completed successfully!")
    print()
    print_info("📝 Don't forget to:")
    print_info(f"   • Close the GitHub issue(s) associated with PR #{pr_number}")
    print_info(f"   • Check PR status: https://github.com/spring-projects/spring-ai/pull/{pr_number}")
    if should_backport:
        print_info("   • Monitor the automatic backport process")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Automated PR merge workflow for Spring AI')
    parser.add_argument('pr_number', help='GitHub PR number to merge')
    parser.add_argument('branch_name', help='Local branch name to merge')
    parser.add_argument('--auto', action='store_true', help='Run without prompts')
    parser.add_argument('--backport', action='store_true', help='Force backport (overrides approval check)')
    parser.add_argument('--dry-run', action='store_true', help='Show commands without executing')
    
    args = parser.parse_args()
    
    # Validate PR number
    if not args.pr_number.isdigit():
        print_error(f"Invalid PR number: {args.pr_number}")
        sys.exit(1)
    
    # Show banner
    print(f"\n{Colors.BOLD}{Colors.CYAN}Spring AI PR Merge Automation{Colors.END}")
    print("=" * 40)
    
    # Execute workflow
    success = merge_workflow(
        pr_number=args.pr_number,
        branch_name=args.branch_name,
        auto=args.auto,
        force_backport=args.backport,
        dry_run=args.dry_run
    )
    
    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Merge workflow completed successfully!{Colors.END}")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Merge workflow failed{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
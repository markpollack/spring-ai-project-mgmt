#!/usr/bin/env python3
"""
Batch process the latest PRs from Spring AI repository

This script:
1. Fetches the most recent open PRs from Spring AI
2. Runs them through batch processing with the new batch mode
3. Generates the orchard report dashboard
"""

import subprocess
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from check_auth import AuthChecker

class Logger:
    @staticmethod
    def info(msg): print(f"\033[34m[INFO]\033[0m {msg}")
    @staticmethod
    def success(msg): print(f"\033[32m[SUCCESS]\033[0m {msg}")
    @staticmethod
    def error(msg): print(f"\033[31m[ERROR]\033[0m {msg}")
    @staticmethod
    def warn(msg): print(f"\033[33m[WARN]\033[0m {msg}")


def fetch_latest_prs(limit: int = 5) -> list:
    """Fetch the latest open PRs from Spring AI repository"""
    Logger.info(f"🔍 Fetching {limit} most recent open PRs from spring-projects/spring-ai...")
    
    try:
        result = subprocess.run([
            "gh", "pr", "list",
            "--repo", "spring-projects/spring-ai",
            "--state", "open",
            "--limit", str(limit),
            "--json", "number,title,author,createdAt"
        ], capture_output=True, text=True, check=True)
        
        prs = json.loads(result.stdout)
        
        Logger.success(f"✅ Found {len(prs)} PRs")
        for pr in prs:
            Logger.info(f"  PR #{pr['number']}: {pr['title'][:60]}... by @{pr['author']['login']}")
        
        return prs
    
    except subprocess.CalledProcessError as e:
        Logger.error(f"Failed to fetch PRs: {e}")
        Logger.error(f"Error output: {e.stderr}")
        return []
    except json.JSONDecodeError as e:
        Logger.error(f"Failed to parse GitHub response: {e}")
        return []


def run_batch_processing(pr_numbers: list, dry_run: bool = False) -> bool:
    """Run batch processing on the given PR numbers"""
    Logger.info(f"\n🚀 Starting batch processing for {len(pr_numbers)} PRs")
    Logger.info(f"📋 PRs: {', '.join(map(str, pr_numbers))}")
    
    if dry_run:
        Logger.warn("🎭 DRY RUN MODE - Simulating execution")
    
    # Prepare command
    cmd = ["python3", "batch_pr_workflow.py"] + list(map(str, pr_numbers))
    
    if dry_run:
        cmd.append("--dry-run")
    
    Logger.info(f"🔧 Command: {' '.join(cmd)}")
    
    try:
        # Run the batch processor
        result = subprocess.run(cmd, check=False)  # Don't check - we want to continue even if some PRs fail
        
        if result.returncode == 0:
            Logger.success("✅ Batch processing completed successfully!")
            return True
        else:
            Logger.warn(f"⚠️  Batch processing completed with some failures (exit code: {result.returncode})")
            return True  # Still consider it a success for report generation
            
    except Exception as e:
        Logger.error(f"❌ Batch processing failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Batch process the latest PRs from Spring AI repository"
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=5,
        help="Number of recent PRs to process (default: 5)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate processing without making changes"
    )
    parser.add_argument(
        "--pr-numbers",
        nargs="+",
        type=int,
        help="Specific PR numbers to process (overrides --count)"
    )
    parser.add_argument(
        "--skip-auth-check",
        action="store_true",
        help="Skip authentication checks (not recommended)"
    )
    
    args = parser.parse_args()
    
    Logger.info("=" * 60)
    Logger.info("🤖 Spring AI Latest PRs Batch Processor")
    Logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    Logger.info("=" * 60)
    
    # Check authentication before proceeding
    if not args.skip_auth_check:
        Logger.info("\n🔐 Checking authentication...")
        checker = AuthChecker()
        if not checker.run_all_checks():
            Logger.error("\n❌ Please fix authentication issues before continuing")
            Logger.info("💡 To skip this check (not recommended): --skip-auth-check")
            return 1
        Logger.info("")  # Empty line for spacing
    
    # Get PR numbers
    if args.pr_numbers:
        # Use provided PR numbers
        pr_numbers = args.pr_numbers
        Logger.info(f"📋 Using provided PR numbers: {pr_numbers}")
    else:
        # Fetch latest PRs
        prs = fetch_latest_prs(args.count)
        if not prs:
            Logger.error("❌ No PRs found to process")
            return 1
        
        pr_numbers = [pr['number'] for pr in prs]
    
    # Run batch processing
    if run_batch_processing(pr_numbers, args.dry_run):
        Logger.success("\n🎉 Batch processing workflow completed!")
        Logger.info("📊 Check the orchard report dashboard for results")
        
        # Show where to find the reports
        script_dir = Path(__file__).parent
        run_dirs = sorted([d for d in (script_dir / "runs").glob("run-*") if d.is_dir()])
        if run_dirs:
            latest_run = run_dirs[-1]
            dashboard = latest_run / "pr_orchard_dashboard.html"
            if dashboard.exists():
                Logger.info(f"🌐 Dashboard: file://{dashboard.absolute()}")
        
        return 0
    else:
        Logger.error("❌ Batch processing failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
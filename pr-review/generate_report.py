#!/usr/bin/env python3
"""
Standalone PR Report Generator

This script generates only the PR analysis report for an already prepared PR.
It's a convenience wrapper around the report-only functionality.
"""

import sys
import argparse
from pathlib import Path

# Import the main workflow classes
from pr_workflow import WorkflowConfig, PRWorkflow, Logger


def main():
    parser = argparse.ArgumentParser(
        description="Generate PR Analysis Report for Spring AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 generate_report.py 3386           # Generate report for PR #3386
  python3 generate_report.py --dry-run 3386 # Preview what would be generated
        """
    )
    
    parser.add_argument('pr_number', help='GitHub PR number to analyze')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    # Validate PR number
    if not args.pr_number.isdigit():
        Logger.error(f"PR number must be a positive integer: {args.pr_number}")
        sys.exit(1)
    
    # Setup configuration
    script_dir = Path(__file__).parent.absolute()
    config = WorkflowConfig(script_dir)
    
    # Create workflow instance and run report generation
    workflow = PRWorkflow(config)
    success = workflow.run_report_only(
        pr_number=args.pr_number,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
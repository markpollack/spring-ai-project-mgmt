#!/usr/bin/env python3
"""
Batch PR Workflow Processing for Spring AI

Processes multiple PRs through the complete PR workflow with comprehensive
monitoring, error handling, and performance tracking.

Features:
- Batch processing of multiple PRs
- Performance monitoring and metrics collection
- Error handling with graceful continuation
- Progress tracking and resumption capability
- Cleanup management between PRs
- Comprehensive summary reporting
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import subprocess

# Import the existing PR workflow
from pr_workflow import PRWorkflow, WorkflowConfig


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
class PRProcessingResult:
    """Results from processing a single PR"""
    pr_number: str
    success: bool
    start_time: datetime
    end_time: datetime
    processing_time: timedelta
    workflow_phase: str  # Which phase it reached
    error_message: Optional[str] = None
    
    # Performance metrics
    prompt_size_bytes: Optional[int] = None
    token_count: Optional[int] = None
    files_analyzed: Optional[int] = None
    
    # Workflow details
    phases_completed: List[str] = None
    report_generated: bool = False
    tests_passed: Optional[bool] = None


@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing"""
    cleanup_between_prs: bool = True
    continue_on_error: bool = True
    max_parallel_jobs: int = 1  # Start with sequential processing
    dry_run: bool = False
    report_only: bool = False
    force_reprocess: bool = False
    
    # Performance monitoring
    collect_metrics: bool = True
    save_logs: bool = True


class PerformanceMonitor:
    """Monitors and tracks performance metrics during batch processing"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        self.metrics_file = log_dir / f"batch-metrics-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        self.metrics = {
            'batch_start_time': datetime.now().isoformat(),
            'batch_end_time': None,
            'total_processing_time': None,
            'prs_processed': [],
            'summary_stats': {},
            'smart_prompt_performance': {},
            'system_info': {
                'python_version': sys.version,
                'working_directory': str(Path.cwd()),
            }
        }
    
    def record_pr_start(self, pr_number: str) -> datetime:
        """Record start of PR processing"""
        start_time = datetime.now()
        Logger.info(f"📊 Starting performance monitoring for PR #{pr_number}")
        return start_time
    
    def record_pr_completion(self, result: PRProcessingResult):
        """Record completion of PR processing"""
        self.metrics['prs_processed'].append(asdict(result))
        Logger.info(f"📊 Recorded metrics for PR #{result.pr_number}: {result.processing_time.total_seconds():.1f}s")
    
    def extract_prompt_metrics(self, pr_number: str) -> Dict[str, Any]:
        """Extract smart prompt metrics from log files"""
        metrics = {}
        try:
            # Look for the Claude prompt log file
            log_file = Path(f"logs/claude-prompt-risk-assessor.txt")
            if log_file.exists():
                # Read the file and extract metrics
                with open(log_file, 'r') as f:
                    content = f.read()
                    
                # Extract prompt size (look for size information in logs)
                if "Prompt size:" in content:
                    # Parse size information from logs
                    for line in content.split('\n'):
                        if "Prompt size:" in line:
                            # Extract bytes from log line
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if "bytes" in part and i > 0:
                                    metrics['prompt_size_bytes'] = int(parts[i-1].replace(',', ''))
                                    break
                        elif "tokens" in line.lower():
                            # Extract token count
                            for part in line.split():
                                if part.replace(',', '').isdigit():
                                    metrics['token_count'] = int(part.replace(',', ''))
                                    break
                
        except Exception as e:
            Logger.warn(f"Could not extract prompt metrics for PR #{pr_number}: {e}")
        
        return metrics
    
    def finalize_batch(self):
        """Finalize batch processing and calculate summary statistics"""
        self.metrics['batch_end_time'] = datetime.now().isoformat()
        
        # Calculate summary stats
        results = self.metrics['prs_processed']
        if results:
            # Convert processing_time strings back to timedelta objects for calculation
            processing_times = []
            for r in results:
                if r.get('processing_time'):
                    # Handle both timedelta objects and duration strings
                    pt = r['processing_time']
                    if isinstance(pt, str):
                        # Parse timedelta string format like "0:00:01.234567"
                        try:
                            time_parts = pt.split(':')
                            if len(time_parts) == 3:
                                hours = int(time_parts[0])
                                minutes = int(time_parts[1])
                                seconds = float(time_parts[2])
                                total_seconds = hours * 3600 + minutes * 60 + seconds
                                processing_times.append(total_seconds)
                        except:
                            continue
                    else:
                        processing_times.append(pt.total_seconds())
            
            self.metrics['summary_stats'] = {
                'total_prs': len(results),
                'successful_prs': len([r for r in results if r['success']]),
                'failed_prs': len([r for r in results if not r['success']]),
                'success_rate': len([r for r in results if r['success']]) / len(results) * 100,
                'avg_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0,
                'total_batch_time': (datetime.fromisoformat(self.metrics['batch_end_time']) - 
                                   datetime.fromisoformat(self.metrics['batch_start_time'])).total_seconds()
            }
            
            # Smart prompt performance analysis
            prompt_sizes = [r.get('prompt_size_bytes') for r in results if r.get('prompt_size_bytes')]
            token_counts = [r.get('token_count') for r in results if r.get('token_count')]
            
            if prompt_sizes:
                self.metrics['smart_prompt_performance'] = {
                    'avg_prompt_size_bytes': sum(prompt_sizes) / len(prompt_sizes),
                    'max_prompt_size_bytes': max(prompt_sizes),
                    'min_prompt_size_bytes': min(prompt_sizes),
                    'avg_token_count': sum(token_counts) / len(token_counts) if token_counts else None,
                    'token_efficiency': 'All PRs stayed under 25K token limit' if all(t < 25000 for t in token_counts if t) else 'Some PRs exceeded optimal token usage'
                }
        
        # Save metrics to file
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
        
        Logger.success(f"📊 Batch metrics saved to: {self.metrics_file}")


class BatchPRWorkflow:
    """Manages batch processing of multiple PRs"""
    
    def __init__(self, config: BatchProcessingConfig):
        self.config = config
        self.script_dir = Path(__file__).parent.absolute()
        self.workflow_config = WorkflowConfig(self.script_dir)
        self.workflow = PRWorkflow(self.workflow_config)
        
        # Setup logging and monitoring
        self.batch_log_dir = self.script_dir / "logs" / f"batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.batch_log_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config.collect_metrics:
            self.monitor = PerformanceMonitor(self.batch_log_dir)
        else:
            self.monitor = None
        
        self.results: List[PRProcessingResult] = []
    
    def process_pr_list(self, pr_numbers: List[str]) -> bool:
        """Process a list of PRs through the complete workflow"""
        Logger.info(f"🚀 Starting batch processing of {len(pr_numbers)} PRs")
        Logger.info(f"📋 PRs to process: {', '.join(pr_numbers)}")
        
        if self.config.dry_run:
            Logger.warn("🎭 DRY RUN MODE - No actual changes will be made")
        
        batch_success = True
        
        for i, pr_number in enumerate(pr_numbers, 1):
            Logger.info(f"\n{'='*60}")
            Logger.info(f"📋 Processing PR #{pr_number} ({i}/{len(pr_numbers)})")
            Logger.info(f"{'='*60}")
            
            # Process single PR
            result = self._process_single_pr(pr_number)
            self.results.append(result)
            
            if not result.success:
                batch_success = False
                if not self.config.continue_on_error:
                    Logger.error(f"❌ Stopping batch processing due to failure in PR #{pr_number}")
                    break
                else:
                    Logger.warn(f"⚠️  PR #{pr_number} failed, continuing with next PR...")
            
            # Cleanup between PRs if requested
            if self.config.cleanup_between_prs and i < len(pr_numbers):
                self._cleanup_between_prs(pr_number)
        
        # Generate batch summary
        self._generate_batch_summary()
        
        if self.monitor:
            self.monitor.finalize_batch()
        
        Logger.info(f"\n🎉 Batch processing completed!")
        Logger.info(f"📊 Processed {len(self.results)} PRs")
        Logger.info(f"✅ Success rate: {len([r for r in self.results if r.success])}/{len(self.results)}")
        
        return batch_success
    
    def _process_single_pr(self, pr_number: str) -> PRProcessingResult:
        """Process a single PR and return results"""
        start_time = datetime.now()
        if self.monitor:
            start_time = self.monitor.record_pr_start(pr_number)
        
        result = PRProcessingResult(
            pr_number=pr_number,
            success=False,
            start_time=start_time,
            end_time=datetime.now(),
            processing_time=timedelta(0),
            workflow_phase="initialization",
            phases_completed=[]
        )
        
        try:
            # Determine which workflow to run based on config
            if self.config.report_only:
                success = self.workflow.run_report_only(pr_number, self.config.dry_run)
                result.workflow_phase = "report_generation"
                result.phases_completed = ["report_generation"]
            else:
                # Run complete workflow
                success = self.workflow.run_complete_workflow(
                    pr_number=pr_number,
                    skip_squash=False,
                    skip_compile=False,
                    skip_tests=False,
                    auto_resolve=True,  # Use intelligent conflict resolution
                    force=False,
                    generate_report=True,
                    dry_run=self.config.dry_run
                )
                result.workflow_phase = "complete_workflow"
                result.phases_completed = ["setup", "checkout", "build", "squash", "rebase", "report", "tests"]
            
            result.success = success
            
            # Extract performance metrics if available
            if self.monitor and not self.config.dry_run:
                metrics = self.monitor.extract_prompt_metrics(pr_number)
                result.prompt_size_bytes = metrics.get('prompt_size_bytes')
                result.token_count = metrics.get('token_count')
            
            # Check if report was generated
            report_file = self.script_dir / "reports" / f"review-pr-{pr_number}.md"
            result.report_generated = report_file.exists()
            
        except Exception as e:
            result.error_message = str(e)
            Logger.error(f"❌ Error processing PR #{pr_number}: {e}")
        
        finally:
            result.end_time = datetime.now()
            result.processing_time = result.end_time - result.start_time
            
            if self.monitor:
                self.monitor.record_pr_completion(result)
        
        return result
    
    def _cleanup_between_prs(self, pr_number: str):
        """Cleanup state between PR processing"""
        Logger.info(f"🧹 Cleaning up after PR #{pr_number}")
        
        try:
            # Run cleanup for the current PR
            if not self.config.dry_run:
                self.workflow.cleanup_pr_workspace(pr_number, cleanup_mode='light')
            else:
                Logger.info("🎭 DRY RUN: Would run cleanup")
                
        except Exception as e:
            Logger.warn(f"⚠️  Cleanup warning for PR #{pr_number}: {e}")
    
    def _generate_batch_summary(self):
        """Generate comprehensive batch processing summary"""
        summary_file = self.batch_log_dir / "batch-summary.md"
        
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        summary_content = f"""# Batch PR Processing Summary

## Overview
- **Batch Start Time**: {self.results[0].start_time.strftime('%Y-%m-%d %H:%M:%S') if self.results else 'N/A'}
- **Batch End Time**: {self.results[-1].end_time.strftime('%Y-%m-%d %H:%M:%S') if self.results else 'N/A'}
- **Total PRs Processed**: {len(self.results)}
- **Successful**: {len(successful)}
- **Failed**: {len(failed)}
- **Success Rate**: {len(successful) / len(self.results) * 100:.1f}% if {len(self.results)} > 0 else 0%

## Processing Results

### ✅ Successful PRs
"""
        
        for result in successful:
            summary_content += f"""
- **PR #{result.pr_number}**: {result.processing_time.total_seconds():.1f}s
  - Report Generated: {'✅' if result.report_generated else '❌'}
  - Prompt Size: {result.prompt_size_bytes or 'N/A'} bytes
  - Token Count: {result.token_count or 'N/A'}
"""
        
        if failed:
            summary_content += f"""
### ❌ Failed PRs
"""
            for result in failed:
                summary_content += f"""
- **PR #{result.pr_number}**: Failed at {result.workflow_phase}
  - Processing Time: {result.processing_time.total_seconds():.1f}s
  - Error: {result.error_message or 'Unknown error'}
"""
        
        # Performance analysis
        if successful:
            avg_time = sum(r.processing_time.total_seconds() for r in successful) / len(successful)
            prompt_sizes = [r.prompt_size_bytes for r in successful if r.prompt_size_bytes]
            token_counts = [r.token_count for r in successful if r.token_count]
            
            summary_content += f"""
## Performance Analysis

### Processing Times
- **Average Processing Time**: {avg_time:.1f} seconds
- **Fastest PR**: {min(r.processing_time.total_seconds() for r in successful):.1f}s
- **Slowest PR**: {max(r.processing_time.total_seconds() for r in successful):.1f}s

### Smart Prompt Optimization
"""
            if prompt_sizes:
                summary_content += f"""- **Average Prompt Size**: {sum(prompt_sizes) / len(prompt_sizes):.0f} bytes
- **Largest Prompt**: {max(prompt_sizes):,} bytes  
- **Smallest Prompt**: {min(prompt_sizes):,} bytes
"""
            
            if token_counts:
                summary_content += f"""- **Average Token Count**: {sum(token_counts) / len(token_counts):.0f}
- **Token Efficiency**: {'All under 25K limit ✅' if all(t < 25000 for t in token_counts) else 'Some exceeded optimal usage ⚠️'}
"""
        
        summary_content += f"""
## Configuration Used
- **Cleanup Between PRs**: {self.config.cleanup_between_prs}
- **Continue on Error**: {self.config.continue_on_error}
- **Dry Run Mode**: {self.config.dry_run}
- **Report Only Mode**: {self.config.report_only}

## Generated Reports
"""
        
        for result in self.results:
            if result.report_generated:
                summary_content += f"- [PR #{result.pr_number} Report](../reports/review-pr-{result.pr_number}.md)\n"
        
        summary_content += f"""
---
*Generated by batch_pr_workflow.py on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(summary_file, 'w') as f:
            f.write(summary_content)
        
        Logger.success(f"📋 Batch summary generated: {summary_file}")


def main():
    """Main entry point for batch PR processing"""
    parser = argparse.ArgumentParser(
        description="Batch PR Workflow Processing for Spring AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 batch_pr_workflow.py 3922 3921 3920                    # Process 3 PRs with full workflow
  python3 batch_pr_workflow.py --dry-run 3922 3921 3920          # Preview what would happen
  python3 batch_pr_workflow.py --report-only 3922 3921 3920      # Generate reports only
  python3 batch_pr_workflow.py --no-cleanup 3922 3921 3920       # Skip cleanup between PRs
  python3 batch_pr_workflow.py --stop-on-error 3922 3921 3920    # Stop on first error
        """
    )
    
    parser.add_argument('pr_numbers', nargs='+', help='GitHub PR numbers to process')
    parser.add_argument('--dry-run', action='store_true', help='Preview the workflow without executing')
    parser.add_argument('--report-only', action='store_true', help='Generate only analysis reports (assumes PRs already prepared)')
    parser.add_argument('--no-cleanup', action='store_true', help='Skip cleanup between PRs')
    parser.add_argument('--stop-on-error', action='store_true', help='Stop processing on first error (default: continue)')
    parser.add_argument('--force-reprocess', action='store_true', help='Force reprocessing of PRs that already have reports')
    parser.add_argument('--no-metrics', action='store_true', help='Disable performance metrics collection')
    
    args = parser.parse_args()
    
    # Validate PR numbers
    for pr_num in args.pr_numbers:
        if not pr_num.isdigit():
            Logger.error(f"Invalid PR number: {pr_num}")
            sys.exit(1)
    
    # Setup configuration
    config = BatchProcessingConfig(
        cleanup_between_prs=not args.no_cleanup,
        continue_on_error=not args.stop_on_error,
        dry_run=args.dry_run,
        report_only=args.report_only,
        force_reprocess=args.force_reprocess,
        collect_metrics=not args.no_metrics
    )
    
    # Create batch processor
    batch_processor = BatchPRWorkflow(config)
    
    # Process the PRs
    success = batch_processor.process_pr_list(args.pr_numbers)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
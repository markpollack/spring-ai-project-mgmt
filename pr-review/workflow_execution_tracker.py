#!/usr/bin/env python3
"""
Workflow Execution Tracker for PR Review System

Tracks and records the execution of each workflow step, including:
- Success/failure status
- Execution time
- Error messages
- AI interventions
- Test results
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum


class StepStatus(Enum):
    """Status of a workflow step"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"
    WARNING = "warning"  # Completed with warnings


@dataclass
class WorkflowStep:
    """Represents a single workflow step execution"""
    name: str
    status: str  # Using string for JSON serialization
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    sub_steps: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "details": self.details,
            "sub_steps": self.sub_steps
        }


class WorkflowExecutionTracker:
    """Tracks workflow execution progress and results"""
    
    def __init__(self, pr_number: str, context_dir: Path):
        self.pr_number = pr_number
        self.context_dir = context_dir
        self.pr_context_dir = context_dir / f"pr-{pr_number}"
        self.pr_context_dir.mkdir(parents=True, exist_ok=True)
        
        self.execution_file = self.pr_context_dir / "workflow-execution.json"
        self.steps: Dict[str, WorkflowStep] = {}
        self.workflow_start_time = None
        self.workflow_end_time = None
        
        # Load existing execution data if available
        self._load_existing_data()
    
    def _load_existing_data(self):
        """Load existing execution data if file exists"""
        if self.execution_file.exists():
            try:
                with open(self.execution_file, 'r') as f:
                    data = json.load(f)
                    for step_data in data.get("steps", []):
                        step = WorkflowStep(**step_data)
                        self.steps[step.name] = step
                    self.workflow_start_time = data.get("workflow_start_time")
                    self.workflow_end_time = data.get("workflow_end_time")
            except Exception as e:
                print(f"Warning: Could not load existing execution data: {e}")
    
    def start_workflow(self):
        """Mark the workflow as started"""
        self.workflow_start_time = datetime.now().isoformat()
        self.save()
    
    def end_workflow(self, success: bool = True):
        """Mark the workflow as completed"""
        self.workflow_end_time = datetime.now().isoformat()
        self.save()
    
    def start_step(self, name: str, details: Optional[Dict[str, Any]] = None):
        """Start tracking a workflow step"""
        step = WorkflowStep(
            name=name,
            status=StepStatus.RUNNING.value,
            start_time=datetime.now().isoformat(),
            details=details or {}
        )
        self.steps[name] = step
        self.save()
        return step
    
    def end_step(self, name: str, success: bool = True, error_message: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """End tracking a workflow step"""
        if name not in self.steps:
            # Create step if it doesn't exist (for edge cases)
            self.steps[name] = WorkflowStep(name=name, status=StepStatus.PENDING.value)
        
        step = self.steps[name]
        step.end_time = datetime.now().isoformat()
        
        # Calculate duration if start_time exists
        if step.start_time:
            start = datetime.fromisoformat(step.start_time)
            end = datetime.fromisoformat(step.end_time)
            step.duration_seconds = (end - start).total_seconds()
        
        # Set status
        if success:
            step.status = StepStatus.SUCCESS.value
        else:
            step.status = StepStatus.FAILURE.value
        
        # Add error message if provided
        if error_message:
            step.error_message = error_message
        
        # Update details
        if details:
            step.details.update(details)
        
        self.save()
        return step
    
    def skip_step(self, name: str, reason: Optional[str] = None):
        """Mark a step as skipped"""
        step = WorkflowStep(
            name=name,
            status=StepStatus.SKIPPED.value,
            details={"reason": reason} if reason else {}
        )
        self.steps[name] = step
        self.save()
        return step
    
    def add_sub_step(self, parent_name: str, sub_step_data: Dict[str, Any]):
        """Add a sub-step to a parent step"""
        if parent_name in self.steps:
            self.steps[parent_name].sub_steps.append(sub_step_data)
            self.save()
    
    def update_step_details(self, name: str, details: Dict[str, Any]):
        """Update step details"""
        if name in self.steps:
            self.steps[name].details.update(details)
            self.save()
    
    def record_test_results(self, total_tests: int, passed: int, failed: int, 
                          failed_tests: Optional[List[str]] = None):
        """Record test execution results"""
        test_step = self.steps.get("test_execution")
        if not test_step:
            test_step = self.start_step("test_execution")
        
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        test_step.details = {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "success_rate": f"{success_rate:.1f}%",
            "failed_tests": failed_tests or []
        }
        
        # Set status based on results
        if failed == 0:
            test_step.status = StepStatus.SUCCESS.value
        elif passed > 0:
            test_step.status = StepStatus.WARNING.value
        else:
            test_step.status = StepStatus.FAILURE.value
        
        self.save()
    
    def record_build_attempt(self, command: str, success: bool, output_file: Optional[str] = None):
        """Record a build/compilation attempt"""
        if "compilation" not in self.steps:
            self.start_step("compilation")
        
        build_attempt = {
            "command": command,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "output_file": output_file
        }
        
        self.add_sub_step("compilation", build_attempt)
        
        # Update overall compilation status
        if success:
            self.steps["compilation"].status = StepStatus.SUCCESS.value
    
    def record_squash_operation(self, original_commits: int, squashed_to: int = 1):
        """Record squash operation details"""
        self.update_step_details("squash_commits", {
            "original_commits": original_commits,
            "squashed_to": squashed_to,
            "commits_reduced": original_commits - squashed_to
        })
    
    def record_rebase_operation(self, conflicts: bool = False, resolved: bool = False):
        """Record rebase operation details"""
        self.update_step_details("rebase", {
            "had_conflicts": conflicts,
            "conflicts_resolved": resolved,
            "auto_resolved": resolved and conflicts
        })
    
    def record_ai_intervention(self, step_name: str, intervention_type: str, 
                             success: bool, details: Optional[str] = None):
        """Record an AI intervention in the workflow"""
        intervention = {
            "type": intervention_type,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if step_name not in self.steps:
            self.start_step(step_name)
        
        if "ai_interventions" not in self.steps[step_name].details:
            self.steps[step_name].details["ai_interventions"] = []
        
        self.steps[step_name].details["ai_interventions"].append(intervention)
        self.save()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow execution"""
        total_steps = len(self.steps)
        successful_steps = sum(1 for s in self.steps.values() if s.status == StepStatus.SUCCESS.value)
        failed_steps = sum(1 for s in self.steps.values() if s.status == StepStatus.FAILURE.value)
        skipped_steps = sum(1 for s in self.steps.values() if s.status == StepStatus.SKIPPED.value)
        warning_steps = sum(1 for s in self.steps.values() if s.status == StepStatus.WARNING.value)
        
        # Calculate total duration
        total_duration = None
        if self.workflow_start_time and self.workflow_end_time:
            start = datetime.fromisoformat(self.workflow_start_time)
            end = datetime.fromisoformat(self.workflow_end_time)
            total_duration = (end - start).total_seconds()
        
        return {
            "pr_number": self.pr_number,
            "workflow_start_time": self.workflow_start_time,
            "workflow_end_time": self.workflow_end_time,
            "total_duration_seconds": total_duration,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "warning_steps": warning_steps,
            "skipped_steps": skipped_steps,
            "success_rate": f"{(successful_steps / total_steps * 100):.1f}%" if total_steps > 0 else "0%"
        }
    
    def save(self):
        """Save execution data to JSON file"""
        data = {
            "pr_number": self.pr_number,
            "workflow_start_time": self.workflow_start_time,
            "workflow_end_time": self.workflow_end_time,
            "summary": self.get_summary(),
            "steps": [step.to_dict() for step in self.steps.values()],
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.execution_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self) -> Dict[str, Any]:
        """Load and return the execution data"""
        if self.execution_file.exists():
            with open(self.execution_file, 'r') as f:
                return json.load(f)
        return {}
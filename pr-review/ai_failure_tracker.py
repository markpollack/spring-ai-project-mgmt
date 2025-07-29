#!/usr/bin/env python3
"""
AI Assessment Failure Tracker

Tracks and analyzes AI component failures across batch processing runs
to help debug and improve AI assessment reliability.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict, Counter

class AIFailureTracker:
    """Tracks and analyzes AI assessment failures for debugging"""
    
    def __init__(self, logs_dir: Path = None):
        self.logs_dir = logs_dir or Path(__file__).parent / "logs"
        self.failure_log = self.logs_dir / "ai_assessment_failures.jsonl"
    
    def log_failure(self, pr_number: str, component: str, error: str, response: str = ""):
        """Log an AI assessment failure"""
        self.logs_dir.mkdir(exist_ok=True)
        
        failure_entry = {
            "timestamp": datetime.now().isoformat(),
            "pr_number": pr_number,
            "component": component,
            "error": error,
            "response_length": len(response) if response else 0,
            "response_preview": response[:200] if response else "No response"
        }
        
        with open(self.failure_log, 'a') as f:
            f.write(json.dumps(failure_entry) + '\n')
    
    def get_failures(self, pr_number: str = None) -> List[Dict]:
        """Get failures for a specific PR or all failures"""
        if not self.failure_log.exists():
            return []
        
        failures = []
        with open(self.failure_log, 'r') as f:
            for line in f:
                if line.strip():
                    failure = json.loads(line.strip())
                    if pr_number is None or failure.get('pr_number') == pr_number:
                        failures.append(failure)
        
        return failures
    
    def analyze_failures(self) -> Dict[str, Any]:
        """Analyze failure patterns for debugging insights"""
        failures = self.get_failures()
        
        if not failures:
            return {"message": "No AI assessment failures logged"}
        
        # Group by component
        by_component = defaultdict(list)
        for failure in failures:
            by_component[failure['component']].append(failure)
        
        # Common error patterns
        error_patterns = Counter(failure['error'] for failure in failures)
        
        # Recent failures (last 24 hours)
        recent_cutoff = datetime.now().timestamp() - 86400  # 24 hours
        recent_failures = [
            f for f in failures 
            if datetime.fromisoformat(f['timestamp']).timestamp() > recent_cutoff
        ]
        
        analysis = {
            "total_failures": len(failures),
            "recent_failures_24h": len(recent_failures),
            "components_affected": dict(by_component.keys()),
            "failure_counts_by_component": {
                comp: len(fails) for comp, fails in by_component.items()
            },
            "common_error_patterns": dict(error_patterns.most_common(5)),
            "recent_prs_affected": list(set(f['pr_number'] for f in recent_failures)),
            "recommendations": self._generate_recommendations(by_component, error_patterns)
        }
        
        return analysis
    
    def _generate_recommendations(self, by_component: Dict, error_patterns: Counter) -> List[str]:
        """Generate debugging recommendations based on failure patterns"""
        recommendations = []
        
        # Component-specific recommendations
        if 'solution_assessment' in by_component:
            recommendations.append("Solution assessment failures detected - check Claude Code timeout and prompt complexity")
        
        if 'ai_risk_assessment' in by_component:
            recommendations.append("Risk assessment failures - verify file access and prompt structure")
        
        # Error pattern recommendations
        for error, count in error_patterns.most_common(3):
            if "Execution error" in error:
                recommendations.append(f"Frequent 'Execution error' ({count}x) - investigate Claude Code CLI issues")
            elif "JSON" in error:
                recommendations.append(f"JSON parsing errors ({count}x) - review response format expectations")
            elif "timeout" in error.lower():
                recommendations.append(f"Timeout errors ({count}x) - consider increasing timeout limits")
        
        return recommendations
    
    def generate_failure_report(self) -> str:
        """Generate a detailed failure report for debugging"""
        analysis = self.analyze_failures()
        
        if "message" in analysis:
            return analysis["message"]
        
        report = f"""# AI Assessment Failure Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total Failures**: {analysis['total_failures']}
- **Recent Failures (24h)**: {analysis['recent_failures_24h']}
- **Components Affected**: {len(analysis['components_affected'])}
- **Recent PRs Affected**: {len(analysis['recent_prs_affected'])}

## Failure Breakdown by Component
"""
        
        for component, count in analysis['failure_counts_by_component'].items():
            report += f"- **{component}**: {count} failures\n"
        
        report += f"\n## Common Error Patterns\n"
        for error, count in analysis['common_error_patterns'].items():
            report += f"- `{error}`: {count} occurrences\n"
        
        if analysis['recent_prs_affected']:
            report += f"\n## Recent PRs Affected\n"
            for pr in analysis['recent_prs_affected']:
                report += f"- PR #{pr}\n"
        
        if analysis['recommendations']:
            report += f"\n## Debugging Recommendations\n"
            for i, rec in enumerate(analysis['recommendations'], 1):
                report += f"{i}. {rec}\n"
        
        return report


def main():
    """CLI interface for failure analysis"""
    import sys
    
    tracker = AIFailureTracker()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--analyze":
            analysis = tracker.analyze_failures()
            print(json.dumps(analysis, indent=2))
        elif sys.argv[1] == "--report":
            print(tracker.generate_failure_report())
        elif sys.argv[1] == "--pr" and len(sys.argv) > 2:
            pr_failures = tracker.get_failures(sys.argv[2])
            print(f"Failures for PR #{sys.argv[2]}:")
            for failure in pr_failures:
                print(f"  - {failure['component']}: {failure['error']}")
    else:
        print("Usage:")
        print("  python3 ai_failure_tracker.py --analyze    # JSON analysis")
        print("  python3 ai_failure_tracker.py --report     # Human-readable report")
        print("  python3 ai_failure_tracker.py --pr 3927    # Failures for specific PR")


if __name__ == "__main__":
    main()
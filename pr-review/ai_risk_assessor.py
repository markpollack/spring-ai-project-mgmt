#!/usr/bin/env python3
"""
AI-Powered Risk Assessment for Spring AI PRs

Uses Claude Code to analyze PR changes and identify genuine security, performance, 
and maintainability risks while avoiding false positives from legitimate test patterns.

Usage:
    python3 ai_risk_assessor.py <pr_number>
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

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
class RiskAssessmentResult:
    """Results from AI-powered risk assessment"""
    critical_issues: List[Dict[str, Any]]
    important_issues: List[Dict[str, Any]]
    risk_factors: List[str]
    positive_findings: List[str]
    overall_risk_level: str
    risk_summary: str
    assessment_timestamp: str


class AIRiskAssessor:
    """AI-powered risk assessment using Claude Code"""
    
    def __init__(self, working_dir: Path, spring_ai_dir: Path):
        self.working_dir = working_dir
        self.spring_ai_dir = spring_ai_dir
        self.context_dir = working_dir / "context"
    
    def check_claude_available(self) -> bool:
        """Check if Claude Code CLI is available"""
        try:
            subprocess.run(['claude', '--version'], capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def load_pr_context_data(self, pr_number: str) -> Dict[str, Any]:
        """Load PR context data for risk assessment"""
        pr_context_dir = self.context_dir / f"pr-{pr_number}"
        
        if not pr_context_dir.exists():
            Logger.error(f"No context data found for PR #{pr_number}")
            return {}
        
        # Load basic PR data
        context_data = {}
        
        try:
            # Load PR metadata
            pr_data_file = pr_context_dir / "pr-data.json"
            if pr_data_file.exists():
                with open(pr_data_file, 'r') as f:
                    context_data['pr_data'] = json.load(f)
            
            # Load file changes
            file_changes_file = pr_context_dir / "file-changes.json"
            if file_changes_file.exists():
                with open(file_changes_file, 'r') as f:
                    context_data['file_changes'] = json.load(f)
            
            # Load conversation analysis if available
            conv_analysis_file = pr_context_dir / "ai-conversation-analysis.json"
            if conv_analysis_file.exists():
                with open(conv_analysis_file, 'r') as f:
                    context_data['conversation_analysis'] = json.load(f)
            
            return context_data
            
        except Exception as e:
            Logger.warn(f"Error loading context data: {e}")
            return {}
    
    def build_file_changes_detail(self, file_changes: List[Dict[str, Any]]) -> str:
        """Build simple file changes summary for the prompt"""
        if not file_changes:
            return "*No file changes data available*"
        
        details = []
        for change in file_changes[:10]:  # Simple limit to first 10 files
            filename = change.get('filename', 'Unknown')
            status = change.get('status', 'unknown')
            additions = change.get('additions', 0)
            deletions = change.get('deletions', 0)
            
            details.append(f"**{filename}** ({status})")
            details.append(f"  - +{additions}/-{deletions} lines")
            details.append("")
        
        if len(file_changes) > 10:
            details.append(f"... and {len(file_changes) - 10} more files")
        
        return '\n'.join(details)
    
    def create_risk_assessment_prompt(self, pr_number: str, context_data: Dict[str, Any]) -> str:
        """Create the AI prompt for risk assessment"""
        
        # Load the prompt template
        template_path = self.working_dir / "templates" / "ai_risk_assessment_prompt.md"
        if not template_path.exists():
            Logger.error(f"AI risk assessment template not found: {template_path}")
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Extract data from context
        pr_data = context_data.get('pr_data', {})
        file_changes = context_data.get('file_changes', [])
        conversation_analysis = context_data.get('conversation_analysis', {})
        
        # Build template variables
        template_vars = {
            'pr_number': pr_number,
            'pr_title': pr_data.get('title', 'Unknown'),
            'pr_author': pr_data.get('author', 'Unknown'),
            'problem_summary': conversation_analysis.get('problem_summary', 'Not available'),
            'total_files_changed': len(file_changes),
            'total_lines_added': sum(f.get('additions', 0) for f in file_changes),
            'total_lines_removed': sum(f.get('deletions', 0) for f in file_changes),
            'file_changes_detail': self.build_file_changes_detail(file_changes),
            'key_requirements_list': self._format_list_items(conversation_analysis.get('key_requirements', [])),
            'outstanding_concerns_list': self._format_list_items(conversation_analysis.get('outstanding_concerns', []))
        }
        
        # Format the template
        try:
            formatted_prompt = template.format(**template_vars)
            return formatted_prompt
        except KeyError as e:
            Logger.error(f"Template formatting error - missing variable: {e}")
            raise
    
    def _format_list_items(self, items: List[str]) -> str:
        """Format list items for the prompt"""
        if not items:
            return "*None identified*"
        return '\n'.join(f"- {item}" for item in items[:5])  # Limit to 5 items
    
    def run_ai_risk_assessment(self, pr_number: str) -> Optional[RiskAssessmentResult]:
        """Run AI-powered risk assessment using Claude Code"""
        
        Logger.info(f"🤖 Running AI risk assessment for PR #{pr_number}")
        
        # Check Claude Code availability
        if not self.check_claude_available():
            Logger.error("Claude Code CLI not available for AI risk assessment")
            return None
        
        # Load context data
        context_data = self.load_pr_context_data(pr_number)
        if not context_data:
            Logger.error("No context data available for risk assessment")
            return None
        
        # Show basic context stats
        file_changes = context_data.get('file_changes', [])
        Logger.info(f"📊 Loaded {len(file_changes)} files for analysis")
        
        try:
            # Create the AI prompt
            risk_prompt = self.create_risk_assessment_prompt(pr_number, context_data)
            
            # Create temporary file for the prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as prompt_file:
                prompt_file.write(risk_prompt)
                prompt_file_path = prompt_file.name
            
            try:
                Logger.info("🧠 Starting Claude Code AI analysis...")
                
                # Call Claude Code to perform risk assessment - exact same pattern as pr_workflow.py
                with open(prompt_file_path, 'r') as stdin:
                    result = subprocess.run(
                        ['claude', '--print'],
                        stdin=stdin,
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5 minute timeout
                        check=False
                    )
                
                if result.returncode == 0 and result.stdout.strip():
                    response_content = result.stdout.strip()
                    response_size_kb = len(response_content) / 1024
                    Logger.success(f"✅ Claude Code returned response ({response_size_kb:.1f}KB)")
                    
                    # Parse JSON response
                    Logger.info("🔍 Parsing AI response...")
                    try:
                        # Extract JSON from response (handle potential markdown code blocks)
                        json_start = response_content.find('{')
                        json_end = response_content.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            Logger.info(f"📋 Found JSON content at positions {json_start}-{json_end}")
                            json_content = response_content[json_start:json_end]
                            assessment_data = json.loads(json_content)
                            
                            # Log what we found
                            critical_count = len(assessment_data.get('critical_issues', []))
                            important_count = len(assessment_data.get('important_issues', []))
                            risk_count = len(assessment_data.get('risk_factors', []))
                            positive_count = len(assessment_data.get('positive_findings', []))
                            
                            Logger.info(f"📊 Parsed assessment: {critical_count} critical, {important_count} important, {risk_count} risk factors, {positive_count} positive")
                            
                            # Create result object
                            result_obj = RiskAssessmentResult(
                                critical_issues=assessment_data.get('critical_issues', []),
                                important_issues=assessment_data.get('important_issues', []),
                                risk_factors=assessment_data.get('risk_factors', []),
                                positive_findings=assessment_data.get('positive_findings', []),
                                overall_risk_level=assessment_data.get('overall_risk_level', 'UNKNOWN'),
                                risk_summary=assessment_data.get('risk_summary', 'No summary available'),
                                assessment_timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            )
                            
                            Logger.success("✅ AI risk assessment completed successfully")
                            return result_obj
                        else:
                            Logger.error("❌ Could not extract JSON from AI response")
                            Logger.error(f"Response preview: {response_content[:200]}...")
                            return None
                            
                    except json.JSONDecodeError as e:
                        Logger.error(f"❌ Failed to parse AI response as JSON: {e}")
                        Logger.error(f"Response content preview: {response_content[:500]}...")
                        return None
                else:
                    Logger.error(f"❌ Claude Code failed with return code: {result.returncode}")
                    if result.stderr:
                        Logger.error(f"Claude Code error: {result.stderr.strip()}")
                    if result.stdout:
                        Logger.error(f"Claude Code output: {result.stdout[:200]}...")
                    return None
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(prompt_file_path)
                except OSError:
                    pass
                    
        except Exception as e:
            Logger.error(f"Error during AI risk assessment: {e}")
            return None
    
    def save_assessment_result(self, pr_number: str, result: RiskAssessmentResult) -> bool:
        """Save assessment result to context directory"""
        try:
            pr_context_dir = self.context_dir / f"pr-{pr_number}"
            pr_context_dir.mkdir(exist_ok=True)
            
            # Convert to dictionary for JSON serialization
            result_dict = {
                'critical_issues': result.critical_issues,
                'important_issues': result.important_issues,
                'risk_factors': result.risk_factors,
                'positive_findings': result.positive_findings,
                'overall_risk_level': result.overall_risk_level,
                'risk_summary': result.risk_summary,
                'assessment_timestamp': result.assessment_timestamp
            }
            
            # Save to JSON file
            assessment_file = pr_context_dir / "ai-risk-assessment.json"
            with open(assessment_file, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            
            Logger.success(f"💾 Risk assessment results saved: {assessment_file}")
            return True
            
        except Exception as e:
            Logger.error(f"Error saving assessment result: {e}")
            return False


def main():
    """Command-line interface for AI risk assessment"""
    if len(sys.argv) < 2:
        print("Usage: python3 ai_risk_assessor.py <pr_number>")
        print("\nExamples:")
        print("  python3 ai_risk_assessor.py 3386")
        sys.exit(1)
    
    pr_number = sys.argv[1]
    
    # Use current directory setup (same as other scripts)
    working_dir = Path(__file__).parent
    spring_ai_dir = working_dir / "spring-ai"
    
    assessor = AIRiskAssessor(working_dir, spring_ai_dir)
    
    # Run AI risk assessment
    result = assessor.run_ai_risk_assessment(pr_number)
    
    if result:
        # Save results
        assessor.save_assessment_result(pr_number, result)
        
        # Print summary
        print(f"\n✅ AI Risk Assessment completed for PR #{pr_number}")
        print(f"📊 Overall Risk Level: {result.overall_risk_level}")
        print(f"🔍 Critical Issues: {len(result.critical_issues)}")
        print(f"⚠️  Important Issues: {len(result.important_issues)}")
        print(f"📋 Risk Factors: {len(result.risk_factors)}")
        print(f"✨ Positive Findings: {len(result.positive_findings)}")
        print(f"\n📝 Summary: {result.risk_summary}")
        
        sys.exit(0)
    else:
        print(f"\n❌ AI Risk Assessment failed for PR #{pr_number}")
        sys.exit(1)


if __name__ == "__main__":
    main()
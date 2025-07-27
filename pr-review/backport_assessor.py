#!/usr/bin/env python3
"""
AI-Powered Backport Candidate Assessment for Spring AI PRs

Evaluates PRs to determine if they are suitable for backporting to the Spring AI 1.0.x maintenance branch.
Uses Claude Code to analyze PR changes, API impact, and compatibility with established backporting criteria.

Usage:
    python3 backport_assessor.py <pr_number>
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
from claude_code_wrapper import ClaudeCodeWrapper

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

try:
    from github_utils import GitHubUtils
except ImportError:
    Logger.warn("GitHub utilities not available - branch management disabled")
    GitHubUtils = None


@dataclass
class BackportAssessmentResult:
    """Results from AI-powered backport candidate assessment"""
    decision: str  # "APPROVE" or "REJECT"
    classification: str  # "Bug Fix", "Feature", "Documentation", etc.
    scope: str  # Brief description of what changed
    api_impact: str  # "None", "Minor", "Major"
    risk_level: str  # "Low", "Medium", "High"
    files_changed_count: int
    dependencies_changed: bool
    key_findings: List[str]
    reasoning: str
    recommendations: str
    assessment_timestamp: str
    analysis_details: Dict[str, Any]


class BackportAssessor:
    """AI-powered backport candidate assessment for Spring AI PRs"""
    
    def __init__(self, working_dir: Path, spring_ai_dir: Path):
        """Initialize the backport assessor
        
        Args:
            working_dir: Directory containing scripts and templates
            spring_ai_dir: Path to Spring AI repository clone
        """
        self.working_dir = working_dir
        self.spring_ai_dir = spring_ai_dir
        self.context_dir = working_dir / "context"
        self.logs_dir = working_dir / "logs"
        self.template_path = working_dir / "templates" / "backport-candidate.md"
        
        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        
        # Initialize Claude Code wrapper
        self.claude = ClaudeCodeWrapper()
        
        # Initialize GitHub utilities if available
        self.github_utils = None
        if GitHubUtils:
            try:
                self.github_utils = GitHubUtils(working_dir, "spring-projects/spring-ai")
            except Exception as e:
                Logger.warn(f"GitHub utilities initialization failed: {e}")
    
    def run_backport_assessment(self, pr_number: str) -> Optional[BackportAssessmentResult]:
        """Run complete backport candidate assessment for a PR
        
        Args:
            pr_number: GitHub PR number to assess
            
        Returns:
            BackportAssessmentResult if successful, None if failed
        """
        Logger.info(f"🔍 Starting backport candidate assessment for PR #{pr_number}")
        
        # Validate input
        if not pr_number.isdigit():
            Logger.error(f"Invalid PR number: {pr_number}")
            return None
        
        # Check if Claude Code is available
        if not self.claude.is_available():
            Logger.error("❌ Claude Code CLI not available for backport assessment")
            return None
        
        # Check if backport template exists
        if not self.template_path.exists():
            Logger.error(f"❌ Backport assessment template not found: {self.template_path}")
            return None
        
        try:
            # Ensure we're working with the correct PR branch
            if not self._ensure_correct_branch(pr_number):
                Logger.error(f"❌ Could not switch to correct branch for PR #{pr_number}")
                return None
            
            # Collect PR context data
            context_data = self._collect_pr_context(pr_number)
            if not context_data:
                Logger.error("❌ Failed to collect PR context data")
                return None
            
            # Build prompt for AI analysis
            prompt_file = self._build_assessment_prompt(pr_number, context_data)
            if not prompt_file:
                Logger.error("❌ Failed to build assessment prompt")
                return None
            
            # Run AI analysis
            ai_result = self._run_ai_analysis(pr_number, prompt_file)
            if not ai_result:
                Logger.error("❌ AI analysis failed")
                return None
            
            # Parse and validate results
            assessment_result = self._parse_assessment_result(pr_number, ai_result, context_data)
            if not assessment_result:
                Logger.error("❌ Failed to parse assessment results")
                return None
            
            # Save assessment result
            self._save_assessment_result(pr_number, assessment_result)
            
            Logger.success(f"✅ Backport assessment completed for PR #{pr_number}")
            Logger.info(f"🎯 Decision: {assessment_result.decision}")
            Logger.info(f"📊 Classification: {assessment_result.classification}")
            Logger.info(f"⚠️  Risk Level: {assessment_result.risk_level}")
            
            return assessment_result
            
        except Exception as e:
            Logger.error(f"❌ Backport assessment failed: {e}")
            return None
    
    def _ensure_correct_branch(self, pr_number: str) -> bool:
        """Ensure we're working with the correct branch for the PR"""
        if not self.github_utils:
            Logger.warn("⚠️  GitHub utilities not available - assuming correct branch")
            return True
        
        try:
            return self.github_utils.ensure_correct_branch(pr_number, self.spring_ai_dir)
        except Exception as e:
            Logger.warn(f"⚠️  Could not verify branch for PR #{pr_number}: {e}")
            return True  # Continue with assessment even if branch verification fails
    
    def _collect_pr_context(self, pr_number: str) -> Optional[Dict[str, Any]]:
        """Collect PR context data from existing context files"""
        pr_context_dir = self.context_dir / f"pr-{pr_number}"
        
        if not pr_context_dir.exists():
            Logger.error(f"❌ No context data found for PR #{pr_number}")
            Logger.error("❌ Run context collection first: python3 pr_context_collector.py <pr_number>")
            return None
        
        context_data = {}
        
        # Load essential context files
        context_files = {
            'pr_data': 'pr-data.json',
            'issue_data': 'issue-data.json', 
            'file_changes': 'file-changes.json',
            'conversation': 'conversation.json'
        }
        
        for key, filename in context_files.items():
            file_path = pr_context_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        context_data[key] = json.load(f)
                    Logger.info(f"📄 Loaded {filename} ({len(json.dumps(context_data[key]))} chars)")
                except Exception as e:
                    Logger.warn(f"⚠️  Could not load {filename}: {e}")
                    context_data[key] = {}
            else:
                Logger.warn(f"⚠️  Context file not found: {filename}")
                context_data[key] = {}
        
        # Validate we have minimum required data
        if not context_data.get('pr_data') or not context_data.get('file_changes'):
            Logger.error("❌ Missing essential context data (pr-data.json or file-changes.json)")
            return None
        
        Logger.success(f"✅ Collected context data for PR #{pr_number}")
        return context_data
    
    def _build_assessment_prompt(self, pr_number: str, context_data: Dict[str, Any]) -> Optional[Path]:
        """Build the complete prompt for AI backport assessment"""
        
        # Load backport assessment template
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except Exception as e:
            Logger.error(f"❌ Could not load backport template: {e}")
            return None
        
        # Build context summary for the prompt
        pr_data = context_data.get('pr_data', {})
        file_changes = context_data.get('file_changes', [])
        issue_data = context_data.get('issue_data', {})
        conversation = context_data.get('conversation', [])
        
        # Create formatted context sections
        pr_summary = self._format_pr_summary(pr_data)
        files_summary = self._format_files_summary(file_changes)
        issue_summary = self._format_issue_summary(issue_data)
        conversation_summary = self._format_conversation_summary(conversation)
        
        # Build complete prompt
        prompt_content = f"""# Backport Candidate Assessment Request

Please analyze this Spring AI Pull Request to determine if it's suitable for backporting to the 1.0.x maintenance branch.

## PR Overview
{pr_summary}

## Issue Context
{issue_summary}

## File Changes Summary
{files_summary}

## Conversation Summary
{conversation_summary}

## Assessment Instructions
{template_content}

## Context Files Available

You have access to the complete PR context data. Please analyze:
1. PR metadata and description for initial classification
2. File changes and code diffs for API impact assessment
3. Issue links and conversation for understanding the problem being solved
4. Any AI risk assessment data if available

Please provide your assessment following the exact format specified in the template above.
"""
        
        # Save prompt to temporary file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_file = self.logs_dir / f"backport-assessment-prompt-{pr_number}-{timestamp}.txt"
        
        try:
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt_content)
            
            Logger.info(f"📝 Built assessment prompt: {prompt_file}")
            Logger.info(f"📊 Prompt length: {len(prompt_content)} characters")
            
            return prompt_file
            
        except Exception as e:
            Logger.error(f"❌ Could not save prompt file: {e}")
            return None
    
    def _format_pr_summary(self, pr_data: Dict[str, Any]) -> str:
        """Format PR data into readable summary"""
        if not pr_data:
            return "PR data not available"
        
        title = pr_data.get('title', 'Unknown')
        author = pr_data.get('author', 'Unknown')
        state = pr_data.get('state', 'Unknown')
        body = pr_data.get('body', '')[:500] + ('...' if len(pr_data.get('body', '')) > 500 else '')
        
        return f"""**Title**: {title}
**Author**: {author}
**State**: {state}
**Description**: {body}"""
    
    def _format_files_summary(self, file_changes: List[Dict[str, Any]]) -> str:
        """Format file changes into readable summary"""
        if not file_changes:
            return "No file changes data available"
        
        total_files = len(file_changes)
        java_files = len([f for f in file_changes if f.get('path', '').endswith('.java')])
        test_files = len([f for f in file_changes if 'test' in f.get('path', '').lower()])
        doc_files = len([f for f in file_changes if f.get('path', '').endswith(('.md', '.adoc'))])
        
        summary = f"""**Total Files**: {total_files}
**Java Files**: {java_files}
**Test Files**: {test_files}
**Documentation Files**: {doc_files}

**File Types by Status**:"""
        
        status_counts = {}
        for file_change in file_changes[:10]:  # Show first 10 files
            status = file_change.get('status', 'unknown')
            path = file_change.get('path', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            summary += f"\n- {status}: {path}"
        
        if total_files > 10:
            summary += f"\n- ... and {total_files - 10} more files"
        
        return summary
    
    def _format_issue_summary(self, issue_data: Dict[str, Any]) -> str:
        """Format issue context into readable summary"""
        if not issue_data:
            return "No linked issues found"
        
        issues = issue_data.get('issues', [])
        if not issues:
            return "No linked issues found"
        
        summary = f"**Linked Issues**: {len(issues)} issue(s)\n"
        
        for issue in issues[:3]:  # Show first 3 issues
            title = issue.get('title', 'Unknown')
            state = issue.get('state', 'Unknown')
            labels = ', '.join([label.get('name', '') for label in issue.get('labels', [])])
            summary += f"- #{issue.get('number', 'N/A')}: {title} ({state}) [{labels}]\n"
        
        if len(issues) > 3:
            summary += f"- ... and {len(issues) - 3} more issues"
        
        return summary
    
    def _format_conversation_summary(self, conversation: List[Dict[str, Any]]) -> str:
        """Format conversation data into readable summary"""
        if not conversation:
            return "No conversation data available"
        
        total_comments = len(conversation)
        participants = set(comment.get('author', 'Unknown') for comment in conversation)
        
        return f"""**Total Comments**: {total_comments}
**Participants**: {len(participants)} ({', '.join(list(participants)[:5])})
**Latest Activity**: {conversation[-1].get('created_at', 'Unknown') if conversation else 'Unknown'}"""
    
    def _run_ai_analysis(self, pr_number: str, prompt_file: Path) -> Optional[Dict[str, Any]]:
        """Run AI analysis using Claude Code"""
        Logger.info(f"🤖 Running AI backport assessment for PR #{pr_number}")
        
        # Create output file for AI response
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.logs_dir / f"backport-assessment-response-{pr_number}-{timestamp}.txt"
        
        try:
            # Use ClaudeCodeWrapper to analyze the prompt
            result = self.claude.analyze_from_file(
                str(prompt_file), 
                str(output_file), 
                timeout=300,  # 5 minutes for thorough analysis
                use_json_output=False  # We'll parse the structured response ourselves
            )
            
            if result['success'] and result['response']:
                Logger.success(f"✅ AI analysis completed for PR #{pr_number}")
                Logger.info(f"📄 Response saved to: {output_file}")
                
                return {
                    'response': result['response'],
                    'response_file': str(output_file),
                    'success': True
                }
            else:
                Logger.error(f"❌ AI analysis failed: {result.get('error', 'Unknown error')}")
                if result.get('stderr'):
                    Logger.error(f"❌ Claude Code stderr: {result['stderr']}")
                return None
                
        except Exception as e:
            Logger.error(f"❌ Exception during AI analysis: {e}")
            return None
    
    def _parse_assessment_result(self, pr_number: str, ai_result: Dict[str, Any], context_data: Dict[str, Any]) -> Optional[BackportAssessmentResult]:
        """Parse AI assessment response into structured result"""
        
        response_text = ai_result.get('response', '')
        if not response_text:
            Logger.error("❌ Empty AI response")
            return None
        
        try:
            # Parse structured sections from the AI response
            decision = self._extract_section(response_text, "Backporting Decision")
            classification = self._extract_section(response_text, "Type")
            scope = self._extract_section(response_text, "Scope")
            api_impact = self._extract_section(response_text, "API Impact")
            risk_level = self._extract_section(response_text, "Risk Level")
            key_findings = self._extract_list_section(response_text, "Key Findings")
            reasoning = self._extract_section(response_text, "Reasoning")
            recommendations = self._extract_section(response_text, "Recommended Actions")
            
            
            # Extract file count from context
            file_changes = context_data.get('file_changes', [])
            files_changed_count = len(file_changes)
            
            # Check for dependency changes
            dependencies_changed = self._check_dependency_changes(file_changes)
            
            # Build analysis details
            analysis_details = {
                'files_analyzed': files_changed_count,
                'java_files': len([f for f in file_changes if f.get('path', '').endswith('.java')]),
                'test_files': len([f for f in file_changes if 'test' in f.get('path', '').lower()]),
                'documentation_files': len([f for f in file_changes if f.get('path', '').endswith(('.md', '.adoc'))]),
                'pom_files_changed': len([f for f in file_changes if f.get('path', '').endswith('pom.xml')]),
                'ai_response_file': ai_result.get('response_file', ''),
                'full_response': response_text
            }
            
            # Create result object
            result = BackportAssessmentResult(
                decision=decision or "UNKNOWN",
                classification=classification or "Unknown",
                scope=scope or "Analysis not available",
                api_impact=api_impact or "Unknown",
                risk_level=risk_level or "Unknown",
                files_changed_count=files_changed_count,
                dependencies_changed=dependencies_changed,
                key_findings=key_findings or ["Analysis not available"],
                reasoning=reasoning or "Analysis not available",
                recommendations=recommendations or "Analysis not available",
                assessment_timestamp=datetime.now().isoformat(),
                analysis_details=analysis_details
            )
            
            Logger.success(f"✅ Parsed backport assessment for PR #{pr_number}")
            return result
            
        except Exception as e:
            Logger.error(f"❌ Failed to parse assessment result: {e}")
            return None
    
    def _extract_section(self, text: str, section_name: str) -> Optional[str]:
        """Extract a specific section from AI response text"""
        import re
        
        # Look for section headers with various formats
        patterns = [
            # Pattern for "**Backporting Decision:** APPROVE"
            rf'\*\*{section_name}:\*\*\s*(.+)',
            # Pattern for "- **Type:** Something"
            rf'- \*\*{section_name}:\*\*\s*(.+)',
            # Pattern for plain section headers
            rf'^{section_name}:\s*(.+)',
            # Pattern for within sections like "## Key Findings" content
            rf'## {section_name}\s*\n(.+?)(?=\n##|\n---|\Z)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            if match:
                result = match.group(1).strip()
                # Clean up extra formatting and take only first line for simple fields
                if section_name in ['Backporting Decision', 'Type', 'Scope', 'API Impact', 'Risk Level']:
                    result = result.split('\n')[0].strip()
                else:
                    result = re.sub(r'\n\s*\n', '\n', result)  # Remove double newlines
                return result
        
        return None
    
    def _extract_list_section(self, text: str, section_name: str) -> List[str]:
        """Extract a list section from AI response text"""
        section_text = self._extract_section(text, section_name)
        if not section_text:
            return []
        
        # Parse bullet points
        lines = section_text.split('\n')
        items = []
        
        for line in lines:
            line = line.strip()
            if line.startswith(('- ', '* ', '• ')):
                items.append(line[2:].strip())
            elif line.startswith(('1. ', '2. ', '3. ', '4. ', '5. ')):
                items.append(line[3:].strip())
        
        return items if items else [section_text.strip()]
    
    def _check_dependency_changes(self, file_changes: List[Dict[str, Any]]) -> bool:
        """Check if any dependency files (pom.xml) were changed"""
        for file_change in file_changes:
            path = file_change.get('path', '')
            if path.endswith('pom.xml') or 'gradle' in path.lower():
                return True
        return False
    
    def _save_assessment_result(self, pr_number: str, result: BackportAssessmentResult) -> None:
        """Save assessment result to context directory"""
        
        pr_context_dir = self.context_dir / f"pr-{pr_number}"
        pr_context_dir.mkdir(exist_ok=True)
        
        # Convert result to dictionary for JSON serialization
        result_dict = {
            'decision': result.decision,
            'classification': result.classification,
            'scope': result.scope,
            'api_impact': result.api_impact,
            'risk_level': result.risk_level,
            'files_changed_count': result.files_changed_count,
            'dependencies_changed': result.dependencies_changed,
            'key_findings': result.key_findings,
            'reasoning': result.reasoning,
            'recommendations': result.recommendations,
            'assessment_timestamp': result.assessment_timestamp,
            'analysis_details': result.analysis_details
        }
        
        # Save to context directory
        output_file = pr_context_dir / "backport-assessment.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            
            Logger.success(f"💾 Backport assessment saved: {output_file}")
            
        except Exception as e:
            Logger.error(f"❌ Could not save assessment result: {e}")


def main():
    """Command-line interface for backport assessment"""
    if len(sys.argv) < 2:
        print("Usage: python3 backport_assessor.py <pr_number>")
        print("\nExamples:")
        print("  python3 backport_assessor.py 3386")
        print("  python3 backport_assessor.py 3914")
        sys.exit(1)
    
    pr_number = sys.argv[1]
    
    # Validate PR number
    if not pr_number.isdigit():
        Logger.error(f"Invalid PR number: {pr_number}")
        sys.exit(1)
    
    # Use script directory as working directory
    working_dir = Path(__file__).parent.absolute()
    spring_ai_dir = working_dir / "spring-ai"
    
    # Create assessor and run assessment
    assessor = BackportAssessor(working_dir, spring_ai_dir)
    result = assessor.run_backport_assessment(pr_number)
    
    if result:
        print(f"\n✅ Backport assessment completed for PR #{pr_number}")
        print(f"🎯 Decision: {result.decision}")
        print(f"📊 Classification: {result.classification}")
        print(f"⚠️  Risk Level: {result.risk_level}")
        print(f"📄 Files Changed: {result.files_changed_count}")
        print(f"💾 Assessment saved to: context/pr-{pr_number}/backport-assessment.json")
        sys.exit(0)
    else:
        print(f"\n❌ Backport assessment failed for PR #{pr_number}")
        sys.exit(1)


if __name__ == "__main__":
    main()
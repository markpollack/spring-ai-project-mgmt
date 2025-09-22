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
from typing import Dict, List, Optional, Any, Union
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
    
    def __init__(self, working_dir: Path, spring_ai_dir: Path, context_dir: Path = None, logs_dir: Path = None):
        """Initialize the backport assessor
        
        Args:
            working_dir: Directory containing scripts and templates
            spring_ai_dir: Path to Spring AI repository clone
        """
        self.working_dir = working_dir
        self.spring_ai_dir = spring_ai_dir
        
        # Use provided context directory or default to working_dir/context
        if context_dir is None:
            self.context_dir = working_dir / "context"
        else:
            self.context_dir = Path(context_dir).absolute()
            
        # Use provided logs directory or default to working_dir/logs
        if logs_dir is None:
            self.logs_dir = working_dir / "logs"
        else:
            self.logs_dir = Path(logs_dir).absolute()
            
        self.template_path = working_dir / "templates" / "backport-candidate.md"
        
        # Ensure directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Claude Code wrapper with logs directory
        self.claude = ClaudeCodeWrapper(logs_dir=self.logs_dir)
        
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
        
        # Validate data structure for issue_data and add logging
        issue_data = context_data.get('issue_data', [])
        if issue_data:
            if isinstance(issue_data, list):
                Logger.info(f"🔍 Issue data is correctly formatted as list with {len(issue_data)} items")
            elif isinstance(issue_data, dict):
                Logger.info(f"🔍 Issue data is dict format - keys: {list(issue_data.keys())}")
            else:
                Logger.warn(f"⚠️  Unexpected issue_data type: {type(issue_data)}")
        else:
            Logger.info("🔍 No issue data found for this PR")
        
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
        
        # Create formatted context sections with error handling
        try:
            pr_summary = self._format_pr_summary(pr_data)
        except Exception as e:
            Logger.warn(f"⚠️  Error formatting PR summary: {e}")
            pr_summary = "PR summary formatting failed - using basic data"
            
        try:
            files_summary = self._format_files_summary(file_changes)
        except Exception as e:
            Logger.warn(f"⚠️  Error formatting files summary: {e}")
            files_summary = f"Files summary formatting failed - {len(file_changes) if file_changes else 0} files changed"
            
        try:
            issue_summary = self._format_issue_summary(issue_data)
        except Exception as e:
            Logger.warn(f"⚠️  Error formatting issue summary: {e}")
            issue_summary = "Issue summary formatting failed - data may be malformed"
            
        try:
            conversation_summary = self._format_conversation_summary(conversation)
        except Exception as e:
            Logger.warn(f"⚠️  Error formatting conversation summary: {e}")
            conversation_summary = f"Conversation summary formatting failed - {len(conversation) if conversation else 0} comments"
        
        # Build complete prompt with explicit file paths
        context_dir = self.working_dir / "context" / f"pr-{pr_number}"
        
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

## Required Analysis Steps

**CRITICAL**: Please analyze the complete PR context data using these file paths:

1. **File Changes Analysis**: Read the complete file changes data:
```
Please read the file {context_dir}/file-changes.json and analyze ALL files listed in it.
```

2. **PR Context Data**: Read the PR metadata:
```
Please read the file {context_dir}/pr-data.json for detailed PR information.
```

3. **Risk Assessment Data**: If available, read the risk assessment:
```
Please read the file {context_dir}/ai-risk-assessment.json for breaking change analysis (if it exists).
```

4. **Solution Assessment Data**: If available, read the solution assessment:
```
Please read the file {context_dir}/solution-assessment.json for technical analysis (if it exists).
```

After analyzing all available data, provide your assessment following the exact JSON format specified in the template above.
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
    
    def _is_security_related(self, pr_data: Dict[str, Any]) -> bool:
        """Detect if PR is security-related based on title/description"""
        if not pr_data:
            return False
            
        title = pr_data.get('title', '').lower()
        body = pr_data.get('body', '').lower()
        
        security_keywords = ['cve', 'security', 'vulnerability', 'exploit', 'security fix', 'sec fix']
        
        for keyword in security_keywords:
            if keyword in title or keyword in body:
                return True
        
        return False
    
    def _format_pr_summary(self, pr_data: Dict[str, Any]) -> str:
        """Format PR data into readable summary"""
        if not pr_data:
            return "PR data not available"
        
        title = pr_data.get('title', 'Unknown')
        author = pr_data.get('author', 'Unknown')
        state = pr_data.get('state', 'Unknown')
        body = pr_data.get('body', '')[:500] + ('...' if len(pr_data.get('body', '')) > 500 else '')
        
        # Add security context if detected
        security_note = ""
        if self._is_security_related(pr_data):
            security_note = "\n**⚠️ SECURITY CONTEXT DETECTED**: This PR appears to address a security issue/CVE - consider security exception for dependency upgrades"
        
        return f"""**Title**: {title}
**Author**: {author}
**State**: {state}
**Description**: {body}{security_note}"""
    
    def _format_files_summary(self, file_changes: List[Dict[str, Any]]) -> str:
        """Format file changes into readable summary"""
        if not file_changes:
            return "No file changes data available"
        
        total_files = len(file_changes)
        java_files = len([f for f in file_changes if f.get('filename', '').endswith('.java')])
        test_files = len([f for f in file_changes if 'test' in f.get('filename', '').lower()])
        doc_files = len([f for f in file_changes if f.get('filename', '').endswith(('.md', '.adoc'))])
        
        summary = f"""**Total Files**: {total_files}
**Java Files**: {java_files}
**Test Files**: {test_files}
**Documentation Files**: {doc_files}

**File Types by Status**:"""
        
        status_counts = {}
        for file_change in file_changes[:10]:  # Show first 10 files
            status = file_change.get('status', 'unknown')
            filename = file_change.get('filename', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            summary += f"\n- {status}: {filename}"
        
        if total_files > 10:
            summary += f"\n- ... and {total_files - 10} more files"
        
        return summary
    
    def _format_issue_summary(self, issue_data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> str:
        """Format issue context into readable summary"""
        if not issue_data:
            return "No linked issues found"
        
        # Handle both data structure formats:
        # Format 1: Direct list of issues: [{"number": 3931, ...}]
        # Format 2: Dict with issues key: {"issues": [{"number": 3931, ...}]}
        if isinstance(issue_data, list):
            Logger.info(f"🔍 Using direct list format for issue data ({len(issue_data)} issues)")
            issues = issue_data
        else:
            issues = issue_data.get('issues', [])
            Logger.info(f"🔍 Using dict format for issue data ({len(issues)} issues)")
            
        if not issues:
            return "No linked issues found"
        
        summary = f"**Linked Issues**: {len(issues)} issue(s)\n"
        
        for issue in issues[:3]:  # Show first 3 issues
            # Defensive check - ensure issue is a dict
            if not isinstance(issue, dict):
                Logger.warn(f"⚠️  Invalid issue format in list: {type(issue)}")
                continue
                
            title = issue.get('title', 'Unknown')
            state = issue.get('state', 'Unknown')
            
            # Defensive handling of labels
            labels_data = issue.get('labels', [])
            if isinstance(labels_data, list):
                labels = ', '.join([label.get('name', '') if isinstance(label, dict) else str(label) for label in labels_data])
            else:
                labels = str(labels_data)
                
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
**Latest Activity**: {conversation[-1].get('created_at', 'Unknown') if conversation and len(conversation) > 0 else 'Unknown'}"""
    
    def _run_ai_analysis(self, pr_number: str, prompt_file: Path) -> Optional[Dict[str, Any]]:
        """Run AI analysis using Claude Code"""
        Logger.info(f"🤖 Running AI backport assessment for PR #{pr_number}")
        
        # Create output file for AI response
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.logs_dir / f"backport-assessment-response-{pr_number}-{timestamp}.txt"
        
        try:
            # Use ClaudeCodeWrapper with centralized JSON extraction
            result = self.claude.analyze_from_file_with_json(
                str(prompt_file), 
                str(output_file), 
                timeout=300,  # 5 minutes for thorough analysis
                show_progress=True,  # Show progress animation during analysis
                system_debug_mode=True,
                pr_number=pr_number
            )
            
            if result['success'] and result['response']:
                Logger.success(f"✅ AI analysis completed for PR #{pr_number}")
                Logger.info(f"📄 Response saved to: {output_file}")
                
                # Log JSON extraction status
                if result.get('json_extraction_success'):
                    Logger.info("✅ JSON extraction successful using centralized method")
                else:
                    Logger.warn("⚠️  JSON extraction failed, will use fallback parsing")
                
                return {
                    'response': result['response'],
                    'json_data': result.get('json_data'),  # Pre-extracted JSON
                    'json_extraction_success': result.get('json_extraction_success', False),
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
        """Parse AI assessment response into structured result using centralized JSON extraction"""
        
        response_text = ai_result.get('response', '')
        if not response_text:
            Logger.error("❌ Empty AI response")
            return None
        
        try:
            # Try to use pre-extracted JSON data first (from centralized extraction)
            ai_data = ai_result.get('json_data')
            
            if ai_data and ai_result.get('json_extraction_success'):
                Logger.info("✅ Using pre-extracted JSON data from ClaudeCodeWrapper")
                decision = ai_data.get("decision", "").upper()
                classification = ai_data.get("classification", "")
                scope = ai_data.get("scope", "")
                api_impact = ai_data.get("api_impact", "")
                risk_level = ai_data.get("risk_level", "")
                key_findings = ai_data.get("key_findings", [])
                reasoning = ai_data.get("reasoning", "")
                recommendations = ai_data.get("recommendations", "")
            else:
                # Fallback: Try centralized JSON extraction as backup
                Logger.info("🔄 Pre-extracted JSON not available, using fallback extraction...")
                ai_data = self.claude.extract_json_from_response(response_text)
                
                if ai_data:
                    Logger.info("✅ Fallback JSON extraction successful")
                    decision = ai_data.get("decision", "").upper()
                    classification = ai_data.get("classification", "")
                    scope = ai_data.get("scope", "")
                    api_impact = ai_data.get("api_impact", "")
                    risk_level = ai_data.get("risk_level", "")
                    key_findings = ai_data.get("key_findings", [])
                    reasoning = ai_data.get("reasoning", "")
                    recommendations = ai_data.get("recommendations", "")
                else:
                    # Final fallback to markdown parsing (legacy format)
                    Logger.info("🔄 JSON extraction failed, falling back to markdown parsing")
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
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-powered backport assessment for Spring AI PRs')
    parser.add_argument('pr_number', help='GitHub PR number to assess')
    parser.add_argument('--context-dir', type=Path, help='Context directory path')
    parser.add_argument('--logs-dir', type=Path, help='Logs directory path')
    
    args = parser.parse_args()
    
    # Validate PR number
    if not args.pr_number.isdigit():
        Logger.error(f"Invalid PR number: {args.pr_number}")
        sys.exit(1)
    
    # Use script directory as working directory
    working_dir = Path(__file__).parent.absolute()
    spring_ai_dir = working_dir / "spring-ai"
    
    # Create assessor and run assessment
    assessor = BackportAssessor(
        working_dir=working_dir,
        spring_ai_dir=spring_ai_dir,
        context_dir=args.context_dir,
        logs_dir=args.logs_dir
    )
    result = assessor.run_backport_assessment(args.pr_number)
    
    if result:
        print(f"\n✅ Backport assessment completed for PR #{args.pr_number}")
        print(f"🎯 Decision: {result.decision}")
        print(f"📊 Classification: {result.classification}")
        print(f"⚠️  Risk Level: {result.risk_level}")
        print(f"📄 Files Changed: {result.files_changed_count}")
        print(f"💾 Assessment saved to: context/pr-{args.pr_number}/backport-assessment.json")
        sys.exit(0)
    else:
        print(f"\n❌ Backport assessment failed for PR #{args.pr_number}")
        sys.exit(1)


if __name__ == "__main__":
    main()
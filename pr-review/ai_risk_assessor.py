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
        
        # Initialize GitHub utilities for branch management
        if GitHubUtils:
            self.github_utils = GitHubUtils(working_dir)
        else:
            self.github_utils = None
    
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
        """Build file changes detail with full file content and patches for AI analysis"""
        if not file_changes:
            return "*No file changes data available*"
        
        details = []
        # Calculate token count and include files up to ~80,000 tokens
        included_changes = self._select_files_by_token_limit(file_changes, max_tokens=80000)
        
        for change in included_changes:
            filename = change.get('filename', 'Unknown')
            status = change.get('status', 'unknown')
            additions = change.get('additions', 0)
            deletions = change.get('deletions', 0)
            patch = change.get('patch', '')
            
            details.append(f"**{filename}** ({status})")
            details.append(f"  - +{additions}/-{deletions} lines")
            
            # Get full file content for context
            full_content = self._get_full_file_content(filename)
            if full_content:
                details.append("  - Full file content:")
                details.append("```java")
                # Truncate very large files but keep substantial context
                if len(full_content) > 8000:  # 8KB limit per file
                    details.append(full_content[:8000] + "\n... [file truncated] ...")
                else:
                    details.append(full_content)
                details.append("```")
                details.append("")
            
            # Include patch to show exactly what changed
            if patch:
                details.append("  - Patch (changes made):")
                details.append("```diff")
                # Include full patch but truncate if extremely long
                if len(patch) > 4000:  # 4KB limit for patch
                    details.append(patch[:4000] + "\n... [patch truncated] ...")
                else:
                    details.append(patch)
                details.append("```")
            
            details.append("")
        
        # Note: No partial inclusion anymore - we exit if all files don't fit
        
        return '\n'.join(details)
    
    def _create_fallback_assessment_from_narrative(self, narrative_text: str) -> Dict[str, Any]:
        """Create a basic assessment structure from Claude Code's narrative response"""
        # Try to extract risk level from the narrative
        risk_level = "UNKNOWN"
        if "LOW" in narrative_text.upper():
            risk_level = "LOW"
        elif "MEDIUM" in narrative_text.upper():
            risk_level = "MEDIUM"
        elif "HIGH" in narrative_text.upper():
            risk_level = "HIGH"
        
        # Create a basic structure with the narrative content
        return {
            'critical_issues': [],
            'important_issues': [],
            'risk_factors': ["AI analysis returned narrative format instead of structured data"],
            'positive_findings': ["Analysis completed successfully"],
            'overall_risk_level': risk_level,
            'risk_summary': narrative_text[:500] + "..." if len(narrative_text) > 500 else narrative_text
        }
    
    def _count_tokens(self, text: str) -> int:
        """Estimate token count using 1 word = 1.3 tokens approximation"""
        if not text:
            return 0
        # Simple word count (split on whitespace)
        word_count = len(text.split())
        # Convert to tokens: 1 word = 1.3 tokens
        return int(word_count * 1.3)
    
    def _select_files_by_token_limit(self, file_changes: List[Dict[str, Any]], max_tokens: int = 80000) -> List[Dict[str, Any]]:
        """Select files up to token limit, prioritizing by importance"""
        if not file_changes:
            return []
        
        # Calculate token count for each file (full content + patch)
        file_token_counts = []
        for change in file_changes:
            filename = change.get('filename', '')
            patch = change.get('patch', '')
            
            # Get full file content if available
            full_content = self._get_full_file_content(filename)
            
            # Count tokens for full content + patch + metadata
            content_tokens = self._count_tokens(full_content) if full_content else 0
            patch_tokens = self._count_tokens(patch)
            metadata_tokens = self._count_tokens(f"{filename} {change.get('status', '')} +{change.get('additions', 0)}/-{change.get('deletions', 0)}")
            
            total_tokens = content_tokens + patch_tokens + metadata_tokens
            
            file_token_counts.append({
                'change': change,
                'tokens': total_tokens,
                'filename': filename
            })
        
        # Sort by importance (prioritize main source files over tests)
        def file_priority(item):
            filename = item['filename'].lower()
            # Higher priority (lower number) = included first
            if filename.endswith('.java') and 'test' not in filename:
                return 1  # Main Java files first
            elif filename.endswith('.java') and 'test' in filename:
                return 2  # Test files second
            elif filename.endswith(('.yml', '.yaml', '.properties', '.xml')):
                return 3  # Config files third
            else:
                return 4  # Other files last
        
        file_token_counts.sort(key=file_priority)
        
        # Select files up to token limit
        selected_files = []
        total_tokens = 0
        
        for item in file_token_counts:
            if total_tokens + item['tokens'] <= max_tokens:
                selected_files.append(item['change'])
                total_tokens += item['tokens']
            else:
                break
        
        Logger.info(f"📊 Token analysis: {len(selected_files)}/{len(file_changes)} files selected (~{total_tokens:,} tokens)")
        
        # Exit if we can't include all files within token limit
        if len(selected_files) < len(file_changes):
            excluded_count = len(file_changes) - len(selected_files)
            Logger.error(f"❌ Cannot fit all {len(file_changes)} files within 80,000 token limit")
            Logger.error(f"   {excluded_count} files would be excluded")
            Logger.error(f"   Consider increasing token limit or reducing file content")
            raise RuntimeError(f"Token limit exceeded: {excluded_count} files cannot be included")
        
        return selected_files
    
    def _filter_patch_lines(self, patch: str) -> List[str]:
        """Filter patch lines to remove noise and keep relevant content"""
        if not patch:
            return []
        
        filtered_lines = []
        patch_lines = patch.split('\n')
        
        for line in patch_lines:
            # Skip diff headers
            if line.startswith(('@@', '+++', '---', 'diff --git', 'index ')):
                continue
            
            # Only include addition lines (skip deletions for context saving)
            if not line.startswith('+'):
                continue
            
            line_content = line[1:].strip()  # Remove the '+' prefix
            
            # Skip common noise patterns
            if self._is_noise_line(line_content):
                continue
            
            # Keep the line (truncated)
            filtered_lines.append(line[:80])
            
            # Limit lines per file to control context size
            if len(filtered_lines) >= 8:
                break
        
        return filtered_lines
    
    def _is_noise_line(self, line: str) -> bool:
        """Check if a line is noise that can be filtered out"""
        line_lower = line.lower().strip()
        
        # Skip empty lines
        if not line_lower:
            return True
        
        # Skip copyright headers and license text
        if any(keyword in line_lower for keyword in [
            'copyright', 'license', 'licensed under', 'apache license',
            'permission', 'warranty', 'author', '@since', '@version'
        ]):
            return True
        
        # Skip simple imports (keep only security-relevant ones)
        if line_lower.startswith('import ') or line_lower.startswith('from '):
            # Keep security-related imports
            if any(keyword in line_lower for keyword in [
                'security', 'auth', 'credential', 'password', 'key', 'token',
                'encrypt', 'hash', 'ssl', 'tls'
            ]):
                return False
            return True
        
        # Skip package declarations
        if line_lower.startswith('package '):
            return True
        
        # Skip simple comments and javadoc
        if line_lower.startswith(('*', '//', '/**', '*/')):
            return True
        
        # Skip bracket-only lines
        if line_lower in ['{', '}', '};', ');']:
            return True
        
        return False
    
    def _get_full_file_content(self, filename: str) -> Optional[str]:
        """Get full file content from the Spring AI repository"""
        try:
            # Construct path to file in the spring-ai directory
            file_path = self.spring_ai_dir / filename
            
            if not file_path.exists():
                Logger.warn(f"File not found: {file_path}")
                return None
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Skip very large files (over 50KB)
            if len(content) > 50000:
                Logger.warn(f"Skipping large file: {filename} ({len(content)/1024:.1f}KB)")
                return None
            
            return content
            
        except Exception as e:
            Logger.warn(f"Error reading file {filename}: {e}")
            return None
    
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
    
    def _log_files_being_sent(self, file_changes: List[Dict[str, Any]]):
        """Log which files are being sent to the AI for analysis"""
        if not file_changes:
            return
        
        included_files = self._select_files_by_token_limit(file_changes, max_tokens=80000)
        
        Logger.info("📁 Files being sent to AI:")
        for i, change in enumerate(included_files, 1):
            filename = change.get('filename', 'Unknown')
            status = change.get('status', 'unknown')
            additions = change.get('additions', 0)
            deletions = change.get('deletions', 0)
            
            # Check if we can get full content
            full_content = self._get_full_file_content(filename)
            content_status = "✅ full content" if full_content else "⚠️ patch only"
            content_size = f"({len(full_content)/1024:.1f}KB)" if full_content else ""
            
            Logger.info(f"   {i}. {filename} ({status}) +{additions}/-{deletions} - {content_status} {content_size}")
        
        # Note: No partial inclusion anymore - we exit if all files don't fit
    
    def _log_context_optimization_stats(self, file_changes: List[Dict[str, Any]]):
        """Log context size for full file + patch approach"""
        if not file_changes:
            return
        
        # Calculate original stats
        original_file_count = len(file_changes)
        original_patch_size = sum(len(f.get('patch', '')) for f in file_changes)
        
        # Calculate what we'll actually include based on token limit
        included_files = self._select_files_by_token_limit(file_changes, max_tokens=80000)
        included_file_count = len(included_files)
        
        # Calculate estimated context size with full files + patches
        total_full_content_size = 0
        total_patch_size = 0
        files_with_content = 0
        
        for change in included_files:
            filename = change.get('filename', '')
            patch = change.get('patch', '')
            
            # Estimate full file size
            full_content = self._get_full_file_content(filename)
            if full_content:
                content_size = min(len(full_content), 8000)  # Cap at 8KB per file
                total_full_content_size += content_size
                files_with_content += 1
            
            # Add patch size (capped at 4KB)
            if patch:
                patch_size = min(len(patch), 4000)
                total_patch_size += patch_size
        
        total_context_size = total_full_content_size + total_patch_size
        
        # Log the stats
        Logger.info("📊 Context Analysis (Full Files + Patches):")
        Logger.info(f"   Files: {original_file_count} → {included_file_count} (showing top {included_file_count})")
        Logger.info(f"   Files with content: {files_with_content}/{included_file_count}")
        Logger.info(f"   Full content size: {total_full_content_size/1024:.1f}KB")
        Logger.info(f"   Patch content size: {total_patch_size/1024:.1f}KB") 
        Logger.info(f"   Total context size: {total_context_size/1024:.1f}KB")
    
    def run_ai_risk_assessment(self, pr_number: str) -> Optional[RiskAssessmentResult]:
        """Run AI-powered risk assessment using Claude Code"""
        
        Logger.info(f"🤖 Running AI risk assessment for PR #{pr_number}")
        
        # Ensure we're on the correct branch for this PR
        if self.github_utils and self.spring_ai_dir.exists():
            Logger.info(f"🔄 Ensuring correct branch for PR #{pr_number}")
            if not self.github_utils.ensure_correct_branch(pr_number, self.spring_ai_dir):
                Logger.error(f"Failed to switch to correct branch for PR #{pr_number}")
                return None
        elif not self.spring_ai_dir.exists():
            Logger.error(f"Spring AI repository not found: {self.spring_ai_dir}")
            Logger.error("Please run the full PR workflow first to set up the repository")
            return None
        
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
            # Show which files will be sent to AI
            self._log_files_being_sent(file_changes)
            
            # Show context optimization stats
            file_changes = context_data.get('file_changes', [])
            self._log_context_optimization_stats(file_changes)
            
            # Create the AI prompt
            risk_prompt = self.create_risk_assessment_prompt(pr_number, context_data)
            prompt_size_kb = len(risk_prompt) / 1024
            Logger.info(f"📏 Final prompt size: {prompt_size_kb:.1f}KB")
            
            # Create temporary file for the prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as prompt_file:
                prompt_file.write(risk_prompt)
                prompt_file_path = prompt_file.name
            
            try:
                Logger.info("🧠 Starting Claude Code AI analysis...")
                
                # Use ClaudeCodeWrapper for reliable integration
                claude = ClaudeCodeWrapper()
                
                if not claude.is_available():
                    Logger.error("❌ Claude Code is not available")
                    return None
                
                # Use wrapper to analyze from file with JSON output
                logs_dir = Path(prompt_file_path).parent
                debug_response_file = logs_dir / "claude-response-risk-assessor.txt"
                result = claude.analyze_from_file(str(prompt_file_path), str(debug_response_file), timeout=300, use_json_output=False)
                
                if result['success'] and result['response'].strip():
                    response_content = result['response'].strip()
                    response_size_kb = len(response_content) / 1024
                    Logger.success(f"✅ Claude Code returned response ({response_size_kb:.1f}KB)")
                    
                    # Use raw markdown/text response directly
                    Logger.info("🔍 Using AI response as-is...")
                    try:
                        # Extract risk level for basic categorization
                        risk_level = "LOW"
                        if "HIGH" in response_content.upper():
                            risk_level = "HIGH"
                        elif "MEDIUM" in response_content.upper():
                            risk_level = "MEDIUM"
                        
                        # Create simple structure with raw content
                        assessment_data = {
                            'critical_issues': [],
                            'important_issues': [],
                            'risk_factors': [],
                            'positive_findings': [],
                            'overall_risk_level': risk_level,
                            'risk_summary': response_content,
                            'raw_assessment': response_content  # Keep the full response
                        }
                        
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
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
        
        # Cache for file content to avoid repeated stripping
        self._file_content_cache = {}
        
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
        """Build file changes detail with status-aware content strategy"""
        if not file_changes:
            return "*No file changes data available*"
        
        details = []
        details.append("**IMPORTANT**: Use your Read tool to examine files as needed for analysis.")
        details.append("")
        
        # Group files by status for better organization
        new_files = [f for f in file_changes if f.get('status') == 'added']
        modified_files = [f for f in file_changes if f.get('status') == 'modified']
        removed_files = [f for f in file_changes if f.get('status') == 'removed']
        
        if new_files:
            details.extend(self._format_new_files(new_files))
        if modified_files:
            details.extend(self._format_modified_files(modified_files))
        if removed_files:
            details.extend(self._format_removed_files(removed_files))
        
        return '\n'.join(details)
    
    def _format_new_files(self, new_files: List[Dict[str, Any]]) -> List[str]:
        """Format new files without any patch content (completely redundant for new files)"""
        details = ["## New Files Added"]
        details.append("")
        
        # Prioritize Java files first
        java_files = [f for f in new_files if f.get('filename', '').endswith('.java')]
        other_files = [f for f in new_files if not f.get('filename', '').endswith('.java')]
        
        for file_info in java_files + other_files:
            filename = file_info.get('filename', 'Unknown')
            additions = file_info.get('additions', 0)
            file_path = f"/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/spring-ai/{filename}"
            
            details.append(f"### {filename}")
            details.append(f"- **Status**: New file (patch content omitted - would be identical to full file)")
            details.append(f"- **File Path**: `{file_path}`")
            details.append(f"- **Size**: {additions} lines")
            details.append(f"- **Analysis**: Use Read tool to examine complete file content")
            
            # Add contextual summary for Java files (prioritized)
            if filename.endswith('.java'):
                file_summary = self._generate_java_file_summary(filename, file_info)
                details.append(f"- **Priority**: HIGH - Java source file")
                details.append(f"- **Purpose**: {file_summary}")
            else:
                file_summary = self._generate_file_summary(filename, file_info)
                if file_summary:
                    details.append(f"- **Purpose**: {file_summary}")
            
            details.append("")
        
        return details
    
    def _format_modified_files(self, modified_files: List[Dict[str, Any]]) -> List[str]:
        """Format modified files with relevant patch excerpts"""
        details = ["## Modified Files"]
        details.append("")
        
        for file_info in modified_files:
            filename = file_info.get('filename', 'Unknown')
            additions = file_info.get('additions', 0)
            deletions = file_info.get('deletions', 0)
            patch = file_info.get('patch', '')
            file_path = f"/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/spring-ai/{filename}"
            
            details.append(f"### {filename}")
            details.append(f"- **Status**: Modified")
            details.append(f"- **File Path**: `{file_path}`")
            details.append(f"- **Changes**: +{additions}/-{deletions} lines")
            
            # Include filtered patch excerpts for context
            if patch:
                filtered_patch = self._filter_patch_for_security_analysis(patch)
                if filtered_patch:
                    details.append(f"- **Key Changes**:")
                    details.extend(f"  - {line}" for line in filtered_patch[:5])  # Top 5 changes
            
            details.append(f"- **Full Analysis**: Use Read tool for complete context")
            details.append("")
        
        return details
    
    def _format_removed_files(self, removed_files: List[Dict[str, Any]]) -> List[str]:
        """Format removed files with minimal context"""
        details = ["## Removed Files"]
        details.append("")
        
        for file_info in removed_files:
            filename = file_info.get('filename', 'Unknown')
            deletions = file_info.get('deletions', 0)
            
            details.append(f"### {filename}")
            details.append(f"- **Status**: Removed")
            details.append(f"- **Size**: {deletions} lines removed")
            details.append(f"- **Analysis**: Consider security implications of removed functionality")
            details.append("")
        
        return details
    
    def _generate_java_file_summary(self, filename: str, file_info: Dict[str, Any]) -> str:
        """Generate contextual summary for Java files based on path/type"""
        if 'test' in filename.lower():
            return "Test class - examine for test coverage and security test patterns"
        elif 'autoconfigure' in filename.lower() or 'AutoConfiguration' in filename:
            return "Auto-configuration class - check for proper Spring Boot setup and security"  
        elif filename.endswith('Properties.java'):
            return "Configuration properties - examine for credential handling and validation"
        elif 'Controller' in filename:
            return "Spring Controller - check for input validation, authentication, and authorization"
        elif 'Service' in filename:
            return "Service class - analyze for business logic security and data handling"
        elif 'Repository' in filename:
            return "Repository class - examine for SQL injection prevention and data access security"
        else:
            return "Java source file - analyze for security, performance, and integration risks"
    
    def _generate_file_summary(self, filename: str, file_info: Dict[str, Any]) -> str:
        """Generate contextual summary for non-Java files based on path/type"""
        if filename.endswith('.xml'):
            if filename == 'pom.xml':
                return "Maven POM - check dependencies, plugins, and build security"
            else:
                return "XML configuration - examine for injection risks and sensitive data"
        elif filename.endswith('.md'):
            return "Documentation - review for sensitive information disclosure"
        elif filename.endswith(('.yml', '.yaml', '.properties')):
            return "Configuration file - check for hardcoded credentials and security settings"
        else:
            return "Source file - perform comprehensive security and quality analysis"
    
    def _filter_patch_for_security_analysis(self, patch: str) -> List[str]:
        """Filter patch lines to highlight security-relevant changes"""
        if not patch:
            return []
        
        filtered_lines = []
        patch_lines = patch.split('\n')
        
        for line in patch_lines:
            # Skip diff headers
            if line.startswith(('@@', '+++', '---', 'diff --git', 'index ')):
                continue
            
            # Only include addition lines for security focus
            if not line.startswith('+'):
                continue
            
            line_content = line[1:].strip()  # Remove the '+' prefix
            
            # Prioritize security-relevant changes
            if any(keyword in line_content.lower() for keyword in [
                'password', 'key', 'secret', 'token', 'auth', 'credential',
                'security', 'validation', 'sanitize', 'encrypt', 'decrypt',
                'sql', 'query', 'inject', 'xss', 'csrf'
            ]):
                filtered_lines.append(line[:80])  # Truncate long lines
                
            # Keep method signatures and class declarations
            elif any(pattern in line_content for pattern in [
                'public ', 'private ', 'protected ', 'class ', 'interface '
            ]):
                filtered_lines.append(line[:80])
            
            # Limit lines to prevent prompt bloat  
            if len(filtered_lines) >= 8:
                break
        
        return filtered_lines
    
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
    
    def _validate_file_access(self, file_changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate that Claude Code can access all the files we're referencing"""
        accessible_files = []
        inaccessible_files = []
        
        for change in file_changes:
            filename = change.get('filename', '')
            file_path = self.spring_ai_dir / filename
            
            if file_path.exists() and file_path.is_file():
                accessible_files.append(change)
            else:
                inaccessible_files.append(filename)
        
        if inaccessible_files:
            Logger.warn(f"⚠️ Some files not accessible: {', '.join(inaccessible_files)}")
        
        Logger.info(f"📊 File accessibility: {len(accessible_files)}/{len(file_changes)} files accessible to Claude Code")
        
        return accessible_files
    
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
        # Check cache first
        if filename in self._file_content_cache:
            return self._file_content_cache[filename]
            
        try:
            # Construct path to file in the spring-ai directory
            file_path = self.spring_ai_dir / filename
            
            if not file_path.exists():
                Logger.warn(f"File not found: {file_path}")
                self._file_content_cache[filename] = None
                return None
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Skip very large files (over 50KB)
            if len(content) > 50000:
                Logger.warn(f"Skipping large file: {filename} ({len(content)/1024:.1f}KB)")
                self._file_content_cache[filename] = None
                return None
            
            # Strip copyright headers and imports for Java files
            if filename.endswith('.java'):
                content = self._strip_java_boilerplate(content)
            
            # Cache the result
            self._file_content_cache[filename] = content
            return content
            
        except Exception as e:
            Logger.warn(f"Error reading file {filename}: {e}")
            self._file_content_cache[filename] = None
            return None
    
    def _strip_java_boilerplate(self, content: str) -> str:
        """Strip copyright headers and import statements from Java files"""
        original_size = len(content)
        lines = content.split('\n')
        filtered_lines = []
        in_copyright_block = False
        skip_imports = False
        copyright_lines_removed = 0
        import_lines_removed = 0
        
        for line in lines:
            stripped_line = line.strip()
            
            # Detect start of copyright block (must be at beginning of file)
            if not in_copyright_block and stripped_line == '/*' and copyright_lines_removed == 0:
                in_copyright_block = True
                copyright_lines_removed += 1
                continue
                
            # If in copyright block, remove all lines until closing
            if in_copyright_block:
                copyright_lines_removed += 1
                if stripped_line.endswith('*/'):
                    in_copyright_block = False
                continue
            
            # Skip single-line copyright comments  
            if stripped_line.startswith('//') and ('copyright' in line.lower() or 'licensed under' in line.lower()):
                copyright_lines_removed += 1
                continue
                
            # Skip import statements
            if stripped_line.startswith('import ') or stripped_line.startswith('from '):
                skip_imports = True
                import_lines_removed += 1
                continue
                
            # Stop skipping imports when we hit package or class declaration
            if skip_imports and (stripped_line.startswith('package ') or 
                               stripped_line.startswith('@') or
                               stripped_line.startswith('public class') or
                               stripped_line.startswith('public interface') or
                               stripped_line.startswith('class ') or
                               stripped_line.startswith('interface ')):
                skip_imports = False
            
            # Skip if we're still in import section
            if skip_imports:
                import_lines_removed += 1
                continue
                
            # Keep the line
            filtered_lines.append(line)
        
        stripped_content = '\n'.join(filtered_lines)
        stripped_size = len(stripped_content)
        reduction_percent = ((original_size - stripped_size) / original_size * 100) if original_size > 0 else 0
        
        if copyright_lines_removed > 0 or import_lines_removed > 0:
            Logger.info(f"🔍 Stripped Java boilerplate: {copyright_lines_removed} copyright lines, {import_lines_removed} import lines ({reduction_percent:.1f}% size reduction)")
        
        return stripped_content
    
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
        """Log which files will be available for Claude Code to read"""
        if not file_changes:
            return
        
        accessible_files = self._validate_file_access(file_changes)
        
        Logger.info("📁 Files available for Claude Code analysis:")
        for i, change in enumerate(accessible_files, 1):
            filename = change.get('filename', 'Unknown')
            status = change.get('status', 'unknown')
            additions = change.get('additions', 0)
            deletions = change.get('deletions', 0)
            
            # Check file size for reference
            file_path = self.spring_ai_dir / filename
            try:
                file_size = file_path.stat().st_size if file_path.exists() else 0
                size_kb = file_size / 1024
                size_status = "📖 available via Read tool"
                Logger.info(f"   {i}. {filename} ({status}) +{additions}/-{deletions} - {size_status} ({size_kb:.1f}KB)")
            except Exception:
                Logger.info(f"   {i}. {filename} ({status}) +{additions}/-{deletions} - ❓ size unknown")
        
        Logger.info(f"🔗 Strategy: File path references (no token concatenation limits)")
    
    def _log_context_optimization_stats(self, file_changes: List[Dict[str, Any]]):
        """Log context size for full file + patch approach"""
        if not file_changes:
            return
        
        # Calculate original stats
        original_file_count = len(file_changes)
        original_patch_size = sum(len(f.get('patch', '')) for f in file_changes)
        
        # Calculate what we'll actually include based on token limit
        included_files = self._validate_file_access(file_changes)
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
            # Log file accessibility for Claude Code
            file_changes = context_data.get('file_changes', [])
            self._log_files_being_sent(file_changes)
            
            # Create the AI prompt
            risk_prompt = self.create_risk_assessment_prompt(pr_number, context_data)
            
            # Save prompt to logs directory for debugging
            logs_dir = self.working_dir / "logs"
            logs_dir.mkdir(exist_ok=True)
            prompt_file_path = logs_dir / "claude-prompt-risk-assessor.txt"
            
            with open(prompt_file_path, 'w', encoding='utf-8') as f:
                f.write(risk_prompt)
            
            # Log prompt size with token estimation before sending to Claude Code
            prompt_size = len(risk_prompt.encode('utf-8'))
            prompt_size_kb = prompt_size / 1024
            estimated_tokens_method1 = prompt_size / 5  # 5 bytes per token
            estimated_tokens_method2 = prompt_size_kb * 200  # 200 tokens per KB
            
            Logger.info(f"🔍 Saved risk assessment prompt to: {prompt_file_path}")
            Logger.info(f"🔍 Prompt size: {prompt_size:,} bytes ({prompt_size_kb:.1f}KB)")
            Logger.info(f"🔍 Estimated tokens (5 bytes/token): {estimated_tokens_method1:,.0f}")
            Logger.info(f"🔍 Estimated tokens (200/KB): {estimated_tokens_method2:,.0f}")
            Logger.info(f"🔗 File strategy: {len(file_changes)} files referenced (not concatenated)")
            
            if estimated_tokens_method1 > 25000:
                Logger.warn(f"⚠️  Prompt exceeds 25,000 token limit (Claude Code Read tool limit)")
            elif estimated_tokens_method1 < 25000:
                Logger.info(f"✅ Prompt under Claude Code Read tool limit ({25000 - estimated_tokens_method1:,.0f} tokens remaining)")
            
            try:
                Logger.info("🧠 Starting Claude Code AI analysis...")
                
                # Use ClaudeCodeWrapper for reliable integration
                claude = ClaudeCodeWrapper()
                
                if not claude.is_available():
                    Logger.error("❌ Claude Code is not available")
                    return None
                
                # Use wrapper to analyze from file
                debug_response_file = logs_dir / "claude-response-risk-assessor.txt"
                result = claude.analyze_from_file(str(prompt_file_path), str(debug_response_file), timeout=300, use_json_output=True)
                
                # Debug logging to trace the 'list' object error
                Logger.info(f"🔍 Claude wrapper result type: {type(result)}")
                Logger.info(f"🔍 Claude wrapper result keys: {result.keys() if isinstance(result, dict) else 'Not a dict!'}")
                
                if result['success'] and result['response'].strip():
                    response_content = result['response'].strip()
                    response_size_kb = len(response_content) / 1024
                    Logger.success(f"✅ Claude Code returned response ({response_size_kb:.1f}KB)")
                    
                    try:
                        # Parse as JSON - no fallbacks, fail fast
                        assessment_data = json.loads(response_content)
                        
                        # Validate required keys exist
                        required_keys = ['critical_issues', 'important_issues', 'risk_factors', 'positive_findings', 'overall_risk_level', 'risk_summary']
                        for key in required_keys:
                            if key not in assessment_data:
                                Logger.error(f"❌ Missing required key in JSON response: {key}")
                                return None
                        
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
                        Logger.error(f"❌ Failed to parse AI response as JSON - EXECUTION STOPPED: {e}")
                        Logger.error(f"Response content preview: {response_content[:500]}...")
                        return None
                else:
                    Logger.error(f"❌ Claude Code failed: {result.get('error', 'Unknown error')}")
                    if result.get('stderr'):
                        Logger.error(f"Claude Code error: {result['stderr'].strip()}")
                    return None
                    
            finally:
                # Keep prompt file in logs for debugging
                Logger.info(f"🔍 Risk assessment prompt saved at: {prompt_file_path}")
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
#!/usr/bin/env python3
"""
Commit Message Generator for Spring AI PR Review System

This module provides AI-powered generation of comprehensive, professional commit messages
for Spring AI project PRs after squashing. It uses Claude Code AI to analyze PR context
and generate commit messages that follow Spring AI conventions and best practices.

Features:
- Context-aware commit message generation using all available PR data
- Spring AI project-specific conventions and formatting
- Structured commit message format with proper type/scope classification
- Fallback to basic messages if AI generation fails
- Integration with existing PR context collection system

Usage:
    from commit_message_generator import CommitMessageGenerator
    
    generator = CommitMessageGenerator()
    message = generator.generate_commit_message(pr_number, pr_context_dir)
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from claude_code_wrapper import ClaudeCodeWrapper
except ImportError:
    ClaudeCodeWrapper = None


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
class CommitMessageResult:
    """Result of commit message generation"""
    success: bool
    message: str
    fallback_used: bool = False
    error: Optional[str] = None
    processing_time: Optional[float] = None


class CommitMessageGenerator:
    """Generates comprehensive commit messages using Claude Code AI"""
    
    def __init__(self, script_dir: Path = None):
        """Initialize the commit message generator
        
        Args:
            script_dir: Directory containing templates and scripts
        """
        self.script_dir = script_dir or Path(__file__).parent.absolute()
        self.template_file = self.script_dir / "templates" / "review-commit-message.md"
        self.logs_dir = self.script_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Initialize Claude Code wrapper
        self.claude = ClaudeCodeWrapper() if ClaudeCodeWrapper else None
        
    def generate_commit_message(self, pr_number: str, pr_context_dir: Path, 
                              fallback_title: str = None) -> CommitMessageResult:
        """Generate a comprehensive commit message for a PR
        
        Args:
            pr_number: GitHub PR number
            pr_context_dir: Directory containing PR context data
            fallback_title: Basic title to use if AI generation fails
            
        Returns:
            CommitMessageResult with the generated message and metadata
        """
        start_time = datetime.now()
        
        try:
            Logger.info(f"🤖 Generating AI-powered commit message for PR #{pr_number}")
            
            # Check if Claude Code is available
            if not self.claude or not self.claude.is_available():
                Logger.warn("Claude Code not available - using fallback commit message")
                return self._generate_fallback_message(pr_number, fallback_title, 
                                                     "Claude Code not available")
            
            # Validate template exists
            if not self.template_file.exists():
                Logger.error(f"Template file not found: {self.template_file}")
                return self._generate_fallback_message(pr_number, fallback_title,
                                                     "Template file not found")
            
            # Load PR context data
            context_data = self._load_pr_context(pr_context_dir)
            if not context_data:
                Logger.warn("No PR context data available - using fallback")
                return self._generate_fallback_message(pr_number, fallback_title,
                                                     "No context data available")
            
            # Generate the commit message using Claude Code
            result = self._generate_with_claude_code(pr_number, context_data)
            
            if result.success:
                # Calculate processing time
                processing_time = (datetime.now() - start_time).total_seconds()
                result.processing_time = processing_time
                
                Logger.success(f"✅ Generated comprehensive commit message for PR #{pr_number} ({processing_time:.1f}s)")
                return result
            else:
                Logger.warn(f"AI generation failed: {result.error}")
                return self._generate_fallback_message(pr_number, fallback_title, result.error)
                
        except Exception as e:
            Logger.error(f"❌ Error generating commit message for PR #{pr_number}: {e}")
            return self._generate_fallback_message(pr_number, fallback_title, str(e))
    
    def _load_pr_context(self, pr_context_dir: Path) -> Optional[Dict[str, Any]]:
        """Load all available PR context data"""
        context = {}
        
        # Define context files to load
        context_files = {
            'pr_data': 'pr-data.json',
            'file_changes': 'file-changes.json', 
            'conversation': 'conversation.json',
            'issue_data': 'issue-data.json',
            'ai_analysis': 'ai-conversation-analysis.json',
            'solution_assessment': 'solution-assessment.json',
            'risk_assessment': 'ai-risk-assessment.json',
            'backport_assessment': 'backport-assessment.json'
        }
        
        # Load available context files
        for key, filename in context_files.items():
            file_path = pr_context_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        context[key] = json.load(f)
                except Exception as e:
                    Logger.warn(f"Could not load {filename}: {e}")
        
        return context if context else None
    
    def _generate_with_claude_code(self, pr_number: str, context_data: Dict[str, Any]) -> CommitMessageResult:
        """Generate commit message using Claude Code AI"""
        try:
            # Create temporary context file for Claude Code to read
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(context_data, f, indent=2, ensure_ascii=False)
                context_file = f.name
            
            # Create prompt for Claude Code
            prompt = f"""Please read the commit message generation template at {self.template_file} and the PR context data at {context_file}.

Generate a comprehensive, professional commit message for Spring AI PR #{pr_number} following the exact guidelines and format specified in the template.

The context includes PR metadata, file changes, conversations, and AI analysis. Use this information to create a commit message that:

1. Follows the exact structure: type(scope): description + body paragraphs + footer
2. Uses appropriate Spring AI terminology and conventions  
3. Explains the problem, solution, and impact clearly
4. References the original issue number if available
5. Stays within the specified length guidelines

Respond with ONLY the complete commit message text, exactly as it should appear in git."""

            # Create temporary prompt file for Claude Code to read
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                f.write(prompt)
                prompt_file = f.name
            
            # Use Claude Code to generate the commit message
            result = self.claude.analyze_from_file(
                prompt_file_path=prompt_file,
                output_file_path=str(self.logs_dir / f"claude-response-commit-message-{pr_number}.txt"),
                use_json_output=False  # We want text output for commit messages
            )
            
            if result['success']:
                raw_response = result['response'].strip()
                
                # Extract commit message from Claude Code response
                commit_message = self._extract_commit_message(raw_response)
                
                # Basic validation of the generated message
                if commit_message and self._validate_commit_message(commit_message):
                    return CommitMessageResult(
                        success=True,
                        message=commit_message,
                        fallback_used=False
                    )
                else:
                    return CommitMessageResult(
                        success=False,
                        message="",
                        error=f"Generated message failed validation or extraction. Raw response: {raw_response[:100]}..."
                    )
            else:
                return CommitMessageResult(
                    success=False,
                    message="", 
                    error=result.get('error', 'Claude Code analysis failed')
                )
                
        except Exception as e:
            return CommitMessageResult(
                success=False,
                message="",
                error=f"Exception during Claude Code generation: {e}"
            )
        finally:
            # Clean up temporary files
            try:
                Path(context_file).unlink()
            except:
                pass
            try:
                Path(prompt_file).unlink()
            except:
                pass
    
    def _extract_commit_message(self, raw_response: str) -> Optional[str]:
        """Extract the actual commit message from Claude Code response"""
        if not raw_response:
            return None
        
        # Look for markdown code blocks first
        import re
        
        # Try to find commit message in markdown code blocks
        code_block_pattern = r'```\s*\n(.*?)\n```'
        matches = re.findall(code_block_pattern, raw_response, re.DOTALL)
        
        if matches:
            # Use the first code block as the commit message
            commit_message = matches[0].strip()
            if commit_message and len(commit_message) > 10:
                return commit_message
        
        # If no code blocks found, look for patterns that indicate a commit message
        lines = raw_response.split('\n')
        
        # Skip explanatory text and look for commit-like content
        message_lines = []
        in_commit_message = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines at the start
            if not line and not message_lines:
                continue
                
            # Skip obvious explanation text
            if any(phrase in line.lower() for phrase in [
                'based on the template', 'here is the commit message', 
                'commit message for pr', 'following the guidelines'
            ]):
                continue
            
            # Look for conventional commit format or commit-like lines
            if ((':' in line and len(line) < 100) or 
                (line and not line.startswith('Based on') and not line.startswith('Here is'))):
                in_commit_message = True
            
            if in_commit_message:
                message_lines.append(line)
        
        if message_lines:
            commit_message = '\n'.join(message_lines).strip()
            if len(commit_message) > 10:
                return commit_message
        
        # Fallback: use the entire response if it looks like a commit message
        if len(raw_response) < 2000 and '\n' in raw_response:
            return raw_response.strip()
        
        return None
    
    def _validate_commit_message(self, message: str) -> bool:
        """Basic validation of generated commit message format"""
        if not message or len(message.strip()) < 10:
            return False
            
        lines = message.strip().split('\n')
        if not lines:
            return False
            
        # Check first line has basic structure (type or description)
        first_line = lines[0].strip()
        if not first_line or len(first_line) > 100:
            return False
            
        # Check for common commit message patterns
        has_colon = ':' in first_line
        has_parentheses = '(' in first_line and ')' in first_line
        
        # Accept messages with either conventional commit format or descriptive format
        return has_colon or len(first_line.split()) >= 2
    
    def _generate_fallback_message(self, pr_number: str, fallback_title: str = None, 
                                 error_reason: str = None) -> CommitMessageResult:
        """Generate a basic fallback commit message"""
        if fallback_title:
            # Try to extract a reasonable title from PR title
            title = fallback_title.strip()
            if title.startswith(f"#{pr_number}:"):
                title = title[len(f"#{pr_number}:"):].strip()
            elif title.startswith("#") and ":" in title:
                title = title.split(":", 1)[1].strip()
                
            message = f"{title}\n\nSquashed commits from PR #{pr_number}"
        else:
            message = f"Squashed commits from PR #{pr_number}"
        
        return CommitMessageResult(
            success=True,
            message=message,
            fallback_used=True,
            error=error_reason
        )


def main():
    """Command line entry point for testing"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate commit message for PR")
    parser.add_argument('pr_number', help='GitHub PR number')
    parser.add_argument('--context-dir', help='PR context directory', 
                       default='context/pr-{pr_number}')
    parser.add_argument('--fallback-title', help='Fallback title if AI generation fails')
    
    args = parser.parse_args()
    
    # Setup context directory
    context_dir = Path(args.context_dir.format(pr_number=args.pr_number))
    if not context_dir.exists():
        print(f"❌ Context directory not found: {context_dir}")
        sys.exit(1)
    
    # Generate commit message
    generator = CommitMessageGenerator()
    result = generator.generate_commit_message(
        args.pr_number, 
        context_dir,
        args.fallback_title
    )
    
    if result.success:
        print("Generated Commit Message:")
        print("=" * 50)
        print(result.message)
        print("=" * 50)
        
        if result.fallback_used:
            print(f"\n⚠️  Used fallback message due to: {result.error}")
        else:
            print(f"\n✅ AI-generated message ({result.processing_time:.1f}s)")
    else:
        print(f"❌ Failed to generate commit message: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
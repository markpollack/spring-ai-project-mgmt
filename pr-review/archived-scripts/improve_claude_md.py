#!/usr/bin/env python3
"""
CLAUDE.md Improvement Script

Automated tool to improve CLAUDE.md files using research-based best practices from:
- Anthropic Engineering Blog (official best practices)
- API Dog Blog (5 best practices for Claude.md)
- Maxitect Blog (effective CLAUDE.md structure)

This script uses Claude Code to analyze and transform CLAUDE.md files according to
established guidelines for conciseness, structure, and actionability.
"""

import sys
import subprocess
from pathlib import Path
from claude_code_wrapper import ClaudeCodeWrapper


# Simple logger to avoid circular imports
class Logger:
    @staticmethod
    def info(msg): print(f"\033[34m[INFO]\033[0m {msg}")
    @staticmethod
    def success(msg): print(f"\033[32m[SUCCESS]\033[0m {msg}")
    @staticmethod
    def warn(msg): print(f"\033[33m[WARN]\033[0m {msg}")
    @staticmethod
    def error(msg): print(f"\033[31m[ERROR]\033[0m {msg}")


class ClaudeMdImprover:
    """Automated CLAUDE.md improvement using research-based best practices"""
    
    def __init__(self, working_dir: Path = None):
        if working_dir is None:
            working_dir = Path(__file__).parent.absolute()
        
        self.working_dir = working_dir.absolute()
        self.templates_dir = self.working_dir / "templates"
        self.logs_dir = self.working_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
    
    def improve_claude_md(self, claude_md_path: str, backup: bool = True) -> bool:
        """
        Improve a CLAUDE.md file using research-based best practices
        
        Args:
            claude_md_path: Path to the CLAUDE.md file to improve
            backup: Whether to create a backup of the original file
            
        Returns:
            bool: True if improvement was successful, False otherwise
        """
        claude_md_file = Path(claude_md_path).absolute()
        
        if not claude_md_file.exists():
            Logger.error(f"❌ CLAUDE.md file not found: {claude_md_file}")
            return False
        
        Logger.info(f"🔍 Analyzing CLAUDE.md file: {claude_md_file}")
        
        # Create backup if requested
        if backup:
            backup_file = claude_md_file.with_suffix('.md.backup')
            backup_file.write_text(claude_md_file.read_text())
            Logger.info(f"💾 Created backup: {backup_file}")
        
        # Load improvement template
        template_file = self.templates_dir / "claude-md-improvement-prompt.md"
        if not template_file.exists():
            Logger.error(f"❌ Improvement template not found: {template_file}")
            return False
        
        # Create analysis prompt
        prompt = self._create_improvement_prompt(template_file, claude_md_file)
        if not prompt:
            Logger.error("❌ Failed to create improvement prompt")
            return False
        
        # Execute Claude Code analysis
        improved_content = self._execute_claude_improvement(prompt)
        if not improved_content:
            Logger.error("❌ Claude Code improvement failed")
            return False
        
        # Extract improved CLAUDE.md from response
        final_content = self._extract_improved_content(improved_content)
        if not final_content:
            Logger.error("❌ Failed to extract improved content")
            return False
        
        # Validate improvement
        if not self._validate_improvement(final_content):
            Logger.warn("⚠️  Improved content may not meet all best practices")
        
        # Write improved file
        claude_md_file.write_text(final_content)
        Logger.success(f"✅ CLAUDE.md improved successfully: {claude_md_file}")
        
        # Show improvement summary
        self._show_improvement_summary(claude_md_file, final_content)
        
        return True
    
    def _create_improvement_prompt(self, template_file: Path, claude_md_file: Path) -> str:
        """Create the improvement prompt with current CLAUDE.md content"""
        try:
            template = template_file.read_text()
            current_content = claude_md_file.read_text()
            
            prompt = f"""{template}

## Current CLAUDE.md File to Improve

Please read and analyze the current CLAUDE.md file at: {claude_md_file}

Based on the best practices outlined above, provide an improved version that:
1. Follows the required structure
2. Is under 150 lines
3. Uses bullet points throughout
4. Focuses on actionable directives
5. Removes implementation details

Provide the complete improved CLAUDE.md file in a markdown code block.
"""
            
            return prompt
            
        except Exception as e:
            Logger.error(f"❌ Failed to create prompt: {e}")
            return ""
    
    def _execute_claude_improvement(self, prompt: str) -> str:
        """Execute Claude Code improvement analysis"""
        try:
            Logger.info("🤖 Running Claude Code analysis for CLAUDE.md improvement...")
            
            # Initialize Claude Code wrapper
            claude = ClaudeCodeWrapper()
            
            if not claude.is_available():
                Logger.error("❌ Claude Code is not available")
                return ""
            
            # Save prompt for debugging
            debug_prompt_file = self.logs_dir / "claude-md-improvement-prompt.txt"
            debug_prompt_file.write_text(prompt)
            Logger.info(f"🔍 Saved prompt to: {debug_prompt_file}")
            
            # Execute analysis
            debug_response_file = self.logs_dir / "claude-md-improvement-response.txt"
            result = claude.analyze_from_file(
                str(debug_prompt_file), 
                str(debug_response_file), 
                timeout=300, 
                use_json_output=False, 
                show_progress=True
            )
            
            if result['success']:
                Logger.info(f"🔍 Claude Code response length: {len(result['response'])} chars")
                Logger.info(f"🔍 Saved response to: {debug_response_file}")
                return result['response']
            else:
                Logger.error(f"❌ Claude Code analysis failed: {result['error']}")
                return ""
                
        except Exception as e:
            Logger.error(f"❌ Failed to execute Claude Code: {e}")
            return ""
    
    def _extract_improved_content(self, claude_response: str) -> str:
        """Extract the improved CLAUDE.md content from Claude's response"""
        try:
            # Look for markdown code block with improved content
            import re
            
            # Try to find markdown code block (with or without language specification)
            md_pattern = r'```(?:markdown|md)?\s*\n(.*?)\n```'
            md_match = re.search(md_pattern, claude_response, re.DOTALL)
            
            if md_match:
                content = md_match.group(1).strip()
                Logger.info(f"🔍 Extracted content from markdown code block ({len(content)} chars)")
                return content
            
            # Try to find any code block at all
            code_pattern = r'```[^`]*?\n(.*?)\n```'
            code_match = re.search(code_pattern, claude_response, re.DOTALL)
            
            if code_match:
                content = code_match.group(1).strip()
                # Check if it looks like CLAUDE.md content
                if content.startswith('#') or 'spring ai' in content.lower():
                    Logger.info(f"🔍 Extracted content from generic code block ({len(content)} chars)")
                    return content
            
            # Fallback: look for content that starts with a header
            lines = claude_response.split('\n')
            content_lines = []
            capturing = False
            
            for line in lines:
                if line.strip().startswith('# ') and not capturing:
                    capturing = True
                    content_lines.append(line)
                elif capturing and line.strip():
                    content_lines.append(line)
                elif capturing and not line.strip():
                    # Keep empty lines in content
                    content_lines.append(line)
            
            if content_lines and len(content_lines) > 5:  # Must have substantial content
                content = '\n'.join(content_lines).strip()
                Logger.info(f"🔍 Extracted content by header detection ({len(content)} chars)")
                return content
            
            # Debug output for troubleshooting
            Logger.warn("⚠️  Could not extract improved content from Claude response")
            Logger.info(f"🔍 Response preview: {claude_response[:200]}...")
            Logger.info(f"🔍 Response contains '#': {'#' in claude_response}")
            Logger.info(f"🔍 Response contains code block: {'```' in claude_response}")
            return ""
            
        except Exception as e:
            Logger.error(f"❌ Failed to extract content: {e}")
            return ""
    
    def _validate_improvement(self, content: str) -> bool:
        """Validate that the improved content meets best practices"""
        lines = content.split('\n')
        line_count = len(lines)
        
        # Check line count
        if line_count > 150:
            Logger.warn(f"⚠️  Content is {line_count} lines (recommended: under 150)")
            return False
        
        # Check for required sections
        required_sections = ['#', 'commands', 'files']
        has_sections = any(section.lower() in content.lower() for section in required_sections)
        
        if not has_sections:
            Logger.warn("⚠️  Content may be missing required sections")
            return False
        
        # Check for bullet points
        bullet_count = content.count('- ')
        if bullet_count < 5:
            Logger.warn("⚠️  Content may not use enough bullet points")
            return False
        
        Logger.info(f"✅ Content validation passed ({line_count} lines, {bullet_count} bullet points)")
        return True
    
    def _show_improvement_summary(self, file_path: Path, content: str):
        """Show summary of improvements made"""
        lines = content.split('\n')
        bullet_points = content.count('- ')
        sections = content.count('## ') + content.count('# ')
        
        Logger.info("📊 Improvement Summary:")
        Logger.info(f"   - Total lines: {len(lines)}")
        Logger.info(f"   - Bullet points: {bullet_points}")
        Logger.info(f"   - Sections: {sections}")
        Logger.info(f"   - File size: {len(content)} characters")


def main():
    """Command-line interface for CLAUDE.md improvement"""
    if len(sys.argv) < 2:
        print("Usage: python3 improve_claude_md.py <claude_md_path> [--no-backup]")
        print("")
        print("Examples:")
        print("  python3 improve_claude_md.py CLAUDE.md")
        print("  python3 improve_claude_md.py ../project/CLAUDE.md --no-backup")
        print("")
        print("This script improves CLAUDE.md files using research-based best practices")
        print("from Anthropic and industry experts.")
        sys.exit(1)
    
    claude_md_path = sys.argv[1]
    backup = "--no-backup" not in sys.argv
    
    # Initialize improver
    working_dir = Path(__file__).parent.absolute()
    improver = ClaudeMdImprover(working_dir)
    
    # Run improvement
    success = improver.improve_claude_md(claude_md_path, backup=backup)
    
    if success:
        print(f"\n✅ CLAUDE.md improvement completed successfully!")
        print(f"📁 Improved file: {Path(claude_md_path).absolute()}")
        if backup:
            print(f"💾 Backup saved: {Path(claude_md_path).with_suffix('.md.backup')}")
        sys.exit(0)
    else:
        print(f"\n❌ CLAUDE.md improvement failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Claude Code Wrapper - Robust utility for Claude Code CLI integration

Provides a reliable interface for calling Claude Code from Python scripts with proper
error handling, file I/O, and debugging capabilities.
"""

import subprocess
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

class ClaudeCodeWrapper:
    """Robust wrapper for Claude Code CLI interactions"""
    
    def __init__(self, claude_binary_path: str = '/home/mark/.nvm/versions/node/v22.15.0/bin/claude'):
        self.claude_binary_path = claude_binary_path
    
    def is_available(self) -> bool:
        """Check if Claude Code is available"""
        try:
            subprocess.run([self.claude_binary_path, '--version'], 
                         capture_output=True, check=True, timeout=10)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def get_version(self) -> Optional[str]:
        """Get Claude Code version"""
        try:
            result = subprocess.run([self.claude_binary_path, '--version'], 
                                  capture_output=True, text=True, check=True, timeout=10)
            return result.stdout.strip()
        except Exception:
            return None
    
    def analyze_from_file(self, prompt_file_path: str, output_file_path: Optional[str] = None, 
                         timeout: int = 300, use_json_output: bool = True) -> Dict[str, Any]:
        """
        Analyze using Claude Code by having it read the prompt file directly
        
        Args:
            prompt_file_path: Path to file containing the prompt
            output_file_path: Optional path to save the response
            timeout: Timeout in seconds (default 300 = 5 minutes)
            use_json_output: Use --output-format json for structured responses
            
        Returns:
            Dict containing success status, response, error info, etc.
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Claude Code is not available',
                'stderr': None,
                'response': None
            }
        
        prompt_path = Path(prompt_file_path)
        if not prompt_path.exists():
            return {
                'success': False,
                'error': f'Prompt file not found: {prompt_file_path}',
                'stderr': None,
                'response': None
            }
        
        try:
            # Build command with optional JSON output format and skip permissions
            cmd = [self.claude_binary_path, '-p', '--dangerously-skip-permissions']
            if use_json_output:
                cmd.extend(['--output-format', 'json'])
            
            # Ask Claude Code to read and analyze the file directly
            file_prompt = f"Read the file {prompt_path.absolute()} and follow the instructions contained within it."
            cmd.append(file_prompt)
            
            # Call Claude Code using subprocess.run for simplicity
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=True
                )
                stdout = result.stdout
                stderr = result.stderr
                returncode = result.returncode
                
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': f'Claude Code analysis timed out after {timeout} seconds',
                    'stderr': None,
                    'response': None
                }
            except subprocess.CalledProcessError as e:
                return {
                    'success': False,
                    'error': f'Claude Code failed with return code {e.returncode}',
                    'stderr': e.stderr,
                    'response': None
                }
            
            # Save output if requested
            if output_file_path:
                output_path = Path(output_file_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"Return code: {returncode}\n")
                    f.write(f"Stdout length: {len(stdout)}\n")
                    f.write(f"Stderr: {stderr or 'None'}\n")
                    f.write(f"Response:\n{stdout}")
            
            return {
                'success': True,
                'response': stdout,
                'output_file': output_file_path,
                'stderr': stderr,
                'error': None
            }
            
        except Exception as e:
            stderr_val = stderr if 'stderr' in locals() else None
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'stderr': stderr_val,
                'response': None
            }
    
    def analyze_from_text(self, prompt_text: str, output_file_path: Optional[str] = None,
                         timeout: int = 300, use_json_output: bool = True) -> Dict[str, Any]:
        """
        Analyze using Claude Code with prompt text directly
        
        Args:
            prompt_text: The prompt text to analyze
            output_file_path: Optional path to save the response
            timeout: Timeout in seconds (default 300 = 5 minutes)
            use_json_output: Use --output-format json for structured responses
            
        Returns:
            Dict containing success status, response, error info, etc.
        """
        # Create temporary file with prompt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(prompt_text)
            temp_file_path = temp_file.name
        
        try:
            # Use the file-based analysis
            result = self.analyze_from_file(temp_file_path, output_file_path, timeout, use_json_output)
            return result
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass


# Test function when run directly
if __name__ == "__main__":
    """Test the ClaudeCodeWrapper with the saved prompt"""
    claude = ClaudeCodeWrapper()
    
    print("Claude Code Wrapper Test")
    print("=" * 40)
    
    if claude.is_available():
        version = claude.get_version()
        print(f"✅ Claude Code available: {version}")
        
        # Test with the saved prompt
        prompt_file = '/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/logs/claude-prompt-ai-analyzer.txt'
        output_file = '/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/logs/claude-response-wrapper-test.txt'
        
        if Path(prompt_file).exists():
            print(f"🧪 Testing with prompt file: {prompt_file}")
            result = claude.analyze_from_file(prompt_file, output_file)
            
            if result['success']:
                print("✅ Analysis completed successfully!")
                print(f"📁 Output saved to: {result['output_file']}")
                print(f"📊 Response length: {len(result['response'])} chars")
                print(f"🔍 Response preview: {result['response'][:200]}...")
            else:
                print(f"❌ Error: {result['error']}")
                if result.get('stderr'):
                    print(f"stderr: {result['stderr']}")
        else:
            print(f"❌ Prompt file not found: {prompt_file}")
    else:
        print("❌ Claude Code is not available")
#!/usr/bin/env python3
"""
Claude Code Wrapper - Robust utility for Claude Code CLI integration

Provides a reliable interface for calling Claude Code from Python scripts with proper
error handling, file I/O, and debugging capabilities.
"""

import subprocess
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional
from animated_progress import AnimatedProgress

class ClaudeCodeWrapper:
    """Robust wrapper for Claude Code CLI interactions"""
    
    def __init__(self, claude_binary_path: str = None):
        if claude_binary_path is None:
            # Try to find Claude Code in PATH
            try:
                result = subprocess.run(['which', 'claude'], capture_output=True, text=True, check=True)
                self.claude_binary_path = result.stdout.strip()
            except subprocess.CalledProcessError:
                # Fallback to hardcoded path
                self.claude_binary_path = '/home/mark/.nvm/versions/node/v22.15.0/bin/claude'
        else:
            self.claude_binary_path = claude_binary_path
    
    def is_available(self) -> bool:
        """Check if Claude Code is available"""
        try:
            # Use 'claude' command directly and set working directory to avoid yoga.wasm issues
            result = subprocess.run(['claude', '--version'], 
                         capture_output=True, check=True, timeout=10,
                         cwd='/home/mark/.nvm/versions/node/v22.15.0/lib/node_modules/@anthropic-ai/claude-code')
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            # Debug: print the actual exception for troubleshooting
            print(f"DEBUG: Claude Code availability check failed: {type(e).__name__}: {e}")
            if hasattr(e, 'stdout') and e.stdout:
                print(f"DEBUG: stdout: {e.stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"DEBUG: stderr: {e.stderr}")
            return False
        except Exception as e:
            # Catch any other unexpected exceptions
            print(f"DEBUG: Unexpected exception in is_available(): {type(e).__name__}: {e}")
            return False
    
    def get_version(self) -> Optional[str]:
        """Get Claude Code version"""
        try:
            result = subprocess.run(['claude', '--version'], 
                                  capture_output=True, text=True, check=True, timeout=10,
                                  cwd='/home/mark/.nvm/versions/node/v22.15.0/lib/node_modules/@anthropic-ai/claude-code')
            return result.stdout.strip()
        except Exception:
            return None
    
    def analyze_from_file(self, prompt_file_path: str, output_file_path: Optional[str] = None, 
                         timeout: int = 300, use_json_output: bool = True, show_progress: bool = True) -> Dict[str, Any]:
        """
        Analyze using Claude Code by having it read the prompt file directly
        
        Args:
            prompt_file_path: Path to file containing the prompt
            output_file_path: Optional path to save the response
            timeout: Timeout in seconds (default 300 = 5 minutes)
            use_json_output: Use --output-format json for structured responses
            show_progress: Show animated progress during execution (default True)
            
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
            cmd = ['claude', '-p', '--dangerously-skip-permissions', '--verbose']
            if use_json_output:
                cmd.extend(['--output-format', 'json'])
            
            # Ask Claude Code to read and analyze the file directly
            file_prompt = f"Please read the file {prompt_path.absolute()} and follow the instructions contained within it."
            cmd.append(file_prompt)
            
            # Log prompt size for debugging with token estimation
            try:
                prompt_size = prompt_path.stat().st_size
                prompt_size_kb = prompt_size / 1024
                # Token estimation: ~5 bytes per token or ~200 tokens per KB
                estimated_tokens_method1 = prompt_size / 5  # 5 bytes per token
                estimated_tokens_method2 = prompt_size_kb * 200  # 200 tokens per KB
                
                # Log to both stdout and add to response for debugging
                import logging
                logging.basicConfig(level=logging.INFO)
                logger = logging.getLogger(__name__)
                
                logger.info(f"🔍 Claude Code prompt file: {prompt_path}")
                logger.info(f"🔍 Prompt size: {prompt_size:,} bytes ({prompt_size_kb:.1f}KB)")
                logger.info(f"🔍 Estimated tokens (5 bytes/token): {estimated_tokens_method1:,.0f}")
                logger.info(f"🔍 Estimated tokens (200/KB): {estimated_tokens_method2:,.0f}")
                
                # Show if this is likely to cause issues (Claude supports ~200K tokens)
                if prompt_size_kb > 400:  # ~80K tokens at 200 tokens/KB
                    logger.warning(f"⚠️  Large prompt detected - may cause Claude Code processing issues")
                if estimated_tokens_method1 > 150000:  # Getting close to 200K limit
                    logger.warning(f"⚠️  Prompt approaching Claude's 200K token limit")
                    
            except Exception as e:
                print(f"🔍 Could not get prompt size: {e}")
            
            # Call Claude Code with optional progress animation
            try:
                start_time = time.time()
                logger.info(f"🔍 Starting Claude Code execution...")
                
                # Start progress animation if requested
                progress = None
                if show_progress:
                    progress = AnimatedProgress("🧠 Claude Code analyzing")
                    progress.start()
                
                try:
                    # Use Popen for non-blocking execution with progress
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd='/home/mark/.nvm/versions/node/v22.15.0/lib/node_modules/@anthropic-ai/claude-code'
                    )
                    
                    # Wait for completion with timeout
                    stdout, stderr = process.communicate(timeout=timeout)
                    returncode = process.returncode
                    
                finally:
                    # Always stop progress animation
                    if progress:
                        progress.stop()
                
                end_time = time.time()
                duration = end_time - start_time
                logger.info(f"🔍 Claude Code completed in {duration:.1f} seconds")
                
                # Check if command succeeded
                if returncode != 0:
                    raise subprocess.CalledProcessError(returncode, cmd, stdout, stderr)
                
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
            
            # Process the response based on output format
            if use_json_output:
                # Extract actual content from Claude Code JSON response
                try:
                    import json
                    claude_response = json.loads(stdout)
                    
                    # Check if this is an error response
                    if isinstance(claude_response, dict) and claude_response.get('subtype') == 'error_during_execution':
                        return {
                            'success': False,
                            'error': 'Claude Code execution error - likely timeout or processing failure',
                            'stderr': stderr,
                            'response': None
                        }
                    
                    # Extract actual content from Claude Code JSON response
                    actual_content = None
                    
                    try:
                        # Debug logging to see what we're working with
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Claude response type: {type(claude_response)}")
                        if isinstance(claude_response, list):
                            logger.info(f"List length: {len(claude_response)}")
                            if len(claude_response) > 0:
                                logger.info(f"First item type: {type(claude_response[0])}")
                        
                        # Handle array format (conversation messages)
                        if isinstance(claude_response, list):
                            # Find the last assistant message with content
                            for i, message in enumerate(reversed(claude_response)):
                                logger.info(f"Processing message {i}: type={type(message)}")
                                if not isinstance(message, dict):
                                    continue
                                logger.info(f"Message keys: {message.keys()}")
                                if message.get('type') == 'assistant':
                                    msg_data = message.get('message', {})
                                    logger.info(f"Message data type: {type(msg_data)}")
                                    if isinstance(msg_data, dict) and 'content' in msg_data:
                                        content_list = msg_data['content']
                                        logger.info(f"Content list type: {type(content_list)}")
                                        if isinstance(content_list, list) and len(content_list) > 0:
                                            # Get text content from the last content item
                                            last_content = content_list[-1]
                                            logger.info(f"Last content type: {type(last_content)}")
                                            if isinstance(last_content, dict) and 'text' in last_content:
                                                actual_content = last_content['text']
                                                logger.info(f"Found content: {actual_content[:100] if actual_content else 'None'}...")
                                                break
                        
                        # Handle single object format
                        elif isinstance(claude_response, dict):
                            if 'result' in claude_response:
                                actual_content = claude_response['result']
                            elif 'content' in claude_response:
                                actual_content = claude_response['content']
                            elif 'response' in claude_response:
                                actual_content = claude_response['response']
                        
                    except Exception as parse_error:
                        # Log the parsing error but continue with fallback
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Error parsing Claude Code JSON response: {parse_error}")
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    # If we couldn't extract content, fallback to raw JSON as string
                    if actual_content is None:
                        actual_content = json.dumps(claude_response) if isinstance(claude_response, (dict, list)) else stdout
                    
                    return {
                        'success': True,
                        'response': actual_content,
                        'output_file': output_file_path,
                        'stderr': stderr,
                        'error': None
                    }
                    
                except json.JSONDecodeError:
                    # If it's not valid JSON, return as-is (probably plain text response)
                    return {
                        'success': True,
                        'response': stdout,
                        'output_file': output_file_path,
                        'stderr': stderr,
                        'error': None
                    }
            else:
                # Plain text response
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
                         timeout: int = 300, use_json_output: bool = True, show_progress: bool = True) -> Dict[str, Any]:
        """
        Analyze using Claude Code with prompt text directly
        
        Args:
            prompt_text: The prompt text to analyze
            output_file_path: Optional path to save the response
            timeout: Timeout in seconds (default 300 = 5 minutes)
            use_json_output: Use --output-format json for structured responses
            show_progress: Show animated progress during execution (default True)
            
        Returns:
            Dict containing success status, response, error info, etc.
        """
        # Create temporary file with prompt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(prompt_text)
            temp_file_path = temp_file.name
        
        try:
            # Use the file-based analysis
            result = self.analyze_from_file(temp_file_path, output_file_path, timeout, use_json_output, show_progress)
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
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
import signal
import psutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from animated_progress import AnimatedProgress

class ClaudeCodeWrapper:
    """Robust wrapper for Claude Code CLI interactions"""
    
    # Class-level marker for processes launched by this wrapper
    WRAPPER_MARKER_ENV = "CLAUDE_CODE_WRAPPER_ID"
    
    def __init__(self, claude_binary_path: str = None, logs_dir: Path = None):
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
        
        # Set up logs directory for debugging
        if logs_dir is None:
            # Default to current working directory logs
            self.logs_dir = Path.cwd() / "logs"
        else:
            self.logs_dir = Path(logs_dir)
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Track active processes with metadata
        self.active_processes = {}  # Changed from list to dict for metadata
        
        # Process tracking log file
        self.process_log_path = self.logs_dir / "claude_process_tracking.log"
        
        # Generate unique session ID for this wrapper instance
        self.session_id = str(uuid.uuid4())

        # Detect if running inside a Claude Code session (nested invocation)
        self._nested = os.environ.get('CLAUDECODE') is not None
        self._claude_run_sh = os.path.expanduser('~/scripts/claude-run.sh')

        self._log_process_event("WRAPPER_INIT", details=f"session_id={self.session_id}, nested={self._nested}")
    
    def _wrap_cmd(self, cmd: list) -> list:
        """Wrap command through claude-run.sh if in a nested Claude Code session."""
        if self._nested and os.path.isfile(self._claude_run_sh):
            return [self._claude_run_sh] + cmd
        return cmd

    def is_available(self) -> bool:
        """Check if Claude Code is available"""
        try:
            # Prepare environment with our marker
            env = os.environ.copy()
            env[self.WRAPPER_MARKER_ENV] = self.session_id

            # Use claude-run.sh wrapper if inside a nested session
            check_cmd = self._wrap_cmd(['claude', '--version'])
            result = subprocess.run(check_cmd,
                         capture_output=True, check=True, timeout=15,
                         env=env)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"DEBUG: Claude Code availability check failed: {type(e).__name__}: {e}")
            if hasattr(e, 'stdout') and e.stdout:
                print(f"DEBUG: stdout: {e.stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"DEBUG: stderr: {e.stderr}")
            return False
        except Exception as e:
            print(f"DEBUG: Unexpected exception in is_available(): {type(e).__name__}: {e}")
            return False
    
    def get_version(self) -> Optional[str]:
        """Get Claude Code version"""
        try:
            env = os.environ.copy()
            env[self.WRAPPER_MARKER_ENV] = self.session_id

            check_cmd = self._wrap_cmd(['claude', '--version'])
            result = subprocess.run(check_cmd,
                                  capture_output=True, text=True, check=True, timeout=15,
                                  env=env)
            return result.stdout.strip()
        except Exception:
            return None
    
    def _log_process_event(self, event: str, pid: int = None, details: str = None):
        """Log process tracking events for debugging"""
        try:
            with open(self.process_log_path, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                log_entry = f"[{timestamp}] {event}"
                if pid:
                    log_entry += f" PID={pid}"
                if details:
                    log_entry += f" {details}"
                f.write(log_entry + '\n')
        except Exception as e:
            print(f"Failed to log process event: {e}")
    
    def _find_claude_processes(self, wrapper_only: bool = False) -> List[psutil.Process]:
        """Find all running Claude processes
        
        Args:
            wrapper_only: If True, only return processes launched by this wrapper
        """
        claude_processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'environ']):
                try:
                    # Check if this is a Claude process
                    if proc.info['name'] == 'claude' or (proc.info['cmdline'] and 'claude' in ' '.join(proc.info['cmdline'])):
                        if wrapper_only:
                            # Check for our wrapper marker in environment
                            try:
                                environ = proc.environ()
                                if self.WRAPPER_MARKER_ENV in environ:
                                    claude_processes.append(proc)
                                    self._log_process_event("FOUND_WRAPPER_PROCESS", pid=proc.pid, 
                                                          details=f"wrapper_id={environ[self.WRAPPER_MARKER_ENV]}")
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                # Can't read environment, skip this process
                                continue
                        else:
                            claude_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self._log_process_event("ERROR", details=f"Failed to find Claude processes: {e}")
        return claude_processes
    
    def cleanup_hanging_processes(self):
        """Clean up any hanging Claude processes launched by this wrapper"""
        cleaned_count = 0
        try:
            # Log current Claude processes - only get wrapper processes
            claude_procs = self._find_claude_processes(wrapper_only=True)
            self._log_process_event("CLEANUP_START", details=f"Found {len(claude_procs)} wrapper Claude processes")
            
            for proc in claude_procs:
                try:
                    pid = proc.pid
                    # Check if this is one of our tracked processes
                    if pid in self.active_processes:
                        self._log_process_event("CLEANUP_KILL_TRACKED", pid=pid)
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            proc.kill()
                        del self.active_processes[pid]
                        cleaned_count += 1
                    else:
                        # Log but don't kill untracked processes automatically
                        self._log_process_event("CLEANUP_FOUND_UNTRACKED", pid=pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    self._log_process_event("CLEANUP_ERROR", pid=pid, details=str(e))
            
            self._log_process_event("CLEANUP_END", details=f"Cleaned {cleaned_count} processes")
            
        except Exception as e:
            self._log_process_event("CLEANUP_FATAL_ERROR", details=str(e))
        
        return cleaned_count
    
    def force_cleanup_all_claude_processes(self) -> int:
        """Force cleanup ALL Claude processes (use with caution)"""
        killed_count = 0
        try:
            claude_procs = self._find_claude_processes()
            self._log_process_event("FORCE_CLEANUP_START", details=f"Found {len(claude_procs)} Claude processes")
            
            for proc in claude_procs:
                try:
                    pid = proc.pid
                    self._log_process_event("FORCE_CLEANUP_KILL", pid=pid)
                    proc.kill()
                    killed_count += 1
                    # Remove from tracking if it was tracked
                    if pid in self.active_processes:
                        del self.active_processes[pid]
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    self._log_process_event("FORCE_CLEANUP_ERROR", pid=pid, details=str(e))
            
            self._log_process_event("FORCE_CLEANUP_END", details=f"Killed {killed_count} processes")
            
        except Exception as e:
            self._log_process_event("FORCE_CLEANUP_FATAL_ERROR", details=str(e))
        
        return killed_count
    
    def analyze_from_file(self, prompt_file_path: str, output_file_path: Optional[str] = None, 
                         timeout: int = 300, use_json_output: bool = True, show_progress: bool = True,
                         debug_mode: bool = False, system_debug_mode: bool = False,
                         model: str = "sonnet", pr_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze using Claude Code by having it read the prompt file directly
        
        Args:
            prompt_file_path: Path to file containing the prompt
            output_file_path: Optional path to save the response
            timeout: Timeout in seconds (default 300 = 5 minutes)
            use_json_output: Use --output-format json for structured responses
            show_progress: Show animated progress during execution (default True)
            debug_mode: Enable detailed debug logging with real-time output streaming
            system_debug_mode: Enable system-level debugging (strace, file access monitoring)
            pr_number: Optional PR number to include in log filenames for easier debugging
            model: Model to use (default 'sonnet' for cost control)
            
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
            # Add model specification for cost control
            cmd.extend(['--model', model])
            
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
                    # Prepare environment with our marker
                    env = os.environ.copy()
                    env[self.WRAPPER_MARKER_ENV] = self.session_id
                    
                    debug_log_path = None
                    strace_log_path = None
                    system_monitor_processes = []
                    
                    if debug_mode:
                        # Create debug log file
                        debug_log_path = self.logs_dir / f"claude-debug-{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                        logger.info(f"🔍 Debug mode enabled, streaming output to: {debug_log_path}")
                    
                    if system_debug_mode:
                        # Create system debug log files
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        strace_log_path = self.logs_dir / f"claude-strace-{timestamp}.log"
                        lsof_log_path = self.logs_dir / f"claude-lsof-{timestamp}.log"
                        iotop_log_path = self.logs_dir / f"claude-iotop-{timestamp}.log"
                        logger.info(f"🔍 System debug mode enabled:")
                        logger.info(f"    - strace: {strace_log_path}")
                        logger.info(f"    - lsof: {lsof_log_path}")
                        logger.info(f"    - iotop: {iotop_log_path}")
                        
                        # Wrap command with strace for file system monitoring
                        strace_cmd = [
                            'strace', 
                            '-e', 'trace=file,openat,read,write,close',  # Track file operations
                            '-f',  # Follow forks
                            '-t',  # Add timestamps
                            '-o', str(strace_log_path)
                        ] + cmd
                        
                        actual_cmd = strace_cmd
                    else:
                        actual_cmd = cmd

                    # Wrap through claude-run.sh if nested in Claude Code session
                    actual_cmd = self._wrap_cmd(actual_cmd)

                    # Use Popen for non-blocking execution with progress
                    process = subprocess.Popen(
                        actual_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=os.path.dirname(self.claude_binary_path) or '/tmp',
                        env=env,
                        bufsize=1  # Line buffered
                    )
                    
                    # Track the process with metadata
                    pid = process.pid
                    self.active_processes[pid] = {
                        'start_time': datetime.now(),
                        'prompt_file': prompt_path.absolute(),
                        'timeout': timeout,
                        'cwd': os.getcwd()
                    }
                    self._log_process_event("PROCESS_START", pid=pid, details=f"timeout={timeout}s, prompt={prompt_path.name}")
                    
                    # Start system monitoring processes if requested
                    if system_debug_mode:
                        try:
                            # Find the actual Claude process (skip strace wrapper)
                            time.sleep(0.5)  # Give process time to start
                            
                            # Find Claude child process
                            parent_proc = psutil.Process(pid)
                            claude_processes = []
                            
                            def find_claude_children(proc):
                                try:
                                    if proc.name() == 'claude' or 'claude' in ' '.join(proc.cmdline()):
                                        claude_processes.append(proc)
                                    for child in proc.children():
                                        find_claude_children(child)
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass
                            
                            find_claude_children(parent_proc)
                            
                            if claude_processes:
                                claude_pid = claude_processes[0].pid
                                logger.info(f"🔍 Found Claude process PID: {claude_pid}")
                                
                                # Start lsof monitoring
                                lsof_process = subprocess.Popen([
                                    'bash', '-c',
                                    f'while kill -0 {claude_pid} 2>/dev/null; do '
                                    f'echo "=== $(date) ===" >> {lsof_log_path}; '
                                    f'lsof -p {claude_pid} >> {lsof_log_path} 2>&1; '
                                    f'sleep 2; done'
                                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                system_monitor_processes.append(lsof_process)
                                
                                # Start resource monitoring
                                resource_process = subprocess.Popen([
                                    'bash', '-c',
                                    f'while kill -0 {claude_pid} 2>/dev/null; do '
                                    f'echo "=== $(date) ===" >> {iotop_log_path}; '
                                    f'ps -o pid,ppid,%cpu,%mem,time,comm -p {claude_pid} >> {iotop_log_path} 2>&1; '
                                    f'sleep 1; done'
                                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                system_monitor_processes.append(resource_process)
                                
                        except Exception as e:
                            logger.warning(f"Failed to start system monitoring: {e}")
                    
                    # Wait for completion with timeout
                    if debug_mode:
                        # Stream output in real-time for debugging
                        import select
                        import threading
                        import queue
                        
                        stdout_lines = []
                        stderr_lines = []
                        
                        def stream_output(pipe, output_list, pipe_name, debug_file):
                            """Stream output from pipe to list and debug file"""
                            try:
                                for line in iter(pipe.readline, ''):
                                    if line:
                                        output_list.append(line)
                                        debug_file.write(f"[{pipe_name}] {line}")
                                        debug_file.flush()
                                        if pipe_name == "STDOUT" and len(line.strip()) > 0:
                                            logger.debug(f"🔍 Claude output: {line.strip()[:100]}...")
                            except Exception as e:
                                logger.error(f"Stream error ({pipe_name}): {e}")
                            finally:
                                pipe.close()
                        
                        with open(debug_log_path, 'w') as debug_file:
                            debug_file.write(f"=== Claude Code Debug Log ===\n")
                            debug_file.write(f"Started: {datetime.now()}\n")
                            debug_file.write(f"PID: {pid}\n")
                            debug_file.write(f"Command: {' '.join(cmd)}\n")
                            debug_file.write(f"Prompt: {prompt_path}\n")
                            debug_file.write(f"=== Output ===\n")
                            
                            # Start threads to read stdout and stderr
                            stdout_thread = threading.Thread(
                                target=stream_output,
                                args=(process.stdout, stdout_lines, "STDOUT", debug_file)
                            )
                            stderr_thread = threading.Thread(
                                target=stream_output,
                                args=(process.stderr, stderr_lines, "STDERR", debug_file)
                            )
                            
                            stdout_thread.start()
                            stderr_thread.start()
                            
                            # Wait for process with timeout
                            try:
                                returncode = process.wait(timeout=timeout)
                            except subprocess.TimeoutExpired:
                                debug_file.write(f"\n=== TIMEOUT after {timeout}s ===\n")
                                raise
                            
                            # Wait for threads to finish reading
                            stdout_thread.join(timeout=5)
                            stderr_thread.join(timeout=5)
                            
                            stdout = ''.join(stdout_lines)
                            stderr = ''.join(stderr_lines)
                            
                            debug_file.write(f"\n=== Process completed with return code: {returncode} ===\n")
                    else:
                        # Normal mode - use communicate
                        stdout, stderr = process.communicate(timeout=timeout)
                        returncode = process.returncode
                    
                    # Process completed normally, remove from tracking
                    if pid in self.active_processes:
                        del self.active_processes[pid]
                    self._log_process_event("PROCESS_END", pid=pid, details=f"returncode={returncode}")
                    
                finally:
                    # Always stop progress animation
                    if progress:
                        progress.stop()
                    
                    # Clean up system monitoring processes
                    if system_debug_mode and system_monitor_processes:
                        for monitor_proc in system_monitor_processes:
                            try:
                                monitor_proc.terminate()
                                monitor_proc.wait(timeout=2)
                            except Exception:
                                try:
                                    monitor_proc.kill()
                                except Exception:
                                    pass
                
                end_time = time.time()
                duration = end_time - start_time
                logger.info(f"🔍 Claude Code completed in {duration:.1f} seconds")
                
                # Check if command succeeded
                if returncode != 0:
                    raise subprocess.CalledProcessError(returncode, cmd, stdout, stderr)
                
            except subprocess.TimeoutExpired:
                # Process timed out - kill it
                if 'process' in locals() and process.poll() is None:
                    pid = process.pid
                    self._log_process_event("PROCESS_TIMEOUT", pid=pid, details=f"Killing after {timeout}s")
                    
                    try:
                        # Try graceful termination first
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                            self._log_process_event("PROCESS_TERMINATED", pid=pid)
                        except subprocess.TimeoutExpired:
                            # Force kill if graceful termination failed
                            process.kill()
                            process.wait()
                            self._log_process_event("PROCESS_KILLED", pid=pid)
                    except Exception as kill_error:
                        self._log_process_event("PROCESS_KILL_ERROR", pid=pid, details=str(kill_error))
                    
                    # Remove from tracking
                    if pid in self.active_processes:
                        del self.active_processes[pid]
                
                # Log timeout case for debugging
                timeout_log_path = self.logs_dir / f"claude-timeout-{prompt_path.stem}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                try:
                    with open(timeout_log_path, 'w', encoding='utf-8') as f:
                        f.write(f"# Claude Code Timeout Log\n\n")
                        f.write(f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"**Request File**: {prompt_path.name}\n")
                        f.write(f"**Timeout After**: {timeout} seconds\n")
                        f.write(f"**Process PID**: {pid if 'pid' in locals() else 'Unknown'}\n\n")
                        
                        f.write(f"## Request Prompt\n```\n")
                        try:
                            with open(prompt_path, 'r', encoding='utf-8') as prompt_f:
                                f.write(prompt_f.read())
                        except Exception as e:
                            f.write(f"Error reading prompt: {e}")
                        f.write(f"\n```\n\n")
                        
                        f.write(f"## Timeout Details\n")
                        f.write(f"**Command**: {' '.join(cmd)}\n")
                        f.write(f"**Working Directory**: {os.getcwd()}\n")
                    
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"🔍 Timeout logged: {timeout_log_path}")
                    
                except Exception as log_error:
                    pass  # Don't fail on logging errors
                
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
            
            # ENHANCED LOGGING: Save both request and response with pairing
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create a response log file paired with the prompt (include PR number if available)
            pr_suffix = f"-pr-{pr_number}" if pr_number else ""
            response_log_path = self.logs_dir / f"claude-response-{prompt_path.stem}{pr_suffix}-{timestamp}.md"
            try:
                # Ensure duration is available (it should be from the main execution path)
                duration_str = f"{duration:.1f} seconds" if 'duration' in locals() else "Unknown"
                
                with open(response_log_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Claude Code Request-Response Log\n\n")
                    f.write(f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**Request File**: {prompt_path.name}\n")
                    f.write(f"**Duration**: {duration_str}\n")
                    f.write(f"**Return Code**: {returncode}\n")
                    f.write(f"**Success**: {returncode == 0}\n\n")
                    
                    f.write(f"## Request Prompt\n```\n")
                    try:
                        with open(prompt_path, 'r', encoding='utf-8') as prompt_f:
                            f.write(prompt_f.read())
                    except Exception as e:
                        f.write(f"Error reading prompt: {e}")
                    f.write(f"\n```\n\n")
                    
                    f.write(f"## Response (Raw stdout)\n")
                    f.write(f"**Length**: {len(stdout)} characters\n\n")
                    f.write(f"```\n{stdout}\n```\n\n")
                    
                    if stderr:
                        f.write(f"## Error Output (stderr)\n")
                        f.write(f"```\n{stderr}\n```\n\n")
                    
                    # Add command info for debugging
                    f.write(f"## Command Details\n")
                    f.write(f"**Command**: {' '.join(cmd)}\n")
                    f.write(f"**Working Directory**: {os.getcwd()}\n")
                    f.write(f"**Environment Marker**: {env.get(self.WRAPPER_MARKER_ENV, 'Not set')}\n")
                
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"🔍 Request-Response pair logged: {response_log_path}")
                
            except Exception as log_error:
                logger.warning(f"Failed to create response log: {log_error}")
            
            # Save output if requested (legacy behavior)
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
                    token_usage = None
                    cost_info = None
                    
                    try:
                        # Debug logging to see what we're working with
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Claude response type: {type(claude_response)}")
                        if isinstance(claude_response, list):
                            logger.info(f"List length: {len(claude_response)}")
                            if len(claude_response) > 0:
                                logger.info(f"First item type: {type(claude_response[0])}")
                                
                                # Look for usage and cost information
                                for item in claude_response:
                                    if isinstance(item, dict):
                                        if 'usage' in item:
                                            token_usage = item['usage']
                                            logger.info(f"Found token usage: {token_usage}")
                                        if 'total_cost_usd' in item:
                                            cost_info = item['total_cost_usd']
                                            logger.info(f"Found cost info: ${cost_info}")
                        
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
                        'error': None,
                        'token_usage': token_usage,
                        'cost_usd': cost_info
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
    
    def extract_json_from_response(self, text_content: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from Claude Code response text using multiple fallback strategies.
        
        This centralizes all JSON extraction logic that was previously duplicated
        across backport_assessor.py, solution_assessor.py, ai_conversation_analyzer.py, etc.
        
        Args:
            text_content: Raw text content from Claude Code response
            
        Returns:
            Parsed JSON dict if successful, None if extraction fails
        """
        import re
        import json
        import logging
        
        logger = logging.getLogger(__name__)
        
        if not text_content:
            logger.warning("🔍 extract_json_from_response: Empty text content provided")
            return None
        
        logger.info(f"🔍 Extracting JSON from response ({len(text_content)} chars)")
        
        # Strategy 1: Try to extract JSON from markdown code block
        try:
            json_pattern = r'```json\s*\n(.*?)\n```'
            json_match = re.search(json_pattern, text_content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1).strip()
                logger.info(f"🔍 Found JSON in markdown code block ({len(json_str)} chars)")
                
                try:
                    parsed_json = json.loads(json_str)
                    logger.info("✅ Successfully parsed JSON from markdown code block")
                    return parsed_json
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️  JSON code block parse error: {e}")
                    # Continue to next strategy
        except Exception as e:
            logger.warning(f"⚠️  Markdown code block extraction failed: {e}")
        
        # Strategy 2: Try direct JSON parsing (look for { ... } blocks)
        try:
            logger.info("🔍 Trying direct JSON parsing from response...")
            lines = text_content.split('\n')
            json_lines = []
            in_json = False
            brace_count = 0
            
            for line in lines:
                line_stripped = line.strip()
                
                # Start JSON block detection
                if line_stripped.startswith('{') and not in_json:
                    in_json = True
                    brace_count = 0
                    json_lines = [line]  # Reset and start fresh
                elif in_json:
                    json_lines.append(line)
                
                # Count braces to handle nested objects
                if in_json:
                    brace_count += line.count('{') - line.count('}')
                    
                    # End of JSON block
                    if brace_count == 0 and line_stripped.endswith('}'):
                        break
            
            if json_lines and in_json:
                json_str = '\n'.join(json_lines).strip()
                logger.info(f"🔍 Found direct JSON block ({len(json_str)} chars)")
                
                try:
                    parsed_json = json.loads(json_str)
                    logger.info("✅ Successfully parsed JSON from direct parsing")
                    return parsed_json
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️  Direct JSON parse error: {e}")
                    logger.warning(f"⚠️  Problematic JSON preview: {json_str[:200]}...")
                    # Continue to next strategy
        except Exception as e:
            logger.warning(f"⚠️  Direct JSON parsing failed: {e}")
        
        # Strategy 3: Try to find JSON using simple bracket matching
        try:
            logger.info("🔍 Trying bracket-based JSON extraction...")
            
            # Find first { and last }
            first_brace = text_content.find('{')
            last_brace = text_content.rfind('}')
            
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = text_content[first_brace:last_brace+1].strip()
                logger.info(f"🔍 Found bracket-based JSON ({len(json_str)} chars)")
                
                try:
                    parsed_json = json.loads(json_str)
                    logger.info("✅ Successfully parsed JSON using bracket matching")
                    return parsed_json
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️  Bracket-based JSON parse error: {e}")
        except Exception as e:
            logger.warning(f"⚠️  Bracket-based JSON extraction failed: {e}")
        
        # All strategies failed
        logger.error("❌ All JSON extraction strategies failed")
        logger.error(f"❌ Text preview: {text_content[:500]}...")
        return None
    
    def analyze_from_file_with_json(self, prompt_file_path: str, output_file_path: Optional[str] = None,
                                   timeout: int = 300, show_progress: bool = True,
                                   system_debug_mode: bool = False, model: str = "sonnet", 
                                   pr_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze from file and automatically extract JSON from the response.
        
        This is a convenience method that combines analyze_from_file() with JSON extraction.
        
        Args:
            prompt_file_path: Path to the prompt file
            output_file_path: Optional path to save the response
            timeout: Timeout in seconds
            show_progress: Show animated progress
            system_debug_mode: Enable system-level debugging
            model: Model to use (default 'sonnet' for cost control)
            pr_number: Optional PR number to include in log filenames
            
        Returns:
            Dict with keys: success, response (raw text), json_data (parsed), error, etc.
        """
        # Get raw response using JSON output mode
        result = self.analyze_from_file(
            prompt_file_path=prompt_file_path,
            output_file_path=output_file_path,
            timeout=timeout,
            use_json_output=True,  # Force JSON mode for better parsing
            show_progress=show_progress,
            system_debug_mode=system_debug_mode,
            model=model,
            pr_number=pr_number
        )
        
        # If the call failed, return as-is
        if not result.get('success'):
            return result
        
        # Extract JSON from the response
        raw_response = result.get('response', '')
        json_data = self.extract_json_from_response(raw_response)
        
        # Add JSON data to the result
        result['json_data'] = json_data
        result['json_extraction_success'] = json_data is not None
        
        return result
    
    def analyze_from_text_with_json(self, prompt_text: str, output_file_path: Optional[str] = None,
                                   timeout: int = 300, show_progress: bool = True,
                                   log_prefix: str = None) -> Dict[str, Any]:
        """
        Analyze from text and automatically extract JSON from the response.
        
        This is a convenience method that combines analyze_from_text() with JSON extraction.
        
        Args:
            prompt_text: The prompt text to analyze
            output_file_path: Optional path to save the response
            timeout: Timeout in seconds
            show_progress: Show animated progress
            
        Returns:
            Dict with keys: success, response (raw text), json_data (parsed), error, etc.
        """
        # Get raw response using JSON output mode
        result = self.analyze_from_text(
            prompt_text=prompt_text,
            output_file_path=output_file_path,
            timeout=timeout,
            use_json_output=True,  # Force JSON mode for better parsing
            show_progress=show_progress,
            log_prefix=log_prefix
        )
        
        # If the call failed, return as-is
        if not result.get('success'):
            return result
        
        # Extract JSON from the response
        raw_response = result.get('response', '')
        json_data = self.extract_json_from_response(raw_response)
        
        # Add JSON data to the result
        result['json_data'] = json_data
        result['json_extraction_success'] = json_data is not None
        
        return result
    
    def analyze_from_text(self, prompt_text: str, output_file_path: Optional[str] = None,
                         timeout: int = 300, use_json_output: bool = True, show_progress: bool = True,
                         log_prefix: str = None) -> Dict[str, Any]:
        """
        Analyze using Claude Code with prompt text directly
        
        Args:
            prompt_text: The prompt text to analyze
            output_file_path: Optional path to save the response
            timeout: Timeout in seconds (default 300 = 5 minutes)
            use_json_output: Use --output-format json for structured responses
            show_progress: Show animated progress during execution (default True)
            log_prefix: Descriptive prefix for log file naming (e.g., 'compilation-error-type-mismatch')
            
        Returns:
            Dict containing success status, response, error info, etc.
        """
        # Create persistent prompt file for debugging with descriptive naming
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if log_prefix:
            prompt_file_path = self.logs_dir / f"claude-prompt-{log_prefix}-{timestamp}.md"
        else:
            prompt_file_path = self.logs_dir / f"claude-prompt-{timestamp}.md"
        
        with open(prompt_file_path, 'w', encoding='utf-8') as f:
            f.write(prompt_text)
        
        temp_file_path = str(prompt_file_path)
        
        try:
            # Use the file-based analysis
            result = self.analyze_from_file(temp_file_path, output_file_path, timeout, use_json_output, show_progress)
            # Keep the prompt file for debugging - don't delete it
            return result
        except Exception as e:
            # Log error but keep prompt file for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in analyze_from_text, prompt saved to: {prompt_file_path}")
            raise


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
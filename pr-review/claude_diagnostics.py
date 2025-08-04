#!/usr/bin/env python3
"""
Claude Code Diagnostics Tool

Helps diagnose why Claude Code hangs or times out on certain prompts.
"""

import sys
import time
import psutil
import threading
from pathlib import Path
from datetime import datetime
from claude_code_wrapper import ClaudeCodeWrapper

class ClaudeDiagnostics:
    def __init__(self):
        self.claude = ClaudeCodeWrapper()
        self.monitoring_active = False
        self.process_stats = []
        
    def monitor_process(self, pid: int, interval: float = 1.0):
        """Monitor CPU and memory usage of a process"""
        self.monitoring_active = True
        self.process_stats = []
        
        while self.monitoring_active:
            try:
                proc = psutil.Process(pid)
                stats = {
                    'timestamp': datetime.now(),
                    'cpu_percent': proc.cpu_percent(interval=0.1),
                    'memory_mb': proc.memory_info().rss / 1024 / 1024,
                    'num_threads': proc.num_threads(),
                    'status': proc.status()
                }
                self.process_stats.append(stats)
                
                # Also monitor child processes
                children = proc.children(recursive=True)
                if children:
                    stats['children'] = []
                    for child in children:
                        try:
                            child_stats = {
                                'pid': child.pid,
                                'name': child.name(),
                                'cpu_percent': child.cpu_percent(interval=0.1),
                                'memory_mb': child.memory_info().rss / 1024 / 1024
                            }
                            stats['children'].append(child_stats)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                            
            except psutil.NoSuchProcess:
                print(f"Process {pid} no longer exists")
                break
            except Exception as e:
                print(f"Monitoring error: {e}")
                
            time.sleep(interval)
    
    def diagnose_prompt(self, prompt_file: str, timeout: int = 60):
        """Run diagnostic analysis on a prompt"""
        print(f"🔍 Claude Code Diagnostics")
        print(f"=" * 60)
        print(f"Prompt file: {prompt_file}")
        print(f"Timeout: {timeout}s")
        print()
        
        # Check prompt file
        prompt_path = Path(prompt_file)
        if not prompt_path.exists():
            print(f"❌ Prompt file not found: {prompt_file}")
            return
            
        # Analyze prompt characteristics
        prompt_size = prompt_path.stat().st_size
        with open(prompt_path, 'r') as f:
            prompt_content = f.read()
            line_count = len(prompt_content.splitlines())
            
        print(f"📊 Prompt Analysis:")
        print(f"  - Size: {prompt_size:,} bytes ({prompt_size/1024:.1f} KB)")
        print(f"  - Lines: {line_count:,}")
        print(f"  - Estimated tokens: {prompt_size/5:,.0f} (@ 5 bytes/token)")
        
        # Check for potential issues
        print(f"\n🔍 Checking for potential issues:")
        
        # Large file references
        file_refs = [line for line in prompt_content.splitlines() if '/home/' in line or 'file:' in line]
        if file_refs:
            print(f"  ⚠️  Found {len(file_refs)} file path references - may cause Claude to read large files")
            for ref in file_refs[:3]:
                print(f"     - {ref.strip()[:80]}...")
                
        # Complex analysis requests
        complex_keywords = ['analyze every', 'all files', 'entire repository', 'comprehensive', 'detailed analysis']
        complex_found = [kw for kw in complex_keywords if kw.lower() in prompt_content.lower()]
        if complex_found:
            print(f"  ⚠️  Found complex analysis keywords: {', '.join(complex_found)}")
            
        # JSON parsing requests
        if 'json' in prompt_content.lower() and ('parse' in prompt_content.lower() or 'extract' in prompt_content.lower()):
            print(f"  ⚠️  Contains JSON parsing request - may cause parsing loops")
            
        print(f"\n🚀 Starting Claude Code with debug mode...")
        
        # Run with monitoring
        result = None
        monitor_thread = None
        
        try:
            # Create a monitoring thread
            class MonitorRunner:
                def __init__(self, diagnostics):
                    self.diagnostics = diagnostics
                    self.pid = None
                    
                def run(self):
                    # Wait for PID to be set
                    while self.pid is None:
                        time.sleep(0.1)
                    self.diagnostics.monitor_process(self.pid)
            
            monitor_runner = MonitorRunner(self)
            
            # Start Claude with debug mode
            start_time = time.time()
            
            # Hook into the process creation to get PID
            original_analyze = self.claude.analyze_from_file
            def analyze_with_monitor(*args, **kwargs):
                # Enable debug mode
                kwargs['debug_mode'] = True
                kwargs['timeout'] = timeout
                
                # Call original method and capture process
                result = original_analyze(*args, **kwargs)
                
                # Extract PID from active processes
                if self.claude.active_processes:
                    monitor_runner.pid = list(self.claude.active_processes.keys())[0]
                    
                return result
                
            self.claude.analyze_from_file = analyze_with_monitor
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=monitor_runner.run)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # Run analysis
            result = self.claude.analyze_from_file(prompt_file)
            
        except KeyboardInterrupt:
            print(f"\n⚠️  Interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            self.monitoring_active = False
            if monitor_thread:
                monitor_thread.join(timeout=2)
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Show results
        print(f"\n📊 Execution Summary:")
        print(f"  - Duration: {duration:.1f}s")
        print(f"  - Success: {result['success'] if result else 'N/A'}")
        if result and not result['success']:
            print(f"  - Error: {result.get('error', 'Unknown')}")
            
        # Show resource usage
        if self.process_stats:
            print(f"\n📈 Resource Usage:")
            max_cpu = max(s['cpu_percent'] for s in self.process_stats)
            max_mem = max(s['memory_mb'] for s in self.process_stats)
            avg_cpu = sum(s['cpu_percent'] for s in self.process_stats) / len(self.process_stats)
            
            print(f"  - Peak CPU: {max_cpu:.1f}%")
            print(f"  - Average CPU: {avg_cpu:.1f}%")
            print(f"  - Peak Memory: {max_mem:.1f} MB")
            
            # Check for child processes
            child_procs = [s for s in self.process_stats if 'children' in s and s['children']]
            if child_procs:
                print(f"  - Child processes detected: Yes ({len(child_procs)} samples)")
                
        # Check debug logs
        debug_logs = list(self.claude.logs_dir.glob("claude-debug-*.log"))
        if debug_logs:
            latest_debug = max(debug_logs, key=lambda p: p.stat().st_mtime)
            print(f"\n📝 Debug log: {latest_debug}")
            
            # Show last few lines
            with open(latest_debug, 'r') as f:
                lines = f.readlines()
                if len(lines) > 20:
                    print(f"  Last 10 lines:")
                    for line in lines[-10:]:
                        print(f"    {line.rstrip()}")
                        
        print(f"\n✅ Diagnostics complete!")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 claude_diagnostics.py <prompt_file> [timeout]")
        print("Example: python3 claude_diagnostics.py logs/claude-prompt-solution-assessor.txt 60")
        sys.exit(1)
        
    prompt_file = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    
    diagnostics = ClaudeDiagnostics()
    diagnostics.diagnose_prompt(prompt_file, timeout)

if __name__ == "__main__":
    main()
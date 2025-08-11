#!/usr/bin/env python3
"""Test system-level debugging for Claude Code wrapper"""

import time
from pathlib import Path
from claude_code_wrapper import ClaudeCodeWrapper

def test_system_debugging():
    """Test system debugging with the problematic solution assessor prompt"""
    print("🔍 Testing System-Level Debugging")
    print("=" * 60)
    
    claude = ClaudeCodeWrapper()
    
    if not claude.is_available():
        print("❌ Claude Code not available")
        return
    
    # Test with the problematic prompt
    prompt_file = "/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/logs/claude-prompt-solution-assessor.txt"
    
    if not Path(prompt_file).exists():
        print(f"❌ Prompt file not found: {prompt_file}")
        return
    
    print(f"📁 Prompt file: {prompt_file}")
    print(f"⏱️  Timeout: 60 seconds")
    print(f"🔍 System debug mode: ENABLED")
    print()
    
    print("🚀 Starting Claude Code with full system debugging...")
    print("   This will monitor:")
    print("   - File system access (strace)")
    print("   - Open file descriptors (lsof)")
    print("   - CPU/Memory usage (ps)")
    print()
    
    start_time = time.time()
    
    result = claude.analyze_from_file(
        prompt_file,
        timeout=60,  # 1 minute timeout for testing
        debug_mode=True,
        system_debug_mode=True,
        show_progress=True
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n📊 Results:")
    print(f"   Duration: {duration:.1f}s")
    print(f"   Success: {result['success']}")
    
    if result['success']:
        response_preview = result.get('response', '')[:200]
        print(f"   Response: {response_preview}...")
        
        # Check for cost information
        if 'cost_usd' in result and result['cost_usd']:
            print(f"   Cost: ${result['cost_usd']:.4f}")
        if 'token_usage' in result and result['token_usage']:
            print(f"   Tokens: {result['token_usage']}")
    else:
        print(f"   Error: {result.get('error', 'Unknown')}")
    
    # Show debug files created
    logs_dir = claude.logs_dir
    debug_files = list(logs_dir.glob("claude-*-*.log"))
    if debug_files:
        print(f"\n📝 Debug files created:")
        for debug_file in sorted(debug_files)[-6:]:  # Show last 6 files
            size = debug_file.stat().st_size
            print(f"   - {debug_file.name} ({size:,} bytes)")
    
    # Show analysis of what happened
    print(f"\n🔍 Analysis:")
    if duration < 10:
        print("   ⚡ Fast completion - likely succeeded or failed quickly")
    elif duration >= 55:
        print("   ⏰ Timeout - process was killed after hitting time limit")
        print("   📋 Check strace logs to see what files were being accessed")
    else:
        print("   🤔 Intermediate duration - partial completion or specific bottleneck")
    
    print(f"\n✅ System debugging test complete!")
    return result

def analyze_debug_logs():
    """Analyze the debug logs to understand what happened"""
    print(f"\n🔍 Analyzing Debug Logs:")
    print("=" * 40)
    
    logs_dir = Path("logs")
    
    # Find latest strace log
    strace_logs = list(logs_dir.glob("claude-strace-*.log"))
    if strace_logs:
        latest_strace = max(strace_logs, key=lambda p: p.stat().st_mtime)
        print(f"📊 Latest strace log: {latest_strace}")
        
        # Analyze file access patterns
        try:
            with open(latest_strace, 'r') as f:
                lines = f.readlines()
            
            # Count file operations
            file_ops = {'openat': 0, 'read': 0, 'write': 0, 'close': 0}
            accessed_files = set()
            
            for line in lines:
                for op in file_ops:
                    if f'{op}(' in line:
                        file_ops[op] += 1
                
                # Extract file paths
                if 'openat(' in line and '"' in line:
                    try:
                        path_start = line.find('"') + 1
                        path_end = line.find('"', path_start)
                        if path_end > path_start:
                            file_path = line[path_start:path_end]
                            if file_path.startswith('/'):
                                accessed_files.add(file_path)
                    except:
                        pass
            
            print(f"   File operations: {file_ops}")
            print(f"   Unique files accessed: {len(accessed_files)}")
            
            # Show some accessed files
            if accessed_files:
                print(f"   Sample files:")
                for file_path in sorted(list(accessed_files))[:10]:
                    print(f"     - {file_path}")
                if len(accessed_files) > 10:
                    print(f"     ... and {len(accessed_files) - 10} more")
        
        except Exception as e:
            print(f"   Error analyzing strace log: {e}")
    
    # Find latest lsof log
    lsof_logs = list(logs_dir.glob("claude-lsof-*.log"))
    if lsof_logs:
        latest_lsof = max(lsof_logs, key=lambda p: p.stat().st_mtime)
        print(f"📊 Latest lsof log: {latest_lsof}")
        
        # Show file descriptors at different times
        try:
            with open(latest_lsof, 'r') as f:
                content = f.read()
            
            # Count timestamps to see how long it ran
            timestamps = content.count("=== ")
            print(f"   Monitoring samples: {timestamps}")
            
            # Show last few lines for current state
            lines = content.split('\n')
            if len(lines) > 10:
                print(f"   Last few entries:")
                for line in lines[-10:]:
                    if line.strip():
                        print(f"     {line}")
        
        except Exception as e:
            print(f"   Error analyzing lsof log: {e}")

if __name__ == "__main__":
    result = test_system_debugging()
    analyze_debug_logs()
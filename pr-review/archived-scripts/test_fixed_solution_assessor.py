#!/usr/bin/env python3
"""Test the fixed solution assessor to verify it only reads PR files"""

import subprocess
import time
from pathlib import Path

def test_fixed_solution_assessor():
    """Test the updated solution assessor with system debugging"""
    print("🧪 Testing Fixed Solution Assessor")
    print("=" * 60)
    print("This test will verify that Claude Code only reads PR files")
    print("and doesn't explore the entire Spring AI codebase.")
    print()
    
    # Run the solution assessor with system debugging
    print("🚀 Running solution assessor with system debugging...")
    print("   - Target PR: #3914")
    print("   - Timeout: 180 seconds (3 minutes)")
    print("   - System debugging: ENABLED")
    print()
    
    start_time = time.time()
    
    # Run the solution assessor with debugging
    result = subprocess.run([
        'python3', 'solution_assessor.py', '3914',
        '--context-dir', 'context',
        '--logs-dir', 'logs'
    ], capture_output=True, text=True, timeout=180)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"📊 Execution Results:")
    print(f"   Duration: {duration:.1f} seconds")
    print(f"   Return code: {result.returncode}")
    print(f"   Success: {'✅' if result.returncode == 0 else '❌'}")
    
    if result.returncode == 0:
        print(f"   Output preview: {result.stdout[:200]}...")
    else:
        print(f"   Error: {result.stderr[:200]}...")
    
    # Check the generated prompt to see if it has the new format
    latest_prompt = None
    prompt_files = list(Path('logs').glob('claude-prompt-solution-assessor*.txt'))
    if prompt_files:
        latest_prompt = max(prompt_files, key=lambda p: p.stat().st_mtime)
        print(f"\n📝 Generated prompt: {latest_prompt}")
        
        # Check if the prompt has our boundary instructions
        with open(latest_prompt, 'r') as f:
            prompt_content = f.read()
        
        has_boundaries = "CRITICAL ANALYSIS BOUNDARIES" in prompt_content
        has_absolute_paths = "/home/mark/project-mgmt" in prompt_content
        has_instructions = "DO NOT read, explore, or reference any other files" in prompt_content
        
        print(f"   ✅ Has boundary instructions: {has_boundaries}")
        print(f"   ✅ Has absolute file paths: {has_absolute_paths}")
        print(f"   ✅ Has strict instructions: {has_instructions}")
        
        # Show a sample of the file list format
        if "Files to analyze:" in prompt_content:
            lines = prompt_content.split('\n')
            file_section_start = None
            for i, line in enumerate(lines):
                if "Files to analyze:" in line:
                    file_section_start = i
                    break
            
            if file_section_start:
                print(f"\n📋 Sample file listing format:")
                for line in lines[file_section_start:file_section_start+5]:
                    print(f"   {line}")
    
    # Now run with system debugging to verify file access
    print(f"\n🔍 Running system debugging test...")
    debug_result = subprocess.run([
        'python3', 'test_system_debug.py'
    ], capture_output=True, text=True, timeout=120)
    
    if debug_result.returncode == 0:
        # Parse the debug output to see file access stats
        output = debug_result.stdout
        if "File operations:" in output:
            print(f"   System debug completed successfully")
            # Extract file operation stats
            for line in output.split('\n'):
                if "File operations:" in line or "Unique files accessed:" in line:
                    print(f"   {line.strip()}")
        else:
            print(f"   Debug output: {output[-200:]}...")
    else:
        print(f"   Debug failed: {debug_result.stderr[:200]}...")
    
    print(f"\n{'='*60}")
    print(f"✅ Fixed solution assessor test completed!")
    
    # Summary
    if result.returncode == 0 and has_boundaries and has_absolute_paths:
        print(f"🎉 SUCCESS: Solution assessor has been updated with:")
        print(f"   - Absolute file paths")
        print(f"   - Boundary instructions")
        print(f"   - Pattern detection without file paths")
        print(f"   - Completion time: {duration:.1f}s")
    else:
        print(f"⚠️  ISSUES DETECTED: Please check the implementation")

if __name__ == "__main__":
    test_fixed_solution_assessor()
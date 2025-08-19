#!/usr/bin/env python3
"""Test timeout calculation for PR #4179"""

import json
from pathlib import Path
from solution_assessor import AIPoweredSolutionAssessor

def test_timeout_calculation():
    print("🧪 Testing timeout calculation for PR #4179...")
    
    # Initialize assessor
    working_dir = Path(__file__).parent.absolute()
    spring_ai_dir = working_dir / "spring-ai"
    context_dir = working_dir / "context"
    logs_dir = working_dir / "logs"
    
    assessor = AIPoweredSolutionAssessor(
        working_dir=working_dir,
        spring_ai_dir=spring_ai_dir,
        context_dir=context_dir,
        logs_dir=logs_dir
    )
    
    # Simulate PR #4179 data
    file_count = 60
    lines_changed = 7591 + 490  # additions + deletions
    architectural_significance = 'high'  # Based on our doc analysis
    
    print(f"📊 PR #4179 Parameters:")
    print(f"   - Files: {file_count}")
    print(f"   - Lines changed: {lines_changed}")
    print(f"   - Architectural significance: {architectural_significance}")
    print()
    
    # Calculate timeout
    timeout = assessor._calculate_timeout(file_count, lines_changed, architectural_significance)
    
    print(f"\n⏱️  Result: {timeout} seconds ({timeout//60}m{timeout%60:02d}s)")
    
    # Test with different PR sizes for comparison
    print("\n📊 Timeout examples for different PR sizes:")
    
    test_cases = [
        ("Small PR", 5, 100, 'low'),
        ("Medium PR", 20, 1500, 'medium'), 
        ("Large PR", 40, 5000, 'high'),
        ("PR #4179", 60, 8081, 'high'),
        ("Very Large PR", 80, 10000, 'high')
    ]
    
    for name, files, lines, arch in test_cases:
        timeout = assessor._calculate_timeout(files, lines, arch)
        print(f"   - {name}: {files} files, {lines} lines, {arch} → {timeout}s ({timeout//60}m{timeout%60:02d}s)")

if __name__ == "__main__":
    test_timeout_calculation()
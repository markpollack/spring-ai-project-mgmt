#!/usr/bin/env python3
"""Debug the code analysis method that's causing issues"""

from pathlib import Path
from solution_assessor import AIPoweredSolutionAssessor

def debug_code_analysis():
    print("🐛 Debugging code analysis for PR #4179...")
    
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
    
    print("🔍 Testing _analyze_code_changes method...")
    try:
        result = assessor._analyze_code_changes("4179")
        print(f"✅ Code analysis result: {result}")
        print(f"✅ Type: {type(result)}")
        if result:
            print(f"✅ Total lines added: {result.get('total_lines_added', 'N/A')}")
            print(f"✅ Total lines removed: {result.get('total_lines_removed', 'N/A')}")
            print(f"✅ File count: {result.get('file_count', 'N/A')}")
            print(f"✅ Implementation patterns: {len(result.get('implementation_patterns', []))}")
        else:
            print("❌ Code analysis returned None!")
            
    except Exception as e:
        print(f"❌ Code analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_code_analysis()
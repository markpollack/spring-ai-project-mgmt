#!/usr/bin/env python3
"""Test complete PR #4179 analysis to verify timeout resolution"""

import sys
from pathlib import Path
from solution_assessor import AIPoweredSolutionAssessor

def test_pr_4179_analysis():
    print("🧪 Testing complete PR #4179 analysis (original timeout case)...")
    print("="*80)
    
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
    
    # Verify context exists for PR #4179
    pr_context_dir = context_dir / "pr-4179"
    if not pr_context_dir.exists():
        print(f"❌ PR #4179 context not found at {pr_context_dir}")
        print("Please ensure PR context is collected first:")
        print("  python3 pr_context_collector.py 4179")
        return False
    
    print(f"✅ PR #4179 context found at {pr_context_dir}")
    
    # Check required files
    required_files = [
        "pr-data.json",
        "file-changes.json"
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path = pr_context_dir / file_name
        if not file_path.exists():
            missing_files.append(file_name)
        else:
            print(f"✅ Found {file_name}")
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("\n🚀 Starting full solution assessment for PR #4179...")
    print("This was the original case that timed out after 5 minutes")
    print("With our improvements, it should complete in ≤10 minutes with appropriate strategy")
    print()
    
    try:
        # Run the assessment
        assessment = assessor.assess_solution("4179")
        
        if assessment:
            print("\n🎉 SUCCESS! PR #4179 analysis completed without timeout!")
            print(f"✅ Assessment result: {assessment}")
            print(f"✅ Code quality score: {assessment.code_quality_score}/10")
            print(f"✅ Final complexity: {assessment.final_complexity_score}/10")
            print(f"✅ Risk factors: {len(assessment.risk_factors)}")
            print(f"✅ Recommendations: {len(assessment.recommendations)}")
            
            if hasattr(assessment, 'analysis_notes'):
                print(f"📋 Analysis notes: {assessment.analysis_notes}")
            
            return True
        else:
            print("❌ Assessment returned None - analysis failed")
            return False
            
    except Exception as e:
        print(f"❌ Assessment failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("PR #4179 Large PR Analysis Test")
    print("=" * 50)
    print("Testing the complete implementation against the original timeout case")
    print()
    
    success = test_pr_4179_analysis()
    
    if success:
        print("\n" + "=" * 80)
        print("🎉 TEST PASSED: Large PR analysis optimization is working!")
        print("PR #4179 analysis completed successfully without timeout")
        print("=" * 80)
        exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED: Large PR analysis still has issues")
        print("Review the logs and implementation")
        print("=" * 80)
        exit(1)

if __name__ == "__main__":
    main()
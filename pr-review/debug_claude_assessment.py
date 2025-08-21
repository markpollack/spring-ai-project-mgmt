#!/usr/bin/env python3
"""Debug the Claude assessment execution that's failing"""

import json
from pathlib import Path
from solution_assessor import AIPoweredSolutionAssessor

def debug_claude_assessment():
    print("🐛 Debugging Claude assessment execution for PR #4179...")
    
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
    
    print("🔍 Loading context data...")
    pr_context_dir = context_dir / "pr-4179"
    context_data = assessor._load_assessment_context(pr_context_dir)
    
    if not context_data:
        print("❌ Failed to load context data")
        return
    
    print(f"✅ Context data loaded: {list(context_data.keys())}")
    
    print("🔍 Testing documentation and classification...")
    file_changes = context_data.get('file_changes', [])
    doc_analysis = assessor._analyze_documentation_changes("4179", file_changes)
    total_lines = sum(change.get('additions', 0) + change.get('deletions', 0) for change in file_changes)
    pr_classification = assessor._classify_pr_size(len(file_changes), total_lines, doc_analysis)
    
    print(f"✅ PR classification: {pr_classification}")
    
    print("🔍 Testing code analysis...")
    code_analysis = assessor._analyze_code_changes("4179")
    print(f"✅ Code analysis: {code_analysis is not None}")
    
    print("🔍 Testing assessment prompt creation...")
    try:
        assessment_prompt = assessor._create_assessment_prompt(
            context_data, code_analysis, doc_analysis, pr_classification, "4179"
        )
        print(f"✅ Assessment prompt created: {len(assessment_prompt)} chars")
        print(f"✅ Prompt preview: {assessment_prompt[:200]}...")
        
        # Test the Claude execution part
        print("🔍 Testing Claude Code execution...")
        timeout = assessor._calculate_timeout(
            len(file_changes), 
            total_lines,
            doc_analysis.get('architectural_significance', 'low')
        )
        print(f"✅ Calculated timeout: {timeout}s")
        
        # Try to execute a minimal assessment
        result = assessor._execute_claude_assessment(assessment_prompt, timeout)
        print(f"✅ Claude execution result: {result}")
        
    except Exception as e:
        print(f"❌ Assessment prompt creation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_claude_assessment()
#!/usr/bin/env python3
"""Test PR classification for different PR sizes"""

import json
from pathlib import Path
from solution_assessor import AIPoweredSolutionAssessor

def test_pr_classification():
    print("🧪 Testing PR classification for different sizes...")
    
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
    
    # Test cases with different PR characteristics
    test_cases = [
        {
            'name': 'Small PR',
            'file_count': 3,
            'lines_changed': 150,
            'doc_analysis': {'doc_files_count': 0, 'architectural_significance': 'low', 'documentation_summary': 'No documentation changes'}
        },
        {
            'name': 'Medium PR',
            'file_count': 15,
            'lines_changed': 2500,
            'doc_analysis': {'doc_files_count': 1, 'architectural_significance': 'medium', 'documentation_summary': 'API Documentation: 1 file changed'}
        },
        {
            'name': 'Large PR',
            'file_count': 45,
            'lines_changed': 6000,
            'doc_analysis': {'doc_files_count': 3, 'architectural_significance': 'high', 'documentation_summary': 'NEW Feature Documentation: 2 new files'}
        },
        {
            'name': 'PR #4179 (Architectural)',
            'file_count': 60,
            'lines_changed': 8081,
            'doc_analysis': {
                'doc_files_count': 7, 
                'architectural_significance': 'high', 
                'documentation_summary': 'NEW MCP Documentation: 3 new files suggest major MCP feature additions | Navigation structure updated - indicates significant feature additions | MAJOR documentation changes: +1072 lines added'
            }
        }
    ]
    
    print("\n📊 Classification Results:")
    for case in test_cases:
        print(f"\n{'='*50}")
        print(f"Testing: {case['name']}")
        print(f"Files: {case['file_count']}, Lines: {case['lines_changed']}")
        
        classification = assessor._classify_pr_size(
            case['file_count'], 
            case['lines_changed'], 
            case['doc_analysis']
        )
        
        print(f"✅ Classification: {classification}")

if __name__ == "__main__":
    test_pr_classification()
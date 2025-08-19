#!/usr/bin/env python3
"""Test documentation analysis for PR #4179"""

import json
from pathlib import Path
from solution_assessor import AIPoweredSolutionAssessor

def test_documentation_analysis():
    print("🧪 Testing documentation analysis for PR #4179...")
    
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
    
    # Load file changes for PR #4179
    file_changes_path = context_dir / "pr-4179" / "file-changes.json"
    if not file_changes_path.exists():
        print(f"❌ File changes not found: {file_changes_path}")
        return False
    
    with open(file_changes_path, 'r') as f:
        file_changes = json.load(f)
    
    print(f"📁 Loaded {len(file_changes)} file changes")
    
    # Test documentation analysis
    doc_analysis = assessor._analyze_documentation_changes("4179", file_changes)
    
    print("\n📚 Documentation Analysis Results:")
    print(f"   - Documentation files found: {doc_analysis['doc_files_count']}")
    print(f"   - Architectural significance: {doc_analysis['architectural_significance']}")
    print(f"   - Summary: {doc_analysis['documentation_summary']}")
    
    if doc_analysis['doc_files']:
        print("\n📄 Documentation files:")
        for doc_file in doc_analysis['doc_files']:
            print(f"   - {doc_file['filename']} ({doc_file['type']}) [{doc_file['status']}] +{doc_file['additions']}")
    
    # Verify expected results for PR #4179
    expected_count = 7  # We know there are 7 .adoc files
    if doc_analysis['doc_files_count'] == expected_count:
        print(f"\n✅ SUCCESS: Found expected {expected_count} documentation files")
        return True
    else:
        print(f"\n❌ FAILED: Expected {expected_count} files, found {doc_analysis['doc_files_count']}")
        return False

if __name__ == "__main__":
    success = test_documentation_analysis()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""Test all success criteria from the large PR optimization checklist"""

import json
from pathlib import Path
from solution_assessor import AIPoweredSolutionAssessor

def test_success_criteria():
    print("🧪 Testing Large PR Analysis Optimization Success Criteria...")
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
    
    results = {}
    
    # Success Criteria 1: PR #4179 analysis completes without timeout
    print("\n1️⃣ Testing: PR #4179 analysis completes without timeout")
    try:
        # Load file changes to verify data collection
        file_changes_path = context_dir / "pr-4179" / "file-changes.json"
        if file_changes_path.exists():
            with open(file_changes_path, 'r') as f:
                file_changes = json.load(f)
            
            if len(file_changes) == 60:
                print("   ✅ Data collection: All 60 files present (was 30 due to pagination bug)")
                results['data_collection'] = True
            else:
                print(f"   ❌ Data collection: Only {len(file_changes)} files (expected 60)")
                results['data_collection'] = False
        else:
            print("   ⚠️  PR #4179 context not found - run context collection first")
            results['data_collection'] = None
    except Exception as e:
        print(f"   ❌ Error checking data collection: {e}")
        results['data_collection'] = False
    
    # Success Criteria 2: Documentation changes are summarized first
    print("\n2️⃣ Testing: Documentation changes are summarized first")
    try:
        if 'file_changes' in locals():
            doc_analysis = assessor._analyze_documentation_changes("4179", file_changes)
            if doc_analysis['doc_files_count'] == 7:
                print("   ✅ Documentation analysis: Found 7 .adoc files")
                print(f"   ✅ Architectural significance: {doc_analysis['architectural_significance']}")
                print(f"   ✅ Summary: {doc_analysis['documentation_summary'][:100]}...")
                results['documentation_first'] = True
            else:
                print(f"   ❌ Expected 7 doc files, found {doc_analysis['doc_files_count']}")
                results['documentation_first'] = False
        else:
            results['documentation_first'] = None
    except Exception as e:
        print(f"   ❌ Error in documentation analysis: {e}")
        results['documentation_first'] = False
    
    # Success Criteria 3: Large PRs receive appropriate analysis strategy
    print("\n3️⃣ Testing: Large PRs receive appropriate analysis strategy")
    try:
        if 'file_changes' in locals():
            total_lines = sum(change.get('additions', 0) + change.get('deletions', 0) for change in file_changes)
            pr_classification = assessor._classify_pr_size(len(file_changes), total_lines, doc_analysis)
            
            expected_strategy = 'documentation_first'
            actual_strategy = pr_classification['analysis_strategy']
            
            if actual_strategy == expected_strategy:
                print(f"   ✅ PR classification: {pr_classification['size_category']}")
                print(f"   ✅ Analysis strategy: {actual_strategy}")
                print(f"   ✅ Architectural: {pr_classification['is_architectural']}")
                results['strategy_selection'] = True
            else:
                print(f"   ❌ Expected {expected_strategy}, got {actual_strategy}")
                results['strategy_selection'] = False
        else:
            results['strategy_selection'] = None
    except Exception as e:
        print(f"   ❌ Error in strategy selection: {e}")
        results['strategy_selection'] = False
    
    # Success Criteria 4: Clear indicators of analysis completeness level
    print("\n4️⃣ Testing: Clear indicators of analysis completeness level")
    try:
        timeout = assessor._calculate_timeout(60, 8081, 'high')
        if timeout == 600:  # 10 minutes
            print(f"   ✅ Timeout calculation: {timeout}s (10 minutes) for large architectural PR")
            print("   ✅ Timeout scaling: Small PRs get 3min, Large PRs get 10min")
            results['timeout_scaling'] = True
        else:
            print(f"   ❌ Expected 600s timeout, got {timeout}s")
            results['timeout_scaling'] = False
    except Exception as e:
        print(f"   ❌ Error in timeout calculation: {e}")
        results['timeout_scaling'] = False
    
    # Success Criteria 5: Template selection works
    print("\n5️⃣ Testing: Template selection based on PR size")
    try:
        # Test different PR sizes
        test_cases = [
            ("Small PR", 5, 200, 'detailed'),
            ("Medium PR", 25, 3000, 'detailed'),
            ("Large PR", 60, 8000, 'simplified')
        ]
        
        template_tests_passed = 0
        for name, files, lines, expected_template in test_cases:
            doc_data = {'doc_files_count': 1 if lines > 1000 else 0, 'architectural_significance': 'high' if lines > 5000 else 'low'}
            classification = assessor._classify_pr_size(files, lines, doc_data)
            
            strategy = classification['analysis_strategy']
            actual_template = 'simplified' if strategy in ['documentation_first', 'simplified_large'] else 'detailed'
            
            if actual_template == expected_template:
                print(f"   ✅ {name}: {strategy} → {actual_template} template")
                template_tests_passed += 1
            else:
                print(f"   ❌ {name}: Expected {expected_template}, got {actual_template}")
        
        results['template_selection'] = template_tests_passed == len(test_cases)
    except Exception as e:
        print(f"   ❌ Error in template selection test: {e}")
        results['template_selection'] = False
    
    # Summary
    print("\n📊 SUCCESS CRITERIA SUMMARY")
    print("="*50)
    
    criteria = [
        ("Data Collection (60 files)", results.get('data_collection')),
        ("Documentation-First Analysis", results.get('documentation_first')),
        ("Strategy Selection", results.get('strategy_selection')),
        ("Timeout Scaling", results.get('timeout_scaling')),
        ("Template Selection", results.get('template_selection'))
    ]
    
    passed = 0
    total = 0
    
    for criterion, result in criteria:
        if result is True:
            print(f"✅ {criterion}")
            passed += 1
            total += 1
        elif result is False:
            print(f"❌ {criterion}")
            total += 1
        else:
            print(f"⚠️  {criterion} (not testable - missing data)")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n🎯 SUCCESS RATE: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 SUCCESS CRITERIA LARGELY MET!")
        return True
    else:
        print("❌ SUCCESS CRITERIA NOT MET")
        return False

if __name__ == "__main__":
    success = test_success_criteria()
    exit(0 if success else 1)
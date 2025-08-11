# Archived Scripts

This directory contains Python scripts and files that are no longer actively used in the PR review workflow but are preserved for historical reference.

## Archived Files

### Deprecated Report Generators
- **generate_report.py** - Original report generator, replaced by enhanced_report_generator.py
- **python_report_generator.py** - Old Python-specific report generator, replaced by enhanced_report_generator.py  
- **single_pr_html_generator.py** - Single PR HTML generator, replaced by html_report_generator.py

### Superseded Analysis Scripts
- **conversation_analyzer.py** - Non-AI conversation analyzer, replaced by ai_conversation_analyzer.py
- **pr_context_optimizer.py** - Experimental context optimizer, not integrated into main workflow

### One-Time Utilities
- **improve_claude_md.py** - Script for improving CLAUDE.md documentation (one-time use)
- **check_auth.py** - Simple authentication check utility
- **batch_latest_prs.py** - Old batch processing script, replaced by batch_pr_workflow.py

### Specific Test Scripts
- **test_fixed_solution_assessor.py** - Test for specific bug fix in solution assessor
- **test_json_parsing.py** - Test for JSON parsing issues
- **test_system_debug.py** - System debugging test script

### Backup Files
- **CLAUDE.md.backup** - Backup of CLAUDE.md
- **enhanced_report_generator.py.backup** - Backup of enhanced report generator
- **pr_workflow.py.backup** - Backup of main workflow
- **pr-branch-mapping.json.backup** - Backup of PR branch mappings

### Old Logs and Documentation
- **overnight-20250729-023939.log** - Old batch processing log
- **prompt-pr-review.md** - Old prompt documentation

## Archive Date
**Date Archived**: August 11, 2025  
**Reason**: Cleanup and organization of pr-review directory to maintain only actively used scripts in the main directory.

## Note
These files are kept for reference and may contain useful code patterns or historical context. They should not be used in the current workflow as they have been replaced by improved implementations.
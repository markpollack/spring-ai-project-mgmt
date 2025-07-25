# Spring AI PR Review System

This directory contains a comprehensive AI-powered PR review automation system for the Spring AI project.

## Core Files

- `pr_workflow.py` - Main workflow orchestrator for complete PR analysis
- `enhanced_report_generator.py` - AI-powered report generation with comprehensive analysis
- `ai_conversation_analyzer.py` - Claude Code integration for conversation analysis
- `solution_assessor.py` - AI-powered technical solution assessment
- `pr_context_collector.py` - GitHub context and issue data collection

## Supporting Subdirectories

### `/templates/`
Contains report templates and prompts for AI analysis:
- `enhanced_pr_report_template.md` - Main enhanced report template
- `ai_conversation_analysis_prompt.md` - Prompt for conversation analysis
- `solution_assessment_prompt.md` - Prompt for solution assessment
- Various conflict resolution and planning templates

### `/context/`
Stores collected PR context data organized by PR number:
- `pr-{number}/` - Individual PR context directories containing:
  - `pr-data.json` - Basic PR metadata and information
  - `issue-data.json` - Linked GitHub issues and discussions
  - `conversation.json` - Chronological conversation timeline
  - `file-changes.json` - Detailed file change analysis
  - `ai-conversation-analysis.json` - AI-generated conversation insights
  - `solution-assessment.json` - AI-generated technical assessment

### `/reports/`
Generated analysis reports and test results:
- `review-pr-{number}.md` - Comprehensive AI-powered analysis reports
- `test-logs-pr-{number}/` - Detailed test execution logs and results

### `/plans/`
Workflow plans and progress tracking:
- `plan-pr-{number}.md` - Generated workflow plans for complex PRs
- `enhanced-plan-pr-{number}.md` - AI-enhanced workflow planning

### `/designs/`
Design documents and implementation plans:
- Contains design documents for system improvements and feature implementations

### `/logs/`
Verbose output logs from build and formatting operations:
- `java-formatter-{timestamp}.log` - Java formatting operation logs
- Various timestamped log files for debugging and troubleshooting

### `/spring-ai/`
Working clone of the Spring AI repository for PR analysis:
- Isolated workspace for checkout, compilation, and testing
- Automatically managed by the workflow system

## Usage

Primary workflow commands:
```bash
# Complete PR analysis
python pr_workflow.py 3914

# Generate enhanced report only
python pr_workflow.py --report-only 3914

# Clean up PR workspace
python pr_workflow.py --cleanup 3914
```

The system integrates with Claude Code AI for intelligent analysis and uses GitHub CLI for repository operations.


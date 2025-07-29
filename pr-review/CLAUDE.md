# Spring AI PR Review System

This directory contains a comprehensive AI-powered PR review automation system for the Spring AI project.

## Core Files

- `pr_workflow.py` - Main workflow orchestrator for complete PR analysis
- `enhanced_report_generator.py` - AI-powered report generation with comprehensive analysis
- `ai_conversation_analyzer.py` - Claude Code integration for conversation analysis
- `solution_assessor.py` - AI-powered technical solution assessment
- `ai_risk_assessor.py` - AI-powered security and quality risk assessment
- `backport_assessor.py` - AI-powered backport candidate evaluation for maintenance branches
- `commit_message_generator.py` - AI-powered comprehensive commit message generation
- `pr_context_collector.py` - GitHub context and issue data collection
- `claude_code_wrapper.py` - Robust utility class for Claude Code CLI integration
- `animated_progress.py` - ASCII progress animation for long-running AI operations

## Supporting Subdirectories

### `/templates/`
Contains report templates and prompts for AI analysis:
- `enhanced_pr_report_template.md` - Main enhanced report template
- `ai_conversation_analysis_prompt.md` - Prompt for conversation analysis
- `solution_assessment_prompt.md` - Prompt for solution assessment
- `backport-candidate.md` - Spring AI 1.0.x backporting evaluation criteria
- `review-commit-message.md` - Comprehensive commit message generation template
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
- `claude-prompt-*.txt` - Saved prompts sent to Claude Code for debugging
- `claude-response-*.txt` - Claude Code responses saved for troubleshooting
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

## Claude Code Integration

All AI-powered analysis components use the robust `ClaudeCodeWrapper` utility class for reliable Claude Code integration:

### Key Features
- **File Reading Approach**: Leverages Claude Code's native file reading capability by specifying file paths in prompts
- **Permissions Handling**: Uses `--dangerously-skip-permissions` to handle temporary files
- **Token-Based Limits**: Uses 80,000 token limit (~62,000 words) with 1 word = 1.3 tokens estimation
- **Fail-Fast Approach**: Exits immediately if analysis fails (no fallback to placeholder data)
- **Comprehensive Error Handling**: Proper timeout handling, error reporting, and debug logging
- **Debug Logging**: All prompts and responses saved to `/logs/` directory for troubleshooting
- **Direct File Access**: Claude Code reads files directly when given file paths in prompts (never use stdin piping)

### Claude Code Integration Best Practices
- **Always use file paths**: Structure prompts like `"Please read the file /path/to/file.java and analyze it"`
- **Never use stdin**: Claude Code file reading works best with direct file access, not piped content
- **Use --dangerously-skip-permissions**: Required for temporary files and workspace access
- **Expect markdown responses**: Claude Code returns analysis in markdown format, parse JSON from code blocks

### Components Using ClaudeCodeWrapper
- `ai_conversation_analyzer.py` - For parsing PR conversations and generating insights
- `solution_assessor.py` - For technical solution quality assessment
- `ai_risk_assessor.py` - For security and quality risk evaluation
- `backport_assessor.py` - For evaluating backport candidate eligibility
- `commit_message_generator.py` - For generating comprehensive commit messages
- `pr_workflow.py` - For automated conflict resolution

### Usage Pattern
```python
from claude_code_wrapper import ClaudeCodeWrapper

claude = ClaudeCodeWrapper()
if claude.is_available():
    result = claude.analyze_from_file(prompt_file, output_file, use_json_output=True, show_progress=True)
    if result['success']:
        response = result['response']
```

This ensures consistent, reliable Claude Code integration across all system components.

## Progress Animation System

### Overview
The system includes ASCII progress animations for long-running Claude Code operations (typically 13-15+ seconds). This provides visual feedback that the system is actively processing instead of appearing frozen.

### Animation Features
- **Professional Braille Spinner**: `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏` (Unicode-based, works on most terminals)
- **Real-time Duration**: Shows elapsed time: `⠋ 🧠 Claude Code analyzing... 7.3s`
- **Thread-safe Implementation**: Non-blocking animation runs in background thread
- **Clean Shutdown**: Animation stops cleanly when Claude Code operation completes
- **Configurable**: Can be disabled with `show_progress=False` parameter

### Where Animations Appear
Progress animations are integrated into all major AI analysis operations:

1. **AI Risk Assessment** (~15s) - Security and quality analysis
2. **AI Conversation Analysis** (~15s) - PR discussion understanding  
3. **Solution Assessment** (~15s) - Technical solution evaluation
4. **Backport Assessment** (~15s) - Maintenance branch compatibility
5. **Commit Message Generation** (~15s) - AI-powered commit messages

### Usage Example
```python
from claude_code_wrapper import ClaudeCodeWrapper

wrapper = ClaudeCodeWrapper()
# Animation enabled by default
result = wrapper.analyze_from_file("prompt.txt", show_progress=True)

# Disable animation if needed
result = wrapper.analyze_from_file("prompt.txt", show_progress=False)
```

### Implementation Details
- **File**: `animated_progress.py` - Core animation system
- **Integration**: All Claude Code wrapper calls include `show_progress=True` by default
- **Subprocess Compatibility**: Enhanced report generator removes `capture_output=True` to show animations
- **Fallback**: Gracefully handles terminals that don't support Unicode characters


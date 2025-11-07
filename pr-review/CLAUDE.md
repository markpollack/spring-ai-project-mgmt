# Spring AI PR Review System

AI-powered PR review automation system for Spring AI project with comprehensive analysis, risk assessment, and automated reporting.

📖 **For comprehensive documentation, setup instructions, and troubleshooting, see [README.md](README.md)**

## Essential Commands

```bash
# Pre-flight validation (recommended before running workflow)
python3 validate.py                          # Quick system check
python3 validate.py --verbose                # Detailed validation

# Complete PR analysis
python3 pr_workflow.py 3914

# Generate enhanced report only
python3 pr_workflow.py --report-only 3914

# Clean up PR workspace
python3 pr_workflow.py --cleanup 3914

# Batch processing multiple PRs
python3 batch_pr_workflow.py 3920 3919 3921 3922 3927 3929
```

## Core Files

- `pr_workflow.py` - Main workflow orchestrator
- `batch_pr_workflow.py` - Batch processing for multiple PRs
- `validate.py` - Pre-flight validation for system state
- `intelligent_squash.py` - Optimized commit squashing with reset_soft strategy
- `enhanced_report_generator.py` - AI-powered report generation with test failure summaries
- `ai_conversation_analyzer.py` - Claude Code conversation analysis
- `solution_assessor.py` - Technical solution assessment
- `ai_risk_assessor.py` - Security and quality risk assessment
- `backport_assessor.py` - Backport candidate evaluation
- `commit_message_generator.py` - Commit message generation
- `pr_context_collector.py` - GitHub context collection
- `claude_code_wrapper.py` - Claude Code CLI integration utility

## Code Style & Conventions

- Use `ClaudeCodeWrapper` for all Claude Code integrations
- Structure prompts with direct file paths: `"Please read the file /path/to/file.java and analyze it"`
- Never use stdin piping - always use direct file access
- Parse JSON responses from markdown code blocks
- Save all prompts/responses to `/logs/` for debugging
- Use fail-fast approach - exit immediately on analysis failures

## Development Workflow

- Use file-based analysis approach
- Token limit: 80,000 tokens (~62,000 words)
- Error handling: comprehensive timeout and debug logging
- Progress animation for operations 13+ seconds
- All AI operations show Braille spinner with elapsed time

## Environment Setup

- Requires Claude Code CLI with `--dangerously-skip-permissions` flag
- GitHub CLI for repository operations
- Python dependencies for AI analysis components
- Working Spring AI repository clone in `/spring-ai/`

## Important: Spring AI Directory Management

**Critical: Never commit spring-ai directory changes**
- The `/spring-ai/` directory is a working repository clone managed by workflow scripts
- **NEVER commit any changes from the spring-ai directory to this project**
- The directory is included in .gitignore and should always be ignored
- If you see `git status` showing changes in spring-ai/, always ignore them
- All git operations in spring-ai/ are handled by automation scripts only

## Integration Notes

### Claude Code Usage Pattern
```python
from claude_code_wrapper import ClaudeCodeWrapper

claude = ClaudeCodeWrapper()
if claude.is_available():
    result = claude.analyze_from_file(prompt_file, output_file, use_json_output=True, show_progress=True)
    if result['success']:
        response = result['response']
```

### Directory Structure
- `/templates/` - AI analysis prompts and report templates
- `/context/pr-{number}/` - PR data, issues, conversations, file changes
- `/reports/` - Generated analysis reports and test logs  
- `/plans/` - Workflow plans and progress tracking
- `/logs/` - Debug logs, prompts, and responses
- `/spring-ai/` - Working repository clone
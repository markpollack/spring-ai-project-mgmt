# spring-ai-project-mgmt
Project Management Agent for Spring AI

## Overview

This repository provides comprehensive tooling for managing the Spring AI project, including automated PR review, issue collection, and workflow automation.

## Main Components

### 1. PR Review System (`pr-review/`)
An AI-powered PR review automation system that provides comprehensive analysis of Spring AI pull requests.

**Key Features**:
- **AI-Powered Analysis**: Uses Claude Code integration for intelligent code review
- **Token-Based File Selection**: Processes up to 80,000 tokens (~62,000 words) with 1 word = 1.3 tokens estimation
- **Fail-Fast Approach**: Exits immediately if analysis fails (no fallback to placeholder data)
- **Comprehensive Context**: Collects GitHub data, conversation analysis, and file changes
- **Detailed Reports**: Generates markdown reports with risk assessment and recommendations

**Quick Start**:
```bash
cd pr-review
python pr_workflow.py 3914              # Complete PR analysis
python pr_workflow.py --report-only 3914 # Generate enhanced report only
python pr_workflow.py --cleanup 3914     # Clean up PR workspace
```

**See**: [`pr-review/CLAUDE.md`](pr-review/CLAUDE.md) for detailed documentation.

### 2. GitHub Issues Collector (`scripts/`)
A comprehensive JBang-based tool for collecting GitHub issues with advanced filtering capabilities.

**Location**: `scripts/CollectGithubIssues.java`

**Documentation**: See [`scripts/COLLECT_GITHUB_ISSUES_USER_GUIDE.md`](scripts/COLLECT_GITHUB_ISSUES_USER_GUIDE.md) for complete usage guide.

**Key Features**:
- State filtering (open/closed/all)
- Label filtering with AND/OR logic
- Batch processing with resume support
- GitHub API rate limit management
- JSON output with comprehensive metadata
- Zip archive output with command line documentation

**Quick Start**:
```bash
export GITHUB_TOKEN="your_token_here"
cd scripts
jbang CollectGithubIssues.java --repo spring-projects/spring-ai --state open --labels bug --zip
```

## Token Estimation Guidelines

For AI analysis and batching operations, the system uses:
- **Token Estimation**: 1 word = 1.3 tokens
- **File Size Estimation**: ~5 bytes per token or ~200 tokens per KB
- **Context Limits**: 80,000 tokens maximum for AI analysis

## Requirements

- Python 3.8+
- GitHub CLI (`gh`)
- Claude Code CLI
- JBang (via SDKMAN at `/home/mark/.sdkman/candidates/jbang/current/bin/jbang`)
- Java 17+ (for JBang scripts)

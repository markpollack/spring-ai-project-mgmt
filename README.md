# Spring AI Project Management

This repository contains comprehensive tooling for managing the [Spring AI project](https://github.com/spring-projects/spring-ai) using GitHub CLI and AI-powered automation.

## Overview

The repository provides four main subsystems for complete Spring AI project management:

- **PR Review System** - AI-powered pull request analysis and reporting
- **GitHub Issues Collection** - Advanced issue filtering and data collection
- **Issue Classification** - LLM-powered issue labeling (82.1% F1 score)
- **Release Management** - Automation tools for Spring AI releases

## Architecture Overview

### 1. PR Review System (`pr-review/`)
AI-powered PR review automation with comprehensive analysis capabilities.

**Core Components:**
- `pr_workflow.py` - Main workflow orchestrator
  - **Main Function**: `PRWorkflow.run_complete_workflow()` - pr_workflow.py:282
- `enhanced_report_generator.py` - AI-powered report generation
  - **Main Function**: `EnhancedReportGenerator.generate_report()` - enhanced_report_generator.py:156
- `ai_conversation_analyzer.py` - Conversation analysis
  - **Main Function**: `AIConversationAnalyzer.analyze_conversation()` - ai_conversation_analyzer.py:89
- `ai_risk_assessor.py` - Security and quality risk assessment
  - **Main Function**: `AIRiskAssessor.assess_risks()` - ai_risk_assessor.py:112
- `claude_code_wrapper.py` - Claude Code CLI integration utility
  - **Main Function**: `ClaudeCodeWrapper.run_analysis()` - claude_code_wrapper.py:248

**Key Features:**
- **AI-Powered Analysis**: Uses Claude Code integration for intelligent code review
- **Token-Based File Selection**: Processes up to 80,000 tokens (~62,000 words) with 1 word = 1.3 tokens estimation
- **Fail-Fast Approach**: Exits immediately if analysis fails (no fallback to placeholder data)
- **Comprehensive Context**: Collects GitHub data, conversation analysis, and file changes
- **Detailed Reports**: Generates markdown reports with risk assessment and recommendations

**Quick Start:**
```bash
cd pr-review
python3 pr_workflow.py 3914              # Complete PR analysis
python3 pr_workflow.py --report-only 3914 # Generate enhanced report only
python3 pr_workflow.py --cleanup 3914     # Clean up PR workspace

# Batch processing multiple PRs
python3 batch_pr_workflow.py 3920 3919 3921 3922
```

**Documentation**: [`pr-review/CLAUDE.md`](pr-review/CLAUDE.md)

### 2. GitHub Issues Collection (`scripts/`)
JBang-based and Maven-based tools for collecting GitHub issues with advanced filtering.

**Key Files:**
- `CollectGithubIssues.java` - JBang script for issue collection
  - **Main Function**: `CollectGithubIssues.main()` - CollectGithubIssues.java:217
- `project/` - Maven-based modular architecture (refactored from JBang)
  - **Main Function**: `CollectGithubIssues.run()` - project/src/main/java/org/springaicommunity/github/ai/collection/CollectGithubIssues.java:94
- `project/collection-library/` - Java-based GitHub API integration library
  - **GitHubRestService.java**: REST API wrapper using org.kohsuke:github-api
  - **PRCollectionService.java**: Full PR collection with metadata
  - **Note**: Uses Java GitHub libraries (not shell execution)
- `application.yaml` - Configuration for collection parameters

**Features:**
- State filtering (open/closed/all)
- Label filtering with AND/OR logic
- Batch processing with resume support
- GitHub API rate limit management
- JSON output with comprehensive metadata
- Zip archive output with command line documentation

**Quick Start:**
```bash
export GITHUB_TOKEN="your_token_here"
cd scripts

# JBang Script (Legacy)
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --repo spring-projects/spring-ai --state open

# Maven Project (Current)
cd project
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --dry-run"
```

**Documentation**: [`scripts/README.md`](scripts/README.md)

### 3. Issue Classification (`issue-analysis/`, `scripts/project/classification-engine/`)
LLM-powered multi-label classification of GitHub issues, achieving **82.1% F1 score** on 111 held-out test issues from the Spring AI repository.

**Key Results:**
- 76.6% precision, 88.5% recall across 35+ technical labels
- Top-performing labels: `vector store` (92.3% F1), `tool/function calling` (91.7% F1), `documentation` (90.9% F1)
- Conservative strategy focusing on objective, content-based labels

**Implementations:**
- `issue-analysis/` - Python prototype (data collection, evaluation, prompt engineering)
- `scripts/project/classification-engine/` - Java/Spring production implementation with Claude SDK integration

**Documentation**: [`issue-analysis/README.md`](issue-analysis/README.md) | [Replication Guide](SPRING_ECOSYSTEM_CLASSIFICATION_GUIDE.md)

### 4. Release Management (`release/`)
Automation tools for managing Spring AI releases.

**Components:**
- `spring-ai-point-release.py` - Point release automation
  - **Main Function**: `main()` - spring-ai-point-release.py:1893
  - **Core Workflow**: `ReleaseWorkflow.run_release_workflow()` - spring-ai-point-release.py:1368
- `spring-ai-release/` - Working release repository clone

**Quick Start:**
```bash
cd release
python3 spring-ai-point-release.py
```

## Prerequisites

### Core Requirements
- **GitHub CLI (`gh`)** - Repository operations
- **Claude Code CLI** - AI analysis (requires `--dangerously-skip-permissions`)
- **Python 3.8+** - PR review system
- **Java 17+** - Issues collection tools

### Build Tools
- **JBang** - Legacy script execution (via SDKMAN at `/home/mark/.sdkman/candidates/jbang/current/bin/jbang`)
- **Maven Daemon (`mvnd`)** - Fast builds (recommended)

### Setup
```bash
# GitHub CLI setup
gh auth login
gh repo set-default spring-projects/spring-ai

# Python environment for PR reviews
cd pr-review
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Maven setup for issue collection
cd scripts/project
mvnd clean compile -Dmaven.javadoc.skip=true -DskipTests
```

## Configuration

### Environment Variables
```bash
export GITHUB_TOKEN="your_github_token"
export CLAUDE_CODE_PATH="/path/to/claude-code"
```

### Configuration Files
- `scripts/application.yaml` - Issue collection parameters
- `pr-review/templates/` - AI analysis templates
- `scripts/project/src/test/resources/` - Test configurations

## Spring AI Release Lifecycle

- **Milestone Releases**: `1.1.0.M1`, `1.1.0.M2`, `1.1.0.M3` (feature development)
- **Release Candidate**: `1.1.0.RC1` (API freeze, final validation)  
- **General Availability**: `1.1.0` (stable production release)

### Project Boards
- [1.1 M1 Release Board](https://github.com/orgs/spring-projects/projects/38/)
- [1.0.1 Release Board](https://github.com/orgs/spring-projects/projects/40/)

## Token Estimation Guidelines

For AI analysis and batching operations:
- **Token Estimation**: 1 word = 1.3 tokens
- **File Size Estimation**: ~5 bytes per token or ~200 tokens per KB
- **Context Limits**: 80,000 tokens maximum for AI analysis

## Important Directory Management

**Critical: Spring AI Repository Clones**
- The `pr-review/spring-ai/` and `release/spring-ai-release/` directories are working clones
- Managed exclusively by Python workflow scripts
- **Never directly manipulate these directories or run git commands within them**
- All git operations handled by automation scripts with subprocess calls

## Contributing

1. Follow existing code patterns and architecture
2. Add tests for new functionality
3. Update documentation as needed
4. Use `--dry-run` flags for safe testing

For detailed subsystem documentation, see:
- [`pr-review/CLAUDE.md`](pr-review/CLAUDE.md) - PR Review System
- [`scripts/README.md`](scripts/README.md) - Issues Collection Tools
- [`release/README.md`](release/README.md) - Release Management

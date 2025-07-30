# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Spring AI Project Management

This repository contains tooling for managing the Spring AI project using GitHub CLI and AI-powered automation.

## Repository Context
- Target Repository: https://github.com/spring-projects/spring-ai
- Primary Tool: GitHub CLI (`gh`)
- Purpose: Project management automation and workflow enhancement

## Architecture Overview

The repository is organized into three main subsystems:

### 1. PR Review System (`pr-review/`)
AI-powered PR review automation with comprehensive analysis capabilities.

**Core Components:**
- `pr_workflow.py` - Main workflow orchestrator
- `enhanced_report_generator.py` - AI-powered report generation
- `ai_conversation_analyzer.py` - Conversation analysis
- `ai_risk_assessor.py` - Security and quality risk assessment
- `claude_code_wrapper.py` - Claude Code CLI integration utility

### 2. GitHub Issues Collection (`scripts/`)
JBang-based and Maven-based tools for collecting GitHub issues with advanced filtering.

**Key Files:**
- `CollectGithubIssues.java` - JBang script for issue collection
- `project/` - Maven-based modular architecture (refactored from JBang)
- `application.yaml` - Configuration for collection parameters

### 3. Release Management (`release/`)
Automation tools for managing Spring AI releases.

**Components:**
- `spring-ai-point-release.py` - Point release automation
- `spring-ai-release/` - Working release repository clone

## Development Commands

### PR Review System
```bash
cd pr-review

# Complete PR analysis
python3 pr_workflow.py 3914

# Generate enhanced report only
python3 pr_workflow.py --report-only 3914

# Clean up PR workspace
python3 pr_workflow.py --cleanup 3914

# Batch processing multiple PRs
python3 batch_pr_workflow.py 3920 3919 3921 3922 3927 3929
```

### GitHub Issues Collection

**JBang Script (Legacy):**
```bash
cd scripts
export GITHUB_TOKEN="your_token_here"

# Basic collection
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --repo spring-projects/spring-ai --state open

# With filtering
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --repo spring-projects/spring-ai --labels bug --dry-run

# Help
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --help
```

**Maven Project (Current):**
```bash
cd scripts/project

# Fast compilation (skip tests and javadoc)
mvnd clean compile -Dmaven.javadoc.skip=true -DskipTests

# Run tests
mvnd test

# Run application
mvnd spring-boot:run -Dspring-boot.run.arguments="--help"
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --dry-run"
```

### GitHub CLI Operations
```bash
# Setup
gh auth login
gh repo set-default spring-projects/spring-ai

# Issue management
gh issue list --limit 5 --json number,title,author,createdAt,state
gh issue view <issue-number>

# Pull request management
gh pr list
gh pr view <pr-number>

# Project management
gh project item-list 38 --owner spring-projects --format json
gh api repos/spring-projects/spring-ai/milestones
```

## Build Systems

### Python (PR Review)
- Uses virtual environments for dependency isolation
- Claude Code CLI integration with `--dangerously-skip-permissions` flag
- Token limit: 80,000 tokens (~62,000 words)

### JBang (Legacy Issues Collection)
- Single-file Java execution with dependency management
- Located at `/home/mark/.sdkman/candidates/jbang/current/bin/jbang`
- Dependencies embedded in script headers

### Maven (Current Issues Collection)
- Spring Boot application with modular architecture
- Java 17+ required
- Maven Daemon (`mvnd`) recommended for fast builds

## Environment Requirements

- **GitHub CLI (`gh`)** - Repository operations
- **Claude Code CLI** - AI analysis (requires `--dangerously-skip-permissions`)
- **Python 3.8+** - PR review system
- **Java 17+** - Issues collection tools
- **JBang** - Legacy script execution (via SDKMAN)
- **Maven Daemon (`mvnd`)** - Fast builds (recommended)

## Configuration Files

### GitHub Issues Collection
- `scripts/application.yaml` - Spring Boot configuration
- `scripts/project/src/test/resources/application-test.yaml` - Test configuration
- Rate limiting, batch sizes, and output directories configurable

### PR Review System
- `pr-review/templates/` - AI analysis prompts and report templates
- Environment variables for GitHub token and Claude Code paths
- Context limits and token estimation settings

## Important Directory Management

**Critical: Spring AI Repository Clone**
- The `/pr-review/spring-ai/` and `/release/spring-ai-release/` directories are working clones
- Managed exclusively by Python workflow scripts
- **Never directly manipulate these directories or run git commands within them**
- All git operations handled by automation scripts with subprocess calls

## Data Management

### File Patterns to Ignore
- `issues/` - Generated issue data
- `logs/` - Debug and operation logs  
- `batch_*` - Temporary batch files
- `target/` - Maven build artifacts
- `*.log` - Log files

### Token Estimation Guidelines
- **Token Estimation**: 1 word = 1.3 tokens
- **File Size Estimation**: ~5 bytes per token or ~200 tokens per KB
- **Context Limits**: 80,000 tokens maximum for AI analysis

## Testing Strategies

### PR Review System
- Use `--dry-run` flags for safe testing
- File-based analysis approach with direct file paths
- Comprehensive timeout and debug logging

### Issues Collection (Maven)
- **Critical**: Avoid `@SpringBootTest` - triggers CommandLineRunner production operations
- Use `@SpringJUnitConfig` with minimal TestConfiguration instead  
- Mock external dependencies (GitHub API, file system)
- Use `--dry-run` flag for collection testing

### Safety Measures
```bash
# Repository cleanup before commits
rm -rf issues/
find . -name "batch_*" -type f -delete
find . -name "logs" -type d -exec rm -rf {} + 2>/dev/null || true
```

## Common Workflows

### Adding New CLI Arguments (Issues Collection)
1. Update `CollectionProperties` class with new property and default
2. Modify argument parsing logic in `ArgumentParser.java`  
3. Add comprehensive tests for new arguments
4. Update help text and documentation

### PR Analysis Workflow
1. Context collection from GitHub API
2. File change analysis with token optimization
3. AI-powered risk assessment and conversation analysis
4. Report generation with security focus
5. Optional backport candidate evaluation

### Release Process Support
- Milestone tracking (M1, M2, M3, RC, GA releases)
- Author contribution analysis
- Documentation build verification
- Version management automation

## Security Considerations

- Never commit GitHub tokens or API keys
- Use environment variables for sensitive configuration
- Validate all user inputs in CLI parsing
- Implement proper rate limiting for GitHub API calls
- File access patterns use absolute paths for security

## Troubleshooting

### Common Issues
- **JBang not in PATH**: Use full path `/home/mark/.sdkman/candidates/jbang/current/bin/jbang`
- **Maven builds slow**: Use `mvnd` with skip flags for faster compilation
- **Tests trigger production operations**: Avoid `@SpringBootTest`, use minimal Spring context
- **Claude Code integration**: Ensure `--dangerously-skip-permissions` flag is used

### Debug Commands
```bash
# Verify GitHub connectivity
gh auth status

# Test JBang script
cd scripts && /home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --help

# Test Maven application
cd scripts/project && mvnd spring-boot:run -Dspring-boot.run.arguments="--dry-run"

# Test PR workflow (safe)
cd pr-review && python3 pr_workflow.py --cleanup 1234
```

## Project-Specific Notes

### Spring AI Release Lifecycle
- **Milestone Releases**: `1.1.0.M1`, `1.1.0.M2`, `1.1.0.M3` (feature development)
- **Release Candidate**: `1.1.0.RC1` (API freeze, final validation)  
- **General Availability**: `1.1.0` (stable production release)

### GitHub Projects
- **1.1 M1 Release Board**: https://github.com/orgs/spring-projects/projects/38/
- **1.0.1 Release Board**: https://github.com/orgs/spring-projects/projects/40/

This repository provides comprehensive tooling to support the entire Spring AI project lifecycle from issue tracking through release management.
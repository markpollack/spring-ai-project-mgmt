# Spring AI Project Management

This repository contains tooling for managing the Spring AI project using GitHub CLI.

## Repository Context
- Target Repository: https://github.com/spring-projects/spring-ai
- Primary Tool: GitHub CLI (`gh`)
- Purpose: Project management automation and workflow enhancement

## Github Projects
- 1.1 M1 Release Board: https://github.com/orgs/spring-projects/projects/38/
- Default Project Number: 38
- 1.0.1 Release Board: https://github.com/orgs/spring-projects/projects/40/
- 1.0.1 Release Project Number: 40

## Common Commands

### GitHub CLI Setup
```bash
# Authenticate with GitHub
gh auth login

# Set default repository
gh repo set-default spring-projects/spring-ai
```

### Issue Management
```bash
# List open issues
gh issue list

# List latest 5 issues with detailed JSON output
gh issue list --repo spring-projects/spring-ai --limit 5 --json number,title,author,createdAt,state

# View issue details
gh issue view <issue-number>

# Create new issue
gh issue create --title "Title" --body "Description"

# Close issue
gh issue close <issue-number>
```

### Pull Request Management
```bash
# List pull requests
gh pr list

# View PR details
gh pr view <pr-number>

# Review PR
gh pr review <pr-number>

# Merge PR
gh pr merge <pr-number>
```

### Project Management
```bash
# List projects
gh project list

# View project items
gh project item-list <project-number>

# Add item to project
gh project item-add <project-number> --url <issue-or-pr-url>

# List items in Spring AI project (project 38)
gh project item-list 38 --owner spring-projects --format json

# List all milestones
gh api repos/spring-projects/spring-ai/milestones
```

## Release Process

Spring AI follows the standard Spring project release lifecycle with three main types of releases:

### Milestone Releases (M1, M2, M3, etc.)
- **Format**: `1.1.0.M1`, `1.1.0.M2`, `1.1.0.M3`
- **Purpose**: Feature development and testing milestones
- **Characteristics**: 
  - New features and APIs may be added
  - APIs may change between milestones
  - Used for community feedback and testing
  - Multiple milestones can exist for a single major/minor version

### Release Candidate (RC)
- **Format**: `1.1.0.RC1`
- **Purpose**: Final pre-release validation
- **Characteristics**:
  - All APIs are stable and frozen
  - Only bug fixes, documentation, and testing improvements allowed
  - Typically only one RC release per version
  - Usually one week from RC to GA release
  - Prepares for General Availability release

### General Availability (GA)
- **Format**: `1.1.0` (no GA suffix)
- **Purpose**: Production-ready stable release
- **Characteristics**:
  - Final stable release for public consumption
  - All features complete and APIs stable
  - Full documentation and testing coverage

## Automation Scripts

Complex project management tasks may require bash scripts that combine multiple `gh` commands for efficient workflow automation.

## Usage Notes

- All GitHub operations should use the `gh` CLI tool
- Scripts should be created in this repository for reusable automation
- Focus on Spring AI project management workflows
- Prefer direct `gh` commands for simple operations
- Use bash scripts for complex multi-step operations


## Script creation guidance

Your bash code must follow best practices and be maintainable. Use safe and strict scripting conventions. All scripts should:

- Begin with #!/usr/bin/env bash
- Enable strict mode: set -Eeuo pipefail
- Use trap to clean up on exit or error
- Define usage/help functions
- Validate arguments and input
- Use logging functions (info, warn, error)
- Avoid using eval unless absolutely necessary
- Use functions to break down logic
- Quote all variable expansions ("$var")
- Use $() for command substitution instead of backticks
- Support --help and --version flags
- Document your code. Include inline comments and example usages. Output in markdown code blocks.

## JBang Script Usage

The repository includes JBang-based Java scripts for enhanced functionality. JBang is installed via SDKMAN but may not be in the PATH.

### JBang Location
JBang is located at: `/home/mark/.sdkman/candidates/jbang/current/bin/jbang`

### Usage Examples
```bash
# Test help functionality
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --help

# Dry run with new filtering options
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --repo spring-projects/spring-ai --state open --dry-run

# Test label filtering
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --repo spring-projects/spring-ai --labels bug --dry-run

# Combined filtering
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --repo spring-projects/spring-ai --state closed --labels bug,enhancement --label-mode any --dry-run
```

### Testing Protocol
When implementing new functionality in JBang scripts:
1. Use the full path to jbang for testing
2. Always test with --dry-run first
3. Verify help output for new options
4. Test error handling with invalid inputs
5. Confirm backward compatibility


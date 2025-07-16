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
```

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


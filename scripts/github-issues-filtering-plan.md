# GitHub Issues Filtering Implementation Plan

## Overview
Add support for filtering GitHub issues by label and state (open/closed/all) to the existing JBang GitHub Issues collector.

## Current State
The existing `CollectGithubIssues.java` script collects all issues from a repository without filtering options.

## Required Features

### 1. Issue State Filtering
- Support for `open`, `closed`, and `all` states
- Default to `closed` (current behavior)
- Command line option: `--state` or `-s`

### 2. Label Filtering
- Support for filtering by one or more labels
- Command line option: `--labels` or `-l`
- Comma-separated list of labels
- Support for exact label name matching

### 3. Label Matching Modes
- `any` mode: Issue has at least one of the specified labels (OR logic)
- `all` mode: Issue has all specified labels (AND logic)
- Default to `any` mode
- Command line option: `--label-mode`

## Implementation Changes

### 1. Add New Fields to Main Class
```java
private String issueState = "closed";
private List<String> labelFilters = new ArrayList<>();
private String labelMode = "any";
```

### 2. Command Line Argument Parsing
Add support for:
- `--state open|closed|all`
- `--labels label1,label2,label3`
- `--label-mode any|all`

### 3. Switch to GitHub Search API
Current implementation uses repository issues API. Need to switch to Search API for filtering support.

#### Search Query Builder
Create method to build GitHub search queries:
```
repo:owner/repo is:issue is:open label:"bug" label:"enhancement"
```

### 4. Update GraphQL Queries
Replace repository-based queries with search-based queries using GitHub's search API.

### 5. Configuration Updates
Add default values to configuration properties:
- `defaultState`
- `defaultLabels`
- `defaultLabelMode`

## Technical Implementation Details

### Search API Limitations
- Search API has lower rate limits (30 requests/minute)
- Results limited to 1000 issues per query
- May need time-based pagination for large datasets

### Query Examples
- Open bugs: `repo:spring-projects/spring-ai is:issue is:open label:"bug"`
- Closed enhancements: `repo:spring-projects/spring-ai is:issue is:closed label:"enhancement"`
- All issues with multiple labels: `repo:spring-projects/spring-ai is:issue label:"bug" label:"priority:high"`

## Command Line Examples
```bash
# Get open issues only
./CollectGithubIssues.java --repo spring-projects/spring-ai --state open

# Get issues with specific label
./CollectGithubIssues.java --repo spring-projects/spring-ai --labels bug

# Get issues with multiple labels (any match)
./CollectGithubIssues.java --repo spring-projects/spring-ai --labels bug,enhancement --label-mode any

# Get closed issues with all specified labels
./CollectGithubIssues.java --repo spring-projects/spring-ai --state closed --labels bug,priority:high --label-mode all
```

## Validation Requirements
- Validate state is one of: open, closed, all
- Validate label-mode is one of: any, all
- Handle empty label lists gracefully
- Provide clear error messages for invalid inputs

## Backward Compatibility
- All existing functionality preserved
- Default behavior unchanged (closed issues, no label filtering)
- Existing command line options continue to work
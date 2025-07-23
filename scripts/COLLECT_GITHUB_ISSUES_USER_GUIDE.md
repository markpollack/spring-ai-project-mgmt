# GitHub Issues Collector - User Guide

A comprehensive JBang-based tool for collecting GitHub issues from repositories using GitHub's GraphQL and REST APIs with advanced filtering capabilities.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Basic Usage](#basic-usage)
- [Filtering Options](#filtering-options)
- [Output Format](#output-format)
- [Configuration](#configuration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [API Rate Limiting](#api-rate-limiting)

## Overview

The GitHub Issues Collector is a Spring Boot 3.x application that runs as a JBang script, designed to efficiently collect GitHub issues from repositories with powerful filtering capabilities:

- **State Filtering**: Collect open, closed, or all issues
- **Label Filtering**: Filter by single or multiple labels with AND/OR logic
- **Batch Processing**: Efficient collection in configurable batch sizes
- **Resume Support**: Continue interrupted collections
- **Rate Limiting**: Built-in GitHub API rate limit management
- **Multiple Formats**: JSON output with optional compression

## Prerequisites

- **Java 17** or higher
- **JBang** (installation instructions below)
- **GitHub Personal Access Token** with repository read permissions
- **Internet connection** for GitHub API access

### JBang Installation

```bash
# Install via SDKMAN (recommended)
sdk install jbang

# Or install manually - see https://www.jbang.dev/download/
```

If JBang is not on your PATH, you can use the full path:
```bash
/home/mark/.sdkman/candidates/jbang/current/bin/jbang
```

## Installation & Setup

1. **Set up GitHub Token**:
   ```bash
   export GITHUB_TOKEN="your_github_personal_access_token"
   ```

2. **Download the Script**:
   ```bash
   # The script is self-contained - just download CollectGithubIssues.java
   ```

3. **Verify Installation**:
   ```bash
   jbang CollectGithubIssues.java --help
   ```

## Basic Usage

### Command Syntax
```bash
jbang CollectGithubIssues.java [OPTIONS]
```

### Essential Options

| Option | Description | Default |
|--------|-------------|---------|
| `-r, --repo REPO` | Repository in format owner/repo | spring-projects/spring-ai |
| `-s, --state STATE` | Issue state: open, closed, all | closed |
| `-l, --labels LABELS` | Comma-separated list of labels | none |
| `--label-mode MODE` | Label matching: any, all | any |
| `-b, --batch-size SIZE` | Issues per batch file | 100 |
| `-d, --dry-run` | Show what would be collected | false |
| `--clean` | Clean previous collection data (default) | true |
| `--no-clean, --append` | Keep previous data, append new | false |

### Quick Start Example
```bash
# Collect all closed issues from spring-ai repository
jbang CollectGithubIssues.java

# Collect open bugs with dry-run first
jbang CollectGithubIssues.java --state open --labels bug --dry-run
jbang CollectGithubIssues.java --state open --labels bug
```

## Filtering Options

### State Filtering

Control which issues to collect based on their state:

```bash
# Collect only open issues
jbang CollectGithubIssues.java --state open

# Collect only closed issues (default)
jbang CollectGithubIssues.java --state closed

# Collect all issues (open + closed)
jbang CollectGithubIssues.java --state all
```

### Label Filtering

Filter issues by labels with flexible matching modes:

#### Single Label
```bash
# Collect issues with "bug" label
jbang CollectGithubIssues.java --labels bug
```

#### Multiple Labels - ANY mode (default)
```bash
# Collect issues with "bug" OR "enhancement" labels
jbang CollectGithubIssues.java --labels bug,enhancement --label-mode any
```

⚠️ **Note**: GitHub Search API limitations mean "any" mode currently uses only the first label. A warning will be displayed.

#### Multiple Labels - ALL mode
```bash
# Collect issues with "bug" AND "priority:high" labels
jbang CollectGithubIssues.java --labels bug,priority:high --label-mode all
```

### Combined Filtering
```bash
# Open bugs only
jbang CollectGithubIssues.java --state open --labels bug

# Closed issues with multiple labels
jbang CollectGithubIssues.java --state closed --labels documentation,enhancement --label-mode all
```

## Default Behavior: Clean Start

**By default, the tool cleans previous collection data before starting a new collection.** This ensures you always get fresh, current data for analysis.

**Why clean by default?**
- **Data freshness**: Each collection represents the current state of issues
- **Analysis accuracy**: Prevents analysis of stale/mixed data  
- **Simple workflow**: "Collect → Analyze" pattern works out of the box
- **Prevents confusion**: No accidental analysis of old data

**When to use `--no-clean` or `--append`:**
- Building historical datasets over time
- Incremental collection workflows  
- When disk space for full re-collection is limited

```bash
# Default: Clean start (recommended for analysis)
jbang CollectGithubIssues.java --state open --labels bug

# Keep previous data and append new issues
jbang CollectGithubIssues.java --state open --labels bug --no-clean
```

## Output Format

### Directory Structure
```
issues/
└── raw/
    └── closed/  # or 'open' based on state filter
        └── batch_2025-07-23_12-16-41/
            ├── issues_batch_001.json
            ├── issues_batch_002.json
            ├── ...
            └── metadata.json
```

### Issue JSON Structure
```json
{
  "batchNumber": 1,
  "issues": [
    {
      "number": 3880,
      "title": "Issue title here",
      "body": "Issue description...",
      "state": "CLOSED",
      "createdAt": [2025, 7, 22, 11, 32, 49],
      "updatedAt": [2025, 7, 22, 12, 28, 49],
      "closedAt": [2025, 7, 22, 12, 25, 4],
      "url": "https://github.com/spring-projects/spring-ai/issues/3880",
      "author": {
        "login": "username",
        "name": "Display Name"
      },
      "comments": [
        {
          "author": {
            "login": "commenter",
            "name": "Commenter Name"
          },
          "body": "Comment text...",
          "createdAt": [2025, 7, 22, 11, 35, 42]
        }
      ],
      "labels": [
        {
          "name": "bug",
          "color": "d73a4a",
          "description": "Something isn't working"
        }
      ]
    }
  ],
  "timestamp": "2025-07-23_12-16-41"
}
```

### Metadata File
```json
{
  "timestamp": "2025-07-23T16:17:23.717724150Z",
  "repository": "spring-projects/spring-ai",
  "totalIssues": 1122,
  "processedIssues": 1000,
  "batchSize": 3,
  "compressed": false
}
```

## Configuration

### Command Line Options (Complete List)

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--help` | `-h` | Show help message |  |
| `--repo REPO` | `-r` | Repository (owner/repo) | spring-projects/spring-ai |
| `--state STATE` | `-s` | Issue state (open/closed/all) | closed |
| `--labels LABELS` | `-l` | Comma-separated labels |  |
| `--label-mode MODE` |  | Label matching (any/all) | any |
| `--batch-size SIZE` | `-b` | Issues per batch | 100 |
| `--dry-run` | `-d` | Preview without collection | false |
| `--incremental` | `-i` | Skip collected issues | false |
| `--compress` | `-c` | Compress output files | false |
| `--verbose` | `-v` | Enable verbose logging | false |
| `--clean` |  | Remove previous data (default) | true |
| `--no-clean, --append` |  | Keep previous data, append new | false |
| `--resume` |  | Resume interrupted collection | false |

### Configuration File

Create `application.yaml` for default settings:

```yaml
github:
  issues:
    defaultRepository: "your-org/your-repo"
    batchSize: 50
    maxRetries: 3
    retryDelay: 1000
    rateLimit: 5000
    defaultState: "closed"
    defaultLabels: []
    defaultLabelMode: "any"
```

## Examples

### Common Use Cases

#### 1. Collect All Open Issues
```bash
jbang CollectGithubIssues.java --repo myorg/myrepo --state open
```

#### 2. Collect Bug Reports Only
```bash
jbang CollectGithubIssues.java --labels bug --dry-run
jbang CollectGithubIssues.java --labels bug
```

#### 3. Collect High Priority Issues
```bash
jbang CollectGithubIssues.java \
  --labels "priority:high,bug" \
  --label-mode all \
  --state open
```

#### 4. Large Repository with Small Batches
```bash
jbang CollectGithubIssues.java \
  --repo kubernetes/kubernetes \
  --batch-size 25 \
  --compress \
  --verbose
```

#### 5. Resume Interrupted Collection
```bash
jbang CollectGithubIssues.java --resume
```

### Advanced Filtering Examples

#### Documentation Issues
```bash
jbang CollectGithubIssues.java \
  --labels documentation \
  --state all \
  --batch-size 50
```

#### Recently Closed Bugs
```bash
jbang CollectGithubIssues.java \
  --state closed \
  --labels bug \
  --verbose
```

#### Enhancement Requests
```bash
jbang CollectGithubIssues.java \
  --labels enhancement,feature \
  --label-mode any \
  --state open
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
```
Error: GitHub API authentication failed
```
**Solution**: Verify your `GITHUB_TOKEN` environment variable:
```bash
echo $GITHUB_TOKEN  # Should show your token
export GITHUB_TOKEN="ghp_your_token_here"
```

#### 2. Repository Not Found
```
Error: Repository 'owner/repo' not found or not accessible
```
**Solution**: 
- Check repository name spelling
- Ensure your token has access to the repository
- For private repos, token needs appropriate permissions

#### 3. Rate Limit Exceeded
```
Warning: GitHub API rate limit approaching
```
**Solution**: The tool automatically handles rate limits, but you can:
- Use smaller batch sizes: `--batch-size 25`
- Enable verbose logging to monitor: `--verbose`
- Check current rate limit: Tool displays remaining requests

#### 4. JBang Not Found
```
jbang: command not found
```
**Solution**: Use full path or fix installation:
```bash
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --help
```

#### 5. No Issues Found
```
Total issues found: 0
```
**Solution**: 
- Verify repository has issues matching your filters
- Try `--dry-run` to see the search query being used
- Check if labels exist in the repository

### Debugging Tips

#### 1. Use Dry-Run Mode
Always test with `--dry-run` first:
```bash
jbang CollectGithubIssues.java --repo myorg/myrepo --labels bug --dry-run
```

#### 2. Enable Verbose Logging
```bash
jbang CollectGithubIssues.java --verbose
```

#### 3. Check Search Query
Look for log messages showing the generated search query:
```
Search query: repo:spring-projects/spring-ai is:issue is:open label:"bug"
```

#### 4. Verify API Connectivity
The tool tests GitHub API connectivity on startup:
```
GitHub API connectivity test passed
GitHub API Rate Limit - Remaining: 4950/5000
```

## API Rate Limiting

### Understanding GitHub Rate Limits

- **GraphQL API**: 5,000 points per hour
- **REST API**: 5,000 requests per hour
- **Search API**: 30 requests per minute (used for filtered queries)

### Rate Limit Management

The tool automatically:
- Monitors rate limit usage
- Implements exponential backoff on rate limit errors
- Displays remaining rate limit in logs
- Pauses collection when approaching limits

### Optimizing for Rate Limits

```bash
# Use smaller batches for large collections
jbang CollectGithubIssues.java --batch-size 25

# Use filtering to reduce total API calls
jbang CollectGithubIssues.java --labels bug --state open

# Monitor usage with verbose logging
jbang CollectGithubIssues.java --verbose
```

### Rate Limit Information
```bash
# Check current rate limit status (shown in logs)
GitHub API Rate Limit - Remaining: 4950/5000
```

---

## Support

For issues or questions:
1. Check this user guide
2. Review the troubleshooting section
3. Use `--dry-run` to test your filters
4. Enable `--verbose` logging for debugging
5. Check GitHub API status: https://www.githubstatus.com/

## Version History

- **v1.0.0**: Initial implementation with basic collection
- **v2.0.0**: Added state and label filtering capabilities
- **Current**: Full filtering support with comprehensive testing
# GitHub Issues & Pull Requests Collector - User Guide

A comprehensive Maven-based Spring Boot tool for collecting GitHub issues and pull requests from repositories using GitHub's GraphQL and REST APIs with advanced filtering capabilities.

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

The GitHub Issues & Pull Requests Collector is a Spring Boot 3.x Maven application designed to efficiently collect GitHub issues and pull requests from repositories with powerful filtering capabilities:

### Issue Collection Features
- **State Filtering**: Collect open, closed, or all issues
- **Label Filtering**: Filter by single or multiple labels with AND/OR logic
- **Dashboard Support**: Limited result sets with sorting for UI applications
- **Batch Processing**: Efficient collection in configurable batch sizes
- **Resume Support**: Continue interrupted collections
- **Rate Limiting**: Built-in GitHub API rate limit management
- **Multiple Formats**: JSON output with optional compression

### Pull Request Collection Features (New!)
- **PR Collection**: Collect specific pull requests or all PRs from a repository
- **Soft Approval Detection**: Identify PRs with approvals from contributors (not members)
- **Review Analysis**: Collect and analyze PR reviews and author associations
- **PR State Filtering**: Filter by open, closed, merged, or all PR states
- **Specific PR Targeting**: Collect individual PRs by number

## Architecture

This application uses a modular Spring Boot architecture with the following components:

### Core Modules

- **DataModels.java**: Record definitions for GitHub API data structures
  - Issue collection: `Issue`, `Comment`, `Author`, `Label`
  - **PR collection**: `PullRequest`, `Review` (with author association for soft approval detection)
  - Collection metadata: `CollectionRequest`, `CollectionResult`
- **ConfigurationSupport.java**: Spring configuration classes and application properties
  - `GitHubConfig`: Spring beans for GitHub API clients (GitHub, RestClient, GraphQL, ObjectMapper)
  - `CollectionProperties`: Configuration properties with defaults for collection behavior
- **ArgumentParser.java**: Command-line argument parsing and validation
  - Pure Java implementation with comprehensive CLI argument support
  - **PR collection arguments**: `--type prs`, `--number`, `--pr-state`
  - `ParsedConfiguration`: Type-safe parsed argument results
  - Environment validation and help text generation
- **GitHubServices.java**: GitHub API service classes
  - `GitHubRestService`: GitHub REST API operations and search query building
  - **PR methods**: `getPullRequest()`, `getPullRequestReviews()`, `buildPRSearchQuery()`
  - `GitHubGraphQLService`: GraphQL query execution and issue counting
  - `JsonNodeUtils`: Safe JSON navigation with Optional return types
- **IssueCollectionService.java**: Core business logic for issue collection
  - Main collection orchestration and workflow management
  - Batch processing with adaptive sizing based on issue content
  - File operations, compression, and metadata generation
  - Resume state management and error recovery with exponential backoff
  - Search query building with advanced filtering capabilities
- **CollectGithubIssuesApp.java**: Main Spring Boot application class with CommandLineRunner
  - **PR collection logic**: `collectPullRequests()` method
  - **Soft approval detection**: `detectSoftApproval()` method for contributor reviews

### Configuration Properties

The application uses Spring Boot's `@ConfigurationProperties` with the prefix `github.issues`:

```yaml
github:
  issues:
    defaultRepository: "spring-projects/spring-ai"
    batchSize: 100
    maxBatchSizeBytes: 1048576  # 1MB
    maxRetries: 3
    defaultState: "closed"
    defaultLabelMode: "any"
    verbose: false
    debug: false
```

## Prerequisites

- **Java 17** or higher
- **Maven 3.6+** or **Maven Daemon (mvnd)** for faster builds
- **GitHub Personal Access Token** with repository read permissions
- **Internet connection** for GitHub API access

### Maven Installation

```bash
# Install via SDKMAN (recommended)
sdk install maven

# Or install Maven Daemon for faster builds
sdk install mvnd

# Verify installation
mvn --version
# or
mvnd --version
```

## Building and Testing

### Quick Start

```bash
# 1. Clone and navigate to project
cd /path/to/collection-project

# 2. Set GitHub token for integration tests (optional)
export GITHUB_TOKEN="your_github_token_here"

# 3. Build and run unit tests
mvn clean test

# 4. Run integration tests (requires GitHub token)
mvn verify -Pintegration-tests

# 5. Build the application
mvn clean package
```

### Test Categories

This project follows standard Maven testing conventions:

#### Unit Tests (162 tests)
```bash
# Run only unit and component tests (fast)
mvn test

# Or with Maven Daemon for faster execution
mvnd test
```

**What's tested:**
- Individual class functionality with mocks
- Spring context wiring and configuration
- CLI argument parsing and validation
- Data model serialization/deserialization
- Service interactions with mocked dependencies

#### Integration Tests (3 test classes)
```bash
# Run integration tests (requires GITHUB_TOKEN)
export GITHUB_TOKEN="your_token"
mvn verify -Pintegration-tests

# Run ONLY integration tests (skip unit tests)
export GITHUB_TOKEN="your_token"
mvn verify -Pintegration-tests -DskipUnitTests

# Run specific integration test
mvn verify -Pintegration-tests -Dit.test=GitHubRestServiceIT
```

**What's tested:**
- Real GitHub API connectivity (REST and GraphQL)
- Actual JSON file generation and validation
- End-to-end issue collection workflow
- Error handling with real API responses

#### Complete Test Suite
```bash
# Run both unit and integration tests
export GITHUB_TOKEN="your_token"
mvn clean verify -Pintegration-tests
```

### Build Commands

#### Development Builds
```bash
# Fast compilation (no tests, no javadoc)
mvnd clean compile -Dmaven.javadoc.skip=true -DskipTests

# Quick test run
mvnd test

# Full build with unit tests
mvnd clean package
```

#### Production Builds
```bash
# Complete build with all tests
export GITHUB_TOKEN="your_token"
mvn clean verify -Pintegration-tests

# Create distribution package
mvn clean package
```

#### Test-Specific Commands
```bash
# Unit tests only (default)
mvn test

# Integration tests only (skip unit tests)
export GITHUB_TOKEN="your_token"
mvn verify -Pintegration-tests -DskipUnitTests

# Skip both unit and integration tests
mvn verify -Pintegration-tests -DskipTests

# Run tests with specific patterns
mvn test -Dtest="*ArgumentParser*"
mvn verify -Pintegration-tests -Dit.test="*RestService*"
```

### Build and Test Troubleshooting

#### Integration Tests Skipped
```
Tests run: 0, Failures: 0, Errors: 0, Skipped: X
```
**Cause**: Missing `GITHUB_TOKEN` environment variable  
**Solution**: Set the token before running:
```bash
export GITHUB_TOKEN="your_github_token_here"
mvn verify -Pintegration-tests
```

#### Integration Test Failures
```
401 Unauthorized or 403 Forbidden
```
**Cause**: Invalid or expired GitHub token  
**Solution**: Create a new Personal Access Token with `public_repo` scope

#### Build Slow
**Cause**: Maven downloading dependencies or running all tests  
**Solution**: Use Maven Daemon and skip unnecessary steps:
```bash
mvnd clean compile -DskipTests -Dmaven.javadoc.skip=true
```

#### Test Compilation Errors
**Cause**: Missing dependencies or Java version issues  
**Solution**: Verify Java 17+ and clean rebuild:
```bash
java --version  # Should be 17+
mvnd clean compile
```

### Performance Tips

- **Use Maven Daemon (`mvnd`)** instead of `mvn` for 2-3x faster builds
- **Skip tests during development** with `-DskipTests` 
- **Skip javadoc generation** with `-Dmaven.javadoc.skip=true`
- **Run integration tests selectively** using `-Dit.test=ClassName`

## Installation & Setup

1. **Set up GitHub Token**:
   ```bash
   export GITHUB_TOKEN="your_github_personal_access_token"
   ```

2. **Clone or Download the Project**:
   ```bash
   # Navigate to the project directory
   cd /path/to/collection-project
   ```

3. **Build the Project**:
   ```bash
   # Using Maven Daemon (recommended for faster builds)
   mvnd clean compile
   
   # Or using standard Maven
   mvn clean compile
   ```

4. **Verify Installation**:
   ```bash
   mvnd spring-boot:run -Dspring-boot.run.arguments="--help"
   ```

## Basic Usage

### Command Syntax
```bash
# Using Maven Daemon (recommended)
mvnd spring-boot:run -Dspring-boot.run.arguments="[OPTIONS]"

# Using standard Maven  
mvn spring-boot:run -Dspring-boot.run.arguments="[OPTIONS]"
```

### Essential Options

#### Common Options
| Option | Description | Default |
|--------|-------------|---------|
| `-r, --repo REPO` | Repository in format owner/repo | spring-projects/spring-ai |
| `-b, --batch-size SIZE` | Items per batch file | 100 |
| `-d, --dry-run` | Show what would be collected | false |
| `--clean` | Clean previous collection data (default) | true |
| `--no-clean, --append` | Keep previous data, append new | false |
| `-z, --zip` | Create zip archive of collected data | false |

#### Issue Collection Options
| Option | Description | Default |
|--------|-------------|---------|
| `-s, --state STATE` | Issue state: open, closed, all | closed |
| `-l, --labels LABELS` | Comma-separated list of labels | none |
| `--label-mode MODE` | Label matching: any, all | any |
| `--max-issues COUNT` | Limit total issues collected | unlimited |
| `--sort-by FIELD` | Sort field: updated, created, comments, reactions | updated |
| `--sort-order ORDER` | Sort order: desc, asc | desc |

#### Pull Request Collection Options (New!)
| Option | Description | Default |
|--------|-------------|---------|
| `-t, --type TYPE` | Collection type: issues, prs | issues |
| `-n, --number NUMBER` | Specific PR number to collect | all |
| `--pr-state STATE` | PR state: open, closed, merged, all | open |

### Quick Start Examples

#### Issue Collection
```bash
# Collect all closed issues from spring-ai repository
mvnd spring-boot:run -Dspring-boot.run.arguments="--state closed"

# Collect open bugs with dry-run first
mvnd spring-boot:run -Dspring-boot.run.arguments="--state open --labels bug --dry-run"
mvnd spring-boot:run -Dspring-boot.run.arguments="--state open --labels bug --zip"

# Dashboard use case: Get 20 most recent open issues
mvnd spring-boot:run -Dspring-boot.run.arguments="--state open --max-issues 20 --sort-by updated"
```

#### Pull Request Collection (New!)
```bash
# Collect specific PR and detect soft approval
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --number 4347 --dry-run"
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --number 4347"

# Collect all open PRs from repository
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --pr-state open"

# Collect recently merged PRs with labels
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --pr-state merged --labels bug --max-issues 10"
```

#### Soft Approval Detection
The PR collection feature includes soft approval detection:
```bash
# Example output when collecting PR #4347:
# Found approval from sunyuhan1998 (association: CONTRIBUTOR)
# Soft approval detected from contributor: sunyuhan1998
# Soft approval detected: true
```

**Soft approvals** are approvals from contributors with `CONTRIBUTOR` or `FIRST_TIME_CONTRIBUTOR` association that don't count toward formal merge requirements but indicate community support.

## Development

### Current Status (All Phases Complete!)
- ✅ JBang script converted to Maven project
- ✅ Spring Boot parent POM and dependencies configured
- ✅ Test dependencies added (spring-boot-starter-test, assertj-core)
- ✅ Correct package structure: `org.springaicommunity.github.ai.collection`
- ✅ **DataModels.java extracted** - Pure data structures with comprehensive tests
- ✅ **ConfigurationSupport.java extracted** - Spring configuration and properties
- ✅ **ArgumentParser.java extracted** - Command-line parsing with Spring @Component
- ✅ **GitHubServices.java extracted** - API service classes with PR support
- ✅ **IssueCollectionService.java extracted** - Core business logic
- ✅ **PR Collection implemented** - Full pull request collection with soft approval detection
- ✅ All core functionality preserved, verified, and enhanced

### Maven Commands

```bash
# Fast compilation (recommended during development)
mvnd clean compile -Dmaven.javadoc.skip=true -DskipTests

# Full build with tests (when tests are added)
mvnd clean package

# Run application (fully functional!)
mvnd spring-boot:run -Dspring-boot.run.arguments="--help"

# Test PR collection
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --number 4347 --dry-run"
```

### Modular Architecture Progress (Complete!)
1. **Phase 1**: ✅ DataModels.java - Pure data structures (16 tests, all passing)
2. **Phase 2**: ✅ ConfigurationSupport.java (Spring configuration extracted)
3. **Phase 3**: ✅ ArgumentParser.java (CLI processing with @Component)
4. **Phase 4**: ✅ GitHubServices.java (API interactions with PR support)
5. **Phase 5**: ✅ IssueCollectionService.java (business logic extracted)
6. **Phase 6**: ✅ Comprehensive test suite (162 tests passing)
7. **Phase 7**: ✅ PR collection integration and documentation

## Filtering Options

### Collection Type Selection

Choose between issue and pull request collection:

```bash
# Collect issues (default)
mvnd spring-boot:run -Dspring-boot.run.arguments="--type issues --state open"

# Collect pull requests
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --pr-state open"
```

### Issue State Filtering

Control which issues to collect based on their state:

```bash
# Collect only open issues
mvnd spring-boot:run -Dspring-boot.run.arguments="--state open"

# Collect only closed issues (default)
mvnd spring-boot:run -Dspring-boot.run.arguments="--state closed"

# Collect all issues (open + closed)
mvnd spring-boot:run -Dspring-boot.run.arguments="--state all"
```

### Pull Request State Filtering

Control which PRs to collect based on their state:

```bash
# Collect only open PRs (default for PR collection)
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --pr-state open"

# Collect only closed PRs
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --pr-state closed"

# Collect only merged PRs
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --pr-state merged"

# Collect all PRs (open + closed + merged)
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --pr-state all"
```

### Label Filtering

Filter issues by labels with flexible matching modes:

#### Single Label
```bash
# Collect issues with "bug" label
mvnd spring-boot:run -Dspring-boot.run.arguments="--labels bug"
```

#### Multiple Labels - ANY mode (default)
```bash
# Collect issues with "bug" OR "enhancement" labels
mvnd spring-boot:run -Dspring-boot.run.arguments="--labels bug,enhancement --label-mode any"
```

⚠️ **Note**: GitHub Search API limitations mean "any" mode currently uses only the first label. A warning will be displayed.

#### Multiple Labels - ALL mode
```bash
# Collect issues with "bug" AND "priority:high" labels
mvnd spring-boot:run -Dspring-boot.run.arguments="--labels bug,priority:high --label-mode all"
```

### Specific Pull Request Collection

Target specific PRs by number:

```bash
# Collect specific PR with soft approval detection
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --number 4347"

# Dry run for specific PR
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --number 4347 --dry-run"

# Collect specific PR with verbose output
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --number 4347 --verbose"
```

### Combined Filtering Examples

```bash
# Open bugs only
mvnd spring-boot:run -Dspring-boot.run.arguments="--state open --labels bug"

# Closed issues with multiple labels
mvnd spring-boot:run -Dspring-boot.run.arguments="--state closed --labels documentation,enhancement --label-mode all"

# Recently merged PRs with bug label
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --pr-state merged --labels bug --max-issues 10"

# Open PRs from contributors (for soft approval analysis)
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --pr-state open --verbose"
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

## Output Formats

The tool supports two output formats:

### 1. Standard JSON Output (Default)

#### Directory Structure
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
  "zipped": false
}
```

### 2. Zip Archive Output (`--zip`)

When using the `--zip` flag, all output is packaged into a single compressed archive for easy sharing and uploading.

#### Archive Structure
```
issues-compressed/
└── spring-projects-spring-ai_open_2025-07-23_12-46-56_labels-design.zip
    ├── collection-info.md      # Command line arguments and reproduction info
    ├── issues_batch_001.json   # Collected issues data
    ├── issues_batch_002.json   # Additional batches as needed
    └── metadata.json           # Collection metadata
```

#### Archive Naming Convention
```
{repository}_{state}_{timestamp}_{filters}.zip
```

Examples:
- `spring-projects-spring-ai_open_2025-07-23_12-46-56_labels-design.zip`
- `kubernetes-kubernetes_closed_2025-07-23_14-30-15_labels-bug-priority-high.zip`
- `microsoft-vscode_all_2025-07-23_16-20-42.zip`

#### Collection Info File
Each zip archive includes a `collection-info.md` file with:
- **Original Command**: Exact command to reproduce the collection
- **Collection Parameters**: All settings and filters used
- **Usage Notes**: Instructions for reproduction

Example `collection-info.md`:
```markdown
# GitHub Issues Collection - Command Line Arguments
# Generated: 2025-07-23T12:46:56.988172944

## Original Command
```bash
jbang CollectGithubIssues.java --repo spring-projects/spring-ai --state open --labels design --zip
```

## Collection Parameters
- **Repository**: spring-projects/spring-ai
- **Issue State**: open
- **Label Filters**: design
- **Label Mode**: any
- **Batch Size**: 100
- **Create Zip**: true

## Usage Notes
This zip archive contains all issues and metadata collected using the above parameters.
To reproduce this collection, run the command shown above.
```

#### Benefits of Zip Output
- **Single File**: Easy to upload, share, and manage
- **Complete Provenance**: Full command line arguments for reproduction
- **Compressed**: Reduced file size for efficient transfer
- **Self-Documenting**: Includes all necessary information for understanding the dataset

## Configuration

### Command Line Options (Complete List)

#### Common Options
| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--help` | `-h` | Show help message |  |
| `--repo REPO` | `-r` | Repository (owner/repo) | spring-projects/spring-ai |
| `--batch-size SIZE` | `-b` | Items per batch | 100 |
| `--dry-run` | `-d` | Preview without collection | false |
| `--incremental` | `-i` | Skip collected items | false |
| `--zip` | `-z` | Create zip archive of collected data | false |
| `--verbose` | `-v` | Enable verbose logging | false |
| `--clean` |  | Remove previous data (default) | true |
| `--no-clean, --append` |  | Keep previous data, append new | false |
| `--resume` |  | Resume interrupted collection | false |

#### Issue Collection Options
| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--state STATE` | `-s` | Issue state (open/closed/all) | closed |
| `--labels LABELS` | `-l` | Comma-separated labels |  |
| `--label-mode MODE` |  | Label matching (any/all) | any |
| `--max-issues COUNT` |  | Limit total issues collected | unlimited |
| `--sort-by FIELD` |  | Sort field: updated/created/comments/reactions | updated |
| `--sort-order ORDER` |  | Sort order: desc/asc | desc |

#### Pull Request Collection Options
| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--type TYPE` | `-t` | Collection type: issues/prs | issues |
| `--number NUMBER` | `-n` | Specific PR number to collect | all |
| `--pr-state STATE` |  | PR state: open/closed/merged/all | open |

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
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo myorg/myrepo --state open"
```

#### 2. Collect Bug Reports Only
```bash
mvnd spring-boot:run -Dspring-boot.run.arguments="--labels bug --dry-run"
mvnd spring-boot:run -Dspring-boot.run.arguments="--labels bug --zip"
```

#### 3. Collect High Priority Issues
```bash
mvnd spring-boot:run -Dspring-boot.run.arguments="--labels priority:high,bug --label-mode all --state open"
```

#### 4. Large Repository with Small Batches
```bash
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo kubernetes/kubernetes --batch-size 25 --zip --verbose"
```

#### 5. Resume Interrupted Collection
```bash
mvnd spring-boot:run -Dspring-boot.run.arguments="--resume"
```

#### 6. Pull Request Collection (New!)
```bash
# Collect specific PR with soft approval detection
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --repo spring-projects/spring-ai --number 4347"

# Collect all open PRs
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --pr-state open --verbose"

# Collect recently merged PRs
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --pr-state merged --max-issues 20"
```

#### 7. Dashboard Use Cases
```bash
# Get 20 most recent open issues for dashboard
mvnd spring-boot:run -Dspring-boot.run.arguments="--state open --max-issues 20 --sort-by updated"

# Get 10 most commented issues
mvnd spring-boot:run -Dspring-boot.run.arguments="--max-issues 10 --sort-by comments --sort-order desc"
```

### Advanced Filtering Examples

#### Documentation Issues
```bash
mvnd spring-boot:run -Dspring-boot.run.arguments="--labels documentation --state all --batch-size 50"
```

#### Recently Closed Bugs
```bash
mvnd spring-boot:run -Dspring-boot.run.arguments="--state closed --labels bug --verbose"
```

#### Enhancement Requests
```bash
mvnd spring-boot:run -Dspring-boot.run.arguments="--labels enhancement,feature --label-mode any --state open"
```

#### Advanced PR Collection Examples
```bash
# Collect PRs with soft approval analysis
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --pr-state open --labels bug --verbose"

# Collect specific PRs for review analysis
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --number 4347 --verbose"

# Collect recently merged PRs with contributor analysis
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --pr-state merged --max-issues 50 --sort-by updated"

# Dashboard view: Recent PR activity
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --max-issues 20 --sort-by updated --sort-order desc"
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

## What is Soft Approval?

**Soft approval** is a key feature of the PR collection system that identifies pull requests with approvals from contributors who are not official project members.

### Why Soft Approval Matters

- **Community Engagement**: Shows which PRs have community support even without official approval
- **Merge Decision Making**: Helps maintainers identify PRs that have been vetted by contributors
- **Contributor Recognition**: Highlights valuable review contributions from the community
- **Process Insights**: Reveals how community members participate in the review process

### How It Works

The system analyzes PR reviews and detects approvals from users with these associations:
- `CONTRIBUTOR`: Users who have contributed to the repository
- `FIRST_TIME_CONTRIBUTOR`: New contributors to the repository

**Example output:**
```
Found approval from sunyuhan1998 (association: CONTRIBUTOR)
Soft approval detected from contributor: sunyuhan1998
Soft approval detected: true
```

### Use Cases

- **Maintainer Workflow**: Quickly identify PRs with community backing
- **Analytics**: Measure community engagement in the review process
- **Quality Assurance**: PRs with soft approvals often indicate good community validation
- **Prioritization**: Consider community-approved PRs for faster review

## Version History

- **v1.0.0**: Initial implementation with basic issue collection
- **v2.0.0**: Added state and label filtering capabilities for issues
- **v3.0.0**: Added dashboard support with sorting and limited result sets
- **v4.0.0**: **Pull Request Collection with Soft Approval Detection**
  - Full PR collection with state filtering (open/closed/merged/all)
  - Soft approval detection for contributor reviews
  - Specific PR targeting by number
  - Review analysis with author association tracking
  - Comprehensive CLI argument support for PR workflows
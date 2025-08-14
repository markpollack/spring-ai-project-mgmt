# GitHub Issues Collection Tools

This directory contains tools for collecting and analyzing GitHub issues from the Spring AI project with advanced filtering capabilities.

## Overview

The issues collection system has evolved from a single JBang script to a comprehensive Maven-based Spring Boot application with modular architecture.

## Architecture

### Current Implementation (Maven-based)
- **Location**: `project/` subdirectory
- **Technology**: Spring Boot application with Java 17+
- **Build Tool**: Maven with Maven Daemon (`mvnd`) recommended

### Legacy Implementation (JBang-based)
- **Location**: `CollectGithubIssues.java`
- **Technology**: Single-file Java execution
- **Status**: Maintained for compatibility

## Quick Start

### Prerequisites
```bash
export GITHUB_TOKEN="your_github_token"
```

### Maven Application (Recommended)
```bash
cd project

# Fast compilation (skip tests and javadoc)
mvnd clean compile -Dmaven.javadoc.skip=true -DskipTests

# Run with dry-run for testing
mvnd spring-boot:run -Dspring-boot.run.arguments="--help"
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --dry-run"

# Collect open issues with specific labels
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --labels bug,enhancement --state open"
```

### JBang Script (Legacy)
```bash
# Basic collection
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --repo spring-projects/spring-ai --state open

# With filtering
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --repo spring-projects/spring-ai --labels bug --dry-run

# Help
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --help
```

## Features

### Core Capabilities
- **State Filtering**: `open`, `closed`, or `all` issues
- **Label Filtering**: Multiple labels with configurable matching mode (any/all)
- **Batch Processing**: Resume support for large collections with configurable batch sizes
- **Rate Limit Management**: Intelligent GitHub API rate limiting
- **Incremental Collection**: Skip already collected issues
- **Collection Resume**: Continue from last successful batch after interruption

### Output Options
- **JSON Format**: Structured issue data with comprehensive metadata
- **Zip Archives**: Compressed output with documentation
- **Batch Files**: Split large datasets into numbered JSON files for processing
- **Collection Metadata**: Comprehensive collection statistics and configuration tracking

### Advanced Features
- **Dry Run Mode**: Test filtering without API calls
- **Progress Tracking**: Real-time collection progress
- **Error Recovery**: Robust error handling and retry logic
- **Token Estimation**: For AI analysis integration

## Configuration

### Application Configuration (`application.yaml`)
```yaml
github:
  api:
    baseUrl: https://api.github.com
    rateLimit:
      requestsPerHour: 5000
      bufferPercentage: 10
  collection:
    batchSize: 100
    retryAttempts: 3
    retryDelayMs: 1000

output:
  directory: "./issues"
  format: json
  compression: true
```

### Environment Variables
```bash
export GITHUB_TOKEN="your_personal_access_token"
export GITHUB_API_URL="https://api.github.com"  # Optional
```

## Command Line Arguments

### Core Options
```bash
-r, --repo OWNER/NAME       # Target repository (required)
-h, --help                  # Show help information
-d, --dry-run              # Test mode without API calls
-v, --verbose              # Enable verbose logging
```

### Collection Control
```bash
-b, --batch-size SIZE      # Issues per batch file (default: 100)
-i, --incremental          # Skip already collected issues
-z, --zip                  # Create zip archive of collected data
--clean                    # Clean up previous collection data before starting (default)
--no-clean, --append       # Keep previous collection data and append new data
--resume                   # Resume from last successful batch
```

### Filtering Options
```bash
-s, --state <state>        # Issue state: open, closed, all (default: all)
-l, --labels <labels>      # Comma-separated list of labels to filter by
--label-mode <mode>        # Label matching mode: any, all (default: any)
                          # Note: 'any' mode uses first label only due to API limitations
```

## Usage Examples

### Basic Collection
```bash
# Collect all open issues
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --state open"

# Collect bug reports
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --labels bug"
```

### Advanced Filtering
```bash
# Multiple labels (AND logic)
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --labels 'bug,enhancement' --label-mode all"

# Open issues only
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --state open"

# Closed issues with specific labels
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --state closed --labels documentation"
```

### Output Customization
```bash
# Create compressed archive
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --zip"

# Custom batch size for large repositories
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --batch-size 25"

# Verbose logging for debugging
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --verbose"
```

## Output Structure

### JSON Format
```json
{
  "metadata": {
    "repository": "spring-projects/spring-ai",
    "collectionDate": "2024-01-15T10:30:00Z",
    "totalIssues": 150,
    "filters": {
      "state": "open",
      "labels": ["bug", "enhancement"]
    }
  },
  "issues": [
    {
      "number": 1234,
      "title": "Issue title",
      "state": "open",
      "author": "username",
      "createdAt": "2024-01-01T12:00:00Z",
      "labels": ["bug"],
      "milestone": "1.1.0.M1",
      "body": "Issue description..."
    }
  ]
}
```

### Directory Structure
```
issues/
├── raw/
│   ├── open/
│   │   ├── batch_YYYY-MM-DD_HH-MM-SS/
│   │   │   ├── issues_batch_001.json
│   │   │   ├── issues_batch_002.json
│   │   │   └── metadata.json
│   │   └── collection.log
│   └── closed/
└── analysis/
    └── issues_analysis_ready.json
```

## Development

### Running Tests
```bash
cd project

# Run all tests
mvnd test

# Run specific test class
mvnd test -Dtest=CollectionServiceTest
```

### Adding New CLI Arguments
1. Update `CollectionProperties` class with new property and default
2. Modify argument parsing logic in `ArgumentParser.java`
3. Add comprehensive tests for new arguments
4. Update help text and documentation

### Testing Strategies
- **Critical**: Avoid `@SpringBootTest` - triggers CommandLineRunner production operations
- Use `@SpringJUnitConfig` with minimal TestConfiguration instead
- Mock external dependencies (GitHub API, file system)
- Use `--dry-run` flag for collection testing

## Integration with Other Systems

### Token Estimation for AI Analysis
- **Token Estimation**: 1 word = 1.3 tokens
- **File Size Estimation**: ~5 bytes per token or ~200 tokens per KB
- **Context Limits**: 80,000 tokens maximum for AI analysis

### PR Review System Integration
Issues data can be used for:
- Understanding project patterns and trends
- Contextualizing PR changes against known issues
- Identifying potential regression risks

## Troubleshooting

### Common Issues

**JBang not in PATH**
```bash
# Use full path
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --help
```

**Maven builds slow**
```bash
# Use mvnd with skip flags
mvnd clean compile -Dmaven.javadoc.skip=true -DskipTests
```

**GitHub API Rate Limits**
- Ensure `GITHUB_TOKEN` is set
- Use smaller batch sizes
- Check rate limit status: `gh api rate_limit`

**Tests trigger production operations**
- Avoid `@SpringBootTest` in tests
- Use minimal Spring context with `@SpringJUnitConfig`

### Debug Commands
```bash
# Verify GitHub connectivity
gh auth status

# Test Maven application
cd project && mvnd spring-boot:run -Dspring-boot.run.arguments="--dry-run"

# Test JBang script
/home/mark/.sdkman/candidates/jbang/current/bin/jbang CollectGithubIssues.java --help
```

## Migration from JBang to Maven

The Maven-based implementation provides:
- Better dependency management
- Improved testing capabilities
- Spring Boot configuration system
- Modular architecture for future enhancements

The JBang script remains available for compatibility but new features are added to the Maven application.

## Performance Considerations

- **Batch Size**: Adjust based on API rate limits (default: 100)
- **Rate Limiting**: Built-in GitHub API rate limit management
- **Memory Usage**: Large datasets are processed in batches
- **Network Efficiency**: Optimized API request patterns

## Contributing

1. Follow existing code patterns in the Maven project
2. Add comprehensive tests for new functionality
3. Update configuration documentation
4. Test with both `--dry-run` and real API calls
5. Maintain backward compatibility where possible

## TODO - Planned Features

The following features are planned but not yet implemented:

### Planned Features (Not Yet Implemented)

The following features are planned for future releases:

#### Date Range Filtering
- `--since YYYY-MM-DD` - Issues/PRs created after date
- `--since-hours N` - Issues/PRs created in the past N hours (e.g., `--since-hours 24`)
- `--until YYYY-MM-DD` - Issues/PRs created before date  
- `--updated-since YYYY-MM-DD` - Issues/PRs updated after date
- `--limit N` - Limit number of issues/PRs collected

#### Content Type Selection
- `--type issues` - Collect issues only (default)
- `--type prs` - Collect pull requests only
- `--type both` - Collect both issues and pull requests

#### Advanced Filtering Options
- `--milestone MILESTONE` - Filter by specific milestones
- `--author USERNAME` - Filter by author (issues/PRs)
- `--assignee USERNAME` - Filter by assignee (issues/PRs)
- `--reviewer USERNAME` - Filter PRs by reviewer (PRs only)

#### Output Format Options
- `--format csv` - CSV export for spreadsheet compatibility
- `--output-dir PATH` - Custom output directory specification

### Implementation Notes
- Date filtering would require GitHub API query parameter additions to search queries
- Milestone/author filtering needs API endpoint parameter support in GitHubRestService
- CSV export requires data transformation from current JSON-only output in IssueCollectionService
- Custom output directory needs path validation and creation logic
- Limit functionality would need integration with batch processing logic

### Priority Implementation Order
1. **Recent activity tracking (`--since-hours`, `--type`, `--limit`)** - High priority for daily monitoring
   - `--since-hours 24` for past 24 hours
   - `--type prs` for pull request tracking
   - `--limit 50` to avoid overwhelming results
2. **Date filtering (`--since YYYY-MM-DD`)** - High priority for historical analysis
3. **Output directory customization** - Medium priority for workflow integration
4. **CSV export** - Medium priority for analysis workflows
5. **Advanced filtering (milestone, author, assignee, reviewer)** - Lower priority for specialized use cases

### Use Case Examples (When Implemented)
```bash
# New issues in past 24 hours
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --type issues --state open --since-hours 24 --limit 20"

# New PRs in past 24 hours
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --type prs --state open --since-hours 24 --limit 20"

# All recent activity (issues + PRs) in past week
mvnd spring-boot:run -Dspring-boot.run.arguments="--repo spring-projects/spring-ai --type both --since-hours 168 --limit 100"
```
# spring-ai-project-mgmt
Project Management Agent for Spring AI

## Tools

### GitHub Issues Collector
A comprehensive JBang-based tool for collecting GitHub issues with advanced filtering capabilities.

**Location**: `scripts/CollectGithubIssues.java`

**Documentation**: See [`scripts/COLLECT_GITHUB_ISSUES_USER_GUIDE.md`](scripts/COLLECT_GITHUB_ISSUES_USER_GUIDE.md) for complete usage guide.

**Key Features**:
- State filtering (open/closed/all)
- Label filtering with AND/OR logic
- Batch processing with resume support
- GitHub API rate limit management
- JSON output with comprehensive metadata

**Quick Start**:
```bash
export GITHUB_TOKEN="your_token_here"
cd scripts
jbang CollectGithubIssues.java --repo spring-projects/spring-ai --state open --labels bug --dry-run
```

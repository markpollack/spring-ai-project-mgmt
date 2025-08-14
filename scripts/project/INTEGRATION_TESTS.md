# Integration Tests

This document describes the real integration tests for the GitHub Issues Collector application using Maven Failsafe plugin.

## Overview

The project follows standard Maven testing conventions with proper separation of concerns:

- **Unit Tests** - Test individual classes with mocks (`*Test.java`) - run with `mvn test`
- **Component Tests** - Test service interactions with mocks (nested classes in `*Test.java`) - run with `mvn test`
- **Integration Tests** - Test real API calls and file operations (`*IT.java`) - run with `mvn verify -Pintegration-tests`

## Integration Test Classes

### GitHubRestServiceIT.java
Tests actual REST API calls to GitHub:
- Repository information retrieval
- Issue count queries
- Search query building and validation
- Error handling with real API responses
- Response structure validation

### GitHubGraphQLServiceIT.java  
Tests actual GraphQL API calls to GitHub:
- GraphQL query execution
- Issue counting with different states
- Complex search queries with filters
- Custom GraphQL queries
- Response parsing and validation

### IssueCollectionServiceIT.java
Tests complete end-to-end workflow:
- Real issue collection from GitHub repositories
- JSON file generation and structure validation
- Metadata file creation and validation
- Label filtering with real data
- File safety and cleanup operations

## Running Integration Tests

### Prerequisites

1. **GitHub Token**: Set the `GITHUB_TOKEN` environment variable
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   ```

2. **Internet Connectivity**: Tests make real API calls to GitHub

3. **Maven Failsafe Plugin**: Configured with `integration-tests` profile

### Running the Tests

Integration tests use the Maven Failsafe plugin and follow standard naming conventions (`*IT.java`).

#### Run All Integration Tests (Recommended)
```bash
# Set GitHub token and run integration tests
export GITHUB_TOKEN="your_token"
mvn verify -Pintegration-tests
```

#### Run Only Unit Tests (Default)
```bash
# This runs only unit and component tests (*Test.java)
mvn test
```

#### Run Specific Integration Test Classes
```bash
# GitHub REST Service integration tests
mvn verify -Pintegration-tests -Dit.test=GitHubRestServiceIT

# GitHub GraphQL Service integration tests  
mvn verify -Pintegration-tests -Dit.test=GitHubGraphQLServiceIT

# End-to-end collection integration tests
mvn verify -Pintegration-tests -Dit.test=IssueCollectionServiceIT
```

#### Full Build with All Tests
```bash
# Run unit tests, then integration tests
export GITHUB_TOKEN="your_token"
mvn clean verify -Pintegration-tests
```

### Test Repositories Used

The integration tests use these public repositories to minimize API usage:

- **octocat/Hello-World** - Small, stable demo repository
- **spring-projects/spring-boot** - For testing with real issue volumes and labels

### What Integration Tests Validate

#### API Connectivity
- REST API endpoint accessibility
- GraphQL API endpoint accessibility
- Authentication token validation
- Rate limiting handling

#### Data Structure Validation
- GitHub API response structure
- JSON field presence and types
- Data consistency across API calls

#### File Operations
- JSON file creation and structure
- Metadata file generation
- File compression operations
- Directory structure creation

#### Error Handling
- Network connectivity issues
- Invalid repository names
- API rate limiting
- Authentication failures

#### Search and Filtering
- Issue state filtering (open/closed/all)
- Label-based filtering
- Complex search query construction
- Pagination handling

### Expected Results

When integration tests run successfully, they will:

1. **Connect to GitHub APIs** - Validate authentication and connectivity
2. **Retrieve Real Data** - Get actual issue data from test repositories
3. **Generate Files** - Create JSON files with valid structure
4. **Validate Content** - Ensure data integrity and expected formats
5. **Clean Up** - Remove temporary files and directories

### Troubleshooting

#### Common Issues

**Tests Skipped**:
```
org.junit.jupiter.api.Assumptions$TestAbortedException: Assumption failed: assumption is not true
```
- Solution: Ensure `GITHUB_TOKEN` environment variable is set

**Authentication Errors**:
```
401 Unauthorized or 403 Forbidden
```
- Solution: Verify `GITHUB_TOKEN` is valid and has appropriate permissions

**Rate Limiting**:
```
403 rate limit exceeded
```
- Solution: Wait for rate limit reset or use a token with higher limits

**Network Connectivity**:
```
Connection refused or timeout errors
```
- Solution: Check internet connectivity and GitHub API status

### Best Practices

1. **Use Personal Access Tokens** - Not OAuth tokens for consistency
2. **Minimize API Calls** - Tests use small repositories and limited data
3. **Handle Rate Limits** - Tests include appropriate delays and error handling
4. **Clean Up Resources** - Tests clean up any created files and directories
5. **Test Real Scenarios** - Use actual GitHub repositories and real data patterns

### CI/CD Integration

For continuous integration:

```yaml
# Example GitHub Actions workflow
- name: Run Integration Tests
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: mvn verify -Pintegration-tests
```

### Security Considerations

- Integration tests use read-only operations on public repositories
- GitHub tokens should have minimal required permissions
- Tests do not modify any GitHub data
- Temporary files are created in secure temporary directories
- All API calls are logged for debugging but tokens are never logged

## Comparison with Unit/Component Tests

| Test Type | GitHub API | File System | Purpose |
|-----------|------------|-------------|---------|
| Unit Tests | Mocked | Mocked | Fast feedback, isolated testing |
| Component Tests | Mocked | Mocked | Service interaction validation |
| Integration Tests | **Real** | **Real** | End-to-end workflow validation |

The integration tests complement the existing unit and component tests by providing confidence that the application works correctly with real GitHub APIs and actual file operations.
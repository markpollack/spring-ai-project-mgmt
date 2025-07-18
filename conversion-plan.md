# GitHub Issues Collection Script Conversion Plan

## Overview
Converting `collect_github_issues.sh` (935 lines) to a JBang Spring Boot application with type safety, better error handling, and maintainability.

## Design Approach

### Technology Stack
- **JBang**: Single-file Spring Boot application for simplicity
- **Spring Boot**: Dependency injection, configuration, logging (traditional servlet stack)
- **Spring Web**: For HTTP calls and GraphQL client (if GraphQL absolutely required)
- **Hub4j GitHub API**: For REST API calls and authentication
- **Jackson**: JSON processing with JsonNode for GraphQL responses
- **Simple argument parsing**: Hardcoded parsing for now, can upgrade to Spring Shell later
- **Records**: For core domain objects (Issue, Comment, Author)
- **No Lombok**: Avoid additional dependencies

### API Access Strategy
- **GraphQL**: Primary method for bulk data collection (main collection loop)
- **REST API**: For utility calls (rate limits, repo info, search counts)
- **JsonNode**: For GraphQL responses and one-off REST calls
- **Hub4j POJOs**: For structured REST API responses where beneficial
- **Authentication**: Use GITHUB_TOKEN environment variable with Hub4j GitHub API

### Data Processing Approach
- **Records for core entities**: Issue, Comment, Author, CollectionMetadata
- **JsonNode + Stream API**: For GraphQL response processing
- **Utility helper methods**: Clean navigation of nested JSON structures
- **No full POJO mapping**: Avoid over-engineering for one-off queries

## Iterative Implementation Plan

### Phase 1: Foundation Setup
**Goal**: Create basic JBang Spring Boot structure with CLI

**Tasks**:
- [x] Create `scripts/collect_github_issues.java` with JBang headers
- [x] Set up Spring Boot dependencies and basic structure
- [x] Implement simple hardcoded argument parsing (no external frameworks)
- [x] Add basic logging and configuration
- [x] Create core domain records (Issue, Comment, Author)

**Testing**: Basic command line parsing and help output

### Phase 2: GitHub API Integration
**Goal**: Establish GitHub API connectivity

**Tasks**:
- [x] Configure GitHub authentication using GITHUB_TOKEN environment variable
- [x] Set up Hub4j GitHub API client for REST calls
- [x] Implement GraphQL client setup (evaluate if Spring Web is sufficient vs WebFlux)
- [x] Create utility methods for JsonNode navigation
- [x] Implement rate limiting and error handling

**Testing**: Basic connectivity, authentication, and rate limit checks

### Phase 3: Core Collection Logic
**Goal**: Implement main GraphQL-based collection

**Tasks**:
- [x] Port GraphQL query building from bash script
- [x] Implement batch processing with pagination
- [x] Add JsonNode to Record conversion methods
- [x] Create file system management (directories, JSON output)
- [x] Implement progress tracking and ETA calculation

**Testing**: Collect small batches of issues, verify JSON output structure

### Phase 4: Advanced Features
**Goal**: Add sophisticated features from original script

**Tasks**:
- [ ] Implement large issue detection and individual file storage
- [ ] Add compression support
- [ ] Create resume/incremental collection logic
- [ ] Add metadata generation
- [ ] Implement cleanup and error recovery

**Testing**: Full collection runs, resume functionality, error scenarios

### Phase 5: Performance & Polish
**Goal**: Optimize and finalize

**Tasks**:
- [ ] Add parallel processing for API calls
- [ ] Implement caching for repeated queries
- [ ] Add comprehensive error messages and validation
- [ ] Create output formatting options
- [ ] Add configuration file support

**Testing**: Performance testing, error handling, edge cases

### Phase 6: Migration & Comparison
**Goal**: Validate against original script

**Tasks**:
- [ ] Run side-by-side comparisons with bash script
- [ ] Verify output format compatibility
- [ ] Test all command line options
- [ ] Performance benchmarking
- [ ] Create migration guide

**Testing**: Full regression testing against bash script behavior

## File Structure

```
spring-ai-project-mgmt/
├── scripts/
│   └── collect_github_issues.java     # Single JBang file
├── collect_github_issues.sh           # Original bash script (reference)
├── conversion-plan.md                  # This file
└── README.md
```

## Core Components Design

### Main Application Class
```java
@SpringBootApplication
public class CollectGithubIssues implements ApplicationRunner {
    
    @Override
    public void run(ApplicationArguments args) throws Exception {
        // Simple hardcoded argument parsing
        // Main CLI entry point
    }
    
    public static void main(String[] args) {
        SpringApplication.run(CollectGithubIssues.class, args);
    }
}
```

### Service Layer
```java
@Component
public class GitHubGraphQLService {
    // GraphQL query execution, pagination handling
    // Uses simple HTTP client (RestTemplate or WebClient if needed)
}

@Component 
public class GitHubRestService {
    // REST API calls using Hub4j GitHub API
    // Authentication via GITHUB_TOKEN environment variable
}

@Component
public class IssueCollectionService {
    // Core collection logic, orchestration
}

@Component
public class FileSystemService {
    // File management, compression, metadata
}
```

### Domain Models
```java
public record Issue(
    int number, String title, String body, String state,
    LocalDateTime createdAt, LocalDateTime updatedAt, LocalDateTime closedAt,
    Author author, List<Comment> comments, List<Label> labels,
    String url
) {}

public record Comment(Author author, String body, LocalDateTime createdAt) {}
public record Author(String login, String name) {}
public record Label(String name, String color) {}
```

### Configuration
```java
@ConfigurationProperties(prefix = "github")
public record GitHubConfig(
    String repo, int batchSize, int maxRetries,
    Duration retryDelay, int largeIssueThreshold
) {}

// Authentication handled via GITHUB_TOKEN environment variable
@Component
public class GitHubAuthConfig {
    @Value("${GITHUB_TOKEN}")
    private String githubToken;
    
    // Configuration for Hub4j GitHub API
}
```

## Key Differences from Bash Script

### Improvements
- **Type Safety**: Compile-time error checking
- **Error Handling**: Proper exception handling vs bash error codes
- **Parallel Processing**: Easy multithreading for API calls
- **IDE Support**: Debugging, refactoring, auto-completion
- **Testing**: Unit testable components (future Maven export)
- **Authentication**: Clean environment variable-based authentication
- **Dependency Management**: Simplified stack without unnecessary frameworks

### Maintained Features
- **All CLI options**: Exact same command line interface
- **Resume functionality**: State persistence and recovery
- **Progress tracking**: ETA calculations and status updates
- **File formats**: Compatible JSON output structure
- **Rate limiting**: Respect GitHub API limits
- **Compression**: Gzip support for large files

## Success Criteria

### Phase 1-2 Success
- [x] JBang script executes without errors
- [x] GitHub API authentication working
- [x] Basic GraphQL queries execute

### Phase 3-4 Success
- [x] Collects issues in batches equivalent to bash script
- [x] Produces compatible JSON output
- [x] Resume functionality works

### Phase 5-6 Success
- [x] Performance equal to or better than bash script
- [x] All original CLI options supported
- [x] Error handling robust and user-friendly

## Migration Strategy

1. **Parallel Development**: Keep bash script functional during development
2. **Incremental Testing**: Test each phase against bash script output
3. **Feature Parity**: Ensure all bash script features are preserved
4. **Performance Validation**: Benchmark against original script
5. **Gradual Adoption**: Use JBang version for new features, bash for production until fully validated

## Notes

- **Single File Approach**: Keep as single JBang file until complexity requires Maven export
- **Backward Compatibility**: Maintain exact same CLI interface and output format
- **Error Messages**: Improve error messages compared to bash script
- **Documentation**: Inline documentation for complex GraphQL queries
- **Future Expansion**: Design with PR collection in mind for future enhancement
- **CLI Framework Upgrade Path**: Start with simple argument parsing, can upgrade to Spring Shell when CLI complexity grows
- **Authentication**: GITHUB_TOKEN environment variable for clean auth setup

## Current Status

- [ ] Phase 1: Foundation Setup
- [ ] Phase 2: GitHub API Integration  
- [ ] Phase 3: Core Collection Logic
- [ ] Phase 4: Advanced Features
- [ ] Phase 5: Performance & Polish
- [ ] Phase 6: Migration & Comparison

## Next Steps

1. Begin Phase 1 implementation
2. Create basic JBang script structure with Spring Boot (servlet stack)
3. Set up Hub4j GitHub API dependency
4. Implement simple hardcoded argument parsing
5. Configure GITHUB_TOKEN environment variable authentication
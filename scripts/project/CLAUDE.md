# GitHub Issues Collector - Claude Code Assistant Guide

## Project Overview

This is a Spring Boot Maven application for collecting GitHub issues and pull requests with advanced filtering capabilities. The project has been refactored from a monolithic JBang script into a multi-module, testable Maven architecture with comprehensive PR collection and soft approval detection.

## Current Architecture

### Multi-Module Architecture

#### collection-library Module
Reusable components for GitHub API interactions:

1. **DataModels.java** - GitHub API data structures
   - Issue collection: `Issue`, `Comment`, `Author`, `Label`
   - **PR collection**: `PullRequest`, `Review` (with author association for soft approval detection)
   - Collection metadata: `CollectionMetadata`, `CollectionRequest`, `CollectionResult`
   - Internal processing: `BatchData`, `CollectionStats`, `ResumeState`

2. **ConfigurationSupport.java** - Spring configuration and properties
   - `GitHubConfig`: Spring beans for GitHub API clients (GitHub, RestClient, GraphQL, ObjectMapper)
   - `CollectionProperties`: @ConfigurationProperties with application defaults

3. **ArgumentParser.java** - Command-line argument parsing and validation
   - Pure Java implementation with no Spring dependencies
   - `ParsedConfiguration`: Type-safe parsed argument results
   - Comprehensive CLI argument support and validation
   - Environment validation and help text generation

4. **GitHubServices.java** - GitHub API service classes
   - `GitHubRestService`: GitHub REST API operations and search query building
   - `GitHubGraphQLService`: GraphQL query execution and issue counting
   - `JsonNodeUtils`: Safe JSON navigation with Optional return types
   - Pure Java services with minimal Spring dependencies for better testability

5. **IssueCollectionService.java** - Core business logic for issue collection
   - Main collection orchestration and workflow management (780+ lines extracted)
   - Batch processing with adaptive sizing based on issue content
   - File operations, compression, and metadata generation
   - Resume state management and error recovery with exponential backoff
   - Search query building with advanced filtering capabilities
   - Pure Java service with comprehensive mocked testing strategy

6. **PRCollectionService.java** - **NEW: Pull request collection with soft approval detection**
   - PR collection orchestration with state filtering (open/closed/merged/all)
   - **Soft approval detection** for contributor reviews (not formal members)
   - Review analysis with author association tracking
   - Specific PR targeting by number
   - Integration with existing batch processing and file operations

#### collection-app Module
Main Spring Boot CLI application:

7. **CollectGithubIssuesApp.java** - Main Spring Boot application with CommandLineRunner
   - **PR collection logic**: `collectPullRequests()` method
   - **Soft approval detection**: `detectSoftApproval()` method for contributor reviews
   - Multi-type collection support (issues, PRs)

### Refactoring Status

**Completed Phases:**
- ✅ Phase 0: JBang to Maven conversion using `jbang export portable`
- ✅ Phase 1: DataModels.java extraction
- ✅ Phase 2: ConfigurationSupport.java extraction
- ✅ Phase 3: ArgumentParser.java extraction
- ✅ Phase 4: GitHubServices.java extraction
- ✅ Phase 5: IssueCollectionService.java extraction (Highest Risk Phase)
- ✅ Phase 6: Multi-module architecture implementation
- ✅ Phase 7: **PR Collection with Soft Approval Detection**
- ✅ Phase 8: Integration testing and comprehensive documentation

**ALL PHASES COMPLETE! ✅**

## Development Guidelines

### Testing Strategy

**CRITICAL: Avoid @SpringBootTest for Configuration Testing**
- This application implements `CommandLineRunner` which automatically executes main application logic
- Using `@SpringBootTest` triggers full Spring context including CommandLineRunner
- This causes accidental production operations (real GitHub API calls, data collection)

**REQUIRED PATTERN: Use @SpringJUnitConfig with ClassificationConfiguration**
```java
// CORRECT PATTERN - Used by EvaluationParityTest (F1 calculation)
@SpringJUnitConfig(ClassificationConfiguration.class)
public class EvaluationParityTest {
    @Autowired
    private FilteredEvaluationService evaluationService;
    @Autowired
    private ObjectMapper objectMapper;
    // Minimal Spring context, no production operations
}

// WRONG - DO NOT USE @SpringBootTest
@SpringBootTest  // ❌ Triggers CommandLineRunner
public class BadTest {
    // This will cause production GitHub API calls!
}
```

**Safe Testing Approaches:**
```java
// For data models - use plain JUnit
@Nested
@DisplayName("CollectionProperties Tests - Plain JUnit")
class CollectionPropertiesPlainTest {
    // No Spring context, safe for data validation
}

// For Spring beans - use @SpringJUnitConfig with ClassificationConfiguration
@SpringJUnitConfig(ClassificationConfiguration.class)
static class GoodSpringTest {
    // Minimal Spring context, specific configuration, no CommandLineRunner
}
```

**IMPORTANT: ClassificationConfiguration Pattern**
- ALL tests requiring Spring context MUST use `@SpringJUnitConfig(ClassificationConfiguration.class)`
- This provides access to evaluation services, ObjectMapper, and other beans WITHOUT triggering production operations
- Example: `EvaluationParityTest` successfully calculated F1 scores using this pattern

### Build Commands

**Multi-Module Structure:**
```bash
# From collection-app directory (recommended for development)
cd collection-app
mvnd clean compile -Dmaven.javadoc.skip=true -DskipTests
mvnd test
mvnd spring-boot:run -Dspring-boot.run.arguments="--help"

# From parent project directory (build all modules)
cd project
mvnd clean compile -Dmaven.javadoc.skip=true -DskipTests
mvnd test  # Tests all modules

# Test PR collection features
cd collection-app
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --number 4347 --dry-run"
```

### Safety Measures

**Before Any Testing:**
1. Verify `.gitignore` prevents data file commits (`issues/`, `logs/`, `batch_*`)
2. Always use `--dry-run` flag when testing collection functionality
3. Clean up any generated data before git commits

**Repository Cleanup:**
```bash
# Remove accidental production data
rm -rf issues/
find . -name "batch_*" -type f -delete
find . -name "logs" -type d -exec rm -rf {} + 2>/dev/null || true
```

## Common Modification Patterns

### Adding New CLI Arguments
1. Update `CollectionProperties` class with new property and default
2. Modify argument parsing logic (currently in main class, will be extracted to ArgumentParser)
3. Add comprehensive tests for new arguments
4. Update help text and documentation

### Adding New Configuration Properties
1. Add property to `CollectionProperties` class with appropriate default
2. Add getter/setter methods following existing patterns
3. Add validation tests in `ConfigurationSupportTest`
4. Document in README.md configuration section

### Modifying GitHub API Integration
1. Update relevant classes in `ConfigurationSupport.java` (GitHubConfig)
2. Ensure proper bean configuration for new API clients
3. Add integration tests with mocked responses
4. Update error handling patterns

## Multi-Module Dependencies

```
collection-app/
└── CollectGithubIssuesApp.java (main)
    ├── Issue collection workflow
    ├── **PR collection workflow** (NEW)
    └── **Soft approval detection** (NEW)

collection-library/
├── DataModels.java (records)
│   ├── Issue, Comment, Author, Label
│   ├── **PullRequest, Review** (NEW)
│   └── CollectionMetadata, CollectionRequest, CollectionResult
├── ConfigurationSupport.java (Spring config)
│   ├── GitHubConfig (beans)
│   └── CollectionProperties (properties)
├── ArgumentParser.java (CLI parsing)
│   └── **PR collection arguments** (NEW)
├── GitHubServices.java (API services)
│   ├── GitHubRestService (REST operations)
│   │   └── **PR methods and search queries** (NEW)
│   ├── GitHubGraphQLService (GraphQL operations)
│   └── JsonNodeUtils (JSON utilities)
├── IssueCollectionService.java (issue business logic)
└── **PRCollectionService.java** (PR business logic - NEW)
    ├── **PR collection orchestration**
    ├── **Soft approval detection logic**
    ├── **Review analysis with author associations**
    └── **PR state filtering (open/closed/merged/all)**
```

## Testing Requirements

### Unit Testing
- All new classes must have comprehensive unit tests
- Use plain JUnit for data models and validation logic
- Use minimal Spring context only when testing actual Spring integration
- Mock external dependencies (GitHub API, file system)

### Integration Testing
- End-to-end workflow testing with `--dry-run` flag
- No real GitHub API calls in automated tests
- Verify all CLI argument combinations work correctly

### Large-Scale Testing (100+ Issues)
- **Run in background** using `timeout 3600 mvn test -Dtest=TestName` with `run_in_background=true`
- **Monitor progress** using `BashOutput` tool to track batch completion
- **Set appropriate timeouts** (1 hour minimum for full 111-issue runs)
- **Enable detailed logging** to track success/failure rates per batch

### Safety Testing
- Verify no production operations occur during test execution
- Confirm proper cleanup of temporary files
- Test error handling and recovery scenarios

## Claude Code Java SDK Integration

**Source Location:** `/home/mark/claude/bud/experiments/spring-ai-agents/supporting-repos/claude-code-java-sdk`

### Known Issues and Enhancement Opportunities

**Empty Response Bug (Intermittent Claude CLI Issue):**
- **Symptoms**: Claude CLI returns 0 characters despite successful execution and token charging
- **Occurrence**: Intermittent, load-dependent, more frequent during high-volume batch processing
- **Current Detection**: Implemented in CLITransport.java with warning logs
- **Recommended Fix**: Implement retry logic with exponential backoff in CLITransport.executeQuery()
- **Evidence**: Confirmed in batches during debugging - some batches fail 3+ consecutive attempts

**Format Inconsistency (Prompt Engineering Issue):**
- **Symptoms**: Claude returns markdown-wrapped JSON instead of raw JSON despite `--output-format json`
- **Current Solution**: Robust JSON extraction with multiple fallback strategies
- **Location**: ClaudeCodeWrapperService.extractJsonFromResponse()

### SDK Enhancement Plan

**High Priority - CLITransport Retry Logic:**
```java
// In CLITransport.executeQuery() around line 98
// Add retry logic for empty responses with:
// 1. Configurable max attempts (default: 3)
// 2. Exponential backoff delays (1s, 2s, 4s)
// 3. Empty response detection (result.outputUTF8().trim().isEmpty())
// 4. Preserve original exception on final failure
// 5. Log retry attempts for debugging
```

## Troubleshooting

### Common Issues

**Tests Trigger Production Operations:**
- Problem: Using `@SpringBootTest` loads full Spring context including CommandLineRunner
- Solution: Use `@SpringJUnitConfig` with minimal TestConfiguration instead

**Maven Build Slow:**
- Problem: Default Maven build includes tests and javadoc generation
- Solution: Use `mvnd clean compile -Dmaven.javadoc.skip=true -DskipTests` for fast compilation

**Accidental Data Generation:**
- Problem: Test execution or development runs create `issues/`, `logs/`, `batch_*` files
- Solution: Always use `--dry-run` flag and clean up before commits

**Empty Response Failures:**
- Problem: Claude CLI returns empty output despite token usage during batch processing
- Symptoms: 0-character responses, tokens charged, intermittent occurrence
- Current Workaround: Application-level retry logic in FailedBatchesDebugTest
- Long-term Solution: Implement retry logic in Claude Code Java SDK CLITransport layer

### Debug Commands

```bash
# From collection-app directory
cd collection-app

# Verify Spring context loads correctly
mvnd spring-boot:run -Dspring-boot.run.arguments="--dry-run"

# Check configuration properties and PR collection options
mvnd spring-boot:run -Dspring-boot.run.arguments="--help"

# Test PR collection functionality
mvnd spring-boot:run -Dspring-boot.run.arguments="--type prs --number 4347 --dry-run"

# Test specific functionality
mvnd test -Dtest=ConfigurationSupportTest
mvnd test -Dtest=DataModelsTest
mvnd test -Dtest=PRCollectionServiceTest  # NEW
```

## Phase-Specific Notes

### Phase 2 Lessons Learned
- Successfully implemented safe testing strategy avoiding @SpringBootTest
- Applied clean migration approach from Phase 1 (create new files first, then remove from main)
- Prevented namespace conflicts through proper sequencing
- Established comprehensive cleanup procedures for production data

### Phase 3 Lessons Learned
- Pure Java design with no Spring dependencies enables comprehensive plain JUnit testing
- 70 tests executed successfully in under 5 seconds with no external dependencies
- @ParameterizedTest excellent for CLI argument validation scenarios
- Clean migration approach successfully applied: removed 270+ lines of parsing logic
- ArgumentParser integration seamless with type-safe ParsedConfiguration class

### Phase 4 Lessons Learned
- Successfully extracted GitHub service classes using clean migration approach
- Comprehensive mocking strategy prevents accidental production operations during testing
- Spring's component scanning eliminates need for explicit @Service class imports
- RestClient mocking requires careful generic type handling in tests
- Functional testing via dry-run validation more reliable than complex unit test mocking
- Successfully removed 229 lines of service logic from main application

### Phase 5 Lessons Learned (Highest Risk Phase)
- Successfully extracted massive IssueCollectionService with 780+ lines of core business logic
- Applied strictest safety protocols using @TempDir and comprehensive mocking
- AssertJ test compilation errors resolved using ArgumentCaptor for complex mock verification
- File naming conflicts resolved by matching class names with file names
- Maintained perfect safety record - zero production operations during highest-risk phase
- Clean migration approach successfully applied to largest service extraction

### Future Phase Considerations
- Phase 6: Documentation completion and architectural review
- Phase 7: Integration testing with minimal Spring context for service interaction validation
- All extraction phases completed successfully with zero functionality regression
- Modular architecture fully established with clear service boundaries
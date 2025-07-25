# JBang to Maven Multi-Module Refactoring - Design Document

## Context & Problem Statement

The `CollectGithubIssues.java` JBang script has grown to 1,644 lines (updated July 24, 2025), making it difficult for Claude Code and developers to manage effectively. Additionally, JBang's multi-file approach has significant limitations:

- **Multi-file constraints**: All source files must be in same directory with potential compilation order issues
- **Testing complexity**: Spring Boot Test integration challenges with JBang multi-file setup
- **IDE limitations**: Reduced tooling support compared to standard Maven projects
- **Development friction**: Limited refactoring and debugging capabilities

The solution is to use **JBang's export feature** to seamlessly convert the single-file JBang script to a proper Maven project, avoiding the multi-file limitations entirely while preserving all functionality.

The single-file approach, while initially convenient, has become an anti-pattern that hinders:

- **Code navigation**: Finding specific functionality in a massive file
- **Testing**: No unit tests for individual components
- **Collaboration**: Multiple developers can't work on different features simultaneously
- **Maintenance**: Changes to one feature risk breaking unrelated functionality

## Design Goals

### Primary Goals
1. **Maintainability**: Break into logical, focused modules that are easier to understand and modify
2. **Seamless Conversion**: Use JBang's export feature to automatically create Maven project with zero manual dependency management
3. **Professional Tooling**: Leverage Maven's mature ecosystem and IDE integration
4. **Testability**: Enable comprehensive unit and integration testing with full Spring Boot Test support
5. **Modularity**: Create clean separation of concerns with well-defined interfaces
6. **Development Velocity**: Fast edit-compile-test cycle with Maven daemon and Spring Boot DevTools

### Secondary Goals
- **Claude Code Friendly**: Standard Maven structure that AI tools understand well
- **Spring Boot Native**: Full framework capabilities without JBang limitations
- **Enterprise Ready**: Proper packaging, dependency management, and CI/CD integration

## High-Level Architecture

### Module Breakdown
The 1,644-line monolith will be decomposed into 6 focused modules:

```
┌─────────────────────┐
│ CollectGithubIssues │  Main orchestration (~100 lines)
│   (Entry Point)    │
└─────────┬───────────┘
          │
    ┌─────▼─────┐
    │   Spring  │
    │ Container │
    └─────┬─────┘
          │
    ┌─────▼─────────────────────────────────────┐
    │              Core Services              │
    ├─────────────┬─────────────┬─────────────┤
    │ArgumentParser│GitHubServices│CollectionSvc│
    │(~200 lines)  │(~150 lines)  │(~780 lines) │
    └─────────────┴─────────────┴─────────────┘
          │              │              │
    ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
    │DataModels │  │   Config  │  │  Testing  │
    │(~60 lines)│  │(~110 lines)│  │Framework  │
    └───────────┘  └───────────┘  └───────────┘
```

### Dependency Flow
- **DataModels**: Pure data structures (no dependencies)
- **ConfigurationSupport**: Spring configuration and properties
- **ArgumentParser**: CLI processing (depends on DataModels, Config)
- **GitHubServices**: API interaction (depends on DataModels, Config)
- **CollectionService**: Business logic (depends on all above)
- **Main Class**: Orchestration (depends on services only)

## Package Structure & Maven Coordinates

### Spring AI Community Namespace
- **Package**: `org.springaicommunity.github.ai.collection`
- **Maven GroupId**: `org.springaicommunity.github.ai`
- **Maven ArtifactId**: `collection`

This package structure provides:
- **`org.springaicommunity`** - Spring AI community namespace
- **`github`** - Platform-specific scope  
- **`ai`** - AI/ML focus, perfect for Spring AI community
- **`collection`** - First step in the AI pipeline (collect → analyze → predict)

This leaves room for natural expansion like:
- `org.springaicommunity.github.ai.analysis`
- `org.springaicommunity.github.ai.classification` 
- `org.springaicommunity.github.ai.prediction`
- `org.springaicommunity.github.ai.sentiment`

## Module Specifications

### 1. DataModels.java (~60 lines)
**Purpose**: All record definitions and data structures
**Package**: `org.springaicommunity.github.ai.collection`
**Contents**:
- `Issue`, `Comment`, `Author`, `Label` records (Lines 501-530)
- `CollectionMetadata`, `CollectionRequest`, `CollectionResult` records (Lines 532-559)
- Internal records: `BatchData`, `CollectionStats`, `ResumeState` (Lines 1555-1565)

**Why First**: Pure data with zero dependencies - safest extraction

### 2. ConfigurationSupport.java (~110 lines)
**Purpose**: Spring configuration and application properties
**Package**: `org.springaicommunity.github.ai.collection`
**Contents**:
- `GitHubConfig` class with bean definitions (Lines 562-596)
- `CollectionProperties` class with configuration binding (Lines 1568-1644)
- Environment-specific settings

**Dependencies**: DataModels only

### 3. ArgumentParser.java (~200 lines)
**Purpose**: Command-line interface processing and validation
**Package**: `org.springaicommunity.github.ai.collection`
**Contents**:
- Argument parsing logic from `parseArguments()` (Lines 222-340)
- Configuration validation from `validateConfiguration()` (Lines 377-435)
- Environment validation from `validateEnvironment()` (Lines 352-375)
- Help text generation from `showHelp()` (Lines 438-490)

**Key Behavior**: Read-only operations, no GitHub state changes

### 4. GitHubServices.java (~150 lines)
**Purpose**: GitHub API interaction layer
**Package**: `org.springaicommunity.github.ai.collection`
**Contents**:
- `GitHubRestService` for basic API operations (Lines 599-653)
- `GitHubGraphQLService` for complex queries (Lines 655-723)
- `JsonNodeUtils` for response parsing (Lines 724-773)

**Important**: All operations are **read-only** - no issue/PR modifications

### 5. CollectionService.java (~780 lines)
**Purpose**: Core business logic for issue collection
**Package**: `org.springaicommunity.github.ai.collection`
**Contents**:
- `IssueCollectionService` class (Lines 775-1555)
- Batch processing logic (Lines 1023-1091)
- File operations and compression (Lines 1296-1470)
- Resume/recovery functionality
- Search query building (Lines 1472-1514)

**Behavior**: Creates local files only, no GitHub state changes

### 6. CollectGithubIssues.java (~100 lines)
**Purpose**: Application entry point and orchestration
**Package**: `org.springaicommunity.github.ai.collection`
**Contents**:
- Spring Boot application setup (Lines 70-73)
- High-level workflow coordination (Lines 114-220)
- Dependency injection wiring (Lines 75-81)

**Remaining**: Only main(), run(), and high-level orchestration methods

## Testing Strategy

### Testing Framework
- **JUnit 5**: Modern testing framework with excellent Maven integration
- **Spring Boot Test**: Full Spring context testing capabilities with @SpringBootTest
- **AssertJ**: Fluent assertion library for readable tests
- **Mockito**: Mock GitHub API responses to avoid external dependencies
- **Maven Surefire**: Parallel test execution and comprehensive reporting

### Test Categories
1. **Unit Tests**: Test individual methods and classes in isolation
2. **Integration Tests**: Test module interactions and full Spring context
3. **API Tests**: Test GitHub service layer with mocked responses (no external calls)
4. **CLI Tests**: Test argument parsing with various input combinations

### Test Resources Strategy

#### Comprehensive Test Resource Structure
```
src/test/resources/
├── application-test.yaml              # Test-specific Spring configuration
├── mock-responses/
│   ├── github-search-response.json    # Sample GitHub search API response
│   ├── github-issue-response.json     # Sample individual issue response
│   ├── github-error-response.json     # Error response samples
│   └── github-ratelimit-response.json # Rate limit response samples
├── test-data/
│   ├── sample-issues.json             # Test issue datasets
│   ├── large-issue-dataset.json       # Performance testing data
│   └── edge-case-issues.json          # Edge cases and boundary conditions
└── config/
    ├── test-profiles/                 # Different test configurations
    │   ├── mock-github.yaml           # Full mock setup
    │   └── integration-test.yaml      # Integration test setup
    └── logging-test.yaml              # Test-specific logging config
```

#### Test Data Generation Strategy
- **Realistic Mock Data**: All test responses based on actual GitHub API responses
- **Comprehensive Coverage**: Cover all API endpoints and response variations
- **Error Scenarios**: Include rate limit, network, and authentication errors
- **Performance Data**: Large datasets for batch processing and memory testing
- **Edge Cases**: Malformed responses, empty results, Unicode content

#### Test Utilities and Patterns
- **MockResponseBuilder**: Utility for creating consistent mock GitHub responses
- **TestDataFactory**: Factory for generating test issues with various characteristics
- **AssertionHelpers**: Custom AssertJ assertions for domain objects
- **TempFileManager**: Utility for managing temporary files in tests
- **SpringTestConfig**: Shared test configuration across all test classes

### Maven Test Integration
- **Test-specific profiles**: Separate configurations for different test scenarios
- **Test resources**: Structured test data and configuration files under `src/test/resources`
- **Coverage reporting**: Integration with JaCoCo for test coverage metrics
- **Continuous testing**: Fast feedback with Maven's incremental compilation

## JBang Export Strategy

### Automated Maven Project Creation
The conversion from JBang to Maven leverages JBang's built-in export capabilities with full configuration:

```bash
jbang export portable CollectGithubIssues.java \
  --output-dir=project \
  --group=org.springaicommunity.github.ai \
  --artifact=collection \
  --version=1.0.0-SNAPSHOT \
  --deps=org.springframework.boot:spring-boot-starter-test,org.assertj:assertj-core \
  --force
```

### Key Benefits of JBang Export Approach
- **Zero Manual Configuration**: JBang automatically handles Maven coordinates, dependencies, and package structure
- **Reliable Package Management**: Eliminates error-prone sed/find commands for package restructuring
- **Test Dependencies Included**: Spring Boot Test and AssertJ automatically added to pom.xml
- **Consistent Results**: Same output every time, no manual file manipulation required
- **Faster Setup**: Single command replaces 20+ lines of manual setup scripts

### JBang Export Features Utilized
1. **`--group`**: Sets Maven groupId to Spring AI Community namespace
2. **`--artifact`**: Sets Maven artifactId to "collection"
3. **`--version`**: Sets project version to SNAPSHOT for development
4. **`--deps`**: Automatically adds test dependencies to pom.xml
5. **`--force`**: Overwrites existing project directory for clean starts
6. **`--output-dir`**: Creates project in specified directory structure

This approach transforms what was previously a complex, error-prone manual process into a single, reliable command that handles all Maven project setup automatically.

## End Game: Maven Migration

### Final Project Structure
The Maven project will be organized within the existing project management structure:

```
/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/
├── design/
│   └── jbang_refactoring_plan.md
├── plans/
│   └── refactoring_implementation_plan.md
└── project/
    ├── pom.xml                                    # Maven configuration
    ├── README.md                                  # User guide and documentation
    ├── claude.md                                  # Claude Code assistant guide  
    └── src/
        ├── main/java/org/springaicommunity/github/ai/collection/
        │   ├── CollectGithubIssues.java           # Main orchestration
        │   ├── DataModels.java                    # Record definitions
        │   ├── ConfigurationSupport.java         # Spring configuration
        │   ├── ArgumentParser.java               # CLI processing
        │   ├── GitHubServices.java               # API interactions
        │   └── CollectionService.java            # Business logic
        ├── test/java/org/springaicommunity/github/ai/collection/
        │   ├── DataModelsTest.java
        │   ├── ConfigurationSupportTest.java
        │   ├── ArgumentParserTest.java
        │   ├── GitHubServicesTest.java
        │   ├── CollectionServiceTest.java
        │   └── IntegrationTest.java
        └── test/resources/
            ├── application-test.yaml
            └── mock-responses/
                ├── github-search-response.json
                └── github-issue-response.json
```

### Documentation Strategy
The project will include two key documentation files:
- **README.md**: End-user documentation for running and using the tool
- **claude.md**: Technical documentation for Claude Code development assistance, including:
  - Module architecture and dependencies
  - Common modification patterns
  - Testing guidelines and requirements
  - Troubleshooting guide for development issues

## Risk Mitigation

### Technical Risks
- **Spring Context Issues**: Mitigated by maintaining bean definitions
- **Circular Dependencies**: Prevented by clear dependency hierarchy
- **JBang Limitations**: Use `//SOURCES` directive for multi-file support

### Process Risks
- **Breaking Changes**: Each phase includes regression testing
- **Lost Functionality**: Golden dataset comparison after each extraction
- **Integration Issues**: Full workflow testing at module boundaries

### Rollback Strategy
- **Git Branching**: Separate branch for each extraction phase
- **Backup Preservation**: Keep working single-file version as fallback
- **Incremental Validation**: Each phase must pass full test suite

This design provides a clear path from the current monolithic JBang script to a well-structured, testable, and maintainable codebase that's ready for enterprise Maven deployment.
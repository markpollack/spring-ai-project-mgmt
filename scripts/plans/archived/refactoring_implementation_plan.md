# JBang to Maven Multi-Module Refactoring - Implementation Plan

## Build Performance Note
**For fastest compilation throughout this refactoring process, use:**
```bash
mvnd clean package -Dmaven.javadoc.skip=true -DskipTests
```
This command uses Maven Daemon (mvnd) for faster builds and skips time-consuming javadoc generation and test execution when you only need to verify compilation.

## Phase 0: Convert to Maven Project Using JBang Export
**Risk Level**: Very Low (fully automated with JBang built-in configuration)

## IMPORTANT: Phase Completion Requirements

**Every phase must include these steps before committing:**

1. **Create Lessons Learned Document**: 
   - Document in `plans/phase{N}_lessons_learned.md` all issues encountered
   - Include improvements for future similar extractions on other codebases
   - Capture testing strategies, safety measures, and process improvements

2. **Verify Clean Repository State**:
   - Run `git status` to check for unexpected files
   - Ensure no `issues/`, `logs/`, `batch_*` files are staged for commit
   - Verify .gitignore prevents temporary/generated files
   - Remove any application data created during testing

### Tasks
- [ ] Create backup of current implementation:
  ```bash
  cp /home/mark/project-mgmt/spring-ai-project-mgmt/scripts/CollectGithubIssues.java \
     /home/mark/project-mgmt/spring-ai-project-mgmt/scripts/CollectGithubIssues.backup.java
  ```
- [ ] **Use JBang export with full Maven configuration**:
  ```bash
  cd /home/mark/project-mgmt/spring-ai-project-mgmt/scripts
  
  /home/mark/.sdkman/candidates/jbang/current/bin/jbang export portable CollectGithubIssues.java \
    --output-dir=project \
    --group=org.springaicommunity.github.ai \
    --artifact=collection \
    --version=1.0.0-SNAPSHOT \
    --deps=org.springframework.boot:spring-boot-starter-test,org.assertj:assertj-core \
    --force
  ```
- [ ] **Verify JBang export results**:
  ```bash
  cd project
  
  # Verify Maven coordinates are correct
  echo "=== Maven Coordinates ==="
  grep -A 3 -B 3 "groupId\|artifactId\|version" pom.xml | head -12
  
  # Verify project structure
  echo "=== Project Structure ==="
  find src -name "*.java" -type f
  
  # Verify test dependencies were added
  echo "=== Test Dependencies ==="
  grep -A 5 -B 5 "spring-boot-starter-test\|assertj" pom.xml
  
  # Verify package declarations
  echo "=== Package Declarations ==="
  find src -name "*.java" -type f -exec grep "^package" {} \;
  ```
- [ ] Move and rename user guide:
  ```bash
  mv /home/mark/project-mgmt/spring-ai-project-mgmt/scripts/COLLECT_GITHUB_ISSUES_USER_GUIDE.md \
     /home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/README.md
  ```
- [ ] Create test resource structure:
  ```bash
  cd /home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project
  mkdir -p src/test/resources
  ```
- [ ] **Verify Maven compilation**: `mvnd clean compile -Dmaven.javadoc.skip=true -DskipTests`
- [ ] **Test Maven execution**: `mvnd spring-boot:run -Dspring-boot.run.arguments="--help"`
- [ ] **Test functionality**: `mvnd spring-boot:run -Dspring-boot.run.arguments="--dry-run"`
- [ ] **Update README.md for Maven usage**:
  ```bash
  # Update README.md to reflect Maven-based usage instead of JBang
  # Replace jbang commands with mvnd spring-boot:run commands
  # Update installation section to mention Maven requirements
  # Add Maven development workflow section
  ```
- [ ] **Git commit Phase 0 completion**:
  ```bash
  cd /home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project
  git add .
  git commit -m "Phase 0: Convert JBang to Maven project using jbang export

  - Use jbang export with full Maven configuration (group, artifact, test deps)
  - Automated package structure setup via JBang built-in capabilities
  - Move user guide to README.md
  - Create test resource directories
  - Verify Maven compilation and execution"
  ```

### Working Directory
All subsequent phases will work from: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/`

### Success Criteria
- [ ] Maven project compiles successfully with `mvnd clean package -Dmaven.javadoc.skip=true -DskipTests`
- [ ] Spring Boot application runs with Maven daemon: `mvnd spring-boot:run`
- [ ] All CLI functionality preserved
- [ ] Dry-run mode works correctly
- [ ] Phase 0 committed to git

---

## Phase 1: Extract DataModels.java
**Estimated Time**: 1-2 days  
**Risk Level**: Low (no dependencies)

### Tasks
- [ ] **Read previous lessons learned**: Review any existing `plans/phase*_lessons_learned.md` documents to apply improvements to current phase planning
- [ ] Create `src/main/java/org/springaicommunity/github/ai/collection/DataModels.java` with package declaration
- [ ] Copy all record definitions from main file:
  - [ ] Core records (Lines 501-530): `Issue`, `Comment`, `Author`, `Label`
  - [ ] Collection records (Lines 532-559): `CollectionMetadata`, `CollectionRequest`, `CollectionResult`
  - [ ] Internal records (Lines 1555-1565): `BatchData`, `CollectionStats`, `ResumeState`
- [ ] Create comprehensive test resources:
  - [ ] `src/test/resources/application-test.yaml` for test configuration
  - [ ] `src/test/resources/mock-responses/github-search-response.json`
  - [ ] `src/test/resources/mock-responses/github-issue-response.json`
- [ ] Create `src/test/java/org/springaicommunity/github/ai/collection/DataModelsTest.java` with comprehensive tests:
  - [ ] Test record creation and field access
  - [ ] Test CollectionRequest with filtering fields
  - [ ] Test with AssertJ fluent assertions
  - [ ] Test JSON serialization/deserialization of records
- [ ] Verify compilation: `mvnd clean package -Dmaven.javadoc.skip=true -DskipTests`
- [ ] Run tests: `mvnd test -Dtest=DataModelsTest`
- [ ] Remove record definitions from main file
- [ ] Final verification: `mvnd spring-boot:run -Dspring-boot.run.arguments="--dry-run"`
- [ ] **Create lessons learned document**: 
  - [ ] Create `plans/phase1_lessons_learned.md` documenting issues encountered and improvements for future DataModels extractions
  - [ ] Include updated task sequencing, testing strategies, and safety measures
- [ ] **Verify clean repository state**:
  - [ ] Run `git status` to check for unexpected files (issues/, logs/, batch files)
  - [ ] Ensure .gitignore is comprehensive and prevents data file commits
  - [ ] Remove any temporary/generated files before commit
- [ ] **Update documentation**:
  - [ ] Update `README.md` with new Maven structure and DataModels module
  - [ ] Update `claude.md` with DataModels architecture and testing patterns
- [ ] **Git commit and push Phase 1 completion**

### Success Criteria
- [ ] All tests pass with `mvnd test -Dtest=DataModelsTest`
- [ ] Main application still compiles and runs
- [ ] No functionality regression in dry-run mode
- [ ] Test resources properly organized
- [ ] Documentation updated for users and Claude Code
- [ ] Changes committed and pushed to git

---

## Phase 2: Extract ConfigurationSupport.java
**Estimated Time**: 1-2 days  
**Risk Level**: Low (foundational)

### Tasks
- [ ] **Read previous lessons learned**: Review all previous `plans/phase*_lessons_learned.md` documents to apply cumulative improvements
- [ ] Create `src/main/java/org/springaicommunity/github/ai/collection/ConfigurationSupport.java`
- [ ] Move `GitHubConfig` class (Lines 562-596)
- [ ] Move `CollectionProperties` class (Lines 1568-1644)
- [ ] Create `src/test/java/org/springaicommunity/github/ai/collection/ConfigurationSupportTest.java`:
  - [ ] Test Spring bean creation (GitHub, RestClient, GraphQL, ObjectMapper)
  - [ ] Test property binding with test profiles
  - [ ] Test configuration validation
  - [ ] Use `@SpringBootTest` for context testing
- [ ] Enhance `src/test/resources/application-test.yaml` for configuration testing
- [ ] Verify Spring context loads: `mvnd spring-boot:run -Dspring-boot.run.arguments="--dry-run"`
- [ ] Run configuration tests: `mvnd test -Dtest=ConfigurationSupportTest`
- [ ] Remove configuration classes from main file
- [ ] **Create comprehensive lessons learned document**: 
  - [ ] Create `plans/phase2_lessons_learned.md` with DETAILED, step-by-step instructions for future phases
  - [ ] Document exact testing strategies that prevent accidental production operations
  - [ ] Include emergency procedures, red flag indicators, and mandatory safety checklists
  - [ ] Provide specific testing requirements for each upcoming phase (Phase 3-7)
  - [ ] Include "what NOT to do" examples with explanations of why they're dangerous
- [ ] **Verify clean repository state**:
  - [ ] Run `git status` to check for unexpected files (issues/, logs/, batch files)
  - [ ] Ensure no application data generated during configuration testing
  - [ ] Remove any temporary/generated files before commit
- [ ] **Update documentation**:
  - [ ] Update `README.md` with ConfigurationSupport module details
  - [ ] Update `claude.md` with Spring configuration patterns and testing approach
- [ ] **Git commit and push Phase 2 completion**

### Success Criteria
- [ ] Spring context loads without errors
- [ ] Configuration tests pass with `mvnd test -Dtest=ConfigurationSupportTest`
- [ ] GitHub connectivity test still works
- [ ] All existing functionality preserved
- [ ] Documentation updated for users and Claude Code
- [ ] Changes committed and pushed to git

---

## Phase 3: Extract ArgumentParser.java
**Estimated Time**: 2-3 days  
**Risk Level**: Medium (complex logic)

### Tasks
- [ ] **Read previous lessons learned**: Review all previous `plans/phase*_lessons_learned.md` documents to apply cumulative improvements
- [ ] Create `src/main/java/org/springaicommunity/github/ai/collection/ArgumentParser.java` as Spring service
- [ ] Extract and refactor parsing methods:
  - [ ] `parseArguments()` → `parseAndValidate()` (Lines 222-340)
  - [ ] `validateConfiguration()` (Lines 377-435)
  - [ ] `validateEnvironment()` (Lines 352-375)
  - [ ] `showHelp()` (Lines 438-490)
  - [ ] `isHelpRequested()` (Lines 343-350)
- [ ] Create `ParsedConfiguration` class to hold results
- [ ] Update main class to use `ArgumentParser` service
- [ ] Create comprehensive `src/test/java/org/springaicommunity/github/ai/collection/ArgumentParserTest.java`:
  - [ ] Test all CLI argument combinations including new filtering options
  - [ ] Test validation error cases
  - [ ] Test help text generation with updated content
  - [ ] Test repository format validation
  - [ ] Test label parsing and validation (--labels, --label-mode)
  - [ ] Test state filtering validation (--state open/closed/all)
  - [ ] Test clean/no-clean flag behavior
  - [ ] Test zip flag functionality
  - [ ] Use parameterized tests for multiple scenarios
- [ ] Verify all CLI arguments work: Test matrix of common combinations
- [ ] Remove parsing logic from main file
- [ ] **Create comprehensive lessons learned document**: 
  - [ ] Create `plans/phase3_lessons_learned.md` with DETAILED, actionable instructions for future phases
  - [ ] Document specific testing approaches that prevent accidental production operations
  - [ ] Include step-by-step CLI testing patterns, parameterized test strategies, and validation approaches
  - [ ] Provide emergency procedures and safety checklists specific to argument parsing
  - [ ] Update testing requirements for remaining phases (Phase 4-7) based on new insights
  - [ ] Include examples of dangerous patterns to avoid and why they're problematic
- [ ] **Verify clean repository state**:
  - [ ] Run `git status` to check for unexpected files (issues/, logs/, batch files)
  - [ ] Ensure no test execution generated application data
  - [ ] Remove any temporary/generated files before commit
- [ ] **Update documentation**:
  - [ ] Update `README.md` with ArgumentParser module and CLI usage
  - [ ] Update `claude.md` with argument parsing patterns and validation testing
- [ ] **Git commit and push Phase 3 completion**

### Key Test Cases
```java
@ParameterizedTest
@ValueSource(strings = {"spring-projects/spring-ai", "microsoft/vscode", "kubernetes/kubernetes"})
void testValidRepositoryFormats(String repo) { ... }

@Test
void testInvalidRepositoryFormat() {
    assertThatThrownBy(() -> parser.parseAndValidate(new String[]{"--repo", "invalid"}, properties))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("Repository must be in format 'owner/repo'");
}
```

### Success Criteria
- [ ] All CLI arguments work as before
- [ ] Comprehensive test coverage for edge cases with `mvnd test -Dtest=ArgumentParserTest`
- [ ] Help text displays correctly
- [ ] Error messages are clear and helpful
- [ ] Documentation updated for users and Claude Code
- [ ] Changes committed and pushed to git

---

## Phase 4: Extract GitHubServices.java
**Estimated Time**: 2-3 days  
**Risk Level**: Medium (API interactions)

### Tasks
- [ ] **Read previous lessons learned**: Review all previous `plans/phase*_lessons_learned.md` documents to apply cumulative improvements
- [ ] Create `src/main/java/org/springaicommunity/github/ai/collection/GitHubServices.java`
- [ ] Move service classes:
  - [ ] `GitHubRestService` (Lines 599-653)
  - [ ] `GitHubGraphQLService` (Lines 655-723)
  - [ ] `JsonNodeUtils` (Lines 724-773)
- [ ] Create `src/test/java/org/springaicommunity/github/ai/collection/GitHubServicesTest.java` with mocked APIs:
  - [ ] Mock RestClient responses
  - [ ] Test search query building logic with filtering
  - [ ] Test GraphQL query construction for search-based queries
  - [ ] Test JSON response parsing
  - [ ] Test rate limit handling (simulated)
  - [ ] Test `getSearchIssueCount()` method
- [ ] Enhance test resources with realistic GitHub API response data
- [ ] Test connectivity verification still works
- [ ] Remove service classes from main file
- [ ] **Create comprehensive lessons learned document**: 
  - [ ] Create `plans/phase4_lessons_learned.md` with DETAILED, step-by-step instructions for future phases
  - [ ] Document exact API mocking strategies that prevent real GitHub API calls during testing
  - [ ] Include comprehensive patterns for mocking RestClient, GitHub responses, and network dependencies
  - [ ] Provide emergency procedures for accidental API calls and rate limit violations
  - [ ] Update testing requirements for remaining phases (Phase 5-7) with API interaction safety measures
  - [ ] Include examples of dangerous API testing patterns and their consequences
  - [ ] Document mock response creation, test data management, and network isolation techniques
- [ ] **Verify clean repository state**:
  - [ ] Run `git status` to check for unexpected files (issues/, logs/, batch files)
  - [ ] Ensure no real API calls generated data during testing
  - [ ] Remove any temporary/generated files before commit
- [ ] **Update documentation**:
  - [ ] Update `README.md` with GitHubServices module and API architecture
  - [ ] Update `claude.md` with GitHub API patterns and mocking strategies
- [ ] **Git commit and push Phase 4 completion**

### Test Approach - Read-Only Operations
```java
@Test
void testSearchQueryBuilding() {
    String query = searchService.buildSearchQuery("spring-projects", "spring-ai", 
                                                  "closed", List.of("bug"), "any");
    
    assertThat(query)
        .contains("repo:spring-projects/spring-ai")
        .contains("is:issue")
        .contains("is:closed")
        .contains("label:\"bug\"");
}

@Test
void testSearchBasedIssueCount() {
    // Mock the GraphQL search response
    JsonNode mockResponse = createMockSearchResponse(42);
    when(mockRestClient.post().body(anyString()).retrieve().body(String.class))
        .thenReturn(mockResponse.toString());
    
    int count = graphQLService.getSearchIssueCount("repo:spring-projects/spring-ai is:issue is:closed");
    
    assertThat(count).isEqualTo(42);
}
```

### Success Criteria
- [ ] GitHub connectivity test passes
- [ ] All API service tests pass with mocked responses: `mvnd test -Dtest=GitHubServicesTest`
- [ ] No actual GitHub API calls in tests
- [ ] Query building logic thoroughly tested
- [ ] Documentation updated for users and Claude Code
- [ ] Changes committed and pushed to git

---

## Phase 5: Extract CollectionService.java
**Estimated Time**: 3-4 days  
**Risk Level**: High (largest component)

### Tasks
- [ ] **Read previous lessons learned**: Review all previous `plans/phase*_lessons_learned.md` documents to apply cumulative improvements
- [ ] Create `src/main/java/org/springaicommunity/github/ai/collection/CollectionService.java`
- [ ] Move `IssueCollectionService` class (Lines 775-1555):
  - [ ] Include all collection logic, batch processing, file operations
  - [ ] Include search integration and query building
  - [ ] Include compression and command-line documentation features
- [ ] Create comprehensive `src/test/java/org/springaicommunity/github/ai/collection/CollectionServiceTest.java`:
  - [ ] Test batch processing logic with sample data
  - [ ] Test file operations with temporary directories
  - [ ] Test compression functionality with zip creation
  - [ ] Test resume state management
  - [ ] Test adaptive batch sizing
  - [ ] Test search query building with state and label filters
  - [ ] Test command line documentation in zip files
  - [ ] Mock GitHub service dependencies
- [ ] Create test utilities for file system operations
- [ ] Test error handling and recovery scenarios
- [ ] Remove collection service from main file
- [ ] **Create comprehensive lessons learned document - HIGHEST PRIORITY**: 
  - [ ] Create `plans/phase5_lessons_learned.md` with EXTREMELY DETAILED safety instructions for future phases
  - [ ] Document CRITICAL file system testing patterns using @TempDir to prevent production data creation
  - [ ] Include comprehensive batch processing test strategies with mocked data only
  - [ ] Provide emergency procedures for accidental file system operations and data generation
  - [ ] Update testing requirements for remaining phases (Phase 6-7) with file system safety measures
  - [ ] Include FORBIDDEN patterns list - testing approaches that MUST NEVER be used
  - [ ] Document temporary directory management, cleanup procedures, and data isolation techniques
  - [ ] Include step-by-step verification commands to ensure no production data is created during testing
  - [ ] Provide specific guidance for testing compression, file operations, and batch processing safely
- [ ] **Verify clean repository state**:
  - [ ] Run `git status` to check for unexpected files (issues/, logs/, batch files)
  - [ ] Ensure test temporary directories were cleaned up
  - [ ] Verify no zip files or collection data left behind
  - [ ] Remove any temporary/generated files before commit
- [ ] **Update documentation**:
  - [ ] Update `README.md` with CollectionService module and business logic architecture
  - [ ] Update `claude.md` with collection patterns, batch processing, and file operations
- [ ] **Git commit and push Phase 5 completion**

### Key Test Areas
```java
@Test
void testAdaptiveBatchCreation() {
    List<Issue> largeIssueSet = createTestIssues(500);
    
    List<Issue> batch = collectionService.createAdaptiveBatch(largeIssueSet, 100);
    
    assertThat(batch)
        .hasSizeLessThanOrEqualTo(100)
        .allSatisfy(issue -> assertThat(estimateSize(issue)).isLessThan(MAX_SIZE));
}

@Test
void testSearchQueryBuildingWithFilters(@TempDir Path tempDir) {
    String query = collectionService.buildSearchQuery("spring-projects", "spring-ai", 
                                                      "closed", List.of("bug", "enhancement"), "all");
    
    assertThat(query)
        .contains("repo:spring-projects/spring-ai")
        .contains("is:issue")
        .contains("is:closed")
        .contains("label:\"bug\"")
        .contains("label:\"enhancement\"");
}

@Test
void testZipArchiveWithCommandLineDocumentation(@TempDir Path tempDir) {
    CollectionRequest request = new CollectionRequest(
        "spring-projects/spring-ai", 100, false, false, true, true, false,
        "closed", List.of("bug"), "any"
    );
    
    collectionService.createCompressedArchive(tempDir, request);
    
    Path zipFile = tempDir.resolve("issues-compressed")
                          .resolve("spring-projects-spring-ai_closed_*_labels-bug.zip");
    
    assertThat(zipFile.getParent()).exists();
    // Verify zip contains collection-info.md with command line args
}
```

### Success Criteria
- [ ] All collection tests pass: `mvnd test -Dtest=CollectionServiceTest`
- [ ] File operations work correctly
- [ ] Compression generates valid zip files
- [ ] Resume functionality works as expected
- [ ] No data loss in batch processing
- [ ] Documentation updated for users and Claude Code
- [ ] Changes committed and pushed to git

---

## Phase 6: Create Claude Code Assistant Documentation
**Risk Level**: None (documentation only)

### Tasks
- [ ] **Read previous lessons learned**: Review all previous `plans/phase*_lessons_learned.md` documents to apply cumulative improvements
- [ ] Create `claude.md` in project root with Claude Code specific guidance
- [ ] Document the modular architecture for Claude Code understanding
- [ ] Provide common modification patterns and examples
- [ ] Include testing guidelines for Claude Code
- [ ] Document module boundaries and responsibilities
- [ ] Create troubleshooting guide for development issues
- [ ] **Create comprehensive lessons learned document**: 
  - [ ] Create `plans/phase6_lessons_learned.md` with DETAILED documentation and knowledge management strategies
  - [ ] Document effective documentation patterns that prevent future development mistakes
  - [ ] Include comprehensive guidelines for creating safety-focused development documentation
  - [ ] Provide templates and examples for phase-specific safety instructions
  - [ ] Update documentation requirements for Phase 7 with accumulated safety knowledge
  - [ ] Include best practices for maintaining safety documentation across complex refactoring projects
  - [ ] Document effective knowledge transfer patterns for future developers and AI assistants
- [ ] **Verify clean repository state**:
  - [ ] Run `git status` to check for unexpected files
  - [ ] Ensure all documentation is properly organized
  - [ ] Remove any temporary/generated files before commit
- [ ] **Update documentation**:
  - [ ] Update `README.md` with final modular architecture overview
  - [ ] Finalize `claude.md` with complete development guide
- [ ] **Git commit and push Phase 6 completion**

### Claude.md Content Structure
```markdown
# CollectGithubIssues - Claude Code Assistant Guide

## Architecture Overview
- Module structure and dependencies
- Key design patterns used
- Testing approach and frameworks

## Common Modification Patterns
- Adding new CLI arguments
- Adding new GitHub API features
- Modifying collection logic
- Adding new output formats

## Development Guidelines
- Testing requirements for changes
- Module boundary rules
- Error handling patterns

## Troubleshooting
- Common development issues
- Testing problems and solutions
- Maven-specific considerations
```

### Success Criteria
- [ ] Claude.md file created with comprehensive guidance
- [ ] Documentation covers all modules and their purposes
- [ ] Common modification patterns documented
- [ ] Testing guidelines included
- [ ] README.md updated with final architecture overview
- [ ] Changes committed and pushed to git

---

## Phase 7: Refactor Main Class & Integration Testing
**Estimated Time**: 2-3 days  
**Risk Level**: Medium (integration)

### Tasks
- [ ] **Read previous lessons learned**: Review all previous `plans/phase*_lessons_learned.md` documents to apply cumulative improvements
- [ ] Refactor `src/main/java/org/springaicommunity/github/ai/collection/CollectGithubIssues.java` to orchestration only
- [ ] Create comprehensive `src/test/java/org/springaicommunity/github/ai/collection/IntegrationTest.java`:
  - [ ] End-to-end workflow testing
  - [ ] Test complete argument processing pipeline
  - [ ] Test Spring context integration
  - [ ] Test with multiple repository scenarios
- [ ] Performance testing with realistic data volumes
- [ ] Create test documentation and examples
- [ ] Final cleanup and code review
- [ ] **Create comprehensive final lessons learned document**: 
  - [ ] Create `plans/phase7_lessons_learned.md` with COMPLETE refactoring retrospective and safety guidelines
  - [ ] Document safe integration testing patterns that prevent accidental production operations
  - [ ] Include comprehensive end-to-end testing strategies with full mocking and --dry-run simulation
  - [ ] Provide final safety checklist for entire refactored application
  - [ ] Create master reference guide combining all phase learnings into unified safety protocol
  - [ ] Include performance validation techniques that don't trigger real data collection
  - [ ] Document long-term maintenance patterns and safety measures for future development
  - [ ] Provide comprehensive troubleshooting guide for common integration testing issues
  - [ ] Include final recommendations for similar refactoring projects on other codebases
- [ ] **Verify clean repository state**:
  - [ ] Run `git status` to check for unexpected files (issues/, logs/, batch files)
  - [ ] Ensure integration tests didn't generate application data
  - [ ] Verify no performance test artifacts remain
  - [ ] Remove any temporary/generated files before commit
- [ ] **Update documentation**:
  - [ ] Final update to `README.md` with complete usage instructions
  - [ ] Final update to `claude.md` with integration testing patterns
- [ ] **Git commit and push Phase 7 completion**

### Main Class Final Structure
```java
package org.springaicommunity.github.ai.collection;

@SpringBootApplication
public class CollectGithubIssues implements CommandLineRunner {
    
    private final ArgumentParser argumentParser;
    private final IssueCollectionService collectionService;
    private final GitHubRestService restService;
    
    public static void main(String[] args) {
        SpringApplication.run(CollectGithubIssues.class, args);
    }
    
    @Override
    public void run(String... args) throws Exception {
        // 1. Parse arguments (includes filtering options)
        // 2. Test connectivity
        // 3. Start collection (with search-based queries)
    }
}
```

### Integration Test Coverage
- [ ] Full dry-run workflow
- [ ] Argument validation integration
- [ ] Service layer integration
- [ ] Error handling across modules
- [ ] Performance with large argument sets

### Success Criteria
- [ ] All integration tests pass: `mvnd test -Dtest=IntegrationTest`
- [ ] Performance meets or exceeds original
- [ ] Error handling works across module boundaries
- [ ] Complete feature parity with original
- [ ] Documentation updated for users and Claude Code
- [ ] Changes committed and pushed to git

---

## Final Validation Checklist

### Functionality Tests
- [ ] Basic collection: `mvnd spring-boot:run -Dspring-boot.run.arguments="--dry-run"`
- [ ] State filtering: `mvnd spring-boot:run -Dspring-boot.run.arguments="--state open --dry-run"`
- [ ] Label filtering: `mvnd spring-boot:run -Dspring-boot.run.arguments="--labels bug --dry-run"`
- [ ] Combined filtering: `mvnd spring-boot:run -Dspring-boot.run.arguments="--state closed --labels documentation,enhancement --label-mode all --dry-run"`
- [ ] Batch sizing: `mvnd spring-boot:run -Dspring-boot.run.arguments="--batch-size 50 --dry-run"`
- [ ] Zip functionality: `mvnd spring-boot:run -Dspring-boot.run.arguments="--zip --dry-run"`
- [ ] Clean behavior: `mvnd spring-boot:run -Dspring-boot.run.arguments="--no-clean --dry-run"`
- [ ] Help display: `mvnd spring-boot:run -Dspring-boot.run.arguments="--help"`
- [ ] Error handling: `mvnd spring-boot:run -Dspring-boot.run.arguments="--repo invalid"`

### Test Suite Validation
- [ ] All unit tests pass: `mvnd test`
- [ ] Integration tests pass: `mvnd test -Dtest=IntegrationTest`
- [ ] No external API calls in test runs
- [ ] Test coverage meets expectations: `mvnd jacoco:report`

### Documentation Updates
- [ ] Update README with new Maven structure
- [ ] Create module documentation
- [ ] Update troubleshooting guide
- [ ] Document testing approach

## Rollback Procedures

### Per-Phase Rollback
If any phase fails:
1. **Stop immediately** - don't proceed to next phase
2. **Revert to previous git branch** - each phase has its own branch
3. **Analyze failure** - determine root cause
4. **Fix and retry** - address issues before proceeding

### Emergency Rollback
If critical issues discovered after multiple phases:
1. **Use backup single file**: `CollectGithubIssues.backup.java`
2. **Restore from git tag**: Each completed phase tagged
3. **Document lessons learned**: Update implementation plan

This plan provides a systematic, low-risk approach to refactoring the monolithic JBang script into a maintainable, testable Maven-based architecture.
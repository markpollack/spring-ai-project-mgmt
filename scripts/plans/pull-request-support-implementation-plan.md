# Pull Request Support Implementation Plan
*Adding Pull Request Collection to CollectGithubIssues.java*

## Overview

This plan outlines the step-by-step implementation to extend the existing `CollectGithubIssues.java` application to support collecting pull requests in addition to issues. The implementation will maintain backward compatibility while adding comprehensive pull request collection capabilities.

## Project Context

- **Base Application**: CollectGithubIssues.java - JBang Spring Boot 3.x application
- **Current Capability**: Collects GitHub issues with advanced filtering (state, labels, batch processing)
- **Target Enhancement**: Add pull request collection with similar filtering and processing capabilities
- **Architecture**: Spring Boot with GraphQL and REST API integration, JSON output with optional ZIP compression

## Implementation Phases

### Phase 1: Planning and Analysis ✅

**Objectives**: Understand current architecture and API requirements for pull requests

**Tasks Completed**:
- [x] Analyze existing CollectGithubIssues.java structure and components
- [x] Research GitHub API capabilities for pull request collection
- [x] Compare pull request vs issue data structures and API access patterns
- [x] Identify implementation approach and architecture changes needed

**Key Findings**:
- Pull requests share most infrastructure with issues but offer richer code review data
- Same GitHub APIs (GraphQL, REST, Search) with different object types and fields
- Requires new data models and query adaptations but minimal architectural changes

---

### Phase 2: Data Model Enhancement

**Objectives**: Extend data models to support pull request-specific fields while maintaining compatibility

#### Task 2.1: Create Pull Request Data Models
- [ ] Create `PullRequest` record class with all PR-specific fields
  - [ ] Add basic metadata (extends issue fields)
  - [ ] Add PR-specific fields (`isDraft`, `mergeable`, `merged`, etc.)
  - [ ] Add code change statistics (`additions`, `deletions`, `changedFiles`)
  - [ ] Add branch information (`baseRefName`, `headRefName`, commit SHAs)
  - [ ] Add review data (`reviewDecision`, merge information)

#### Task 2.2: Create Supporting Data Models
- [ ] Create `PullRequestReview` record for review data
- [ ] Create `PullRequestCommit` record for commit information
- [ ] Create `PullRequestFile` record for changed files (optional for initial implementation)
- [ ] Update JSON serialization to handle new models

#### Task 2.3: Enhance Collection Types
- [ ] Create `CollectionType` enum (ISSUES, PULL_REQUESTS, BOTH)
- [ ] Update configuration properties to support collection type selection
- [ ] Modify CLI argument parsing to accept collection type

**Expected Outcome**: Complete data model support for pull requests with JSON serialization

---

### Phase 3: API Service Enhancement

**Objectives**: Extend GraphQL and REST services to handle pull request queries and data fetching

#### Task 3.1: GraphQL Service Updates
- [ ] Create pull request-specific GraphQL queries
  - [ ] Base PR query template with core fields
  - [ ] Enhanced PR query template with review/commit data
  - [ ] Search query modifications for PR filtering
- [ ] Update `GitHubGraphQLService` class
  - [ ] Add PR query methods parallel to issue methods
  - [ ] Handle PR-specific pagination and batching
  - [ ] Add PR search query building with `is:pr` qualifier
- [ ] Update query response parsing
  - [ ] Add PR response parsing methods
  - [ ] Handle PR-specific nested data (reviews, commits)
  - [ ] Update error handling for PR queries

#### Task 3.2: REST Service Updates  
- [ ] Add pull request REST endpoints to `GitHubRestService`
  - [ ] PR listing endpoint (`/repos/{owner}/{repo}/pulls`)
  - [ ] Individual PR details endpoint
  - [ ] PR-specific metadata endpoints (optional)
- [ ] Update search service for PR search queries
- [ ] Add PR rate limiting considerations (same limits as issues)

#### Task 3.3: Search Query Enhancement
- [ ] Extend search query builder for PR-specific qualifiers
  - [ ] Add `is:pr` qualifier support
  - [ ] Add `is:draft` filter support  
  - [ ] Add `review:` state filters
  - [ ] Add `base:` and `head:` branch filters
- [ ] Update filter validation for PR-specific filters
- [ ] Maintain backward compatibility with issue-only searches

**Expected Outcome**: Complete API service layer capable of fetching pull request data with filtering

---

### Phase 4: Collection Service Integration

**Objectives**: Integrate pull request collection into the main collection workflow

#### Task 4.1: Collection Service Updates
- [ ] Update `IssueCollectionService` to `ItemCollectionService` (generic)
  - [ ] Add collection type parameter to main collection methods
  - [ ] Branch collection logic based on type (issues vs PRs vs both)
  - [ ] Maintain separate batch processing for each type
- [ ] Update batch processing for pull requests
  - [ ] Handle larger PR data payloads (may need smaller batch sizes)
  - [ ] Add PR-specific metadata to batch files
  - [ ] Update progress reporting for PR collection

#### Task 4.2: File Organization Updates
- [ ] Update output directory structure
  - [ ] Create separate directories: `issues/`, `pull-requests/`, `combined/`
  - [ ] Maintain existing structure for backward compatibility
  - [ ] Update ZIP archive organization for multiple collection types
- [ ] Update metadata.json format
  - [ ] Add collection type information
  - [ ] Add PR-specific statistics
  - [ ] Include both issue and PR counts when collecting both

#### Task 4.3: Dual Collection Support
- [ ] Implement BOTH collection type
  - [ ] Sequential collection: issues first, then PRs
  - [ ] Separate batch processing with combined metadata
  - [ ] Unified progress reporting across both types
- [ ] Add collection resume support for PRs
- [ ] Update incremental collection logic

**Expected Outcome**: Fully integrated collection service supporting issues, PRs, or both

---

### Phase 5: Command Line Interface Enhancement

**Objectives**: Extend CLI to support pull request collection with intuitive options

#### Task 5.1: CLI Argument Updates
- [ ] Add `--type` or `--collection-type` option
  - [ ] Values: `issues`, `pull-requests`, `prs`, `both` (default: `issues`)
  - [ ] Maintain backward compatibility (default to issues only)
- [ ] Add PR-specific filter options
  - [ ] `--draft` / `--no-draft` for draft PR filtering
  - [ ] `--review-state` for review status filtering
  - [ ] `--base-branch` and `--head-branch` for branch filtering
- [ ] Update help text and usage examples

#### Task 5.2: Configuration Integration
- [ ] Update `CollectionProperties` for PR options
- [ ] Add application.yaml configuration examples
- [ ] Update CLI parsing logic for new options
- [ ] Add validation for PR-specific option combinations

#### Task 5.3: User Experience Updates
- [ ] Update dry-run output to show PR collection plans
- [ ] Add collection type to progress logging
- [ ] Update final summary to include PR statistics
- [ ] Improve error messages for PR-specific scenarios

**Expected Outcome**: Complete CLI interface supporting all PR collection options

---

### Phase 6: Output Format and Documentation

**Objectives**: Ensure consistent output formats and comprehensive documentation

#### Task 6.1: Output Format Consistency
- [ ] Update JSON batch file structure for PRs
  - [ ] Maintain same batch structure as issues
  - [ ] Add PR-specific fields to JSON output
  - [ ] Ensure consistent timestamp and metadata format
- [ ] Update ZIP archive format
  - [ ] Include collection type in archive naming
  - [ ] Update collection-info.md for PR commands
  - [ ] Maintain backward compatibility with issue-only archives

#### Task 6.2: Documentation Updates
- [ ] Update main user guide (`COLLECT_GITHUB_ISSUES_USER_GUIDE.md`)
  - [ ] Add pull request collection section
  - [ ] Update all examples to show PR options
  - [ ] Add PR-specific filtering examples
  - [ ] Update troubleshooting section
- [ ] Update README and inline documentation
- [ ] Add PR-specific configuration examples
- [ ] Update JBang usage examples in CLAUDE.md

#### Task 6.3: Example and Template Updates
- [ ] Create example PR collection commands
- [ ] Update application.yaml with PR configuration
- [ ] Add PR collection to testing scripts
- [ ] Update validation scripts to test PR functionality

**Expected Outcome**: Complete documentation and examples for PR collection

---

### Phase 7: Testing and Validation

**Objectives**: Comprehensive testing of PR collection functionality with backward compatibility verification

#### Task 7.1: Unit Testing
- [ ] Test PR data model serialization/deserialization
- [ ] Test GraphQL query generation for PRs
- [ ] Test REST API integration for PRs
- [ ] Test filtering logic for PR-specific options
- [ ] Test collection type branching logic

#### Task 7.2: Integration Testing
- [ ] Test end-to-end PR collection workflow
  - [ ] Small repository with few PRs
  - [ ] Large repository with many PRs
  - [ ] Repository with mix of issues and PRs
- [ ] Test all collection types (issues, PRs, both)
- [ ] Test filtering combinations
  - [ ] State filtering (open, closed, merged)
  - [ ] Label filtering with PRs
  - [ ] Draft PR filtering
  - [ ] Review state filtering

#### Task 7.3: Backward Compatibility Testing
- [ ] Verify existing issue collection unchanged
- [ ] Test existing CLI options still work
- [ ] Verify existing output formats unchanged
- [ ] Test existing configuration files still work
- [ ] Validate existing scripts and workflows

#### Task 7.4: Performance Testing
- [ ] Test PR collection performance vs issues
- [ ] Validate batch size recommendations for PRs
- [ ] Test rate limiting behavior with PR queries
- [ ] Measure memory usage with PR data

**Expected Outcome**: Fully tested implementation with verified backward compatibility

---

### Phase 8: Final Integration and Documentation

**Objectives**: Polish implementation and finalize all documentation

#### Task 8.1: Code Review and Refinement
- [ ] Code review of all changes
- [ ] Performance optimization for PR queries
- [ ] Error handling refinement
- [ ] Logging improvements

#### Task 8.2: Documentation Finalization
- [ ] Final user guide review and updates
- [ ] Code documentation and inline comments
- [ ] Example command validation
- [ ] Migration guide for users (if needed)

#### Task 8.3: Release Preparation
- [ ] Final testing on target repositories (spring-projects/spring-ai)
- [ ] Version tagging and changelog
- [ ] Usage example validation
- [ ] Performance benchmark documentation

**Expected Outcome**: Production-ready implementation with complete documentation

---

## Technical Implementation Details

### Key Architecture Changes

```java
// Enhanced Collection Type Support
public enum CollectionType {
    ISSUES("issues", "is:issue"),
    PULL_REQUESTS("pull-requests", "is:pr"), 
    BOTH("both", null);
    
    private final String directoryName;
    private final String searchQualifier;
}

// Updated CLI Arguments
@CommandLineRunner
public class CollectGithubIssues {
    @Value("${collection.type:issues}")
    private String collectionType;
    
    @Value("${pullrequest.draft-filter:}")
    private String draftFilter; // "draft", "no-draft", ""
    
    @Value("${pullrequest.review-state:}")
    private String reviewState; // "approved", "changes_requested", etc.
}

// Enhanced Data Models
public record PullRequest(
    // Issue fields
    int number, String title, String body, String state,
    LocalDateTime createdAt, LocalDateTime updatedAt, LocalDateTime closedAt,
    String url, Author author, List<Label> labels,
    
    // PR-specific fields
    boolean isDraft, String mergeable, boolean merged, LocalDateTime mergedAt,
    Author mergedBy, int additions, int deletions, int changedFiles,
    String baseRefName, String headRefName, String reviewDecision,
    List<PullRequestReview> reviews
) {}
```

### Directory Structure Changes

```
collection-output/
├── issues/                    # Issue collections (existing)
│   └── raw/closed/batch_*/
├── pull-requests/             # PR collections (new)
│   └── raw/open/batch_*/
└── combined/                  # Both issues and PRs (new)
    └── batch_*/
        ├── issues_batch_*.json
        └── pullrequests_batch_*.json
```

### CLI Usage Examples

```bash
# Existing usage (unchanged)
jbang CollectGithubIssues.java --repo spring-projects/spring-ai

# New PR collection options
jbang CollectGithubIssues.java --type pull-requests --state open
jbang CollectGithubIssues.java --type prs --draft --labels bug
jbang CollectGithubIssues.java --type both --zip

# Advanced PR filtering
jbang CollectGithubIssues.java --type prs --review-state approved --base-branch main
```

## Risk Assessment and Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|---------|-------------|------------|
| **API Rate Limits** | High | Medium | Implement same rate limiting as issues, provide batch size guidance |
| **Large PR Data** | Medium | High | Use smaller default batch sizes, add memory monitoring |
| **Backward Compatibility** | High | Low | Comprehensive testing, default to existing behavior |
| **GraphQL Complexity** | Medium | Medium | Optimize queries, provide fallback to REST |

### User Experience Risks

| Risk | Impact | Probability | Mitigation |
|------|---------|-------------|------------|
| **CLI Confusion** | Medium | Medium | Clear documentation, intuitive defaults, good help text |
| **Output Format Changes** | High | Low | Maintain existing formats, separate PR outputs |
| **Performance Degradation** | Low | Low | Performance testing, optimization |

## Success Criteria

### Functional Requirements
- [ ] Collect pull requests with same reliability as issues
- [ ] Support all filtering options (state, labels, draft status, review state)
- [ ] Maintain 100% backward compatibility with existing issue collection
- [ ] Support combined collection of both issues and PRs
- [ ] Generate consistent JSON and ZIP outputs

### Performance Requirements  
- [ ] PR collection performance within 2x of issue collection time
- [ ] Memory usage remains reasonable for large repositories
- [ ] Rate limiting handled gracefully for PR queries

### User Experience Requirements
- [ ] Intuitive CLI options following existing patterns
- [ ] Clear documentation with comprehensive examples
- [ ] Helpful error messages for PR-specific scenarios
- [ ] Dry-run support for all PR collection options

## Timeline Estimate

**Total Estimated Time**: 3-4 weeks

- **Phase 1**: ✅ Completed
- **Phase 2-3**: 1 week (Data models and API services)
- **Phase 4-5**: 1 week (Collection service and CLI)
- **Phase 6**: 0.5 weeks (Documentation and output formats)
- **Phase 7**: 1 week (Testing and validation)
- **Phase 8**: 0.5 weeks (Final integration and polish)

## Dependencies

- Existing CollectGithubIssues.java functionality must remain stable
- GitHub API access and rate limits
- JBang and Spring Boot 3.x framework
- GitHub token with repository read permissions
- Test repositories with sufficient PR data for validation

---

*This implementation plan provides a comprehensive roadmap for adding pull request support to CollectGithubIssues.java while maintaining full backward compatibility and providing a consistent user experience.*
# GitHub Downloader - Dashboard UI Enhancement Specification

## Overview

This specification defines enhancements to the github-downloader library to support dashboard and UI use cases that require limited, sorted, and filtered issue collections rather than complete repository dumps.

## Problem Statement

**Current Behavior**: The github-downloader library collects ALL issues matching search criteria (e.g., 631 open issues from spring-projects/spring-ai), with `batchSize` only controlling file chunking.

**Dashboard Requirement**: UI applications need limited, recent, sorted collections (e.g., "20 most recently updated issues") for performance and user experience.

**Example Use Case**: Spring AI Garden Hunt dashboard needs 20 most recent open issues, but currently gets all 631 issues and must filter client-side.

## Proposed CollectionRequest Enhancements

### Phase 1: Essential Parameters (High Priority)

Add these parameters to `CollectionRequest` record:

```java
public record CollectionRequest(
    // Existing parameters
    String repository,
    int batchSize,
    boolean dryRun,
    boolean incremental,
    boolean zip,
    boolean clean,
    boolean resume,
    String issueState,
    List<String> labelFilters,
    String labelMode,
    
    // NEW: Essential for dashboard UIs
    Integer maxIssues,        // null = unlimited (backward compatible)
    String sortBy,            // "updated" | "created" | "comments" | "reactions"
    String sortOrder          // "desc" | "asc"
) {}
```

### Phase 2: Date Filtering (Medium Priority)

```java
    // NEW: Date-based filtering
    LocalDateTime since,      // Only issues updated/created since this date
    LocalDateTime until,      // Only issues updated/created before this date
    String dateRange         // "last_week" | "last_month" | "last_3_months" | null
```

### Phase 3: Advanced Search (Lower Priority)

```java
    // NEW: Enhanced search capabilities
    List<String> searchTerms,     // Additional search keywords
    boolean includePullRequests,  // Include PRs in results (default: false)
    String assigneeFilter,        // "unassigned" | username | "any"
    String collectionMode        // "dashboard" | "full" | "sample"
```

## Implementation Details

### 1. maxIssues Parameter

**Behavior**:
- `null` or `0`: Unlimited collection (current behavior, backward compatible)
- `> 0`: Limit total issues collected to this number
- Combined with sorting to get "top N" results

**Implementation**:
- Modify GitHub API queries to use `per_page` and pagination limits
- For GraphQL: Use `first: maxIssues` parameter
- For REST API: Use `per_page` parameter and stop after reaching limit

### 2. sortBy and sortOrder Parameters

**Valid sortBy Values**:
- `"updated"`: Sort by `updated_at` field (default for dashboard use)
- `"created"`: Sort by `created_at` field
- `"comments"`: Sort by comment count
- `"reactions"`: Sort by reaction count

**Valid sortOrder Values**:
- `"desc"`: Descending order (newest/highest first) - default
- `"asc"`: Ascending order (oldest/lowest first)

**GitHub API Integration**:
- REST API: Use `sort` and `direction` parameters
- GraphQL: Use `orderBy` parameter in queries

### 3. Date Filtering

**Implementation Options**:
1. **since/until**: Direct date parameters passed to GitHub API
2. **dateRange**: Predefined ranges converted to since/until internally

**GitHub API Integration**:
- Use `updated` or `created` qualifiers in search queries
- Example: `repo:spring-projects/spring-ai is:issue is:open updated:>2024-08-01`

## Usage Examples

### Dashboard Use Case (Spring AI Garden Hunt)
```java
CollectionRequest request = new CollectionRequest(
    "spring-projects/spring-ai",  // repository
    20,                           // batchSize (file chunking)
    false,                        // dryRun
    false,                        // incremental
    false,                        // zip
    true,                         // clean
    false,                        // resume
    "open",                       // issueState
    List.of(),                    // labelFilters
    "any",                        // labelMode
    20,                           // maxIssues ← NEW: Only collect 20 issues
    "updated",                    // sortBy ← NEW: Sort by last updated
    "desc"                        // sortOrder ← NEW: Most recent first
);
```

### Recent Activity Dashboard
```java
CollectionRequest request = new CollectionRequest(
    // ... other parameters
    50,                           // maxIssues: Show 50 most recent
    "updated",                    // sortBy: Sort by activity
    "desc",                       // sortOrder: Most recent first
    LocalDateTime.now().minus(7, ChronoUnit.DAYS), // since: Last week only
    null,                         // until: No end date
    null                          // dateRange: Using explicit dates
);
```

### Good First Issues for Newcomers
```java
CollectionRequest request = new CollectionRequest(
    // ... other parameters
    25,                           // maxIssues: Show 25 beginner-friendly issues
    "created",                    // sortBy: Sort by creation date
    "desc",                       // sortOrder: Newest first
    List.of("good first issue"),  // labelFilters: Beginner-friendly
    "all"                         // labelMode: Must have all labels
);
```

## Backward Compatibility

**Guaranteed**: All existing code continues to work without changes.

**Default Values**:
- `maxIssues`: `null` (unlimited collection)
- `sortBy`: `"updated"` (GitHub API default)
- `sortOrder`: `"desc"` (most recent first)

**Migration Path**: Existing `CollectionRequest` constructors remain valid; new parameters are optional.

## Implementation Priority

### Phase 1 (Critical for Dashboard UIs)
1. Add `maxIssues`, `sortBy`, `sortOrder` parameters
2. Modify GitHub API queries to respect limits and sorting
3. Update documentation and examples
4. Add unit tests for new parameters

### Phase 2 (Enhanced Filtering)
1. Add date filtering parameters
2. Implement predefined date ranges
3. Add integration tests

### Phase 3 (Advanced Features)
1. Enhanced search capabilities
2. Collection modes
3. Performance optimizations

## Testing Requirements

### Unit Tests
- Parameter validation
- Default value handling
- Backward compatibility
- GitHub API query construction

### Integration Tests
- Real GitHub API calls with new parameters
- Performance testing with large repositories
- Dashboard use case validation

### Performance Benchmarks
- Compare collection times: unlimited vs. limited
- Memory usage with different `maxIssues` values
- API rate limit efficiency

## Expected Benefits

### For Dashboard Applications
- **Performance**: 20 issues vs. 631 issues = ~30x faster
- **UX**: Immediate loading of relevant issues
- **API Efficiency**: Fewer GitHub API calls and rate limit usage

### For Spring AI Garden Hunt
- **Current**: 21+ seconds to collect 631 issues
- **With Enhancement**: ~1-2 seconds to collect 20 recent issues
- **User Experience**: Near-instant "fresh hunt" results

## Files to Modify

### Core Changes
1. `CollectionRequest.java` - Add new parameters
2. `IssueCollectionService.java` - Implement filtering logic
3. `GitHubGraphQLService.java` - Add sorting/limiting to GraphQL queries
4. `GitHubRestService.java` - Add sorting/limiting to REST queries

### Supporting Changes
1. Update argument parsing for CLI usage
2. Update documentation and examples
3. Add comprehensive test coverage
4. Update Spring configuration examples

## Success Criteria

1. **Dashboard Performance**: 20-issue collection completes in <3 seconds
2. **Backward Compatibility**: All existing code works unchanged
3. **API Efficiency**: Reduced GitHub API calls for limited collections
4. **Documentation**: Clear examples for common dashboard use cases
5. **Testing**: >90% code coverage for new functionality

This enhancement will make the github-downloader library suitable for both comprehensive data collection and efficient dashboard applications.
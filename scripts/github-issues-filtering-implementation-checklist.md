
# GitHub Issues Filtering - Implementation Checklist

## Phase 1: Core Infrastructure Setup ✅

### 1.1 Add New Fields to Main Class ✅
- [x] Add `issueState` field with default value "closed"
- [x] Add `labelFilters` field as `List<String>` initialized to empty ArrayList
- [x] Add `labelMode` field with default value "any"
- [x] Add getter methods for all new fields

### 1.2 Update Configuration Properties ✅
- [x] Add `defaultState` property to `CollectionProperties` class
- [x] Add `defaultLabels` property as `List<String>` to `CollectionProperties` class
- [x] Add `defaultLabelMode` property to `CollectionProperties` class
- [x] Add getter and setter methods for all new properties

### 1.3 Initialize Configuration ✅
- [x] Update `initializeConfiguration()` method to set filtering fields from properties
- [x] Add debug logging for initialized filtering values

## Phase 2: Command Line Interface ✅

### 2.1 Add Command Line Argument Parsing ✅
- [x] Add case for `-s, --state` option in `parseArguments()` method
- [x] Validate state value is one of: open, closed, all
- [x] Add case for `-l, --labels` option in `parseArguments()` method
- [x] Parse comma-separated labels and trim whitespace
- [x] Add case for `--label-mode` option in `parseArguments()` method
- [x] Validate label-mode value is one of: any, all
- [x] Add error handling and exit for invalid values

### 2.2 Update Help Documentation ✅
- [x] Add state option to help text with default value
- [x] Add labels option to help text with example
- [x] Add label-mode option to help text with default value

### 2.3 Update Validation ✅
- [x] Add state validation to `validateConfiguration()` method
- [x] Add label-mode validation to `validateConfiguration()` method
- [x] Add appropriate error messages for validation failures

## Phase 3: Search API Integration

### 3.1 Create Search Query Builder
- [ ] Create `buildSearchQuery()` method in `IssueCollectionService` class
- [ ] Add repository and issue type to base query
- [ ] Add state filtering logic (open/closed/all)
- [ ] Add label filtering logic for single labels
- [ ] Add label filtering logic for multiple labels with "all" mode
- [ ] Add label filtering logic for multiple labels with "any" mode
- [ ] Add proper label escaping and quoting

### 3.2 Update GraphQL Queries
- [ ] Create new `buildSearchIssuesQuery()` method
- [ ] Replace repository-based query with search-based query
- [ ] Ensure all required issue fields are included
- [ ] Update query to handle search pagination

### 3.3 Add Search Count Method
- [ ] Create `getSearchIssueCount()` method in `GitHubGraphQLService`
- [ ] Use search API to get total count for filtered results
- [ ] Handle search API response structure

## Phase 4: Collection Logic Updates

### 4.1 Update Collection Request
- [ ] Add new filtering fields to `CollectionRequest` record
- [ ] Update record constructor to include new fields
- [ ] Update all places that create `CollectionRequest` instances

### 4.2 Update Collection Method
- [ ] Modify `collectInBatches()` to use search query instead of repository query
- [ ] Update GraphQL variables to use search parameters
- [ ] Update result extraction to handle search response structure
- [ ] Update pagination logic for search API

### 4.3 Update Main Collection Flow
- [ ] Update `collectIssues()` method to use search-based counting
- [ ] Update progress logging to reflect filtered results
- [ ] Update `run()` method to pass new fields to `CollectionRequest`

## Phase 5: Testing and Validation

### 5.1 Basic Functionality Tests
- [ ] Test default behavior (closed issues, no labels) - should be unchanged
- [ ] Test state filtering: `--state open`
- [ ] Test state filtering: `--state closed`
- [ ] Test state filtering: `--state all`

### 5.2 Label Filtering Tests
- [ ] Test single label filtering: `--labels bug`
- [ ] Test multiple labels with any mode: `--labels bug,enhancement --label-mode any`
- [ ] Test multiple labels with all mode: `--labels bug,priority:high --label-mode all`
- [ ] Test with labels containing spaces and special characters

### 5.3 Combined Filtering Tests
- [ ] Test state + single label: `--state open --labels bug`
- [ ] Test state + multiple labels: `--state closed --labels bug,enhancement`
- [ ] Test all combinations with dry-run mode

### 5.4 Error Handling Tests
- [ ] Test invalid state values
- [ ] Test invalid label-mode values
- [ ] Test empty label strings
- [ ] Test malformed label input

### 5.5 Performance Tests
- [ ] Test with repositories that have many issues
- [ ] Monitor API rate limiting behavior
- [ ] Test pagination with filtered results
- [ ] Verify memory usage with large result sets

## Phase 6: Documentation and Polish

### 6.1 Update Documentation
- [ ] Update help text with complete examples
- [ ] Add inline code comments for new methods
- [ ] Update any existing documentation files

### 6.2 Code Quality
- [ ] Run linting and fix any issues
- [ ] Add proper error handling for all edge cases
- [ ] Ensure consistent logging levels
- [ ] Add appropriate debug/info logging

### 6.3 Final Integration
- [ ] Test with actual Spring AI repository
- [ ] Verify backward compatibility
- [ ] Test incremental collection with filters
- [ ] Test resume functionality with filters

## Completion Criteria
- [ ] All existing functionality preserved
- [ ] New filtering options work as specified
- [ ] Command line help is accurate and complete
- [ ] Error messages are clear and helpful
- [ ] Performance is acceptable for typical use cases
- [ ] Code passes all quality checks
# CollectGithubIssues.java - Code Structure Reference

**File Length**: 1,515 lines (updated after clean-by-default implementation)  
**Last Updated**: 2025-07-23

> **Important**: Always refer to this file before adding new code to CollectGithubIssues.java. Update this file after making changes.

## File Header (Lines 1-73)
- **Lines 1-9**: JBang shebang and dependencies
- **Lines 10-51**: Package declaration and imports
- **Lines 53-69**: JavaDoc documentation
- **Lines 70-73**: Spring annotations for main class

## Main Application Class: CollectGithubIssues (Lines 73-473)

### Class Declaration and Fields (Lines 73-113)
- **Line 73**: `public class CollectGithubIssues implements CommandLineRunner`
- **Lines 75-81**: Dependency injection fields
- **Lines 95-107**: Configuration fields (original)
  - **Line 106**: `private boolean clean = true;` **UPDATED** - Now defaults to true
- **Lines 109-112**: **NEW** Issue filtering fields (added in Phase 1)
  - `issueState`, `labelFilters`, `labelMode`

### Main Methods (Lines 114-152)
- **Lines 114-117**: `main()` method
- **Lines 121-150**: `run()` method (main entry point)

### Configuration Methods (Lines 154-220)
- **Lines 154-171**: `initializeConfiguration()` - **UPDATED** in Phase 1
- **Lines 173-197**: `testGitHubConnectivity()`
- **Lines 200-220**: `startCollection()`

### Argument Parsing (Lines 222-342)
- **Lines 222-340**: `parseArguments()` - **UPDATED** in Phase 2 & clean-by-default
  - **Lines 279-282**: `--clean` flag (sets clean = true)
  - **Lines 284-287**: **NEW** `--no-clean` and `--append` flags (sets clean = false)
  - **Lines 288-328**: **NEW** State and label filtering arguments
- **Lines 343-350**: `isHelpRequested()`

### Validation Methods (Lines 352-436)
- **Lines 352-375**: `validateEnvironment()`
- **Lines 377-435**: `validateConfiguration()` - **UPDATED** in Phase 2
  - **Lines 416-424**: **NEW** State and label mode validation

### Help Method (Lines 438-490)
- **Lines 438-490**: `showHelp()` - **UPDATED** in Phase 2 & clean-by-default
  - **Lines 443-445**: **NEW** Filtering options in help text
  - **Lines 458-459**: **UPDATED** Clean options help text with new defaults
  - **Lines 485-486**: **NEW** Examples showing --no-clean usage

## Data Models - Records (Lines 474-531)
- **Lines 474-487**: `record Issue(...)`
- **Lines 488-493**: `record Comment(...)`
- **Lines 494-498**: `record Author(...)`
- **Lines 499-504**: `record Label(...)`
- **Lines 505-513**: `record CollectionMetadata(...)`
- **Lines 514-523**: `record CollectionRequest(...)` - **TO UPDATE** in Phase 4
- **Lines 524-531**: `record CollectionResult(...)`

## Configuration Class: GitHubConfig (Lines 532-568)
- **Lines 532-568**: Spring @Configuration class with beans
- **Lines 539-542**: GitHub client bean
- **Lines 544-550**: REST client bean
- **Lines 552-559**: GraphQL client bean
- **Lines 561-566**: ObjectMapper bean

## Service Classes

### GitHubRestService (Lines 569-623)
- **Lines 569-623**: REST API service for basic GitHub operations
- **Lines 584-586**: Rate limit checking
- **Lines 588-590**: Repository access
- **Lines 592-604**: Repository info fetching
- **Lines 606-621**: Total issue count (REST-based)

### GitHubGraphQLService (Lines 631-699)
- **Lines 631-699**: GraphQL API service
- **Lines 641-657**: `executeQuery()` - core GraphQL execution
- **Lines 659-678**: `getTotalIssueCount()` - repository-based count
- **Lines 680-697**: `getSearchIssueCount()` - **COMPLETED** search-based count for filtering

### JsonNodeUtils (Lines 700-749)
- **Lines 700-749**: Utility service for JSON navigation
- **Lines 702-708**: String extraction
- **Lines 710-716**: Integer extraction  
- **Lines 718-728**: DateTime parsing
- **Lines 730-748**: Array handling

### IssueCollectionService (Lines 750-1400)
**Main collection service - all filtering functionality implemented**

#### Constructor and Main Methods (Lines 750-835)
- **Lines 750-784**: Class declaration and constructor
- **Lines 782-834**: `collectIssues()` - **COMPLETED** uses search-based counting

#### Collection Core Logic (Lines 836-947)
- **Lines 836-946**: `collectInBatches()` - **COMPLETED** uses search API integration

#### Utility Methods (Lines 948-996)
- **Lines 948-976**: Retry and backoff logic
- **Lines 978-984**: Rate limit error detection
- **Lines 986-992**: Backoff delay calculation
- **Lines 994-996**: Exception interface

#### Batch Processing (Lines 998-1066)
- **Lines 998-1033**: Adaptive batch creation
- **Lines 1035-1050**: Issue size estimation
- **Lines 1052-1065**: Large issue detection

#### GraphQL Query Building (Lines 1067-1200)
- **Lines 1067-1132**: `buildIssuesQuery()` - repository-based query (legacy)
- **Lines 1134-1200**: `buildSearchIssuesQuery()` - **COMPLETED** search-based query

#### Data Conversion (Lines 1202-1270)
- **Lines 1202-1257**: Issue conversion from JSON
- **Lines 1259-1269**: DateTime parsing utility

#### File Operations (Lines 1271-1356)
- **Lines 1271-1287**: Metadata file creation
- **Lines 1289-1307**: Resume state management
- **Lines 1309-1323**: Resume state loading
- **Lines 1325-1333**: Resume cleanup
- **Lines 1335-1355**: Previous data cleanup

#### Search Integration (Lines 1357-1399)
- **Lines 1357-1399**: **COMPLETED** `buildSearchQuery()` - search query builder with state and label filtering

#### Internal Records (Lines 1401-1444)
- **Lines 1401**: `BatchData` record
- **Lines 1403**: `CollectionStats` record  
- **Lines 1405-1443**: `ResumeState` record

## Configuration Properties: CollectionProperties (Lines 1445-1490)
- **Lines 1445-1490**: Application configuration class with getter/setter methods
- **Configuration fields include:**
  - Default repository, batch settings, rate limiting
  - Large issue thresholds, file paths, logging settings
  - **COMPLETED** Issue filtering defaults: `defaultState`, `defaultLabels`, `defaultLabelMode`

## Implementation Status - ALL PHASES 1-6 COMPLETED ✅

### ✅ Phase 1-4: GitHub Issues Filtering Implementation
1. **Lines 680-697**: `getSearchIssueCount()` method implemented
2. **Lines 1134-1200**: `buildSearchIssuesQuery()` search-based query implemented
3. **Lines 1357-1399**: `buildSearchQuery()` with state and label filtering
4. **Lines 514-523**: `CollectionRequest` record updated with filtering fields
5. **Lines 782-834**: `collectIssues()` updated to use search queries
6. **Lines 836-946**: `collectInBatches()` updated to use search API

### ✅ Phase 5-6: Testing and Documentation
1. ✅ **COMPLETED**: Comprehensive testing of all filtering functionality
2. ✅ **COMPLETED**: Updated documentation and examples
3. ✅ **COMPLETED**: Performance testing and optimization

### ✅ Clean-by-Default Enhancement:
1. **Line 106**: `private boolean clean = true;` - Changed default to true
2. **Lines 284-287**: Added `--no-clean` and `--append` flags
3. **Lines 458-459**: Updated help text to reflect new defaults
4. **Lines 485-486**: Added examples showing --no-clean usage

## Method Dependencies
- `parseArguments()` → sets filtering fields → used by `collectIssues()`
- `buildSearchQuery()` → used by updated collection methods
- `getSearchIssueCount()` → needed for accurate progress reporting
- `CollectionRequest` → needs filtering fields for method signatures

## Integration Points
- **Command line args** → **filtering fields** → **search query** → **GraphQL API** → **results**
- Configuration validation happens before collection starts
- Search queries replace repository-based queries throughout the collection pipeline
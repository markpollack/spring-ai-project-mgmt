# CollectGithubIssues.java - Code Structure Reference

**File Length**: 1,644 lines (current state)  
**Last Updated**: 2025-07-24

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
  - **Line 108**: `private boolean zip = false;` **UPDATED** - Renamed from compress
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
- **Lines 222-340**: `parseArguments()` - **UPDATED** in Phase 2, clean-by-default & zip
  - **Lines 271-274**: **UPDATED** `-z, --zip` flag (renamed from --compress)
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

## Data Models - Records (Lines 500-559)
- **Lines 501-513**: `record Issue(...)` - Core issue data model
- **Lines 515-519**: `record Comment(...)` - Issue comment data
- **Lines 521-524**: `record Author(...)` - User/author information
- **Lines 526-530**: `record Label(...)` - Issue label data
- **Lines 532-539**: `record CollectionMetadata(...)` - Collection run metadata
- **Lines 541-552**: `record CollectionRequest(...)` - Collection parameters with filtering
- **Lines 554-559**: `record CollectionResult(...)` - Collection results summary

## Configuration Class: GitHubConfig (Lines 562-596)
- **Lines 562-596**: Spring @Configuration class with beans
- **Lines 568-571**: GitHub client bean
- **Lines 573-579**: REST client bean  
- **Lines 581-588**: GraphQL client bean
- **Lines 590-596**: ObjectMapper bean with JSR310 time module

## Service Classes

### GitHubRestService (Lines 599-653)
- **Lines 599-653**: REST API service for basic GitHub operations
- **Lines 614-616**: Rate limit checking
- **Lines 618-620**: Repository access
- **Lines 622-634**: Repository info fetching
- **Lines 636-651**: Total issue count (REST-based)

### GitHubGraphQLService (Lines 655-723)
- **Lines 655-723**: GraphQL API service
- **Lines 665-681**: `executeQuery()` - core GraphQL execution
- **Lines 683-702**: `getTotalIssueCount()` - repository-based count
- **Lines 704-721**: `getSearchIssueCount()` - **COMPLETED** search-based count for filtering

### JsonNodeUtils (Lines 724-773)
- **Lines 724-773**: Utility service for JSON navigation
- **Lines 726-732**: String extraction
- **Lines 734-740**: Integer extraction  
- **Lines 742-752**: DateTime parsing
- **Lines 754-772**: Array handling

### IssueCollectionService (Lines 775-1555)
**Main collection service - all filtering functionality implemented**

#### Constructor and Main Methods (Lines 775-860)
- **Lines 775-809**: Class declaration and constructor
- **Lines 807-859**: `collectIssues()` - **COMPLETED** uses search-based counting

#### Collection Core Logic (Lines 861-972)
- **Lines 861-971**: `collectInBatches()` - **COMPLETED** uses search API integration

#### Utility Methods (Lines 973-1021)
- **Lines 973-1001**: Retry and backoff logic
- **Lines 1003-1009**: Rate limit error detection
- **Lines 1011-1017**: Backoff delay calculation
- **Lines 1019-1021**: Exception interface

#### Batch Processing (Lines 1023-1091)
- **Lines 1023-1058**: Adaptive batch creation
- **Lines 1060-1075**: Issue size estimation
- **Lines 1077-1090**: Large issue detection

#### GraphQL Query Building (Lines 1092-1225)
- **Lines 1092-1157**: `buildIssuesQuery()` - repository-based query (legacy)
- **Lines 1159-1225**: `buildSearchIssuesQuery()` - **COMPLETED** search-based query

#### Data Conversion (Lines 1227-1295)
- **Lines 1227-1282**: Issue conversion from JSON
- **Lines 1284-1294**: DateTime parsing utility

#### File Operations (Lines 1296-1470)
- **Lines 1296-1345**: Metadata file creation with zip integration
- **Lines 1347-1384**: **COMPLETED** `createCompressedArchive()` - zip creation functionality
- **Lines 1386-1451**: **COMPLETED** `addCommandLineArgsToZip()` - command line documentation
- **Lines 1453-1458**: Filter suffix building for zip names
- **Lines 1460-1464**: File size formatting utility
- **Lines 1466-1470**: Previous data cleanup

#### Search Integration (Lines 1472-1514)
- **Lines 1472-1514**: **COMPLETED** `buildSearchQuery()` - search query builder with state and label filtering

#### Internal Records (Lines 1555-1565)
- **Lines 1555**: `BatchData` record
- **Lines 1557**: `CollectionStats` record  
- **Lines 1559-1565**: `ResumeState` record

## Configuration Properties: CollectionProperties (Lines 1568-1644)
- **Lines 1568-1644**: Application configuration class with getter/setter methods
- **Configuration fields include:**
  - Default repository, batch settings, rate limiting
  - Large issue thresholds, file paths, logging settings
  - **COMPLETED** Issue filtering defaults: `defaultState`, `defaultLabels`, `defaultLabelMode`

## Implementation Status - ALL PHASES 1-6 COMPLETED ✅

### ✅ Phase 1-4: GitHub Issues Filtering Implementation
1. **Lines 704-721**: `getSearchIssueCount()` method implemented
2. **Lines 1159-1225**: `buildSearchIssuesQuery()` search-based query implemented
3. **Lines 1472-1514**: `buildSearchQuery()` with state and label filtering
4. **Lines 541-552**: `CollectionRequest` record updated with filtering fields
5. **Lines 807-859**: `collectIssues()` updated to use search queries
6. **Lines 861-971**: `collectInBatches()` updated to use search API

### ✅ Phase 5-6: Testing and Documentation
1. ✅ **COMPLETED**: Comprehensive testing of all filtering functionality
2. ✅ **COMPLETED**: Updated documentation and examples
3. ✅ **COMPLETED**: Performance testing and optimization

### ✅ Clean-by-Default Enhancement:
1. **Line 106**: `private boolean clean = true;` - Changed default to true
2. **Lines 284-287**: Added `--no-clean` and `--append` flags
3. **Lines 458-459**: Updated help text to reflect new defaults
4. **Lines 485-486**: Added examples showing --no-clean usage

### ✅ Zip Archive Enhancement:
1. **Line 108**: `private boolean zip = false;` - Renamed from compress
2. **Lines 271-274**: Changed to `-z, --zip` flag (was -c, --compress)
3. **Lines 1347-1384**: Added `createCompressedArchive()` method
4. **Lines 1386-1451**: Added `addCommandLineArgsToZip()` method for command line documentation
5. **Lines 1453-1464**: Added utility methods for zip file naming and formatting
6. **Updated Records**: Changed `compressed` to `zipped` in CollectionMetadata record

## Method Dependencies
- `parseArguments()` → sets filtering fields → used by `collectIssues()`
- `buildSearchQuery()` → used by updated collection methods
- `getSearchIssueCount()` → needed for accurate progress reporting
- `CollectionRequest` → needs filtering fields for method signatures

## Integration Points
- **Command line args** → **filtering fields** → **search query** → **GraphQL API** → **results**
- Configuration validation happens before collection starts
- Search queries replace repository-based queries throughout the collection pipeline
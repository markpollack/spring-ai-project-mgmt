# GitHub Issues Label Filtering - Implementation Plan

## Code Changes Required

### 1. CollectionProperties Updates

Add these fields to the `CollectionProperties` class (around line 1216):

```java
// Issue filtering
private String defaultState = "closed";
private List<String> defaultLabels = new ArrayList<>();
private String defaultLabelMode = "any";

// Getters and setters
public String getDefaultState() { return defaultState; }
public void setDefaultState(String defaultState) { this.defaultState = defaultState; }

public List<String> getDefaultLabels() { return defaultLabels; }
public void setDefaultLabels(List<String> defaultLabels) { this.defaultLabels = defaultLabels; }

public String getDefaultLabelMode() { return defaultLabelMode; }
public void setDefaultLabelMode(String defaultLabelMode) { this.defaultLabelMode = defaultLabelMode; }
```

### 2. Main Class Field Updates

Add these fields to `CollectGithubIssues` class (around line 95):

```java
private String issueState;
private List<String> labelFilters;
private String labelMode;
```

### 3. Configuration Initialization

Update `initializeConfiguration()` method (around line 149):

```java
private void initializeConfiguration() {
    // Existing code...
    
    // New filtering options
    issueState = properties.getDefaultState();
    labelFilters = new ArrayList<>(properties.getDefaultLabels());
    labelMode = properties.getDefaultLabelMode();
    
    logger.debug("Initialized filtering: state={}, labels={}, mode={}", 
                issueState, labelFilters, labelMode);
}
```

### 4. Command Line Argument Parsing

Add these cases to `parseArguments()` method (around line 211):

```java
case "-s", "--state":
    if (i + 1 < args.length) {
        issueState = args[++i].toLowerCase();
        if (!List.of("open", "closed", "all").contains(issueState)) {
            logger.error("Invalid state '{}': must be 'open', 'closed', or 'all'", issueState);
            System.exit(1);
        }
        logger.debug("Parsed issue state: {}", issueState);
    } else {
        logger.error("Missing value for state option");
        System.exit(1);
    }
    break;

case "-l", "--labels":
    if (i + 1 < args.length) {
        String labelStr = args[++i];
        labelFilters = Arrays.stream(labelStr.split(","))
            .map(String::trim)
            .filter(s -> !s.isEmpty())
            .collect(ArrayList::new, ArrayList::add, ArrayList::addAll);
        logger.debug("Parsed labels: {}", labelFilters);
    } else {
        logger.error("Missing value for labels option");
        System.exit(1);
    }
    break;

case "--label-mode":
    if (i + 1 < args.length) {
        labelMode = args[++i].toLowerCase();
        if (!List.of("any", "all").contains(labelMode)) {
            logger.error("Invalid label mode '{}': must be 'any' or 'all'", labelMode);
            System.exit(1);
        }
        logger.debug("Parsed label mode: {}", labelMode);
    } else {
        logger.error("Missing value for label-mode option");
        System.exit(1);
    }
    break;
```

### 5. Help Text Updates

Update `showHelp()` method (around line 375):

```java
System.out.println("    -s, --state <state>     Issue state: open, closed, all (default: " + properties.getDefaultState() + ")");
System.out.println("    -l, --labels <labels>   Comma-separated list of labels to filter by");
System.out.println("    --label-mode <mode>     Label matching mode: any, all (default: " + properties.getDefaultLabelMode() + ")");
```

### 6. Search Query Builder Method

Add new method to `IssueCollectionService` class:

```java
private String buildSearchQuery(String owner, String repo, String state, List<String> labels, String labelMode) {
    StringBuilder query = new StringBuilder();
    
    // Repository and type
    query.append("repo:").append(owner).append("/").append(repo).append(" is:issue");
    
    // State filter
    switch (state.toLowerCase()) {
        case "open":
            query.append(" is:open");
            break;
        case "closed":
            query.append(" is:closed");
            break;
        case "all":
            // No state filter for 'all'
            break;
        default:
            throw new IllegalArgumentException("Invalid state: " + state);
    }
    
    // Label filters
    if (labels != null && !labels.isEmpty()) {
        if ("all".equals(labelMode.toLowerCase())) {
            // All labels must match (AND logic)
            for (String label : labels) {
                query.append(" label:\"").append(label.trim()).append("\"");
            }
        } else {
            // Any label can match (OR logic) - use multiple queries or search syntax
            if (labels.size() == 1) {
                query.append(" label:\"").append(labels.get(0).trim()).append("\"");
            } else {
                // For multiple labels with OR logic, we'll need to handle this in post-processing
                // or make multiple API calls. For now, we'll use the first label and warn.
                logger.warn("Multiple labels with 'any' mode not fully supported in search API. Using first label: {}", labels.get(0));
                query.append(" label:\"").append(labels.get(0).trim()).append("\"");
            }
        }
    }
    
    return query.toString();
}
```

### 7. Update GraphQL Query for Search API

Replace `buildIssuesQuery()` method (around line 981):

```java
private String buildSearchIssuesQuery() {
    return """
        query($query: String!, $first: Int!, $after: String) {
            search(query: $query, type: ISSUE, first: $first, after: $after) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                issueCount
                nodes {
                    ... on Issue {
                        number
                        title
                        body
                        state
                        createdAt
                        updatedAt
                        closedAt
                        url
                        author {
                            login
                            ... on User {
                                name
                            }
                        }
                        assignees(first: 10) {
                            nodes {
                                login
                                ... on User {
                                    name
                                }
                            }
                        }
                        labels(first: 20) {
                            nodes {
                                name
                                color
                                description
                            }
                        }
                        milestone {
                            title
                            number
                            state
                            description
                        }
                        comments(first: 100) {
                            nodes {
                                author {
                                    login
                                    ... on User {
                                        name
                                    }
                                }
                                body
                                createdAt
                                reactions {
                                    totalCount
                                }
                            }
                        }
                    }
                }
            }
        }
        """;
}
```

### 8. Update Collection Logic

Update `collectInBatches()` method (around line 748) to use search query:

```java
// Build search query instead of repository-based query
String searchQuery = buildSearchQuery(owner, repoName, issueState, labelFilters, labelMode);
logger.info("Using search query: {}", searchQuery);

// Build GraphQL query with search
String query = buildSearchIssuesQuery();
Map<String, Object> variables = Map.of(
    "query", searchQuery,
    "first", fetchSize,
    "after", cursor != null ? cursor : ""
);

// Execute query and extract search results
JsonNode result = executeWithRetryAndBackoff(() -> {
    JsonNode response = graphQLService.executeQuery(query, variables);
    
    if (response.has("errors")) {
        throw new RuntimeException("GraphQL errors: " + response.get("errors").toString());
    }
    
    return response;
});

// Extract issues data from search results
JsonNode searchData = result.path("data").path("search");
JsonNode issues = searchData.path("nodes");
JsonNode pageInfo = searchData.path("pageInfo");
```

### 9. Update Total Count Method

Add new method to `GitHubGraphQLService`:

```java
public int getSearchIssueCount(String searchQuery) {
    String query = """
        query($query: String!) {
            search(query: $query, type: ISSUE, first: 1) {
                issueCount
            }
        }
        """;
    
    Object variables = Map.of("query", searchQuery);
    
    JsonNode result = executeQuery(query, variables);
    return result.path("data").path("search").path("issueCount").asInt(0);
}
```

### 10. Update Main Collection Method

Update `collectIssues()` method to use search-based counting:

```java
// Get total issue count using search
String searchQuery = buildSearchQuery(owner, repoName, 
    request.issueState(), request.labelFilters(), request.labelMode());
int totalIssues = graphQLService.getSearchIssueCount(searchQuery);
logger.info("Total issues found with filters: {}", totalIssues);
```

### 11. Update CollectionRequest Record

Update the `CollectionRequest` record (around line 448):

```java
record CollectionRequest(
    String repository,
    int batchSize,
    boolean dryRun,
    boolean incremental,
    boolean compress,
    boolean clean,
    boolean resume,
    String issueState,
    List<String> labelFilters,
    String labelMode
) {}
```

### 12. Update Main Run Method

Update the collection request creation in `run()` method:

```java
CollectionRequest request = new CollectionRequest(
    repo, batchSize, dryRun, incremental, compress, clean, resume,
    issueState, labelFilters, labelMode
);
```

## Testing Commands

```bash
# Test open issues with design label
./CollectGithubIssues.java --repo spring-projects/spring-ai --state open --labels design --dry-run

# Test closed issues with multiple labels
./CollectGithubIssues.java --repo spring-projects/spring-ai --state closed --labels bug,enhancement --label-mode any --dry-run

# Test all issues with specific label
./CollectGithubIssues.java --repo spring-projects/spring-ai --state all --labels priority:high --dry-run
```

## Error Handling

Add validation in `validateConfiguration()` method:

```java
// Validate issue state
if (!List.of("open", "closed", "all").contains(issueState.toLowerCase())) {
    errors.add("Invalid issue state: " + issueState + " (must be 'open', 'closed', or 'all')");
}

// Validate label mode
if (!List.of("any", "all").contains(labelMode.toLowerCase())) {
    errors.add("Invalid label mode: " + labelMode + " (must be 'any' or 'all')");
}
```

## Performance Considerations

- Search API has different rate limits (30 requests per minute for authenticated requests)
- Search results are limited to 1000 issues per query
- For large result sets, may need time-based pagination
- Consider adding progress indicators for long-running searches
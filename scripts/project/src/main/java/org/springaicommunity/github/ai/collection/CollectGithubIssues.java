///usr/bin/env jbang "$0" "$@" ; exit $?

//DEPS org.springframework.boot:spring-boot-starter:3.2.0
//DEPS org.springframework.boot:spring-boot-starter-web:3.2.0
//DEPS org.springframework.boot:spring-boot-configuration-processor:3.2.0
//DEPS org.kohsuke:github-api:1.317
//DEPS com.fasterxml.jackson.core:jackson-databind:2.15.2
//DEPS com.fasterxml.jackson.datatype:jackson-datatype-jsr310:2.15.2

package org.springaicommunity.github.ai.collection;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.kohsuke.github.GitHub;
import org.kohsuke.github.GitHubBuilder;
import org.kohsuke.github.GHRepository;
import org.kohsuke.github.GHRateLimit;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Arrays;

import static org.springaicommunity.github.ai.collection.DataModels.*;
import java.util.Optional;
import java.util.Map;
import java.util.ArrayList;
import java.util.Iterator;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.format.DateTimeFormatter;
import java.time.ZonedDateTime;
import java.util.zip.ZipOutputStream;
import java.util.zip.ZipEntry;
import java.io.FileOutputStream;
import java.io.ByteArrayOutputStream;
import java.util.stream.Stream;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * GitHub Issues Collection Tool
 * 
 * JBang Spring Boot application to collect GitHub issues from a repository
 * using GraphQL and REST APIs. This is a port of the bash script collect_github_issues.sh
 * 
 * Usage:
 *   ./collect_github_issues.java [OPTIONS]
 * 
 * Environment Variables:
 *   GITHUB_TOKEN - GitHub personal access token for authentication
 * 
 * Examples:
 *   ./collect_github_issues.java --repo spring-projects/spring-ai
 *   ./collect_github_issues.java --batch-size 50 --incremental
 *   ./collect_github_issues.java --dry-run --verbose
 */
@SpringBootApplication
@EnableConfigurationProperties(CollectionProperties.class)
public class CollectGithubIssues implements CommandLineRunner {
    
    private static final Logger logger = LoggerFactory.getLogger(CollectGithubIssues.class);
    
    private final GitHubGraphQLService graphQLService;
    private final GitHubRestService restService;
    private final IssueCollectionService collectionService;
    private final CollectionProperties properties;
    private final JsonNodeUtils jsonUtils;
    
    public CollectGithubIssues(GitHubGraphQLService graphQLService, 
                              GitHubRestService restService,
                              IssueCollectionService collectionService,
                              CollectionProperties properties,
                              JsonNodeUtils jsonUtils) {
        this.graphQLService = graphQLService;
        this.restService = restService;
        this.collectionService = collectionService;
        this.properties = properties;
        this.jsonUtils = jsonUtils;
    }
    
    // Configuration fields
    private String repo;
    private int batchSize;
    private int maxRetries;
    private int retryDelay;
    private int largeIssueThreshold;
    private int sizeThreshold;
    private boolean dryRun = false;
    private boolean incremental = false;
    private boolean zip = false;
    private boolean verbose = false;
    private boolean clean = true;
    private boolean resume = false;
    
    // Issue filtering fields
    private String issueState = "closed";
    private List<String> labelFilters = new ArrayList<>();
    private String labelMode = "any";
    
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(CollectGithubIssues.class);
        app.setWebApplicationType(WebApplicationType.NONE);
        app.run(args);
    }
    
    @Override
    public void run(String... args) throws Exception {
        logger.info("Starting GitHub Issues Collection Tool");
        
        // Initialize configuration from properties
        initializeConfiguration();
        
        // Parse and validate command line arguments using ArgumentParser
        ArgumentParser argumentParser = new ArgumentParser(properties);
        
        // Check for help request first
        if (argumentParser.isHelpRequested(args)) {
            System.out.println(argumentParser.generateHelpText());
            return;
        }
        
        // Parse and validate arguments
        ArgumentParser.ParsedConfiguration config = argumentParser.parseAndValidate(args);
        argumentParser.validateEnvironment();
        
        // Apply parsed configuration to instance variables
        applyParsedConfiguration(config);
        
        logger.info("Configuration:");
        logger.info("  Repository: {}", repo);
        logger.info("  Batch Size: {}", batchSize);
        logger.info("  Dry Run: {}", dryRun);
        logger.info("  Incremental: {}", incremental);
        logger.info("  Zip: {}", zip);
        
        // Test GitHub API connectivity
        testGitHubConnectivity();
        
        // Start collection
        startCollection();
    }
    
    private void initializeConfiguration() {
        // Initialize from configuration properties
        repo = properties.getDefaultRepository();
        batchSize = properties.getBatchSize();
        maxRetries = properties.getMaxRetries();
        retryDelay = properties.getRetryDelay();
        largeIssueThreshold = properties.getLargeIssueThreshold();
        sizeThreshold = properties.getSizeThreshold();
        verbose = properties.isVerbose();
        
        // Initialize filtering options
        issueState = properties.getDefaultState();
        labelFilters = new ArrayList<>(properties.getDefaultLabels());
        labelMode = properties.getDefaultLabelMode();
        
        logger.debug("Initialized configuration from properties: repo={}, batchSize={}", repo, batchSize);
        logger.debug("Initialized filtering: state={}, labels={}, mode={}", issueState, labelFilters, labelMode);
    }
    
    private void testGitHubConnectivity() {
        try {
            logger.info("Testing GitHub API connectivity...");
            
            // Test Hub4j GitHub API
            String githubToken = System.getenv("GITHUB_TOKEN");
            GitHub github = new GitHubBuilder().withOAuthToken(githubToken).build();
            
            // Test rate limit (simple connectivity test)
            GHRateLimit rateLimit = github.getRateLimit();
            logger.info("GitHub API Rate Limit - Remaining: {}/{}", rateLimit.getRemaining(), rateLimit.getLimit());
            
            // Test repository access
            String[] repoParts = repo.split("/");
            GHRepository repository = github.getRepository(repo);
            logger.info("Repository access successful: {} ({})", repository.getFullName(), repository.getDescription());
            
            logger.info("GitHub API connectivity test passed");
        } catch (Exception e) {
            logger.error("GitHub API connectivity test failed: {}", e.getMessage());
            if (verbose) {
                logger.error("Stack trace:", e);
            }
            System.exit(1);
        }
    }
    
    private void startCollection() {
        try {
            CollectionRequest request = new CollectionRequest(
                repo, batchSize, dryRun, incremental, zip, clean, resume,
                issueState, labelFilters, labelMode
            );
            
            CollectionResult result = collectionService.collectIssues(request);
            
            logger.info("Collection completed successfully");
            logger.info("Total issues found: {}", result.totalIssues());
            logger.info("Issues processed: {}", result.processedIssues());
            logger.info("Output directory: {}", result.outputDirectory());
            
        } catch (Exception e) {
            logger.error("Collection failed: {}", e.getMessage());
            if (verbose) {
                logger.error("Stack trace:", e);
            }
            System.exit(1);
        }
    }
    
    private void applyParsedConfiguration(ArgumentParser.ParsedConfiguration config) {
        this.repo = config.repository;
        this.batchSize = config.batchSize;
        this.dryRun = config.dryRun;
        this.incremental = config.incremental;
        this.zip = config.zip;
        this.verbose = config.verbose;
        this.clean = config.clean;
        this.resume = config.resume;
        this.issueState = config.issueState;
        this.labelFilters = config.labelFilters;
        this.labelMode = config.labelMode;
        
        // Enable debug logging if verbose is set
        if (verbose) {
            System.setProperty("logging.level.com.github.issues", "DEBUG");
        }
    }
}

// Main collection service
@Service
class IssueCollectionService {
    
    private static final Logger logger = LoggerFactory.getLogger(IssueCollectionService.class);
    
    private final GitHubGraphQLService graphQLService;
    private final GitHubRestService restService;
    private final JsonNodeUtils jsonUtils;
    private final ObjectMapper objectMapper;
    private final CollectionProperties properties;
    
    // Configuration constants (will be initialized from properties)
    private final int MAX_BATCH_SIZE_BYTES;
    private final int LARGE_ISSUE_THRESHOLD;
    private final int SIZE_THRESHOLD;
    private final String RESUME_FILE;
    
    public IssueCollectionService(GitHubGraphQLService graphQLService,
                                 GitHubRestService restService,
                                 JsonNodeUtils jsonUtils,
                                 ObjectMapper objectMapper,
                                 CollectionProperties properties) {
        this.graphQLService = graphQLService;
        this.restService = restService;
        this.jsonUtils = jsonUtils;
        this.objectMapper = objectMapper;
        this.properties = properties;
        
        // Initialize configuration constants from properties
        this.MAX_BATCH_SIZE_BYTES = properties.getMaxBatchSizeBytes();
        this.LARGE_ISSUE_THRESHOLD = properties.getLargeIssueThreshold();
        this.SIZE_THRESHOLD = properties.getSizeThreshold();
        this.RESUME_FILE = properties.getResumeFile();
    }
    
    public CollectionResult collectIssues(CollectionRequest request) throws Exception {
        String[] repoParts = request.repository().split("/");
        String owner = repoParts[0];
        String repoName = repoParts[1];
        
        // Get total issue count using search query
        String searchQuery = buildSearchQuery(owner, repoName, 
            request.issueState(), request.labelFilters(), request.labelMode());
        int totalIssues = graphQLService.getSearchIssueCount(searchQuery);
        logger.info("Total issues found with filters: {}", totalIssues);
        logger.info("Search query: {}", searchQuery);
        
        if (request.dryRun()) {
            logger.info("DRY RUN: Would collect {} issues in batches of {}", totalIssues, request.batchSize());
            return new CollectionResult(totalIssues, 0, "dry-run", List.of());
        }
        
        // Setup output directory
        String timestamp = ZonedDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd_HH-mm-ss"));
        String outputDir = "issues/raw/closed/batch_" + timestamp;
        Path outputPath = Paths.get(outputDir);
        Files.createDirectories(outputPath);
        
        logger.info("Output directory: {}", outputDir);
        
        // Handle cleanup if requested
        if (request.clean()) {
            logger.info("Cleaning up previous collection data");
            cleanupPreviousData(outputPath);
        }
        
        // Handle incremental collection
        if (request.incremental()) {
            logger.info("Incremental mode enabled - will skip previously collected issues");
            // The resume state handling in collectInBatches will take care of this
        }
        
        // Collect issues in batches with error handling
        CollectionStats stats;
        try {
            stats = collectInBatches(owner, repoName, request.batchSize(), outputPath, timestamp, searchQuery);
        } catch (Exception e) {
            logger.error("Collection failed: {}", e.getMessage());
            // Save resume state on error so we can restart
            saveResumeState(outputPath, null, 1, 0, List.of());
            throw e;
        }
        
        // Create metadata file
        createMetadataFile(outputPath, request, totalIssues, stats.processedIssues());
        
        return new CollectionResult(totalIssues, stats.processedIssues(), outputDir, stats.batchFiles());
    }
    
    private CollectionStats collectInBatches(String owner, String repoName, int targetBatchSize, Path outputPath, String timestamp, String searchQuery) throws Exception {
        long startTime = System.currentTimeMillis();
        List<String> batchFiles = new ArrayList<>();
        String cursor = null;
        int batchNum = 1;
        boolean hasMoreFromAPI = true;
        AtomicInteger processedCount = new AtomicInteger(0);
        
        // Check for resume state
        ResumeState resumeState = loadResumeState(outputPath);
        if (resumeState != null) {
            cursor = resumeState.cursor();
            batchNum = resumeState.batchNumber();
            processedCount.set(resumeState.processedIssues());
            batchFiles.addAll(resumeState.completedBatches());
            logger.info("Resuming from batch {}, cursor: {}, processed: {}", 
                       batchNum, cursor != null ? "present" : "null", processedCount.get());
        }
        
        // Use a larger fetch size for efficiency, but batch adaptively
        int fetchSize = Math.max(targetBatchSize, 100);
        List<Issue> pendingIssues = new ArrayList<>();
        
        while (hasMoreFromAPI || !pendingIssues.isEmpty()) {
            // Fetch more issues if needed
            if (pendingIssues.size() < targetBatchSize && hasMoreFromAPI) {
                logger.info("Fetching issues from API (cursor: {})", cursor != null ? "present" : "null");
                
                // Build GraphQL search query with pagination
                String query = buildSearchIssuesQuery();
                Map<String, Object> variables = Map.of(
                    "query", searchQuery,
                    "first", fetchSize,
                    "after", cursor != null ? cursor : ""
                );
                
                // Execute GraphQL query with retry and backoff
                JsonNode result = executeWithRetryAndBackoff(() -> {
                    JsonNode response = graphQLService.executeQuery(query, variables);
                    
                    // Check for errors
                    if (response.has("errors")) {
                        throw new RuntimeException("GraphQL errors: " + response.get("errors").toString());
                    }
                    
                    return response;
                });
                
                // Extract issues data from search results
                JsonNode searchData = result.path("data").path("search");
                JsonNode issues = searchData.path("nodes");
                JsonNode pageInfo = searchData.path("pageInfo");
                
                // Convert to Issue records and add to pending
                for (JsonNode issueNode : issues) {
                    Issue issue = convertToIssue(issueNode);
                    if (issue != null) {
                        pendingIssues.add(issue);
                    }
                }
                
                // Update pagination
                hasMoreFromAPI = pageInfo.path("hasNextPage").asBoolean(false);
                cursor = pageInfo.path("endCursor").asText(null);
                
                logger.info("Fetched {} issues, {} pending", issues.size(), pendingIssues.size());
            }
            
            // Create adaptive batch
            List<Issue> currentBatch = createAdaptiveBatch(pendingIssues, targetBatchSize);
            
            if (currentBatch.isEmpty()) {
                break; // No more issues to process
            }
            
            // Save batch to file
            String batchFile = String.format("issues_batch_%03d.json", batchNum);
            Path batchPath = outputPath.resolve(batchFile);
            
            BatchData batchData = new BatchData(batchNum, currentBatch, timestamp);
            objectMapper.writeValue(batchPath.toFile(), batchData);
            
            batchFiles.add(batchFile);
            processedCount.addAndGet(currentBatch.size());
            
            // Log batch info with progress statistics
            long batchSizeBytes = batchPath.toFile().length();
            long elapsedTime = System.currentTimeMillis() - startTime;
            double currentRate = processedCount.get() / (elapsedTime / 1000.0);
            logger.info("Saved batch {} with {} issues ({} bytes) to {} | Total: {} issues, Rate: {:.2f} issues/sec", 
                       batchNum, currentBatch.size(), batchSizeBytes, batchFile, 
                       processedCount.get(), currentRate);
            
            // Save resume state after each batch
            saveResumeState(outputPath, cursor, batchNum + 1, processedCount.get(), batchFiles);
            
            batchNum++;
        }
        
        // Log final statistics
        long totalTime = System.currentTimeMillis() - startTime;
        double avgIssuesPerSecond = processedCount.get() / (totalTime / 1000.0);
        logger.info("Collection completed: {} issues processed in {} batches", processedCount.get(), batchFiles.size());
        logger.info("Total time: {} seconds, Average rate: {:.2f} issues/second", 
                   totalTime / 1000.0, avgIssuesPerSecond);
        
        // Clean up resume state on successful completion
        cleanupResumeState(outputPath);
        
        return new CollectionStats(batchFiles, processedCount.get());
    }
    
    private <T> T executeWithRetryAndBackoff(SupplierWithException<T> operation) throws Exception {
        int maxRetries = properties.getMaxRetries();
        int baseDelay = properties.getRetryDelay();
        
        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return operation.get();
            } catch (Exception e) {
                if (attempt == maxRetries) {
                    logger.error("Max retries ({}) exceeded. Final error: {}", maxRetries, e.getMessage());
                    throw e;
                }
                
                // Check if it's a rate limit error
                if (isRateLimitError(e)) {
                    int delaySeconds = calculateBackoffDelay(attempt, baseDelay);
                    logger.warn("Rate limit hit on attempt {}/{}. Backing off for {} seconds...", 
                               attempt, maxRetries, delaySeconds);
                    Thread.sleep(delaySeconds * 1000L);
                } else {
                    logger.warn("Error on attempt {}/{}: {}. Retrying in {} seconds...", 
                               attempt, maxRetries, e.getMessage(), baseDelay);
                    Thread.sleep(baseDelay * 1000L);
                }
            }
        }
        
        throw new RuntimeException("Should not reach here");
    }
    
    private boolean isRateLimitError(Exception e) {
        String message = e.getMessage().toLowerCase();
        return message.contains("rate limit") || 
               message.contains("rate_limit") || 
               message.contains("too many requests") ||
               message.contains("403");
    }
    
    private int calculateBackoffDelay(int attempt, int baseDelay) {
        // Exponential backoff with jitter: baseDelay * 2^(attempt-1) + random(0, baseDelay)
        int exponentialDelay = baseDelay * (int) Math.pow(2, attempt - 1);
        int jitter = (int) (Math.random() * baseDelay);
        return Math.min(exponentialDelay + jitter, 300); // Cap at 5 minutes
    }
    
    @FunctionalInterface
    private interface SupplierWithException<T> {
        T get() throws Exception;
    }
    
    private List<Issue> createAdaptiveBatch(List<Issue> pendingIssues, int targetBatchSize) throws Exception {
        if (pendingIssues.isEmpty()) {
            return new ArrayList<>();
        }
        
        List<Issue> currentBatch = new ArrayList<>();
        int currentBatchSizeBytes = 0;
        int maxBatchSizeBytes = MAX_BATCH_SIZE_BYTES;
        
        Iterator<Issue> iterator = pendingIssues.iterator();
        while (iterator.hasNext() && currentBatch.size() < targetBatchSize) {
            Issue issue = iterator.next();
            int issueSize = estimateIssueSize(issue);
            
            // Check if adding this issue would exceed size limit
            if (currentBatchSizeBytes + issueSize > maxBatchSizeBytes && !currentBatch.isEmpty()) {
                logger.info("Batch size limit reached ({} bytes), finalizing batch with {} issues", 
                           currentBatchSizeBytes, currentBatch.size());
                break;
            }
            
            // Add issue to current batch
            currentBatch.add(issue);
            currentBatchSizeBytes += issueSize;
            iterator.remove();
            
            // Check if this is a large issue
            if (isLargeIssue(issue)) {
                logger.info("Large issue detected #{} ({} comments, {} bytes), finalizing batch early", 
                           issue.number(), issue.comments().size(), issueSize);
                break;
            }
        }
        
        return currentBatch;
    }
    
    private int estimateIssueSize(Issue issue) {
        try {
            // Quick estimate based on content length
            int titleSize = issue.title() != null ? issue.title().length() : 0;
            int bodySize = issue.body() != null ? issue.body().length() : 0;
            int commentsSize = issue.comments().stream()
                .mapToInt(comment -> comment.body() != null ? comment.body().length() : 0)
                .sum();
            
            // Add overhead for JSON structure (rough estimate)
            return (titleSize + bodySize + commentsSize) * 2; // 2x for JSON overhead
        } catch (Exception e) {
            logger.warn("Failed to estimate size for issue #{}: {}", issue.number(), e.getMessage());
            return 1024; // Default estimate
        }
    }
    
    private boolean isLargeIssue(Issue issue) {
        int commentCount = issue.comments().size();
        int estimatedSize = estimateIssueSize(issue);
        
        boolean isLarge = commentCount > LARGE_ISSUE_THRESHOLD || 
                         estimatedSize > SIZE_THRESHOLD;
        
        if (isLarge) {
            logger.debug("Large issue detected #{}: {} comments, ~{} bytes", 
                        issue.number(), commentCount, estimatedSize);
        }
        
        return isLarge;
    }
    
    private String buildIssuesQuery() {
        return """
            query($owner: String!, $repo: String!, $first: Int!, $after: String, $states: [IssueState!]!) {
                repository(owner: $owner, name: $repo) {
                    issues(first: $first, after: $after, states: $states, orderBy: {field: CREATED_AT, direction: DESC}) {
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                        nodes {
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
    
    // GraphQL query for search-based issue collection with filtering
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
    
    private Issue convertToIssue(JsonNode issueNode) {
        try {
            int number = issueNode.path("number").asInt();
            String title = issueNode.path("title").asText();
            String body = issueNode.path("body").asText();
            String state = issueNode.path("state").asText();
            String url = issueNode.path("url").asText();
            
            LocalDateTime createdAt = parseDateTime(issueNode.path("createdAt").asText());
            LocalDateTime updatedAt = parseDateTime(issueNode.path("updatedAt").asText());
            LocalDateTime closedAt = parseDateTime(issueNode.path("closedAt").asText());
            
            // Parse author
            JsonNode authorNode = issueNode.path("author");
            Author author = new Author(
                authorNode.path("login").asText(),
                authorNode.path("name").asText("")
            );
            
            // Parse comments
            List<Comment> comments = new ArrayList<>();
            JsonNode commentsNodes = issueNode.path("comments").path("nodes");
            for (JsonNode commentNode : commentsNodes) {
                JsonNode commentAuthorNode = commentNode.path("author");
                Author commentAuthor = new Author(
                    commentAuthorNode.path("login").asText(),
                    commentAuthorNode.path("name").asText("")
                );
                
                LocalDateTime commentCreatedAt = parseDateTime(commentNode.path("createdAt").asText());
                
                comments.add(new Comment(
                    commentAuthor,
                    commentNode.path("body").asText(),
                    commentCreatedAt
                ));
            }
            
            // Parse labels
            List<Label> labels = new ArrayList<>();
            JsonNode labelsNodes = issueNode.path("labels").path("nodes");
            for (JsonNode labelNode : labelsNodes) {
                labels.add(new Label(
                    labelNode.path("name").asText(),
                    labelNode.path("color").asText(),
                    labelNode.path("description").asText("")
                ));
            }
            
            return new Issue(number, title, body, state, createdAt, updatedAt, closedAt, url, author, comments, labels);
            
        } catch (Exception e) {
            logger.error("Failed to convert issue: {}", e.getMessage());
            return null;
        }
    }
    
    private LocalDateTime parseDateTime(String dateTimeStr) {
        if (dateTimeStr == null || dateTimeStr.isEmpty() || "null".equals(dateTimeStr)) {
            return null;
        }
        try {
            return ZonedDateTime.parse(dateTimeStr).toLocalDateTime();
        } catch (Exception e) {
            logger.warn("Failed to parse datetime: {}", dateTimeStr);
            return null;
        }
    }
    
    private void createMetadataFile(Path outputPath, CollectionRequest request, int totalIssues, int processedIssues) throws Exception {
        String timestamp = ZonedDateTime.now().format(DateTimeFormatter.ISO_INSTANT);
        
        CollectionMetadata metadata = new CollectionMetadata(
            timestamp,
            request.repository(),
            totalIssues,
            processedIssues,
            request.batchSize(),
            request.zip()
        );
        
        Path metadataPath = outputPath.resolve("metadata.json");
        objectMapper.writeValue(metadataPath.toFile(), metadata);
        
        logger.info("Created metadata file: {}", metadataPath);
        
        // Create compressed archive if compression is enabled
        if (request.zip()) {
            createCompressedArchive(outputPath, request);
        }
    }
    
    private void createCompressedArchive(Path outputPath, CollectionRequest request) throws Exception {
        // Create compressed output directory
        Path compressedDir = Paths.get("issues-compressed");
        Files.createDirectories(compressedDir);
        
        // Generate zip filename with timestamp and filters
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd_HH-mm-ss"));
        String repoName = request.repository().replace("/", "-");
        String filters = buildFilterSuffix(request);
        String zipFileName = String.format("%s_%s_%s%s.zip", repoName, request.issueState(), timestamp, filters);
        Path zipPath = compressedDir.resolve(zipFileName);
        
        logger.info("Creating compressed archive: {}", zipPath);
        
        try (ZipOutputStream zipOut = new ZipOutputStream(new FileOutputStream(zipPath.toFile()))) {
            // Add command line arguments file
            addCommandLineArgsToZip(zipOut, request);
            
            // Add all batch files to zip
            try (Stream<Path> paths = Files.walk(outputPath)) {
                paths.filter(Files::isRegularFile)
                     .filter(path -> path.getFileName().toString().endsWith(".json"))
                     .forEach(path -> {
                         try {
                             String entryName = path.getFileName().toString();
                             ZipEntry zipEntry = new ZipEntry(entryName);
                             zipOut.putNextEntry(zipEntry);
                             Files.copy(path, zipOut);
                             zipOut.closeEntry();
                         } catch (Exception e) {
                             logger.error("Failed to add {} to zip: {}", path, e.getMessage());
                         }
                     });
            }
        }
        
        logger.info("Compressed archive created: {} ({})", zipPath, formatFileSize(Files.size(zipPath)));
    }
    
    private void addCommandLineArgsToZip(ZipOutputStream zipOut, CollectionRequest request) throws Exception {
        // Create command line arguments documentation
        StringBuilder argsContent = new StringBuilder();
        argsContent.append("# GitHub Issues Collection - Command Line Arguments\n");
        argsContent.append("# Generated: ").append(LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)).append("\n\n");
        
        argsContent.append("## Original Command\n");
        argsContent.append("```bash\n");
        argsContent.append("jbang CollectGithubIssues.java");
        
        // Add repository
        argsContent.append(" --repo ").append(request.repository());
        
        // Add state filter
        if (!"closed".equals(request.issueState())) {
            argsContent.append(" --state ").append(request.issueState());
        }
        
        // Add label filters
        if (request.labelFilters() != null && !request.labelFilters().isEmpty()) {
            argsContent.append(" --labels ").append(String.join(",", request.labelFilters()));
            if (!"any".equals(request.labelMode())) {
                argsContent.append(" --label-mode ").append(request.labelMode());
            }
        }
        
        // Add batch size if not default
        if (request.batchSize() != 100) {
            argsContent.append(" --batch-size ").append(request.batchSize());
        }
        
        // Add flags
        if (request.dryRun()) argsContent.append(" --dry-run");
        if (request.incremental()) argsContent.append(" --incremental");
        if (request.zip()) argsContent.append(" --zip");
        if (!request.clean()) argsContent.append(" --no-clean");
        if (request.resume()) argsContent.append(" --resume");
        
        argsContent.append("\n```\n\n");
        
        // Add detailed parameters
        argsContent.append("## Collection Parameters\n");
        argsContent.append("- **Repository**: ").append(request.repository()).append("\n");
        argsContent.append("- **Issue State**: ").append(request.issueState()).append("\n");
        argsContent.append("- **Batch Size**: ").append(request.batchSize()).append("\n");
        argsContent.append("- **Dry Run**: ").append(request.dryRun()).append("\n");
        argsContent.append("- **Incremental**: ").append(request.incremental()).append("\n");
        argsContent.append("- **Create Zip**: ").append(request.zip()).append("\n");
        argsContent.append("- **Clean**: ").append(request.clean()).append("\n");
        argsContent.append("- **Resume**: ").append(request.resume()).append("\n");
        
        if (request.labelFilters() != null && !request.labelFilters().isEmpty()) {
            argsContent.append("- **Label Filters**: ").append(String.join(", ", request.labelFilters())).append("\n");
            argsContent.append("- **Label Mode**: ").append(request.labelMode()).append("\n");
        }
        
        argsContent.append("\n## Usage Notes\n");
        argsContent.append("This zip archive contains all issues and metadata collected using the above parameters.\n");
        argsContent.append("To reproduce this collection, run the command shown above.\n");
        
        // Add to zip
        ZipEntry argsEntry = new ZipEntry("collection-info.md");
        zipOut.putNextEntry(argsEntry);
        zipOut.write(argsContent.toString().getBytes());
        zipOut.closeEntry();
    }
    
    private String buildFilterSuffix(CollectionRequest request) {
        StringBuilder suffix = new StringBuilder();
        if (request.labelFilters() != null && !request.labelFilters().isEmpty()) {
            suffix.append("_labels-").append(String.join("-", request.labelFilters()));
        }
        return suffix.toString().replaceAll("[^a-zA-Z0-9_-]", "");
    }
    
    private String formatFileSize(long bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return String.format("%.1f KB", bytes / 1024.0);
        return String.format("%.1f MB", bytes / (1024.0 * 1024.0));
    }
    
    private void saveResumeState(Path outputPath, String cursor, int batchNumber, int processedIssues, List<String> completedBatches) {
        if (cursor == null) return; // Don't save if we're done
        
        try {
            ResumeState state = new ResumeState(
                cursor,
                batchNumber,
                processedIssues,
                ZonedDateTime.now().format(DateTimeFormatter.ISO_INSTANT),
                new ArrayList<>(completedBatches)
            );
            
            Path resumePath = outputPath.resolve(RESUME_FILE);
            objectMapper.writeValue(resumePath.toFile(), state);
            logger.debug("Saved resume state: batch {}, processed {}", batchNumber, processedIssues);
        } catch (Exception e) {
            logger.warn("Failed to save resume state: {}", e.getMessage());
        }
    }
    
    private ResumeState loadResumeState(Path outputPath) {
        try {
            Path resumePath = outputPath.resolve(RESUME_FILE);
            if (!Files.exists(resumePath)) {
                return null;
            }
            
            ResumeState state = objectMapper.readValue(resumePath.toFile(), ResumeState.class);
            logger.info("Loaded resume state: batch {}, processed {}", state.batchNumber(), state.processedIssues());
            return state;
        } catch (Exception e) {
            logger.warn("Failed to load resume state: {}", e.getMessage());
            return null;
        }
    }
    
    private void cleanupResumeState(Path outputPath) {
        try {
            Path resumePath = outputPath.resolve(RESUME_FILE);
            Files.deleteIfExists(resumePath);
            logger.debug("Cleaned up resume state file");
        } catch (Exception e) {
            logger.warn("Failed to cleanup resume state: {}", e.getMessage());
        }
    }
    
    private void cleanupPreviousData(Path outputPath) {
        try {
            if (Files.exists(outputPath)) {
                // Delete all files in the output directory
                try (Stream<Path> paths = Files.walk(outputPath)) {
                    paths.filter(Files::isRegularFile)
                         .forEach(path -> {
                             try {
                                 Files.delete(path);
                                 logger.debug("Deleted: {}", path);
                             } catch (Exception e) {
                                 logger.warn("Failed to delete {}: {}", path, e.getMessage());
                             }
                         });
                }
                logger.info("Cleaned up previous collection data in {}", outputPath);
            }
        } catch (Exception e) {
            logger.warn("Failed to cleanup previous data: {}", e.getMessage());
        }
    }
    
    // Build GitHub search query with state and label filtering
    private String buildSearchQuery(String owner, String repo, String state, List<String> labels, String labelMode) {
        StringBuilder query = new StringBuilder();
        
        // Repository and type
        query.append("repo:").append(owner).append("/").append(repo).append(" is:issue");
        
        // State filter (open/closed/all)
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
        
        // Label filters with AND/OR logic
        if (labels != null && !labels.isEmpty()) {
            if ("all".equals(labelMode.toLowerCase())) {
                // All labels must match (AND logic) - multiple label: terms
                for (String label : labels) {
                    query.append(" label:\"").append(label.trim()).append("\"");
                }
            } else {
                // Any label can match (OR logic) - GitHub Search API limitation
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
    
}


///usr/bin/env jbang "$0" "$@" ; exit $?

//DEPS org.springframework.boot:spring-boot-starter:3.2.0
//DEPS org.springframework.boot:spring-boot-starter-web:3.2.0
//DEPS org.springframework.boot:spring-boot-configuration-processor:3.2.0
//DEPS org.kohsuke:github-api:1.317
//DEPS com.fasterxml.jackson.core:jackson-databind:2.15.2
//DEPS com.fasterxml.jackson.datatype:jackson-datatype-jsr310:2.15.2

package com.github.issues;

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
@EnableAutoConfiguration
@ComponentScan(basePackages = "com.github.issues")
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
    private boolean compress = false;
    private boolean verbose = false;
    private boolean clean = false;
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
        
        // Parse command line arguments (can override config)
        parseArguments(args);
        
        // Show help if requested
        if (isHelpRequested(args)) {
            showHelp();
            return;
        }
        
        // Validate environment and configuration
        validateEnvironment();
        validateConfiguration();
        
        logger.info("Configuration:");
        logger.info("  Repository: {}", repo);
        logger.info("  Batch Size: {}", batchSize);
        logger.info("  Dry Run: {}", dryRun);
        logger.info("  Incremental: {}", incremental);
        logger.info("  Compress: {}", compress);
        
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
                repo, batchSize, dryRun, incremental, compress, clean, resume,
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
    
    private void parseArguments(String... args) {
        for (int i = 0; i < args.length; i++) {
            String arg = args[i];
            
            switch (arg) {
                case "-r", "--repo":
                    if (i + 1 < args.length) {
                        repo = args[++i];
                        logger.debug("Parsed repository: {}", repo);
                    } else {
                        logger.error("Missing value for repository option");
                        System.exit(1);
                    }
                    break;
                    
                case "-b", "--batch-size":
                    if (i + 1 < args.length) {
                        try {
                            batchSize = Integer.parseInt(args[++i]);
                            logger.info("Parsed batch size from arguments: {}", batchSize);
                            if (batchSize <= 0) {
                                logger.error("Batch size must be positive: {}", batchSize);
                                System.exit(1);
                            }
                        } catch (NumberFormatException e) {
                            logger.error("Invalid batch size '{}': must be a positive integer", args[i]);
                            System.exit(1);
                        }
                    } else {
                        logger.error("Missing value for batch-size option");
                        System.exit(1);
                    }
                    break;
                    
                case "-d", "--dry-run":
                    dryRun = true;
                    logger.debug("Dry run enabled");
                    break;
                    
                case "-i", "--incremental":
                    incremental = true;
                    logger.debug("Incremental mode enabled");
                    break;
                    
                case "-c", "--compress":
                    compress = true;
                    logger.debug("Compression enabled");
                    break;
                    
                case "-v", "--verbose":
                    verbose = true;
                    logger.debug("Verbose logging enabled");
                    // Enable debug logging
                    System.setProperty("logging.level.com.github.issues", "DEBUG");
                    break;
                    
                case "--clean":
                    clean = true;
                    logger.debug("Clean mode enabled");
                    break;
                    
                case "--resume":
                    resume = true;
                    logger.debug("Resume mode enabled");
                    break;
                    
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
                    
                case "-h", "--help":
                    // Help is handled separately
                    break;
                    
                default:
                    if (arg.startsWith("-")) {
                        logger.warn("Unknown option: {}", arg);
                    }
                    break;
            }
        }
    }
    
    private boolean isHelpRequested(String... args) {
        for (String arg : args) {
            if ("-h".equals(arg) || "--help".equals(arg)) {
                return true;
            }
        }
        return false;
    }
    
    private void validateEnvironment() {
        // Check for GitHub token
        String githubToken = System.getenv("GITHUB_TOKEN");
        if (githubToken == null || githubToken.trim().isEmpty()) {
            logger.error("GITHUB_TOKEN environment variable is required");
            logger.error("Please set your GitHub personal access token:");
            logger.error("  export GITHUB_TOKEN=your_token_here");
            System.exit(1);
        }
        
        // Validate batch size
        if (batchSize < 1 || batchSize > 1000) {
            logger.error("Invalid batch size: {} (must be 1-1000)", batchSize);
            System.exit(1);
        }
        
        // Validate repository format
        if (!repo.contains("/") || repo.split("/").length != 2) {
            logger.error("Invalid repository format: {} (expected: owner/repo)", repo);
            System.exit(1);
        }
        
        logger.info("Environment validation passed");
    }
    
    private void validateConfiguration() {
        List<String> errors = new ArrayList<>();
        
        // Validate repository format
        if (repo == null || repo.trim().isEmpty()) {
            errors.add("Repository cannot be empty");
        } else if (!repo.matches("^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$")) {
            errors.add("Repository must be in format 'owner/repo' (e.g., 'spring-projects/spring-ai')");
        }
        
        // Validate batch size
        if (batchSize <= 0) {
            errors.add("Batch size must be positive (got: " + batchSize + ")");
        } else if (batchSize > 1000) {
            errors.add("Batch size too large (got: " + batchSize + ", max: 1000)");
        }
        
        // Validate retry settings
        if (maxRetries < 0) {
            errors.add("Max retries must be non-negative (got: " + maxRetries + ")");
        } else if (maxRetries > 10) {
            errors.add("Max retries too large (got: " + maxRetries + ", max: 10)");
        }
        
        if (retryDelay <= 0) {
            errors.add("Retry delay must be positive (got: " + retryDelay + ")");
        } else if (retryDelay > 60) {
            errors.add("Retry delay too large (got: " + retryDelay + " seconds, max: 60 seconds)");
        }
        
        // Validate large issue thresholds
        if (largeIssueThreshold <= 0) {
            errors.add("Large issue threshold must be positive (got: " + largeIssueThreshold + ")");
        }
        
        if (sizeThreshold <= 0) {
            errors.add("Size threshold must be positive (got: " + sizeThreshold + ")");
        }
        
        // Validate issue state
        if (!List.of("open", "closed", "all").contains(issueState.toLowerCase())) {
            errors.add("Invalid issue state: " + issueState + " (must be 'open', 'closed', or 'all')");
        }
        
        // Validate label mode
        if (!List.of("any", "all").contains(labelMode.toLowerCase())) {
            errors.add("Invalid label mode: " + labelMode + " (must be 'any' or 'all')");
        }
        
        // Report validation errors
        if (!errors.isEmpty()) {
            logger.error("Configuration validation failed:");
            for (String error : errors) {
                logger.error("  - {}", error);
            }
            System.exit(1);
        }
        
        logger.info("Configuration validation passed");
    }
    
    private void showHelp() {
        System.out.println("Usage: collect_github_issues.java [OPTIONS]");
        System.out.println();
        System.out.println("Collect GitHub issues from a repository with advanced filtering capabilities.");
        System.out.println();
        System.out.println("OPTIONS:");
        System.out.println("    -h, --help              Show this help message");
        System.out.println("    -r, --repo REPO         Repository in format owner/repo (default: " + properties.getDefaultRepository() + ")");
        System.out.println("    -b, --batch-size SIZE   Issues per batch file (default: " + properties.getBatchSize() + ")");
        System.out.println("    -d, --dry-run          Show what would be collected without doing it");
        System.out.println("    -i, --incremental      Skip already collected issues");
        System.out.println("    -c, --compress         Compress output files");
        System.out.println("    -v, --verbose          Enable verbose logging");
        System.out.println("    --clean                Clean up previous collection data before starting");
        System.out.println("    --resume               Resume from last successful batch");
        System.out.println();
        System.out.println("FILTERING OPTIONS:");
        System.out.println("    -s, --state <state>     Issue state: open, closed, all (default: " + properties.getDefaultState() + ")");
        System.out.println("    -l, --labels <labels>   Comma-separated list of labels to filter by");
        System.out.println("    --label-mode <mode>     Label matching mode: any, all (default: " + properties.getDefaultLabelMode() + ")");
        System.out.println("                           Note: 'any' mode uses first label only due to API limitations");
        System.out.println();
        System.out.println("CONFIGURATION:");
        System.out.println("    Configuration can be customized via application.yaml file");
        System.out.println("    All settings under 'github.issues' prefix can be overridden");
        System.out.println("    Command-line arguments take precedence over configuration file");
        System.out.println();
        System.out.println("ENVIRONMENT VARIABLES:");
        System.out.println("    GITHUB_TOKEN           GitHub personal access token (required)");
        System.out.println();
        System.out.println("EXAMPLES:");
        System.out.println("    # Basic usage");
        System.out.println("    ./collect_github_issues.java --repo spring-projects/spring-ai");
        System.out.println();
        System.out.println("    # State filtering");
        System.out.println("    ./collect_github_issues.java --state open --dry-run");
        System.out.println("    ./collect_github_issues.java --state all --batch-size 50");
        System.out.println();
        System.out.println("    # Label filtering");
        System.out.println("    ./collect_github_issues.java --labels bug --clean");
        System.out.println("    ./collect_github_issues.java --labels \"bug,priority:high\" --label-mode all");
        System.out.println();
        System.out.println("    # Combined filtering");
        System.out.println("    ./collect_github_issues.java --state open --labels bug --verbose");
        System.out.println("    ./collect_github_issues.java --state closed --labels documentation,enhancement");
        System.out.println();
    }
}

// Core domain records for type safety
record Issue(
    int number,
    String title,
    String body,
    String state,
    LocalDateTime createdAt,
    LocalDateTime updatedAt,
    LocalDateTime closedAt,
    String url,
    Author author,
    List<Comment> comments,
    List<Label> labels
) {}

record Comment(
    Author author,
    String body,
    LocalDateTime createdAt
) {}

record Author(
    String login,
    String name
) {}

record Label(
    String name,
    String color,
    String description
) {}

record CollectionMetadata(
    String timestamp,
    String repository,
    int totalIssues,
    int processedIssues,
    int batchSize,
    boolean compressed
) {}

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

record CollectionResult(
    int totalIssues,
    int processedIssues,
    String outputDirectory,
    List<String> batchFiles
) {}

// Configuration for GitHub API clients
@Configuration
class GitHubConfig {
    
    @Value("${GITHUB_TOKEN}")
    private String githubToken;
    
    @Bean
    public GitHub gitHub() throws IOException {
        return new GitHubBuilder().withOAuthToken(githubToken).build();
    }
    
    @Bean
    public RestClient restClient() {
        return RestClient.builder()
            .defaultHeader("Authorization", "token " + githubToken)
            .defaultHeader("Accept", "application/vnd.github.v3+json")
            .build();
    }
    
    @Bean
    public RestClient graphQLClient() {
        return RestClient.builder()
            .baseUrl("https://api.github.com/graphql")
            .defaultHeader("Authorization", "Bearer " + githubToken)
            .defaultHeader("Content-Type", "application/json")
            .build();
    }
    
    @Bean
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new com.fasterxml.jackson.datatype.jsr310.JavaTimeModule());
        return mapper;
    }
}

// Service for GitHub REST API operations
@Service
class GitHubRestService {
    
    private static final Logger logger = LoggerFactory.getLogger(GitHubRestService.class);
    
    private final GitHub gitHub;
    private final RestClient restClient;
    private final ObjectMapper objectMapper;
    
    public GitHubRestService(GitHub gitHub, RestClient restClient, ObjectMapper objectMapper) {
        this.gitHub = gitHub;
        this.restClient = restClient;
        this.objectMapper = objectMapper;
    }
    
    public GHRateLimit getRateLimit() throws IOException {
        return gitHub.getRateLimit();
    }
    
    public GHRepository getRepository(String repoName) throws IOException {
        return gitHub.getRepository(repoName);
    }
    
    public JsonNode getRepositoryInfo(String owner, String repo) {
        String response = restClient.get()
            .uri("https://api.github.com/repos/{owner}/{repo}", owner, repo)
            .retrieve()
            .body(String.class);
        
        try {
            return objectMapper.readTree(response);
        } catch (Exception e) {
            logger.error("Failed to parse repository info: {}", e.getMessage());
            return objectMapper.createObjectNode();
        }
    }
    
    public int getTotalIssueCount(String owner, String repo, String state) {
        try {
            String query = String.format("repo:%s/%s is:issue is:%s", owner, repo, state);
            String response = restClient.get()
                .uri("https://api.github.com/search/issues?q={query}", query)
                .retrieve()
                .body(String.class);
            
            JsonNode searchResult = objectMapper.readTree(response);
            return searchResult.path("total_count").asInt(0);
        } catch (Exception e) {
            logger.error("Failed to get total issue count: {}", e.getMessage());
            return 0;
        }
    }
}

// Service for GitHub GraphQL operations
@Service
class GitHubGraphQLService {
    
    private static final Logger logger = LoggerFactory.getLogger(GitHubGraphQLService.class);
    
    private final RestClient graphQLClient;
    private final ObjectMapper objectMapper;
    
    public GitHubGraphQLService(RestClient graphQLClient, ObjectMapper objectMapper) {
        this.graphQLClient = graphQLClient;
        this.objectMapper = objectMapper;
    }
    
    public JsonNode executeQuery(String query, Object variables) {
        try {
            String requestBody = objectMapper.writeValueAsString(
                Map.of("query", query, "variables", variables != null ? variables : Map.of())
            );
            
            String response = graphQLClient.post()
                .body(requestBody)
                .retrieve()
                .body(String.class);
            
            return objectMapper.readTree(response);
        } catch (Exception e) {
            logger.error("GraphQL query failed: {}", e.getMessage());
            return objectMapper.createObjectNode();
        }
    }
    
    public int getTotalIssueCount(String owner, String repo, String state) {
        String query = """
            query($owner: String!, $repo: String!, $states: [IssueState!]!) {
                repository(owner: $owner, name: $repo) {
                    issues(states: $states) {
                        totalCount
                    }
                }
            }
            """;
        
        Object variables = Map.of(
            "owner", owner,
            "repo", repo,
            "states", List.of(state.toUpperCase())
        );
        
        JsonNode result = executeQuery(query, variables);
        return result.path("data").path("repository").path("issues").path("totalCount").asInt(0);
    }
    
    // Get issue count using GitHub Search API for filtered queries
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
}

// Utility service for JsonNode navigation
@Service
class JsonNodeUtils {
    
    private static final Logger logger = LoggerFactory.getLogger(JsonNodeUtils.class);
    
    public Optional<String> getString(JsonNode node, String... path) {
        JsonNode target = node;
        for (String p : path) {
            target = target.path(p);
        }
        return target.isMissingNode() ? Optional.empty() : Optional.of(target.asText());
    }
    
    public Optional<Integer> getInt(JsonNode node, String... path) {
        JsonNode target = node;
        for (String p : path) {
            target = target.path(p);
        }
        return target.isMissingNode() ? Optional.empty() : Optional.of(target.asInt());
    }
    
    public Optional<LocalDateTime> getDateTime(JsonNode node, String... path) {
        return getString(node, path)
            .map(str -> {
                try {
                    return LocalDateTime.parse(str.replace("Z", ""));
                } catch (Exception e) {
                    logger.warn("Failed to parse datetime: {}", str);
                    return null;
                }
            });
    }
    
    public List<JsonNode> getArray(JsonNode node, String... path) {
        JsonNode target = node;
        for (String p : path) {
            target = target.path(p);
        }
        
        if (target.isArray()) {
            List<JsonNode> result = new ArrayList<>();
            target.forEach(result::add);
            return result;
        }
        
        return List.of();
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
            request.compress()
        );
        
        Path metadataPath = outputPath.resolve("metadata.json");
        objectMapper.writeValue(metadataPath.toFile(), metadata);
        
        logger.info("Created metadata file: {}", metadataPath);
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
    
    private record BatchData(int batchNumber, List<Issue> issues, String timestamp) {}
    
    private record CollectionStats(List<String> batchFiles, int processedIssues) {}
    
    private record ResumeState(
        String cursor,
        int batchNumber,
        int processedIssues,
        String timestamp,
        List<String> completedBatches
    ) {}
}

@ConfigurationProperties(prefix = "github.issues")
class CollectionProperties {
    
    // Repository settings
    private String defaultRepository = "spring-projects/spring-ai";
    
    // Batch configuration
    private int batchSize = 100;
    private int maxBatchSizeBytes = 1048576; // 1MB
    
    // Rate limiting
    private int maxRetries = 3;
    private int retryDelay = 5;
    private int rateLimit = 5000; // requests per hour
    
    // Large issue detection
    private int largeIssueThreshold = 50; // comments
    private int sizeThreshold = 102400; // 100KB
    
    // File paths
    private String baseOutputDir = "issues/raw/closed";
    private String resumeFile = ".resume_state.json";
    
    // Logging
    private boolean verbose = false;
    private boolean debug = false;
    
    // Issue filtering defaults
    private String defaultState = "closed";
    private List<String> defaultLabels = new ArrayList<>();
    private String defaultLabelMode = "any";
    
    // Getters and setters
    public String getDefaultRepository() { return defaultRepository; }
    public void setDefaultRepository(String defaultRepository) { this.defaultRepository = defaultRepository; }
    
    public int getBatchSize() { return batchSize; }
    public void setBatchSize(int batchSize) { this.batchSize = batchSize; }
    
    public int getMaxBatchSizeBytes() { return maxBatchSizeBytes; }
    public void setMaxBatchSizeBytes(int maxBatchSizeBytes) { this.maxBatchSizeBytes = maxBatchSizeBytes; }
    
    public int getMaxRetries() { return maxRetries; }
    public void setMaxRetries(int maxRetries) { this.maxRetries = maxRetries; }
    
    public int getRetryDelay() { return retryDelay; }
    public void setRetryDelay(int retryDelay) { this.retryDelay = retryDelay; }
    
    public int getRateLimit() { return rateLimit; }
    public void setRateLimit(int rateLimit) { this.rateLimit = rateLimit; }
    
    public int getLargeIssueThreshold() { return largeIssueThreshold; }
    public void setLargeIssueThreshold(int largeIssueThreshold) { this.largeIssueThreshold = largeIssueThreshold; }
    
    public int getSizeThreshold() { return sizeThreshold; }
    public void setSizeThreshold(int sizeThreshold) { this.sizeThreshold = sizeThreshold; }
    
    public String getBaseOutputDir() { return baseOutputDir; }
    public void setBaseOutputDir(String baseOutputDir) { this.baseOutputDir = baseOutputDir; }
    
    public String getResumeFile() { return resumeFile; }
    public void setResumeFile(String resumeFile) { this.resumeFile = resumeFile; }
    
    public boolean isVerbose() { return verbose; }
    public void setVerbose(boolean verbose) { this.verbose = verbose; }
    
    public boolean isDebug() { return debug; }
    public void setDebug(boolean debug) { this.debug = debug; }
    
    public String getDefaultState() { return defaultState; }
    public void setDefaultState(String defaultState) { this.defaultState = defaultState; }
    
    public List<String> getDefaultLabels() { return defaultLabels; }
    public void setDefaultLabels(List<String> defaultLabels) { this.defaultLabels = defaultLabels; }
    
    public String getDefaultLabelMode() { return defaultLabelMode; }
    public void setDefaultLabelMode(String defaultLabelMode) { this.defaultLabelMode = defaultLabelMode; }
}
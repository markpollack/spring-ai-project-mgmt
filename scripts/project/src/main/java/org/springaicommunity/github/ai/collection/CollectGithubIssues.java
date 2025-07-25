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
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


import java.util.List;
import java.util.ArrayList;

import static org.springaicommunity.github.ai.collection.DataModels.*;

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
            
            // Use injected GitHub service for connectivity test
            String searchQuery = restService.buildSearchQuery(
                repo.split("/")[0], repo.split("/")[1], 
                issueState, labelFilters, labelMode);
            
            int issueCount = graphQLService.getSearchIssueCount(searchQuery);
            logger.info("GitHub API connectivity test passed - found {} issues", issueCount);
            
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



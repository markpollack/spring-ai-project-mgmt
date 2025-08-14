package org.springaicommunity.github.ai.collection.app;

import org.springaicommunity.github.ai.collection.*;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.ComponentScan;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.ArrayList;

/**
 * GitHub Issues Collection CLI Application
 * 
 * Spring Boot command-line application to collect GitHub issues from a repository
 * using GraphQL and REST APIs with library components.
 * 
 * Usage:
 *   java -jar collection-app.jar [OPTIONS]
 * 
 * Environment Variables:
 *   GITHUB_TOKEN - GitHub personal access token for authentication
 * 
 * Examples:
 *   java -jar collection-app.jar --repo spring-projects/spring-ai
 *   java -jar collection-app.jar --batch-size 50 --incremental
 *   java -jar collection-app.jar --dry-run --verbose
 */
@SpringBootApplication
@EnableConfigurationProperties(CollectionProperties.class)
@ComponentScan(basePackages = {
    "org.springaicommunity.github.ai.collection",
    "org.springaicommunity.github.ai.collection.app"
})
public class CollectGithubIssuesApp implements CommandLineRunner {
    
    private static final Logger logger = LoggerFactory.getLogger(CollectGithubIssuesApp.class);
    
    private final GitHubGraphQLService graphQLService;
    private final GitHubRestService restService;
    private final IssueCollectionService collectionService;
    private final ArgumentParser argumentParser;
    
    // Collection configuration - will be set from parsed arguments
    private String repo;
    private int batchSize;
    private boolean dryRun = false;
    private boolean incremental = false;
    private boolean zip = false;
    private boolean verbose = false;
    private boolean clean = true;
    private boolean resume = false;
    private String issueState;
    private List<String> labelFilters = new ArrayList<>();
    private String labelMode;
    
    public CollectGithubIssuesApp(
            GitHubGraphQLService graphQLService,
            GitHubRestService restService,
            IssueCollectionService collectionService,
            ArgumentParser argumentParser) {
        this.graphQLService = graphQLService;
        this.restService = restService;
        this.collectionService = collectionService;
        this.argumentParser = argumentParser;
    }
    
    public static void main(String[] args) {
        // Configure Spring Boot to run as console application
        SpringApplication app = new SpringApplication(CollectGithubIssuesApp.class);
        app.setWebApplicationType(WebApplicationType.NONE);
        app.run(args);
    }
    
    @Override
    public void run(String... args) throws Exception {
        // Check for help request first
        if (argumentParser.isHelpRequested(args)) {
            System.out.println(argumentParser.generateHelpText());
            return;
        }
        
        // Parse and validate arguments
        ParsedConfiguration config = argumentParser.parseAndValidate(args);
        argumentParser.validateEnvironment();
        
        // Apply parsed configuration to instance variables
        applyParsedConfiguration(config);
        
        logger.info("Configuration:");
        logger.info("  Repository: {}", repo);
        logger.info("  Batch size: {}", batchSize);
        logger.info("  Dry run: {}", dryRun);
        logger.info("  Incremental: {}", incremental);
        logger.info("  Zip: {}", zip);
        logger.info("  Verbose: {}", verbose);
        logger.info("  Clean: {}", clean);
        logger.info("  Resume: {}", resume);
        logger.info("  Issue state: {}", issueState);
        logger.info("  Label filters: {}", labelFilters);
        logger.info("  Label mode: {}", labelMode);
        
        try {
            // Create collection request
            CollectionRequest request = new CollectionRequest(
                repo, batchSize, dryRun, incremental, zip, clean, resume,
                issueState, labelFilters, labelMode
            );
            
            // Execute collection
            CollectionResult result = collectionService.collectIssues(request);
            
            // Log results
            logger.info("Collection completed successfully!");
            logger.info("Total issues: {}", result.totalIssues());
            logger.info("Processed issues: {}", result.processedIssues());
            logger.info("Output directory: {}", result.outputDirectory());
            logger.info("Batch files created: {}", result.batchFiles().size());
            
            if (verbose && !result.batchFiles().isEmpty()) {
                logger.info("Batch files:");
                for (String batchFile : result.batchFiles()) {
                    logger.info("  - {}", batchFile);
                }
            }
            
        } catch (Exception e) {
            logger.error("Collection failed: {}", e.getMessage());
            if (verbose) {
                logger.error("Stack trace:", e);
            }
            System.exit(1);
        }
    }
    
    private void applyParsedConfiguration(ParsedConfiguration config) {
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
    }
}
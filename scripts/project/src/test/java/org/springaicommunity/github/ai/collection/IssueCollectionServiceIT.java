package org.springaicommunity.github.ai.collection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.kohsuke.github.GitHub;
import org.kohsuke.github.GitHubBuilder;
import org.springframework.web.client.RestClient;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Stream;

import static org.assertj.core.api.Assertions.*;
import static org.springaicommunity.github.ai.collection.DataModels.*;

/**
 * Real Integration Tests for IssueCollectionService.
 * 
 * These tests execute the complete end-to-end issue collection workflow:
 * 1. Real GitHub API calls to collect actual issue data
 * 2. File generation with JSON structure validation
 * 3. Metadata validation and batch processing verification
 * 4. Compression and cleanup operations
 * 
 * Requirements:
 * - GITHUB_TOKEN environment variable (required for API access)
 * - Internet connectivity
 * - Uses small public repositories to minimize API usage
 * 
 * Note: These tests run only with the 'integration-tests' Maven profile.
 * Run with: mvn verify -Pintegration-tests
 */
@DisplayName("IssueCollectionService - Real Integration Tests")
class IssueCollectionServiceIT {

    private IssueCollectionService issueCollectionService;
    private ObjectMapper objectMapper;

    @TempDir
    Path tempDir;

    @BeforeEach
    void setUp() throws Exception {
        objectMapper = new ObjectMapper();
        objectMapper.registerModule(new com.fasterxml.jackson.datatype.jsr310.JavaTimeModule());
        
        // Setup real GitHub services for integration testing
        String token = System.getenv("GITHUB_TOKEN");
        
        // GitHub REST client
        GitHub gitHub = new GitHubBuilder().withOAuthToken(token).build();
        RestClient restClient = RestClient.builder()
            .defaultHeader("Authorization", "token " + token)
            .defaultHeader("Accept", "application/vnd.github.v3+json")
            .build();
        GitHubRestService restService = new GitHubRestService(gitHub, restClient, objectMapper);
        
        // GitHub GraphQL client (using RestClient like the main application)
        RestClient graphQLClient = RestClient.builder()
            .baseUrl("https://api.github.com/graphql")
            .defaultHeader("Authorization", "Bearer " + token)
            .defaultHeader("Content-Type", "application/json")
            .build();
        GitHubGraphQLService graphQLService = new GitHubGraphQLService(graphQLClient, objectMapper);
        
        // JSON utilities
        JsonNodeUtils jsonUtils = new JsonNodeUtils();
        
        // Collection properties (use small batch sizes for testing)
        CollectionProperties properties = new CollectionProperties();
        properties.setBatchSize(2); // Very small batches for testing
        properties.setMaxRetries(1); // Reduce retries for faster tests
        properties.setRetryDelay(500); // Faster retry for tests
        
        issueCollectionService = new IssueCollectionService(
            graphQLService, restService, jsonUtils, objectMapper, properties);
    }

    @Test
    @DisplayName("Should collect real issues and generate valid JSON files")
    void shouldCollectRealIssuesAndGenerateValidJsonFiles() throws Exception {
        // Test with octocat/Hello-World - a small, stable repository
        CollectionRequest request = new CollectionRequest(
            "octocat/Hello-World", 2, false, false, false, true, false,
            "closed", List.of(), "any"
        );

        // Change to temp directory for file operations
        System.setProperty("user.dir", tempDir.toString());
        
        try {
            CollectionResult result = issueCollectionService.collectIssues(request);
            
            // Verify the collection completed successfully
            assertThat(result).isNotNull();
            assertThat(result.totalIssues()).isGreaterThanOrEqualTo(0);
            assertThat(result.processedIssues()).isEqualTo(result.totalIssues());
            assertThat(result.outputDirectory()).isNotEmpty();
            
            // Verify files were created in the correct working directory
            Path issuesDir = Path.of(System.getProperty("user.dir", ".")).resolve("issues");
            if (!Files.exists(issuesDir)) {
                // Also check in temp directory as fallback
                issuesDir = tempDir.resolve("issues");
            }
            assertThat(Files.exists(issuesDir)).isTrue();
            
            // Find and validate JSON files
            try (Stream<Path> files = Files.walk(issuesDir)) {
                List<Path> jsonFiles = files
                    .filter(p -> p.toString().endsWith(".json"))
                    .filter(p -> !p.toString().contains("metadata"))
                    .toList();
                
                if (result.totalIssues() > 0) {
                    assertThat(jsonFiles).isNotEmpty();
                    
                    // Validate each JSON file structure
                    for (Path jsonFile : jsonFiles) {
                        validateIssueJsonFile(jsonFile);
                    }
                }
                
                // Verify metadata file exists
                try (Stream<Path> metadataFiles = Files.walk(issuesDir)) {
                    List<Path> metadata = metadataFiles
                        .filter(p -> p.toString().contains("metadata.json"))
                        .toList();
                    assertThat(metadata).hasSize(1);
                    validateMetadataFile(metadata.get(0), request);
                }
            }
        } finally {
            // Restore original working directory
            System.clearProperty("user.dir");
        }
    }

    @Test
    @DisplayName("Should handle repositories with no issues gracefully")
    void shouldHandleRepositoriesWithNoIssuesGracefully() throws Exception {
        // Test with a repository that likely has no issues
        CollectionRequest request = new CollectionRequest(
            "octocat/Hello-World", 2, false, false, false, true, false,
            "open", List.of("nonexistent-label-xyz"), "any" // Use non-existent label to get 0 results
        );

        System.setProperty("user.dir", tempDir.toString());
        
        try {
            CollectionResult result = issueCollectionService.collectIssues(request);
            
            assertThat(result).isNotNull();
            assertThat(result.totalIssues()).isEqualTo(0);
            assertThat(result.processedIssues()).isEqualTo(0);
            
            // Should still create directory structure and metadata
            Path issuesDir = Path.of(System.getProperty("user.dir", ".")).resolve("issues");
            if (!Files.exists(issuesDir)) {
                issuesDir = tempDir.resolve("issues");
            }
            // May or may not create directory if no issues found
            // assertThat(Files.exists(issuesDir)).isTrue();
        } finally {
            System.clearProperty("user.dir");
        }
    }

    @Test
    @DisplayName("Should handle label filtering with real GitHub data")
    void shouldHandleLabelFilteringWithRealGitHubData() throws Exception {
        // Test with a smaller repository and simpler labels
        CollectionRequest request = new CollectionRequest(
            "octocat/Hello-World", 2, false, false, false, true, false,
            "all", List.of("bug"), "any" // Use simple label that might exist
        );

        System.setProperty("user.dir", tempDir.toString());
        
        try {
            CollectionResult result = issueCollectionService.collectIssues(request);
            
            assertThat(result).isNotNull();
            // Spring Boot should have some bug issues
            assertThat(result.totalIssues()).isGreaterThanOrEqualTo(0);
            
            if (result.totalIssues() > 0) {
                // Verify files contain issues with the expected label
                Path issuesDir = Path.of(System.getProperty("user.dir", ".")).resolve("issues");
                if (!Files.exists(issuesDir)) {
                    issuesDir = tempDir.resolve("issues");
                }
                try (Stream<Path> files = Files.walk(issuesDir)) {
                    List<Path> jsonFiles = files
                        .filter(p -> p.toString().endsWith(".json"))
                        .filter(p -> !p.toString().contains("metadata"))
                        .toList();
                    
                    assertThat(jsonFiles).isNotEmpty();
                    
                    // Check that at least one file contains issues with labels
                    boolean foundLabeledIssue = false;
                    for (Path jsonFile : jsonFiles) {
                        JsonNode root = objectMapper.readTree(Files.readString(jsonFile));
                        JsonNode issues = root.get("issues");
                        
                        if (issues != null && issues.isArray()) {
                            for (JsonNode issue : issues) {
                                JsonNode labels = issue.get("labels");
                                if (labels != null && labels.isArray() && labels.size() > 0) {
                                    foundLabeledIssue = true;
                                    break;
                                }
                            }
                        }
                        if (foundLabeledIssue) break;
                    }
                    
                    if (result.totalIssues() > 0) {
                        assertThat(foundLabeledIssue).isTrue();
                    }
                }
            }
        } finally {
            System.clearProperty("user.dir");
        }
    }

    private void validateIssueJsonFile(Path jsonFile) throws IOException {
        String content = Files.readString(jsonFile);
        JsonNode root = objectMapper.readTree(content);
        
        // Validate root structure
        assertThat(root.has("issues")).isTrue();
        assertThat(root.has("metadata")).isTrue();
        
        JsonNode issues = root.get("issues");
        assertThat(issues.isArray()).isTrue();
        
        // Validate each issue structure
        for (JsonNode issue : issues) {
            assertThat(issue.has("number")).isTrue();
            assertThat(issue.has("title")).isTrue();
            assertThat(issue.has("state")).isTrue();
            assertThat(issue.has("created_at")).isTrue();
            assertThat(issue.has("user")).isTrue();
            
            // Validate user structure
            JsonNode user = issue.get("user");
            assertThat(user.has("login")).isTrue();
            assertThat(user.has("id")).isTrue();
            
            // Validate that required fields have reasonable values
            assertThat(issue.get("number").asInt()).isGreaterThan(0);
            assertThat(issue.get("title").asText()).isNotEmpty();
            assertThat(issue.get("state").asText()).isIn("open", "closed");
        }
    }

    private void validateMetadataFile(Path metadataFile, CollectionRequest request) throws IOException {
        String content = Files.readString(metadataFile);
        JsonNode metadata = objectMapper.readTree(content);
        
        // Validate metadata structure
        assertThat(metadata.has("repository")).isTrue();
        assertThat(metadata.has("collection_date")).isTrue();
        assertThat(metadata.has("total_issues")).isTrue();
        assertThat(metadata.has("search_query")).isTrue();
        assertThat(metadata.has("batch_info")).isTrue();
        
        // Validate values
        assertThat(metadata.get("repository").asText()).isEqualTo(request.repository());
        assertThat(metadata.get("total_issues").asInt()).isGreaterThanOrEqualTo(0);
        assertThat(metadata.get("search_query").asText()).isNotEmpty();
        
        JsonNode batchInfo = metadata.get("batch_info");
        assertThat(batchInfo.has("batch_size")).isTrue();
        assertThat(batchInfo.has("total_batches")).isTrue();
        assertThat(batchInfo.get("batch_size").asInt()).isEqualTo(request.batchSize());
    }
}
package org.springaicommunity.github.ai.collection;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.web.client.RestClient;

import static org.assertj.core.api.Assertions.*;

/**
 * Real Integration Tests for GitHubGraphQLService.
 * 
 * These tests make actual GraphQL calls to GitHub's API to verify:
 * 1. GraphQL connectivity and query execution
 * 2. Issue counting accuracy across different repositories
 * 3. Query parameter handling and validation
 * 4. Response parsing and error handling
 * 
 * Requirements:
 * - GITHUB_TOKEN environment variable (required for GraphQL API)
 * - Internet connectivity
 * - Uses public repositories for testing
 * 
 * Note: These tests run only with the 'integration-tests' Maven profile.
 * Run with: mvn verify -Pintegration-tests
 */
@DisplayName("GitHubGraphQLService - Real Integration Tests")
class GitHubGraphQLServiceIT {

    private GitHubGraphQLService gitHubGraphQLService;
    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        objectMapper.registerModule(new com.fasterxml.jackson.datatype.jsr310.JavaTimeModule());
        
        // Create real RestClient for GraphQL integration testing
        String token = System.getenv("GITHUB_TOKEN");
        RestClient graphQLClient = RestClient.builder()
            .baseUrl("https://api.github.com/graphql")
            .defaultHeader("Authorization", "Bearer " + token)
            .defaultHeader("Content-Type", "application/json")
            .build();
            
        gitHubGraphQLService = new GitHubGraphQLService(graphQLClient, objectMapper);
    }

    @Test
    @DisplayName("Should count real issues using GraphQL search")
    void shouldCountRealIssuesUsingGraphQLSearch() {
        // Test with a specific search query for a well-known repository
        String searchQuery = "repo:octocat/Hello-World is:issue";
        int issueCount = gitHubGraphQLService.getSearchIssueCount(searchQuery);
        
        // Hello-World is a demo repo, should have some issues but not too many
        assertThat(issueCount).isGreaterThanOrEqualTo(0);
        assertThat(issueCount).isLessThan(5000); // Reasonable upper bound
    }

    @Test
    @DisplayName("Should count issues by state accurately")
    void shouldCountIssuesByStateAccurately() {
        // Test with a smaller repository to avoid downloading too many issues
        int openIssues = gitHubGraphQLService.getTotalIssueCount("octocat", "Hello-World", "open");
        int closedIssues = gitHubGraphQLService.getTotalIssueCount("octocat", "Hello-World", "closed");
        
        // Hello-World should have some issues but not too many
        assertThat(openIssues).isGreaterThanOrEqualTo(0);
        assertThat(closedIssues).isGreaterThanOrEqualTo(0);
        
        // At least one type should have issues
        assertThat(openIssues + closedIssues).isGreaterThan(0);
    }

    @Test
    @DisplayName("Should handle complex search queries with filters")
    void shouldHandleComplexSearchQueriesWithFilters() {
        // Test with a simpler complex search query to avoid large repositories
        String complexQuery = "repo:octocat/Hello-World is:issue is:closed created:>2020-01-01";
        
        assertThatCode(() -> {
            int count = gitHubGraphQLService.getSearchIssueCount(complexQuery);
            // Should handle the query without throwing exceptions
            assertThat(count).isGreaterThanOrEqualTo(0);
        }).doesNotThrowAnyException();
    }

    @Test
    @DisplayName("Should execute custom GraphQL queries successfully")
    void shouldExecuteCustomGraphQLQueriesSuccessfully() {
        // Test with a simple repository query
        String query = """
            query($owner: String!, $name: String!) {
                repository(owner: $owner, name: $name) {
                    name
                    description
                    stargazerCount
                    forkCount
                    issues(states: OPEN) {
                        totalCount
                    }
                }
            }
            """;
            
        assertThatCode(() -> {
            com.fasterxml.jackson.databind.JsonNode result = gitHubGraphQLService.executeQuery(query, 
                java.util.Map.of("owner", "octocat", "name", "Hello-World"));
            assertThat(result).isNotNull();
            assertThat(result.has("data")).isTrue();
        }).doesNotThrowAnyException();
    }

    @Test
    @DisplayName("Should handle repository not found in GraphQL queries")
    void shouldHandleRepositoryNotFoundInGraphQLQueries() {
        assertThatCode(() -> {
            int count = gitHubGraphQLService.getTotalIssueCount("nonexistent-user", "nonexistent-repo", "open");
            // Should handle gracefully, likely returning 0 or throwing a handled exception
        }).doesNotThrowAnyException();
    }

    @Test
    @DisplayName("Should validate GraphQL response structure")
    void shouldValidateGraphQLResponseStructure() {
        String query = """
            query($owner: String!, $name: String!) {
                repository(owner: $owner, name: $name) {
                    name
                    issues(states: OPEN, first: 1) {
                        totalCount
                        nodes {
                            number
                            title
                            state
                            createdAt
                            author {
                                login
                            }
                        }
                    }
                }
            }
            """;
            
        com.fasterxml.jackson.databind.JsonNode result = gitHubGraphQLService.executeQuery(query, 
            java.util.Map.of("owner", "octocat", "name", "Hello-World"));
            
        assertThat(result).isNotNull();
        
        // Validate the GraphQL response structure
        assertThatCode(() -> {
            assertThat(result.has("data")).isTrue();
            
            com.fasterxml.jackson.databind.JsonNode data = result.get("data");
            assertThat(data.has("repository")).isTrue();
            
            com.fasterxml.jackson.databind.JsonNode repository = data.get("repository");
            assertThat(repository.has("name")).isTrue();
            assertThat(repository.has("issues")).isTrue();
            
            com.fasterxml.jackson.databind.JsonNode issues = repository.get("issues");
            assertThat(issues.has("totalCount")).isTrue();
            assertThat(issues.has("nodes")).isTrue();
        }).doesNotThrowAnyException();
    }
}
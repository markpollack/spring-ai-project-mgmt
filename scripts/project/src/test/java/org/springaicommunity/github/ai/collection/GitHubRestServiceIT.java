package org.springaicommunity.github.ai.collection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.kohsuke.github.GitHub;
import org.kohsuke.github.GitHubBuilder;
import org.springframework.web.client.RestClient;

import java.util.List;

import static org.assertj.core.api.Assertions.*;

/**
 * Real Integration Tests for GitHubRestService.
 * 
 * These tests make actual HTTP calls to GitHub's public API to verify:
 * 1. REST API connectivity and response parsing
 * 2. Query building and search functionality  
 * 3. JSON response structure validation
 * 4. Error handling with real API responses
 * 
 * Requirements:
 * - GITHUB_TOKEN environment variable (required for API access)
 * - Internet connectivity
 * - Uses public repositories to avoid authentication issues
 * 
 * Note: These tests run only with the 'integration-tests' Maven profile.
 * Run with: mvn verify -Pintegration-tests
 */
@DisplayName("GitHubRestService - Real Integration Tests")
class GitHubRestServiceIT {

    private GitHubRestService gitHubRestService;
    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() throws Exception {
        objectMapper = new ObjectMapper();
        objectMapper.registerModule(new com.fasterxml.jackson.datatype.jsr310.JavaTimeModule());
        
        // Create real GitHub client and RestClient for integration testing
        String token = System.getenv("GITHUB_TOKEN");
        GitHub gitHub = new GitHubBuilder().withOAuthToken(token).build();
        RestClient restClient = RestClient.builder()
            .defaultHeader("Authorization", "token " + token)
            .defaultHeader("Accept", "application/vnd.github.v3+json")
            .build();
            
        gitHubRestService = new GitHubRestService(gitHub, restClient, objectMapper);
    }

    @Test
    @DisplayName("Should fetch real repository information from GitHub")
    void shouldFetchRealRepositoryInformationFromGitHub() {
        // Test with a well-known public repository
        JsonNode repoInfo = gitHubRestService.getRepositoryInfo("spring-projects", "spring-ai");
        
        assertThat(repoInfo).isNotNull();
        assertThat(repoInfo.has("name")).isTrue();
        assertThat(repoInfo.has("full_name")).isTrue();
        assertThat(repoInfo.has("owner")).isTrue();
        assertThat(repoInfo.get("name").asText()).isEqualTo("spring-ai");
        assertThat(repoInfo.get("full_name").asText()).isEqualTo("spring-projects/spring-ai");
    }

    @Test
    @DisplayName("Should get real issue count from GitHub API")
    void shouldGetRealIssueCountFromGitHubAPI() {
        // Test with spring-ai repository
        int issueCount = gitHubRestService.getTotalIssueCount("spring-projects", "spring-ai", "all");
        
        // Spring AI should have a reasonable number of issues
        assertThat(issueCount).isGreaterThan(50); // Active project
        assertThat(issueCount).isLessThan(5000); // Reasonable upper bound
    }

    @Test
    @DisplayName("Should build valid search queries for different states")
    void shouldBuildValidSearchQueriesForDifferentStates() {
        String openQuery = gitHubRestService.buildSearchQuery("spring-projects", "spring-ai", "open", List.of(), "any");
        String closedQuery = gitHubRestService.buildSearchQuery("spring-projects", "spring-ai", "closed", List.of(), "any");
        String allQuery = gitHubRestService.buildSearchQuery("spring-projects", "spring-ai", "all", List.of(), "any");
        
        assertThat(openQuery).contains("repo:spring-projects/spring-ai");
        assertThat(openQuery).contains("is:issue");
        assertThat(openQuery).contains("is:open");
        
        assertThat(closedQuery).contains("is:closed");
        assertThat(allQuery).doesNotContain("is:open").doesNotContain("is:closed");
    }

    @Test
    @DisplayName("Should build search queries with labels correctly")
    void shouldBuildSearchQueriesWithLabelsCorrectly() {
        String queryWithSingleLabel = gitHubRestService.buildSearchQuery(
            "spring-projects", "spring-ai", "open", List.of("enhancement"), "any");
        String queryWithMultipleLabels = gitHubRestService.buildSearchQuery(
            "spring-projects", "spring-ai", "open", List.of("enhancement", "status: waiting-for-triage"), "all");
            
        assertThat(queryWithSingleLabel).contains("label:\"enhancement\"");
        assertThat(queryWithMultipleLabels).contains("label:\"enhancement\"").contains("label:\"status: waiting-for-triage\"");
    }

    @Test
    @DisplayName("Should handle repository not found gracefully")
    void shouldHandleRepositoryNotFoundGracefully() {
        // Test with a non-existent repository
        assertThatThrownBy(() -> {
            JsonNode result = gitHubRestService.getRepositoryInfo("nonexistent-user", "nonexistent-repo");
        }).isInstanceOf(Exception.class);
    }

    @Test
    @DisplayName("Should validate response structure from real GitHub API")
    void shouldValidateResponseStructureFromRealGitHubAPI() {
        JsonNode repoInfo = gitHubRestService.getRepositoryInfo("spring-projects", "spring-ai");
        
        // Validate the actual GitHub API response structure
        assertThat(repoInfo.has("id")).isTrue();
        assertThat(repoInfo.has("node_id")).isTrue();
        assertThat(repoInfo.has("name")).isTrue();
        assertThat(repoInfo.has("full_name")).isTrue();
        assertThat(repoInfo.has("private")).isTrue();
        assertThat(repoInfo.has("owner")).isTrue();
        assertThat(repoInfo.has("html_url")).isTrue();
        assertThat(repoInfo.has("description")).isTrue();
        assertThat(repoInfo.has("created_at")).isTrue();
        assertThat(repoInfo.has("updated_at")).isTrue();
        
        // Validate owner structure
        JsonNode owner = repoInfo.get("owner");
        assertThat(owner.has("login")).isTrue();
        assertThat(owner.has("id")).isTrue();
        assertThat(owner.has("avatar_url")).isTrue();
    }
}
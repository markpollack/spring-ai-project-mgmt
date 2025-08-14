package org.springaicommunity.github.ai.collection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.Map;

/**
 * Service for GitHub GraphQL API operations.
 */
@Service
public class GitHubGraphQLService {
    
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
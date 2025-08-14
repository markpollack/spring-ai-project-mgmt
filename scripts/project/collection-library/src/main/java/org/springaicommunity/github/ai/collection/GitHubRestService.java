package org.springaicommunity.github.ai.collection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.kohsuke.github.GHRateLimit;
import org.kohsuke.github.GHRepository;
import org.kohsuke.github.GitHub;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.io.IOException;
import java.util.List;

/**
 * Service for GitHub REST API operations.
 */
@Service
public class GitHubRestService {
    
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
    
    /**
     * Build search query string for GitHub API (backward compatible)
     * @param owner Repository owner
     * @param repo Repository name
     * @param state Issue state (open/closed/all)
     * @param labels List of labels to filter by
     * @param labelMode Label matching mode (any/all)
     * @return Formatted search query string
     */
    public String buildSearchQuery(String owner, String repo, String state, List<String> labels, String labelMode) {
        return buildSearchQuery(owner, repo, state, labels, labelMode, null, null, null);
    }
    
    /**
     * Build search query string for GitHub API with dashboard enhancements
     * @param owner Repository owner
     * @param repo Repository name
     * @param state Issue state (open/closed/all)
     * @param labels List of labels to filter by
     * @param labelMode Label matching mode (any/all)
     * @param sortBy Sort field (updated/created/comments/reactions)
     * @param sortOrder Sort direction (desc/asc)
     * @param maxIssues Maximum number of issues to collect (null for unlimited)
     * @return Formatted search query string
     */
    public String buildSearchQuery(String owner, String repo, String state, List<String> labels, String labelMode,
                                  String sortBy, String sortOrder, Integer maxIssues) {
        StringBuilder query = new StringBuilder();
        query.append("repo:").append(owner).append("/").append(repo);
        query.append(" is:issue");
        
        if (!"all".equals(state)) {
            query.append(" is:").append(state);
        }
        
        if (labels != null && !labels.isEmpty()) {
            if ("all".equals(labelMode)) {
                // For "all" mode, add each label requirement
                for (String label : labels) {
                    query.append(" label:\"").append(label).append("\"");
                }
            } else {
                // For "any" mode, use first label only due to GitHub API limitations
                query.append(" label:\"").append(labels.get(0)).append("\"");
                if (labels.size() > 1) {
                    logger.warn("Label mode 'any' with multiple labels - using first label only due to GitHub API limitations");
                }
            }
        }
        
        return query.toString();
    }
    
    /**
     * Execute GitHub search with sorting and pagination support
     * @param searchQuery The formatted search query string
     * @param sortBy Sort field (updated/created/comments/reactions)
     * @param sortOrder Sort direction (desc/asc)
     * @param perPage Number of issues per page (max 100)
     * @param page Page number (1-based)
     * @return JsonNode containing search results
     */
    public JsonNode searchIssues(String searchQuery, String sortBy, String sortOrder, int perPage, int page) {
        try {
            String uri = "https://api.github.com/search/issues?q={query}&sort={sort}&order={order}&per_page={perPage}&page={page}";
            String response = restClient.get()
                .uri(uri, searchQuery, sortBy, sortOrder, perPage, page)
                .retrieve()
                .body(String.class);
            
            return objectMapper.readTree(response);
        } catch (Exception e) {
            logger.error("Failed to search issues: {}", e.getMessage());
            return objectMapper.createObjectNode();
        }
    }
    
    /**
     * Get total issue count with search parameters
     * @param searchQuery The formatted search query string
     * @return Total number of issues matching the query
     */
    public int getTotalIssueCount(String searchQuery) {
        try {
            String response = restClient.get()
                .uri("https://api.github.com/search/issues?q={query}", searchQuery)
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
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
     * Build search query string for GitHub API
     * @param owner Repository owner
     * @param repo Repository name
     * @param state Issue state (open/closed/all)
     * @param labels List of labels to filter by
     * @param labelMode Label matching mode (any/all)
     * @return Formatted search query string
     */
    public String buildSearchQuery(String owner, String repo, String state, List<String> labels, String labelMode) {
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
}
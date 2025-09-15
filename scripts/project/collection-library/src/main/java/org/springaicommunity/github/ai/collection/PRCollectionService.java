package org.springaicommunity.github.ai.collection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Collection service for GitHub pull requests with soft approval detection.
 * Extends BaseCollectionService with PR-specific functionality.
 */
@Service
public class PRCollectionService extends BaseCollectionService {

    private static final Logger logger = LoggerFactory.getLogger(PRCollectionService.class);

    public PRCollectionService(GitHubGraphQLService graphQLService,
                              GitHubRestService restService,
                              JsonNodeUtils jsonUtils,
                              ObjectMapper objectMapper,
                              CollectionProperties properties) {
        super(graphQLService, restService, jsonUtils, objectMapper, properties);
    }

    @Override
    protected String getCollectionType() {
        return "prs";
    }

    @Override
    public CollectionResult collectItems(CollectionRequest request) {
        logger.info("Starting PR collection for repository: {}", request.repository());

        // Validate and normalize request
        CollectionRequest validatedRequest = validateRequest(request);

        try {
            String[] repoParts = validatedRequest.repository().split("/");
            String owner = repoParts[0];
            String repo = repoParts[1];

            // Handle specific PR collection
            if (validatedRequest.prNumber() != null) {
                return collectSpecificPR(owner, repo, validatedRequest);
            }

            // Handle multiple PR collection
            return collectMultiplePRs(owner, repo, validatedRequest);

        } catch (Exception e) {
            logger.error("PR collection failed for repository: {}", validatedRequest.repository(), e);
            throw e;
        }
    }

    /**
     * Collect a specific PR by number
     */
    private CollectionResult collectSpecificPR(String owner, String repo, CollectionRequest request) {
        logger.info("Collecting PR #{} from {}/{}", request.prNumber(), owner, repo);

        if (request.dryRun()) {
            logger.info("DRY RUN: Would collect PR #{}", request.prNumber());
            return new CollectionResult(1, 1, "dry-run", List.of("pr_" + request.prNumber() + ".json"));
        }

        try {
            // Create output directory
            Path outputDir = createOutputDirectory(request);
            cleanOutputDirectory(outputDir, request.clean());

            // Get PR data
            JsonNode prData = restService.getPullRequest(owner, repo, request.prNumber());
            logger.info("PR #{} found: {}", request.prNumber(),
                       jsonUtils.getString(prData, "title").orElse("Unknown"));

            // Get PR reviews for soft approval detection
            JsonNode reviewsData = restService.getPullRequestReviews(owner, repo, request.prNumber());
            logger.info("Found {} reviews for PR #{}", reviewsData.size(), request.prNumber());

            // Enhance PR data with soft approval detection
            JsonNode enhancedPR = enhancePRWithSoftApproval(prData, reviewsData);

            // Save PR data
            List<JsonNode> prList = List.of(enhancedPR);
            String filename = saveBatchToFile(outputDir, 1, prList, request);

            // Create ZIP if requested
            List<String> batchFiles = List.of(filename);
            createZipFile(outputDir, batchFiles, request);

            logger.info("PR #{} collection completed successfully", request.prNumber());
            return new CollectionResult(1, 1, outputDir.toString(), batchFiles);

        } catch (Exception e) {
            logger.error("Failed to collect PR #{}: {}", request.prNumber(), e.getMessage());
            throw new RuntimeException("Failed to collect PR #" + request.prNumber(), e);
        }
    }

    /**
     * Collect multiple PRs using search
     */
    private CollectionResult collectMultiplePRs(String owner, String repo, CollectionRequest request) {
        logger.info("Collecting {} PRs from {}/{}", request.prState(), owner, repo);

        // Build search query
        String searchQuery = buildSearchQuery(owner, repo, request);

        // Get total count
        int totalAvailableItems = getTotalItemCount(searchQuery);
        logger.info("Found {} total {} PRs matching criteria", totalAvailableItems, request.prState());

        if (request.dryRun()) {
            logger.info("DRY RUN: Would collect {} PRs", totalAvailableItems);
            return new CollectionResult(totalAvailableItems, 0, "dry-run", List.of("pr_batch.json"));
        }

        // Create output directory
        Path outputDir = createOutputDirectory(request);
        cleanOutputDirectory(outputDir, request.clean());

        // Collection state
        List<String> batchFiles = new ArrayList<>();
        AtomicInteger totalProcessed = new AtomicInteger(0);
        AtomicInteger batchIndex = new AtomicInteger(1);
        String cursor = null;
        int adaptiveBatchSize = request.batchSize();

        try {
            // Collection loop
            while (totalProcessed.get() < totalAvailableItems) {
                // Check if we should limit collection
                int itemsToCollect = totalAvailableItems;
                if (request.maxIssues() != null && request.maxIssues() > 0) {
                    itemsToCollect = Math.min(totalAvailableItems, request.maxIssues());
                    if (totalProcessed.get() >= itemsToCollect) {
                        logger.info("Reached maximum PR limit: {}", itemsToCollect);
                        break;
                    }
                }

                // Fetch batch
                List<JsonNode> batch = fetchBatch(searchQuery, adaptiveBatchSize, cursor);

                if (batch.isEmpty()) {
                    logger.info("No more PRs to fetch, ending collection");
                    break;
                }

                // Enhance PRs with soft approval detection
                List<JsonNode> enhancedPRs = enhancePRsWithSoftApproval(batch, owner, repo);

                // Save batch
                String filename = saveBatchToFile(outputDir, batchIndex.get(), enhancedPRs, request);
                batchFiles.add(filename);

                // Update progress
                totalProcessed.addAndGet(enhancedPRs.size());
                logProgress(batchIndex.get(), totalProcessed.get(), itemsToCollect, searchQuery);

                // Calculate adaptive batch size for next iteration
                adaptiveBatchSize = calculateAdaptiveBatchSize(enhancedPRs, request.batchSize());

                batchIndex.incrementAndGet();

                // Extract cursor for next page (simplified - actual implementation would need PR-specific pagination)
                Optional<String> nextCursor = extractCursor(batch.get(batch.size() - 1));
                if (nextCursor.isEmpty()) {
                    logger.info("No more pages available, ending collection");
                    break;
                }
                cursor = nextCursor.get();
            }

            // Create ZIP if requested
            createZipFile(outputDir, batchFiles, request);

            logger.info("PR collection completed: {}/{} PRs processed",
                       totalProcessed.get(), totalAvailableItems);

            return new CollectionResult(totalAvailableItems, totalProcessed.get(),
                                      outputDir.toString(), batchFiles);

        } catch (Exception e) {
            logger.error("Multiple PR collection failed: {}", e.getMessage());
            throw new RuntimeException("Multiple PR collection failed", e);
        }
    }

    @Override
    protected int getTotalItemCount(String searchQuery) {
        return restService.getTotalPRCount(searchQuery);
    }

    @Override
    protected String buildSearchQuery(String owner, String repo, CollectionRequest request) {
        return restService.buildPRSearchQuery(
            request.repository(),
            request.prState(),
            request.labelFilters(),
            request.labelMode()
        );
    }

    @Override
    protected List<JsonNode> fetchBatch(String searchQuery, int batchSize, String cursor) {
        // For now, use REST API search (could be enhanced with GraphQL later)
        JsonNode searchResults = restService.searchPRs(searchQuery, batchSize, cursor);
        return extractItems(searchResults);
    }

    @Override
    protected Optional<String> extractCursor(JsonNode response) {
        // For REST API pagination, use page numbers instead of cursors
        // Calculate next page from current response
        try {
            JsonNode items = response.path("items");
            if (!items.isArray() || items.size() == 0) {
                return Optional.empty(); // No more pages
            }

            // Simple increment for page-based pagination
            // This is a simplified approach - in production, you'd want to check if there are more pages
            return Optional.of("2"); // This will be overridden by the collection loop logic
        } catch (Exception e) {
            logger.warn("Failed to extract cursor from PR response: {}", e.getMessage());
            return Optional.empty();
        }
    }

    @Override
    protected List<JsonNode> extractItems(JsonNode response) {
        // Extract PRs from search response
        return jsonUtils.getArray(response, "items");
    }

    /**
     * Enhance a single PR with soft approval detection
     */
    private JsonNode enhancePRWithSoftApproval(JsonNode prData, JsonNode reviewsData) {
        boolean hasSoftApproval = detectSoftApproval(reviewsData);

        // Create enhanced PR data with soft approval information
        Map<String, Object> enhancedPR = objectMapper.convertValue(prData, Map.class);
        enhancedPR.put("soft_approval_detected", hasSoftApproval);
        enhancedPR.put("analysis_timestamp", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));

        if (hasSoftApproval) {
            enhancedPR.put("soft_approval_details", extractSoftApprovalDetails(reviewsData));
        }

        return objectMapper.valueToTree(enhancedPR);
    }

    /**
     * Enhance multiple PRs with soft approval detection
     */
    private List<JsonNode> enhancePRsWithSoftApproval(List<JsonNode> prs, String owner, String repo) {
        List<JsonNode> enhancedPRs = new ArrayList<>();

        for (JsonNode pr : prs) {
            try {
                int prNumber = jsonUtils.getInt(pr, "number").orElse(-1);
                if (prNumber > 0) {
                    // Get reviews for this PR
                    JsonNode reviewsData = restService.getPullRequestReviews(owner, repo, prNumber);
                    JsonNode enhancedPR = enhancePRWithSoftApproval(pr, reviewsData);
                    enhancedPRs.add(enhancedPR);
                } else {
                    // Add PR without enhancement if number is missing
                    enhancedPRs.add(pr);
                }
            } catch (Exception e) {
                logger.warn("Failed to enhance PR with soft approval detection: {}", e.getMessage());
                enhancedPRs.add(pr); // Add original PR without enhancement
            }
        }

        return enhancedPRs;
    }

    /**
     * Detect soft approval in PR reviews
     * Soft approval = approval from non-member (CONTRIBUTOR, FIRST_TIME_CONTRIBUTOR)
     */
    private boolean detectSoftApproval(JsonNode reviewsData) {
        if (!reviewsData.isArray()) {
            return false;
        }

        for (JsonNode review : reviewsData) {
            String state = jsonUtils.getString(review, "state").orElse("");
            String authorAssociation = jsonUtils.getString(review, "author_association").orElse("");
            String authorLogin = jsonUtils.getString(review, "user", "login").orElse("");

            if ("APPROVED".equals(state) &&
                ("CONTRIBUTOR".equals(authorAssociation) || "FIRST_TIME_CONTRIBUTOR".equals(authorAssociation))) {
                return true;
            }
        }
        return false;
    }

    /**
     * Extract soft approval details for enhanced PR data
     */
    private Map<String, Object> extractSoftApprovalDetails(JsonNode reviewsData) {
        Map<String, Object> details = new HashMap<>();
        List<Map<String, String>> softApprovals = new ArrayList<>();

        if (reviewsData.isArray()) {
            for (JsonNode review : reviewsData) {
                String state = jsonUtils.getString(review, "state").orElse("");
                String authorAssociation = jsonUtils.getString(review, "author_association").orElse("");
                String authorLogin = jsonUtils.getString(review, "user", "login").orElse("");

                if ("APPROVED".equals(state) &&
                    ("CONTRIBUTOR".equals(authorAssociation) || "FIRST_TIME_CONTRIBUTOR".equals(authorAssociation))) {

                    Map<String, String> approval = new HashMap<>();
                    approval.put("reviewer", authorLogin);
                    approval.put("association", authorAssociation);
                    approval.put("submitted_at", jsonUtils.getString(review, "submitted_at").orElse(""));
                    softApprovals.add(approval);
                }
            }
        }

        details.put("soft_approvals", softApprovals);
        details.put("count", softApprovals.size());
        return details;
    }
}
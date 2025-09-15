package org.springaicommunity.github.ai.collection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.FileOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

/**
 * Base class for collection services providing common functionality for issues and PRs.
 * Contains shared file operations, batching logic, and ZIP generation.
 */
public abstract class BaseCollectionService {

    private static final Logger logger = LoggerFactory.getLogger(BaseCollectionService.class);

    protected final GitHubGraphQLService graphQLService;
    protected final GitHubRestService restService;
    protected final JsonNodeUtils jsonUtils;
    protected final ObjectMapper objectMapper;
    protected final CollectionProperties properties;

    // Configuration constants (will be initialized from properties)
    protected final int MAX_BATCH_SIZE_BYTES;
    protected final int LARGE_ISSUE_THRESHOLD;
    protected final int SIZE_THRESHOLD;
    protected final String RESUME_FILE;

    public BaseCollectionService(GitHubGraphQLService graphQLService,
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

    /**
     * Main collection method to be implemented by subclasses
     */
    public abstract CollectionResult collectItems(CollectionRequest request);

    /**
     * Get the collection type name (e.g., "issues", "prs")
     */
    protected abstract String getCollectionType();

    /**
     * Get the total count of available items
     */
    protected abstract int getTotalItemCount(String searchQuery);

    /**
     * Build search query for the specific collection type
     */
    protected abstract String buildSearchQuery(String owner, String repo, CollectionRequest request);

    /**
     * Fetch a batch of items
     */
    protected abstract List<JsonNode> fetchBatch(String searchQuery, int batchSize, String cursor);

    /**
     * Extract cursor for pagination
     */
    protected abstract Optional<String> extractCursor(JsonNode response);

    /**
     * Extract items from response
     */
    protected abstract List<JsonNode> extractItems(JsonNode response);

    /**
     * Common validation logic for collection requests
     */
    protected CollectionRequest validateRequest(CollectionRequest request) {
        if (request == null) {
            throw new IllegalArgumentException("Collection request cannot be null");
        }

        String repository = request.repository();
        if (repository == null || repository.trim().isEmpty()) {
            repository = properties.getDefaultRepository();
            if (repository == null || repository.trim().isEmpty()) {
                throw new IllegalArgumentException("Repository must be specified either in request or configuration");
            }
        }

        int batchSize = request.batchSize() <= 0 ? properties.getBatchSize() : request.batchSize();
        // Note: Using getBatchSize() as both default and max since no separate max method exists
        // In production, you'd want a separate max batch size configuration

        String state = request.issueState();
        if (state == null || state.trim().isEmpty()) {
            state = properties.getDefaultState();
        }

        String labelMode = request.labelMode();
        if (labelMode == null || labelMode.trim().isEmpty()) {
            labelMode = properties.getDefaultLabelMode();
        }

        return new CollectionRequest(
            repository, batchSize, request.dryRun(), request.incremental(),
            request.zip(), request.clean(), request.resume(),
            state, request.labelFilters(), labelMode,
            request.maxIssues(), request.sortBy(), request.sortOrder(),
            request.collectionType(), request.prNumber(), request.prState()
        );
    }

    /**
     * Create output directory structure
     */
    protected Path createOutputDirectory(CollectionRequest request) {
        String[] repoParts = request.repository().split("/");
        String owner = repoParts[0];
        String repo = repoParts[1];

        // Use the appropriate state field based on collection type
        String state = getCollectionType().equals("prs") ? request.prState() : request.issueState();
        String baseDir = getCollectionType() + "/raw/" + state;
        Path outputDir = Paths.get(baseDir, owner, repo);

        try {
            Files.createDirectories(outputDir);
            logger.info("Created output directory: {}", outputDir);
            return outputDir;
        } catch (Exception e) {
            throw new RuntimeException("Failed to create output directory: " + outputDir, e);
        }
    }

    /**
     * Clean existing output directory if requested
     */
    protected void cleanOutputDirectory(Path outputDir, boolean clean) {
        if (!clean) {
            return;
        }

        try {
            if (Files.exists(outputDir)) {
                Files.walk(outputDir)
                    .sorted(java.util.Comparator.reverseOrder())
                    .forEach(path -> {
                        try {
                            Files.delete(path);
                        } catch (Exception e) {
                            logger.warn("Failed to delete: {}", path);
                        }
                    });

                // Recreate the directory after cleaning
                Files.createDirectories(outputDir);
                logger.info("Cleaned output directory: {}", outputDir);
            }
        } catch (Exception e) {
            logger.warn("Failed to clean output directory: {}", e.getMessage());
        }
    }

    /**
     * Save batch data to file
     */
    protected String saveBatchToFile(Path outputDir, int batchIndex, List<JsonNode> items,
                                   CollectionRequest request) {
        if (request.dryRun()) {
            String filename = String.format("batch_%03d_%s.json", batchIndex, getCollectionType());
            logger.info("DRY RUN: Would save {} items to {}", items.size(), filename);
            return filename;
        }

        try {
            String filename = String.format("batch_%03d_%s.json", batchIndex, getCollectionType());
            Path filePath = outputDir.resolve(filename);

            Map<String, Object> batchData = new HashMap<>();
            batchData.put("metadata", createBatchMetadata(batchIndex, items.size(), request));
            batchData.put(getCollectionType(), items);

            objectMapper.writerWithDefaultPrettyPrinter()
                       .writeValue(filePath.toFile(), batchData);

            logger.info("Saved batch {} with {} {} to {}",
                       batchIndex, items.size(), getCollectionType(), filename);
            return filename;

        } catch (Exception e) {
            throw new RuntimeException("Failed to save batch " + batchIndex, e);
        }
    }

    /**
     * Create metadata for a batch
     */
    protected Map<String, Object> createBatchMetadata(int batchIndex, int itemCount,
                                                    CollectionRequest request) {
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("batch_index", batchIndex);
        metadata.put("item_count", itemCount);
        metadata.put("collection_type", getCollectionType());
        metadata.put("repository", request.repository());
        // Use the appropriate state field based on collection type
        String state = getCollectionType().equals("prs") ? request.prState() : request.issueState();
        metadata.put("state", state);
        metadata.put("timestamp", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));

        if (request.labelFilters() != null && !request.labelFilters().isEmpty()) {
            metadata.put("label_filters", request.labelFilters());
            metadata.put("label_mode", request.labelMode());
        }

        return metadata;
    }

    /**
     * Create ZIP file from batch files
     */
    protected void createZipFile(Path outputDir, List<String> batchFiles, CollectionRequest request) {
        if (!request.zip() || request.dryRun()) {
            if (request.zip() && request.dryRun()) {
                logger.info("DRY RUN: Would create ZIP file with {} batch files", batchFiles.size());
            }
            return;
        }

        try {
            // Use the appropriate state field based on collection type
            String state = getCollectionType().equals("prs") ? request.prState() : request.issueState();
            String zipFilename = String.format("%s_%s_%s.zip",
                                              getCollectionType(),
                                              request.repository().replace("/", "_"),
                                              state);
            Path zipPath = outputDir.resolve(zipFilename);

            try (ZipOutputStream zos = new ZipOutputStream(new FileOutputStream(zipPath.toFile()))) {
                for (String batchFile : batchFiles) {
                    Path filePath = outputDir.resolve(batchFile);
                    if (Files.exists(filePath)) {
                        ZipEntry entry = new ZipEntry(batchFile);
                        zos.putNextEntry(entry);
                        Files.copy(filePath, zos);
                        zos.closeEntry();
                    }
                }
            }

            logger.info("Created ZIP file: {} with {} batch files", zipFilename, batchFiles.size());

        } catch (Exception e) {
            logger.error("Failed to create ZIP file", e);
            throw new RuntimeException("Failed to create ZIP file", e);
        }
    }

    /**
     * Calculate adaptive batch size based on item content
     */
    protected int calculateAdaptiveBatchSize(List<JsonNode> items, int requestedBatchSize) {
        if (items.isEmpty()) {
            return requestedBatchSize;
        }

        try {
            // Calculate average size of current items
            int totalSize = 0;
            for (JsonNode item : items) {
                String itemJson = objectMapper.writeValueAsString(item);
                totalSize += itemJson.length();
            }

            int averageSize = totalSize / items.size();

            // If items are large, reduce batch size
            if (averageSize > LARGE_ISSUE_THRESHOLD) {
                int adaptiveBatchSize = Math.max(1, requestedBatchSize / 2);
                logger.info("Large items detected (avg: {} bytes), reducing batch size to {}",
                           averageSize, adaptiveBatchSize);
                return adaptiveBatchSize;
            }

            return requestedBatchSize;

        } catch (Exception e) {
            logger.warn("Failed to calculate adaptive batch size: {}", e.getMessage());
            return requestedBatchSize;
        }
    }

    /**
     * Log collection progress
     */
    protected void logProgress(int currentBatch, int totalProcessed, int totalAvailable,
                             String searchQuery) {
        double percentage = totalAvailable > 0 ? (double) totalProcessed / totalAvailable * 100 : 0;
        logger.info("Progress: Batch {} - {}/{} {} processed ({:.1f}%)",
                   currentBatch, totalProcessed, totalAvailable, getCollectionType(), percentage);

        if (logger.isDebugEnabled()) {
            logger.debug("Search query: {}", searchQuery);
        }
    }

    /**
     * Handle collection errors with retry logic
     */
    protected void handleCollectionError(Exception e, int attempt, int maxRetries) {
        logger.error("Collection attempt {} failed: {}", attempt, e.getMessage());

        if (attempt < maxRetries) {
            int delaySeconds = (int) Math.pow(2, attempt); // Exponential backoff
            logger.info("Retrying in {} seconds... (attempt {}/{})", delaySeconds, attempt + 1, maxRetries);

            try {
                Thread.sleep(delaySeconds * 1000L);
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                throw new RuntimeException("Collection interrupted", ie);
            }
        } else {
            throw new RuntimeException("Collection failed after " + maxRetries + " attempts", e);
        }
    }
}
package org.springaicommunity.github.ai.classification.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Collections;
import java.util.List;
import java.util.Set;

/**
 * Configuration for the classification system behavior.
 * 
 * <p>This class encapsulates all configuration needed for classification,
 * including thresholds, batch sizes, label groups, and ignored labels.</p>
 * 
 * <p>Based on the Python configuration constants and provides sensible defaults
 * matching the proven Python implementation.</p>
 * 
 * @param confidenceThreshold Minimum confidence for accepting predictions (default: 0.7)
 * @param maxLabelsPerIssue Maximum number of labels to assign per issue (default: 3)
 * @param batchSize Number of issues to process in each LLM batch (default: 25)
 * @param labelGroups Label grouping rules for normalization
 * @param ignoredLabels Labels to exclude from processing
 * @param trainTestSplitRatio Ratio for train/test split (default: 0.8)
 * @param randomSeed Seed for reproducible splitting (default: 42)
 */
public record ClassificationConfig(
    @JsonProperty("confidence_threshold") double confidenceThreshold,
    @JsonProperty("max_labels_per_issue") int maxLabelsPerIssue,
    @JsonProperty("batch_size") int batchSize,
    @JsonProperty("label_groups") List<LabelGroup> labelGroups,
    @JsonProperty("ignored_labels") Set<String> ignoredLabels,
    @JsonProperty("train_test_split_ratio") double trainTestSplitRatio,
    @JsonProperty("random_seed") long randomSeed
) {
    
    /**
     * Constructor with validation and defaults.
     */
    @JsonCreator
    public ClassificationConfig {
        if (confidenceThreshold < 0.0 || confidenceThreshold > 1.0) {
            throw new IllegalArgumentException("Confidence threshold must be between 0.0 and 1.0, got: " + confidenceThreshold);
        }
        if (maxLabelsPerIssue < 1) {
            throw new IllegalArgumentException("Max labels per issue must be at least 1, got: " + maxLabelsPerIssue);
        }
        if (batchSize < 1) {
            throw new IllegalArgumentException("Batch size must be at least 1, got: " + batchSize);
        }
        if (trainTestSplitRatio <= 0.0 || trainTestSplitRatio >= 1.0) {
            throw new IllegalArgumentException("Train test split ratio must be between 0.0 and 1.0, got: " + trainTestSplitRatio);
        }
        
        // Ensure immutable collections
        if (labelGroups == null) {
            labelGroups = Collections.emptyList();
        } else {
            labelGroups = List.copyOf(labelGroups);
        }
        
        if (ignoredLabels == null) {
            ignoredLabels = Collections.emptySet();
        } else {
            // Normalize ignored labels to lowercase
            ignoredLabels = ignoredLabels.stream()
                .map(String::toLowerCase)
                .map(String::trim)
                .collect(java.util.stream.Collectors.toUnmodifiableSet());
        }
    }
    
    /**
     * Creates a default configuration with proven settings from Python implementation.
     * 
     * @return configuration with default values
     */
    public static ClassificationConfig defaults() {
        return new Builder().build();
    }
    
    /**
     * Builder for constructing ClassificationConfig instances.
     */
    public static class Builder {
        private double confidenceThreshold = 0.7;
        private int maxLabelsPerIssue = 3;
        private int batchSize = 25;
        private List<LabelGroup> labelGroups = getDefaultLabelGroups();
        private Set<String> ignoredLabels = getDefaultIgnoredLabels();
        private double trainTestSplitRatio = 0.8;
        private long randomSeed = 42;
        
        public Builder confidenceThreshold(double threshold) {
            this.confidenceThreshold = threshold;
            return this;
        }
        
        public Builder maxLabelsPerIssue(int max) {
            this.maxLabelsPerIssue = max;
            return this;
        }
        
        public Builder batchSize(int size) {
            this.batchSize = size;
            return this;
        }
        
        public Builder labelGroups(List<LabelGroup> groups) {
            this.labelGroups = groups;
            return this;
        }
        
        public Builder ignoredLabels(Set<String> labels) {
            this.ignoredLabels = labels;
            return this;
        }
        
        public Builder trainTestSplitRatio(double ratio) {
            this.trainTestSplitRatio = ratio;
            return this;
        }
        
        public Builder randomSeed(long seed) {
            this.randomSeed = seed;
            return this;
        }
        
        public ClassificationConfig build() {
            return new ClassificationConfig(
                confidenceThreshold, maxLabelsPerIssue, batchSize,
                labelGroups, ignoredLabels, trainTestSplitRatio, randomSeed
            );
        }
    }
    
    /**
     * Creates a new builder instance.
     * 
     * @return new builder
     */
    public static Builder builder() {
        return new Builder();
    }
    
    /**
     * Returns the default label groups from Python implementation.
     */
    private static List<LabelGroup> getDefaultLabelGroups() {
        return List.of(
            LabelGroup.of("vector store", "pinecone", "qdrant", "weaviate", "typesense", 
                         "opensearch", "chromadb", "pgvector", "milvus"),
            LabelGroup.of("model client", "openai", "claude", "ollama", "gemini", 
                         "deepseek", "mistral", "moonshot", "zhipu"),
            LabelGroup.of("data store", "mongo", "oracle", "neo4j", "cassandra", 
                         "mariadb", "postgresml", "elastic search", "coherence")
        );
    }
    
    /**
     * Returns the default ignored labels from Python implementation.
     */
    private static Set<String> getDefaultIgnoredLabels() {
        return Set.of(
            "triage", "duplicate", "invalid", "status: waiting-for-triage",
            "status: waiting-for-feedback", "status: backported", "follow up"
        );
    }
    
    /**
     * Checks if a label should be ignored during processing.
     * 
     * @param labelName the label to check
     * @return true if the label should be ignored
     */
    public boolean isIgnoredLabel(String labelName) {
        if (labelName == null) {
            return true;
        }
        return ignoredLabels.contains(labelName.toLowerCase().trim());
    }
    
    /**
     * Finds the label group that contains the given label variant.
     * 
     * @param labelVariant the label to look up
     * @return the group name if found, or the original label if not grouped
     */
    public String normalizeLabel(String labelVariant) {
        if (labelVariant == null) {
            return null;
        }
        
        return labelGroups.stream()
            .filter(group -> group.contains(labelVariant))
            .findFirst()
            .map(LabelGroup::groupName)
            .orElse(labelVariant.toLowerCase().trim());
    }
}
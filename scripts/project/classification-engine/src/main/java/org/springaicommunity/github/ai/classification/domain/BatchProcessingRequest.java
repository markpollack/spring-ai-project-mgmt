package org.springaicommunity.github.ai.classification.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import org.springaicommunity.github.ai.collection.Issue;

import java.util.Collections;
import java.util.List;

/**
 * Represents a request for batch processing of issues for classification.
 * 
 * <p>This record encapsulates all information needed to process a batch of issues
 * through the LLM classification pipeline, including the issues to classify,
 * configuration parameters, and context information.</p>
 * 
 * @param issues The issues to classify in this batch
 * @param batchNumber The batch number (for tracking and logging)
 * @param totalBatches Total number of batches in the full processing run
 * @param config Configuration for this batch processing
 * @param promptTemplate The classification prompt template to use
 */
public record BatchProcessingRequest(
    @JsonProperty("issues") List<Issue> issues,
    @JsonProperty("batch_number") int batchNumber,
    @JsonProperty("total_batches") int totalBatches,
    @JsonProperty("config") ClassificationConfig config,
    @JsonProperty("prompt_template") String promptTemplate
) {
    
    /**
     * Constructor with validation and immutable list creation.
     */
    @JsonCreator
    public BatchProcessingRequest {
        if (batchNumber < 1) {
            throw new IllegalArgumentException("Batch number must be at least 1, got: " + batchNumber);
        }
        if (totalBatches < 1) {
            throw new IllegalArgumentException("Total batches must be at least 1, got: " + totalBatches);
        }
        if (batchNumber > totalBatches) {
            throw new IllegalArgumentException("Batch number (" + batchNumber + ") cannot exceed total batches (" + totalBatches + ")");
        }
        if (config == null) {
            throw new IllegalArgumentException("Configuration cannot be null");
        }
        
        // Ensure immutable collections
        if (issues == null) {
            issues = Collections.emptyList();
        } else {
            issues = List.copyOf(issues);
        }
        
        if (promptTemplate == null) {
            promptTemplate = "";
        }
    }
    
    /**
     * Returns the number of issues in this batch.
     * 
     * @return issue count
     */
    public int getIssueCount() {
        return issues.size();
    }
    
    /**
     * Checks if this is the first batch.
     * 
     * @return true if batch number is 1
     */
    public boolean isFirstBatch() {
        return batchNumber == 1;
    }
    
    /**
     * Checks if this is the last batch.
     * 
     * @return true if this is the final batch
     */
    public boolean isLastBatch() {
        return batchNumber == totalBatches;
    }
    
    /**
     * Returns the progress percentage for this batch.
     * 
     * @return percentage complete (0.0 to 100.0)
     */
    public double getProgressPercentage() {
        return ((double) batchNumber / totalBatches) * 100.0;
    }
    
    /**
     * Returns a batch identifier string for logging.
     * 
     * @return formatted batch identifier
     */
    public String getBatchId() {
        return String.format("batch-%d-of-%d", batchNumber, totalBatches);
    }
    
    /**
     * Returns issue numbers in this batch for easy identification.
     * 
     * @return list of issue numbers
     */
    public List<Integer> getIssueNumbers() {
        return issues.stream()
            .map(Issue::number)
            .toList();
    }
    
    /**
     * Creates a summary string for logging and monitoring.
     * 
     * @return formatted summary
     */
    public String getSummary() {
        return String.format(
            "Batch %d/%d: %d issues, %.1f%% complete",
            batchNumber, totalBatches, issues.size(), getProgressPercentage()
        );
    }
    
    /**
     * Builder for constructing BatchProcessingRequest instances.
     */
    public static class Builder {
        private List<Issue> issues = Collections.emptyList();
        private int batchNumber = 1;
        private int totalBatches = 1;
        private ClassificationConfig config;
        private String promptTemplate = "";
        
        public Builder issues(List<Issue> issues) {
            this.issues = issues;
            return this;
        }
        
        public Builder batchNumber(int number) {
            this.batchNumber = number;
            return this;
        }
        
        public Builder totalBatches(int total) {
            this.totalBatches = total;
            return this;
        }
        
        public Builder config(ClassificationConfig config) {
            this.config = config;
            return this;
        }
        
        public Builder promptTemplate(String template) {
            this.promptTemplate = template;
            return this;
        }
        
        public BatchProcessingRequest build() {
            return new BatchProcessingRequest(issues, batchNumber, totalBatches, config, promptTemplate);
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
}
package org.springaicommunity.github.ai.classification.domain;

import java.util.List;
import java.util.Objects;

/**
 * Request for LLM-based issue classification containing issue data and configuration.
 * 
 * <p>This record encapsulates all information needed to classify a GitHub issue,
 * including the issue content, available labels to choose from, and configuration
 * parameters that control classification behavior.</p>
 * 
 * <p>Based on Python classification inputs with issue_number, title, body fields
 * and enhanced with Java-specific improvements for type safety and validation.</p>
 * 
 * @param issueNumber The GitHub issue number for tracking and correlation
 * @param title The issue title text for classification
 * @param body The issue body/description text for classification
 * @param availableLabels List of labels that can be assigned to this issue
 * @param config Classification configuration settings
 */
public record ClassificationRequest(
    int issueNumber,
    String title,
    String body,
    List<String> availableLabels,
    ClassificationConfig config
) {
    
    /**
     * Constructs a ClassificationRequest with validation.
     * 
     * @throws IllegalArgumentException if required fields are invalid
     */
    public ClassificationRequest {
        Objects.requireNonNull(title, "Title cannot be null");
        Objects.requireNonNull(body, "Body cannot be null");
        Objects.requireNonNull(availableLabels, "Available labels cannot be null");
        Objects.requireNonNull(config, "Classification config cannot be null");
        
        if (issueNumber <= 0) {
            throw new IllegalArgumentException("Issue number must be positive");
        }
        
        if (title.trim().isEmpty()) {
            throw new IllegalArgumentException("Title cannot be empty");
        }
        
        if (availableLabels.isEmpty()) {
            throw new IllegalArgumentException("Available labels cannot be empty");
        }
        
        // Make defensive copies
        availableLabels = List.copyOf(availableLabels);
    }
    
    /**
     * Get the combined text content for classification (title + body).
     * 
     * @return combined text content, suitable for LLM analysis
     */
    public String getCombinedText() {
        return title + "\n\n" + body;
    }
    
    /**
     * Get estimated character count for token usage calculations.
     * 
     * @return approximate character count of the request content
     */
    public int getCharacterCount() {
        return title.length() + body.length();
    }
    
    /**
     * Check if this request contains enough content for meaningful classification.
     * 
     * @return true if content seems sufficient for classification
     */
    public boolean hasMinimalContent() {
        String combined = getCombinedText().trim();
        return combined.length() >= 10; // Minimum reasonable content length
    }
    
    /**
     * Convenience constructor with default configuration.
     */
    public ClassificationRequest(int issueNumber, String title, String body, List<String> availableLabels) {
        this(issueNumber, title, body, availableLabels, ClassificationConfig.defaults());
    }
    
    /**
     * Create a builder for constructing ClassificationRequest instances.
     * 
     * @return new ClassificationRequest.Builder
     */
    public static Builder builder() {
        return new Builder();
    }
    
    /**
     * Builder class for ClassificationRequest with fluent API.
     */
    public static class Builder {
        private int issueNumber;
        private String title;
        private String body = "";
        private List<String> availableLabels = List.of();
        private ClassificationConfig config = ClassificationConfig.defaults();
        
        public Builder issueNumber(int issueNumber) {
            this.issueNumber = issueNumber;
            return this;
        }
        
        public Builder title(String title) {
            this.title = title;
            return this;
        }
        
        public Builder body(String body) {
            this.body = body != null ? body : "";
            return this;
        }
        
        public Builder availableLabels(List<String> availableLabels) {
            this.availableLabels = availableLabels != null ? availableLabels : List.of();
            return this;
        }
        
        public Builder config(ClassificationConfig config) {
            this.config = config != null ? config : ClassificationConfig.defaults();
            return this;
        }
        
        public ClassificationRequest build() {
            return new ClassificationRequest(issueNumber, title, body, availableLabels, config);
        }
    }
}
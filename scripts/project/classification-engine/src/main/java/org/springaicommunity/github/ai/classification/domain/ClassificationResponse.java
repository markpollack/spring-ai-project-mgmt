package org.springaicommunity.github.ai.classification.domain;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.OptionalDouble;

/**
 * Response from LLM-based issue classification containing predicted labels and metadata.
 * 
 * <p>This record represents the complete result of classifying a GitHub issue,
 * including the predicted labels with confidence scores, explanation, and 
 * processing metadata for monitoring and debugging.</p>
 * 
 * <p>Based on Python classification output structure:
 * <pre>{@code
 * {
 *   "issue_number": 1776,
 *   "predicted_labels": [{"label": "vector store", "confidence": 0.9}],
 *   "explanation": "Issue explicitly mentions vector database..."
 * }
 * }</pre>
 * 
 * @param issueNumber The GitHub issue number that was classified
 * @param predictedLabels List of predicted labels with confidence scores
 * @param explanation Human-readable explanation of the classification reasoning
 * @param processingTime Duration taken for classification
 * @param timestamp When the classification was performed
 * @param tokenUsage Number of tokens consumed during classification (if available)
 */
public record ClassificationResponse(
    int issueNumber,
    List<LabelPrediction> predictedLabels,
    String explanation,
    Duration processingTime,
    Instant timestamp,
    Long tokenUsage
) {
    
    /**
     * Constructs a ClassificationResponse with validation.
     * 
     * @throws IllegalArgumentException if required fields are invalid
     */
    public ClassificationResponse {
        Objects.requireNonNull(predictedLabels, "Predicted labels cannot be null");
        Objects.requireNonNull(explanation, "Explanation cannot be null");
        Objects.requireNonNull(processingTime, "Processing time cannot be null");
        Objects.requireNonNull(timestamp, "Timestamp cannot be null");
        
        if (issueNumber <= 0) {
            throw new IllegalArgumentException("Issue number must be positive");
        }
        
        if (explanation.trim().isEmpty()) {
            throw new IllegalArgumentException("Explanation cannot be empty");
        }
        
        if (processingTime.isNegative()) {
            throw new IllegalArgumentException("Processing time cannot be negative");
        }
        
        // Make defensive copy
        predictedLabels = List.copyOf(predictedLabels);
    }
    
    /**
     * Get the highest confidence score among all predicted labels.
     * 
     * @return maximum confidence score, or empty if no predictions
     */
    public OptionalDouble getMaxConfidence() {
        return predictedLabels.stream()
            .mapToDouble(LabelPrediction::confidence)
            .max();
    }
    
    /**
     * Get the average confidence score across all predicted labels.
     * 
     * @return average confidence score, or empty if no predictions
     */
    public OptionalDouble getAverageConfidence() {
        return predictedLabels.stream()
            .mapToDouble(LabelPrediction::confidence)
            .average();
    }
    
    /**
     * Check if this response contains high-confidence predictions.
     * 
     * @param threshold minimum confidence threshold (typically 0.6-0.8)
     * @return true if any prediction exceeds the threshold
     */
    public boolean hasHighConfidencePredictions(double threshold) {
        return predictedLabels.stream()
            .anyMatch(pred -> pred.confidence() >= threshold);
    }
    
    /**
     * Check if this response represents a "needs more info" fallback classification.
     * 
     * @return true if this appears to be a fallback classification
     */
    public boolean isFallbackClassification() {
        return predictedLabels.size() == 1 && 
               "needs more info".equals(predictedLabels.get(0).label());
    }
    
    /**
     * Check if this classification was successful (not an error state).
     * 
     * @return true if classification completed successfully
     */
    public boolean isSuccessful() {
        return !predictedLabels.isEmpty() || isFallbackClassification();
    }
    
    /**
     * Get just the label names as a list of strings.
     * 
     * @return list of predicted label names
     */
    public List<String> getLabelNames() {
        return predictedLabels.stream()
            .map(LabelPrediction::label)
            .toList();
    }
    
    /**
     * Create a builder for constructing ClassificationResponse instances.
     * 
     * @return new ClassificationResponse.Builder
     */
    public static Builder builder() {
        return new Builder();
    }
    
    /**
     * Builder class for ClassificationResponse with fluent API.
     */
    public static class Builder {
        private int issueNumber;
        private List<LabelPrediction> predictedLabels = List.of();
        private String explanation = "";
        private Duration processingTime = Duration.ZERO;
        private Instant timestamp = Instant.now();
        private Long tokenUsage = null;
        
        public Builder issueNumber(int issueNumber) {
            this.issueNumber = issueNumber;
            return this;
        }
        
        public Builder predictedLabels(List<LabelPrediction> predictedLabels) {
            this.predictedLabels = predictedLabels != null ? predictedLabels : List.of();
            return this;
        }
        
        public Builder explanation(String explanation) {
            this.explanation = explanation != null ? explanation : "";
            return this;
        }
        
        public Builder processingTime(Duration processingTime) {
            this.processingTime = processingTime != null ? processingTime : Duration.ZERO;
            return this;
        }
        
        public Builder timestamp(Instant timestamp) {
            this.timestamp = timestamp != null ? timestamp : Instant.now();
            return this;
        }
        
        public Builder tokenUsage(Long tokenUsage) {
            this.tokenUsage = tokenUsage;
            return this;
        }
        
        public ClassificationResponse build() {
            return new ClassificationResponse(issueNumber, predictedLabels, explanation, 
                                            processingTime, timestamp, tokenUsage);
        }
    }
}
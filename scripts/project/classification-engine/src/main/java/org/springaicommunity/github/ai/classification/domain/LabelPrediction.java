package org.springaicommunity.github.ai.classification.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Represents a single label prediction with confidence score from LLM classification.
 * 
 * <p>This record captures the result of classifying an issue with a specific label,
 * including the confidence score provided by the LLM. Used as part of 
 * {@link ClassificationResult} to represent all predicted labels for an issue.</p>
 * 
 * @param label The predicted label name (e.g., "vector store", "documentation")
 * @param confidence The confidence score from 0.0 to 1.0 (typically 0.7+ for valid predictions)
 */
public record LabelPrediction(
    @JsonProperty("label") String label,
    @JsonProperty("confidence") double confidence
) {
    
    /**
     * Constructor with validation for confidence score.
     */
    @JsonCreator
    public LabelPrediction {
        if (label == null || label.trim().isEmpty()) {
            throw new IllegalArgumentException("Label cannot be null or empty");
        }
        if (confidence < 0.0 || confidence > 1.0) {
            throw new IllegalArgumentException("Confidence must be between 0.0 and 1.0, got: " + confidence);
        }
    }
    
    /**
     * Checks if this prediction meets the default confidence threshold (0.7).
     * 
     * @return true if confidence >= 0.7
     */
    public boolean isHighConfidence() {
        return confidence >= 0.7;
    }
    
    /**
     * Checks if this prediction meets a custom confidence threshold.
     * 
     * @param threshold the minimum confidence threshold
     * @return true if confidence >= threshold
     */
    public boolean meetsThreshold(double threshold) {
        return confidence >= threshold;
    }
    
    /**
     * Returns the normalized label name (trimmed and lowercase).
     * 
     * @return normalized label for comparison
     */
    public String normalizedLabel() {
        return label.trim().toLowerCase();
    }
}
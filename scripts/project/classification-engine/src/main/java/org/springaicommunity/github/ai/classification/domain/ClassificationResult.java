package org.springaicommunity.github.ai.classification.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Represents the complete classification result for a single GitHub issue.
 * 
 * <p>This record captures the output from LLM-based classification, including
 * all predicted labels with confidence scores and an explanation of the 
 * classification reasoning.</p>
 * 
 * <p>Based on the Python classification output structure:
 * <pre>
 * {
 *   "issue_number": 1776,
 *   "predicted_labels": [{"label": "vector store", "confidence": 0.9}],
 *   "explanation": "Issue explicitly mentions vector database configuration..."
 * }
 * </pre></p>
 * 
 * @param issueNumber The GitHub issue number
 * @param predictedLabels List of label predictions with confidence scores
 * @param explanation Human-readable explanation of the classification reasoning
 */
public record ClassificationResult(
    @JsonProperty("issue_number") int issueNumber,
    @JsonProperty("predicted_labels") List<LabelPrediction> predictedLabels,
    @JsonProperty("explanation") String explanation
) {
    
    /**
     * Constructor with validation and immutable list creation.
     */
    @JsonCreator
    public ClassificationResult {
        if (issueNumber <= 0) {
            throw new IllegalArgumentException("Issue number must be positive, got: " + issueNumber);
        }
        if (predictedLabels == null) {
            predictedLabels = Collections.emptyList();
        } else {
            predictedLabels = List.copyOf(predictedLabels); // Ensure immutability
        }
        if (explanation == null) {
            explanation = "";
        }
    }
    
    /**
     * Returns the set of predicted label names (without confidence scores).
     * 
     * @return set of label names for easy comparison with ground truth
     */
    public Set<String> getLabelNames() {
        return predictedLabels.stream()
            .map(LabelPrediction::label)
            .collect(Collectors.toSet());
    }
    
    /**
     * Returns only high-confidence predictions (>= 0.7).
     * 
     * @return list of predictions that meet the default confidence threshold
     */
    public List<LabelPrediction> getHighConfidencePredictions() {
        return predictedLabels.stream()
            .filter(LabelPrediction::isHighConfidence)
            .toList();
    }
    
    /**
     * Returns predictions that meet a custom confidence threshold.
     * 
     * @param threshold minimum confidence score
     * @return list of predictions meeting the threshold
     */
    public List<LabelPrediction> getPredictionsAboveThreshold(double threshold) {
        return predictedLabels.stream()
            .filter(pred -> pred.meetsThreshold(threshold))
            .toList();
    }
    
    /**
     * Returns the highest confidence score among all predictions.
     * 
     * @return maximum confidence score, or 0.0 if no predictions
     */
    public double getMaxConfidence() {
        return predictedLabels.stream()
            .mapToDouble(LabelPrediction::confidence)
            .max()
            .orElse(0.0);
    }
    
    /**
     * Returns the number of predicted labels.
     * 
     * @return count of predictions
     */
    public int getLabelCount() {
        return predictedLabels.size();
    }
    
    /**
     * Checks if any predictions were made for this issue.
     * 
     * @return true if there are any predicted labels
     */
    public boolean hasPredictions() {
        return !predictedLabels.isEmpty();
    }
    
    /**
     * Checks if this result contains a specific label.
     * 
     * @param labelName the label to search for
     * @return true if the label is predicted for this issue
     */
    public boolean hasLabel(String labelName) {
        return predictedLabels.stream()
            .anyMatch(pred -> pred.label().equals(labelName));
    }
}
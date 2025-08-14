package org.springaicommunity.github.ai.classification.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Represents detailed statistics for a specific label in classification evaluation.
 * 
 * <p>This class provides comprehensive metrics for individual labels, including
 * confusion matrix values and calculated performance metrics. Used as part of
 * {@link EvaluationReport} to show per-label performance.</p>
 * 
 * @param labelName The name of the label
 * @param truePositives Number of correct positive predictions
 * @param falsePositives Number of incorrect positive predictions
 * @param falseNegatives Number of missed positive predictions
 * @param trueNegatives Number of correct negative predictions
 * @param metrics Calculated precision, recall, and F1 metrics
 */
public record LabelStatistics(
    @JsonProperty("label_name") String labelName,
    @JsonProperty("true_positives") int truePositives,
    @JsonProperty("false_positives") int falsePositives,
    @JsonProperty("false_negatives") int falseNegatives,
    @JsonProperty("true_negatives") int trueNegatives,
    @JsonProperty("metrics") ClassificationMetrics metrics
) {
    
    /**
     * Constructor with validation and automatic metrics calculation.
     */
    @JsonCreator
    public LabelStatistics {
        if (labelName == null || labelName.trim().isEmpty()) {
            throw new IllegalArgumentException("Label name cannot be null or empty");
        }
        if (truePositives < 0 || falsePositives < 0 || falseNegatives < 0 || trueNegatives < 0) {
            throw new IllegalArgumentException("All confusion matrix values must be non-negative");
        }
        if (metrics == null) {
            metrics = ClassificationMetrics.fromConfusionMatrix(truePositives, falsePositives, falseNegatives);
        }
    }
    
    /**
     * Creates LabelStatistics from confusion matrix values.
     * 
     * @param labelName the label name
     * @param tp true positives
     * @param fp false positives
     * @param fn false negatives
     * @param tn true negatives
     * @return label statistics with calculated metrics
     */
    public static LabelStatistics fromConfusionMatrix(String labelName, int tp, int fp, int fn, int tn) {
        ClassificationMetrics metrics = ClassificationMetrics.fromConfusionMatrix(tp, fp, fn);
        return new LabelStatistics(labelName, tp, fp, fn, tn, metrics);
    }
    
    /**
     * Creates empty statistics for a label (no predictions or ground truth).
     * 
     * @param labelName the label name
     * @return empty statistics
     */
    public static LabelStatistics empty(String labelName) {
        return new LabelStatistics(labelName, 0, 0, 0, 0, ClassificationMetrics.empty());
    }
    
    /**
     * Returns the total number of predictions made for this label.
     * 
     * @return true positives + false positives
     */
    public int getTotalPredictions() {
        return truePositives + falsePositives;
    }
    
    /**
     * Returns the total number of actual instances of this label.
     * 
     * @return true positives + false negatives (support)
     */
    public int getTotalActual() {
        return truePositives + falseNegatives;
    }
    
    /**
     * Returns the total number of examples evaluated.
     * 
     * @return sum of all confusion matrix values
     */
    public int getTotalExamples() {
        return truePositives + falsePositives + falseNegatives + trueNegatives;
    }
    
    /**
     * Returns the accuracy for this label.
     * 
     * @return (TP + TN) / (TP + FP + FN + TN)
     */
    public double getAccuracy() {
        int total = getTotalExamples();
        return total > 0 ? (double) (truePositives + trueNegatives) / total : 0.0;
    }
    
    /**
     * Checks if this label had any predictions or ground truth instances.
     * 
     * @return true if any classification activity occurred for this label
     */
    public boolean hasActivity() {
        return getTotalPredictions() > 0 || getTotalActual() > 0;
    }
    
    /**
     * Returns a detailed formatted string representation.
     * 
     * @return formatted string with all statistics
     */
    public String toDetailedString() {
        return String.format("%s: TP=%d, FP=%d, FN=%d, TN=%d, %s, Accuracy=%.3f", 
                           labelName, truePositives, falsePositives, falseNegatives, trueNegatives,
                           metrics.toFormattedString(), getAccuracy());
    }
}
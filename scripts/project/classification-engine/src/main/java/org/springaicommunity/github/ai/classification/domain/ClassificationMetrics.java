package org.springaicommunity.github.ai.classification.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Represents classification metrics (precision, recall, F1) for evaluation.
 * 
 * <p>This record provides the core metrics used to evaluate classification
 * performance, supporting both micro-averaged (overall) and macro-averaged
 * (per-label) calculations.</p>
 * 
 * <p>Metrics calculation follows the standard formulas:
 * <ul>
 *   <li>Precision = TP / (TP + FP)</li>
 *   <li>Recall = TP / (TP + FN)</li>
 *   <li>F1 = 2 * Precision * Recall / (Precision + Recall)</li>
 * </ul></p>
 * 
 * @param precision Precision score (0.0 to 1.0)
 * @param recall Recall score (0.0 to 1.0)  
 * @param f1 F1 score (0.0 to 1.0)
 * @param support Number of true instances for this metric
 */
public record ClassificationMetrics(
    @JsonProperty("precision") double precision,
    @JsonProperty("recall") double recall,
    @JsonProperty("f1") double f1,
    @JsonProperty("support") int support
) {
    
    /**
     * Constructor with validation for metric ranges.
     */
    @JsonCreator
    public ClassificationMetrics {
        if (precision < 0.0 || precision > 1.0) {
            throw new IllegalArgumentException("Precision must be between 0.0 and 1.0, got: " + precision);
        }
        if (recall < 0.0 || recall > 1.0) {
            throw new IllegalArgumentException("Recall must be between 0.0 and 1.0, got: " + recall);
        }
        if (f1 < 0.0 || f1 > 1.0) {
            throw new IllegalArgumentException("F1 must be between 0.0 and 1.0, got: " + f1);
        }
        if (support < 0) {
            throw new IllegalArgumentException("Support must be non-negative, got: " + support);
        }
    }
    
    /**
     * Creates metrics from confusion matrix values.
     * 
     * @param tp True positives
     * @param fp False positives
     * @param fn False negatives
     * @return calculated metrics
     */
    public static ClassificationMetrics fromConfusionMatrix(int tp, int fp, int fn) {
        double precision = (tp + fp) > 0 ? (double) tp / (tp + fp) : 0.0;
        double recall = (tp + fn) > 0 ? (double) tp / (tp + fn) : 0.0;
        double f1 = (precision + recall) > 0 ? 2.0 * precision * recall / (precision + recall) : 0.0;
        
        return new ClassificationMetrics(precision, recall, f1, tp + fn);
    }
    
    /**
     * Creates empty metrics (all zeros).
     * 
     * @return metrics with all values set to 0
     */
    public static ClassificationMetrics empty() {
        return new ClassificationMetrics(0.0, 0.0, 0.0, 0);
    }
    
    /**
     * Checks if this represents perfect classification (all metrics = 1.0).
     * 
     * @return true if precision, recall, and F1 are all 1.0
     */
    public boolean isPerfect() {
        return precision == 1.0 && recall == 1.0 && f1 == 1.0;
    }
    
    /**
     * Checks if classification was attempted (support > 0).
     * 
     * @return true if there were true instances to classify
     */
    public boolean hasSupport() {
        return support > 0;
    }
    
    /**
     * Returns a formatted string representation of the metrics.
     * 
     * @return formatted string with 3 decimal places
     */
    public String toFormattedString() {
        return String.format("Precision: %.3f, Recall: %.3f, F1: %.3f (support: %d)", 
                           precision, recall, f1, support);
    }
}
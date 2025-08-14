package org.springaicommunity.github.ai.classification.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Duration;
import java.time.Instant;
import java.util.Collections;
import java.util.Map;

/**
 * Comprehensive evaluation report for LLM-based classification results.
 * 
 * <p>This record implements the improved design pattern from the porting plan,
 * providing a complete evaluation report that can be serialized to both JSON
 * and Markdown formats for different consumption needs.</p>
 * 
 * <p>Includes both micro-averaged (overall) and macro-averaged (per-label) metrics,
 * execution timing, and per-label statistics for detailed analysis.</p>
 * 
 * @param microF1 Micro-averaged F1 score (overall performance)
 * @param microPrecision Micro-averaged precision
 * @param microRecall Micro-averaged recall
 * @param macroPrecision Macro-averaged precision (mean of per-label precision)
 * @param macroRecall Macro-averaged recall (mean of per-label recall)
 * @param macroF1 Macro-averaged F1 score (mean of per-label F1)
 * @param perLabelMetrics Detailed statistics for each label
 * @param executionTime Duration of the evaluation process
 * @param timestamp When this evaluation was completed
 * @param totalIssues Number of issues evaluated
 * @param totalPredictions Total number of label predictions made
 * @param totalLabels Number of unique labels in the evaluation
 */
public record EvaluationReport(
    @JsonProperty("micro_f1") double microF1,
    @JsonProperty("micro_precision") double microPrecision,
    @JsonProperty("micro_recall") double microRecall,
    @JsonProperty("macro_precision") double macroPrecision,
    @JsonProperty("macro_recall") double macroRecall,
    @JsonProperty("macro_f1") double macroF1,
    @JsonProperty("per_label_metrics") Map<String, LabelStatistics> perLabelMetrics,
    @JsonProperty("execution_time") Duration executionTime,
    @JsonProperty("timestamp") Instant timestamp,
    @JsonProperty("total_issues") int totalIssues,
    @JsonProperty("total_predictions") int totalPredictions,
    @JsonProperty("total_labels") int totalLabels
) {
    
    /**
     * Constructor with validation and immutable collections.
     */
    @JsonCreator
    public EvaluationReport {
        // Validate metric ranges
        validateMetric("microF1", microF1);
        validateMetric("microPrecision", microPrecision);
        validateMetric("microRecall", microRecall);
        validateMetric("macroPrecision", macroPrecision);
        validateMetric("macroRecall", macroRecall);
        validateMetric("macroF1", macroF1);
        
        // Validate counts
        if (totalIssues < 0) {
            throw new IllegalArgumentException("Total issues must be non-negative, got: " + totalIssues);
        }
        if (totalPredictions < 0) {
            throw new IllegalArgumentException("Total predictions must be non-negative, got: " + totalPredictions);
        }
        if (totalLabels < 0) {
            throw new IllegalArgumentException("Total labels must be non-negative, got: " + totalLabels);
        }
        
        // Ensure immutable collections
        if (perLabelMetrics == null) {
            perLabelMetrics = Collections.emptyMap();
        } else {
            perLabelMetrics = Map.copyOf(perLabelMetrics);
        }
        
        // Default values for required fields
        if (executionTime == null) {
            executionTime = Duration.ZERO;
        }
        if (timestamp == null) {
            timestamp = Instant.now();
        }
    }
    
    private static void validateMetric(String name, double value) {
        if (value < 0.0 || value > 1.0) {
            throw new IllegalArgumentException(name + " must be between 0.0 and 1.0, got: " + value);
        }
    }
    
    /**
     * Builder for constructing EvaluationReport instances.
     */
    public static class Builder {
        private double microF1;
        private double microPrecision;
        private double microRecall;
        private double macroPrecision;
        private double macroRecall;
        private double macroF1;
        private Map<String, LabelStatistics> perLabelMetrics = Collections.emptyMap();
        private Duration executionTime = Duration.ZERO;
        private Instant timestamp = Instant.now();
        private int totalIssues;
        private int totalPredictions;
        private int totalLabels;
        
        public Builder microMetrics(double precision, double recall, double f1) {
            this.microPrecision = precision;
            this.microRecall = recall;
            this.microF1 = f1;
            return this;
        }
        
        public Builder macroMetrics(double precision, double recall, double f1) {
            this.macroPrecision = precision;
            this.macroRecall = recall;
            this.macroF1 = f1;
            return this;
        }
        
        public Builder perLabelMetrics(Map<String, LabelStatistics> metrics) {
            this.perLabelMetrics = metrics;
            return this;
        }
        
        public Builder executionTime(Duration duration) {
            this.executionTime = duration;
            return this;
        }
        
        public Builder timestamp(Instant timestamp) {
            this.timestamp = timestamp;
            return this;
        }
        
        public Builder totals(int issues, int predictions, int labels) {
            this.totalIssues = issues;
            this.totalPredictions = predictions;
            this.totalLabels = labels;
            return this;
        }
        
        public EvaluationReport build() {
            return new EvaluationReport(
                microF1, microPrecision, microRecall,
                macroPrecision, macroRecall, macroF1,
                perLabelMetrics, executionTime, timestamp,
                totalIssues, totalPredictions, totalLabels
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
     * Checks if this evaluation meets the target F1 score (82.1% from Python baseline).
     * 
     * @return true if micro F1 >= 0.821
     */
    public boolean meetsTargetF1() {
        return microF1 >= 0.821;
    }
    
    /**
     * Checks if this evaluation shows good overall performance (F1 >= 0.80).
     * 
     * @return true if micro F1 >= 0.80
     */
    public boolean showsGoodPerformance() {
        return microF1 >= 0.80;
    }
    
    /**
     * Returns the average number of predictions per issue.
     * 
     * @return predictions per issue, or 0 if no issues
     */
    public double getAveragePredictionsPerIssue() {
        return totalIssues > 0 ? (double) totalPredictions / totalIssues : 0.0;
    }
    
    /**
     * Returns execution time in seconds.
     * 
     * @return execution time as double seconds
     */
    public double getExecutionTimeSeconds() {
        return executionTime.toMillis() / 1000.0;
    }
    
    /**
     * Gets the best performing label by F1 score.
     * 
     * @return label statistics for the highest F1 score, or null if no labels
     */
    public LabelStatistics getBestPerformingLabel() {
        return perLabelMetrics.values().stream()
            .filter(stats -> stats.metrics().hasSupport())
            .max((a, b) -> Double.compare(a.metrics().f1(), b.metrics().f1()))
            .orElse(null);
    }
    
    /**
     * Gets the worst performing label by F1 score (with support > 0).
     * 
     * @return label statistics for the lowest F1 score, or null if no labels
     */
    public LabelStatistics getWorstPerformingLabel() {
        return perLabelMetrics.values().stream()
            .filter(stats -> stats.metrics().hasSupport())
            .min((a, b) -> Double.compare(a.metrics().f1(), b.metrics().f1()))
            .orElse(null);
    }
    
    /**
     * Returns a summary string of the key metrics.
     * 
     * @return formatted summary
     */
    public String getSummary() {
        return String.format("F1: %.3f, Precision: %.3f, Recall: %.3f (%d issues, %d predictions, %.1fs)", 
                           microF1, microPrecision, microRecall, totalIssues, totalPredictions, getExecutionTimeSeconds());
    }
}
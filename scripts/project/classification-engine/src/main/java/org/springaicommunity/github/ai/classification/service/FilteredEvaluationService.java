package org.springaicommunity.github.ai.classification.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springaicommunity.github.ai.classification.config.LabelSpaceConfiguration;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.domain.LabelPrediction;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Evaluation service that implements Python's post-processing filtering approach.
 * 
 * <p>This service applies the exact same filtering methodology used in Python's
 * evaluate_filtered_predictions.py script to achieve 82.1% F1 score:</p>
 * 
 * <ol>
 *   <li>Load Java LLM classification results</li>
 *   <li>Load ground truth from test dataset</li>
 *   <li>Filter both predictions and ground truth by removing 12 problematic labels</li>
 *   <li>Calculate metrics on the filtered datasets</li>
 * </ol>
 * 
 * <p>The key insight is that this post-processing filter during evaluation 
 * (not during classification) matches Python's approach that achieved 82.1% F1.</p>
 */
@Service
public class FilteredEvaluationService {
    
    private static final Logger log = LoggerFactory.getLogger(FilteredEvaluationService.class);
    
    private final PostProcessingFilter postProcessingFilter;
    private final ComprehensiveMetricsCalculator metricsCalculator;
    private final ObjectMapper objectMapper;
    
    public FilteredEvaluationService(PostProcessingFilter postProcessingFilter,
                                   ComprehensiveMetricsCalculator metricsCalculator,
                                   ObjectMapper objectMapper) {
        this.postProcessingFilter = postProcessingFilter;
        this.metricsCalculator = metricsCalculator;
        this.objectMapper = objectMapper;
    }
    
    /**
     * Evaluate Java classification results using Python's filtering approach.
     * 
     * @param javaClassificationResults List of Java classification responses  
     * @param testDatasetPath Path to test_set.json file
     * @return Filtered evaluation results matching Python's methodology
     */
    public FilteredEvaluationResult evaluateWithPythonFiltering(
            List<ClassificationResponse> javaClassificationResults,
            String testDatasetPath) {
        
        log.info("Starting filtered evaluation with {} classification results", 
                javaClassificationResults.size());
        
        // Step 1: Load ground truth from test dataset
        Map<Integer, Set<String>> groundTruth = loadGroundTruthFromTestSet(testDatasetPath);
        log.info("Loaded ground truth for {} issues", groundTruth.size());
        
        // Step 2: Apply post-processing filter to predictions (remove 12 labels)
        List<ClassificationResponse> filteredPredictions = 
            postProcessingFilter.applyPythonFilterBatch(javaClassificationResults);
        
        // Step 3: Filter ground truth (remove same 12 labels)
        Map<Integer, Set<String>> filteredGroundTruth = filterGroundTruth(groundTruth);
        
        // Step 4: Calculate unfiltered metrics for comparison
        ComprehensiveMetricsCalculator.MetricsBundle unfilteredMetrics = 
            metricsCalculator.calculateMetrics(javaClassificationResults, groundTruth);
        
        // Step 5: Calculate filtered metrics (the target 82.1% F1)
        ComprehensiveMetricsCalculator.MetricsBundle filteredMetrics = 
            metricsCalculator.calculateMetrics(filteredPredictions, filteredGroundTruth);
        
        // Step 6: Generate filtering statistics
        PostProcessingFilter.FilteringStats filteringStats = 
            postProcessingFilter.getFilteringStats(javaClassificationResults, filteredPredictions);
        
        log.info("Evaluation complete - Unfiltered F1: {:.3f}, Filtered F1: {:.3f}", 
                unfilteredMetrics.microMetrics().f1(), filteredMetrics.microMetrics().f1());
        
        return new FilteredEvaluationResult(
            unfilteredMetrics,
            filteredMetrics,
            filteringStats,
            LabelSpaceConfiguration.EXCLUDED_LABELS,
            javaClassificationResults.size(),
            groundTruth.size()
        );
    }
    
    /**
     * Load ground truth labels from test_set.json file.
     * 
     * @param testDatasetPath Path to the test dataset JSON file
     * @return Map of issue number to ground truth label sets
     */
    private Map<Integer, Set<String>> loadGroundTruthFromTestSet(String testDatasetPath) {
        try {
            File testFile = new File(testDatasetPath);
            if (!testFile.exists()) {
                throw new IllegalArgumentException("Test dataset not found: " + testDatasetPath);
            }
            
            JsonNode testSetArray = objectMapper.readTree(testFile);
            Map<Integer, Set<String>> groundTruth = new HashMap<>();
            
            for (JsonNode issueNode : testSetArray) {
                int issueNumber = issueNode.get("issue_number").asInt();
                
                Set<String> labels = new HashSet<>();
                JsonNode labelsArray = issueNode.get("labels");
                if (labelsArray != null && labelsArray.isArray()) {
                    for (JsonNode labelNode : labelsArray) {
                        labels.add(labelNode.asText());
                    }
                }
                
                groundTruth.put(issueNumber, labels);
            }
            
            log.debug("Loaded ground truth for {} issues from {}", groundTruth.size(), testDatasetPath);
            return groundTruth;
            
        } catch (IOException e) {
            throw new RuntimeException("Failed to load test dataset: " + testDatasetPath, e);
        }
    }
    
    /**
     * Filter ground truth by removing the same 12 labels that are filtered from predictions.
     * 
     * @param originalGroundTruth Original ground truth labels
     * @return Filtered ground truth with excluded labels removed
     */
    private Map<Integer, Set<String>> filterGroundTruth(Map<Integer, Set<String>> originalGroundTruth) {
        Map<Integer, Set<String>> filteredGroundTruth = new HashMap<>();
        
        for (Map.Entry<Integer, Set<String>> entry : originalGroundTruth.entrySet()) {
            Set<String> filteredLabels = entry.getValue().stream()
                .filter(label -> !LabelSpaceConfiguration.EXCLUDED_LABELS.contains(label))
                .collect(Collectors.toSet());
            
            filteredGroundTruth.put(entry.getKey(), filteredLabels);
        }
        
        log.debug("Filtered ground truth: {} excluded labels removed from all issues", 
                LabelSpaceConfiguration.EXCLUDED_LABELS.size());
        
        return filteredGroundTruth;
    }
    
    /**
     * Create a summary report matching Python's evaluation output format.
     * 
     * @param result Filtered evaluation results
     * @return Formatted report string
     */
    public String generateSummaryReport(FilteredEvaluationResult result) {
        StringBuilder report = new StringBuilder();
        
        report.append("=== JAVA FILTERED EVALUATION RESULTS ===\n");
        report.append(String.format("(Excluding %d labels: %s)\n\n", 
            result.excludedLabels().size(),
            String.join(", ", result.excludedLabels().stream().sorted().collect(Collectors.toList()))));
        
        // Unfiltered results
        report.append("UNFILTERED METRICS:\n");
        report.append("------------------------------\n");
        report.append(String.format("Precision: %.3f\n", result.unfilteredMetrics().microMetrics().precision()));
        report.append(String.format("Recall: %.3f\n", result.unfilteredMetrics().microMetrics().recall()));
        report.append(String.format("F1 Score: %.3f\n\n", result.unfilteredMetrics().microMetrics().f1()));
        
        // Filtered results
        report.append("FILTERED METRICS:\n");
        report.append("------------------------------\n");
        report.append(String.format("Precision: %.3f\n", result.filteredMetrics().microMetrics().precision()));
        report.append(String.format("Recall: %.3f\n", result.filteredMetrics().microMetrics().recall()));
        report.append(String.format("F1 Score: %.3f\n\n", result.filteredMetrics().microMetrics().f1()));
        
        // Performance improvement
        double f1Improvement = result.filteredMetrics().microMetrics().f1() - result.unfilteredMetrics().microMetrics().f1();
        report.append("FILTERING IMPACT:\n");
        report.append("------------------------------\n");
        report.append(String.format("F1 Score Improvement: %+.3f points\n", f1Improvement));
        report.append(String.format("Precision Improvement: %+.3f points\n", 
            result.filteredMetrics().microMetrics().precision() - result.unfilteredMetrics().microMetrics().precision()));
        report.append(String.format("Recall Change: %+.3f points\n\n", 
            result.filteredMetrics().microMetrics().recall() - result.unfilteredMetrics().microMetrics().recall()));
        
        // Filtering statistics
        report.append("FILTERING STATISTICS:\n");
        report.append("------------------------------\n");
        report.append(result.filteringStats().toString()).append("\n\n");
        
        // Comparison with Python baseline
        report.append("PYTHON BASELINE COMPARISON:\n");
        report.append("------------------------------\n");
        report.append("Python Filtered F1: 0.821 (82.1%)\n");
        report.append(String.format("Java Filtered F1: %.3f (%.1f%%)\n", 
            result.filteredMetrics().microMetrics().f1(), result.filteredMetrics().microMetrics().f1() * 100));
        
        double parity = result.filteredMetrics().microMetrics().f1() / 0.821;
        report.append(String.format("Parity Achievement: %.1f%% of Python baseline\n", parity * 100));
        
        if (parity >= 0.99) {
            report.append("✅ PARITY ACHIEVED!\n");
        } else if (parity >= 0.95) {
            report.append("🟡 Close to parity (within 5%)\n");
        } else {
            report.append("🔴 Parity gap detected\n");
        }
        
        return report.toString();
    }
    
    /**
     * Results of filtered evaluation matching Python's approach.
     * 
     * @param unfilteredMetrics Metrics calculated on original predictions/ground truth
     * @param filteredMetrics Metrics calculated after applying 12-label exclusion  
     * @param filteringStats Statistics about the filtering operation
     * @param excludedLabels Set of labels that were excluded
     * @param totalPredictions Number of classification predictions processed
     * @param totalGroundTruth Number of ground truth issues loaded
     */
    public record FilteredEvaluationResult(
        ComprehensiveMetricsCalculator.MetricsBundle unfilteredMetrics,
        ComprehensiveMetricsCalculator.MetricsBundle filteredMetrics,
        PostProcessingFilter.FilteringStats filteringStats,
        Set<String> excludedLabels,
        int totalPredictions,
        int totalGroundTruth
    ) {
        /**
         * Check if parity with Python's 82.1% F1 baseline has been achieved.
         * 
         * @param threshold Minimum parity percentage (e.g., 0.99 for 99%)
         * @return true if Java filtered F1 is within threshold of Python's 82.1%
         */
        public boolean achievedParity(double threshold) {
            double pythonBaseline = 0.821;
            return (filteredMetrics.microMetrics().f1() / pythonBaseline) >= threshold;
        }
        
        /**
         * Get the F1 score improvement from filtering.
         * 
         * @return Difference between filtered and unfiltered F1 scores
         */
        public double getF1Improvement() {
            return filteredMetrics.microMetrics().f1() - unfilteredMetrics.microMetrics().f1();
        }
    }
}
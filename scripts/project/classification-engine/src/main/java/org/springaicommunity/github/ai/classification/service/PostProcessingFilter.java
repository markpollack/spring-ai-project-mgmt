package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.config.LabelSpaceConfiguration;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.domain.LabelPrediction;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Post-processing filter for implementing Python's evaluation-time label filtering.
 * 
 * <p>This service implements Mode B of our reproducibility experiment: predict on the full
 * label space (L_FULL) but filter out problematic labels during evaluation. This matches
 * the Python approach that achieved 82.1% F1 score.</p>
 * 
 * <p>The key insight is that Python allowed the model to benefit from the context of ALL
 * labels during prediction (including bug, enhancement, etc.) but then removed those 
 * labels during evaluation to avoid penalizing poor performance on subjective labels.</p>
 * 
 * <p>Usage example:</p>
 * <pre>
 * // Mode B: Python approach
 * ClassificationRequest request = buildRequest(issue, fullLabelSpace);
 * ClassificationResponse rawResponse = llmClient.classify(request);
 * ClassificationResponse filteredResponse = postProcessingFilter.filterLabels(
 *     rawResponse, LabelSpaceConfiguration.EXCLUDED_LABELS);
 * </pre>
 */
@Service
public class PostProcessingFilter {
    
    private static final Logger log = LoggerFactory.getLogger(PostProcessingFilter.class);
    
    /**
     * Filter labels from a classification response by removing specified labels.
     * 
     * <p>This method preserves all other response data (issue number, explanation,
     * timing, token usage) while only filtering the predicted labels. This ensures
     * that evaluation metrics are calculated only on the remaining labels.</p>
     * 
     * @param response Original classification response
     * @param labelsToRemove Set of labels to filter out  
     * @return New response with filtered labels
     */
    public ClassificationResponse filterLabels(ClassificationResponse response, Set<String> labelsToRemove) {
        if (response == null) {
            log.warn("Received null response, returning null");
            return null;
        }
        
        if (labelsToRemove == null || labelsToRemove.isEmpty()) {
            log.debug("No labels to filter, returning original response");
            return response;
        }
        
        // Filter predicted labels
        List<LabelPrediction> filteredPredictions = response.predictedLabels().stream()
            .filter(prediction -> !labelsToRemove.contains(prediction.label()))
            .collect(Collectors.toList());
        
        // Count filtered labels for logging
        int originalCount = response.predictedLabels().size();
        int filteredCount = filteredPredictions.size();
        int removedCount = originalCount - filteredCount;
        
        if (removedCount > 0) {
            List<String> removedLabels = response.predictedLabels().stream()
                .map(LabelPrediction::label)
                .filter(labelsToRemove::contains)
                .collect(Collectors.toList());
            
            log.debug("Filtered {} labels from issue #{}: {}", 
                     removedCount, response.issueNumber(), removedLabels);
        }
        
        // Create new response with filtered predictions
        return ClassificationResponse.builder()
            .issueNumber(response.issueNumber())
            .predictedLabels(filteredPredictions)
            .explanation(updateExplanation(response.explanation(), removedCount))
            .processingTime(response.processingTime())
            .timestamp(response.timestamp())
            .tokenUsage(response.tokenUsage())
            .build();
    }
    
    /**
     * Apply the standard Python exclusion filter (12 labels).
     * 
     * <p>Convenience method that applies the exact same filtering used in Python's
     * evaluate_filtered_predictions.py script.</p>
     * 
     * @param response Original classification response
     * @return Response with Python's 12 excluded labels filtered out
     */
    public ClassificationResponse applyPythonFilter(ClassificationResponse response) {
        return filterLabels(response, LabelSpaceConfiguration.EXCLUDED_LABELS);
    }
    
    /**
     * Filter multiple responses in batch.
     * 
     * @param responses List of classification responses
     * @param labelsToRemove Set of labels to filter out
     * @return List of responses with filtered labels
     */
    public List<ClassificationResponse> filterBatch(List<ClassificationResponse> responses, 
                                                   Set<String> labelsToRemove) {
        if (responses == null || responses.isEmpty()) {
            return responses;
        }
        
        return responses.stream()
            .map(response -> filterLabels(response, labelsToRemove))
            .collect(Collectors.toList());
    }
    
    /**
     * Apply Python filter to multiple responses.
     * 
     * @param responses List of classification responses
     * @return List of responses with Python's excluded labels filtered out
     */
    public List<ClassificationResponse> applyPythonFilterBatch(List<ClassificationResponse> responses) {
        return filterBatch(responses, LabelSpaceConfiguration.EXCLUDED_LABELS);
    }
    
    /**
     * Get filtering statistics for a set of responses.
     * 
     * @param originalResponses Original responses before filtering
     * @param filteredResponses Responses after filtering
     * @return Statistics about the filtering operation
     */
    public FilteringStats getFilteringStats(List<ClassificationResponse> originalResponses,
                                           List<ClassificationResponse> filteredResponses) {
        if (originalResponses.size() != filteredResponses.size()) {
            throw new IllegalArgumentException("Response lists must be same size");
        }
        
        int totalIssues = originalResponses.size();
        int totalOriginalPredictions = originalResponses.stream()
            .mapToInt(r -> r.predictedLabels().size())
            .sum();
        
        int totalFilteredPredictions = filteredResponses.stream()
            .mapToInt(r -> r.predictedLabels().size())
            .sum();
        
        int totalRemovedPredictions = totalOriginalPredictions - totalFilteredPredictions;
        
        // Count issues that had labels removed
        int issuesAffected = 0;
        for (int i = 0; i < totalIssues; i++) {
            int originalSize = originalResponses.get(i).predictedLabels().size();
            int filteredSize = filteredResponses.get(i).predictedLabels().size();
            if (originalSize > filteredSize) {
                issuesAffected++;
            }
        }
        
        return new FilteringStats(
            totalIssues,
            issuesAffected,
            totalOriginalPredictions,
            totalFilteredPredictions, 
            totalRemovedPredictions
        );
    }
    
    /**
     * Update explanation to reflect filtering operation.
     * 
     * @param originalExplanation Original explanation text
     * @param removedCount Number of labels that were filtered out
     * @return Updated explanation
     */
    private String updateExplanation(String originalExplanation, int removedCount) {
        if (removedCount == 0) {
            return originalExplanation;
        }
        
        String filterNote = String.format(" [Post-processed: %d label(s) filtered out]", removedCount);
        return originalExplanation + filterNote;
    }
    
    /**
     * Statistics about a filtering operation.
     * 
     * @param totalIssues Total number of issues processed
     * @param issuesAffected Number of issues that had labels filtered
     * @param originalPredictions Total predictions before filtering  
     * @param filteredPredictions Total predictions after filtering
     * @param removedPredictions Total predictions that were filtered out
     */
    public record FilteringStats(
        int totalIssues,
        int issuesAffected,
        int originalPredictions,
        int filteredPredictions,
        int removedPredictions
    ) {
        public double getAffectedPercentage() {
            return totalIssues == 0 ? 0.0 : (double) issuesAffected / totalIssues * 100.0;
        }
        
        public double getRemovedPercentage() {
            return originalPredictions == 0 ? 0.0 : (double) removedPredictions / originalPredictions * 100.0;
        }
        
        @Override
        public String toString() {
            return String.format(
                "FilteringStats{issues: %d/%d affected (%.1f%%), predictions: %d→%d removed %d (%.1f%%)}",
                issuesAffected, totalIssues, getAffectedPercentage(),
                originalPredictions, filteredPredictions, removedPredictions, getRemovedPercentage()
            );
        }
    }
}
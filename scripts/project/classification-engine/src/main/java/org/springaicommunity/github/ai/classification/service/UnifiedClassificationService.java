package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.collection.Issue;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * Unified classification service providing both LLM-based and rule-based classification.
 * 
 * <p>This service acts as a facade that provides access to both classification approaches
 * implemented in the Java system, matching the capabilities of the Python implementation
 * that achieved 82.1% F1 score.</p>
 * 
 * <p>Available approaches:
 * <ul>
 *   <li><b>LLM-based</b>: Uses Claude AI with enhanced Spring AI context in prompts</li>
 *   <li><b>Rule-based</b>: Direct keyword/phrase matching (fast, deterministic)</li>
 * </ul>
 * 
 * <p>This unified interface allows for easy comparison and evaluation of both approaches
 * to reproduce and validate the Python results.</p>
 */
@Service
public class UnifiedClassificationService {
    
    private final IssueClassificationService llmClassificationService;
    private final RuleBasedClassificationService ruleBasedClassificationService;
    
    public UnifiedClassificationService(
            IssueClassificationService llmClassificationService,
            RuleBasedClassificationService ruleBasedClassificationService) {
        this.llmClassificationService = llmClassificationService;
        this.ruleBasedClassificationService = ruleBasedClassificationService;
    }
    
    /**
     * Classify using LLM-based approach (Claude AI with enhanced prompts).
     * 
     * This matches the LLM-based classification approach from the Python system
     * that used classification-4.md prompt with Claude AI.
     */
    public ClassificationResponse classifyWithLLM(ClassificationRequest request) {
        // Convert request to Issue and classify
        Issue issue = new Issue(
            request.issueNumber(),
            request.title(),
            request.body(),
            "open",
            null, null, null, null, null,
            List.of(), List.of()
        );
        
        try {
            var result = llmClassificationService.classifyIssue(issue, request.availableLabels());
            return ClassificationResponse.builder()
                .issueNumber(result.issueNumber())
                .predictedLabels(result.predictedLabels())
                .explanation(result.explanation())
                .processingTime(Duration.ZERO) // Not tracked in ClassificationResult
                .timestamp(Instant.now())
                .tokenUsage(null) // Not tracked in ClassificationResult
                .build();
        } catch (Exception e) {
            return ClassificationResponse.builder()
                .issueNumber(request.issueNumber())
                .predictedLabels(List.of())
                .explanation("LLM classification failed: " + e.getMessage())
                .processingTime(Duration.ZERO)
                .timestamp(Instant.now())
                .tokenUsage(0L)
                .build();
        }
    }
    
    /**
     * Classify using rule-based approach (direct keyword/phrase matching).
     * 
     * This matches the rule-based classification from classify_full_test_set.py
     * that used direct keyword and context matching.
     */
    public ClassificationResponse classifyWithRules(ClassificationRequest request) {
        return ruleBasedClassificationService.classifyFromRequest(request);
    }
    
    /**
     * Classify multiple issues using LLM-based approach.
     */
    public List<ClassificationResponse> classifyBatchWithLLM(List<ClassificationRequest> requests) {
        return requests.stream()
            .map(this::classifyWithLLM)
            .toList();
    }
    
    /**
     * Classify multiple issues using rule-based approach.
     */
    public List<ClassificationResponse> classifyBatchWithRules(List<ClassificationRequest> requests) {
        return requests.stream()
            .map(this::classifyWithRules)
            .toList();
    }
    
    /**
     * Classify multiple issues using rule-based approach (Issue objects).
     */
    public List<ClassificationResponse> classifyIssuesWithRules(List<Issue> issues, List<String> availableLabels) {
        return ruleBasedClassificationService.classifyIssues(issues, availableLabels);
    }
    
    /**
     * Async classification using LLM-based approach.
     */
    public CompletableFuture<ClassificationResponse> classifyWithLLMAsync(ClassificationRequest request) {
        return CompletableFuture.supplyAsync(() -> classifyWithLLM(request));
    }
    
    /**
     * Get classification approach comparison for evaluation.
     * 
     * This method allows comparing both approaches on the same data to validate
     * that the Java implementation reproduces the Python results.
     */
    public ClassificationComparison compareApproaches(ClassificationRequest request) {
        ClassificationResponse llmResult = classifyWithLLM(request);
        ClassificationResponse ruleBasedResult = classifyWithRules(request);
        
        return new ClassificationComparison(
            request.issueNumber(),
            llmResult,
            ruleBasedResult
        );
    }
    
    /**
     * Get statistics about both classification engines.
     */
    public UnifiedClassificationStats getStatistics() {
        RuleBasedClassificationService.ClassificationEngineStats ruleStats = 
            ruleBasedClassificationService.getEngineStats();
        
        return new UnifiedClassificationStats(
            ruleStats.labelsWithRichContext(),
            ruleStats.labelsWithContext(),
            true, // LLM available (assuming Claude Code SDK is configured)
            true  // Rule-based available
        );
    }
    
    /**
     * Result of comparing LLM-based vs rule-based classification.
     */
    public record ClassificationComparison(
        int issueNumber,
        ClassificationResponse llmResult,
        ClassificationResponse ruleBasedResult
    ) {
        
        /**
         * Check if both approaches agree on the primary label.
         */
        public boolean primaryLabelsAgree() {
            String llmPrimary = llmResult.predictedLabels().isEmpty() ? 
                null : llmResult.predictedLabels().get(0).label();
            String rulesPrimary = ruleBasedResult.predictedLabels().isEmpty() ? 
                null : ruleBasedResult.predictedLabels().get(0).label();
            
            return llmPrimary != null && llmPrimary.equals(rulesPrimary);
        }
        
        /**
         * Get the confidence difference for the primary label.
         */
        public double primaryConfidenceDifference() {
            if (llmResult.predictedLabels().isEmpty() || ruleBasedResult.predictedLabels().isEmpty()) {
                return Double.NaN;
            }
            
            double llmConfidence = llmResult.predictedLabels().get(0).confidence();
            double rulesConfidence = ruleBasedResult.predictedLabels().get(0).confidence();
            
            return Math.abs(llmConfidence - rulesConfidence);
        }
    }
    
    /**
     * Statistics about the unified classification system.
     */
    public record UnifiedClassificationStats(
        int labelsWithRichContext,
        java.util.Set<String> labelsWithContext,
        boolean llmAvailable,
        boolean ruleBasedAvailable
    ) {}
}
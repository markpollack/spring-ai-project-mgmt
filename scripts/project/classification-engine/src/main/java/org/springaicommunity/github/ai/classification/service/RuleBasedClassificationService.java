package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.domain.LabelPrediction;
import org.springaicommunity.github.ai.collection.Issue;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Main rule-based classification service.
 * 
 * <p>This service implements the complete rule-based classification workflow
 * from the Python classify_full_test_set.py script. It orchestrates the
 * keyword, context, and phrase matching engines to produce final 
 * classification results.</p>
 * 
 * <p>Key features matching Python implementation:
 * - Processes enhanced labels from Spring AI context
 * - Applies confidence thresholds (0.3 inclusion, 0.6 high confidence)
 * - Sorts predictions by confidence
 * - Falls back to "needs more info" when no high confidence predictions
 * - Provides detailed explanations for each classification</p>
 */
@Service
public class RuleBasedClassificationService {
    
    private final RuleBasedConfidenceCalculator confidenceCalculator;
    private final SpringAIContextService contextService;
    
    public RuleBasedClassificationService(
            RuleBasedConfidenceCalculator confidenceCalculator,
            SpringAIContextService contextService) {
        this.confidenceCalculator = confidenceCalculator;
        this.contextService = contextService;
    }
    
    /**
     * Classify a single issue using rule-based approach.
     * 
     * @param issue The issue to classify
     * @param availableLabels List of available labels to consider
     * @return Classification response with predictions and explanation
     */
    public ClassificationResponse classifyIssue(Issue issue, List<String> availableLabels) {
        // Combine title and body for analysis (matching Python)
        String issueText = combineIssueText(issue.title(), issue.body()).toLowerCase();
        
        List<LabelPrediction> predictions = new ArrayList<>();
        
        // Process each available label
        for (String label : availableLabels) {
            // Skip labels not found in codebase (matching Python logic)
            if (isLabelNotFoundInCodebase(label)) {
                continue;
            }
            
            // Calculate confidence using all engines
            RuleBasedConfidenceCalculator.ConfidenceResult result = 
                confidenceCalculator.calculateConfidence(issueText, label);
            
            // Add to predictions if confidence meets inclusion threshold
            if (result.meetsInclusionThreshold()) {
                predictions.add(new LabelPrediction(
                    label,
                    result.totalConfidence()
                ));
            }
        }
        
        // Sort by confidence (descending) - matching Python
        predictions.sort((a, b) -> Double.compare(b.confidence(), a.confidence()));
        
        // Apply high confidence threshold - matching Python logic
        List<LabelPrediction> highConfidencePredictions = predictions.stream()
            .filter(p -> confidenceCalculator.meetsHighConfidenceThreshold(p.confidence()))
            .collect(Collectors.toList());
        
        // Generate final predictions and explanation
        List<LabelPrediction> finalPredictions;
        String explanation;
        
        if (highConfidencePredictions.isEmpty()) {
            // Fallback to "needs more info" - matching Python
            double maxConfidence = predictions.isEmpty() ? 0.3 : 
                predictions.get(0).confidence();
            finalPredictions = List.of(new LabelPrediction(
                "needs more info", 
                maxConfidence
            ));
            explanation = "Insufficient information to confidently assign specific labels";
        } else {
            finalPredictions = highConfidencePredictions;
            explanation = generateExplanation(issue, finalPredictions);
        }
        
        return ClassificationResponse.builder()
            .issueNumber(issue.number())
            .predictedLabels(finalPredictions)
            .explanation(explanation)
            .processingTime(Duration.ZERO) // Rule-based is essentially instant
            .timestamp(Instant.now())
            .tokenUsage(0L) // No tokens used for rule-based
            .build();
    }
    
    /**
     * Classify multiple issues in batch.
     */
    public List<ClassificationResponse> classifyIssues(List<Issue> issues, List<String> availableLabels) {
        return issues.stream()
            .map(issue -> classifyIssue(issue, availableLabels))
            .collect(Collectors.toList());
    }
    
    /**
     * Convert Issue to ClassificationRequest and classify.
     */
    public ClassificationResponse classifyFromRequest(ClassificationRequest request) {
        // Create a minimal Issue object from the request
        Issue issue = new Issue(
            request.issueNumber(),
            request.title(),
            request.body(),
            "open", // state not critical for classification
            null, // createdAt not needed
            null, // updatedAt not needed
            null, // closedAt not needed
            null, // url not needed
            null, // author not needed for classification
            List.of(), // comments not needed for rule-based
            List.of() // labels not needed for input
        );
        
        return classifyIssue(issue, request.availableLabels());
    }
    
    /**
     * Combine issue title and body for analysis.
     * Matches Python: "text = f\"{title} {body}\".lower()"
     */
    private String combineIssueText(String title, String body) {
        StringBuilder combined = new StringBuilder();
        if (title != null && !title.trim().isEmpty()) {
            combined.append(title.trim());
        }
        if (body != null && !body.trim().isEmpty()) {
            if (combined.length() > 0) {
                combined.append(" ");
            }
            combined.append(body.trim());
        }
        return combined.toString();
    }
    
    /**
     * Check if label should be skipped (not found in codebase).
     * Matches Python: "if label_info['description'] == \"Not found in project codebase\": continue"
     */
    private boolean isLabelNotFoundInCodebase(String label) {
        return contextService.getLabelContext(label)
            .map(context -> "Not found in project codebase".equals(context.description()))
            .orElse(true); // If no context, assume not found
    }
    
    /**
     * Generate explanation for classification results.
     */
    private String generateExplanation(Issue issue, List<LabelPrediction> predictions) {
        if (predictions.isEmpty()) {
            return "No confident predictions available";
        }
        
        if (predictions.size() == 1 && "needs more info".equals(predictions.get(0).label())) {
            return "Insufficient information to confidently assign specific labels";
        }
        
        StringBuilder explanation = new StringBuilder();
        explanation.append("Issue about '").append(issue.title()).append("' - ");
        
        if (predictions.size() == 1) {
            LabelPrediction pred = predictions.get(0);
            explanation.append("classified as '").append(pred.label()).append("' ");
            explanation.append("with ").append(String.format("%.1f", pred.confidence() * 100)).append("% confidence");
        } else {
            explanation.append("classified with multiple labels: ");
            explanation.append(predictions.stream()
                .map(p -> p.label() + " (" + String.format("%.1f", p.confidence() * 100) + "%)")
                .collect(Collectors.joining(", ")));
        }
        
        return explanation.toString();
    }
    
    /**
     * Get statistics about the classification engines.
     */
    public ClassificationEngineStats getEngineStats() {
        return new ClassificationEngineStats(
            contextService.getLabelsWithRichContext().size(),
            contextService.getLabelsWithRichContext()
        );
    }
    
    /**
     * Statistics about the classification engines.
     */
    public record ClassificationEngineStats(
        int labelsWithRichContext,
        Set<String> labelsWithContext
    ) {}
}
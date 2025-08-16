package org.springaicommunity.github.ai.classification.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springaicommunity.github.ai.classification.domain.*;
import org.springaicommunity.github.ai.collection.Issue;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * Default implementation of IssueClassificationService.
 * 
 * <p>This service orchestrates the complete classification workflow:
 * <ul>
 *   <li>Converting GitHub issues to classification requests</li>
 *   <li>Delegating to LLM client for actual classification</li>
 *   <li>Converting LLM responses back to domain results</li>
 *   <li>Handling validation and error recovery</li>
 * </ul>
 * 
 * <p>Based on the Python batch processing approach with improved error handling
 * and monitoring capabilities.</p>
 */
@Service
public class DefaultIssueClassificationService implements IssueClassificationService {
    
    private static final Logger log = LoggerFactory.getLogger(DefaultIssueClassificationService.class);
    
    private final LLMClient llmClient;
    private final ClassificationConfig defaultConfig;
    
    public DefaultIssueClassificationService(LLMClient llmClient, ClassificationConfig defaultConfig) {
        this.llmClient = llmClient;
        this.defaultConfig = defaultConfig;
    }
    
    @Override
    public ClassificationResult classifyIssue(Issue issue, List<String> availableLabels) throws ClassificationException {
        log.debug("Classifying issue #{}: {}", issue.number(), issue.title());
        
        // Convert to classification request
        ClassificationRequest request = buildClassificationRequest(issue, availableLabels);
        
        // Perform classification
        ClassificationResponse response = llmClient.classifyIssue(request);
        
        // Convert to domain result
        return convertToClassificationResult(response, issue, Instant.now());
    }
    
    @Override
    public List<ClassificationResult> classifyBatch(List<Issue> issues, List<String> availableLabels) throws ClassificationException {
        if (issues.isEmpty()) {
            return List.of();
        }
        
        log.debug("Classifying batch of {} issues", issues.size());
        
        // Split into optimal batch sizes if needed
        List<ClassificationResult> allResults = new ArrayList<>();
        int batchSize = Math.min(issues.size(), llmClient.getMaxBatchSize());
        
        for (int i = 0; i < issues.size(); i += batchSize) {
            int endIndex = Math.min(i + batchSize, issues.size());
            List<Issue> batch = issues.subList(i, endIndex);
            
            log.debug("Processing batch {}-{} of {}", i + 1, endIndex, issues.size());
            
            // Convert batch to requests
            List<ClassificationRequest> requests = batch.stream()
                .map(issue -> buildClassificationRequest(issue, availableLabels))
                .toList();
            
            // Perform batch classification
            List<ClassificationResponse> responses = llmClient.classifyBatch(requests);
            
            // Convert responses to results
            Instant batchTimestamp = Instant.now();
            for (int j = 0; j < responses.size() && j < batch.size(); j++) {
                ClassificationResponse response = responses.get(j);
                Issue issue = batch.get(j);
                allResults.add(convertToClassificationResult(response, issue, batchTimestamp));
            }
        }
        
        log.info("Successfully classified {} issues in batches", allResults.size());
        return allResults;
    }
    
    @Override
    public CompletableFuture<ClassificationResult> classifyIssueAsync(Issue issue, List<String> availableLabels) {
        return llmClient.classifyIssueAsync(buildClassificationRequest(issue, availableLabels))
            .thenApply(response -> convertToClassificationResult(response, issue, Instant.now()));
    }
    
    @Override
    public CompletableFuture<List<ClassificationResult>> classifyBatchAsync(List<Issue> issues, List<String> availableLabels) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                return classifyBatch(issues, availableLabels);
            } catch (ClassificationException e) {
                throw new RuntimeException(e);
            }
        });
    }
    
    @Override
    public EvaluationReport evaluateClassification(List<ClassificationResult> predictions, List<Issue> groundTruth) {
        log.debug("Evaluating {} predictions against {} ground truth issues", 
                 predictions.size(), groundTruth.size());
        
        // This is a complex implementation that would calculate precision, recall, F1
        // For now, return a basic evaluation report structure
        return EvaluationReport.builder()
            .totals(predictions.size(), 
                    predictions.stream().mapToInt(result -> result.predictedLabels().size()).sum(),
                    0) // TODO: Calculate unique labels
            .timestamp(Instant.now())
            .build();
    }
    
    @Override
    public boolean isAvailable() {
        return llmClient.isAvailable();
    }
    
    @Override
    public int getMaxBatchSize() {
        return llmClient.getMaxBatchSize();
    }
    
    /**
     * Convert GitHub Issue to ClassificationRequest.
     */
    private ClassificationRequest buildClassificationRequest(Issue issue, List<String> availableLabels) {
        return ClassificationRequest.builder()
            .issueNumber(issue.number())
            .title(issue.title())
            .body(issue.body() != null ? issue.body() : "")
            .availableLabels(availableLabels)
            .config(defaultConfig)
            .build();
    }
    
    /**
     * Convert ClassificationResponse to ClassificationResult.
     */
    private ClassificationResult convertToClassificationResult(ClassificationResponse response, 
                                                               Issue originalIssue, 
                                                               Instant timestamp) {
        return new ClassificationResult(
            response.issueNumber(),
            response.predictedLabels(),
            response.explanation()
        );
    }
}
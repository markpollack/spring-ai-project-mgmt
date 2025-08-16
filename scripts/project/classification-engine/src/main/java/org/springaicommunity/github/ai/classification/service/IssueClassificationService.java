package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.domain.ClassificationResult;
import org.springaicommunity.github.ai.classification.domain.EvaluationReport;
import org.springaicommunity.github.ai.collection.Issue;

import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * Service interface for GitHub issue classification using LLM-based analysis.
 * 
 * <p>This service provides the main entry point for classifying GitHub issues,
 * handling both single and batch processing, with validation and error handling.</p>
 */
public interface IssueClassificationService {
    
    /**
     * Classify a single GitHub issue.
     * 
     * @param issue The GitHub issue to classify
     * @param availableLabels List of available labels for classification
     * @return Classification result with predicted labels and metadata
     * @throws ClassificationException if classification fails
     */
    ClassificationResult classifyIssue(Issue issue, List<String> availableLabels) throws ClassificationException;
    
    /**
     * Classify multiple GitHub issues in batch for efficiency.
     * 
     * @param issues List of GitHub issues to classify
     * @param availableLabels List of available labels for classification
     * @return List of classification results in the same order as input
     * @throws ClassificationException if batch classification fails
     */
    List<ClassificationResult> classifyBatch(List<Issue> issues, List<String> availableLabels) throws ClassificationException;
    
    /**
     * Asynchronously classify a single GitHub issue.
     * 
     * @param issue The GitHub issue to classify
     * @param availableLabels List of available labels for classification
     * @return CompletableFuture containing the classification result
     */
    CompletableFuture<ClassificationResult> classifyIssueAsync(Issue issue, List<String> availableLabels);
    
    /**
     * Asynchronously classify multiple issues in batch.
     * 
     * @param issues List of GitHub issues to classify
     * @param availableLabels List of available labels for classification
     * @return CompletableFuture containing list of classification results
     */
    CompletableFuture<List<ClassificationResult>> classifyBatchAsync(List<Issue> issues, List<String> availableLabels);
    
    /**
     * Evaluate classification performance against ground truth labels.
     * 
     * @param predictions List of classification results
     * @param groundTruth List of issues with actual labels for comparison
     * @return Comprehensive evaluation report with metrics
     */
    EvaluationReport evaluateClassification(List<ClassificationResult> predictions, List<Issue> groundTruth);
    
    /**
     * Check if the classification service is ready and available.
     * 
     * @return true if service can process classification requests
     */
    boolean isAvailable();
    
    /**
     * Get the maximum number of issues that can be processed in a single batch.
     * 
     * @return maximum batch size supported
     */
    int getMaxBatchSize();
}
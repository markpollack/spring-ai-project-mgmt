package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;

import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * Abstraction for LLM-based issue classification services.
 * Provides methods for single and batch classification with confidence scoring.
 */
public interface LLMClient {
    
    /**
     * Classify a single issue and return predicted labels with confidence scores.
     * 
     * @param request The classification request containing issue data
     * @return Classification response with predicted labels and explanations
     * @throws ClassificationException if classification fails
     */
    ClassificationResponse classifyIssue(ClassificationRequest request) throws ClassificationException;
    
    /**
     * Classify multiple issues in a single batch request for efficiency.
     * 
     * @param requests List of classification requests
     * @return List of classification responses in the same order as requests
     * @throws ClassificationException if batch classification fails
     */
    List<ClassificationResponse> classifyBatch(List<ClassificationRequest> requests) throws ClassificationException;
    
    /**
     * Asynchronously classify a single issue.
     * 
     * @param request The classification request
     * @return CompletableFuture containing the classification response
     */
    CompletableFuture<ClassificationResponse> classifyIssueAsync(ClassificationRequest request);
    
    /**
     * Asynchronously classify multiple issues in batch.
     * 
     * @param requests List of classification requests
     * @return CompletableFuture containing list of classification responses
     */
    CompletableFuture<List<ClassificationResponse>> classifyBatchAsync(List<ClassificationRequest> requests);
    
    /**
     * Check if the LLM client is available and ready to process requests.
     * 
     * @return true if client is ready, false otherwise
     */
    boolean isAvailable();
    
    /**
     * Get the maximum number of issues that can be processed in a single batch.
     * 
     * @return maximum batch size supported by this client
     */
    int getMaxBatchSize();
    
    /**
     * Get estimated token usage for a classification request.
     * Useful for batch sizing and cost estimation.
     * 
     * @param request The classification request to estimate
     * @return estimated number of tokens that will be consumed
     */
    long estimateTokenUsage(ClassificationRequest request);
}
package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;

import java.util.List;

/**
 * Service for building LLM prompts for GitHub issue classification.
 * 
 * <p>This service generates structured prompts that match the proven Python
 * implementation approach, with conservative classification guidelines and
 * focus on high-performing technical labels.</p>
 */
public interface PromptTemplateService {
    
    /**
     * Build a classification prompt for a single issue.
     * 
     * @param request The classification request with issue data
     * @return formatted prompt string for LLM processing
     */
    String buildClassificationPrompt(ClassificationRequest request);
    
    /**
     * Build a batch classification prompt for multiple issues.
     * 
     * @param requests List of classification requests to process in batch
     * @return formatted batch prompt string for LLM processing
     */
    String buildBatchClassificationPrompt(List<ClassificationRequest> requests);
    
    /**
     * Get the standard system prompt that establishes classification rules.
     * 
     * @return system prompt with classification guidelines
     */
    String getSystemPrompt();
    
    /**
     * Get example JSON format for classification responses.
     * 
     * @return JSON example string for response format
     */
    String getResponseFormatExample();
    
    /**
     * Get the list of high-performing labels to focus on during classification.
     * Based on Python evaluation results.
     * 
     * @return list of prioritized label names
     */
    List<String> getHighPerformingLabels();
}
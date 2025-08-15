package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.domain.ClassificationConfig;

import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Service interface for normalizing and filtering GitHub issue labels.
 * 
 * <p>This service provides label normalization capabilities based on the Python
 * implementation, including label grouping (e.g., "pgvector" → "vector store")
 * and filtering of ignored labels (e.g., "triage", "duplicate").</p>
 * 
 * <p>Core functionality matches the Python normalize_labels() function:
 * <ul>
 *   <li>Case-insensitive label matching</li>
 *   <li>Label grouping based on technology variants</li>
 *   <li>Filtering of administrative/ignored labels</li>
 *   <li>Frequency analysis for rare label detection</li>
 * </ul></p>
 */
public interface LabelNormalizationService {
    
    /**
     * Normalizes a list of raw labels from GitHub issues.
     * 
     * <p>This method implements the core Python normalize_labels() logic:
     * <ol>
     *   <li>Convert labels to lowercase and trim whitespace</li>
     *   <li>Filter out ignored labels (triage, duplicate, etc.)</li>
     *   <li>Map label variants to canonical group names</li>
     *   <li>Return normalized labels or empty list if all filtered</li>
     * </ol></p>
     * 
     * @param rawLabels the original labels from GitHub issue
     * @return normalized and filtered labels, empty if all labels ignored
     */
    List<String> normalizeLabels(List<String> rawLabels);
    
    /**
     * Normalizes a single label using the same logic as batch normalization.
     * 
     * @param rawLabel the original label from GitHub
     * @return normalized label, or null if label should be ignored
     */
    String normalizeLabel(String rawLabel);
    
    /**
     * Checks if a label should be ignored during processing.
     * 
     * @param labelName the label to check (case-insensitive)
     * @return true if the label should be filtered out
     */
    boolean isIgnoredLabel(String labelName);
    
    /**
     * Finds the canonical group name for a label variant.
     * 
     * <p>Example: "pgvector" → "vector store", "openai" → "model client"</p>
     * 
     * @param labelVariant the specific technology label
     * @return canonical group name if found, or original label if not grouped
     */
    String findGroupName(String labelVariant);
    
    /**
     * Analyzes label frequency distribution across a collection of issues.
     * 
     * <p>Used for stratified splitting to identify rare labels (< 3 occurrences)
     * that should be forced into the training set.</p>
     * 
     * @param issueLabels map of issue number to normalized labels
     * @return map of label to frequency count
     */
    Map<String, Integer> analyzeLabelFrequency(Map<Integer, List<String>> issueLabels);
    
    /**
     * Identifies rare labels that should be handled specially in data splitting.
     * 
     * <p>Labels with fewer than the minimum occurrence threshold are considered
     * rare and typically forced into the training set to ensure representation.</p>
     * 
     * @param labelFrequency frequency distribution from analyzeLabelFrequency
     * @param minOccurrences minimum occurrences to not be considered rare (default: 3)
     * @return set of rare label names
     */
    Set<String> identifyRareLabels(Map<String, Integer> labelFrequency, int minOccurrences);
    
    /**
     * Validates that the service configuration is properly set up.
     * 
     * @return true if configuration is valid and service is ready
     */
    boolean isConfigurationValid();
    
    /**
     * Returns the current configuration used by this service.
     * 
     * @return classification configuration
     */
    ClassificationConfig getConfiguration();
    
    /**
     * Returns statistics about the normalization process for monitoring.
     * 
     * @return formatted string with normalization statistics
     */
    String getNormalizationStatistics();
}
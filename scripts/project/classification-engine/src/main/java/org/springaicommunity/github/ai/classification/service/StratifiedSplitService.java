package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.domain.DataSplit;
import org.springaicommunity.github.ai.collection.Issue;

import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Service interface for performing stratified train/test splits on GitHub issues.
 * 
 * <p>This service implements the Python stratified split algorithm that maintains
 * label distribution while ensuring rare labels (< 3 occurrences) are placed
 * in the training set for adequate representation.</p>
 * 
 * <p>Core functionality matches the Python stratified_split.py implementation:
 * <ul>
 *   <li>Identifies rare labels and forces them into training set</li>
 *   <li>Maintains approximately 80/20 train/test split ratio</li>
 *   <li>Ensures test set has representative distribution of each label</li>
 *   <li>Uses reproducible random seeding for consistent splits</li>
 * </ul></p>
 * 
 * <p>The algorithm uses a heuristic approach: if any label in an issue is rare,
 * the entire issue goes to training. Otherwise, issues are assigned to test set
 * until each label reaches ~20% of its total frequency.</p>
 */
public interface StratifiedSplitService {
    
    /**
     * Performs stratified split on normalized issues with default configuration.
     * 
     * <p>Uses default parameters from Python implementation:
     * <ul>
     *   <li>Random seed: 42 (for reproducibility)</li>
     *   <li>Test ratio: 0.2 (80/20 split)</li>
     *   <li>Rare label threshold: 3 occurrences</li>
     * </ul></p>
     * 
     * @param normalizedIssues issues with normalized labels ready for splitting
     * @return DataSplit containing train/test sets with metadata
     * @throws IllegalArgumentException if issues list is null or empty
     */
    DataSplit performStratifiedSplit(List<Issue> normalizedIssues);
    
    /**
     * Performs stratified split with custom configuration parameters.
     * 
     * @param normalizedIssues issues with normalized labels ready for splitting
     * @param testRatio desired test set ratio (e.g., 0.2 for 20% test set)
     * @param rareThreshold minimum occurrences for label to not be considered rare
     * @param randomSeed seed for reproducible random shuffling
     * @return DataSplit containing train/test sets with metadata
     * @throws IllegalArgumentException if parameters are invalid or issues empty
     */
    DataSplit performStratifiedSplit(List<Issue> normalizedIssues, 
                                   double testRatio, 
                                   int rareThreshold, 
                                   long randomSeed);
    
    /**
     * Analyzes label frequency distribution across all normalized issues.
     * 
     * <p>This method implements the Python Counter logic:
     * {@code label_counts_total = Counter(label for issue in issues for label in issue["normalized_labels"])}</p>
     * 
     * @param normalizedIssues issues with normalized labels
     * @return map of label to frequency count across all issues
     */
    Map<String, Integer> analyzeLabelFrequency(List<Issue> normalizedIssues);
    
    /**
     * Identifies rare labels that should be forced into training set.
     * 
     * <p>Implements Python logic: {@code rare_labels = {label for label, count in counts.items() if count < threshold}}</p>
     * 
     * @param labelFrequency frequency distribution from analyzeLabelFrequency
     * @param rareThreshold minimum occurrences to not be considered rare (default: 3)
     * @return set of rare label names that need special handling
     */
    Set<String> identifyRareLabels(Map<String, Integer> labelFrequency, int rareThreshold);
    
    /**
     * Validates that split maintains proper label distribution balance.
     * 
     * <p>Ensures:
     * <ul>
     *   <li>All rare labels appear in training set</li>
     *   <li>Test set has reasonable representation of each label</li>
     *   <li>Overall split ratio is close to target ratio</li>
     *   <li>No labels are completely missing from either set (except rares from test)</li>
     * </ul></p>
     * 
     * @param split the data split to validate
     * @param originalIssues the original issue list for comparison
     * @param targetTestRatio the intended test set ratio
     * @return true if split meets quality criteria
     */
    boolean validateSplitQuality(DataSplit split, List<Issue> originalIssues, double targetTestRatio);
    
    /**
     * Generates detailed statistics about the split distribution.
     * 
     * <p>Similar to Python script output showing:
     * <ul>
     *   <li>Train/test set sizes and ratios</li>
     *   <li>Label distribution in each set</li>
     *   <li>Rare label handling summary</li>
     *   <li>Split quality metrics</li>
     * </ul></p>
     * 
     * @param split the completed data split
     * @param originalIssues the original issue list
     * @return formatted statistics string for logging/reporting
     */
    String generateSplitStatistics(DataSplit split, List<Issue> originalIssues);
    
    /**
     * Calculates label distribution within a specific set of issues.
     * 
     * <p>Implements Python label_distribution() function:
     * {@code counter.update(issue["normalized_labels"]) for issue in issues}</p>
     * 
     * @param issues subset of issues (train or test set)
     * @return map of label to count within this specific set
     */
    Map<String, Integer> calculateSetLabelDistribution(List<Issue> issues);
    
    /**
     * Checks if the split algorithm configuration is valid.
     * 
     * @param testRatio test set ratio (must be between 0.1 and 0.9)
     * @param rareThreshold rare label threshold (must be >= 1)
     * @param randomSeed random seed for reproducibility
     * @return true if configuration parameters are valid
     */
    boolean isConfigurationValid(double testRatio, int rareThreshold, long randomSeed);
    
    /**
     * Returns algorithm statistics for monitoring and debugging.
     * 
     * @return formatted string with algorithm performance metrics
     */
    String getAlgorithmStatistics();
}
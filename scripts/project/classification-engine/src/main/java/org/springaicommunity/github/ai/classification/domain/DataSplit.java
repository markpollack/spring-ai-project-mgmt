package org.springaicommunity.github.ai.classification.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Collections;
import java.util.List;

/**
 * Represents a stratified train/test split of issues for evaluation.
 * 
 * <p>This record captures the result of stratified splitting, maintaining
 * label distribution across train and test sets while handling rare labels
 * appropriately (labels with < 3 occurrences go to training set).</p>
 * 
 * @param trainSet Issues assigned to training set
 * @param testSet Issues assigned to test set
 * @param splitRatio The ratio used for splitting (e.g., 0.8 for 80/20)
 * @param randomSeed Seed used for reproducible splitting
 * @param rareLabels Labels with < 3 occurrences (forced to training set)
 */
public record DataSplit(
    @JsonProperty("train_set") List<Integer> trainSet,
    @JsonProperty("test_set") List<Integer> testSet,
    @JsonProperty("split_ratio") double splitRatio,
    @JsonProperty("random_seed") long randomSeed,
    @JsonProperty("rare_labels") List<String> rareLabels
) {
    
    /**
     * Constructor with validation and immutable list creation.
     */
    @JsonCreator
    public DataSplit {
        if (splitRatio <= 0.0 || splitRatio >= 1.0) {
            throw new IllegalArgumentException("Split ratio must be between 0.0 and 1.0, got: " + splitRatio);
        }
        
        // Ensure immutable collections
        if (trainSet == null) {
            trainSet = Collections.emptyList();
        } else {
            trainSet = List.copyOf(trainSet);
        }
        
        if (testSet == null) {
            testSet = Collections.emptyList();
        } else {
            testSet = List.copyOf(testSet);
        }
        
        if (rareLabels == null) {
            rareLabels = Collections.emptyList();
        } else {
            rareLabels = List.copyOf(rareLabels);
        }
    }
    
    /**
     * Returns the total number of issues in the split.
     * 
     * @return train set size + test set size
     */
    public int getTotalIssues() {
        return trainSet.size() + testSet.size();
    }
    
    /**
     * Returns the actual train/test ratio achieved.
     * 
     * @return actual train size / total size
     */
    public double getActualTrainRatio() {
        int total = getTotalIssues();
        return total > 0 ? (double) trainSet.size() / total : 0.0;
    }
    
    /**
     * Returns the actual test ratio achieved.
     * 
     * @return actual test size / total size
     */
    public double getActualTestRatio() {
        int total = getTotalIssues();
        return total > 0 ? (double) testSet.size() / total : 0.0;
    }
    
    /**
     * Checks if this split is well-balanced (within 5% of target ratio).
     * 
     * @return true if actual ratio is within 5% of target
     */
    public boolean isWellBalanced() {
        double actualRatio = getActualTrainRatio();
        double difference = Math.abs(actualRatio - splitRatio);
        return difference <= 0.05; // 5% tolerance
    }
    
    /**
     * Returns statistics about the split.
     * 
     * @return formatted string with split information
     */
    public String getStatistics() {
        return String.format(
            "Split: %d train, %d test (%.1f%% / %.1f%%), %d rare labels, seed: %d",
            trainSet.size(), testSet.size(),
            getActualTrainRatio() * 100, getActualTestRatio() * 100,
            rareLabels.size(), randomSeed
        );
    }
    
    /**
     * Checks if an issue is in the training set.
     * 
     * @param issueNumber the issue number to check
     * @return true if in training set
     */
    public boolean isInTrainSet(int issueNumber) {
        return trainSet.contains(issueNumber);
    }
    
    /**
     * Checks if an issue is in the test set.
     * 
     * @param issueNumber the issue number to check
     * @return true if in test set
     */
    public boolean isInTestSet(int issueNumber) {
        return testSet.contains(issueNumber);
    }
}
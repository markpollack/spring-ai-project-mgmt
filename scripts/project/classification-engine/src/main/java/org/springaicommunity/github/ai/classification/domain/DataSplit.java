package org.springaicommunity.github.ai.classification.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Duration;
import java.time.Instant;
import java.util.Collections;
import java.util.List;
import java.util.Set;

/**
 * Represents a stratified train/test split of issues for evaluation.
 * 
 * <p>This record captures the result of stratified splitting, maintaining
 * label distribution across train and test sets while handling rare labels
 * appropriately (labels with < 3 occurrences go to training set).</p>
 * 
 * @param trainSet Issues assigned to training set
 * @param testSet Issues assigned to test set
 * @param splitRatio The ratio used for splitting (e.g., 0.2 for 20% test)
 * @param rareThreshold Threshold for rare label detection
 * @param randomSeed Seed used for reproducible splitting
 * @param totalIssues Total number of issues processed
 * @param rareLabels Labels with < threshold occurrences (forced to training set)
 * @param rareIssuesCount Number of issues forced to training due to rare labels
 * @param executionTime Time taken to perform the split
 * @param timestamp When the split was performed
 */
public record DataSplit(
    @JsonProperty("train_set") List<Integer> trainSet,
    @JsonProperty("test_set") List<Integer> testSet,
    @JsonProperty("split_ratio") double splitRatio,
    @JsonProperty("rare_threshold") int rareThreshold,
    @JsonProperty("random_seed") long randomSeed,
    @JsonProperty("total_issues") int totalIssues,
    @JsonProperty("rare_labels") Set<String> rareLabels,
    @JsonProperty("rare_issues_count") int rareIssuesCount,
    @JsonProperty("execution_time") Duration executionTime,
    @JsonProperty("timestamp") Instant timestamp
) {
    
    /**
     * Constructor with validation and immutable list creation.
     */
    @JsonCreator
    public DataSplit {
        if (splitRatio <= 0.0 || splitRatio >= 1.0) {
            throw new IllegalArgumentException("Split ratio must be between 0.0 and 1.0, got: " + splitRatio);
        }
        
        if (rareThreshold < 1) {
            throw new IllegalArgumentException("Rare threshold must be >= 1, got: " + rareThreshold);
        }
        
        if (totalIssues < 0) {
            throw new IllegalArgumentException("Total issues must be >= 0, got: " + totalIssues);
        }
        
        if (rareIssuesCount < 0) {
            throw new IllegalArgumentException("Rare issues count must be >= 0, got: " + rareIssuesCount);
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
            rareLabels = Collections.emptySet();
        } else {
            rareLabels = Set.copyOf(rareLabels);
        }
    }
    
    /**
     * Creates a new builder instance.
     * 
     * @return new builder for DataSplit
     */
    public static Builder builder() {
        return new Builder();
    }
    
    /**
     * Builder for creating DataSplit instances.
     */
    public static class Builder {
        private List<Integer> trainSet = Collections.emptyList();
        private List<Integer> testSet = Collections.emptyList();
        private double splitRatio = 0.2;
        private int rareThreshold = 3;
        private long randomSeed = 42L;
        private int totalIssues = 0;
        private Set<String> rareLabels = Collections.emptySet();
        private int rareIssuesCount = 0;
        private Duration executionTime = Duration.ZERO;
        private Instant timestamp = Instant.now();
        
        public Builder trainSet(List<Integer> trainSet) {
            this.trainSet = trainSet;
            return this;
        }
        
        public Builder testSet(List<Integer> testSet) {
            this.testSet = testSet;
            return this;
        }
        
        public Builder splitRatio(double splitRatio) {
            this.splitRatio = splitRatio;
            return this;
        }
        
        public Builder rareThreshold(int rareThreshold) {
            this.rareThreshold = rareThreshold;
            return this;
        }
        
        public Builder randomSeed(long randomSeed) {
            this.randomSeed = randomSeed;
            return this;
        }
        
        public Builder totalIssues(int totalIssues) {
            this.totalIssues = totalIssues;
            return this;
        }
        
        public Builder rareLabels(Set<String> rareLabels) {
            this.rareLabels = rareLabels;
            return this;
        }
        
        public Builder rareIssuesCount(int rareIssuesCount) {
            this.rareIssuesCount = rareIssuesCount;
            return this;
        }
        
        public Builder executionTime(Duration executionTime) {
            this.executionTime = executionTime;
            return this;
        }
        
        public Builder timestamp(Instant timestamp) {
            this.timestamp = timestamp;
            return this;
        }
        
        public DataSplit build() {
            return new DataSplit(trainSet, testSet, splitRatio, rareThreshold, randomSeed,
                               totalIssues, rareLabels, rareIssuesCount, executionTime, timestamp);
        }
    }
    
    /**
     * Returns the actual train/test ratio achieved.
     * 
     * @return actual train size / total size
     */
    public double getActualTrainRatio() {
        return totalIssues > 0 ? (double) trainSet.size() / totalIssues : 0.0;
    }
    
    /**
     * Returns the actual test ratio achieved.
     * 
     * @return actual test size / total size
     */
    public double getActualTestRatio() {
        return totalIssues > 0 ? (double) testSet.size() / totalIssues : 0.0;
    }
    
    /**
     * Checks if this split is well-balanced (within 5% of target ratio).
     * 
     * @return true if actual test ratio is within 5% of target
     */
    public boolean isWellBalanced() {
        double actualTestRatio = getActualTestRatio();
        double difference = Math.abs(actualTestRatio - splitRatio);
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
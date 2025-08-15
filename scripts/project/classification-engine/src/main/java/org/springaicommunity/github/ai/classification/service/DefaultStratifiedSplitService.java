package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.domain.DataSplit;
import org.springaicommunity.github.ai.collection.Issue;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/**
 * Default implementation of StratifiedSplitService.
 * 
 * <p>This service implements the exact Python stratified_split.py algorithm with proper
 * Spring integration, comprehensive statistics tracking, and thread-safe operation.</p>
 * 
 * <p>Algorithm matches Python implementation lines 80-100:
 * <ol>
 *   <li>Count label frequencies across all issues</li>
 *   <li>Identify rare labels (< threshold occurrences)</li>
 *   <li>Shuffle issues with reproducible random seed</li>
 *   <li>Apply heuristic: rare labels → train, others → test until 20% reached</li>
 * </ol></p>
 * 
 * <p>Thread-safe implementation suitable for concurrent use in multi-threaded
 * processing scenarios with comprehensive monitoring and debugging support.</p>
 */
@Service
public class DefaultStratifiedSplitService implements StratifiedSplitService {
    
    private static final Logger logger = LoggerFactory.getLogger(DefaultStratifiedSplitService.class);
    
    private final LabelNormalizationService labelNormalizationService;
    
    /**
     * Constructor with dependency injection.
     * 
     * @param labelNormalizationService service for normalizing issue labels
     */
    public DefaultStratifiedSplitService(LabelNormalizationService labelNormalizationService) {
        this.labelNormalizationService = Objects.requireNonNull(labelNormalizationService, 
                                                               "LabelNormalizationService cannot be null");
    }
    
    // Default configuration constants from Python implementation
    private static final double DEFAULT_TEST_RATIO = 0.2;
    private static final int DEFAULT_RARE_THRESHOLD = 3;
    private static final long DEFAULT_RANDOM_SEED = 42L;
    
    // Statistics tracking (thread-safe)
    private final AtomicLong totalSplitsPerformed = new AtomicLong(0);
    private final AtomicLong totalIssuesProcessed = new AtomicLong(0);
    private final AtomicLong totalRareLabelsFound = new AtomicLong(0);
    private final AtomicLong totalRareIssuesAssigned = new AtomicLong(0);
    
    @Override
    public DataSplit performStratifiedSplit(List<Issue> issues) {
        return performStratifiedSplit(issues, DEFAULT_TEST_RATIO, 
                                    DEFAULT_RARE_THRESHOLD, DEFAULT_RANDOM_SEED);
    }
    
    @Override
    public DataSplit performStratifiedSplit(List<Issue> issues, 
                                          double testRatio, 
                                          int rareThreshold, 
                                          long randomSeed) {
        if (issues == null || issues.isEmpty()) {
            throw new IllegalArgumentException("Issues list cannot be null or empty");
        }
        
        if (!isConfigurationValid(testRatio, rareThreshold, randomSeed)) {
            throw new IllegalArgumentException(
                String.format("Invalid configuration: testRatio=%.2f, rareThreshold=%d, randomSeed=%d", 
                            testRatio, rareThreshold, randomSeed));
        }
        
        totalSplitsPerformed.incrementAndGet();
        totalIssuesProcessed.addAndGet(issues.size());
        
        Instant startTime = Instant.now();
        
        logger.info("Starting stratified split: {} issues, testRatio={}, rareThreshold={}, seed={}", 
                   issues.size(), testRatio, rareThreshold, randomSeed);
        
        // Step 1: Count label frequencies (Python lines 81-82)
        Map<String, Integer> labelCounts = analyzeLabelFrequency(issues);
        Set<String> rareLabels = identifyRareLabels(labelCounts, rareThreshold);
        
        totalRareLabelsFound.addAndGet(rareLabels.size());
        
        logger.debug("Found {} unique labels, {} rare labels: {}", 
                    labelCounts.size(), rareLabels.size(), rareLabels);
        
        // Step 2: Shuffle issues with reproducible seed (Python lines 88-89)
        List<Issue> shuffledIssues = new ArrayList<>(issues);
        Random random = new Random(randomSeed);
        Collections.shuffle(shuffledIssues, random);
        
        // Step 3: Perform heuristic split (Python lines 91-100)
        List<Issue> trainSet = new ArrayList<>();
        List<Issue> testSet = new ArrayList<>();
        Map<String, Integer> testLabelCounts = new HashMap<>();
        
        int rareIssuesCount = 0;
        
        for (Issue issue : shuffledIssues) {
            // Normalize labels on the fly using LabelNormalizationService
            List<String> rawLabelNames = issue.labels().stream()
                .map(label -> label.name())
                .collect(Collectors.toList());
            
            List<String> normalizedLabels = labelNormalizationService.normalizeLabels(rawLabelNames);
            
            if (normalizedLabels.isEmpty()) {
                // Issues without normalized labels go to training set
                trainSet.add(issue);
                continue;
            }
            
            // Python logic: if any(label in rare_labels for label in labels)
            boolean hasRareLabel = normalizedLabels.stream().anyMatch(rareLabels::contains);
            
            if (hasRareLabel) {
                trainSet.add(issue);
                rareIssuesCount++;
                continue;
            }
            
            // Python logic: if all(test_label_counts[label] < (testRatio * total_count) for label in labels)
            boolean canGoToTest = normalizedLabels.stream().allMatch(label -> {
                int currentTestCount = testLabelCounts.getOrDefault(label, 0);
                int totalCount = labelCounts.getOrDefault(label, 0);
                return currentTestCount < (testRatio * totalCount);
            });
            
            if (canGoToTest) {
                testSet.add(issue);
                // Update test label counts (Python: test_label_counts.update(labels))
                for (String label : normalizedLabels) {
                    testLabelCounts.merge(label, 1, Integer::sum);
                }
            } else {
                trainSet.add(issue);
            }
        }
        
        totalRareIssuesAssigned.addAndGet(rareIssuesCount);
        
        Instant endTime = Instant.now();
        
        // Create DataSplit result with comprehensive metadata
        DataSplit result = DataSplit.builder()
            .trainSet(trainSet.stream().map(Issue::number).collect(Collectors.toList()))
            .testSet(testSet.stream().map(Issue::number).collect(Collectors.toList()))
            .splitRatio(testRatio)
            .rareThreshold(rareThreshold)
            .randomSeed(randomSeed)
            .totalIssues(issues.size())
            .rareLabels(rareLabels)
            .rareIssuesCount(rareIssuesCount)
            .executionTime(java.time.Duration.between(startTime, endTime))
            .timestamp(endTime)
            .build();
        
        logger.info("Stratified split completed: train={}, test={} ({}%), {} rare issues, took {}ms", 
                   trainSet.size(), testSet.size(), 
                   String.format("%.1f", (testSet.size() * 100.0) / issues.size()),
                   rareIssuesCount, 
                   java.time.Duration.between(startTime, endTime).toMillis());
        
        return result;
    }
    
    @Override
    public Map<String, Integer> analyzeLabelFrequency(List<Issue> issues) {
        if (issues == null || issues.isEmpty()) {
            return Collections.emptyMap();
        }
        
        // Python: Counter(label for issue in issues for label in issue["normalized_labels"])
        Map<String, Integer> frequency = new HashMap<>();
        
        for (Issue issue : issues) {
            // Extract raw label names and normalize them
            List<String> rawLabelNames = issue.labels().stream()
                .map(label -> label.name())
                .collect(Collectors.toList());
            
            List<String> normalizedLabels = labelNormalizationService.normalizeLabels(rawLabelNames);
            
            for (String label : normalizedLabels) {
                frequency.merge(label, 1, Integer::sum);
            }
        }
        
        logger.debug("Analyzed label frequency for {} issues, found {} unique labels", 
                    issues.size(), frequency.size());
        
        return frequency;
    }
    
    @Override
    public Set<String> identifyRareLabels(Map<String, Integer> labelFrequency, int rareThreshold) {
        if (labelFrequency == null || labelFrequency.isEmpty()) {
            return Collections.emptySet();
        }
        
        // Python: {label for label, count in counts.items() if count < threshold}
        Set<String> rareLabels = labelFrequency.entrySet().stream()
            .filter(entry -> entry.getValue() < rareThreshold)
            .map(Map.Entry::getKey)
            .collect(Collectors.toSet());
        
        logger.debug("Identified {} rare labels (< {} occurrences) out of {} total labels",
                    rareLabels.size(), rareThreshold, labelFrequency.size());
        
        return rareLabels;
    }
    
    @Override
    public boolean validateSplitQuality(DataSplit split, List<Issue> originalIssues, double targetTestRatio) {
        if (split == null || originalIssues == null) {
            return false;
        }
        
        try {
            // Check basic split properties
            int totalIssues = split.totalIssues();
            int trainSize = split.trainSet().size();
            int testSize = split.testSet().size();
            
            // Verify sizes match
            if (trainSize + testSize != totalIssues) {
                logger.warn("Split size mismatch: train={} + test={} != total={}", 
                           trainSize, testSize, totalIssues);
                return false;
            }
            
            // Check if test ratio is reasonable (within 10% of target)
            double actualTestRatio = (double) testSize / totalIssues;
            double ratioDifference = Math.abs(actualTestRatio - targetTestRatio);
            if (ratioDifference > 0.1) {
                logger.warn("Test ratio too far from target: actual={:.3f}, target={:.3f}, diff={:.3f}",
                           actualTestRatio, targetTestRatio, ratioDifference);
                return false;
            }
            
            // Verify no duplicate issues between sets
            Set<Integer> trainIssues = new HashSet<>(split.trainSet());
            Set<Integer> testIssues = new HashSet<>(split.testSet());
            trainIssues.retainAll(testIssues);
            if (!trainIssues.isEmpty()) {
                logger.warn("Found {} overlapping issues between train and test sets", trainIssues.size());
                return false;
            }
            
            logger.debug("Split quality validation passed: train={}, test={}, ratio={:.3f}", 
                        trainSize, testSize, actualTestRatio);
            
            return true;
            
        } catch (Exception e) {
            logger.error("Split quality validation failed", e);
            return false;
        }
    }
    
    @Override
    public String generateSplitStatistics(DataSplit split, List<Issue> originalIssues) {
        if (split == null) {
            return "No split data available";
        }
        
        StringBuilder stats = new StringBuilder();
        stats.append("=== Stratified Split Results ===\n");
        
        // Basic statistics
        int totalIssues = split.totalIssues();
        int trainSize = split.trainSet().size();
        int testSize = split.testSet().size();
        double actualTestRatio = (double) testSize / totalIssues;
        
        stats.append(String.format("Total issues: %d\n", totalIssues));
        stats.append(String.format("Train set size: %d\n", trainSize));
        stats.append(String.format("Test set size: %d\n", testSize));
        stats.append(String.format("Split ratio: %d/%d (%.1f%%/%.1f%%)\n", 
                                  trainSize, testSize, 
                                  (trainSize * 100.0) / totalIssues, 
                                  (testSize * 100.0) / totalIssues));
        
        // Rare label statistics
        Set<String> rareLabels = split.rareLabels();
        int rareIssuesCount = split.rareIssuesCount();
        stats.append(String.format("Rare labels found: %d (%s)\n", 
                                  rareLabels.size(), 
                                  rareLabels.stream().sorted().collect(Collectors.joining(", "))));
        stats.append(String.format("Issues with rare labels (forced to train): %d\n", rareIssuesCount));
        
        // Performance statistics
        if (split.executionTime() != null) {
            stats.append(String.format("Execution time: %d ms\n", split.executionTime().toMillis()));
        }
        
        // Configuration
        stats.append(String.format("Configuration: testRatio=%.2f, rareThreshold=%d, seed: %d\n",
                                  split.splitRatio(), split.rareThreshold(), split.randomSeed()));
        
        return stats.toString();
    }
    
    @Override
    public Map<String, Integer> calculateSetLabelDistribution(List<Issue> issues) {
        if (issues == null || issues.isEmpty()) {
            return Collections.emptyMap();
        }
        
        // Python: counter.update(issue["normalized_labels"]) for issue in issues
        Map<String, Integer> distribution = new HashMap<>();
        
        for (Issue issue : issues) {
            // Extract raw label names and normalize them
            List<String> rawLabelNames = issue.labels().stream()
                .map(label -> label.name())
                .collect(Collectors.toList());
            
            List<String> normalizedLabels = labelNormalizationService.normalizeLabels(rawLabelNames);
            
            for (String label : normalizedLabels) {
                distribution.merge(label, 1, Integer::sum);
            }
        }
        
        return distribution;
    }
    
    @Override
    public boolean isConfigurationValid(double testRatio, int rareThreshold, long randomSeed) {
        if (testRatio <= 0.0 || testRatio >= 1.0) {
            logger.warn("Invalid test ratio: {} (must be between 0.0 and 1.0)", testRatio);
            return false;
        }
        
        if (rareThreshold < 1) {
            logger.warn("Invalid rare threshold: {} (must be >= 1)", rareThreshold);
            return false;
        }
        
        // Random seed can be any long value, no validation needed
        
        return true;
    }
    
    @Override
    public String getAlgorithmStatistics() {
        return String.format(
            "Stratified Split Algorithm Statistics: %d splits performed, %d issues processed, " +
            "%d rare labels found, %d rare issues assigned to training",
            totalSplitsPerformed.get(),
            totalIssuesProcessed.get(), 
            totalRareLabelsFound.get(),
            totalRareIssuesAssigned.get()
        );
    }
}
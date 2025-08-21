package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springaicommunity.github.ai.classification.config.ClassificationConfiguration;
import org.springaicommunity.github.ai.classification.domain.IssueData;
import org.springframework.beans.factory.annotation.Autowired;

import java.io.File;
import java.io.IOException;
import java.time.Duration;
import java.util.*;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * BatchFailureAnalysisTest identifies patterns in failed vs successful batches
 * to understand why 26/111 issues are missing from our classification results.
 * 
 * Current Status: 85/111 issues classified (76.6% coverage)
 * Goal: Identify root causes of missing 26 issues
 */
@SpringJUnitConfig(classes = {ClassificationConfiguration.class})
public class BatchFailureAnalysisTest {
    
    private static final Logger logger = LoggerFactory.getLogger(BatchFailureAnalysisTest.class);
    
    @Autowired
    private ObjectMapper objectMapper;
    
    // File paths for analysis
    private static final String PREDICTIONS_FILE = "java_small_batch_classification_2025-08-18_17-34-22.json";
    private static final String DEDUP_PREDICTIONS_FILE = "java_small_batch_classification_2025-08-18_17-34-22_dedup.json";
    private static final String TEST_SET_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json";
    
    private List<IssueData> allIssueDatas;
    private List<Integer> classifiedIssues;
    private List<Integer> missingIssues;
    
    @BeforeEach
    void setUp() throws IOException {
        loadTestData();
    }
    
    @Test
    @DisplayName("Analyze batch failure patterns and identify missing issues")
    void analyzeBatchFailurePatterns() throws IOException {
        logger.info("=== BATCH FAILURE PATTERN ANALYSIS ===");
        logger.info("📊 Total test issues: {}", allIssueDatas.size());
        logger.info("📊 Classified issues: {}", classifiedIssues.size());
        logger.info("📊 Missing issues: {}", missingIssues.size());
        logger.info("📊 Coverage: {:.1f}%", (double) classifiedIssues.size() / allIssueDatas.size() * 100);
        
        // Analysis 1: Issue size correlation
        analyzeIssueSizeCorrelation();
        
        // Analysis 2: Batch composition analysis
        analyzeBatchComposition();
        
        // Analysis 3: Missing issue characteristics
        analyzeMissingIssueCharacteristics();
        
        // Analysis 4: Duplicate pattern analysis
        analyzeDuplicatePatterns();
        
        // Analysis 5: Size distribution analysis
        analyzeSizeDistribution();
        
        logger.info("✅ Batch failure analysis complete");
    }
    
    
    
    /**
     * Analyze correlation between issue size and classification success.
     */
    private void analyzeIssueSizeCorrelation() {
        logger.info("=== ISSUE SIZE CORRELATION ANALYSIS ===");
        
        Map<Integer, Integer> classifiedSizes = new HashMap<>();
        Map<Integer, Integer> missingSizes = new HashMap<>();
        
        // Calculate sizes for classified issues
        for (Integer issueNum : classifiedIssues) {
            IssueData issue = findIssueByNumber(issueNum);
            if (issue != null) {
                int size = calculateIssueSize(issue);
                classifiedSizes.put(issueNum, size);
            }
        }
        
        // Calculate sizes for missing issues
        for (Integer issueNum : missingIssues) {
            IssueData issue = findIssueByNumber(issueNum);
            if (issue != null) {
                int size = calculateIssueSize(issue);
                missingSizes.put(issueNum, size);
            }
        }
        
        // Statistical analysis
        double avgClassifiedSize = classifiedSizes.values().stream()
            .mapToInt(Integer::intValue)
            .average()
            .orElse(0.0);
            
        double avgMissingSize = missingSizes.values().stream()
            .mapToInt(Integer::intValue)
            .average()
            .orElse(0.0);
        
        logger.info("📊 Average classified issue size: {:.0f} chars", avgClassifiedSize);
        logger.info("📊 Average missing issue size: {:.0f} chars", avgMissingSize);
        logger.info("📊 Size difference: {:.0f} chars ({:.1f}%)", 
            avgMissingSize - avgClassifiedSize, 
            (avgMissingSize - avgClassifiedSize) / avgClassifiedSize * 100);
        
        // Size distribution analysis
        analyzeSizeDistribution("Classified", classifiedSizes.values());
        analyzeSizeDistribution("Missing", missingSizes.values());
    }
    
    /**
     * Analyze batch composition to understand successful vs failed batch patterns.
     */
    private void analyzeBatchComposition() throws IOException {
        logger.info("=== BATCH COMPOSITION ANALYSIS ===");
        
        // Simulate batch creation (5 issues per batch like our test)
        int batchSize = 5;
        List<List<IssueData>> batches = createBatches(allIssueDatas, batchSize);
        
        logger.info("📊 Total batches created: {}", batches.size());
        
        for (int i = 0; i < batches.size(); i++) {
            List<IssueData> batch = batches.get(i);
            
            // Count how many issues from this batch were successfully classified
            int successCount = 0;
            int totalPromptSize = 0;
            List<Integer> batchIssueNumbers = new ArrayList<>();
            
            for (IssueData issue : batch) {
                batchIssueNumbers.add(issue.issueNumber());
                totalPromptSize += calculateIssueSize(issue);
                
                if (classifiedIssues.contains(issue.issueNumber())) {
                    successCount++;
                }
            }
            
            double batchSuccessRate = (double) successCount / batch.size() * 100;
            
            logger.info("📊 Batch {}: {}/{} success ({:.1f}%), prompt ~{}KB, issues: {}", 
                i + 1, successCount, batch.size(), batchSuccessRate, 
                totalPromptSize / 1024, batchIssueNumbers);
            
            if (batchSuccessRate < 50) {
                logger.warn("⚠️ Poor performing batch {} - investigating...", i + 1);
                investigatePoorPerformingBatch(batch, i + 1);
            }
        }
    }
    
    /**
     * Analyze characteristics of missing issues to identify patterns.
     */
    private void analyzeMissingIssueCharacteristics() {
        logger.info("=== MISSING ISSUE CHARACTERISTICS ANALYSIS ===");
        
        Map<String, Integer> labelCounts = new HashMap<>();
        Map<String, Integer> authorCounts = new HashMap<>();
        int totalLabels = 0;
        
        for (Integer issueNum : missingIssues) {
            IssueData issue = findIssueByNumber(issueNum);
            if (issue != null) {
                // Analyze labels
                for (String label : issue.labels()) {
                    labelCounts.put(label, labelCounts.getOrDefault(label, 0) + 1);
                    totalLabels++;
                }
                
                // Analyze authors
                authorCounts.put(issue.author(), authorCounts.getOrDefault(issue.author(), 0) + 1);
            }
        }
        
        logger.info("📊 Missing issues total labels: {}", totalLabels);
        logger.info("📊 Average labels per missing issue: {:.1f}", 
            (double) totalLabels / missingIssues.size());
        
        // Top labels in missing issues
        labelCounts.entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .limit(10)
            .forEach(entry -> 
                logger.info("📊 Missing issue label: {} ({})", entry.getKey(), entry.getValue()));
        
        // Top authors with missing issues
        authorCounts.entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .limit(5)
            .forEach(entry -> 
                logger.info("📊 Missing issue author: {} ({})", entry.getKey(), entry.getValue()));
    }
    
    /**
     * Analyze duplicate patterns to understand retry behavior.
     */
    private void analyzeDuplicatePatterns() throws IOException {
        logger.info("=== DUPLICATE PATTERN ANALYSIS ===");
        
        // Load raw predictions (with duplicates)
        JsonNode rawPredictions = loadPredictions(PREDICTIONS_FILE);
        JsonNode dedupPredictions = loadPredictions(DEDUP_PREDICTIONS_FILE);
        
        logger.info("📊 Raw predictions: {}", rawPredictions.size());
        logger.info("📊 Deduplicated predictions: {}", dedupPredictions.size());
        logger.info("📊 Duplicates removed: {}", rawPredictions.size() - dedupPredictions.size());
        
        // Find duplicate issue numbers
        Map<Integer, Integer> issueCountMap = new HashMap<>();
        for (JsonNode pred : rawPredictions) {
            int issueNum = pred.get("issue_number").asInt();
            issueCountMap.put(issueNum, issueCountMap.getOrDefault(issueNum, 0) + 1);
        }
        
        // Analyze duplicates
        List<Map.Entry<Integer, Integer>> duplicates = issueCountMap.entrySet().stream()
            .filter(entry -> entry.getValue() > 1)
            .sorted(Map.Entry.<Integer, Integer>comparingByValue().reversed())
            .collect(Collectors.toList());
        
        logger.info("📊 Issues with duplicates: {}", duplicates.size());
        for (Map.Entry<Integer, Integer> duplicate : duplicates) {
            logger.info("📊 Issue #{} appeared {} times", duplicate.getKey(), duplicate.getValue());
        }
        
        // This suggests retry logic may be creating duplicates - investigate batch boundaries
    }
    
    /**
     * Analyze size distribution of classified vs missing issues.
     */
    private void analyzeSizeDistribution() {
        logger.info("=== SIZE DISTRIBUTION ANALYSIS ===");
        
        // Test different batch sizes with prompt generation
        int[] batchSizes = {1, 2, 3, 5, 10};
        
        for (int batchSize : batchSizes) {
            List<IssueData> testBatch = allIssueDatas.subList(0, Math.min(batchSize, allIssueDatas.size()));
            // String prompt = promptService.generatePrompt(testBatch);
            
            logger.info("📊 Batch size {}: total issue size {}KB", 
                batchSize, testBatch.stream().mapToInt(this::calculateIssueSize).sum() / 1024);
        }
        
        // Test with problematic large issues
        List<IssueData> largeIssues = missingIssues.stream()
            .map(this::findIssueByNumber)
            .filter(Objects::nonNull)
            .sorted((a, b) -> Integer.compare(calculateIssueSize(b), calculateIssueSize(a)))
            .limit(5)
            .collect(Collectors.toList());
        
        logger.info("📊 Testing large missing issues:");
        for (IssueData issue : largeIssues) {
            int size = calculateIssueSize(issue);
            // String prompt = promptService.generatePrompt(List.of(issue));
            logger.info("📊 Issue #{}: {}KB issue, labels: {}", 
                issue.issueNumber(), size / 1024, issue.labels().size());
        }
    }
    
    /**
     * Investigate poor performing batches in detail.
     */
    private void investigatePoorPerformingBatch(List<IssueData> batch, int batchNumber) {
        logger.info("🔍 Investigating poor performing batch {}", batchNumber);
        
        for (IssueData issue : batch) {
            int size = calculateIssueSize(issue);
            boolean wasClassified = classifiedIssues.contains(issue.issueNumber());
            
            logger.info("🔍   Issue #{}: {}KB, classified: {}, labels: {}", 
                issue.issueNumber(), size / 1024, wasClassified, issue.labels().size());
        }
        
        // Calculate total batch issue size
        int totalBatchSize = batch.stream().mapToInt(this::calculateIssueSize).sum();
        logger.info("🔍   Total batch size: {}KB", totalBatchSize / 1024);
        
        if (totalBatchSize > 100000) { // 100KB threshold for issue content
            logger.warn("⚠️   Batch {} exceeds 100KB issue threshold - likely cause of failure", batchNumber);
        }
    }
    
    /**
     * Helper methods for data analysis
     */
    private void loadTestData() throws IOException {
        // Load all test issues
        File testSetFile = new File(TEST_SET_PATH);
        JsonNode testSetArray = objectMapper.readTree(testSetFile);
        
        allIssueDatas = new ArrayList<>();
        for (JsonNode issueNode : testSetArray) {
            IssueData issue = new IssueData(
                issueNode.get("issue_number").asInt(),
                issueNode.get("title").asText(),
                issueNode.get("body").asText(),
                issueNode.get("author").asText(),
                objectMapper.convertValue(issueNode.get("labels"), Set.class)
            );
            allIssueDatas.add(issue);
        }
        
        // Load classified issue numbers
        JsonNode predictions = loadPredictions(DEDUP_PREDICTIONS_FILE);
        classifiedIssues = new ArrayList<>();
        for (JsonNode pred : predictions) {
            classifiedIssues.add(pred.get("issue_number").asInt());
        }
        
        // Calculate missing issues
        Set<Integer> allIssueNumbers = allIssueDatas.stream()
            .map(IssueData::issueNumber)
            .collect(Collectors.toSet());
        
        missingIssues = allIssueNumbers.stream()
            .filter(num -> !classifiedIssues.contains(num))
            .sorted()
            .collect(Collectors.toList());
    }
    
    private JsonNode loadPredictions(String filename) throws IOException {
        File file = new File(filename);
        if (!file.exists()) {
            logger.warn("Predictions file not found: {}", filename);
            return objectMapper.createArrayNode();
        }
        return objectMapper.readTree(file);
    }
    
    private IssueData findIssueByNumber(int issueNumber) {
        return allIssueDatas.stream()
            .filter(issue -> issue.issueNumber() == issueNumber)
            .findFirst()
            .orElse(null);
    }
    
    private int calculateIssueSize(IssueData issue) {
        return (issue.title().length() + issue.body().length());
    }
    
    private void analyzeSizeDistribution(String category, Collection<Integer> sizes) {
        if (sizes.isEmpty()) return;
        
        List<Integer> sortedSizes = sizes.stream()
            .sorted()
            .collect(Collectors.toList());
        
        int min = sortedSizes.get(0);
        int max = sortedSizes.get(sortedSizes.size() - 1);
        int median = sortedSizes.get(sortedSizes.size() / 2);
        
        logger.info("📊 {} size distribution: min={}chars, median={}chars, max={}chars", 
            category, min, median, max);
    }
    
    private List<List<IssueData>> createBatches(List<IssueData> issues, int batchSize) {
        List<List<IssueData>> batches = new ArrayList<>();
        for (int i = 0; i < issues.size(); i += batchSize) {
            int end = Math.min(i + batchSize, issues.size());
            batches.add(new ArrayList<>(issues.subList(i, end)));
        }
        return batches;
    }
    
    private List<IssueData> getMissingIssuesSubset(int count) {
        return missingIssues.stream()
            .limit(count)
            .map(this::findIssueByNumber)
            .filter(Objects::nonNull)
            .collect(Collectors.toList());
    }
}
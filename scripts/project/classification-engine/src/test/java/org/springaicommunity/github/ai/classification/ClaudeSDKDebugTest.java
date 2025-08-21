package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springaicommunity.github.ai.classification.config.ClassificationConfiguration;
import org.springaicommunity.github.ai.classification.domain.IssueData;
import org.springaicommunity.github.ai.classification.service.DebugClaudeCodeWrapperService;

import java.io.File;
import java.io.IOException;
import java.time.Duration;
import java.util.*;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.*;

/**
 * Claude SDK Debug Test - Phase 2.1 of debugging plan
 * 
 * Investigates why specific batches (5, 10, 11, 15, 22, 23) failed completely
 * while others succeeded perfectly. This suggests SDK or API issues with 
 * certain content types or issue combinations.
 * 
 * Key Findings from Phase 1:
 * - Failed batches: 0% success rate, smaller/different content
 * - Successful batches: 100% success rate, normal content
 * - Pattern suggests systematic content-related failures
 */
@SpringJUnitConfig(classes = {ClassificationConfiguration.class})
@DisplayName("Phase 2.1: Claude SDK Debug Test")
public class ClaudeSDKDebugTest {
    
    private static final Logger logger = LoggerFactory.getLogger(ClaudeSDKDebugTest.class);
    
    @Autowired
    private ObjectMapper objectMapper;
    
    private DebugClaudeCodeWrapperService debugClaudeService;
    
    // Failed batch numbers identified in Phase 1
    private static final int[] FAILED_BATCHES = {5, 10, 11, 15, 22, 23};
    private static final int[] SUCCESSFUL_BATCHES = {1, 2, 3, 4, 6, 7, 8, 9, 12, 13, 14, 16, 17, 18, 19, 20, 21};
    
    private static final String TEST_SET_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json";
    
    private List<IssueData> allTestIssues;
    
    @BeforeEach
    void setUp() throws IOException {
        loadTestData();
        
        // Create debug service manually since it's not in ClassificationConfiguration
        debugClaudeService = new DebugClaudeCodeWrapperService(objectMapper);
    }
    
    @Test
    @DisplayName("Test Claude SDK with failed batch patterns vs successful patterns")
    void testFailedVsSuccessfulBatchPatterns() throws IOException {
        logger.info("=== CLAUDE SDK BATCH PATTERN DEBUG ===");
        logger.info("🔍 Testing why batches {} failed while others succeeded", Arrays.toString(FAILED_BATCHES));
        
        // Test a few failed batches with the debug service
        testSpecificFailedBatches();
        
        // Test a few successful batches for comparison
        testSpecificSuccessfulBatches();
        
        // Test individual issues from failed batches
        testIndividualIssuesFromFailedBatches();
        
        // Get final debug statistics
        DebugClaudeCodeWrapperService.DebugStats finalStats = debugClaudeService.getDebugStats();
        logger.info("📊 Final Debug Stats: {}", finalStats);
        
        // Log conclusions
        logDebugConclusions(finalStats);
    }
    
    /**
     * Test specific failed batches to understand why they fail
     */
    private void testSpecificFailedBatches() {
        logger.info("=== TESTING FAILED BATCHES ===");
        
        // Test first 3 failed batches to identify patterns
        int[] testBatches = {5, 10, 11};
        
        for (int batchNum : testBatches) {
            logger.info("🔍 Testing failed batch {}", batchNum);
            
            // Recreate the exact batch that failed
            List<IssueData> failedBatch = recreateBatch(batchNum, 5);
            
            if (failedBatch.isEmpty()) {
                logger.warn("⚠️ Could not recreate batch {}", batchNum);
                continue;
            }
            
            logger.info("🔍 Batch {} contains {} issues:", batchNum, failedBatch.size());
            for (IssueData issue : failedBatch) {
                logger.info("🔍   Issue #{}: {}KB, labels: {}", 
                    issue.issueNumber(), issue.getTextSize() / 1024, issue.labels().size());
            }
            
            // Create a simple prompt for testing
            String testPrompt = createSimplePrompt(failedBatch);
            logger.info("🔍 Test prompt size: {}KB", testPrompt.length() / 1024);
            
            // Test with Claude SDK
            try {
                DebugClaudeCodeWrapperService.ClassificationAnalysisResult result = 
                    debugClaudeService.analyzeFromText(testPrompt, Duration.ofMinutes(2), "sonnet");
                
                if (result.isSuccess()) {
                    logger.info("✅ Batch {} SUCCEEDED with debug service (unexpected!)", batchNum);
                } else {
                    logger.warn("❌ Batch {} FAILED with debug service: {}", batchNum, result.getError());
                }
                
            } catch (Exception e) {
                logger.error("💥 Batch {} threw exception: {}", batchNum, e.getMessage());
            }
            
            // Add delay between tests to avoid rate limiting
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }
    
    /**
     * Test successful batches for comparison
     */
    private void testSpecificSuccessfulBatches() {
        logger.info("=== TESTING SUCCESSFUL BATCHES (for comparison) ===");
        
        // Test first 2 successful batches
        int[] testBatches = {1, 2};
        
        for (int batchNum : testBatches) {
            logger.info("🔍 Testing successful batch {}", batchNum);
            
            List<IssueData> successfulBatch = recreateBatch(batchNum, 5);
            
            if (successfulBatch.isEmpty()) {
                logger.warn("⚠️ Could not recreate batch {}", batchNum);
                continue;
            }
            
            logger.info("🔍 Batch {} contains {} issues:", batchNum, successfulBatch.size());
            for (IssueData issue : successfulBatch) {
                logger.info("🔍   Issue #{}: {}KB, labels: {}", 
                    issue.issueNumber(), issue.getTextSize() / 1024, issue.labels().size());
            }
            
            String testPrompt = createSimplePrompt(successfulBatch);
            logger.info("🔍 Test prompt size: {}KB", testPrompt.length() / 1024);
            
            try {
                DebugClaudeCodeWrapperService.ClassificationAnalysisResult result = 
                    debugClaudeService.analyzeFromText(testPrompt, Duration.ofMinutes(2), "sonnet");
                
                if (result.isSuccess()) {
                    logger.info("✅ Batch {} SUCCEEDED with debug service (expected)", batchNum);
                } else {
                    logger.warn("❌ Batch {} FAILED with debug service (unexpected!): {}", batchNum, result.getError());
                }
                
            } catch (Exception e) {
                logger.error("💥 Batch {} threw exception: {}", batchNum, e.getMessage());
            }
            
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }
    
    /**
     * Test individual issues from failed batches to narrow down the problem
     */
    private void testIndividualIssuesFromFailedBatches() {
        logger.info("=== TESTING INDIVIDUAL ISSUES FROM FAILED BATCHES ===");
        
        // Get a few specific issues from failed batch 5 (smallest issues that failed)
        List<IssueData> batch5 = recreateBatch(5, 5);
        
        if (!batch5.isEmpty()) {
            IssueData testIssue = batch5.get(0); // Test just the first issue
            logger.info("🔍 Testing individual issue #{} from failed batch 5", testIssue.issueNumber());
            
            String singleIssuePrompt = createSimplePrompt(List.of(testIssue));
            logger.info("🔍 Single issue prompt size: {}KB", singleIssuePrompt.length() / 1024);
            
            try {
                DebugClaudeCodeWrapperService.ClassificationAnalysisResult result = 
                    debugClaudeService.analyzeFromText(singleIssuePrompt, Duration.ofMinutes(2), "sonnet");
                
                if (result.isSuccess()) {
                    logger.info("✅ Individual issue #{} SUCCEEDED - problem is batch-level", testIssue.issueNumber());
                } else {
                    logger.warn("❌ Individual issue #{} FAILED - problem is issue-level: {}", 
                        testIssue.issueNumber(), result.getError());
                }
                
            } catch (Exception e) {
                logger.error("💥 Individual issue #{} threw exception: {}", testIssue.issueNumber(), e.getMessage());
            }
        }
    }
    
    /**
     * Recreate a specific batch from the original test
     */
    private List<IssueData> recreateBatch(int batchNumber, int batchSize) {
        int startIdx = (batchNumber - 1) * batchSize;
        int endIdx = Math.min(startIdx + batchSize, allTestIssues.size());
        
        if (startIdx >= allTestIssues.size()) {
            return List.of();
        }
        
        return new ArrayList<>(allTestIssues.subList(startIdx, endIdx));
    }
    
    /**
     * Create a simple prompt for testing (not the full classification prompt)
     */
    private String createSimplePrompt(List<IssueData> issues) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("Please analyze these GitHub issues and classify them:\n\n");
        
        for (IssueData issue : issues) {
            prompt.append("Issue #").append(issue.issueNumber()).append("\n");
            prompt.append("Title: ").append(issue.getNormalizedTitle()).append("\n");
            prompt.append("Body: ").append(issue.getNormalizedBody().length() > 1000 ? 
                issue.getNormalizedBody().substring(0, 1000) + "..." : issue.getNormalizedBody()).append("\n");
            prompt.append("Current Labels: ").append(issue.getSafeLabels()).append("\n\n");
        }
        
        prompt.append("Please respond with a simple JSON array containing classifications for each issue.");
        
        return prompt.toString();
    }
    
    /**
     * Log debug conclusions based on test results
     */
    private void logDebugConclusions(DebugClaudeCodeWrapperService.DebugStats stats) {
        logger.info("=== CLAUDE SDK DEBUG CONCLUSIONS ===");
        
        double successRate = stats.getSuccessRate();
        logger.info("📊 Overall SDK Success Rate: {:.1f}%", successRate);
        
        if (successRate < 50) {
            logger.error("🔴 MAJOR SDK ISSUE: Success rate below 50% - SDK has fundamental problems");
        } else if (successRate < 80) {
            logger.warn("🟡 SDK RELIABILITY ISSUE: Success rate below 80% - some systematic failures");
        } else {
            logger.info("✅ SDK WORKING: Success rate above 80% - isolated failures only");
        }
        
        // Analyze error patterns
        Map<String, Integer> errorCounts = stats.getErrorCounts();
        if (!errorCounts.isEmpty()) {
            logger.info("📊 Error Pattern Analysis:");
            errorCounts.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .forEach(entry -> 
                    logger.info("📊   {}: {} occurrences", entry.getKey(), entry.getValue()));
        }
        
        // Response time analysis
        long avgResponseTime = stats.getAverageResponseTime();
        logger.info("📊 Average Response Time: {}ms", avgResponseTime);
        
        if (avgResponseTime > 30000) { // 30 seconds
            logger.warn("⚠️ SLOW RESPONSES: Average response time over 30 seconds may indicate issues");
        }
    }
    
    /**
     * Load test data using the same approach as BatchFailureAnalysisTest
     */
    private void loadTestData() throws IOException {
        File testSetFile = new File(TEST_SET_PATH);
        JsonNode testSetArray = objectMapper.readTree(testSetFile);
        
        allTestIssues = new ArrayList<>();
        for (JsonNode issueNode : testSetArray) {
            IssueData issue = new IssueData(
                issueNode.get("issue_number").asInt(),
                issueNode.get("title").asText(),
                issueNode.get("body").asText(),
                issueNode.get("author").asText(),
                objectMapper.convertValue(issueNode.get("labels"), Set.class)
            );
            allTestIssues.add(issue);
        }
        
        logger.info("🔧 Loaded {} test issues for SDK debugging", allTestIssues.size());
    }
}
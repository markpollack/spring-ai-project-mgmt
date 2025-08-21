package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.test.context.SpringBootTest;
import org.springaicommunity.github.ai.classification.service.ClaudeCodeWrapperService;
import org.springaicommunity.github.ai.classification.service.ManualClaudePromptService;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

/**
 * Targeted Debug Test for Failed Batches from 111-Issue Run
 * 
 * Runs ONLY the 6 failed batches (5, 10, 11, 15, 22, 23) using the EXACT same
 * conditions as the original 111-issue test to identify why they fail.
 * 
 * Failed Batches Identified:
 * - Batch 5: Issues 700, 1028, 3526, 3659, 3741
 * - Batch 10: Issues 295, 368, 613, 1936, 526  
 * - Batch 11: Issues 576, 1101, 1202, 1882, 2301
 * - Batch 15: Issues 549, 833, 1543, 3734, 3745
 * - Batch 22: Issues 179, 445, 753, 1234, 2691
 * - Batch 23: Issues 392
 */
@SpringBootTest(classes = {ClaudeCodeWrapperService.class, ManualClaudePromptService.class, ObjectMapper.class})
@DisplayName("Failed Batches Debug Test - Why Do These 6 Batches Fail?")
class FailedBatchesDebugTest {
    
    private static final Logger logger = LoggerFactory.getLogger(FailedBatchesDebugTest.class);
    
    private ClaudeCodeWrapperService claudeWrapper;
    private ManualClaudePromptService manualPromptService;
    private ObjectMapper objectMapper;
    private List<JsonNode> testIssues;
    private JsonNode labelMapping;
    private String claudeMd;
    
    // Failed batch numbers from 111-issue run analysis
    private static final int[] FAILED_BATCHES = {5, 10, 11, 15, 22, 23};
    private static final int BATCH_SIZE = 5;
    
    @BeforeEach
    void setUp() throws IOException {
        objectMapper = new ObjectMapper();
        claudeWrapper = new ClaudeCodeWrapperService(objectMapper);
        manualPromptService = new ManualClaudePromptService(objectMapper);
        
        // Load the EXACT same data that the 111-issue test used
        Path testSetPath = Paths.get("/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json");
        Path labelMappingPath = Paths.get("/home/mark/project-mgmt/spring-ai-project-mgmt/github-labels-mapping-enhanced.json");
        Path claudeMdPath = Paths.get("/home/mark/project-mgmt/spring-ai-project-mgmt/claude-md-for-springai.md");
        
        // Load test issues
        JsonNode testSetNode = objectMapper.readTree(testSetPath.toFile());
        testIssues = objectMapper.convertValue(testSetNode, objectMapper.getTypeFactory().constructCollectionType(List.class, JsonNode.class));
        
        // Load label mapping
        labelMapping = objectMapper.readTree(labelMappingPath.toFile());
        
        // Load Claude MD
        claudeMd = Files.readString(claudeMdPath);
        
        logger.info("🎯 FAILED BATCHES DEBUG TEST");
        logger.info("📊 Test Data Loaded:");
        logger.info("  • Test issues: {}", testIssues.size());
        logger.info("  • Label mapping entries: {}", labelMapping.size());
        logger.info("  • Failed batches to debug: {}", java.util.Arrays.toString(FAILED_BATCHES));
    }
    
    @Test
    @DisplayName("Debug why batches 5, 10, 11, 15, 22, 23 fail in 111-issue test")
    void debugFailedBatches() throws IOException {
        logger.info("\n🚀 Starting Failed Batches Debug");
        logger.info("🔍 Method: EXACT reproduction of 111-issue test conditions");
        
        int successfulBatches = 0;
        int failedBatches = 0;
        List<String> detailedResults = new ArrayList<>();
        
        for (int batchNum : FAILED_BATCHES) {
            logger.info("\n" + "=".repeat(60));
            logger.info("🔍 DEBUGGING BATCH {} (Known to fail in 111-issue test)", batchNum);
            logger.info("=".repeat(60));
            
            // Recreate the exact batch from 111-issue test
            List<JsonNode> batchIssues = recreateBatch(batchNum);
            
            if (batchIssues.isEmpty()) {
                logger.error("❌ Could not recreate batch {}", batchNum);
                continue;
            }
            
            logger.info("📦 Batch {} Details:", batchNum);
            logger.info("  • Issues in batch: {}", batchIssues.size());
            for (int i = 0; i < batchIssues.size(); i++) {
                JsonNode issue = batchIssues.get(i);
                int issueNum = issue.get("issue_number").asInt();
                String title = issue.get("title").asText();
                int bodyLength = issue.get("body").asText().length();
                logger.info("  • Issue #{}: '{}' ({}KB body)", issueNum, 
                    title.length() > 60 ? title.substring(0, 60) + "..." : title, bodyLength / 1024);
            }
            
            // Generate prompts using EXACT same method as 111-issue test
            ManualClaudePromptService.ClassificationPrompts prompts = 
                manualPromptService.generateExactPythonPrompts(batchIssues, labelMapping, claudeMd);
            
            String combinedPrompt = prompts.systemPrompt() + "\n\n" + prompts.userPrompt();
            logger.info("📝 Prompt Details:");
            logger.info("  • System prompt size: {}KB", prompts.systemPrompt().length() / 1024);
            logger.info("  • User prompt size: {}KB", prompts.userPrompt().length() / 1024);
            logger.info("  • Combined prompt size: {}KB", combinedPrompt.length() / 1024);
            
            // Use EXACT same method as 111-issue test (file-based approach) WITH empty response retry
            logger.info("🔧 Using analyzeFromFile() (EXACT same as 111-issue test) with empty response retry");
            
            long startTime = System.currentTimeMillis();
            ClaudeCodeWrapperService.ClassificationAnalysisResult result = null;
            int attempt = 1;
            int maxAttempts = 3;
            
            while (attempt <= maxAttempts) {
                logger.info("🔄 Attempt {}/{} for batch {}", attempt, maxAttempts, batchNum);
                
                result = claudeWrapper.analyzeFromFile(combinedPrompt, Duration.ofMinutes(5), "sonnet");
                
                // Check for empty response bug
                if (result.isSuccess() && (result.getRawResponse() == null || result.getRawResponse().trim().isEmpty())) {
                    logger.warn("🚨 EMPTY RESPONSE detected on attempt {} for batch {} - retrying", attempt, batchNum);
                    if (attempt < maxAttempts) {
                        try {
                            Thread.sleep(5000); // 5 second delay before retry
                        } catch (InterruptedException e) {
                            Thread.currentThread().interrupt();
                            break;
                        }
                    }
                } else {
                    // Success or non-empty response error - break
                    break;
                }
                attempt++;
            }
            
            long duration = System.currentTimeMillis() - startTime;
            
            // Enhanced debugging of the result
            String batchResult = analyzeBatchResult(batchNum, result, duration, batchIssues.size());
            detailedResults.add(batchResult);
            logger.info(batchResult);
            
            if (result.isSuccess() && result.getJsonData() != null && result.getJsonData().isArray()) {
                int predictionsFound = 0;
                for (JsonNode prediction : result.getJsonData()) {
                    predictionsFound++;
                }
                
                if (predictionsFound == batchIssues.size()) {
                    successfulBatches++;
                    logger.info("✅ Batch {} UNEXPECTEDLY SUCCEEDED! (Was failing in 111-issue test)", batchNum);
                } else {
                    failedBatches++;
                    logger.info("❌ Batch {} CONFIRMED FAILURE (Partial results: {}/{})", 
                        batchNum, predictionsFound, batchIssues.size());
                }
            } else {
                failedBatches++;
                logger.info("❌ Batch {} CONFIRMED FAILURE", batchNum);
            }
            
            // Pause between batches (same as 111-issue test)
            try {
                Thread.sleep(2000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
        
        // Final analysis
        logger.info("\n" + "=".repeat(60));
        logger.info("🎯 FAILED BATCHES DEBUG SUMMARY");
        logger.info("=".repeat(60));
        logger.info("📊 Batches tested: {}", FAILED_BATCHES.length);
        logger.info("✅ Unexpected successes: {}", successfulBatches);
        logger.info("❌ Confirmed failures: {}", failedBatches);
        
        logger.info("\n🔍 DETAILED RESULTS:");
        for (String result : detailedResults) {
            logger.info(result);
        }
        
        if (failedBatches > 0) {
            logger.info("\n🚨 ROOT CAUSE ANALYSIS NEEDED:");
            logger.info("  → {} batches still failing with same conditions", failedBatches);
            logger.info("  → Check Claude CLI SDK, temporary file handling, or API issues");
            logger.info("  → Consider environmental factors (rate limits, network, etc.)");
        } else {
            logger.info("\n🎉 SURPRISING RESULT: All previously failed batches now succeed!");
            logger.info("  → This suggests intermittent issues (rate limits, timeouts, etc.)");
            logger.info("  → Consider implementing retry logic for flaky batches");
        }
    }
    
    /**
     * Recreate the exact batch from the 111-issue test
     */
    private List<JsonNode> recreateBatch(int batchNum) {
        int startIdx = (batchNum - 1) * BATCH_SIZE;
        int endIdx = Math.min(startIdx + BATCH_SIZE, testIssues.size());
        
        if (startIdx >= testIssues.size()) {
            return List.of();
        }
        
        return new ArrayList<>(testIssues.subList(startIdx, endIdx));
    }
    
    /**
     * Analyze batch result with detailed debugging
     */
    private String analyzeBatchResult(int batchNum, ClaudeCodeWrapperService.ClassificationAnalysisResult result, 
                                    long duration, int expectedIssues) {
        StringBuilder analysis = new StringBuilder();
        analysis.append(String.format("📊 Batch %d Analysis:\n", batchNum));
        analysis.append(String.format("  • Duration: %dms (%.1fs)\n", duration, duration / 1000.0));
        analysis.append(String.format("  • Success: %s\n", result.isSuccess()));
        
        if (result.isSuccess()) {
            int responseLength = result.getRawResponse() != null ? result.getRawResponse().length() : 0;
            analysis.append(String.format("  • Response length: %d chars\n", responseLength));
            
            if (responseLength == 0) {
                analysis.append("  • ⚠️ EMPTY RESPONSE - This is the root cause!\n");
            }
            
            if (result.getJsonData() != null && result.getJsonData().isArray()) {
                int actualPredictions = result.getJsonData().size();
                analysis.append(String.format("  • JSON predictions: %d/%d\n", actualPredictions, expectedIssues));
                
                if (actualPredictions != expectedIssues) {
                    analysis.append("  • ⚠️ PREDICTION COUNT MISMATCH\n");
                }
            } else {
                analysis.append("  • ❌ JSON PARSING FAILED\n");
            }
            
            if (result.getCost() != null) {
                double cost = result.getCost().inputTokenCost() + result.getCost().outputTokenCost();
                analysis.append(String.format("  • Cost: $%.4f\n", cost));
            }
            
            if (result.getTokenUsage() != null) {
                analysis.append(String.format("  • Tokens: %d in, %d out\n", 
                    result.getTokenUsage().inputTokens(), result.getTokenUsage().outputTokens()));
            }
        } else {
            analysis.append(String.format("  • Error: %s\n", result.getError()));
        }
        
        return analysis.toString();
    }
}
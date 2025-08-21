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
import org.springaicommunity.github.ai.classification.service.ManualClaudePromptService;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.*;

import static org.assertj.core.api.Assertions.*;

/**
 * Phase 2.2: Python Prompt SDK Debug Test
 * 
 * Tests if using the EXACT Python prompts (instead of simplified test prompts)
 * resolves the empty response issue discovered in ClaudeSDKDebugTest.
 * 
 * Key Hypothesis: The simplified test prompts are causing Claude SDK to return
 * empty responses, while the complex Python prompts work correctly.
 */
@SpringJUnitConfig(classes = {ClassificationConfiguration.class})
@DisplayName("Phase 2.2: Python Prompt SDK Debug Test")
public class PythonPromptSDKDebugTest {
    
    private static final Logger logger = LoggerFactory.getLogger(PythonPromptSDKDebugTest.class);
    
    @Autowired
    private ObjectMapper objectMapper;
    
    private DebugClaudeCodeWrapperService debugClaudeService;
    private ManualClaudePromptService manualClaudePromptService;
    
    // Test file paths - use the actual locations
    private static final String TEST_SET_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json";
    private static final String LABEL_MAPPING_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/src/main/resources/github-labels-mapping-enhanced.json";
    private static final String CLAUDE_MD_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/src/main/resources/claude-md-for-springai.md";
    
    // Failed batch from ClaudeSDKDebugTest
    private static final int FAILED_BATCH_NUMBER = 5;
    private static final int BATCH_SIZE = 5;
    
    private List<JsonNode> allTestIssues;
    private JsonNode labelMapping;
    private String claudeMd;
    
    @BeforeEach
    void setUp() throws IOException {
        loadTestData();
        
        // Create services
        debugClaudeService = new DebugClaudeCodeWrapperService(objectMapper);
        manualClaudePromptService = new ManualClaudePromptService(objectMapper);
    }
    
    @Test
    @DisplayName("Test Claude SDK with EXACT Python prompts vs simplified prompts")
    void testPythonPromptsVsSimplifiedPrompts() throws IOException {
        logger.info("=== PYTHON PROMPT VS SIMPLIFIED PROMPT COMPARISON ==");
        logger.info("🔍 Testing if Python prompts resolve empty response issue");
        
        // Get failed batch 5 (from ClaudeSDKDebugTest)
        List<JsonNode> failedBatch = recreateBatch(FAILED_BATCH_NUMBER, BATCH_SIZE);
        
        if (failedBatch.isEmpty()) {
            logger.error("❌ Could not recreate failed batch {}", FAILED_BATCH_NUMBER);
            return;
        }
        
        logger.info("🔍 Testing batch {} with {} issues", FAILED_BATCH_NUMBER, failedBatch.size());
        
        // Test 1: Use simplified prompt (like ClaudeSDKDebugTest)
        testSimplifiedPrompt(failedBatch);
        
        // Test 2: Use EXACT Python prompts
        testPythonPrompts(failedBatch);
        
        // Get final debug statistics
        DebugClaudeCodeWrapperService.DebugStats finalStats = debugClaudeService.getDebugStats();
        logger.info("📊 Final Debug Stats: {}", finalStats);
        
        // Log conclusions
        logPythonPromptConclusions(finalStats);
    }
    
    /**
     * Test with simplified prompt (reproduces ClaudeSDKDebugTest failure)
     */
    private void testSimplifiedPrompt(List<JsonNode> batch) {
        logger.info("=== TESTING SIMPLIFIED PROMPT ==");
        
        String simplifiedPrompt = createSimplifiedPrompt(batch);
        logger.info("🔍 Simplified prompt size: {}KB", simplifiedPrompt.length() / 1024);
        
        try {
            DebugClaudeCodeWrapperService.ClassificationAnalysisResult result = 
                debugClaudeService.analyzeFromText(simplifiedPrompt, Duration.ofMinutes(2), "sonnet");
            
            if (result.isSuccess()) {
                logger.info("✅ Simplified prompt SUCCEEDED (unexpected!)");
            } else {
                logger.warn("❌ Simplified prompt FAILED: {}", result.getError());
            }
            
        } catch (Exception e) {
            logger.error("💥 Simplified prompt threw exception: {}", e.getMessage());
        }
    }
    
    /**
     * Test with EXACT Python prompts (hypothesis: this will work)
     */
    private void testPythonPrompts(List<JsonNode> batch) {
        logger.info("=== TESTING EXACT PYTHON PROMPTS ==");
        
        // Generate exact Python prompts with all the proper context
        ManualClaudePromptService.ClassificationPrompts pythonPrompts = 
            manualClaudePromptService.generateExactPythonPrompts(batch, labelMapping, claudeMd);
        
        logger.info("🔍 Python system prompt size: {}KB", pythonPrompts.systemPrompt().length() / 1024);
        logger.info("🔍 Python user prompt size: {}KB", pythonPrompts.userPrompt().length() / 1024);
        
        // For Claude SDK, we need to combine system and user prompts
        String combinedPythonPrompt = pythonPrompts.systemPrompt() + "\n\n" + pythonPrompts.userPrompt();
        logger.info("🔍 Combined Python prompt size: {}KB", combinedPythonPrompt.length() / 1024);
        
        try {
            DebugClaudeCodeWrapperService.ClassificationAnalysisResult result = 
                debugClaudeService.analyzeFromText(combinedPythonPrompt, Duration.ofMinutes(2), "sonnet");
            
            if (result.isSuccess()) {
                logger.info("✅ Python prompt SUCCEEDED - HYPOTHESIS CONFIRMED!");
            } else {
                logger.warn("❌ Python prompt FAILED - hypothesis rejected: {}", result.getError());
            }
            
        } catch (Exception e) {
            logger.error("💥 Python prompt threw exception: {}", e.getMessage());
        }
    }
    
    /**
     * Create simplified prompt similar to ClaudeSDKDebugTest
     */
    private String createSimplifiedPrompt(List<JsonNode> issues) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("Please analyze these GitHub issues and classify them:\n\n");
        
        for (JsonNode issue : issues) {
            prompt.append("Issue #").append(issue.get("issue_number").asInt()).append("\n");
            prompt.append("Title: ").append(issue.get("title").asText()).append("\n");
            
            String body = issue.get("body").asText();
            prompt.append("Body: ").append(body.length() > 1000 ? 
                body.substring(0, 1000) + "..." : body).append("\n");
            
            prompt.append("Current Labels: ").append(issue.get("labels")).append("\n\n");
        }
        
        prompt.append("Please respond with a simple JSON array containing classifications for each issue.");
        
        return prompt.toString();
    }
    
    /**
     * Recreate a specific batch from the test data
     */
    private List<JsonNode> recreateBatch(int batchNumber, int batchSize) {
        int startIdx = (batchNumber - 1) * batchSize;
        int endIdx = Math.min(startIdx + batchSize, allTestIssues.size());
        
        if (startIdx >= allTestIssues.size()) {
            return List.of();
        }
        
        return new ArrayList<>(allTestIssues.subList(startIdx, endIdx));
    }
    
    /**
     * Log conclusions about Python prompt effectiveness
     */
    private void logPythonPromptConclusions(DebugClaudeCodeWrapperService.DebugStats stats) {
        logger.info("=== PYTHON PROMPT DEBUG CONCLUSIONS ==");
        
        double successRate = stats.getSuccessRate();
        logger.info("📊 Overall Success Rate: {:.1f}%", successRate);
        
        // Analyze error patterns
        Map<String, Integer> errorCounts = stats.getErrorCounts();
        if (!errorCounts.isEmpty()) {
            logger.info("📊 Error Pattern Analysis:");
            errorCounts.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .forEach(entry -> 
                    logger.info("📊   {}: {} occurrences", entry.getKey(), entry.getValue()));
        }
        
        // Critical insight: does Python prompt reduce json_extraction_failed errors?
        int jsonFailures = errorCounts.getOrDefault("json_extraction_failed", 0);
        if (jsonFailures < stats.getTotalRequests() / 2) {
            logger.info("🎉 SUCCESS: Python prompts significantly reduce empty response issues!");
            logger.info("🎯 ROOT CAUSE IDENTIFIED: Simplified prompts cause empty responses");
        } else {
            logger.warn("⚠️ Python prompts did not resolve empty response issue");
            logger.warn("🔍 Need to investigate Claude SDK configuration or other factors");
        }
    }
    
    /**
     * Load all test data required for Python prompt generation
     */
    private void loadTestData() throws IOException {
        // Load test issues
        File testSetFile = new File(TEST_SET_PATH);
        JsonNode testSetArray = objectMapper.readTree(testSetFile);
        
        allTestIssues = new ArrayList<>();
        for (JsonNode issueNode : testSetArray) {
            allTestIssues.add(issueNode);
        }
        
        // Load label mapping
        File labelMappingFile = new File(LABEL_MAPPING_PATH);
        labelMapping = objectMapper.readTree(labelMappingFile);
        
        // Load Claude MD
        claudeMd = Files.readString(Path.of(CLAUDE_MD_PATH));
        
        logger.info("🔧 Loaded {} test issues for Python prompt testing", allTestIssues.size());
        logger.info("🔧 Loaded {} labels from mapping", labelMapping.size());
        logger.info("🔧 Loaded Claude MD ({} chars)", claudeMd.length());
    }
}
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
import org.springaicommunity.github.ai.classification.service.ClaudeCodeWrapperService;
import org.springaicommunity.github.ai.classification.service.DebugClaudeCodeWrapperService;
import org.springaicommunity.github.ai.classification.service.ManualClaudePromptService;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.*;

/**
 * Critical Test: File-based vs Text-based Claude CLI Methods
 * 
 * Tests if the empty response issue is caused by the difference between:
 * - analyzeFromFile() (used in 111-issue test, failing with empty responses)
 * - analyzeFromText() (used in debug test, working correctly)
 */
@SpringJUnitConfig(classes = {ClassificationConfiguration.class})
@DisplayName("File vs Text Method Debug Test")
public class FileVsTextMethodDebugTest {
    
    private static final Logger logger = LoggerFactory.getLogger(FileVsTextMethodDebugTest.class);
    
    @Autowired
    private ObjectMapper objectMapper;
    
    private ClaudeCodeWrapperService claudeCodeWrapper;
    private DebugClaudeCodeWrapperService debugClaudeService;
    private ManualClaudePromptService manualClaudePromptService;
    
    // Test file paths
    private static final String TEST_SET_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json";
    private static final String LABEL_MAPPING_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/src/main/resources/github-labels-mapping-enhanced.json";
    private static final String CLAUDE_MD_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/src/main/resources/claude-md-for-springai.md";
    
    // Failed batch from previous tests
    private static final int TEST_BATCH_NUMBER = 5;
    private static final int BATCH_SIZE = 5;
    
    private List<JsonNode> allTestIssues;
    private JsonNode labelMapping;
    private String claudeMd;
    
    @BeforeEach
    void setUp() throws IOException {
        loadTestData();
        
        // Create services
        claudeCodeWrapper = new ClaudeCodeWrapperService(objectMapper);
        debugClaudeService = new DebugClaudeCodeWrapperService(objectMapper);
        manualClaudePromptService = new ManualClaudePromptService(objectMapper);
    }
    
    @Test
    @DisplayName("Test File-based vs Text-based Claude CLI methods with same prompt")
    void testFileVsTextMethods() throws IOException {
        logger.info("=== FILE VS TEXT METHOD COMPARISON ===");
        logger.info("🔍 Testing if file-based approach causes empty responses");
        
        // Get test batch 5 (the failed batch)
        List<JsonNode> testBatch = recreateBatch(TEST_BATCH_NUMBER, BATCH_SIZE);
        
        if (testBatch.isEmpty()) {
            logger.error("❌ Could not recreate test batch {}", TEST_BATCH_NUMBER);
            return;
        }
        
        logger.info("🔍 Testing batch {} with {} issues", TEST_BATCH_NUMBER, testBatch.size());
        
        // Generate EXACT Python prompts (same as 111-issue test)
        ManualClaudePromptService.ClassificationPrompts pythonPrompts = 
            manualClaudePromptService.generateExactPythonPrompts(testBatch, labelMapping, claudeMd);
        
        String combinedPrompt = pythonPrompts.systemPrompt() + "\n\n" + pythonPrompts.userPrompt();
        logger.info("🔍 Combined prompt size: {}KB", combinedPrompt.length() / 1024);
        
        // Test 1: File-based approach (like 111-issue test)
        testFileBased(combinedPrompt);
        
        // Test 2: Text-based approach (like debug test)  
        testTextBased(combinedPrompt);
        
        // Log conclusions
        logMethodComparison();
    }
    
    /**
     * Test file-based approach (used in 111-issue test)
     */
    private void testFileBased(String prompt) {
        logger.info("=== TESTING FILE-BASED APPROACH ===");
        logger.info("🔍 Using analyzeFromFile() (same as 111-issue test)");
        
        try {
            ClaudeCodeWrapperService.ClassificationAnalysisResult result = 
                claudeCodeWrapper.analyzeFromFile(prompt, Duration.ofMinutes(2), "sonnet");
            
            if (result.isSuccess()) {
                int responseLength = result.getRawResponse() != null ? result.getRawResponse().length() : 0;
                logger.info("✅ File-based method SUCCESS: {} chars response", responseLength);
                
                if (responseLength == 0) {
                    logger.warn("⚠️ File-based method returned EMPTY response (0 chars)");
                } else {
                    logger.info("🎉 File-based method returned VALID response");
                }
                
                // Check JSON parsing
                if (result.getJsonData() != null) {
                    logger.info("✅ File-based JSON parsing successful");
                } else {
                    logger.warn("❌ File-based JSON parsing failed");
                }
                
            } else {
                logger.warn("❌ File-based method FAILED: {}", result.getError());
            }
            
        } catch (Exception e) {
            logger.error("💥 File-based method threw exception: {}", e.getMessage());
        }
    }
    
    /**
     * Test text-based approach (used in debug test)
     */
    private void testTextBased(String prompt) {
        logger.info("=== TESTING TEXT-BASED APPROACH ===");
        logger.info("🔍 Using analyzeFromText() (same as debug test)");
        
        try {
            DebugClaudeCodeWrapperService.ClassificationAnalysisResult result = 
                debugClaudeService.analyzeFromText(prompt, Duration.ofMinutes(2), "sonnet");
            
            if (result.isSuccess()) {
                logger.info("✅ Text-based method SUCCESS");
                logger.info("🎉 Text-based method confirmed working");
            } else {
                logger.warn("❌ Text-based method FAILED: {}", result.getError());
            }
            
        } catch (Exception e) {
            logger.error("💥 Text-based method threw exception: {}", e.getMessage());
        }
    }
    
    /**
     * Log conclusions about method differences
     */
    private void logMethodComparison() {
        logger.info("=== METHOD COMPARISON CONCLUSIONS ===");
        logger.info("🔍 If file-based returns empty responses but text-based works:");
        logger.info("  → ROOT CAUSE: File-based Claude CLI method has issues");
        logger.info("  → SOLUTION: Switch 111-issue test to use analyzeFromText()");
        logger.info("🔍 If both methods work the same:");
        logger.info("  → Need to investigate other factors (batch size, timing, etc.)");
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
     * Load all test data
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
        
        logger.info("🔧 Loaded {} test issues for method comparison", allTestIssues.size());
        logger.info("🔧 Loaded {} labels from mapping", labelMapping.size());
        logger.info("🔧 Loaded Claude MD ({} chars)", claudeMd.length());
    }
}
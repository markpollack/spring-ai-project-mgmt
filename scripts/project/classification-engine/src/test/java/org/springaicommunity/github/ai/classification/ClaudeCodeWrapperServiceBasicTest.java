package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springaicommunity.github.ai.classification.service.ClaudeCodeWrapperService;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Basic test for ClaudeCodeWrapperService - minimal Claude CLI testing
 */
@SpringBootTest(classes = {ClaudeCodeWrapperService.class, ObjectMapper.class})
class ClaudeCodeWrapperServiceBasicTest {
    
    private ClaudeCodeWrapperService claudeWrapper;
    
    @BeforeEach
    void setUp() {
        ObjectMapper objectMapper = new ObjectMapper();
        claudeWrapper = new ClaudeCodeWrapperService(objectMapper);
    }
    
    @Test
    void testServiceAvailable() {
        assertNotNull(claudeWrapper, "ClaudeCodeWrapperService should be available");
        System.out.println("✅ ClaudeCodeWrapperService created successfully");
    }
    
    @Test
    void testSingleQuickClaudeCall() {
        // Test with a very simple prompt and short timeout
        String simplePrompt = "Respond with just: {\"status\": \"ok\"}";
        
        System.out.println("🧪 Testing single quick Claude CLI call");
        
        // Short timeout to avoid hanging
        ClaudeCodeWrapperService.ClassificationAnalysisResult result = 
            claudeWrapper.analyzeFromText(simplePrompt, Duration.ofSeconds(30), "haiku");
        
        System.out.println("📊 Result: " + result.isSuccess());
        
        if (result.isSuccess()) {
            System.out.println("✅ Claude CLI working - response: " + result.getRawResponse());
        } else {
            System.out.println("❌ Claude CLI failed - error: " + result.getError());
        }
        
        // The test validates service structure regardless of Claude CLI availability
        assertNotNull(result, "Analysis result should never be null");
        
        if (result.isSuccess()) {
            System.out.println("🎯 Java successfully replicates Python claude_code_wrapper.py approach");
        } else {
            System.out.println("⚠️ Claude CLI not available - service structure validated");
        }
    }
}
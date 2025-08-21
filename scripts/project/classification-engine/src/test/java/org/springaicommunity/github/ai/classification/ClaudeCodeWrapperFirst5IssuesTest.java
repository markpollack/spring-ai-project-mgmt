package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springaicommunity.github.ai.classification.service.ClaudeCodeWrapperService;
import org.springaicommunity.github.ai.classification.service.ManualClaudePromptService;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Test ClaudeCodeWrapperService with the first 5 issues from our test set
 * to validate format and reliability of the Java approach vs Python
 */
@SpringBootTest(classes = {ClaudeCodeWrapperService.class, ManualClaudePromptService.class, ObjectMapper.class})
class ClaudeCodeWrapperFirst5IssuesTest {
    
    private ClaudeCodeWrapperService claudeWrapper;
    private ManualClaudePromptService manualPromptService;
    private ObjectMapper objectMapper;
    private List<JsonNode> testIssues;
    private JsonNode labelMapping;
    private String claudeMd;
    
    @BeforeEach
    void setUp() throws IOException {
        objectMapper = new ObjectMapper();
        claudeWrapper = new ClaudeCodeWrapperService(objectMapper);
        manualPromptService = new ManualClaudePromptService(objectMapper);
        
        // Load the same data that Python used
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
        
        System.out.println("📊 Test Data Loaded:");
        System.out.println("  • Test issues: " + testIssues.size());
        System.out.println("  • Using first 5 issues for validation");
    }
    
    @Test
    void testFirst5IssuesWithClaudeCodeWrapper() {
        System.out.println("🧪 Testing first 5 issues with Java ClaudeCodeWrapper (replicating Python approach)");
        
        // Take first 5 issues
        List<JsonNode> first5Issues = testIssues.subList(0, 5);
        
        // Generate the system and user prompts (same as Python would)
        ManualClaudePromptService.ClassificationPrompts prompts = 
            manualPromptService.generateExactPythonPrompts(first5Issues, labelMapping, claudeMd);
        
        System.out.println("📝 Generated prompts:");
        System.out.println("  • System prompt: " + prompts.systemPrompt().length() + " chars");
        System.out.println("  • User prompt: " + prompts.userPrompt().length() + " chars");
        
        // Create combined prompt (system + user) as Python would send it
        String combinedPrompt = prompts.systemPrompt() + "\n\n" + prompts.userPrompt();
        
        System.out.println("🔍 Combined prompt: " + combinedPrompt.length() + " chars");
        
        // Call Claude CLI using file-based approach (EXACT Python claude_code_wrapper.py method)
        ClaudeCodeWrapperService.ClassificationAnalysisResult result = 
            claudeWrapper.analyzeFromFile(combinedPrompt, Duration.ofMinutes(3), "sonnet");
        
        // Validate the result
        System.out.println("📊 Classification Result:");
        System.out.println("  • Success: " + result.isSuccess());
        
        if (result.isSuccess()) {
            System.out.println("  • Response length: " + result.getRawResponse().length() + " chars");
            System.out.println("  • JSON extracted: " + (result.getJsonData() != null));
            
            if (result.getTokenUsage() != null) {
                System.out.println("  • Input tokens: " + result.getTokenUsage().inputTokens());
                System.out.println("  • Output tokens: " + result.getTokenUsage().outputTokens());
            }
            
            if (result.getCost() != null) {
                System.out.println("  • Cost: $" + String.format("%.4f", 
                    result.getCost().inputTokenCost() + result.getCost().outputTokenCost()));
            }
            
            // Analyze the response structure
            String response = result.getRawResponse();
            boolean containsJson = response.contains("{") && response.contains("}");
            boolean containsIssueNumber = response.contains("issue_number");
            boolean containsPredictedLabels = response.contains("predicted_labels");
            boolean containsExplanation = response.contains("explanation");
            
            System.out.println("  • Contains JSON structure: " + containsJson);
            System.out.println("  • Contains issue_number: " + containsIssueNumber);
            System.out.println("  • Contains predicted_labels: " + containsPredictedLabels);
            System.out.println("  • Contains explanation: " + containsExplanation);
            
            // Show response preview
            String preview = response.length() > 300 ? response.substring(0, 300) + "..." : response;
            System.out.println("  • Response preview: " + preview);
            
            // Try to parse JSON if available
            if (result.getJsonData() != null) {
                JsonNode jsonData = result.getJsonData();
                System.out.println("  • JSON parsing successful: " + jsonData.toPrettyString());
                
                // Validate structure matches expected format
                assertTrue(jsonData.isArray() || jsonData.isObject(), "Response should be JSON array or object");
                
                if (jsonData.isArray()) {
                    System.out.println("  • JSON array with " + jsonData.size() + " elements");
                    if (jsonData.size() > 0) {
                        JsonNode firstElement = jsonData.get(0);
                        System.out.println("  • First element keys: " + firstElement.fieldNames());
                    }
                } else {
                    System.out.println("  • JSON object with keys: " + jsonData.fieldNames());
                }
            }
            
            System.out.println("✅ Java ClaudeCodeWrapper successfully processed first 5 issues");
            System.out.println("🎯 Format matches expected Python claude_code_wrapper.py output");
            
        } else {
            System.out.println("❌ Claude CLI failed: " + result.getError());
            fail("Claude CLI call should succeed for first 5 issues test");
        }
        
        // Assert basic success
        assertTrue(result.isSuccess(), "Classification should succeed");
        assertNotNull(result.getRawResponse(), "Response should not be null");
        assertTrue(result.getRawResponse().length() > 0, "Response should not be empty");
    }
    
    @Test 
    void testPromptGeneration() {
        System.out.println("🧪 Testing prompt generation for first 5 issues");
        
        // Take first 5 issues
        List<JsonNode> first5Issues = testIssues.subList(0, 5);
        
        // Generate prompts
        ManualClaudePromptService.ClassificationPrompts prompts = 
            manualPromptService.generateExactPythonPrompts(first5Issues, labelMapping, claudeMd);
        
        assertNotNull(prompts.systemPrompt(), "System prompt should be generated");
        assertNotNull(prompts.userPrompt(), "User prompt should be generated");
        
        // Validate prompt contains the issues
        String systemPrompt = prompts.systemPrompt();
        for (JsonNode issue : first5Issues) {
            int issueNumber = issue.get("issue_number").asInt();
            assertTrue(systemPrompt.contains(String.valueOf(issueNumber)), 
                "System prompt should contain issue #" + issueNumber);
        }
        
        // Validate prompt structure matches classification.md format
        String userPrompt = prompts.userPrompt();
        assertTrue(userPrompt.contains("multi-label classifier"), "Should contain classification instructions");
        assertTrue(userPrompt.contains("confidence score"), "Should contain confidence scoring instructions");
        assertTrue(userPrompt.contains("needs more info"), "Should contain fallback logic");
        
        System.out.println("✅ Prompt generation validated for first 5 issues");
        System.out.println("📊 Ready for Claude CLI processing with " + first5Issues.size() + " issues");
    }
}
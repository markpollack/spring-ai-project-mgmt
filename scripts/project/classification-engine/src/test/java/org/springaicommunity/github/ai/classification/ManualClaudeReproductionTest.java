package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springaicommunity.github.ai.classification.service.ManualClaudePromptService;
import org.springaicommunity.github.ai.classification.service.ManualClaudePromptService.ClassificationPrompts;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Test that reproduces the EXACT manual Claude approach used to generate 
 * Python's 82.1% baseline from classification.md
 * 
 * Key Insight: Python's approach was MANUAL interaction with Claude using
 * the prompts from classification.md, NOT programmatic classification.
 */
@SpringBootTest(classes = {ManualClaudePromptService.class, ObjectMapper.class})
class ManualClaudeReproductionTest {
    
    @Autowired
    private ManualClaudePromptService manualPromptService;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    private List<JsonNode> testIssues;
    private JsonNode labelMapping;
    private String claudeMd;
    
    @BeforeEach
    void setUp() throws IOException {
        // Load the exact same files used in Python's manual process
        Path testSetPath = Paths.get("/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json");
        Path labelMappingPath = Paths.get("/home/mark/project-mgmt/spring-ai-project-mgmt/github-labels-mapping-enhanced.json");
        Path claudeMdPath = Paths.get("/home/mark/project-mgmt/spring-ai-project-mgmt/claude-md-for-springai.md");
        
        assertTrue(Files.exists(testSetPath), "Test set file must exist: " + testSetPath);
        assertTrue(Files.exists(labelMappingPath), "Label mapping file must exist: " + labelMappingPath);
        assertTrue(Files.exists(claudeMdPath), "Claude MD file must exist: " + claudeMdPath);
        
        // Load test issues
        JsonNode testSetNode = objectMapper.readTree(testSetPath.toFile());
        testIssues = objectMapper.convertValue(testSetNode, objectMapper.getTypeFactory().constructCollectionType(List.class, JsonNode.class));
        
        // Load label mapping
        labelMapping = objectMapper.readTree(labelMappingPath.toFile());
        
        // Load Claude MD
        claudeMd = Files.readString(claudeMdPath);
        
        System.out.println("📊 Test Data Loaded:");
        System.out.println("  • Test issues: " + testIssues.size());
        System.out.println("  • Label mapping entries: " + labelMapping.size());
        System.out.println("  • Claude MD length: " + claudeMd.length() + " chars");
    }
    
    @Test
    void testGenerateExactPythonPrompts() {
        ClassificationPrompts prompts = manualPromptService.generateExactPythonPrompts(testIssues, labelMapping, claudeMd);
        
        assertNotNull(prompts.systemPrompt(), "System prompt must be generated");
        assertNotNull(prompts.userPrompt(), "User prompt must be generated");
        
        // Verify system prompt contains all required data
        assertTrue(prompts.systemPrompt().contains("test_set.json"), "System prompt must reference test_set.json");
        assertTrue(prompts.systemPrompt().contains("github-labels-mapping-enhanced.json"), "System prompt must reference label mapping");
        assertTrue(prompts.systemPrompt().contains("claude-md-for-springai.md"), "System prompt must reference Claude MD");
        
        // Verify user prompt matches classification.md exactly
        String userPrompt = prompts.userPrompt();
        assertTrue(userPrompt.contains("We're building a multi-label classifier"), "Must start with exact classification.md opening");
        assertTrue(userPrompt.contains("confidence score between 0.0 and 1.0"), "Must include confidence scoring instructions");
        assertTrue(userPrompt.contains("needs more info"), "Must include fallback label logic");
        assertTrue(userPrompt.contains("0.9–1.0** = very confident"), "Must include calibration instructions");
        assertTrue(userPrompt.contains("Only respond with the JSON output"), "Must include output format constraints");
        
        System.out.println("✅ Generated prompts that exactly match Python's manual approach");
        System.out.println("📝 System prompt length: " + prompts.systemPrompt().length() + " chars");
        System.out.println("📝 User prompt length: " + prompts.userPrompt().length() + " chars");
    }
    
    @Test
    void testSystemPromptContainsAllData() throws IOException {
        ClassificationPrompts prompts = manualPromptService.generateExactPythonPrompts(testIssues, labelMapping, claudeMd);
        String systemPrompt = prompts.systemPrompt();
        
        // Verify all data is embedded in system prompt
        assertTrue(systemPrompt.contains("issue_number"), "Must contain test issue data");
        assertTrue(systemPrompt.contains("\"label\":"), "Must contain label mapping data");
        assertTrue(systemPrompt.contains("Spring AI"), "Must contain Claude MD content");
        
        // Save system prompt for manual inspection
        Path outputPath = Paths.get("/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/manual_claude_system_prompt.txt");
        Files.writeString(outputPath, systemPrompt);
        
        System.out.println("💾 System prompt saved to: " + outputPath);
        System.out.println("🔍 This prompt contains ALL data needed for manual Claude reproduction");
    }
    
    @Test
    void testUserPromptMatchesClassificationMd() throws IOException {
        ClassificationPrompts prompts = manualPromptService.generateExactPythonPrompts(testIssues, labelMapping, claudeMd);
        String userPrompt = prompts.userPrompt();
        
        // Load original classification.md for comparison
        Path classificationMdPath = Paths.get("/home/mark/project-mgmt/spring-ai-project-mgmt/classification.md");
        String originalClassificationMd = Files.readString(classificationMdPath);
        
        // Key phrases that must match exactly
        String[] keyPhrases = {
            "We're building a multi-label classifier for GitHub issues in the Spring AI project",
            "Each issue may have **multiple labels**",
            "confidence score between 0.0 and 1.0",
            "needs more info",
            "0.9–1.0** = very confident, strong evidence",
            "0.6–0.8** = moderately confident, relevant match",
            "< 0.6** = uncertain; fallback to",
            "Only respond with the JSON output—no extra commentary"
        };
        
        for (String phrase : keyPhrases) {
            assertTrue(userPrompt.contains(phrase), "User prompt must contain key phrase: " + phrase);
            assertTrue(originalClassificationMd.contains(phrase), "Original classification.md must contain: " + phrase);
        }
        
        // Save user prompt for manual inspection
        Path outputPath = Paths.get("/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/manual_claude_user_prompt.txt");
        Files.writeString(outputPath, userPrompt);
        
        System.out.println("💾 User prompt saved to: " + outputPath);
        System.out.println("✅ User prompt exactly matches classification.md approach");
    }
    
    @Test
    void testReproductionInstructions() {
        ClassificationPrompts prompts = manualPromptService.generateExactPythonPrompts(testIssues, labelMapping, claudeMd);
        
        // Generate reproduction instructions
        String instructions = generateManualReproductionInstructions(prompts);
        
        // Save instructions
        try {
            Path instructionsPath = Paths.get("/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/MANUAL_CLAUDE_REPRODUCTION_INSTRUCTIONS.md");
            Files.writeString(instructionsPath, instructions);
            System.out.println("📋 Manual reproduction instructions saved to: " + instructionsPath);
        } catch (IOException e) {
            fail("Failed to save reproduction instructions: " + e.getMessage());
        }
        
        assertFalse(instructions.isEmpty(), "Instructions must be generated");
        assertTrue(instructions.contains("82.1% F1 baseline"), "Must reference the target baseline");
        assertTrue(instructions.contains("conservative_full_classification.json"), "Must reference expected output");
        
        System.out.println("🎯 Ready to reproduce Python's 82.1% baseline using manual Claude approach");
    }
    
    private String generateManualReproductionInstructions(ClassificationPrompts prompts) {
        return String.format("""
            # Manual Claude Reproduction Instructions
            
            ## Objective
            Reproduce Python's **82.1% F1 baseline** using the EXACT manual approach that generated `conservative_full_classification.json`.
            
            ## Key Discovery
            Python's 82.1%% baseline was NOT generated programmatically. It was created through **manual interaction with Claude** using the prompts from `classification.md`.
            
            ## Manual Reproduction Steps
            
            ### Step 1: Load System Context
            Copy the following system prompt into Claude as initial context:
            
            ```
            %s
            ```
            
            ### Step 2: Execute Classification Request  
            Send the following user prompt to Claude:
            
            ```
            %s
            ```
            
            ### Step 3: Process All 111 Issues
            - Claude will initially classify "first 5 issues" 
            - Continue requesting next batches until all 111 issues are classified
            - Maintain consistent format and confidence scoring throughout
            
            ### Step 4: Validate Output Format
            Ensure output matches this structure:
            ```json
            {
              "issue_number": 123,
              "predicted_labels": [
                {"label": "bug", "confidence": 0.82},
                {"label": "pinecone", "confidence": 0.76}
              ],
              "explanation": "Classification rationale"
            }
            ```
            
            ### Step 5: Save and Evaluate
            - Save complete output as `java_manual_claude_classification.json`
            - Run Java evaluation to confirm 82.1%% F1 score achievement
            - Compare with original `conservative_full_classification.json`
            
            ## Expected Outcome
            - **Target**: 82.1%% F1 score (matching Python baseline)
            - **Method**: Manual Claude interaction (not programmatic)
            - **Validation**: Java evaluation confirms parity
            
            ## Critical Success Factors
            1. **Exact Prompt Match**: Use classification.md prompts verbatim
            2. **Complete Data Context**: Include all 111 test issues, label mapping, and Claude MD
            3. **Consistent Confidence Scoring**: Maintain 0.6 threshold throughout
            4. **Batch Processing**: Process all issues systematically
            
            This approach directly replicates how Python achieved 82.1%% - through manual Claude interaction, not code.
            """, 
            prompts.systemPrompt(), 
            prompts.userPrompt()
        );
    }
}
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
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Validation test: 10 issues in 2 batches of 5 to validate prompt bug fix
 * Target: 100% JSON parsing success rate
 */
@SpringBootTest(classes = {ClaudeCodeWrapperService.class, ManualClaudePromptService.class, ObjectMapper.class})
class ClaudeCodeWrapper10IssuesTest {
    
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
        
        // Load test issues - ONLY FIRST 10 for validation
        JsonNode testSetNode = objectMapper.readTree(testSetPath.toFile());
        List<JsonNode> allIssues = objectMapper.convertValue(testSetNode, objectMapper.getTypeFactory().constructCollectionType(List.class, JsonNode.class));
        testIssues = allIssues.subList(0, 10); // Only first 10 issues
        
        // Load label mapping
        labelMapping = objectMapper.readTree(labelMappingPath.toFile());
        
        // Load Claude MD
        claudeMd = Files.readString(claudeMdPath);
        
        System.out.println("🎯 VALIDATION TEST - 10 Issues, Prompt Bug Fix Verification");
        System.out.println("📊 Test Data Loaded:");
        System.out.println("  • Test issues: " + testIssues.size() + " (first 10 only)");
        System.out.println("  • Label mapping entries: " + labelMapping.size());
        System.out.println("  • Target: 100% JSON parsing success rate");
    }
    
    @Test
    void testFirst10IssuesWithFixedPrompt() throws IOException {
        System.out.println("\n🚀 Starting 10-Issue Validation Test");
        System.out.println("📝 Method: Java file-based Claude CLI with fixed prompt (no file output bug)");
        
        long startTime = System.currentTimeMillis();
        
        // Process in 2 batches of 5 issues each
        int batchSize = 5;
        int totalBatches = 2; // Exactly 2 batches for 10 issues
        
        System.out.println("📦 Batch Processing:");
        System.out.println("  • Total issues: " + testIssues.size());
        System.out.println("  • Batch size: " + batchSize);
        System.out.println("  • Total batches: " + totalBatches);
        
        List<JsonNode> allPredictions = new ArrayList<>();
        double totalCost = 0.0;
        int totalInputTokens = 0;
        int totalOutputTokens = 0;
        int successfulBatches = 0;
        int failedBatches = 0;
        
        // Process each batch
        for (int batchNum = 0; batchNum < totalBatches; batchNum++) {
            int startIdx = batchNum * batchSize;
            int endIdx = Math.min(startIdx + batchSize, testIssues.size());
            List<JsonNode> batchIssues = testIssues.subList(startIdx, endIdx);
            
            System.out.println("\n📦 Processing Batch " + (batchNum + 1) + "/" + totalBatches);
            System.out.println("  • Issues " + (startIdx + 1) + "-" + endIdx + " (" + batchIssues.size() + " issues)");
            
            // Generate prompts for this batch (with fixed prompt - no file output bug)
            ManualClaudePromptService.ClassificationPrompts prompts = 
                manualPromptService.generateExactPythonPrompts(batchIssues, labelMapping, claudeMd);
            
            String combinedPrompt = prompts.systemPrompt() + "\n\n" + prompts.userPrompt();
            System.out.println("  • Prompt size: " + combinedPrompt.length() + " chars");
            
            // Use file-based approach with updated SDK JSON output
            System.out.println("  • Using file-based approach (fixed prompt, updated SDK)");
            ClaudeCodeWrapperService.ClassificationAnalysisResult result = 
                claudeWrapper.analyzeFromFile(combinedPrompt, Duration.ofMinutes(5), "sonnet");
            
            if (result.isSuccess()) {
                System.out.println("  • ✅ Success: " + result.getRawResponse().length() + " chars response");
                
                // Track costs and tokens
                if (result.getCost() != null) {
                    double batchCost = result.getCost().inputTokenCost() + result.getCost().outputTokenCost();
                    totalCost += batchCost;
                    System.out.println("  • 💰 Cost: $" + String.format("%.4f", batchCost));
                }
                
                if (result.getTokenUsage() != null) {
                    totalInputTokens += result.getTokenUsage().inputTokens();
                    totalOutputTokens += result.getTokenUsage().outputTokens();
                    System.out.println("  • 🔤 Tokens: " + result.getTokenUsage().inputTokens() + " in, " + 
                                      result.getTokenUsage().outputTokens() + " out");
                }
                
                // Parse JSON response - THIS SHOULD NOW WORK 100% OF THE TIME
                if (result.getJsonData() != null && result.getJsonData().isArray()) {
                    int predictionsFound = 0;
                    for (JsonNode prediction : result.getJsonData()) {
                        allPredictions.add(prediction);
                        predictionsFound++;
                    }
                    System.out.println("  • 📊 Parsed " + predictionsFound + " predictions");
                    
                    if (predictionsFound == batchIssues.size()) {
                        successfulBatches++;
                        System.out.println("  • ✅ PERFECT: Complete batch processing (all " + batchIssues.size() + " issues classified)");
                    } else {
                        System.out.println("  • ⚠️ PARTIAL: Only " + predictionsFound + "/" + batchIssues.size() + " issues classified");
                    }
                } else {
                    System.out.println("  • ❌ FAILED: JSON parsing failed for batch " + (batchNum + 1));
                    System.out.println("  • 🔍 Response preview: " + result.getRawResponse().substring(0, Math.min(200, result.getRawResponse().length())));
                    failedBatches++;
                }
                
            } else {
                System.out.println("  • ❌ FAILED: " + result.getError());
                failedBatches++;
            }
            
            // Brief pause between batches
            if (batchNum < totalBatches - 1) {
                try {
                    Thread.sleep(2000);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }
        }
        
        long endTime = System.currentTimeMillis();
        long totalDuration = endTime - startTime;
        
        System.out.println("\n🎯 VALIDATION TEST COMPLETE");
        System.out.println("⏱️ Total Duration: " + (totalDuration / 1000) + " seconds");
        System.out.println("💰 Total Cost: $" + String.format("%.4f", totalCost));
        System.out.println("🔤 Total Tokens: " + totalInputTokens + " in, " + totalOutputTokens + " out");
        System.out.println("📊 Total Predictions: " + allPredictions.size());
        System.out.println("✅ Successful Batches: " + successfulBatches + "/" + totalBatches);
        System.out.println("❌ Failed Batches: " + failedBatches + "/" + totalBatches);
        
        // Save the predictions to file
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd_HH-mm-ss"));
        String outputFileName = "java_10_issues_validation_" + timestamp + ".json";
        Path outputPath = Paths.get("/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine", outputFileName);
        
        String predictionsJson = objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(allPredictions);
        Files.writeString(outputPath, predictionsJson);
        
        System.out.println("💾 Predictions saved to: " + outputPath);
        
        System.out.println("\n🎯 VALIDATION RESULTS:");
        System.out.println("=====================================");
        System.out.println("📊 Generated " + allPredictions.size() + "/10 predictions");
        System.out.println("📈 Success Rate: " + String.format("%.1f%%", (double) allPredictions.size() / 10 * 100));
        System.out.println("🎯 GOAL: 100% success rate (bug fix validation)");
        
        if (successfulBatches == totalBatches && allPredictions.size() == 10) {
            System.out.println("🎉 PROMPT BUG FIX VALIDATED: 100% success rate achieved!");
        } else {
            System.out.println("⚠️ PROMPT BUG FIX NEEDS MORE WORK: " + failedBatches + " batches failed");
        }
        
        // Assert 100% success for validation
        assertEquals(10, allPredictions.size(), "Should have exactly 10 predictions (100% success rate)");
        assertEquals(2, successfulBatches, "Both batches should succeed completely");
        assertEquals(0, failedBatches, "No batches should fail with the prompt bug fix");
        
        System.out.println("\n✅ VALIDATION TEST PASSED - PROMPT BUG FIX WORKS!");
    }
}
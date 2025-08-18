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
 * Full 111-issue evaluation using small batches (5 issues per batch) to avoid Claude CLI large file issues
 * Target: Achieve 82.1% F1 score matching Python baseline with complete coverage
 */
@SpringBootTest(classes = {ClaudeCodeWrapperService.class, ManualClaudePromptService.class, ObjectMapper.class})
class ClaudeCodeWrapperSmallBatchTest {
    
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
        
        System.out.println("🎯 FULL 111-ISSUE EVALUATION - Small Batches for Reliability");
        System.out.println("📊 Test Data Loaded:");
        System.out.println("  • Test issues: " + testIssues.size());
        System.out.println("  • Label mapping entries: " + labelMapping.size());
        System.out.println("  • Target: 82.1% F1 score (Python baseline)");
    }
    
    @Test
    void testFull111IssuesWithSmallBatches() throws IOException {
        System.out.println("\n🚀 Starting Full 111-Issue Classification");
        System.out.println("📝 Method: Java file-based Claude CLI with small batches for reliability");
        
        long startTime = System.currentTimeMillis();
        
        // Process in small batches to avoid Claude CLI large file issues
        int batchSize = 5;  // Small batches for reliable Claude CLI processing
        int totalBatches = (int) Math.ceil((double) testIssues.size() / batchSize);
        
        System.out.println("📦 Batch Processing:");
        System.out.println("  • Total issues: " + testIssues.size());
        System.out.println("  • Batch size: " + batchSize + " (small batches for Claude CLI reliability)");
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
            
            // Generate prompts for this batch (exact Python method)
            ManualClaudePromptService.ClassificationPrompts prompts = 
                manualPromptService.generateExactPythonPrompts(batchIssues, labelMapping, claudeMd);
            
            String combinedPrompt = prompts.systemPrompt() + "\n\n" + prompts.userPrompt();
            System.out.println("  • Prompt size: " + combinedPrompt.length() + " chars");
            
            // Use file-based approach (EXACT Python claude_code_wrapper.py method)
            System.out.println("  • Using file-based approach (Python claude_code_wrapper.py method)");
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
                
                // Parse JSON response
                if (result.getJsonData() != null && result.getJsonData().isArray()) {
                    int predictionsFound = 0;
                    for (JsonNode prediction : result.getJsonData()) {
                        allPredictions.add(prediction);
                        predictionsFound++;
                    }
                    System.out.println("  • 📊 Parsed " + predictionsFound + " predictions");
                    
                    if (predictionsFound == batchIssues.size()) {
                        successfulBatches++;
                        System.out.println("  • ✅ Complete batch processing (all " + batchIssues.size() + " issues classified)");
                    } else {
                        System.out.println("  • ⚠️ Partial batch processing (" + predictionsFound + "/" + batchIssues.size() + " issues classified)");
                    }
                } else {
                    System.out.println("  • ❌ JSON parsing failed for batch " + (batchNum + 1));
                    failedBatches++;
                }
                
            } else {
                System.out.println("  • ❌ Failed: " + result.getError());
                failedBatches++;
                // Continue with next batch despite failure
            }
            
            // Brief pause between batches to avoid rate limiting
            if (batchNum < totalBatches - 1) {
                try {
                    Thread.sleep(2000); // 2 second pause
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }
        }
        
        long endTime = System.currentTimeMillis();
        long totalDuration = endTime - startTime;
        
        System.out.println("\n🎯 CLASSIFICATION COMPLETE");
        System.out.println("⏱️ Total Duration: " + (totalDuration / 1000) + " seconds (" + (totalDuration / 60000) + " minutes)");
        System.out.println("💰 Total Cost: $" + String.format("%.4f", totalCost));
        System.out.println("🔤 Total Tokens: " + totalInputTokens + " in, " + totalOutputTokens + " out");
        System.out.println("📊 Total Predictions: " + allPredictions.size());
        System.out.println("✅ Successful Batches: " + successfulBatches + "/" + totalBatches);
        System.out.println("❌ Failed Batches: " + failedBatches + "/" + totalBatches);
        
        // Report how many predictions we got
        System.out.println("📊 Expected " + testIssues.size() + " predictions, got " + allPredictions.size());
        
        // Save the predictions to file
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd_HH-mm-ss"));
        String outputFileName = "java_small_batch_classification_" + timestamp + ".json";
        Path outputPath = Paths.get("/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine", outputFileName);
        
        String predictionsJson = objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(allPredictions);
        Files.writeString(outputPath, predictionsJson);
        
        System.out.println("💾 Predictions saved to: " + outputPath);
        
        System.out.println("\n🎯 CLASSIFICATION COMPLETE!");
        System.out.println("=====================================");
        System.out.println("📊 Successfully generated " + allPredictions.size() + " predictions");
        System.out.println("🔬 Next Step: Run evaluation using existing FilteredEvaluationService");
        System.out.println("📁 Predictions file: " + outputFileName);
        System.out.println("🎯 Target: 82.1% F1 score (Python baseline)");
        System.out.println("⚡ To evaluate, run: FilteredEvaluationServiceTest with this predictions file");
        
        // Assert basic success - require at least 80% completion rate
        double completionRate = (double) allPredictions.size() / testIssues.size();
        assertTrue(completionRate >= 0.8, "Should have at least 80% completion rate, got " + String.format("%.1f%%", completionRate * 100));
        
        // Report success rate
        System.out.println("📈 Completion Rate: " + String.format("%.1f%%", completionRate * 100) + 
                          " (" + allPredictions.size() + "/" + testIssues.size() + " issues)");
        
        System.out.println("\n🎉 SMALL BATCH EVALUATION COMPLETE!");
    }
}
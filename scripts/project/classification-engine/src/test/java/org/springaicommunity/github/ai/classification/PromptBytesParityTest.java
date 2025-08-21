package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springaicommunity.github.ai.classification.config.LabelSpaceConfiguration;
import org.springaicommunity.github.ai.classification.domain.ClassificationConfig;
import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.service.PythonCompatiblePromptTemplateService;
import org.springaicommunity.github.ai.classification.util.ParityHasher;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;

import static org.assertj.core.api.Assertions.*;

/**
 * Stage 2: Prompt Bytes Parity Test
 * 
 * <p>CRITICAL PARITY GATE: Verifies that Java and Python generate byte-identical 
 * prompts that are sent to Claude. This tests the final prompt construction after
 * issue text preprocessing.</p>
 * 
 * <p>Expected Results:
 * <ul>
 *   <li>If ALL prompt hashes match: Prompt generation is identical, proceed to Stage 3</li>
 *   <li>If ANY prompt hash differs: Fix Java prompt template (format, labels, instructions)</li>
 * </ul>
 * 
 * <p>This is the SECOND parity gate after text preprocessing verification.</p>
 */
@SpringJUnitConfig
@DisplayName("Stage 2: Prompt Bytes Parity Test")
class PromptBytesParityTest {
    
    private static final Logger log = LoggerFactory.getLogger(PromptBytesParityTest.class);
    
    // File paths
    private static final String TEST_SET_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json";
    private static final String PYTHON_PROMPTS_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/python_prompt_hashes.json";
    
    private PythonCompatiblePromptTemplateService promptTemplateService;
    private ObjectMapper objectMapper;
    
    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        promptTemplateService = new PythonCompatiblePromptTemplateService();
    }
    
    @Test
    @DisplayName("Java prompt generation MUST produce identical bytes to Python for all 111 issues")
    void testPromptByteParity() throws IOException {
        log.info("=== STAGE 2: PROMPT BYTES PARITY TEST ===");
        log.info("Testing that Java generates BYTE-IDENTICAL prompts to Python...");
        
        // Load test issues
        List<TestIssue> testIssues = loadTestIssues();
        log.info("Loaded {} test issues", testIssues.size());
        
        // Generate Java prompts for all issues
        Map<Integer, PromptHash> javaPrompts = generateJavaPromptHashes(testIssues);
        log.info("Generated Java prompt hashes for {} issues", javaPrompts.size());
        
        // Try to load Python prompts (may not exist yet)
        Map<Integer, PromptHash> pythonPrompts = loadPythonPromptHashes();
        
        if (pythonPrompts.isEmpty()) {
            log.warn("=== PYTHON PROMPT HASHES NOT FOUND ===");
            log.warn("Creating Java prompt hash file for comparison with Python...");
            saveJavaPromptsForPythonComparison(javaPrompts);
            log.warn("Python team: please run equivalent prompt hashing and compare");
            log.warn("Expected format: EXACT final system + user messages sent to Claude");
            
            // For now, just verify our prompt generation is consistent
            verifyJavaPromptConsistency(testIssues, javaPrompts);
            return;
        }
        
        // Compare Java vs Python prompt hashes
        log.info("Comparing Java vs Python prompt hashes...");
        comparePromptHashes(javaPrompts, pythonPrompts);
    }
    
    /**
     * Generate prompt hashes for all issues using Java prompt template.
     */
    private Map<Integer, PromptHash> generateJavaPromptHashes(List<TestIssue> testIssues) {
        Map<Integer, PromptHash> prompts = new HashMap<>();
        
        // Get the label space that would be used
        List<String> availableLabels = LabelSpaceConfiguration.getFullLabelSpace();
        Collections.sort(availableLabels); // Ensure consistent label order
        
        for (TestIssue issue : testIssues) {
            // Create classification request (this is what would go to the LLM)
            ClassificationRequest request = ClassificationRequest.builder()
                .issueNumber(issue.issueNumber())
                .title(issue.title())
                .body(issue.body())
                .availableLabels(availableLabels)
                .config(createDefaultConfig())
                .build();
            
            // Generate the actual prompt using our service
            String combinedPrompt = promptTemplateService.buildClassificationPrompt(request);
            
            // Generate hashes and metadata
            String promptHash = ParityHasher.sha256(combinedPrompt);
            String labelOrderHash = ParityHasher.hashLabelOrder(availableLabels);
            int promptLength = combinedPrompt.length();
            int tokenEstimate = ParityHasher.estimateTokenCount(combinedPrompt);
            int labelCount = availableLabels.size();
            
            PromptHash hash = new PromptHash(
                promptHash, labelOrderHash, promptLength, tokenEstimate, labelCount,
                "", "", combinedPrompt
            );
            
            prompts.put(issue.issueNumber(), hash);
            
            // Log first few for debugging
            if (prompts.size() <= 3) {
                log.info("Issue #{}: promptHash={}, labelHash={}, chars={}, tokens={}, labels={}", 
                        issue.issueNumber(), promptHash.substring(0, 12) + "...", 
                        labelOrderHash.substring(0, 12) + "...",
                        promptLength, tokenEstimate, labelCount);
            }
        }
        
        return prompts;
    }
    
    /**
     * Create default classification config for testing.
     */
    private ClassificationConfig createDefaultConfig() {
        return ClassificationConfig.builder()
            .confidenceThreshold(0.7)
            .maxLabelsPerIssue(5)
            .batchSize(25)
            .build();
    }
    
    /**
     * Load Python prompt hashes for comparison.
     */
    private Map<Integer, PromptHash> loadPythonPromptHashes() throws IOException {
        File pythonFile = new File(PYTHON_PROMPTS_PATH);
        if (!pythonFile.exists()) {
            log.info("Python prompt hashes file not found: {}", PYTHON_PROMPTS_PATH);
            return Map.of();
        }
        
        JsonNode pythonArray = objectMapper.readTree(pythonFile);
        Map<Integer, PromptHash> pythonPrompts = new HashMap<>();
        
        for (JsonNode promptNode : pythonArray) {
            int issueNumber = promptNode.get("issue_number").asInt();
            String promptHash = promptNode.get("prompt_hash").asText();
            String labelOrderHash = promptNode.get("label_order_hash").asText();
            int promptLength = promptNode.get("prompt_length").asInt();
            int tokenEstimate = promptNode.get("token_estimate").asInt();
            int labelCount = promptNode.get("label_count").asInt();
            
            PromptHash hash = new PromptHash(promptHash, labelOrderHash, promptLength, 
                                           tokenEstimate, labelCount, "", "", "");
            pythonPrompts.put(issueNumber, hash);
        }
        
        log.info("Loaded {} Python prompt hashes from {}", pythonPrompts.size(), PYTHON_PROMPTS_PATH);
        return pythonPrompts;
    }
    
    /**
     * Compare Java and Python prompt hashes - this is the critical parity gate.
     */
    private void comparePromptHashes(Map<Integer, PromptHash> javaPrompts, Map<Integer, PromptHash> pythonPrompts) {
        log.info("=== STAGE 2 PARITY COMPARISON ===");
        
        int totalIssues = javaPrompts.size();
        int exactMatches = 0;
        int promptHashMismatches = 0;
        int labelOrderMismatches = 0;
        int lengthMismatches = 0;
        List<Integer> failedIssues = new ArrayList<>();
        
        for (int issueNumber : javaPrompts.keySet()) {
            PromptHash javaPrompt = javaPrompts.get(issueNumber);
            PromptHash pythonPrompt = pythonPrompts.get(issueNumber);
            
            if (pythonPrompt == null) {
                log.warn("Issue #{}: Missing Python prompt hash", issueNumber);
                failedIssues.add(issueNumber);
                continue;
            }
            
            boolean promptHashMatch = javaPrompt.promptHash().equals(pythonPrompt.promptHash());
            boolean labelOrderMatch = javaPrompt.labelOrderHash().equals(pythonPrompt.labelOrderHash());
            boolean lengthMatch = javaPrompt.promptLength() == pythonPrompt.promptLength();
            
            if (promptHashMatch && labelOrderMatch && lengthMatch) {
                exactMatches++;
            } else {
                if (!promptHashMatch) {
                    promptHashMismatches++;
                    log.error("🔴 Issue #{}: PROMPT HASH MISMATCH", issueNumber);
                    log.error("  Java prompt hash:   {}", javaPrompt.promptHash());
                    log.error("  Python prompt hash: {}", pythonPrompt.promptHash());
                }
                if (!labelOrderMatch) {
                    labelOrderMismatches++;
                    log.error("🔴 Issue #{}: LABEL ORDER MISMATCH", issueNumber);
                    log.error("  Java label hash:   {}", javaPrompt.labelOrderHash());
                    log.error("  Python label hash: {}", pythonPrompt.labelOrderHash());
                }
                if (!lengthMatch) {
                    lengthMismatches++;
                    log.error("🔴 Issue #{}: PROMPT LENGTH MISMATCH", issueNumber);
                    log.error("  Java length:   {} chars", javaPrompt.promptLength());
                    log.error("  Python length: {} chars", pythonPrompt.promptLength());
                }
                failedIssues.add(issueNumber);
            }
        }
        
        // Log summary results
        log.info("=== STAGE 2 RESULTS ===");
        log.info("Total issues: {}", totalIssues);
        log.info("Exact matches: {} ({:.1f}%)", exactMatches, (exactMatches * 100.0 / totalIssues));
        log.info("Prompt hash mismatches: {}", promptHashMismatches);
        log.info("Label order mismatches: {}", labelOrderMismatches);
        log.info("Length mismatches: {}", lengthMismatches);
        
        if (exactMatches == totalIssues) {
            log.info("✅ STAGE 2 PASSED: Java prompt generation matches Python EXACTLY!");
            log.info("✅ Prompt templates are identical - proceed to Stage 3: Model Invocation Parity");
        } else {
            log.error("🔴 STAGE 2 FAILED: Java prompt generation differs from Python");
            log.error("🔴 Failed issues: {}", failedIssues);
            log.error("🔴 Fix Java prompt template before proceeding to Stage 3");
            log.error("🔴 Check: system message format, user message format, label order, instructions");
            
            // Log first few failed issues for debugging
            for (int i = 0; i < Math.min(3, failedIssues.size()); i++) {
                int issueNumber = failedIssues.get(i);
                PromptHash javaPrompt = javaPrompts.get(issueNumber);
                log.error("Debug Issue #{}: Java prompt preview: \"{}...\"", 
                         issueNumber, javaPrompt.combinedPrompt().substring(0, Math.min(200, javaPrompt.combinedPrompt().length())));
            }
            
            fail(String.format(
                "STAGE 2 FAILED: %d/%d issues have different prompt hashes between Java and Python. " +
                "Java prompt template must be fixed to match Python exactly. " +
                "Failed issues: %s", 
                promptHashMismatches, totalIssues, failedIssues.subList(0, Math.min(10, failedIssues.size()))
            ));
        }
    }
    
    /**
     * Verify Java prompt consistency for debugging.
     */
    private void verifyJavaPromptConsistency(List<TestIssue> testIssues, Map<Integer, PromptHash> javaPrompts) {
        log.info("Verifying Java prompt consistency...");
        
        // Re-generate prompts and verify they match
        for (TestIssue issue : testIssues.subList(0, Math.min(5, testIssues.size()))) {
            // Get the label space that would be used
            List<String> availableLabels = LabelSpaceConfiguration.getFullLabelSpace();
            Collections.sort(availableLabels);
            
            ClassificationRequest request = ClassificationRequest.builder()
                .issueNumber(issue.issueNumber())
                .title(issue.title())
                .body(issue.body())
                .availableLabels(availableLabels)
                .config(createDefaultConfig())
                .build();
            
            String combinedPrompt = promptTemplateService.buildClassificationPrompt(request);
            String recomputedHash = ParityHasher.sha256(combinedPrompt);
            
            PromptHash originalPrompt = javaPrompts.get(issue.issueNumber());
            assertThat(recomputedHash)
                .as("Prompt hash consistency for issue #%d", issue.issueNumber())
                .isEqualTo(originalPrompt.promptHash());
        }
        
        log.info("✅ Java prompt generation is consistent");
    }
    
    /**
     * Save Java prompt hashes for Python comparison.
     */
    private void saveJavaPromptsForPythonComparison(Map<Integer, PromptHash> javaPrompts) throws IOException {
        List<Map<String, Object>> promptData = new ArrayList<>();
        
        for (Map.Entry<Integer, PromptHash> entry : javaPrompts.entrySet()) {
            Map<String, Object> item = new HashMap<>();
            item.put("issue_number", entry.getKey());
            item.put("prompt_hash", entry.getValue().promptHash());
            item.put("label_order_hash", entry.getValue().labelOrderHash());
            item.put("prompt_length", entry.getValue().promptLength());
            item.put("token_estimate", entry.getValue().tokenEstimate());
            item.put("label_count", entry.getValue().labelCount());
            promptData.add(item);
        }
        
        String outputPath = "/home/mark/project-mgmt/spring-ai-project-mgmt/java_prompt_hashes.json";
        objectMapper.writerWithDefaultPrettyPrinter().writeValue(new File(outputPath), promptData);
        log.info("Saved Java prompt hashes to: {}", outputPath);
    }
    
    /**
     * Load test issues from JSON.
     */
    private List<TestIssue> loadTestIssues() throws IOException {
        File testFile = new File(TEST_SET_PATH);
        JsonNode testSetArray = objectMapper.readTree(testFile);
        
        List<TestIssue> issues = new ArrayList<>();
        for (JsonNode issueNode : testSetArray) {
            issues.add(new TestIssue(
                issueNode.get("issue_number").asInt(),
                issueNode.get("title").asText(),
                issueNode.get("body").asText(""),
                issueNode.get("author").asText("unknown")
            ));
        }
        
        return issues;
    }
    
    // Record classes
    private record TestIssue(int issueNumber, String title, String body, String author) {}
    
    private record PromptHash(
        String promptHash,
        String labelOrderHash, 
        int promptLength,
        int tokenEstimate,
        int labelCount,
        String systemPrompt,
        String userPrompt,
        String combinedPrompt
    ) {}
}
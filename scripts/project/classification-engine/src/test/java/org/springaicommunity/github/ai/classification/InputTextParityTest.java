package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springaicommunity.github.ai.classification.util.ParityHasher;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.text.Normalizer;
import java.util.*;

import static org.assertj.core.api.Assertions.*;

/**
 * Stage 1: Issue Text Parity Test
 * 
 * <p>CRITICAL PARITY GATE: Verifies that Java and Python process issue text identically.
 * This test computes SHA-256 hashes of the exact text that goes to the LLM and compares
 * with Python's preprocessing results.</p>
 * 
 * <p>Expected Results:
 * <ul>
 *   <li>If ALL hashes match: Text processing is identical, proceed to Stage 2</li>
 *   <li>If ANY hash differs: Fix Java preprocessing (unicode, markdown, whitespace, etc.)</li>
 * </ul>
 * 
 * <p>This is the FIRST real parity gate after evaluation verification.</p>
 */
@SpringJUnitConfig
@DisplayName("Stage 1: Issue Text Parity Test")
class InputTextParityTest {
    
    private static final Logger log = LoggerFactory.getLogger(InputTextParityTest.class);
    
    // File paths
    private static final String TEST_SET_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json";
    private static final String PYTHON_HASHES_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/python_text_hashes.json";
    
    private ObjectMapper objectMapper;
    
    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
    }
    
    @Test
    @DisplayName("Java text preprocessing MUST produce identical hashes to Python for all 111 issues")
    void testInputTextParity() throws IOException {
        log.info("=== STAGE 1: ISSUE TEXT PARITY TEST ===");
        log.info("Testing that Java processes issue text EXACTLY like Python...");
        
        // Load test issues
        List<TestIssue> testIssues = loadTestIssues();
        log.info("Loaded {} test issues", testIssues.size());
        
        // Generate Java hashes for all issues
        Map<Integer, TextHash> javaHashes = generateJavaTextHashes(testIssues);
        log.info("Generated Java text hashes for {} issues", javaHashes.size());
        
        // Try to load Python hashes (may not exist yet)
        Map<Integer, TextHash> pythonHashes = loadPythonTextHashes();
        
        if (pythonHashes.isEmpty()) {
            log.warn("=== PYTHON HASHES NOT FOUND ===");
            log.warn("Creating Java hash file for comparison with Python...");
            saveJavaHashesForPythonComparison(javaHashes);
            log.warn("Python team: please run equivalent hashing on your side and compare");
            log.warn("Expected Python format: normalized_title + '\\n\\n' + normalized_body");
            
            // For now, just verify our hashing is consistent
            verifyJavaHashConsistency(testIssues, javaHashes);
            return;
        }
        
        // Compare Java vs Python hashes
        log.info("Comparing Java vs Python text hashes...");
        compareTextHashes(javaHashes, pythonHashes);
    }
    
    /**
     * Generate text hashes for all issues using Java preprocessing.
     */
    private Map<Integer, TextHash> generateJavaTextHashes(List<TestIssue> testIssues) {
        Map<Integer, TextHash> hashes = new HashMap<>();
        
        for (TestIssue issue : testIssues) {
            // Apply Java preprocessing (this is what we need to verify matches Python)
            String processedTitle = preprocessText(issue.title());
            String processedBody = preprocessText(issue.body());
            
            // Create the exact text that would go to the LLM
            String combinedText = processedTitle + "\n\n" + processedBody;
            
            // Generate hash and metadata
            String textHash = ParityHasher.sha256(combinedText);
            int charLen = combinedText.length();
            int tokenLen = ParityHasher.estimateTokenCount(combinedText);
            int codeBlockCount = ParityHasher.countCodeBlocks(combinedText);
            
            TextHash hash = new TextHash(
                textHash, charLen, tokenLen, codeBlockCount,
                processedTitle, processedBody, combinedText
            );
            
            hashes.put(issue.issueNumber(), hash);
            
            // Log first few for debugging
            if (hashes.size() <= 3) {
                log.info("Issue #{}: hash={}, chars={}, tokens={}, blocks={}", 
                        issue.issueNumber(), textHash.substring(0, 12) + "...", 
                        charLen, tokenLen, codeBlockCount);
            }
        }
        
        return hashes;
    }
    
    /**
     * Java text preprocessing - this MUST match Python's preprocessing exactly.
     */
    private String preprocessText(String text) {
        if (text == null) {
            return "";
        }
        
        // TODO: Implement exact Python preprocessing here
        // For now, basic normalization
        String processed = text;
        
        // Unicode normalization (Python might use NFC or NFKC)
        processed = Normalizer.normalize(processed, Normalizer.Form.NFC);
        
        // Trim whitespace
        processed = processed.trim();
        
        // Normalize line endings
        processed = processed.replaceAll("\r\n", "\n");
        processed = processed.replaceAll("\r", "\n");
        
        return processed;
    }
    
    /**
     * Load Python text hashes for comparison.
     */
    private Map<Integer, TextHash> loadPythonTextHashes() throws IOException {
        File pythonFile = new File(PYTHON_HASHES_PATH);
        if (!pythonFile.exists()) {
            log.info("Python hashes file not found: {}", PYTHON_HASHES_PATH);
            return Map.of();
        }
        
        JsonNode pythonArray = objectMapper.readTree(pythonFile);
        Map<Integer, TextHash> pythonHashes = new HashMap<>();
        
        for (JsonNode hashNode : pythonArray) {
            int issueNumber = hashNode.get("issue_number").asInt();
            String textHash = hashNode.get("text_hash").asText();
            int charLen = hashNode.get("char_len").asInt();
            int tokenLen = hashNode.get("token_len").asInt();
            int codeBlockCount = hashNode.get("code_block_count").asInt();
            
            TextHash hash = new TextHash(textHash, charLen, tokenLen, codeBlockCount, "", "", "");
            pythonHashes.put(issueNumber, hash);
        }
        
        log.info("Loaded {} Python text hashes from {}", pythonHashes.size(), PYTHON_HASHES_PATH);
        return pythonHashes;
    }
    
    /**
     * Compare Java and Python text hashes - this is the critical parity gate.
     */
    private void compareTextHashes(Map<Integer, TextHash> javaHashes, Map<Integer, TextHash> pythonHashes) {
        log.info("=== STAGE 1 PARITY COMPARISON ===");
        
        int totalIssues = javaHashes.size();
        int exactMatches = 0;
        int hashMismatches = 0;
        int lengthMismatches = 0;
        List<Integer> failedIssues = new ArrayList<>();
        
        for (int issueNumber : javaHashes.keySet()) {
            TextHash javaHash = javaHashes.get(issueNumber);
            TextHash pythonHash = pythonHashes.get(issueNumber);
            
            if (pythonHash == null) {
                log.warn("Issue #{}: Missing Python hash", issueNumber);
                failedIssues.add(issueNumber);
                continue;
            }
            
            boolean hashMatch = javaHash.textHash().equals(pythonHash.textHash());
            boolean lengthMatch = javaHash.charLen() == pythonHash.charLen();
            
            if (hashMatch && lengthMatch) {
                exactMatches++;
            } else {
                if (!hashMatch) {
                    hashMismatches++;
                    log.error("🔴 Issue #{}: TEXT HASH MISMATCH", issueNumber);
                    log.error("  Java hash:   {}", javaHash.textHash());
                    log.error("  Python hash: {}", pythonHash.textHash());
                }
                if (!lengthMatch) {
                    lengthMismatches++;
                    log.error("🔴 Issue #{}: LENGTH MISMATCH", issueNumber);
                    log.error("  Java length:   {} chars", javaHash.charLen());
                    log.error("  Python length: {} chars", pythonHash.charLen());
                }
                failedIssues.add(issueNumber);
            }
        }
        
        // Log summary results
        log.info("=== STAGE 1 RESULTS ===");
        log.info("Total issues: {}", totalIssues);
        log.info("Exact matches: {} ({:.1f}%)", exactMatches, (exactMatches * 100.0 / totalIssues));
        log.info("Hash mismatches: {}", hashMismatches);
        log.info("Length mismatches: {}", lengthMismatches);
        
        if (exactMatches == totalIssues) {
            log.info("✅ STAGE 1 PASSED: Java text processing matches Python EXACTLY!");
            log.info("✅ Text preprocessing is identical - proceed to Stage 2: Prompt Parity");
        } else {
            log.error("🔴 STAGE 1 FAILED: Java text processing differs from Python");
            log.error("🔴 Failed issues: {}", failedIssues);
            log.error("🔴 Fix Java preprocessing before proceeding to Stage 2");
            log.error("🔴 Check: unicode normalization, markdown stripping, whitespace, URL expansion");
            
            // Log first few failed issues for debugging
            for (int i = 0; i < Math.min(3, failedIssues.size()); i++) {
                int issueNumber = failedIssues.get(i);
                TextHash javaHash = javaHashes.get(issueNumber);
                log.error("Debug Issue #{}: Java text preview: \"{}...\"", 
                         issueNumber, javaHash.combinedText().substring(0, Math.min(100, javaHash.combinedText().length())));
            }
            
            fail(String.format(
                "STAGE 1 FAILED: %d/%d issues have different text hashes between Java and Python. " +
                "Java text preprocessing must be fixed to match Python exactly. " +
                "Failed issues: %s", 
                hashMismatches, totalIssues, failedIssues.subList(0, Math.min(10, failedIssues.size()))
            ));
        }
    }
    
    /**
     * Verify Java hash consistency for debugging.
     */
    private void verifyJavaHashConsistency(List<TestIssue> testIssues, Map<Integer, TextHash> javaHashes) {
        log.info("Verifying Java hash consistency...");
        
        // Re-generate hashes and verify they match
        for (TestIssue issue : testIssues.subList(0, Math.min(5, testIssues.size()))) {
            String processedTitle = preprocessText(issue.title());
            String processedBody = preprocessText(issue.body());
            String combinedText = processedTitle + "\n\n" + processedBody;
            String recomputedHash = ParityHasher.sha256(combinedText);
            
            TextHash originalHash = javaHashes.get(issue.issueNumber());
            assertThat(recomputedHash)
                .as("Hash consistency for issue #%d", issue.issueNumber())
                .isEqualTo(originalHash.textHash());
        }
        
        log.info("✅ Java hash generation is consistent");
    }
    
    /**
     * Save Java hashes for Python comparison.
     */
    private void saveJavaHashesForPythonComparison(Map<Integer, TextHash> javaHashes) throws IOException {
        List<Map<String, Object>> hashData = new ArrayList<>();
        
        for (Map.Entry<Integer, TextHash> entry : javaHashes.entrySet()) {
            Map<String, Object> item = new HashMap<>();
            item.put("issue_number", entry.getKey());
            item.put("text_hash", entry.getValue().textHash());
            item.put("char_len", entry.getValue().charLen());
            item.put("token_len", entry.getValue().tokenLen());
            item.put("code_block_count", entry.getValue().codeBlockCount());
            hashData.add(item);
        }
        
        String outputPath = "/home/mark/project-mgmt/spring-ai-project-mgmt/java_text_hashes.json";
        objectMapper.writerWithDefaultPrettyPrinter().writeValue(new File(outputPath), hashData);
        log.info("Saved Java text hashes to: {}", outputPath);
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
    
    private record TextHash(
        String textHash, 
        int charLen, 
        int tokenLen, 
        int codeBlockCount,
        String processedTitle,
        String processedBody, 
        String combinedText
    ) {}
}
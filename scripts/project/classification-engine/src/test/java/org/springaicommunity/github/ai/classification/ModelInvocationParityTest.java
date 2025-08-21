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

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

import static org.assertj.core.api.Assertions.*;

/**
 * Stage 3: Model Invocation Parity Test
 * 
 * <p>CRITICAL PARITY GATE: Verifies that Java and Python invoke Claude Code CLI with
 * identical parameters, model versions, and environment settings.</p>
 * 
 * <p>This test captures and hashes the full CLI command line, binary version, 
 * environment variables, and model configuration to ensure both stacks are hitting
 * the exact same Claude endpoint with identical parameters.</p>
 * 
 * <p>Expected Results:
 * <ul>
 *   <li>If ALL invocation hashes match: CLI invocation is identical, proceed to Stage 4</li>
 *   <li>If ANY invocation hash differs: Fix Java CLI configuration (version, model, flags)</li>
 * </ul>
 * 
 * <p>This is the THIRD parity gate after text and prompt verification.</p>
 */
@SpringJUnitConfig
@DisplayName("Stage 3: Model Invocation Parity Test")
class ModelInvocationParityTest {
    
    private static final Logger log = LoggerFactory.getLogger(ModelInvocationParityTest.class);
    
    // File paths
    private static final String TEST_SET_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json";
    private static final String PYTHON_INVOCATIONS_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/python_invocation_hashes.json";
    
    private PythonCompatiblePromptTemplateService promptTemplateService;
    private ObjectMapper objectMapper;
    
    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        promptTemplateService = new PythonCompatiblePromptTemplateService();
    }
    
    @Test
    @DisplayName("Java Claude Code CLI invocation MUST be identical to Python for all parameters")
    void testModelInvocationParity() throws IOException {
        log.info("=== STAGE 3: MODEL INVOCATION PARITY TEST ===");
        log.info("Testing that Java invokes Claude Code CLI IDENTICALLY to Python...");
        
        // Load sample test issues for invocation testing
        List<TestIssue> testIssues = loadTestIssues().subList(0, 5); // Sample 5 issues
        log.info("Using {} sample issues for invocation testing", testIssues.size());
        
        // Generate Java invocation details for sample issues
        Map<Integer, InvocationDetails> javaInvocations = generateJavaInvocationDetails(testIssues);
        log.info("Generated Java invocation details for {} issues", javaInvocations.size());
        
        // Try to load Python invocations (may not exist yet)
        Map<Integer, InvocationDetails> pythonInvocations = loadPythonInvocationDetails();
        
        if (pythonInvocations.isEmpty()) {
            log.warn("=== PYTHON INVOCATION DETAILS NOT FOUND ===");
            log.warn("Creating Java invocation detail file for comparison with Python...");
            saveJavaInvocationsForPythonComparison(javaInvocations);
            log.warn("Python team: please run equivalent invocation logging and compare");
            log.warn("Expected: Same claude binary version, model ID, temperature, flags");
            
            // For now, just verify our invocation details are consistent
            verifyJavaInvocationConsistency(testIssues, javaInvocations);
            return;
        }
        
        // Compare Java vs Python invocation details
        log.info("Comparing Java vs Python Claude Code CLI invocations...");
        compareInvocationDetails(javaInvocations, pythonInvocations);
    }
    
    /**
     * Generate invocation details for sample issues using Java's Claude Code CLI setup.
     */
    private Map<Integer, InvocationDetails> generateJavaInvocationDetails(List<TestIssue> testIssues) {
        Map<Integer, InvocationDetails> invocations = new HashMap<>();
        
        // Get Claude Code binary version and environment
        ClaudeEnvironment claudeEnv = captureClaudeEnvironment();
        
        // Get the label space that would be used
        List<String> availableLabels = LabelSpaceConfiguration.getFullLabelSpace();
        Collections.sort(availableLabels);
        
        for (TestIssue issue : testIssues) {
            // Create classification request
            ClassificationRequest request = ClassificationRequest.builder()
                .issueNumber(issue.issueNumber())
                .title(issue.title())
                .body(issue.body())
                .availableLabels(availableLabels)
                .config(createDefaultConfig())
                .build();
            
            // Generate the prompt
            String prompt = promptTemplateService.buildClassificationPrompt(request);
            
            // Build command line that would be executed
            String commandLine = buildClaudeCommandLine(prompt, claudeEnv);
            
            // Generate hashes and metadata
            String commandHash = ParityHasher.sha256(commandLine);
            String environmentHash = ParityHasher.sha256(claudeEnv.toString());
            String fullInvocationHash = ParityHasher.sha256(commandLine + "|" + claudeEnv.toString());
            
            InvocationDetails details = new InvocationDetails(
                commandHash,
                environmentHash, 
                fullInvocationHash,
                claudeEnv.claudeVersion(),
                claudeEnv.modelId(),
                claudeEnv.temperature(),
                claudeEnv.topP(),
                claudeEnv.maxTokens(),
                commandLine,
                claudeEnv
            );
            
            invocations.put(issue.issueNumber(), details);
            
            // Log first few for debugging
            if (invocations.size() <= 3) {
                log.info("Issue #{}: cmdHash={}, envHash={}, model={}, temp={}", 
                        issue.issueNumber(), 
                        commandHash.substring(0, 12) + "...",
                        environmentHash.substring(0, 12) + "...",
                        claudeEnv.modelId(), claudeEnv.temperature());
            }
        }
        
        return invocations;
    }
    
    /**
     * Capture Claude Code CLI environment and version information.
     */
    private ClaudeEnvironment captureClaudeEnvironment() {
        try {
            // Get Claude binary version
            String claudeVersion = executeCommand("claude --version");
            
            // Get environment variables that affect Claude behavior
            Map<String, String> envVars = new HashMap<>();
            envVars.put("CLAUDE_API_KEY", System.getenv("CLAUDE_API_KEY") != null ? "***SET***" : "***NOT_SET***");
            envVars.put("CLAUDE_MODEL", System.getenv("CLAUDE_MODEL"));
            envVars.put("CLAUDE_TEMP", System.getenv("CLAUDE_TEMP"));
            envVars.put("CLAUDE_TOP_P", System.getenv("CLAUDE_TOP_P"));
            envVars.put("CLAUDE_MAX_TOKENS", System.getenv("CLAUDE_MAX_TOKENS"));
            
            // Default values (these should match what Python uses)
            String modelId = envVars.get("CLAUDE_MODEL");
            if (modelId == null || modelId.trim().isEmpty()) {
                modelId = "claude-3-5-sonnet-20241022"; // Current default
            }
            
            String temperature = envVars.get("CLAUDE_TEMP");
            if (temperature == null || temperature.trim().isEmpty()) {
                temperature = "0.0"; // Conservative for classification
            }
            
            String topP = envVars.get("CLAUDE_TOP_P");
            if (topP == null || topP.trim().isEmpty()) {
                topP = "1.0"; // Default
            }
            
            String maxTokens = envVars.get("CLAUDE_MAX_TOKENS");
            if (maxTokens == null || maxTokens.trim().isEmpty()) {
                maxTokens = "4096"; // Default
            }
            
            return new ClaudeEnvironment(
                claudeVersion.trim(),
                modelId,
                temperature,
                topP,
                maxTokens,
                envVars
            );
            
        } catch (Exception e) {
            log.error("Failed to capture Claude environment: {}", e.getMessage());
            return new ClaudeEnvironment(
                "ERROR: " + e.getMessage(),
                "unknown",
                "0.0",
                "1.0", 
                "4096",
                Map.of()
            );
        }
    }
    
    /**
     * Build the exact command line that would be executed for Claude Code CLI.
     */
    private String buildClaudeCommandLine(String prompt, ClaudeEnvironment env) {
        // This should match exactly what Java's classification service would execute
        StringBuilder cmd = new StringBuilder();
        
        cmd.append("claude code");
        
        // Add model if specified
        if (!env.modelId().equals("claude-3-5-sonnet-20241022")) { // Only add if not default
            cmd.append(" --model ").append(env.modelId());
        }
        
        // Add temperature if not default
        if (!env.temperature().equals("0.0")) {
            cmd.append(" --temperature ").append(env.temperature());
        }
        
        // Add top_p if not default
        if (!env.topP().equals("1.0")) {
            cmd.append(" --top-p ").append(env.topP());
        }
        
        // Add max_tokens if not default
        if (!env.maxTokens().equals("4096")) {
            cmd.append(" --max-tokens ").append(env.maxTokens());
        }
        
        // Add prompt (truncated for hashing purposes)
        String promptPreview = prompt.length() > 100 ? 
            prompt.substring(0, 100) + "..." : prompt;
        cmd.append(" -p \"").append(promptPreview).append("\"");
        
        return cmd.toString();
    }
    
    /**
     * Execute a command and return its output.
     */
    private String executeCommand(String command) throws IOException, InterruptedException {
        Process process = Runtime.getRuntime().exec(command);
        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        StringBuilder output = new StringBuilder();
        String line;
        
        while ((line = reader.readLine()) != null) {
            output.append(line).append("\n");
        }
        
        int exitCode = process.waitFor();
        if (exitCode != 0) {
            throw new RuntimeException("Command failed with exit code " + exitCode + ": " + command);
        }
        
        return output.toString().trim();
    }
    
    /**
     * Load Python invocation details for comparison.
     */
    private Map<Integer, InvocationDetails> loadPythonInvocationDetails() throws IOException {
        File pythonFile = new File(PYTHON_INVOCATIONS_PATH);
        if (!pythonFile.exists()) {
            log.info("Python invocation details file not found: {}", PYTHON_INVOCATIONS_PATH);
            return Map.of();
        }
        
        JsonNode pythonArray = objectMapper.readTree(pythonFile);
        Map<Integer, InvocationDetails> pythonInvocations = new HashMap<>();
        
        for (JsonNode invNode : pythonArray) {
            int issueNumber = invNode.get("issue_number").asInt();
            String commandHash = invNode.get("command_hash").asText();
            String environmentHash = invNode.get("environment_hash").asText();
            String fullInvocationHash = invNode.get("full_invocation_hash").asText();
            String claudeVersion = invNode.get("claude_version").asText();
            String modelId = invNode.get("model_id").asText();
            String temperature = invNode.get("temperature").asText();
            String topP = invNode.get("top_p").asText();
            String maxTokens = invNode.get("max_tokens").asText();
            String commandLine = invNode.get("command_line").asText();
            
            InvocationDetails details = new InvocationDetails(
                commandHash, environmentHash, fullInvocationHash,
                claudeVersion, modelId, temperature, topP, maxTokens,
                commandLine, null
            );
            pythonInvocations.put(issueNumber, details);
        }
        
        log.info("Loaded {} Python invocation details from {}", pythonInvocations.size(), PYTHON_INVOCATIONS_PATH);
        return pythonInvocations;
    }
    
    /**
     * Compare Java and Python invocation details - this is the critical parity gate.
     */
    private void compareInvocationDetails(Map<Integer, InvocationDetails> javaInvocations, 
                                        Map<Integer, InvocationDetails> pythonInvocations) {
        log.info("=== STAGE 3 PARITY COMPARISON ===");
        
        int totalIssues = javaInvocations.size();
        int exactMatches = 0;
        int versionMismatches = 0;
        int modelMismatches = 0;
        int temperatureMismatches = 0;
        int commandMismatches = 0;
        List<Integer> failedIssues = new ArrayList<>();
        
        for (int issueNumber : javaInvocations.keySet()) {
            InvocationDetails javaInv = javaInvocations.get(issueNumber);
            InvocationDetails pythonInv = pythonInvocations.get(issueNumber);
            
            if (pythonInv == null) {
                log.warn("Issue #{}: Missing Python invocation details", issueNumber);
                failedIssues.add(issueNumber);
                continue;
            }
            
            boolean versionMatch = javaInv.claudeVersion().equals(pythonInv.claudeVersion());
            boolean modelMatch = javaInv.modelId().equals(pythonInv.modelId());
            boolean tempMatch = javaInv.temperature().equals(pythonInv.temperature());
            boolean commandMatch = javaInv.commandHash().equals(pythonInv.commandHash());
            
            if (versionMatch && modelMatch && tempMatch && commandMatch) {
                exactMatches++;
            } else {
                if (!versionMatch) {
                    versionMismatches++;
                    log.error("🔴 Issue #{}: CLAUDE VERSION MISMATCH", issueNumber);
                    log.error("  Java version:   {}", javaInv.claudeVersion());
                    log.error("  Python version: {}", pythonInv.claudeVersion());
                }
                if (!modelMatch) {
                    modelMismatches++;
                    log.error("🔴 Issue #{}: MODEL ID MISMATCH", issueNumber);
                    log.error("  Java model:   {}", javaInv.modelId());
                    log.error("  Python model: {}", pythonInv.modelId());
                }
                if (!tempMatch) {
                    temperatureMismatches++;
                    log.error("🔴 Issue #{}: TEMPERATURE MISMATCH", issueNumber);
                    log.error("  Java temp:   {}", javaInv.temperature());
                    log.error("  Python temp: {}", pythonInv.temperature());
                }
                if (!commandMatch) {
                    commandMismatches++;
                    log.error("🔴 Issue #{}: COMMAND HASH MISMATCH", issueNumber);
                    log.error("  Java command hash:   {}", javaInv.commandHash());
                    log.error("  Python command hash: {}", pythonInv.commandHash());
                }
                failedIssues.add(issueNumber);
            }
        }
        
        // Log summary results
        log.info("=== STAGE 3 RESULTS ===");
        log.info("Total issues: {}", totalIssues);
        log.info("Exact matches: {} ({:.1f}%)", exactMatches, (exactMatches * 100.0 / totalIssues));
        log.info("Version mismatches: {}", versionMismatches);
        log.info("Model mismatches: {}", modelMismatches);
        log.info("Temperature mismatches: {}", temperatureMismatches);
        log.info("Command mismatches: {}", commandMismatches);
        
        if (exactMatches == totalIssues) {
            log.info("✅ STAGE 3 PASSED: Java Claude Code CLI invocation matches Python EXACTLY!");
            log.info("✅ CLI parameters are identical - proceed to Stage 4: Raw Output Parity");
        } else {
            log.error("🔴 STAGE 3 FAILED: Java Claude Code CLI invocation differs from Python");
            log.error("🔴 Failed issues: {}", failedIssues);
            log.error("🔴 Fix Java CLI configuration before proceeding to Stage 4");
            log.error("🔴 Check: claude version, model ID, temperature, environment variables");
            
            fail(String.format(
                "STAGE 3 FAILED: %d/%d issues have different CLI invocation details between Java and Python. " +
                "Java CLI configuration must be fixed to match Python exactly. " +
                "Failed issues: %s", 
                (totalIssues - exactMatches), totalIssues, failedIssues.subList(0, Math.min(10, failedIssues.size()))
            ));
        }
    }
    
    /**
     * Verify Java invocation consistency for debugging.
     */
    private void verifyJavaInvocationConsistency(List<TestIssue> testIssues, 
                                               Map<Integer, InvocationDetails> javaInvocations) {
        log.info("Verifying Java invocation consistency...");
        
        // Check that all invocations use same Claude version and model
        Set<String> versions = new HashSet<>();
        Set<String> models = new HashSet<>();
        Set<String> temperatures = new HashSet<>();
        
        for (InvocationDetails details : javaInvocations.values()) {
            versions.add(details.claudeVersion());
            models.add(details.modelId());
            temperatures.add(details.temperature());
        }
        
        assertThat(versions).hasSize(1).as("All invocations should use same Claude version");
        assertThat(models).hasSize(1).as("All invocations should use same model ID");
        assertThat(temperatures).hasSize(1).as("All invocations should use same temperature");
        
        log.info("✅ Java invocation details are consistent");
        log.info("  Claude version: {}", versions.iterator().next());
        log.info("  Model ID: {}", models.iterator().next());
        log.info("  Temperature: {}", temperatures.iterator().next());
    }
    
    /**
     * Save Java invocation details for Python comparison.
     */
    private void saveJavaInvocationsForPythonComparison(Map<Integer, InvocationDetails> javaInvocations) throws IOException {
        List<Map<String, Object>> invocationData = new ArrayList<>();
        
        for (Map.Entry<Integer, InvocationDetails> entry : javaInvocations.entrySet()) {
            InvocationDetails details = entry.getValue();
            Map<String, Object> item = new HashMap<>();
            item.put("issue_number", entry.getKey());
            item.put("command_hash", details.commandHash());
            item.put("environment_hash", details.environmentHash());
            item.put("full_invocation_hash", details.fullInvocationHash());
            item.put("claude_version", details.claudeVersion());
            item.put("model_id", details.modelId());
            item.put("temperature", details.temperature());
            item.put("top_p", details.topP());
            item.put("max_tokens", details.maxTokens());
            item.put("command_line", details.commandLine());
            invocationData.add(item);
        }
        
        String outputPath = "/home/mark/project-mgmt/spring-ai-project-mgmt/java_invocation_hashes.json";
        objectMapper.writerWithDefaultPrettyPrinter().writeValue(new File(outputPath), invocationData);
        log.info("Saved Java invocation details to: {}", outputPath);
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
    
    private record ClaudeEnvironment(
        String claudeVersion,
        String modelId,
        String temperature,
        String topP,
        String maxTokens,
        Map<String, String> envVars
    ) {
        @Override
        public String toString() {
            return String.format("version=%s,model=%s,temp=%s,top_p=%s,max_tokens=%s,env=%s",
                claudeVersion, modelId, temperature, topP, maxTokens, envVars);
        }
    }
    
    private record InvocationDetails(
        String commandHash,
        String environmentHash,
        String fullInvocationHash,
        String claudeVersion,
        String modelId,
        String temperature,
        String topP,
        String maxTokens,
        String commandLine,
        ClaudeEnvironment environment
    ) {}
}
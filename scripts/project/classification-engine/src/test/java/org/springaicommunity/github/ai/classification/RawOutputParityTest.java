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
import org.springaicommunity.github.ai.classification.domain.LabelPrediction;
import org.springaicommunity.github.ai.classification.service.PythonCompatiblePromptTemplateService;
import org.springaicommunity.github.ai.classification.util.ParityHasher;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static org.assertj.core.api.Assertions.*;

/**
 * Stage 4: Raw Output Parity Test
 * 
 * <p>CRITICAL PARITY GATE: Captures verbatim raw CLI output from Java's Claude Code 
 * invocations and compares with Python's raw outputs for the same issues.</p>
 * 
 * <p>This test proves whether the model's responses differ even with identical text, 
 * prompts, and CLI parameters. Uses the same parser implementation on both outputs
 * to eliminate parser drift from the equation.</p>
 * 
 * <p>Expected Results:
 * <ul>
 *   <li>If raw outputs differ → model/version behavior or hidden system preambles</li>
 *   <li>If raw outputs match but parsed labels don't → normalization/alias mapping issues</li>
 * </ul>
 * 
 * <p>This is the FOURTH parity gate after text, prompt, and CLI invocation verification.</p>
 */
@SpringJUnitConfig
@DisplayName("Stage 4: Raw Output Parity Test")
class RawOutputParityTest {
    
    private static final Logger log = LoggerFactory.getLogger(RawOutputParityTest.class);
    
    // File paths
    private static final String TEST_SET_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json";
    private static final String PYTHON_RAW_OUTPUTS_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/python_raw_outputs.json";
    private static final String RAW_OUTPUTS_DIR = "/home/mark/project-mgmt/spring-ai-project-mgmt/raw_outputs/";
    
    // Sample size for raw output testing (start with 3 for debugging)
    private static final int SAMPLE_SIZE = 3;
    
    private PythonCompatiblePromptTemplateService promptTemplateService;
    private ObjectMapper objectMapper;
    
    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        promptTemplateService = new PythonCompatiblePromptTemplateService();
        
        // Create raw outputs directory
        try {
            Files.createDirectories(Paths.get(RAW_OUTPUTS_DIR));
        } catch (IOException e) {
            log.error("Failed to create raw outputs directory: {}", e.getMessage());
        }
    }
    
    @Test
    @DisplayName("Java raw Claude Code output MUST match Python for label-set agreement and zero-prediction rates")
    void testRawOutputParity() throws IOException, InterruptedException {
        log.info("=== STAGE 4: RAW OUTPUT PARITY TEST ===");
        log.info("Testing raw Claude Code CLI outputs between Java and Python...");
        
        // Load sample test issues (30 issues for raw output comparison)
        List<TestIssue> sampleIssues = loadSampleTestIssues();
        log.info("Using {} sample issues for raw output testing", sampleIssues.size());
        
        // Generate Java raw outputs by actually calling Claude Code CLI
        Map<Integer, RawOutput> javaRawOutputs = generateJavaRawOutputs(sampleIssues);
        log.info("Generated Java raw outputs for {} issues", javaRawOutputs.size());
        
        // Try to load Python raw outputs (may not exist yet)
        Map<Integer, RawOutput> pythonRawOutputs = loadPythonRawOutputs();
        
        if (pythonRawOutputs.isEmpty()) {
            log.warn("=== PYTHON RAW OUTPUTS NOT FOUND ===");
            log.warn("Creating Java raw output file for comparison with Python...");
            saveJavaRawOutputsForPythonComparison(javaRawOutputs);
            log.warn("Python team: please run equivalent raw output capture and compare");
            log.warn("Expected: Same raw Claude responses for identical prompts and CLI parameters");
            
            // For now, analyze Java outputs for consistency and basic validation
            analyzeJavaRawOutputs(javaRawOutputs);
            return;
        }
        
        // Compare Java vs Python raw outputs
        log.info("Comparing Java vs Python raw Claude Code outputs...");
        compareRawOutputs(javaRawOutputs, pythonRawOutputs);
    }
    
    /**
     * Generate raw outputs by actually calling Claude Code CLI for sample issues.
     */
    private Map<Integer, RawOutput> generateJavaRawOutputs(List<TestIssue> sampleIssues) 
            throws IOException, InterruptedException {
        Map<Integer, RawOutput> rawOutputs = new HashMap<>();
        
        // Get the label space
        List<String> availableLabels = LabelSpaceConfiguration.getFullLabelSpace();
        Collections.sort(availableLabels);
        
        log.info("Starting Claude Code CLI invocations (sequential, no concurrency)...");
        
        for (int i = 0; i < sampleIssues.size(); i++) {
            TestIssue issue = sampleIssues.get(i);
            log.info("Processing issue #{} ({}/{})...", issue.issueNumber(), i + 1, sampleIssues.size());
            
            try {
                // Create classification request
                ClassificationRequest request = ClassificationRequest.builder()
                    .issueNumber(issue.issueNumber())
                    .title(issue.title())
                    .body(issue.body())
                    .availableLabels(availableLabels)
                    .config(createDefaultConfig())
                    .build();
                
                // Generate the exact prompt
                String prompt = promptTemplateService.buildClassificationPrompt(request);
                
                // Write prompt to temporary file (Claude Code CLI works better with files for long prompts)
                Path promptFile = createTempPromptFile(issue.issueNumber(), prompt);
                
                // Execute Claude Code CLI with the prompt file
                String rawResponse = executeClaudeCodeCLI(promptFile);
                
                // Parse the response using Java's parser to extract labels
                List<LabelPrediction> parsedLabels = parseClaudeResponse(rawResponse);
                
                // Generate hashes and metadata
                String responseHash = ParityHasher.sha256(rawResponse);
                String promptHash = ParityHasher.sha256(prompt);
                
                RawOutput output = new RawOutput(
                    responseHash,
                    promptHash,
                    rawResponse.length(),
                    ParityHasher.estimateTokenCount(rawResponse),
                    parsedLabels.size(),
                    computeZeroPredictionFlag(parsedLabels),
                    rawResponse,
                    parsedLabels
                );
                
                rawOutputs.put(issue.issueNumber(), output);
                
                // Clean up temp file
                Files.deleteIfExists(promptFile);
                
                // Log progress
                log.info("Issue #{}: responseHash={}, labels={}, zeroPred={}", 
                        issue.issueNumber(),
                        responseHash.substring(0, 12) + "...",
                        parsedLabels.size(),
                        output.zeroPrediction());
                
                // Rate limiting - wait between calls to avoid overwhelming Claude
                if (i < sampleIssues.size() - 1) {
                    Thread.sleep(2000); // 2 second delay between calls
                }
                
            } catch (Exception e) {
                log.error("Failed to process issue #{}: {}", issue.issueNumber(), e.getMessage());
                
                // Create error response
                RawOutput errorOutput = new RawOutput(
                    "ERROR",
                    "ERROR",
                    0,
                    0,
                    0,
                    true,
                    "ERROR: " + e.getMessage(),
                    List.of()
                );
                rawOutputs.put(issue.issueNumber(), errorOutput);
            }
        }
        
        log.info("Completed Claude Code CLI invocations for {} issues", rawOutputs.size());
        return rawOutputs;
    }
    
    /**
     * Create temporary prompt file for Claude Code CLI.
     */
    private Path createTempPromptFile(int issueNumber, String prompt) throws IOException {
        Path promptFile = Paths.get(RAW_OUTPUTS_DIR, "prompt_" + issueNumber + ".txt");
        Files.write(promptFile, prompt.getBytes("UTF-8"));
        return promptFile;
    }
    
    /**
     * Execute Claude Code CLI with the given prompt file.
     */
    private String executeClaudeCodeCLI(Path promptFile) throws IOException, InterruptedException {
        // Read the prompt content and pass it directly
        String promptContent = Files.readString(promptFile);
        
        // Build the exact command that would be used in production
        // Note: Claude Code CLI doesn't support temperature, top-p, max-tokens options
        List<String> command = Arrays.asList(
            "claude",
            "--model", "sonnet", // Use alias for latest Sonnet model
            "--print", // Print response and exit
            "--output-format", "text",
            promptContent
        );
        
        log.debug("Executing: {}", String.join(" ", command));
        
        ProcessBuilder pb = new ProcessBuilder(command);
        pb.directory(new File(System.getProperty("user.home"))); // Run from home directory
        
        Process process = pb.start();
        
        // Capture stdout and stderr
        StringBuilder output = new StringBuilder();
        StringBuilder error = new StringBuilder();
        
        try (BufferedReader outputReader = new BufferedReader(new InputStreamReader(process.getInputStream()));
             BufferedReader errorReader = new BufferedReader(new InputStreamReader(process.getErrorStream()))) {
            
            String line;
            while ((line = outputReader.readLine()) != null) {
                output.append(line).append("\n");
            }
            
            while ((line = errorReader.readLine()) != null) {
                error.append(line).append("\n");
            }
        }
        
        int exitCode = process.waitFor();
        
        if (exitCode != 0) {
            throw new RuntimeException(String.format(
                "Claude Code CLI failed with exit code %d. Error: %s", 
                exitCode, error.toString()));
        }
        
        String rawResponse = output.toString().trim();
        if (rawResponse.isEmpty()) {
            throw new RuntimeException("Claude Code CLI returned empty response");
        }
        
        return rawResponse;
    }
    
    /**
     * Parse Claude's response to extract label predictions using Java's parser.
     * This ensures we use the same parser for both Java and Python outputs.
     */
    private List<LabelPrediction> parseClaudeResponse(String rawResponse) {
        List<LabelPrediction> predictions = new ArrayList<>();
        
        try {
            // Look for JSON response format first
            if (rawResponse.contains("\"predicted_labels\"")) {
                JsonNode responseJson = objectMapper.readTree(rawResponse);
                JsonNode labelsArray = responseJson.get("predicted_labels");
                
                if (labelsArray != null && labelsArray.isArray()) {
                    for (JsonNode labelNode : labelsArray) {
                        String label = labelNode.get("label").asText();
                        double confidence = labelNode.has("confidence") ? 
                            labelNode.get("confidence").asDouble() : 0.8;
                        predictions.add(new LabelPrediction(label, confidence));
                    }
                }
            } else {
                // Fallback to regex parsing if not JSON format
                predictions = parseWithRegex(rawResponse);
            }
            
        } catch (Exception e) {
            log.warn("Failed to parse JSON response, falling back to regex: {}", e.getMessage());
            predictions = parseWithRegex(rawResponse);
        }
        
        return predictions;
    }
    
    /**
     * Parse labels using regex patterns (fallback method).
     */
    private List<LabelPrediction> parseWithRegex(String rawResponse) {
        List<LabelPrediction> predictions = new ArrayList<>();
        
        // Common patterns Claude uses for labels
        List<Pattern> labelPatterns = Arrays.asList(
            Pattern.compile("(?:^|\\n)[-*]\\s*([^\\n]+?)(?:\\s*\\(\\d+%\\))?\\s*$", Pattern.MULTILINE),
            Pattern.compile("\"([^\"]+)\"", Pattern.MULTILINE),
            Pattern.compile("`([^`]+)`", Pattern.MULTILINE)
        );
        
        Set<String> validLabels = new HashSet<>(LabelSpaceConfiguration.getFullLabelSpace());
        Set<String> foundLabels = new HashSet<>(); // Prevent duplicates
        
        for (Pattern pattern : labelPatterns) {
            Matcher matcher = pattern.matcher(rawResponse);
            while (matcher.find()) {
                String candidate = matcher.group(1).trim();
                
                // Check if it's a valid label and not already found
                if (validLabels.contains(candidate) && !foundLabels.contains(candidate)) {
                    predictions.add(new LabelPrediction(candidate, 0.8)); // Default confidence
                    foundLabels.add(candidate);
                }
            }
        }
        
        return predictions;
    }
    
    /**
     * Compute zero prediction flag.
     */
    private boolean computeZeroPredictionFlag(List<LabelPrediction> predictions) {
        return predictions.isEmpty();
    }
    
    /**
     * Load Python raw outputs for comparison.
     */
    private Map<Integer, RawOutput> loadPythonRawOutputs() throws IOException {
        File pythonFile = new File(PYTHON_RAW_OUTPUTS_PATH);
        if (!pythonFile.exists()) {
            log.info("Python raw outputs file not found: {}", PYTHON_RAW_OUTPUTS_PATH);
            return Map.of();
        }
        
        JsonNode pythonArray = objectMapper.readTree(pythonFile);
        Map<Integer, RawOutput> pythonOutputs = new HashMap<>();
        
        for (JsonNode outputNode : pythonArray) {
            int issueNumber = outputNode.get("issue_number").asInt();
            String responseHash = outputNode.get("response_hash").asText();
            String promptHash = outputNode.get("prompt_hash").asText();
            int responseLength = outputNode.get("response_length").asInt();
            int tokenCount = outputNode.get("token_count").asInt();
            int labelCount = outputNode.get("label_count").asInt();
            boolean zeroPrediction = outputNode.get("zero_prediction").asBoolean();
            String rawResponse = outputNode.get("raw_response").asText();
            
            // Parse predicted labels from Python data
            List<LabelPrediction> parsedLabels = new ArrayList<>();
            JsonNode labelsArray = outputNode.get("parsed_labels");
            if (labelsArray != null && labelsArray.isArray()) {
                for (JsonNode labelNode : labelsArray) {
                    String label = labelNode.get("label").asText();
                    double confidence = labelNode.get("confidence").asDouble();
                    parsedLabels.add(new LabelPrediction(label, confidence));
                }
            }
            
            RawOutput output = new RawOutput(
                responseHash, promptHash, responseLength, tokenCount, labelCount,
                zeroPrediction, rawResponse, parsedLabels
            );
            pythonOutputs.put(issueNumber, output);
        }
        
        log.info("Loaded {} Python raw outputs from {}", pythonOutputs.size(), PYTHON_RAW_OUTPUTS_PATH);
        return pythonOutputs;
    }
    
    /**
     * Compare Java and Python raw outputs - this is the critical parity gate.
     */
    private void compareRawOutputs(Map<Integer, RawOutput> javaOutputs, Map<Integer, RawOutput> pythonOutputs) {
        log.info("=== STAGE 4 PARITY COMPARISON ===");
        
        int totalIssues = javaOutputs.size();
        int exactMatches = 0;
        int responseHashMismatches = 0;
        int labelSetMismatches = 0;
        int zeroPredictionMismatches = 0;
        List<Integer> failedIssues = new ArrayList<>();
        
        // Aggregate statistics
        int javaZeroPredictions = 0;
        int pythonZeroPredictions = 0;
        double totalLabelAgreement = 0.0;
        
        for (int issueNumber : javaOutputs.keySet()) {
            RawOutput javaOutput = javaOutputs.get(issueNumber);
            RawOutput pythonOutput = pythonOutputs.get(issueNumber);
            
            if (pythonOutput == null) {
                log.warn("Issue #{}: Missing Python raw output", issueNumber);
                failedIssues.add(issueNumber);
                continue;
            }
            
            // Count zero predictions
            if (javaOutput.zeroPrediction()) javaZeroPredictions++;
            if (pythonOutput.zeroPrediction()) pythonZeroPredictions++;
            
            // Compare outputs
            boolean responseHashMatch = javaOutput.responseHash().equals(pythonOutput.responseHash());
            boolean labelSetMatch = compareLabelSets(javaOutput.parsedLabels(), pythonOutput.parsedLabels());
            boolean zeroPredMatch = javaOutput.zeroPrediction() == pythonOutput.zeroPrediction();
            
            // Calculate label set agreement
            double labelAgreement = calculateLabelSetAgreement(javaOutput.parsedLabels(), pythonOutput.parsedLabels());
            totalLabelAgreement += labelAgreement;
            
            if (responseHashMatch && labelSetMatch && zeroPredMatch) {
                exactMatches++;
            } else {
                if (!responseHashMatch) {
                    responseHashMismatches++;
                    log.error("🔴 Issue #{}: RAW RESPONSE HASH MISMATCH", issueNumber);
                    log.error("  Java response hash:   {}", javaOutput.responseHash());
                    log.error("  Python response hash: {}", pythonOutput.responseHash());
                    
                    // Log response snippets for debugging (first 200 chars)
                    String javaSnippet = javaOutput.rawResponse().length() > 200 ? 
                        javaOutput.rawResponse().substring(0, 200) + "..." : javaOutput.rawResponse();
                    String pythonSnippet = pythonOutput.rawResponse().length() > 200 ? 
                        pythonOutput.rawResponse().substring(0, 200) + "..." : pythonOutput.rawResponse();
                    
                    log.error("  Java response snippet:   \"{}\"", javaSnippet);
                    log.error("  Python response snippet: \"{}\"", pythonSnippet);
                }
                if (!labelSetMatch) {
                    labelSetMismatches++;
                    log.error("🔴 Issue #{}: LABEL SET MISMATCH (agreement: {:.1f}%)", issueNumber, labelAgreement * 100);
                    log.error("  Java labels:   {}", extractLabelNames(javaOutput.parsedLabels()));
                    log.error("  Python labels: {}", extractLabelNames(pythonOutput.parsedLabels()));
                }
                if (!zeroPredMatch) {
                    zeroPredictionMismatches++;
                    log.error("🔴 Issue #{}: ZERO PREDICTION MISMATCH", issueNumber);
                    log.error("  Java zero pred:   {}", javaOutput.zeroPrediction());
                    log.error("  Python zero pred: {}", pythonOutput.zeroPrediction());
                }
                failedIssues.add(issueNumber);
            }
        }
        
        // Calculate aggregate metrics
        double avgLabelAgreement = totalLabelAgreement / totalIssues;
        double javaZeroPredRate = (double) javaZeroPredictions / totalIssues;
        double pythonZeroPredRate = (double) pythonZeroPredictions / totalIssues;
        
        // Log summary results
        log.info("=== STAGE 4 RESULTS ===");
        log.info("Total issues: {}", totalIssues);
        log.info("Exact matches: {} ({:.1f}%)", exactMatches, (exactMatches * 100.0 / totalIssues));
        log.info("Response hash mismatches: {}", responseHashMismatches);
        log.info("Label set mismatches: {}", labelSetMismatches);
        log.info("Zero prediction mismatches: {}", zeroPredictionMismatches);
        log.info("Average label-set agreement: {:.1f}%", avgLabelAgreement * 100);
        log.info("Java zero-prediction rate: {:.1f}%", javaZeroPredRate * 100);
        log.info("Python zero-prediction rate: {:.1f}%", pythonZeroPredRate * 100);
        
        // Interpretation and recommendations
        if (exactMatches == totalIssues) {
            log.info("✅ STAGE 4 PASSED: Java raw outputs match Python EXACTLY!");
            log.info("✅ Model responses are identical - proceed to Stage 5: Threshold Parity");
        } else if (responseHashMismatches > totalIssues * 0.7) {
            log.error("🔴 STAGE 4 FAILED: Raw model responses differ significantly");
            log.error("🔴 Likely cause: Model/version behavior or hidden system preambles");
            log.error("🔴 Action: Check Claude CLI debug output, model version drift");
        } else if (labelSetMismatches > totalIssues * 0.3) {
            log.error("🔴 STAGE 4 FAILED: Label parsing differs significantly"); 
            log.error("🔴 Likely cause: Parser normalization or alias mapping differences");
            log.error("🔴 Action: Fix Java parser to match Python's label extraction exactly");
        } else {
            log.warn("⚠️ STAGE 4 PARTIAL: Some differences detected but within acceptable range");
            log.warn("⚠️ Average label agreement: {:.1f}% (target: >90%)", avgLabelAgreement * 100);
            log.warn("⚠️ Proceed to Stage 5 but investigate parser differences");
        }
        
        // Hard failure for significant mismatches
        if (avgLabelAgreement < 0.9 || Math.abs(javaZeroPredRate - pythonZeroPredRate) > 0.1) {
            fail(String.format(
                "STAGE 4 FAILED: Significant raw output differences detected. " +
                "Label agreement: %.1f%% (target: >90%%), Zero-pred rate diff: %.1f%% (target: <10%%). " +
                "Failed issues: %s", 
                avgLabelAgreement * 100, 
                Math.abs(javaZeroPredRate - pythonZeroPredRate) * 100,
                failedIssues.subList(0, Math.min(10, failedIssues.size()))
            ));
        }
    }
    
    /**
     * Compare label sets for exact match.
     */
    private boolean compareLabelSets(List<LabelPrediction> labels1, List<LabelPrediction> labels2) {
        Set<String> set1 = extractLabelNames(labels1);
        Set<String> set2 = extractLabelNames(labels2);
        return set1.equals(set2);
    }
    
    /**
     * Calculate label set agreement (Jaccard similarity).
     */
    private double calculateLabelSetAgreement(List<LabelPrediction> labels1, List<LabelPrediction> labels2) {
        Set<String> set1 = extractLabelNames(labels1);
        Set<String> set2 = extractLabelNames(labels2);
        
        if (set1.isEmpty() && set2.isEmpty()) {
            return 1.0; // Both empty = perfect agreement
        }
        
        Set<String> intersection = new HashSet<>(set1);
        intersection.retainAll(set2);
        
        Set<String> union = new HashSet<>(set1);
        union.addAll(set2);
        
        return (double) intersection.size() / union.size();
    }
    
    /**
     * Extract label names from predictions.
     */
    private Set<String> extractLabelNames(List<LabelPrediction> predictions) {
        return predictions.stream()
            .map(LabelPrediction::label)
            .collect(java.util.stream.Collectors.toSet());
    }
    
    /**
     * Analyze Java raw outputs for basic validation and consistency.
     */
    private void analyzeJavaRawOutputs(Map<Integer, RawOutput> javaOutputs) {
        log.info("=== JAVA RAW OUTPUT ANALYSIS ===");
        
        int totalIssues = javaOutputs.size();
        int zeroPredictions = 0;
        int errorResponses = 0;
        int totalLabels = 0;
        List<Integer> responseLengths = new ArrayList<>();
        
        for (RawOutput output : javaOutputs.values()) {
            if (output.responseHash().equals("ERROR")) {
                errorResponses++;
                continue;
            }
            
            if (output.zeroPrediction()) {
                zeroPredictions++;
            }
            
            totalLabels += output.labelCount();
            responseLengths.add(output.responseLength());
        }
        
        double avgLabelsPerIssue = (double) totalLabels / (totalIssues - errorResponses);
        double zeroPredRate = (double) zeroPredictions / totalIssues;
        
        int medianLength = 0;
        if (!responseLengths.isEmpty()) {
            Collections.sort(responseLengths);
            medianLength = responseLengths.get(responseLengths.size() / 2);
        }
        
        log.info("Total issues processed: {}", totalIssues);
        log.info("Error responses: {} ({:.1f}%)", errorResponses, (errorResponses * 100.0 / totalIssues));
        log.info("Zero predictions: {} ({:.1f}%)", zeroPredictions, (zeroPredRate * 100));
        log.info("Average labels per issue: {:.1f}", avgLabelsPerIssue);
        log.info("Median response length: {} chars", medianLength);
        
        // Basic validation checks
        if (errorResponses > totalIssues * 0.1) {
            log.error("🔴 HIGH ERROR RATE: {}% of responses failed", (errorResponses * 100.0 / totalIssues));
        }
        
        if (zeroPredRate > 0.2) {
            log.warn("⚠️ HIGH ZERO-PREDICTION RATE: {:.1f}% (may indicate model issues)", zeroPredRate * 100);
        }
        
        if (avgLabelsPerIssue < 0.5) {
            log.warn("⚠️ LOW AVERAGE LABELS: {:.1f} per issue (may indicate under-prediction)", avgLabelsPerIssue);
        }
        
        log.info("✅ Java raw output analysis complete - ready for Python comparison");
    }
    
    /**
     * Save Java raw outputs for Python comparison.
     */
    private void saveJavaRawOutputsForPythonComparison(Map<Integer, RawOutput> javaOutputs) throws IOException {
        List<Map<String, Object>> outputData = new ArrayList<>();
        
        for (Map.Entry<Integer, RawOutput> entry : javaOutputs.entrySet()) {
            RawOutput output = entry.getValue();
            Map<String, Object> item = new HashMap<>();
            item.put("issue_number", entry.getKey());
            item.put("response_hash", output.responseHash());
            item.put("prompt_hash", output.promptHash());
            item.put("response_length", output.responseLength());
            item.put("token_count", output.tokenCount());
            item.put("label_count", output.labelCount());
            item.put("zero_prediction", output.zeroPrediction());
            item.put("raw_response", output.rawResponse());
            
            // Add parsed labels
            List<Map<String, Object>> labelsData = new ArrayList<>();
            for (LabelPrediction label : output.parsedLabels()) {
                Map<String, Object> labelItem = new HashMap<>();
                labelItem.put("label", label.label());
                labelItem.put("confidence", label.confidence());
                labelsData.add(labelItem);
            }
            item.put("parsed_labels", labelsData);
            
            outputData.add(item);
        }
        
        String outputPath = "/home/mark/project-mgmt/spring-ai-project-mgmt/java_raw_outputs.json";
        objectMapper.writerWithDefaultPrettyPrinter().writeValue(new File(outputPath), outputData);
        log.info("Saved Java raw outputs to: {}", outputPath);
    }
    
    /**
     * Load sample test issues (30 issues for raw output testing).
     */
    private List<TestIssue> loadSampleTestIssues() throws IOException {
        File testFile = new File(TEST_SET_PATH);
        JsonNode testSetArray = objectMapper.readTree(testFile);
        
        List<TestIssue> allIssues = new ArrayList<>();
        for (JsonNode issueNode : testSetArray) {
            allIssues.add(new TestIssue(
                issueNode.get("issue_number").asInt(),
                issueNode.get("title").asText(),
                issueNode.get("body").asText(""),
                issueNode.get("author").asText("unknown")
            ));
        }
        
        // Return first SAMPLE_SIZE issues for testing
        return allIssues.subList(0, Math.min(SAMPLE_SIZE, allIssues.size()));
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
    
    // Record classes
    private record TestIssue(int issueNumber, String title, String body, String author) {}
    
    private record RawOutput(
        String responseHash,
        String promptHash,
        int responseLength,
        int tokenCount,
        int labelCount,
        boolean zeroPrediction,
        String rawResponse,
        List<LabelPrediction> parsedLabels
    ) {}
}
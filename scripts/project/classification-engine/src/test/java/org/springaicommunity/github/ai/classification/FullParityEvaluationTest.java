package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.service.FilteredEvaluationService;
import org.springaicommunity.github.ai.classification.service.UnifiedClassificationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springaicommunity.github.ai.classification.config.ClassificationConfiguration;
import org.springaicommunity.github.ai.classification.service.*;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.assertj.core.api.Assertions.*;

/**
 * Full parity evaluation test - Phase 2 of Python-Java parity plan.
 * 
 * <p>This test executes the complete parity evaluation process:
 * 1. Load all 111 test issues from test_set.json
 * 2. Run Java LLM classification on each issue
 * 3. Apply Python's post-processing filter (12-label exclusion)
 * 4. Compare results against Python's validated 82.1% F1 baseline
 * 5. Generate comprehensive parity analysis report
 * </p>
 * 
 * <p><strong>Important:</strong> This test makes real Claude AI API calls and may take
 * significant time to complete. It should be run manually when ready for full evaluation.</p>
 */
@SpringJUnitConfig(classes = {
    ClassificationConfiguration.class,
    FilteredEvaluationService.class,
    PostProcessingFilter.class,
    ComprehensiveMetricsCalculator.class,
    // Add other required services
    DefaultIssueClassificationService.class,
    ClaudeLLMClient.class,
    DefaultPromptTemplateService.class,
    SpringAIContextService.class,
    UnifiedClassificationService.class,
    RuleBasedClassificationService.class,
    KeywordMatchingEngine.class,
    ContextMatchingEngine.class,
    PhraseMatchingEngine.class,
    RuleBasedConfidenceCalculator.class
})
@DisplayName("Full Parity Evaluation - Phase 2")
class FullParityEvaluationTest {
    
    private static final Logger log = LoggerFactory.getLogger(FullParityEvaluationTest.class);
    
    // Test dataset path
    private static final String TEST_SET_PATH = "/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json";
    
    @Autowired
    private UnifiedClassificationService classificationService;
    
    @Autowired
    private FilteredEvaluationService evaluationService;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    private List<TestIssue> testIssues;
    
    @BeforeEach
    void setUp() throws IOException {
        // Load test issues
        testIssues = loadTestIssues();
        log.info("Loaded {} test issues for evaluation", testIssues.size());
        
        assertThat(testIssues)
            .as("Should load exactly 111 test issues")
            .hasSize(111);
        
        log.info("Spring services initialized - ready for LLM classification");
    }
    
    @Test
    @DisplayName("Run full Java LLM classification and parity evaluation")
    void runFullParityEvaluation() throws IOException {
        log.info("=== STARTING FULL PARITY EVALUATION ===");
        log.info("This will run Java LLM classification on {} issues", testIssues.size());
        
        // Step 1: Run Java LLM classification on all test issues
        List<ClassificationResponse> javaClassificationResults = runJavaLLMClassification();
        
        // Step 2: Apply post-processing filter and evaluate
        FilteredEvaluationService.FilteredEvaluationResult parityResult = 
            evaluationService.evaluateWithPythonFiltering(javaClassificationResults, TEST_SET_PATH);
        
        // Step 3: Generate and save comprehensive report
        String report = evaluationService.generateSummaryReport(parityResult);
        saveParityReport(report, parityResult);
        
        // Step 4: Log key results
        logParityResults(parityResult);
        
        // Step 5: Verify results meet minimum expectations
        verifyParityResults(parityResult);
        
        log.info("=== FULL PARITY EVALUATION COMPLETE ===");
    }
    
    /**
     * Run Java LLM classification on all 111 test issues.
     * 
     * @return List of classification responses from Java LLM
     */
    private List<ClassificationResponse> runJavaLLMClassification() {
        log.info("Running Java LLM classification on {} issues...", testIssues.size());
        
        List<ClassificationResponse> results = new ArrayList<>();
        int processed = 0;
        
        // Get all available labels for classification (full label space for LLM)
        List<String> availableLabels = org.springaicommunity.github.ai.classification.config.LabelSpaceConfiguration.getFullLabelSpace();
        log.info("Using {} available labels for LLM classification", availableLabels.size());
        
        for (TestIssue issue : testIssues) {
            try {
                // Create classification request with full label space (matching Python approach)
                ClassificationRequest request = ClassificationRequest.builder()
                    .issueNumber(issue.issueNumber())
                    .title(issue.title())
                    .body(issue.body())
                    .availableLabels(availableLabels)
                    .build();
                
                // Classify with Java LLM
                ClassificationResponse response = classificationService.classifyWithLLM(request);
                results.add(response);
                
                processed++;
                
                // Log progress every 10 issues
                if (processed % 10 == 0) {
                    log.info("Processed {}/{} issues ({:.1f}%)", 
                            processed, testIssues.size(), 
                            (double) processed / testIssues.size() * 100);
                }
                
                // Small delay to avoid overwhelming the API
                Thread.sleep(1000);
                
            } catch (Exception e) {
                log.error("Failed to classify issue #{}: {}", issue.issueNumber(), e.getMessage());
                // Continue with other issues rather than failing completely
            }
        }
        
        log.info("Java LLM classification complete: {}/{} issues processed", 
                results.size(), testIssues.size());
        
        return results;
    }
    
    /**
     * Load test issues from test_set.json file.
     * 
     * @return List of test issues
     */
    private List<TestIssue> loadTestIssues() throws IOException {
        File testFile = new File(TEST_SET_PATH);
        assertThat(testFile)
            .as("Test dataset file should exist")
            .exists();
        
        JsonNode testSetArray = objectMapper.readTree(testFile);
        List<TestIssue> issues = new ArrayList<>();
        
        for (JsonNode issueNode : testSetArray) {
            TestIssue issue = new TestIssue(
                issueNode.get("issue_number").asInt(),
                issueNode.get("title").asText(),
                issueNode.get("body").asText(""),
                issueNode.get("author").asText("unknown"),
                extractLabels(issueNode.get("labels"))
            );
            issues.add(issue);
        }
        
        return issues;
    }
    
    /**
     * Extract labels from JSON array node.
     */
    private Set<String> extractLabels(JsonNode labelsNode) {
        Set<String> labels = new HashSet<>();
        if (labelsNode != null && labelsNode.isArray()) {
            for (JsonNode labelNode : labelsNode) {
                labels.add(labelNode.asText());
            }
        }
        return labels;
    }
    
    /**
     * Save parity evaluation report to file.
     */
    private void saveParityReport(String report, FilteredEvaluationService.FilteredEvaluationResult result) {
        try {
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd_HH-mm-ss"));
            String filename = String.format("java-parity-evaluation-%s.md", timestamp);
            File reportFile = new File(filename);
            
            try (FileWriter writer = new FileWriter(reportFile)) {
                writer.write("# Java-Python Classification Parity Evaluation Report\n\n");
                writer.write(String.format("**Generated:** %s\n", LocalDateTime.now()));
                writer.write(String.format("**Test Issues:** %d\n", result.totalPredictions()));
                writer.write(String.format("**Java Classification Results:** %d\n\n", result.totalPredictions()));
                writer.write(report);
            }
            
            log.info("Parity evaluation report saved to: {}", reportFile.getAbsolutePath());
            
        } catch (IOException e) {
            log.error("Failed to save parity report: {}", e.getMessage());
        }
    }
    
    /**
     * Log key parity results.
     */
    private void logParityResults(FilteredEvaluationService.FilteredEvaluationResult result) {
        log.info("=== PARITY EVALUATION RESULTS ===");
        
        // Unfiltered results
        double unfilteredF1 = result.unfilteredMetrics().microMetrics().f1();
        double unfilteredPrecision = result.unfilteredMetrics().microMetrics().precision();
        double unfilteredRecall = result.unfilteredMetrics().microMetrics().recall();
        
        log.info("Unfiltered Java Results:");
        log.info("  Precision: {:.3f} ({:.1f}%)", unfilteredPrecision, unfilteredPrecision * 100);
        log.info("  Recall: {:.3f} ({:.1f}%)", unfilteredRecall, unfilteredRecall * 100);
        log.info("  F1 Score: {:.3f} ({:.1f}%)", unfilteredF1, unfilteredF1 * 100);
        
        // Filtered results (target: 82.1% F1)
        double filteredF1 = result.filteredMetrics().microMetrics().f1();
        double filteredPrecision = result.filteredMetrics().microMetrics().precision();
        double filteredRecall = result.filteredMetrics().microMetrics().recall();
        
        log.info("Filtered Java Results (with Python's 12-label exclusion):");
        log.info("  Precision: {:.3f} ({:.1f}%)", filteredPrecision, filteredPrecision * 100);
        log.info("  Recall: {:.3f} ({:.1f}%)", filteredRecall, filteredRecall * 100);
        log.info("  F1 Score: {:.3f} ({:.1f}%)", filteredF1, filteredF1 * 100);
        
        // Parity analysis
        double pythonBaseline = 0.821;
        double parityPercentage = (filteredF1 / pythonBaseline) * 100;
        
        log.info("Parity Analysis:");
        log.info("  Python Baseline F1: {:.3f} ({:.1f}%)", pythonBaseline, pythonBaseline * 100);
        log.info("  Java Filtered F1: {:.3f} ({:.1f}%)", filteredF1, filteredF1 * 100);
        log.info("  Parity Achievement: {:.1f}% of Python baseline", parityPercentage);
        
        if (result.achievedParity(0.99)) {
            log.info("✅ PARITY ACHIEVED! (within 1% of Python baseline)");
        } else if (result.achievedParity(0.95)) {
            log.info("🟡 Close to parity (within 5% of Python baseline)");
        } else {
            log.info("🔴 Parity gap detected - further optimization needed");
        }
        
        // Filtering impact
        double f1Improvement = result.getF1Improvement();
        log.info("Filtering Impact: F1 improved by {:.3f} points ({:+.1f}%)", 
                f1Improvement, f1Improvement * 100);
    }
    
    /**
     * Verify parity results meet minimum expectations.
     */
    private void verifyParityResults(FilteredEvaluationService.FilteredEvaluationResult result) {
        // Verify we processed the right number of issues
        assertThat(result.totalPredictions())
            .as("Should have processed all test issues")
            .isEqualTo(111);
        
        // Verify filtering improved performance (as expected from Python experience)
        double unfilteredF1 = result.unfilteredMetrics().microMetrics().f1();
        double filteredF1 = result.filteredMetrics().microMetrics().f1();
        
        assertThat(filteredF1)
            .as("Filtered F1 should be higher than unfiltered F1 (due to removing problematic labels)")
            .isGreaterThan(unfilteredF1);
        
        // Verify metrics are reasonable (between 0 and 1)
        assertThat(filteredF1)
            .as("Filtered F1 should be a valid metric")
            .isBetween(0.0, 1.0);
        
        assertThat(result.filteredMetrics().microMetrics().precision())
            .as("Filtered precision should be a valid metric")
            .isBetween(0.0, 1.0);
        
        assertThat(result.filteredMetrics().microMetrics().recall())
            .as("Filtered recall should be a valid metric")
            .isBetween(0.0, 1.0);
        
        log.info("✅ Parity evaluation results verified - all metrics are valid");
    }
    
    /**
     * Test issue record for easier handling.
     */
    private record TestIssue(
        int issueNumber,
        String title,
        String body,
        String author,
        Set<String> labels
    ) {}
}
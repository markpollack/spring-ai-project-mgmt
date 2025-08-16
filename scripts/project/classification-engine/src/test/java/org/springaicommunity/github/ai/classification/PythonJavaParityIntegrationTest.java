package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springaicommunity.github.ai.classification.config.LabelSpaceConfiguration;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.domain.LabelPrediction;
import org.springaicommunity.github.ai.classification.service.ComprehensiveMetricsCalculator;
import org.springaicommunity.github.ai.classification.service.FilteredEvaluationService;
import org.springaicommunity.github.ai.classification.service.PostProcessingFilter;

import java.time.Duration;
import java.time.Instant;
import java.util.*;

import static org.assertj.core.api.Assertions.*;

/**
 * Integration test to demonstrate Python-Java parity evaluation.
 * 
 * <p>This test simulates the complete parity evaluation process:
 * 1. Java LLM classification results (simulated)
 * 2. Apply Python's 12-label post-processing filter
 * 3. Compare with Python's validated 82.1% F1 baseline
 * 4. Generate parity report
 * </p>
 */
@DisplayName("Python-Java Parity Integration Test")
class PythonJavaParityIntegrationTest {
    
    private static final Logger log = LoggerFactory.getLogger(PythonJavaParityIntegrationTest.class);
    
    private FilteredEvaluationService evaluationService;
    private ObjectMapper objectMapper;
    
    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        PostProcessingFilter postProcessingFilter = new PostProcessingFilter();
        ComprehensiveMetricsCalculator metricsCalculator = new ComprehensiveMetricsCalculator();
        evaluationService = new FilteredEvaluationService(
            postProcessingFilter, metricsCalculator, objectMapper);
    }
    
    @Test
    @DisplayName("Demonstrate filtering impact on F1 score - simulated perfect parity")
    void testFilteringImpactOnF1Score() {
        // Simulate Java classification results that would achieve parity with Python
        // after filtering (this demonstrates the concept without requiring real LLM calls)
        List<ClassificationResponse> simulatedJavaResults = createSimulatedParityResults();
        
        // Simulate ground truth data
        Map<Integer, Set<String>> simulatedGroundTruth = createSimulatedGroundTruth();
        
        // Manually calculate metrics to demonstrate the filtering effect
        PostProcessingFilter postProcessingFilter = new PostProcessingFilter();
        ComprehensiveMetricsCalculator metricsCalculator = new ComprehensiveMetricsCalculator();
        
        // Apply filtering
        List<ClassificationResponse> filteredResults = 
            postProcessingFilter.applyPythonFilterBatch(simulatedJavaResults);
        
        // Filter ground truth the same way
        Map<Integer, Set<String>> filteredGroundTruth = simulatedGroundTruth.entrySet().stream()
            .collect(HashMap::new, 
                (map, entry) -> {
                    Set<String> filteredLabels = entry.getValue().stream()
                        .filter(label -> !LabelSpaceConfiguration.EXCLUDED_LABELS.contains(label))
                        .collect(HashSet::new, Set::add, Set::addAll);
                    map.put(entry.getKey(), filteredLabels);
                },
                HashMap::putAll);
        
        // Calculate metrics
        var unfilteredMetrics = metricsCalculator.calculateMetrics(simulatedJavaResults, simulatedGroundTruth);
        var filteredMetrics = metricsCalculator.calculateMetrics(filteredResults, filteredGroundTruth);
        
        // Verify filtering improves performance (as expected from Python experience)
        double unfilteredF1 = unfilteredMetrics.microMetrics().f1();
        double filteredF1 = filteredMetrics.microMetrics().f1();
        
        log.info("Unfiltered F1: {:.3f}, Filtered F1: {:.3f} (improvement: +{:.3f})", 
                unfilteredF1, filteredF1, filteredF1 - unfilteredF1);
        
        // In this simulation, filtering should improve performance
        assertThat(filteredF1)
            .as("Filtered F1 should be higher than unfiltered F1 due to removing problematic labels")
            .isGreaterThan(unfilteredF1);
        
        // Verify the filtered metrics structure is correct
        assertThat(filteredMetrics.microMetrics())
            .as("Filtered metrics should have valid micro metrics")
            .isNotNull();
        
        assertThat(filteredMetrics.microMetrics().precision())
            .as("Filtered precision should be valid")
            .isBetween(0.0, 1.0);
    }
    
    @Test
    @DisplayName("Verify excluded labels are properly filtered from both predictions and ground truth")
    void testExcludedLabelsFilteredFromBothSides() {
        // Create test data with excluded labels
        List<ClassificationResponse> responses = List.of(
            createResponseWithLabels(1, List.of("vector store", "bug", "MCP")),
            createResponseWithLabels(2, List.of("enhancement", "tool/function calling")),
            createResponseWithLabels(3, List.of("question", "documentation", "help wanted"))
        );
        
        Map<Integer, Set<String>> groundTruth = Map.of(
            1, Set.of("vector store", "bug", "design"),
            2, Set.of("enhancement", "tool/function calling", "good first issue"),
            3, Set.of("question", "documentation")
        );
        
        // Apply filtering
        PostProcessingFilter filter = new PostProcessingFilter();
        List<ClassificationResponse> filteredResponses = filter.applyPythonFilterBatch(responses);
        
        // Verify predictions were filtered
        for (ClassificationResponse response : filteredResponses) {
            Set<String> predictedLabels = response.predictedLabels().stream()
                .map(LabelPrediction::label)
                .collect(HashSet::new, Set::add, Set::addAll);
            
            // Verify no excluded labels remain in predictions
            Set<String> excludedInPredictions = new HashSet<>(predictedLabels);
            excludedInPredictions.retainAll(LabelSpaceConfiguration.EXCLUDED_LABELS);
            
            assertThat(excludedInPredictions)
                .as("Issue #{} predictions should not contain excluded labels", response.issueNumber())
                .isEmpty();
        }
        
        // Verify ground truth filtering works the same way
        Map<Integer, Set<String>> filteredGroundTruth = groundTruth.entrySet().stream()
            .collect(HashMap::new,
                (map, entry) -> {
                    Set<String> filtered = entry.getValue().stream()
                        .filter(label -> !LabelSpaceConfiguration.EXCLUDED_LABELS.contains(label))
                        .collect(HashSet::new, Set::add, Set::addAll);
                    map.put(entry.getKey(), filtered);
                },
                HashMap::putAll);
        
        // Check that excluded labels were removed from ground truth
        for (Map.Entry<Integer, Set<String>> entry : filteredGroundTruth.entrySet()) {
            Set<String> excludedInGroundTruth = new HashSet<>(entry.getValue());
            excludedInGroundTruth.retainAll(LabelSpaceConfiguration.EXCLUDED_LABELS);
            
            assertThat(excludedInGroundTruth)
                .as("Issue #{} ground truth should not contain excluded labels", entry.getKey())
                .isEmpty();
        }
        
        log.info("Successfully verified that all 12 excluded labels are removed from both predictions and ground truth");
    }
    
    @Test
    @DisplayName("Demonstrate report generation for parity analysis")
    void testParityReportGeneration() {
        // Create mock evaluation result
        var unfilteredMetrics = createMockMetrics(0.632, 0.803, 0.707); // Python's unfiltered baseline
        var filteredMetrics = createMockMetrics(0.766, 0.885, 0.821);   // Python's filtered baseline
        
        var filteringStats = new PostProcessingFilter.FilteringStats(111, 85, 258, 171, 87);
        
        var result = new FilteredEvaluationService.FilteredEvaluationResult(
            unfilteredMetrics, filteredMetrics, filteringStats,
            LabelSpaceConfiguration.EXCLUDED_LABELS, 111, 111);
        
        // Generate parity report
        String report = evaluationService.generateSummaryReport(result);
        
        // Verify report structure and content
        assertThat(report)
            .as("Report should contain filtered evaluation header")
            .contains("=== JAVA FILTERED EVALUATION RESULTS ===");
            
        assertThat(report)
            .as("Report should mention all 12 excluded labels")
            .contains("(Excluding 12 labels:");
            
        assertThat(report)
            .as("Report should show Python baseline comparison")
            .contains("Python Filtered F1: 0.821");
            
        assertThat(report)
            .as("Report should indicate parity achievement")
            .contains("✅ PARITY ACHIEVED!");
        
        // Verify parity calculation
        assertThat(result.achievedParity(0.99))
            .as("Perfect parity should be detected")
            .isTrue();
        
        log.info("Generated parity report:\n{}", report);
    }
    
    /**
     * Create simulated Java classification results that would achieve parity after filtering.
     */
    private List<ClassificationResponse> createSimulatedParityResults() {
        // Create realistic classification results for a few test issues
        return List.of(
            // Issue 1: Perfect prediction
            createResponseWithLabels(1, List.of("vector store", "pgvector")),
            
            // Issue 2: Good prediction with some excluded labels (will be filtered)
            createResponseWithLabels(2, List.of("tool/function calling", "bug", "enhancement")),
            
            // Issue 3: Mix of good and excluded predictions
            createResponseWithLabels(3, List.of("MCP", "documentation", "question", "help wanted")),
            
            // Issue 4: Perfect prediction
            createResponseWithLabels(4, List.of("anthropic", "claude")),
            
            // Issue 5: Good prediction  
            createResponseWithLabels(5, List.of("type: backport"))
        );
    }
    
    /**
     * Create simulated ground truth that matches realistic Spring AI issue patterns.
     */
    private Map<Integer, Set<String>> createSimulatedGroundTruth() {
        return Map.of(
            1, Set.of("vector store", "pgvector"),
            2, Set.of("tool/function calling", "bug"),  // bug will be filtered
            3, Set.of("MCP", "documentation", "question"), // question will be filtered  
            4, Set.of("anthropic"),
            5, Set.of("type: backport")
        );
    }
    
    private ClassificationResponse createResponseWithLabels(int issueNumber, List<String> labels) {
        List<LabelPrediction> predictions = labels.stream()
            .map(label -> new LabelPrediction(label, 0.8))
            .collect(ArrayList::new, List::add, List::addAll);
        
        return ClassificationResponse.builder()
            .issueNumber(issueNumber)
            .predictedLabels(predictions)
            .explanation("Simulated classification")
            .processingTime(Duration.ofMillis(1000))
            .timestamp(Instant.now())
            .build();
    }
    
    private ComprehensiveMetricsCalculator.MetricsBundle createMockMetrics(
            double precision, double recall, double f1) {
        var microMetrics = new ComprehensiveMetricsCalculator.MicroMetrics(
            10, 5, 3, precision, recall, f1);
        var macroMetrics = new ComprehensiveMetricsCalculator.MacroMetrics(
            precision, recall, f1, 5);
        var multiLabelMetrics = new ComprehensiveMetricsCalculator.MultiLabelMetrics(
            0.5, 0.3, 2.0, 1.8);
        
        return new ComprehensiveMetricsCalculator.MetricsBundle(
            microMetrics, macroMetrics, Collections.emptyMap(),
            multiLabelMetrics, Collections.emptyList());
    }
}
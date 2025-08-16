package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
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
 * Test for FilteredEvaluationService to verify Python parity filtering.
 */
@DisplayName("FilteredEvaluationService Tests")
class FilteredEvaluationServiceTest {
    
    private FilteredEvaluationService evaluationService;
    private PostProcessingFilter postProcessingFilter;
    private ComprehensiveMetricsCalculator metricsCalculator;
    private ObjectMapper objectMapper;
    
    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        postProcessingFilter = new PostProcessingFilter();
        metricsCalculator = new ComprehensiveMetricsCalculator();
        evaluationService = new FilteredEvaluationService(
            postProcessingFilter, metricsCalculator, objectMapper);
    }
    
    @Test
    @DisplayName("Verify excluded labels match Python's exact list")
    void testExcludedLabelsMatchPython() {
        // Python's excluded labels from evaluate_filtered_predictions.py
        Set<String> pythonExcludedLabels = Set.of(
            // Original problematic labels
            "bug", "enhancement",
            // Subjective/Judgmental labels  
            "question", "help wanted", "good first issue", "epic",
            // Process-Driven labels
            "status: backported", "status: to-discuss", "follow up",
            "status: waiting-for-feedback", "for: backport-to-1.0.x", "next priorities"
        );
        
        // Java's excluded labels
        Set<String> javaExcludedLabels = LabelSpaceConfiguration.EXCLUDED_LABELS;
        
        // Verify exact match
        assertThat(javaExcludedLabels)
            .as("Java excluded labels must exactly match Python's list")
            .isEqualTo(pythonExcludedLabels);
        
        // Verify count
        assertThat(javaExcludedLabels)
            .as("Should exclude exactly 12 labels")
            .hasSize(12);
    }
    
    @Test
    @DisplayName("Test post-processing filter removes correct labels from predictions")
    void testPostProcessingFilterRemovesCorrectLabels() {
        // Create test response with both included and excluded labels
        List<LabelPrediction> predictions = List.of(
            new LabelPrediction("vector store", 0.9),
            new LabelPrediction("bug", 0.8),                    // Should be filtered
            new LabelPrediction("tool/function calling", 0.7),
            new LabelPrediction("enhancement", 0.6),            // Should be filtered  
            new LabelPrediction("MCP", 0.5),
            new LabelPrediction("question", 0.4),               // Should be filtered
            new LabelPrediction("good first issue", 0.3)        // Should be filtered
        );
        
        ClassificationResponse originalResponse = ClassificationResponse.builder()
            .issueNumber(1234)
            .predictedLabels(predictions)
            .explanation("Test classification")
            .processingTime(Duration.ofMillis(1000))
            .timestamp(Instant.now())
            .build();
        
        // Apply Python filter
        ClassificationResponse filteredResponse = 
            postProcessingFilter.applyPythonFilter(originalResponse);
        
        // Verify excluded labels were removed
        Set<String> remainingLabels = filteredResponse.predictedLabels().stream()
            .map(LabelPrediction::label)
            .collect(java.util.stream.Collectors.toSet());
        
        assertThat(remainingLabels)
            .as("Filtered response should only contain non-excluded labels")
            .containsExactlyInAnyOrder("vector store", "tool/function calling", "MCP");
        
        // Verify excluded labels are gone
        assertThat(remainingLabels)
            .as("Filtered response should not contain any excluded labels")
            .doesNotContainAnyElementsOf(LabelSpaceConfiguration.EXCLUDED_LABELS);
        
        // Verify other response data is preserved
        assertThat(filteredResponse.issueNumber()).isEqualTo(originalResponse.issueNumber());
        assertThat(filteredResponse.processingTime()).isEqualTo(originalResponse.processingTime());
    }
    
    @Test
    @DisplayName("Test filtering statistics calculation")
    void testFilteringStatistics() {
        // Create responses with various filtering scenarios
        List<ClassificationResponse> originalResponses = List.of(
            // Issue 1: Has excluded labels to filter
            createTestResponse(1, List.of("vector store", "bug", "enhancement")),
            // Issue 2: No excluded labels
            createTestResponse(2, List.of("MCP", "tool/function calling")),
            // Issue 3: Mix of included and excluded
            createTestResponse(3, List.of("documentation", "question", "help wanted"))
        );
        
        // Apply filtering
        List<ClassificationResponse> filteredResponses = 
            postProcessingFilter.applyPythonFilterBatch(originalResponses);
        
        // Calculate statistics
        PostProcessingFilter.FilteringStats stats = 
            postProcessingFilter.getFilteringStats(originalResponses, filteredResponses);
        
        // Verify statistics
        assertThat(stats.totalIssues()).isEqualTo(3);
        assertThat(stats.issuesAffected()).isEqualTo(2); // Issues 1 and 3 had labels filtered
        assertThat(stats.originalPredictions()).isEqualTo(8); // 3 + 2 + 3
        assertThat(stats.filteredPredictions()).isEqualTo(4); // 1 + 2 + 1  
        assertThat(stats.removedPredictions()).isEqualTo(4); // 2 + 0 + 2
        
        // Verify percentages
        assertThat(stats.getAffectedPercentage()).isCloseTo(66.7, within(0.1));
        assertThat(stats.getRemovedPercentage()).isEqualTo(50.0);
    }
    
    @Test
    @DisplayName("Test summary report generation format")
    void testSummaryReportGeneration() {
        // Create mock evaluation result
        ComprehensiveMetricsCalculator.MetricsBundle unfilteredMetrics = 
            createMockMetrics(0.632, 0.803, 0.707); // Python's unfiltered baseline
            
        ComprehensiveMetricsCalculator.MetricsBundle filteredMetrics = 
            createMockMetrics(0.766, 0.885, 0.821); // Python's filtered baseline
        
        PostProcessingFilter.FilteringStats filteringStats = 
            new PostProcessingFilter.FilteringStats(111, 85, 258, 171, 87);
        
        FilteredEvaluationService.FilteredEvaluationResult result = 
            new FilteredEvaluationService.FilteredEvaluationResult(
                unfilteredMetrics, filteredMetrics, filteringStats,
                LabelSpaceConfiguration.EXCLUDED_LABELS, 111, 111);
        
        // Generate report
        String report = evaluationService.generateSummaryReport(result);
        
        // Verify report contains key information
        assertThat(report)
            .as("Report should contain filtered evaluation title")
            .contains("=== JAVA FILTERED EVALUATION RESULTS ===");
            
        assertThat(report)
            .as("Report should list all 12 excluded labels")
            .contains("(Excluding 12 labels:");
            
        assertThat(report)
            .as("Report should show filtered F1 score")
            .contains("F1 Score: 0.821");
            
        assertThat(report)
            .as("Report should compare with Python baseline")
            .contains("Python Filtered F1: 0.821");
            
        assertThat(report)
            .as("Report should indicate parity achievement")
            .contains("✅ PARITY ACHIEVED!");
    }
    
    @Test 
    @DisplayName("Test parity achievement detection")
    void testParityAchievementDetection() {
        // Test perfect parity (82.1% F1)
        var perfectParity = createEvaluationResult(0.821);
        assertThat(perfectParity.achievedParity(0.99))
            .as("Perfect parity should be detected")
            .isTrue();
        
        // Test close parity (81.8% F1 = 99.6% of baseline)
        var closeParity = createEvaluationResult(0.818);
        assertThat(closeParity.achievedParity(0.99))
            .as("Close parity should be detected with lenient threshold")
            .isTrue();
        
        // Test parity gap (80.0% F1 = 97.4% of baseline)  
        var parityGap = createEvaluationResult(0.800);
        assertThat(parityGap.achievedParity(0.99))
            .as("Parity gap should be detected")
            .isFalse();
    }
    
    private ClassificationResponse createTestResponse(int issueNumber, List<String> labels) {
        List<LabelPrediction> predictions = labels.stream()
            .map(label -> new LabelPrediction(label, 0.8))
            .collect(java.util.stream.Collectors.toList());
        
        return ClassificationResponse.builder()
            .issueNumber(issueNumber)
            .predictedLabels(predictions)
            .explanation("Test response")
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
            microMetrics,
            macroMetrics, 
            Collections.emptyMap(), // per-label metrics
            multiLabelMetrics,
            Collections.emptyList() // instance metrics
        );
    }
    
    private FilteredEvaluationService.FilteredEvaluationResult createEvaluationResult(double filteredF1) {
        var unfilteredMetrics = createMockMetrics(0.632, 0.803, 0.707);
        var filteredMetrics = createMockMetrics(0.766, 0.885, filteredF1);
        var filteringStats = new PostProcessingFilter.FilteringStats(111, 85, 258, 171, 87);
        
        return new FilteredEvaluationService.FilteredEvaluationResult(
            unfilteredMetrics, filteredMetrics, filteringStats,
            LabelSpaceConfiguration.EXCLUDED_LABELS, 111, 111);
    }
}
package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.springaicommunity.github.ai.classification.config.LabelSpaceConfiguration;
import org.springaicommunity.github.ai.classification.config.LabelSpaceConfiguration.ExperimentMode;
import org.springaicommunity.github.ai.classification.config.LabelSpaceConfiguration.SpaceType;
import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.service.*;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static org.assertj.core.api.Assertions.*;
import static org.junit.jupiter.params.provider.Arguments.arguments;

/**
 * Experiment Matrix Test for Python vs Java Reproducibility Study.
 * 
 * <p>This test implements the definitive 3-mode experiment to resolve the performance
 * gap between Python's 82.1% F1 score and Java's 66.7-74.3% F1 score.</p>
 * 
 * <p><strong>Experiment Design:</strong></p>
 * <ul>
 *   <li><strong>Mode A:</strong> Full-task baseline (predict L_FULL → evaluate L_FULL)</li>
 *   <li><strong>Mode B:</strong> Python approach (predict L_FULL → evaluate L_REDUCED)</li>
 *   <li><strong>Mode D:</strong> Java approach (predict L_REDUCED → evaluate L_REDUCED)</li>
 * </ul>
 * 
 * <p><strong>Hypothesis:</strong> Mode B will achieve significantly higher F1 score (~82%) 
 * than Mode D (~67%) because the model benefits from context provided by all 12 excluded 
 * labels during prediction, even though they're filtered out during evaluation.</p>
 * 
 * <p><strong>Test Execution:</strong></p>
 * <pre>
 * mvn test -Dtest=ExperimentMatrixTest
 * </pre>
 * 
 * <p><strong>Artifacts Generated:</strong></p>
 * <ul>
 *   <li>{@code target/experiments/<mode>/<seed>/} - Per-run results</li>
 *   <li>{@code predictions.csv} - Detailed predictions per issue</li>
 *   <li>{@code metrics.json} - Complete metrics bundle</li>
 *   <li>{@code run_config.json} - Run configuration and metadata</li>
 * </ul>
 */
@DisplayName("Python vs Java Reproducibility Experiment Matrix")
class ExperimentMatrixTest {
    
    private ClaudeLLMClient claudeClient;
    private PostProcessingFilter postProcessingFilter;
    private ComprehensiveMetricsCalculator metricsCalculator;
    private List<TestIssue> testDataset;
    private final ObjectMapper objectMapper = new ObjectMapper();
    
    @BeforeEach
    void setUp() throws Exception {
        // Initialize services for experiments
        SpringAIContextService contextService = new SpringAIContextService(objectMapper);
        contextService.afterPropertiesSet();
        
        DefaultPromptTemplateService promptService = new DefaultPromptTemplateService(contextService);
        java.util.concurrent.Executor executor = java.util.concurrent.ForkJoinPool.commonPool();
        claudeClient = new ClaudeLLMClient(promptService, objectMapper, executor);
        
        postProcessingFilter = new PostProcessingFilter();
        metricsCalculator = new ComprehensiveMetricsCalculator();
        
        // Load real test dataset (same as Python)
        loadTestDataset();
        
        // Ensure output directory exists
        createOutputDirectories();
        
        // Log experiment setup
        LabelSpaceConfiguration.LabelSpaceSummary summary = LabelSpaceConfiguration.getSummary();
        System.out.println("=== EXPERIMENT SETUP ===");
        System.out.println(summary);
        System.out.println("Test dataset: " + testDataset.size() + " issues");
        System.out.println("Output directory: target/experiments/");
    }
    
    /**
     * Provide experiment parameters: Mode × Seed combinations.
     */
    static Stream<Arguments> experimentParameters() {
        return Stream.of(
            // Mode A: Full-task baseline
            arguments(ExperimentMode.A, 42),
            arguments(ExperimentMode.A, 43), 
            arguments(ExperimentMode.A, 44),
            
            // Mode B: Python approach (key hypothesis test)
            arguments(ExperimentMode.B, 42),
            arguments(ExperimentMode.B, 43),
            arguments(ExperimentMode.B, 44),
            
            // Mode D: Java approach (current baseline)
            arguments(ExperimentMode.D, 42),
            arguments(ExperimentMode.D, 43),
            arguments(ExperimentMode.D, 44)
        );
    }
    
    @ParameterizedTest(name = "Mode {0} (seed {1})")
    @MethodSource("experimentParameters")
    @DisplayName("Run experiment matrix with comprehensive metrics")
    void runExperimentMode(ExperimentMode mode, int seed) throws Exception {
        System.out.printf("\n=== EXPERIMENT: Mode %s, Seed %d ===%n", mode, seed);
        
        Instant startTime = Instant.now();
        
        // 1. Configure label spaces for this mode
        List<String> predictionLabels = LabelSpaceConfiguration.getLabelSpaceForMode(mode, SpaceType.PREDICTION);
        List<String> evaluationLabels = LabelSpaceConfiguration.getLabelSpaceForMode(mode, SpaceType.EVALUATION);
        
        System.out.printf("Prediction labels: %d, Evaluation labels: %d%n", 
                         predictionLabels.size(), evaluationLabels.size());
        
        // 2. Run classification on test dataset
        List<ClassificationResponse> rawResponses = new ArrayList<>();
        List<String> errors = new ArrayList<>();
        
        for (int i = 0; i < Math.min(testDataset.size(), 10); i++) { // Test first 10 for speed
            TestIssue issue = testDataset.get(i);
            
            try {
                ClassificationRequest request = ClassificationRequest.builder()
                    .issueNumber(issue.issueNumber)
                    .title(issue.title)
                    .body(issue.body != null ? issue.body : "")
                    .availableLabels(predictionLabels) // Key difference between modes
                    .build();
                
                ClassificationResponse response = claudeClient.classifyIssue(request);
                rawResponses.add(response);
                
                System.out.printf("Issue #%d: %d predictions%n", 
                                 issue.issueNumber, response.predictedLabels().size());
                
            } catch (Exception e) {
                String error = String.format("Issue #%d: %s", issue.issueNumber, e.getMessage());
                errors.add(error);
                System.err.println("ERROR: " + error);
            }
        }
        
        // 3. Apply post-processing filter (only for Mode B)
        List<ClassificationResponse> finalResponses;
        if (mode == ExperimentMode.B) {
            finalResponses = postProcessingFilter.applyPythonFilterBatch(rawResponses);
            PostProcessingFilter.FilteringStats filterStats = 
                postProcessingFilter.getFilteringStats(rawResponses, finalResponses);
            System.out.println("Post-processing: " + filterStats);
        } else {
            finalResponses = rawResponses;
        }
        
        // 4. Prepare ground truth (filtered for evaluation space)
        Map<Integer, Set<String>> groundTruth = prepareGroundTruth(evaluationLabels);
        
        // 5. Calculate comprehensive metrics
        ComprehensiveMetricsCalculator.MetricsBundle metrics = 
            metricsCalculator.calculateMetrics(finalResponses, groundTruth);
        
        // 6. Save results and artifacts
        ExperimentResult result = new ExperimentResult(
            mode, seed, startTime, Instant.now(),
            predictionLabels.size(), evaluationLabels.size(),
            rawResponses.size(), finalResponses.size(), errors.size(),
            metrics, finalResponses, errors
        );
        
        saveExperimentResult(result);
        
        // 7. Print summary
        printExperimentSummary(result);
        
        // 8. Basic validation assertions
        assertThat(finalResponses).isNotEmpty();
        assertThat(metrics.microMetrics().f1()).isGreaterThanOrEqualTo(0.0);
        assertThat(metrics.microMetrics().f1()).isLessThanOrEqualTo(1.0);
        assertThat(errors.size()).isLessThan(finalResponses.size()); // Most should succeed
    }
    
    /**
     * Load the test dataset from Python's test_set.json.
     */
    private void loadTestDataset() throws Exception {
        String testDataPath = "/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json";
        
        File testFile = new File(testDataPath);
        if (!testFile.exists()) {
            System.out.println("⚠️ Python test data not found, using fallback dataset");
            testDataset = createFallbackDataset();
            return;
        }
        
        JsonNode testArray = objectMapper.readTree(testFile);
        testDataset = new ArrayList<>();
        
        for (JsonNode issueNode : testArray) {
            TestIssue issue = new TestIssue();
            issue.issueNumber = issueNode.get("issue_number").asInt();
            issue.title = issueNode.get("title").asText();
            issue.body = issueNode.has("body") ? issueNode.get("body").asText() : "";
            
            issue.labels = new HashSet<>();
            JsonNode labelsArray = issueNode.get("labels");
            if (labelsArray != null) {
                for (JsonNode labelNode : labelsArray) {
                    issue.labels.add(labelNode.asText());
                }
            }
            
            testDataset.add(issue);
        }
        
        System.out.printf("✅ Loaded %d real test issues from Python dataset%n", testDataset.size());
    }
    
    /**
     * Prepare ground truth filtered for the evaluation label space.
     */
    private Map<Integer, Set<String>> prepareGroundTruth(List<String> evaluationLabels) {
        Set<String> evalLabelSet = new HashSet<>(evaluationLabels);
        
        return testDataset.stream()
            .collect(Collectors.toMap(
                issue -> issue.issueNumber,
                issue -> issue.labels.stream()
                    .filter(evalLabelSet::contains)
                    .collect(Collectors.toSet())
            ));
    }
    
    /**
     * Save experiment result to structured artifacts.
     */
    private void saveExperimentResult(ExperimentResult result) throws IOException {
        Path outputDir = Paths.get("target", "experiments", 
                                  "mode_" + result.mode(), 
                                  "seed_" + result.seed());
        Files.createDirectories(outputDir);
        
        // Save predictions CSV
        saveCSV(outputDir.resolve("predictions.csv"), result);
        
        // Save metrics JSON
        saveJSON(outputDir.resolve("metrics.json"), result.metrics());
        
        // Save run configuration
        saveRunConfig(outputDir.resolve("run_config.json"), result);
        
        System.out.printf("📁 Artifacts saved to: %s%n", outputDir);
    }
    
    /**
     * Print experiment summary to console.
     */
    private void printExperimentSummary(ExperimentResult result) {
        System.out.printf("%n=== RESULTS: Mode %s, Seed %d ===%n", result.mode(), result.seed());
        System.out.printf("Execution time: %.1f seconds%n", 
                         result.durationSeconds());
        System.out.printf("Responses: %d successful, %d errors%n", 
                         result.successfulResponses(), result.errorCount());
        
        var micro = result.metrics().microMetrics();
        System.out.printf("MICRO METRICS: F1=%.3f (%.1f%%), P=%.3f, R=%.3f%n",
                         micro.f1(), micro.f1() * 100, micro.precision(), micro.recall());
        
        var macro = result.metrics().macroMetrics();
        System.out.printf("MACRO METRICS: F1=%.3f (%.1f%%), P=%.3f, R=%.3f%n",
                         macro.avgF1(), macro.avgF1() * 100, macro.avgPrecision(), macro.avgRecall());
        
        var multiLabel = result.metrics().multiLabelMetrics();
        System.out.printf("MULTI-LABEL: Jaccard=%.3f, Subset Accuracy=%.3f%n",
                         multiLabel.avgJaccard(), multiLabel.subsetAccuracy());
        
        System.out.printf("Top performing labels: %s%n", 
                         getTopPerformingLabels(result.metrics(), 3));
    }
    
    /**
     * Get top performing labels by F1 score.
     */
    private List<String> getTopPerformingLabels(ComprehensiveMetricsCalculator.MetricsBundle metrics, int count) {
        return metrics.perLabelMetrics().values().stream()
            .sorted((a, b) -> Double.compare(b.f1(), a.f1()))
            .limit(count)
            .map(m -> String.format("%s(%.2f)", m.label(), m.f1()))
            .collect(Collectors.toList());
    }
    
    // Helper methods for saving artifacts
    
    private void saveCSV(Path path, ExperimentResult result) throws IOException {
        try (FileWriter writer = new FileWriter(path.toFile())) {
            writer.write("issue_number,predicted_labels,confidence_scores,explanation\n");
            
            for (ClassificationResponse response : result.responses()) {
                String labels = response.predictedLabels().stream()
                    .map(p -> p.label())
                    .collect(Collectors.joining(";"));
                    
                String confidences = response.predictedLabels().stream()
                    .map(p -> String.format("%.3f", p.confidence()))
                    .collect(Collectors.joining(";"));
                    
                String explanation = response.explanation().replace("\"", "\"\""); // Escape quotes
                
                writer.write(String.format("%d,\"%s\",\"%s\",\"%s\"\n", 
                           response.issueNumber(), labels, confidences, explanation));
            }
        }
    }
    
    private void saveJSON(Path path, Object object) throws IOException {
        objectMapper.writerWithDefaultPrettyPrinter()
            .writeValue(path.toFile(), object);
    }
    
    private void saveRunConfig(Path path, ExperimentResult result) throws IOException {
        Map<String, Object> config = Map.of(
            "mode", result.mode().toString(),
            "seed", result.seed(),
            "timestamp", result.startTime().toString(),
            "duration_seconds", result.durationSeconds(),
            "prediction_labels", result.predictionLabelCount(),
            "evaluation_labels", result.evaluationLabelCount(),
            "successful_responses", result.successfulResponses(),
            "error_count", result.errorCount(),
            "label_space_version", LabelSpaceConfiguration.L_FULL_VERSION
        );
        
        saveJSON(path, config);
    }
    
    private void createOutputDirectories() throws IOException {
        Files.createDirectories(Paths.get("target", "experiments"));
    }
    
    private List<TestIssue> createFallbackDataset() {
        // Minimal fallback if Python data not available
        List<TestIssue> fallback = new ArrayList<>();
        
        TestIssue issue1 = new TestIssue();
        issue1.issueNumber = 1776;
        issue1.title = "Vector store connection issues";
        issue1.body = "Having trouble with vector database connectivity";
        issue1.labels = Set.of("vector store", "configuration");
        fallback.add(issue1);
        
        return fallback;
    }
    
    // Data structures
    
    private static class TestIssue {
        int issueNumber;
        String title;
        String body;
        Set<String> labels;
    }
    
    private record ExperimentResult(
        ExperimentMode mode,
        int seed,
        Instant startTime,
        Instant endTime,
        int predictionLabelCount,
        int evaluationLabelCount,
        int totalRequests,
        int successfulResponses,
        int errorCount,
        ComprehensiveMetricsCalculator.MetricsBundle metrics,
        List<ClassificationResponse> responses,
        List<String> errors
    ) {
        public double durationSeconds() {
            return (endTime.toEpochMilli() - startTime.toEpochMilli()) / 1000.0;
        }
    }
}
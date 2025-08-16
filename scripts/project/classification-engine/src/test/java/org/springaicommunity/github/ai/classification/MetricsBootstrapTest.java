package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springaicommunity.github.ai.classification.config.LabelSpaceConfiguration.ExperimentMode;
import org.springaicommunity.github.ai.classification.service.ComprehensiveMetricsCalculator;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.*;

/**
 * Bootstrap confidence interval testing for statistical analysis of experiment results.
 * 
 * <p>This test performs statistical analysis on the results from ExperimentMatrixTest
 * to determine if the differences between modes are statistically significant.</p>
 * 
 * <p><strong>Key Analysis:</strong></p>
 * <ul>
 *   <li><strong>Bootstrap Confidence Intervals:</strong> 95% CI for F1 scores</li>
 *   <li><strong>Paired Comparisons:</strong> Mode B vs Mode D (key hypothesis test)</li>
 *   <li><strong>Statistical Significance:</strong> p-values for mode differences</li>
 *   <li><strong>Effect Size:</strong> Cohen's d for practical significance</li>
 * </ul>
 * 
 * <p><strong>Prerequisites:</strong> Must run after ExperimentMatrixTest has generated artifacts.</p>
 * 
 * <p><strong>Test Execution:</strong></p>
 * <pre>
 * # Run experiments first, then statistical analysis
 * mvn test -Dtest=ExperimentMatrixTest
 * mvn test -Dtest=MetricsBootstrapTest
 * </pre>
 * 
 * <p><strong>Output:</strong></p>
 * <ul>
 *   <li>{@code target/experiments/summary/} - Statistical analysis results</li>
 *   <li>{@code bootstrap_confidence.json} - Confidence intervals</li>
 *   <li>{@code mode_comparison.json} - Pairwise comparisons</li>
 *   <li>{@code final_report.md} - Human-readable analysis report</li>
 * </ul>
 */
@DisplayName("Bootstrap Statistical Analysis of Experiment Results")
class MetricsBootstrapTest {
    
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final Random random = new Random(12345); // Fixed seed for reproducibility
    private static final int BOOTSTRAP_SAMPLES = 1000;
    private static final double CONFIDENCE_LEVEL = 0.95;
    
    @BeforeEach
    void setUp() throws IOException {
        // Ensure summary directory exists
        Files.createDirectories(Paths.get("target", "experiments", "summary"));
    }
    
    @Test
    @DisplayName("Bootstrap confidence intervals for all experiment modes")
    void computeBootstrapConfidenceIntervals() throws IOException {
        System.out.println("\n=== BOOTSTRAP CONFIDENCE INTERVAL ANALYSIS ===");
        
        // Load results for all modes
        Map<ExperimentMode, List<ModeResult>> modeResults = loadModeResults();
        
        if (modeResults.isEmpty()) {
            fail("No experiment results found. Run ExperimentMatrixTest first.");
        }
        
        // Calculate bootstrap confidence intervals for each mode
        Map<ExperimentMode, BootstrapResult> bootstrapResults = new HashMap<>();
        
        for (ExperimentMode mode : modeResults.keySet()) {
            List<ModeResult> results = modeResults.get(mode);
            
            if (results.isEmpty()) {
                System.out.printf("⚠️ No results found for Mode %s%n", mode);
                continue;
            }
            
            System.out.printf("\n--- Mode %s Analysis ---%n", mode);
            System.out.printf("Runs available: %d%n", results.size());
            
            BootstrapResult bootstrap = computeBootstrap(results);
            bootstrapResults.put(mode, bootstrap);
            
            System.out.printf("Micro F1: %.3f [%.3f, %.3f] (95%% CI)%n", 
                             bootstrap.microF1Mean, bootstrap.microF1LowerCI, bootstrap.microF1UpperCI);
            System.out.printf("Macro F1: %.3f [%.3f, %.3f] (95%% CI)%n",
                             bootstrap.macroF1Mean, bootstrap.macroF1LowerCI, bootstrap.macroF1UpperCI);
        }
        
        // Save bootstrap results
        saveBootstrapResults(bootstrapResults);
        
        // Validate that we have meaningful results
        assertThat(bootstrapResults).isNotEmpty();
        for (BootstrapResult result : bootstrapResults.values()) {
            assertThat(result.microF1Mean).isBetween(0.0, 1.0);
            assertThat(result.macroF1Mean).isBetween(0.0, 1.0);
        }
    }
    
    @Test
    @DisplayName("Statistical comparison: Mode B vs Mode D (key hypothesis test)")
    void compareModeBvsD() throws IOException {
        System.out.println("\n=== MODE B vs MODE D COMPARISON ===");
        System.out.println("Hypothesis: Mode B (Python approach) > Mode D (Java approach)");
        
        // Load results for modes B and D
        List<ModeResult> modeB = loadResultsForMode(ExperimentMode.B);
        List<ModeResult> modeD = loadResultsForMode(ExperimentMode.D);
        
        if (modeB.isEmpty() || modeD.isEmpty()) {
            fail("Missing results for Mode B or D. Run ExperimentMatrixTest first.");
        }
        
        System.out.printf("Mode B runs: %d, Mode D runs: %d%n", modeB.size(), modeD.size());
        
        // Compute paired comparison statistics
        ComparisonResult comparison = computePairedComparison(modeB, modeD);
        
        System.out.println("\n--- Micro F1 Comparison ---");
        System.out.printf("Mode B mean: %.3f (%.1f%%)%n", comparison.bMicroF1Mean, comparison.bMicroF1Mean * 100);
        System.out.printf("Mode D mean: %.3f (%.1f%%)%n", comparison.dMicroF1Mean, comparison.dMicroF1Mean * 100);
        System.out.printf("Difference: %.3f (%.1f%% points)%n", comparison.microF1Difference, comparison.microF1Difference * 100);
        System.out.printf("Effect size (Cohen's d): %.3f%n", comparison.microF1CohenD);
        System.out.printf("Bootstrap p-value: %.4f%n", comparison.microF1PValue);
        
        System.out.println("\n--- Macro F1 Comparison ---");
        System.out.printf("Mode B mean: %.3f (%.1f%%)%n", comparison.bMacroF1Mean, comparison.bMacroF1Mean * 100);
        System.out.printf("Mode D mean: %.3f (%.1f%%)%n", comparison.dMacroF1Mean, comparison.dMacroF1Mean * 100);
        System.out.printf("Difference: %.3f (%.1f%% points)%n", comparison.macroF1Difference, comparison.macroF1Difference * 100);
        System.out.printf("Effect size (Cohen's d): %.3f%n", comparison.macroF1CohenD);
        System.out.printf("Bootstrap p-value: %.4f%n", comparison.macroF1PValue);
        
        // Interpret results
        interpretComparison(comparison);
        
        // Save comparison results
        saveComparisonResults(comparison);
        
        // Statistical validation
        assertThat(comparison.microF1PValue).isBetween(0.0, 1.0);
        assertThat(comparison.macroF1PValue).isBetween(0.0, 1.0);
    }
    
    @Test
    @DisplayName("Generate comprehensive final report")
    void generateFinalReport() throws IOException {
        System.out.println("\n=== GENERATING FINAL REPORT ===");
        
        // Load all available data
        Map<ExperimentMode, List<ModeResult>> allResults = loadModeResults();
        Map<ExperimentMode, BootstrapResult> bootstrapResults = loadBootstrapResults();
        ComparisonResult comparison = loadComparisonResults();
        
        // Generate markdown report
        StringBuilder report = new StringBuilder();
        
        addReportHeader(report);
        addExecutiveSummary(report, allResults, comparison);
        addDetailedResults(report, allResults, bootstrapResults);
        addStatisticalAnalysis(report, comparison);
        addConclusions(report, comparison);
        addMethodology(report);
        
        // Save report
        Path reportPath = Paths.get("target", "experiments", "summary", "final_report.md");
        Files.writeString(reportPath, report.toString());
        
        System.out.printf("📄 Final report generated: %s%n", reportPath);
        
        // Validate report content
        String reportContent = report.toString();
        assertThat(reportContent).contains("# Reproducibility Experiment Results");
        assertThat(reportContent).contains("Mode B vs Mode D");
        assertThat(reportContent).contains("Statistical Significance");
    }
    
    /**
     * Load experiment results for all modes.
     */
    private Map<ExperimentMode, List<ModeResult>> loadModeResults() throws IOException {
        Map<ExperimentMode, List<ModeResult>> results = new HashMap<>();
        
        for (ExperimentMode mode : ExperimentMode.values()) {
            results.put(mode, loadResultsForMode(mode));
        }
        
        return results;
    }
    
    /**
     * Load experiment results for a specific mode.
     */
    private List<ModeResult> loadResultsForMode(ExperimentMode mode) throws IOException {
        List<ModeResult> results = new ArrayList<>();
        Path modeDir = Paths.get("target", "experiments", "mode_" + mode);
        
        if (!Files.exists(modeDir)) {
            return results;
        }
        
        Files.list(modeDir)
            .filter(Files::isDirectory)
            .forEach(seedDir -> {
                try {
                    Path metricsFile = seedDir.resolve("metrics.json");
                    if (Files.exists(metricsFile)) {
                        JsonNode metrics = objectMapper.readTree(metricsFile.toFile());
                        
                        double microF1 = metrics.path("microMetrics").path("f1").asDouble();
                        double macroF1 = metrics.path("macroMetrics").path("avgF1").asDouble();
                        
                        int seed = Integer.parseInt(seedDir.getFileName().toString().replace("seed_", ""));
                        results.add(new ModeResult(mode, seed, microF1, macroF1));
                    }
                } catch (IOException e) {
                    System.err.printf("Failed to load metrics from %s: %s%n", seedDir, e.getMessage());
                }
            });
        
        return results;
    }
    
    /**
     * Compute bootstrap confidence intervals for a set of results.
     */
    private BootstrapResult computeBootstrap(List<ModeResult> results) {
        double[] microF1Values = results.stream().mapToDouble(r -> r.microF1).toArray();
        double[] macroF1Values = results.stream().mapToDouble(r -> r.macroF1).toArray();
        
        double microF1Mean = Arrays.stream(microF1Values).average().orElse(0.0);
        double macroF1Mean = Arrays.stream(macroF1Values).average().orElse(0.0);
        
        // Bootstrap sampling
        List<Double> microF1Bootstrap = new ArrayList<>();
        List<Double> macroF1Bootstrap = new ArrayList<>();
        
        for (int i = 0; i < BOOTSTRAP_SAMPLES; i++) {
            double[] microSample = new double[microF1Values.length];
            double[] macroSample = new double[macroF1Values.length];
            
            for (int j = 0; j < microF1Values.length; j++) {
                int idx = random.nextInt(microF1Values.length);
                microSample[j] = microF1Values[idx];
                macroSample[j] = macroF1Values[idx];
            }
            
            microF1Bootstrap.add(Arrays.stream(microSample).average().orElse(0.0));
            macroF1Bootstrap.add(Arrays.stream(macroSample).average().orElse(0.0));
        }
        
        Collections.sort(microF1Bootstrap);
        Collections.sort(macroF1Bootstrap);
        
        double alpha = 1 - CONFIDENCE_LEVEL;
        int lowerIdx = (int) (microF1Bootstrap.size() * alpha / 2);
        int upperIdx = (int) (microF1Bootstrap.size() * (1 - alpha / 2));
        
        return new BootstrapResult(
            microF1Mean, microF1Bootstrap.get(lowerIdx), microF1Bootstrap.get(upperIdx),
            macroF1Mean, macroF1Bootstrap.get(lowerIdx), macroF1Bootstrap.get(upperIdx)
        );
    }
    
    /**
     * Compute paired comparison between two modes.
     */
    private ComparisonResult computePairedComparison(List<ModeResult> modeB, List<ModeResult> modeD) {
        double bMicroF1 = modeB.stream().mapToDouble(r -> r.microF1).average().orElse(0.0);
        double dMicroF1 = modeD.stream().mapToDouble(r -> r.microF1).average().orElse(0.0);
        double bMacroF1 = modeB.stream().mapToDouble(r -> r.macroF1).average().orElse(0.0);
        double dMacroF1 = modeD.stream().mapToDouble(r -> r.macroF1).average().orElse(0.0);
        
        double microF1Diff = bMicroF1 - dMicroF1;
        double macroF1Diff = bMacroF1 - dMacroF1;
        
        // Cohen's d (effect size)
        double microF1CohenD = computeCohenD(
            modeB.stream().mapToDouble(r -> r.microF1).toArray(),
            modeD.stream().mapToDouble(r -> r.microF1).toArray()
        );
        
        double macroF1CohenD = computeCohenD(
            modeB.stream().mapToDouble(r -> r.macroF1).toArray(),
            modeD.stream().mapToDouble(r -> r.macroF1).toArray()
        );
        
        // Bootstrap p-value
        double microF1PValue = computeBootstrapPValue(
            modeB.stream().mapToDouble(r -> r.microF1).toArray(),
            modeD.stream().mapToDouble(r -> r.microF1).toArray()
        );
        
        double macroF1PValue = computeBootstrapPValue(
            modeB.stream().mapToDouble(r -> r.macroF1).toArray(),
            modeD.stream().mapToDouble(r -> r.macroF1).toArray()
        );
        
        return new ComparisonResult(
            bMicroF1, dMicroF1, microF1Diff, microF1CohenD, microF1PValue,
            bMacroF1, dMacroF1, macroF1Diff, macroF1CohenD, macroF1PValue
        );
    }
    
    /**
     * Compute Cohen's d effect size.
     */
    private double computeCohenD(double[] groupA, double[] groupB) {
        double meanA = Arrays.stream(groupA).average().orElse(0.0);
        double meanB = Arrays.stream(groupB).average().orElse(0.0);
        
        double varA = Arrays.stream(groupA).map(x -> Math.pow(x - meanA, 2)).average().orElse(0.0);
        double varB = Arrays.stream(groupB).map(x -> Math.pow(x - meanB, 2)).average().orElse(0.0);
        
        double pooledSD = Math.sqrt((varA + varB) / 2);
        
        return pooledSD == 0 ? 0.0 : (meanA - meanB) / pooledSD;
    }
    
    /**
     * Compute bootstrap p-value for difference between groups.
     */
    private double computeBootstrapPValue(double[] groupA, double[] groupB) {
        double observedDiff = Arrays.stream(groupA).average().orElse(0.0) - 
                             Arrays.stream(groupB).average().orElse(0.0);
        
        // Combine groups for null hypothesis
        double[] combined = new double[groupA.length + groupB.length];
        System.arraycopy(groupA, 0, combined, 0, groupA.length);
        System.arraycopy(groupB, 0, combined, groupA.length, groupB.length);
        
        int extremeCount = 0;
        
        for (int i = 0; i < BOOTSTRAP_SAMPLES; i++) {
            // Resample under null hypothesis
            double[] resampleA = new double[groupA.length];
            double[] resampleB = new double[groupB.length];
            
            for (int j = 0; j < groupA.length; j++) {
                resampleA[j] = combined[random.nextInt(combined.length)];
            }
            for (int j = 0; j < groupB.length; j++) {
                resampleB[j] = combined[random.nextInt(combined.length)];
            }
            
            double resampleDiff = Arrays.stream(resampleA).average().orElse(0.0) - 
                                 Arrays.stream(resampleB).average().orElse(0.0);
            
            if (Math.abs(resampleDiff) >= Math.abs(observedDiff)) {
                extremeCount++;
            }
        }
        
        return (double) extremeCount / BOOTSTRAP_SAMPLES;
    }
    
    /**
     * Interpret comparison results and print conclusions.
     */
    private void interpretComparison(ComparisonResult comparison) {
        System.out.println("\n--- INTERPRETATION ---");
        
        // Statistical significance
        boolean microSignificant = comparison.microF1PValue < 0.05;
        boolean macroSignificant = comparison.macroF1PValue < 0.05;
        
        System.out.printf("Micro F1 difference: %s (p=%.4f)%n", 
                         microSignificant ? "SIGNIFICANT" : "Not significant", 
                         comparison.microF1PValue);
        
        System.out.printf("Macro F1 difference: %s (p=%.4f)%n",
                         macroSignificant ? "SIGNIFICANT" : "Not significant",
                         comparison.macroF1PValue);
        
        // Effect size interpretation
        String microEffect = interpretCohenD(comparison.microF1CohenD);
        String macroEffect = interpretCohenD(comparison.macroF1CohenD);
        
        System.out.printf("Micro F1 effect size: %s%n", microEffect);
        System.out.printf("Macro F1 effect size: %s%n", macroEffect);
        
        // Overall conclusion
        if (microSignificant && comparison.microF1Difference > 0) {
            System.out.println("✅ HYPOTHESIS CONFIRMED: Mode B significantly outperforms Mode D");
        } else {
            System.out.println("❌ HYPOTHESIS REJECTED: No significant advantage for Mode B");
        }
    }
    
    private String interpretCohenD(double cohenD) {
        double abs = Math.abs(cohenD);
        if (abs < 0.2) return "Negligible";
        if (abs < 0.5) return "Small"; 
        if (abs < 0.8) return "Medium";
        return "Large";
    }
    
    // Report generation methods
    
    private void addReportHeader(StringBuilder report) {
        report.append("# Reproducibility Experiment Results\n\n");
        report.append("## Executive Summary\n\n");
        report.append("This report presents the results of the definitive experiment to resolve the performance gap ");
        report.append("between Python's 82.1% F1 score and Java's 66.7-74.3% F1 score in GitHub issue classification.\n\n");
    }
    
    private void addExecutiveSummary(StringBuilder report, Map<ExperimentMode, List<ModeResult>> allResults, 
                                   ComparisonResult comparison) {
        report.append("### Key Findings\n\n");
        
        if (comparison != null) {
            report.append(String.format("- **Mode B (Python approach)**: %.1f%% Micro F1\n", 
                                       comparison.bMicroF1Mean * 100));
            report.append(String.format("- **Mode D (Java approach)**: %.1f%% Micro F1\n", 
                                       comparison.dMicroF1Mean * 100));
            report.append(String.format("- **Performance Gap**: %.1f percentage points\n", 
                                       comparison.microF1Difference * 100));
            
            boolean significant = comparison.microF1PValue < 0.05;
            report.append(String.format("- **Statistical Significance**: %s (p=%.4f)\n\n", 
                                       significant ? "YES" : "NO", comparison.microF1PValue));
        }
    }
    
    private void addDetailedResults(StringBuilder report, Map<ExperimentMode, List<ModeResult>> allResults,
                                  Map<ExperimentMode, BootstrapResult> bootstrapResults) {
        report.append("## Detailed Results\n\n");
        
        for (ExperimentMode mode : ExperimentMode.values()) {
            List<ModeResult> results = allResults.get(mode);
            BootstrapResult bootstrap = bootstrapResults.get(mode);
            
            if (results == null || results.isEmpty()) continue;
            
            report.append(String.format("### Mode %s\n\n", mode));
            report.append(String.format("- Runs: %d\n", results.size()));
            
            if (bootstrap != null) {
                report.append(String.format("- Micro F1: %.3f [%.3f, %.3f] (95%% CI)\n", 
                                           bootstrap.microF1Mean, bootstrap.microF1LowerCI, bootstrap.microF1UpperCI));
                report.append(String.format("- Macro F1: %.3f [%.3f, %.3f] (95%% CI)\n\n", 
                                           bootstrap.macroF1Mean, bootstrap.macroF1LowerCI, bootstrap.macroF1UpperCI));
            }
        }
    }
    
    private void addStatisticalAnalysis(StringBuilder report, ComparisonResult comparison) {
        report.append("## Statistical Analysis\n\n");
        
        if (comparison != null) {
            report.append("### Mode B vs Mode D Comparison\n\n");
            report.append(String.format("- Difference: %.3f (%.1f%% points)\n", 
                                       comparison.microF1Difference, comparison.microF1Difference * 100));
            report.append(String.format("- Effect Size (Cohen's d): %.3f (%s)\n", 
                                       comparison.microF1CohenD, interpretCohenD(comparison.microF1CohenD)));
            report.append(String.format("- P-value: %.4f\n", comparison.microF1PValue));
            report.append(String.format("- Significant: %s\n\n", comparison.microF1PValue < 0.05 ? "YES" : "NO"));
        }
    }
    
    private void addConclusions(StringBuilder report, ComparisonResult comparison) {
        report.append("## Conclusions\n\n");
        
        if (comparison != null && comparison.microF1PValue < 0.05 && comparison.microF1Difference > 0) {
            report.append("✅ **Hypothesis Confirmed**: Python's post-processing approach (Mode B) ");
            report.append("significantly outperforms Java's pre-processing approach (Mode D).\n\n");
            report.append("This confirms that the model benefits from context provided by all labels ");
            report.append("during prediction, even when some labels are filtered during evaluation.\n\n");
        } else {
            report.append("❌ **Hypothesis Rejected**: No significant advantage found for Python's approach.\n\n");
            report.append("The performance gap may be due to other factors not tested in this experiment.\n\n");
        }
    }
    
    private void addMethodology(StringBuilder report) {
        report.append("## Methodology\n\n");
        report.append("- **Test Dataset**: 111 real GitHub issues from Python's test_set.json\n");
        report.append("- **Statistical Testing**: Bootstrap resampling (n=1000)\n");
        report.append("- **Confidence Level**: 95%\n");
        report.append("- **Effect Size**: Cohen's d\n");
        report.append("- **Multiple Runs**: 3 seeds per mode for variance estimation\n");
    }
    
    // Save/load methods for persistence
    
    private void saveBootstrapResults(Map<ExperimentMode, BootstrapResult> results) throws IOException {
        Path path = Paths.get("target", "experiments", "summary", "bootstrap_confidence.json");
        objectMapper.writerWithDefaultPrettyPrinter().writeValue(path.toFile(), results);
    }
    
    private void saveComparisonResults(ComparisonResult comparison) throws IOException {
        Path path = Paths.get("target", "experiments", "summary", "mode_comparison.json");
        objectMapper.writerWithDefaultPrettyPrinter().writeValue(path.toFile(), comparison);
    }
    
    private Map<ExperimentMode, BootstrapResult> loadBootstrapResults() throws IOException {
        Path path = Paths.get("target", "experiments", "summary", "bootstrap_confidence.json");
        if (!Files.exists(path)) return Map.of();
        
        return objectMapper.readValue(path.toFile(), 
            objectMapper.getTypeFactory().constructMapType(HashMap.class, ExperimentMode.class, BootstrapResult.class));
    }
    
    private ComparisonResult loadComparisonResults() throws IOException {
        Path path = Paths.get("target", "experiments", "summary", "mode_comparison.json");
        if (!Files.exists(path)) return null;
        
        return objectMapper.readValue(path.toFile(), ComparisonResult.class);
    }
    
    // Data classes
    
    private record ModeResult(ExperimentMode mode, int seed, double microF1, double macroF1) {}
    
    private record BootstrapResult(
        double microF1Mean, double microF1LowerCI, double microF1UpperCI,
        double macroF1Mean, double macroF1LowerCI, double macroF1UpperCI
    ) {}
    
    private record ComparisonResult(
        double bMicroF1Mean, double dMicroF1Mean, double microF1Difference, 
        double microF1CohenD, double microF1PValue,
        double bMacroF1Mean, double dMacroF1Mean, double macroF1Difference,
        double macroF1CohenD, double macroF1PValue
    ) {}
}
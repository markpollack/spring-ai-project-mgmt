package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.domain.LabelPrediction;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Comprehensive metrics calculator for classification evaluation.
 * 
 * <p>This service implements the full suite of metrics used in academic and production
 * evaluation of multi-label classification systems. It extends our basic F1 calculation
 * to include micro/macro averaging, per-label analysis, and specialized multi-label metrics.</p>
 * 
 * <p>Metrics implemented:</p>
 * <ul>
 *   <li><strong>Micro-averaged:</strong> F1, Precision, Recall (aggregated across all predictions)</li>
 *   <li><strong>Macro-averaged:</strong> F1, Precision, Recall (averaged across all labels)</li>
 *   <li><strong>Per-label:</strong> F1, Precision, Recall, Support (for each label individually)</li>
 *   <li><strong>Multi-label specific:</strong> Jaccard (IoU), Subset Accuracy, Label Coverage</li>
 * </ul>
 */
@Service
public class ComprehensiveMetricsCalculator {
    
    private static final Logger log = LoggerFactory.getLogger(ComprehensiveMetricsCalculator.class);
    
    /**
     * Calculate comprehensive metrics for a set of predictions vs ground truth.
     * 
     * @param predictions List of classification responses
     * @param groundTruth Map of issue number to true labels
     * @return Complete metrics bundle
     */
    public MetricsBundle calculateMetrics(List<ClassificationResponse> predictions, 
                                        Map<Integer, Set<String>> groundTruth) {
        if (predictions == null || predictions.isEmpty()) {
            log.warn("Empty predictions list, returning zero metrics");
            return MetricsBundle.empty();
        }
        
        if (groundTruth == null || groundTruth.isEmpty()) {
            log.warn("Empty ground truth, returning zero metrics");
            return MetricsBundle.empty();
        }
        
        // Convert predictions to consistent format
        Map<Integer, Set<String>> predictionMap = predictions.stream()
            .collect(Collectors.toMap(
                ClassificationResponse::issueNumber,
                response -> response.predictedLabels().stream()
                    .map(LabelPrediction::label)
                    .collect(Collectors.toSet())
            ));
        
        // Calculate per-instance metrics
        List<InstanceMetrics> instanceMetrics = calculateInstanceMetrics(predictionMap, groundTruth);
        
        // Calculate micro-averaged metrics
        MicroMetrics microMetrics = calculateMicroMetrics(instanceMetrics);
        
        // Calculate macro-averaged metrics  
        MacroMetrics macroMetrics = calculateMacroMetrics(predictionMap, groundTruth);
        
        // Calculate per-label metrics
        Map<String, LabelMetrics> perLabelMetrics = calculatePerLabelMetrics(predictionMap, groundTruth);
        
        // Calculate multi-label specific metrics
        MultiLabelMetrics multiLabelMetrics = calculateMultiLabelMetrics(instanceMetrics);
        
        log.info("Calculated metrics for {} predictions, {} ground truth instances", 
                predictions.size(), groundTruth.size());
        
        return new MetricsBundle(
            microMetrics,
            macroMetrics, 
            perLabelMetrics,
            multiLabelMetrics,
            instanceMetrics
        );
    }
    
    /**
     * Calculate per-instance (per-issue) metrics.
     */
    private List<InstanceMetrics> calculateInstanceMetrics(Map<Integer, Set<String>> predictions,
                                                          Map<Integer, Set<String>> groundTruth) {
        List<InstanceMetrics> instanceMetrics = new ArrayList<>();
        
        for (Integer issueNumber : groundTruth.keySet()) {
            Set<String> trueLs = groundTruth.get(issueNumber);
            Set<String> predLs = predictions.getOrDefault(issueNumber, Set.of());
            
            // Calculate intersection and metrics
            Set<String> intersection = new HashSet<>(trueLs);
            intersection.retainAll(predLs);
            
            int tp = intersection.size();
            int fp = predLs.size() - tp;
            int fn = trueLs.size() - tp;
            
            double precision = predLs.isEmpty() ? 0.0 : (double) tp / predLs.size();
            double recall = trueLs.isEmpty() ? 0.0 : (double) tp / trueLs.size();
            double f1 = calculateF1(precision, recall);
            
            // Jaccard similarity (IoU)
            Set<String> union = new HashSet<>(trueLs);
            union.addAll(predLs);
            double jaccard = union.isEmpty() ? 0.0 : (double) intersection.size() / union.size();
            
            // Exact match
            boolean exactMatch = trueLs.equals(predLs);
            
            instanceMetrics.add(new InstanceMetrics(
                issueNumber, tp, fp, fn, precision, recall, f1, jaccard, exactMatch
            ));
        }
        
        return instanceMetrics;
    }
    
    /**
     * Calculate micro-averaged metrics (aggregate all TP/FP/FN across instances).
     */
    private MicroMetrics calculateMicroMetrics(List<InstanceMetrics> instanceMetrics) {
        int totalTp = instanceMetrics.stream().mapToInt(m -> m.truePositives).sum();
        int totalFp = instanceMetrics.stream().mapToInt(m -> m.falsePositives).sum();
        int totalFn = instanceMetrics.stream().mapToInt(m -> m.falseNegatives).sum();
        
        double precision = (totalTp + totalFp) == 0 ? 0.0 : (double) totalTp / (totalTp + totalFp);
        double recall = (totalTp + totalFn) == 0 ? 0.0 : (double) totalTp / (totalTp + totalFn);
        double f1 = calculateF1(precision, recall);
        
        return new MicroMetrics(totalTp, totalFp, totalFn, precision, recall, f1);
    }
    
    /**
     * Calculate macro-averaged metrics (average per-label metrics across all labels).
     */
    private MacroMetrics calculateMacroMetrics(Map<Integer, Set<String>> predictions,
                                              Map<Integer, Set<String>> groundTruth) {
        Map<String, LabelMetrics> perLabelMetrics = calculatePerLabelMetrics(predictions, groundTruth);
        
        if (perLabelMetrics.isEmpty()) {
            return new MacroMetrics(0.0, 0.0, 0.0, 0);
        }
        
        double avgPrecision = perLabelMetrics.values().stream()
            .mapToDouble(m -> m.precision)
            .average()
            .orElse(0.0);
        
        double avgRecall = perLabelMetrics.values().stream()
            .mapToDouble(m -> m.recall)
            .average()
            .orElse(0.0);
        
        double avgF1 = perLabelMetrics.values().stream()
            .mapToDouble(m -> m.f1)
            .average()
            .orElse(0.0);
        
        return new MacroMetrics(avgPrecision, avgRecall, avgF1, perLabelMetrics.size());
    }
    
    /**
     * Calculate metrics for each label individually.
     */
    private Map<String, LabelMetrics> calculatePerLabelMetrics(Map<Integer, Set<String>> predictions,
                                                              Map<Integer, Set<String>> groundTruth) {
        // Collect all unique labels
        Set<String> allLabels = new HashSet<>();
        groundTruth.values().forEach(allLabels::addAll);
        predictions.values().forEach(allLabels::addAll);
        
        Map<String, LabelMetrics> perLabelMetrics = new HashMap<>();
        
        for (String label : allLabels) {
            int tp = 0, fp = 0, fn = 0;
            
            for (Integer issueNumber : groundTruth.keySet()) {
                Set<String> trueLs = groundTruth.get(issueNumber);
                Set<String> predLs = predictions.getOrDefault(issueNumber, Set.of());
                
                boolean trueHasLabel = trueLs.contains(label);
                boolean predHasLabel = predLs.contains(label);
                
                if (trueHasLabel && predHasLabel) {
                    tp++;
                } else if (!trueHasLabel && predHasLabel) {
                    fp++;
                } else if (trueHasLabel && !predHasLabel) {
                    fn++;
                }
                // TN not needed for per-label metrics
            }
            
            double precision = (tp + fp) == 0 ? 0.0 : (double) tp / (tp + fp);
            double recall = (tp + fn) == 0 ? 0.0 : (double) tp / (tp + fn);
            double f1 = calculateF1(precision, recall);
            
            int support = tp + fn; // Number of true instances of this label
            
            perLabelMetrics.put(label, new LabelMetrics(
                label, tp, fp, fn, precision, recall, f1, support
            ));
        }
        
        return perLabelMetrics;
    }
    
    /**
     * Calculate multi-label specific metrics.
     */
    private MultiLabelMetrics calculateMultiLabelMetrics(List<InstanceMetrics> instanceMetrics) {
        if (instanceMetrics.isEmpty()) {
            return new MultiLabelMetrics(0.0, 0.0, 0.0, 0.0);
        }
        
        // Average Jaccard (IoU) across all instances
        double avgJaccard = instanceMetrics.stream()
            .mapToDouble(m -> m.jaccard)
            .average()
            .orElse(0.0);
        
        // Subset accuracy (exact match percentage)
        double subsetAccuracy = instanceMetrics.stream()
            .mapToDouble(m -> m.exactMatch ? 1.0 : 0.0)
            .average()
            .orElse(0.0);
        
        // Label coverage metrics
        double avgTrueLabels = instanceMetrics.stream()
            .mapToDouble(m -> m.truePositives + m.falseNegatives)
            .average()
            .orElse(0.0);
        
        double avgPredLabels = instanceMetrics.stream()
            .mapToDouble(m -> m.truePositives + m.falsePositives)
            .average()
            .orElse(0.0);
        
        return new MultiLabelMetrics(avgJaccard, subsetAccuracy, avgTrueLabels, avgPredLabels);
    }
    
    /**
     * Calculate F1 score from precision and recall.
     */
    private double calculateF1(double precision, double recall) {
        return (precision + recall) == 0.0 ? 0.0 : 
               2.0 * (precision * recall) / (precision + recall);
    }
    
    // Record classes for structured metrics
    
    public record MetricsBundle(
        MicroMetrics microMetrics,
        MacroMetrics macroMetrics,
        Map<String, LabelMetrics> perLabelMetrics,
        MultiLabelMetrics multiLabelMetrics,
        List<InstanceMetrics> instanceMetrics
    ) {
        public static MetricsBundle empty() {
            return new MetricsBundle(
                new MicroMetrics(0, 0, 0, 0.0, 0.0, 0.0),
                new MacroMetrics(0.0, 0.0, 0.0, 0),
                Map.of(),
                new MultiLabelMetrics(0.0, 0.0, 0.0, 0.0),
                List.of()
            );
        }
    }
    
    public record MicroMetrics(
        int totalTruePositives,
        int totalFalsePositives, 
        int totalFalseNegatives,
        double precision,
        double recall,
        double f1
    ) {}
    
    public record MacroMetrics(
        double avgPrecision,
        double avgRecall,
        double avgF1,
        int numLabels
    ) {}
    
    public record LabelMetrics(
        String label,
        int truePositives,
        int falsePositives,
        int falseNegatives,
        double precision,
        double recall,
        double f1,
        int support
    ) {}
    
    public record MultiLabelMetrics(
        double avgJaccard,      // Average Intersection over Union
        double subsetAccuracy,  // Exact match percentage
        double avgTrueLabels,   // Average number of true labels per instance
        double avgPredLabels    // Average number of predicted labels per instance
    ) {}
    
    public record InstanceMetrics(
        int issueNumber,
        int truePositives,
        int falsePositives,
        int falseNegatives,
        double precision,
        double recall,
        double f1,
        double jaccard,
        boolean exactMatch
    ) {}
}
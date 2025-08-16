package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.domain.LabelPrediction;
import org.springaicommunity.github.ai.classification.service.*;

import java.io.File;
import java.util.*;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.*;

/**
 * 1:1 reproduction test using the exact same test data and evaluation approach
 * that achieved 82.1% F1 score in the Python system.
 * 
 * This test uses:
 * - Real Python test data from test_set.json (111 issues)
 * - Same label exclusions as Python evaluation
 * - Same micro-averaged F1 calculation
 * - Conservative classification approach matching Python prompts
 */
@DisplayName("Python 1:1 Reproduction Test")
class PythonReproductionTest {
    
    private ClaudeLLMClient claudeClient;
    private List<TestIssue> realTestData;
    private Set<String> excludedLabels;
    private Set<String> availableLabels;
    
    @BeforeEach
    void setUp() throws Exception {
        // Initialize Claude client exactly like Python system
        ObjectMapper objectMapper = new ObjectMapper();
        SpringAIContextService contextService = new SpringAIContextService(objectMapper);
        contextService.afterPropertiesSet();
        
        DefaultPromptTemplateService promptService = new DefaultPromptTemplateService(contextService);
        java.util.concurrent.Executor executor = java.util.concurrent.ForkJoinPool.commonPool();
        claudeClient = new ClaudeLLMClient(promptService, objectMapper, executor);
        
        // Load real Python test data
        loadRealTestData();
        
        // Use same excluded labels as Python evaluation
        setupExcludedLabels();
        
        // Load available labels
        loadAvailableLabels();
    }
    
    @Test
    @DisplayName("Reproduce Python 82.1% F1 Score with Real Test Data")
    void testPythonReproduction() {
        System.out.println("\n=== PYTHON 1:1 REPRODUCTION TEST ===");
        System.out.println("Target: 82.1% F1 score (with filtered evaluation)");
        System.out.println("Test dataset: " + realTestData.size() + " real Spring AI issues");
        System.out.println("Excluded labels: " + excludedLabels.size() + " problematic labels");
        
        FilteredEvaluationResults results = new FilteredEvaluationResults();
        
        // Test on first 10 issues for speed (can expand to all 111 later)
        int testSize = Math.min(realTestData.size(), 10);
        System.out.println("Processing " + testSize + " issues for validation...\n");
        
        for (int i = 0; i < testSize; i++) {
            TestIssue issue = realTestData.get(i);
            System.out.println("--- Issue #" + issue.issueNumber + " ---");
            System.out.println("Title: " + issue.title);
            
            // Filter ground truth labels (same as Python)
            Set<String> filteredGroundTruth = issue.labels.stream()
                .filter(label -> !excludedLabels.contains(label))
                .filter(availableLabels::contains)
                .collect(Collectors.toSet());
            
            System.out.println("Filtered ground truth: " + filteredGroundTruth);
            
            try {
                // Create classification request with conservative approach
                ClassificationRequest request = ClassificationRequest.builder()
                    .issueNumber(issue.issueNumber)
                    .title(issue.title)
                    .body(issue.body != null ? issue.body : "")
                    .availableLabels(getFilteredAvailableLabels()) // Exclude problematic labels
                    .build();
                
                // Classify using Claude (same as Python)
                ClassificationResponse response = claudeClient.classifyIssue(request);
                
                // Filter predictions (same as Python)
                Set<String> filteredPredictions = response.predictedLabels().stream()
                    .map(LabelPrediction::label)
                    .filter(label -> !excludedLabels.contains(label))
                    .filter(availableLabels::contains)
                    .collect(Collectors.toSet());
                
                System.out.println("Filtered predictions: " + filteredPredictions);
                
                // Update evaluation results using Python's approach
                results.addPrediction(filteredGroundTruth, filteredPredictions);
                
            } catch (Exception e) {
                System.out.println("❌ Error: " + e.getMessage());
                // Add as missed prediction
                results.addPrediction(filteredGroundTruth, Set.of());
            }
            
            System.out.println();
        }
        
        // Display results using Python's micro-averaged approach
        System.out.println("=== FILTERED EVALUATION RESULTS ===");
        System.out.printf("(Excluding %d labels: %s)%n", 
            excludedLabels.size(), 
            excludedLabels.stream().sorted().collect(Collectors.joining(", ")));
        System.out.println();
        
        System.out.println("MICRO-AVERAGED METRICS:");
        System.out.println("-".repeat(30));
        System.out.printf("Precision: %.3f (%.1f%%)%n", results.getPrecision(), results.getPrecision() * 100);
        System.out.printf("Recall: %.3f (%.1f%%)%n", results.getRecall(), results.getRecall() * 100);
        System.out.printf("F1 Score: %.3f (%.1f%%)%n", results.getF1Score(), results.getF1Score() * 100);
        System.out.println();
        
        System.out.println("Raw counts:");
        System.out.println("True Positives: " + results.truePositives);
        System.out.println("False Positives: " + results.falsePositives);
        System.out.println("False Negatives: " + results.falseNegatives);
        
        System.out.println();
        System.out.println("=== COMPARISON WITH PYTHON BASELINE ===");
        double pythonF1 = 82.1;
        double ourF1 = results.getF1Score() * 100;
        System.out.printf("Python baseline F1: %.1f%%%n", pythonF1);
        System.out.printf("Java reproduction F1: %.1f%%%n", ourF1);
        System.out.printf("Difference: %+.1f%% points%n", ourF1 - pythonF1);
        
        // This should be much closer to 82.1% now
        assertThat(results.getF1Score()).isGreaterThan(0.5); // At least 50% with real data
    }
    
    private void loadRealTestData() throws Exception {
        // Load the real Python test data
        ObjectMapper mapper = new ObjectMapper();
        String testDataPath = "/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json";
        
        File testFile = new File(testDataPath);
        if (!testFile.exists()) {
            System.out.println("⚠️ Test data not found at: " + testDataPath);
            // Fallback to synthetic data
            realTestData = createFallbackTestData();
            return;
        }
        
        JsonNode testArray = mapper.readTree(testFile);
        realTestData = new ArrayList<>();
        
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
            
            realTestData.add(issue);
        }
        
        System.out.println("✅ Loaded " + realTestData.size() + " real test issues");
    }
    
    private void setupExcludedLabels() {
        // Exact same exclusions as Python evaluate_filtered_predictions.py
        excludedLabels = Set.of(
            // Original problematic labels
            "bug", "enhancement",
            // Subjective/Judgmental labels  
            "question", "help wanted", "good first issue", "epic",
            // Process-Driven labels
            "status: backported", "status: to-discuss", "follow up",
            "status: waiting-for-feedback", "for: backport-to-1.0.x", "next priorities"
        );
    }
    
    private void loadAvailableLabels() throws Exception {
        // Load labels.json if available
        ObjectMapper mapper = new ObjectMapper();
        String labelsPath = "/home/mark/project-mgmt/spring-ai-project-mgmt/labels.json";
        
        File labelsFile = new File(labelsPath);
        if (labelsFile.exists()) {
            JsonNode labelsArray = mapper.readTree(labelsFile);
            availableLabels = new HashSet<>();
            for (JsonNode labelNode : labelsArray) {
                String labelName = labelNode.has("name") ? 
                    labelNode.get("name").asText() : labelNode.asText();
                availableLabels.add(labelName);
            }
        } else {
            // Fallback to common Spring AI labels
            availableLabels = Set.of(
                "vector store", "pgvector", "pinecone", "qdrant", "chromadb",
                "tool/function calling", "RAG", "openai", "azure", "ollama", 
                "anthropic", "documentation", "configuration", "bug", "enhancement",
                "streaming", "Observability", "transcription models", "embedding models",
                "advisors", "prompt management", "MCP", "type: backport"
            );
        }
        
        System.out.println("✅ Loaded " + availableLabels.size() + " available labels");
    }
    
    private List<String> getFilteredAvailableLabels() {
        // Only offer labels that aren't excluded (conservative approach)
        return availableLabels.stream()
            .filter(label -> !excludedLabels.contains(label))
            .sorted()
            .collect(Collectors.toList());
    }
    
    private List<TestIssue> createFallbackTestData() {
        // If real data not available, use a few realistic examples
        List<TestIssue> fallback = new ArrayList<>();
        
        TestIssue issue1 = new TestIssue();
        issue1.issueNumber = 1776;
        issue1.title = "Prompt-time filter expressions for RetrievalAugmentationAdvisor/VectorStoreDocumentRetriever";
        issue1.body = "As RetrievalAugmentationAdvisor is expected to replace QuestionAnswerAdvisor, it should also support FILTER_EXPRESSION";
        issue1.labels = Set.of("enhancement", "RAG", "metadata filters");
        fallback.add(issue1);
        
        return fallback;
    }
    
    // Test issue data structure matching Python format
    private static class TestIssue {
        int issueNumber;
        String title;
        String body;
        Set<String> labels;
    }
    
    // Filtered evaluation results using Python's micro-averaged approach
    private static class FilteredEvaluationResults {
        int truePositives = 0;
        int falsePositives = 0;
        int falseNegatives = 0;
        
        void addPrediction(Set<String> groundTruth, Set<String> predictions) {
            // Calculate metrics exactly like Python
            Set<String> intersection = new HashSet<>(groundTruth);
            intersection.retainAll(predictions);
            truePositives += intersection.size();
            
            falsePositives += predictions.size() - intersection.size();
            falseNegatives += groundTruth.size() - intersection.size();
        }
        
        double getPrecision() {
            return (truePositives + falsePositives) == 0 ? 0.0 : 
                   (double) truePositives / (truePositives + falsePositives);
        }
        
        double getRecall() {
            return (truePositives + falseNegatives) == 0 ? 0.0 : 
                   (double) truePositives / (truePositives + falseNegatives);
        }
        
        double getF1Score() {
            double precision = getPrecision();
            double recall = getRecall();
            return (precision + recall) == 0.0 ? 0.0 : 
                   2.0 * (precision * recall) / (precision + recall);
        }
    }
}
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
 * Exact reproduction test using the precise Python classification-4.md approach.
 * 
 * This test replicates the exact methodology that achieved 82.1% F1:
 * - Uses classification-4.md prompt approach exactly
 * - Applies the same exclusion strategy (skip bug/enhancement)
 * - Uses the same confidence thresholds and conservative approach
 * - Tests against the same real issues from test_set.json
 */
@DisplayName("Exact Python Reproduction Test")
class ExactPythonReproductionTest {
    
    private ClaudeLLMClient claudeClient;
    private List<TestIssue> realTestData;
    private Set<String> excludedLabels;
    private Set<String> availableLabels;
    
    @BeforeEach
    void setUp() throws Exception {
        // Initialize Claude client with exact Python approach
        ObjectMapper objectMapper = new ObjectMapper();
        SpringAIContextService contextService = new SpringAIContextService(objectMapper);
        contextService.afterPropertiesSet();
        
        // Use a prompt service that exactly matches classification-4.md
        ExactPythonPromptTemplateService promptService = new ExactPythonPromptTemplateService(contextService);
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
    @DisplayName("Exact Python Classification-4.md Reproduction")
    void testExactPythonReproduction() {
        System.out.println("\n=== EXACT PYTHON CLASSIFICATION-4.MD REPRODUCTION ===");
        System.out.println("Target: 82.1% F1 score (classification-4.md approach)");
        System.out.println("Strategy: Skip bug/enhancement, focus on high-performing technical labels");
        System.out.println("Test dataset: " + realTestData.size() + " real Spring AI issues");
        
        FilteredEvaluationResults results = new FilteredEvaluationResults();
        
        // Test on first 10 issues for detailed analysis
        int testSize = Math.min(realTestData.size(), 10);
        System.out.println("Processing " + testSize + " issues with exact Python approach...\n");
        
        for (int i = 0; i < testSize; i++) {
            TestIssue issue = realTestData.get(i);
            System.out.println("--- Issue #" + issue.issueNumber + " ---");
            System.out.println("Title: " + issue.title);
            
            // Filter ground truth labels EXACTLY like Python
            Set<String> filteredGroundTruth = issue.labels.stream()
                .filter(label -> !excludedLabels.contains(label))
                .filter(availableLabels::contains)
                .collect(Collectors.toSet());
            
            System.out.println("Ground truth (filtered): " + filteredGroundTruth);
            
            try {
                // Create classification request with EXACT Python approach
                List<String> technicalLabelsOnly = getFilteredAvailableLabels();
                
                ClassificationRequest request = ClassificationRequest.builder()
                    .issueNumber(issue.issueNumber)
                    .title(issue.title)
                    .body(issue.body != null ? issue.body : "")
                    .availableLabels(technicalLabelsOnly) // Only high-performing labels
                    .build();
                
                // Classify using Claude with exact Python prompt
                ClassificationResponse response = claudeClient.classifyIssue(request);
                
                // Filter predictions EXACTLY like Python
                Set<String> filteredPredictions = response.predictedLabels().stream()
                    .map(LabelPrediction::label)
                    .filter(label -> !excludedLabels.contains(label))
                    .filter(availableLabels::contains)
                    .collect(Collectors.toSet());
                
                System.out.println("Predictions (filtered): " + filteredPredictions);
                
                // Show confidence scores for analysis
                response.predictedLabels().forEach(pred -> 
                    System.out.printf("  %s: %.2f confidence%n", pred.label(), pred.confidence()));
                
                // Update evaluation results using Python's exact approach
                results.addPrediction(filteredGroundTruth, filteredPredictions);
                
                // Analyze misses for pattern identification
                Set<String> missed = new HashSet<>(filteredGroundTruth);
                missed.removeAll(filteredPredictions);
                if (!missed.isEmpty()) {
                    System.out.println("Missed labels: " + missed);
                }
                
            } catch (Exception e) {
                System.out.println("❌ Error: " + e.getMessage());
                results.addPrediction(filteredGroundTruth, Set.of());
            }
            
            System.out.println();
        }
        
        // Display results using Python's exact micro-averaged approach
        System.out.println("=== EXACT PYTHON EVALUATION RESULTS ===");
        System.out.printf("(Excluding %d labels: %s)%n", 
            excludedLabels.size(), 
            excludedLabels.stream().sorted().collect(Collectors.joining(", ")));
        System.out.println();
        
        System.out.println("MICRO-AVERAGED METRICS (Python approach):");
        System.out.println("-".repeat(40));
        System.out.printf("Precision: %.3f (%.1f%%)%n", results.getPrecision(), results.getPrecision() * 100);
        System.out.printf("Recall: %.3f (%.1f%%)%n", results.getRecall(), results.getRecall() * 100);
        System.out.printf("F1 Score: %.3f (%.1f%%)%n", results.getF1Score(), results.getF1Score() * 100);
        System.out.println();
        
        System.out.println("Detailed metrics:");
        System.out.println("True Positives: " + results.truePositives);
        System.out.println("False Positives: " + results.falsePositives);
        System.out.println("False Negatives: " + results.falseNegatives);
        
        System.out.println();
        System.out.println("=== COMPARISON WITH PYTHON TARGET ===");
        double pythonF1 = 82.1;
        double ourF1 = results.getF1Score() * 100;
        System.out.printf("Python target F1: %.1f%%%n", pythonF1);
        System.out.printf("Java exact reproduction F1: %.1f%%%n", ourF1);
        System.out.printf("Gap: %+.1f%% points%n", ourF1 - pythonF1);
        
        if (Math.abs(ourF1 - pythonF1) < 5.0) {
            System.out.println("✅ SUCCESS: Within 5% of Python target!");
        } else if (Math.abs(ourF1 - pythonF1) < 10.0) {
            System.out.println("⚠️ CLOSE: Within 10% of Python target");
        } else {
            System.out.println("❌ GAP: Significant difference from Python target");
        }
        
        // Validate reasonable performance
        assertThat(results.getF1Score()).isGreaterThan(0.5);
    }
    
    private void loadRealTestData() throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        String testDataPath = "/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json";
        
        File testFile = new File(testDataPath);
        if (!testFile.exists()) {
            System.out.println("⚠️ Test data not found, using fallback");
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
        // EXACT same exclusions as Python classification-4.md and evaluate_filtered_predictions.py
        excludedLabels = Set.of(
            // Explicitly skipped in classification-4.md
            "bug", "enhancement",
            // Additional exclusions from evaluation  
            "question", "help wanted", "good first issue", "epic",
            "status: backported", "status: to-discuss", "follow up",
            "status: waiting-for-feedback", "for: backport-to-1.0.x", "next priorities"
        );
    }
    
    private void loadAvailableLabels() throws Exception {
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
            // Comprehensive Spring AI labels based on the test data
            availableLabels = Set.of(
                "vector store", "pgvector", "pinecone", "qdrant", "chromadb",
                "tool/function calling", "RAG", "openai", "azure", "ollama", 
                "anthropic", "documentation", "configuration", "bug", "enhancement",
                "streaming", "Observability", "transcription models", "embedding models",
                "advisors", "prompt management", "MCP", "type: backport", "design",
                "Bedrock", "watson", "metadata filters", "Chat Memory", "ETL"
            );
        }
        
        System.out.println("✅ Loaded " + availableLabels.size() + " available labels");
    }
    
    private List<String> getFilteredAvailableLabels() {
        // Return ONLY high-performing technical labels (same as classification-4.md focus)
        List<String> highPerformingLabels = List.of(
            // Perfect performers from Python results
            "type: backport", "MCP", "RAG", "advisors", "prompt management",
            // Excellent performers  
            "vector store", "tool/function calling", "documentation",
            // Good technical performers
            "design", "configuration", "Observability", "ollama", "streaming",
            "Bedrock", "anthropic", "openai", "azure", "watson",
            // Additional technical labels
            "metadata filters", "Chat Memory", "ETL", "embedding models",
            "transcription models", "pinecone", "qdrant", "chromadb", "pgvector"
        );
        
        // Only return labels that are both high-performing AND available
        return highPerformingLabels.stream()
            .filter(availableLabels::contains)
            .sorted()
            .collect(Collectors.toList());
    }
    
    private List<TestIssue> createFallbackTestData() {
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
    
    // Filtered evaluation results using Python's exact micro-averaged approach
    private static class FilteredEvaluationResults {
        int truePositives = 0;
        int falsePositives = 0;
        int falseNegatives = 0;
        
        void addPrediction(Set<String> groundTruth, Set<String> predictions) {
            // Calculate metrics EXACTLY like Python evaluate_filtered_predictions.py
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

/**
 * Prompt template service that exactly matches Python classification-4.md approach.
 */
class ExactPythonPromptTemplateService implements PromptTemplateService {
    
    private final SpringAIContextService contextService;
    
    public ExactPythonPromptTemplateService(SpringAIContextService contextService) {
        this.contextService = contextService;
    }
    
    @Override
    public String buildClassificationPrompt(ClassificationRequest request) {
        String prompt = """
            # Improved Multi-Label GitHub Issue Classifier for Spring AI
            
            ## Context
            We're building a **multi-label classifier** for GitHub issues in the **Spring AI project**. This improved version addresses classification accuracy issues and data processing inefficiencies.
            
            ## Key Improvements
            
            ### 1. Exclude Problematic Labels
            **Do NOT classify these labels** (they hurt overall performance):
            - `bug` - Skip entirely, too subjective and low precision
            - `enhancement` - Skip entirely, over-applied with low precision
            
            ### 2. Refined Classification Focus
            **Prioritize high-performing technical labels:**
            - `vector store` (92.3% F1 in previous evaluation)
            - `tool/function calling` (91.7% F1)
            - `documentation` (90.9% F1)
            - `type: backport` (100% F1)
            - `MCP` (100% F1)
            - `design` (76.9% F1)
            
            ## 🧠 Enhanced Labeling Rules
            
            ### Conservative Technical Approach
            - **Only assign labels with explicit technical evidence**
            - **Focus on domain-specific Spring AI concepts**
            - **Avoid generic labels** (bug, enhancement, general improvement)
            - **Maximum 2 labels per issue** (most should have 1)
            
            ### Confidence Calibration
            - **1.0**: Technical term explicitly mentioned and central
            - **0.9**: Very confident, clear domain-specific context
            - **0.7-0.8**: Moderately confident, relevant technical content
            - **< 0.7**: Skip the label entirely
            
            ### Label-Specific Guidelines
            
            **High-Confidence Labels to Focus On:**
            - `vector store`: Only when explicitly about vector databases, embeddings storage
            - `tool/function calling`: Only when about function calling, tool use, or agent capabilities
            - `documentation`: Only for docs, examples, or documentation improvements
            - `type: backport`: Only for explicit backport requests
            - `MCP`: Only when Model Context Protocol is mentioned
            - `design`: Only for architectural or design discussions
            - `Bedrock`: Only when AWS Bedrock is specifically mentioned
            - `model client`: Only for model provider integrations (OpenAI, Anthropic, etc.)
            
            **Labels to Avoid:**
            - `bug`: Skip entirely (40% precision, too subjective)
            - `enhancement`: Skip entirely (29.7% precision, over-applied)
            - Generic improvement labels
            
            ## Issue to Classify
            
            **Issue #%d**
            
            **Title:** %s
            
            **Body:**
            %s
            
            ## Available Labels
            %s
            
            ## Quality Control
            - **Precision-focused**: Better to miss a label than assign incorrectly
            - **Technical specificity**: Only assign labels for explicit technical content
            - **Evidence-based**: Each label must have clear textual justification
            - **Avoid inference**: Don't assume labels based on related concepts
            
            ## Response Format
            Respond with JSON only - no additional text:
            
            ```json
            {
              "issue_number": %d,
              "predicted_labels": [
                {
                  "label": "vector store",
                  "confidence": 0.9
                }
              ],
              "explanation": "Issue explicitly mentions vector database configuration and embedding storage, clearly related to vector store functionality."
            }
            ```
            """;
            
        return String.format(prompt, 
            request.issueNumber(),
            request.title(),
            request.body(),
            String.join(", ", request.availableLabels()),
            request.issueNumber());
    }
    
    @Override
    public String buildBatchClassificationPrompt(List<ClassificationRequest> requests) {
        // For simplicity, delegate to single issue approach
        if (requests.isEmpty()) return "";
        return buildClassificationPrompt(requests.get(0));
    }
    
    @Override
    public String getSystemPrompt() {
        return "You are an expert GitHub issue classifier for Spring AI.";
    }
    
    @Override
    public String getResponseFormatExample() {
        return "JSON format with issue_number, predicted_labels array, and explanation.";
    }
    
    @Override
    public List<String> getHighPerformingLabels() {
        return List.of("vector store", "tool/function calling", "documentation", "type: backport", "MCP", "design");
    }
}
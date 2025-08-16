package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.domain.LabelPrediction;
import org.springaicommunity.github.ai.classification.service.*;
import org.springaicommunity.github.ai.collection.Author;
import org.springaicommunity.github.ai.collection.Issue;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.*;

/**
 * Comprehensive F1 Score evaluation test to measure our Java implementation
 * against the Python baseline of 82.1% F1 score.
 * 
 * This test evaluates both LLM-based and rule-based classification approaches
 * on a realistic test dataset to assess performance.
 */
@DisplayName("F1 Score Evaluation Test")
class F1ScoreEvaluationTest {
    
    private UnifiedClassificationService unifiedService;
    private SpringAIContextService contextService;
    
    // Test dataset representing diverse Spring AI issues
    private List<TestCase> testDataset;
    
    @BeforeEach
    void setUp() {
        // Initialize services manually for testing
        ObjectMapper objectMapper = new ObjectMapper();
        contextService = new SpringAIContextService(objectMapper);
        contextService.afterPropertiesSet(); // Load Spring AI context data
        
        // Set up rule-based service
        KeywordMatchingEngine keywordEngine = new KeywordMatchingEngine();
        ContextMatchingEngine contextEngine = new ContextMatchingEngine(contextService);
        PhraseMatchingEngine phraseEngine = new PhraseMatchingEngine(contextService);
        RuleBasedConfidenceCalculator confidenceCalculator = new RuleBasedConfidenceCalculator(
            keywordEngine, contextEngine, phraseEngine);
        RuleBasedClassificationService ruleBasedService = new RuleBasedClassificationService(
            confidenceCalculator, contextService);
        
        // Set up LLM-based service with real Claude Code SDK
        DefaultPromptTemplateService promptService = new DefaultPromptTemplateService(contextService);
        ObjectMapper claudeObjectMapper = new ObjectMapper();
        java.util.concurrent.Executor executor = java.util.concurrent.ForkJoinPool.commonPool();
        ClaudeLLMClient claudeClient = new ClaudeLLMClient(promptService, claudeObjectMapper, executor);
        org.springaicommunity.github.ai.classification.domain.ClassificationConfig defaultConfig = 
            org.springaicommunity.github.ai.classification.domain.ClassificationConfig.defaults();
        DefaultIssueClassificationService llmService = new DefaultIssueClassificationService(claudeClient, defaultConfig);
        
        unifiedService = new UnifiedClassificationService(llmService, ruleBasedService);
        
        // Initialize test dataset
        initializeTestDataset();
    }
    
    @Test
    @DisplayName("Comprehensive F1 Score Evaluation - LLM vs Rule-based vs Ground Truth")
    void testF1ScoreEvaluation() {
        System.out.println("\n=== F1 Score Evaluation Test ===");
        System.out.println("Target: 82.1% F1 score (Python baseline)");
        System.out.println("Test dataset size: " + testDataset.size() + " issues");
        
        EvaluationResults llmResults = new EvaluationResults("LLM-based (Claude AI)");
        EvaluationResults ruleResults = new EvaluationResults("Rule-based");
        
        // Process each test case
        for (int i = 0; i < Math.min(testDataset.size(), 10); i++) { // Test first 10 issues for speed
            TestCase testCase = testDataset.get(i);
            System.out.println("\n--- Processing Issue #" + testCase.issueNumber + " ---");
            System.out.println("Title: " + testCase.title);
            System.out.println("Expected labels: " + testCase.expectedLabels);
            
            ClassificationRequest request = ClassificationRequest.builder()
                .issueNumber(testCase.issueNumber)
                .title(testCase.title)
                .body(testCase.body)
                .availableLabels(getAllAvailableLabels())
                .build();
            
            try {
                // Compare both approaches
                UnifiedClassificationService.ClassificationComparison comparison = 
                    unifiedService.compareApproaches(request);
                
                // Extract predicted labels
                Set<String> llmPredicted = comparison.llmResult().predictedLabels().stream()
                    .map(LabelPrediction::label)
                    .collect(Collectors.toSet());
                
                Set<String> rulePredicted = comparison.ruleBasedResult().predictedLabels().stream()
                    .map(LabelPrediction::label)
                    .collect(Collectors.toSet());
                
                System.out.println("LLM predicted: " + llmPredicted);
                System.out.println("Rule predicted: " + rulePredicted);
                
                // Update evaluation results
                llmResults.addPrediction(testCase.expectedLabels, llmPredicted);
                ruleResults.addPrediction(testCase.expectedLabels, rulePredicted);
                
            } catch (Exception e) {
                System.out.println("❌ Error processing issue: " + e.getMessage());
                // Add as missed prediction
                llmResults.addPrediction(testCase.expectedLabels, Set.of());
                ruleResults.addPrediction(testCase.expectedLabels, Set.of());
            }
        }
        
        // Calculate and display results
        System.out.println("\n=== EVALUATION RESULTS ===");
        displayResults(llmResults);
        displayResults(ruleResults);
        
        // Compare against Python baseline
        System.out.println("\n=== COMPARISON WITH PYTHON BASELINE ===");
        double pythonF1 = 82.1;
        System.out.println("Python baseline F1: " + String.format("%.1f%%", pythonF1));
        System.out.println("LLM-based F1: " + String.format("%.1f%%", llmResults.getF1Score() * 100));
        System.out.println("Rule-based F1: " + String.format("%.1f%%", ruleResults.getF1Score() * 100));
        
        double llmDifference = (llmResults.getF1Score() * 100) - pythonF1;
        System.out.println("LLM vs Python: " + String.format("%+.1f%%", llmDifference));
        
        // Validate that we're getting reasonable results
        assertThat(llmResults.getF1Score()).isGreaterThan(0.3); // At least 30% F1
        assertThat(ruleResults.getF1Score()).isGreaterThan(0.2); // At least 20% F1
        // Don't assert equal predictions since approaches differ in number of labels predicted
    }
    
    private void displayResults(EvaluationResults results) {
        System.out.println("\n--- " + results.methodName + " Results ---");
        System.out.println("Precision: " + String.format("%.3f (%.1f%%)", results.getPrecision(), results.getPrecision() * 100));
        System.out.println("Recall: " + String.format("%.3f (%.1f%%)", results.getRecall(), results.getRecall() * 100));
        System.out.println("F1 Score: " + String.format("%.3f (%.1f%%)", results.getF1Score(), results.getF1Score() * 100));
        System.out.println("True Positives: " + results.truePositives);
        System.out.println("False Positives: " + results.falsePositives);
        System.out.println("False Negatives: " + results.falseNegatives);
        System.out.println("Total Predictions: " + results.totalPredictions);
        System.out.println("Total Ground Truth: " + results.totalGroundTruth);
    }
    
    private void initializeTestDataset() {
        testDataset = Arrays.asList(
            // Vector store issues
            new TestCase(1776, "PGVector connection timeout issues", 
                "I'm having trouble connecting to my postgres vector database. The connection " +
                "times out when trying to store embeddings using spring-ai-pgvector-store.",
                Set.of("vector store", "pgvector", "configuration")),
            
            // Function calling issues  
            new TestCase(1777, "Function calling not working with custom tools",
                "My function calling implementation is failing. I've defined a custom tool with " +
                "@Tool annotation but the LLM is not calling it properly.",
                Set.of("tool/function calling", "configuration")),
            
            // RAG issues
            new TestCase(1778, "RAG retrieval returns no results",
                "My RAG implementation is not returning any results from the vector store. " +
                "The similarity search seems to be working but no documents are retrieved.",
                Set.of("RAG", "vector store")),
            
            // OpenAI issues
            new TestCase(1779, "OpenAI API timeout errors", 
                "Getting frequent timeout errors when calling OpenAI GPT-4 API through Spring AI. " +
                "The requests work fine directly but fail through the Spring AI client.",
                Set.of("openai", "configuration")),
            
            // Documentation issues
            new TestCase(1780, "Missing documentation for vector store configuration",
                "The documentation doesn't explain how to configure multiple vector stores. " +
                "Need examples for setting up both Pinecone and Qdrant together.",
                Set.of("documentation", "vector store")),
            
            // Ollama issues  
            new TestCase(1781, "Ollama model loading failures",
                "Cannot load Llama models through Ollama integration. Getting model not found " +
                "errors even though the model is available locally.",
                Set.of("ollama", "configuration")),
            
            // Azure issues
            new TestCase(1782, "Azure OpenAI streaming not working",
                "Streaming responses from Azure OpenAI service are not working. Regular " +
                "requests work fine but streaming returns empty responses.",
                Set.of("azure", "streaming")),
            
            // Observability issues
            new TestCase(1783, "Spring Boot metrics not being exported", 
                "Prometheus metrics for AI operations are not being exported by Spring Boot Actuator. " +
                "Need to see token usage and response times.",
                Set.of("Observability", "configuration")),
            
            // Chroma issues
            new TestCase(1784, "ChromaDB connection refused errors",
                "Getting connection refused errors when trying to connect to ChromaDB instance. " +
                "The database is running but Spring AI cannot connect.",
                Set.of("chromadb", "configuration")),
            
            // Transcription issues
            new TestCase(1785, "Audio transcription failing with file format error",
                "Audio transcription is failing with unsupported file format error. " +
                "Using WAV files but getting format not supported message.",
                Set.of("transcription models", "configuration")),
            
            // Generic configuration issue
            new TestCase(1786, "Application properties not being loaded",
                "Spring AI configuration properties in application.yml are not being loaded. " +
                "The application starts but uses default values instead of configured ones.",
                Set.of("configuration")),
            
            // Enhancement request  
            new TestCase(1787, "Add support for custom embedding models",
                "Would like to add support for custom embedding models beyond the built-in ones. " +
                "Need ability to plug in custom model implementations.",
                Set.of("enhancement", "embedding models"))
        );
    }
    
    private List<String> getAllAvailableLabels() {
        return Arrays.asList(
            "vector store", "pgvector", "pinecone", "qdrant", "chromadb",
            "tool/function calling", "RAG", "openai", "azure", "ollama", 
            "anthropic", "documentation", "configuration", "bug", "enhancement",
            "streaming", "Observability", "transcription models", "embedding models",
            "advisors", "prompt management", "MCP"
        );
    }
    
    // Test case data structure
    private static class TestCase {
        final int issueNumber;
        final String title;
        final String body;
        final Set<String> expectedLabels;
        
        TestCase(int issueNumber, String title, String body, Set<String> expectedLabels) {
            this.issueNumber = issueNumber;
            this.title = title;
            this.body = body;
            this.expectedLabels = expectedLabels;
        }
    }
    
    // Evaluation results tracker
    private static class EvaluationResults {
        final String methodName;
        int truePositives = 0;
        int falsePositives = 0;
        int falseNegatives = 0;
        int totalPredictions = 0;
        int totalGroundTruth = 0;
        
        EvaluationResults(String methodName) {
            this.methodName = methodName;
        }
        
        void addPrediction(Set<String> expected, Set<String> predicted) {
            // Calculate intersection for true positives
            Set<String> intersection = new HashSet<>(expected);
            intersection.retainAll(predicted);
            truePositives += intersection.size();
            
            // False positives: predicted but not in expected
            Set<String> falsePosSet = new HashSet<>(predicted);
            falsePosSet.removeAll(expected);
            falsePositives += falsePosSet.size();
            
            // False negatives: expected but not predicted
            Set<String> falseNegSet = new HashSet<>(expected);
            falseNegSet.removeAll(predicted);
            falseNegatives += falseNegSet.size();
            
            totalPredictions += predicted.size();
            totalGroundTruth += expected.size();
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
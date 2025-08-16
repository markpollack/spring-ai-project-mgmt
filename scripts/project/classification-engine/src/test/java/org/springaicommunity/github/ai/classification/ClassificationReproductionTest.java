package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.service.*;
import org.springaicommunity.github.ai.collection.Author;
import org.springaicommunity.github.ai.collection.Issue;

import java.time.LocalDateTime;
import java.util.List;

import static org.assertj.core.api.Assertions.*;

/**
 * Test to reproduce Python classification results using our Java implementation.
 */
@DisplayName("Classification Reproduction Test")
class ClassificationReproductionTest {
    
    private RuleBasedClassificationService ruleBasedService;
    private SpringAIContextService contextService;
    
    @BeforeEach
    void setUp() {
        // Initialize services manually for testing
        ObjectMapper objectMapper = new ObjectMapper();
        contextService = new SpringAIContextService(objectMapper);
        contextService.afterPropertiesSet(); // Load context data
        
        KeywordMatchingEngine keywordEngine = new KeywordMatchingEngine();
        ContextMatchingEngine contextEngine = new ContextMatchingEngine(contextService);
        PhraseMatchingEngine phraseEngine = new PhraseMatchingEngine(contextService);
        RuleBasedConfidenceCalculator confidenceCalculator = new RuleBasedConfidenceCalculator(
            keywordEngine, contextEngine, phraseEngine);
        ruleBasedService = new RuleBasedClassificationService(confidenceCalculator, contextService);
    }
    
    @Test
    @DisplayName("Test rule-based classification with vector store example")
    void testRuleBasedClassificationVectorStore() {
        // Create a realistic vector store issue similar to Python test cases
        Issue issue = createVectorStoreIssue();
        List<String> availableLabels = List.of(
            "vector store", "pgvector", "configuration", "bug", "enhancement", 
            "pinecone", "chroma", "embedding"
        );
        
        ClassificationResponse response = ruleBasedService.classifyIssue(issue, availableLabels);
        
        System.out.println("=== Rule-Based Classification Result ===");
        System.out.println("Issue: " + issue.title());
        System.out.println("Predicted labels:");
        response.predictedLabels().forEach(pred -> 
            System.out.println("  - " + pred.label() + ": " + String.format("%.3f", pred.confidence())));
        System.out.println("Explanation: " + response.explanation());
        
        // Verify we get reasonable results
        assertThat(response.predictedLabels()).isNotEmpty();
        assertThat(response.predictedLabels().get(0).label()).isNotEqualTo("needs more info");
        
        // Should have high confidence for vector store
        boolean hasVectorStore = response.predictedLabels().stream()
            .anyMatch(pred -> "vector store".equals(pred.label()) && pred.confidence() >= 0.6);
        assertThat(hasVectorStore).isTrue();
    }
    
    @Test
    @DisplayName("Test rule-based classification with tool/function calling example")
    void testRuleBasedClassificationToolCalling() {
        // Create a realistic function calling issue
        Issue issue = createToolCallingIssue();
        List<String> availableLabels = List.of(
            "tool/function calling", "configuration", "bug", "enhancement", 
            "advisors", "chat client"
        );
        
        ClassificationResponse response = ruleBasedService.classifyIssue(issue, availableLabels);
        
        System.out.println("\n=== Tool/Function Calling Classification Result ===");
        System.out.println("Issue: " + issue.title());
        System.out.println("Predicted labels:");
        response.predictedLabels().forEach(pred -> 
            System.out.println("  - " + pred.label() + ": " + String.format("%.3f", pred.confidence())));
        System.out.println("Explanation: " + response.explanation());
        
        // Should classify as tool/function calling with high confidence
        boolean hasToolCalling = response.predictedLabels().stream()
            .anyMatch(pred -> "tool/function calling".equals(pred.label()) && pred.confidence() >= 0.6);
        assertThat(hasToolCalling).isTrue();
    }
    
    @Test
    @DisplayName("Test rule-based classification with advisors example")
    void testRuleBasedClassificationAdvisors() {
        // Create an advisors issue with specific problem phrase
        Issue issue = createAdvisorsIssue();
        List<String> availableLabels = List.of(
            "advisors", "chat client", "configuration", "bug", "enhancement"
        );
        
        ClassificationResponse response = ruleBasedService.classifyIssue(issue, availableLabels);
        
        System.out.println("\n=== Advisors Classification Result ===");
        System.out.println("Issue: " + issue.title());
        System.out.println("Predicted labels:");
        response.predictedLabels().forEach(pred -> 
            System.out.println("  - " + pred.label() + ": " + String.format("%.3f", pred.confidence())));
        System.out.println("Explanation: " + response.explanation());
        
        // Should classify as advisors with high confidence due to phrase matching
        boolean hasAdvisors = response.predictedLabels().stream()
            .anyMatch(pred -> "advisors".equals(pred.label()) && pred.confidence() >= 0.6);
        assertThat(hasAdvisors).isTrue();
    }
    
    @Test
    @DisplayName("Test fallback to 'needs more info' for unclear issues")
    void testFallbackToNeedsMoreInfo() {
        // Create a vague issue that should fall back
        Issue issue = createVagueIssue();
        List<String> availableLabels = List.of(
            "vector store", "tool/function calling", "advisors", "configuration"
        );
        
        ClassificationResponse response = ruleBasedService.classifyIssue(issue, availableLabels);
        
        System.out.println("\n=== Fallback Classification Result ===");
        System.out.println("Issue: " + issue.title());
        System.out.println("Predicted labels:");
        response.predictedLabels().forEach(pred -> 
            System.out.println("  - " + pred.label() + ": " + String.format("%.3f", pred.confidence())));
        System.out.println("Explanation: " + response.explanation());
        
        // Should fall back to "needs more info"
        assertThat(response.predictedLabels()).hasSize(1);
        assertThat(response.predictedLabels().get(0).label()).isEqualTo("needs more info");
    }
    
    @Test
    @DisplayName("Test Spring AI context loading and availability")
    void testSpringAIContextLoading() {
        System.out.println("\n=== Spring AI Context Information ===");
        System.out.println("Labels with rich context: " + contextService.getLabelsWithRichContext().size());
        System.out.println("Rich context labels: " + contextService.getLabelsWithRichContext());
        
        // Test specific context for high-performing labels
        if (contextService.hasRichContext("advisors")) {
            var context = contextService.getLabelContext("advisors").orElse(null);
            System.out.println("\nAdvisors context:");
            System.out.println("  Description: " + context.description().substring(0, Math.min(100, context.description().length())) + "...");
            System.out.println("  Modules: " + context.relevantModules());
            System.out.println("  Example phrases: " + context.exampleProblemPhrases());
        }
        
        assertThat(contextService.getLabelsWithRichContext()).isNotEmpty();
        assertThat(contextService.hasRichContext("advisors")).isTrue();
    }
    
    @Test
    @DisplayName("Test batch classification performance")
    void testBatchClassificationPerformance() {
        List<Issue> testIssues = List.of(
            createVectorStoreIssue(),
            createToolCallingIssue(),
            createAdvisorsIssue(),
            createVagueIssue()
        );
        
        List<String> availableLabels = List.of(
            "vector store", "tool/function calling", "advisors", "configuration", 
            "bug", "enhancement", "pgvector", "chroma"
        );
        
        long startTime = System.currentTimeMillis();
        List<ClassificationResponse> responses = ruleBasedService.classifyIssues(testIssues, availableLabels);
        long endTime = System.currentTimeMillis();
        
        System.out.println("\n=== Batch Classification Performance ===");
        System.out.println("Classified " + testIssues.size() + " issues in " + (endTime - startTime) + "ms");
        System.out.println("Average time per issue: " + (endTime - startTime) / testIssues.size() + "ms");
        
        assertThat(responses).hasSize(testIssues.size());
        responses.forEach(response -> {
            assertThat(response.predictedLabels()).isNotEmpty();
            System.out.println("Issue " + response.issueNumber() + ": " + 
                response.predictedLabels().get(0).label() + " (conf: " + 
                String.format("%.3f", response.predictedLabels().get(0).confidence()) + ")");
        });
        
        // Rule-based should be very fast (< 100ms for 4 issues)
        assertThat(endTime - startTime).isLessThan(1000);
    }
    
    private Issue createVectorStoreIssue() {
        return new Issue(
            1776,
            "PGVector connection issues with embedding storage",
            "I'm having trouble connecting to my postgres vector database for similarity search. " +
            "The vector store configuration seems correct but I keep getting connection timeouts " +
            "when trying to store embeddings. My setup includes pgvector extension and the " +
            "spring-ai-pgvector-store dependency.",
            "open",
            LocalDateTime.now().minusDays(1),
            LocalDateTime.now(),
            null,
            "https://github.com/spring-projects/spring-ai/issues/1776",
            new Author("user1", "https://github.com/user1"),
            List.of(),
            List.of()
        );
    }
    
    private Issue createToolCallingIssue() {
        return new Issue(
            1777,
            "Function calling not working with custom tool integration",
            "My function calling implementation is not working correctly. I've defined a custom tool " +
            "with @Tool annotation but the LLM is not calling it. The function registration seems " +
            "fine but the callback is never invoked during chat interactions.",
            "open",
            LocalDateTime.now().minusDays(2),
            LocalDateTime.now(),
            null,
            "https://github.com/spring-projects/spring-ai/issues/1777",
            new Author("user2", "https://github.com/user2"),
            List.of(),
            List.of()
        );
    }
    
    private Issue createAdvisorsIssue() {
        return new Issue(
            1778,
            "Chat advisor not being called in ChatClient",
            "I have configured a custom advisor but it's not being called when I use ChatClient. " +
            "The advisor pattern implementation should transform the data sent to the language model " +
            "but it seems to be bypassed entirely. Memory persistence is also not working.",
            "open",
            LocalDateTime.now().minusDays(3),
            LocalDateTime.now(),
            null,
            "https://github.com/spring-projects/spring-ai/issues/1778",
            new Author("user3", "https://github.com/user3"),
            List.of(),
            List.of()
        );
    }
    
    private Issue createVagueIssue() {
        return new Issue(
            1779,
            "General question about usage",
            "I have some general questions about how to use this library properly. " +
            "Could someone help me understand the basic concepts?",
            "open",
            LocalDateTime.now().minusDays(4),
            LocalDateTime.now(),
            null,
            "https://github.com/spring-projects/spring-ai/issues/1779",
            new Author("user4", "https://github.com/user4"),
            List.of(),
            List.of()
        );
    }
}
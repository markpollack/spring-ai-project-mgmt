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
 * Test to reproduce Python LLM-based classification results that achieved 82.1% F1 score.
 * This tests our Java implementation of the Claude AI approach using classification-4.md prompt.
 */
@DisplayName("LLM Classification Reproduction Test")
class LLMClassificationReproductionTest {
    
    private UnifiedClassificationService unifiedService;
    private SpringAIContextService contextService;
    
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
    }
    
    @Test
    @DisplayName("Test LLM vs Rule-based classification comparison")
    void testLLMVsRuleBasedComparison() {
        System.out.println("\n=== LLM vs Rule-Based Classification Comparison ===");
        
        // Test with high-confidence vector store issue
        ClassificationRequest request = ClassificationRequest.builder()
            .issueNumber(1776)
            .title("PGVector connection issues with embedding storage")
            .body("I'm having trouble connecting to my postgres vector database for similarity search. " +
                  "The vector store configuration seems correct but I keep getting connection timeouts " +
                  "when trying to store embeddings. My setup includes pgvector extension and the " +
                  "spring-ai-pgvector-store dependency.")
            .availableLabels(List.of("vector store", "pgvector", "configuration", "bug", "enhancement"))
            .build();
        
        // Compare both approaches
        UnifiedClassificationService.ClassificationComparison comparison = 
            unifiedService.compareApproaches(request);
        
        System.out.println("Issue: " + request.title());
        System.out.println("\nLLM-based result:");
        comparison.llmResult().predictedLabels().forEach(pred -> 
            System.out.println("  - " + pred.label() + ": " + String.format("%.3f", pred.confidence())));
        
        System.out.println("\nRule-based result:");
        comparison.ruleBasedResult().predictedLabels().forEach(pred -> 
            System.out.println("  - " + pred.label() + ": " + String.format("%.3f", pred.confidence())));
        
        System.out.println("\nPrimary labels agree: " + comparison.primaryLabelsAgree());
        if (!Double.isNaN(comparison.primaryConfidenceDifference())) {
            System.out.println("Confidence difference: " + 
                String.format("%.3f", comparison.primaryConfidenceDifference()));
        }
        
        // Both approaches should produce reasonable results
        assertThat(comparison.llmResult().predictedLabels()).isNotEmpty();
        assertThat(comparison.ruleBasedResult().predictedLabels()).isNotEmpty();
    }
    
    @Test
    @DisplayName("Test Spring AI enhanced prompt generation")
    void testSpringAIEnhancedPromptGeneration() {
        System.out.println("\n=== Spring AI Enhanced Prompt Test ===");
        
        // Create prompt template service to test enhanced prompts
        DefaultPromptTemplateService promptService = new DefaultPromptTemplateService(contextService);
        
        ClassificationRequest request = ClassificationRequest.builder()
            .issueNumber(1777)
            .title("Function calling not working with custom tool integration")
            .body("My function calling implementation is not working correctly. I've defined a custom tool " +
                  "with @Tool annotation but the LLM is not calling it.")
            .availableLabels(List.of("tool/function calling", "advisors", "configuration", "bug"))
            .build();
        
        String prompt = promptService.buildClassificationPrompt(request);
        
        System.out.println("Generated prompt length: " + prompt.length() + " characters");
        System.out.println("Contains Spring AI context: " + prompt.contains("Spring AI Project Context"));
        System.out.println("Contains high-priority labels: " + prompt.contains("High-Priority Technical Labels"));
        System.out.println("Contains conservative instructions: " + prompt.contains("conservative confidence"));
        
        // Should contain Spring AI-specific enhancements
        assertThat(prompt).contains("Spring AI Project Context");
        assertThat(prompt).contains("High-Priority Technical Labels with Spring AI Context");
        assertThat(prompt).contains("conservative confidence");
        assertThat(prompt).contains("maximum 2 labels");
        assertThat(prompt).contains("confidence >= 0.7");
        
        // Should contain enhanced label information for tool/function calling
        if (request.availableLabels().contains("tool/function calling")) {
            // The prompt should contain rich context for this high-performing label
            assertThat(prompt.length()).isGreaterThan(1000); // Should be substantial with context
        }
    }
    
    @Test
    @DisplayName("Test system statistics and availability")
    void testSystemStatisticsAndAvailability() {
        System.out.println("\n=== Classification System Statistics ===");
        
        UnifiedClassificationService.UnifiedClassificationStats stats = 
            unifiedService.getStatistics();
        
        System.out.println("Labels with rich context: " + stats.labelsWithRichContext());
        System.out.println("LLM available: " + stats.llmAvailable());
        System.out.println("Rule-based available: " + stats.ruleBasedAvailable());
        System.out.println("Sample context labels: " + 
            stats.labelsWithContext().stream().limit(10).toList());
        
        // Should have substantial Spring AI context
        assertThat(stats.labelsWithRichContext()).isGreaterThan(50);
        assertThat(stats.ruleBasedAvailable()).isTrue();
        assertThat(stats.labelsWithContext()).contains("advisors", "vector store");
    }
    
}
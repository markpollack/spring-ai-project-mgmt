package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.service.*;
import org.springaicommunity.github.ai.collection.Issue;

import java.util.List;

import static org.assertj.core.api.Assertions.*;

/**
 * Comprehensive unit tests for rule-based classification system.
 * Uses plain JUnit to avoid Spring context issues.
 */
@DisplayName("Rule-Based Classification - Unit Tests")
class RuleBasedClassification_Unit_Tests extends ClassificationTestBase {
    
    private KeywordMatchingEngine keywordEngine;
    private ContextMatchingEngine contextEngine;
    private PhraseMatchingEngine phraseEngine;
    private RuleBasedConfidenceCalculator confidenceCalculator;
    private RuleBasedClassificationService classificationService;
    private SpringAIContextService contextService;
    
    @BeforeEach
    void setUp() {
        // Initialize services manually for unit testing
        ObjectMapper objectMapper = getTestObjectMapper();
        contextService = new SpringAIContextService(objectMapper);
        contextService.afterPropertiesSet(); // Initialize context data
        
        keywordEngine = new KeywordMatchingEngine();
        contextEngine = new ContextMatchingEngine(contextService);
        phraseEngine = new PhraseMatchingEngine(contextService);
        confidenceCalculator = new RuleBasedConfidenceCalculator(keywordEngine, contextEngine, phraseEngine);
        classificationService = new RuleBasedClassificationService(confidenceCalculator, contextService);
    }
    
    @Nested
    @DisplayName("Keyword Matching Engine Tests")
    class KeywordMatchingEngineTests {
        
        @Test
        @DisplayName("Should match vector store keywords correctly")
        void shouldMatchVectorStoreKeywords() {
            String issueText = "i'm having issues with my vector database and embedding storage";
            
            double confidence = keywordEngine.calculateKeywordConfidence(issueText, "vector store");
            
            // Should match "vector" and "embedding" = 2 * 0.3 = 0.6
            assertThat(confidence).isEqualTo(0.6);
        }
        
        @Test
        @DisplayName("Should match tool/function calling keywords")
        void shouldMatchToolFunctionCallingKeywords() {
            String issueText = "my function calling is not working with the new tool integration";
            
            double confidence = keywordEngine.calculateKeywordConfidence(issueText, "tool/function calling");
            
            // Should match "function" and "tool" = 2 * 0.3 = 0.6
            assertThat(confidence).isEqualTo(0.6);
        }
        
        @Test
        @DisplayName("Should return zero confidence for unknown labels")
        void shouldReturnZeroForUnknownLabels() {
            String issueText = "some random issue text";
            
            double confidence = keywordEngine.calculateKeywordConfidence(issueText, "unknown-label");
            
            assertThat(confidence).isEqualTo(0.0);
        }
        
        @Test
        @DisplayName("Should be case insensitive")
        void shouldBeCaseInsensitive() {
            String issueText = "VECTOR DATABASE ISSUES";
            
            double confidence = keywordEngine.calculateKeywordConfidence(issueText, "vector store");
            
            assertThat(confidence).isGreaterThan(0.0);
        }
        
        @Test
        @DisplayName("Should have keywords for high-performing labels")
        void shouldHaveKeywordsForHighPerformingLabels() {
            assertThat(keywordEngine.hasKeywordsForLabel("vector store")).isTrue();
            assertThat(keywordEngine.hasKeywordsForLabel("tool/function calling")).isTrue();
            assertThat(keywordEngine.hasKeywordsForLabel("advisors")).isTrue();
            assertThat(keywordEngine.hasKeywordsForLabel("anthropic")).isTrue();
        }
    }
    
    @Nested
    @DisplayName("Context Matching Engine Tests")
    class ContextMatchingEngineTests {
        
        @Test
        @DisplayName("Should match Spring AI context data")
        void shouldMatchSpringAIContextData() {
            String issueText = "problem with spring-ai-client-chat advisor pattern implementations";
            
            double confidence = contextEngine.calculateContextConfidence(issueText, "advisors");
            
            // Should match module name and description words
            assertThat(confidence).isGreaterThan(0.0);
        }
        
        @Test
        @DisplayName("Should match package names")
        void shouldMatchPackageNames() {
            String issueText = "issue in org.springframework.ai.vectorstore.pinecone package";
            
            double confidence = contextEngine.calculateContextConfidence(issueText, "pinecone");
            
            assertThat(confidence).isGreaterThan(0.0);
        }
        
        @Test
        @DisplayName("Should return zero for labels without context")
        void shouldReturnZeroForLabelsWithoutContext() {
            String issueText = "some random text";
            
            double confidence = contextEngine.calculateContextConfidence(issueText, "unknown-label");
            
            assertThat(confidence).isEqualTo(0.0);
        }
        
        @Test
        @DisplayName("Should identify labels with rich context")
        void shouldIdentifyLabelsWithRichContext() {
            // These should have rich context from the enhanced JSON
            assertThat(contextEngine.hasContextForLabel("advisors")).isTrue();
            assertThat(contextEngine.hasContextForLabel("vector store")).isTrue();
        }
    }
    
    @Nested
    @DisplayName("Phrase Matching Engine Tests")
    class PhraseMatchingEngineTests {
        
        @Test
        @DisplayName("Should match example problem phrases")
        void shouldMatchExampleProblemPhrases() {
            String issueText = "advisor not being called in my chat client";
            
            double confidence = phraseEngine.calculatePhraseConfidence(issueText, "advisors");
            
            // Should match "advisor not being called" phrase = 0.4
            assertThat(confidence).isGreaterThanOrEqualTo(0.4);
        }
        
        @Test
        @DisplayName("Should find matching phrases for explanation")
        void shouldFindMatchingPhrasesForExplanation() {
            String issueText = "advisor not being called in my application";
            
            PhraseMatchingEngine.PhraseMatchResult result = 
                phraseEngine.findMatchingPhrases(issueText, "advisors");
            
            assertThat(result.hasMatches()).isTrue();
            assertThat(result.matchedProblemPhrases()).isNotEmpty();
            assertThat(result.getExplanation()).contains("advisor not being called");
        }
        
        @Test
        @DisplayName("Should return zero confidence for no phrase matches")
        void shouldReturnZeroForNoPhraseMatches() {
            String issueText = "completely unrelated issue content";
            
            double confidence = phraseEngine.calculatePhraseConfidence(issueText, "advisors");
            
            assertThat(confidence).isEqualTo(0.0);
        }
        
        @Test
        @DisplayName("Should identify labels with phrase data")
        void shouldIdentifyLabelsWithPhraseData() {
            assertThat(phraseEngine.hasPhraseDataForLabel("advisors")).isTrue();
            assertThat(phraseEngine.hasPhraseDataForLabel("unknown-label")).isFalse();
        }
    }
    
    @Nested
    @DisplayName("Confidence Calculator Tests")
    class ConfidenceCalculatorTests {
        
        @Test
        @DisplayName("Should aggregate confidence from all engines")
        void shouldAggregateConfidenceFromAllEngines() {
            String issueText = "vector database embedding storage similarity search";
            
            RuleBasedConfidenceCalculator.ConfidenceResult result = 
                confidenceCalculator.calculateConfidence(issueText, "vector store");
            
            assertThat(result.totalConfidence()).isGreaterThan(0.0);
            assertThat(result.keywordConfidence()).isGreaterThan(0.0);
            // Context and phrase confidence may be zero if no rich data for this label
        }
        
        @Test
        @DisplayName("Should cap confidence at 1.0")
        void shouldCapConfidenceAtOne() {
            // Create text with many matches to test capping
            String issueText = "vector vectorstore embedding similarity search " +
                             "database storage retrieval spring-ai-vectorstore " +
                             "vector database issues vector problems";
            
            RuleBasedConfidenceCalculator.ConfidenceResult result = 
                confidenceCalculator.calculateConfidence(issueText, "vector store");
            
            assertThat(result.totalConfidence()).isLessThanOrEqualTo(1.0);
        }
        
        @Test
        @DisplayName("Should apply correct thresholds")
        void shouldApplyCorrectThresholds() {
            assertThat(confidenceCalculator.meetsInclusionThreshold(0.4)).isTrue();
            assertThat(confidenceCalculator.meetsInclusionThreshold(0.2)).isFalse();
            
            assertThat(confidenceCalculator.meetsHighConfidenceThreshold(0.7)).isTrue();
            assertThat(confidenceCalculator.meetsHighConfidenceThreshold(0.5)).isFalse();
        }
        
        @Test
        @DisplayName("Should provide detailed explanation")
        void shouldProvideDetailedExplanation() {
            String issueText = "vector database issues";
            
            RuleBasedConfidenceCalculator.ConfidenceResult result = 
                confidenceCalculator.calculateConfidence(issueText, "vector store");
            
            String explanation = result.getExplanation();
            assertThat(explanation).contains("Total:");
            if (result.keywordConfidence() > 0) {
                assertThat(explanation).contains("Keywords:");
            }
        }
    }
    
    @Nested
    @DisplayName("Rule-Based Classification Service Tests")
    class RuleBasedClassificationServiceTests {
        
        @Test
        @DisplayName("Should classify issue with high confidence labels")
        void shouldClassifyIssueWithHighConfidenceLabels() {
            Issue issue = createTestIssue(
                1234,
                "Vector database configuration issues",
                "I'm having problems with my vector store setup and embedding storage"
            );
            
            List<String> availableLabels = List.of("vector store", "configuration", "bug");
            
            ClassificationResponse response = classificationService.classifyIssue(issue, availableLabels);
            
            assertThat(response.isSuccessful()).isTrue();
            assertThat(response.predictedLabels()).isNotEmpty();
            assertThat(response.predictedLabels().get(0).label()).isNotEqualTo("needs more info");
        }
        
        @Test
        @DisplayName("Should fall back to 'needs more info' for low confidence")
        void shouldFallBackToNeedsMoreInfo() {
            Issue issue = createTestIssue(
                1234,
                "Vague issue title",
                "Some unclear problem description"
            );
            
            List<String> availableLabels = List.of("vector store", "advisors");
            
            ClassificationResponse response = classificationService.classifyIssue(issue, availableLabels);
            
            assertThat(response.isSuccessful()).isTrue();
            assertThat(response.predictedLabels()).hasSize(1);
            assertThat(response.predictedLabels().get(0).label()).isEqualTo("needs more info");
        }
        
        @Test
        @DisplayName("Should sort predictions by confidence")
        void shouldSortPredictionsByConfidence() {
            Issue issue = createTestIssue(
                1234,
                "Vector database tool function calling",
                "Issues with vector store and function calling tools"
            );
            
            List<String> availableLabels = List.of("vector store", "tool/function calling", "configuration");
            
            ClassificationResponse response = classificationService.classifyIssue(issue, availableLabels);
            
            assertThat(response.predictedLabels()).hasSizeGreaterThan(1);
            
            // Verify sorted by confidence (descending)
            for (int i = 0; i < response.predictedLabels().size() - 1; i++) {
                double currentConfidence = response.predictedLabels().get(i).confidence();
                double nextConfidence = response.predictedLabels().get(i + 1).confidence();
                assertThat(currentConfidence).isGreaterThanOrEqualTo(nextConfidence);
            }
        }
        
        @Test
        @DisplayName("Should handle classification request format")
        void shouldHandleClassificationRequestFormat() {
            ClassificationRequest request = new ClassificationRequest(
                1234,
                "Vector database issues",
                "Problems with embedding storage",
                List.of("vector store", "configuration")
            );
            
            ClassificationResponse response = classificationService.classifyFromRequest(request);
            
            assertThat(response.isSuccessful()).isTrue();
            assertThat(response.issueNumber()).isEqualTo(1234);
        }
        
        @Test
        @DisplayName("Should provide engine statistics")
        void shouldProvideEngineStatistics() {
            RuleBasedClassificationService.ClassificationEngineStats stats = 
                classificationService.getEngineStats();
            
            assertThat(stats.labelsWithRichContext()).isGreaterThan(0);
            assertThat(stats.labelsWithContext()).isNotEmpty();
        }
        
        @Test
        @DisplayName("Should skip labels not found in codebase")
        void shouldSkipLabelsNotFoundInCodebase() {
            Issue issue = createTestIssue(
                1234,
                "Some issue",
                "Some description"
            );
            
            // Include labels that should be skipped according to context service
            List<String> availableLabels = List.of("vector store", "unknown-label", "agents");
            
            ClassificationResponse response = classificationService.classifyIssue(issue, availableLabels);
            
            // Should not include predictions for labels marked as "Not found in project codebase"
            response.predictedLabels().forEach(prediction -> {
                assertThat(prediction.label()).isNotEqualTo("agents"); // This should be skipped
            });
        }
    }
    
    @Nested
    @DisplayName("Integration Tests")
    class IntegrationTests {
        
        @Test
        @DisplayName("Should reproduce Python classification logic for vector store")
        void shouldReproducePythonClassificationLogicForVectorStore() {
            // Test case based on typical vector store issue
            Issue issue = createTestIssue(
                1776,
                "PGVector connection issues",
                "I'm having trouble connecting to my postgres vector database for similarity search"
            );
            
            List<String> availableLabels = List.of("vector store", "pgvector", "configuration", "bug");
            
            ClassificationResponse response = classificationService.classifyIssue(issue, availableLabels);
            
            assertThat(response.isSuccessful()).isTrue();
            assertThat(response.predictedLabels()).isNotEmpty();
            
            // Should have high confidence for vector store related labels
            boolean hasVectorStoreLabel = response.predictedLabels().stream()
                .anyMatch(p -> "vector store".equals(p.label()) && p.confidence() >= 0.6);
            
            assertThat(hasVectorStoreLabel).isTrue();
        }
        
        @Test
        @DisplayName("Should handle batch classification")
        void shouldHandleBatchClassification() {
            List<Issue> issues = List.of(
                createTestIssue(1, "Vector store issues", "embedding problems"),
                createTestIssue(2, "Function calling not working", "tool integration fails"),
                createTestIssue(3, "Unclear problem", "vague description")
            );
            
            List<String> availableLabels = List.of("vector store", "tool/function calling", "configuration");
            
            List<ClassificationResponse> responses = classificationService.classifyIssues(issues, availableLabels);
            
            assertThat(responses).hasSize(3);
            assertThat(responses).allMatch(ClassificationResponse::isSuccessful);
        }
    }
}
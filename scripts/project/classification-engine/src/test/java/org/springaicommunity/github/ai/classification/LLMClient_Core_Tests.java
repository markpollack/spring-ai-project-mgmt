package org.springaicommunity.github.ai.classification;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.service.ClassificationException;
import org.springaicommunity.github.ai.classification.service.ClaudeLLMClient;
import org.springaicommunity.github.ai.classification.service.PromptTemplateService;

import java.util.List;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Core tests for LLMClient interface and ClaudeLLMClient implementation.
 * Uses flattened test architecture with comprehensive mocking.
 */
@DisplayName("LLM Client - Core Tests")
class LLMClient_Core_Tests extends ClassificationTestBase {
    
    @Mock
    private PromptTemplateService promptTemplateService;
    
    private ClaudeLLMClient llmClient;
    
    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        llmClient = new ClaudeLLMClient(
            promptTemplateService, 
            getTestObjectMapper(), 
            getTestExecutor()
        );
    }
    
    @Test
    @DisplayName("Max batch size should be correctly configured")
    void maxBatchSizeConfiguration() {
        assertThat(llmClient.getMaxBatchSize()).isEqualTo(25);
    }
    
    @Test
    @DisplayName("Token usage estimation should be reasonable")
    void tokenUsageEstimation() {
        ClassificationRequest request = createTestRequest();
        long estimated = llmClient.estimateTokenUsage(request);
        
        assertThat(estimated).isGreaterThan(2000); // Base prompt tokens
        assertThat(estimated).isLessThan(10000); // Reasonable upper bound
        
        // Should include content and label tokens
        int expectedContentTokens = request.getCharacterCount() / 4; // ~4 chars per token
        int expectedLabelTokens = request.availableLabels().size() * 5; // ~5 tokens per label
        assertThat(estimated).isGreaterThan(expectedContentTokens + expectedLabelTokens);
    }
    
    @Test
    @DisplayName("Empty batch classification should return empty list")
    void emptyBatchClassification() throws ClassificationException {
        List<ClassificationResponse> results = llmClient.classifyBatch(List.of());
        
        assertThat(results).isEmpty();
        verify(promptTemplateService, never()).buildBatchClassificationPrompt(any());
    }
    
    @Test
    @DisplayName("Oversized batch should be rejected")
    void oversizedBatchRejection() {
        List<ClassificationRequest> oversizedBatch = createTestRequestBatch(30); // > 25 limit
        
        assertThatThrownBy(() -> llmClient.classifyBatch(oversizedBatch))
            .isInstanceOf(ClassificationException.class)
            .hasMessageContaining("Batch size 30 exceeds maximum of 25")
            .extracting(ex -> ((ClassificationException) ex).getErrorType())
            .isEqualTo(ClassificationException.ErrorType.INVALID_REQUEST);
    }
    
    @Test
    @DisplayName("Prompt template service integration should work")
    void promptTemplateServiceIntegration() throws ClassificationException {
        ClassificationRequest request = createTestRequest();
        String mockPrompt = "Mock classification prompt for issue #" + request.issueNumber();
        
        when(promptTemplateService.buildClassificationPrompt(request)).thenReturn(mockPrompt);
        
        // This will fail due to actual Claude API call, but we can verify the prompt was built
        assertThatThrownBy(() -> llmClient.classifyIssue(request))
            .isInstanceOf(ClassificationException.class);
        
        verify(promptTemplateService).buildClassificationPrompt(request);
    }
    
    @Test
    @DisplayName("Batch prompt template integration should work")
    void batchPromptTemplateIntegration() {
        List<ClassificationRequest> requests = createTestRequestBatch(3);
        String mockBatchPrompt = "Mock batch classification prompt for " + requests.size() + " issues";
        
        when(promptTemplateService.buildBatchClassificationPrompt(requests)).thenReturn(mockBatchPrompt);
        
        // This will fail due to actual Claude API call, but we can verify the prompt was built
        assertThatThrownBy(() -> llmClient.classifyBatch(requests))
            .isInstanceOf(ClassificationException.class);
        
        verify(promptTemplateService).buildBatchClassificationPrompt(requests);
    }
    
    @Test
    @DisplayName("Async classification should be supported")
    void asyncClassificationSupport() {
        ClassificationRequest request = createTestRequest();
        when(promptTemplateService.buildClassificationPrompt(request)).thenReturn("Mock prompt");
        
        // Should return CompletableFuture without blocking
        var future = llmClient.classifyIssueAsync(request);
        
        assertThat(future).isNotNull();
        assertThat(future.isDone()).isFalse(); // Not immediately completed
        
        // Cancel to avoid actual API call
        future.cancel(true);
    }
    
    @Test
    @DisplayName("Async batch classification should be supported")
    void asyncBatchClassificationSupport() {
        List<ClassificationRequest> requests = createTestRequestBatch(2);
        when(promptTemplateService.buildBatchClassificationPrompt(requests)).thenReturn("Mock batch prompt");
        
        // Should return CompletableFuture without blocking
        var future = llmClient.classifyBatchAsync(requests);
        
        assertThat(future).isNotNull();
        assertThat(future.isDone()).isFalse(); // Not immediately completed
        
        // Cancel to avoid actual API call
        future.cancel(true);
    }
    
    /**
     * Helper method to create a batch of test requests.
     */
    private List<ClassificationRequest> createTestRequestBatch(int count) {
        return java.util.stream.IntStream.range(0, count)
            .mapToObj(i -> createTestRequest(1000 + i, "Test Issue " + i, "Test body " + i))
            .toList();
    }
}
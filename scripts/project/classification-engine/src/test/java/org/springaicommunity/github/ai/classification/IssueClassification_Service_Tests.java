package org.springaicommunity.github.ai.classification;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.domain.ClassificationResult;
import org.springaicommunity.github.ai.classification.service.*;
import org.springaicommunity.github.ai.collection.Issue;

import java.util.List;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Tests for IssueClassificationService implementation.
 * Uses flattened test architecture with comprehensive mocking.
 */
@DisplayName("Issue Classification - Service Tests")
class IssueClassification_Service_Tests extends ClassificationTestBase {
    
    @Mock
    private LLMClient llmClient;
    
    private DefaultIssueClassificationService classificationService;
    
    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        classificationService = new DefaultIssueClassificationService(llmClient, DEFAULT_CONFIG);
    }
    
    @Test
    @DisplayName("Single issue classification should work correctly")
    void singleIssueClassification() throws ClassificationException {
        Issue issue = createTestIssue();
        ClassificationResponse mockResponse = createSuccessResponse();
        
        when(llmClient.classifyIssue(any(ClassificationRequest.class))).thenReturn(mockResponse);
        
        ClassificationResult result = classificationService.classifyIssue(issue, TEST_AVAILABLE_LABELS);
        
        assertThat(result).isNotNull();
        assertThat(result.issueNumber()).isEqualTo(TEST_ISSUE_NUMBER);
        assertThat(result.predictedLabels()).hasSize(1);
        assertThat(result.predictedLabels().get(0).label()).isEqualTo("vector store");
        assertThat(result.predictedLabels().get(0).confidence()).isEqualTo(0.9);
        
        verify(llmClient).classifyIssue(any(ClassificationRequest.class));
    }
    
    @Test
    @DisplayName("Batch classification should split large batches")
    void batchClassificationWithSplitting() throws ClassificationException {
        // Create batch larger than max batch size
        List<Issue> issues = createTestIssueBatch(30); // > 25 max batch size
        
        when(llmClient.getMaxBatchSize()).thenReturn(25);
        when(llmClient.classifyBatch(any())).thenReturn(
            createMockResponseBatch(25), // First batch
            createMockResponseBatch(5)   // Second batch
        );
        
        List<ClassificationResult> results = classificationService.classifyBatch(issues, TEST_AVAILABLE_LABELS);
        
        assertThat(results).hasSize(30);
        
        // Should have made two batch calls
        verify(llmClient, times(2)).classifyBatch(any());
        
        // First call with 25 issues, second with 5
        verify(llmClient).classifyBatch(argThat(batch -> batch.size() == 25));
        verify(llmClient).classifyBatch(argThat(batch -> batch.size() == 5));
    }
    
    @Test
    @DisplayName("Empty batch should return empty results")
    void emptyBatchClassification() throws ClassificationException {
        List<ClassificationResult> results = classificationService.classifyBatch(List.of(), TEST_AVAILABLE_LABELS);
        
        assertThat(results).isEmpty();
        verify(llmClient, never()).classifyBatch(any());
    }
    
    @Test
    @DisplayName("Classification request conversion should be correct")
    void classificationRequestConversion() throws ClassificationException {
        Issue issue = createTestIssue(456, "Custom Title", "Custom Body");
        when(llmClient.classifyIssue(any())).thenReturn(createSuccessResponse(456, "test", 0.8));
        
        classificationService.classifyIssue(issue, TEST_AVAILABLE_LABELS);
        
        verify(llmClient).classifyIssue(argThat(request -> 
            request.issueNumber() == 456 &&
            request.title().equals("Custom Title") &&
            request.body().equals("Custom Body") &&
            request.availableLabels().equals(TEST_AVAILABLE_LABELS) &&
            request.config().equals(DEFAULT_CONFIG)
        ));
    }
    
    @Test
    @DisplayName("Null issue body should be handled")
    void nullIssueBodyHandling() throws ClassificationException {
        Issue issueWithNullBody = new Issue(
            123, "Title", null, "open", null, null, null,
            null, null, List.of(), List.of()
        );
        
        when(llmClient.classifyIssue(any())).thenReturn(createSuccessResponse(123, "test", 0.8));
        
        classificationService.classifyIssue(issueWithNullBody, TEST_AVAILABLE_LABELS);
        
        verify(llmClient).classifyIssue(argThat(request -> 
            request.body().equals("") // Null body should become empty string
        ));
    }
    
    @Test
    @DisplayName("LLM client exceptions should propagate")
    void llmClientExceptionPropagation() throws ClassificationException {
        Issue issue = createTestIssue();
        ClassificationException llmException = new ClassificationException(
            "API rate limit exceeded", 
            ClassificationException.ErrorType.RATE_LIMIT,
            300 // retry after seconds
        );
        
        when(llmClient.classifyIssue(any())).thenThrow(llmException);
        
        assertThatThrownBy(() -> classificationService.classifyIssue(issue, TEST_AVAILABLE_LABELS))
            .isInstanceOf(ClassificationException.class)
            .hasMessage("API rate limit exceeded")
            .extracting(ex -> ((ClassificationException) ex).getErrorType())
            .isEqualTo(ClassificationException.ErrorType.RATE_LIMIT);
    }
    
    @Test
    @DisplayName("Async classification should delegate to LLM client")
    void asyncClassificationDelegation() {
        Issue issue = createTestIssue();
        
        classificationService.classifyIssueAsync(issue, TEST_AVAILABLE_LABELS);
        
        verify(llmClient).classifyIssueAsync(any(ClassificationRequest.class));
    }
    
    @Test
    @DisplayName("Async batch classification should use sync implementation")
    void asyncBatchClassificationDelegation() throws ClassificationException {
        List<Issue> issues = createTestIssueBatch(3);
        when(llmClient.getMaxBatchSize()).thenReturn(25);
        when(llmClient.classifyBatch(any())).thenReturn(createMockResponseBatch(3));
        
        var future = classificationService.classifyBatchAsync(issues, TEST_AVAILABLE_LABELS);
        
        assertThat(future).isNotNull();
        assertThat(future.isDone()).isFalse();
        
        // Cancel to avoid blocking
        future.cancel(true);
    }
    
    @Test
    @DisplayName("Service availability should delegate to LLM client")
    void serviceAvailabilityDelegation() {
        when(llmClient.isAvailable()).thenReturn(true);
        
        boolean available = classificationService.isAvailable();
        
        assertThat(available).isTrue();
        verify(llmClient).isAvailable();
    }
    
    @Test
    @DisplayName("Max batch size should delegate to LLM client")
    void maxBatchSizeDelegation() {
        when(llmClient.getMaxBatchSize()).thenReturn(25);
        
        int maxBatchSize = classificationService.getMaxBatchSize();
        
        assertThat(maxBatchSize).isEqualTo(25);
        verify(llmClient).getMaxBatchSize();
    }
    
    @Test
    @DisplayName("Evaluation should create basic evaluation report")
    void evaluationReportCreation() {
        List<ClassificationResult> predictions = List.of(
            new ClassificationResult(100, List.of(), "Test"),
            new ClassificationResult(200, List.of(), "Test")
        );
        List<Issue> groundTruth = createTestIssueBatch(2);
        
        var report = classificationService.evaluateClassification(predictions, groundTruth);
        
        assertThat(report).isNotNull();
        assertThat(report.totalIssues()).isEqualTo(2);
        assertThat(report.timestamp()).isNotNull();
    }
    
    /**
     * Create a mock response batch for testing.
     */
    private List<ClassificationResponse> createMockResponseBatch(int count) {
        return java.util.stream.IntStream.range(0, count)
            .mapToObj(i -> createSuccessResponse(1000 + i, "test", 0.8))
            .toList();
    }
}
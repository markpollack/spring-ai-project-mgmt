package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springaicommunity.github.ai.classification.domain.*;
import org.springaicommunity.github.ai.collection.Issue;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.Executor;
import java.util.concurrent.ForkJoinPool;

/**
 * Base class providing shared test fixtures and utilities for classification tests.
 * 
 * <p>This class follows the flattened test architecture pattern established in Task 4,
 * providing common test data, mock setups, and utility methods without using nested
 * test classes that can cause JUnit 5 parameter resolution issues.</p>
 */
public class ClassificationTestBase {
    
    // Test fixtures
    protected static final int TEST_ISSUE_NUMBER = 1776;
    protected static final String TEST_ISSUE_TITLE = "Vector store integration failing with timeout";
    protected static final String TEST_ISSUE_BODY = "When using PineconeVectorStore with large embeddings, " +
        "the connection times out after 30 seconds. This affects retrieval performance in production.";
    
    protected static final List<String> TEST_AVAILABLE_LABELS = List.of(
        "vector store", "pinecone", "performance", "timeout", "bug", "enhancement"
    );
    
    protected static final List<String> HIGH_PERFORMING_LABELS = List.of(
        "vector store", "tool/function calling", "documentation", "type: backport", 
        "MCP", "design", "Bedrock", "model client"
    );
    
    // Configuration fixtures
    protected static final ClassificationConfig DEFAULT_CONFIG = ClassificationConfig.defaults();
    protected static final ClassificationConfig STRICT_CONFIG = ClassificationConfig.builder()
        .confidenceThreshold(0.8)
        .maxLabelsPerIssue(1)
        .batchSize(10)
        .build();
    
    // Timing fixtures
    protected static final Duration FAST_PROCESSING = Duration.ofMillis(100);
    protected static final Duration SLOW_PROCESSING = Duration.ofSeconds(2);
    protected static final Instant FIXED_TIMESTAMP = Instant.parse("2024-01-15T10:30:00Z");
    
    /**
     * Create a test GitHub Issue with default values.
     */
    protected Issue createTestIssue() {
        return createTestIssue(TEST_ISSUE_NUMBER, TEST_ISSUE_TITLE, TEST_ISSUE_BODY);
    }
    
    /**
     * Create a test GitHub Issue with custom values.
     */
    protected Issue createTestIssue(int number, String title, String body) {
        return new Issue(
            number, title, body, "open", null, null, null, 
            null, null, List.of(), List.of()
        );
    }
    
    /**
     * Create a test ClassificationRequest with default values.
     */
    protected ClassificationRequest createTestRequest() {
        return createTestRequest(TEST_ISSUE_NUMBER, TEST_ISSUE_TITLE, TEST_ISSUE_BODY);
    }
    
    /**
     * Create a test ClassificationRequest with custom values.
     */
    protected ClassificationRequest createTestRequest(int issueNumber, String title, String body) {
        return ClassificationRequest.builder()
            .issueNumber(issueNumber)
            .title(title)
            .body(body)
            .availableLabels(TEST_AVAILABLE_LABELS)
            .config(DEFAULT_CONFIG)
            .build();
    }
    
    /**
     * Create a successful classification response with vector store prediction.
     */
    protected ClassificationResponse createSuccessResponse() {
        return createSuccessResponse(TEST_ISSUE_NUMBER, "vector store", 0.9);
    }
    
    /**
     * Create a successful classification response with custom prediction.
     */
    protected ClassificationResponse createSuccessResponse(int issueNumber, String label, double confidence) {
        return ClassificationResponse.builder()
            .issueNumber(issueNumber)
            .predictedLabels(List.of(new LabelPrediction(label, confidence)))
            .explanation("Issue explicitly mentions " + label + " functionality")
            .processingTime(FAST_PROCESSING)
            .timestamp(FIXED_TIMESTAMP)
            .tokenUsage(1500L)
            .build();
    }
    
    /**
     * Create a fallback response for low confidence predictions.
     */
    protected ClassificationResponse createFallbackResponse(int issueNumber) {
        return ClassificationResponse.builder()
            .issueNumber(issueNumber)
            .predictedLabels(List.of(new LabelPrediction("needs more info", 0.3)))
            .explanation("Insufficient information to confidently assign specific labels")
            .processingTime(FAST_PROCESSING)
            .timestamp(FIXED_TIMESTAMP)
            .tokenUsage(800L)
            .build();
    }
    
    /**
     * Create a multi-label classification response.
     */
    protected ClassificationResponse createMultiLabelResponse(int issueNumber) {
        return ClassificationResponse.builder()
            .issueNumber(issueNumber)
            .predictedLabels(List.of(
                new LabelPrediction("vector store", 0.9),
                new LabelPrediction("performance", 0.8)
            ))
            .explanation("Issue involves vector store performance problems")
            .processingTime(FAST_PROCESSING)
            .timestamp(FIXED_TIMESTAMP)
            .tokenUsage(2000L)
            .build();
    }
    
    /**
     * Get a pre-configured ObjectMapper for testing.
     */
    protected ObjectMapper getTestObjectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JavaTimeModule());
        return mapper;
    }
    
    /**
     * Get a test executor for async operations.
     */
    protected Executor getTestExecutor() {
        return ForkJoinPool.commonPool();
    }
    
    /**
     * Create a list of test issues for batch processing.
     */
    protected List<Issue> createTestIssueBatch(int count) {
        return createTestIssueBatch(count, "Test issue");
    }
    
    /**
     * Create a list of test issues with custom title prefix.
     */
    protected List<Issue> createTestIssueBatch(int count, String titlePrefix) {
        List<Issue> issues = new java.util.ArrayList<>();
        for (int i = 1; i <= count; i++) {
            issues.add(createTestIssue(
                1000 + i,
                titlePrefix + " #" + i,
                "Test body for issue " + i
            ));
        }
        return issues;
    }
    
    /**
     * Assert that a classification response has valid structure.
     */
    protected void assertValidClassificationResponse(ClassificationResponse response, int expectedIssueNumber) {
        org.junit.jupiter.api.Assertions.assertNotNull(response, "Response should not be null");
        org.junit.jupiter.api.Assertions.assertEquals(expectedIssueNumber, response.issueNumber(), 
            "Issue number should match");
        org.junit.jupiter.api.Assertions.assertNotNull(response.predictedLabels(), 
            "Predicted labels should not be null");
        org.junit.jupiter.api.Assertions.assertNotNull(response.explanation(), 
            "Explanation should not be null");
        org.junit.jupiter.api.Assertions.assertFalse(response.explanation().trim().isEmpty(), 
            "Explanation should not be empty");
        org.junit.jupiter.api.Assertions.assertNotNull(response.processingTime(), 
            "Processing time should not be null");
        org.junit.jupiter.api.Assertions.assertNotNull(response.timestamp(), 
            "Timestamp should not be null");
    }
}
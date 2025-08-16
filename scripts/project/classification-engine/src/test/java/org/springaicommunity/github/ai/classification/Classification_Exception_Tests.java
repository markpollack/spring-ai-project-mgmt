package org.springaicommunity.github.ai.classification;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.springaicommunity.github.ai.classification.service.ClassificationException;

import static org.assertj.core.api.Assertions.*;

/**
 * Tests for ClassificationException error handling and behavior.
 * Uses flattened test architecture focused on exception scenarios.
 */
@DisplayName("Classification - Exception Tests")
class Classification_Exception_Tests extends ClassificationTestBase {
    
    @Test
    @DisplayName("Basic exception construction should work")
    void basicExceptionConstruction() {
        ClassificationException exception = new ClassificationException("Test message");
        
        assertThat(exception.getMessage()).isEqualTo("Test message");
        assertThat(exception.getErrorType()).isEqualTo(ClassificationException.ErrorType.UNKNOWN);
        assertThat(exception.getOriginalMessage()).isEqualTo("Test message");
        assertThat(exception.getRetryAfterSeconds()).isEqualTo(-1);
        assertThat(exception.getCause()).isNull();
    }
    
    @Test
    @DisplayName("Exception with cause should preserve cause")
    void exceptionWithCause() {
        RuntimeException cause = new RuntimeException("Root cause");
        ClassificationException exception = new ClassificationException("Test message", cause);
        
        assertThat(exception.getMessage()).isEqualTo("Test message");
        assertThat(exception.getCause()).isSameAs(cause);
        assertThat(exception.getErrorType()).isEqualTo(ClassificationException.ErrorType.UNKNOWN);
    }
    
    @Test
    @DisplayName("Exception with error type should preserve type")
    void exceptionWithErrorType() {
        ClassificationException exception = new ClassificationException(
            "Rate limit exceeded", 
            ClassificationException.ErrorType.RATE_LIMIT
        );
        
        assertThat(exception.getErrorType()).isEqualTo(ClassificationException.ErrorType.RATE_LIMIT);
        assertThat(exception.getMessage()).isEqualTo("Rate limit exceeded");
        assertThat(exception.getRetryAfterSeconds()).isEqualTo(-1);
    }
    
    @Test
    @DisplayName("Exception with retry delay should preserve delay")
    void exceptionWithRetryDelay() {
        ClassificationException exception = new ClassificationException(
            "Service unavailable",
            ClassificationException.ErrorType.SERVICE_UNAVAILABLE,
            300
        );
        
        assertThat(exception.getErrorType()).isEqualTo(ClassificationException.ErrorType.SERVICE_UNAVAILABLE);
        assertThat(exception.getRetryAfterSeconds()).isEqualTo(300);
        assertThat(exception.getMessage()).isEqualTo("Service unavailable");
    }
    
    @Test
    @DisplayName("Exception with all parameters should work")
    void exceptionWithAllParameters() {
        RuntimeException cause = new RuntimeException("API error");
        ClassificationException exception = new ClassificationException(
            "Authentication failed",
            ClassificationException.ErrorType.AUTH_ERROR,
            cause
        );
        
        assertThat(exception.getMessage()).isEqualTo("Authentication failed");
        assertThat(exception.getErrorType()).isEqualTo(ClassificationException.ErrorType.AUTH_ERROR);
        assertThat(exception.getCause()).isSameAs(cause);
        assertThat(exception.getOriginalMessage()).isEqualTo("Authentication failed");
    }
    
    @ParameterizedTest
    @DisplayName("Retry logic should work for retryable error types")
    @EnumSource(value = ClassificationException.ErrorType.class, 
               names = {"RATE_LIMIT", "SERVICE_UNAVAILABLE", "API_ERROR"})
    void retryableErrorTypes(ClassificationException.ErrorType errorType) {
        ClassificationException exception = new ClassificationException(
            "Test message", 
            errorType
        );
        
        assertThat(exception.isRetryable()).isTrue();
    }
    
    @ParameterizedTest
    @DisplayName("Non-retry logic should work for non-retryable error types")
    @EnumSource(value = ClassificationException.ErrorType.class, 
               names = {"INVALID_REQUEST", "AUTH_ERROR", "RESPONSE_PARSING_ERROR", "UNKNOWN"})
    void nonRetryableErrorTypes(ClassificationException.ErrorType errorType) {
        ClassificationException exception = new ClassificationException(
            "Test message", 
            errorType
        );
        
        assertThat(exception.isRetryable()).isFalse();
    }
    
    @Test
    @DisplayName("ToString should include relevant information")
    void toStringContent() {
        ClassificationException exception = new ClassificationException(
            "Service temporarily unavailable",
            ClassificationException.ErrorType.SERVICE_UNAVAILABLE,
            120
        );
        
        String toString = exception.toString();
        
        assertThat(toString).contains("ClassificationException");
        assertThat(toString).contains("SERVICE_UNAVAILABLE");
        assertThat(toString).contains("Service temporarily unavailable");
        assertThat(toString).contains("retryAfterSeconds=120");
    }
    
    @Test
    @DisplayName("ToString without retry delay should not include retry info")
    void toStringWithoutRetryDelay() {
        ClassificationException exception = new ClassificationException(
            "Invalid request format",
            ClassificationException.ErrorType.INVALID_REQUEST
        );
        
        String toString = exception.toString();
        
        assertThat(toString).contains("ClassificationException");
        assertThat(toString).contains("INVALID_REQUEST");
        assertThat(toString).contains("Invalid request format");
        assertThat(toString).doesNotContain("retryAfterSeconds");
    }
    
    @Test
    @DisplayName("Error type enum should have all expected values")
    void errorTypeEnumCompleteness() {
        ClassificationException.ErrorType[] errorTypes = ClassificationException.ErrorType.values();
        
        assertThat(errorTypes).contains(
            ClassificationException.ErrorType.API_ERROR,
            ClassificationException.ErrorType.RATE_LIMIT,
            ClassificationException.ErrorType.INVALID_REQUEST,
            ClassificationException.ErrorType.RESPONSE_PARSING_ERROR,
            ClassificationException.ErrorType.AUTH_ERROR,
            ClassificationException.ErrorType.SERVICE_UNAVAILABLE,
            ClassificationException.ErrorType.UNKNOWN
        );
        
        assertThat(errorTypes).hasSize(7); // Ensure no unexpected additions
    }
    
    @Test
    @DisplayName("Exception chaining should work properly")
    void exceptionChaining() {
        Exception rootCause = new IllegalStateException("Root problem");
        RuntimeException intermediateCause = new RuntimeException("Intermediate problem", rootCause);
        ClassificationException finalException = new ClassificationException(
            "Classification failed", 
            ClassificationException.ErrorType.API_ERROR,
            intermediateCause
        );
        
        assertThat(finalException.getCause()).isSameAs(intermediateCause);
        assertThat(finalException.getCause().getCause()).isSameAs(rootCause);
        
        // Test stack trace preservation
        assertThat(finalException.getStackTrace()).isNotEmpty();
    }
    
    @Test
    @DisplayName("Exception should be properly serializable")
    void exceptionSerialization() {
        ClassificationException exception = new ClassificationException(
            "Test serialization",
            ClassificationException.ErrorType.RATE_LIMIT,
            60
        );
        
        // Basic serialization test - ensure all fields are accessible
        assertThat(exception.getMessage()).isNotNull();
        assertThat(exception.getErrorType()).isNotNull();
        assertThat(exception.getOriginalMessage()).isNotNull();
        assertThat(exception.getRetryAfterSeconds()).isGreaterThan(0);
        assertThat(exception.isRetryable()).isTrue();
    }
}
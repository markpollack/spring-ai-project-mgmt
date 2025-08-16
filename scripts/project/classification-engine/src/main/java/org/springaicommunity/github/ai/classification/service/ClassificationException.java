package org.springaicommunity.github.ai.classification.service;

/**
 * Exception thrown when LLM-based classification operations fail.
 * Provides specific error types and context information.
 */
public class ClassificationException extends Exception {
    
    /**
     * Types of classification errors that can occur
     */
    public enum ErrorType {
        /** API communication failure */
        API_ERROR,
        /** Request rate limit exceeded */
        RATE_LIMIT,
        /** Invalid request format or content */
        INVALID_REQUEST,
        /** LLM response parsing failure */
        RESPONSE_PARSING_ERROR,
        /** Authentication or authorization failure */
        AUTH_ERROR,
        /** Service temporarily unavailable */
        SERVICE_UNAVAILABLE,
        /** Unknown or unexpected error */
        UNKNOWN
    }
    
    private final ErrorType errorType;
    private final String originalMessage;
    private final int retryAfterSeconds;
    
    public ClassificationException(String message) {
        this(message, ErrorType.UNKNOWN);
    }
    
    public ClassificationException(String message, Throwable cause) {
        this(message, ErrorType.UNKNOWN, cause);
    }
    
    public ClassificationException(String message, ErrorType errorType) {
        super(message);
        this.errorType = errorType;
        this.originalMessage = message;
        this.retryAfterSeconds = -1;
    }
    
    public ClassificationException(String message, ErrorType errorType, Throwable cause) {
        super(message, cause);
        this.errorType = errorType;
        this.originalMessage = message;
        this.retryAfterSeconds = -1;
    }
    
    public ClassificationException(String message, ErrorType errorType, int retryAfterSeconds) {
        super(message);
        this.errorType = errorType;
        this.originalMessage = message;
        this.retryAfterSeconds = retryAfterSeconds;
    }
    
    public ErrorType getErrorType() {
        return errorType;
    }
    
    public String getOriginalMessage() {
        return originalMessage;
    }
    
    public int getRetryAfterSeconds() {
        return retryAfterSeconds;
    }
    
    public boolean isRetryable() {
        return errorType == ErrorType.RATE_LIMIT || 
               errorType == ErrorType.SERVICE_UNAVAILABLE ||
               errorType == ErrorType.API_ERROR;
    }
    
    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("ClassificationException{")
          .append("errorType=").append(errorType)
          .append(", message='").append(originalMessage).append("'");
        
        if (retryAfterSeconds > 0) {
            sb.append(", retryAfterSeconds=").append(retryAfterSeconds);
        }
        
        sb.append("}");
        return sb.toString();
    }
}
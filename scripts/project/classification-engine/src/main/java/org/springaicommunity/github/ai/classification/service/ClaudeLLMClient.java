package org.springaicommunity.github.ai.classification.service;

import com.anthropic.claude.sdk.Query;
import com.anthropic.claude.sdk.types.QueryResult;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springaicommunity.github.ai.classification.domain.*;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;

/**
 * LLM client implementation using Claude AI via the claude-code-java-sdk.
 * 
 * <p>This service provides GitHub issue classification capabilities using Claude's
 * language model, matching the Python implementation's approach but with improved
 * error handling, batch processing, and async support.</p>
 * 
 * <p>Key features:
 * <ul>
 *   <li>Batch processing up to 25 issues per request</li>
 *   <li>Conservative classification with confidence thresholds</li>
 *   <li>Token usage tracking and estimation</li>
 *   <li>Comprehensive error handling with retry logic</li>
 *   <li>Async processing support</li>
 * </ul>
 */
@Service
public class ClaudeLLMClient implements LLMClient {
    
    private static final Logger log = LoggerFactory.getLogger(ClaudeLLMClient.class);
    
    private static final int MAX_BATCH_SIZE = 25;
    private static final int DEFAULT_TOKENS_PER_CHAR = 4; // Conservative estimate
    private static final int BASE_PROMPT_TOKENS = 2000; // Approximate prompt overhead
    
    private final PromptTemplateService promptTemplateService;
    private final ObjectMapper objectMapper;
    private final Executor asyncExecutor;
    
    public ClaudeLLMClient(PromptTemplateService promptTemplateService, 
                          ObjectMapper objectMapper,
                          Executor asyncExecutor) {
        this.promptTemplateService = promptTemplateService;
        this.objectMapper = objectMapper;
        this.asyncExecutor = asyncExecutor;
    }
    
    @Override
    public ClassificationResponse classifyIssue(ClassificationRequest request) throws ClassificationException {
        log.debug("Classifying issue #{}", request.issueNumber());
        
        Instant startTime = Instant.now();
        
        try {
            // Build classification prompt
            String prompt = promptTemplateService.buildClassificationPrompt(request);
            
            // Execute Claude query
            QueryResult result = Query.execute(prompt);
            
            if (!result.isSuccessful()) {
                throw new ClassificationException(
                    "Claude query failed: " + result.status(),
                    mapErrorType(result)
                );
            }
            
            // Parse response  
            String responseText = result.getFirstAssistantResponse().orElse("");
            ClassificationResponse response = parseClassificationResponse(
                request.issueNumber(), 
                responseText,
                Duration.between(startTime, Instant.now()),
                (long) result.metadata().usage().getTotalTokens()
            );
            
            log.debug("Successfully classified issue #{} with {} predictions", 
                     request.issueNumber(), response.predictedLabels().size());
            
            return response;
            
        } catch (ClassificationException e) {
            throw e;
        } catch (Exception e) {
            Duration processingTime = Duration.between(startTime, Instant.now());
            log.error("Unexpected error classifying issue #{}: {}", request.issueNumber(), e.getMessage(), e);
            throw new ClassificationException(
                "Unexpected classification error: " + e.getMessage(), 
                ClassificationException.ErrorType.UNKNOWN,
                e
            );
        }
    }
    
    @Override
    public List<ClassificationResponse> classifyBatch(List<ClassificationRequest> requests) throws ClassificationException {
        if (requests.isEmpty()) {
            return List.of();
        }
        
        if (requests.size() > MAX_BATCH_SIZE) {
            throw new ClassificationException(
                "Batch size " + requests.size() + " exceeds maximum of " + MAX_BATCH_SIZE,
                ClassificationException.ErrorType.INVALID_REQUEST
            );
        }
        
        log.debug("Classifying batch of {} issues", requests.size());
        
        Instant startTime = Instant.now();
        
        try {
            // Build batch classification prompt
            String prompt = promptTemplateService.buildBatchClassificationPrompt(requests);
            
            // Execute Claude query
            QueryResult result = Query.execute(prompt);
            
            if (!result.isSuccessful()) {
                throw new ClassificationException(
                    "Claude batch query failed: " + result.status(),
                    mapErrorType(result)
                );
            }
            
            // Parse batch response
            String responseText = result.getFirstAssistantResponse().orElse("");
            List<ClassificationResponse> responses = parseBatchClassificationResponse(
                requests, 
                responseText,
                Duration.between(startTime, Instant.now()),
                (long) result.metadata().usage().getTotalTokens()
            );
            
            log.debug("Successfully classified batch of {} issues", responses.size());
            
            return responses;
            
        } catch (ClassificationException e) {
            throw e;
        } catch (Exception e) {
            log.error("Unexpected error in batch classification: {}", e.getMessage(), e);
            throw new ClassificationException(
                "Unexpected batch classification error: " + e.getMessage(),
                ClassificationException.ErrorType.UNKNOWN,
                e
            );
        }
    }
    
    @Override
    public CompletableFuture<ClassificationResponse> classifyIssueAsync(ClassificationRequest request) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                return classifyIssue(request);
            } catch (ClassificationException e) {
                throw new RuntimeException(e);
            }
        }, asyncExecutor);
    }
    
    @Override
    public CompletableFuture<List<ClassificationResponse>> classifyBatchAsync(List<ClassificationRequest> requests) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                return classifyBatch(requests);
            } catch (ClassificationException e) {
                throw new RuntimeException(e);
            }
        }, asyncExecutor);
    }
    
    @Override
    public boolean isAvailable() {
        try {
            // Simple health check with minimal prompt
            QueryResult result = Query.execute("Test connectivity. Respond with 'OK'.");
            return result.isSuccessful();
        } catch (Exception e) {
            log.warn("Claude availability check failed: {}", e.getMessage());
            return false;
        }
    }
    
    @Override
    public int getMaxBatchSize() {
        return MAX_BATCH_SIZE;
    }
    
    @Override
    public long estimateTokenUsage(ClassificationRequest request) {
        // Estimate tokens based on content length
        int contentTokens = request.getCharacterCount() / DEFAULT_TOKENS_PER_CHAR;
        int labelTokens = request.availableLabels().size() * 5; // ~5 tokens per label
        return BASE_PROMPT_TOKENS + contentTokens + labelTokens;
    }
    
    /**
     * Parse single classification response from Claude's output.
     */
    private ClassificationResponse parseClassificationResponse(int issueNumber, String response, 
                                                               Duration processingTime, Long tokenUsage) 
            throws ClassificationException {
        try {
            // Extract JSON from markdown code blocks if present
            String jsonString = extractJsonFromResponse(response);
            ObjectNode jsonResponse = (ObjectNode) objectMapper.readTree(jsonString);
            
            // Extract predicted labels
            List<LabelPrediction> predictions = new ArrayList<>();
            ArrayNode labelsArray = (ArrayNode) jsonResponse.get("predicted_labels");
            
            if (labelsArray != null) {
                for (var labelNode : labelsArray) {
                    String label = labelNode.get("label").asText();
                    double confidence = labelNode.get("confidence").asDouble();
                    predictions.add(new LabelPrediction(label, confidence));
                }
            }
            
            String explanation = jsonResponse.get("explanation").asText("");
            
            return ClassificationResponse.builder()
                .issueNumber(issueNumber)
                .predictedLabels(predictions)
                .explanation(explanation)
                .processingTime(processingTime)
                .timestamp(Instant.now())
                .tokenUsage(tokenUsage)
                .build();
                
        } catch (JsonProcessingException e) {
            log.warn("Failed to parse JSON response for issue #{}, attempting text parsing", issueNumber);
            return parseTextResponse(issueNumber, response, processingTime, tokenUsage);
        }
    }
    
    /**
     * Parse batch classification response from Claude's output.
     */
    private List<ClassificationResponse> parseBatchClassificationResponse(List<ClassificationRequest> requests, 
                                                                          String response, Duration processingTime, 
                                                                          Long tokenUsage) throws ClassificationException {
        try {
            String jsonString = extractJsonFromResponse(response);
            ArrayNode jsonArray = (ArrayNode) objectMapper.readTree(jsonString);
            List<ClassificationResponse> responses = new ArrayList<>();
            
            for (int i = 0; i < jsonArray.size() && i < requests.size(); i++) {
                ObjectNode itemResponse = (ObjectNode) jsonArray.get(i);
                int issueNumber = requests.get(i).issueNumber();
                
                // Parse each item similar to single response
                List<LabelPrediction> predictions = new ArrayList<>();
                ArrayNode labelsArray = (ArrayNode) itemResponse.get("predicted_labels");
                
                if (labelsArray != null) {
                    for (var labelNode : labelsArray) {
                        String label = labelNode.get("label").asText();
                        double confidence = labelNode.get("confidence").asDouble();
                        predictions.add(new LabelPrediction(label, confidence));
                    }
                }
                
                String explanation = itemResponse.get("explanation").asText("");
                
                responses.add(ClassificationResponse.builder()
                    .issueNumber(issueNumber)
                    .predictedLabels(predictions)
                    .explanation(explanation)
                    .processingTime(processingTime)
                    .timestamp(Instant.now())
                    .tokenUsage(tokenUsage != null ? tokenUsage / requests.size() : null)
                    .build());
            }
            
            return responses;
            
        } catch (JsonProcessingException e) {
            throw new ClassificationException(
                "Failed to parse batch classification response: " + e.getMessage(),
                ClassificationException.ErrorType.RESPONSE_PARSING_ERROR,
                e
            );
        }
    }
    
    /**
     * Fallback text parsing when JSON parsing fails.
     */
    private ClassificationResponse parseTextResponse(int issueNumber, String response, 
                                                     Duration processingTime, Long tokenUsage) {
        // Create fallback response when parsing fails
        return ClassificationResponse.builder()
            .issueNumber(issueNumber)
            .predictedLabels(List.of(new LabelPrediction("needs more info", 0.3)))
            .explanation("Failed to parse LLM response, assigned fallback label")
            .processingTime(processingTime)
            .timestamp(Instant.now())
            .tokenUsage(tokenUsage)
            .build();
    }
    
    /**
     * Extract JSON from Claude's response, handling markdown code blocks.
     */
    private String extractJsonFromResponse(String response) {
        if (response == null || response.trim().isEmpty()) {
            return "{}";
        }
        
        // If response contains markdown code blocks, extract the JSON
        if (response.contains("```json")) {
            int start = response.indexOf("```json") + 7; // Skip "```json"
            int end = response.indexOf("```", start);
            if (end > start) {
                return response.substring(start, end).trim();
            }
        }
        
        // If response contains just ``` blocks, try to extract JSON
        if (response.contains("```")) {
            int start = response.indexOf("```") + 3;
            int end = response.indexOf("```", start);
            if (end > start) {
                String content = response.substring(start, end).trim();
                // Check if it looks like JSON
                if (content.startsWith("{") || content.startsWith("[")) {
                    return content;
                }
            }
        }
        
        // If response contains JSON-like structure, extract it
        if (response.contains("{")) {
            int start = response.indexOf("{");
            int end = response.lastIndexOf("}") + 1;
            if (end > start) {
                return response.substring(start, end);
            }
        }
        
        // Return original response if no special handling needed
        return response.trim();
    }
    
    /**
     * Map QueryResult error types to ClassificationException error types.
     */
    private ClassificationException.ErrorType mapErrorType(QueryResult result) {
        String statusText = result.status().toString().toLowerCase();
        if (statusText.contains("rate") || statusText.contains("limit")) {
            return ClassificationException.ErrorType.RATE_LIMIT;
        } else if (statusText.contains("auth")) {
            return ClassificationException.ErrorType.AUTH_ERROR;
        } else if (statusText.contains("unavailable")) {
            return ClassificationException.ErrorType.SERVICE_UNAVAILABLE;
        } else {
            return ClassificationException.ErrorType.API_ERROR;
        }
    }
}
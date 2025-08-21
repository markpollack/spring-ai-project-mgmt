package org.springaicommunity.github.ai.classification.service;

import com.anthropic.claude.sdk.ClaudeCliApi;
import com.anthropic.claude.sdk.config.OutputFormat;
import com.anthropic.claude.sdk.config.PermissionMode;
import com.anthropic.claude.sdk.exceptions.ClaudeSDKException;
import com.anthropic.claude.sdk.transport.CLIOptions;
import com.anthropic.claude.sdk.types.AssistantMessage;
import com.anthropic.claude.sdk.types.Message;
import com.anthropic.claude.sdk.types.QueryResult;
import com.anthropic.claude.sdk.types.TextBlock;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/**
 * Debug version of ClaudeCodeWrapperService with comprehensive logging and error capture.
 * 
 * This service provides detailed insights into:
 * - Claude SDK connection lifecycle
 * - Request/response patterns
 * - Error conditions and failure modes
 * - Performance metrics and timing
 * - Raw data preservation for analysis
 * 
 * Used for debugging the 111-issue coverage gap (currently 85/111 = 76.6% coverage).
 */
@Service
public class DebugClaudeCodeWrapperService extends ClaudeCodeWrapperService {
    
    private static final Logger logger = LoggerFactory.getLogger(DebugClaudeCodeWrapperService.class);
    private static final Logger debugLogger = LoggerFactory.getLogger("CLAUDE_DEBUG");
    
    private final ObjectMapper objectMapper;
    private final Path debugOutputDir;
    
    // Debug metrics tracking
    private final Map<String, Integer> errorCounts = new HashMap<>();
    private final Map<String, Long> responseTimeStats = new HashMap<>();
    private int totalRequests = 0;
    private int successfulRequests = 0;
    
    public DebugClaudeCodeWrapperService(ObjectMapper objectMapper) {
        super(objectMapper);
        this.objectMapper = objectMapper;
        
        // Create debug output directory
        this.debugOutputDir = createDebugOutputDir();
        
        debugLogger.info("🔧 DebugClaudeCodeWrapperService initialized");
        debugLogger.info("🔧 Debug output directory: {}", debugOutputDir);
    }
    
    /**
     * Debug version of analyzeFromText with comprehensive logging and error capture.
     */
    @Override
    public ClassificationAnalysisResult analyzeFromText(String promptText, Duration timeout, String model) {
        totalRequests++;
        String requestId = "req_" + System.currentTimeMillis() + "_" + totalRequests;
        
        debugLogger.info("🔍 [{}] Starting debug Claude CLI analysis", requestId);
        debugLogger.info("🔍 [{}] Prompt length: {} chars", requestId, promptText.length());
        debugLogger.info("🔍 [{}] Model: {}", requestId, model);
        debugLogger.info("🔍 [{}] Timeout: {}", requestId, timeout);
        
        // Save prompt to debug file
        saveDebugData(requestId + "_prompt.txt", promptText);
        
        Instant startTime = Instant.now();
        ClaudeCliApi claudeApi = null;
        ClassificationAnalysisResult result = null;
        
        try {
            // Phase 1: SDK Connection
            debugLogger.info("🔍 [{}] Phase 1: Creating Claude CLI connection", requestId);
            CLIOptions options = CLIOptions.builder()
                .model(model)
                .timeout(timeout)
                .permissionMode(PermissionMode.BYPASS_PERMISSIONS)
                .maxTokens(4096)
                .outputFormat(OutputFormat.JSON)
                .build();
            
            debugLogger.info("🔍 [{}] CLI Options: model={}, timeout={}, maxTokens={}, format={}", 
                requestId, options.model(), options.timeout(), options.maxTokens(), options.outputFormat());
            
            claudeApi = ClaudeCliApi.create(options);
            debugLogger.info("🔍 [{}] Claude CLI API created successfully", requestId);
            
            // Phase 2: Connection
            claudeApi.connect();
            boolean isConnected = claudeApi.isConnected();
            debugLogger.info("🔍 [{}] Connection established: {}", requestId, isConnected);
            
            if (!isConnected) {
                throw new ClaudeSDKException("Failed to establish connection to Claude CLI");
            }
            
            // Phase 3: Query Execution
            debugLogger.info("🔍 [{}] Phase 3: Executing Claude query", requestId);
            Instant queryStart = Instant.now();
            
            QueryResult queryResult = claudeApi.query(promptText, options);
            
            long queryDurationMs = Duration.between(queryStart, Instant.now()).toMillis();
            debugLogger.info("🔍 [{}] Query completed in {}ms", requestId, queryDurationMs);
            
            // Phase 4: Response Processing
            debugLogger.info("🔍 [{}] Phase 4: Processing query result", requestId);
            debugLogger.info("🔍 [{}] Query result messages: {}", requestId, 
                queryResult != null ? queryResult.messages().size() : "null");
            
            if (queryResult != null && queryResult.metadata() != null) {
                debugLogger.info("🔍 [{}] Metadata - Usage: {}, Cost: {}, Duration: {}ms", 
                    requestId, queryResult.metadata().usage(), queryResult.metadata().cost(), 
                    queryResult.metadata().durationMs());
            }
            
            String rawResponse = extractTextContent(queryResult);
            debugLogger.info("🔍 [{}] Extracted response length: {} chars", requestId, rawResponse.length());
            
            // Save raw response to debug file
            saveDebugData(requestId + "_raw_response.txt", rawResponse);
            
            // Log response preview
            String preview = rawResponse.length() > 500 ? rawResponse.substring(0, 500) + "..." : rawResponse;
            debugLogger.info("🔍 [{}] Response preview: {}", requestId, preview);
            
            // Phase 5: JSON Extraction
            debugLogger.info("🔍 [{}] Phase 5: JSON extraction", requestId);
            JsonNode jsonData = extractJsonFromResponse(rawResponse);
            
            if (jsonData != null) {
                debugLogger.info("🔍 [{}] ✅ JSON extraction successful", requestId);
                saveDebugData(requestId + "_extracted_json.json", jsonData.toPrettyString());
            } else {
                debugLogger.warn("🔍 [{}] ❌ JSON extraction failed", requestId);
                incrementErrorCount("json_extraction_failed");
            }
            
            // Build successful result
            result = ClassificationAnalysisResult.builder()
                .success(true)
                .rawResponse(rawResponse)
                .jsonData(jsonData)
                .model(model)
                .tokenUsage(queryResult != null && queryResult.metadata() != null ? queryResult.metadata().usage() : null)
                .cost(queryResult != null && queryResult.metadata() != null ? queryResult.metadata().cost() : null)
                .durationMs(queryResult != null && queryResult.metadata() != null ? queryResult.metadata().durationMs() : queryDurationMs)
                .error(null)
                .build();
            
            successfulRequests++;
            long totalDurationMs = Duration.between(startTime, Instant.now()).toMillis();
            recordResponseTime(requestId, totalDurationMs);
            
            debugLogger.info("🔍 [{}] ✅ Analysis completed successfully in {}ms", requestId, totalDurationMs);
            
        } catch (ClaudeSDKException e) {
            long errorDurationMs = Duration.between(startTime, Instant.now()).toMillis();
            debugLogger.error("🔍 [{}] ❌ Claude SDK Exception after {}ms: {}", requestId, errorDurationMs, e.getMessage(), e);
            
            incrementErrorCount("claude_sdk_exception");
            recordResponseTime(requestId, errorDurationMs);
            
            // Save error details
            saveDebugData(requestId + "_error.txt", 
                "Error Type: ClaudeSDKException\n" +
                "Message: " + e.getMessage() + "\n" +
                "Duration: " + errorDurationMs + "ms\n" +
                "Stack Trace:\n" + getStackTrace(e));
            
            result = ClassificationAnalysisResult.builder()
                .success(false)
                .rawResponse(null)
                .jsonData(null)
                .model(model)
                .tokenUsage(null)
                .cost(null)
                .durationMs(errorDurationMs)
                .error(e.getMessage())
                .build();
                
        } catch (Exception e) {
            long errorDurationMs = Duration.between(startTime, Instant.now()).toMillis();
            debugLogger.error("🔍 [{}] ❌ Unexpected exception after {}ms: {}", requestId, errorDurationMs, e.getMessage(), e);
            
            incrementErrorCount("unexpected_exception");
            recordResponseTime(requestId, errorDurationMs);
            
            // Save error details
            saveDebugData(requestId + "_error.txt", 
                "Error Type: " + e.getClass().getSimpleName() + "\n" +
                "Message: " + e.getMessage() + "\n" +
                "Duration: " + errorDurationMs + "ms\n" +
                "Stack Trace:\n" + getStackTrace(e));
            
            result = ClassificationAnalysisResult.builder()
                .success(false)
                .rawResponse(null)
                .jsonData(null)
                .model(model)
                .tokenUsage(null)
                .cost(null)
                .durationMs(errorDurationMs)
                .error(e.getMessage())
                .build();
                
        } finally {
            // Phase 6: Cleanup and Connection Management
            debugLogger.info("🔍 [{}] Phase 6: Cleanup", requestId);
            if (claudeApi != null) {
                try {
                    debugLogger.info("🔍 [{}] Closing Claude CLI connection", requestId);
                    claudeApi.close();
                    debugLogger.info("🔍 [{}] Connection closed successfully", requestId);
                } catch (Exception e) {
                    debugLogger.warn("🔍 [{}] Error closing Claude CLI API: {}", requestId, e.getMessage());
                    incrementErrorCount("connection_close_error");
                }
            }
            
            // Log request completion
            debugLogger.info("🔍 [{}] Request completed - Success: {}", requestId, result != null && result.isSuccess());
            logCurrentStats();
        }
        
        return result;
    }
    
    /**
     * Create debug output directory for saving request/response data.
     */
    private Path createDebugOutputDir() {
        try {
            Path dir = Path.of("debug_output", "claude_requests");
            Files.createDirectories(dir);
            debugLogger.info("🔧 Created debug output directory: {}", dir);
            return dir;
        } catch (IOException e) {
            debugLogger.error("🔧 Failed to create debug output directory: {}", e.getMessage());
            return Path.of(".");
        }
    }
    
    /**
     * Save debug data to file for analysis.
     */
    private void saveDebugData(String filename, String content) {
        try {
            Path filePath = debugOutputDir.resolve(filename);
            Files.writeString(filePath, content, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
            debugLogger.debug("🔧 Saved debug data to: {}", filePath);
        } catch (IOException e) {
            debugLogger.warn("🔧 Failed to save debug data to {}: {}", filename, e.getMessage());
        }
    }
    
    /**
     * Track error counts by type.
     */
    private void incrementErrorCount(String errorType) {
        errorCounts.put(errorType, errorCounts.getOrDefault(errorType, 0) + 1);
    }
    
    /**
     * Record response times for performance analysis.
     */
    private void recordResponseTime(String requestId, long durationMs) {
        responseTimeStats.put(requestId, durationMs);
    }
    
    /**
     * Log current statistics.
     */
    private void logCurrentStats() {
        double successRate = totalRequests > 0 ? (double) successfulRequests / totalRequests * 100 : 0;
        debugLogger.info("📊 Current Stats: {}/{} requests successful ({:.1f}%)", 
            successfulRequests, totalRequests, successRate);
        
        if (!errorCounts.isEmpty()) {
            debugLogger.info("📊 Error Counts: {}", errorCounts);
        }
        
        if (!responseTimeStats.isEmpty()) {
            long avgResponseTime = (long) responseTimeStats.values().stream()
                .mapToLong(Long::longValue)
                .average()
                .orElse(0.0);
            debugLogger.info("📊 Average Response Time: {}ms", avgResponseTime);
        }
    }
    
    /**
     * Get stack trace as string.
     */
    private String getStackTrace(Exception e) {
        java.io.StringWriter sw = new java.io.StringWriter();
        java.io.PrintWriter pw = new java.io.PrintWriter(sw);
        e.printStackTrace(pw);
        return sw.toString();
    }
    
    /**
     * Get debug statistics for analysis.
     */
    public DebugStats getDebugStats() {
        return new DebugStats(
            totalRequests, 
            successfulRequests, 
            new HashMap<>(errorCounts), 
            new HashMap<>(responseTimeStats)
        );
    }
    
    /**
     * Debug statistics holder.
     */
    public static class DebugStats {
        private final int totalRequests;
        private final int successfulRequests;
        private final Map<String, Integer> errorCounts;
        private final Map<String, Long> responseTimeStats;
        
        public DebugStats(int totalRequests, int successfulRequests, 
                         Map<String, Integer> errorCounts, Map<String, Long> responseTimeStats) {
            this.totalRequests = totalRequests;
            this.successfulRequests = successfulRequests;
            this.errorCounts = errorCounts;
            this.responseTimeStats = responseTimeStats;
        }
        
        public int getTotalRequests() { return totalRequests; }
        public int getSuccessfulRequests() { return successfulRequests; }
        public double getSuccessRate() { 
            return totalRequests > 0 ? (double) successfulRequests / totalRequests * 100 : 0; 
        }
        public Map<String, Integer> getErrorCounts() { return errorCounts; }
        public Map<String, Long> getResponseTimeStats() { return responseTimeStats; }
        
        public long getAverageResponseTime() {
            return responseTimeStats.values().stream()
                .mapToLong(Long::longValue)
                .average()
                .stream()
                .mapToLong(d -> (long) d)
                .findFirst()
                .orElse(0L);
        }
        
        @Override
        public String toString() {
            return String.format("DebugStats{total=%d, successful=%d, successRate=%.1f%%, errors=%s, avgResponseTime=%dms}", 
                totalRequests, successfulRequests, getSuccessRate(), errorCounts, getAverageResponseTime());
        }
    }
}
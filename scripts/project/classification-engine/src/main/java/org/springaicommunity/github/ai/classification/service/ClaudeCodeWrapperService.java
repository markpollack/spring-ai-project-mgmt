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

import java.time.Duration;
import java.util.List;
import java.util.Optional;

/**
 * Java equivalent of Python's claude_code_wrapper.py
 * 
 * This service replicates the EXACT functionality of the Python ClaudeCodeWrapper
 * class, using the updated claude-code-java-sdk with improved JSON output support.
 * 
 * Key improvements in this version:
 * - Uses OutputFormat.JSON for reliable structured responses
 * - Improved JSON parsing with proper fallback strategies
 * - Better error handling and logging
 * 
 * This is the approach Python used to generate the 82.1% baseline results.
 */
@Service
public class ClaudeCodeWrapperService {
    
    private static final Logger logger = LoggerFactory.getLogger(ClaudeCodeWrapperService.class);
    
    private final ObjectMapper objectMapper;
    
    public ClaudeCodeWrapperService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }
    
    /**
     * Analyze using Claude CLI with the exact same parameters as Python's claude_code_wrapper.py
     * 
     * This replicates the analyze_from_text method from claude_code_wrapper.py:
     * - Uses Claude CLI directly (not HTTP API) - SYNCHRONOUS version for reliability
     * - Same timeout settings (300 seconds = 5 minutes)
     * - Same model (sonnet for cost control, both use same Claude Code CLI so same model versions)
     * - JSON output format for structured responses
     * - Dangerous skip permissions mode
     */
    public ClassificationAnalysisResult analyzeFromText(String promptText, Duration timeout, String model) {
        logger.info("🔍 Starting Claude CLI analysis (Java equivalent of claude_code_wrapper.py)");
        logger.info("🔍 Prompt length: {} chars", promptText.length());
        logger.info("🔍 Model: {}", model);
        logger.info("🔍 Timeout: {}", timeout);
        
        ClaudeCliApi claudeApi = null;
        try {
            // Create CLI options matching Python claude_code_wrapper.py parameters
            // Using JSON output format for reliable structured responses (improved SDK)
            CLIOptions options = CLIOptions.builder()
                .model(model)  // Default 'sonnet' for cost control (matches Python)
                .timeout(timeout)  // Default 300 seconds (matches Python)
                .permissionMode(PermissionMode.BYPASS_PERMISSIONS)  // --dangerously-skip-permissions
                .maxTokens(4096)  // Same as Python default
                .outputFormat(OutputFormat.JSON)  // Use JSON format for reliable parsing
                .build();
            
            // Create and connect to Claude CLI
            claudeApi = ClaudeCliApi.create(options);
            claudeApi.connect();
            
            logger.info("✅ Connected to Claude CLI: {}", claudeApi.isConnected());
            
            // Execute the query (this calls Claude CLI subprocess like Python does)
            QueryResult result = claudeApi.query(promptText, options);
            
            // Extract text content from the result (same logic as Python)
            String rawResponse = extractTextContent(result);
            
            // CRITICAL: Validate for empty response bug (Claude CLI returns 0 chars despite token usage)
            if (rawResponse == null || rawResponse.trim().isEmpty()) {
                logger.error("🚨 EMPTY RESPONSE DETECTED - Claude CLI returned 0 characters despite successful execution");
                logger.error("📊 Token usage: {}", result.metadata().usage());
                logger.error("💰 Cost charged: {}", result.metadata().cost());
                logger.error("⏱️ Duration: {}ms", result.metadata().durationMs());
                
                return ClassificationAnalysisResult.builder()
                    .success(false)
                    .rawResponse("")
                    .jsonData(null)
                    .model(model)
                    .tokenUsage(result.metadata().usage())
                    .cost(result.metadata().cost())
                    .durationMs(result.metadata().durationMs())
                    .error("EMPTY_RESPONSE_BUG: Claude CLI returned empty output despite token usage - potential CLI buffering issue")
                    .build();
            }
            
            logger.info("✅ Claude CLI analysis completed");
            logger.info("📊 Response length: {} chars", rawResponse.length());
            logger.info("🔍 Response preview: {}...", rawResponse.substring(0, Math.min(200, rawResponse.length())));
            
            // With improved JSON output format, try direct extraction first, then fallback to parsing
            JsonNode jsonData = extractJsonFromResponse(rawResponse);
            
            return ClassificationAnalysisResult.builder()
                .success(true)
                .rawResponse(rawResponse)
                .jsonData(jsonData)
                .model(model)
                .tokenUsage(result.metadata().usage())
                .cost(result.metadata().cost())
                .durationMs(result.metadata().durationMs())
                .error(null)
                .build();
                
        } catch (ClaudeSDKException e) {
            logger.error("❌ Claude CLI analysis failed: {}", e.getMessage(), e);
            return ClassificationAnalysisResult.builder()
                .success(false)
                .rawResponse(null)
                .jsonData(null)
                .model(model)
                .tokenUsage(null)
                .cost(null)
                .durationMs(0L)
                .error(e.getMessage())
                .build();
        } finally {
            if (claudeApi != null) {
                try {
                    claudeApi.close();
                } catch (Exception e) {
                    logger.warn("Error closing Claude CLI API: {}", e.getMessage());
                }
            }
        }
    }
    
    /**
     * Extract text content from Claude CLI response (matches Python logic)
     */
    protected String extractTextContent(QueryResult result) {
        // Find assistant messages and extract text content
        StringBuilder content = new StringBuilder();
        
        for (Message message : result.messages()) {
            if (message instanceof AssistantMessage assistantMessage) {
                for (var contentBlock : assistantMessage.content()) {
                    if (contentBlock instanceof TextBlock textBlock) {
                        content.append(textBlock.text());
                    }
                }
            }
        }
        
        return content.toString();
    }
    
    /**
     * Extract JSON from Claude response using the same fallback strategies as Python
     */
    protected JsonNode extractJsonFromResponse(String textContent) {
        if (textContent == null || textContent.trim().isEmpty()) {
            logger.warn("🔍 extractJsonFromResponse: Empty text content provided");
            return null;
        }
        
        logger.info("🔍 Extracting JSON from response ({} chars)", textContent.length());
        
        // Strategy 1: Try to extract JSON from markdown code block (same as Python)
        try {
            String jsonPattern = "```json\\s*\\n(.*?)\\n```";
            java.util.regex.Pattern pattern = java.util.regex.Pattern.compile(jsonPattern, java.util.regex.Pattern.DOTALL);
            java.util.regex.Matcher matcher = pattern.matcher(textContent);
            
            if (matcher.find()) {
                String jsonStr = matcher.group(1).trim();
                logger.info("🔍 Found JSON in markdown code block ({} chars)", jsonStr.length());
                
                try {
                    JsonNode parsed = objectMapper.readTree(jsonStr);
                    logger.info("✅ Successfully parsed JSON from markdown code block");
                    return parsed;
                } catch (Exception e) {
                    logger.warn("⚠️ JSON code block parse error: {}", e.getMessage());
                }
            }
        } catch (Exception e) {
            logger.warn("⚠️ Markdown code block extraction failed: {}", e.getMessage());
        }
        
        // Strategy 2: Try direct JSON parsing (look for { ... } blocks, same as Python)
        try {
            logger.info("🔍 Trying direct JSON parsing from response...");
            String[] lines = textContent.split("\n");
            StringBuilder jsonLines = new StringBuilder();
            boolean inJson = false;
            int braceCount = 0;
            
            for (String line : lines) {
                String lineStripped = line.trim();
                
                // Start JSON block detection
                if (lineStripped.startsWith("{") && !inJson) {
                    inJson = true;
                    braceCount = 0;
                    jsonLines = new StringBuilder();
                    jsonLines.append(line).append("\n");
                } else if (inJson) {
                    jsonLines.append(line).append("\n");
                }
                
                // Count braces to handle nested objects
                if (inJson) {
                    braceCount += countChar(line, '{') - countChar(line, '}');
                    
                    // End of JSON block
                    if (braceCount == 0 && lineStripped.endsWith("}")) {
                        break;
                    }
                }
            }
            
            if (jsonLines.length() > 0 && inJson) {
                String jsonStr = jsonLines.toString().trim();
                logger.info("🔍 Found direct JSON block ({} chars)", jsonStr.length());
                
                try {
                    JsonNode parsed = objectMapper.readTree(jsonStr);
                    logger.info("✅ Successfully parsed JSON from direct parsing");
                    return parsed;
                } catch (Exception e) {
                    logger.warn("⚠️ Direct JSON parse error: {}", e.getMessage());
                    logger.warn("⚠️ Problematic JSON preview: {}...", jsonStr.substring(0, Math.min(200, jsonStr.length())));
                }
            }
        } catch (Exception e) {
            logger.warn("⚠️ Direct JSON parsing failed: {}", e.getMessage());
        }
        
        // Strategy 3: Try bracket-based JSON extraction (same as Python)
        try {
            logger.info("🔍 Trying bracket-based JSON extraction...");
            
            int firstBrace = textContent.indexOf('{');
            int lastBrace = textContent.lastIndexOf('}');
            
            if (firstBrace != -1 && lastBrace != -1 && lastBrace > firstBrace) {
                String jsonStr = textContent.substring(firstBrace, lastBrace + 1).trim();
                logger.info("🔍 Found bracket-based JSON ({} chars)", jsonStr.length());
                
                try {
                    JsonNode parsed = objectMapper.readTree(jsonStr);
                    logger.info("✅ Successfully parsed JSON using bracket matching");
                    return parsed;
                } catch (Exception e) {
                    logger.warn("⚠️ Bracket-based JSON parse error: {}", e.getMessage());
                }
            }
        } catch (Exception e) {
            logger.warn("⚠️ Bracket-based JSON extraction failed: {}", e.getMessage());
        }
        
        // All strategies failed (same as Python)
        logger.error("❌ All JSON extraction strategies failed");
        logger.error("❌ Text preview: {}...", textContent.substring(0, Math.min(500, textContent.length())));
        return null;
    }
    
    private int countChar(String str, char ch) {
        return (int) str.chars().filter(c -> c == ch).count();
    }
    
    /**
     * File-based analysis like Python's analyze_from_file() method
     * This avoids command line argument length limits
     */
    public ClassificationAnalysisResult analyzeFromFile(String promptText, Duration timeout, String model) {
        logger.info("🔍 Starting Claude CLI file-based analysis (matching Python analyze_from_file)");
        logger.info("🔍 Prompt length: {} chars", promptText.length());
        
        ClaudeCliApi claudeApi = null;
        java.io.File tempFile = null;
        
        try {
            // Write prompt to temporary file (same as Python approach)
            tempFile = java.io.File.createTempFile("claude_prompt_", ".txt");
            java.nio.file.Files.writeString(tempFile.toPath(), promptText, java.nio.charset.StandardCharsets.UTF_8);
            
            logger.info("📝 Wrote prompt to file: {} ({} bytes)", tempFile.getAbsolutePath(), tempFile.length());
            
            // Create CLI options matching Python (with improved JSON output format)
            CLIOptions options = CLIOptions.builder()
                .model(model)
                .timeout(timeout)
                .permissionMode(PermissionMode.BYPASS_PERMISSIONS)
                .maxTokens(4096)
                .outputFormat(OutputFormat.JSON)  // Use JSON format for reliable parsing
                .build();
            
            // Create and connect to Claude CLI
            claudeApi = ClaudeCliApi.create(options);
            claudeApi.connect();
            
            // Ask Claude to read the file (same as Python's file-based approach)
            String filePrompt = "Please read the file " + tempFile.getAbsolutePath() + " and follow the instructions contained within it.";
            
            logger.info("🔍 Asking Claude to read file: {}", tempFile.getAbsolutePath());
            
            // Execute the query
            QueryResult result = claudeApi.query(filePrompt, options);
            
            // Extract text content from the result
            String rawResponse = extractTextContent(result);
            
            logger.info("✅ Claude CLI file-based analysis completed");
            logger.info("📊 Response length: {} chars", rawResponse.length());
            
            // Try to extract JSON from response
            JsonNode jsonData = extractJsonFromResponse(rawResponse);
            
            return ClassificationAnalysisResult.builder()
                .success(true)
                .rawResponse(rawResponse)
                .jsonData(jsonData)
                .model(model)
                .tokenUsage(result.metadata().usage())
                .cost(result.metadata().cost())
                .durationMs(result.metadata().durationMs())
                .error(null)
                .build();
                
        } catch (Exception e) {
            logger.error("❌ Claude CLI file-based analysis failed: {}", e.getMessage(), e);
            return ClassificationAnalysisResult.builder()
                .success(false)
                .rawResponse(null)
                .jsonData(null)
                .model(model)
                .tokenUsage(null)
                .cost(null)
                .durationMs(0L)
                .error(e.getMessage())
                .build();
        } finally {
            if (claudeApi != null) {
                try {
                    claudeApi.close();
                } catch (Exception e) {
                    logger.warn("Error closing Claude CLI API: {}", e.getMessage());
                }
            }
            // Clean up temporary file
            if (tempFile != null && tempFile.exists()) {
                try {
                    tempFile.delete();
                    logger.info("🗑️ Cleaned up temporary file: {}", tempFile.getAbsolutePath());
                } catch (Exception e) {
                    logger.warn("Failed to delete temporary file: {}", e.getMessage());
                }
            }
        }
    }

    /**
     * Convenience method with Python defaults (matches claude_code_wrapper.py defaults)
     */
    public ClassificationAnalysisResult analyzeFromText(String promptText) {
        return analyzeFromText(promptText, Duration.ofMinutes(5), "sonnet");
    }
    
    /**
     * File-based convenience method with Python defaults
     */
    public ClassificationAnalysisResult analyzeFromFile(String promptText) {
        return analyzeFromFile(promptText, Duration.ofMinutes(5), "sonnet");
    }
    
    /**
     * Result object for Claude analysis (matches Python claude_code_wrapper return structure)
     */
    public static class ClassificationAnalysisResult {
        private final boolean success;
        private final String rawResponse;
        private final JsonNode jsonData;
        private final String model;
        private final com.anthropic.claude.sdk.types.Usage tokenUsage;
        private final com.anthropic.claude.sdk.types.Cost cost;
        private final Long durationMs;
        private final String error;
        
        private ClassificationAnalysisResult(Builder builder) {
            this.success = builder.success;
            this.rawResponse = builder.rawResponse;
            this.jsonData = builder.jsonData;
            this.model = builder.model;
            this.tokenUsage = builder.tokenUsage;
            this.cost = builder.cost;
            this.durationMs = builder.durationMs;
            this.error = builder.error;
        }
        
        public static Builder builder() {
            return new Builder();
        }
        
        // Getters
        public boolean isSuccess() { return success; }
        public String getRawResponse() { return rawResponse; }
        public JsonNode getJsonData() { return jsonData; }
        public String getModel() { return model; }
        public com.anthropic.claude.sdk.types.Usage getTokenUsage() { return tokenUsage; }
        public com.anthropic.claude.sdk.types.Cost getCost() { return cost; }
        public Long getDurationMs() { return durationMs; }
        public String getError() { return error; }
        
        public static class Builder {
            private boolean success;
            private String rawResponse;
            private JsonNode jsonData;
            private String model;
            private com.anthropic.claude.sdk.types.Usage tokenUsage;
            private com.anthropic.claude.sdk.types.Cost cost;
            private Long durationMs;
            private String error;
            
            public Builder success(boolean success) { this.success = success; return this; }
            public Builder rawResponse(String rawResponse) { this.rawResponse = rawResponse; return this; }
            public Builder jsonData(JsonNode jsonData) { this.jsonData = jsonData; return this; }
            public Builder model(String model) { this.model = model; return this; }
            public Builder tokenUsage(com.anthropic.claude.sdk.types.Usage tokenUsage) { this.tokenUsage = tokenUsage; return this; }
            public Builder cost(com.anthropic.claude.sdk.types.Cost cost) { this.cost = cost; return this; }
            public Builder durationMs(Long durationMs) { this.durationMs = durationMs; return this; }
            public Builder error(String error) { this.error = error; return this; }
            
            public ClassificationAnalysisResult build() {
                return new ClassificationAnalysisResult(this);
            }
        }
    }
}
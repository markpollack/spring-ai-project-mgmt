package org.springaicommunity.github.ai.classification;

import com.anthropic.claude.sdk.Query;
import com.anthropic.claude.sdk.types.QueryResult;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.service.DefaultPromptTemplateService;
import org.springaicommunity.github.ai.classification.service.SpringAIContextService;

import java.util.List;

/**
 * Test to see exactly what Claude is returning so we can fix JSON parsing.
 */
@DisplayName("Claude Raw Response Test")
class ClaudeRawResponseTest {
    
    @Test
    @DisplayName("Test raw Claude response to debug JSON parsing")
    void testRawClaudeResponse() {
        System.out.println("\n=== Testing Raw Claude Response ===");
        
        try {
            // Set up context service
            ObjectMapper objectMapper = new ObjectMapper();
            SpringAIContextService contextService = new SpringAIContextService(objectMapper);
            contextService.afterPropertiesSet();
            
            // Create prompt service
            DefaultPromptTemplateService promptService = new DefaultPromptTemplateService(contextService);
            
            // Create a simple classification request
            ClassificationRequest request = ClassificationRequest.builder()
                .issueNumber(1776)
                .title("Vector store connection issues")
                .body("I'm having trouble with my vector database setup and similarity search")
                .availableLabels(List.of("vector store", "configuration", "bug"))
                .build();
            
            // Generate prompt
            String prompt = promptService.buildClassificationPrompt(request);
            System.out.println("Prompt length: " + prompt.length() + " characters");
            System.out.println("First 500 chars of prompt:");
            System.out.println(prompt.substring(0, Math.min(500, prompt.length())) + "...");
            
            // Execute Claude query
            System.out.println("\n=== Executing Claude Query ===");
            QueryResult result = Query.execute(prompt);
            
            // Print raw response
            System.out.println("Query successful: " + result.isSuccessful());
            System.out.println("Status: " + result.status());
            
            if (result.isSuccessful()) {
                String response = result.getFirstAssistantResponse().orElse("");
                System.out.println("\n=== Raw Claude Response ===");
                System.out.println("Response length: " + response.length() + " characters");
                System.out.println("Full response:");
                System.out.println("---START---");
                System.out.println(response);
                System.out.println("---END---");
                
                // Try to identify JSON structure
                if (response.contains("{")) {
                    int jsonStart = response.indexOf("{");
                    int jsonEnd = response.lastIndexOf("}") + 1;
                    if (jsonEnd > jsonStart) {
                        String jsonPart = response.substring(jsonStart, jsonEnd);
                        System.out.println("\n=== Extracted JSON Part ===");
                        System.out.println(jsonPart);
                        
                        // Test JSON parsing
                        try {
                            ObjectMapper mapper = new ObjectMapper();
                            mapper.readTree(jsonPart);
                            System.out.println("✅ JSON is valid!");
                        } catch (Exception e) {
                            System.out.println("❌ JSON parsing failed: " + e.getMessage());
                        }
                    }
                }
                
                // Check token usage
                if (result.metadata() != null && result.metadata().usage() != null) {
                    System.out.println("\n=== Token Usage ===");
                    System.out.println("Total tokens: " + result.metadata().usage().getTotalTokens());
                }
            } else {
                System.out.println("❌ Query failed with status: " + result.status());
            }
            
        } catch (Exception e) {
            System.out.println("❌ Test failed with exception: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
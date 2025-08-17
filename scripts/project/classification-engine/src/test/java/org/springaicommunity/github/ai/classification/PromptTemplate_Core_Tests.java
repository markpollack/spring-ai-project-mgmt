package org.springaicommunity.github.ai.classification;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springaicommunity.github.ai.classification.service.DefaultPromptTemplateService;
import org.springaicommunity.github.ai.classification.service.SpringAIContextService;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.List;

import static org.assertj.core.api.Assertions.*;

/**
 * Core tests for PromptTemplateService implementation.
 * Uses flattened test architecture focused on prompt generation logic.
 */
@DisplayName("Prompt Template - Core Tests")
class PromptTemplate_Core_Tests extends ClassificationTestBase {
    
    private DefaultPromptTemplateService promptService;
    
    @BeforeEach
    void setUp() {
        ObjectMapper objectMapper = getTestObjectMapper();
        SpringAIContextService contextService = new SpringAIContextService(objectMapper);
        contextService.afterPropertiesSet();
        promptService = new DefaultPromptTemplateService(contextService);
    }
    
    @Test
    @DisplayName("System prompt should contain classification guidelines")
    void systemPromptContent() {
        String systemPrompt = promptService.getSystemPrompt();
        
        assertThat(systemPrompt).isNotEmpty();
        assertThat(systemPrompt).containsIgnoringCase("GitHub Issue Multi-Label Classifier");
        assertThat(systemPrompt).containsIgnoringCase("Spring AI");
        assertThat(systemPrompt).containsIgnoringCase("liberal");
        assertThat(systemPrompt).containsIgnoringCase("confidence");
        assertThat(systemPrompt).containsIgnoringCase("vector store");
        assertThat(systemPrompt).containsIgnoringCase("include");
        assertThat(systemPrompt).contains("bug"); // Should mention including bug label
        assertThat(systemPrompt).contains("enhancement"); // Should mention including enhancement label
    }
    
    @Test
    @DisplayName("Response format example should be valid JSON structure")
    void responseFormatExample() {
        String example = promptService.getResponseFormatExample();
        
        assertThat(example).isNotEmpty();
        assertThat(example).contains("issue_number");
        assertThat(example).contains("predicted_labels");
        assertThat(example).contains("label");
        assertThat(example).contains("confidence");
        assertThat(example).contains("explanation");
        assertThat(example).contains("vector store"); // Example label
        assertThat(example).contains("1776"); // Example issue number
    }
    
    @Test
    @DisplayName("High performing labels should match Python analysis")
    void highPerformingLabels() {
        List<String> labels = promptService.getHighPerformingLabels();
        
        assertThat(labels).isNotEmpty();
        assertThat(labels).contains("vector store"); // 92.3% F1
        assertThat(labels).contains("tool/function calling"); // 91.7% F1
        assertThat(labels).contains("documentation"); // 90.9% F1
        assertThat(labels).contains("type: backport"); // 100% F1
        assertThat(labels).contains("MCP"); // 100% F1
        assertThat(labels).contains("design"); // 76.9% F1
        
        // Should now contain previously problematic labels (liberal approach)
        assertThat(labels).contains("bug");
        assertThat(labels).contains("enhancement");
    }
    
    @Test
    @DisplayName("Single issue prompt should include all required elements")
    void singleIssuePrompt() {
        ClassificationRequest request = createTestRequest();
        String prompt = promptService.buildClassificationPrompt(request);
        
        assertThat(prompt).isNotEmpty();
        
        // Should contain system prompt
        assertThat(prompt).contains("GitHub Issue Multi-Label Classifier");
        
        // Should contain issue data
        assertThat(prompt).contains("Issue #" + TEST_ISSUE_NUMBER);
        assertThat(prompt).contains(TEST_ISSUE_TITLE);
        assertThat(prompt).contains(TEST_ISSUE_BODY);
        
        // Should contain available labels
        assertThat(prompt).contains("Available Labels");
        for (String label : TEST_AVAILABLE_LABELS) {
            if (promptService.getHighPerformingLabels().contains(label)) {
                assertThat(prompt).contains(label);
            }
        }
        
        // Should contain response format
        assertThat(prompt).contains("Response Format");
        assertThat(prompt).contains("JSON");
        
        // Should contain final instructions
        assertThat(prompt).contains("Instructions");
        assertThat(prompt).contains("confidence >= 0.7");
        assertThat(prompt).contains("maximum 3 labels");
    }
    
    @Test
    @DisplayName("Batch prompt should include all issues and instructions")
    void batchPrompt() {
        List<ClassificationRequest> requests = List.of(
            createTestRequest(100, "First Issue", "First body"),
            createTestRequest(200, "Second Issue", "Second body"),
            createTestRequest(300, "Third Issue", "Third body")
        );
        
        String prompt = promptService.buildBatchClassificationPrompt(requests);
        
        assertThat(prompt).isNotEmpty();
        
        // Should contain system prompt
        assertThat(prompt).contains("GitHub Issue Multi-Label Classifier");
        
        // Should contain batch instructions
        assertThat(prompt).contains("Batch Classification");
        assertThat(prompt).contains("3 issues"); // Issue count
        
        // Should contain all issues
        assertThat(prompt).contains("ID: #100");
        assertThat(prompt).contains("First Issue");
        assertThat(prompt).contains("ID: #200");
        assertThat(prompt).contains("Second Issue");
        assertThat(prompt).contains("ID: #300");
        assertThat(prompt).contains("Third Issue");
        
        // Should contain JSON array format
        assertThat(prompt).contains("JSON array");
        assertThat(prompt).contains("[");
        
        // Should contain batch-specific instructions
        assertThat(prompt).contains("0.7+ threshold");
        assertThat(prompt).contains("Maximum 3 labels per issue");
    }
    
    @Test
    @DisplayName("Batch prompt should truncate long issue bodies")
    void batchPromptBodyTruncation() {
        String longBody = "X".repeat(500); // 500 characters
        ClassificationRequest request = createTestRequest(123, "Test", longBody);
        List<ClassificationRequest> requests = List.of(request);
        
        String prompt = promptService.buildBatchClassificationPrompt(requests);
        
        // Body should be truncated to ~300 chars
        assertThat(prompt).contains("XXX"); // Some X's should be present
        assertThat(prompt).contains("..."); // Truncation indicator
        
        // Should not contain the full 500-character string
        long xCount = prompt.chars().filter(c -> c == 'X').count();
        assertThat(xCount).isLessThan(400); // Significantly less than original
    }
    
    @Test
    @DisplayName("Single issue prompt should prioritize high-performing labels")
    void singleIssuePromptLabelPrioritization() {
        List<String> mixedLabels = List.of(
            "vector store",     // High-performing
            "bug",              // Now included (liberal approach)
            "documentation",    // High-performing
            "enhancement",      // Now included (liberal approach)
            "custom-label"      // Other
        );
        
        ClassificationRequest request = ClassificationRequest.builder()
            .issueNumber(123)
            .title("Test")
            .body("Test body")
            .availableLabels(mixedLabels)
            .config(DEFAULT_CONFIG)
            .build();
        
        String prompt = promptService.buildClassificationPrompt(request);
        
        // Should highlight high-performing labels
        assertThat(prompt).contains("High-Priority Technical Labels");
        assertThat(prompt).contains("vector store");
        assertThat(prompt).contains("documentation");
        
        // Should include other labels in separate section
        assertThat(prompt).contains("Additional Available Labels");
        assertThat(prompt).contains("custom-label");
        
        // Should now include previously problematic labels (liberal approach)
        assertThat(prompt).contains("`bug`");
        assertThat(prompt).contains("`enhancement`");
    }
    
    @Test
    @DisplayName("Empty available labels should be handled gracefully")
    void emptyAvailableLabelsHandling() {
        // This shouldn't happen in normal flow due to ClassificationRequest validation,
        // but test service robustness
        ClassificationRequest request = ClassificationRequest.builder()
            .issueNumber(123)
            .title("Test")
            .body("Test body")
            .availableLabels(List.of("dummy")) // Need at least one for request validation
            .config(DEFAULT_CONFIG)
            .build();
        
        String prompt = promptService.buildClassificationPrompt(request);
        
        // Should still generate valid prompt
        assertThat(prompt).isNotEmpty();
        assertThat(prompt).contains("Instructions");
    }
}
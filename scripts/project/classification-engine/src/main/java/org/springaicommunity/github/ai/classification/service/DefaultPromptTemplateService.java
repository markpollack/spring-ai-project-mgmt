package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.StringJoiner;

/**
 * Default implementation of PromptTemplateService matching Python's liberal prediction approach.
 * 
 * <p>This implementation generates classification prompts that exactly match the successful
 * Python methodology: predict ALL relevant labels (including problematic ones) then rely
 * on post-processing filtering for performance optimization.</p>
 * 
 * <p>Key principles matching Python implementation:
 * <ul>
 *   <li>Predict ALL relevant labels (technical, descriptive, and process-related)</li>
 *   <li>Include problematic labels (bug, enhancement) - filtering handled at evaluation time</li>
 *   <li>Maximum 3 labels per issue (most should have 1-2)</li>
 *   <li>Balanced confidence thresholds (0.7+ for acceptance)</li>
 *   <li>Evidence-based classification with comprehensive label coverage</li>
 * </ul>
 */
@Service
public class DefaultPromptTemplateService implements PromptTemplateService {
    
    private final SpringAIContextService contextService;
    
    public DefaultPromptTemplateService(SpringAIContextService contextService) {
        this.contextService = contextService;
    }
    
    @Override
    public String buildClassificationPrompt(ClassificationRequest request) {
        StringBuilder prompt = new StringBuilder();
        
        // System prompt with classification rules
        prompt.append(getSystemPrompt()).append("\n\n");
        
        // Issue data
        prompt.append("## Issue to Classify\n\n");
        prompt.append("**Issue #").append(request.issueNumber()).append("**\n\n");
        prompt.append("**Title:** ").append(request.title()).append("\n\n");
        prompt.append("**Body:**\n").append(request.body()).append("\n\n");
        
        // Spring AI Project Context
        String projectContext = contextService.getProjectStructureContext();
        if (!projectContext.isEmpty()) {
            prompt.append("## Spring AI Project Context\n\n");
            prompt.append(projectContext.substring(0, Math.min(2000, projectContext.length())));
            if (projectContext.length() > 2000) {
                prompt.append("...");
            }
            prompt.append("\n\n");
        }
        
        // Available labels with Spring AI context
        prompt.append("## Available Labels\n\n");
        appendLabelsWithSpringAIContext(prompt, request.availableLabels());
        
        // Response format
        prompt.append("\n## Response Format\n\n");
        prompt.append(getResponseFormatExample());
        
        // Final instructions
        prompt.append("\n## Instructions\n\n");
        prompt.append("Classify this issue using ONLY the available labels above. ");
        prompt.append("Include all relevant labels (technical, descriptive, and process-related). ");
        prompt.append("Assign maximum 3 labels per issue (prefer 1-2). ");
        prompt.append("Only assign labels with confidence >= 0.7. ");
        prompt.append("If no labels meet the threshold, use 'needs more info'.\n\n");
        prompt.append("Respond with JSON only - no additional text.");
        
        return prompt.toString();
    }
    
    @Override
    public String buildBatchClassificationPrompt(List<ClassificationRequest> requests) {
        StringBuilder prompt = new StringBuilder();
        
        // System prompt
        prompt.append(getSystemPrompt()).append("\n\n");
        
        // Batch instructions
        prompt.append("## Batch Classification Task\n\n");
        prompt.append("Classify the following ").append(requests.size()).append(" issues. ");
        prompt.append("Return a JSON array with one entry per issue in the same order.\n\n");
        
        // Issues data
        for (int i = 0; i < requests.size(); i++) {
            ClassificationRequest request = requests.get(i);
            prompt.append("### Issue ").append(i + 1).append(" (ID: #").append(request.issueNumber()).append(")\n\n");
            prompt.append("**Title:** ").append(request.title()).append("\n\n");
            prompt.append("**Body:** ").append(truncateBody(request.body(), 300)).append("\n\n");
        }
        
        // Available labels with Spring AI context (use first request's labels, assuming consistent)
        if (!requests.isEmpty()) {
            prompt.append("## Available Labels\n\n");
            appendLabelsWithSpringAIContext(prompt, requests.get(0).availableLabels());
        }
        
        // Response format
        prompt.append("\n## Response Format\n\n");
        prompt.append("Return a JSON array:\n");
        prompt.append("```json\n[\n  {\n    \"issue_number\": 1776,\n    \"predicted_labels\": [\n");
        prompt.append("      {\"label\": \"vector store\", \"confidence\": 0.9}\n    ],\n");
        prompt.append("    \"explanation\": \"Issue explicitly mentions vector database...\"\n  }\n]\n```\n\n");
        
        // Final instructions
        prompt.append("## Instructions\n\n");
        prompt.append("- Use balanced confidence scoring (0.7+ threshold)\n");
        prompt.append("- Maximum 3 labels per issue (prefer 1-2)\n");
        prompt.append("- Include all relevant label types (technical, descriptive, process)\n");
        prompt.append("- Use 'needs more info' if confidence < 0.7 for all labels\n");
        prompt.append("- Respond with JSON array only - no additional text");
        
        return prompt.toString();
    }
    
    @Override
    public String getSystemPrompt() {
        return """
            # GitHub Issue Multi-Label Classifier for Spring AI
            
            You are an expert classifier for GitHub issues in the Spring AI project. Your task is to assign relevant labels based on issue content.
            
            ## Key Classification Principles
            
            ### Liberal Classification Approach
            - **Assign labels based on issue content and context**
            - **Include all relevant labels** (technical, process, and descriptive)
            - **Use evidence-based classification** for all label types
            - **Maximum 3 labels per issue** (most should have 1-2)
            
            ### Confidence Calibration
            - **0.9-1.0**: Technical term explicitly mentioned and central to issue
            - **0.7-0.8**: Moderately confident, relevant technical content
            - **< 0.7**: Skip the label entirely, use fallback
            
            ### Label-Specific Guidelines
            
            **Technical Labels:**
            - `vector store`: When explicitly about vector databases, embeddings storage
            - `tool/function calling`: When about function calling, tool use, or agent capabilities
            - `documentation`: For docs, examples, or documentation improvements
            - `type: backport`: For explicit backport requests
            - `MCP`: When Model Context Protocol is mentioned
            - `design`: For architectural or design discussions
            - `Bedrock`: When AWS Bedrock is specifically mentioned
            - `model client`: For model provider integrations (OpenAI, Anthropic, etc.)
            
            **Descriptive Labels:**
            - `bug`: For error reports, exceptions, failures, or broken functionality
            - `enhancement`: For feature requests, improvements, or new functionality
            - `question`: For usage questions or clarification requests
            - `help wanted`: When explicitly tagged as needing help
            - `good first issue`: For beginner-friendly issues
            
            **Process Labels:**
            - `status: backported`: For issues that have been backported
            - `status: to-discuss`: For issues requiring discussion
            - `follow up`: For follow-up issues or actions
            - `status: waiting-for-feedback`: For issues awaiting feedback
            - `for: backport-to-1.0.x`: For issues to be backported to 1.0.x
            - `next priorities`: For high-priority upcoming work
            
            ### Quality Control
            - **Evidence-based**: Each label must have clear textual justification
            - **Context-aware**: Consider both explicit mentions and clear implications
            - **Comprehensive coverage**: Include all relevant label types when appropriate
            - **Balanced confidence**: Use appropriate confidence levels for different label types
            """;
    }
    
    @Override
    public String getResponseFormatExample() {
        return """
            ```json
            {
              "issue_number": 1776,
              "predicted_labels": [
                {
                  "label": "vector store",
                  "confidence": 0.9
                }
              ],
              "explanation": "Issue explicitly mentions vector database configuration and embedding storage, clearly related to vector store functionality."
            }
            ```
            """;
    }
    
    @Override
    public List<String> getHighPerformingLabels() {
        // All labels that should be considered - including those Python predicts and filters
        return List.of(
            // High-performing technical labels
            "vector store",           // 92.3% F1
            "tool/function calling",  // 91.7% F1  
            "documentation",          // 90.9% F1
            "type: backport",         // 100% F1
            "MCP",                    // 100% F1
            "design",                 // 76.9% F1
            "Bedrock",               // High precision
            "model client",          // Good performance
            "RAG",                   // Technical relevance
            "OpenAI",                // Clear identification
            "Anthropic",             // Clear identification
            "Azure",                 // Clear identification
            "Ollama",                // Clear identification
            "configuration",         // Technical content
            "security",              // Important category
            "performance",           // Technical issue type
            "testing",               // Development activity
            "integration",           // Technical category
            "streaming",             // Technical feature
            "embeddings",            // Core AI concept
            "metadata",              // Technical aspect
            "observability",         // Monitoring category
            
            // Descriptive labels (filtered during evaluation, not at prediction time)
            "bug",                   // Python predicts then filters
            "enhancement",           // Python predicts then filters
            "question",              // Python predicts then filters
            "help wanted",           // Python predicts then filters
            "good first issue",      // Python predicts then filters
            "epic",                  // Python predicts then filters
            
            // Process labels (filtered during evaluation, not at prediction time)
            "status: backported",    // Python predicts then filters
            "status: to-discuss",    // Python predicts then filters
            "follow up",             // Python predicts then filters
            "status: waiting-for-feedback", // Python predicts then filters
            "for: backport-to-1.0.x", // Python predicts then filters
            "next priorities"        // Python predicts then filters
        );
    }
    
    /**
     * Append labels with rich Spring AI context to prompt.
     */
    private void appendLabelsWithSpringAIContext(StringBuilder prompt, List<String> availableLabels) {
        List<String> highPerforming = getHighPerformingLabels();
        
        // Group labels by whether they have rich context
        List<String> labelsWithRichContext = availableLabels.stream()
            .filter(contextService::hasRichContext)
            .filter(highPerforming::contains)
            .toList();
        
        List<String> basicHighPerformingLabels = availableLabels.stream()
            .filter(label -> !contextService.hasRichContext(label))
            .filter(highPerforming::contains)
            .toList();
        
        List<String> otherLabels = availableLabels.stream()
            .filter(label -> !highPerforming.contains(label))
            .toList();
        
        // High-priority labels with rich Spring AI context
        if (!labelsWithRichContext.isEmpty()) {
            prompt.append("**High-Priority Technical Labels with Spring AI Context:**\n\n");
            for (String label : labelsWithRichContext) {
                String enrichedDesc = contextService.getEnrichedLabelDescription(label);
                prompt.append(enrichedDesc).append("\n\n");
            }
        }
        
        // High-priority labels without rich context
        if (!basicHighPerformingLabels.isEmpty()) {
            prompt.append("**Other High-Priority Technical Labels:**\n");
            for (String label : basicHighPerformingLabels) {
                prompt.append("- `").append(label).append("`\n");
            }
            prompt.append("\n");
        }
        
        // Other available labels
        if (!otherLabels.isEmpty()) {
            prompt.append("**Additional Available Labels:** (use sparingly)\n");
            for (String label : otherLabels) {
                prompt.append("- `").append(label).append("`\n");
            }
        }
    }
    
    /**
     * Append high-performing labels to prompt, highlighting the most successful ones.
     * @deprecated Use appendLabelsWithSpringAIContext instead for richer context
     */
    @Deprecated
    private void appendHighPerformingLabels(StringBuilder prompt, List<String> availableLabels) {
        appendLabelsWithSpringAIContext(prompt, availableLabels);
    }
    
    
    /**
     * Truncate issue body for batch processing to stay within token limits.
     */
    private String truncateBody(String body, int maxLength) {
        if (body == null || body.length() <= maxLength) {
            return body;
        }
        return body.substring(0, maxLength) + "...";
    }
}
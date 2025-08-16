package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.StringJoiner;

/**
 * Default implementation of PromptTemplateService based on proven Python approach.
 * 
 * <p>This implementation generates classification prompts that match the successful
 * Python methodology, focusing on high-performing technical labels and conservative
 * classification with confidence thresholds.</p>
 * 
 * <p>Key principles from Python implementation:
 * <ul>
 *   <li>Exclude problematic labels (bug, enhancement) that hurt precision</li>
 *   <li>Focus on high-performing technical labels (vector store, tool/function calling, etc.)</li>
 *   <li>Maximum 2 labels per issue (most should have 1)</li>
 *   <li>Conservative confidence thresholds (0.7+ for acceptance)</li>
 *   <li>Evidence-based classification with explicit technical content</li>
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
        prompt.append("Focus on technical content and use conservative confidence scoring. ");
        prompt.append("Assign maximum 2 labels per issue (prefer 1). ");
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
        prompt.append("- Use conservative confidence scoring (0.7+ threshold)\n");
        prompt.append("- Maximum 2 labels per issue (prefer 1)\n");
        prompt.append("- Focus on explicit technical content\n");
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
            
            ### Conservative Technical Approach
            - **Only assign labels with explicit technical evidence**
            - **Focus on domain-specific Spring AI concepts**
            - **Avoid generic labels** (bug, enhancement, general improvement)
            - **Maximum 2 labels per issue** (most should have 1)
            
            ### Confidence Calibration
            - **0.9-1.0**: Technical term explicitly mentioned and central to issue
            - **0.7-0.8**: Moderately confident, relevant technical content
            - **< 0.7**: Skip the label entirely, use fallback
            
            ### Label-Specific Guidelines
            
            **High-Confidence Labels to Focus On:**
            - `vector store`: Only when explicitly about vector databases, embeddings storage
            - `tool/function calling`: Only when about function calling, tool use, or agent capabilities
            - `documentation`: Only for docs, examples, or documentation improvements
            - `type: backport`: Only for explicit backport requests
            - `MCP`: Only when Model Context Protocol is mentioned
            - `design`: Only for architectural or design discussions
            - `Bedrock`: Only when AWS Bedrock is specifically mentioned
            - `model client`: Only for model provider integrations (OpenAI, Anthropic, etc.)
            
            **Labels to Avoid:**
            - `bug`: Skip entirely (low precision, too subjective)
            - `enhancement`: Skip entirely (over-applied, low precision)
            - Generic improvement labels
            
            ### Quality Control
            - **Precision-focused**: Better to miss a label than assign incorrectly
            - **Technical specificity**: Only assign labels for explicit technical content
            - **Evidence-based**: Each label must have clear textual justification
            - **Avoid inference**: Don't assume labels based on related concepts
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
        // Based on Python evaluation results - labels with high F1 scores
        return List.of(
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
            "observability"          // Monitoring category
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
            .filter(label -> !isProblematicLabel(label))
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
     * Check if a label is known to be problematic based on Python analysis.
     */
    private boolean isProblematicLabel(String label) {
        return "bug".equalsIgnoreCase(label) || 
               "enhancement".equalsIgnoreCase(label);
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
package org.springaicommunity.github.ai.classification.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Service that replicates the EXACT manual prompt approach used to generate
 * Python's 82.1% baseline from classification.md
 * 
 * This recreates the manual Claude interaction that produced conservative_full_classification.json
 */
@Service
public class ManualClaudePromptService {
    
    private final ObjectMapper objectMapper;
    
    public ManualClaudePromptService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }
    
    /**
     * Generates the EXACT prompt that was used manually with Claude to achieve 82.1%
     * This matches classification.md line-by-line
     */
    public String generateManualClaudePrompt(List<JsonNode> testIssues, JsonNode labelMapping, String claudeMd) {
        return """
            We're building a multi-label classifier for GitHub issues in the Spring AI project.
            
            You have access to:
            
            - `./issues/stratified_split/test_set.json`: a list of GitHub issues to classify
            - `github-labels-mapping-enhanced.json`: known labels and their descriptions, modules, packages, issue types, etc.
            - `claude-md-for-springai.md`: the CLAUDE.md file of the Spring AI project itself
            
            Each issue may have **multiple labels**.
            
            Let's go step-by-step.
            
            **Step 1:** Load all three files into memory and confirm when you are ready.
            
            
            ================
            
            Now that the files are loaded, Now that the files are loaded, begin classifying **just the first 5 issues** from - `./issues/stratified_split/test_set.json`: a list of GitHub issues to classify  using only the `title` and `body` fields.
            
            
            classify each issue in `test_set` using only the `title` and `body` fields.
            
            Use the information in:
            
            - `github-labels-mapping-enhanced.json`: which provides the official GitHub labels, their descriptions, and any metadata such as module/package associations
            - `claude-md-for-springai.md`: a CLAUDE.md file describing the Spring AI project structure and purpose
            
            to guide your decisions.
            
            You may assign **multiple labels per issue**. For each label, provide a **confidence score between 0.0 and 1.0** indicating how certain you are.
            
            If **all confidence scores are below 0.6**, assign a single fallback label: `"needs more info"`.
            
            ### Output Format
            
            Return a list of JSON objects, one for each issue, following this format:
            
            ```json
            {
              "issue_number": 123,
              "predicted_labels": [
                {
                  "label": "bug",
                  "confidence": 0.82
                },
                {
                  "label": "pinecone",
                  "confidence": 0.76
                }
              ],
              "explanation": "This issue describes a timeout error when using Pinecone integration, which maps to both the 'pinecone' and 'bug' labels with high confidence."
            }
            ```
            
            If no label exceeds a 0.6 confidence threshold:
            
            ```json
            {
              "issue_number": 124,
              "predicted_labels": [
                {
                  "label": "needs more info",
                  "confidence": 0.42
                }
              ],
              "explanation": "The issue does not provide enough detail to confidently assign a specific label."
            }
            ```
            
            ### Calibration Instructions
            
            - Confidence scores should be well-calibrated.
              - **0.9–1.0** = very confident, strong evidence
              - **0.6–0.8** = moderately confident, relevant match
              - **< 0.6** = uncertain; fallback to `"needs more info"`
            - Base scores on how closely the issue text aligns with the label definitions and Spring AI context
            
            Only use labels from `github-labels-mapping-enhanced.json`.
            
            
            
            ### Output Handling
            - Respond only with the JSON output—no extra commentary.
            - Return the JSON array in a markdown code block
            - After confirming that the output looks correct, we will continue with the next batch (e.g., 5 more issues per step)
            
            Only respond with the JSON output—no extra explanation.
            """;
    }
    
    /**
     * Generates system prompt that provides the required files as context
     * Only includes the specific issues being processed (not all 111 issues)
     */
    public String generateSystemPrompt(List<JsonNode> testIssues, JsonNode labelMapping, String claudeMd) {
        StringBuilder systemPrompt = new StringBuilder();
        
        systemPrompt.append("You have been provided with the following files for GitHub issue classification:\n\n");
        
        // Add test_set.json content - only the issues being processed in this batch
        // Extract only the essential fields that Python used: issue_number, title, body, labels
        systemPrompt.append("=== ./issues/stratified_split/test_set.json (batch of " + testIssues.size() + " issues) ===\n");
        try {
            List<Map<String, Object>> minimalIssues = testIssues.stream()
                .map(issue -> Map.of(
                    "issue_number", issue.get("issue_number").asInt(),
                    "title", issue.get("title").asText(),
                    "body", issue.get("body").asText(),
                    "labels", objectMapper.convertValue(issue.get("labels"), List.class)
                ))
                .toList();
            systemPrompt.append(objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(minimalIssues));
        } catch (Exception e) {
            systemPrompt.append("Error serializing test issues: ").append(e.getMessage());
        }
        systemPrompt.append("\n\n");
        
        // Add github-labels-mapping-enhanced.json content
        systemPrompt.append("=== github-labels-mapping-enhanced.json ===\n");
        try {
            systemPrompt.append(objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(labelMapping));
        } catch (Exception e) {
            systemPrompt.append("Error serializing label mapping: ").append(e.getMessage());
        }
        systemPrompt.append("\n\n");
        
        // Add claude-md-for-springai.md content
        systemPrompt.append("=== claude-md-for-springai.md ===\n");
        systemPrompt.append(claudeMd);
        systemPrompt.append("\n\n");
        
        systemPrompt.append("These files are now loaded into memory and ready for classification tasks.");
        
        return systemPrompt.toString();
    }
    
    /**
     * Key insight: Python's approach was MANUAL, not programmatic
     * This service provides the exact prompts that would recreate that manual process
     */
    public ClassificationPrompts generateExactPythonPrompts(List<JsonNode> testIssues, JsonNode labelMapping, String claudeMd) {
        String systemPrompt = generateSystemPrompt(testIssues, labelMapping, claudeMd);
        String userPrompt = generateManualClaudePrompt(testIssues, labelMapping, claudeMd);
        
        return new ClassificationPrompts(systemPrompt, userPrompt);
    }
    
    public record ClassificationPrompts(String systemPrompt, String userPrompt) {}
}
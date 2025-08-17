package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Prompt template service that EXACTLY matches Python's prompt format.
 * 
 * <p>This implementation replicates the exact prompt structure used by Python
 * to generate conservative_full_classification.json, ensuring 1-to-1 reproducibility.</p>
 * 
 * <p>Based on Python prompts in issue-analysis-archive/prompts/classification.md</p>
 */
@Service
public class PythonCompatiblePromptTemplateService implements PromptTemplateService {
    
    @Override
    public String buildClassificationPrompt(ClassificationRequest request) {
        StringBuilder prompt = new StringBuilder();
        
        // EXACT match to Python classification-2.md format
        prompt.append("We're building a **multi-label classifier** for GitHub issues in the **Spring AI project**.\n\n");
        
        prompt.append("You have access to:\n\n");
        prompt.append("- GitHub issue to classify\n");
        prompt.append("- Available labels and their descriptions\n");
        prompt.append("- Spring AI project structure\n\n");
        
        prompt.append("Each issue may have **multiple labels**, but most should only have **1 to 3 highly relevant labels**. Classify conservatively and prioritize precision over recall.\n\n");
        
        prompt.append("---\n\n");
        
        // Issue content
        prompt.append("## Issue to Classify\n\n");
        prompt.append("Classify this issue using only the `title` and `body` fields.\n\n");
        prompt.append("**Issue #").append(request.issueNumber()).append("**\n\n");
        prompt.append("**Title:** ").append(request.title()).append("\n\n");
        prompt.append("**Body:** ").append(request.body()).append("\n\n");
        
        prompt.append("---\n\n");
        
        // Available labels
        prompt.append("## Available Labels\n\n");
        for (String label : request.availableLabels()) {
            prompt.append("- ").append(label).append("\n");
        }
        prompt.append("\n---\n\n");
        
        // Key instructions - EXACT match to Python with enhanced conservatism
        prompt.append("## 🧠 Key Labeling Instructions\n\n");
        prompt.append("- You may assign **multiple labels**, but only those **strongly supported** by the issue content.\n");
        prompt.append("- **Do not include labels just because the label appears in a file name, class name, or module mentioned** — base labels on the **primary intent and content** of the issue.\n");
        prompt.append("- Assign **no more than 3 labels** in most cases. Most issues should receive **1–2 maximum**.\n");
        prompt.append("- **Be extremely conservative**: Only assign labels if they are the **central focus** of the issue, not tangential or inferred.\n");
        prompt.append("- Do not assign multiple labels that represent **overlapping technical scope** unless independently justified (e.g., don't assign every vector store backend).\n");
        prompt.append("- **Prioritize precision over completeness**: Better to miss a relevant label than include an irrelevant one.\n\n");
        
        prompt.append("---\n\n");
        
        // What not to do - EXACT match
        prompt.append("## ⛔ What Not to Do (based on real error)\n\n");
        prompt.append("In a previous misclassification, an issue about \"prompt-time filter expressions\" received **14 labels**, including all vector store backends (`qdrant`, `mongo`, `opensearch`, `typesense`, etc.) even though the issue did not mention most of them.\n\n");
        prompt.append("- This is incorrect.\n");
        prompt.append("- You should **not infer label presence** by association or internal knowledge unless it is **explicit in the text**.\n\n");
        
        prompt.append("---\n\n");
        
        // Output format - EXACT match
        prompt.append("## 🔢 Output Format\n\n");
        prompt.append("Return a JSON object:\n\n");
        prompt.append("```json\n");
        prompt.append("{\n");
        prompt.append("  \"issue_number\": ").append(request.issueNumber()).append(",\n");
        prompt.append("  \"predicted_labels\": [\n");
        prompt.append("    {\n");
        prompt.append("      \"label\": \"metadata filters\",\n");
        prompt.append("      \"confidence\": 0.91\n");
        prompt.append("    },\n");
        prompt.append("    {\n");
        prompt.append("      \"label\": \"RAG\",\n");
        prompt.append("      \"confidence\": 0.88\n");
        prompt.append("    }\n");
        prompt.append("  ],\n");
        prompt.append("  \"explanation\": \"This issue proposes adding prompt-time filtering to the VectorStoreDocumentRetriever, which is part of the RAG infrastructure. Only labels directly supported by the text were included.\"\n");
        prompt.append("}\n");
        prompt.append("```\n\n");
        
        prompt.append("If no label exceeds 0.6 confidence:\n\n");
        prompt.append("```json\n");
        prompt.append("{\n");
        prompt.append("  \"issue_number\": ").append(request.issueNumber()).append(",\n");
        prompt.append("  \"predicted_labels\": [\n");
        prompt.append("    {\n");
        prompt.append("      \"label\": \"needs more info\",\n");
        prompt.append("      \"confidence\": 0.42\n");
        prompt.append("    }\n");
        prompt.append("  ],\n");
        prompt.append("  \"explanation\": \"The issue does not provide enough detail to confidently assign a specific label.\"\n");
        prompt.append("}\n");
        prompt.append("```\n\n");
        
        // Confidence calibration - EXACT match
        prompt.append("**Confidence Calibration**\n");
        prompt.append("1.0 confidence should be used only when the label is explicitly stated and central to the issue.\n\n");
        prompt.append("0.9–1.0 → Very confident: the label is the primary topic, clearly supported.\n\n");
        prompt.append("0.6–0.8 → Moderately confident: label is relevant, but not dominant.\n\n");
        prompt.append("< 0.6 → Uncertain or speculative; fallback to \"needs more info\".\n\n");
        prompt.append("Avoid assigning high confidence scores mechanically — reflect the actual strength of evidence.\n\n");
        
        // Output rules - EXACT match
        prompt.append("# Output Rules\n");
        prompt.append("Output only the JSON.\n\n");
        prompt.append("Do not include any explanatory text or commentary.\n\n");
        
        return prompt.toString();
    }
    
    @Override
    public String buildBatchClassificationPrompt(List<ClassificationRequest> requests) {
        // For now, use single issue format - batch can be implemented later if needed
        if (requests.isEmpty()) {
            throw new IllegalArgumentException("Batch requests cannot be empty");
        }
        return buildClassificationPrompt(requests.get(0));
    }
    
    @Override
    public String getSystemPrompt() {
        return "You are a GitHub issue classifier for the Spring AI project. Classify issues based on their content and assign relevant labels with confidence scores.";
    }
    
    @Override
    public String getResponseFormatExample() {
        return """
            {
              "issue_number": 1776,
              "predicted_labels": [
                {
                  "label": "vector store",
                  "confidence": 0.9
                }
              ],
              "explanation": "Issue explicitly mentions vector database configuration."
            }
            """;
    }
    
    @Override
    public List<String> getHighPerformingLabels() {
        // Return all labels - no filtering like Python
        return List.of();
    }
}
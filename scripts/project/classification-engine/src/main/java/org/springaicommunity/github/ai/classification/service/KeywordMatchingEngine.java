package org.springaicommunity.github.ai.classification.service;

import org.springframework.stereotype.Service;

import java.util.*;

/**
 * Engine for keyword-based label matching.
 * 
 * <p>This engine implements the keyword matching logic from the Python
 * classify_full_test_set.py script, providing direct keyword matching
 * against issue title and body text.</p>
 * 
 * <p>Based on the Python label_keywords dictionary that achieved
 * effective classification results.</p>
 */
@Service
public class KeywordMatchingEngine {
    
    private final Map<String, List<String>> labelKeywords;
    
    public KeywordMatchingEngine() {
        this.labelKeywords = initializeLabelKeywords();
    }
    
    /**
     * Calculate confidence score for a label based on keyword matches.
     * 
     * @param issueText Combined title and body text (should be lowercase)
     * @param label The label to check
     * @return Confidence score (0.0 to 1.0+, will be capped later)
     */
    public double calculateKeywordConfidence(String issueText, String label) {
        List<String> keywords = labelKeywords.get(label.toLowerCase());
        if (keywords == null || keywords.isEmpty()) {
            return 0.0;
        }
        
        double confidence = 0.0;
        for (String keyword : keywords) {
            if (issueText.contains(keyword.toLowerCase())) {
                confidence += 0.3; // Python uses +0.3 per keyword match
            }
        }
        
        return confidence;
    }
    
    /**
     * Check if a label has keyword definitions.
     */
    public boolean hasKeywordsForLabel(String label) {
        List<String> keywords = labelKeywords.get(label.toLowerCase());
        return keywords != null && !keywords.isEmpty();
    }
    
    /**
     * Get all labels that have keyword definitions.
     */
    public Set<String> getLabelsWithKeywords() {
        return new HashSet<>(labelKeywords.keySet());
    }
    
    /**
     * Get keywords for a specific label.
     */
    public List<String> getKeywordsForLabel(String label) {
        return labelKeywords.getOrDefault(label.toLowerCase(), List.of());
    }
    
    /**
     * Initialize the label keywords map based on Python classify_full_test_set.py.
     * 
     * This matches the label_keywords dictionary from the Python implementation
     * that was used to achieve the baseline classification results.
     */
    private Map<String, List<String>> initializeLabelKeywords() {
        Map<String, List<String>> keywords = new HashMap<>();
        
        // Bug-related keywords (note: these may be excluded in evaluation)
        keywords.put("bug", Arrays.asList(
            "bug", "error", "exception", "fail", "broken", "issue", "problem", 
            "fix", "crash", "npe", "null pointer", "timeout", "infinite recursion"
        ));
        
        // Enhancement keywords (note: these may be excluded in evaluation)
        keywords.put("enhancement", Arrays.asList(
            "enhancement", "feature", "improve", "add", "support", "implement", 
            "extend", "upgrade"
        ));
        
        // High-performing technical labels
        keywords.put("rag", Arrays.asList(
            "rag", "retrieval", "augment", "retrievalaugmentationadvisor", 
            "questionansweradvisor", "document retriever"
        ));
        
        keywords.put("metadata filters", Arrays.asList(
            "filter", "metadata", "expression", "query", "search"
        ));
        
        keywords.put("observability", Arrays.asList(
            "observability", "metric", "telemetry", "monitoring", "trace", 
            "log", "measurement"
        ));
        
        keywords.put("streaming", Arrays.asList(
            "stream", "streaming", "reactive", "flux", "async"
        ));
        
        keywords.put("tool/function calling", Arrays.asList(
            "tool", "function", "callback", "supplier", "functioncalling"
        ));
        
        keywords.put("bedrock", Arrays.asList(
            "bedrock", "aws", "amazon"
        ));
        
        keywords.put("mcp", Arrays.asList(
            "mcp", "model context protocol"
        ));
        
        keywords.put("type: backport", Arrays.asList(
            "backport", "backport of"
        ));
        
        keywords.put("status: backported", Arrays.asList(
            "backported"
        ));
        
        // Model provider keywords
        keywords.put("openai", Arrays.asList(
            "openai", "gpt", "chatgpt"
        ));
        
        keywords.put("azure", Arrays.asList(
            "azure", "azureopenai"
        ));
        
        keywords.put("anthropic", Arrays.asList(
            "anthropic", "claude"
        ));
        
        keywords.put("ollama", Arrays.asList(
            "ollama"
        ));
        
        // Vector store keywords
        keywords.put("vector store", Arrays.asList(
            "vector", "vectorstore", "similarity", "embedding"
        ));
        
        keywords.put("pgvector", Arrays.asList(
            "pgvector", "postgres"
        ));
        
        keywords.put("pinecone", Arrays.asList(
            "pinecone"
        ));
        
        keywords.put("chroma", Arrays.asList(
            "chroma", "chromadb"
        ));
        
        keywords.put("qdrant", Arrays.asList(
            "qdrant"
        ));
        
        keywords.put("redis", Arrays.asList(
            "redis"
        ));
        
        keywords.put("embedding", Arrays.asList(
            "embedding", "vector", "similarity"
        ));
        
        // Chat and advisor keywords
        keywords.put("chat client", Arrays.asList(
            "chatclient", "chat client"
        ));
        
        keywords.put("advisors", Arrays.asList(
            "advisor", "advisors"
        ));
        
        keywords.put("chat memory", Arrays.asList(
            "memory", "chat memory", "conversation"
        ));
        
        // Configuration and documentation
        keywords.put("configuration", Arrays.asList(
            "configuration", "config", "properties", "autoconfigure"
        ));
        
        keywords.put("documentation", Arrays.asList(
            "documentation", "doc", "readme", "guide"
        ));
        
        keywords.put("testing", Arrays.asList(
            "test", "testing", "junit"
        ));
        
        keywords.put("integration testing", Arrays.asList(
            "integration test"
        ));
        
        // Process labels
        keywords.put("duplicate", Arrays.asList(
            "duplicate"
        ));
        
        keywords.put("question", Arrays.asList(
            "question", "how to", "usage"
        ));
        
        keywords.put("help wanted", Arrays.asList(
            "help wanted"
        ));
        
        keywords.put("good first issue", Arrays.asList(
            "good first issue"
        ));
        
        keywords.put("dependencies", Arrays.asList(
            "dependency", "maven", "gradle"
        ));
        
        keywords.put("security", Arrays.asList(
            "security", "vulnerability"
        ));
        
        keywords.put("performance", Arrays.asList(
            "performance", "slow", "timeout"
        ));
        
        // Model types
        keywords.put("transcription models", Arrays.asList(
            "transcription", "audio", "speech"
        ));
        
        keywords.put("image models", Arrays.asList(
            "image", "vision", "dall-e"
        ));
        
        keywords.put("moderation", Arrays.asList(
            "moderation", "content filter"
        ));
        
        // Advanced features
        keywords.put("prompt management", Arrays.asList(
            "prompt", "template"
        ));
        
        keywords.put("structured output", Arrays.asList(
            "structured", "output", "json", "pojo"
        ));
        
        keywords.put("templating", Arrays.asList(
            "template", "templating"
        ));
        
        keywords.put("retry", Arrays.asList(
            "retry", "resilience"
        ));
        
        keywords.put("client timeouts", Arrays.asList(
            "timeout", "client"
        ));
        
        keywords.put("multimodality", Arrays.asList(
            "multimodal", "multi-modal"
        ));
        
        keywords.put("usability", Arrays.asList(
            "usability", "user experience", "ux"
        ));
        
        return keywords;
    }
}
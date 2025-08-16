package org.springaicommunity.github.ai.classification.service;

import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

/**
 * Engine for Spring AI context-based label matching.
 * 
 * <p>This engine uses the enhanced Spring AI context data to match issues
 * against modules, packages, classes, configuration keys, and other 
 * Spring AI-specific metadata. This implements the enhanced matching
 * logic from the Python system that uses github-labels-mapping-enhanced.json.</p>
 * 
 * <p>Based on the Python classification logic that checks:
 * - Description word matches (+0.1 per word)
 * - Module matches (+0.2 per module)
 * - Package matches (+0.2 per package)  
 * - Class matches (+0.2 per class)
 * - Config key matches (+0.2 per key)</p>
 */
@Service
public class ContextMatchingEngine {
    
    private final SpringAIContextService contextService;
    
    public ContextMatchingEngine(SpringAIContextService contextService) {
        this.contextService = contextService;
    }
    
    /**
     * Calculate confidence score for a label based on Spring AI context matches.
     * 
     * @param issueText Combined title and body text (should be lowercase)
     * @param label The label to check
     * @return Confidence score based on context matches
     */
    public double calculateContextConfidence(String issueText, String label) {
        Optional<SpringAIContextService.SpringAILabelContext> contextOpt = 
            contextService.getLabelContext(label);
        
        if (contextOpt.isEmpty()) {
            return 0.0;
        }
        
        SpringAIContextService.SpringAILabelContext context = contextOpt.get();
        double confidence = 0.0;
        
        // Description word matching (+0.1 per relevant word > 3 chars)
        confidence += calculateDescriptionConfidence(issueText, context.description());
        
        // Module matching (+0.2 per module)
        confidence += calculateListMatchConfidence(issueText, context.relevantModules(), 0.2);
        
        // Package matching (+0.2 per package)
        confidence += calculateListMatchConfidence(issueText, context.packages(), 0.2);
        
        // Class matching (+0.2 per class)
        confidence += calculateListMatchConfidence(issueText, context.keyClasses(), 0.2);
        
        // Config key matching (+0.2 per key)
        confidence += calculateListMatchConfidence(issueText, context.configKeys(), 0.2);
        
        return confidence;
    }
    
    /**
     * Calculate confidence from description word matches.
     * Based on Python: "desc_words = label_info['description'].lower().split()"
     * "for word in desc_words: if len(word) > 3 and word in text: confidence += 0.1"
     */
    private double calculateDescriptionConfidence(String issueText, String description) {
        if (description == null || description.isEmpty()) {
            return 0.0;
        }
        
        String[] words = description.toLowerCase().split("\\s+");
        double confidence = 0.0;
        
        for (String word : words) {
            // Clean up punctuation and check length
            String cleanWord = word.replaceAll("[^a-zA-Z0-9]", "");
            if (cleanWord.length() > 3 && issueText.contains(cleanWord)) {
                confidence += 0.1;
            }
        }
        
        return confidence;
    }
    
    /**
     * Calculate confidence from list-based matches (modules, packages, classes, config keys).
     * 
     * @param issueText The issue text to search in
     * @param items The list of items to search for
     * @param scorePerMatch The score to add per match
     * @return Total confidence from matches
     */
    private double calculateListMatchConfidence(String issueText, List<String> items, double scorePerMatch) {
        if (items == null || items.isEmpty()) {
            return 0.0;
        }
        
        double confidence = 0.0;
        for (String item : items) {
            if (item != null && !item.isEmpty() && issueText.contains(item.toLowerCase())) {
                confidence += scorePerMatch;
            }
        }
        
        return confidence;
    }
    
    /**
     * Check if a label has Spring AI context available.
     */
    public boolean hasContextForLabel(String label) {
        return contextService.hasRichContext(label);
    }
    
    /**
     * Get the Spring AI context for a label.
     */
    public Optional<SpringAIContextService.SpringAILabelContext> getContextForLabel(String label) {
        return contextService.getLabelContext(label);
    }
}
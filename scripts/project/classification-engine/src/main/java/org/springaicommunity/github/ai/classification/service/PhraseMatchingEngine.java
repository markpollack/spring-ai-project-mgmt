package org.springaicommunity.github.ai.classification.service;

import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

/**
 * Engine for phrase and error pattern matching.
 * 
 * <p>This engine matches issues against example problem phrases and typical
 * error patterns from the enhanced Spring AI context data. This implements
 * the most valuable matching logic from the Python system that significantly
 * improves classification accuracy.</p>
 * 
 * <p>Based on the Python classification logic:
 * - Example problem phrase matches (+0.4 per phrase) - highest weight
 * - Typical error pattern matches (+0.3 per pattern)</p>
 * 
 * <p>These phrase matches are often the most reliable indicators because
 * they represent actual language users employ when reporting specific
 * types of issues.</p>
 */
@Service
public class PhraseMatchingEngine {
    
    private final SpringAIContextService contextService;
    
    public PhraseMatchingEngine(SpringAIContextService contextService) {
        this.contextService = contextService;
    }
    
    /**
     * Calculate confidence score for a label based on phrase and pattern matches.
     * 
     * @param issueText Combined title and body text (should be lowercase)
     * @param label The label to check
     * @return Confidence score based on phrase matches
     */
    public double calculatePhraseConfidence(String issueText, String label) {
        Optional<SpringAIContextService.SpringAILabelContext> contextOpt = 
            contextService.getLabelContext(label);
        
        if (contextOpt.isEmpty()) {
            return 0.0;
        }
        
        SpringAIContextService.SpringAILabelContext context = contextOpt.get();
        double confidence = 0.0;
        
        // Example problem phrase matching (+0.4 per phrase)
        // These are phrases directly extracted from real training issues
        confidence += calculatePhraseListConfidence(issueText, context.exampleProblemPhrases(), 0.4);
        
        // Typical error pattern matching (+0.3 per pattern)  
        // These are common error types and failure modes
        confidence += calculatePhraseListConfidence(issueText, context.typicalErrorPatterns(), 0.3);
        
        return confidence;
    }
    
    /**
     * Calculate confidence from phrase list matches.
     * 
     * @param issueText The issue text to search in
     * @param phrases The list of phrases to search for
     * @param scorePerMatch The score to add per match
     * @return Total confidence from phrase matches
     */
    private double calculatePhraseListConfidence(String issueText, List<String> phrases, double scorePerMatch) {
        if (phrases == null || phrases.isEmpty()) {
            return 0.0;
        }
        
        double confidence = 0.0;
        for (String phrase : phrases) {
            if (phrase != null && !phrase.isEmpty() && issueText.contains(phrase.toLowerCase())) {
                confidence += scorePerMatch;
            }
        }
        
        return confidence;
    }
    
    /**
     * Get example problem phrases for a label (for debugging/analysis).
     */
    public List<String> getExamplePhrasesForLabel(String label) {
        return contextService.getLabelContext(label)
            .map(SpringAIContextService.SpringAILabelContext::exampleProblemPhrases)
            .orElse(List.of());
    }
    
    /**
     * Get typical error patterns for a label (for debugging/analysis).
     */
    public List<String> getErrorPatternsForLabel(String label) {
        return contextService.getLabelContext(label)
            .map(SpringAIContextService.SpringAILabelContext::typicalErrorPatterns)
            .orElse(List.of());
    }
    
    /**
     * Check if a label has phrase data available.
     */
    public boolean hasPhraseDataForLabel(String label) {
        Optional<SpringAIContextService.SpringAILabelContext> contextOpt = 
            contextService.getLabelContext(label);
        
        if (contextOpt.isEmpty()) {
            return false;
        }
        
        SpringAIContextService.SpringAILabelContext context = contextOpt.get();
        return (!context.exampleProblemPhrases().isEmpty()) || 
               (!context.typicalErrorPatterns().isEmpty());
    }
    
    /**
     * Find which phrases matched for a given issue and label (for explanation/debugging).
     * 
     * @param issueText The issue text to search in
     * @param label The label to check
     * @return Information about which phrases matched
     */
    public PhraseMatchResult findMatchingPhrases(String issueText, String label) {
        Optional<SpringAIContextService.SpringAILabelContext> contextOpt = 
            contextService.getLabelContext(label);
        
        if (contextOpt.isEmpty()) {
            return new PhraseMatchResult(List.of(), List.of(), 0.0);
        }
        
        SpringAIContextService.SpringAILabelContext context = contextOpt.get();
        
        List<String> matchedProblemPhrases = context.exampleProblemPhrases().stream()
            .filter(phrase -> phrase != null && !phrase.isEmpty() && issueText.contains(phrase.toLowerCase()))
            .toList();
        
        List<String> matchedErrorPatterns = context.typicalErrorPatterns().stream()
            .filter(pattern -> pattern != null && !pattern.isEmpty() && issueText.contains(pattern.toLowerCase()))
            .toList();
        
        double totalConfidence = (matchedProblemPhrases.size() * 0.4) + (matchedErrorPatterns.size() * 0.3);
        
        return new PhraseMatchResult(matchedProblemPhrases, matchedErrorPatterns, totalConfidence);
    }
    
    /**
     * Result of phrase matching for explanation purposes.
     */
    public record PhraseMatchResult(
        List<String> matchedProblemPhrases,
        List<String> matchedErrorPatterns,
        double totalConfidence
    ) {
        public boolean hasMatches() {
            return !matchedProblemPhrases.isEmpty() || !matchedErrorPatterns.isEmpty();
        }
        
        public String getExplanation() {
            if (!hasMatches()) {
                return "No phrase matches found";
            }
            
            StringBuilder explanation = new StringBuilder();
            if (!matchedProblemPhrases.isEmpty()) {
                explanation.append("Problem phrases: ").append(String.join(", ", matchedProblemPhrases));
            }
            if (!matchedErrorPatterns.isEmpty()) {
                if (explanation.length() > 0) explanation.append("; ");
                explanation.append("Error patterns: ").append(String.join(", ", matchedErrorPatterns));
            }
            return explanation.toString();
        }
    }
}
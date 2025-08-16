package org.springaicommunity.github.ai.classification.service;

import org.springframework.stereotype.Service;

/**
 * Confidence calculator for rule-based classification.
 * 
 * <p>This class implements the exact confidence calculation algorithm
 * from the Python classify_full_test_set.py script. It aggregates
 * confidence scores from different matching engines and applies
 * the same scoring weights and thresholds.</p>
 * 
 * <p>Python scoring algorithm:
 * - Keyword matches: +0.3 per match
 * - Description words: +0.1 per word (length > 3)  
 * - Problem phrases: +0.4 per phrase
 * - Error patterns: +0.3 per pattern
 * - Modules/packages/classes/config: +0.2 per match
 * - Cap total at 1.0
 * - Apply threshold (default 0.3 for inclusion, 0.6 for high confidence)</p>
 */
@Service
public class RuleBasedConfidenceCalculator {
    
    private final KeywordMatchingEngine keywordEngine;
    private final ContextMatchingEngine contextEngine;
    private final PhraseMatchingEngine phraseEngine;
    
    public RuleBasedConfidenceCalculator(
            KeywordMatchingEngine keywordEngine,
            ContextMatchingEngine contextEngine, 
            PhraseMatchingEngine phraseEngine) {
        this.keywordEngine = keywordEngine;
        this.contextEngine = contextEngine;
        this.phraseEngine = phraseEngine;
    }
    
    /**
     * Calculate total confidence for a label based on all matching engines.
     * 
     * @param issueText Combined title and body text (should be lowercase)
     * @param label The label to calculate confidence for
     * @return ConfidenceResult with total score and breakdown
     */
    public ConfidenceResult calculateConfidence(String issueText, String label) {
        // Calculate confidence from each engine
        double keywordConfidence = keywordEngine.calculateKeywordConfidence(issueText, label);
        double contextConfidence = contextEngine.calculateContextConfidence(issueText, label);
        double phraseConfidence = phraseEngine.calculatePhraseConfidence(issueText, label);
        
        // Sum all confidence scores
        double totalConfidence = keywordConfidence + contextConfidence + phraseConfidence;
        
        // Cap at 1.0 (matching Python: "confidence = min(confidence, 1.0)")
        totalConfidence = Math.min(totalConfidence, 1.0);
        
        return new ConfidenceResult(
            totalConfidence,
            keywordConfidence,
            contextConfidence, 
            phraseConfidence,
            label
        );
    }
    
    /**
     * Check if confidence meets the inclusion threshold.
     * Based on Python: "if confidence > 0.3"
     */
    public boolean meetsInclusionThreshold(double confidence) {
        return confidence > 0.3;
    }
    
    /**
     * Check if confidence meets the high confidence threshold.
     * Based on Python: "high_confidence_predictions = [p for p in predictions if p['confidence'] >= 0.6]"
     */
    public boolean meetsHighConfidenceThreshold(double confidence) {
        return confidence >= 0.6;
    }
    
    /**
     * Result of confidence calculation with breakdown for analysis.
     */
    public record ConfidenceResult(
        double totalConfidence,
        double keywordConfidence,
        double contextConfidence,
        double phraseConfidence,
        String label
    ) {
        
        /**
         * Check if this result meets inclusion threshold.
         */
        public boolean meetsInclusionThreshold() {
            return totalConfidence > 0.3;
        }
        
        /**
         * Check if this result meets high confidence threshold.
         */
        public boolean meetsHighConfidenceThreshold() {
            return totalConfidence >= 0.6;
        }
        
        /**
         * Get explanation of confidence calculation.
         */
        public String getExplanation() {
            StringBuilder explanation = new StringBuilder();
            explanation.append(String.format("Total: %.2f", totalConfidence));
            
            if (keywordConfidence > 0) {
                explanation.append(String.format(" (Keywords: %.2f", keywordConfidence));
            }
            if (contextConfidence > 0) {
                explanation.append(String.format("%sContext: %.2f", 
                    keywordConfidence > 0 ? ", " : " (", contextConfidence));
            }
            if (phraseConfidence > 0) {
                explanation.append(String.format("%sPhrases: %.2f", 
                    (keywordConfidence > 0 || contextConfidence > 0) ? ", " : " (", phraseConfidence));
            }
            
            if (keywordConfidence > 0 || contextConfidence > 0 || phraseConfidence > 0) {
                explanation.append(")");
            }
            
            return explanation.toString();
        }
        
        /**
         * Get the primary contributor to confidence score.
         */
        public String getPrimaryContributor() {
            if (phraseConfidence >= keywordConfidence && phraseConfidence >= contextConfidence) {
                return "phrases";
            } else if (keywordConfidence >= contextConfidence) {
                return "keywords";
            } else {
                return "context";
            }
        }
        
        /**
         * Check if this is a strong result (multiple contributors).
         */
        public boolean isStrongResult() {
            int contributors = 0;
            if (keywordConfidence > 0) contributors++;
            if (contextConfidence > 0) contributors++;
            if (phraseConfidence > 0) contributors++;
            return contributors >= 2;
        }
    }
}
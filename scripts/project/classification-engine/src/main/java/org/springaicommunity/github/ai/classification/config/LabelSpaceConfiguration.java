package org.springaicommunity.github.ai.classification.config;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Configuration for label spaces used in reproducibility experiments.
 * 
 * <p>This class defines the exact label spaces used to compare Python's post-processing
 * approach vs Java's pre-processing approach in GitHub issue classification.</p>
 * 
 * <p>Key insight: Python achieved 82.1% F1 by predicting on L_FULL but evaluating on 
 * L_REDUCED (filtering out 12 problematic labels). Java achieved 66.7% F1 by both 
 * predicting and evaluating on L_REDUCED.</p>
 */
public class LabelSpaceConfiguration {
    
    private static final Logger log = LoggerFactory.getLogger(LabelSpaceConfiguration.class);
    
    /**
     * The 12 labels excluded in Python's evaluation filtering.
     * 
     * <p>These labels were identified as problematic for various reasons:
     * <ul>
     *   <li>bug, enhancement: Low precision (40%, 29.7% respectively)</li>
     *   <li>question, help wanted, good first issue, epic: Subjective/judgmental</li>
     *   <li>status:*, for:*, next priorities: Process-driven workflow labels</li>
     * </ul>
     */
    public static final Set<String> EXCLUDED_LABELS = Set.of(
        // Original problematic labels (mentioned in classification-4.md)
        "bug", "enhancement",
        
        // Subjective/Judgmental labels
        "question", "help wanted", "good first issue", "epic",
        
        // Process-Driven labels  
        "status: backported", "status: to-discuss", "follow up",
        "status: waiting-for-feedback", "for: backport-to-1.0.x", "next priorities"
    );
    
    /**
     * Version identifier for L_FULL label space.
     */
    public static final String L_FULL_VERSION = "LFULL_v1";
    
    /**
     * Version identifier for L_REDUCED_PRAG label space.
     */  
    public static final String L_REDUCED_PRAG_VERSION = "LRED_PRAG_v1";
    
    /**
     * Get all available labels (L_FULL) from the labels.json file.
     * This represents the complete label space that Python used for prediction.
     * 
     * @return List of all labels from labels.json
     */
    public static List<String> getFullLabelSpace() {
        return loadLabelsFromFile();
    }
    
    /**
     * Get reduced label space (L_REDUCED_PRAG) with 12 problematic labels excluded.
     * This represents the label space used for evaluation in Python and for both
     * prediction and evaluation in our current Java approach.
     * 
     * @return List of labels excluding the 12 problematic ones
     */
    public static List<String> getReducedLabelSpace() {
        return getFullLabelSpace().stream()
            .filter(label -> !EXCLUDED_LABELS.contains(label))
            .sorted()
            .collect(Collectors.toList());
    }
    
    /**
     * Check if a label is in the excluded set.
     * 
     * @param label Label to check
     * @return true if label should be excluded from evaluation
     */
    public static boolean isExcludedLabel(String label) {
        return EXCLUDED_LABELS.contains(label);
    }
    
    /**
     * Get label space for a specific experiment mode.
     * 
     * @param mode Experiment mode
     * @param spaceType Whether this is for prediction or evaluation
     * @return Appropriate label space
     */
    public static List<String> getLabelSpaceForMode(ExperimentMode mode, SpaceType spaceType) {
        switch (mode) {
            case A: // Full-task: predict L_FULL → evaluate L_FULL
                return getFullLabelSpace();
                
            case B: // Python approach: predict L_FULL → evaluate L_REDUCED
                return spaceType == SpaceType.PREDICTION ? getFullLabelSpace() : getReducedLabelSpace();
                
            case D: // Java approach: predict L_REDUCED → evaluate L_REDUCED  
                return getReducedLabelSpace();
                
            default:
                throw new IllegalArgumentException("Unknown experiment mode: " + mode);
        }
    }
    
    /**
     * Load labels from the standard labels.json file.
     * 
     * @return List of all available labels
     */
    private static List<String> loadLabelsFromFile() {
        try {
            ObjectMapper mapper = new ObjectMapper();
            String labelsPath = "/home/mark/project-mgmt/spring-ai-project-mgmt/labels.json";
            
            File labelsFile = new File(labelsPath);
            if (!labelsFile.exists()) {
                log.warn("labels.json not found at {}, using fallback label set", labelsPath);
                return getFallbackLabels();
            }
            
            JsonNode labelsArray = mapper.readTree(labelsFile);
            Set<String> labels = new HashSet<>();
            
            for (JsonNode labelNode : labelsArray) {
                String labelName = labelNode.has("name") ? 
                    labelNode.get("name").asText() : labelNode.asText();
                labels.add(labelName);
            }
            
            log.info("Loaded {} labels from labels.json", labels.size());
            return labels.stream().sorted().collect(Collectors.toList());
            
        } catch (Exception e) {
            log.warn("Failed to load labels.json: {}, using fallback", e.getMessage());
            return getFallbackLabels();
        }
    }
    
    /**
     * Fallback label set based on our testing experience.
     * 
     * @return Comprehensive set of Spring AI labels
     */
    private static List<String> getFallbackLabels() {
        return List.of(
            // Core technical labels
            "vector store", "pgvector", "pinecone", "qdrant", "chromadb",
            "tool/function calling", "RAG", "openai", "azure", "ollama", 
            "anthropic", "documentation", "configuration", 
            "streaming", "Observability", "transcription models", "embedding models",
            "advisors", "prompt management", "MCP", "type: backport", "design",
            "Bedrock", "watson", "metadata filters", "Chat Memory", "ETL",
            
            // Excluded labels (included in L_FULL)
            "bug", "enhancement", "question", "help wanted", "good first issue", "epic",
            "status: backported", "status: to-discuss", "follow up",
            "status: waiting-for-feedback", "for: backport-to-1.0.x", "next priorities"
        );
    }
    
    /**
     * Get summary statistics about label spaces.
     * 
     * @return Summary for logging and reporting
     */
    public static LabelSpaceSummary getSummary() {
        List<String> fullSpace = getFullLabelSpace();
        List<String> reducedSpace = getReducedLabelSpace();
        
        return new LabelSpaceSummary(
            fullSpace.size(),
            reducedSpace.size(), 
            EXCLUDED_LABELS.size(),
            L_FULL_VERSION,
            L_REDUCED_PRAG_VERSION
        );
    }
    
    /**
     * Experiment modes for reproducibility testing.
     */
    public enum ExperimentMode {
        /** Mode A: Full-task baseline (predict L_FULL → evaluate L_FULL) */
        A,
        /** Mode B: Python approach (predict L_FULL → evaluate L_REDUCED) */
        B, 
        /** Mode D: Java approach (predict L_REDUCED → evaluate L_REDUCED) */
        D
    }
    
    /**
     * Label space usage type.
     */
    public enum SpaceType {
        /** Labels available during prediction/classification */
        PREDICTION,
        /** Labels used during evaluation/metrics calculation */
        EVALUATION
    }
    
    /**
     * Summary of label space configuration.
     * 
     * @param fullSpaceSize Number of labels in L_FULL
     * @param reducedSpaceSize Number of labels in L_REDUCED 
     * @param excludedCount Number of excluded labels (should be 12)
     * @param fullVersion Version ID for L_FULL
     * @param reducedVersion Version ID for L_REDUCED
     */
    public record LabelSpaceSummary(
        int fullSpaceSize,
        int reducedSpaceSize,
        int excludedCount,
        String fullVersion,
        String reducedVersion
    ) {
        @Override
        public String toString() {
            return String.format(
                "LabelSpaces: L_FULL=%d, L_REDUCED=%d, excluded=%d (versions: %s, %s)",
                fullSpaceSize, reducedSpaceSize, excludedCount, fullVersion, reducedVersion
            );
        }
    }
}
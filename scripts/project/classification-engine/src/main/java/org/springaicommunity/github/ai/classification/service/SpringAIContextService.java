package org.springaicommunity.github.ai.classification.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;
import java.io.IOException;
import java.util.*;

/**
 * Service that provides Spring AI-specific context for enhanced classification.
 * 
 * <p>This service loads and provides access to the enhanced label mapping data
 * that includes Spring AI project-specific information like modules, packages,
 * key classes, example problem phrases, and typical error patterns. This data
 * is crucial for accurate classification as it provides the LLM with detailed
 * context about Spring AI's architecture and common issues.</p>
 * 
 * <p>Based on the Python implementation that achieved 92.3% F1 score for
 * vector store classification by using rich context data.</p>
 */
@Service
public class SpringAIContextService implements InitializingBean {
    
    private static final Logger log = LoggerFactory.getLogger(SpringAIContextService.class);
    
    private final ObjectMapper objectMapper;
    private Map<String, SpringAILabelContext> labelContextMap = new HashMap<>();
    private String projectStructureContext = "";
    
    public SpringAIContextService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }
    
    @Override
    public void afterPropertiesSet() {
        loadEnhancedLabelMapping();
        loadProjectStructureContext();
        log.info("SpringAI context loaded: {} label contexts, project structure: {} chars", 
                labelContextMap.size(), projectStructureContext.length());
    }
    
    /**
     * Get Spring AI-specific context for a label.
     */
    public Optional<SpringAILabelContext> getLabelContext(String labelName) {
        return Optional.ofNullable(labelContextMap.get(labelName.toLowerCase()));
    }
    
    /**
     * Get enriched label description with Spring AI context.
     */
    public String getEnrichedLabelDescription(String labelName) {
        return getLabelContext(labelName)
            .map(this::buildEnrichedDescription)
            .orElse("Technical label: " + labelName);
    }
    
    /**
     * Get Spring AI project structure context for prompts.
     */
    public String getProjectStructureContext() {
        return projectStructureContext;
    }
    
    /**
     * Check if a label has rich Spring AI context available.
     */
    public boolean hasRichContext(String labelName) {
        return getLabelContext(labelName)
            .map(context -> !context.description().contains("Not found in project codebase"))
            .orElse(false);
    }
    
    /**
     * Get all labels that have rich Spring AI context.
     */
    public Set<String> getLabelsWithRichContext() {
        return labelContextMap.entrySet().stream()
            .filter(entry -> hasRichContext(entry.getKey()))
            .map(Map.Entry::getKey)
            .collect(java.util.stream.Collectors.toSet());
    }
    
    private void loadEnhancedLabelMapping() {
        try {
            // Try to load from classpath first, then from external file
            ClassPathResource resource = new ClassPathResource("github-labels-mapping-enhanced.json");
            JsonNode labelsArray;
            
            if (resource.exists()) {
                labelsArray = objectMapper.readTree(resource.getInputStream());
            } else {
                // Fallback to external file
                java.io.File externalFile = new java.io.File("github-labels-mapping-enhanced.json");
                if (externalFile.exists()) {
                    labelsArray = objectMapper.readTree(externalFile);
                } else {
                    log.warn("Enhanced label mapping not found, using minimal context");
                    return;
                }
            }
            
            for (JsonNode labelNode : labelsArray) {
                SpringAILabelContext context = parseLabelContext(labelNode);
                labelContextMap.put(context.label().toLowerCase(), context);
            }
            
        } catch (IOException e) {
            log.error("Failed to load enhanced label mapping: {}", e.getMessage(), e);
        }
    }
    
    private void loadProjectStructureContext() {
        try {
            ClassPathResource resource = new ClassPathResource("claude-md-for-springai.md");
            if (resource.exists()) {
                projectStructureContext = new String(resource.getInputStream().readAllBytes());
            } else {
                // Fallback to external file
                java.io.File externalFile = new java.io.File("claude-md-for-springai.md");
                if (externalFile.exists()) {
                    projectStructureContext = java.nio.file.Files.readString(externalFile.toPath());
                }
            }
        } catch (IOException e) {
            log.error("Failed to load project structure context: {}", e.getMessage(), e);
        }
    }
    
    private SpringAILabelContext parseLabelContext(JsonNode labelNode) {
        return new SpringAILabelContext(
            labelNode.get("label").asText(),
            labelNode.get("description").asText(),
            parseStringList(labelNode.get("relevant_modules")),
            parseStringList(labelNode.get("packages")),
            parseStringList(labelNode.get("key_classes")),
            parseStringList(labelNode.get("config_keys")),
            parseStringList(labelNode.get("example_problem_phrases")),
            parseStringList(labelNode.get("typical_error_patterns")),
            parseStringList(labelNode.get("developer_touchpoints"))
        );
    }
    
    private List<String> parseStringList(JsonNode node) {
        if (node == null || !node.isArray()) {
            return List.of();
        }
        
        List<String> result = new ArrayList<>();
        for (JsonNode item : node) {
            result.add(item.asText());
        }
        return result;
    }
    
    private String buildEnrichedDescription(SpringAILabelContext context) {
        StringBuilder desc = new StringBuilder();
        desc.append("**").append(context.label()).append("**: ");
        desc.append(context.description());
        
        if (!context.relevantModules().isEmpty()) {
            desc.append("\n\n**Modules**: ").append(String.join(", ", context.relevantModules()));
        }
        
        if (!context.packages().isEmpty()) {
            desc.append("\n**Packages**: ").append(String.join(", ", context.packages()));
        }
        
        if (!context.keyClasses().isEmpty()) {
            desc.append("\n**Key Classes**: ").append(String.join(", ", context.keyClasses()));
        }
        
        if (!context.exampleProblemPhrases().isEmpty()) {
            desc.append("\n**Common Issues**: ");
            for (String phrase : context.exampleProblemPhrases()) {
                desc.append("\"").append(phrase).append("\", ");
            }
            desc.setLength(desc.length() - 2); // Remove trailing comma
        }
        
        return desc.toString();
    }
    
    /**
     * Record representing Spring AI-specific context for a label.
     */
    public record SpringAILabelContext(
        String label,
        String description,
        List<String> relevantModules,
        List<String> packages, 
        List<String> keyClasses,
        List<String> configKeys,
        List<String> exampleProblemPhrases,
        List<String> typicalErrorPatterns,
        List<String> developerTouchpoints
    ) {}
}
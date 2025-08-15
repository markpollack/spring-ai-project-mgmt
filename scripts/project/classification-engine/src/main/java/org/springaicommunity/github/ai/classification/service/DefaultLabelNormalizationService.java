package org.springaicommunity.github.ai.classification.service;

import org.springaicommunity.github.ai.classification.domain.ClassificationConfig;
import org.springaicommunity.github.ai.classification.domain.LabelGroup;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/**
 * Default implementation of LabelNormalizationService.
 * 
 * <p>This service implements the Python normalize_labels() logic with proper
 * Spring integration, constructor-based dependency injection, and comprehensive
 * statistics tracking for monitoring and debugging.</p>
 * 
 * <p>Thread-safe implementation suitable for concurrent use in multi-threaded
 * classification scenarios.</p>
 */
@Service
public class DefaultLabelNormalizationService implements LabelNormalizationService {
    
    private static final Logger logger = LoggerFactory.getLogger(DefaultLabelNormalizationService.class);
    
    private final ClassificationConfig config;
    
    // Statistics tracking (thread-safe)
    private final AtomicLong totalLabelsProcessed = new AtomicLong(0);
    private final AtomicLong totalLabelsIgnored = new AtomicLong(0);
    private final AtomicLong totalLabelsGrouped = new AtomicLong(0);
    private final AtomicLong totalNormalizationCalls = new AtomicLong(0);
    
    // Cached mappings for performance (immutable after construction)
    private final Map<String, String> labelToGroupCache;
    private final Set<String> normalizedIgnoredLabels;
    
    /**
     * Constructor with dependency injection.
     * 
     * @param config the classification configuration
     */
    public DefaultLabelNormalizationService(ClassificationConfig config) {
        this.config = Objects.requireNonNull(config, "Configuration cannot be null");
        
        // Pre-compute mappings for performance
        this.labelToGroupCache = buildLabelToGroupCache(config.labelGroups());
        this.normalizedIgnoredLabels = normalizeIgnoredLabels(config.ignoredLabels());
        
        logger.info("LabelNormalizationService initialized with {} label groups and {} ignored labels",
                   config.labelGroups().size(), config.ignoredLabels().size());
    }
    
    @Override
    public List<String> normalizeLabels(List<String> rawLabels) {
        if (rawLabels == null || rawLabels.isEmpty()) {
            return Collections.emptyList();
        }
        
        totalNormalizationCalls.incrementAndGet();
        
        Set<String> normalized = new LinkedHashSet<>(); // Preserve order, avoid duplicates
        
        for (String rawLabel : rawLabels) {
            totalLabelsProcessed.incrementAndGet();
            
            String normalizedLabel = normalizeLabel(rawLabel);
            if (normalizedLabel != null) {
                normalized.add(normalizedLabel);
            }
        }
        
        List<String> result = new ArrayList<>(normalized);
        
        logger.debug("Normalized {} labels to {} unique labels: {} -> {}",
                    rawLabels.size(), result.size(), rawLabels, result);
        
        return result;
    }
    
    @Override
    public String normalizeLabel(String rawLabel) {
        if (rawLabel == null || rawLabel.trim().isEmpty()) {
            return null;
        }
        
        // Step 1: Normalize case and whitespace (Python: label.strip().lower())
        String normalized = rawLabel.trim().toLowerCase();
        
        // Step 2: Check if label should be ignored (Python: if lower_label in IGNORED_LABELS)
        if (isIgnoredLabel(normalized)) {
            totalLabelsIgnored.incrementAndGet();
            logger.debug("Ignoring label: {}", rawLabel);
            return null;
        }
        
        // Step 3: Check for label grouping (Python: for group_name, group_members in LABEL_GROUPS.items())
        String groupName = findGroupName(normalized);
        if (!groupName.equals(normalized)) {
            totalLabelsGrouped.incrementAndGet();
            logger.debug("Grouped label: {} -> {}", rawLabel, groupName);
            return groupName;
        }
        
        // Step 4: Return normalized label if not grouped (Python: normalized.add(lower_label))
        return normalized;
    }
    
    @Override
    public boolean isIgnoredLabel(String labelName) {
        if (labelName == null) {
            return true;
        }
        
        String normalized = labelName.trim().toLowerCase();
        return normalizedIgnoredLabels.contains(normalized);
    }
    
    @Override
    public String findGroupName(String labelVariant) {
        if (labelVariant == null) {
            return null;
        }
        
        String normalized = labelVariant.trim().toLowerCase();
        return labelToGroupCache.getOrDefault(normalized, normalized);
    }
    
    @Override
    public Map<String, Integer> analyzeLabelFrequency(Map<Integer, List<String>> issueLabels) {
        if (issueLabels == null || issueLabels.isEmpty()) {
            return Collections.emptyMap();
        }
        
        Map<String, Integer> frequency = new HashMap<>();
        
        for (List<String> labels : issueLabels.values()) {
            for (String label : labels) {
                frequency.merge(label, 1, Integer::sum);
            }
        }
        
        logger.info("Analyzed label frequency for {} issues, found {} unique labels",
                   issueLabels.size(), frequency.size());
        
        return frequency;
    }
    
    @Override
    public Set<String> identifyRareLabels(Map<String, Integer> labelFrequency, int minOccurrences) {
        if (labelFrequency == null) {
            return Collections.emptySet();
        }
        
        Set<String> rareLabels = labelFrequency.entrySet().stream()
            .filter(entry -> entry.getValue() < minOccurrences)
            .map(Map.Entry::getKey)
            .collect(Collectors.toSet());
        
        logger.info("Identified {} rare labels (< {} occurrences) out of {} total labels",
                   rareLabels.size(), minOccurrences, labelFrequency.size());
        
        return rareLabels;
    }
    
    @Override
    public boolean isConfigurationValid() {
        try {
            return config != null &&
                   config.labelGroups() != null &&
                   config.ignoredLabels() != null &&
                   !labelToGroupCache.isEmpty();
        } catch (Exception e) {
            logger.error("Configuration validation failed", e);
            return false;
        }
    }
    
    @Override
    public ClassificationConfig getConfiguration() {
        return config;
    }
    
    @Override
    public String getNormalizationStatistics() {
        return String.format(
            "Normalization Statistics: %d calls, %d labels processed, %d ignored (%.1f%%), %d grouped (%.1f%%)",
            totalNormalizationCalls.get(),
            totalLabelsProcessed.get(),
            totalLabelsIgnored.get(),
            getPercentage(totalLabelsIgnored.get(), totalLabelsProcessed.get()),
            totalLabelsGrouped.get(),
            getPercentage(totalLabelsGrouped.get(), totalLabelsProcessed.get())
        );
    }
    
    /**
     * Builds the label-to-group mapping cache for fast lookups.
     */
    private Map<String, String> buildLabelToGroupCache(List<LabelGroup> labelGroups) {
        Map<String, String> cache = new HashMap<>();
        
        for (LabelGroup group : labelGroups) {
            String groupName = group.groupName();
            for (String member : group.members()) {
                String normalizedMember = member.trim().toLowerCase();
                cache.put(normalizedMember, groupName);
                logger.debug("Mapped label variant: {} -> {}", normalizedMember, groupName);
            }
        }
        
        return Collections.unmodifiableMap(cache);
    }
    
    /**
     * Pre-normalizes ignored labels for consistent comparison.
     */
    private Set<String> normalizeIgnoredLabels(Set<String> ignoredLabels) {
        return ignoredLabels.stream()
            .map(label -> label.trim().toLowerCase())
            .collect(Collectors.toUnmodifiableSet());
    }
    
    /**
     * Helper method to calculate percentage with division by zero protection.
     */
    private double getPercentage(long numerator, long denominator) {
        return denominator > 0 ? (numerator * 100.0) / denominator : 0.0;
    }
}
package org.springaicommunity.github.ai.classification.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Collections;
import java.util.Set;

/**
 * Represents a label group for normalization and mapping.
 * 
 * <p>Label groups allow mapping specific technology variants to broader categories.
 * For example, "pgvector", "qdrant", "weaviate" all map to "vector store".</p>
 * 
 * <p>Based on the Python LABEL_GROUPS configuration:
 * <pre>
 * LABEL_GROUPS = {
 *     "vector store": {"pinecone", "qdrant", "weaviate", "pgvector", ...},
 *     "model client": {"openai", "claude", "ollama", ...}
 * }
 * </pre></p>
 * 
 * @param groupName The canonical label name (e.g., "vector store")
 * @param members Set of variant names that map to this group
 */
public record LabelGroup(
    @JsonProperty("group_name") String groupName,
    @JsonProperty("members") Set<String> members
) {
    
    /**
     * Constructor with validation and immutable set creation.
     */
    @JsonCreator
    public LabelGroup {
        if (groupName == null || groupName.trim().isEmpty()) {
            throw new IllegalArgumentException("Group name cannot be null or empty");
        }
        if (members == null) {
            members = Collections.emptySet();
        } else {
            // Normalize all members to lowercase for consistent matching
            members = members.stream()
                .map(String::toLowerCase)
                .map(String::trim)
                .collect(java.util.stream.Collectors.toUnmodifiableSet());
        }
    }
    
    /**
     * Checks if a label variant belongs to this group.
     * 
     * @param labelVariant the label to check (case-insensitive)
     * @return true if the variant maps to this group
     */
    public boolean contains(String labelVariant) {
        if (labelVariant == null) {
            return false;
        }
        return members.contains(labelVariant.toLowerCase().trim());
    }
    
    /**
     * Returns the normalized group name (lowercase, trimmed).
     * 
     * @return normalized group name for comparison
     */
    public String normalizedGroupName() {
        return groupName.toLowerCase().trim();
    }
    
    /**
     * Creates a label group with the given name and members.
     * 
     * @param groupName the canonical group name
     * @param members the variant names
     * @return new label group
     */
    public static LabelGroup of(String groupName, String... members) {
        return new LabelGroup(groupName, Set.of(members));
    }
    
    /**
     * Creates a label group with a single member.
     * 
     * @param groupName the canonical group name
     * @param member the single variant name
     * @return new label group
     */
    public static LabelGroup single(String groupName, String member) {
        return new LabelGroup(groupName, Set.of(member));
    }
}
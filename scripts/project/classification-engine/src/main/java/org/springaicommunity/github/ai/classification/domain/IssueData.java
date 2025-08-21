package org.springaicommunity.github.ai.classification.domain;

import java.util.Set;

/**
 * Type-safe representation of GitHub issue data for classification analysis.
 * 
 * This record provides type safety and convenience methods for accessing
 * issue information loaded from test_set.json and other issue data sources.
 */
public record IssueData(
    int issueNumber,
    String title,
    String body,
    String author,
    Set<String> labels
) {
    
    /**
     * Calculate the total text size of this issue (title + body).
     */
    public int getTextSize() {
        return (title != null ? title.length() : 0) + 
               (body != null ? body.length() : 0);
    }
    
    /**
     * Get a normalized title (handling nulls).
     */
    public String getNormalizedTitle() {
        return title != null ? title.trim() : "";
    }
    
    /**
     * Get a normalized body (handling nulls).
     */
    public String getNormalizedBody() {
        return body != null ? body.trim() : "";
    }
    
    /**
     * Check if this issue has a specific label.
     */
    public boolean hasLabel(String label) {
        return labels != null && labels.contains(label);
    }
    
    /**
     * Get the number of labels on this issue.
     */
    public int getLabelCount() {
        return labels != null ? labels.size() : 0;
    }
    
    /**
     * Get a safe copy of labels (never null).
     */
    public Set<String> getSafeLabels() {
        return labels != null ? Set.copyOf(labels) : Set.of();
    }
}
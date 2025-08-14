package org.springaicommunity.github.ai.collection;

import java.util.List;

/**
 * Internal record for resume state management.
 */
public record ResumeState(
    String cursor,
    int batchNumber,
    int processedIssues,
    String timestamp,
    List<String> completedBatches
) {}
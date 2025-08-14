package org.springaicommunity.github.ai.collection;

import java.util.List;

/**
 * Internal record for tracking collection statistics.
 */
public record CollectionStats(
    List<String> batchFiles, 
    int processedIssues
) {}
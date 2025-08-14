package org.springaicommunity.github.ai.collection;

import java.util.List;

/**
 * Internal record for batch processing data.
 */
public record BatchData(
    int batchNumber, 
    List<Issue> issues, 
    String timestamp
) {}
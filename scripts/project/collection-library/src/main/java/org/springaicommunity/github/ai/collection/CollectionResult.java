package org.springaicommunity.github.ai.collection;

import java.util.List;

/**
 * Results of a collection operation.
 */
public record CollectionResult(
    int totalIssues,
    int processedIssues,
    String outputDirectory,
    List<String> batchFiles
) {}
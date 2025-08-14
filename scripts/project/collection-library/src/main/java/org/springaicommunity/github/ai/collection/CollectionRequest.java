package org.springaicommunity.github.ai.collection;

import java.util.List;

/**
 * Configuration parameters for an issue collection request.
 */
public record CollectionRequest(
    String repository,
    int batchSize,
    boolean dryRun,
    boolean incremental,
    boolean zip,
    boolean clean,
    boolean resume,
    String issueState,
    List<String> labelFilters,
    String labelMode
) {}
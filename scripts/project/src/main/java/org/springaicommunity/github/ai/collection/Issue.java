package org.springaicommunity.github.ai.collection;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Represents a GitHub issue with all relevant metadata.
 */
public record Issue(
    int number,
    String title,
    String body,
    String state,
    LocalDateTime createdAt,
    LocalDateTime updatedAt,
    LocalDateTime closedAt,
    String url,
    Author author,
    List<Comment> comments,
    List<Label> labels
) {}
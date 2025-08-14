package org.springaicommunity.github.ai.collection;

import java.time.LocalDateTime;

/**
 * Represents a comment on a GitHub issue.
 */
public record Comment(
    Author author,
    String body,
    LocalDateTime createdAt
) {}
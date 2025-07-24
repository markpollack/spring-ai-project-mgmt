package org.springaicommunity.github.ai.collection;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Data models and record definitions for GitHub Issues Collection.
 * 
 * This module contains all record definitions used throughout the application:
 * - Core GitHub data structures (Issue, Comment, Author, Label)
 * - Collection metadata and configuration (CollectionMetadata, CollectionRequest, CollectionResult)
 * - Internal processing records (BatchData, CollectionStats, ResumeState)
 */
public class DataModels {

    // ================================
    // Core GitHub Data Structures
    // ================================

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

    /**
     * Represents a comment on a GitHub issue.
     */
    public record Comment(
        Author author,
        String body,
        LocalDateTime createdAt
    ) {}

    /**
     * Represents a GitHub user (author of issues or comments).
     */
    public record Author(
        String login,
        String name
    ) {}

    /**
     * Represents a GitHub label with styling information.
     */
    public record Label(
        String name,
        String color,
        String description
    ) {}

    // ================================
    // Collection Configuration & Metadata
    // ================================

    /**
     * Metadata about a completed collection run.
     */
    public record CollectionMetadata(
        String timestamp,
        String repository,
        int totalIssues,
        int processedIssues,
        int batchSize,
        boolean zipped
    ) {}

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

    /**
     * Results of a collection operation.
     */
    public record CollectionResult(
        int totalIssues,
        int processedIssues,
        String outputDirectory,
        List<String> batchFiles
    ) {}

    // ================================
    // Internal Processing Records
    // ================================

    /**
     * Internal record for batch processing data.
     */
    public record BatchData(
        int batchNumber, 
        List<Issue> issues, 
        String timestamp
    ) {}

    /**
     * Internal record for tracking collection statistics.
     */
    public record CollectionStats(
        List<String> batchFiles, 
        int processedIssues
    ) {}

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
}
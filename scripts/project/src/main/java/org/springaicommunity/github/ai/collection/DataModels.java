package org.springaicommunity.github.ai.collection;

/**
 * @deprecated This class has been refactored. Individual record classes are now separate files:
 * 
 * Core GitHub Data Structures:
 * - {@link Issue} - Represents a GitHub issue with all relevant metadata
 * - {@link Comment} - Represents a comment on a GitHub issue  
 * - {@link Author} - Represents a GitHub user (author of issues or comments)
 * - {@link Label} - Represents a GitHub label with styling information
 * 
 * Collection Configuration & Metadata:
 * - {@link CollectionMetadata} - Metadata about a completed collection run
 * - {@link CollectionRequest} - Configuration parameters for an issue collection request
 * - {@link CollectionResult} - Results of a collection operation
 * 
 * Internal Processing Records:
 * - {@link BatchData} - Internal record for batch processing data
 * - {@link CollectionStats} - Internal record for tracking collection statistics
 * - {@link ResumeState} - Internal record for resume state management
 */
@Deprecated(since = "1.0.0", forRemoval = true)
public class DataModels {
    // This class is deprecated - use individual record classes instead
}
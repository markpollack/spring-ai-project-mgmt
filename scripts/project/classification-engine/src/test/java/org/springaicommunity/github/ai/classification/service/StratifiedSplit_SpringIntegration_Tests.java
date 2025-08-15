package org.springaicommunity.github.ai.classification.service;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springaicommunity.github.ai.classification.domain.DataSplit;
import org.springaicommunity.github.ai.collection.Issue;

import java.util.*;

import static org.assertj.core.api.Assertions.*;

/**
 * Spring integration tests for StratifiedSplitService.
 * 
 * <p>Tests service injection and complex operations requiring Spring context.</p>
 */
@DisplayName("StratifiedSplitService - Spring Integration Tests")
class StratifiedSplit_SpringIntegration_Tests extends StratifiedSplitServiceTestBase {

    @Test
    @DisplayName("Should inject service correctly")
    void shouldInjectServiceCorrectly() {
        assertThat(service).isNotNull();
        assertThat(service).isInstanceOf(DefaultStratifiedSplitService.class);
    }

    @Test
    @DisplayName("Should perform end-to-end stratified split")
    void shouldPerformEndToEndStratifiedSplit() {
        // Given
        List<Issue> issues = createTestIssues();

        // When
        DataSplit split = service.performStratifiedSplit(issues);

        // Then
        assertThat(split).isNotNull();
        assertThat(split.totalIssues()).isEqualTo(issues.size());
        assertThat(split.trainSet().size() + split.testSet().size()).isEqualTo(issues.size());
        assertThat(service.validateSplitQuality(split, issues, 0.2)).isTrue();
    }

    @Test
    @DisplayName("Should analyze label frequency correctly")
    void shouldAnalyzeLabelFrequencyCorrectly() {
        // Given
        List<Issue> issues = List.of(
            createIssue(1, "pgvector", "bug"),      // vector store, bug
            createIssue(2, "openai", "enhancement"), // model client, enhancement  
            createIssue(3, "pgvector", "bug"),      // vector store, bug
            createIssue(4, "bug")                   // bug
        );

        // When
        Map<String, Integer> frequency = service.analyzeLabelFrequency(issues);

        // Then
        assertThat(frequency).containsEntry("vector store", 2); // pgvector -> vector store
        assertThat(frequency).containsEntry("model client", 1); // openai -> model client
        assertThat(frequency).containsEntry("bug", 3);
        assertThat(frequency).containsEntry("enhancement", 1);
    }

    @Test
    @DisplayName("Should identify rare labels correctly")
    void shouldIdentifyRareLabelsCorrectly() {
        // Given
        Map<String, Integer> labelFrequency = Map.of(
            "common1", 5,
            "common2", 4,
            "rare1", 2,    // rare (< 3)
            "rare2", 1,    // rare (< 3)
            "borderline", 3 // not rare (== 3)
        );

        // When
        Set<String> rareLabels = service.identifyRareLabels(labelFrequency, 3);

        // Then
        assertThat(rareLabels).containsExactlyInAnyOrder("rare1", "rare2");
    }

    @Test
    @DisplayName("Should generate meaningful split statistics")
    void shouldGenerateMeaningfulSplitStatistics() {
        // Given
        List<Issue> issues = createTestIssues();
        DataSplit split = service.performStratifiedSplit(issues);

        // When
        String statistics = service.generateSplitStatistics(split, issues);

        // Then
        assertThat(statistics)
            .contains("Stratified Split Results")
            .contains("Total issues:")
            .contains("Train set size:")
            .contains("Test set size:")
            .contains("Split ratio:")
            .contains("Rare labels found:")
            .contains("seed: 42");
    }

    @Test
    @DisplayName("Should validate split quality correctly")
    void shouldValidateSplitQualityCorrectly() {
        // Given
        List<Issue> issues = createTestIssues();
        DataSplit split = service.performStratifiedSplit(issues);

        // When & Then - Valid split
        assertThat(service.validateSplitQuality(split, issues, 0.2)).isTrue();

        // Invalid split (null)
        assertThat(service.validateSplitQuality(null, issues, 0.2)).isFalse();
        assertThat(service.validateSplitQuality(split, null, 0.2)).isFalse();
    }

    @Test
    @DisplayName("Should calculate set label distribution correctly")
    void shouldCalculateSetLabelDistributionCorrectly() {
        // Given
        List<Issue> trainSet = List.of(
            createIssue(1, "pgvector", "bug"),      // vector store, bug
            createIssue(2, "openai", "enhancement") // model client, enhancement
        );

        // When
        Map<String, Integer> distribution = service.calculateSetLabelDistribution(trainSet);

        // Then
        assertThat(distribution).containsEntry("vector store", 1);
        assertThat(distribution).containsEntry("model client", 1);
        assertThat(distribution).containsEntry("bug", 1);
        assertThat(distribution).containsEntry("enhancement", 1);
    }
}
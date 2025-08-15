package org.springaicommunity.github.ai.classification.service;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.assertj.core.api.Assertions.*;

/**
 * Spring integration tests for LabelNormalizationService.
 * 
 * <p>Tests service injection and complex operations requiring Spring context.</p>
 */
@DisplayName("LabelNormalizationService - Spring Integration Tests")
class LabelNormalization_SpringIntegration_Tests extends LabelServiceTestBase {

    @Test
    @DisplayName("Should inject service correctly")
    void shouldInjectServiceCorrectly() {
        assertThat(service).isNotNull();
        assertThat(service).isInstanceOf(DefaultLabelNormalizationService.class);
        assertThat(service.isConfigurationValid()).isTrue();
    }

    @Test
    @DisplayName("Should normalize label lists correctly")
    void shouldNormalizeLabelListsCorrectly() {
        // Given
        List<String> rawLabels = List.of(
            "pgvector", "OPENAI", " bug ", "triage", "Enhancement", "duplicate", "qdrant"
        );

        // When
        List<String> normalized = service.normalizeLabels(rawLabels);

        // Then
        assertThat(normalized).containsExactlyInAnyOrder(
            "vector store", "model client", "bug", "enhancement"
        );
    }

    @Test
    @DisplayName("Should handle duplicate normalization correctly")
    void shouldHandleDuplicateNormalizationCorrectly() {
        // Given - multiple variants that map to same group
        List<String> rawLabels = List.of("pgvector", "qdrant", "weaviate", "openai", "claude");

        // When
        List<String> normalized = service.normalizeLabels(rawLabels);

        // Then - should only contain unique normalized labels
        assertThat(normalized).containsExactlyInAnyOrder("vector store", "model client");
    }

    @Test
    @DisplayName("Should analyze label frequency correctly")
    void shouldAnalyzeLabelFrequencyCorrectly() {
        // Given
        Map<Integer, List<String>> issueLabels = Map.of(
            1, List.of("bug", "enhancement"),
            2, List.of("bug", "documentation"),
            3, List.of("enhancement", "documentation"),
            4, List.of("bug")
        );

        // When
        Map<String, Integer> frequency = service.analyzeLabelFrequency(issueLabels);

        // Then
        assertThat(frequency).containsEntry("bug", 3);
        assertThat(frequency).containsEntry("enhancement", 2);
        assertThat(frequency).containsEntry("documentation", 2);
    }

    @Test
    @DisplayName("Should identify rare labels correctly")
    void shouldIdentifyRareLabelsCorrectly() {
        // Given
        Map<String, Integer> labelFrequency = Map.of(
            "bug", 5,
            "enhancement", 4,
            "documentation", 2, // rare
            "question", 1,      // rare
            "feature", 3        // not rare
        );

        // When
        Set<String> rareLabels = service.identifyRareLabels(labelFrequency, 3);

        // Then
        assertThat(rareLabels).containsExactlyInAnyOrder("documentation", "question");
    }
}
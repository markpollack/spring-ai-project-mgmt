package org.springaicommunity.github.ai.classification.service;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.assertj.core.api.Assertions.*;

/**
 * Performance and statistics tests for LabelNormalizationService.
 * 
 * <p>Tests performance characteristics and statistics tracking.</p>
 */
@DisplayName("LabelNormalizationService - Performance and Statistics")
class LabelNormalization_Performance_Tests extends LabelServiceTestBase {

    @Test
    @DisplayName("Should handle large label sets efficiently")
    void shouldHandleLargeLabelSetsEfficiently() {
        // Given - create a large set of labels
        List<String> largeSet = new ArrayList<>();
        for (int i = 0; i < 1000; i++) {
            largeSet.add("label-" + i);
            if (i % 100 == 0) largeSet.add("pgvector"); // Add some grouped labels
            if (i % 150 == 0) largeSet.add("triage");   // Add some ignored labels
        }

        // When
        long startTime = System.currentTimeMillis();
        List<String> result = service.normalizeLabels(largeSet);
        long duration = System.currentTimeMillis() - startTime;

        // Then
        assertThat(duration).isLessThan(1000); // Should complete in under 1 second
        assertThat(result).isNotEmpty();
        assertThat(result).contains("vector store"); // Should contain grouped labels
    }
}
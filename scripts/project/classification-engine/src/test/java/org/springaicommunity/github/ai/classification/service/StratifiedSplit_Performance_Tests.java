package org.springaicommunity.github.ai.classification.service;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springaicommunity.github.ai.classification.domain.DataSplit;
import org.springaicommunity.github.ai.collection.Issue;

import java.util.*;

import static org.assertj.core.api.Assertions.*;

/**
 * Performance and edge cases tests for StratifiedSplitService.
 * 
 * <p>Tests performance characteristics and boundary conditions.</p>
 */
@DisplayName("StratifiedSplitService - Performance and Edge Cases")
class StratifiedSplit_Performance_Tests extends StratifiedSplitServiceTestBase {

    @Test
    @DisplayName("Should handle large datasets efficiently")
    void shouldHandleLargeDatasetEfficiently() {
        // Given
        List<Issue> largeDataset = createLargeTestDataset(1000);

        // When
        long startTime = System.currentTimeMillis();
        DataSplit split = service.performStratifiedSplit(largeDataset);
        long duration = System.currentTimeMillis() - startTime;

        // Then
        assertThat(duration).isLessThan(5000); // Should complete in under 5 seconds
        assertThat(split.totalIssues()).isEqualTo(1000);
        assertThat(split.trainSet().size() + split.testSet().size()).isEqualTo(1000);
    }

    @Test
    @DisplayName("Should handle issues with no labels")
    void shouldHandleIssuesWithNoLabels() {
        // Given
        List<Issue> issues = List.of(
            createIssue(1, "bug"),
            createIssue(2), // no labels
            createIssue(3, "enhancement"),
            createIssue(4)  // no labels
        );

        // When
        DataSplit split = service.performStratifiedSplit(issues);

        // Then
        assertThat(split.totalIssues()).isEqualTo(4);
        assertThat(split.trainSet()).contains(2, 4); // Issues without labels go to training
    }

    @Test
    @DisplayName("Should provide algorithm statistics")
    void shouldProvideAlgorithmStatistics() {
        // Given
        List<Issue> issues = createTestIssues();
        service.performStratifiedSplit(issues); // Perform split to generate statistics

        // When
        String stats = service.getAlgorithmStatistics();

        // Then
        assertThat(stats)
            .contains("splits performed")
            .contains("issues processed")
            .contains("rare labels found")
            .contains("rare issues assigned");
    }

    @ParameterizedTest
    @CsvSource({
        "1, -0.1, 42", // Invalid test ratio (negative)
        "2, 0.0, 42",  // Invalid test ratio (zero) 
        "3, 1.0, 42",  // Invalid test ratio (one)
        "3, 1.5, 42",  // Invalid test ratio (> 1)
        "0, 0.2, 42"   // Invalid rare threshold (zero)
    })
    @DisplayName("Should validate configuration parameters")
    void shouldValidateConfigurationParameters(int rareThreshold, double testRatio, long seed) {
        // When & Then
        assertThat(service.isConfigurationValid(testRatio, rareThreshold, seed)).isFalse();
    }
}
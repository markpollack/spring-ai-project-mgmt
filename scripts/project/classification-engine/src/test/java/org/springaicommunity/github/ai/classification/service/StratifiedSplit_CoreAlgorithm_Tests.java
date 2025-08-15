package org.springaicommunity.github.ai.classification.service;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springaicommunity.github.ai.classification.domain.ClassificationConfig;
import org.springaicommunity.github.ai.classification.domain.DataSplit;
import org.springaicommunity.github.ai.collection.Issue;

import java.util.*;

import static org.assertj.core.api.Assertions.*;

/**
 * Core algorithm tests for StratifiedSplitService (no Spring context).
 * 
 * <p>Tests fundamental stratified splitting behavior using plain JUnit
 * for fast execution and reliable testing.</p>
 */
@DisplayName("StratifiedSplitService - Core Algorithm Tests")
class StratifiedSplit_CoreAlgorithm_Tests {

    private final ClassificationConfig config = ClassificationConfig.builder()
        .labelGroups(StratifiedSplitServiceTestBase.TestConfig.getTestLabelGroups())
        .ignoredLabels(StratifiedSplitServiceTestBase.TestConfig.getTestIgnoredLabels())
        .build();
    private final LabelNormalizationService labelService = new DefaultLabelNormalizationService(config);
    private final StratifiedSplitService service = new DefaultStratifiedSplitService(labelService);

    @Test
    @DisplayName("Should perform basic stratified split with default parameters")
    void shouldPerformBasicStratifiedSplit() {
        // Given
        List<Issue> issues = StratifiedSplitServiceTestBase.createTestIssues();

        // When
        DataSplit split = service.performStratifiedSplit(issues);

        // Then
        assertThat(split).isNotNull();
        assertThat(split.trainSet()).isNotEmpty();
        assertThat(split.testSet()).isNotEmpty();
        assertThat(split.totalIssues()).isEqualTo(issues.size());
        assertThat(split.randomSeed()).isEqualTo(42L);
        assertThat(split.splitRatio()).isEqualTo(0.2);
        assertThat(split.rareThreshold()).isEqualTo(3);
    }

    @Test
    @DisplayName("Should handle rare labels correctly")
    void shouldHandleRareLabelsCorrectly() {
        // Given - issues with rare labels (< 3 occurrences)
        List<Issue> issues = List.of(
            StratifiedSplitServiceTestBase.createIssue(1, "rare1", "common"),
            StratifiedSplitServiceTestBase.createIssue(2, "rare2", "common"),
            StratifiedSplitServiceTestBase.createIssue(3, "rare3", "common"),
            StratifiedSplitServiceTestBase.createIssue(4, "common"),
            StratifiedSplitServiceTestBase.createIssue(5, "common"),
            StratifiedSplitServiceTestBase.createIssue(6, "common"),
            StratifiedSplitServiceTestBase.createIssue(7, "common"),
            StratifiedSplitServiceTestBase.createIssue(8, "common"),
            StratifiedSplitServiceTestBase.createIssue(9, "common"),
            StratifiedSplitServiceTestBase.createIssue(10, "common")
        );

        // When
        DataSplit split = service.performStratifiedSplit(issues);

        // Then
        assertThat(split.rareLabels()).containsExactlyInAnyOrder("rare1", "rare2", "rare3");
        assertThat(split.rareIssuesCount()).isEqualTo(3);
        
        // Issues with rare labels should be in training set
        assertThat(split.trainSet()).contains(1, 2, 3);
        assertThat(split.testSet()).doesNotContain(1, 2, 3);
    }

    @Test
    @DisplayName("Should maintain reproducible splits with same seed")
    void shouldMaintainReproducibleSplits() {
        // Given
        List<Issue> issues = StratifiedSplitServiceTestBase.createTestIssues();

        // When
        DataSplit split1 = service.performStratifiedSplit(issues, 0.2, 3, 42L);
        DataSplit split2 = service.performStratifiedSplit(issues, 0.2, 3, 42L);

        // Then
        assertThat(split1.trainSet()).isEqualTo(split2.trainSet());
        assertThat(split1.testSet()).isEqualTo(split2.testSet());
        assertThat(split1.rareLabels()).isEqualTo(split2.rareLabels());
    }

    @Test
    @DisplayName("Should produce different splits with different seeds")
    void shouldProduceDifferentSplitsWithDifferentSeeds() {
        // Given
        List<Issue> issues = StratifiedSplitServiceTestBase.createTestIssues();

        // When
        DataSplit split1 = service.performStratifiedSplit(issues, 0.2, 3, 42L);
        DataSplit split2 = service.performStratifiedSplit(issues, 0.2, 3, 123L);

        // Then
        // Splits should be different (unless extremely unlucky)
        boolean trainSetsDifferent = !split1.trainSet().equals(split2.trainSet());
        boolean testSetsDifferent = !split1.testSet().equals(split2.testSet());
        
        assertThat(trainSetsDifferent || testSetsDifferent).isTrue();
    }

    @Test
    @DisplayName("Should respect custom test ratio")
    void shouldRespectCustomTestRatio() {
        // Given
        List<Issue> issues = StratifiedSplitServiceTestBase.createLargeTestDataset(100); // Need larger dataset for ratio testing

        // When
        DataSplit split = service.performStratifiedSplit(issues, 0.3, 3, 42L);

        // Then
        double actualTestRatio = split.getActualTestRatio();
        assertThat(actualTestRatio).isBetween(0.2, 0.4); // Within reasonable range
        assertThat(split.splitRatio()).isEqualTo(0.3);
    }

    @Test
    @DisplayName("Should validate configuration parameters")
    void shouldValidateConfigurationParameters() {
        // Given
        List<Issue> issues = StratifiedSplitServiceTestBase.createTestIssues();

        // When & Then - Invalid test ratio
        assertThatThrownBy(() -> service.performStratifiedSplit(issues, 0.0, 3, 42L))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Invalid configuration");

        assertThatThrownBy(() -> service.performStratifiedSplit(issues, 1.0, 3, 42L))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Invalid configuration");

        // Invalid rare threshold
        assertThatThrownBy(() -> service.performStratifiedSplit(issues, 0.2, 0, 42L))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Invalid configuration");
    }

    @Test
    @DisplayName("Should handle null and empty inputs")
    void shouldHandleNullAndEmptyInputs() {
        // When & Then
        assertThatThrownBy(() -> service.performStratifiedSplit(null))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("cannot be null or empty");

        assertThatThrownBy(() -> service.performStratifiedSplit(Collections.emptyList()))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("cannot be null or empty");
    }

    @ParameterizedTest
    @ValueSource(doubles = {0.1, 0.15, 0.2, 0.25, 0.3})
    @DisplayName("Should handle various test ratios correctly")
    void shouldHandleVariousTestRatiosCorrectly(double testRatio) {
        // Given
        List<Issue> issues = StratifiedSplitServiceTestBase.createLargeTestDataset(50);

        // When
        DataSplit split = service.performStratifiedSplit(issues, testRatio, 3, 42L);

        // Then
        assertThat(split.splitRatio()).isEqualTo(testRatio);
        assertThat(split.getActualTestRatio()).isBetween(testRatio - 0.1, testRatio + 0.1);
    }
}
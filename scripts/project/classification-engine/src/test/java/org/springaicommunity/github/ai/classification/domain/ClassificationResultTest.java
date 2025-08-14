package org.springaicommunity.github.ai.classification.domain;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Nested;

import java.util.Collections;
import java.util.List;
import java.util.Set;

import static org.assertj.core.api.Assertions.*;

/**
 * Tests for ClassificationResult record - Plain JUnit Only (No Spring Context).
 * 
 * Following consolidated learnings: Use plain JUnit for data models with no Spring dependencies.
 */
@DisplayName("ClassificationResult Tests - Plain JUnit Only")
class ClassificationResultTest {

    @Nested
    @DisplayName("Constructor Validation")
    class ConstructorValidation {

        @Test
        @DisplayName("Should create valid result with valid inputs")
        void shouldCreateValidResult() {
            // Given
            List<LabelPrediction> predictions = List.of(
                new LabelPrediction("vector store", 0.9),
                new LabelPrediction("documentation", 0.8)
            );

            // When
            ClassificationResult result = new ClassificationResult(1776, predictions, "Test explanation");

            // Then
            assertThat(result.issueNumber()).isEqualTo(1776);
            assertThat(result.predictedLabels()).hasSize(2);
            assertThat(result.explanation()).isEqualTo("Test explanation");
        }

        @Test
        @DisplayName("Should reject invalid issue numbers")
        void shouldRejectInvalidIssueNumbers() {
            // Given
            List<LabelPrediction> predictions = List.of(new LabelPrediction("test", 0.8));

            // When & Then
            assertThatThrownBy(() -> new ClassificationResult(0, predictions, "explanation"))
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessage("Issue number must be positive, got: 0");

            assertThatThrownBy(() -> new ClassificationResult(-1, predictions, "explanation"))
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessage("Issue number must be positive, got: -1");
        }

        @Test
        @DisplayName("Should handle null inputs gracefully")
        void shouldHandleNullInputsGracefully() {
            // When
            ClassificationResult result = new ClassificationResult(1776, null, null);

            // Then
            assertThat(result.predictedLabels()).isEmpty();
            assertThat(result.explanation()).isEmpty();
        }

        @Test
        @DisplayName("Should create immutable list from predicted labels")
        void shouldCreateImmutableListFromPredictedLabels() {
            // Given
            List<LabelPrediction> mutableList = new java.util.ArrayList<>();
            mutableList.add(new LabelPrediction("test", 0.8));

            // When
            ClassificationResult result = new ClassificationResult(1776, mutableList, "explanation");
            
            // Modify original list
            mutableList.add(new LabelPrediction("other", 0.7));

            // Then
            assertThat(result.predictedLabels()).hasSize(1); // Should not be affected by external changes
        }
    }

    @Nested
    @DisplayName("Label Names and Sets")
    class LabelNamesAndSets {

        @Test
        @DisplayName("Should extract label names correctly")
        void shouldExtractLabelNamesCorrectly() {
            // Given
            List<LabelPrediction> predictions = List.of(
                new LabelPrediction("vector store", 0.9),
                new LabelPrediction("documentation", 0.8),
                new LabelPrediction("enhancement", 0.7)
            );
            ClassificationResult result = new ClassificationResult(1776, predictions, "explanation");

            // When
            Set<String> labelNames = result.getLabelNames();

            // Then
            assertThat(labelNames).containsExactlyInAnyOrder("vector store", "documentation", "enhancement");
        }

        @Test
        @DisplayName("Should return empty set for no predictions")
        void shouldReturnEmptySetForNoPredictions() {
            // Given
            ClassificationResult result = new ClassificationResult(1776, Collections.emptyList(), "explanation");

            // When
            Set<String> labelNames = result.getLabelNames();

            // Then
            assertThat(labelNames).isEmpty();
        }

        @Test
        @DisplayName("Should check if result has specific label")
        void shouldCheckIfResultHasSpecificLabel() {
            // Given
            List<LabelPrediction> predictions = List.of(
                new LabelPrediction("vector store", 0.9),
                new LabelPrediction("documentation", 0.8)
            );
            ClassificationResult result = new ClassificationResult(1776, predictions, "explanation");

            // When & Then
            assertThat(result.hasLabel("vector store")).isTrue();
            assertThat(result.hasLabel("documentation")).isTrue();
            assertThat(result.hasLabel("bug")).isFalse();
            assertThat(result.hasLabel("nonexistent")).isFalse();
        }
    }

    @Nested
    @DisplayName("Confidence Filtering")
    class ConfidenceFiltering {

        @Test
        @DisplayName("Should filter high confidence predictions")
        void shouldFilterHighConfidencePredictions() {
            // Given
            List<LabelPrediction> predictions = List.of(
                new LabelPrediction("high1", 0.9),
                new LabelPrediction("low1", 0.6),
                new LabelPrediction("high2", 0.8),
                new LabelPrediction("low2", 0.5),
                new LabelPrediction("exact", 0.7)
            );
            ClassificationResult result = new ClassificationResult(1776, predictions, "explanation");

            // When
            List<LabelPrediction> highConfidence = result.getHighConfidencePredictions();

            // Then
            assertThat(highConfidence).hasSize(3);
            assertThat(highConfidence)
                    .extracting(LabelPrediction::label)
                    .containsExactlyInAnyOrder("high1", "high2", "exact");
        }

        @Test
        @DisplayName("Should filter predictions above custom threshold")
        void shouldFilterPredictionsAboveCustomThreshold() {
            // Given
            List<LabelPrediction> predictions = List.of(
                new LabelPrediction("very_high", 0.95),
                new LabelPrediction("high", 0.85),
                new LabelPrediction("medium", 0.75),
                new LabelPrediction("low", 0.65)
            );
            ClassificationResult result = new ClassificationResult(1776, predictions, "explanation");

            // When
            List<LabelPrediction> aboveThreshold = result.getPredictionsAboveThreshold(0.8);

            // Then
            assertThat(aboveThreshold).hasSize(2);
            assertThat(aboveThreshold)
                    .extracting(LabelPrediction::label)
                    .containsExactlyInAnyOrder("very_high", "high");
        }
    }

    @Nested
    @DisplayName("Statistics and Metrics")
    class StatisticsAndMetrics {

        @Test
        @DisplayName("Should calculate maximum confidence correctly")
        void shouldCalculateMaximumConfidenceCorrectly() {
            // Given
            List<LabelPrediction> predictions = List.of(
                new LabelPrediction("low", 0.6),
                new LabelPrediction("high", 0.95),
                new LabelPrediction("medium", 0.8)
            );
            ClassificationResult result = new ClassificationResult(1776, predictions, "explanation");

            // When
            double maxConfidence = result.getMaxConfidence();

            // Then
            assertThat(maxConfidence).isEqualTo(0.95);
        }

        @Test
        @DisplayName("Should return 0.0 max confidence for no predictions")
        void shouldReturnZeroMaxConfidenceForNoPredictions() {
            // Given
            ClassificationResult result = new ClassificationResult(1776, Collections.emptyList(), "explanation");

            // When
            double maxConfidence = result.getMaxConfidence();

            // Then
            assertThat(maxConfidence).isEqualTo(0.0);
        }

        @Test
        @DisplayName("Should count labels correctly")
        void shouldCountLabelsCorrectly() {
            // Given
            List<LabelPrediction> predictions = List.of(
                new LabelPrediction("label1", 0.8),
                new LabelPrediction("label2", 0.9),
                new LabelPrediction("label3", 0.7)
            );
            ClassificationResult result = new ClassificationResult(1776, predictions, "explanation");

            // When & Then
            assertThat(result.getLabelCount()).isEqualTo(3);
            assertThat(result.hasPredictions()).isTrue();
        }

        @Test
        @DisplayName("Should handle empty predictions")
        void shouldHandleEmptyPredictions() {
            // Given
            ClassificationResult result = new ClassificationResult(1776, Collections.emptyList(), "explanation");

            // When & Then
            assertThat(result.getLabelCount()).isEqualTo(0);
            assertThat(result.hasPredictions()).isFalse();
        }
    }

    @Nested
    @DisplayName("Record Properties and Behavior")
    class RecordPropertiesAndBehavior {

        @Test
        @DisplayName("Should provide proper equals and hashCode")
        void shouldProvideProperEqualsAndHashCode() {
            // Given
            List<LabelPrediction> predictions = List.of(new LabelPrediction("test", 0.8));
            ClassificationResult result1 = new ClassificationResult(1776, predictions, "explanation");
            ClassificationResult result2 = new ClassificationResult(1776, predictions, "explanation");
            ClassificationResult result3 = new ClassificationResult(1777, predictions, "explanation");

            // When & Then
            assertThat(result1).isEqualTo(result2);
            assertThat(result1).isNotEqualTo(result3);
            assertThat(result1.hashCode()).isEqualTo(result2.hashCode());
        }

        @Test
        @DisplayName("Should provide meaningful toString")
        void shouldProvideMeaningfulToString() {
            // Given
            List<LabelPrediction> predictions = List.of(new LabelPrediction("vector store", 0.9));
            ClassificationResult result = new ClassificationResult(1776, predictions, "Test explanation");

            // When
            String toString = result.toString();

            // Then
            assertThat(toString)
                    .contains("1776")
                    .contains("vector store")
                    .contains("Test explanation");
        }
    }

    @Nested
    @DisplayName("JSON Structure Compatibility")
    class JsonStructureCompatibility {

        @Test
        @DisplayName("Should match Python JSON structure")
        void shouldMatchPythonJsonStructure() {
            // This test ensures our Java structure matches the Python output format
            // Given
            List<LabelPrediction> predictions = List.of(
                new LabelPrediction("vector store", 0.9),
                new LabelPrediction("documentation", 0.8)
            );
            ClassificationResult result = new ClassificationResult(1776, predictions, 
                "Issue explicitly mentions vector database configuration and documentation updates.");

            // When & Then - Check that all required fields are present and accessible
            assertThat(result.issueNumber()).isPositive();
            assertThat(result.predictedLabels()).isNotEmpty();
            assertThat(result.explanation()).isNotBlank();
            
            // Verify the structure supports the expected Python format:
            // {"issue_number": 1776, "predicted_labels": [...], "explanation": "..."}
            assertThat(result.predictedLabels().get(0).label()).isEqualTo("vector store");
            assertThat(result.predictedLabels().get(0).confidence()).isEqualTo(0.9);
        }
    }
}
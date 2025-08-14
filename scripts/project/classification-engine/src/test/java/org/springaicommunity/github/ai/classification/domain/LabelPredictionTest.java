package org.springaicommunity.github.ai.classification.domain;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import static org.assertj.core.api.Assertions.*;

/**
 * Tests for LabelPrediction record - Plain JUnit Only (No Spring Context).
 * 
 * Following consolidated learnings: Use plain JUnit for data models with no Spring dependencies.
 */
@DisplayName("LabelPrediction Tests - Plain JUnit Only")
class LabelPredictionTest {

    @Nested
    @DisplayName("Constructor Validation")
    class ConstructorValidation {

        @Test
        @DisplayName("Should create valid prediction with valid inputs")
        void shouldCreateValidPrediction() {
            // Given & When
            LabelPrediction prediction = new LabelPrediction("vector store", 0.9);

            // Then
            assertThat(prediction.label()).isEqualTo("vector store");
            assertThat(prediction.confidence()).isEqualTo(0.9);
        }

        @Test
        @DisplayName("Should reject null label")
        void shouldRejectNullLabel() {
            // When & Then
            assertThatThrownBy(() -> new LabelPrediction(null, 0.8))
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessage("Label cannot be null or empty");
        }

        @Test
        @DisplayName("Should reject empty label")
        void shouldRejectEmptyLabel() {
            // When & Then
            assertThatThrownBy(() -> new LabelPrediction("", 0.8))
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessage("Label cannot be null or empty");
        }

        @Test
        @DisplayName("Should reject whitespace-only label")
        void shouldRejectWhitespaceOnlyLabel() {
            // When & Then
            assertThatThrownBy(() -> new LabelPrediction("   ", 0.8))
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessage("Label cannot be null or empty");
        }

        @ParameterizedTest
        @ValueSource(doubles = {-0.1, -1.0, 1.1, 2.0, Double.NEGATIVE_INFINITY, Double.POSITIVE_INFINITY})
        @DisplayName("Should reject invalid confidence values")
        void shouldRejectInvalidConfidence(double invalidConfidence) {
            // When & Then
            assertThatThrownBy(() -> new LabelPrediction("test", invalidConfidence))
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessage("Confidence must be between 0.0 and 1.0, got: " + invalidConfidence);
        }

        @ParameterizedTest
        @ValueSource(doubles = {0.0, 0.5, 0.7, 0.999, 1.0})
        @DisplayName("Should accept valid confidence values")
        void shouldAcceptValidConfidence(double validConfidence) {
            // When & Then
            assertThatCode(() -> new LabelPrediction("test", validConfidence))
                    .doesNotThrowAnyException();
        }
    }

    @Nested
    @DisplayName("Confidence Threshold Methods")
    class ConfidenceThresholdMethods {

        @Test
        @DisplayName("Should correctly identify high confidence predictions")
        void shouldIdentifyHighConfidencePredictions() {
            // Given
            LabelPrediction highConfidence = new LabelPrediction("test", 0.8);
            LabelPrediction lowConfidence = new LabelPrediction("test", 0.6);
            LabelPrediction exactThreshold = new LabelPrediction("test", 0.7);

            // When & Then
            assertThat(highConfidence.isHighConfidence()).isTrue();
            assertThat(lowConfidence.isHighConfidence()).isFalse();
            assertThat(exactThreshold.isHighConfidence()).isTrue(); // >= 0.7
        }

        @ParameterizedTest
        @ValueSource(doubles = {0.5, 0.75, 0.9})
        @DisplayName("Should correctly check custom thresholds")
        void shouldCheckCustomThresholds(double threshold) {
            // Given
            LabelPrediction prediction = new LabelPrediction("test", 0.8);

            // When & Then
            if (0.8 >= threshold) {
                assertThat(prediction.meetsThreshold(threshold)).isTrue();
            } else {
                assertThat(prediction.meetsThreshold(threshold)).isFalse();
            }
        }
    }

    @Nested
    @DisplayName("Label Normalization")
    class LabelNormalization {

        @Test
        @DisplayName("Should normalize label to lowercase and trimmed")
        void shouldNormalizeLabel() {
            // Given
            LabelPrediction prediction = new LabelPrediction("  Vector Store  ", 0.8);

            // When
            String normalized = prediction.normalizedLabel();

            // Then
            assertThat(normalized).isEqualTo("vector store");
        }

        @Test
        @DisplayName("Should handle already normalized labels")
        void shouldHandleAlreadyNormalizedLabels() {
            // Given
            LabelPrediction prediction = new LabelPrediction("vector store", 0.8);

            // When
            String normalized = prediction.normalizedLabel();

            // Then
            assertThat(normalized).isEqualTo("vector store");
        }
    }

    @Nested
    @DisplayName("Record Properties")
    class RecordProperties {

        @Test
        @DisplayName("Should provide proper equals and hashCode")
        void shouldProvideProperEqualsAndHashCode() {
            // Given
            LabelPrediction prediction1 = new LabelPrediction("test", 0.8);
            LabelPrediction prediction2 = new LabelPrediction("test", 0.8);
            LabelPrediction prediction3 = new LabelPrediction("other", 0.8);

            // When & Then
            assertThat(prediction1).isEqualTo(prediction2);
            assertThat(prediction1).isNotEqualTo(prediction3);
            assertThat(prediction1.hashCode()).isEqualTo(prediction2.hashCode());
        }

        @Test
        @DisplayName("Should provide meaningful toString")
        void shouldProvideMeaningfulToString() {
            // Given
            LabelPrediction prediction = new LabelPrediction("vector store", 0.85);

            // When
            String toString = prediction.toString();

            // Then
            assertThat(toString)
                    .contains("vector store")
                    .contains("0.85");
        }
    }

    @Nested
    @DisplayName("Edge Cases")
    class EdgeCases {

        @Test
        @DisplayName("Should handle minimum confidence")
        void shouldHandleMinimumConfidence() {
            // Given & When
            LabelPrediction prediction = new LabelPrediction("test", 0.0);

            // Then
            assertThat(prediction.confidence()).isEqualTo(0.0);
            assertThat(prediction.isHighConfidence()).isFalse();
            assertThat(prediction.meetsThreshold(0.0)).isTrue();
        }

        @Test
        @DisplayName("Should handle maximum confidence")
        void shouldHandleMaximumConfidence() {
            // Given & When
            LabelPrediction prediction = new LabelPrediction("test", 1.0);

            // Then
            assertThat(prediction.confidence()).isEqualTo(1.0);
            assertThat(prediction.isHighConfidence()).isTrue();
            assertThat(prediction.meetsThreshold(1.0)).isTrue();
        }

        @Test
        @DisplayName("Should handle special characters in label")
        void shouldHandleSpecialCharactersInLabel() {
            // Given & When
            LabelPrediction prediction = new LabelPrediction("type: backport", 0.9);

            // Then
            assertThat(prediction.label()).isEqualTo("type: backport");
            assertThat(prediction.normalizedLabel()).isEqualTo("type: backport");
        }
    }
}
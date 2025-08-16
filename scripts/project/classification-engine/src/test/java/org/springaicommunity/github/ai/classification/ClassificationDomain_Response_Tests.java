package org.springaicommunity.github.ai.classification;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springaicommunity.github.ai.classification.domain.ClassificationResponse;
import org.springaicommunity.github.ai.classification.domain.LabelPrediction;

import java.time.Duration;
import java.time.Instant;
import java.util.List;

import static org.assertj.core.api.Assertions.*;

/**
 * Tests for ClassificationResponse domain model validation and behavior.
 * Uses flattened test architecture to avoid JUnit 5 parameter resolution issues.
 */
@DisplayName("Classification Domain - Response Tests")
class ClassificationDomain_Response_Tests extends ClassificationTestBase {
    
    @Test
    @DisplayName("Valid response construction should succeed")
    void validResponseConstruction() {
        ClassificationResponse response = createSuccessResponse();
        
        assertThat(response.issueNumber()).isEqualTo(TEST_ISSUE_NUMBER);
        assertThat(response.predictedLabels()).hasSize(1);
        assertThat(response.predictedLabels().get(0).label()).isEqualTo("vector store");
        assertThat(response.predictedLabels().get(0).confidence()).isEqualTo(0.9);
        assertThat(response.explanation()).isNotEmpty();
        assertThat(response.processingTime()).isEqualTo(FAST_PROCESSING);
        assertThat(response.timestamp()).isEqualTo(FIXED_TIMESTAMP);
        assertThat(response.tokenUsage()).isEqualTo(1500L);
    }
    
    @Test
    @DisplayName("Builder pattern should work correctly")
    void builderPattern() {
        ClassificationResponse response = ClassificationResponse.builder()
            .issueNumber(456)
            .predictedLabels(List.of(new LabelPrediction("test", 0.8)))
            .explanation("Test explanation")
            .processingTime(Duration.ofSeconds(1))
            .timestamp(FIXED_TIMESTAMP)
            .tokenUsage(1000L)
            .build();
        
        assertThat(response.issueNumber()).isEqualTo(456);
        assertThat(response.predictedLabels()).hasSize(1);
        assertThat(response.explanation()).isEqualTo("Test explanation");
    }
    
    @ParameterizedTest
    @DisplayName("Invalid issue numbers should be rejected")
    @ValueSource(ints = {0, -1, -100})
    void invalidIssueNumbers(int invalidNumber) {
        assertThatThrownBy(() -> 
            ClassificationResponse.builder()
                .issueNumber(invalidNumber)
                .predictedLabels(List.of(new LabelPrediction("test", 0.8)))
                .explanation("Test")
                .processingTime(FAST_PROCESSING)
                .timestamp(FIXED_TIMESTAMP)
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Issue number must be positive");
    }
    
    @Test
    @DisplayName("Null predicted labels should be rejected")
    void nullPredictedLabelsRejection() {
        assertThatThrownBy(() -> 
            ClassificationResponse.builder()
                .issueNumber(123)
                .predictedLabels(null)
                .explanation("Test")
                .processingTime(FAST_PROCESSING)
                .timestamp(FIXED_TIMESTAMP)
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Predicted labels cannot be null");
    }
    
    @Test
    @DisplayName("Empty predicted labels should be allowed")
    void emptyPredictedLabelsAllowed() {
        assertThatCode(() -> 
            ClassificationResponse.builder()
                .issueNumber(123)
                .predictedLabels(List.of())
                .explanation("No predictions")
                .processingTime(FAST_PROCESSING)
                .timestamp(FIXED_TIMESTAMP)
                .build())
            .doesNotThrowAnyException();
    }
    
    @Test
    @DisplayName("Null explanation should be rejected")
    void nullExplanationRejection() {
        assertThatThrownBy(() -> 
            ClassificationResponse.builder()
                .issueNumber(123)
                .predictedLabels(List.of())
                .explanation(null)
                .processingTime(FAST_PROCESSING)
                .timestamp(FIXED_TIMESTAMP)
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Explanation cannot be null");
    }
    
    @Test
    @DisplayName("Empty explanation should be rejected")
    void emptyExplanationRejection() {
        assertThatThrownBy(() -> 
            ClassificationResponse.builder()
                .issueNumber(123)
                .predictedLabels(List.of())
                .explanation("")
                .processingTime(FAST_PROCESSING)
                .timestamp(FIXED_TIMESTAMP)
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Explanation cannot be empty");
    }
    
    @Test
    @DisplayName("Negative processing time should be rejected")
    void negativeProcessingTimeRejection() {
        assertThatThrownBy(() -> 
            ClassificationResponse.builder()
                .issueNumber(123)
                .predictedLabels(List.of())
                .explanation("Test")
                .processingTime(Duration.ofSeconds(-1))
                .timestamp(FIXED_TIMESTAMP)
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Processing time cannot be negative");
    }
    
    @Test
    @DisplayName("Max confidence should return highest score")
    void maxConfidenceCalculation() {
        ClassificationResponse response = createMultiLabelResponse(123);
        
        assertThat(response.getMaxConfidence()).isPresent();
        assertThat(response.getMaxConfidence().getAsDouble()).isEqualTo(0.9);
    }
    
    @Test
    @DisplayName("Max confidence should be empty for no predictions")
    void maxConfidenceEmptyForNoPredictions() {
        ClassificationResponse response = ClassificationResponse.builder()
            .issueNumber(123)
            .predictedLabels(List.of())
            .explanation("No predictions")
            .processingTime(FAST_PROCESSING)
            .timestamp(FIXED_TIMESTAMP)
            .build();
        
        assertThat(response.getMaxConfidence()).isEmpty();
    }
    
    @Test
    @DisplayName("Average confidence should be calculated correctly")
    void averageConfidenceCalculation() {
        ClassificationResponse response = createMultiLabelResponse(123);
        
        assertThat(response.getAverageConfidence()).isPresent();
        assertThat(response.getAverageConfidence().getAsDouble()).isEqualTo(0.85); // (0.9 + 0.8) / 2
    }
    
    @Test
    @DisplayName("High confidence detection should work")
    void highConfidenceDetection() {
        ClassificationResponse highConf = createSuccessResponse(123, "test", 0.9);
        ClassificationResponse lowConf = createFallbackResponse(456);
        
        assertThat(highConf.hasHighConfidencePredictions(0.8)).isTrue();
        assertThat(highConf.hasHighConfidencePredictions(0.95)).isFalse();
        assertThat(lowConf.hasHighConfidencePredictions(0.4)).isFalse();
    }
    
    @Test
    @DisplayName("Fallback classification detection should work")
    void fallbackClassificationDetection() {
        ClassificationResponse fallback = createFallbackResponse(123);
        ClassificationResponse normal = createSuccessResponse(456, "test", 0.8);
        
        assertThat(fallback.isFallbackClassification()).isTrue();
        assertThat(normal.isFallbackClassification()).isFalse();
    }
    
    @Test
    @DisplayName("Label names extraction should work")
    void labelNamesExtraction() {
        ClassificationResponse response = createMultiLabelResponse(123);
        
        assertThat(response.getLabelNames())
            .containsExactly("vector store", "performance");
    }
    
    @Test
    @DisplayName("Predicted labels should be immutable")
    void predictedLabelsImmutability() {
        List<LabelPrediction> originalPredictions = new java.util.ArrayList<>();
        originalPredictions.add(new LabelPrediction("test", 0.8));
        
        ClassificationResponse response = ClassificationResponse.builder()
            .issueNumber(123)
            .predictedLabels(originalPredictions)
            .explanation("Test")
            .processingTime(FAST_PROCESSING)
            .timestamp(FIXED_TIMESTAMP)
            .build();
        
        // Modify original list
        originalPredictions.add(new LabelPrediction("new", 0.7));
        
        // Response should be unaffected
        assertThat(response.predictedLabels()).hasSize(1);
        assertThat(response.getLabelNames()).containsExactly("test");
    }
    
    @Test
    @DisplayName("Builder should handle default values correctly")
    void builderDefaultValues() {
        Instant beforeBuild = Instant.now();
        
        ClassificationResponse response = ClassificationResponse.builder()
            .issueNumber(123)
            .predictedLabels(List.of())
            .explanation("Test")
            .build(); // Using defaults for time and timestamp
        
        Instant afterBuild = Instant.now();
        
        assertThat(response.processingTime()).isEqualTo(Duration.ZERO);
        assertThat(response.timestamp()).isBetween(beforeBuild, afterBuild);
        assertThat(response.tokenUsage()).isNull();
    }
}
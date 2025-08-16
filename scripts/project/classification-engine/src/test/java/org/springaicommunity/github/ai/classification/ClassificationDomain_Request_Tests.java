package org.springaicommunity.github.ai.classification;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springaicommunity.github.ai.classification.domain.ClassificationRequest;

import java.util.List;

import static org.assertj.core.api.Assertions.*;

/**
 * Tests for ClassificationRequest domain model validation and behavior.
 * Uses flattened test architecture to avoid JUnit 5 parameter resolution issues.
 */
@DisplayName("Classification Domain - Request Tests")
class ClassificationDomain_Request_Tests extends ClassificationTestBase {
    
    @Test
    @DisplayName("Valid request construction should succeed")
    void validRequestConstruction() {
        ClassificationRequest request = createTestRequest();
        
        assertThat(request.issueNumber()).isEqualTo(TEST_ISSUE_NUMBER);
        assertThat(request.title()).isEqualTo(TEST_ISSUE_TITLE);
        assertThat(request.body()).isEqualTo(TEST_ISSUE_BODY);
        assertThat(request.availableLabels()).containsExactlyElementsOf(TEST_AVAILABLE_LABELS);
        assertThat(request.config()).isNotNull();
    }
    
    @Test
    @DisplayName("Builder pattern should work correctly")
    void builderPattern() {
        ClassificationRequest request = ClassificationRequest.builder()
            .issueNumber(123)
            .title("Test Title")
            .body("Test Body")
            .availableLabels(List.of("label1", "label2"))
            .build();
        
        assertThat(request.issueNumber()).isEqualTo(123);
        assertThat(request.title()).isEqualTo("Test Title");
        assertThat(request.body()).isEqualTo("Test Body");
        assertThat(request.availableLabels()).containsExactly("label1", "label2");
        assertThat(request.config()).isEqualTo(DEFAULT_CONFIG); // Default config
    }
    
    @ParameterizedTest
    @DisplayName("Invalid issue numbers should be rejected")
    @ValueSource(ints = {0, -1, -100})
    void invalidIssueNumbers(int invalidNumber) {
        assertThatThrownBy(() -> 
            createTestRequest(invalidNumber, "Valid Title", "Valid Body"))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Issue number must be positive");
    }
    
    @Test
    @DisplayName("Null title should be rejected")
    void nullTitleRejection() {
        assertThatThrownBy(() -> 
            ClassificationRequest.builder()
                .issueNumber(123)
                .title(null)
                .body("Valid Body")
                .availableLabels(List.of("label1"))
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Title cannot be null");
    }
    
    @Test
    @DisplayName("Empty title should be rejected")
    void emptyTitleRejection() {
        assertThatThrownBy(() -> 
            createTestRequest(123, "", "Valid Body"))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Title cannot be empty");
    }
    
    @Test
    @DisplayName("Whitespace-only title should be rejected")
    void whitespaceTitleRejection() {
        assertThatThrownBy(() -> 
            createTestRequest(123, "   ", "Valid Body"))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Title cannot be empty");
    }
    
    @Test
    @DisplayName("Null body should be rejected")
    void nullBodyRejection() {
        assertThatThrownBy(() -> 
            ClassificationRequest.builder()
                .issueNumber(123)
                .title("Valid Title")
                .body(null)
                .availableLabels(List.of("label1"))
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Body cannot be null");
    }
    
    @Test
    @DisplayName("Empty body should be allowed")
    void emptyBodyAllowed() {
        assertThatCode(() -> 
            createTestRequest(123, "Valid Title", ""))
            .doesNotThrowAnyException();
    }
    
    @Test
    @DisplayName("Null available labels should be rejected")
    void nullAvailableLabelsRejection() {
        assertThatThrownBy(() -> 
            ClassificationRequest.builder()
                .issueNumber(123)
                .title("Valid Title")
                .body("Valid Body")
                .availableLabels(null)
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Available labels cannot be null");
    }
    
    @Test
    @DisplayName("Empty available labels should be rejected")
    void emptyAvailableLabelsRejection() {
        assertThatThrownBy(() -> 
            ClassificationRequest.builder()
                .issueNumber(123)
                .title("Valid Title")
                .body("Valid Body")
                .availableLabels(List.of())
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Available labels cannot be empty");
    }
    
    @Test
    @DisplayName("Combined text should include title and body")
    void combinedTextContent() {
        ClassificationRequest request = createTestRequest();
        String combined = request.getCombinedText();
        
        assertThat(combined).contains(TEST_ISSUE_TITLE);
        assertThat(combined).contains(TEST_ISSUE_BODY);
        assertThat(combined).contains("\n\n"); // Separator
    }
    
    @Test
    @DisplayName("Character count should be accurate")
    void characterCountAccuracy() {
        ClassificationRequest request = createTestRequest();
        int expected = TEST_ISSUE_TITLE.length() + TEST_ISSUE_BODY.length();
        
        assertThat(request.getCharacterCount()).isEqualTo(expected);
    }
    
    @Test
    @DisplayName("Minimal content detection should work")
    void minimalContentDetection() {
        // Request with sufficient content
        ClassificationRequest sufficient = createTestRequest(123, "Long title", "Long body content");
        assertThat(sufficient.hasMinimalContent()).isTrue();
        
        // Request with insufficient content
        ClassificationRequest insufficient = createTestRequest(456, "Hi", "");
        assertThat(insufficient.hasMinimalContent()).isFalse();
    }
    
    @Test
    @DisplayName("Available labels should be immutable")
    void availableLabelsImmutability() {
        List<String> originalLabels = new java.util.ArrayList<>(TEST_AVAILABLE_LABELS);
        ClassificationRequest request = ClassificationRequest.builder()
            .issueNumber(123)
            .title("Title")
            .body("Body")
            .availableLabels(originalLabels)
            .build();
        
        // Modify original list
        originalLabels.add("new-label");
        
        // Request should be unaffected
        assertThat(request.availableLabels()).hasSize(TEST_AVAILABLE_LABELS.size());
        assertThat(request.availableLabels()).doesNotContain("new-label");
    }
    
    @Test
    @DisplayName("Builder should handle null values gracefully")
    void builderNullHandling() {
        ClassificationRequest request = ClassificationRequest.builder()
            .issueNumber(123)
            .title("Title")
            .body(null) // Will be converted to empty string in builder
            .availableLabels(List.of("label1"))
            .config(null) // Will use defaults
            .build();
        
        assertThat(request.body()).isEqualTo("");
        assertThat(request.config()).isEqualTo(DEFAULT_CONFIG);
    }
}
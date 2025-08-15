package org.springaicommunity.github.ai.classification.service;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.assertj.core.api.Assertions.*;

/**
 * Edge cases and error handling tests for LabelNormalizationService.
 * 
 * <p>Tests boundary conditions and error scenarios.</p>
 */
@DisplayName("LabelNormalizationService - Edge Cases and Error Handling")
class LabelNormalization_EdgeCases_Tests extends LabelServiceTestBase {

    @Test
    @DisplayName("Should handle malformed input gracefully")
    void shouldHandleMalformedInputGracefully() {
        // Given malformed inputs (using Arrays.asList to allow null)
        List<String> malformedLabels = Arrays.asList(
            "", "   ", null, "VALID", "\t\n\r", "another-valid"
        );

        // When
        List<String> result = service.normalizeLabels(malformedLabels);

        // Then
        assertThat(result).containsExactlyInAnyOrder("valid", "another-valid");
    }

    @Test
    @DisplayName("Should handle empty frequency maps")
    void shouldHandleEmptyFrequencyMaps() {
        assertThat(service.analyzeLabelFrequency(Collections.emptyMap())).isEmpty();
        assertThat(service.analyzeLabelFrequency(null)).isEmpty();
        
        assertThat(service.identifyRareLabels(Collections.emptyMap(), 3)).isEmpty();
        assertThat(service.identifyRareLabels(null, 3)).isEmpty();
    }

    @Test
    @DisplayName("Should validate configuration")
    void shouldValidateConfiguration() {
        assertThat(service.isConfigurationValid()).isTrue();
        assertThat(service.getConfiguration()).isNotNull();
        assertThat(service.getConfiguration().labelGroups()).isNotEmpty();
        assertThat(service.getConfiguration().ignoredLabels()).isNotEmpty();
    }

    @Test
    @DisplayName("Should handle case variations correctly")
    void shouldHandleCaseVariationsCorrectly() {
        // Test various case combinations
        assertThat(service.normalizeLabel("PgVector")).isEqualTo("vector store");
        assertThat(service.normalizeLabel("PGVECTOR")).isEqualTo("vector store");
        assertThat(service.normalizeLabel("pgvector")).isEqualTo("vector store");
        assertThat(service.normalizeLabel("pgVector")).isEqualTo("vector store");
        
        assertThat(service.isIgnoredLabel("TRIAGE")).isTrue();
        assertThat(service.isIgnoredLabel("Triage")).isTrue();
        assertThat(service.isIgnoredLabel("triage")).isTrue();
    }
}
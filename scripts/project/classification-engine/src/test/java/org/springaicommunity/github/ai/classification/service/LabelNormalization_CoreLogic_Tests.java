package org.springaicommunity.github.ai.classification.service;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.junit.jupiter.params.provider.CsvSource;
import org.springaicommunity.github.ai.classification.domain.ClassificationConfig;

import java.util.*;

import static org.assertj.core.api.Assertions.*;

/**
 * Core logic tests for LabelNormalizationService (no Spring context).
 * 
 * <p>Tests fundamental label normalization behavior using plain JUnit
 * for fast execution and reliable testing.</p>
 */
@DisplayName("LabelNormalizationService - Core Logic Tests")
class LabelNormalization_CoreLogic_Tests {

    private final ClassificationConfig config = ClassificationConfig.builder()
        .labelGroups(LabelServiceTestBase.TestConfig.getTestLabelGroups())
        .ignoredLabels(LabelServiceTestBase.TestConfig.getTestIgnoredLabels())
        .build();
    private final LabelNormalizationService service = new DefaultLabelNormalizationService(config);

    @ParameterizedTest
    @CsvSource({
        "PGVECTOR, vector store",
        "' OpenAI ', model client", 
        "neo4j, data store",
        "bug, bug",
        "Enhancement, enhancement"
    })
    @DisplayName("Should normalize single labels correctly")
    void shouldNormalizeSingleLabels(String input, String expected) {
        assertThat(service.normalizeLabel(input)).isEqualTo(expected);
    }

    @ParameterizedTest
    @ValueSource(strings = {"triage", "DUPLICATE", " Status: Waiting-For-Triage ", "FOLLOW UP"})
    @DisplayName("Should handle ignored labels")
    void shouldHandleIgnoredLabels(String ignoredLabel) {
        assertThat(service.normalizeLabel(ignoredLabel)).isNull();
        assertThat(service.isIgnoredLabel(ignoredLabel)).isTrue();
    }

    @ParameterizedTest
    @CsvSource({
        "pgvector, vector store",
        "qdrant, vector store", 
        "openai, model client",
        "claude, model client",
        "mongo, data store",
        "neo4j, data store"
    })
    @DisplayName("Should map all label variants to correct groups")
    void shouldMapLabelVariantsToGroups(String variant, String expectedGroup) {
        assertThat(service.findGroupName(variant)).isEqualTo(expectedGroup);
    }

    @Test
    @DisplayName("Should handle null and empty inputs")
    void shouldHandleNullAndEmptyInputs() {
        assertThat(service.normalizeLabel(null)).isNull();
        assertThat(service.normalizeLabel("")).isNull();
        assertThat(service.normalizeLabel("   ")).isNull();
        
        assertThat(service.normalizeLabels(null)).isEmpty();
        assertThat(service.normalizeLabels(Collections.emptyList())).isEmpty();
    }

    @Test
    @DisplayName("Should validate configuration")
    void shouldValidateConfiguration() {
        assertThat(service.isConfigurationValid()).isTrue();
        assertThat(service.getConfiguration()).isNotNull();
        assertThat(service.getConfiguration().labelGroups()).isNotEmpty();
        assertThat(service.getConfiguration().ignoredLabels()).isNotEmpty();
    }

    @ParameterizedTest
    @CsvSource({
        "PgVector, vector store",
        "PGVECTOR, vector store",
        "pgvector, vector store",
        "pgVector, vector store"
    })
    @DisplayName("Should handle case variations correctly")
    void shouldHandleCaseVariations(String input, String expected) {
        assertThat(service.normalizeLabel(input)).isEqualTo(expected);
    }
}
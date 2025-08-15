package org.springaicommunity.github.ai.classification.service;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.assertj.core.api.Assertions.*;

/**
 * Python compatibility tests for LabelNormalizationService.
 * 
 * <p>Ensures Java implementation matches Python stratified_split.py behavior exactly.</p>
 */
@DisplayName("LabelNormalizationService - Python Compatibility Tests")
class LabelNormalization_PythonCompatibility_Tests extends LabelServiceTestBase {

    @Test
    @DisplayName("Should match Python normalize_labels() logic exactly")
    void shouldMatchPythonNormalizeLabelsLogic() {
        // Test case from Python stratified_split.py lines 19-33
        // Given
        List<String> pythonLabels = List.of("pgvector", "OpenAI", "Bug", "triage", "Enhancement");

        // When
        List<String> javaResult = service.normalizeLabels(pythonLabels);

        // Then - should match Python behavior exactly
        assertThat(javaResult).containsExactlyInAnyOrder("vector store", "model client", "bug", "enhancement");
    }

    @Test
    @DisplayName("Should handle Python label groups correctly")
    void shouldHandlePythonLabelGroupsCorrectly() {
        // Test all Python LABEL_GROUPS from stratified_split.py lines 13-17
        
        // Vector store group
        assertThat(service.findGroupName("pinecone")).isEqualTo("vector store");
        assertThat(service.findGroupName("weaviate")).isEqualTo("vector store");
        assertThat(service.findGroupName("chromadb")).isEqualTo("vector store");
        
        // Model client group  
        assertThat(service.findGroupName("openai")).isEqualTo("model client");
        assertThat(service.findGroupName("claude")).isEqualTo("model client");
        assertThat(service.findGroupName("ollama")).isEqualTo("model client");
        
        // Data store group
        assertThat(service.findGroupName("mongo")).isEqualTo("data store");
        assertThat(service.findGroupName("neo4j")).isEqualTo("data store");
        assertThat(service.findGroupName("oracle")).isEqualTo("data store");
    }

    @Test
    @DisplayName("Should handle Python ignored labels correctly")
    void shouldHandlePythonIgnoredLabelsCorrectly() {
        // Test all Python IGNORED_LABELS from stratified_split.py lines 8-11
        List<String> pythonIgnored = List.of(
            "triage", "duplicate", "invalid", "status: waiting-for-triage",
            "status: waiting-for-feedback", "status: backported", "follow up"
        );

        for (String ignored : pythonIgnored) {
            assertThat(service.isIgnoredLabel(ignored))
                .as("Label '%s' should be ignored", ignored)
                .isTrue();
            assertThat(service.normalizeLabel(ignored))
                .as("Label '%s' should normalize to null", ignored)
                .isNull();
        }
    }

    @Test
    @DisplayName("Should reproduce Python frequency analysis")
    void shouldReproducePythonFrequencyAnalysis() {
        // Test similar to Python label_distribution() function lines 35-39
        // Given
        List<Map<String, Object>> pythonStyleIssues = List.of(
            Map.of("normalized_labels", List.of("vector store", "bug")),
            Map.of("normalized_labels", List.of("model client", "enhancement")),
            Map.of("normalized_labels", List.of("vector store", "documentation"))
        );

        Map<Integer, List<String>> issueLabels = new HashMap<>();
        for (int i = 0; i < pythonStyleIssues.size(); i++) {
            @SuppressWarnings("unchecked")
            List<String> labels = (List<String>) pythonStyleIssues.get(i).get("normalized_labels");
            issueLabels.put(i + 1, labels);
        }

        // When
        Map<String, Integer> frequency = service.analyzeLabelFrequency(issueLabels);

        // Then
        assertThat(frequency).containsEntry("vector store", 2);
        assertThat(frequency).containsEntry("bug", 1);
        assertThat(frequency).containsEntry("model client", 1);
        assertThat(frequency).containsEntry("enhancement", 1);
        assertThat(frequency).containsEntry("documentation", 1);
    }
}
package org.springaicommunity.github.ai.classification.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springaicommunity.github.ai.classification.domain.ClassificationConfig;
import org.springaicommunity.github.ai.classification.domain.LabelGroup;
import org.springaicommunity.github.ai.collection.Issue;
import org.springaicommunity.github.ai.collection.Label;
import org.springaicommunity.github.ai.collection.Author;

import java.time.LocalDateTime;
import java.util.*;

/**
 * Base class for StratifiedSplitService tests providing common setup.
 * 
 * <p>This base class eliminates nested test class issues and provides
 * shared configuration for both unit tests and Spring integration tests.</p>
 */
@SpringJUnitConfig(StratifiedSplitServiceTestBase.TestConfig.class)
abstract class StratifiedSplitServiceTestBase {
    
    @Autowired
    protected StratifiedSplitService service;
    
    @Configuration
    static class TestConfig {
        @Bean
        public ClassificationConfig classificationConfig() {
            return ClassificationConfig.builder()
                .labelGroups(getTestLabelGroups())
                .ignoredLabels(getTestIgnoredLabels())
                .batchSize(25)
                .confidenceThreshold(0.7)
                .randomSeed(42)
                .build();
        }

        @Bean
        public LabelNormalizationService labelNormalizationService(ClassificationConfig config) {
            return new DefaultLabelNormalizationService(config);
        }

        @Bean
        public StratifiedSplitService stratifiedSplitService(LabelNormalizationService labelNormalizationService) {
            return new DefaultStratifiedSplitService(labelNormalizationService);
        }

        static List<LabelGroup> getTestLabelGroups() {
            return List.of(
                LabelGroup.of("vector store", "pinecone", "qdrant", "weaviate", "pgvector", "milvus"),
                LabelGroup.of("model client", "openai", "claude", "ollama", "gemini", "deepseek"),
                LabelGroup.of("data store", "mongo", "oracle", "neo4j", "cassandra", "mariadb")
            );
        }

        static Set<String> getTestIgnoredLabels() {
            return Set.of("triage", "duplicate", "invalid", "status: waiting-for-triage", 
                         "status: waiting-for-feedback", "status: backported", "follow up");
        }
    }
    
    // Helper methods for creating test data
    protected static List<Issue> createTestIssues() {
        return List.of(
            createIssue(1, "pgvector", "bug"),
            createIssue(2, "openai", "enhancement"),
            createIssue(3, "qdrant", "bug"),
            createIssue(4, "bug"),
            createIssue(5, "enhancement"),
            createIssue(6, "documentation"),
            createIssue(7, "question"),
            createIssue(8, "claude", "bug"),
            createIssue(9, "milvus", "enhancement"),
            createIssue(10, "bug")
        );
    }

    protected static List<Issue> createComplexTestDataset() {
        return List.of(
            createIssue(1, "pgvector", "bug", "urgent"),
            createIssue(2, "openai", "enhancement", "feature"),
            createIssue(3, "qdrant", "bug"),
            createIssue(4, "claude", "documentation"),
            createIssue(5, "milvus", "enhancement"),
            createIssue(6, "weaviate", "question"),
            createIssue(7, "ollama", "bug"),
            createIssue(8, "gemini", "enhancement"),
            createIssue(9, "bug", "critical"),
            createIssue(10, "enhancement", "nice-to-have"),
            createIssue(11, "documentation"),
            createIssue(12, "question", "help-wanted"),
            createIssue(13, "bug"),
            createIssue(14, "enhancement"),
            createIssue(15, "rare-label") // This will be rare
        );
    }

    protected static List<Issue> createPythonCompatibleDataset() {
        // Create dataset that matches Python test scenario
        return List.of(
            createIssue(1, "pgvector", "bug"),
            createIssue(2, "openai", "enhancement"),  
            createIssue(3, "qdrant", "bug"),
            createIssue(4, "claude", "documentation"),
            createIssue(5, "bug"),
            createIssue(6, "enhancement"),
            createIssue(7, "rare1"), // rare label
            createIssue(8, "rare2"), // rare label
            createIssue(9, "bug"),
            createIssue(10, "enhancement")
        );
    }

    protected static List<Issue> createLargeTestDataset(int size) {
        List<Issue> issues = new ArrayList<>();
        String[] commonLabels = {"bug", "enhancement", "documentation", "question"};
        String[] techLabels = {"pgvector", "openai", "qdrant", "claude", "milvus"};
        
        for (int i = 1; i <= size; i++) {
            String commonLabel = commonLabels[i % commonLabels.length];
            String techLabel = techLabels[i % techLabels.length];
            issues.add(createIssue(i, commonLabel, techLabel));
        }
        
        return issues;
    }

    protected static Issue createIssue(int number, String... labelNames) {
        List<Label> labels = Arrays.stream(labelNames)
            .map(name -> new Label(name, "#000000", "Test label"))
            .toList();
        
        return new Issue(
            number,
            "Test Issue " + number,
            "Test body " + number,
            "open",
            LocalDateTime.now(),
            LocalDateTime.now(),
            null,
            "https://github.com/test/test/issues/" + number,
            new Author("testuser", "test@example.com"),
            Collections.emptyList(),
            labels
        );
    }
}
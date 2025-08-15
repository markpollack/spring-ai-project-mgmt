package org.springaicommunity.github.ai.classification.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springaicommunity.github.ai.classification.domain.ClassificationConfig;
import org.springaicommunity.github.ai.classification.domain.LabelGroup;

import java.util.List;
import java.util.Set;

/**
 * Base class for LabelNormalizationService tests providing common setup.
 * 
 * <p>This base class eliminates nested test class issues and provides
 * shared configuration for both unit tests and Spring integration tests.</p>
 */
@SpringJUnitConfig(LabelServiceTestBase.TestConfig.class)
abstract class LabelServiceTestBase {
    
    @Autowired
    protected LabelNormalizationService service;
    
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

        static List<LabelGroup> getTestLabelGroups() {
            return List.of(
                LabelGroup.of("vector store", "pinecone", "qdrant", "weaviate", "typesense", "opensearch", "chromadb", "pgvector", "milvus"),
                LabelGroup.of("model client", "openai", "claude", "ollama", "gemini", "deepseek", "mistral", "moonshot", "zhipu"),
                LabelGroup.of("data store", "mongo", "oracle", "neo4j", "cassandra", "mariadb", "postgresml", "elastic search", "coherence")
            );
        }

        static Set<String> getTestIgnoredLabels() {
            return Set.of("triage", "duplicate", "invalid", "status: waiting-for-triage", 
                         "status: waiting-for-feedback", "status: backported", "follow up");
        }
    }
}
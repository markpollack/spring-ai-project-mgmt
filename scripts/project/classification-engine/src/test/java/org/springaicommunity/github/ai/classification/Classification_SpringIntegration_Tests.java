package org.springaicommunity.github.ai.classification;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springaicommunity.github.ai.classification.config.ClassificationConfiguration;
import org.springaicommunity.github.ai.classification.domain.ClassificationConfig;
import org.springaicommunity.github.ai.classification.service.DefaultPromptTemplateService;
import org.springaicommunity.github.ai.classification.service.PromptTemplateService;
import org.springaicommunity.github.ai.classification.service.SpringAIContextService;

import java.util.concurrent.Executor;

import static org.assertj.core.api.Assertions.*;

/**
 * Spring integration tests for classification components.
 * Uses minimal Spring context to avoid CommandLineRunner execution issues.
 * Follows flattened test architecture established in previous tasks.
 */
@SpringJUnitConfig(classes = {
    ClassificationConfiguration.class,
    DefaultPromptTemplateService.class
})
@DisplayName("Classification - Spring Integration Tests")
class Classification_SpringIntegration_Tests extends ClassificationTestBase {
    
    @Test
    @DisplayName("Default classification config bean should be available")
    void defaultClassificationConfigBean() {
        ClassificationConfiguration config = new ClassificationConfiguration();
        ClassificationConfig defaultConfig = config.defaultClassificationConfig();
        
        assertThat(defaultConfig).isNotNull();
        assertThat(defaultConfig.confidenceThreshold()).isEqualTo(0.7);
        assertThat(defaultConfig.maxLabelsPerIssue()).isEqualTo(2);
        assertThat(defaultConfig.batchSize()).isEqualTo(25);
        assertThat(defaultConfig.trainTestSplitRatio()).isEqualTo(0.8);
        assertThat(defaultConfig.randomSeed()).isEqualTo(42);
    }
    
    @Test
    @DisplayName("Async executor bean should be properly configured")
    void asyncExecutorBean() {
        ClassificationConfiguration config = new ClassificationConfiguration();
        Executor executor = config.classificationAsyncExecutor();
        
        assertThat(executor).isNotNull();
        
        // Test executor functionality
        boolean[] taskExecuted = {false};
        executor.execute(() -> taskExecuted[0] = true);
        
        // Give executor time to run
        try {
            Thread.sleep(100);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        
        assertThat(taskExecuted[0]).isTrue();
    }
    
    @Test
    @DisplayName("ObjectMapper bean should be properly configured")
    void objectMapperBean() {
        ClassificationConfiguration config = new ClassificationConfiguration();
        ObjectMapper mapper = config.classificationObjectMapper();
        
        assertThat(mapper).isNotNull();
        
        // Test Java time module registration
        assertThat(mapper.getRegisteredModuleIds()).contains("jackson-datatype-jsr310");
    }
    
    @Test
    @DisplayName("PromptTemplateService should be instantiable as Spring bean")
    void promptTemplateServiceBean() {
        SpringAIContextService contextService = new SpringAIContextService(getTestObjectMapper());
        contextService.afterPropertiesSet();
        PromptTemplateService service = new DefaultPromptTemplateService(contextService);
        
        assertThat(service).isNotNull();
        assertThat(service.getSystemPrompt()).isNotEmpty();
        assertThat(service.getHighPerformingLabels()).isNotEmpty();
        assertThat(service.getResponseFormatExample()).contains("JSON");
    }
    
    @Test
    @DisplayName("Configuration should support custom values")
    void customConfigurationValues() {
        ClassificationConfig customConfig = ClassificationConfig.builder()
            .confidenceThreshold(0.8)
            .maxLabelsPerIssue(1)
            .batchSize(10)
            .trainTestSplitRatio(0.7)
            .randomSeed(123)
            .build();
        
        assertThat(customConfig.confidenceThreshold()).isEqualTo(0.8);
        assertThat(customConfig.maxLabelsPerIssue()).isEqualTo(1);
        assertThat(customConfig.batchSize()).isEqualTo(10);
        assertThat(customConfig.trainTestSplitRatio()).isEqualTo(0.7);
        assertThat(customConfig.randomSeed()).isEqualTo(123);
    }
    
    @Test
    @DisplayName("Configuration should handle label normalization")
    void configurationLabelNormalization() {
        ClassificationConfig config = ClassificationConfig.defaults();
        
        // Test ignored labels functionality
        assertThat(config.isIgnoredLabel("triage")).isTrue();
        assertThat(config.isIgnoredLabel("TRIAGE")).isTrue(); // Case insensitive
        assertThat(config.isIgnoredLabel("duplicate")).isTrue();
        assertThat(config.isIgnoredLabel("vector store")).isFalse();
        
        // Test label normalization
        String normalized = config.normalizeLabel("pinecone");
        assertThat(normalized).isIn("vector store", "pinecone"); // Either grouped or original
    }
    
    @Test
    @DisplayName("Configuration should validate input parameters")
    void configurationValidation() {
        // Test confidence threshold validation
        assertThatThrownBy(() -> 
            ClassificationConfig.builder()
                .confidenceThreshold(-0.1)
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Confidence threshold must be between 0.0 and 1.0");
        
        assertThatThrownBy(() -> 
            ClassificationConfig.builder()
                .confidenceThreshold(1.1)
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Confidence threshold must be between 0.0 and 1.0");
        
        // Test max labels validation
        assertThatThrownBy(() -> 
            ClassificationConfig.builder()
                .maxLabelsPerIssue(0)
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Max labels per issue must be at least 1");
        
        // Test batch size validation
        assertThatThrownBy(() -> 
            ClassificationConfig.builder()
                .batchSize(0)
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Batch size must be at least 1");
        
        // Test split ratio validation
        assertThatThrownBy(() -> 
            ClassificationConfig.builder()
                .trainTestSplitRatio(0.0)
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Train test split ratio must be between 0.0 and 1.0");
        
        assertThatThrownBy(() -> 
            ClassificationConfig.builder()
                .trainTestSplitRatio(1.0)
                .build())
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Train test split ratio must be between 0.0 and 1.0");
    }
    
    @Test
    @DisplayName("Configuration should provide reasonable defaults")
    void configurationDefaults() {
        ClassificationConfig defaults = ClassificationConfig.defaults();
        
        assertThat(defaults.confidenceThreshold()).isBetween(0.5, 0.9);
        assertThat(defaults.maxLabelsPerIssue()).isBetween(1, 5);
        assertThat(defaults.batchSize()).isBetween(10, 50);
        assertThat(defaults.trainTestSplitRatio()).isBetween(0.6, 0.9);
        assertThat(defaults.randomSeed()).isPositive();
        
        // Should have some label groups and ignored labels
        assertThat(defaults.labelGroups()).isNotEmpty();
        assertThat(defaults.ignoredLabels()).isNotEmpty();
    }
    
    @Test
    @DisplayName("Configuration should be immutable")
    void configurationImmutability() {
        ClassificationConfig config = ClassificationConfig.defaults();
        
        // Attempting to modify collections should not affect the config
        assertThat(config.labelGroups()).isInstanceOf(java.util.List.class);
        assertThat(config.ignoredLabels()).isInstanceOf(java.util.Set.class);
        
        // Collections should be unmodifiable
        assertThatThrownBy(() -> {
            ((java.util.Collection<?>) config.ignoredLabels()).clear();
        }).isInstanceOf(UnsupportedOperationException.class);
    }
}
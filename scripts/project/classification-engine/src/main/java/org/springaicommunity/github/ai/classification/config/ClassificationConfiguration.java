package org.springaicommunity.github.ai.classification.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springaicommunity.github.ai.classification.domain.ClassificationConfig;
import org.springaicommunity.github.ai.classification.service.PromptTemplateService;
import org.springaicommunity.github.ai.classification.service.PythonCompatiblePromptTemplateService;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;

/**
 * Spring configuration for the classification engine components.
 * 
 * <p>Provides essential beans for LLM-based classification including:
 * <ul>
 *   <li>Default classification configuration</li>
 *   <li>Async executor for non-blocking operations</li>
 *   <li>JSON mapper for response parsing</li>
 * </ul>
 */
@Configuration
public class ClassificationConfiguration {
    
    /**
     * Default classification configuration matching Python's exact settings.
     */
    @Bean
    public ClassificationConfig defaultClassificationConfig() {
        return ClassificationConfig.builder()
            .confidenceThreshold(0.6)  // Python used 0.6 threshold
            .maxLabelsPerIssue(5)      // Python allowed multiple labels  
            .batchSize(25)
            .trainTestSplitRatio(0.8)
            .randomSeed(42)
            .build();
    }
    
    /**
     * Python-compatible prompt template service for EXACT parity.
     */
    @Bean
    @Primary
    public PromptTemplateService pythonCompatiblePromptTemplateService() {
        return new PythonCompatiblePromptTemplateService();
    }
    
    /**
     * Async executor for classification operations.
     */
    @Bean
    public Executor classificationAsyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(2);
        executor.setMaxPoolSize(5);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("classification-");
        executor.initialize();
        return executor;
    }
    
    /**
     * ObjectMapper configured for classification response parsing.
     */
    @Bean
    public ObjectMapper classificationObjectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JavaTimeModule());
        return mapper;
    }
}
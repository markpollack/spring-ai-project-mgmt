package org.springaicommunity.github.ai.classification.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springaicommunity.github.ai.classification.domain.ClassificationConfig;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
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
     * Default classification configuration with proven settings from Python implementation.
     */
    @Bean
    public ClassificationConfig defaultClassificationConfig() {
        return ClassificationConfig.builder()
            .confidenceThreshold(0.7)
            .maxLabelsPerIssue(2)
            .batchSize(25)
            .trainTestSplitRatio(0.8)
            .randomSeed(42)
            .build();
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
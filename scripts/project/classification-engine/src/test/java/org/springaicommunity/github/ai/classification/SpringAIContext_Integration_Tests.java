package org.springaicommunity.github.ai.classification;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springaicommunity.github.ai.classification.config.ClassificationConfiguration;
import org.springaicommunity.github.ai.classification.service.DefaultPromptTemplateService;
import org.springaicommunity.github.ai.classification.service.SpringAIContextService;

import static org.assertj.core.api.Assertions.*;

/**
 * Tests for Spring AI context integration in classification prompts.
 * Uses minimal Spring context to avoid CommandLineRunner execution issues.
 */
@SpringJUnitConfig(classes = {
    ClassificationConfiguration.class,
    SpringAIContextService.class,
    DefaultPromptTemplateService.class
})
@DisplayName("Spring AI Context - Integration Tests")
class SpringAIContext_Integration_Tests extends ClassificationTestBase {
    
    @Test
    @DisplayName("SpringAI context service should load successfully")
    void contextServiceLoadsSuccessfully() {
        SpringAIContextService service = new SpringAIContextService(getTestObjectMapper());
        service.afterPropertiesSet();
        
        // Should have loaded some context
        assertThat(service.getProjectStructureContext()).isNotEmpty();
        
        // Should recognize high-performing labels with rich context
        assertThat(service.hasRichContext("advisors")).isTrue();
        assertThat(service.hasRichContext("vector store")).isTrue();
        
        // Should provide enriched descriptions
        String advisorsDesc = service.getEnrichedLabelDescription("advisors");
        assertThat(advisorsDesc).contains("advisor pattern implementations");
        assertThat(advisorsDesc).contains("spring-ai-client-chat");
        assertThat(advisorsDesc).contains("Advisor");
    }
    
    @Test
    @DisplayName("Prompt template should include Spring AI context")
    void promptTemplateIncludesSpringAIContext() {
        SpringAIContextService contextService = new SpringAIContextService(getTestObjectMapper());
        contextService.afterPropertiesSet();
        DefaultPromptTemplateService promptService = new DefaultPromptTemplateService(contextService);
        
        var request = createTestRequest();
        String prompt = promptService.buildClassificationPrompt(request);
        
        assertThat(prompt).isNotEmpty();
        
        // Should contain Spring AI project context
        assertThat(prompt).contains("Spring AI Project Context");
        assertThat(prompt).contains("spring-ai-model");
        
        // Should contain enhanced label descriptions for high-priority labels
        assertThat(prompt).contains("High-Priority Technical Labels with Spring AI Context");
        
        // Should include rich context for available labels that have it
        if (request.availableLabels().contains("advisors")) {
            assertThat(prompt).contains("advisor pattern implementations");
        }
        
        // Should still contain conservative classification instructions
        assertThat(prompt).contains("Focus on technical content");
        assertThat(prompt).contains("confidence >= 0.7");
        assertThat(prompt).contains("maximum 2 labels");
    }
    
    @Test
    @DisplayName("Context service should handle missing files gracefully")
    void contextServiceHandlesMissingFilesGracefully() {
        SpringAIContextService service = new SpringAIContextService(getTestObjectMapper());
        // Don't call initialize() to test graceful handling
        
        // Should provide fallback values
        assertThat(service.hasRichContext("advisors")).isFalse();
        assertThat(service.getEnrichedLabelDescription("advisors")).isEqualTo("Technical label: advisors");
        assertThat(service.getProjectStructureContext()).isEmpty();
    }
    
    @Test
    @DisplayName("Context service should identify labels with rich context")
    void contextServiceIdentifiesLabelsWithRichContext() {
        SpringAIContextService service = new SpringAIContextService(getTestObjectMapper());
        service.afterPropertiesSet();
        
        var labelsWithContext = service.getLabelsWithRichContext();
        
        // Should identify common Spring AI labels
        assertThat(labelsWithContext).isNotEmpty();
        
        // Should exclude labels marked as "Not found in project codebase"
        for (String label : labelsWithContext) {
            var context = service.getLabelContext(label);
            assertThat(context).isPresent();
            assertThat(context.get().description()).doesNotContain("Not found in project codebase");
        }
    }
    
    @Test
    @DisplayName("Label context should provide complete Spring AI information")
    void labelContextProvidesCompleteInformation() {
        SpringAIContextService service = new SpringAIContextService(getTestObjectMapper());
        service.afterPropertiesSet();
        
        var advisorsContext = service.getLabelContext("advisors");
        assertThat(advisorsContext).isPresent();
        
        var context = advisorsContext.get();
        assertThat(context.label()).isEqualTo("advisors");
        assertThat(context.description()).contains("advisor pattern implementations");
        assertThat(context.relevantModules()).contains("spring-ai-client-chat");
        assertThat(context.packages()).contains("org.springframework.ai.chat.client.advisor");
        assertThat(context.keyClasses()).contains("Advisor");
        assertThat(context.exampleProblemPhrases()).contains("advisor not being called");
    }
    
    @Test
    @DisplayName("Enhanced prompt should maintain token efficiency")
    void enhancedPromptMaintainsTokenEfficiency() {
        SpringAIContextService contextService = new SpringAIContextService(getTestObjectMapper());
        contextService.afterPropertiesSet();
        DefaultPromptTemplateService promptService = new DefaultPromptTemplateService(contextService);
        
        var request = createTestRequest();
        String prompt = promptService.buildClassificationPrompt(request);
        
        // Should include rich context but limit project context to reasonable length
        assertThat(prompt).contains("Spring AI Project Context");
        
        // Project context should be truncated for token efficiency
        int contextStart = prompt.indexOf("## Spring AI Project Context");
        int contextEnd = prompt.indexOf("## Available Labels", contextStart);
        if (contextStart >= 0 && contextEnd >= 0) {
            String projectContext = prompt.substring(contextStart, contextEnd);
            // Should be reasonable length (not the full file)
            assertThat(projectContext.length()).isLessThan(3000);
        }
    }
}
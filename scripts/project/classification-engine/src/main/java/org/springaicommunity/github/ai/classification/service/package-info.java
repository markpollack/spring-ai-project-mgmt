/**
 * Service layer for LLM-based issue classification.
 * 
 * <p>Contains the core business logic for:</p>
 * 
 * <ul>
 *   <li>{@code LLMClient} - Abstraction for LLM providers (Claude, OpenAI, etc.)</li>
 *   <li>{@code LLMClassificationService} - Main classification orchestration</li>
 *   <li>{@code LabelNormalizationService} - Label grouping and filtering</li>
 *   <li>{@code StratifiedSplitService} - Train/test data splitting</li>
 *   <li>{@code BatchProcessingService} - Efficient batch processing</li>
 * </ul>
 * 
 * <p>Services are designed to be Spring-managed beans with constructor-based
 * dependency injection for better testability.</p>
 */
package org.springaicommunity.github.ai.classification.service;
/**
 * Domain models and data structures for issue classification.
 * 
 * <p>This package contains domain objects and DTOs used throughout the classification system:</p>
 * 
 * <ul>
 *   <li>{@code ClassificationResult} - Results from LLM classification</li>
 *   <li>{@code LabelPrediction} - Individual label predictions with confidence</li>
 *   <li>{@code ClassificationMetrics} - Precision, recall, and F1 metrics</li>
 *   <li>{@code EvaluationReport} - Comprehensive evaluation results</li>
 *   <li>{@code LabelGroup} - Configuration for label grouping</li>
 * </ul>
 * 
 * <p>These models are designed to be immutable where possible (using records) and
 * to work seamlessly with JSON serialization for API integration.</p>
 */
package org.springaicommunity.github.ai.classification.domain;
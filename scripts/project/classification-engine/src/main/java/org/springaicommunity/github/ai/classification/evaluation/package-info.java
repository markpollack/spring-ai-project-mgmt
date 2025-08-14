/**
 * Evaluation metrics and reporting for classification results.
 * 
 * <p>Provides comprehensive evaluation capabilities for LLM-based classification:</p>
 * 
 * <ul>
 *   <li>{@code LLMClassificationEvaluator} - Main evaluation service</li>
 *   <li>{@code MetricsCalculator} - Precision, recall, F1 calculation</li>
 *   <li>{@code ReportSerializer} - JSON and Markdown report generation</li>
 *   <li>{@code ConfusionMatrix} - Custom confusion matrix for LLM predictions</li>
 * </ul>
 * 
 * <p>The evaluation system is designed to work with LLM outputs rather than
 * traditional ML model predictions, using pure Java implementations for
 * metrics calculation.</p>
 */
package org.springaicommunity.github.ai.classification.evaluation;
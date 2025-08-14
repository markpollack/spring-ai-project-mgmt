/**
 * GitHub Issue Classification Engine - LLM-based classification for Spring AI project issues.
 * 
 * <p>This package provides a comprehensive classification system that uses Large Language Models
 * (Claude) to classify GitHub issues into technical categories. The system is designed to 
 * achieve high precision and recall rates through careful prompt engineering and evaluation.</p>
 * 
 * <h3>Key Features:</h3>
 * <ul>
 *   <li>LLM-based classification using Claude Code SDK</li>
 *   <li>Batch processing for efficient LLM API usage</li>
 *   <li>Comprehensive evaluation metrics (precision, recall, F1)</li>
 *   <li>Label normalization and stratified data splitting</li>
 *   <li>JSON and Markdown report generation</li>
 * </ul>
 * 
 * <h3>Architecture:</h3>
 * <pre>
 * classification-engine
 * ├── domain      - Data models and DTOs
 * ├── service     - Business logic and LLM integration
 * ├── config      - Configuration and Spring setup
 * ├── util        - Utility classes and helpers
 * └── evaluation  - Metrics calculation and reporting
 * </pre>
 * 
 * <h3>Dependencies:</h3>
 * <ul>
 *   <li>collection-library - For Issue, Label, and Author models</li>
 *   <li>Claude Code SDK - For LLM classification (abstracted via LLMClient interface)</li>
 *   <li>Spring Framework - For dependency injection and configuration</li>
 *   <li>Jackson - For JSON processing</li>
 * </ul>
 * 
 * @version 1.0.0
 * @since 1.0.0
 */
package org.springaicommunity.github.ai.classification;
# Classification Engine

LLM-based classification engine for GitHub issues in the Spring AI project.

## Overview

This module provides comprehensive classification capabilities for GitHub issues using Large Language Models (Claude). It achieves high precision and recall through careful prompt engineering, batch processing, and systematic evaluation.

## Features

- **LLM-based Classification**: Uses Claude Code SDK for intelligent issue categorization
- **Batch Processing**: Efficient processing of issues in batches of 25 for optimal LLM performance
- **Evaluation Metrics**: Comprehensive precision, recall, and F1 score calculation
- **Label Normalization**: Intelligent grouping and filtering of labels
- **Report Generation**: JSON and Markdown reports for analysis and documentation
- **Provider Abstraction**: LLMClient interface supports multiple LLM providers

## Architecture

```
classification-engine/
├── domain/         # Data models and DTOs
├── service/        # Business logic and LLM integration
├── config/         # Spring configuration
├── util/           # Utility classes
└── evaluation/     # Metrics and reporting
```

## Dependencies

- **collection-library**: For Issue, Label, and Author models
- **Claude Code SDK**: For LLM classification (abstracted via LLMClient)
- **Spring Framework**: For dependency injection
- **Jackson**: For JSON processing

## Key Classes

### Service Layer
- `LLMClient` - Abstraction for LLM providers
- `LLMClassificationService` - Main classification orchestration
- `LabelNormalizationService` - Label processing and grouping
- `StratifiedSplitService` - Train/test data splitting

### Domain Models
- `ClassificationResult` - LLM classification results
- `EvaluationReport` - Comprehensive evaluation metrics
- `LabelPrediction` - Individual label predictions with confidence

### Evaluation
- `LLMClassificationEvaluator` - Main evaluation service
- `MetricsCalculator` - Pure Java metrics calculation
- `ReportSerializer` - Multi-format report generation

## Usage

```java
// Inject the classification service
@Autowired
private LLMClassificationService classificationService;

// Classify issues
List<ClassificationResult> results = classificationService.classify(issues);

// Evaluate results
EvaluationReport report = evaluator.evaluate(results, groundTruth);

// Generate reports
String jsonReport = reportSerializer.toJson(report);
String markdownReport = reportSerializer.toMarkdown(report);
```

## Testing

This module follows strict testing protocols:

- **NEVER use @SpringBootTest** (triggers CommandLineRunner in parent app)
- **Use plain JUnit** for pure Java logic
- **Use @SpringJUnitConfig** with minimal context for Spring integration
- **Mock LLMClient interface** (no MockedStatic needed)

## Configuration

See `ClassificationProperties` for available configuration options.

## Performance

- Target: 82.1% F1 score (matching Python baseline)
- Batch size: 25 issues per LLM call
- Processing: <10 seconds for 100 issues (excluding LLM calls)
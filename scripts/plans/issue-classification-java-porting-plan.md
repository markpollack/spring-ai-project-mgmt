# GitHub Issue Classification - Java Porting Plan

## Date: 2025-08-14
## Phase: PORTING FROM PYTHON TO JAVA
## Version: 1.3
## Current Status: Planning - Ready to Implement
## Last Update: Added LLM client abstraction and evaluation report patterns for better testability and extensibility

### Background
The Python-based GitHub issue classification system achieved **82.1% F1 score** with 76.6% precision and 88.5% recall on Spring AI issues. This plan guides the systematic porting of this classification system to Java as a new Maven module within the existing multi-module project structure.

### Objectives
- Port the proven Python classification algorithms to Java
- Create a reusable `classification-engine` module
- Maintain or exceed the 82.1% F1 score benchmark
- Integrate seamlessly with existing `collection-library` module
- Provide comprehensive testing and documentation

## MANDATORY PROCESS REQUIREMENTS

**IMPORTANT**: All implementation tasks MUST follow the established process:
1. **CRITICAL**: Read `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/plans/consolidated-learnings-issue-classification.md` before starting ANY task
2. Review previous task learnings before starting each task
3. Update checkboxes in this plan as subtasks are completed
4. Create learnings document after each task following the pattern: `task-N-[name]-learnings.md`
5. Commit changes after each task with descriptive messages
6. **NEVER use @SpringBootTest** in any test class - follow safety protocols from consolidated learnings

**Base Reference Document**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/plans/consolidated-learnings-issue-classification.md`
**Learnings Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/plans/learnings/`

## Scope

### In Scope (MVP)
- **LLM-Based Classification**: Integration with Claude Code for classification
- **Prompt Management**: Port classification prompts from Python
- **Keyword-Based Fallback**: Basic keyword classification as backup
- **Label Management**: Normalization, grouping, and filtering
- **Data Splitting**: Stratified train/test split (80/20)
- **Evaluation Metrics**: Precision, recall, F1 scores (micro/macro)
- **Batch Processing**: Process issues in batches of 25 for LLM
- **Integration**: Full integration with `collection-library` data models
- **Testing**: Comprehensive unit and integration tests
- **Data Migration**: Tools to convert Python test data to Java

### Out of Scope (Future Phases)
- Web UI for classification management
- Real-time classification API
- Database persistence layer
- REST API endpoints
- Spring AI integration (using existing Claude Code integration instead)

## Development Setup

### **PROJECT LOCATION**
**CRITICAL**: All implementation work happens in:
```
/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/
```

### Module Structure
```
github-issues-collection/ (parent)
├── collection-library/     (existing - provides Issue, Label, Author models)
├── collection-app/         (existing - command-line collection app)
└── classification-engine/  (NEW - classification algorithms and evaluation)
```

### Architecture Overview
```
classification-engine Module
    ↓ depends on
collection-library (Issue, Label, Comment models)
    ↓ provides
Classification Services → collection-app (optional integration)
```

## Critical Reference Materials

### Claude Code Java SDK
**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/claude-code-java-sdk`
**Symbolic Link Created**: For easy reference during implementation

**Key Components for Classification**:
- `Query.java` - Simple API for one-shot queries: `Query.execute(prompt)`
- `CLIOptions.java` - Configuration for model, prompts, tokens, timeout
- `QueryResult.java` - Response handling with metadata and cost analysis
- `ClaudeSDKClient.java` - Interactive session management
- Built on **zt-exec** for robust process management
- Uses **Jackson** for JSON processing (same as our project)

**Integration Pattern**:
```java
// Example classification with Claude
QueryResult result = Query.execute(classificationPrompt, CLIOptions.builder()
    .model("claude-3-sonnet-20240229")
    .systemPrompt(loadPromptFromResources())
    .maxTokens(2000)
    .timeout(Duration.ofSeconds(30))
    .build());
```

### Python Implementation Reference
**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/issue-analysis-archive/`

**Key Python Scripts to Port**:
- `scripts/stratified_split.py` - Label normalization and data splitting
- `scripts/batch_processor.py` - Batch processing logic (25 issues per LLM call)
- `scripts/evaluate_predictions.py` - Metrics computation
- `prompts/improved_classification_prompt.md` - LLM classification prompt

### Existing Java Infrastructure
**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/collection-library/`

**Available Models**:
- `Issue.java` - GitHub issue record
- `Label.java` - Label record
- `Author.java` - Author information
- `Comment.java` - Issue comments
- `IssueCollectionService.java` - Issue loading service

### Test Data
**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/issue-analysis-archive/data/`
- `issues/stratified_split/train_set.json` - Training data
- `issues/stratified_split/test_set.json` - Test data
- `labels.json` - Valid labels list

## Math Libraries and Evaluation Approach

### CRITICAL: LLM-Based vs Traditional ML Evaluation

**This system uses LLM-based classification, NOT traditional ML models**. This fundamental difference affects our evaluation approach:

#### Traditional ML Approach (NOT our case):
- Train a model (SVM, Random Forest, etc.)
- Model produces predictions directly
- Use evaluation libraries like Tribuo's `LabelEvaluator`
- Libraries expect `Model` objects and structured predictions

#### Our LLM-Based Approach:
- No model training - using Claude's zero-shot/few-shot capabilities
- Classifications via prompts sent to Claude Code SDK
- Predictions returned as JSON from LLM responses
- Need custom evaluation that works with LLM outputs

### Math Library Recommendations

Given the LLM-based nature and simple math requirements (basic arithmetic and set operations), we recommend:

#### **Primary Approach: Pure Java Implementation**
**No external math library needed** - The metrics calculation is straightforward:
```java
// Simple precision, recall, F1 calculation
double precision = tp / (double)(tp + fp);
double recall = tp / (double)(tp + fn);
double f1 = 2.0 * precision * recall / (precision + recall);
```

**Benefits:**
- No additional dependencies
- Full control over implementation
- Matches Python logic exactly
- Simple to test and debug

#### **Optional: Apache Commons Math 3** 
```xml
<dependency>
    <groupId>org.apache.commons</groupId>
    <artifactId>commons-math3</artifactId>
    <version>3.6.1</version>
</dependency>
```
**Use only if needed for:**
- Statistical distributions
- Advanced aggregations
- Matrix operations (if extending beyond current needs)

#### **NOT Recommended: Tribuo Classification Core**
While Tribuo is excellent for traditional ML, its `LabelEvaluator` and evaluation framework:
- Requires Tribuo `Model` objects (we don't have these)
- Expects structured model predictions (not LLM JSON responses)
- Is designed for the "train-then-evaluate" paradigm
- Would require significant adaptation to work with LLM outputs

### Improved Design Patterns

#### LLM Client Abstraction
```java
public interface LLMClient {
    ClassificationResponse classify(ClassificationRequest request);
}

@Service
public class ClaudeLLMClient implements LLMClient {
    @Override
    public ClassificationResponse classify(ClassificationRequest request) {
        // Internally uses Query.execute()
        QueryResult result = Query.execute(request.toPrompt(), buildOptions());
        return parseResponse(result);
    }
}

// Easy to mock in tests - no MockedStatic needed!
@Mock
private LLMClient mockLLMClient;
```

#### Evaluation Report Pattern
```java
public record EvaluationReport(
    double microF1,
    double macroPrecision,
    double macroRecall, 
    double macroF1,
    Map<String, LabelStats> perLabelMetrics,
    Duration executionTime,
    Instant timestamp
) {
    // Serializable to both JSON and Markdown
}

public interface ReportSerializer {
    String toJson(EvaluationReport report);
    String toMarkdown(EvaluationReport report);
    String toTerminalTable(EvaluationReport report);
}
```

#### Custom Evaluation Implementation
```java
@Service
public class LLMClassificationEvaluator {
    private final LLMClient llmClient;
    
    public LLMClassificationEvaluator(LLMClient llmClient) {
        this.llmClient = llmClient;  // Dependency injection
    }
    
    public EvaluationReport evaluate(
            List<Issue> issues,
            Map<Integer, Set<String>> groundTruth) {
        
        Instant start = Instant.now();
        
        // Process with abstracted LLM client
        List<ClassificationResponse> predictions = 
            llmClient.classify(prepareBatch(issues));
        
        // Calculate metrics...
        
        return new EvaluationReport(
            microF1, macroPrecision, macroRecall, macroF1,
            perLabelMetrics,
            Duration.between(start, Instant.now()),
            Instant.now()
        );
    }
}

## Implementation Tasks

### Task 1: Module Setup and Configuration (2 hours)

**Pre-Task**:
- [ ] Review existing module structure in `collection-library` and `collection-app`
- [ ] Understand parent POM configuration and dependency management
- [ ] Plan module dependencies and structure

**Objective**: Create new `classification-engine` module with proper Maven configuration

**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/`

1. Module Creation:
- [ ] Create `classification-engine` directory structure
- [ ] Create module `pom.xml` with Spring Boot dependencies
- [ ] Add module to parent POM's `<modules>` section
- [ ] Configure Java 17 and UTF-8 encoding

2. Package Structure:
- [ ] Create `org.springaicommunity.github.ai.classification` base package
- [ ] Create subpackages: `domain`, `service`, `config`, `util`, `evaluation`
- [ ] Add `package-info.java` files for documentation
- [ ] Create `README.md` for module documentation

3. Dependencies Configuration:
- [ ] Add dependency on `collection-library` module
- [ ] Add Spring Boot starter dependencies
- [ ] Add Jackson for JSON processing (for LLM response parsing)
- [ ] Optional: Add Apache Commons Math 3 (only if needed for extended statistics)
- [ ] Add testing dependencies (JUnit 5, AssertJ, Mockito)

**Verification**: Module compiles, tests run, appears in parent build

**Post-Task**:
- [ ] Create `scripts/plans/learnings/task-1-module-setup-learnings.md`
- [ ] Commit: `git commit -m "Task 1: Classification engine module setup - COMPLETE"`

### Task 2: Domain Models and Data Structures (3 hours)

**Pre-Task**:
- [ ] Read `scripts/plans/learnings/task-1-module-setup-learnings.md`
- [ ] Review Python data structures in classification scripts
- [ ] Study existing `Issue` and `Label` records in collection-library

**Objective**: Create Java domain models for classification system

**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/src/main/java/org/springaicommunity/github/ai/classification/domain/`

1. Classification Models:
- [ ] Create `ClassificationResult` record with issue number, predictions, explanation
- [ ] Create `LabelPrediction` record with label name and confidence score
- [ ] Create `ClassificationMetrics` class for precision/recall/F1
- [ ] Create `LabelStatistics` class for per-label metrics

2. Configuration Models:
- [ ] Create `LabelGroup` record for label grouping (e.g., vector stores)
- [ ] Create `ClassificationConfig` class for runtime configuration
- [ ] Create `ExcludedLabels` configuration class
- [ ] Create `DataSplit` record for train/test split info

3. Processing Models:
- [ ] Create `BatchProcessingRequest` for batch configuration
- [ ] Create `EvaluationReport` for comprehensive metrics
- [ ] Create `ConfusionMatrix` for detailed analysis
- [ ] Add builder patterns where appropriate

**Verification**: All models compile, have proper equals/hashCode/toString

**Post-Task**:
- [ ] Create `scripts/plans/learnings/task-2-domain-models-learnings.md`
- [ ] Commit: `git commit -m "Task 2: Domain models and data structures - COMPLETE"`

### Task 3: Label Normalization Service (4 hours)

**Pre-Task**:
- [ ] Read `scripts/plans/learnings/task-2-domain-models-learnings.md`
- [ ] Study Python `stratified_split.py` normalization logic
- [ ] Review label groupings and ignored labels

**Objective**: Port label normalization and grouping logic from Python

**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/src/main/java/org/springaicommunity/github/ai/classification/service/`

1. Core Service Implementation:
- [ ] Create `LabelNormalizationService` interface
- [ ] Create `DefaultLabelNormalizationService` implementation
- [ ] Port label grouping logic (vector stores, model clients, data stores)
- [ ] Implement ignored labels filtering (triage, duplicate, etc.)

2. Configuration Support:
- [ ] Create `LabelMappingConfig` with YAML/properties support
- [ ] Define default label groups from Python constants
- [ ] Add configurable ignored labels set
- [ ] Support runtime configuration updates

3. Normalization Logic:
- [ ] Implement case-insensitive label matching
- [ ] Handle label variants (e.g., "pgvector" → "vector store")
- [ ] Support custom label mappings
- [ ] Add label frequency analysis

4. Testing:
- [ ] Create comprehensive unit tests
- [ ] Test all label group mappings
- [ ] Verify ignored labels are filtered
- [ ] Test edge cases and null handling

**Verification**: Service correctly normalizes all Python test cases

**Post-Task**:
- [ ] Create `scripts/plans/learnings/task-3-label-normalization-learnings.md`
- [ ] Commit: `git commit -m "Task 3: Label normalization service - COMPLETE"`

### Task 4: Stratified Split Implementation (4 hours)

**Pre-Task**:
- [ ] Read `scripts/plans/learnings/task-3-label-normalization-learnings.md`
- [ ] Analyze Python stratified split algorithm
- [ ] Understand rare label handling (< 3 occurrences)

**Objective**: Implement stratified train/test split maintaining label distribution

**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/src/main/java/org/springaicommunity/github/ai/classification/service/`

1. Split Service Implementation:
- [ ] Create `StratifiedSplitService` interface
- [ ] Create `DefaultStratifiedSplitService` implementation
- [ ] Port 80/20 split algorithm from Python
- [ ] Implement rare label detection and handling

2. Algorithm Implementation:
- [ ] Count label frequencies across all issues
- [ ] Identify rare labels (< 3 occurrences)
- [ ] Ensure rare labels go to training set
- [ ] Maintain label distribution in test set

3. Split Utilities:
- [ ] Create split statistics calculator
- [ ] Add distribution validation
- [ ] Implement reproducible splitting (with seed)
- [ ] Add split quality metrics

4. Integration:
- [ ] Integrate with `LabelNormalizationService`
- [ ] Support custom split ratios
- [ ] Add comprehensive logging
- [ ] Create unit and integration tests

**Verification**: Split maintains label distribution, matches Python output

**Post-Task**:
- [ ] Create `scripts/plans/learnings/task-4-stratified-split-learnings.md`
- [ ] Commit: `git commit -m "Task 4: Stratified split implementation - COMPLETE"`

### Task 5: LLM-Based Classification Core (6 hours)

**Pre-Task**:
- [ ] Read `scripts/plans/learnings/task-4-stratified-split-learnings.md`
- [ ] Study Python classification approach (LLM prompts, not keywords)
- [ ] Review Claude Code SDK integration patterns

**Objective**: Implement LLM-based classification with abstracted LLM client

**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/src/main/java/org/springaicommunity/github/ai/classification/service/`

1. LLM Client Abstraction:
- [ ] Create `LLMClient` interface to abstract LLM provider
- [ ] Define `ClassificationRequest` and `ClassificationResponse` DTOs
- [ ] Create `ClaudeLLMClient` implementation wrapping Claude SDK
- [ ] Design interface to support future providers (OpenAI, Spring AI, etc.)

2. LLM Classification Service:
- [ ] Create `LLMClassificationService` using `LLMClient` interface
- [ ] Load classification prompt from resources (`improved_classification_prompt.md`)
- [ ] Implement batch preparation for LLM (25 issues per call)
- [ ] Use dependency injection for `LLMClient` (easily mockable)

3. Claude Implementation:
- [ ] Implement `ClaudeLLMClient` with Query.execute() internally
- [ ] Configure CLIOptions with appropriate model and token limits
- [ ] Parse JSON response from Claude containing predicted labels
- [ ] Handle API errors and timeouts gracefully

4. Response Processing:
- [ ] Parse LLM JSON response to extract predicted labels
- [ ] Extract confidence scores from LLM response
- [ ] Apply threshold-based filtering (0.7 default)
- [ ] Enforce maximum labels per issue constraint (2-3)

5. Classification Pipeline:
- [ ] Create batch JSON preparation for LLM input
- [ ] Implement retry logic for failed LLM calls
- [ ] Add result aggregation from multiple batches
- [ ] Include explanation extraction from LLM response

6. Testing:
- [ ] Mock `LLMClient` interface (no MockedStatic needed!)
- [ ] Create test cases from Python examples
- [ ] Verify classification accuracy
- [ ] Test edge cases and empty inputs
- [ ] Test provider switching capability

**Verification**: Classifications match Python output for test cases

**Post-Task**:
- [ ] Create `scripts/plans/learnings/task-5-classification-core-learnings.md`
- [ ] Commit: `git commit -m "Task 5: Classification algorithm core - COMPLETE"`

### Task 6: Batch Processing Service (3 hours)

**Pre-Task**:
- [ ] Read `scripts/plans/learnings/task-5-classification-core-learnings.md`
- [ ] Review Python batch_processor.py logic
- [ ] Understand memory optimization strategies

**Objective**: Implement efficient batch processing for large datasets

**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/src/main/java/org/springaicommunity/github/ai/classification/service/`

1. Batch Processing Service:
- [ ] Create `BatchProcessingService` interface
- [ ] Implement configurable batch sizes (default 25)
- [ ] Add memory-efficient streaming processing
- [ ] Support progress tracking and callbacks

2. Batch Optimization:
- [ ] Extract only necessary fields for classification
- [ ] Implement batch result aggregation
- [ ] Add parallel batch processing option
- [ ] Support resume from failure

3. High-Performing Labels:
- [ ] Port high-performing label list from Python
- [ ] Add configurable label filtering
- [ ] Implement label performance tracking
- [ ] Support dynamic label selection

4. Integration:
- [ ] Integrate with classification service
- [ ] Add batch statistics collection
- [ ] Implement comprehensive error handling
- [ ] Create unit tests with mock data

**Verification**: Can process 100+ issues in batches efficiently

**Post-Task**:
- [ ] Create `scripts/plans/learnings/task-6-batch-processing-learnings.md`
- [ ] Commit: `git commit -m "Task 6: Batch processing service - COMPLETE"`

### Task 7: LLM-Aware Evaluation Metrics Engine (4 hours)

**Pre-Task**:
- [ ] Read `scripts/plans/learnings/task-6-batch-processing-learnings.md`
- [ ] Study Python evaluation scripts thoroughly
- [ ] Understand micro/macro averaging differences
- [ ] Review LLM vs Traditional ML evaluation differences in Math Libraries section

**Objective**: Implement evaluation metrics for LLM-based classification outputs

**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/src/main/java/org/springaicommunity/github/ai/classification/evaluation/`

1. LLM-Aware Metrics Calculator:
- [ ] Create `LLMMetricsCalculator` class (pure Java, no ML library dependencies)
- [ ] Implement simple precision, recall, F1 computation with basic arithmetic
- [ ] Add micro-averaged metrics (overall performance)
- [ ] Add macro-averaged metrics (per-label average)

2. LLM Classification Evaluator:
- [ ] Create `LLMClassificationEvaluator` service
- [ ] Parse LLM JSON responses from Claude SDK
- [ ] Implement custom confusion matrix for LLM predictions
- [ ] Add per-label performance analysis using set operations
- [ ] Support filtered evaluation (exclude labels)

3. Statistical Analysis (Pure Java):
- [ ] Port true positive/false positive/false negative counting using Set operations
- [ ] Implement label-wise statistics with HashMap/TreeMap
- [ ] Add support for confidence thresholds from LLM responses
- [ ] Create performance comparison tools

4. Report Generation:
- [ ] Create `EvaluationReport` record with comprehensive metrics
- [ ] Include micro/macro F1, per-label stats, execution duration
- [ ] Implement `ReportSerializer` for multiple output formats
- [ ] Support JSON serialization for programmatic access
- [ ] Support Markdown generation for human-readable reports
- [ ] Include ASCII tables for terminal display
- [ ] Design for future GUI/dashboard integration

5. Testing:
- [ ] Create test cases with known metrics
- [ ] Mock `LLMClient` interface for testing
- [ ] Verify against Python evaluation results
- [ ] Test report serialization to JSON and Markdown
- [ ] Test edge cases (empty predictions, no labels, etc.)
- [ ] Validate arithmetic calculations

**Verification**: Metrics match Python evaluation for same test data

**Post-Task**:
- [ ] Create `scripts/plans/learnings/task-7-evaluation-metrics-learnings.md`
- [ ] Commit: `git commit -m "Task 7: Evaluation metrics engine - COMPLETE"`

### Task 8: Integration with Collection Library (3 hours)

**Pre-Task**:
- [ ] Read `scripts/plans/learnings/task-7-evaluation-metrics-learnings.md`
- [ ] Review collection-library APIs and models
- [ ] Plan integration points and data flow

**Objective**: Seamlessly integrate classification with existing collection infrastructure

**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/src/main/java/org/springaicommunity/github/ai/classification/integration/`

1. Data Loading Integration:
- [ ] Create `IssueDataLoader` using `IssueCollectionService`
- [ ] Implement batch loading from JSON files
- [ ] Add streaming support for large datasets
- [ ] Handle data format conversions

2. Model Adapters:
- [ ] Create adapters between collection and classification models
- [ ] Implement Issue to classification input conversion
- [ ] Add Label extraction and normalization
- [ ] Support metadata preservation

3. Service Facade:
- [ ] Create `ClassificationFacade` for simplified API
- [ ] Implement end-to-end classification workflow
- [ ] Add configuration management
- [ ] Include progress reporting

4. Spring Configuration:
- [ ] Create Spring Boot auto-configuration
- [ ] Add conditional beans based on classpath
- [ ] Configure default properties
- [ ] Support profile-based configuration

**Verification**: Can load and classify issues from collection-library

**Post-Task**:
- [ ] Create `scripts/plans/learnings/task-8-integration-learnings.md`
- [ ] Commit: `git commit -m "Task 8: Collection library integration - COMPLETE"`

### Task 9: Test Data Migration (4 hours)

**Pre-Task**:
- [ ] Read `scripts/plans/learnings/task-8-integration-learnings.md`
- [ ] Inventory Python test data files
- [ ] Plan migration strategy and validation

**Objective**: Migrate Python test data and create Java test infrastructure

**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/src/test/`

1. Test Data Migration:
- [ ] Copy train/test JSON files to test resources
- [ ] Create Java test data loaders
- [ ] Validate data integrity after loading
- [ ] Add test data documentation

2. Test Fixtures:
- [ ] Create classification test fixtures
- [ ] Add golden test cases from Python
- [ ] Include edge cases and error scenarios
- [ ] Create parameterized test data

3. Integration Tests:
- [ ] Create end-to-end classification tests
- [ ] Add performance benchmarks
- [ ] Test with real Spring AI issue data
- [ ] Verify metrics match Python baseline

4. Test Utilities:
- [ ] Create test data generators
- [ ] Add assertion helpers for classifications
- [ ] Implement test report comparisons
- [ ] Create debugging utilities

**Verification**: All test data loads correctly, tests pass

**Post-Task**:
- [ ] Create `scripts/plans/learnings/task-9-test-migration-learnings.md`
- [ ] Commit: `git commit -m "Task 9: Test data migration - COMPLETE"`

### Task 10: Validation and Performance Testing (4 hours)

**Pre-Task**:
- [ ] Read all previous learnings documents
- [ ] Prepare performance testing environment
- [ ] Set up metrics comparison framework

**Objective**: Validate Java implementation matches Python performance

**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/`

1. Accuracy Validation:
- [ ] Run classification on full test set
- [ ] Compare with Python classification results
- [ ] Validate F1 score within 2% of 82.1%
- [ ] Document any discrepancies

2. Performance Testing:
- [ ] Benchmark classification speed
- [ ] Test memory usage with large datasets
- [ ] Verify batch processing efficiency
- [ ] Compare with Python performance

3. Documentation:
- [ ] Create comprehensive README
- [ ] Add API documentation (Javadoc)
- [ ] Include usage examples
- [ ] Document configuration options

4. Final Integration:
- [ ] Update parent project documentation
- [ ] Add module to CI/CD pipeline
- [ ] Create release notes
- [ ] Plan future enhancements

**Verification**: F1 score ≥ 80%, processes 100 issues in < 10 seconds

**Post-Task**:
- [ ] Create `scripts/plans/learnings/task-10-validation-learnings.md`
- [ ] Commit: `git commit -m "Task 10: Validation and performance testing - COMPLETE"`
- [ ] Create final summary document

## Testing Strategy

### Unit Testing
- Test each service in isolation
- Mock external dependencies
- Achieve 80%+ code coverage
- Use parameterized tests for algorithms

### Integration Testing
- Test complete classification pipeline
- Use real test data from Python
- Verify metrics computation
- Test Spring Boot integration

### Performance Testing
- Benchmark against Python baseline
- Test with varying dataset sizes
- Monitor memory usage
- Optimize bottlenecks

## Success Criteria

### Functional Requirements
- ✅ Achieve F1 score within 2% of Python (82.1% ± 2%)
- ✅ Maintain precision > 74% and recall > 86%
- ✅ Support all labels from Python implementation
- ✅ Process 100+ issues efficiently

### Technical Requirements
- ✅ Clean module architecture
- ✅ Full Spring Boot integration
- ✅ Comprehensive test coverage
- ✅ Complete documentation

### Performance Requirements
- ✅ Process 100 issues in < 10 seconds (excluding I/O)
- ✅ Support datasets with 1000+ issues
- ✅ Memory efficient batch processing
- ✅ Configurable performance tuning

## Risk Mitigation

### Technical Risks
- **Risk**: Algorithm differences between Python and Java
- **Mitigation**: Extensive testing with same test data

- **Risk**: Performance degradation
- **Mitigation**: Profiling and optimization, parallel processing

- **Risk**: Integration complexity
- **Mitigation**: Clear interfaces, comprehensive testing

### Schedule Risks
- **Risk**: Underestimated complexity
- **Mitigation**: Incremental implementation, regular validation

## Timeline

### Week 1 (Tasks 1-3)
- Module setup and configuration
- Domain models
- Label normalization

### Week 2 (Tasks 4-6)
- Stratified split
- Classification core
- Batch processing

### Week 3 (Tasks 7-9)
- Evaluation metrics
- Integration
- Test migration

### Week 4 (Task 10)
- Validation
- Performance testing
- Documentation

**Total Duration**: 4 weeks (approximately 40 hours of development)

## Next Steps

1. Review this plan with stakeholders
2. Set up development environment
3. Begin with Task 1: Module Setup
4. Follow mandatory process requirements
5. Track progress with regular commits

---

**Document Version**: 1.0
**Last Updated**: 2025-08-14
**Author**: GitHub Issue Classification Porting Team
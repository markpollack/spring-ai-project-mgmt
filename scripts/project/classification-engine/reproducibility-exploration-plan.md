# Reproducibility Exploration Plan - GitHub Issue Classification

## Project Overview

This document outlines the definitive experiment to resolve the performance gap between Python's 82.1% F1 score and Java's 66.7-74.3% F1 score in GitHub issue classification. The plan implements a rigorous 3-mode experiment matrix to test whether Python's superiority comes from evaluation-time filtering benefits or represents a fundamental methodological advantage.

## MANDATORY PROCESS REQUIREMENTS

### Critical Discovery Context
Our investigation revealed that **Python excludes 12 labels during evaluation**, not just `bug` and `enhancement`:

**Excluded Labels (12 total):**
1. `bug`, `enhancement` (low precision: 40%, 29.7%)
2. `question`, `help wanted`, `good first issue`, `epic` (subjective/judgmental)  
3. `status: backported`, `status: to-discuss`, `follow up`, `status: waiting-for-feedback`, `for: backport-to-1.0.x`, `next priorities` (process-driven)

**Methodological Difference:**
- **Python**: Predict on ALL labels → Filter 12 during evaluation → 82.1% F1
- **Java**: Exclude 12 before prediction → Direct evaluation → 66.7% F1

### Hypothesis to Test
**Context Loss Hypothesis**: Python achieves higher F1 because the model benefits from context provided by all 12 excluded labels during prediction, even though they're filtered out during evaluation.

### Expected Outcome
If hypothesis is correct, Mode B (Python approach) should significantly outperform Mode D (Java approach) due to richer prediction context.

## Experiment Design

### Label Space Definitions

**L_FULL (Full Label Space):** All 116+ labels from `labels.json`
- Used by Python for prediction
- Provides complete context for disambiguation

**L_REDUCED_PRAG (Pragmatic Reduced Space):** L_FULL minus 12 excluded labels
- Used by Python for evaluation only
- Used by Java for both prediction and evaluation

### Experiment Matrix

| Mode | Predict On | Evaluate On | Purpose | Expected F1 |
|------|------------|-------------|---------|-------------|
| **A** | L_FULL | L_FULL | True full-task baseline | ~70% |
| **B** | L_FULL | L_REDUCED | Python approach (hypothesis: highest) | **~82%** |
| **D** | L_REDUCED | L_REDUCED | Java approach (current) | ~67% |

**Mode C Excluded**: Predicting on L_REDUCED but evaluating on L_FULL is nonsensical (can't predict excluded labels).

## ✅ COMPLETED TASKS

### ✅ Phase 0: Foundation (Previous Work)
**Status**: COMPLETE ✅
- Full Java classification system with both LLM and rule-based approaches
- Real Claude AI integration with JSON parsing
- Comprehensive Spring AI context integration
- Performance baseline established: 74.3% F1 (LLM), 66.7% F1 (real data)

## CURRENT IMPLEMENTATION PHASE

### 🎯 Phase 1: Infrastructure Setup (Day 1)

#### 1.1 Label Space Configuration
**Status**: ✅ COMPLETE
- **File**: `LabelSpaceConfiguration.java`
- Defines L_FULL and L_REDUCED_PRAG spaces
- Versioned label sets (`LFULL_v1`, `LRED_PRAG_v1`)
- Support for experiment mode routing

#### 1.2 Post-Processing Filter (In Progress)
**Status**: 🔄 IN PROGRESS
- **File**: `PostProcessingFilter.java`
- Implements evaluation-time label filtering for Mode B
- Preserves all prediction data while filtering labels

#### 1.3 Experiment Matrix Test Framework
**Status**: ⏳ PENDING
- **File**: `ExperimentMatrixTest.java`
- JUnit 5 parameterized tests for all 3 modes
- Integrated with `mvn test` workflow
- Artifact generation for analysis

### 🎯 Phase 2: Metrics Enhancement (Day 1-2)

#### 2.1 Comprehensive Metrics Calculator
**Status**: ⏳ PENDING
- **File**: `ComprehensiveMetricsCalculator.java`
- Extends existing F1 calculation
- Adds: Macro-F1, Jaccard (IoU), Subset Accuracy, Label Coverage
- Per-label F1 scores for detailed analysis

#### 2.2 Results Collection System
**Status**: ⏳ PENDING
- **Files**: `ExperimentResultsCollector.java`
- CSV export for external analysis
- JSON export for programmatic processing
- Structured artifact storage in `target/experiments/`

### 🎯 Phase 3: Statistical Analysis (Day 2-3)

#### 3.1 Bootstrap Confidence Testing
**Status**: ⏳ PENDING
- **File**: `MetricsBootstrapTest.java`
- Bootstrap sampling (n=1000) for confidence intervals
- Paired comparisons with statistical significance testing
- Mode B vs Mode D comparison (key hypothesis test)

#### 3.2 Variance Control
**Status**: ⏳ PENDING
- Multiple seeds (42, 43, 44) for variance measurement
- Deterministic classification with temperature=0
- Cross-run consistency validation

### 🎯 Phase 4: Execution & Analysis (Day 3)

#### 4.1 Experiment Execution
**Status**: ⏳ PENDING
- Run all 3 modes × 3 seeds = 9 total experiments
- Use identical test dataset (111 issues from `test_set.json`)
- Generate comprehensive metrics for each run

#### 4.2 Report Generation
**Status**: ⏳ PENDING
- **File**: `reproducibility-results.md` (auto-generated)
- Statistical comparison of all modes
- Hypothesis validation results
- Production deployment recommendations

## Implementation Architecture

### New Files Required (Minimal Set)
1. ✅ `LabelSpaceConfiguration.java` - Label space management
2. 🔄 `PostProcessingFilter.java` - Mode B filtering
3. ⏳ `ExperimentMatrixTest.java` - Main experiment runner
4. ⏳ `ComprehensiveMetricsCalculator.java` - Enhanced metrics
5. ⏳ `MetricsBootstrapTest.java` - Statistical analysis

### Existing Files Enhanced
- `ClaudeLLMClient.java` - No changes needed (already supports label lists)
- `ClassificationRequest.java` - No changes needed
- `UnifiedClassificationService.java` - Minor extension for mode support

### Test Integration
```bash
# Run all experiments
mvn test -Dtest=ExperimentMatrixTest

# Run statistical analysis
mvn test -Dtest=MetricsBootstrapTest

# Generate artifacts
ls target/experiments/
```

## Data Specifications

### Test Dataset
- **Source**: `/home/mark/project-mgmt/spring-ai-project-mgmt/issues/stratified_split/test_set.json`
- **Size**: 111 real Spring AI GitHub issues
- **Identical to Python evaluation**: Ensures fair comparison

### Ground Truth Handling
- **Mode A**: Use all ground truth labels from test_set.json
- **Mode B & D**: Filter ground truth to exclude 12 problematic labels
- **Consistent filtering**: Same labels excluded from both predictions and ground truth

### Artifact Structure
```
target/experiments/
├── mode_A/
│   ├── seed_42/
│   │   ├── predictions.csv
│   │   ├── metrics.json
│   │   └── run_config.json
│   └── seed_43/...
├── mode_B/...
├── mode_D/...
└── summary/
    ├── comparison_B_vs_D.json
    ├── bootstrap_confidence.json
    └── final_report.md
```

## Success Criteria

### Primary Hypothesis Test
**✅ Success**: Mode B significantly outperforms Mode D (p < 0.05)
**❌ Failure**: No significant difference between Mode B and Mode D

### Performance Targets
- **Mode B**: Achieve ≥80% F1 (close to Python's 82.1%)
- **Mode D**: Achieve ~67% F1 (matching current Java baseline)
- **Mode A**: Establish true full-task baseline (likely ~70%)

### Statistical Rigor
- **Confidence Intervals**: 95% CI for all metrics
- **Significance Testing**: Bootstrap p-values < 0.05
- **Effect Size**: Cohen's d ≥ 0.5 for meaningful difference

### Reproducibility
- **Deterministic**: Identical results across multiple runs with same seed
- **Documented**: Complete methodology documentation
- **Automated**: Full integration with CI/CD pipeline

## Risk Mitigation

### Technical Risks
1. **Claude API Rate Limits**: Use conservative request pacing
2. **Context Length Limits**: Monitor token usage per request
3. **JSON Parsing Failures**: Robust error handling with fallbacks

### Methodological Risks  
1. **Test Set Contamination**: Verify no overlap with training data
2. **Threshold Optimization**: Use fixed thresholds, not test-set optimized
3. **Selection Bias**: Use complete test set, no cherry-picking

### Resource Constraints
1. **Execution Time**: ~3 hours for full matrix (9 experiments × 111 issues)
2. **Token Costs**: Estimated ~$50 for complete execution
3. **Storage**: ~100MB for all artifacts and logs

## Expected Outcomes & Implications

### If Hypothesis Confirmed (Mode B >> Mode D)
**Conclusion**: Python's 82.1% F1 is legitimate, achieved through better context utilization
**Recommendation**: Adopt post-processing approach in Java for production
**Implementation**: Predict on L_FULL, filter for business requirements

### If Hypothesis Rejected (Mode B ≈ Mode D)  
**Conclusion**: Context benefit is minimal, Java approach is optimal for reduced task
**Recommendation**: Continue with current Java pre-processing approach
**Implementation**: Focus on improving reduced-space classification

### If Mode A Dominates
**Conclusion**: Full-task approach is superior, label exclusion is counterproductive
**Recommendation**: Re-evaluate business requirements for label exclusion
**Implementation**: Deploy full-label classification with confidence thresholds

## Timeline & Milestones

### Day 1: Infrastructure
- ✅ LabelSpaceConfiguration.java
- 🔄 PostProcessingFilter.java  
- ⏳ ExperimentMatrixTest.java (basic structure)

### Day 2: Implementation  
- ⏳ ComprehensiveMetricsCalculator.java
- ⏳ Complete ExperimentMatrixTest.java
- ⏳ Execute initial test runs

### Day 3: Analysis
- ⏳ MetricsBootstrapTest.java
- ⏳ Full experiment execution
- ⏳ Generate final report

## Integration with Existing Work

### Builds Upon
- Complete Java classification system (Tasks 1-6)
- Real Claude AI integration 
- Comprehensive testing framework
- Performance analysis methodology

### Extends
- Evaluation metrics (adds Macro-F1, Jaccard, etc.)
- Experimental rigor (bootstrap testing)
- Methodological understanding (3-mode comparison)

### Delivers
- Definitive answer to Python vs Java performance gap
- Production-ready deployment guidance  
- Reproducible experimental framework
- Academic-quality evaluation methodology

## Conclusion

This reproducibility exploration will definitively resolve whether Python's 82.1% F1 score represents:
1. **Legitimate superiority** through better context utilization, or
2. **Methodological artifact** from evaluation filtering

The experiment design ensures rigorous testing while building directly on our existing codebase, requiring minimal new implementation while delivering maximum insight into the fundamental question of classification methodology.
# Python-Java Classification Parity Plan

## Date: 2025-08-16
## Status: Active - Fresh Start Based on Validated Baseline  
## Python Baseline: 82.1% F1 Score (CONFIRMED ✅)
## Note: Plan consolidated - removed redundant mode-based experiments

> **📋 SINGLE SOURCE OF TRUTH**: This plan replaces all previous classification plans. Outdated mode A/B/C/D experiments archived to avoid rabbit holes.

## Executive Summary

After validating the Python baseline, we now have a clear path to Java parity. The 82.1% F1 score is achieved through **LLM-based classification with post-processing label filtering**, not through rule-based algorithms as initially thought.

## Validated Python Baseline (2025-08-16)

### Confirmed Results
- **Unfiltered LLM Results**: 70.7% F1 (63.2% precision, 80.3% recall)
- **Filtered Results**: **82.1% F1** (76.6% precision, 88.5% recall)
- **Performance Boost**: +11.4 F1 points from excluding 12 problematic labels

### Classification Method
- **Primary**: LLM-based (Claude AI) batch processing
- **Data**: 111 test issues from stratified split
- **Output**: `conservative_full_classification.json`
- **Evaluation**: Post-processing filter during metrics calculation

### The 12 Excluded Labels
**Original problematic labels:**
- `bug`, `enhancement`

**Subjective/Judgmental labels:**
- `question`, `help wanted`, `good first issue`, `epic`

**Process-Driven labels:**
- `status: backported`, `status: to-discuss`, `follow up`, `status: waiting-for-feedback`, `for: backport-to-1.0.x`, `next priorities`

## Java Parity Strategy

### Current Java Status
✅ **LLM Classification**: Java already has LLM-based classification with Spring AI + Claude
✅ **Test Data**: Same 111 issues available for classification
✅ **Infrastructure**: Classification engine module exists
❌ **Post-Processing Filter**: Missing the critical 12-label exclusion during evaluation

### Required Implementation

#### Phase 1: Post-Processing Filter Implementation
- [ ] Create Java evaluation service that matches Python's filtering logic
- [ ] Implement identical 12-label exclusion during metrics calculation
- [ ] Ensure filter is applied to both predictions and ground truth
- [ ] Test filter implementation against Python's excluded label list

#### Phase 2: Full Evaluation Run
- [ ] Run Java LLM classification on complete 111-issue test set
- [ ] Apply post-processing filter to Java results
- [ ] Calculate micro/macro averaged metrics
- [ ] Generate per-label performance analysis

#### Phase 3: Parity Analysis
- [ ] Compare Java filtered results against Python's 82.1% baseline
- [ ] Identify any performance gaps
- [ ] Document specific differences in implementation
- [ ] Generate recommendations for achieving full parity

#### Phase 4: Optimization (If Needed)
- [ ] Address any identified performance gaps
- [ ] Fine-tune Java LLM prompts if necessary
- [ ] Optimize response parsing and handling
- [ ] Validate final parity achievement

## Success Criteria

### Primary Success (Parity Achievement)
- **Java Filtered F1 Score**: ≥ 82.0% (within 0.1% of Python baseline)
- **Precision**: ≥ 76.0% (within 0.6% of Python baseline)  
- **Recall**: ≥ 88.0% (within 0.5% of Python baseline)

### Secondary Success (Process Quality)
- **Methodology Identical**: Same 12-label exclusion approach
- **Data Identical**: Same 111 test issues processed
- **Metrics Identical**: Same micro/macro averaging calculations
- **Documentation Complete**: Full comparison analysis documented

## Technical Implementation Notes

### Post-Processing Filter Requirements
```java
// Labels to exclude during evaluation
Set<String> EXCLUDED_LABELS = Set.of(
    // Original problematic
    "bug", "enhancement",
    // Subjective/Judgmental  
    "question", "help wanted", "good first issue", "epic",
    // Process-Driven
    "status: backported", "status: to-discuss", "follow up",
    "status: waiting-for-feedback", "for: backport-to-1.0.x", "next priorities"
);
```

### Evaluation Process
1. Run LLM classification on 111 test issues
2. Filter predictions: remove excluded labels from predicted sets
3. Filter ground truth: remove excluded labels from actual label sets  
4. Calculate metrics on filtered datasets
5. Compare against Python's validated baseline

## Risk Mitigation

### High-Risk Areas
- **LLM Response Variability**: Java and Python may get different Claude responses
- **JSON Parsing Differences**: Different parsing might affect label extraction
- **Prompt Differences**: Java prompts might not match Python prompts exactly

### Mitigation Strategies
- Use same test data set to minimize LLM variability
- Validate JSON parsing against known good examples
- Document and compare prompts between implementations
- Focus on post-filtering as the primary success factor

## Timeline Estimate

- **Phase 1**: 1-2 days (post-processing filter implementation)
- **Phase 2**: 1 day (full evaluation run)
- **Phase 3**: 1 day (parity analysis)
- **Phase 4**: 1-3 days (optimization if needed)

**Total Estimated Duration**: 4-7 days

## File Locations

### Plan Documents (Consolidated)
- **Primary Plan**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/plans/python-java-parity-plan.md` (this file - SINGLE SOURCE OF TRUTH)
- **Critical Discovery**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/CRITICAL-DISCOVERY-PYTHON-VS-JAVA.md`
- **Archived Plans**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/plans/archived/` (outdated plans moved here)

### Python Baseline Validation
- **Unfiltered Evaluation**: `evaluate_predictions.py` → 70.7% F1
- **Filtered Evaluation**: `evaluate_filtered_predictions.py` → 82.1% F1  
- **Summary Report**: `evaluation_summary.md`
- **Prediction Data**: `conservative_full_classification.json`

### Java Implementation Target
- **Module**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine/`
- **Tests**: `src/test/java/org/springaicommunity/github/ai/classification/`
- **Services**: `src/main/java/org/springaicommunity/github/ai/classification/service/`

## Next Actions

1. **Immediate**: Implement post-processing filter in Java evaluation service
2. **Short-term**: Run complete evaluation with filtering applied
3. **Medium-term**: Analyze parity results and optimize if needed
4. **Long-term**: Document final parity achievement and lessons learned

---
*Last Updated: 2025-08-16*
*Python Baseline Validated: ✅ 82.1% F1*
*Status: Ready for Implementation*
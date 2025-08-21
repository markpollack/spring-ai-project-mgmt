# Java Claude SDK Debugging Plan

## Date: 2025-08-18
## Status: ACTIVE - Debugging 111-Issue Coverage Gap
## Current Performance: 85/111 issues classified (76.6% coverage), 77.2% F1 score (94% parity)
## Goal: Achieve 95%+ coverage (105+ issues) while maintaining performance

> **📋 PURPOSE**: Systematic debugging plan to identify and resolve issues preventing full 111-issue classification coverage using the Claude Code Java SDK.

## Executive Summary

After achieving 94% parity with Python baseline (77.2% vs 82.1% F1), we discovered coverage gaps in the Java implementation. While the 85 successfully classified issues demonstrate strong performance, 26 issues remain unclassified due to:
- Empty responses from certain batches
- Duplicate predictions requiring deduplication
- Potential Claude SDK or API limitations

This plan provides a systematic approach to identify root causes and implement solutions.

## Current State Analysis

### Achieved Results ✅
- **85 unique predictions** generated from 95 raw predictions
- **77.2% F1 score** with Python's 12-label filtering
- **94.0% parity** with Python's 82.1% baseline
- **Strong performance metrics**: 84.7% precision, 70.9% recall
- **Prompt bug fixed**: Removed file output instruction causing JSON failures

### Issues Identified 🔍
- **Coverage Gap**: 26/111 issues never classified (23.4% missing)
- **Duplicate Processing**: 10 duplicate predictions from retry logic
- **Batch Failures**: Some batches returned empty responses
- **Inconsistent Success**: Variable batch success rates

### Performance Impact
```
Target: 111/111 issues classified (100% coverage)
Current: 85/111 issues classified (76.6% coverage)
Gap: 26 missing issues requiring investigation
```

## Root Cause Hypotheses

### 1. Prompt Size Issues 📏
**Hypothesis**: Large batch prompts (140-180KB) exceed Claude's practical limits
- **Evidence**: Earlier logs showed batch size correlation with failures
- **Investigation**: Test various prompt sizes and identify thresholds
- **Mitigation**: Adaptive batch sizing based on content length

### 2. Claude SDK Connection Issues 🔌
**Hypothesis**: SDK doesn't handle connection failures gracefully
- **Evidence**: Empty responses suggest complete invocation failure
- **Investigation**: Deep dive into SDK error handling and timeout behavior
- **Mitigation**: Enhanced error handling, retry logic, connection monitoring

### 3. JSON Parsing Edge Cases 📝
**Hypothesis**: Despite prompt fix, some responses still fail JSON extraction
- **Evidence**: Previous 3/4 batch JSON parsing failures before prompt fix
- **Investigation**: Analyze raw responses from failed batches
- **Mitigation**: Robust JSON extraction with multiple fallback strategies

### 4. Rate Limiting and API Issues ⏱️
**Hypothesis**: Claude API has rate limits or transient issues not properly handled
- **Evidence**: Sporadic failures rather than consistent patterns
- **Investigation**: Monitor API response times and error patterns
- **Mitigation**: Exponential backoff, circuit breaker patterns

## Five-Phase Debugging Implementation

### Phase 1: Enhanced Logging and Error Capture 🔍
**Priority**: IMMEDIATE
**Goal**: Understand exactly what's failing and why

#### 1.1 Create DebugClaudeCodeWrapperService.java
- [x] **Location**: `src/main/java/org/.../service/DebugClaudeCodeWrapperService.java`
- [ ] **Features**:
  - Extend ClaudeCodeWrapperService with comprehensive logging
  - Capture all raw responses including error messages  
  - Log prompt sizes, response times, and failure reasons
  - Save all intermediate files for post-mortem analysis
  - Track SDK state throughout request lifecycle

#### 1.2 Create BatchFailureAnalysisTest.java
- [ ] **Location**: `src/test/java/org/.../BatchFailureAnalysisTest.java`
- [ ] **Features**:
  - Analyze patterns in failed vs successful batches
  - Check prompt size correlation with failure rates
  - Identify specific issues that consistently fail
  - Generate failure pattern reports
  - Test edge cases that might break processing

### Phase 2: SDK Deep Dive and Testing 🔧
**Priority**: HIGH
**Goal**: Identify Claude SDK limitations and fix core issues

#### 2.1 Create ClaudeSDKDebugTest.java
- [ ] **Location**: `src/test/java/org/.../ClaudeSDKDebugTest.java`
- [ ] **Features**:
  - Test SDK directly with various prompt sizes (10KB, 50KB, 100KB, 150KB+)
  - Test connection handling and timeout behavior
  - Verify OutputFormat.JSON behavior with edge cases
  - Test error recovery and retry logic
  - Benchmark response times across different scenarios

#### 2.2 SDK Source Code Investigation and Fixes
- [ ] **Target**: `/home/mark/claude/bud/experiments/spring-ai-agents/supporting-repos/claude-code-java-sdk`
- [ ] **Investigation Areas**:
  - Review `ClaudeCliApi.java` connection and error handling
  - Analyze `QueryResult.java` response processing
  - Check `OutputFormat.JSON` implementation details
  - Examine timeout and retry mechanisms
  - Review exception handling and propagation
- [ ] **Local Development Workflow**:
  ```bash
  # Navigate to SDK source
  cd /home/mark/claude/bud/experiments/spring-ai-agents/supporting-repos/claude-code-java-sdk
  
  # Make changes to SDK source
  # Test changes locally
  mvn clean install
  
  # Update project to use modified SDK
  cd /home/mark/project-mgmt/spring-ai-project-mgmt/scripts/project/classification-engine
  mvn clean compile -DskipTests
  ```

#### 2.3 Enhance ClaudeCodeWrapperService Error Handling
- [ ] **Target**: `src/main/java/org/.../service/ClaudeCodeWrapperService.java`
- [ ] **Improvements**:
  - Add comprehensive exception handling for all SDK error types
  - Implement retry logic with exponential backoff (3 attempts)
  - Add circuit breaker for persistent failures
  - Implement graceful degradation for partial failures
  - Enhanced logging for debugging SDK issues

### Phase 3: Batch Processing Improvements 📦
**Priority**: MEDIUM
**Goal**: Improve reliability and coverage through smarter processing

#### 3.1 Create AdaptiveBatchProcessor.java
- [ ] **Location**: `src/main/java/org/.../service/AdaptiveBatchProcessor.java`
- [ ] **Features**:
  - Dynamically adjust batch size based on prompt size
  - Smart batching: group smaller issues together
  - Batch retry mechanism for failed batches
  - Track and skip consistently failing issues
  - Progressive batch size reduction for failures

#### 3.2 Implement Checkpointing System
- [ ] **Target**: `src/main/java/org/.../service/CheckpointService.java`
- [ ] **Features**:
  - Save progress after each successful batch
  - Allow resumption from last successful batch
  - Prevent duplicate processing across runs
  - Metadata tracking for debugging
  - Recovery from partial failures

### Phase 4: Alternative Approaches 🔄
**Priority**: LOW
**Goal**: Provide fallback options for edge cases

#### 4.1 Create DirectClaudeAPIService.java
- [ ] **Location**: `src/main/java/org/.../service/DirectClaudeAPIService.java`
- [ ] **Features**:
  - Bypass Claude Code CLI and use HTTP API directly
  - Compare performance and reliability with CLI approach
  - Test with same prompts that fail with CLI
  - Alternative for SDK compatibility issues

#### 4.2 Create FallbackClassificationService.java
- [ ] **Location**: `src/main/java/org/.../service/FallbackClassificationService.java`
- [ ] **Features**:
  - Use smaller model (haiku) for failed batches
  - Reduce batch size to 1 for problematic issues
  - Try alternative prompt formats
  - Last resort processing for edge cases

### Phase 5: Validation and Monitoring 📊
**Priority**: MEDIUM
**Goal**: Ensure comprehensive coverage and prevent regressions

#### 5.1 Create ComprehensiveValidationTest.java
- [ ] **Location**: `src/test/java/org/.../ComprehensiveValidationTest.java`
- [ ] **Features**:
  - Verify all 111 issues get processed
  - Check for data corruption in responses
  - Validate JSON structure consistency
  - Compare with Python baseline behavior
  - Generate coverage reports

#### 5.2 Create PerformanceMonitoringService.java
- [ ] **Location**: `src/main/java/org/.../service/PerformanceMonitoringService.java`
- [ ] **Features**:
  - Track success rates per batch
  - Monitor token usage and costs
  - Generate detailed failure reports
  - Identify patterns in failures
  - Performance regression detection

## Implementation Tasks

### Immediate Tasks (Phase 1)
- [ ] **Task 1.1**: Create DebugClaudeCodeWrapperService with enhanced logging
- [ ] **Task 1.2**: Create BatchFailureAnalysisTest to identify patterns
- [ ] **Task 1.3**: Run analysis on current failure data
- [ ] **Task 1.4**: Generate initial failure pattern report

### High Priority Tasks (Phase 2)
- [ ] **Task 2.1**: Create ClaudeSDKDebugTest for SDK deep dive
- [ ] **Task 2.2**: Test prompt size limits and identify thresholds
- [ ] **Task 2.3**: Enhance error handling in ClaudeCodeWrapperService
- [ ] **Task 2.4**: Implement retry logic with exponential backoff

### Medium Priority Tasks (Phase 3)
- [ ] **Task 3.1**: Create AdaptiveBatchProcessor for smart batching
- [ ] **Task 3.2**: Implement checkpointing system
- [ ] **Task 3.3**: Create ComprehensiveValidationTest
- [ ] **Task 3.4**: Run full validation test suite

### Low Priority Tasks (Phase 4)
- [ ] **Task 4.1**: Create DirectClaudeAPIService as SDK alternative
- [ ] **Task 4.2**: Create FallbackClassificationService for edge cases
- [ ] **Task 4.3**: Test alternative approaches
- [ ] **Task 4.4**: Performance comparison analysis

## Success Metrics

### Primary Goals
- [ ] **Coverage**: Achieve 95%+ issue classification (105+ out of 111 issues)
- [ ] **Performance**: Maintain or improve 77.2% F1 score
- [ ] **Reliability**: <5% batch failure rate
- [ ] **Consistency**: No duplicate predictions

### Secondary Goals
- [ ] **Efficiency**: Optimize batch sizes for maximum throughput
- [ ] **Cost**: Minimize token usage while maintaining quality
- [ ] **Robustness**: Handle edge cases gracefully
- [ ] **Documentation**: Comprehensive failure analysis and solutions

## Technical Implementation Details

### File Structure
```
src/main/java/org/springaicommunity/github/ai/classification/
├── service/
│   ├── DebugClaudeCodeWrapperService.java      [Phase 1.1]
│   ├── AdaptiveBatchProcessor.java             [Phase 3.1]
│   ├── CheckpointService.java                  [Phase 3.2]
│   ├── DirectClaudeAPIService.java             [Phase 4.1]
│   ├── FallbackClassificationService.java     [Phase 4.2]
│   └── PerformanceMonitoringService.java      [Phase 5.2]

src/test/java/org/springaicommunity/github/ai/classification/
├── BatchFailureAnalysisTest.java              [Phase 1.2]
├── ClaudeSDKDebugTest.java                     [Phase 2.1]
└── ComprehensiveValidationTest.java           [Phase 5.1]
```

### Configuration Updates
- [ ] **application.yaml**: Add debugging configuration
- [ ] **logback.xml**: Enhanced logging for SDK operations
- [ ] **pom.xml**: Add monitoring dependencies if needed

### SDK Investigation Points
1. **Connection Management**: How SDK handles connection lifecycle
2. **Timeout Behavior**: Default vs custom timeout handling
3. **Error Propagation**: How SDK errors bubble up to application
4. **JSON Output**: Reliability of OutputFormat.JSON mode
5. **Rate Limiting**: SDK's built-in rate limiting mechanisms

### Claude Code SDK Source Location 🔧
- **Source Path**: `/home/mark/claude/bud/experiments/spring-ai-agents/supporting-repos/claude-code-java-sdk`
- **Symlink**: `/home/mark/project-mgmt/spring-ai-project-mgmt/scripts/claude-code-java-sdk`
- **Local Development**: Changes can be made directly and reinstalled via local Maven publish
- **Investigation Focus**: 
  - `ClaudeCliApi` connection handling
  - `QueryResult` processing and error states
  - `OutputFormat.JSON` implementation
  - Timeout and retry mechanisms
  - Error handling and exception propagation

## Risk Mitigation Strategies

### High-Risk Areas
1. **SDK Breaking Changes**: New SDK version may have different behavior
   - **Mitigation**: Pin SDK version, comprehensive testing
2. **API Rate Limits**: Hitting Claude API limits
   - **Mitigation**: Exponential backoff, request spacing
3. **Prompt Engineering**: Subtle prompt changes affecting results
   - **Mitigation**: Strict prompt versioning, regression testing

### Contingency Plans
1. **If SDK Issues Persist**: Switch to direct HTTP API approach
2. **If Batch Processing Fails**: Fall back to individual issue processing
3. **If Performance Degrades**: Use smaller model for problematic cases

## Progress Tracking

### Phase 1 Progress
- [ ] DebugClaudeCodeWrapperService created
- [ ] BatchFailureAnalysisTest created  
- [ ] Initial failure analysis completed
- [ ] Root cause hypothesis validated/refuted

### Phase 2 Progress
- [ ] ClaudeSDKDebugTest created
- [ ] SDK limitations identified
- [ ] Error handling enhanced
- [ ] Retry logic implemented

### Phase 3 Progress
- [ ] AdaptiveBatchProcessor created
- [ ] Checkpointing system implemented
- [ ] Validation test suite created
- [ ] Coverage improved to 95%+

### Phases 4-5 Progress
- [ ] Alternative approaches tested
- [ ] Performance monitoring implemented
- [ ] Full documentation completed
- [ ] Solution validated and deployed

## Results Documentation

### Findings Section
- **Root Cause Identified**: [To be filled during implementation]
- **Solution Applied**: [To be filled during implementation]
- **Performance Impact**: [To be filled during implementation]
- **Coverage Improvement**: [To be filled during implementation]

### Lessons Learned
- **SDK Limitations**: [To be documented]
- **Best Practices**: [To be documented]
- **Optimization Techniques**: [To be documented]
- **Future Recommendations**: [To be documented]

## Timeline Estimate

- **Phase 1** (Enhanced Logging): 1-2 days
- **Phase 2** (SDK Deep Dive): 2-3 days  
- **Phase 3** (Batch Improvements): 2-3 days
- **Phase 4** (Alternative Approaches): 1-2 days
- **Phase 5** (Validation): 1 day

**Total Estimated Duration**: 7-11 days

## Next Actions

1. **Immediate**: Begin Phase 1 with DebugClaudeCodeWrapperService creation
2. **Day 1**: Complete enhanced logging and run initial failure analysis
3. **Day 2**: Begin SDK investigation with ClaudeSDKDebugTest
4. **Day 3-4**: Implement identified fixes and retry logic
5. **Day 5-6**: Create adaptive batch processing
6. **Day 7**: Run comprehensive validation and document results

---
*Last Updated: 2025-08-18*  
*STATUS: ✅ PLAN CREATED - Ready for Phase 1 implementation*  
*GOAL: Achieve 95%+ coverage while maintaining 77.2% F1 performance*
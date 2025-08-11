# Batch PR Processing Error Investigation Plan

**Date**: 2025-07-29 (Updated)  
**Context**: Analysis of terminal logs reveals discrepancy between processed PRs and dashboard reporting

## Critical Finding: Dashboard Data Loss
- **Command**: `python batch_pr_workflow.py 3920 3919 3921 3922 3927 3929` (6 PRs)
- **Log Result**: "Processed 6 PRs" with "Success rate: 5/6"
- **Dashboard Result**: Only 2 PRs visible at `file:///home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/runs/run-1/pr_orchard_dashboard.html`
- **Issue**: 4 PRs missing from dashboard despite being processed

## Error Analysis Summary

### Error 1 (PR #3927): Compilation failures due to incomplete formatting
- **Location**: `BeanOutputConverter.java:162`
- **Issue**: `';' expected` suggests unformatted code
- **Root cause**: Formatter wasn't actually applied to all files, not formatter corruption
- **Evidence**: Formatter always works when properly applied

### Error 2 (PR #3929): Backport assessment crashes
- **Location**: `backport_assessor.py` 
- **Issue**: `'list' object has no attribute 'get'`
- **Root cause**: Code expecting dict but receiving list (conversation.json = 2 chars = `[]`)

### Error 3 (NEW): Dashboard Data Aggregation Issue
- **Issue**: Only 2/6 processed PRs appear in HTML dashboard
- **Impact**: Missing data for PRs 3920, 3921, 3922, 3927 despite successful processing
- **Log Evidence**: Shows 5/6 success rate but dashboard incomplete

## Investigation Steps

### Phase 1: Dashboard Data Loss Investigation (NEW - HIGH PRIORITY)
1. **Check batch processing logs**:
   - Examine `/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/runs/run-1/logs/batch-20250728-214149/batch-summary.md`
   - Review `/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/runs/run-1/logs/batch-20250728-214149/batch-metrics-20250728-214149.json`

2. **Verify report generation**:
   - Check if reports exist for all 6 PRs in `/runs/run-1/reports/`
   - Determine which PRs completed successfully vs failed
   - Identify where data gets lost between processing and dashboard

3. **Dashboard generation analysis**:
   - Check `LowHangingFruitReportGenerator` or dashboard generator code
   - Verify it includes all processed PRs, not just successful ones
   - Look for filtering logic that might exclude failed PRs

### Phase 2: Debug Formatter Application Issue (PR #3927)

#### 2.1 Check formatter execution
- Verify formatter log: `java-formatter-20250728_215213.log` shows all files processed
- Look for formatter command that was actually executed
- Check if mvnd formatter completed successfully vs just started

#### 1.2 Identify missing formatter coverage
- Compare which files were supposed to be formatted vs actually formatted
- Check if `BeanOutputConverter.java` was included in formatter scope
- Verify formatter targets all changed files, not just a subset

#### 1.3 Root cause analysis
- Check if formatter process failed silently
- Look for file permission issues or path problems
- Verify mvnd formatter command includes correct file patterns

### Phase 3: Debug Backport Assessment Crash (PR #3929)

#### 3.1 Locate the crash point
- Find where `'list' object has no attribute 'get'` occurs in `backport_assessor.py`
- Examine conversation.json (2 chars = empty list `[]`)

#### 3.2 Fix data handling
- Add type checking: if conversation is list vs dict
- Handle empty conversation data gracefully
- Add fallback when conversation data is malformed

### Phase 4: Implement Fixes

#### 4.1 Dashboard Data Aggregation Fix (NEW)
- Ensure dashboard includes ALL processed PRs regardless of success/failure status
- Add error status indicators for failed PRs
- Verify batch metrics collection includes all attempted PRs

#### 4.2 Formatter Application Fix
- Ensure formatter processes ALL changed files, not subset
- Add verification step: check if formatting actually applied
- Improve error detection when formatter fails silently

#### 4.3 Backport Assessment Fix
- Add type checking for conversation data structure
- Handle empty conversation list (`[]`) vs expected dict format
- Add debugging output to identify exact data structure received

### Phase 5: Test & Validate

#### 5.1 Rerun batch processing
- Test fixes on the same 6 PRs
- Verify dashboard completeness: Ensure all 6 PRs appear in dashboard
- Test error handling: Verify dashboard shows failed PRs with appropriate status

#### 5.2 Regression testing
- Ensure fixes don't break working functionality
- Test batch processing robustness for edge cases
- Verify accurate success/failure rates in reporting

## Expected Outcomes

1. **Dashboard shows all 6 processed PRs** with appropriate success/failure indicators
2. **Formatter applies to ALL changed Java files**, not subset
3. **Backport assessment handles empty conversation data** gracefully
4. **Batch processing robustness** improved for edge cases
5. **Better error reporting** and data aggregation across the pipeline

## Files to Investigate

### Primary Investigation Targets
- `java-formatter-20250728_215213.log` - Formatter execution log
- `backport_assessor.py` - Backport assessment crash location
- `BeanOutputConverter.java:162` on PR #3927 branch
- `conversation.json` for PR #3929 (empty list case)

### Supporting Files
- Formatter configuration files
- PR workflow orchestration code
- Error handling and logging mechanisms

## Success Criteria ✅ COMPLETED

- [x] Dashboard displays all 6 PRs from batch run
- [x] PR #3927 compiles successfully after formatting fix  
- [x] PR #3929 backport assessment completes without crashing
- [x] Batch processing shows accurate success/failure rates
- [x] All processed PRs visible in reporting regardless of final status

## IMPLEMENTATION STATUS: COMPLETED ✅

**All critical issues identified and resolved:**

1. **Git State Contamination**: Fixed by adding `git rebase --abort` and `git merge --abort` to cleanup_pr_workspace in pr_workflow.py
2. **Worktree Management**: Fixed branch deletion errors by detecting and removing worktrees before deletion
3. **Dashboard Data Loss**: Fixed HTML report generator to handle missing data gracefully
4. **AI Solution Assessment**: Enhanced validation to detect incomplete responses with fallback handling
5. **Branch Mapping**: Fixed dashboard to show actual git branch names instead of placeholders

**Date Completed**: August 2025
**Status**: All batch processing errors resolved, system stable for production use

---
*Generated: 2025-07-29*  
*Status: Investigation Plan - Ready for Implementation*
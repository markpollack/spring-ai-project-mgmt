# Large PR Analysis Optimization - Implementation Checklist

**Plan ID**: large-pr-analysis-optimization  
**Created**: 2025-08-19  
**Status**: Planning  
**Priority**: High  

## Problem Statement

PR #4179 (MCP server restructure) timed out after 5 minutes during AI solution assessment. This 60-file, 7,591-line architectural refactoring exceeds current analysis capabilities, revealing systemic issues with large PR processing.

## Pre-Implementation: Commit Outstanding Work
- [x] Run `git status` to review current changes
- [x] Add modified files to staging area
- [x] Create commit with message: "feat: analyze large PR timeout issues and create optimization plan"
- [x] Verify commit succeeded with `git status`

## Phase 0: Fix Data Collection (COMPLETED)
- [x] **CRITICAL BUG FOUND**: `file-changes.json` missing 30 of 60 files due to GitHub API pagination
- [x] **Root Cause**: `pr_context_collector.py` missing `--paginate` flag in GitHub API call
- [x] **Fix Applied**: Added `--paginate` to `_collect_file_changes()` method
- [x] **Verification**: PR #4179 now correctly shows 60 files including all 7 .adoc documentation files
- [x] **Learning**: Always verify data completeness before analysis - use multiple methods to validate file collection

## Phase 1: Documentation-First Analysis for Large PRs
- [ ] Modify `solution_assessor.py` to detect `.adoc` files in PR changes
- [ ] Add method `_analyze_documentation_changes()` to extract high-level changes
- [ ] Create logic to prioritize reading documentation files before code analysis
- [ ] Add documentation summary to assessment context
- [ ] Test with PR #4179 to verify documentation extraction works

## Phase 2: Dynamic Timeout Implementation  
- [ ] Add `_calculate_timeout()` method based on PR size
- [ ] Base timeout: 300s + 30s per 10 files + 60s per 1000 lines
- [ ] Cap maximum timeout at 20 minutes (1200s)
- [ ] Update timeout parameter in `solution_assessor.py:558`
- [ ] Add logging for timeout decisions

## Phase 3: PR Size Classification
- [ ] Implement `classify_pr_size()` method with thresholds:
  - [ ] Small: <10 files, <1000 lines
  - [ ] Medium: 10-40 files, 1000-5000 lines  
  - [ ] Large: 40+ files, 5000+ lines
- [ ] Add architectural change detection (new modules, major restructures)
- [ ] Log classification decisions for debugging

## Phase 4: Analysis Strategy Selection
- [ ] Create simplified analysis template for large PRs
- [ ] Focus on: architecture impact, breaking changes, documentation changes
- [ ] Implement strategy selection based on PR size
- [ ] Add fallback to simplified analysis on timeout

## Phase 5: Enhanced Error Handling
- [ ] Catch `subprocess.TimeoutExpired` exceptions
- [ ] Implement automatic fallback to simplified analysis
- [ ] Add clear user messaging about analysis strategy used
- [ ] Always provide some level of assessment result

## Phase 6: Testing & Validation
- [ ] Test with PR #4179 (60 files, 7591 additions)
- [ ] Verify timeout no longer occurs
- [ ] Validate analysis quality for large PRs
- [ ] Test fallback scenarios
- [ ] Document performance improvements

## Success Criteria
- [ ] PR #4179 analysis completes without timeout
- [ ] Documentation changes are summarized first
- [ ] Large PRs receive appropriate analysis strategy
- [ ] No analysis completely fails (always has fallback)
- [ ] Clear indicators of analysis completeness level

## Key Implementation Details

### Documentation-First Approach
For large PRs, prioritize reading documentation files (*.adoc, *.md, README) to understand:
- High-level architectural changes
- Breaking changes and migration requirements
- Feature additions and modifications
- Impact on existing functionality

### Timeout Calculation Formula
```python
def _calculate_timeout(self, file_count: int, lines_changed: int) -> int:
    base_timeout = 300  # 5 minutes
    file_timeout = (file_count // 10) * 30  # 30s per 10 files
    lines_timeout = (lines_changed // 1000) * 60  # 1 minute per 1000 lines
    return min(base_timeout + file_timeout + lines_timeout, 1200)  # Cap at 20 minutes
```

### Analysis Strategy Selection
- **Small PRs**: Full detailed analysis (current approach)
- **Medium PRs**: Focused analysis on changed files + impact assessment
- **Large PRs**: Documentation-first + architectural overview + sample file analysis
- **Architectural PRs**: High-level design review + breaking change focus

---

**Next Action**: Begin with pre-implementation git commit step.
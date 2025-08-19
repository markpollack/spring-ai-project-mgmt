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

## Phase 1: Documentation-First Analysis for Large PRs (COMPLETED)
- [x] Modify `solution_assessor.py` to detect `.adoc` files in PR changes
- [x] Add method `_analyze_documentation_changes()` to extract high-level changes
- [x] Create logic to prioritize reading documentation files before code analysis
- [x] Add documentation summary to assessment context
- [x] Test with PR #4179 to verify documentation extraction works
- [x] **VERIFICATION**: PR #4179 shows 7 documentation files, high architectural significance, 1,072+ lines of MCP documentation

## Phase 2: Dynamic Timeout Implementation (COMPLETED)
- [x] Add `_calculate_timeout()` method based on PR size
- [x] Base timeout: 180s + 15s per 10 files + 30s per 1000 lines (optimized formula)
- [x] Cap maximum timeout at 10 minutes (600s) - reasonable maximum for very large PRs
- [x] Update timeout parameter in `solution_assessor.py:740`
- [x] Add logging for timeout decisions
- [x] **VERIFICATION**: Small PRs get 3min, Medium PRs get ~4m48s, Large PRs get 10min (PR #4179 gets full 10min)

## Phase 3: PR Size Classification (COMPLETED)
- [x] Implement `classify_pr_size()` method with thresholds:
  - [x] Small: <10 files, <1000 lines
  - [x] Medium: 10-40 files, 1000-5000 lines  
  - [x] Large: 40+ files, 5000+ lines
- [x] Add architectural change detection (new modules, major restructures)
- [x] Log classification decisions for debugging
- [x] **VERIFICATION**: PR #4179 correctly classified as `large`, `architectural`, with `documentation_first` strategy

## Phase 4: Analysis Strategy Selection (COMPLETED)
- [x] Create simplified analysis template for large PRs
- [x] Focus on: architecture impact, breaking changes, documentation changes, Spring AI best practices
- [x] Implement strategy selection based on PR size
- [x] Add fallback to simplified analysis on timeout
- [x] **VERIFICATION**: Different templates selected based on PR classification, Spring auto-configuration patterns included

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

### Timeout Calculation Formula (UPDATED)
```python
def _calculate_timeout(self, file_count: int, lines_changed: int, architectural_significance: str = 'low') -> int:
    base_timeout = 180  # 3 minutes base for small PRs
    file_timeout = (file_count // 10) * 15  # 15s per 10 files
    lines_timeout = (lines_changed // 1000) * 30  # 30s per 1000 lines
    arch_multiplier = {'low': 1.0, 'medium': 1.2, 'high': 1.4}.get(architectural_significance, 1.0)
    calculated = int((base_timeout + file_timeout + lines_timeout) * arch_multiplier)
    return min(calculated, 600)  # Cap at 10 minutes
```

### Analysis Strategy Selection
- **Small PRs**: Full detailed analysis (current approach)
- **Medium PRs**: Focused analysis on changed files + impact assessment
- **Large PRs**: Documentation-first + architectural overview + sample file analysis
- **Architectural PRs**: High-level design review + breaking change focus

---

**Next Action**: Begin with pre-implementation git commit step.
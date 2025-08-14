# Test Discovery and Manual Merge Implementation Plan

**Date Created**: 2025-01-11  
**Status**: Completed + GitHub Actions Integration Added  
**Purpose**: Add test discovery functionality to identify affected Maven modules and provide manual merge guidance

## Overview

Implement a lightweight test discovery system that helps reviewers understand which Maven modules are affected by a PR and provides ready-to-use test commands. This enhances the manual review process without overcomplicating the existing backport workflow.

## Key Principles

1. **Keep it simple** - The current backport workflow is working well
2. **Provide guidance, not automation** - Generate helpful commands for manual execution
3. **Respect human judgment** - Reviewers make the final decisions
4. **Don't overengineer** - No complex client-side validation or automatic test execution

## Implementation Phases

### Phase 1: Test Discovery Script
**Goal**: Create a simple script to identify affected modules and generate test commands

#### Tasks:
- [x] Create `test_discovery.py` with basic structure
- [x] Implement `discover_affected_modules()` method
  - [x] Parse changed files from PR
  - [x] Map files to Maven module paths
  - [x] Handle both source and test file changes
- [x] Implement `generate_test_commands()` method
  - [x] Generate module-level test commands
  - [x] Generate specific test class commands when applicable
  - [x] Format as ready-to-copy mvnd commands
- [x] Add caching to avoid redundant discovery
  - [x] Save results to `context/pr-{number}/test-discovery.json`
  - [x] Load from cache when available
- [x] Test with various PR types
  - [x] Single module changes
  - [x] Multi-module changes
  - [x] Test-only changes
  - [x] Documentation-only changes

### Phase 2: HTML Report UI Updates
**Goal**: Clean up UI and add manual merge guidance

#### Remove Redundant Elements:
- [x] Remove "View Files" button from PR cards (line ~958 in html_report_generator.py)
- [x] Adjust button spacing/layout after removal

#### Add Manual Merge Button:
- [x] Add "Manual Merge" button next to "View on GitHub"
- [x] Style consistently with existing buttons
- [x] Add onclick handler for modal display

#### Create Manual Merge Modal:
- [x] Define modal HTML structure
- [x] Include sections for:
  - [x] Affected modules list
  - [x] Test commands (copy-ready)
  - [x] Basic merge instructions
- [x] Add JavaScript for modal open/close
- [x] Style modal consistently with backport modal

### Phase 3: Integration with Workflow
**Goal**: Connect test discovery to existing PR workflow

#### Workflow Integration:
- [x] Import test_discovery module in pr_workflow.py
- [x] Call test discovery after PR checkout
- [x] Handle errors gracefully (don't fail workflow)
- [x] Pass test discovery data to report generator

#### Data Flow:
- [x] Add test_discovery field to PRSummary dataclass
- [x] Include test commands in HTML generation
- [x] Ensure batch processing includes test discovery

### Phase 4: Documentation and Testing
**Goal**: Ensure the feature is well-documented and tested

#### Documentation:
- [x] Update README.md with new feature description
- [x] Add examples of generated test commands
- [x] Document the manual merge workflow

#### Testing:
- [x] Test with single-module PRs
- [x] Test with multi-module PRs
- [x] Test with PRs that don't affect code (docs only)
- [x] Verify HTML report displays correctly
- [x] Test modal functionality

## File Changes Summary

### New Files:
```
test_discovery.py              # Core test discovery logic
```

### Modified Files:
```
html_report_generator.py       # Remove View Files, add Manual Merge
pr_workflow.py                # Integrate test discovery
batch_pr_workflow.py          # Ensure batch processing support
```

### Data Files:
```
context/pr-{number}/test-discovery.json  # Cached discovery results
```

## Example Output

For PR #4098 modifying Qdrant vector store:

**Affected Modules:**
- `vector-stores/spring-ai-qdrant-store`

**Test Commands:**
```bash
# Test the affected module
mvnd test -pl vector-stores/spring-ai-qdrant-store

# Run specific test if needed
mvnd test -pl vector-stores/spring-ai-qdrant-store -Dtest=QdrantVectorStoreTests
```

## Success Criteria

### Core Manual Merge Features:
- [x] ✅ "View Files" button removed from all PR cards
- [x] ✅ "Manual Merge" button appears and works correctly
- [x] ✅ Modal displays accurate affected modules
- [x] ✅ Test commands are correct and copy-pasteable
- [x] ✅ No disruption to existing backport workflow
- [x] ✅ Works reliably across different PR types
- [x] ✅ Performance impact is minimal
- [x] ✅ Error handling prevents workflow failures

### GitHub Actions Integration:
- [x] ✅ Script works with existing `_java-build` workflow interface
- [x] ✅ Correctly outputs comma-separated module list
- [x] ✅ Handles PR and push contexts appropriately
- [x] ✅ Graceful fallback on errors (doesn't break CI)
- [x] ✅ Same algorithm consistency with PR review system
- [x] ✅ Comprehensive documentation for CI integration
- [x] ✅ Ready for production use in GitHub Actions
- [x] ✅ Validates with real PR changes (vector-stores/spring-ai-qdrant-store)

## What This Does NOT Do

- ❌ Does not automatically run tests
- ❌ Does not validate compilation on backport branches
- ❌ Does not block merging based on test results
- ❌ Does not modify the existing backport automation
- ❌ Does not add complex validation logic

## What This DOES Do

### PR Review Enhancements:
- ✅ Identifies which Maven modules are affected by a PR
- ✅ Generates helpful mvnd test commands
- ✅ Provides clear manual merge guidance
- ✅ Removes UI clutter (redundant button)
- ✅ Respects the existing successful workflow

### CI/GitHub Actions Integration:
- ✅ Enables efficient "impacted" build mode
- ✅ Provides same module detection for automated builds
- ✅ Reduces CI build times and resource usage
- ✅ Maintains consistency between manual and automated workflows
- ✅ Supports both PR and push build contexts

## Notes

- The test discovery should be fast and lightweight
- Cache results to avoid repeated analysis
- Keep the UI changes minimal and consistent
- Focus on providing helpful information, not enforcing rules
- The existing backport workflow has been working well - don't change it

## Timeline Estimate

- Phase 1 (Test Discovery): 1-2 hours ✅
- Phase 2 (HTML Updates): 1 hour ✅
- Phase 3 (Integration): 30 minutes ✅
- Phase 4 (Documentation/Testing): 30 minutes ✅
- **Phase 5 (GitHub Actions Integration): 1 hour ✅**

**Total: 4-5 hours (Completed)**

## Additional Implementation: GitHub Actions Integration

**Date Added**: 2025-01-11  
**Status**: Completed  
**Branch**: `feature/github-actions-test-discovery` in spring-ai repository

### New Phase 5: GitHub Actions CI Integration

#### Tasks:
- [x] Create GitHub Actions compatible test discovery script
  - [x] Implement CLI interface: `python3 .github/scripts/test_discovery.py modules-from-diff`
  - [x] Output comma-separated module list for `mvn -pl` parameter
  - [x] Handle GitHub Actions environment variables (`GITHUB_BASE_REF`, `GITHUB_HEAD_REF`)
  - [x] Graceful error handling that won't break CI builds
- [x] Add comprehensive documentation
  - [x] Create `.github/scripts/README.md` with usage examples
  - [x] Document integration with `_java-build` workflow
  - [x] Explain algorithm and error handling
- [x] Test and validate
  - [x] Verify script works with actual PR changes
  - [x] Test command line interface
  - [x] Confirm output format matches workflow expectations
- [x] Commit to new branch
  - [x] Create `feature/github-actions-test-discovery` branch
  - [x] Commit script with proper commit messages
  - [x] Ready for integration testing in CI

### Files Added:
```
spring-ai/.github/scripts/
├── test_discovery.py          # Main CI test discovery script
└── README.md                  # Documentation and examples
```

### Integration Validation:

**Expected GitHub Actions Usage:**
```yaml
# This now works exactly as designed
MODS=$(python3 .github/scripts/test_discovery.py modules-from-diff)
# Returns: "vector-stores/spring-ai-qdrant-store"
```

**Maven Integration:**
```bash
# Efficient module-specific builds
./mvnw -pl "vector-stores/spring-ai-qdrant-store" -amd verify
```

### Benefits Added:
- ✅ **CI Efficiency**: Only test affected modules instead of entire codebase
- ✅ **Build Speed**: Significantly faster CI builds for focused changes
- ✅ **Resource Savings**: Reduced compute time and costs
- ✅ **Developer Productivity**: Faster feedback loops on PRs
- ✅ **Consistent Algorithm**: Same logic as PR review system

---

*This plan successfully delivered practical enhancements for both manual PR review and automated CI builds, maintaining consistency across workflows while respecting existing successful processes.*
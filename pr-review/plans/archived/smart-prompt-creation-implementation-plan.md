# Smart Prompt Creation Implementation Plan

## Overview
Implement file status-aware prompt creation to eliminate patch content duplication for new files and optimize analysis for PR 3914 (many new Java files).

## IMPLEMENTATION STATUS: NOT STARTED ❌

**Reason for Non-Implementation**: This optimization was planned but never implemented due to:
1. Current system performs adequately for PR analysis workloads
2. Token optimization not critical with current analysis patterns
3. Focus shifted to other higher-priority enhancements (git state management, backport automation)
4. PR 3914 successfully analyzed with existing approach

**Current Status**: Existing file change analysis in ai_risk_assessor.py handles new files adequately without optimization.

## Branch Management Strategy

### Initial Setup
- [ ] Create new feature branch: `feature/smart-prompt-creation`
- [ ] Switch to new branch for all development work
- [ ] Ensure clean working directory before starting

### Git Workflow
- [ ] **Fine-grained commits**: Commit after each successful phase completion
- [ ] **Descriptive commit messages**: Include phase number and key changes
- [ ] **No backup maintenance needed**: Git branch provides rollback capability
- [ ] **Testing verification**: Each commit should represent working, tested code

### Branch Protection
- [ ] Keep `main` branch stable throughout development
- [ ] Only merge to `main` after all phases complete and validated
- [ ] Use branch for incremental testing and validation

## Phase 1: Core File Status Logic

### Phase 1 Pre-Work: Learning Review
- [ ] **First phase**: No previous learnings to review
- [ ] Create learning capture framework for this phase
- [ ] Prepare to document key insights and challenges

### File Status Detection and Routing
- [ ] Modify `build_file_changes_detail()` in `ai_risk_assessor.py` to group files by status
- [ ] Create separate handling for `added`, `modified`, and `removed` files
- [ ] Implement status-based routing logic

### New Files Formatting (`_format_new_files()`)
- [ ] Implement method with **zero patch content** for new files
- [ ] Add Java file prioritization (process .java files first)
- [ ] Include file metadata: size, type, file path
- [ ] Add "Priority: HIGH" marking for Java files
- [ ] Generate contextual summaries without patch duplication

### Modified Files Formatting (`_format_modified_files()`)  
- [ ] Continue current approach with filtered patch excerpts
- [ ] Maintain existing patch content strategy
- [ ] Ensure no regression in analysis quality

### Java File Summary Generation
- [ ] Implement `_generate_java_file_summary()` method
- [ ] Add pattern recognition for auto-configuration, test classes, properties
- [ ] Prioritize security-relevant file types

### Testing - No Regression
- [ ] Test with PR 3386 (modified files) to ensure no regression
- [ ] Verify existing functionality still works correctly
- [ ] Confirm prompt generation remains stable

### Phase 1 Learning Capture
- [ ] **Document learnings**: Create `/plans/learnings/phase-1-learnings.md`
- [ ] **Capture insights**: What worked well, what was challenging, key decisions made
- [ ] **Document gotchas**: Technical issues encountered and solutions
- [ ] **Record metrics**: Implementation time, code complexity, testing challenges
- [ ] **Note improvements**: Ideas for better approaches discovered during implementation

### Phase 1 Completion
- [ ] **Commit Phase 1**: "Phase 1: Implement file status-aware prompt creation with Java prioritization"
- [ ] Verify all Phase 1 functionality working
- [ ] Ensure no regressions in existing PR analysis
- [ ] **Learning file committed**: Include phase-1-learnings.md in the commit

## Phase 2: Critical Template Updates

### Phase 2 Pre-Work: Learning Review
- [ ] **Read Phase 1 learnings**: Review `/plans/learnings/phase-1-learnings.md`
- [ ] **Apply insights**: Use Phase 1 lessons to improve Phase 2 approach
- [ ] **Adjust strategy**: Modify Phase 2 tasks based on Phase 1 discoveries
- [ ] **Identify dependencies**: Note any Phase 1 issues that affect Phase 2 work

### Update `ai_risk_assessment_prompt.md`
- [ ] **CRITICAL**: Eliminate duplicate data in `{file_changes_detail}` section
- [ ] Add status-specific analysis instructions
- [ ] Include guidance for new vs modified file evaluation
- [ ] Add Java file prioritization instructions
- [ ] Clarify when to use Read tool vs patch context

### Template Content Updates
- [ ] Add section explaining new file analysis approach
- [ ] Update instructions to handle files without patch content
- [ ] Add priority guidance for Java source files
- [ ] Include examples of status-aware analysis

### Validation
- [ ] Review template formatting and variable substitution
- [ ] Test template with sample data to ensure proper rendering
- [ ] Verify no template syntax errors

### Phase 2 Learning Capture
- [ ] **Document learnings**: Create `/plans/learnings/phase-2-learnings.md`
- [ ] **Template insights**: What template changes were most effective
- [ ] **Integration challenges**: How Phase 1 and Phase 2 worked together
- [ ] **Testing discoveries**: Key findings from template validation
- [ ] **Improvement ideas**: Better approaches identified for future template work

### Phase 2 Completion
- [ ] **Commit Phase 2**: "Phase 2: Update AI risk assessment template for status-aware analysis"
- [ ] Verify template changes work correctly with new prompt format
- [ ] Test template rendering with both new and modified files
- [ ] **Learning file committed**: Include phase-2-learnings.md in the commit

## Phase 3: Real-World Testing with PR 3914

### Phase 3 Pre-Work: Learning Review
- [ ] **Read Phase 1 learnings**: Review `/plans/learnings/phase-1-learnings.md`
- [ ] **Read Phase 2 learnings**: Review `/plans/learnings/phase-2-learnings.md`
- [ ] **Synthesize insights**: Combine learnings from both phases for testing approach
- [ ] **Identify risks**: Note any issues from previous phases that could affect testing
- [ ] **Adjust testing strategy**: Modify test plan based on accumulated learnings

### Preparation
- [ ] Ensure PR 3914 context data is available
- [ ] Set up logging to measure prompt size reduction
- [ ] Prepare benchmark metrics for comparison

### Testing Execution  
- [ ] Run AI risk assessment on PR 3914 with new approach
- [ ] Measure actual prompt size reduction vs current approach
- [ ] Record processing time improvements
- [ ] Capture token usage statistics

### Quality Validation
- [ ] Verify AI analysis quality remains high
- [ ] Compare risk detection with previous approaches
- [ ] Ensure all new Java files are properly analyzed
- [ ] Confirm no critical analysis gaps

### Metrics Collection
- [ ] Document prompt size before/after optimization
- [ ] Record processing time improvements
- [ ] Measure token efficiency gains
- [ ] Assess analysis completeness

### Phase 3 Learning Capture
- [ ] **Document learnings**: Create `/plans/learnings/phase-3-learnings.md`
- [ ] **Performance insights**: What optimizations had the biggest impact
- [ ] **Testing discoveries**: Unexpected issues or successes with PR 3914
- [ ] **Quality analysis**: How well the new approach maintained analysis depth
- [ ] **Metrics documentation**: Actual vs expected performance improvements
- [ ] **Integration lessons**: How all phases worked together in real-world scenario

### Phase 3 Completion
- [ ] **Commit Phase 3**: "Phase 3: Validate smart prompt creation with PR 3914 real-world testing"
- [ ] Document performance improvements and metrics
- [ ] Confirm analysis quality meets standards
- [ ] **Learning file committed**: Include phase-3-learnings.md in the commit

## Phase 4: Further Optimizations (Based on Test Results)

### Phase 4 Pre-Work: Comprehensive Learning Review
- [ ] **Read all previous learnings**: Review phases 1-3 learning files
- [ ] **Identify patterns**: Common themes and insights across all phases
- [ ] **Prioritize optimizations**: Use learnings to focus on most impactful improvements
- [ ] **Avoid repeated mistakes**: Apply lessons learned to prevent known issues
- [ ] **Build on successes**: Leverage approaches that worked well in previous phases

### Analysis of Test Results
- [ ] Review PR 3914 test results and identify any issues
- [ ] Determine if additional file management strategies are needed
- [ ] Assess need for size-based thresholds

### Optional Enhancements (If Needed)
- [ ] Implement size-based file handling if very large files cause issues
- [ ] Add extended pattern recognition based on encountered file types
- [ ] Optimize further based on real-world performance data

### Documentation Updates
- [ ] Update CLAUDE.md with new prompt creation approach
- [ ] Document configuration options and settings
- [ ] Add troubleshooting guide for common issues

### Phase 4 Learning Capture (If Phase 4 Executed)
- [ ] **Document learnings**: Create `/plans/learnings/phase-4-learnings.md`
- [ ] **Optimization insights**: Which additional improvements were most valuable
- [ ] **Cross-phase synthesis**: How learnings from all phases combined
- [ ] **Final lessons**: Key takeaways for future similar projects
- [ ] **Documentation effectiveness**: What documentation approaches worked best

### Phase 4 Completion (If Needed)
- [ ] **Commit Phase 4**: "Phase 4: Additional optimizations and documentation updates"
- [ ] Finalize all enhancements based on real-world testing
- [ ] Complete documentation updates
- [ ] **Learning file committed**: Include phase-4-learnings.md in the commit (if phase executed)

## Success Criteria

### Prompt Optimization
- [ ] Achieve 50-70% prompt size reduction for new module PRs
- [ ] Stay well under 25k token Read tool limits
- [ ] Eliminate redundant patch content for new files

### Performance  
- [ ] Maintain or improve current ~40s analysis time
- [ ] Ensure stable processing performance
- [ ] No degradation in system reliability

### Analysis Quality
- [ ] Maintain same level of risk detection accuracy
- [ ] Ensure comprehensive coverage of new Java files
- [ ] No loss of security analysis depth

## Risk Mitigation

### Potential Issues and Solutions
- [ ] **Risk**: Loss of analysis context for new files
  - **Mitigation**: Ensure Claude Code Read tool instructions are clear
- [ ] **Risk**: Template complexity increases  
  - **Mitigation**: Keep templates simple, move complexity to Python logic
- [ ] **Risk**: File summary accuracy issues
  - **Mitigation**: Use conservative summaries, focus on file type patterns

### Rollback Plan
- [ ] **No backup needed**: Use git branch for rollback capability
- [ ] Document rollback procedure: `git checkout main` if issues arise
- [ ] Keep `main` branch stable as fallback option

## Final Integration and Merge

### Pre-Merge Validation
- [ ] All phases completed successfully with commits
- [ ] Full end-to-end testing with PR 3914 completed
- [ ] Performance benchmarks documented and acceptable
- [ ] No regressions in existing functionality

### Merge to Main
- [ ] **Final commit**: "Complete smart prompt creation optimization for file status handling"
- [ ] Create pull request or merge feature branch to main
- [ ] Update main branch with all optimizations
- [ ] Tag release if significant performance improvement achieved

### Post-Merge Cleanup
- [ ] Delete feature branch after successful merge
- [ ] Update documentation if needed
- [ ] Monitor system performance with new implementation

## Learning Framework

### Learning Directory Structure
```
/plans/learnings/
├── README.md                          # Learning framework documentation
├── phase-1-learnings-template.md      # Template for Phase 1 learning capture
├── phase-1-learnings.md               # Actual Phase 1 learnings (created during implementation)
├── phase-2-learnings.md               # Phase 2 learnings with Phase 1 insights applied
├── phase-3-learnings.md               # Phase 3 learnings with cumulative insights
└── phase-4-learnings.md               # Phase 4 learnings (if needed)
```

### Learning Review Process
1. **Start each phase**: Read all previous phase learning files
2. **Apply insights**: Use learnings to improve current phase approach
3. **Document discoveries**: Capture new insights during implementation
4. **Include in commit**: Learning file committed with phase completion

## Completion Checklist

- [ ] **Learning framework established**: Created `/plans/learnings/` directory and templates
- [ ] **Branch created**: `feature/smart-prompt-creation` 
- [ ] **Phase 1 committed**: Core file status logic implemented + phase-1-learnings.md
- [ ] **Phase 2 committed**: Template updates completed + phase-2-learnings.md
- [ ] **Phase 3 committed**: Real-world testing validated + phase-3-learnings.md
- [ ] **Phase 4 committed**: Additional optimizations (if needed) + phase-4-learnings.md
- [ ] **Learning synthesis**: Cross-phase insights documented and applied
- [ ] **Final merge**: All changes integrated to main branch
- [ ] **Success criteria met**: Performance and quality targets achieved
- [ ] **Ready for production**: System optimized for PR 3914 and similar workloads
# PR Workflow Enhancement Plan: Claude Code-Powered Compilation Error Resolution

## Overview
Enhance the PR workflow to use Claude Code via `claude_code_wrapper.py` to automatically fix all compilation errors, with templated prompts and progress tracking.

## Implementation Plan

### Phase 1: Setup Infrastructure

1. **Create Template Files**
   - [x] Create `/templates/compilation_error_base_prompt.md` - Base prompt for compilation errors
   - [x] Create `/templates/compilation_error_type_mismatch_prompt.md` - Type mismatch specific prompt
   - [x] Create `/templates/compilation_error_batch_fix_prompt.md` - Batch fixing prompt
   - [x] Create `/templates/compilation_error_missing_symbol_prompt.md` - Missing symbol prompt

2. **Create Progress Tracking**
   - [x] Create `/plans/compilation-error-enhancement-progress.md` - Track implementation progress
   - [x] Create `/plans/learnings/compilation-error-enhancement/` directory for documenting what we learn
   - [x] Create README.md in learnings directory
   - [x] Create phase-1-learnings-template.md

3. **Update CompilationErrorResolver**
   - [x] Add imports for Path and template handling
   - [x] Add `load_prompt_template()` method to load templates
   - [x] Update existing methods to use templates instead of hardcoded prompts
   - [x] Add `_fix_with_claude_code()` universal handler method
   - [x] Update `_classify_error()` to make all errors auto-fixable
   - [x] Update `auto_resolve_errors()` to use Claude Code fallback
   - [x] Test template loading with a simple example

### Phase 2: Implement Generic Claude Code Handler

**Before starting: Read `/plans/learnings/compilation-error-enhancement/phase-1-learnings.md` if it exists**

1. **Update `_fix_generic_types()` method**
   - [ ] Remove "not yet implemented" stub
   - [ ] Load prompt from template using `load_prompt_template()`
   - [ ] Use claude_code_wrapper for execution
   - [ ] Test with a generic type error

2. **Create Universal Handler Method**
   - [ ] Add `_fix_with_claude_code()` method that can handle any error type
   - [ ] Implement template selection logic based on error message
   - [ ] Add proper error context formatting
   - [ ] Pass to claude_code_wrapper with timeout=180 and show_progress=True
   - [ ] Add error handling and logging

3. **Update Error Classification**
   - [ ] Update `_classify_error()` to always return auto_fixable=True
   - [ ] Keep error type classification for template selection
   - [ ] Add new error patterns for better classification

4. **Document Results**
   - [ ] Create `/plans/learnings/compilation-error-enhancement/phase-2-learnings.md`
   - [ ] Note what prompt structures worked best
   - [ ] Document any error patterns that need special handling
   - [ ] Record any issues with Claude Code integration

### Phase 3: Implement Batch Error Resolution

**Before starting: Read all files in `/plans/learnings/compilation-error-enhancement/` directory**

1. **Add File Grouping Method**
   - [ ] Create `group_errors_by_file()` method
   - [ ] Return Dict[str, List[CompilationError]]
   - [ ] Sort errors by line number within each file
   - [ ] Add logging for grouped errors

2. **Create Batch Fix Method**
   - [ ] Create `_fix_file_errors_batch()` method
   - [ ] Load batch fix template with `load_prompt_template()`
   - [ ] Format error list for the prompt
   - [ ] Use claude_code_wrapper with timeout=300
   - [ ] Add progress logging

3. **Test Batch vs Individual Fixing**
   - [ ] Create test case with multiple errors in one file
   - [ ] Try individual fixing approach
   - [ ] Try batch fixing approach
   - [ ] Measure success rate and time taken
   - [ ] Document which approach works better

4. **Document Results**
   - [ ] Create `/plans/learnings/compilation-error-enhancement/phase-3-learnings.md`
   - [ ] Record optimal batch sizes
   - [ ] Note any issues with multi-error fixes
   - [ ] Document performance comparisons

### Phase 4: Enhance Workflow Integration

**Before starting: Read all learnings files to understand best practices**

1. **Add Compilation Check After Rebase**
   - [ ] Locate `rebase_against_upstream()` method in pr_workflow.py
   - [ ] Add compilation check after successful rebase
   - [ ] Call enhanced compilation resolver if errors found
   - [ ] Commit fixes with descriptive message
   - [ ] Test with a PR that needs rebasing

2. **Create Progressive Resolution Method**
   - [ ] Create `resolve_compilation_errors_progressive()` method
   - [ ] Implement max_attempts parameter (default=3)
   - [ ] Track errors fixed in each attempt
   - [ ] Stop if no progress between attempts
   - [ ] Add detailed logging for each attempt

3. **Add Checkpoint/Recovery**
   - [ ] Create `create_checkpoint()` method using git stash
   - [ ] Create `restore_checkpoint()` method
   - [ ] Add checkpoint before compilation fixes
   - [ ] Implement recovery on failure
   - [ ] Test recovery mechanism

4. **Document Results**
   - [ ] Create `/plans/learnings/compilation-error-enhancement/phase-4-learnings.md`
   - [ ] Note integration points that work best
   - [ ] Document recovery scenarios
   - [ ] Record any workflow conflicts

### Phase 5: Test with PR 3914

**Before starting: Review all learnings and update templates based on insights**

1. **Prepare Test**
   - [ ] Review all learnings from phases 1-4
   - [ ] Update templates based on learnings
   - [ ] Run `python3 pr_workflow.py --cleanup 3914`
   - [ ] Verify clean workspace

2. **Run Full Workflow**
   - [ ] Execute `python3 pr_workflow.py 3914`
   - [ ] Monitor compilation error detection
   - [ ] Observe Claude Code fix attempts
   - [ ] Document each fix attempt in logs
   - [ ] Capture any error messages

3. **Specific PR 3914 Fix**
   - [ ] Verify type cast error is detected correctly
   - [ ] Confirm type mismatch template is selected
   - [ ] Verify Claude Code adds casts: `(McpSyncServerExchange)` and `(List<McpSchema.Root>)`
   - [ ] Run compilation to verify fix
   - [ ] Check no new errors introduced

4. **Final Documentation**
   - [ ] Create `/plans/learnings/compilation-error-enhancement/phase-5-learnings.md`
   - [ ] Update templates with final optimizations
   - [ ] Document success metrics
   - [ ] Create summary of all improvements
   - [ ] Update main plan with final notes

## Template Files to Create

### `/templates/compilation_error_base_prompt.md`
```markdown
Fix the Java compilation error in {file_path} at line {line_number}.

Error details:
- File: {file_path}
- Line: {line_number}
- Column: {column}
- Error message: {error_message}

Instructions:
1. Read the file {spring_ai_dir}/{file_path} to understand the context
2. Focus on the error at line {line_number}
3. Use the Edit tool to fix the compilation error
4. Ensure your fix follows Spring AI coding conventions
5. Make the minimal change necessary to fix the error

Working directory: {spring_ai_dir}
```

### `/templates/compilation_error_type_mismatch_prompt.md`
```markdown
Fix the type mismatch compilation error in {file_path}.

Error: {error_message}
Location: Line {line_number}, Column {column}

This is a type conversion error. Please:
1. Read the file {spring_ai_dir}/{file_path}
2. Understand what types are involved in the error
3. Add appropriate type casts or change variable types
4. For lambda expressions, you may need to add explicit casts to parameters
5. Check if this might be due to an API change in dependencies

Example fixes:
- Add cast: (TargetType) variable
- For lambdas: (param1, param2) -> becomes ((Type1) param1, (Type2) param2) ->
- Change variable declaration to match expected type

Use the Edit tool to apply your fix.
```

### `/templates/compilation_error_batch_fix_prompt.md`
```markdown
Fix all compilation errors in the file {file_path}.

The file has {error_count} compilation errors:
{error_list}

Instructions:
1. Read the entire file {spring_ai_dir}/{file_path}
2. Understand all the compilation errors
3. Use the MultiEdit tool to fix all errors in one operation
4. Ensure your fixes are consistent and don't introduce new errors
5. Follow Spring AI coding conventions

Please fix all errors efficiently. Group related fixes where possible.
```

## Progress Tracking

### `/plans/compilation-error-enhancement-progress.md`
```markdown
# Compilation Error Enhancement Progress

## Phase 1: Infrastructure Setup
- [ ] Create template directory structure
- [ ] Create all prompt templates
- [ ] Update CompilationErrorResolver imports
- [ ] Add template loading method
- [ ] Test template loading

## Phase 2: Generic Handler Implementation  
- [ ] Read phase 1 learnings
- [ ] Update _fix_generic_types method
- [ ] Create _fix_with_claude_code method
- [ ] Update error classification
- [ ] Test with simple compilation error
- [ ] Document learnings

## Phase 3: Batch Resolution
- [ ] Read all previous learnings
- [ ] Implement error grouping
- [ ] Create batch fix method
- [ ] Test batch vs individual
- [ ] Document optimal approach

## Phase 4: Workflow Integration
- [ ] Read all learnings
- [ ] Add post-rebase compilation check
- [ ] Implement progressive resolution
- [ ] Add checkpoint system
- [ ] Test error recovery
- [ ] Document integration points

## Phase 5: PR 3914 Testing
- [ ] Review and apply all learnings
- [ ] Update templates with insights
- [ ] Clean PR 3914 workspace
- [ ] Run full workflow
- [ ] Verify compilation fixes
- [ ] Document final results
```

## Benefits

1. **Template-based**: Easy to modify prompts without changing code
2. **Learning-driven**: Each phase builds on previous insights
3. **Claude Code integration**: Leverages existing wrapper
4. **Progressive improvement**: Templates improve with each phase
5. **Clear tracking**: Progress and learnings documented

This approach is practical and focuses on making the compilation error resolver use Claude Code effectively through templates and iterative learning.

## Overall Progress Summary

### Phase Completion Status
- [x] Phase 1: Infrastructure Setup (12/12 tasks)
- [ ] Phase 2: Generic Handler Implementation (0/13 tasks)
- [ ] Phase 3: Batch Error Resolution (0/13 tasks)
- [ ] Phase 4: Workflow Integration (0/15 tasks)
- [ ] Phase 5: Testing with PR 3914 (0/15 tasks)

### Key Milestones
- [ ] Templates created and tested
- [ ] Claude Code integration working
- [ ] Batch processing implemented
- [ ] Workflow integration complete
- [ ] PR 3914 successfully processed

### Notes for Future Sessions
- Always start by reading this plan and checking progress
- Update checkboxes as tasks are completed
- Create learnings files after each phase
- Test incrementally, don't wait until the end
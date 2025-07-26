# Smart Prompt Creation Based on File Status Design

## Problem Statement

The current AI risk assessment system includes patch content in prompts for all files, regardless of whether they are new or modified. For PRs like #3914 that add entirely new modules with many new files, this creates significant prompt bloat since:

1. **New files**: Patch content = full file content (redundant)
2. **Large new files**: Can consume excessive prompt tokens
3. **Patch format overhead**: Git patch headers add noise for new files

This leads to:
- Larger prompts approaching token limits
- Longer processing times
- Potentially hitting Claude Code's 25k token Read tool limit
- Reduced efficiency for file analysis

## Current Architecture

### File Changes Processing (ai_risk_assessor.py)
```python
def build_file_changes_detail(self, file_changes: List[Dict[str, Any]]) -> str:
    for change in file_changes:
        filename = change.get('filename', 'Unknown')
        status = change.get('status', 'unknown')  # 'added', 'modified', 'removed'
        patch = change.get('patch', '')           # Full git patch content
        
        # Currently includes patch for ALL files regardless of status
        if patch:
            patch_line_count = len(patch.split('\n'))
            details.append(f"- **Patch**: {patch_line_count} lines of changes")
```

### Git Status Information Available
From GitHub API, we receive file status:
- `"added"` - New file
- `"modified"` - Existing file with changes  
- `"removed"` - Deleted file
- `"renamed"` - File moved/renamed

## Proposed Solution

### 1. File Status-Aware Prompt Strategy

#### New Files (`status: "added"`)
- **Skip patch content entirely** (since patch = full file content - completely redundant)
- **Include file metadata**: size, type, purpose
- **Provide file path** for Claude Code Read tool access
- **Prioritize .java files** in analysis guidance
- **No patch duplication** in prompt to avoid bloat

#### Modified Files (`status: "modified"`)
- **Continue current approach** with filtered patch excerpts
- **Focus on changed sections** with context
- **Provide full file path** for complete context if needed

#### Removed Files (`status: "removed"`)
- **Include minimal context** about what was removed
- **Skip patch content** (deletion patches are usually not security-relevant)

### 2. Primary Focus Areas
- **Java files prioritized** for detailed analysis guidance
- **Template updates required** for ai_risk_assessment_prompt.md to eliminate duplicate data
- **Real-world testing** with PR 3914 to validate approach before additional optimizations

### 2. Implementation Strategy

#### Phase 1: File Status Detection and Routing
```python
def build_file_changes_detail(self, file_changes: List[Dict[str, Any]]) -> str:
    """Build file changes detail with status-aware content strategy"""
    details = []
    details.append("**IMPORTANT**: Use your Read tool to examine files as needed for analysis.")
    details.append("")
    
    # Group files by status for better organization
    new_files = [f for f in file_changes if f.get('status') == 'added']
    modified_files = [f for f in file_changes if f.get('status') == 'modified']
    removed_files = [f for f in file_changes if f.get('status') == 'removed']
    
    if new_files:
        details.extend(self._format_new_files(new_files))
    if modified_files:
        details.extend(self._format_modified_files(modified_files))
    if removed_files:
        details.extend(self._format_removed_files(removed_files))
    
    return '\n'.join(details)
```

#### Phase 2: Status-Specific Formatters
```python
def _format_new_files(self, new_files: List[Dict[str, Any]]) -> List[str]:
    """Format new files without any patch content (completely redundant for new files)"""
    details = ["## New Files Added"]
    details.append("")
    
    # Prioritize Java files first
    java_files = [f for f in new_files if f.get('filename', '').endswith('.java')]
    other_files = [f for f in new_files if not f.get('filename', '').endswith('.java')]
    
    for file_info in java_files + other_files:
        filename = file_info.get('filename', 'Unknown')
        additions = file_info.get('additions', 0)
        file_path = f"/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/spring-ai/{filename}"
        
        details.append(f"### {filename}")
        details.append(f"- **Status**: New file (patch content omitted - would be identical to full file)")
        details.append(f"- **File Path**: `{file_path}`")
        details.append(f"- **Size**: {additions} lines")
        details.append(f"- **Analysis**: Use Read tool to examine complete file content")
        
        # Add contextual summary for Java files (prioritized)
        if filename.endswith('.java'):
            file_summary = self._generate_java_file_summary(filename, file_info)
            details.append(f"- **Priority**: HIGH - Java source file")
            details.append(f"- **Purpose**: {file_summary}")
        else:
            file_summary = self._generate_file_summary(filename, file_info)
            if file_summary:
                details.append(f"- **Purpose**: {file_summary}")
        
        details.append("")
    
    return details

def _format_modified_files(self, modified_files: List[Dict[str, Any]]) -> List[str]:
    """Format modified files with relevant patch excerpts"""
    details = ["## Modified Files"]
    details.append("")
    
    for file_info in modified_files:
        filename = file_info.get('filename', 'Unknown')
        additions = file_info.get('additions', 0)
        deletions = file_info.get('deletions', 0)
        patch = file_info.get('patch', '')
        file_path = f"/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/spring-ai/{filename}"
        
        details.append(f"### {filename}")
        details.append(f"- **Status**: Modified")
        details.append(f"- **File Path**: `{file_path}`")
        details.append(f"- **Changes**: +{additions}/-{deletions} lines")
        
        # Include filtered patch excerpts for context
        if patch:
            filtered_patch = self._filter_patch_for_security_analysis(patch)
            if filtered_patch:
                details.append(f"- **Key Changes**:")
                details.extend(f"  - {line}" for line in filtered_patch[:5])  # Top 5 changes
        
        details.append(f"- **Full Analysis**: Use Read tool for complete context")
        details.append("")
    
    return details

def _generate_file_summary(self, filename: str, file_info: Dict[str, Any]) -> str:
    """Generate contextual summary for new files based on path/type"""
    if filename.endswith('.java'):
        if 'test' in filename.lower():
            return "Test class - examine for test coverage and security test patterns"
        elif 'autoconfigure' in filename.lower():
            return "Auto-configuration class - check for proper Spring Boot setup and security"
        elif filename.endswith('Properties.java'):
            return "Configuration properties - examine for credential handling and validation"
        else:
            return "Java source file - analyze for security, performance, and integration risks"
    elif filename.endswith('.xml'):
        if filename == 'pom.xml':
            return "Maven POM - check dependencies, plugins, and build security"
        else:
            return "XML configuration - examine for injection risks and sensitive data"
    elif filename.endswith('.md'):
        return "Documentation - review for sensitive information disclosure"
    elif filename.endswith(('.yml', '.yaml', '.properties')):
        return "Configuration file - check for hardcoded credentials and security settings"
    else:
        return "Source file - perform comprehensive security and quality analysis"
```

### 3. Token Optimization Benefits

#### Current Approach (PR 3386)
- 15 files: ~12KB prompt (efficient due to file references)

#### Projected for PR 3914 (with new approach)
- ~50+ new files: Estimated prompt reduction of 60-80%
- **Without optimization**: ~80KB+ (excessive)
- **With optimization**: ~15-25KB (manageable)

#### Token Savings Breakdown
- **New files**: Save ~200-500 tokens per file (no patch content)
- **Modified files**: Save ~50-100 tokens per file (filtered patches)
- **Overall**: Potential 70% reduction for new module PRs

### 4. Template Updates Required

#### AI Risk Assessment Prompt Template (`ai_risk_assessment_prompt.md`)
**Critical Update Needed**: The template currently has a `{file_changes_detail}` section that will contain duplicate data for new files if we include patch content. The template must be updated to:

- **Eliminate redundancy**: Instruct that new files have no patch content (since it's identical to full file)
- **Prioritize Java files**: Add specific guidance for analyzing Java source files first
- **Status-specific instructions**: Different analysis approaches for new vs modified files
- **Read tool guidance**: Clear instructions on when to use Read tool vs patch context

**Template Section to Update**:
```markdown
### File Changes Detail
{file_changes_detail}
```
Must handle new files without patch duplication.

#### Solution Assessment Template  
- Similar status-aware approach for technical evaluation
- Lower priority since risk assessment is primary focus

#### Conversation Analysis Template
- Less affected, but could benefit from file status context

### 5. Implementation Plan

**Note**: Detailed implementation plan with checkboxes moved to `/plans/smart-prompt-creation-implementation-plan.md`

**Summary**:
1. **Phase 1**: Core file status logic with zero patch content for new files
2. **Phase 2**: Critical template updates to eliminate duplicate data  
3. **Phase 3**: Real-world testing with PR 3914
4. **Phase 4**: Further optimizations based on test results

### 6. Configuration Options

Add configuration for prompt optimization:
```python
class PromptOptimizationConfig:
    # Token limits
    MAX_PATCH_LINES_PER_FILE = 10
    MAX_NEW_FILE_SUMMARY_LENGTH = 200
    
    # File size thresholds  
    LARGE_FILE_THRESHOLD_KB = 50
    HUGE_FILE_THRESHOLD_KB = 200
    
    # Content strategies
    INCLUDE_PATCH_FOR_NEW_FILES = False
    INCLUDE_FILE_SUMMARIES = True
    FILTER_SECURITY_RELEVANT_ONLY = True
```

### 7. Success Metrics

- **Prompt Size**: Reduce average prompt size by 50-70% for new module PRs
- **Processing Time**: Maintain or improve current ~40s analysis time
- **Analysis Quality**: Maintain same level of risk detection accuracy
- **Token Efficiency**: Stay well under 25k token Read tool limits

### 8. Risks and Mitigations

#### Risk: Loss of Analysis Context
- **Mitigation**: Ensure Claude Code Read tool instructions are clear
- **Fallback**: Include patch excerpts for high-risk file types

#### Risk: Template Complexity
- **Mitigation**: Keep templates simple, move complexity to Python logic
- **Testing**: Extensive testing with various PR types

#### Risk: File Summary Accuracy  
- **Mitigation**: Conservative summaries, focus on file type/purpose patterns
- **Validation**: Manual review of generated summaries

### 9. Future Enhancements

- **ML-based file importance scoring** for prioritized analysis
- **Diff context analysis** to identify security-relevant changes automatically  
- **Cross-file dependency analysis** for new modules
- **Incremental analysis** for large PRs with file batching

## Conclusion

This smart prompt creation approach will significantly improve efficiency for PRs with many new files while maintaining analysis quality. The status-aware strategy eliminates redundancy and optimizes token usage, making the system more scalable for large feature additions like new Spring AI modules.
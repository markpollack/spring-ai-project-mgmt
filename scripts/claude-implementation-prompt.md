# Claude Code Implementation Prompt

## Task
Implement label and state filtering functionality for the GitHub Issues collector JBang script. The implementation should add command-line options to filter issues by state (open/closed/all) and by labels, while maintaining full backward compatibility.

## Context
You are working on a Spring AI project management repository. The main script is located at:
- `../src/main/java/com/example/CollectGithubIssues.java` (JBang script)

## Implementation Resources
Please read these files first to understand the requirements and implementation plan:
1. `github-issues-filtering-plan.md` - High-level overview and requirements
2. `github-issues-filtering-implementation-checklist.md` - Detailed step-by-step checklist

## Key Requirements
- Add support for `--state open|closed|all` (default: closed)
- Add support for `--labels label1,label2,label3` (comma-separated)
- Add support for `--label-mode any|all` (default: any)
- Switch from repository API to GitHub Search API for filtering
- Maintain full backward compatibility
- All existing functionality must continue to work unchanged

## Implementation Approach
1. Use the detailed checklist in `github-issues-filtering-implementation-checklist.md` to track progress
2. Check off each item as you complete it
3. Test thoroughly with dry-run mode before making live API calls
4. Focus on one phase at a time as outlined in the checklist

## Testing Commands
Once implemented, test with these commands:
```bash
# Basic functionality
./CollectGithubIssues.java --repo spring-projects/spring-ai --dry-run

# State filtering
./CollectGithubIssues.java --repo spring-projects/spring-ai --state open --dry-run

# Label filtering
./CollectGithubIssues.java --repo spring-projects/spring-ai --labels bug --dry-run

# Combined filtering
./CollectGithubIssues.java --repo spring-projects/spring-ai --state open --labels bug,enhancement --label-mode any --dry-run
```

## Success Criteria
- All checkboxes in the implementation checklist are completed
- All test commands work correctly
- Existing functionality remains unchanged
- Error handling provides clear messages
- Help text is accurate and complete

Please start by reading the implementation plan files and then work through the checklist systematically.
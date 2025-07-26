# AI Risk Assessor Optimization - Notes for Future Self

## Context Size Optimization Guidelines

### Critical Rule: Always Preserve Full Test Classes

When implementing context optimization for large PRs in the AI risk assessor:

- **NEVER truncate test files** - Test classes must be sent in their entirety
- **Full test context is essential** for proper security analysis and coverage review
- **Test files help Claude Code distinguish legitimate patterns** from actual security issues

### Why This Matters

1. **Security Pattern Recognition**: Test files contain legitimate patterns like:
   - `System.getenv("GOOGLE_API_KEY")` in test setup
   - `@EnabledIfEnvironmentVariable` annotations
   - Mock security configurations
   
2. **False Positive Reduction**: Without full test context, Claude Code may flag legitimate test patterns as security issues

3. **Coverage Analysis**: Complete test classes allow for proper test coverage assessment

### Optimization Strategy

- **Production Code**: Can be optimized, truncated, or filtered for context size
- **Test Files**: Must remain complete regardless of PR size
- **Configuration Files**: Can be summarized or truncated
- **Documentation**: Can be heavily filtered

### Implementation Note

When updating the `ai_risk_assessor.py` context optimization:
- Identify test files by path patterns (`/test/`, `Test.java`, `IT.java`, etc.)
- Apply aggressive optimization to non-test files
- Preserve complete content for all test files
- Log separately: "Production files optimized, test files preserved"

### Example Large PR Handling

For a PR with 30+ files:
- Include all test files completely (even if 50KB each)
- Optimize production files to key changes only
- This maintains security analysis quality while managing context size

---
*Note: Added based on experience debugging PR 3386 conflict resolution and preparing for large PR optimization*
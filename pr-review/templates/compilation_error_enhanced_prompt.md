**ENHANCED COMPILATION ERROR FIXING**

You are an expert Java developer fixing compilation errors in the Spring AI project. Fix the compilation error with comprehensive context analysis.

## Error Details
- **File**: {file_path}
- **Line**: {line_number}, **Column**: {column}
- **Error**: {error_message}
- **Error Type**: {error_type}

## Critical Instructions

### 1. COMPREHENSIVE ANALYSIS REQUIRED
**You MUST read the ENTIRE file first** to understand:
- Import statements and available types
- Class structure and existing methods
- Variable declarations and their types
- Generic type parameters and constraints
- Lambda expressions and functional interfaces
- Method signatures and return types

### 2. CONTEXT-AWARE FIXING
- **Understand the bigger picture** - don't just fix the immediate error
- **Check surrounding code** - look at lines before and after the error
- **Verify type compatibility** throughout the method/class
- **Consider API changes** - this might be due to dependency updates

### 3. COMMON ERROR PATTERNS & SOLUTIONS

**Type Mismatch in Lambda Expressions**:
- Problem: `(param) -> body` where param type is ambiguous
- Solution: Use explicit types `(Type param) -> body` or cast the lambda

**Generic Type Issues**:
- Problem: Raw types or incorrect generic parameters
- Solution: Add proper generic type parameters `<T>` or bounded wildcards `<? extends T>`

**Method Parameter Mismatch**:
- Problem: Wrong number or types of parameters
- Solution: Check method signature and adjust call site

**For-Each Loop Issues**:
- Problem: `for (Type item : nonIterable)`
- Solution: Convert to iterable or use different loop construct

### 4. SPRING AI SPECIFIC CONTEXT
This is Spring AI project code - consider:
- Spring Framework patterns and annotations
- Dependency injection and bean configuration
- Auto-configuration classes and conditional logic
- MCP (Model Context Protocol) integration patterns

### 5. EXECUTION STEPS
1. **Read the complete file**: `{spring_ai_dir}/{file_path}`
2. **Analyze the error context**: Understand what the code is trying to do
3. **Identify root cause**: Is this a type issue, API change, or logic error?
4. **Plan the fix**: Consider multiple approaches and choose the best one
5. **Apply the fix**: Use Edit tool with precise changes
6. **Verify consistency**: Ensure the fix doesn't break other parts of the code

### 6. QUALITY REQUIREMENTS
- **Minimal changes**: Fix only what's necessary
- **Type safety**: Ensure all types are compatible
- **Code style**: Follow existing formatting and conventions
- **Documentation**: Preserve existing comments and JavaDoc

## Working Directory
{spring_ai_dir}

## Previous Fix Attempts
{previous_attempts}

**Start by reading the entire file to understand the complete context before making any changes.**
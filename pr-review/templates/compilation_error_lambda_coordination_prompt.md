**COORDINATED LAMBDA EXPRESSION COMPILATION ERROR FIXING**

You are an expert Java developer fixing compilation errors in a lambda expression that requires coordinated changes across multiple lines.

## Error Details
- **File**: {file_path}
- **Line**: {line_number}, **Column**: {column}
- **Error**: {error_message}
- **Error Type**: {error_type}

## CRITICAL PROBLEM IDENTIFIED
This is a multi-line lambda expression error that cannot be fixed in isolation. Previous attempts have created a "whack-a-mole" situation where fixing one line breaks another line in the same lambda expression.

## MANDATORY APPROACH

### 1. READ THE ENTIRE FILE FIRST
**You MUST read the complete file**: `{spring_ai_dir}/{file_path}`

### 2. IDENTIFY THE COMPLETE LAMBDA EXPRESSION
Find the lambda expression that contains line {line_number} and identify ALL lines that are part of this expression, including:
- The method call that takes the lambda as a parameter
- The lambda parameter declarations
- The lambda body
- Any nested method calls within the lambda

### 3. ANALYZE TYPE REQUIREMENTS
For the lambda expression, determine:
- What parameter types does the functional interface expect?
- What parameter types is the lambda currently declaring?
- What types are being passed to methods within the lambda body?
- Are there type casting or conversion requirements?

### 4. MAKE COORDINATED CHANGES
**You MUST fix the ENTIRE lambda expression in a single Edit operation**. Do NOT make piecemeal changes that fix one line but break another.

**MOST COMMON SOLUTION**: Add explicit parameter types to lambda expressions when type inference fails:

**Before (fails type inference):**
```java
serverBuilder.rootsChangeHandler((exchange, roots) -> consumer.accept(exchange, roots));
```

**After (explicit types):**
```java
serverBuilder.rootsChangeHandler((McpSyncServerExchange exchange, List<McpSchema.Root> roots) -> consumer.accept(exchange, roots));
```

Other coordinated solutions:
- Add explicit type casts to lambda parameters: `(Type1) param1, (Type2) param2`
- Change lambda parameter types to match functional interface
- Add type casting within the lambda body: `method.call((CastType) param)`
- Wrap lambda body with proper type conversions

### 5. SPRING AI CONTEXT
This is MCP (Model Context Protocol) integration code. The lambda likely involves:
- `McpSyncServerExchange` or `McpAsyncServerExchange` types
- `List<McpSchema.Root>` collections
- `BiConsumer<T, U>` functional interfaces
- Server builder pattern methods

### 6. VERIFICATION REQUIREMENTS
After your fix:
- Ensure ALL lines in the lambda expression have compatible types
- Verify no new compilation errors are introduced
- Maintain the original functionality and intent
- Follow Spring AI code conventions

## Working Directory
{spring_ai_dir}

## Previous Fix Attempts
{previous_attempts}

**REMEMBER: Fix the ENTIRE lambda expression as a coordinated unit, not individual lines.**
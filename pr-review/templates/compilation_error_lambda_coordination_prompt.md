**LAMBDA COMPILATION ERROR FIXING**

Fix the lambda expression compilation error in {file_path}.

## Error Details
- **File**: {file_path}
- **Line**: {line_number}, **Column**: {column}
- **Error**: {error_message}
- **Error Type**: {error_type}

## Instructions
1. **Read the file**: `{spring_ai_dir}/{file_path}`
2. **Find the lambda**: Locate the lambda expression around line {line_number}
3. **Fix type inference**: Most lambda errors are fixed by adding explicit parameter types

## Most Common Fix
If you see `(param1, param2) -> body` and get type errors, change to:
`(Type1 param1, Type2 param2) -> body`

Example:
- Before: `(exchange, roots) -> consumer.accept(exchange, roots)`
- After: `(McpSyncServerExchange exchange, List<McpSchema.Root> roots) -> consumer.accept(exchange, roots)`

## Working Directory
{spring_ai_dir}

## Previous Fix Attempts
{previous_attempts}

**Fix the lambda by adding explicit parameter types where type inference fails.**
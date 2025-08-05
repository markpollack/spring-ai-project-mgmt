**CRITICAL: LAMBDA PARAMETER TYPE FIXING**

You MUST add explicit parameter types to the lambda expression. DO NOT remove types.

## Error Context
- **File**: {file_path}
- **Line**: {line_number}, **Column**: {column}  
- **Error**: {error_message}

## MANDATORY STEPS
1. **Read the file**: `{spring_ai_dir}/{file_path}`
2. **Find line {line_number}**: Look for a lambda expression like `(param1, param2) -> ...`
3. **CRITICAL**: If you see `(exchange, roots) ->`, you MUST change it to `(McpSyncServerExchange exchange, List<McpSchema.Root> roots) ->`

## THE EXACT FIX REQUIRED
**WRONG (causes compilation error):**
```java
serverBuilder.rootsChangeHandler((exchange, roots) -> consumer.accept(exchange, roots));
```

**CORRECT (fixes compilation error):**
```java
serverBuilder.rootsChangeHandler((McpSyncServerExchange exchange, List<McpSchema.Root> roots) -> consumer.accept(exchange, roots));
```

## CRITICAL RULES
- ❌ **NEVER** remove parameter types from lambdas
- ❌ **NEVER** use type inference `(exchange, roots)` - this CAUSES the error
- ✅ **ALWAYS** use explicit types `(McpSyncServerExchange exchange, List<McpSchema.Root> roots)`
- ✅ The error "incompatible parameter types in lambda expression" means ADD types, not remove them

## Working Directory
{spring_ai_dir}

## Previous Fix Attempts  
{previous_attempts}

**CRITICAL: Change `(exchange, roots)` to `(McpSyncServerExchange exchange, List<McpSchema.Root> roots)` - DO NOT do the opposite!**
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
3. **Reference MCP SDK**: Check `{mcp_sdk_dir}` for MCP interface definitions and method signatures
4. **Fix type inference**: Add explicit parameter types based on actual method signatures

## MCP SDK Reference
The MCP Java SDK is available at `{mcp_sdk_dir}` with complete interface definitions.
Key interfaces to check:
- `{mcp_sdk_dir}/mcp/src/main/java/io/modelcontextprotocol/server/McpSyncServerExchange.java`
- `{mcp_sdk_dir}/mcp/src/main/java/io/modelcontextprotocol/spec/McpSchema.java`

## Most Common Fix
If you see `(param1, param2) -> body` and get type errors:
1. Look up the actual method signature in the MCP SDK
2. Add explicit parameter types: `(Type1 param1, Type2 param2) -> body`

Example:
- Before: `(exchange, roots) -> consumer.accept(exchange, roots)`
- After: `(McpSyncServerExchange exchange, List<McpSchema.Root> roots) -> consumer.accept(exchange, roots)`

## Working Directory
{spring_ai_dir}

## Previous Fix Attempts
{previous_attempts}

**Fix the lambda by looking up actual types in the MCP SDK and adding explicit parameter types.**
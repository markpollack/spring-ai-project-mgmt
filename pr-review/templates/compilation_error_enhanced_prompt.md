**COMPILATION ERROR FIXING**

Fix the Java compilation error in {file_path}.

## Error Details
- **File**: {file_path}
- **Line**: {line_number}, **Column**: {column}
- **Error**: {error_message}
- **Error Type**: {error_type}

## Instructions
1. **Read the file**: `{spring_ai_dir}/{file_path}`
2. **Analyze the error**: Understand what the code is trying to do at line {line_number}
3. **Reference MCP SDK**: If the error involves MCP types, check `{mcp_sdk_dir}` for interface definitions
4. **Apply the fix**: Use the Edit tool to make the necessary change

## MCP SDK Reference
If this error involves MCP types (McpSyncServerExchange, McpSchema, etc.), the complete interface definitions are available at:
- `{mcp_sdk_dir}/mcp/src/main/java/io/modelcontextprotocol/server/`
- `{mcp_sdk_dir}/mcp/src/main/java/io/modelcontextprotocol/spec/`

## Common Solutions  
- **Type mismatches**: Add explicit types or casts where needed
- **Lambda issues**: CRITICAL - Add explicit parameter types `(Type param) -> body` - NEVER remove types
- **Missing imports**: Add import statements for missing classes
- **Method signatures**: Check MCP SDK for actual API definitions

## CRITICAL FOR LAMBDA ERRORS
If error message contains "incompatible parameter types in lambda expression":
- ❌ **WRONG**: Remove parameter types `(param1, param2) ->` 
- ✅ **CORRECT**: Add explicit parameter types `(Type1 param1, Type2 param2) ->`

## Working Directory
{spring_ai_dir}

## Previous Fix Attempts
{previous_attempts}

**Read the entire file first, then make the minimal change needed to fix the error.**
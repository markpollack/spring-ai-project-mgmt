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

Working directory: {spring_ai_dir}
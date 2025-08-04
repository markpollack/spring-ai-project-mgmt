Fix the missing symbol compilation error in {file_path}.

Error: {error_message}
Location: Line {line_number}, Column {column}

This is a missing symbol error (class, method, or variable not found). Please:
1. Read the file {spring_ai_dir}/{file_path}
2. Understand what symbol is missing
3. Add the necessary import statement, or
4. Check if the class/method name has changed, or
5. Verify the dependency is available

Common fixes:
- Add import: import package.ClassName;
- Fix typo in class/method name
- Check if API has changed in dependencies
- Verify the symbol exists in the current classpath

Use the Edit tool to apply your fix.

Working directory: {spring_ai_dir}
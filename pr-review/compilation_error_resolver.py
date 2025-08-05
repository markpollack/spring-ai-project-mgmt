#!/usr/bin/env python3
"""
Compilation Error Detection and Resolution Component

Automatically detects and fixes common Java compilation errors in Spring AI PRs.
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
from claude_code_wrapper import ClaudeCodeWrapper

# Simple logger implementation to avoid circular imports
class Logger:
    @staticmethod
    def info(msg): print(f"\033[34m[INFO]\033[0m {msg}")
    @staticmethod
    def success(msg): print(f"\033[32m[SUCCESS]\033[0m {msg}")
    @staticmethod
    def warn(msg): print(f"\033[33m[WARN]\033[0m {msg}")
    @staticmethod
    def error(msg): print(f"\033[31m[ERROR]\033[0m {msg}")


@dataclass
class CompilationError:
    file_path: str
    line_number: int
    column: int
    error_type: str
    message: str
    severity: str = "ERROR"
    auto_fixable: bool = False
    fix_description: str = ""


class CompilationErrorResolver:
    """Detects and automatically resolves common Java compilation errors"""
    
    def __init__(self, spring_ai_dir: Path):
        self.spring_ai_dir = spring_ai_dir
        self.logs_dir = spring_ai_dir.parent / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        self.templates_dir = spring_ai_dir.parent / "templates"
        self.claude_wrapper = ClaudeCodeWrapper(logs_dir=self.logs_dir)
        self.auto_fix_patterns = {
            'incorrect_override': {
                'pattern': r'method does not override or implement a method from a supertype',
                'handler': self._fix_incorrect_override,
                'description': 'Remove incorrect @Override annotation'
            },
            'missing_import': {
                'pattern': r'cannot find symbol.*class (\w+)',
                'handler': self._fix_missing_import,
                'description': 'Add missing import statement'
            },
            'method_signature_mismatch': {
                'pattern': r'method .* in class .* cannot be applied to given types',
                'handler': self._fix_method_signature,
                'description': 'Fix method signature mismatch'
            },
            'access_modifier_conflict': {
                'pattern': r'attempting to assign weaker access privileges',
                'handler': self._fix_access_modifier,
                'description': 'Fix access modifier conflict'
            },
            'generic_type_mismatch': {
                'pattern': r'incompatible types: .* cannot be converted to .*',
                'handler': self._fix_generic_types,
                'description': 'Fix generic type mismatch'
            },
            'missing_semicolon': {
                'pattern': r"';' expected",
                'handler': self._fix_missing_semicolon,
                'description': 'Add missing semicolon'
            }
        }
    
    def load_prompt_template(self, template_name: str, **kwargs) -> str:
        """Load and populate prompt template with provided variables"""
        template_path = self.templates_dir / f"{template_name}.md"
        
        if not template_path.exists():
            Logger.error(f"Template not found: {template_path}")
            return f"Template {template_name} not found"
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Replace placeholders with kwargs
            formatted_prompt = template_content.format(**kwargs)
            
            Logger.info(f"✅ Loaded template: {template_name}")
            return formatted_prompt
            
        except KeyError as e:
            Logger.error(f"Missing template variable: {e}")
            return f"Template {template_name} missing variable: {e}"
        except Exception as e:
            Logger.error(f"Error loading template {template_name}: {e}")
            return f"Error loading template {template_name}: {e}"
    
    def detect_compilation_errors(self) -> List[CompilationError]:
        """Run compilation and detect errors using the same command as the final build"""
        Logger.info("🔍 Detecting compilation errors...")
        
        try:
            # Use the fast compilation command that matches the build behavior
            result = subprocess.run([
                "mvnd", "clean", "package", 
                "-Dmaven.javadoc.skip=true", 
                "-DskipTests"
            ], 
            cwd=self.spring_ai_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
            )
            
            if result.returncode == 0:
                Logger.success("✅ No compilation errors detected")
                return []
            
            # Parse compilation errors from output
            errors = self._parse_compilation_errors(result.stdout, result.stderr)
            Logger.warn(f"Found {len(errors)} compilation error(s)")
            
            return errors
            
        except subprocess.TimeoutExpired:
            Logger.error("Compilation check timed out")
            return []
        except Exception as e:
            Logger.error(f"Error running compilation check: {e}")
            return []
    
    def _parse_compilation_errors(self, stdout: str, stderr: str) -> List[CompilationError]:
        """Parse Maven compilation output to extract error details"""
        errors = []
        combined_output = stdout + "\n" + stderr
        
        # Debug: Log the combined output to see what we're parsing
        Logger.info(f"🔍 DEBUG: Parsing compilation output ({len(combined_output)} chars)")
        Logger.info(f"🔍 DEBUG: stdout lines: {len(stdout.split(chr(10)))}")
        Logger.info(f"🔍 DEBUG: stderr lines: {len(stderr.split(chr(10)))}")
        
        # Maven error pattern: [ERROR] /path/to/file:[line,column] error message
        error_pattern = r'\[ERROR\]\s+([^:]+):?\[(\d+),(\d+)\]\s+(.+)'
        
        matches = list(re.finditer(error_pattern, combined_output, re.MULTILINE))
        Logger.info(f"🔍 DEBUG: Found {len(matches)} regex matches")
        
        # Use a set to track unique errors and avoid duplicates
        seen_errors = set()
        
        for i, match in enumerate(matches):
            file_path = match.group(1).strip()
            line_num = int(match.group(2))
            column = int(match.group(3))
            message = match.group(4).strip()
            
            Logger.info(f"🔍 DEBUG: Match {i+1}: {file_path}:{line_num}:{column} - {message}")
            
            # Make file path relative to spring_ai_dir for deduplication
            relative_file_path = file_path
            if self.spring_ai_dir.as_posix() in file_path:
                relative_file_path = file_path.replace(self.spring_ai_dir.as_posix() + "/", "")
            
            # Create unique key for deduplication (file:line:column:message)
            error_key = (relative_file_path, line_num, column, message)
            
            if error_key in seen_errors:
                Logger.info(f"🔍 DEBUG: Skipping duplicate error: {relative_file_path}:{line_num}:{column}")
                continue
            
            seen_errors.add(error_key)
            
            # Determine error type and if it's auto-fixable
            error_type, auto_fixable, fix_desc = self._classify_error(message)
            
            errors.append(CompilationError(
                file_path=relative_file_path,
                line_number=line_num,
                column=column,
                error_type=error_type,
                message=message,
                auto_fixable=auto_fixable,
                fix_description=fix_desc
            ))
        
        Logger.info(f"🔍 DEBUG: Created {len(errors)} unique CompilationError objects (filtered from {len(matches)} matches)")
        return errors
    
    def _classify_error(self, message: str) -> Tuple[str, bool, str]:
        """Classify error type and determine if auto-fixable"""
        # Check for specific patterns first for better template selection
        for error_type, config in self.auto_fix_patterns.items():
            if re.search(config['pattern'], message, re.IGNORECASE):
                return error_type, True, config['description']
        
        # Enhanced classification for signature mismatches and dependency changes
        if 'incompatible types' in message and 'cannot be converted' in message:
            # Check for specific patterns that suggest dependency signature changes
            if any(keyword in message.lower() for keyword in [
                'server', 'exchange', 'mcp', 'protocol', 'context', 'client', 'async', 'sync'
            ]):
                error_type = 'dependency_signature_mismatch'
            else:
                error_type = 'generic_type_mismatch'
        elif 'cannot find symbol' in message:
            error_type = 'missing_symbol'
        elif 'method does not override' in message:
            error_type = 'incorrect_override'
        elif 'method' in message and ('cannot be applied' in message or 'does not exist' in message):
            error_type = 'method_signature_mismatch'
        else:
            error_type = 'compilation_error'
        
        # ALL errors are now auto-fixable via Claude Code
        return error_type, True, 'Fix via Claude Code AI'
    
    def _is_lambda_related_error(self, error: CompilationError) -> bool:
        """Enhanced detection for lambda-related compilation errors"""
        
        # 1. Direct lambda keywords in error message
        lambda_keywords = [
            "lambda expression", 
            "incompatible parameter types in lambda",
            "lambda parameter",
            "functional interface"
        ]
        
        if any(keyword in error.message.lower() for keyword in lambda_keywords):
            return True
        
        # 2. Context-based detection: check if error occurs on a line with lambda syntax
        try:
            file_path = self.spring_ai_dir / error.file_path
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Check the error line and surrounding lines for lambda patterns
                error_line_idx = error.line_number - 1  # Convert to 0-based index
                lines_to_check = []
                
                # Include current line and a few lines around it for context
                for i in range(max(0, error_line_idx - 2), min(len(lines), error_line_idx + 3)):
                    lines_to_check.append(lines[i])
                
                # Look for lambda patterns in the context
                context_text = ''.join(lines_to_check)
                lambda_patterns = [
                    r'->', # Lambda arrow
                    r'\([^)]*\)\s*->', # Lambda with parameters
                    r'Consumer<', # Common functional interfaces
                    r'Function<',
                    r'BiConsumer<',
                    r'BiFunction<',
                    r'Supplier<',
                    r'Predicate<'
                ]
                
                for pattern in lambda_patterns:
                    if re.search(pattern, context_text):
                        Logger.info(f"🔍 Lambda context detected: pattern '{pattern}' found near error")
                        return True
                        
        except Exception as e:
            Logger.warn(f"Could not analyze lambda context for {error.file_path}: {e}")
        
        # 3. Type signature analysis - common lambda-related type mismatches
        type_mismatch_patterns = [
            r'cannot be converted to.*Exchange', # Server exchange patterns
            r'Object cannot be converted to.*Consumer', # Consumer type issues
            r'Object cannot be converted to.*Function', # Function type issues
        ]
        
        for pattern in type_mismatch_patterns:
            if re.search(pattern, error.message):
                Logger.info(f"🔍 Lambda type pattern detected: '{pattern}'")
                return True
        
        return False
    
    def auto_resolve_errors(self, errors: List[CompilationError]) -> Tuple[int, List[str]]:
        """Automatically resolve fixable compilation errors"""
        resolved_count = 0
        resolution_log = []
        
        Logger.info(f"🔧 Attempting to auto-resolve {len([e for e in errors if e.auto_fixable])} fixable errors...")
        
        for error in errors:
            if not error.auto_fixable:
                continue
                
            try:
                # Try specific handler first if available
                if error.error_type in self.auto_fix_patterns:
                    handler = self.auto_fix_patterns[error.error_type]['handler']
                    if handler(error):
                        resolved_count += 1
                        resolution_log.append(f"✅ Fixed {error.error_type} in {error.file_path}:{error.line_number}")
                        Logger.info(f"🔧 Applied fix attempt: {error.fix_description} in {error.file_path} - validation pending")
                        continue
                
                # Fall back to generic Claude Code handler
                if self._fix_with_claude_code(error):
                    resolved_count += 1
                    resolution_log.append(f"✅ Fixed {error.error_type} in {error.file_path}:{error.line_number}")
                    Logger.info(f"🔧 Applied Claude Code fix attempt for {error.error_type} in {error.file_path} - validation pending")
                else:
                    resolution_log.append(f"❌ Failed to fix {error.error_type} in {error.file_path}:{error.line_number}")
                    
            except Exception as e:
                Logger.warn(f"Error auto-resolving {error.file_path}:{error.line_number}: {e}")
                resolution_log.append(f"❌ Exception fixing {error.file_path}: {str(e)}")
        
        Logger.info(f"Auto-resolved {resolved_count}/{len([e for e in errors if e.auto_fixable])} fixable errors")
        return resolved_count, resolution_log
    
    def _fix_incorrect_override(self, error: CompilationError) -> bool:
        """Remove incorrect @Override annotation"""
        file_path = self.spring_ai_dir / error.file_path
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check if the line before contains @Override
            target_line = error.line_number - 1  # 0-indexed
            if target_line > 0 and '@Override' in lines[target_line - 1]:
                # Remove the @Override line
                lines.pop(target_line - 1)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                    
                return True
                
        except Exception as e:
            Logger.warn(f"Error fixing @Override in {file_path}: {e}")
            
        return False
    
    def _fix_missing_import(self, error: CompilationError) -> bool:
        """Add missing import statement (basic implementation)"""
        # This would require more sophisticated analysis to determine correct import
        Logger.info(f"Missing import auto-fix not yet implemented for: {error.file_path}")
        return False
    
    def _fix_method_signature(self, error: CompilationError) -> bool:
        """Fix method signature mismatch (basic implementation)"""
        Logger.info(f"Method signature auto-fix not yet implemented for: {error.file_path}")
        return False
    
    def _fix_access_modifier(self, error: CompilationError) -> bool:
        """Fix access modifier conflict (basic implementation)"""
        Logger.info(f"Access modifier auto-fix not yet implemented for: {error.file_path}")
        return False
    
    def _fix_generic_types(self, error: CompilationError) -> bool:
        """Fix generic type mismatch using enhanced Claude Code templates"""
        Logger.info(f"🤖 Using Claude Code to fix type mismatch in {error.file_path}")
        
        try:
            # Select template based on error pattern - lambda errors need special coordination
            is_lambda_error = self._is_lambda_related_error(error)
            if is_lambda_error:
                template_name = "compilation_error_lambda_coordination_prompt"
                Logger.info("🎯 Using lambda coordination template for lambda-related error")
            elif error.error_type == 'dependency_signature_mismatch':
                template_name = "compilation_error_enhanced_prompt"
                Logger.info("🔍 Using enhanced template for dependency signature mismatch")
            else:
                template_name = "compilation_error_enhanced_prompt"
            
            # Track previous attempts for this file to provide context
            file_key = f"{error.file_path}:{error.line_number}"
            if not hasattr(self, '_fix_attempts'):
                self._fix_attempts = {}
            
            attempt_count = self._fix_attempts.get(file_key, 0) + 1
            self._fix_attempts[file_key] = attempt_count
            
            # Create previous attempts context
            previous_attempts = ""
            if attempt_count > 1:
                previous_attempts = f"""
CRITICAL: This is attempt #{attempt_count} to fix this type mismatch error.
Previous attempts have been made but the error persists or new type issues have been introduced.
This suggests a cascading type compatibility issue. You MUST:
1. Read the ENTIRE file to understand all type relationships
2. Look for related lambda expressions, generic types, and method signatures
3. Consider that multiple lines may need coordinated changes
4. Verify that your fix doesn't introduce new type mismatches elsewhere
"""
            
            # Load and format the enhanced prompt template
            prompt = self.load_prompt_template(
                template_name,
                file_path=error.file_path,
                line_number=error.line_number,
                column=error.column,
                error_message=error.message,
                error_type="generic_type_mismatch",
                spring_ai_dir=self.spring_ai_dir,
                previous_attempts=previous_attempts
            )
            
            # Use ClaudeCodeWrapper for reliable execution with longer timeout
            result = self.claude_wrapper.analyze_from_text(
                prompt_text=prompt,
                timeout=360,  # 6 minutes for complex type analysis
                use_json_output=False,
                show_progress=True
            )
            
            if result['success']:
                Logger.info(f"🔧 Claude Code applied changes to fix type mismatch in {error.file_path} - validation pending")
                
                # Run Java formatter after the fix
                self._apply_java_formatter()
                
                return True
            else:
                Logger.warn(f"Claude Code failed to fix type mismatch: {result.get('error', 'Unknown error')}")
                if result.get('stderr'):
                    Logger.warn(f"Claude stderr: {result['stderr']}")
                return False
                
        except Exception as e:
            Logger.warn(f"Error using Claude Code to fix type mismatch in {error.file_path}: {e}")
            return False
    
    def _fix_missing_semicolon(self, error: CompilationError) -> bool:
        """Use Claude Code to intelligently fix missing semicolon"""
        try:
            # Create a prompt for Claude Code to fix the compilation error
            prompt = f"""Fix the Java compilation error in {error.file_path} at line {error.line_number}.

Error message: {error.message}
Error type: Missing semicolon

Please:
1. Read the file {error.file_path} and understand the context around line {error.line_number}
2. Fix the missing semicolon error by editing the file directly using the Edit tool
3. Ensure the fix maintains proper Java syntax and code style
4. DO NOT run the Java formatter yourself - this will be done separately

The error indicates a semicolon is expected. Please analyze the code context and add the semicolon in the correct location.

Working directory: {self.spring_ai_dir}"""

            # Use ClaudeCodeWrapper for reliable execution
            Logger.info(f"🤖 Using Claude Code to fix semicolon error in {error.file_path}")
            
            result = self.claude_wrapper.analyze_from_text(
                prompt_text=prompt,
                timeout=120,  # 2 minutes
                use_json_output=False,  # Text output is fine for this
                show_progress=True
            )
            
            if result['success']:
                Logger.success(f"Claude Code successfully processed semicolon fix for {error.file_path}")
                
                # Run Java formatter after the fix
                self._apply_java_formatter()
                
                return True
            else:
                Logger.warn(f"Claude Code failed to fix semicolon error: {result['error']}")
                if result.get('stderr'):
                    Logger.warn(f"Claude stderr: {result['stderr']}")
                return False
                
        except Exception as e:
            Logger.warn(f"Error using Claude Code to fix semicolon in {error.file_path}: {e}")
            return False
    
    def _apply_java_formatter(self):
        """Apply Java formatter after code changes"""
        try:
            Logger.info("🎨 Applying Java formatter after code fix...")
            result = subprocess.run([
                "mvnd", "spring-javaformat:apply", "-q", "-Dmvnd.rollingWindowSize=0"
            ], 
            cwd=self.spring_ai_dir,
            capture_output=True,
            text=True,
            timeout=60
            )
            
            if result.returncode == 0:
                Logger.success("✅ Java formatter applied successfully")
            else:
                Logger.warn(f"Java formatter warning: {result.stderr}")
                
        except Exception as e:
            Logger.warn(f"Error applying Java formatter: {e}")
    
    def _fix_with_claude_code(self, error: CompilationError) -> bool:
        """Universal Claude Code handler for any compilation error with enhanced context"""
        Logger.info(f"🤖 Using Claude Code to fix {error.error_type} in {error.file_path}")
        
        try:
            # Select template based on error pattern
            is_lambda_error = self._is_lambda_related_error(error)
            if is_lambda_error:
                template_name = "compilation_error_lambda_coordination_prompt"
                Logger.info("🎯 Using lambda coordination template for lambda-related error")
            elif error.error_type == 'dependency_signature_mismatch':
                template_name = "compilation_error_enhanced_prompt"
                Logger.info("🔍 Using enhanced template for dependency signature mismatch")
            else:
                template_name = "compilation_error_enhanced_prompt"
            
            # Track previous attempts for this file to provide context
            file_key = f"{error.file_path}:{error.line_number}"
            if not hasattr(self, '_fix_attempts'):
                self._fix_attempts = {}
            
            attempt_count = self._fix_attempts.get(file_key, 0) + 1
            self._fix_attempts[file_key] = attempt_count
            
            # Create previous attempts context
            previous_attempts = ""
            if attempt_count > 1:
                previous_attempts = f"""
IMPORTANT: This is attempt #{attempt_count} to fix this error.
Previous attempts have partially resolved the issue but new errors may have been introduced.
Consider the entire file context and make sure your fix doesn't break other parts of the code.
Look for related type mismatches or missing imports that might be causing cascading errors.
"""
            
            # Load and format the enhanced prompt template with more context
            prompt = self.load_prompt_template(
                template_name,
                file_path=error.file_path,
                line_number=error.line_number,
                column=error.column,
                error_message=error.message,
                error_type=error.error_type,
                spring_ai_dir=self.spring_ai_dir,
                previous_attempts=previous_attempts
            )
            
            # Use ClaudeCodeWrapper for execution with descriptive logging
            log_prefix = f"compilation-error-{error.error_type}-{Path(error.file_path).stem}-line{error.line_number}"
            result = self.claude_wrapper.analyze_from_text(
                prompt_text=prompt,
                timeout=360,  # 6 minutes for more complex analysis
                use_json_output=False,
                show_progress=True,
                log_prefix=log_prefix
            )
            
            if result['success']:
                Logger.info(f"🔧 Claude Code applied changes to fix {error.error_type} in {error.file_path} - validation pending")
                
                # Run Java formatter after the fix
                self._apply_java_formatter()
                
                return True
            else:
                Logger.warn(f"Claude Code failed to fix {error.error_type}: {result.get('error', 'Unknown error')}")
                if result.get('stderr'):
                    Logger.warn(f"Claude stderr: {result['stderr']}")
                return False
                
        except Exception as e:
            Logger.warn(f"Error using Claude Code to fix {error.error_type} in {error.file_path}: {e}")
            return False
    
    def generate_error_report(self, errors: List[CompilationError], resolution_log: List[str]) -> str:
        """Generate detailed compilation error report"""
        if not errors:
            return "✅ No compilation errors detected"
        
        auto_fixable = [e for e in errors if e.auto_fixable]
        manual_review = [e for e in errors if not e.auto_fixable]
        
        report = f"""## 🔨 Compilation Error Analysis

### Summary
- **Total Errors**: {len(errors)}
- **Auto-fixable**: {len(auto_fixable)}
- **Require Manual Review**: {len(manual_review)}

### Auto-fixable Errors
"""
        
        for error in auto_fixable:
            report += f"""
#### {error.file_path}:{error.line_number}
- **Type**: {error.error_type}
- **Fix**: {error.fix_description}
- **Message**: {error.message}
"""
        
        if manual_review:
            report += "\n### Manual Review Required\n"
            for error in manual_review:
                report += f"""
#### {error.file_path}:{error.line_number}
- **Type**: {error.error_type}
- **Message**: {error.message}
- **Action**: Manual code review and fix needed
"""
        
        if resolution_log:
            report += "\n### Resolution Log\n"
            for log_entry in resolution_log:
                report += f"- {log_entry}\n"
        
        return report
    
    def has_unresolved_errors(self, errors: List[CompilationError]) -> bool:
        """Check if there are still unresolved compilation errors"""
        # Re-run compilation to check if errors persist
        new_errors = self.detect_compilation_errors()
        return len(new_errors) > 0


def main():
    """Command-line interface for compilation error resolver"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python3 compilation_error_resolver.py <spring_ai_directory>")
        sys.exit(1)
    
    spring_ai_dir = Path(sys.argv[1])
    resolver = CompilationErrorResolver(spring_ai_dir)
    
    # Detect errors
    errors = resolver.detect_compilation_errors()
    
    if not errors:
        print("✅ No compilation errors found")
        sys.exit(0)
    
    # Attempt auto-resolution
    resolved_count, resolution_log = resolver.auto_resolve_errors(errors)
    
    # Generate report
    report = resolver.generate_error_report(errors, resolution_log)
    print(report)
    
    # Check if all errors resolved
    if resolver.has_unresolved_errors(errors):
        print("❌ Some compilation errors remain - manual review required")
        sys.exit(1)
    else:
        print("✅ All compilation errors resolved successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
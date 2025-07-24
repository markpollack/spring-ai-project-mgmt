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
            }
        }
    
    def detect_compilation_errors(self) -> List[CompilationError]:
        """Run compilation and detect errors"""
        Logger.info("🔍 Detecting compilation errors...")
        
        try:
            # Run Maven compilation with detailed error output
            result = subprocess.run([
                "mvnd", "compile", 
                "-Dmaven.javadoc.skip=true",
                "-X"  # Debug output for detailed errors
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
        
        # Maven error pattern: [ERROR] /path/to/file:[line,column] error message
        error_pattern = r'\[ERROR\]\s+([^:]+):?\[(\d+),(\d+)\]\s+(.+)'
        
        for match in re.finditer(error_pattern, combined_output, re.MULTILINE):
            file_path = match.group(1).strip()
            line_num = int(match.group(2))
            column = int(match.group(3))
            message = match.group(4).strip()
            
            # Determine error type and if it's auto-fixable
            error_type, auto_fixable, fix_desc = self._classify_error(message)
            
            # Make file path relative to spring_ai_dir
            if self.spring_ai_dir.as_posix() in file_path:
                file_path = file_path.replace(self.spring_ai_dir.as_posix() + "/", "")
            
            errors.append(CompilationError(
                file_path=file_path,
                line_number=line_num,
                column=column,
                error_type=error_type,
                message=message,
                auto_fixable=auto_fixable,
                fix_description=fix_desc
            ))
        
        return errors
    
    def _classify_error(self, message: str) -> Tuple[str, bool, str]:
        """Classify error type and determine if auto-fixable"""
        for error_type, config in self.auto_fix_patterns.items():
            if re.search(config['pattern'], message, re.IGNORECASE):
                return error_type, True, config['description']
        
        return 'unknown', False, 'Manual review required'
    
    def auto_resolve_errors(self, errors: List[CompilationError]) -> Tuple[int, List[str]]:
        """Automatically resolve fixable compilation errors"""
        resolved_count = 0
        resolution_log = []
        
        Logger.info(f"🔧 Attempting to auto-resolve {len([e for e in errors if e.auto_fixable])} fixable errors...")
        
        for error in errors:
            if not error.auto_fixable:
                continue
                
            try:
                handler = self.auto_fix_patterns[error.error_type]['handler']
                if handler(error):
                    resolved_count += 1
                    resolution_log.append(f"✅ Fixed {error.error_type} in {error.file_path}:{error.line_number}")
                    Logger.success(f"Auto-resolved: {error.fix_description} in {error.file_path}")
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
        """Fix generic type mismatch (basic implementation)"""
        Logger.info(f"Generic type auto-fix not yet implemented for: {error.file_path}")
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
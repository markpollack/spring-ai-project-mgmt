#!/usr/bin/env python3
"""
Test Discovery for Spring AI PRs

Identifies affected Maven modules and generates test commands for manual verification.
This is a lightweight helper that provides guidance without enforcing rules.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class TestDiscoveryResult:
    """Results from test discovery analysis"""
    pr_number: str
    affected_modules: List[str]
    test_commands: Dict[str, str]  # command_type -> command
    changed_files: List[str]
    has_code_changes: bool
    has_test_changes: bool
    module_to_files: Dict[str, List[str]]  # module -> list of changed files


class TestDiscovery:
    """Discovers affected Maven modules and generates test commands"""
    
    def __init__(self, pr_number: str, spring_ai_dir: Path):
        self.pr_number = pr_number
        self.spring_ai_dir = Path(spring_ai_dir)
        self.cache_file = self.spring_ai_dir.parent / "context" / f"pr-{pr_number}" / "test-discovery.json"
        
    def discover(self, force_refresh: bool = False) -> TestDiscoveryResult:
        """
        Main entry point for test discovery.
        Returns cached results if available unless force_refresh is True.
        """
        # Try to load from cache first
        if not force_refresh and self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    return TestDiscoveryResult(**data)
            except Exception:
                pass  # Fall through to fresh discovery
        
        # Perform fresh discovery
        changed_files = self._get_changed_files()
        affected_modules = self._discover_affected_modules(changed_files)
        module_to_files = self._map_modules_to_files(changed_files, affected_modules)
        has_code_changes = self._has_code_changes(changed_files)
        has_test_changes = self._has_test_changes(changed_files)
        test_commands = self._generate_test_commands(affected_modules, changed_files)
        
        result = TestDiscoveryResult(
            pr_number=self.pr_number,
            affected_modules=affected_modules,
            test_commands=test_commands,
            changed_files=changed_files,
            has_code_changes=has_code_changes,
            has_test_changes=has_test_changes,
            module_to_files=module_to_files
        )
        
        # Cache the results
        self._save_to_cache(result)
        
        return result
    
    def _get_changed_files(self) -> List[str]:
        """Get list of changed files in the PR"""
        try:
            # Try GitHub CLI first
            result = subprocess.run([
                "gh", "pr", "view", self.pr_number,
                "--repo", "spring-projects/spring-ai",
                "--json", "files", "--jq", ".files[].path"
            ], capture_output=True, text=True, check=True)
            
            files = result.stdout.strip().split('\n')
            return [f for f in files if f]
            
        except subprocess.CalledProcessError:
            # Fallback to git diff if PR not accessible
            try:
                result = subprocess.run([
                    "git", "diff", "--name-only", "origin/main...HEAD"
                ], cwd=self.spring_ai_dir, capture_output=True, text=True)
                
                files = result.stdout.strip().split('\n')
                return [f for f in files if f]
            except:
                return []
    
    def _discover_affected_modules(self, changed_files: List[str]) -> List[str]:
        """Identify which Maven modules are affected by the changed files"""
        modules = set()
        
        for file_path in changed_files:
            module = self._find_module_for_file(file_path)
            if module:
                modules.add(module)
        
        return sorted(list(modules))
    
    def _find_module_for_file(self, file_path: str) -> Optional[str]:
        """Find the Maven module that contains a given file"""
        # Skip non-code files
        if not self._is_relevant_file(file_path):
            return None
        
        # Walk up the path looking for pom.xml
        path_parts = file_path.split('/')
        
        for i in range(len(path_parts), 0, -1):
            potential_module = '/'.join(path_parts[:i])
            pom_path = self.spring_ai_dir / potential_module / "pom.xml"
            
            if pom_path.exists():
                # Found a module
                return potential_module
        
        # Check if it's in the root module
        if (self.spring_ai_dir / "pom.xml").exists():
            return "."
        
        return None
    
    def _is_relevant_file(self, file_path: str) -> bool:
        """Check if a file is relevant for module discovery"""
        # Include Java source and test files
        if file_path.endswith('.java'):
            return True
        
        # Include build files
        if file_path.endswith('pom.xml'):
            return True
        
        # Include resource files
        if '/src/main/resources/' in file_path or '/src/test/resources/' in file_path:
            return True
        
        # Skip documentation, configs, etc.
        return False
    
    def _has_code_changes(self, changed_files: List[str]) -> bool:
        """Check if there are actual code changes (not just tests/docs)"""
        for file_path in changed_files:
            if '/src/main/java/' in file_path and file_path.endswith('.java'):
                return True
        return False
    
    def _has_test_changes(self, changed_files: List[str]) -> bool:
        """Check if there are test changes"""
        for file_path in changed_files:
            if '/src/test/java/' in file_path and file_path.endswith('.java'):
                return True
        return False
    
    def _map_modules_to_files(self, changed_files: List[str], modules: List[str]) -> Dict[str, List[str]]:
        """Map each module to its changed files"""
        module_to_files = {module: [] for module in modules}
        
        for file_path in changed_files:
            module = self._find_module_for_file(file_path)
            if module and module in module_to_files:
                module_to_files[module].append(file_path)
        
        return module_to_files
    
    def _generate_test_commands(self, modules: List[str], changed_files: List[str]) -> Dict[str, str]:
        """Generate mvnd test commands for the affected modules"""
        commands = {}
        
        if not modules:
            commands['info'] = "No code modules affected - no tests needed"
            return commands
        
        # Single module test
        if len(modules) == 1:
            module = modules[0]
            if module == ".":
                commands['module_test'] = "mvnd test"
                commands['quick_test'] = "mvnd test -DskipTests=false -Dmaven.test.failure.ignore=false"
            else:
                commands['module_test'] = f"mvnd test -pl {module}"
                commands['quick_test'] = f"mvnd test -pl {module} -DskipTests=false"
        
        # Multi-module test
        else:
            module_list = ",".join(modules)
            commands['all_modules'] = f"mvnd test -pl {module_list}"
            commands['quick_test'] = f"mvnd test -pl {module_list} -DskipTests=false"
            
            # Add individual module commands for reference
            for i, module in enumerate(modules[:3]):  # Limit to first 3 for UI space
                if module == ".":
                    commands[f'module_{i+1}'] = "mvnd test"
                else:
                    commands[f'module_{i+1}'] = f"mvnd test -pl {module}"
        
        # Add specific test commands if we can identify test classes
        test_classes = self._identify_test_classes(changed_files)
        if test_classes:
            for module, tests in test_classes.items():
                if len(tests) == 1:
                    test_name = tests[0]
                    if module == ".":
                        commands['specific_test'] = f"mvnd test -Dtest={test_name}"
                    else:
                        commands['specific_test'] = f"mvnd test -pl {module} -Dtest={test_name}"
        
        # Add integration test command if relevant
        if self._has_integration_tests(changed_files):
            if len(modules) == 1:
                module = modules[0]
                if module == ".":
                    commands['integration'] = "mvnd test -Dtest=*IT"
                else:
                    commands['integration'] = f"mvnd test -pl {module} -Dtest=*IT"
        
        return commands
    
    def _identify_test_classes(self, changed_files: List[str]) -> Dict[str, List[str]]:
        """Identify specific test classes that changed"""
        test_classes = {}
        
        for file_path in changed_files:
            if '/src/test/java/' in file_path and file_path.endswith('.java'):
                # Extract test class name
                class_name = Path(file_path).stem
                if class_name.endswith('Test') or class_name.endswith('Tests') or class_name.endswith('IT'):
                    module = self._find_module_for_file(file_path)
                    if module:
                        if module not in test_classes:
                            test_classes[module] = []
                        test_classes[module].append(class_name)
        
        return test_classes
    
    def _has_integration_tests(self, changed_files: List[str]) -> bool:
        """Check if any integration tests are affected"""
        for file_path in changed_files:
            if file_path.endswith('IT.java'):
                return True
        return False
    
    def _save_to_cache(self, result: TestDiscoveryResult):
        """Save discovery results to cache"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(asdict(result), f, indent=2)
        except Exception:
            pass  # Caching is optional, don't fail if it doesn't work
    
    def format_for_display(self, result: TestDiscoveryResult) -> str:
        """Format the discovery results for display"""
        lines = []
        
        lines.append(f"Test Discovery for PR #{result.pr_number}")
        lines.append("=" * 50)
        
        if not result.affected_modules:
            lines.append("No code modules affected - no tests needed")
            return "\n".join(lines)
        
        lines.append(f"\nAffected Modules ({len(result.affected_modules)}):")
        for module in result.affected_modules:
            if module == ".":
                lines.append("  - Root module")
            else:
                lines.append(f"  - {module}")
        
        lines.append(f"\nTest Commands:")
        for cmd_type, command in result.test_commands.items():
            if cmd_type == 'info':
                continue
            # Make command type human-readable
            readable_type = cmd_type.replace('_', ' ').title()
            lines.append(f"  {readable_type}:")
            lines.append(f"    {command}")
        
        if result.has_code_changes:
            lines.append("\n✓ Contains source code changes")
        if result.has_test_changes:
            lines.append("✓ Contains test changes")
        
        return "\n".join(lines)


def main():
    """CLI interface for testing"""
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python test_discovery.py <pr_number> <spring_ai_dir>")
        sys.exit(1)
    
    pr_number = sys.argv[1]
    spring_ai_dir = Path(sys.argv[2])
    
    if not spring_ai_dir.exists():
        print(f"Error: Directory {spring_ai_dir} does not exist")
        sys.exit(1)
    
    discovery = TestDiscovery(pr_number, spring_ai_dir)
    result = discovery.discover(force_refresh=True)
    
    print(discovery.format_for_display(result))
    
    # Also print JSON for debugging
    print("\n" + "=" * 50)
    print("JSON Output:")
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
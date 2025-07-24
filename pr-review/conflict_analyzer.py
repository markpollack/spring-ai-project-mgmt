#!/usr/bin/env python3
"""
Conflict Analysis and Plan Generation for Spring AI PR Reviews

This module replaces the complex heredoc sections in pr-prepare.sh with clean Python code.
It analyzes git conflicts and generates markdown resolution plans using Jinja2 templates.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("Error: jinja2 not installed. Run: pip install jinja2", file=sys.stderr)
    sys.exit(1)


@dataclass
class ConflictFile:
    """Represents a single conflicted file"""
    path: str
    file_type: str
    conflict_markers: int
    complexity: str  # "simple" or "complex"
    
    
@dataclass
class ConflictAnalysis:
    """Results of conflict analysis"""
    pr_number: str
    simple_conflicts: int
    complex_conflicts: int
    total_conflicts: int
    files: List[ConflictFile]
    repo_dir: str
    branch: str
    generated_at: str


class ConflictAnalyzer:
    """Analyzes git conflicts and generates resolution plans"""
    
    def __init__(self, script_dir: str):
        self.script_dir = Path(script_dir)
        self.plans_dir = self.script_dir / "plans"
        self.templates_dir = self.script_dir / "templates"
        self.spring_ai_dir = self.script_dir / "spring-ai"
        
        # Ensure directories exist
        self.plans_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def get_conflicted_files(self) -> List[str]:
        """Get list of conflicted files from git status"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.spring_ai_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            conflicted_files = []
            for line in result.stdout.strip().split('\n'):
                if line and (line.startswith('UU ') or line.startswith('AA ') or line.startswith('DD ')):
                    file_path = line[3:].strip()
                    conflicted_files.append(file_path)
            
            return conflicted_files
            
        except subprocess.CalledProcessError as e:
            print(f"Error getting git status: {e}", file=sys.stderr)
            return []
    
    def count_conflict_markers(self, file_path: str) -> int:
        """Count conflict markers in a file"""
        full_path = self.spring_ai_dir / file_path
        if not full_path.exists():
            return 0
            
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            markers = ['<<<<<<<', '>>>>>>>', '=======']
            count = sum(content.count(marker) for marker in markers)
            return count
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            return 0
    
    def classify_file_type(self, file_path: str) -> str:
        """Classify file type based on extension"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        type_map = {
            '.java': 'Java source',
            '.md': 'Markdown',
            '.yml': 'YAML config',
            '.yaml': 'YAML config', 
            '.properties': 'Properties file',
            '.xml': 'XML file',
            '.json': 'JSON file',
            '.py': 'Python source',
            '.js': 'JavaScript source',
            '.ts': 'TypeScript source'
        }
        
        return type_map.get(suffix, 'Other')
    
    def classify_complexity(self, conflict_markers: int, file_type: str) -> str:
        """Classify conflict complexity as simple or complex"""
        # Simple conflicts: Few markers in documentation/config files
        if conflict_markers <= 2 and file_type in ['Markdown', 'Properties file', 'YAML config']:
            return 'simple'
        return 'complex'
    
    def get_current_branch(self) -> str:
        """Get current git branch name"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.spring_ai_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip() or 'unknown'
        except subprocess.CalledProcessError:
            return 'unknown'
    
    def analyze_conflicts(self, pr_number: str) -> ConflictAnalysis:
        """Analyze all conflicts and return structured data"""
        conflicted_files = self.get_conflicted_files()
        
        if not conflicted_files:
            return ConflictAnalysis(
                pr_number=pr_number,
                simple_conflicts=0,
                complex_conflicts=0,
                total_conflicts=0,
                files=[],
                repo_dir=str(self.spring_ai_dir),
                branch=self.get_current_branch(),
                generated_at=datetime.now().isoformat()
            )
        
        files = []
        simple_count = 0
        complex_count = 0
        
        for file_path in conflicted_files:
            conflict_markers = self.count_conflict_markers(file_path)
            file_type = self.classify_file_type(file_path)
            complexity = self.classify_complexity(conflict_markers, file_type)
            
            files.append(ConflictFile(
                path=file_path,
                file_type=file_type,
                conflict_markers=conflict_markers,
                complexity=complexity
            ))
            
            if complexity == 'simple':
                simple_count += 1
            else:
                complex_count += 1
        
        return ConflictAnalysis(
            pr_number=pr_number,
            simple_conflicts=simple_count,
            complex_conflicts=complex_count,
            total_conflicts=len(files),
            files=files,
            repo_dir=str(self.spring_ai_dir),
            branch=self.get_current_branch(),
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def create_fallback_templates(self):
        """Create fallback templates if they don't exist"""
        templates = {
            'conflict-plan.md': '''# Conflict Resolution Plan for PR #{{ analysis.pr_number }}

Generated: {{ analysis.generated_at }}
Repository: {{ analysis.repo_dir }}
Branch: {{ analysis.branch }}

## Conflict Summary

- 🟡 Simple conflicts: {{ analysis.simple_conflicts }} (can potentially auto-resolve)
- 🔴 Complex conflicts: {{ analysis.complex_conflicts }} (need manual review)
- 📁 Total conflicted files: {{ analysis.total_conflicts }}

## Conflicted Files

{% for file in analysis.files %}
- {% if file.complexity == 'simple' %}🟡 SIMPLE{% else %}🔴 COMPLEX{% endif %}: {{ file.path }} ({{ file.file_type }}) - {{ file.conflict_markers }} conflict marker(s)
{% endfor %}

## Resolution Strategy

### Automatic Resolution (Simple Conflicts)
For simple conflicts in documentation and config files, common strategies:
- **Markdown files**: Usually take newer version or merge content logically
- **Properties files**: Take newer values unless they conflict with PR intent
- **Version files**: Take newer version numbers

### Manual Resolution Required (Complex Conflicts)
For Java source files and complex conflicts:
1. Understand the intent of both changes
2. Preserve functionality from both branches when possible
3. Follow Spring Boot/AI coding patterns
4. Ensure backward compatibility

## Recommended Actions

{% if analysis.simple_conflicts > 0 %}
### Step 1: Auto-resolve Simple Conflicts
```bash
# Run the script with auto-resolve flag
./pr-prepare.sh --auto-resolve {{ analysis.pr_number }}
```
{% endif %}

{% if analysis.complex_conflicts > 0 %}
### Step 2: Get AI Assistance for Complex Conflicts
```bash
# Call Claude Code for intelligent conflict resolution
./pr-prepare.sh --call-claude {{ analysis.pr_number }}

# Or manually review each conflict:
{% for file in analysis.files %}
{% if file.complexity == 'complex' and file.file_type == 'Java source' %}
git diff HEAD {{ file.path }}  # Review Java conflicts in {{ file.path }}
{% endif %}
{% endfor %}
```

### Step 3: Complete Rebase
After resolving conflicts:
```bash
git add .
git rebase --continue
```
{% endif %}

## Claude Code Integration

To get AI assistance with conflict resolution:
```bash
# Navigate to the spring-ai directory
cd {{ analysis.repo_dir }}

# Call Claude Code with context
export PR_NUMBER={{ analysis.pr_number }}
claude "I have merge conflicts in PR #{{ analysis.pr_number }}. Please analyze the conflicts and suggest resolutions. The conflicts are in: {% for file in analysis.files %}{{ file.path }} {% endfor %}"
```

## Next Steps

1. Review this plan
2. Execute the recommended resolution strategy
3. Test the build after resolution: `fb` or `./gradlew build`
4. Continue with PR review workflow

---
*Generated by conflict_analyzer.py - Spring AI Project Management*
''',
            'claude-prompt.txt': '''I have merge conflicts in Spring AI PR #{{ pr_number }} that need resolution.

Conflicted files:
{% for file in conflicted_files %}
- {{ file }}
{% endfor %}

Context:
- This is a Spring AI project using Java and Spring Boot
- Conflicts occurred during rebase against upstream main
- Need to preserve functionality from both branches when possible
- Follow Spring Boot coding patterns and best practices

Please analyze each conflicted file and provide specific resolution recommendations. For each file, show:
1. The nature of the conflict
2. Recommended resolution strategy
3. Specific commands or edits to make

Plan file created at: {{ plan_file }}'''
        }
        
        for template_name, content in templates.items():
            template_path = self.templates_dir / template_name
            if not template_path.exists():
                template_path.write_text(content)
    
    def generate_plan(self, analysis: ConflictAnalysis) -> str:
        """Generate conflict resolution plan using Jinja2 templates"""
        self.create_fallback_templates()
        
        plan_file = self.plans_dir / f"plan-pr-{analysis.pr_number}.md"
        
        try:
            template = self.jinja_env.get_template('conflict-plan.md')
            content = template.render(analysis=analysis)
            
            plan_file.write_text(content)
            print(f"✅ Conflict resolution plan created: {plan_file}")
            return str(plan_file)
            
        except Exception as e:
            print(f"Error generating plan: {e}", file=sys.stderr)
            # Fallback to simple plan
            fallback_content = f"""# Conflict Resolution Plan for PR #{analysis.pr_number}

Generated: {analysis.generated_at}
Simple conflicts: {analysis.simple_conflicts}, Complex conflicts: {analysis.complex_conflicts}

Files with conflicts:
"""
            for file in analysis.files:
                fallback_content += f"- {file.path} ({file.file_type}) - {file.complexity}\n"
            
            plan_file.write_text(fallback_content)
            return str(plan_file)


def main():
    """Main entry point for command line usage"""
    if len(sys.argv) != 3:
        print("Usage: python3 conflict_analyzer.py <script_dir> <pr_number>", file=sys.stderr)
        sys.exit(1)
    
    script_dir = sys.argv[1]
    pr_number = sys.argv[2]
    
    analyzer = ConflictAnalyzer(script_dir)
    analysis = analyzer.analyze_conflicts(pr_number)
    
    if analysis.total_conflicts == 0:
        print("✅ No conflicts detected")
        sys.exit(0)
    else:
        print(f"⚠️  Found {analysis.total_conflicts} conflicted files:")
        print(f"   🟡 Simple: {analysis.simple_conflicts}")
        print(f"   🔴 Complex: {analysis.complex_conflicts}")
        
        plan_file = analyzer.generate_plan(analysis)
        print(f"📋 Plan generated: {plan_file}")
        
        # Output JSON for shell script consumption
        print("JSON_OUTPUT:", json.dumps(asdict(analysis)))
        sys.exit(1)  # Return 1 to indicate conflicts exist


if __name__ == "__main__":
    main()
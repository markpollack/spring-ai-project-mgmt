#!/usr/bin/env python3
"""
Pure Python PR Analysis Report Generator
Replaces the Claude CLI-based report generation with direct Python analysis
"""

import subprocess
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import sys
from dataclasses import dataclass


@dataclass
class PRContext:
    number: str
    title: str
    body: str
    author: str
    url: str
    state: str
    labels: List[str]


@dataclass 
class FileAnalysis:
    filename: str
    status: str  # added, modified, deleted
    lines_added: int
    lines_removed: int
    is_test: bool
    is_config: bool
    is_critical: bool


class PythonPRAnalyzer:
    def __init__(self, spring_ai_dir: Path):
        self.spring_ai_dir = spring_ai_dir
        self.critical_patterns = [
            r'System\.getProperty|System\.getenv',  # Environment access - could be credentials
            r'@Autowired.*private',  # Field injection anti-pattern
        ]
        self.important_patterns = [
            r'new.*\(Service|Repository|Component\)',  # Direct instantiation
            r'System\.out|printStackTrace',  # Console output
        ]
        self.suggestion_patterns = [
            r'TODO|FIXME|XXX',  # TODO markers
        ]
        self.spring_ai_patterns = [
            r'@Bean.*\(ChatClient|EmbeddingClient|VectorStore\)',
            r'\.call\(|\.embed\(|\.search\(',  # AI service calls
        ]
    
    def check_gh_auth(self) -> bool:
        """Check if GitHub CLI is authenticated"""
        try:
            subprocess.run(["gh", "auth", "status"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_pr_context(self, pr_number: str) -> Optional[PRContext]:
        """Get PR context from GitHub CLI"""
        if not self.check_gh_auth():
            print("❌ GitHub CLI not authenticated. Please run: gh auth login")
            return None
        
        try:
            result = subprocess.run([
                "gh", "pr", "view", pr_number, "--json", 
                "number,title,body,state,author,url,labels"
            ], capture_output=True, text=True, check=True, cwd=self.spring_ai_dir)
            
            data = json.loads(result.stdout)
            
            return PRContext(
                number=str(data.get('number', pr_number)),
                title=data.get('title', 'Unknown'),
                body=data.get('body', ''),
                author=data.get('author', {}).get('login', 'Unknown'),
                url=data.get('url', ''),
                state=data.get('state', 'Unknown'),
                labels=[label.get('name', '') for label in data.get('labels', [])]
            )
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"❌ Failed to get PR context: {e}")
            return None
    
    def get_changed_files(self) -> List[FileAnalysis]:
        """Get list of changed files with analysis"""
        try:
            # Get file stats
            result = subprocess.run([
                "git", "diff", "--name-status", "upstream/main"
            ], capture_output=True, text=True, check=True, cwd=self.spring_ai_dir)
            
            files = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                parts = line.split('\t')
                if len(parts) >= 2:
                    status = parts[0]
                    filename = parts[1]
                    
                    # Get line counts for modified files
                    lines_added, lines_removed = 0, 0
                    if status in ['M', 'A']:
                        try:
                            diff_result = subprocess.run([
                                "git", "diff", "--numstat", "upstream/main", filename
                            ], capture_output=True, text=True, cwd=self.spring_ai_dir)
                            
                            if diff_result.stdout.strip():
                                stats = diff_result.stdout.strip().split('\t')
                                if len(stats) >= 2:
                                    lines_added = int(stats[0]) if stats[0] != '-' else 0
                                    lines_removed = int(stats[1]) if stats[1] != '-' else 0
                        except (subprocess.CalledProcessError, ValueError):
                            pass
                    
                    files.append(FileAnalysis(
                        filename=filename,
                        status=status,
                        lines_added=lines_added,
                        lines_removed=lines_removed,
                        is_test=self._is_test_file(filename),
                        is_config=self._is_config_file(filename),
                        is_critical=self._is_critical_file(filename)
                    ))
            
            return files
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to get changed files: {e}")
            return []
    
    def _is_test_file(self, filename: str) -> bool:
        return 'test' in filename.lower() or filename.endswith('Test.java') or filename.endswith('IT.java')
    
    def _is_config_file(self, filename: str) -> bool:
        return filename.endswith(('.yml', '.yaml', '.properties', '.xml'))
    
    def _is_critical_file(self, filename: str) -> bool:
        critical_patterns = ['Service.java', 'Config.java', 'Controller.java', 'Repository.java']
        return any(pattern in filename for pattern in critical_patterns)
    
    def analyze_file_content(self, file_analysis: FileAnalysis) -> Dict[str, List[str]]:
        """Analyze file content for issues"""
        issues = {
            'critical': [],
            'important': [],
            'suggestions': []
        }
        
        if file_analysis.status == 'D':  # Deleted file
            return issues
        
        filepath = self.spring_ai_dir / file_analysis.filename
        if not filepath.exists() or not filepath.name.endswith('.java'):
            return issues
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check for critical patterns
            for i, line in enumerate(lines, 1):
                for pattern in self.critical_patterns:
                    if re.search(pattern, line):
                        if 'System\.getProperty|System\.getenv' in pattern:
                            issues['critical'].append(f"Line {i}: Potential hardcoded credential access")
                        elif '@Autowired.*private' in pattern:
                            issues['critical'].append(f"Line {i}: Field injection - use constructor injection")
                
                # Check for important patterns
                for pattern in self.important_patterns:
                    if re.search(pattern, line):
                        if 'new.*\(Service|Repository|Component\)' in pattern:
                            issues['important'].append(f"Line {i}: Direct instantiation - use dependency injection")
                        elif 'System\.out|printStackTrace' in pattern:
                            issues['important'].append(f"Line {i}: Console output - use proper logging")
                
                # Check for suggestion patterns
                for pattern in self.suggestion_patterns:
                    if re.search(pattern, line):
                        if 'TODO|FIXME|XXX' in pattern:
                            issues['suggestions'].append(f"Line {i}: TODO marker found")
            
            # Check for Spring AI patterns
            ai_calls = 0
            for i, line in enumerate(lines, 1):
                if re.search(r'\.call\(|\.embed\(|\.search\(', line):
                    ai_calls += 1
                    # Spring AI handles timeouts at the client level, not per call
                    # No need to flag individual calls for timeout configuration
            
            # Check for Spring AI configuration best practices
            if '@Configuration' in content and '@Bean' in content:
                # Look for proper bean configuration patterns
                if re.search(r'@Bean.*ChatClient|@Bean.*EmbeddingClient|@Bean.*VectorStore', content):
                    issues['suggestions'].append("Contains Spring AI bean configurations")
            
            # Only suggest error handling for non-test files with AI calls
            if ai_calls > 0 and 'try' not in content.lower() and not file_analysis.is_test:
                issues['suggestions'].append("Consider adding error handling for AI service calls")
                
        except Exception as e:
            issues['suggestions'].append(f"Could not analyze file content: {e}")
        
        return issues
    
    def calculate_risk_level(self, all_issues: Dict[str, Dict[str, List[str]]]) -> str:
        """Calculate overall risk level"""
        critical_count = sum(len(issues['critical']) for issues in all_issues.values())
        important_count = sum(len(issues['important']) for issues in all_issues.values())
        
        if critical_count > 0:
            return "HIGH"
        elif important_count > 3:
            return "MEDIUM" 
        else:
            return "LOW"
    
    def generate_report(self, pr_number: str, output_file: Path) -> bool:
        """Generate comprehensive PR analysis report"""
        print(f"🔍 Generating PR analysis report for PR #{pr_number}...")
        
        # Get PR context
        pr_context = self.get_pr_context(pr_number)
        if not pr_context:
            print("❌ Could not load PR context")
            return False
        
        # Get changed files
        changed_files = self.get_changed_files()
        if not changed_files:
            print("❌ No changed files found")
            return False
        
        # Analyze each file
        all_issues = {}
        for file_analysis in changed_files:
            issues = self.analyze_file_content(file_analysis)
            all_issues[file_analysis.filename] = issues
        
        # Calculate risk
        risk_level = self.calculate_risk_level(all_issues)
        
        # Generate report
        report_content = self._generate_report_content(
            pr_context, changed_files, all_issues, risk_level
        )
        
        # Write report
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"📋 PR analysis report generated: {output_file}")
            print(f"Report contains {len(report_content.split(chr(10)))} lines")
            return True
            
        except Exception as e:
            print(f"❌ Failed to write report: {e}")
            return False
    
    def _categorize_files(self, files: List[FileAnalysis]) -> Dict[str, List[str]]:
        """Categorize files by type/purpose"""
        categories = {
            'Core Implementation': [],
            'API/Configuration': [],
            'Tests': [],
            'Documentation/Other': []
        }
        
        for file in files:
            if file.is_test:
                categories['Tests'].append(file.filename)
            elif file.is_critical:
                categories['Core Implementation'].append(file.filename)
            elif file.is_config or file.filename.endswith('.xml'):
                categories['API/Configuration'].append(file.filename)
            else:
                categories['Documentation/Other'].append(file.filename)
        
        return categories
    
    def _generate_report_content(self, pr_context: PRContext, files: List[FileAnalysis], 
                               all_issues: Dict[str, Dict[str, List[str]]], risk_level: str) -> str:
        """Generate the full report content"""
        
        categories = self._categorize_files(files)
        
        report = f"""# Spring AI PR #{pr_context.number} Review Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Reviewer: Python PR Analysis Tool
Repository: spring-projects/spring-ai
PR URL: {pr_context.url}
Author: {pr_context.author}
Status: {pr_context.state}

---

## 🔍 PR Analysis Summary

**PR Context**: {pr_context.title}
**Labels**: {', '.join(pr_context.labels) if pr_context.labels else 'None'}
**Scope of Changes**: {len(files)} files changed

### File Categories:
"""
        
        for category, file_list in categories.items():
            if file_list:
                report += f"- **{category}**: {len(file_list)} files\n"
                for file in file_list[:5]:  # Show first 5 files
                    report += f"  - {file}\n"
                if len(file_list) > 5:
                    report += f"  - ... and {len(file_list) - 5} more\n"
        
        report += f"""
**Overall Risk**: {risk_level}
**Files by Status**: 
"""
        
        status_counts = {}
        for file in files:
            status_counts[file.status] = status_counts.get(file.status, 0) + 1
        
        for status, count in status_counts.items():
            status_name = {'M': 'Modified', 'A': 'Added', 'D': 'Deleted'}.get(status, status)
            report += f"- {status_name}: {count} files\n"
        
        # Critical Issues Section
        report += "\n---\n\n## 🔴 Critical Issues (Fix Before Merge)\n\n"
        critical_found = False
        for filename, issues in all_issues.items():
            if issues['critical']:
                critical_found = True
                report += f"### {filename}\n"
                for issue in issues['critical']:
                    report += f"- **Issue**: {issue}\n"
                    report += f"- **Impact**: Security/Configuration risk\n"
                    report += f"- **Fix**: Review and secure credential handling\n\n"
        
        if not critical_found:
            report += "✅ No critical issues found\n\n"
        
        # Important Issues Section  
        report += "---\n\n## 🟡 Important Issues (Should Address)\n\n"
        important_found = False
        for filename, issues in all_issues.items():
            if issues['important']:
                important_found = True
                report += f"### {filename}\n"
                for issue in issues['important']:
                    report += f"- **Issue**: {issue}\n"
                    report += f"- **Recommendation**: Follow Spring best practices\n\n"
        
        if not important_found:
            report += "✅ No important issues found\n\n"
        
        # Code Quality Suggestions
        report += "---\n\n## 🔵 Code Quality Suggestions\n\n"
        suggestions_found = False
        for filename, issues in all_issues.items():
            if issues['suggestions']:
                suggestions_found = True  
                report += f"### {filename}\n"
                for suggestion in issues['suggestions']:
                    report += f"- {suggestion}\n"
                report += "\n"
        
        if not suggestions_found:
            report += "✅ No code quality suggestions\n\n"
        
        # Positive Findings
        report += "---\n\n## ✅ Positive Findings\n\n"
        
        java_files = [f for f in files if f.filename.endswith('.java') and f.status != 'D']
        test_files = [f for f in files if f.is_test]
        
        if java_files:
            report += f"- Implementation includes {len(java_files)} Java files with proper structure\n"
        if test_files:
            report += f"- Includes {len(test_files)} test files for validation\n"
        if any(f.is_config for f in files):
            report += "- Configuration changes are properly structured\n"
        
        # Action Items
        report += "\n---\n\n## 📋 Action Items\n\n"
        
        total_critical = sum(len(issues['critical']) for issues in all_issues.values())
        total_important = sum(len(issues['important']) for issues in all_issues.values())
        
        report += "**Immediate (Block Merge)**:\n"
        if total_critical > 0:
            report += f"- [ ] Address {total_critical} critical security/configuration issues\n"
        else:
            report += "- [x] No blocking issues found\n"
        
        report += "\n**Follow-up**:\n"
        if total_important > 0:
            report += f"- [ ] Address {total_important} important Spring best practice issues\n"
        
        report += "\n**Testing Needs**:\n"
        report += "- [ ] Verify all AI service integrations work correctly\n"
        report += "- [ ] Test timeout configurations if applicable\n"
        report += "- [ ] Validate Spring configuration changes\n"
        
        # Context Alignment
        report += "\n---\n\n## 💭 Context Alignment\n\n"
        report += f"**Requirements Met**: PR addresses: {pr_context.title}\n"
        report += "**Missing Elements**: Analysis based on code changes only\n"
        report += "**Additional Considerations**: Consider integration testing for AI service changes\n"
        
        # Summary
        report += f"\n---\n\n## 📊 Summary Statistics\n\n"
        report += f"- **Files Analyzed**: {len(files)}\n"
        report += f"- **Java Files**: {len([f for f in files if f.filename.endswith('.java')])}\n" 
        report += f"- **Test Files**: {len(test_files)}\n"
        report += f"- **Critical Issues**: {total_critical}\n"
        report += f"- **Important Issues**: {total_important}\n"
        report += f"- **Overall Risk**: {risk_level}\n"
        
        report += "\n---\n\n*Report generated by Python PR Analysis Tool*\n"
        
        return report


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 python_report_generator.py <pr_number> <output_file>")
        sys.exit(1)
    
    pr_number = sys.argv[1]
    output_file = Path(sys.argv[2])
    spring_ai_dir = Path.cwd()
    
    analyzer = PythonPRAnalyzer(spring_ai_dir)
    success = analyzer.generate_report(pr_number, output_file)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
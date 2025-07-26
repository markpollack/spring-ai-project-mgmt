#!/usr/bin/env python3
"""
AI-Powered Solution Assessor - Enhanced PR Analysis with Code Evaluation

Conducts comprehensive solution assessment using Claude Code's reasoning:
- Scope analysis and architecture impact evaluation
- Implementation quality and code pattern analysis
- Risk assessment and complexity scoring with justification
- Testing adequacy and documentation completeness review
- Actionable recommendations for improvement

This is Iteration 3 of the Enhanced PR Analysis implementation.
"""

import json
import subprocess
import tempfile
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from claude_code_wrapper import ClaudeCodeWrapper

# Simple logger to avoid circular imports
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
class SolutionAssessment:
    """Comprehensive solution assessment results"""
    scope_analysis: str
    architecture_impact: List[str]
    implementation_quality: List[str]
    breaking_changes_assessment: List[str]
    testing_adequacy: List[str]
    documentation_completeness: List[str]
    solution_fitness: str
    risk_factors: List[str]
    code_quality_score: int  # 1-10 scale
    complexity_justification: str
    final_complexity_score: int  # 1-10 scale
    recommendations: List[str]


class AIPoweredSolutionAssessor:
    """Uses Claude Code to perform intelligent solution assessment"""
    
    def __init__(self, working_dir: Path = None, spring_ai_dir: Path = None):
        # Default to script directory if not provided (most robust approach)
        if working_dir is None:
            working_dir = Path(__file__).parent.absolute()
        if spring_ai_dir is None:
            spring_ai_dir = working_dir / "spring-ai"
            
        self.working_dir = working_dir.absolute()
        self.spring_ai_dir = spring_ai_dir.absolute()
        self.context_dir = self.working_dir / "context"
    
    def assess_solution(self, pr_number: str) -> Optional[SolutionAssessment]:
        """Perform comprehensive AI-powered solution assessment"""
        Logger.info(f"🔍 Starting AI-powered solution assessment for PR #{pr_number}")
        
        pr_context_dir = self.context_dir / f"pr-{pr_number}"
        if not pr_context_dir.exists():
            Logger.error(f"❌ No context data found for PR #{pr_number}")
            return None
        
        try:
            # Load all required context data
            context_data = self._load_assessment_context(pr_context_dir)
            if not context_data:
                Logger.error("❌ Failed to load assessment context")
                return None
            
            # Analyze code changes in detail
            code_analysis = self._analyze_code_changes(pr_number)
            
            # Create comprehensive assessment prompt
            assessment_prompt = self._create_assessment_prompt(context_data, code_analysis, pr_number)
            
            # Execute AI assessment using Claude Code
            ai_results = self._execute_claude_assessment(assessment_prompt)
            if not ai_results:
                Logger.error("❌ AI assessment failed")
                return None
            
            # Parse and structure AI results
            assessment = self._parse_assessment_results(ai_results, context_data)
            
            # Save assessment results
            self._save_assessment(pr_context_dir, assessment)
            
            Logger.success(f"✅ Solution assessment completed for PR #{pr_number}")
            Logger.info(f"   - Code quality score: {assessment.code_quality_score}/10")
            Logger.info(f"   - Final complexity score: {assessment.final_complexity_score}/10")
            Logger.info(f"   - Risk factors identified: {len(assessment.risk_factors)}")
            Logger.info(f"   - Recommendations: {len(assessment.recommendations)}")
            
            return assessment
            
        except Exception as e:
            Logger.error(f"❌ Solution assessment failed: {e}")
            return None
    
    def _load_assessment_context(self, pr_context_dir: Path) -> Dict[str, Any]:
        """Load all context data needed for assessment"""
        context_data = {}
        
        files_to_load = [
            ("pr_data", "pr-data.json"),
            ("conversation_analysis", "ai-conversation-analysis.json"),
            ("file_changes", "file-changes.json")
        ]
        
        for key, filename in files_to_load:
            file_path = pr_context_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        context_data[key] = json.load(f)
                except Exception as e:
                    Logger.warn(f"⚠️  Could not load {filename}: {e}")
                    context_data[key] = None
            else:
                Logger.warn(f"⚠️  Missing context file: {filename}")
                context_data[key] = None
        
        return context_data
    
    def _analyze_code_changes(self, pr_number: str) -> Dict[str, Any]:
        """Analyze code changes for patterns and quality indicators"""
        Logger.info("📊 Analyzing code changes...")
        
        try:
            # Get diff statistics
            diff_result = subprocess.run([
                "git", "diff", "--numstat", "upstream/main"
            ], capture_output=True, text=True, cwd=self.spring_ai_dir)
            
            total_lines_added = 0
            total_lines_removed = 0
            file_count = 0
            
            if diff_result.stdout:
                for line in diff_result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            try:
                                added = int(parts[0]) if parts[0] != '-' else 0
                                removed = int(parts[1]) if parts[1] != '-' else 0
                                total_lines_added += added
                                total_lines_removed += removed
                                file_count += 1
                            except ValueError:
                                continue
            
            # Analyze implementation patterns
            implementation_patterns = self._detect_implementation_patterns()
            
            # Analyze test coverage
            test_analysis = self._analyze_test_coverage()
            
            return {
                'total_lines_added': total_lines_added,
                'total_lines_removed': total_lines_removed,
                'file_count': file_count,
                'implementation_patterns': implementation_patterns,
                'test_analysis': test_analysis
            }
            
        except Exception as e:
            Logger.warn(f"⚠️  Code analysis failed: {e}")
            return {
                'total_lines_added': 0,
                'total_lines_removed': 0,
                'file_count': 0,
                'implementation_patterns': [],
                'test_analysis': {}
            }
    
    def _detect_implementation_patterns(self) -> List[str]:
        """Detect Spring AI and general implementation patterns in changes"""
        patterns = []
        
        try:
            # Get list of changed files
            files_result = subprocess.run([
                "git", "diff", "--name-only", "upstream/main"
            ], capture_output=True, text=True, cwd=self.spring_ai_dir)
            
            if not files_result.stdout:
                return patterns
            
            changed_files = [f.strip() for f in files_result.stdout.split('\n') if f.strip()]
            
            # Analyze each changed Java file
            for file in changed_files[:10]:  # Limit to avoid excessive processing
                if file.endswith('.java'):
                    file_path = self.spring_ai_dir / file
                    if file_path.exists():
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Detect Spring patterns
                            if '@Configuration' in content:
                                patterns.append(f"Spring Configuration class: {file}")
                            if '@Component' in content or '@Service' in content or '@Repository' in content:
                                patterns.append(f"Spring component: {file}")
                            if '@Bean' in content:
                                patterns.append(f"Bean definition: {file}")
                            if 'ChatClient' in content or 'EmbeddingClient' in content:
                                patterns.append(f"AI client integration: {file}")
                            if re.search(r'class.*Test', content) or 'test' in file.lower():
                                patterns.append(f"Test implementation: {file}")
                            if '@Override' in content:
                                patterns.append(f"Method overrides: {file}")
                            if 'implements' in content:
                                patterns.append(f"Interface implementation: {file}")
                                
                        except Exception as e:
                            Logger.warn(f"⚠️  Could not analyze {file}: {e}")
            
        except Exception as e:
            Logger.warn(f"⚠️  Pattern detection failed: {e}")
        
        return patterns[:15]  # Limit output
    
    def _analyze_test_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage and quality"""
        test_analysis = {
            'test_files_count': 0,
            'test_coverage_areas': [],
            'integration_tests': False,
            'unit_tests': False
        }
        
        try:
            # Get changed test files
            files_result = subprocess.run([
                "git", "diff", "--name-only", "upstream/main"
            ], capture_output=True, text=True, cwd=self.spring_ai_dir)
            
            if files_result.stdout:
                changed_files = [f.strip() for f in files_result.stdout.split('\n') if f.strip()]
                test_files = [f for f in changed_files if 'test' in f.lower() or f.endswith('Test.java')]
                
                test_analysis['test_files_count'] = len(test_files)
                
                for test_file in test_files:
                    if 'IT.java' in test_file or 'IntegrationTest' in test_file:
                        test_analysis['integration_tests'] = True
                        test_analysis['test_coverage_areas'].append(f"Integration test: {test_file}")
                    elif 'Test.java' in test_file:
                        test_analysis['unit_tests'] = True
                        test_analysis['test_coverage_areas'].append(f"Unit test: {test_file}")
        
        except Exception as e:
            Logger.warn(f"⚠️  Test analysis failed: {e}")
        
        return test_analysis
    
    def _create_assessment_prompt(self, context_data: Dict[str, Any], 
                                 code_analysis: Dict[str, Any], pr_number: str) -> str:
        """Create structured assessment prompt using template"""
        
        # Load template
        template_path = self.working_dir / "templates" / "solution_assessment_prompt.md"
        if not template_path.exists():
            Logger.error(f"❌ Template not found: {template_path}")
            raise FileNotFoundError(f"Solution assessment template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Extract context data
        pr_data = context_data.get('pr_data', {})
        conversation_analysis = context_data.get('conversation_analysis', {})
        file_changes = context_data.get('file_changes', [])
        
        # Build file changes detail
        file_changes_detail = self._build_file_changes_detail(file_changes[:10])  # Limit details
        
        # Build file types breakdown
        file_types = {}
        for change in file_changes:
            filename = change.get('filename', '')
            if filename.endswith('.java'):
                if 'test' in filename.lower():
                    file_types['Java Tests'] = file_types.get('Java Tests', 0) + 1
                else:
                    file_types['Java Implementation'] = file_types.get('Java Implementation', 0) + 1
            elif filename.endswith(('.yml', '.yaml', '.properties', '.xml')):
                file_types['Configuration'] = file_types.get('Configuration', 0) + 1
            else:
                file_types['Other'] = file_types.get('Other', 0) + 1
        
        file_types_breakdown = ', '.join(f"{k}: {v}" for k, v in file_types.items())
        
        # Format template
        formatted_prompt = template.format(
            pr_number=pr_number,
            pr_title=pr_data.get('title', 'N/A'),
            pr_author=pr_data.get('author', 'N/A'),
            problem_summary=conversation_analysis.get('problem_summary', 'N/A'),
            conversation_complexity_score=conversation_analysis.get('complexity_score', 5),
            total_files_changed=len(file_changes),
            total_lines_added=code_analysis.get('total_lines_added', 0),
            total_lines_removed=code_analysis.get('total_lines_removed', 0),
            file_types_breakdown=file_types_breakdown,
            file_changes_detail=file_changes_detail,
            implementation_patterns='\n'.join(f"- {pattern}" for pattern in code_analysis.get('implementation_patterns', [])),
            test_files_count=code_analysis.get('test_analysis', {}).get('test_files_count', 0),
            test_coverage_areas=', '.join(code_analysis.get('test_analysis', {}).get('test_coverage_areas', [])),
            key_requirements_list='\n'.join(f"- {req}" for req in conversation_analysis.get('key_requirements', [])),
            outstanding_concerns_list='\n'.join(f"- {concern}" for concern in conversation_analysis.get('outstanding_concerns', []))
        )
        
        return formatted_prompt
    
    def _build_file_changes_detail(self, file_changes: List[Dict[str, Any]]) -> str:
        """Build detailed file changes summary"""
        if not file_changes:
            return "No file changes detected."
        
        details = []
        for change in file_changes:
            filename = change.get('filename', 'Unknown')
            status = change.get('status', 'unknown')
            additions = change.get('additions', 0)
            deletions = change.get('deletions', 0)
            
            status_desc = {
                'added': 'Added',
                'modified': 'Modified', 
                'deleted': 'Deleted',
                'renamed': 'Renamed'
            }.get(status, status)
            
            details.append(f"- **{filename}**: {status_desc} (+{additions}/-{deletions})")
        
        return '\n'.join(details)
    
    def _execute_claude_assessment(self, prompt: str) -> Optional[str]:
        """Execute assessment using Claude Code"""
        try:
            Logger.info("🤖 Running Claude Code solution assessment...")
            
            # Use ClaudeCodeWrapper for reliable integration
            claude = ClaudeCodeWrapper()
            
            if not claude.is_available():
                Logger.error("❌ Claude Code is not available")
                return None
            
            # Save prompt to logs for debugging
            logs_dir = self.working_dir / "logs"
            logs_dir.mkdir(exist_ok=True)
            debug_prompt_file = logs_dir / "claude-prompt-solution-assessor.txt"
            with open(debug_prompt_file, 'w') as f:
                f.write(prompt)
            Logger.info(f"🔍 Saved prompt to: {debug_prompt_file}")
            
            # Use wrapper to analyze from file without JSON output (expecting markdown with JSON blocks)
            debug_response_file = logs_dir / "claude-response-solution-assessor.txt"
            result = claude.analyze_from_file(str(debug_prompt_file), str(debug_response_file), timeout=300, use_json_output=False)
            
            if result['success']:
                Logger.info(f"🔍 Claude Code stdout length: {len(result['response'])} chars")
                return result['response']
            else:
                Logger.error(f"❌ Claude Code assessment failed: {result['error']}")
                if result['stderr']:
                    Logger.error(f"❌ Claude Code stderr: {result['stderr']}")
                return None
                
        except Exception as e:
            Logger.error(f"❌ Failed to execute Claude Code assessment: {e}")
            return None
    
    def _parse_assessment_results(self, ai_output: str, context_data: Dict[str, Any]) -> SolutionAssessment:
        """Parse AI assessment results into structured format"""
        try:
            # Parse the analysis JSON from Claude's markdown response
            import re
            json_pattern = r'```json\s*\n(.*?)\n```'
            json_match = re.search(json_pattern, ai_output, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                ai_data = json.loads(json_str)
            else:
                # Try to find JSON without code blocks
                lines = ai_output.split('\n')
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith('{'):
                        in_json = True
                    if in_json:
                        json_lines.append(line)
                    if line.strip().endswith('}') and in_json:
                        break
                
                if json_lines:
                    json_str = '\n'.join(json_lines)
                    ai_data = json.loads(json_str)
                else:
                    raise ValueError("No analysis JSON found in Claude response")
        
        except (json.JSONDecodeError, ValueError) as e:
            Logger.warn(f"⚠️  Could not parse AI assessment JSON: {e}")
            # Fallback to default values
            ai_data = self._create_fallback_assessment()
        
        # Create assessment object
        return SolutionAssessment(
            scope_analysis=ai_data.get('scope_analysis', 'Assessment unavailable'),
            architecture_impact=ai_data.get('architecture_impact', []),
            implementation_quality=ai_data.get('implementation_quality', []),
            breaking_changes_assessment=ai_data.get('breaking_changes_assessment', []),
            testing_adequacy=ai_data.get('testing_adequacy', []),
            documentation_completeness=ai_data.get('documentation_completeness', []),
            solution_fitness=ai_data.get('solution_fitness', 'Assessment unavailable'),
            risk_factors=ai_data.get('risk_factors', []),
            code_quality_score=ai_data.get('code_quality_score', 5),
            complexity_justification=ai_data.get('complexity_justification', 'Justification unavailable'),
            final_complexity_score=ai_data.get('final_complexity_score', 5),
            recommendations=ai_data.get('recommendations', [])
        )
    
    def _create_fallback_assessment(self) -> Dict[str, Any]:
        """Create fallback assessment if AI parsing fails"""
        return {
            'scope_analysis': 'AI assessment parsing failed - manual review required',
            'architecture_impact': ['Assessment unavailable due to parsing error'],
            'implementation_quality': ['Manual code review required'],
            'breaking_changes_assessment': ['Compatibility analysis needed'],
            'testing_adequacy': ['Test coverage review required'],
            'documentation_completeness': ['Documentation review needed'],
            'solution_fitness': 'Manual assessment required due to AI parsing failure',
            'risk_factors': ['Unknown risks due to assessment failure'],
            'code_quality_score': 5,
            'complexity_justification': 'Assessment failed - default complexity assumed',
            'final_complexity_score': 5,
            'recommendations': ['Retry AI assessment', 'Conduct manual code review']
        }
    
    def _save_assessment(self, pr_context_dir: Path, assessment: SolutionAssessment):
        """Save assessment results"""
        assessment_file = pr_context_dir / "solution-assessment.json"
        
        assessment_data = asdict(assessment)
        assessment_data['assessment_timestamp'] = datetime.now().isoformat()
        assessment_data['assessor_version'] = 'ai-powered-v1.0'
        
        with open(assessment_file, 'w', encoding='utf-8') as f:
            json.dump(assessment_data, f, indent=2, ensure_ascii=False)
        
        Logger.info(f"📁 Solution assessment saved to {assessment_file}")


def main():
    """Command-line interface for AI-powered solution assessment"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 solution_assessor.py <pr_number>")
        print("\nExamples:")
        print("  python3 solution_assessor.py 3386")
        sys.exit(1)
    
    pr_number = sys.argv[1]
    
    # Use script directory for assessment (robust regardless of where script is called from)
    working_dir = Path(__file__).parent.absolute()
    spring_ai_dir = working_dir / "spring-ai"  # Spring AI clone in pr-review directory
    
    assessor = AIPoweredSolutionAssessor(working_dir, spring_ai_dir)
    
    # Perform assessment
    assessment = assessor.assess_solution(pr_number)
    
    if assessment:
        print(f"\n✅ Solution assessment completed for PR #{pr_number}")
        print(f"📊 Assessment summary:")
        print(f"   - Code quality score: {assessment.code_quality_score}/10")
        print(f"   - Final complexity score: {assessment.final_complexity_score}/10")
        print(f"   - Risk factors: {len(assessment.risk_factors)}")
        print(f"   - Recommendations: {len(assessment.recommendations)}")
        sys.exit(0)
    else:
        print(f"\n❌ Solution assessment failed for PR #{pr_number}")
        sys.exit(1)


if __name__ == "__main__":
    main()
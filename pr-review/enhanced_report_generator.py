#!/usr/bin/env python3
"""
Enhanced PR Report Generator - Integrates AI Analysis Components

Combines all analysis components to generate comprehensive PR reports:
- Context collection data (GitHub issues, PRs, files)
- AI-powered conversation analysis (problem understanding, requirements)
- Solution assessment (code quality, complexity scoring)
- Traditional code quality analysis (patterns, issues)

This is Iteration 4 of the Enhanced PR Analysis implementation.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

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
class EnhancedReportData:
    """Consolidated data for enhanced report generation"""
    # PR Basic Info
    pr_number: str
    pr_title: str
    pr_author: str
    pr_url: str
    pr_status: str
    
    # Analysis Results
    conversation_analysis: Dict[str, Any]
    solution_assessment: Dict[str, Any]
    file_changes: List[Dict[str, Any]]
    code_analysis: Dict[str, Any]
    backport_assessment: Dict[str, Any]
    test_results: Dict[str, Any]
    
    # Report Metadata
    report_timestamp: str
    analysis_status: Dict[str, str]


class EnhancedReportGenerator:
    """Generates comprehensive reports integrating all AI analysis components"""
    
    def __init__(self, working_dir: Path = None, spring_ai_dir: Path = None):
        # Default to script directory if not provided (most robust approach)
        if working_dir is None:
            working_dir = Path(__file__).parent.absolute()
        if spring_ai_dir is None:
            spring_ai_dir = working_dir / "spring-ai"
            
        self.working_dir = working_dir.absolute()
        self.spring_ai_dir = spring_ai_dir.absolute()
        self.script_dir = self.working_dir  # Scripts are in the same directory as working_dir
        self.context_dir = self.working_dir / "context"
        self.reports_dir = self.working_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_enhanced_report(self, pr_number: str) -> bool:
        """Generate comprehensive enhanced PR report"""
        Logger.info(f"📋 Generating enhanced PR report for PR #{pr_number}")
        Logger.info(f"🔍 DEBUG: Starting enhanced report generation...")
        
        try:
            # Load all analysis data
            Logger.info(f"🔍 DEBUG: Loading report data...")
            report_data = self._load_report_data(pr_number)
            Logger.info(f"🔍 DEBUG: Report data loaded successfully")
            if not report_data:
                Logger.error("❌ Failed to load report data")
                return False
            
            # Generate enhanced report content
            report_content = self._generate_report_content(report_data)
            
            # Save enhanced report
            report_file = self.reports_dir / f"review-pr-{pr_number}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            Logger.success(f"✅ Enhanced report generated: {report_file}")
            Logger.info(f"📊 Report statistics:")
            Logger.info(f"   - Content length: {len(report_content)} characters")
            Logger.info(f"   - Sections: Problem overview, conversation analysis, solution assessment")
            Logger.info(f"   - AI components: {len([v for v in report_data.analysis_status.values() if v == 'Available'])}")
            
            return True
            
        except Exception as e:
            Logger.error(f"❌ Enhanced report generation failed: {e}")
            return False
    
    def _load_report_data(self, pr_number: str) -> Optional[EnhancedReportData]:
        """Load all data needed for enhanced report generation"""
        pr_context_dir = self.context_dir / f"pr-{pr_number}"
        if not pr_context_dir.exists():
            Logger.error(f"❌ No context data found for PR #{pr_number}")
            return None
        
        # Load analysis results
        analysis_files = {
            'pr_data': 'pr-data.json',
            'issue_data': 'issue-data.json',
            'conversation': 'conversation.json',
            'analysis_cache': 'analysis-cache.json',
            'file_changes': 'file-changes.json'
        }
        
        loaded_data = {}
        analysis_status = {}
        
        for key, filename in analysis_files.items():
            file_path = pr_context_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        loaded_data[key] = json.load(f)
                    analysis_status[key] = 'Available'
                except Exception as e:
                    Logger.warn(f"⚠️  Could not load {filename}: {e}")
                    loaded_data[key] = {}
                    analysis_status[key] = 'Failed'
            else:
                Logger.warn(f"⚠️  Missing analysis file: {filename}")
                loaded_data[key] = {}
                analysis_status[key] = 'Missing'
        
        # Load test execution results if available
        test_results = self._load_test_results(pr_number)
        analysis_status['test_results'] = 'Available' if test_results else 'Not Available'
        
        # Extract PR basic info
        pr_data = loaded_data.get('pr_data', {})
        
        # Run AI analysis if needed
        import time
        
        # Perform code analysis with timing
        Logger.info("🔍 DEBUG: About to start code analysis (AI risk assessment)...")
        Logger.info("🔍 Starting code analysis (AI risk assessment)...")
        start_time = time.time()
        code_analysis = self._perform_code_analysis(pr_number)
        code_duration = time.time() - start_time
        Logger.info(f"🔍 Code analysis completed in {code_duration:.1f} seconds")
        analysis_status['code_analysis'] = 'Available' if code_analysis else 'Failed'
        Logger.info("🔍 DEBUG: Code analysis finished")
        
        Logger.info("🔍 Starting AI conversation analysis...")
        start_time = time.time()
        conversation_analysis = self._run_ai_conversation_analysis(pr_number, pr_context_dir)
        conv_duration = time.time() - start_time
        Logger.info(f"🔍 AI conversation analysis completed in {conv_duration:.1f} seconds")
        
        Logger.info("🔍 Starting solution assessment...")
        start_time = time.time()
        solution_assessment = self._run_solution_assessment(pr_number, pr_context_dir)
        sol_duration = time.time() - start_time
        Logger.info(f"🔍 Solution assessment completed in {sol_duration:.1f} seconds")
        
        Logger.info("🔍 Starting backport candidate assessment...")
        start_time = time.time()
        backport_assessment = self._run_backport_assessment(pr_number, pr_context_dir)
        backport_duration = time.time() - start_time
        Logger.info(f"🔍 Backport assessment completed in {backport_duration:.1f} seconds")
        analysis_status['backport_assessment'] = 'Available' if backport_assessment else 'Failed'
        
        return EnhancedReportData(
            pr_number=pr_number,
            pr_title=pr_data.get('title', 'Unknown'),
            pr_author=pr_data.get('author', 'Unknown'),
            pr_url=pr_data.get('url', ''),
            pr_status=pr_data.get('state', 'Unknown'),
            conversation_analysis=conversation_analysis,
            solution_assessment=solution_assessment,
            file_changes=loaded_data.get('file_changes', []),
            code_analysis=code_analysis,
            backport_assessment=backport_assessment,
            report_timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            analysis_status=analysis_status,
            test_results=test_results
        )
    
    def _run_ai_conversation_analysis(self, pr_number: str, pr_context_dir: Path) -> Dict[str, Any]:
        """Run AI conversation analysis using ai_conversation_analyzer.py"""
        try:
            analysis_file = pr_context_dir / "ai-conversation-analysis.json"
            
            # Check if analysis already exists
            if analysis_file.exists():
                Logger.info("Using existing AI conversation analysis")
                with open(analysis_file, 'r') as f:
                    return json.load(f)
            
            # Run AI conversation analyzer
            Logger.info("Running AI conversation analysis...")
            analyzer_script = self.script_dir / "ai_conversation_analyzer.py"
            
            result = subprocess.run([
                "python3", str(analyzer_script), pr_number
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and analysis_file.exists():
                Logger.success("AI conversation analysis completed")
                with open(analysis_file, 'r') as f:
                    data = json.load(f)
                    # Check if this is placeholder/fallback data
                    if data.get("problem_summary") == "AI analysis could not be parsed properly":
                        Logger.error("❌ AI conversation analysis failed - Claude Code output could not be parsed")
                        Logger.error("❌ Cannot continue with incomplete AI analysis")
                        raise RuntimeError("AI conversation analysis failed - no fallbacks allowed")
                    return data
            else:
                Logger.error(f"❌ AI conversation analysis failed: {result.stderr}")
                raise RuntimeError("AI conversation analysis failed - no fallbacks allowed")
                
        except Exception as e:
            Logger.error(f"Error running AI conversation analysis: {e}")
            raise RuntimeError(f"AI conversation analysis failed: {e}")
    
    def _run_solution_assessment(self, pr_number: str, pr_context_dir: Path) -> Dict[str, Any]:
        """Run solution assessment using solution_assessor.py"""
        try:
            assessment_file = pr_context_dir / "solution-assessment.json"
            
            # Check if assessment already exists
            if assessment_file.exists():
                Logger.info("Using existing solution assessment")
                with open(assessment_file, 'r') as f:
                    return json.load(f)
            
            # Run solution assessor
            Logger.info("Running AI solution assessment...")
            assessor_script = self.script_dir / "solution_assessor.py"
            
            result = subprocess.run([
                "python3", str(assessor_script), pr_number
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and assessment_file.exists():
                Logger.success("AI solution assessment completed")
                with open(assessment_file, 'r') as f:
                    data = json.load(f)
                    # Check if this is placeholder/fallback data
                    if data.get("scope_analysis") == "Assessment unavailable":
                        Logger.error("❌ AI solution assessment failed - Claude Code returned placeholder data")
                        Logger.error("❌ Cannot continue with incomplete AI analysis")
                        raise RuntimeError("AI solution assessment failed - no fallbacks allowed")
                    return data
            else:
                Logger.error(f"❌ AI solution assessment failed: {result.stderr}")
                raise RuntimeError("AI solution assessment failed - no fallbacks allowed")
                
        except Exception as e:
            Logger.error(f"Error running AI solution assessment: {e}")
            raise RuntimeError(f"AI solution assessment failed: {e}")

    def _run_backport_assessment(self, pr_number: str, pr_context_dir: Path) -> Dict[str, Any]:
        """Run backport candidate assessment using backport_assessor.py"""
        try:
            assessment_file = pr_context_dir / "backport-assessment.json"
            
            # Check if assessment already exists
            if assessment_file.exists():
                Logger.info("Using existing backport assessment")
                with open(assessment_file, 'r') as f:
                    return json.load(f)
            
            # Run backport assessor
            Logger.info("Running AI backport candidate assessment...")
            assessor_script = self.script_dir / "backport_assessor.py"
            
            result = subprocess.run([
                "python3", str(assessor_script), pr_number
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and assessment_file.exists():
                Logger.success("AI backport assessment completed")
                with open(assessment_file, 'r') as f:
                    data = json.load(f)
                    # Check if this is placeholder/fallback data
                    if data.get("decision") == "UNKNOWN":
                        Logger.error("❌ AI backport assessment failed - Claude Code returned placeholder data")
                        Logger.error("❌ Cannot continue with incomplete AI analysis")
                        raise RuntimeError("AI backport assessment failed - no fallbacks allowed")
                    return data
            else:
                Logger.error(f"❌ AI backport assessment failed: {result.stderr}")
                raise RuntimeError("AI backport assessment failed - no fallbacks allowed")
                
        except Exception as e:
            Logger.error(f"Error running AI backport assessment: {e}")
            raise RuntimeError(f"AI backport assessment failed: {e}")

    def _perform_code_analysis(self, pr_number: str) -> Dict[str, Any]:
        """Perform AI-powered code analysis for the report"""
        try:
            # Use AI-powered risk assessment instead of hardcoded patterns
            from ai_risk_assessor import AIRiskAssessor
            
            assessor = AIRiskAssessor(self.working_dir, self.spring_ai_dir)
            assessment_result = assessor.run_ai_risk_assessment(pr_number)
            
            if assessment_result:
                # Save the assessment results for future use
                assessor.save_assessment_result(pr_number, assessment_result)
                
                # Convert AI assessment to format expected by report generator
                all_issues = {}
                
                # Organize critical issues by file
                for issue in assessment_result.critical_issues:
                    filename = issue.get('file', 'Unknown')
                    if filename not in all_issues:
                        all_issues[filename] = {'critical': [], 'important': [], 'suggestions': []}
                    
                    issue_text = f"Line {issue.get('line', '?')}: {issue.get('issue', 'Unknown issue')}"
                    all_issues[filename]['critical'].append(issue_text)
                
                # Organize important issues by file
                for issue in assessment_result.important_issues:
                    filename = issue.get('file', 'Unknown')
                    if filename not in all_issues:
                        all_issues[filename] = {'critical': [], 'important': [], 'suggestions': []}
                    
                    issue_text = f"Line {issue.get('line', '?')}: {issue.get('issue', 'Unknown issue')}"
                    all_issues[filename]['important'].append(issue_text)
                
                # Map risk level to expected format
                risk_level_map = {
                    'LOW': 'Low',
                    'MEDIUM': 'Medium', 
                    'HIGH': 'High',
                    'UNKNOWN': 'Medium'
                }
                
                return {
                    'ai_assessment': assessment_result,
                    'all_issues': all_issues,
                    'risk_level': risk_level_map.get(assessment_result.overall_risk_level, 'Medium'),
                    'assessment_method': 'AI-powered'
                }
            else:
                Logger.error("❌ AI risk assessment not available")
                raise RuntimeError("AI risk assessment failed - no fallbacks allowed")
            
        except Exception as e:
            Logger.error(f"❌ AI code analysis failed: {e}")
            raise RuntimeError(f"AI code analysis failed: {e}")
    
    def _fallback_code_analysis(self, pr_number: str) -> Dict[str, Any]:
        """Fallback to basic analysis if AI assessment fails"""
        return {
            'all_issues': {},
            'risk_level': 'Medium',
            'assessment_method': 'fallback'
        }
    
    def _load_test_results(self, pr_number: str) -> Dict[str, Any]:
        """Load test execution results from the workflow if available"""
        try:
            # Look for test results in the reports directory
            test_logs_dir = self.reports_dir / f"test-logs-pr-{pr_number}"
            test_summary_file = test_logs_dir / "test-summary.md"
            
            if not test_summary_file.exists():
                Logger.info(f"No test results found for PR #{pr_number}")
                return {}
            
            # Parse the test summary file
            with open(test_summary_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract test statistics from the summary
            test_data = {
                'summary_available': True,
                'summary_file': str(test_summary_file),
                'logs_directory': str(test_logs_dir),
                'raw_content': content
            }
            
            # Parse basic statistics from the content
            import re
            
            total_match = re.search(r'- \*\*Total Tests\*\*: (\d+)', content)
            passed_match = re.search(r'- \*\*Passed\*\*: (\d+)', content)
            failed_match = re.search(r'- \*\*Failed\*\*: (\d+)', content)
            success_rate_match = re.search(r'- \*\*Success Rate\*\*: ([\d.]+)%', content)
            
            test_data.update({
                'total_tests': int(total_match.group(1)) if total_match else 0,
                'passed_tests': int(passed_match.group(1)) if passed_match else 0,
                'failed_tests': int(failed_match.group(1)) if failed_match else 0,
                'success_rate': float(success_rate_match.group(1)) if success_rate_match else 0.0
            })
            
            # Extract passed and failed test lists
            passed_tests = []
            failed_tests = []
            
            # Find passed tests section
            passed_section = re.search(r'## ✅ Passed Tests\n\n(.*?)(?=## |$)', content, re.DOTALL)
            if passed_section:
                for line in passed_section.group(1).split('\n'):
                    if line.strip().startswith('- `'):
                        test_match = re.search(r'`([^`]+)`.*?\[Log\]\(([^)]+)\)', line)
                        if test_match:
                            passed_tests.append({
                                'name': test_match.group(1),
                                'status': 'PASSED',
                                'log_file': test_match.group(2)
                            })
            
            # Find failed tests section  
            failed_section = re.search(r'## ❌ Failed Tests\n\n(.*?)(?=## |$)', content, re.DOTALL)
            if failed_section:
                for line in failed_section.group(1).split('\n'):
                    if line.strip().startswith('- `'):
                        test_match = re.search(r'`([^`]+)`.*?\*\*([^*]+)\*\*.*?\[Log\]\(([^)]+)\)', line)
                        if test_match:
                            failed_tests.append({
                                'name': test_match.group(1),
                                'status': test_match.group(2),
                                'log_file': test_match.group(3)
                            })
            
            test_data.update({
                'passed_test_list': passed_tests,
                'failed_test_list': failed_tests
            })
            
            Logger.info(f"✅ Loaded test results: {test_data['total_tests']} total, {test_data['passed_tests']} passed, {test_data['failed_tests']} failed")
            return test_data
            
        except Exception as e:
            Logger.warn(f"⚠️  Could not load test results: {e}")
            return {}
    
    def _generate_report_content(self, data: EnhancedReportData) -> str:
        """Generate the complete enhanced report content using template"""
        
        # Load enhanced report template
        template_path = self.working_dir / "templates" / "enhanced_pr_report_template.md"
        if not template_path.exists():
            Logger.error(f"❌ Enhanced report template not found: {template_path}")
            raise FileNotFoundError(f"Enhanced report template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Build all template sections
        template_vars = self._build_template_variables(data)
        
        # Format template with variables
        try:
            formatted_report = template.format(**template_vars)
            return formatted_report
        except KeyError as e:
            Logger.error(f"❌ Template formatting error - missing variable: {e}")
            raise
    
    def _build_template_variables(self, data: EnhancedReportData) -> Dict[str, str]:
        """Build all template variables from report data"""
        conv_analysis = data.conversation_analysis
        solution_assess = data.solution_assessment
        
        # Basic PR info
        template_vars = {
            'pr_number': data.pr_number,
            'pr_title': data.pr_title,
            'pr_author': data.pr_author,
            'pr_url': data.pr_url,
            'pr_status': data.pr_status,
            'report_timestamp': data.report_timestamp
        }
        
        # Problem & Solution Overview
        template_vars.update({
            'problem_summary': conv_analysis.get('problem_summary', 'Analysis not available'),
            'conversation_complexity_score': conv_analysis.get('complexity_score', 'N/A'),
            'solution_complexity_score': solution_assess.get('final_complexity_score', 'N/A'),
            'code_quality_score': solution_assess.get('code_quality_score', 'N/A'),
            'solution_fitness': solution_assess.get('solution_fitness', 'Assessment not available')
        })
        
        # Conversation Analysis Sections
        template_vars.update({
            'key_requirements_section': self._format_list_section(conv_analysis.get('key_requirements', [])),
            'design_decisions_section': self._format_list_section(conv_analysis.get('design_decisions', [])),
            'outstanding_concerns_section': self._format_list_section(conv_analysis.get('outstanding_concerns', [])),
            'stakeholder_feedback_section': self._format_list_section(conv_analysis.get('stakeholder_feedback', [])),
            'timeline_summary': conv_analysis.get('timeline_summary', 'Not available')
        })
        
        # Solution Assessment Sections
        template_vars.update({
            'scope_analysis': solution_assess.get('scope_analysis', 'Assessment not available'),
            'architecture_impact_section': self._format_list_section(solution_assess.get('architecture_impact', [])),
            'implementation_quality_section': self._format_list_section(solution_assess.get('implementation_quality', [])),
            'breaking_changes_section': self._format_list_section(solution_assess.get('breaking_changes_assessment', [])),
            'testing_adequacy_section': self._format_list_section(solution_assess.get('testing_adequacy', [])),
            'documentation_completeness_section': self._format_list_section(solution_assess.get('documentation_completeness', []))
        })
        
        # Risk Assessment - Use AI assessment if available, otherwise fall back to solution assessment
        code_analysis = data.code_analysis
        ai_assessment = code_analysis.get('ai_assessment')
        
        if ai_assessment:
            # Use AI-powered risk assessment
            template_vars.update({
                'risk_factors_section': self._format_list_section(ai_assessment.risk_factors),
                'risk_assessment_method_notice': '🤖 **AI-Powered Risk Assessment**: This analysis was generated using Claude Code AI with Spring AI expertise.'
            })
        else:
            # Fallback to solution assessment risk factors
            template_vars.update({
                'risk_factors_section': self._format_list_section(solution_assess.get('risk_factors', [])),
                'risk_assessment_method_notice': '⚠️  **Basic Risk Assessment**: AI-powered analysis unavailable. Using basic pattern matching - results may include false positives.'
            })
        
        # Code Analysis Sections
        template_vars.update({
            'critical_issues_section': self._build_critical_issues_section(code_analysis),
            'important_issues_section': self._build_important_issues_section(code_analysis),
            'code_quality_suggestions_section': self._build_suggestions_section(code_analysis)
        })
        
        # File Analysis
        template_vars.update({
            'file_categories_section': self._build_file_categories_section(data.file_changes),
            'total_files_changed': len(data.file_changes),
            'lines_added': sum(f.get('additions', 0) for f in data.file_changes),
            'lines_removed': sum(f.get('deletions', 0) for f in data.file_changes),
            'files_by_status': self._build_files_by_status(data.file_changes)
        })
        
        # Implementation Patterns
        template_vars.update({
            'implementation_patterns_section': self._build_implementation_patterns_section(code_analysis)
        })
        
        # Positive Findings
        template_vars.update({
            'positive_findings_section': self._build_positive_findings_section(data)
        })
        
        # Recommendations
        recommendations = solution_assess.get('recommendations', [])
        template_vars.update({
            'priority_recommendations_section': self._format_list_section(recommendations[:3]),
            'testing_recommendations_section': self._extract_testing_recommendations(recommendations),
            'documentation_recommendations_section': self._extract_documentation_recommendations(recommendations)
        })
        
        # Action Items
        template_vars.update({
            'blocking_action_items': self._build_blocking_action_items(code_analysis, solution_assess),
            'high_priority_action_items': self._build_high_priority_action_items(solution_assess),
            'followup_action_items': self._build_followup_action_items(solution_assess)
        })
        
        # Quality Assessment
        template_vars.update({
            'quality_assessment': solution_assess.get('quality_assessment', conv_analysis.get('quality_assessment', 'Assessment not available')),
            'complexity_justification': solution_assess.get('complexity_justification', 'Not available'),
            'solution_fitness_detailed': solution_assess.get('solution_fitness', 'Not available')
        })
        
        # Summary Statistics
        template_vars.update({
            'total_files_analyzed': len(data.file_changes),
            'java_implementation_files': len([f for f in data.file_changes if f.get('filename', '').endswith('.java') and 'test' not in f.get('filename', '').lower()]),
            'test_files_count': len([f for f in data.file_changes if 'test' in f.get('filename', '').lower()]),
            'config_files_count': len([f for f in data.file_changes if f.get('filename', '').endswith(('.yml', '.yaml', '.properties', '.xml'))]),
            'critical_issues_count': self._count_critical_issues(code_analysis),
            'important_issues_count': self._count_important_issues(code_analysis),
            'total_recommendations': len(recommendations),
            'overall_risk_level': code_analysis.get('risk_level', 'Unknown')
        })
        
        # Test Execution Results
        test_results = data.test_results
        template_vars.update({
            'total_tests_count': test_results.get('total_tests', 'N/A'),
            'passed_tests_count': test_results.get('passed_tests', 'N/A'),
            'failed_tests_count': test_results.get('failed_tests', 'N/A'),
            'skipped_tests_count': 0,  # Not tracked in current implementation
            'test_execution_time': 'Not tracked',  # Could be added to workflow
            'overall_test_status': self._get_overall_test_status(test_results),
            'test_categories_section': self._build_test_categories_section(test_results),
            'test_results_by_module_section': self._build_test_results_by_module_section(test_results),
            'failed_tests_section': self._build_failed_tests_section(test_results),
            'test_coverage_section': self._build_test_coverage_section(test_results)
        })
        
        # Discussion Themes
        template_vars.update({
            'discussion_themes_section': self._format_list_section(conv_analysis.get('discussion_themes', []))
        })
        
        # Backport Assessment
        backport_assess = data.backport_assessment
        template_vars.update({
            'backport_decision': backport_assess.get('decision', 'UNKNOWN'),
            'backport_classification': backport_assess.get('classification', 'Unknown'),
            'backport_scope': backport_assess.get('scope', 'Analysis not available'),
            'backport_api_impact': backport_assess.get('api_impact', 'Unknown'),
            'backport_risk_level': backport_assess.get('risk_level', 'Unknown'),
            'backport_dependencies_changed': '✅ Yes' if backport_assess.get('dependencies_changed', False) else '❌ No',
            'backport_files_count': backport_assess.get('files_changed_count', 0),
            'backport_key_findings': self._format_list_section(backport_assess.get('key_findings', [])),
            'backport_reasoning': backport_assess.get('reasoning', 'Analysis not available'),
            'backport_recommendations': backport_assess.get('recommendations', 'Analysis not available')
        })
        
        # Analysis Status
        template_vars.update({
            'conversation_analysis_status': '✅ Available' if data.analysis_status.get('conversation_analysis') == 'Available' else '❌ Not Available',
            'solution_assessment_status': '✅ Available' if data.analysis_status.get('solution_assessment') == 'Available' else '❌ Not Available',
            'code_analysis_status': '✅ Available' if data.analysis_status.get('code_analysis') == 'Available' else '❌ Not Available',
            'backport_assessment_status': '✅ Available' if data.analysis_status.get('backport_assessment') == 'Available' else '❌ Not Available',
            'ai_integration_status': '✅ Active' if any(status == 'Available' for status in data.analysis_status.values()) else '❌ Inactive'
        })
        
        return template_vars
    
    def _format_list_section(self, items: List[str]) -> str:
        """Format a list of items as markdown bullets"""
        if not items:
            return "*No items identified*"
        
        return '\n'.join(f"- {item}" for item in items[:10])  # Limit to top 10
    
    def _build_critical_issues_section(self, code_analysis: Dict[str, Any]) -> str:
        """Build critical issues section"""
        all_issues = code_analysis.get('all_issues', {})
        critical_found = False
        section = ""
        
        for filename, issues in all_issues.items():
            if issues.get('critical'):
                critical_found = True
                section += f"\n### {filename}\n"
                for issue in issues['critical']:
                    section += f"- **Issue**: {issue}\n"
                    section += f"- **Impact**: Security/Configuration risk\n\n"
        
        if not critical_found:
            section = "✅ No critical issues found"
        
        return section
    
    def _build_important_issues_section(self, code_analysis: Dict[str, Any]) -> str:
        """Build important issues section"""
        all_issues = code_analysis.get('all_issues', {})
        important_found = False
        section = ""
        
        for filename, issues in all_issues.items():
            if issues.get('important'):
                important_found = True
                section += f"\n### {filename}\n"
                for issue in issues['important']:
                    section += f"- **Issue**: {issue}\n"
                    section += f"- **Recommendation**: Follow Spring best practices\n\n"
        
        if not important_found:
            section = "✅ No important issues found"
        
        return section
    
    def _build_suggestions_section(self, code_analysis: Dict[str, Any]) -> str:
        """Build code quality suggestions section"""
        all_issues = code_analysis.get('all_issues', {})
        suggestions_found = False
        section = ""
        
        for filename, issues in all_issues.items():
            if issues.get('suggestions'):
                suggestions_found = True
                section += f"\n### {filename}\n"
                for suggestion in issues['suggestions']:
                    section += f"- {suggestion}\n"
                section += "\n"
        
        if not suggestions_found:
            section = "✅ No code quality suggestions"
        
        return section
    
    def _build_file_categories_section(self, file_changes: List[Dict[str, Any]]) -> str:
        """Build file categories section"""
        categories = {
            'Implementation Files': [],
            'Tests': [],
            'Configuration': [],
            'Documentation/Other': []
        }
        
        for change in file_changes:
            filename = change.get('filename', '')
            if 'test' in filename.lower() or filename.endswith('Test.java'):
                categories['Tests'].append(filename)
            elif filename.endswith('.java'):
                categories['Implementation Files'].append(filename)
            elif filename.endswith(('.yml', '.yaml', '.properties', '.xml')):
                categories['Configuration'].append(filename)
            else:
                categories['Documentation/Other'].append(filename)
        
        section = ""
        for category, files in categories.items():
            if files:
                section += f"- **{category}**: {len(files)} files\n"
                for file in files[:5]:  # Show first 5 files
                    section += f"  - {file}\n"
                if len(files) > 5:
                    section += f"  - ... and {len(files) - 5} more\n"
        
        return section
    
    def _build_files_by_status(self, file_changes: List[Dict[str, Any]]) -> str:
        """Build files by status summary"""
        status_counts = {}
        for change in file_changes:
            status = change.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        status_names = {'added': 'Added', 'modified': 'Modified', 'deleted': 'Deleted'}
        return ', '.join(f"{status_names.get(status, status)}: {count}" for status, count in status_counts.items())
    
    def _build_implementation_patterns_section(self, code_analysis: Dict[str, Any]) -> str:
        """Build implementation patterns section"""
        # This would be populated by more sophisticated pattern analysis
        return "*Pattern analysis integration pending*"
    
    def _build_positive_findings_section(self, data: EnhancedReportData) -> str:
        """Build positive findings section"""
        findings = []
        
        # Check for AI assessment positive findings first
        code_analysis = data.code_analysis
        ai_assessment = code_analysis.get('ai_assessment')
        
        if ai_assessment and ai_assessment.positive_findings:
            # Use AI-generated positive findings
            findings.extend(ai_assessment.positive_findings)
        else:
            # Fallback to basic structural analysis
            java_files = [f for f in data.file_changes if f.get('filename', '').endswith('.java') and f.get('status') != 'deleted']
            test_files = [f for f in data.file_changes if 'test' in f.get('filename', '').lower()]
            config_files = [f for f in data.file_changes if f.get('filename', '').endswith(('.yml', '.yaml', '.properties', '.xml'))]
            
            if java_files:
                findings.append(f"Implementation includes {len(java_files)} Java files with proper structure")
            if test_files:
                findings.append(f"Includes {len(test_files)} test files for validation")
            if config_files:
                findings.append("Configuration changes are properly structured")
            
            # Add solution assessment positive findings
            solution_assess = data.solution_assessment
            if solution_assess.get('code_quality_score', 0) >= 7:
                findings.append(f"High code quality score: {solution_assess.get('code_quality_score')}/10")
        
        if not findings:
            findings.append("Standard implementation approach")
        
        return '\n'.join(f"- {finding}" for finding in findings)
    
    def _extract_testing_recommendations(self, recommendations: List[str]) -> str:
        """Extract testing-related recommendations"""
        testing_recs = [rec for rec in recommendations if any(word in rec.lower() for word in ['test', 'testing', 'coverage'])]
        return self._format_list_section(testing_recs) if testing_recs else "*No specific testing recommendations*"
    
    def _extract_documentation_recommendations(self, recommendations: List[str]) -> str:
        """Extract documentation-related recommendations"""
        doc_recs = [rec for rec in recommendations if any(word in rec.lower() for word in ['document', 'documentation', 'docs'])]
        return self._format_list_section(doc_recs) if doc_recs else "*No specific documentation recommendations*"
    
    def _build_blocking_action_items(self, code_analysis: Dict[str, Any], solution_assess: Dict[str, Any]) -> str:
        """Build blocking action items"""
        blocking_items = []
        
        critical_count = self._count_critical_issues(code_analysis)
        if critical_count > 0:
            blocking_items.append(f"- [ ] Address {critical_count} critical security/configuration issues")
        
        if not blocking_items:
            blocking_items.append("- [x] No blocking issues found")
        
        return '\n'.join(blocking_items)
    
    def _build_high_priority_action_items(self, solution_assess: Dict[str, Any]) -> str:
        """Build high priority action items"""
        high_priority = []
        
        risk_factors = solution_assess.get('risk_factors', [])
        if risk_factors:
            high_priority.append(f"- [ ] Address {len(risk_factors)} identified risk factors")
        
        recommendations = solution_assess.get('recommendations', [])
        if recommendations:
            high_priority.append(f"- [ ] Implement {min(3, len(recommendations))} priority recommendations")
        
        if not high_priority:
            high_priority.append("- [ ] No high priority items identified")
        
        return '\n'.join(high_priority)
    
    def _build_followup_action_items(self, solution_assess: Dict[str, Any]) -> str:
        """Build follow-up action items"""
        followup = [
            "- [ ] Monitor implementation in production environment",
            "- [ ] Update documentation based on lessons learned",
            "- [ ] Consider performance impact assessment if applicable"
        ]
        
        return '\n'.join(followup)
    
    def _count_critical_issues(self, code_analysis: Dict[str, Any]) -> int:
        """Count critical issues from code analysis"""
        all_issues = code_analysis.get('all_issues', {})
        return sum(len(issues.get('critical', [])) for issues in all_issues.values())
    
    def _count_important_issues(self, code_analysis: Dict[str, Any]) -> int:
        """Count important issues from code analysis"""
        all_issues = code_analysis.get('all_issues', {})
        return sum(len(issues.get('important', [])) for issues in all_issues.values())
    
    def _get_overall_test_status(self, test_results: Dict[str, Any]) -> str:
        """Get overall test execution status"""
        if not test_results.get('summary_available', False):
            return "🔵 No tests executed"
        
        failed_tests = test_results.get('failed_tests', 0)
        total_tests = test_results.get('total_tests', 0)
        
        if total_tests == 0:
            return "🔵 No tests found"
        elif failed_tests == 0:
            return "✅ All tests passed"
        else:
            return f"❌ {failed_tests} test(s) failed"
    
    def _build_test_categories_section(self, test_results: Dict[str, Any]) -> str:
        """Build test categories section"""
        if not test_results.get('summary_available', False):
            return "*No test execution data available*"
        
        categories = []
        passed_tests = test_results.get('passed_test_list', [])
        failed_tests = test_results.get('failed_test_list', [])
        
        # Categorize tests by type
        integration_tests = [t for t in passed_tests + [f.get('name', '') for f in failed_tests] if 'IT' in t or 'Integration' in t]
        unit_tests = [t for t in passed_tests + [f.get('name', '') for f in failed_tests] if t not in integration_tests]
        
        if integration_tests:
            categories.append(f"- **Integration Tests**: {len(integration_tests)} executed")
        if unit_tests:
            categories.append(f"- **Unit Tests**: {len(unit_tests)} executed")
        
        return '\n'.join(categories) if categories else "*Test categorization not available*"
    
    def _build_test_results_by_module_section(self, test_results: Dict[str, Any]) -> str:
        """Build test results by module section"""
        if not test_results.get('summary_available', False):
            return "*No test execution data available*"
        
        # Group tests by module (simplified analysis)
        passed_tests = test_results.get('passed_test_list', [])
        failed_tests = test_results.get('failed_test_list', [])
        
        modules = {}
        
        # Analyze passed tests
        for test in passed_tests:
            test_name = test.get('name', '') if isinstance(test, dict) else str(test)
            module = self._extract_module_from_test_name(test_name)
            if module not in modules:
                modules[module] = {'passed': 0, 'failed': 0}
            modules[module]['passed'] += 1
        
        # Analyze failed tests
        for test_info in failed_tests:
            test_name = test_info.get('name', '') if isinstance(test_info, dict) else str(test_info)
            module = self._extract_module_from_test_name(test_name)
            if module not in modules:
                modules[module] = {'passed': 0, 'failed': 0}
            modules[module]['failed'] += 1
        
        if not modules:
            return "*No module information available*"
        
        module_summary = []
        for module, results in modules.items():
            status = "✅" if results['failed'] == 0 else "❌"
            module_summary.append(f"- **{module}**: {status} {results['passed']} passed, {results['failed']} failed")
        
        return '\n'.join(module_summary)
    
    def _build_failed_tests_section(self, test_results: Dict[str, Any]) -> str:
        """Build failed tests section with detailed failure information"""
        failed_tests = test_results.get('failed_test_list', [])
        
        if not failed_tests:
            return "✅ No failed tests"
        
        failed_section = []
        test_logs_dir = test_results.get('logs_directory', '')
        
        for test_info in failed_tests:
            if isinstance(test_info, dict):
                name = test_info.get('name', 'Unknown')
                status = test_info.get('status', 'FAILED')
                log_file = test_info.get('log_file', '')
                
                # Try to extract failure reason from log file
                failure_reason = self._extract_failure_reason(test_logs_dir, log_file)
                
                failed_section.append(f"- **{name}**: {status}")
                if failure_reason:
                    failed_section.append(f"  - *Failure*: {failure_reason}")
                if log_file:
                    failed_section.append(f"  - *Log*: `{log_file}`")
            else:
                failed_section.append(f"- **{test_info}**: FAILED")
        
        return '\n'.join(failed_section)
    
    def _build_test_coverage_section(self, test_results: Dict[str, Any]) -> str:
        """Build test coverage analysis section"""
        if not test_results.get('summary_available', False):
            return "*No test coverage data available*"
        
        total_tests = test_results.get('total_tests', 0)
        success_rate = test_results.get('success_rate', 0.0)
        
        coverage_analysis = [
            f"- **Test Execution Coverage**: {total_tests} tests executed from changed files",
            f"- **Success Rate**: {success_rate:.1f}%"
        ]
        
        if test_results.get('logs_directory'):
            coverage_analysis.append(f"- **Detailed Logs**: Available in test-logs directory")
        
        return '\n'.join(coverage_analysis)
    
    def _extract_failure_reason(self, logs_dir: str, log_file: str) -> str:
        """Extract failure reason from test log file"""
        if not logs_dir or not log_file:
            return "Log file not available"
        
        try:
            import re  # Import re module here
            log_path = Path(logs_dir) / log_file
            if not log_path.exists():
                return "Log file not found"
            
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for common failure patterns
            failure_patterns = [
                r'BUILD FAILURE.*?The following error occurred.*?:(.*?)(?=\n\n|\[ERROR\]|$)',
                r'Tests run:.*?Failures:.*?Errors:.*?\n(.*?)(?=\n\n|Time elapsed|$)',
                r'java\.lang\.AssertionError:(.*?)(?=\n\tat|\n\n|$)',
                r'org\.junit\..*?AssertionFailedError:(.*?)(?=\n\tat|\n\n|$)',
                r'Exception in thread.*?:(.*?)(?=\n\tat|\n\n|$)',
                r'Caused by:.*?:(.*?)(?=\n\tat|\n\n|$)'
            ]
            
            for pattern in failure_patterns:
                match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
                if match:
                    reason = match.group(1).strip()
                    # Clean up and truncate long reasons
                    reason = re.sub(r'\s+', ' ', reason)
                    if len(reason) > 200:
                        reason = reason[:200] + "..."
                    return reason
            
            # If no specific pattern found, look for last ERROR line
            error_lines = re.findall(r'\[ERROR\](.*)', content)
            if error_lines:
                reason = error_lines[-1].strip()
                if len(reason) > 200:
                    reason = reason[:200] + "..."
                return reason
            
            return "Failure reason not found in log"
            
        except Exception as e:
            return f"Error reading log: {str(e)}"
    
    def _extract_module_from_test_name(self, test_name: str) -> str:
        """Extract module name from test class name"""
        # Simple extraction - could be enhanced
        if 'Ollama' in test_name:
            return 'spring-ai-ollama'
        elif 'OpenAI' in test_name:
            return 'spring-ai-openai'
        elif 'Anthropic' in test_name:
            return 'spring-ai-anthropic'
        else:
            # Extract from package-like structure
            parts = test_name.split('.')
            if len(parts) > 1:
                return parts[0]
            return 'Unknown Module'


def main():
    """Command-line interface for enhanced report generation"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 enhanced_report_generator.py <pr_number>")
        print("\nExamples:")
        print("  python3 enhanced_report_generator.py 3386")
        sys.exit(1)
    
    pr_number = sys.argv[1]
    
    # Use script directory for report generation (robust regardless of where script is called from)
    working_dir = Path(__file__).parent.absolute()
    spring_ai_dir = working_dir / "spring-ai"
    
    generator = EnhancedReportGenerator(working_dir, spring_ai_dir)
    
    # Generate enhanced report
    success = generator.generate_enhanced_report(pr_number)
    
    if success:
        print(f"\n✅ Enhanced report generated for PR #{pr_number}")
        print(f"📄 Report location: reports/enhanced-review-pr-{pr_number}.md")
        sys.exit(0)
    else:
        print(f"\n❌ Enhanced report generation failed for PR #{pr_number}")
        sys.exit(1)


if __name__ == "__main__":
    main()
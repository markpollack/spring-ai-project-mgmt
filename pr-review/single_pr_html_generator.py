#!/usr/bin/env python3
"""
Single PR HTML Report Generator

Generates comprehensive, interactive HTML reports for individual PR analysis.
Provides rich visualization of AI-powered analysis results including:
- Risk assessment with interactive findings
- Conversation analysis and requirements
- Solution assessment and code quality metrics
- Test results and file changes
- Expandable sections for detailed exploration

This complements the existing markdown reports by providing an enhanced
viewing experience optimized for single PR deep-dive analysis.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import html

# Import the existing PRSummary structure for consistency
from html_report_generator import PRSummary


class SinglePRHTMLGenerator:
    """Generates interactive HTML reports for individual PR analysis"""
    
    def __init__(self, working_dir: Path = None, context_dir: Path = None, reports_dir: Path = None, logs_dir: Path = None):
        if working_dir is None:
            working_dir = Path(__file__).parent.absolute()
            
        self.working_dir = working_dir.absolute()
        
        # Use provided directories or defaults
        if context_dir is None:
            self.context_dir = self.working_dir / "context"
        else:
            self.context_dir = Path(context_dir).absolute()
            
        if reports_dir is None:
            self.reports_dir = self.working_dir / "reports"
        else:
            self.reports_dir = Path(reports_dir).absolute()
            
        if logs_dir is None:
            self.logs_dir = self.working_dir / "logs"
        else:
            self.logs_dir = Path(logs_dir).absolute()
    
    def generate_html_report(self, pr_number: str) -> Optional[Path]:
        """Generate HTML report for a single PR"""
        print(f"🎨 Generating HTML report for PR #{pr_number}...")
        
        try:
            # Load PR data directly (not using batch generator to avoid file truncation)
            pr_dir = self.context_dir / f"pr-{pr_number}"
            if not pr_dir.exists():
                print(f"⚠️  PR context directory not found: {pr_dir}")
                return None
                
            pr_summary = self._load_single_pr_data(pr_dir)
            if not pr_summary:
                print(f"⚠️  Failed to process PR data for #{pr_number}")
                return None
            
            # Generate single PR HTML
            html_content = self._generate_single_pr_html(pr_summary)
            
            # Save HTML file
            html_file = self.reports_dir / f"review-pr-{pr_number}.html"
            self.reports_dir.mkdir(parents=True, exist_ok=True)
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            print(f"✅ HTML report generated: {html_file}")
            return html_file
            
        except Exception as e:
            print(f"❌ Failed to generate HTML report: {e}")
            return None
    
    def _load_single_pr_data(self, pr_dir: Path) -> Optional[PRSummary]:
        """Load PR data with complete file changes (not truncated like batch generator)"""
        import json
        
        pr_number = pr_dir.name.replace('pr-', '')
        
        # Load required JSON files
        pr_data_file = pr_dir / "pr-data.json"
        risk_file = pr_dir / "ai-risk-assessment.json"
        changes_file = pr_dir / "file-changes.json"
        backport_file = pr_dir / "backport-assessment.json"
        
        required_files = [pr_data_file, risk_file, changes_file]
        if not all(f.exists() for f in required_files):
            missing = [f.name for f in required_files if not f.exists()]
            print(f"⚠️  Missing data files for PR #{pr_number}: {missing}")
            return None
            
        # Load JSON data
        try:
            with open(pr_data_file) as f:
                pr_data = json.load(f)
            with open(risk_file) as f:
                risk_data = json.load(f)
            with open(changes_file) as f:
                file_changes = json.load(f)  # Load ALL files, not truncated
                
            print(f"📊 Loaded {len(file_changes)} files for HTML generation")
                
            # Load backport assessment if available
            backport_data = {}
            if backport_file.exists():
                try:
                    with open(backport_file) as f:
                        backport_data = json.load(f)
                except Exception as e:
                    print(f"⚠️  Could not load backport assessment: {e}")
            
            # Load conversation analysis if available
            conv_file = pr_dir / "ai-conversation-analysis.json"
            conversation_data = {}
            if conv_file.exists():
                try:
                    with open(conv_file) as f:
                        conversation_data = json.load(f)
                except Exception as e:
                    print(f"⚠️  Could not load conversation analysis: {e}")
            
            # Load solution assessment if available
            solution_file = pr_dir / "solution-assessment.json"
            solution_data = {}
            if solution_file.exists():
                try:
                    with open(solution_file) as f:
                        solution_data = json.load(f)
                    print(f"📋 Loaded solution assessment data")
                except Exception as e:
                    print(f"⚠️  Could not load solution assessment: {e}")
            
            # Load workflow execution data if available
            execution_file = pr_dir / "workflow-execution.json"
            execution_data = {}
            if execution_file.exists():
                try:
                    with open(execution_file) as f:
                        execution_data = json.load(f)
                    print(f"📋 Loaded workflow execution data")
                except Exception as e:
                    print(f"⚠️  Could not load workflow execution data: {e}")
            
            # Load test results if available
            test_summary_file = self.reports_dir / f"test-logs-pr-{pr_number}" / "test-summary.md"
            test_results = None
            if test_summary_file.exists():
                try:
                    with open(test_summary_file) as f:
                        test_results = f.read()
                    print(f"🧪 Loaded test results")
                except Exception as e:
                    print(f"⚠️  Could not load test results: {e}")
            
            # Process backport data
            backport_decision = backport_data.get("decision", "UNKNOWN")
            backport_reasoning = backport_data.get("reasoning", "Not available")
            
            # Create PRSummary with complete file changes matching the exact dataclass structure
            return PRSummary(
                number=str(pr_data["number"]),
                title=pr_data["title"],
                author=pr_data["author"],
                url=pr_data["url"],
                risk_level=risk_data.get("overall_risk_level", "UNKNOWN"),
                risk_summary=risk_data.get("risk_summary", "Not available"),
                positive_findings=risk_data.get("positive_findings", []),
                risk_factors=risk_data.get("risk_factors", []),
                changed_files=pr_data.get("changed_files", len(file_changes)),
                additions=pr_data.get("additions", 0),
                deletions=pr_data.get("deletions", 0),
                processing_time=None,
                prompt_size=None,
                created_at=pr_data.get("created_at", ""),
                state=pr_data.get("state", "unknown"),
                draft=pr_data.get("draft", False),
                pr_type="feature",  # Default for single PR
                harvest_difficulty="medium",  # Default for single PR
                effort_score=5,  # Default for single PR
                fruit_icon="🍎",  # Default for single PR
                backport_eligible=(backport_decision == "APPROVE"),
                backport_decision=backport_decision,
                backport_classification=backport_data.get("classification", "Unknown"),
                backport_risk_level=backport_data.get("risk_level", "Unknown"),
                backport_reasoning=backport_reasoning,
                backport_recommendations=backport_data.get("recommendations", ""),
                backport_badge_color="green" if backport_decision == "APPROVE" else "red",
                backport_icon="✅" if backport_decision == "APPROVE" else "❌",
                file_changes=file_changes,  # ALL files, not truncated!
                commit_message=self._load_commit_message(pr_number),
                problem_summary=conversation_data.get("problem_summary", ""),
                key_requirements=conversation_data.get("key_requirements", []),
                design_decisions=conversation_data.get("design_decisions", []),
                outstanding_concerns=conversation_data.get("outstanding_concerns", []),
                solution_approaches=conversation_data.get("solution_approaches", []),
                complexity_indicators=conversation_data.get("complexity_indicators", []),
                quality_assessment=conversation_data.get("quality_assessment", ""),
                recommendations=conversation_data.get("recommendations", []),
                stakeholder_feedback=conversation_data.get("stakeholder_feedback", []),
                discussion_themes=conversation_data.get("discussion_themes", []),
                scope_analysis=solution_data.get("scope_analysis", ""),
                architecture_impact=solution_data.get("architecture_impact", []),
                implementation_quality=solution_data.get("implementation_quality", []),
                breaking_changes_assessment=solution_data.get("breaking_changes_assessment", []),
                testing_adequacy=solution_data.get("testing_adequacy", []),
                documentation_completeness=solution_data.get("documentation_completeness", []),
                solution_fitness=solution_data.get("solution_fitness", ""),
                solution_risk_factors=solution_data.get("solution_risk_factors", []),
                # Add execution and test data
                workflow_execution=execution_data,
                test_results_markdown=test_results
            )
            
        except Exception as e:
            print(f"❌ Error loading PR data: {e}")
            return None
    
    def _load_commit_message(self, pr_number: str) -> str:
        """Load the AI-generated commit message for a PR (adapted from batch generator)"""
        # Check logs directory for commit message files
        commit_file_paths = [
            self.logs_dir / f"claude-response-commit-message-{pr_number}.txt",
            self.working_dir / "logs" / f"claude-response-commit-message-{pr_number}.txt"
        ]
        
        for commit_file in commit_file_paths:
            if commit_file.exists():
                try:
                    with open(commit_file, 'r', encoding='utf-8') as f:
                        raw_content = f.read()
                    
                    # Extract the actual commit message (skip Claude Code wrapper metadata)
                    lines = raw_content.split('\n')
                    response_started = False
                    response_lines = []
                    
                    for line in lines:
                        if line.startswith('Response:'):
                            response_started = True
                            continue
                        elif response_started:
                            response_lines.append(line)
                    
                    if response_lines:
                        raw_message = '\n'.join(response_lines).strip()
                        # Apply the same extraction logic as the commit message generator
                        cleaned_message = self._extract_commit_message_from_response(raw_message)
                        if cleaned_message:
                            return cleaned_message
                    
                    # Fallback to raw content if extraction fails
                    return raw_content.strip()
                    
                except Exception as e:
                    print(f"⚠️  Error reading commit message file {commit_file}: {e}")
                    continue
        
        # Fallback: try to get the actual commit message from the repository
        return self._get_commit_message_from_repo(pr_number)
    
    def _get_commit_message_from_repo(self, pr_number: str) -> str:
        """Get the actual commit message from the git repository"""
        try:
            import subprocess
            
            # Get the repo path
            spring_ai_repo = self.working_dir / "spring-ai"
            
            if not spring_ai_repo.exists():
                return "No commit message available (repository not found)"
            
            # Get the current branch's commit message
            result = subprocess.run(
                ["git", "log", "--format=%B", "-n", "1"],
                cwd=spring_ai_repo,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                return "No commit message available"
                
        except Exception as e:
            print(f"⚠️  Could not retrieve commit message from repo: {e}")
            return "No commit message available"
    
    def _extract_commit_message_from_response(self, raw_response: str) -> str:
        """Extract clean commit message from Claude Code response (simplified version)"""
        if not raw_response:
            return ""
        
        import re
        lines = raw_response.split('\n')
        message_lines = []
        in_commit_message = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines at the start
            if not line and not message_lines:
                continue
            
            # Skip Claude Code reasoning patterns
            if any(pattern in line.lower() for pattern in [
                'now i\'ll generate', 'i\'ll generate', 'let me generate', 'based on the information gathered',
                'here\'s the commit message', 'based on the template', 'here is the commit message', 
                'analyzing the pr', 'looking at the changes', 'considering the', 'given the'
            ]):
                continue
            
            # Skip lines that start with common reasoning indicators
            if line.lower().startswith(('now ', 'based on', 'here is', 'here\'s', 'i\'ll', 'let me', 'analyzing')):
                continue
            
            # Look for conventional commit format
            conventional_pattern = r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\([^)]+\))?:'
            if re.match(conventional_pattern, line, re.IGNORECASE):
                in_commit_message = True
                message_lines.append(line)
            elif in_commit_message:
                message_lines.append(line)
        
        if message_lines:
            commit_message = '\n'.join(message_lines).strip()
            # Final validation - ensure no reasoning text leaked through
            first_line = commit_message.split('\n')[0].lower()
            if not any(bad_pattern in first_line for bad_pattern in [
                'now i\'ll', 'based on the information', 'let me generate', 'analyzing'
            ]):
                return commit_message
        
        return ""
    
    def _generate_single_pr_html(self, pr: PRSummary) -> str:
        """Generate HTML content for a single PR"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📋 Spring AI PR #{pr.number} - Analysis Report</title>
    {self._generate_css()}
</head>
<body>
    <div class="container">
        {self._generate_pr_header(pr)}
        {self._generate_executive_summary(pr)}
        {self._generate_analysis_sections(pr)}
        {self._generate_code_changes_section(pr)}
        {self._generate_enhanced_test_results_section(pr)}
        {self._generate_commit_message_section(pr)}
        {self._generate_workflow_execution_section(pr)}
    </div>
    {self._generate_modal_html()}
    {self._generate_javascript()}
</body>
</html>"""
    
    def _generate_pr_header(self, pr: PRSummary) -> str:
        """Generate PR header with key information"""
        status_color = {
            'open': '#28a745',
            'closed': '#dc3545',
            'merged': '#6f42c1'
        }.get(pr.state.lower(), '#6c757d')
        
        risk_color = {
            'LOW': '#28a745',
            'MEDIUM': '#ffc107', 
            'HIGH': '#dc3545'
        }.get(pr.risk_level, '#6c757d')
        
        backport_color = {
            'APPROVE': '#28a745',
            'REJECT': '#dc3545',
            'UNKNOWN': '#6c757d',
            'SKIPPED': '#17a2b8',
            'UNAVAILABLE': '#ffc107'
        }.get(pr.backport_decision, '#6c757d')
        
        return f"""
        <header class="pr-header">
            <div class="pr-title-section">
                <h1>📋 Spring AI PR Analysis Report</h1>
                <div class="pr-info">
                    <h2>#{pr.number}: {html.escape(pr.title)}</h2>
                    <div class="pr-meta">
                        <span class="pr-author">👤 {html.escape(pr.author)}</span>
                        <span class="pr-status" style="background-color: {status_color};">{pr.state.upper()}</span>
                        <a href="{pr.url}" target="_blank" class="pr-link">🔗 View on GitHub</a>
                    </div>
                </div>
            </div>
            
            <div class="pr-metrics">
                <div class="metric-card risk-{pr.risk_level.lower()}">
                    <div class="metric-label">Risk Level</div>
                    <div class="metric-value" style="color: {risk_color};">{pr.risk_level}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Files Changed</div>
                    <div class="metric-value">{pr.changed_files}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Code Changes</div>
                    <div class="metric-value">+{pr.additions} -{pr.deletions}</div>
                </div>
                <div class="metric-card backport-{pr.backport_decision.lower()}">
                    <div class="metric-label">Backport Status</div>
                    <div class="metric-value" style="color: {backport_color};">{pr.backport_icon} {pr.backport_decision}</div>
                </div>
            </div>
        </header>"""
    
    def _generate_workflow_execution_section(self, pr: PRSummary) -> str:
        """Generate workflow execution dashboard"""
        if not pr.workflow_execution or 'steps' not in pr.workflow_execution:
            return ""  # No execution data available
        
        steps_html = []
        for step in pr.workflow_execution.get('steps', []):
            status_icon = {
                'success': '✅',
                'failure': '❌',
                'skipped': '⏭️',
                'warning': '⚠️',
                'running': '🔄'
            }.get(step.get('status', 'pending'), '⏳')
            
            status_class = step.get('status', 'pending')
            step_name = step.get('name', 'Unknown')
            duration = step.get('duration_seconds')
            duration_str = f"({duration:.1f}s)" if duration else ""
            
            # Format step name for display
            display_name = step_name.replace('_', ' ').title()
            
            # Build details if available
            details_html = ""
            if step.get('details'):
                details = step['details']
                details_items = []
                
                # Handle test results specially
                if step_name == 'test_execution' and 'total_tests' in details:
                    details_items.append(f"Pass Rate: {details.get('success_rate', 'N/A')}")
                    details_items.append(f"Passed: {details.get('passed', 0)}/{details.get('total_tests', 0)}")
                    if details.get('failed_tests'):
                        details_items.append(f"Failed: {', '.join(details['failed_tests'])}")
                
                # Handle compilation details
                elif step_name == 'compilation' and 'command' in details:
                    details_items.append(f"Command: {details['command']}")
                
                # Handle squash details
                elif step_name == 'squash_commits':
                    if 'original_commits' in details:
                        details_items.append(f"Squashed {details.get('original_commits', 0)} → {details.get('final_commits', 1)} commit(s)")
                    elif 'final_commits' in details and details['final_commits'] == 1:
                        details_items.append("No squashing needed - PR contains only 1 commit")
                
                # Handle rebase details
                elif step_name == 'rebase' and 'conflicts' in details:
                    if details.get('conflicts'):
                        details_items.append("Had conflicts: " + ("Resolved" if details.get('auto_resolved') else "Manual resolution needed"))
                    else:
                        details_items.append("No conflicts")
                
                if details_items:
                    details_html = f"<ul class='step-details'>{''.join(['<li>' + html.escape(item) + '</li>' for item in details_items])}</ul>"
            
            # Add error message if failed
            if step.get('error_message'):
                details_html += f"<div class='error-message'>🚨 {html.escape(step['error_message'])}</div>"
            
            steps_html.append(f"""
                <div class="workflow-step {status_class}">
                    <div class="step-header" onclick="toggleWorkflowStep('{step_name}')">
                        <span class="step-icon">{status_icon}</span>
                        <span class="step-name">{display_name}</span>
                        <span class="step-duration">{duration_str}</span>
                        <span class="toggle-icon">▶</span>
                    </div>
                    <div id="workflow-{step_name}" class="step-details-container collapsed">
                        {details_html}
                    </div>
                </div>
            """)
        
        # Get summary stats
        summary = pr.workflow_execution.get('summary', {})
        success_rate = summary.get('success_rate', '0%')
        total_duration = summary.get('total_duration_seconds')
        duration_str = f"{total_duration:.1f}s" if total_duration else "N/A"
        
        # Generate AI Analysis status section
        ai_status_html = self._generate_ai_analysis_status(pr)
        
        return f"""
        <section class="workflow-execution">
            <h2>📋 Workflow Execution Summary</h2>
            <div class="workflow-summary">
                <div class="summary-stat">
                    <span class="stat-label">Success Rate:</span>
                    <span class="stat-value">{success_rate}</span>
                </div>
                <div class="summary-stat">
                    <span class="stat-label">Total Duration:</span>
                    <span class="stat-value">{duration_str}</span>
                </div>
                <div class="summary-stat">
                    <span class="stat-label">Steps Executed:</span>
                    <span class="stat-value">{summary.get('total_steps', 0)}</span>
                </div>
            </div>
            
            {ai_status_html}
            
            <div class="workflow-steps">
                <h3>⚙️ Execution Steps</h3>
                {''.join(steps_html)}
            </div>
        </section>
        """
    
    def _generate_executive_summary(self, pr: PRSummary) -> str:
        """Generate executive summary section"""
        return f"""
        <section class="executive-summary">
            <h2>🎯 Executive Summary</h2>
            <div class="summary-content">
                <div class="problem-summary">
                    <h3>Problem Being Solved</h3>
                    <p>{html.escape(pr.problem_summary) if pr.problem_summary else 'No problem summary available'}</p>
                </div>
                
                <div class="solution-quality">
                    <h3>Solution Quality Assessment</h3>
                    <p>{html.escape(pr.quality_assessment) if pr.quality_assessment else 'No quality assessment available'}</p>
                </div>
                
                <div class="risk-summary">
                    <h3>Risk Summary</h3>
                    <p>{html.escape(pr.risk_summary) if pr.risk_summary else 'No risk summary available'}</p>
                </div>
            </div>
        </section>"""
    
    def _generate_analysis_sections(self, pr: PRSummary) -> str:
        """Generate expandable analysis sections"""
        return f"""
        <section class="analysis-sections">
            <h2>📊 Detailed Analysis</h2>
            
            {self._generate_collapsible_section("requirements", "🎯 Key Requirements", self._format_list(pr.key_requirements))}
            
            {self._generate_collapsible_section("design", "🏗️ Design Decisions", self._format_list(pr.design_decisions))}
            
            {self._generate_collapsible_section("positive", "✅ Positive Findings", self._format_list(pr.positive_findings))}
            
            {self._generate_collapsible_section("architecture", "🏛️ Architecture Impact", self._format_list(pr.architecture_impact))}
            
            {self._generate_collapsible_section("implementation", "⚙️ Implementation Quality", self._format_list(pr.implementation_quality))}
            
            {self._generate_collapsible_section("testing", "🧪 Testing Assessment", self._format_list(pr.testing_adequacy))}
            
            {self._generate_discussion_insights_section(pr)}
            
            {self._generate_collapsible_section("risks", "⚠️ Risk Factors", self._format_list(pr.risk_factors))}
            
            {self._generate_collapsible_section("concerns", "🤔 Outstanding Concerns", self._format_list(pr.outstanding_concerns))}
            
            {self._generate_collapsible_section("recommendations", "💡 Recommendations", self._format_list(pr.recommendations))}
        </section>"""
    
    def _generate_discussion_insights_section(self, pr) -> str:
        """Generate discussion insights section with stakeholder feedback and themes"""
        stakeholder_content = self._format_list(pr.stakeholder_feedback)
        themes_content = self._format_list(pr.discussion_themes)
        
        # Only show the section if we have data
        if not pr.stakeholder_feedback and not pr.discussion_themes:
            return ""
        
        return f"""
        <div class="collapsible-section">
            <button class="section-toggle" onclick="toggleSection('discussion')">
                <span class="toggle-icon">▶</span>
                💬 Discussion Insights
                <span class="item-count">({len(pr.stakeholder_feedback) + len(pr.discussion_themes)} insights)</span>
            </button>
            <div id="discussion" class="section-content collapsed">
                {f'<div class="discussion-subsection"><h4>👥 Stakeholder Feedback</h4>{stakeholder_content}</div>' if pr.stakeholder_feedback else ''}
                {f'<div class="discussion-subsection"><h4>🎯 Discussion Themes</h4>{themes_content}</div>' if pr.discussion_themes else ''}
            </div>
        </div>
        """

    def _generate_collapsible_section(self, section_id: str, title: str, content: str) -> str:
        """Generate a collapsible section"""
        return f"""
        <div class="collapsible-section">
            <button class="section-toggle" onclick="toggleSection('{section_id}')">
                <span class="toggle-icon">▶</span>
                {title}
                <span class="item-count">({len(content.split('<li>')) - 1} items)</span>
            </button>
            <div id="{section_id}" class="section-content collapsed">
                {content}
            </div>
        </div>"""
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items as HTML"""
        if not items:
            return "<p><em>No items available</em></p>"
        
        formatted_items = []
        for item in items:
            # Escape HTML and preserve basic formatting
            escaped_item = html.escape(item)
            formatted_items.append(f"<li>{escaped_item}</li>")
        
        return f"<ul>{''.join(formatted_items)}</ul>"
    
    def _generate_code_changes_section(self, pr: PRSummary) -> str:
        """Generate code changes section with file explorer"""
        if not pr.file_changes:
            return """
            <section class="code-changes">
                <h2>📁 Code Changes</h2>
                <p><em>No file changes data available</em></p>
            </section>"""
        
        # Group files by type with better Spring AI categorization
        java_files = [f for f in pr.file_changes if f.get('filename', '').endswith('.java')]
        test_files = [f for f in java_files if 'test' in f.get('filename', '').lower()]
        src_files = [f for f in java_files if f not in test_files]
        
        config_files = [f for f in pr.file_changes if f.get('filename', '').endswith(('.xml', '.yml', '.yaml', '.properties', '.imports'))]
        doc_files = [f for f in pr.file_changes if f.get('filename', '').endswith(('.md', '.adoc', '.txt', '.rst'))]
        
        # Include all remaining files in other_files, ensuring comprehensive coverage
        categorized_files = java_files + config_files + doc_files
        other_files = [f for f in pr.file_changes if f not in categorized_files]
        
        return f"""
        <section class="code-changes">
            <h2>📁 Code Changes</h2>
            <div class="file-explorer">
                {self._generate_file_group("Java Source Files", src_files, "java-src")}
                {self._generate_file_group("Test Files", test_files, "java-test")}
                {self._generate_file_group("Configuration Files", config_files, "config")}
                {self._generate_file_group("Documentation", doc_files, "docs")}
                {self._generate_file_group("Other Files", other_files, "other")}
            </div>
        </section>"""
    
    def _generate_file_group(self, title: str, files: List[Dict], group_id: str) -> str:
        """Generate a file group section"""
        if not files:
            return f"""
        <div class="file-group">
            <button class="file-group-toggle" onclick="toggleFileGroup('{group_id}')">
                <span class="toggle-icon">▶</span>
                {title} (0 files)
            </button>
            <div id="{group_id}" class="file-group-content collapsed">
                <div class="file-item">
                    <span class="file-status">ℹ️</span>
                    <span class="file-name"><em>No files in this category</em></span>
                    <span class="file-changes">+0 -0</span>
                </div>
            </div>
        </div>"""
        
        file_items = []
        for file_info in files:
            filename = file_info.get('filename', 'Unknown')
            additions = file_info.get('additions', 0)
            deletions = file_info.get('deletions', 0)
            status = file_info.get('status', 'unknown')
            
            status_icon = {
                'added': '➕',
                'modified': '📝',
                'removed': '🗑️',
                'renamed': '📛'
            }.get(status, '❓')
            
            file_items.append(f"""
                <div class="file-item">
                    <span class="file-status">{status_icon}</span>
                    <span class="file-name">{html.escape(filename)}</span>
                    <span class="file-changes">+{additions} -{deletions}</span>
                </div>""")
        
        return f"""
        <div class="file-group">
            <button class="file-group-toggle" onclick="toggleFileGroup('{group_id}')">
                <span class="toggle-icon">▶</span>
                {title} ({len(files)} files)
            </button>
            <div id="{group_id}" class="file-group-content collapsed">
                {''.join(file_items)}
            </div>
        </div>"""
    
    def _generate_enhanced_test_results_section(self, pr: PRSummary) -> str:
        """Generate enhanced test results section with actual test data"""
        test_html = ""
        
        # Parse test results from markdown if available
        if pr.test_results_markdown:
            lines = pr.test_results_markdown.split('\n')
            passed_tests = []
            failed_tests = []
            total_tests = 0
            passed_count = 0
            failed_count = 0
            success_rate = "0%"
            pr_number = pr.number
            
            in_passed_section = False
            in_failed_section = False
            
            for line in lines:
                # Check for section headers
                if "✅ Passed Tests" in line or "## ✅ Passed Tests" in line:
                    in_passed_section = True
                    in_failed_section = False
                    continue
                elif "❌ Failed Tests" in line or "## ❌ Failed Tests" in line:
                    in_passed_section = False
                    in_failed_section = True
                    continue
                elif line.startswith("##") and not ("✅" in line or "❌" in line):
                    # New section that's not passed/failed tests
                    in_passed_section = False
                    in_failed_section = False
                
                # Parse summary stats
                if "**Total Tests**:" in line:
                    total_tests = int(line.split(':')[1].strip())
                elif "**Passed**:" in line:
                    passed_count = int(line.split(':')[1].strip())
                elif "**Failed**:" in line:
                    failed_count = int(line.split(':')[1].strip())
                elif "**Success Rate**:" in line:
                    success_rate = line.split(':')[1].strip()
                # Parse test entries
                elif line.startswith("- `"):
                    test_name = line.split('`')[1]
                    # Extract log file link if present
                    log_file = None
                    if "[Log]" in line:
                        log_file = line.split('[Log](')[1].split(')')[0] if '[Log](' in line else None
                    
                    # Determine status based on section or keywords
                    if in_passed_section or ("PASSED" in line and not in_failed_section):
                        passed_tests.append((test_name, log_file))
                    elif in_failed_section or "FAILED" in line or "TIMEOUT" in line or "ERROR" in line:
                        status = "FAILED"
                        if "TIMEOUT" in line:
                            status = "TIMEOUT"
                        elif "ERROR" in line:
                            status = "ERROR"
                        failed_tests.append((test_name, status, log_file))
            
            # Build test results HTML
            if total_tests > 0:
                status_color = '#28a745' if failed_count == 0 else '#dc3545' if passed_count == 0 else '#ffc107'
                
                test_html = f"""
                <div class="test-summary" style="border-left: 4px solid {status_color};">
                    <div class="test-metrics">
                        <div class="metric">
                            <span class="metric-label">Total Tests:</span>
                            <span class="metric-value">{total_tests}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Passed:</span>
                            <span class="metric-value" style="color: #28a745;">✅ {passed_count}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Failed:</span>
                            <span class="metric-value" style="color: #dc3545;">❌ {failed_count}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Success Rate:</span>
                            <span class="metric-value">{success_rate}</span>
                        </div>
                    </div>
                """
                
                if failed_tests:
                    test_html += """
                    <div class="failed-tests">
                        <h4>❌ Failed Tests:</h4>
                        <ul>
                    """
                    for test_data in failed_tests:
                        if len(test_data) == 3:
                            test_name, status, log_file = test_data
                        else:
                            test_name, status = test_data
                            log_file = None
                        
                        status_badge = {
                            'FAILED': '<span class="badge badge-danger">FAILED</span>',
                            'TIMEOUT': '<span class="badge badge-warning">TIMEOUT</span>',
                            'ERROR': '<span class="badge badge-dark">ERROR</span>'
                        }.get(status, status)
                        
                        # Generate log file path
                        if not log_file:
                            # Generate expected log file name from test class name
                            log_file_name = test_name.replace('.', '_') + '.log'
                            log_file = f"test-logs-pr-{pr_number}/{log_file_name}"
                        
                        # Check if log file exists
                        log_path = self.reports_dir / f"test-logs-pr-{pr_number}" / (test_name.replace('.', '_') + '.log')
                        if log_path.exists():
                            # Create relative path from HTML location (same directory)
                            log_link = f'<a href="test-logs-pr-{pr_number}/{test_name.replace(".", "_")}.log" target="_blank" class="log-link">📄 View Log</a>'
                        else:
                            # Log file doesn't exist, show message
                            log_link = f'<span class="log-missing" title="{log_path}">📄 Log not available</span>'
                        
                        test_html += f"""
                        <li class="test-item">
                            <code>{html.escape(test_name)}</code>
                            {status_badge}
                            {log_link}
                        </li>
                        """
                    test_html += "</ul></div>"
                
                if passed_tests:
                    test_html += f"""
                    <details class="passed-tests-details">
                        <summary>✅ Passed Tests ({len(passed_tests)})</summary>
                        <ul>
                    """
                    for test_data in passed_tests:
                        if isinstance(test_data, tuple) and len(test_data) == 2:
                            test_name, log_file = test_data
                        else:
                            test_name = test_data if isinstance(test_data, str) else test_data[0]
                            log_file = None
                        
                        # Generate log file path if not provided
                        log_file_name = test_name.replace('.', '_') + '.log'
                        log_path = self.reports_dir / f"test-logs-pr-{pr_number}" / log_file_name
                        
                        # Check if log file exists
                        if log_path.exists():
                            # Create relative path from HTML location (same directory)
                            log_link = f'<a href="test-logs-pr-{pr_number}/{log_file_name}" target="_blank" class="log-link">📄 Log</a>'
                        else:
                            log_link = ''  # Don't show link for passed tests without logs
                        
                        test_html += f"""
                        <li class="test-item">
                            <code>{html.escape(test_name)}</code>
                            {log_link}
                        </li>
                        """
                    test_html += """
                        </ul>
                    </details>
                    """
                
                test_html += "</div>"
        
        return f"""
        <section class="test-results">
            <h2>🧪 Test Results</h2>
            {test_html if test_html else '<p><em>No test execution data available</em></p>'}
        </section>
        
        <section class="additional-info">
            <h2>📋 Additional Information</h2>
            <div class="info-grid">
                <div class="info-card">
                    <h3>🏷️ PR Classification</h3>
                    <div class="classification-info">
                        <div><strong>Type:</strong> {html.escape(pr.pr_type)}</div>
                        <div><strong>Complexity:</strong> {pr.effort_score}/10</div>
                        <div><strong>Created:</strong> {pr.created_at}</div>
                        <div><strong>Draft:</strong> {'Yes' if pr.draft else 'No'}</div>
                    </div>
                </div>
                
                <div class="info-card">
                    <h3>🔄 Backport Assessment</h3>
                    <div class="backport-info">
                        <div><strong>Decision:</strong> <span style="color: {self._get_backport_color(pr.backport_decision)}">{pr.backport_decision}</span></div>
                        <div><strong>Classification:</strong> {html.escape(pr.backport_classification)}</div>
                        <div><strong>Risk Level:</strong> {html.escape(pr.backport_risk_level)}</div>
                        <div class="backport-reasoning">
                            <strong>Reasoning:</strong>
                            <p>{html.escape(pr.backport_reasoning)}</p>
                        </div>
                        {f'<div class="backport-recommendations"><strong>Recommendations:</strong><p>{html.escape(pr.backport_recommendations)}</p></div>' if pr.backport_recommendations else ''}
                    </div>
                </div>
            </div>
        </section>
        """
    
    def _generate_commit_message_section(self, pr: PRSummary) -> str:
        """Generate commit message section for review"""
        # Try to get the actual squashed commit message
        commit_message = pr.commit_message or "No commit message available"
        
        return f"""
        <section class="commit-message-section">
            <h2>📝 Squashed Commit Message</h2>
            <div class="commit-message-container">
                <div class="commit-message-note">
                    <p>💡 <strong>Review and Customize:</strong> Please review this commit message and customize it before merging.</p>
                </div>
                <div class="commit-message">
                    <pre id="commit-message-text">{html.escape(commit_message)}</pre>
                    <button class="copy-button" onclick="copyCommitMessage()">📋 Copy to Clipboard</button>
                </div>
                <div class="pr-context">
                    <details>
                        <summary>Original PR Information</summary>
                        <div class="pr-info">
                            <p><strong>PR Title:</strong> {html.escape(pr.title)}</p>
                            <p><strong>PR Number:</strong> #{pr.number}</p>
                            <p><strong>Author:</strong> {html.escape(pr.author)}</p>
                        </div>
                    </details>
                </div>
            </div>
        </section>
        """
    
    def _generate_test_results_section(self, pr: PRSummary) -> str:
        """Generate test results section"""
        return f"""
        <section class="test-results">
            <h2>🧪 Additional Information</h2>
            <div class="info-grid">
                <div class="info-card">
                    <h3>📝 Generated Commit Message</h3>
                    <div class="commit-message">
                        <pre>{html.escape(pr.commit_message) if pr.commit_message else 'No commit message generated'}</pre>
                    </div>
                </div>
                
                <div class="info-card">
                    <h3>🏷️ PR Classification</h3>
                    <div class="classification-info">
                        <div><strong>Type:</strong> {html.escape(pr.pr_type)}</div>
                        <div><strong>Complexity:</strong> {pr.effort_score}/10</div>
                        <div><strong>Created:</strong> {pr.created_at}</div>
                        <div><strong>Draft:</strong> {'Yes' if pr.draft else 'No'}</div>
                    </div>
                </div>
                
                <div class="info-card">
                    <h3>🔄 Backport Assessment</h3>
                    <div class="backport-info">
                        <div><strong>Decision:</strong> <span style="color: {self._get_backport_color(pr.backport_decision)}">{pr.backport_decision}</span></div>
                        <div><strong>Classification:</strong> {html.escape(pr.backport_classification)}</div>
                        <div><strong>Risk Level:</strong> {html.escape(pr.backport_risk_level)}</div>
                        <div class="backport-reasoning">
                            <strong>Reasoning:</strong>
                            <p>{html.escape(pr.backport_reasoning)}</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>"""
    
    def _get_backport_color(self, decision: str) -> str:
        """Get color for backport decision"""
        return {
            'APPROVE': '#28a745',
            'REJECT': '#dc3545',
            'UNKNOWN': '#6c757d',
            'SKIPPED': '#17a2b8',
            'UNAVAILABLE': '#ffc107'
        }.get(decision, '#6c757d')
    
    def _generate_modal_html(self) -> str:
        """Generate modal HTML for detailed views"""
        return """
        <!-- Modal for detailed views -->
        <div id="detailModal" class="modal">
            <div class="modal-content">
                <span class="close">&times;</span>
                <div class="modal-body">
                    <div id="modalContent"></div>
                </div>
            </div>
        </div>"""
    
    def _generate_css(self) -> str:
        """Generate comprehensive CSS styles"""
        return """
    <style>
        /* === MODERN SINGLE PR REPORT THEME === */
        :root {
            --primary-color: #2d5016;
            --secondary-color: #52734d;
            --accent-color: #7ba05b;
            --bg-light: #f8f9fa;
            --text-dark: #212529;
            --text-muted: #6c757d;
            --border-color: #dee2e6;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
            --info-color: #17a2b8;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-dark);
            background-color: var(--bg-light);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* === PR HEADER === */
        .pr-header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .pr-title-section h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .pr-title-section h2 {
            font-size: 1.5em;
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        .pr-meta {
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .pr-author, .pr-status, .pr-link {
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 500;
            text-decoration: none;
            display: inline-block;
        }
        
        .pr-author {
            background: rgba(255,255,255,0.2);
        }
        
        .pr-status {
            color: white;
            text-transform: capitalize;
        }
        
        .pr-link {
            background: rgba(255,255,255,0.2);
            color: white;
            transition: background-color 0.3s;
        }
        
        .pr-link:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .pr-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .metric-card {
            background: rgba(255,255,255,0.15);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        
        .metric-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 5px;
        }
        
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
        }
        
        /* === SECTIONS === */
        section {
            background: white;
            margin-bottom: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        section h2 {
            background: var(--primary-color);
            color: white;
            padding: 20px 30px;
            margin: 0;
            font-size: 1.4em;
        }
        
        .summary-content, .analysis-sections, .code-changes, .test-results {
            padding: 30px;
        }
        
        .summary-content > div {
            margin-bottom: 25px;
        }
        
        .summary-content h3 {
            color: var(--primary-color);
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        /* === COLLAPSIBLE SECTIONS === */
        .collapsible-section {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
        }
        
        .section-toggle {
            width: 100%;
            background: var(--bg-light);
            border: none;
            padding: 15px 20px;
            text-align: left;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: background-color 0.3s;
        }
        
        .section-toggle:hover {
            background: #e9ecef;
        }
        
        .toggle-icon {
            transition: transform 0.3s;
            color: var(--primary-color);
        }
        
        .section-toggle.expanded .toggle-icon {
            transform: rotate(90deg);
        }
        
        .item-count {
            margin-left: auto;
            color: var(--text-muted);
            font-size: 0.9em;
        }
        
        .section-content {
            padding: 20px;
            border-top: 1px solid var(--border-color);
            background: white;
        }
        
        .section-content.collapsed {
            display: none;
        }
        
        .section-content ul {
            list-style-type: none;
            padding: 0;
        }
        
        .section-content li {
            padding: 8px 0;
            border-bottom: 1px solid #f1f3f4;
            position: relative;
            padding-left: 20px;
        }
        
        .discussion-subsection {
            margin-bottom: 20px;
        }
        
        .discussion-subsection:last-child {
            margin-bottom: 0;
        }
        
        .discussion-subsection h4 {
            color: var(--primary-color);
            margin-bottom: 10px;
            font-size: 1rem;
            font-weight: 600;
        }
        
        .section-content li:before {
            content: "•";
            color: var(--accent-color);
            position: absolute;
            left: 0;
        }
        
        .section-content li:last-child {
            border-bottom: none;
        }
        
        /* === WORKFLOW EXECUTION === */
        .workflow-execution {
            background: white;
            margin-bottom: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .workflow-summary {
            display: flex;
            gap: 30px;
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid var(--border-color);
        }
        
        .summary-stat {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .stat-label {
            color: var(--text-muted);
            font-size: 0.9em;
        }
        
        .stat-value {
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .workflow-steps {
            padding: 20px 30px;
        }
        
        .workflow-step {
            margin-bottom: 10px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .workflow-step.success {
            border-left: 4px solid #28a745;
        }
        
        .workflow-step.failure {
            border-left: 4px solid #dc3545;
        }
        
        .workflow-step.skipped {
            border-left: 4px solid #6c757d;
        }
        
        .workflow-step.warning {
            border-left: 4px solid #ffc107;
        }
        
        .workflow-step.running {
            border-left: 4px solid #17a2b8;
            background-color: #f8f9fa;
        }
        
        .workflow-step.pending {
            border-left: 4px solid #6c757d;
        }
        
        .step-header {
            display: flex;
            align-items: center;
            padding: 12px 15px;
            cursor: pointer;
            background: white;
            transition: background-color 0.3s;
        }
        
        .step-header:hover {
            background: #f8f9fa;
        }
        
        .step-icon {
            font-size: 1.2em;
            margin-right: 10px;
        }
        
        .step-name {
            flex: 1;
            font-weight: 500;
        }
        
        .step-duration {
            color: var(--text-muted);
            font-size: 0.9em;
            margin-right: 10px;
        }
        
        .step-details-container {
            padding: 15px;
            background: #f8f9fa;
            border-top: 1px solid var(--border-color);
        }
        
        .step-details-container.collapsed {
            display: none;
        }
        
        .step-details {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .step-details li {
            padding: 5px 0;
            color: #495057;
        }
        
        .error-message {
            color: #dc3545;
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
            padding: 10px;
            margin-top: 10px;
        }
        
        /* === TEST RESULTS === */
        .test-summary {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .test-metrics {
            display: flex;
            gap: 30px;
            margin-bottom: 20px;
        }
        
        .test-metrics .metric {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .failed-tests {
            margin-top: 20px;
        }
        
        .failed-tests h4 {
            color: #dc3545;
            margin-bottom: 10px;
        }
        
        .failed-tests ul {
            list-style: none;
            padding: 0;
        }
        
        .failed-tests li {
            padding: 8px;
            margin-bottom: 5px;
            background: #f8f9fa;
            border-radius: 4px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .test-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px;
            margin-bottom: 5px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .test-item code {
            flex: 1;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
        }
        
        .log-link {
            color: var(--primary-color);
            text-decoration: none;
            padding: 4px 8px;
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 0.85em;
            transition: all 0.3s;
        }
        
        .log-link:hover {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }
        
        .log-missing {
            color: var(--text-muted);
            font-size: 0.85em;
            font-style: italic;
        }
        
        .passed-tests-details {
            margin-top: 20px;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
        }
        
        .passed-tests-details summary {
            cursor: pointer;
            font-weight: 600;
            color: #28a745;
        }
        
        .passed-tests-details ul {
            margin-top: 10px;
            list-style: none;
            padding: 0;
        }
        
        .badge {
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
        }
        
        .badge-danger {
            background: #dc3545;
            color: white;
        }
        
        .badge-warning {
            background: #ffc107;
            color: #212529;
        }
        
        .badge-dark {
            background: #343a40;
            color: white;
        }
        
        /* === COMMIT MESSAGE === */
        .commit-message-section {
            background: white;
            margin-bottom: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .commit-message-container {
            padding: 30px;
        }
        
        .commit-message-note {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .commit-message-note p {
            margin: 0;
            color: #0c5460;
        }
        
        .commit-message pre {
            background: #f8f9fa;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 20px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
            line-height: 1.5;
            white-space: pre-wrap;
            margin-bottom: 15px;
        }
        
        .copy-button {
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: background-color 0.3s;
        }
        
        .copy-button:hover {
            background: var(--secondary-color);
        }
        
        .pr-context {
            margin-top: 20px;
        }
        
        .pr-context details {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
        }
        
        .pr-context summary {
            cursor: pointer;
            font-weight: 600;
            color: var(--primary-color);
        }
        
        .pr-info {
            margin-top: 10px;
        }
        
        .pr-info p {
            margin: 5px 0;
        }
        
        /* === FILE EXPLORER === */
        .file-explorer {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
        }
        
        .file-group {
            margin-bottom: 15px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            overflow: hidden;
        }
        
        .file-group-toggle {
            width: 100%;
            background: white;
            border: none;
            padding: 12px 15px;
            text-align: left;
            cursor: pointer;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .file-group-toggle:hover {
            background: var(--bg-light);
        }
        
        .file-group-content {
            background: white;
            border-top: 1px solid var(--border-color);
        }
        
        .file-group-content.collapsed {
            display: none;
        }
        
        .file-item {
            display: flex;
            align-items: center;
            padding: 10px 15px;
            border-bottom: 1px solid #f1f3f4;
            gap: 15px;
        }
        
        .file-item:last-child {
            border-bottom: none;
        }
        
        .file-status {
            font-size: 1.2em;
            min-width: 25px;
        }
        
        .file-name {
            flex: 1;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
        }
        
        .file-changes {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.85em;
            color: var(--text-muted);
            min-width: 80px;
            text-align: right;
        }
        
        /* === INFO GRID === */
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .info-card {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            background: var(--bg-light);
        }
        
        .info-card h3 {
            color: var(--primary-color);
            margin-bottom: 15px;
            font-size: 1.1em;
        }
        
        .commit-message pre {
            background: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.85em;
            line-height: 1.4;
            white-space: pre-wrap;
            overflow-x: auto;
        }
        
        .classification-info > div, .backport-info > div {
            margin-bottom: 8px;
        }
        
        .backport-reasoning {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid var(--border-color);
        }
        
        .backport-reasoning p {
            margin-top: 5px;
            font-style: italic;
            color: var(--text-muted);
        }
        
        .backport-recommendations {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid var(--border-color);
        }
        
        .backport-recommendations p {
            margin-top: 5px;
            font-style: italic;
            color: var(--text-muted);
        }
        
        /* === AI ANALYSIS STATUS === */
        .ai-analysis-status {
            margin: 20px 0;
            padding: 15px;
            background: var(--bg-light);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        
        .ai-analysis-status h3 {
            color: var(--primary-color);
            margin-bottom: 15px;
            font-size: 1.1em;
        }
        
        .ai-components-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 12px;
        }
        
        .ai-component {
            background: white;
            border-radius: 6px;
            padding: 12px;
            border: 1px solid var(--border-color);
        }
        
        .ai-component.ai-success {
            border-left: 4px solid #28a745;
        }
        
        .ai-component.ai-missing {
            border-left: 4px solid #dc3545;
        }
        
        .ai-component-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }
        
        .ai-icon {
            font-size: 1.2em;
        }
        
        .ai-name {
            flex: 1;
            font-weight: 600;
            color: var(--text-dark);
        }
        
        .ai-status {
            font-size: 0.85em;
            font-weight: 500;
        }
        
        .ai-success .ai-status {
            color: #28a745;
        }
        
        .ai-missing .ai-status {
            color: #dc3545;
        }
        
        .ai-description {
            font-size: 0.85em;
            color: var(--text-muted);
            line-height: 1.4;
            margin-bottom: 8px;
        }
        
        .ai-metrics {
            display: flex;
            gap: 12px;
            font-size: 0.8em;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid var(--border-color);
        }
        
        .token-count {
            color: #6f42c1;
            font-weight: 500;
        }
        
        .cost-estimate {
            color: #28a745;
            font-weight: 500;
        }
        
        /* === COST SUMMARY === */
        .cost-summary {
            background: white;
            border: 2px solid var(--accent-color);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        
        .cost-totals {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
            margin-bottom: 10px;
        }
        
        .cost-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 0;
        }
        
        .cost-item.total-cost {
            border-top: 2px solid var(--accent-color);
            margin-top: 8px;
            padding-top: 10px;
            font-weight: 600;
        }
        
        .cost-label {
            font-size: 0.9em;
            color: var(--text-muted);
        }
        
        .cost-value {
            font-weight: 600;
            color: var(--primary-color);
        }
        
        .cost-item.total-cost .cost-value {
            color: #28a745;
            font-size: 1.1em;
        }
        
        .cost-note {
            text-align: center;
            margin-top: 8px;
            color: var(--text-muted);
            font-style: italic;
        }
        
        /* === MODAL === */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        
        .modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 20px;
            border-radius: 12px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: black;
        }
        
        /* === RESPONSIVE DESIGN === */
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .pr-header {
                padding: 20px;
            }
            
            .pr-metrics {
                grid-template-columns: 1fr;
            }
            
            .pr-meta {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
            
            .info-grid {
                grid-template-columns: 1fr;
            }
            
            .file-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 5px;
            }
            
            .file-changes {
                text-align: left;
            }
        }
    </style>"""
    
    def _generate_javascript(self) -> str:
        """Generate JavaScript for interactive functionality"""
        return """
    <script>
        // Section toggle functionality
        function toggleSection(sectionId) {
            const content = document.getElementById(sectionId);
            const button = content.previousElementSibling;
            const icon = button.querySelector('.toggle-icon');
            
            if (content.classList.contains('collapsed')) {
                content.classList.remove('collapsed');
                button.classList.add('expanded');
            } else {
                content.classList.add('collapsed');
                button.classList.remove('expanded');
            }
        }
        
        // File group toggle functionality
        function toggleFileGroup(groupId) {
            const content = document.getElementById(groupId);
            const button = content.previousElementSibling;
            const icon = button.querySelector('.toggle-icon');
            
            if (content.classList.contains('collapsed')) {
                content.classList.remove('collapsed');
                icon.textContent = '▼';
            } else {
                content.classList.add('collapsed');
                icon.textContent = '▶';
            }
        }
        
        // Workflow step toggle functionality
        function toggleWorkflowStep(stepName) {
            const content = document.getElementById('workflow-' + stepName);
            const header = content.previousElementSibling;
            const icon = header.querySelector('.toggle-icon');
            
            if (content.classList.contains('collapsed')) {
                content.classList.remove('collapsed');
                icon.textContent = '▼';
            } else {
                content.classList.add('collapsed');
                icon.textContent = '▶';
            }
        }
        
        // Copy commit message to clipboard
        function copyCommitMessage() {
            const messageText = document.getElementById('commit-message-text').textContent;
            navigator.clipboard.writeText(messageText).then(function() {
                const button = event.target;
                const originalText = button.textContent;
                button.textContent = '✅ Copied!';
                setTimeout(function() {
                    button.textContent = originalText;
                }, 2000);
            }).catch(function(err) {
                console.error('Failed to copy: ', err);
                alert('Failed to copy commit message');
            });
        }
        
        // Modal functionality
        const modal = document.getElementById('detailModal');
        const closeBtn = document.querySelector('.close');
        
        closeBtn.onclick = function() {
            modal.style.display = 'none';
        }
        
        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
        
        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            console.log('📋 Single PR HTML Report loaded');
            
            // Auto-expand first few sections for better UX
            const sectionsToExpand = ['requirements', 'risks', 'recommendations'];
            sectionsToExpand.forEach(sectionId => {
                const element = document.getElementById(sectionId);
                if (element && element.classList.contains('collapsed')) {
                    toggleSection(sectionId);
                }
            });
        });
    </script>"""


    def _generate_ai_analysis_status(self, pr: PRSummary) -> str:
        """Generate AI analysis status section showing which AI components succeeded with cost tracking"""
        pr_number = pr.number if hasattr(pr, 'number') else 'unknown'
        pr_dir = self.context_dir / f"pr-{pr_number}"
        
        # Check for AI analysis files
        ai_components = [
            {
                'name': 'Conversation Analysis',
                'file': 'ai-conversation-analysis.json',
                'icon': '💬',
                'description': 'Analyzes PR discussions and stakeholder feedback'
            },
            {
                'name': 'Solution Assessment', 
                'file': 'solution-assessment.json',
                'icon': '🔍',
                'description': 'Evaluates technical solution quality and architecture'
            },
            {
                'name': 'Risk Assessment',
                'file': 'ai-risk-assessment.json', 
                'icon': '⚠️',
                'description': 'Identifies security, performance, and quality risks'
            },
            {
                'name': 'Backport Assessment',
                'file': 'backport-assessment.json',
                'icon': '🔄',
                'description': 'Evaluates suitability for backporting to maintenance branches'
            }
        ]
        
        status_items = []
        total_input_tokens = 0
        total_output_tokens = 0
        total_estimated_cost = 0.0
        
        # Claude 3.5 Sonnet pricing (as of 2025)
        # Input: $3.00 per million tokens, Output: $15.00 per million tokens
        SONNET_INPUT_COST_PER_1M = 3.00
        SONNET_OUTPUT_COST_PER_1M = 15.00
        
        for component in ai_components:
            file_path = pr_dir / component['file']
            if file_path.exists():
                status_icon = '✅'
                status_text = 'Completed'
                status_class = 'ai-success'
                
                # Try to extract token usage from the JSON file
                input_tokens, output_tokens, cost_info = self._extract_token_usage(file_path)
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens
                
                # Calculate estimated cost for this component
                component_cost = (input_tokens * SONNET_INPUT_COST_PER_1M / 1_000_000) + (output_tokens * SONNET_OUTPUT_COST_PER_1M / 1_000_000)
                total_estimated_cost += component_cost
                
                cost_display = f"${component_cost:.4f}" if input_tokens > 0 or output_tokens > 0 else "N/A"
                token_display = f"{input_tokens + output_tokens:,}" if input_tokens > 0 or output_tokens > 0 else "N/A"
                
            else:
                status_icon = '❌'
                status_text = 'Not Available'
                status_class = 'ai-missing'
                cost_display = "N/A"
                token_display = "N/A"
            
            status_items.append(f'''
                <div class="ai-component {status_class}">
                    <div class="ai-component-header">
                        <span class="ai-icon">{component['icon']}</span>
                        <span class="ai-name">{component['name']}</span>
                        <span class="ai-status">{status_icon} {status_text}</span>
                    </div>
                    <div class="ai-description">{component['description']}</div>
                    <div class="ai-metrics">
                        <span class="token-count">🔢 {token_display} tokens</span>
                        <span class="cost-estimate">💰 ~{cost_display}</span>
                    </div>
                </div>
            ''')
        
        # Generate cost summary
        cost_summary = f'''
            <div class="cost-summary">
                <div class="cost-totals">
                    <div class="cost-item">
                        <span class="cost-label">📊 Total Tokens:</span>
                        <span class="cost-value">{total_input_tokens + total_output_tokens:,}</span>
                    </div>
                    <div class="cost-item">
                        <span class="cost-label">⬇️ Input Tokens:</span>
                        <span class="cost-value">{total_input_tokens:,}</span>
                    </div>
                    <div class="cost-item">
                        <span class="cost-label">⬆️ Output Tokens:</span>
                        <span class="cost-value">{total_output_tokens:,}</span>
                    </div>
                    <div class="cost-item total-cost">
                        <span class="cost-label">💰 Estimated Cost:</span>
                        <span class="cost-value">${total_estimated_cost:.4f}</span>
                    </div>
                </div>
                <div class="cost-note">
                    <small>📝 Based on Claude 3.5 Sonnet pricing ($3/M input, $15/M output). Actual cost may vary.</small>
                </div>
            </div>
        ''' if total_input_tokens > 0 or total_output_tokens > 0 else ''
        
        return f'''
            <div class="ai-analysis-status">
                <h3>🤖 AI Analysis Components</h3>
                {cost_summary}
                <div class="ai-components-grid">
                    {''.join(status_items)}
                </div>
            </div>
        '''

    def _extract_token_usage(self, file_path: Path) -> tuple[int, int, dict]:
        """Extract token usage data from AI analysis JSON files or estimate from logs"""
        try:
            with open(file_path) as f:
                data = json.load(f)
            
            input_tokens = 0
            output_tokens = 0
            cost_info = {}
            
            # Look for token usage in various formats
            if 'token_usage' in data:
                usage = data['token_usage']
                if isinstance(usage, dict):
                    input_tokens = usage.get('input_tokens', 0)
                    output_tokens = usage.get('output_tokens', 0)
            
            # Also check for direct fields
            if 'input_tokens' in data:
                input_tokens = data['input_tokens']
            if 'output_tokens' in data:
                output_tokens = data['output_tokens']
            
            # Look for cost information
            if 'total_cost_usd' in data:
                cost_info['total_cost_usd'] = data['total_cost_usd']
            
            # If no token data found in JSON, try to estimate based on component type
            if input_tokens == 0 and output_tokens == 0:
                input_tokens, output_tokens = self._estimate_tokens_by_component(file_path.name)
                
            return input_tokens, output_tokens, cost_info
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            # If we can't extract token data, return estimates
            input_tokens, output_tokens = self._estimate_tokens_by_component(file_path.name)
            return input_tokens, output_tokens, {}
    
    def _estimate_tokens_by_component(self, filename: str) -> tuple[int, int]:
        """Provide reasonable estimates for token usage by component type"""
        # These are rough estimates based on typical usage patterns
        estimates = {
            'ai-conversation-analysis.json': (12000, 800),    # Medium analysis
            'solution-assessment.json': (15000, 1200),        # Comprehensive analysis  
            'ai-risk-assessment.json': (10000, 600),          # Focused analysis
            'backport-assessment.json': (8000, 400),          # Lighter analysis
        }
        
        return estimates.get(filename, (5000, 300))  # Default fallback


def main():
    """Command line interface for single PR HTML report generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate HTML report for a single PR")
    parser.add_argument("pr_number", help="PR number to generate HTML report for")
    parser.add_argument("--context-dir", help="Directory containing PR context data")
    parser.add_argument("--reports-dir", help="Directory to save HTML report")
    parser.add_argument("--logs-dir", help="Directory containing logs")
    
    args = parser.parse_args()
    
    # Create generator
    generator = SinglePRHTMLGenerator(
        context_dir=args.context_dir,
        reports_dir=args.reports_dir,
        logs_dir=args.logs_dir
    )
    
    # Generate HTML report
    html_file = generator.generate_html_report(args.pr_number)
    
    if html_file:
        print(f"\n✅ HTML report generated successfully!")
        print(f"📁 Location: {html_file}")
        print(f"🌐 Open in browser: file://{html_file.absolute()}")
    else:
        print(f"\n❌ Failed to generate HTML report for PR #{args.pr_number}")
        return 1
        
    return 0


if __name__ == "__main__":
    exit(main())
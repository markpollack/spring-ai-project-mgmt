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
            # Load PR data using the existing batch generator logic
            from html_report_generator import LowHangingFruitReportGenerator
            
            # Create temporary batch generator to reuse data loading logic
            batch_generator = LowHangingFruitReportGenerator(self.working_dir)
            
            # Process single PR directory
            pr_dir = self.context_dir / f"pr-{pr_number}"
            if not pr_dir.exists():
                print(f"⚠️  PR context directory not found: {pr_dir}")
                return None
                
            pr_summary = batch_generator._process_pr_directory(pr_dir)
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
        {self._generate_test_results_section(pr)}
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
            
            {self._generate_collapsible_section("architecture", "🏛️ Architecture Impact", self._format_list(pr.architecture_impact))}
            
            {self._generate_collapsible_section("implementation", "⚙️ Implementation Quality", self._format_list(pr.implementation_quality))}
            
            {self._generate_collapsible_section("testing", "🧪 Testing Assessment", self._format_list(pr.testing_adequacy))}
            
            {self._generate_collapsible_section("risks", "⚠️ Risk Factors", self._format_list(pr.risk_factors))}
            
            {self._generate_collapsible_section("concerns", "🤔 Outstanding Concerns", self._format_list(pr.outstanding_concerns))}
            
            {self._generate_collapsible_section("recommendations", "💡 Recommendations", self._format_list(pr.recommendations))}
            
            {self._generate_collapsible_section("positive", "✅ Positive Findings", self._format_list(pr.positive_findings))}
        </section>"""
    
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
        
        # Group files by type
        java_files = [f for f in pr.file_changes if f.get('filename', '').endswith('.java')]
        test_files = [f for f in java_files if 'test' in f.get('filename', '').lower()]
        src_files = [f for f in java_files if f not in test_files]
        config_files = [f for f in pr.file_changes if f.get('filename', '').endswith(('.xml', '.yml', '.yaml', '.properties'))]
        doc_files = [f for f in pr.file_changes if f.get('filename', '').endswith(('.md', '.adoc', '.txt'))]
        other_files = [f for f in pr.file_changes if f not in java_files + config_files + doc_files]
        
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
            return ""
        
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
        
        .section-content li:before {
            content: "•";
            color: var(--accent-color);
            position: absolute;
            left: 0;
        }
        
        .section-content li:last-child {
            border-bottom: none;
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
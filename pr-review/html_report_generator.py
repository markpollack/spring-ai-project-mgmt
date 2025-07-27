#!/usr/bin/env python3
"""
Low Hanging Fruit HTML Report Generator

Generates beautiful, interactive HTML dashboards for PR batch processing results
using garden/orchard metaphors to identify "low hanging fruit" PRs that are
easy to review and merge.

Features:
- Responsive design with modern CSS
- Interactive PR cards with diff previews
- Risk-based categorization with fruit metaphors
- Direct GitHub integration
- Sortable and filterable PR lists
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import html


@dataclass
class PRSummary:
    """Processed PR data for HTML report generation"""
    number: str
    title: str
    author: str
    url: str
    risk_level: str
    risk_summary: str
    positive_findings: List[str]
    risk_factors: List[str]
    
    # File statistics
    changed_files: int
    additions: int
    deletions: int
    
    # Processing metrics  
    processing_time: Optional[str]
    prompt_size: Optional[str]
    
    # PR metadata
    created_at: str
    state: str
    draft: bool
    pr_type: str  # Derived category (cleanup, docs, feature, etc.)
    
    # Harvest metrics (derived)
    harvest_difficulty: str  # easy, medium, hard
    effort_score: int  # 1-10 scale
    fruit_icon: str  # 🍎, 🍃, 🌿, 🌲
    
    # Diff data for previews
    file_changes: List[Dict[str, Any]]


class LowHangingFruitReportGenerator:
    """Generates interactive HTML reports for batch PR processing results"""
    
    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.context_dir = self.run_dir / "context"
        self.reports_dir = self.run_dir / "reports"
        self.pr_summaries: List[PRSummary] = []
        
    def generate_report(self) -> Path:
        """Generate the complete HTML report"""
        print("🌳 Generating PR Orchard Dashboard...")
        
        # Load and process PR data
        self._load_pr_data()
        
        # Categorize PRs by harvest difficulty
        self._categorize_prs()
        
        # Generate HTML report
        html_file = self.run_dir / "pr_orchard_dashboard.html"
        html_content = self._generate_html()
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"✅ Dashboard generated: {html_file}")
        return html_file
    
    def _load_pr_data(self):
        """Load PR data from context directories"""
        if not self.context_dir.exists():
            print("⚠️  No context directory found")
            return
            
        for pr_dir in self.context_dir.iterdir():
            if not pr_dir.is_dir() or not pr_dir.name.startswith('pr-'):
                continue
                
            try:
                pr_summary = self._process_pr_directory(pr_dir)
                if pr_summary:
                    self.pr_summaries.append(pr_summary)
            except Exception as e:
                print(f"⚠️  Error processing {pr_dir.name}: {e}")
    
    def _process_pr_directory(self, pr_dir: Path) -> Optional[PRSummary]:
        """Process a single PR directory into a PRSummary"""
        pr_number = pr_dir.name.replace('pr-', '')
        
        # Load required JSON files
        pr_data_file = pr_dir / "pr-data.json"
        risk_file = pr_dir / "ai-risk-assessment.json"
        changes_file = pr_dir / "file-changes.json"
        
        if not all(f.exists() for f in [pr_data_file, risk_file, changes_file]):
            print(f"⚠️  Missing data files for PR #{pr_number}")
            return None
            
        # Load JSON data
        with open(pr_data_file) as f:
            pr_data = json.load(f)
        with open(risk_file) as f:
            risk_data = json.load(f)
        with open(changes_file) as f:
            file_changes = json.load(f)
            
        # Determine PR type from analysis
        pr_type = self._classify_pr_type(pr_data, risk_data, file_changes)
        
        # Calculate harvest metrics
        harvest_difficulty, effort_score, fruit_icon = self._calculate_harvest_metrics(
            risk_data, pr_data, file_changes
        )
        
        return PRSummary(
            number=str(pr_data["number"]),
            title=pr_data["title"],
            author=pr_data["author"],
            url=pr_data["url"],
            risk_level=risk_data["overall_risk_level"],
            risk_summary=risk_data["risk_summary"],
            positive_findings=risk_data.get("positive_findings", []),
            risk_factors=risk_data.get("risk_factors", []),
            changed_files=pr_data.get("changed_files", 0),
            additions=pr_data.get("additions", 0),
            deletions=pr_data.get("deletions", 0),
            processing_time=None,  # Will be filled from batch metrics
            prompt_size=None,      # Will be filled from batch metrics
            created_at=pr_data["created_at"],
            state=pr_data["state"],
            draft=pr_data.get("draft", False),
            pr_type=pr_type,
            harvest_difficulty=harvest_difficulty,
            effort_score=effort_score,
            fruit_icon=fruit_icon,
            file_changes=file_changes[:5]  # Limit to first 5 files for preview
        )
    
    def _classify_pr_type(self, pr_data: Dict, risk_data: Dict, file_changes: List) -> str:
        """Classify PR type based on analysis"""
        title = pr_data["title"].lower()
        
        # Check for common patterns
        if any(word in title for word in ["remove", "unused", "import", "cleanup", "polish"]):
            return "cleanup"
        elif any(word in title for word in ["doc", "readme", "guide", "getting-started"]):
            return "documentation"
        elif any(word in title for word in ["test", "coverage", "spec"]):
            return "testing"
        elif any(word in title for word in ["fix", "bug", "error", "issue"]):
            return "bugfix"
        elif len(file_changes) > 20 or pr_data.get("additions", 0) > 500:
            return "major-feature"
        else:
            return "feature"
    
    def _calculate_harvest_metrics(self, risk_data: Dict, pr_data: Dict, 
                                 file_changes: List) -> Tuple[str, int, str]:
        """Calculate harvest difficulty, effort score, and fruit icon"""
        risk_level = risk_data["overall_risk_level"]
        files_changed = len(file_changes)
        additions = pr_data.get("additions", 0)
        deletions = pr_data.get("deletions", 0)
        total_changes = additions + deletions
        
        # Start with base effort score
        effort_score = 1
        
        # Adjust based on risk level
        if risk_level == "LOW":
            effort_score += 0
        elif risk_level == "MEDIUM":
            effort_score += 3
        elif risk_level == "HIGH":
            effort_score += 6
            
        # Adjust based on change size
        if total_changes < 10:
            effort_score += 0
        elif total_changes < 50:
            effort_score += 1
        elif total_changes < 200:
            effort_score += 2
        else:
            effort_score += 4
            
        # Adjust based on files changed
        if files_changed <= 3:
            effort_score += 0
        elif files_changed <= 10:
            effort_score += 1
        else:
            effort_score += 2
            
        # Determine difficulty and icon
        if effort_score <= 2:
            return "easy", effort_score, "🍎"  # Red apples - ready to pick
        elif effort_score <= 4:
            return "medium", effort_score, "🍃"  # Green leaves - easy reach
        elif effort_score <= 6:
            return "hard", effort_score, "🌿"  # Branch - need ladder
        else:
            return "very-hard", effort_score, "🌲"  # Tree top - major effort
    
    def _categorize_prs(self):
        """Sort PRs by harvest difficulty and effort"""
        self.pr_summaries.sort(key=lambda pr: (pr.effort_score, pr.risk_level, pr.changed_files))
    
    def _generate_html(self) -> str:
        """Generate the complete HTML report"""
        # Categorize PRs for display
        categories = {
            "easy": [pr for pr in self.pr_summaries if pr.harvest_difficulty == "easy"],
            "medium": [pr for pr in self.pr_summaries if pr.harvest_difficulty == "medium"],
            "hard": [pr for pr in self.pr_summaries if pr.harvest_difficulty == "hard"],
            "very-hard": [pr for pr in self.pr_summaries if pr.harvest_difficulty == "very-hard"]
        }
        
        # Generate HTML sections
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌳 Spring AI PR Orchard Dashboard</title>
    {self._generate_css()}
</head>
<body>
    <div class="container">
        {self._generate_header()}
        {self._generate_summary_stats()}
        {self._generate_orchard_sections(categories)}
    </div>
    {self._generate_javascript()}
</body>
</html>"""
        return html_content
    
    def _generate_header(self) -> str:
        """Generate dashboard header"""
        run_name = self.run_dir.name
        total_prs = len(self.pr_summaries)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""
        <header class="dashboard-header">
            <h1>🌳 Spring AI PR Orchard Dashboard</h1>
            <div class="header-info">
                <span class="run-info">Run: {run_name}</span>
                <span class="pr-count">PRs Analyzed: {total_prs}</span>
                <span class="timestamp">Generated: {timestamp}</span>
            </div>
        </header>
        """
    
    def _generate_summary_stats(self) -> str:
        """Generate summary statistics section"""
        total = len(self.pr_summaries)
        low_risk = len([pr for pr in self.pr_summaries if pr.risk_level == "LOW"])
        easy_harvest = len([pr for pr in self.pr_summaries if pr.harvest_difficulty == "easy"])
        
        return f"""
        <section class="summary-stats">
            <div class="stat-card low-hanging">
                <div class="stat-icon">🍎</div>
                <div class="stat-content">
                    <div class="stat-number">{easy_harvest}</div>
                    <div class="stat-label">Ready to Harvest</div>
                </div>
            </div>
            <div class="stat-card low-risk">
                <div class="stat-icon">✅</div>
                <div class="stat-content">
                    <div class="stat-number">{low_risk}</div>
                    <div class="stat-label">Low Risk PRs</div>
                </div>
            </div>
            <div class="stat-card total">
                <div class="stat-icon">📊</div>
                <div class="stat-content">
                    <div class="stat-number">{total}</div>
                    <div class="stat-label">Total PRs</div>
                </div>
            </div>
        </section>
        """
    
    def _generate_orchard_sections(self, categories: Dict[str, List[PRSummary]]) -> str:
        """Generate the main orchard sections"""
        sections = []
        
        section_config = {
            "easy": ("🍎 Ready to Harvest", "Low Hanging Fruit - Quick Wins", "ready-harvest"),
            "medium": ("🍃 Easy Picks", "Simple Reach - Low-Medium Effort", "easy-picks"),
            "hard": ("🌿 Requires Ladder", "Medium Risk/Effort", "requires-ladder"),
            "very-hard": ("🌲 Top Shelf", "High Risk/Complex", "top-shelf")
        }
        
        for difficulty, (title, subtitle, css_class) in section_config.items():
            prs = categories[difficulty]
            if prs:  # Only show sections with PRs
                sections.append(f"""
                <section class="orchard-section {css_class}">
                    <div class="section-header">
                        <h2>{title}</h2>
                        <p class="section-subtitle">{subtitle} ({len(prs)} PRs)</p>
                    </div>
                    <div class="pr-grid">
                        {self._generate_pr_cards(prs)}
                    </div>
                </section>
                """)
        
        return "\n".join(sections)
    
    def _generate_pr_cards(self, prs: List[PRSummary]) -> str:
        """Generate PR cards for a section"""
        cards = []
        for pr in prs:
            cards.append(self._generate_pr_card(pr))
        return "\n".join(cards)
    
    def _generate_pr_card(self, pr: PRSummary) -> str:
        """Generate a single PR card"""
        # Escape HTML content
        title = html.escape(pr.title)
        author = html.escape(pr.author)
        risk_summary = html.escape(pr.risk_summary)
        
        # Generate diff preview if available
        diff_preview = self._generate_diff_preview(pr.file_changes) if pr.file_changes else ""
        
        # Generate positive findings list
        positive_list = ""
        if pr.positive_findings:
            items = [f"<li>{html.escape(finding)}</li>" for finding in pr.positive_findings[:3]]
            positive_list = f"<ul class='positive-findings'>{''.join(items)}</ul>"
        
        return f"""
        <div class="pr-card" data-risk="{pr.risk_level.lower()}" data-type="{pr.pr_type}">
            <div class="pr-header">
                <div class="pr-icon">{pr.fruit_icon}</div>
                <div class="pr-title-section">
                    <h3 class="pr-title">
                        <a href="{pr.url}" target="_blank" class="pr-link">
                            #{pr.number}: {title}
                        </a>
                    </h3>
                    <div class="pr-meta">
                        <span class="pr-author">by {author}</span>
                        <span class="pr-type">{pr.pr_type}</span>
                        <span class="risk-badge risk-{pr.risk_level.lower()}">{pr.risk_level}</span>
                    </div>
                </div>
            </div>
            
            <div class="pr-stats">
                <div class="stat">
                    <span class="stat-label">Files:</span>
                    <span class="stat-value">{pr.changed_files}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Lines:</span>
                    <span class="stat-value">+{pr.additions}/-{pr.deletions}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Effort:</span>
                    <span class="stat-value">{pr.effort_score}/10</span>
                </div>
            </div>
            
            <div class="pr-summary">
                <p class="risk-summary">{risk_summary}</p>
                {positive_list}
            </div>
            
            {diff_preview}
            
            <div class="pr-actions">
                <a href="{pr.url}" target="_blank" class="btn btn-primary">View on GitHub</a>
                <a href="{pr.url}/files" target="_blank" class="btn btn-secondary">View Files</a>
            </div>
        </div>
        """
    
    def _generate_diff_preview(self, file_changes: List[Dict[str, Any]]) -> str:
        """Generate diff preview section for small PRs"""
        if not file_changes or len(file_changes) > 3:
            return ""  # Only show previews for small PRs
            
        previews = []
        for change in file_changes[:3]:  # Limit to 3 files
            filename = html.escape(change["filename"])
            patch = change.get("patch", "")
            if patch and len(patch) < 1000:  # Only show small patches
                previews.append(f"""
                <div class="file-diff">
                    <div class="file-header">{filename}</div>
                    <pre class="diff-content">{html.escape(patch)}</pre>
                </div>
                """)
        
        if previews:
            return f"""
            <div class="diff-preview" style="display: none;">
                <div class="diff-header">
                    <h4>📋 Quick Preview</h4>
                    <button class="toggle-diff">Hide Preview</button>
                </div>
                <div class="diff-files">
                    {''.join(previews)}
                </div>
            </div>
            <button class="show-diff-btn">🔍 Show Diff Preview</button>
            """
        return ""
    
    def _generate_css(self) -> str:
        """Generate CSS styles with orchard/garden theme"""
        return """
        <style>
        /* === ORCHARD DASHBOARD THEME === */
        :root {
            --orchard-green: #2d5016;
            --apple-red: #dc3545;
            --leaf-green: #28a745;
            --bark-brown: #8b4513;
            --sky-blue: #87ceeb;
            --earth-tan: #deb887;
            --harvest-gold: #ffd700;
            --fresh-mint: #f0fff0;
            --shadow-soft: rgba(0, 0, 0, 0.1);
            --shadow-medium: rgba(0, 0, 0, 0.15);
        }
        
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #f0fff0 0%, #e8f5e8 100%);
            min-height: 100vh;
            color: var(--orchard-green);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* === HEADER STYLES === */
        .dashboard-header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: linear-gradient(45deg, var(--orchard-green), var(--leaf-green));
            border-radius: 20px;
            color: white;
            box-shadow: 0 8px 32px var(--shadow-medium);
        }
        
        .dashboard-header h1 {
            margin: 0 0 15px 0;
            font-size: 2.5rem;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header-info {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            font-size: 1rem;
            opacity: 0.9;
        }
        
        .header-info span {
            padding: 8px 16px;
            background: rgba(255,255,255,0.2);
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }
        
        /* === SUMMARY STATS === */
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: white;
            border-radius: 16px;
            padding: 25px;
            display: flex;
            align-items: center;
            gap: 20px;
            box-shadow: 0 4px 20px var(--shadow-soft);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border-left: 5px solid;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 30px var(--shadow-medium);
        }
        
        .stat-card.low-hanging {
            border-left-color: var(--apple-red);
            background: linear-gradient(135deg, #fff 0%, #ffe6e6 100%);
        }
        
        .stat-card.low-risk {
            border-left-color: var(--leaf-green);
            background: linear-gradient(135deg, #fff 0%, #e6ffe6 100%);
        }
        
        .stat-card.total {
            border-left-color: var(--sky-blue);
            background: linear-gradient(135deg, #fff 0%, #e6f7ff 100%);
        }
        
        .stat-icon {
            font-size: 3rem;
            line-height: 1;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--orchard-green);
            line-height: 1;
        }
        
        .stat-label {
            font-size: 1rem;
            color: #666;
            margin-top: 5px;
            font-weight: 500;
        }
        
        /* === ORCHARD SECTIONS === */
        .orchard-section {
            margin-bottom: 50px;
        }
        
        .section-header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 2px 10px var(--shadow-soft);
        }
        
        .section-header h2 {
            margin: 0 0 10px 0;
            font-size: 2rem;
            font-weight: 600;
        }
        
        .ready-harvest .section-header {
            background: linear-gradient(135deg, #ffe6e6 0%, #ffcccc 100%);
            border-left: 5px solid var(--apple-red);
        }
        
        .easy-picks .section-header {
            background: linear-gradient(135deg, #e6ffe6 0%, #ccffcc 100%);
            border-left: 5px solid var(--leaf-green);
        }
        
        .requires-ladder .section-header {
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b3 100%);
            border-left: 5px solid #ff9800;
        }
        
        .top-shelf .section-header {
            background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
            border-left: 5px solid #9c27b0;
        }
        
        .section-subtitle {
            margin: 0;
            color: #666;
            font-size: 1.1rem;
        }
        
        /* === PR GRID === */
        .pr-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 25px;
        }
        
        /* === PR CARDS === */
        .pr-card {
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 4px 20px var(--shadow-soft);
            transition: all 0.3s ease;
            border-left: 4px solid transparent;
            position: relative;
            overflow: hidden;
        }
        
        .pr-card::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 100px;
            height: 100px;
            background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%);
            transform: translate(30px, -30px);
        }
        
        .pr-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 40px var(--shadow-medium);
        }
        
        .pr-card[data-risk="low"] {
            border-left-color: var(--leaf-green);
        }
        
        .pr-card[data-risk="medium"] {
            border-left-color: #ff9800;
        }
        
        .pr-card[data-risk="high"] {
            border-left-color: var(--apple-red);
        }
        
        .pr-header {
            display: flex;
            align-items: flex-start;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .pr-icon {
            font-size: 2.5rem;
            line-height: 1;
            flex-shrink: 0;
        }
        
        .pr-title-section {
            flex-grow: 1;
            min-width: 0;
        }
        
        .pr-title {
            margin: 0 0 10px 0;
            font-size: 1.2rem;
            font-weight: 600;
            line-height: 1.3;
        }
        
        .pr-link {
            text-decoration: none;
            color: var(--orchard-green);
            transition: color 0.3s ease;
        }
        
        .pr-link:hover {
            color: var(--leaf-green);
            text-decoration: underline;
        }
        
        .pr-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            font-size: 0.9rem;
        }
        
        .pr-author {
            color: #666;
            font-weight: 500;
        }
        
        .pr-type {
            background: var(--earth-tan);
            color: var(--orchard-green);
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: capitalize;
        }
        
        .risk-badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .risk-low {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .risk-medium {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .risk-high {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        /* === PR STATS === */
        .pr-stats {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-label {
            display: block;
            font-size: 0.8rem;
            color: #666;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        .stat-value {
            display: block;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--orchard-green);
        }
        
        /* === PR SUMMARY === */
        .pr-summary {
            margin-bottom: 20px;
        }
        
        .risk-summary {
            margin: 0 0 15px 0;
            color: #333;
            line-height: 1.5;
            font-size: 0.95rem;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 3px solid var(--leaf-green);
        }
        
        .positive-findings {
            margin: 0;
            padding-left: 20px;
            list-style: none;
        }
        
        .positive-findings li {
            position: relative;
            margin-bottom: 8px;
            padding-left: 25px;
            font-size: 0.9rem;
            color: #2d5016;
            line-height: 1.4;
        }
        
        .positive-findings li::before {
            content: '✅';
            position: absolute;
            left: 0;
            top: 0;
        }
        
        /* === DIFF PREVIEW === */
        .show-diff-btn {
            background: var(--leaf-green);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.3s ease;
            margin-bottom: 15px;
        }
        
        .show-diff-btn:hover {
            background: var(--orchard-green);
            transform: translateY(-2px);
        }
        
        .diff-preview {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid #e9ecef;
        }
        
        .diff-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .diff-header h4 {
            margin: 0;
            color: var(--orchard-green);
            font-size: 1rem;
        }
        
        .toggle-diff {
            background: none;
            border: 1px solid #ccc;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8rem;
        }
        
        .file-diff {
            margin-bottom: 15px;
        }
        
        .file-header {
            background: var(--earth-tan);
            padding: 8px 12px;
            border-radius: 5px 5px 0 0;
            font-weight: 500;
            font-size: 0.9rem;
            color: var(--orchard-green);
        }
        
        .diff-content {
            background: #f8f9fa;
            padding: 12px;
            margin: 0;
            border-radius: 0 0 5px 5px;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
            font-size: 0.8rem;
            line-height: 1.4;
            overflow-x: auto;
            border: 1px solid #e9ecef;
            border-top: none;
        }
        
        /* === PR ACTIONS === */
        .pr-actions {
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 10px 20px;
            border-radius: 20px;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
            text-align: center;
            flex: 1;
        }
        
        .btn-primary {
            background: var(--leaf-green);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--orchard-green);
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: white;
            color: var(--orchard-green);
            border: 2px solid var(--leaf-green);
        }
        
        .btn-secondary:hover {
            background: var(--leaf-green);
            color: white;
            transform: translateY(-2px);
        }
        
        /* === RESPONSIVE DESIGN === */
        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            .dashboard-header h1 {
                font-size: 2rem;
            }
            
            .header-info {
                flex-direction: column;
                gap: 10px;
            }
            
            .pr-grid {
                grid-template-columns: 1fr;
            }
            
            .pr-header {
                flex-direction: column;
                gap: 10px;
            }
            
            .pr-stats {
                flex-direction: column;
                gap: 10px;
            }
            
            .pr-actions {
                flex-direction: column;
            }
        }
        
        /* === LOADING AND ANIMATIONS === */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .pr-card {
            animation: fadeInUp 0.6s ease forwards;
        }
        
        .pr-card:nth-child(2) { animation-delay: 0.1s; }
        .pr-card:nth-child(3) { animation-delay: 0.2s; }
        .pr-card:nth-child(4) { animation-delay: 0.3s; }
        .pr-card:nth-child(5) { animation-delay: 0.4s; }
        .pr-card:nth-child(6) { animation-delay: 0.5s; }
        </style>
        """
    
    def _generate_javascript(self) -> str:
        """Generate JavaScript for interactivity"""
        return """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🌳 PR Orchard Dashboard loaded');
            
            // Initialize diff preview toggles
            initializeDiffPreviews();
            
            // Add smooth scrolling to anchors
            addSmoothScrolling();
            
            // Add card hover effects
            addCardInteractions();
            
            console.log('✅ Dashboard initialization complete');
        });
        
        function initializeDiffPreviews() {
            // Handle diff preview toggle buttons
            document.querySelectorAll('.show-diff-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const card = this.closest('.pr-card');
                    const preview = card.querySelector('.diff-preview');
                    
                    if (preview) {
                        const isVisible = preview.style.display !== 'none';
                        
                        if (isVisible) {
                            preview.style.display = 'none';
                            this.innerHTML = '🔍 Show Diff Preview';
                            this.style.background = 'var(--leaf-green)';
                        } else {
                            preview.style.display = 'block';
                            this.innerHTML = '📋 Hide Diff Preview';
                            this.style.background = 'var(--orchard-green)';
                        }
                        
                        // Smooth scroll to show the preview
                        if (!isVisible) {
                            setTimeout(() => {
                                preview.scrollIntoView({ 
                                    behavior: 'smooth', 
                                    block: 'nearest' 
                                });
                            }, 100);
                        }
                    }
                });
            });
            
            // Handle individual diff toggle buttons
            document.querySelectorAll('.toggle-diff').forEach(button => {
                button.addEventListener('click', function() {
                    const preview = this.closest('.diff-preview');
                    preview.style.display = 'none';
                    
                    const showBtn = preview.parentElement.querySelector('.show-diff-btn');
                    if (showBtn) {
                        showBtn.innerHTML = '🔍 Show Diff Preview';
                        showBtn.style.background = 'var(--leaf-green)';
                    }
                });
            });
        }
        
        function addSmoothScrolling() {
            // Add scroll-to-section functionality
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });
            
            document.querySelectorAll('.orchard-section').forEach(section => {
                section.style.opacity = '0';
                section.style.transform = 'translateY(30px)';
                section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                observer.observe(section);
            });
        }
        
        function addCardInteractions() {
            // Add enhanced hover effects and interactions
            document.querySelectorAll('.pr-card').forEach(card => {
                const icon = card.querySelector('.pr-icon');
                
                card.addEventListener('mouseenter', function() {
                    if (icon) {
                        icon.style.transform = 'scale(1.1) rotate(5deg)';
                        icon.style.transition = 'transform 0.3s ease';
                    }
                });
                
                card.addEventListener('mouseleave', function() {
                    if (icon) {
                        icon.style.transform = 'scale(1) rotate(0deg)';
                    }
                });
                
                // Add click-to-expand functionality for mobile
                if (window.innerWidth <= 768) {
                    card.addEventListener('click', function(e) {
                        if (e.target.tagName !== 'A' && e.target.tagName !== 'BUTTON') {
                            this.classList.toggle('expanded');
                        }
                    });
                }
            });
        }
        
        // Add keyboard navigation
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                // Hide all open diff previews
                document.querySelectorAll('.diff-preview').forEach(preview => {
                    if (preview.style.display !== 'none') {
                        preview.style.display = 'none';
                        const showBtn = preview.parentElement.querySelector('.show-diff-btn');
                        if (showBtn) {
                            showBtn.innerHTML = '🔍 Show Diff Preview';
                            showBtn.style.background = 'var(--leaf-green)';
                        }
                    }
                });
            }
        });
        
        // Add performance monitoring
        window.addEventListener('load', function() {
            const loadTime = performance.now();
            console.log(`🚀 Dashboard loaded in ${Math.round(loadTime)}ms`);
            
            // Add subtle fade-in effect after load
            document.body.style.opacity = '0';
            document.body.style.transition = 'opacity 0.5s ease';
            setTimeout(() => {
                document.body.style.opacity = '1';
            }, 100);
        });
        </script>
        """


def main():
    """Command line entry point for testing"""
    import sys
    if len(sys.argv) != 2:
        print("Usage: python html_report_generator.py <run_directory>")
        sys.exit(1)
        
    run_dir = Path(sys.argv[1])
    if not run_dir.exists():
        print(f"Error: Run directory {run_dir} does not exist")
        sys.exit(1)
        
    generator = LowHangingFruitReportGenerator(run_dir)
    html_file = generator.generate_report()
    print(f"🎉 Report generated successfully: {html_file}")


if __name__ == "__main__":
    main()
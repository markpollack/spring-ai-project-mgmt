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
    
    # Git branch info
    actual_branch: str = ""  # The actual git branch name for this PR
    
    # PR metadata
    created_at: str
    state: str
    draft: bool
    pr_type: str  # Derived category (cleanup, docs, feature, etc.)
    
    # Harvest metrics (derived)
    harvest_difficulty: str  # easy, medium, hard
    effort_score: int  # 1-10 scale
    fruit_icon: str  # 🍎, 🍃, 🌿, 🌲
    
    # Backport eligibility information
    backport_eligible: bool  # Whether PR is approved for backporting
    backport_decision: str  # APPROVE/REJECT/UNKNOWN
    backport_classification: str  # Bug Fix/Documentation/Feature/etc.
    backport_risk_level: str  # Low/Medium/High backport risk
    backport_reasoning: str  # Brief reasoning for decision
    backport_recommendations: str  # Recommendations for backporting
    backport_badge_color: str  # CSS color class for badge
    backport_icon: str  # Icon for backport status
    
    # Diff data for previews
    file_changes: List[Dict[str, Any]]
    
    # AI-generated commit message
    commit_message: str
    
    # Conversation analysis data
    problem_summary: str
    key_requirements: List[str]
    design_decisions: List[str]
    outstanding_concerns: List[str]
    solution_approaches: List[str]
    complexity_indicators: List[str]
    quality_assessment: str
    recommendations: List[str]
    stakeholder_feedback: List[str]
    
    # Solution assessment data
    scope_analysis: str
    architecture_impact: List[str]
    implementation_quality: List[str]
    breaking_changes_assessment: List[str]
    testing_adequacy: List[str]
    documentation_completeness: List[str]
    solution_fitness: str
    solution_risk_factors: List[str]


class LowHangingFruitReportGenerator:
    """Generates interactive HTML reports for batch PR processing results"""
    
    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.context_dir = self.run_dir / "context"
        self.reports_dir = self.run_dir / "reports"
        self.pr_summaries: List[PRSummary] = []
        # Load branch mapping from state directory
        self.branch_mapping = self._load_branch_mapping()
    
    def _load_branch_mapping(self) -> Dict[str, str]:
        """Load PR to branch name mapping from state file"""
        # Try to find the state directory (could be in parent dir)
        state_file = self.run_dir.parent.parent / "state" / "pr-branch-mapping.json"
        if not state_file.exists():
            # Try alternate location
            state_file = Path(__file__).parent / "state" / "pr-branch-mapping.json"
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    mapping = json.load(f)
                    print(f"✅ Loaded branch mapping with {len(mapping)} entries")
                    return mapping
            except Exception as e:
                print(f"⚠️  Could not load branch mapping: {e}")
        else:
            print("⚠️  No branch mapping file found")
        return {}
        
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
        backport_file = pr_dir / "backport-assessment.json"
        
        # At minimum, we need pr-data to show something
        if not pr_data_file.exists():
            print(f"⚠️  No PR data file for PR #{pr_number}, skipping")
            return None
            
        # Load PR data (required)
        with open(pr_data_file) as f:
            pr_data = json.load(f)
        
        # Load risk assessment (optional - use defaults if missing)
        if risk_file.exists():
            with open(risk_file) as f:
                risk_data = json.load(f)
        else:
            print(f"⚠️  Missing risk assessment for PR #{pr_number}, using defaults")
            risk_data = {
                "critical_issues": [],
                "important_issues": [],
                "risk_factors": [],
                "positive_findings": ["Risk assessment unavailable"]
            }
        
        # Load file changes (optional - use empty if missing)
        if changes_file.exists():
            with open(changes_file) as f:
                file_changes = json.load(f)
        else:
            print(f"⚠️  Missing file changes for PR #{pr_number}, using empty list")
            file_changes = []
            
        # Load backport assessment if available
        backport_data = {}
        if backport_file.exists():
            try:
                with open(backport_file) as f:
                    backport_data = json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading backport data for PR #{pr_number}: {e}")
                backport_data = {}
        
        # Load conversation analysis if available
        conversation_file = pr_dir / "ai-conversation-analysis.json"
        conversation_data = {}
        if conversation_file.exists():
            try:
                with open(conversation_file) as f:
                    conversation_data = json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading conversation data for PR #{pr_number}: {e}")
                conversation_data = {}
                
        # Load solution assessment if available  
        solution_file = pr_dir / "solution-assessment.json"
        solution_data = {}
        if solution_file.exists():
            try:
                with open(solution_file) as f:
                    solution_data = json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading solution data for PR #{pr_number}: {e}")
                solution_data = {}
            
        # Determine PR type from analysis
        pr_type = self._classify_pr_type(pr_data, risk_data, file_changes)
        
        # Calculate harvest metrics
        harvest_difficulty, effort_score, fruit_icon = self._calculate_harvest_metrics(
            risk_data, pr_data, file_changes
        )
        
        # Process backport assessment data
        backport_info = self._process_backport_data(backport_data)
        
        # Load commit message
        commit_message = self._load_commit_message(str(pr_data["number"]))
        
        # Get actual branch name from mapping
        pr_num = str(pr_data["number"])
        actual_branch = self.branch_mapping.get(pr_num, f"pr-{pr_num}-branch")  # Fallback to placeholder
        
        return PRSummary(
            number=pr_num,
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
            actual_branch=actual_branch,
            created_at=pr_data["created_at"],
            state=pr_data["state"],
            draft=pr_data.get("draft", False),
            pr_type=pr_type,
            harvest_difficulty=harvest_difficulty,
            effort_score=effort_score,
            fruit_icon=fruit_icon,
            # Backport information
            backport_eligible=backport_info["eligible"],
            backport_decision=backport_info["decision"],
            backport_classification=backport_info["classification"],
            backport_risk_level=backport_info["risk_level"],
            backport_reasoning=backport_info["reasoning"],
            backport_recommendations=backport_info["recommendations"],
            backport_badge_color=backport_info["badge_color"],
            backport_icon=backport_info["icon"],
            file_changes=file_changes[:5],  # Limit to first 5 files for preview
            commit_message=commit_message,
            # Conversation analysis data
            problem_summary=conversation_data.get("problem_summary", ""),
            key_requirements=conversation_data.get("key_requirements", []),
            design_decisions=conversation_data.get("design_decisions", []),
            outstanding_concerns=conversation_data.get("outstanding_concerns", []),
            solution_approaches=conversation_data.get("solution_approaches", []),
            complexity_indicators=conversation_data.get("complexity_indicators", []),
            quality_assessment=conversation_data.get("quality_assessment", ""),
            recommendations=conversation_data.get("recommendations", []),
            stakeholder_feedback=conversation_data.get("stakeholder_feedback", []),
            # Solution assessment data
            scope_analysis=solution_data.get("scope_analysis", ""),
            architecture_impact=solution_data.get("architecture_impact", []),
            implementation_quality=solution_data.get("implementation_quality", []),
            breaking_changes_assessment=solution_data.get("breaking_changes_assessment", []),
            testing_adequacy=solution_data.get("testing_adequacy", []),
            documentation_completeness=solution_data.get("documentation_completeness", []),
            solution_fitness=solution_data.get("solution_fitness", ""),
            solution_risk_factors=solution_data.get("risk_factors", [])
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
    
    def _enhance_tooltip_content(self, content: str, tooltip_type: str = "general") -> str:
        """Enhance tooltip content for better readability and formatting"""
        if not content:
            return content
        
        # Clean up the content
        enhanced = content.strip()
        
        # Debug removed - tooltip content processing working correctly
        
        # Format based on tooltip type
        if tooltip_type == "risk":
            # Risk tooltips: Add structure for better readability
            if "Low risk" in enhanced:
                enhanced = f"🟢 {enhanced}"
            elif "Medium risk" in enhanced:
                enhanced = f"🟡 {enhanced}"
            elif "High risk" in enhanced:
                enhanced = f"🔴 {enhanced}"
                
        elif tooltip_type == "backport":
            # Backport tooltips: Add structure and icons
            if "APPROVE" in enhanced or "recommended" in enhanced.lower():
                enhanced = f"✅ {enhanced}"
            elif "REJECT" in enhanced or "not recommended" in enhanced.lower():
                enhanced = f"❌ {enhanced}"
            elif "CONSIDER" in enhanced or "consider" in enhanced.lower():
                enhanced = f"⚠️ {enhanced}"
        
        # Ensure proper sentence structure
        if enhanced and not enhanced.endswith('.'):
            enhanced += '.'
        
        # Temporarily remove truncation to debug tooltip issues
        # TODO: Re-add sensible limits after debugging
        # max_length = 500 if tooltip_type == "backport" else 300
        # break_length = 450 if tooltip_type == "backport" else 250
        # min_break = 300 if tooltip_type == "backport" else 150
        
        # if len(enhanced) > max_length:
        #     # Find a good break point
        #     break_point = enhanced[:break_length].rfind('. ')
        #     if break_point > min_break:  # Only truncate if we found a reasonable break point
        #         enhanced = enhanced[:break_point + 1] + "..."
        
        return enhanced
    
    def _get_risk_tooltip(self, risk_level: str) -> str:
        """Get tooltip text for risk badges"""
        risk_tooltips = {
            "LOW": "Low Risk: Minimal security/stability impact, safe to review",
            "MEDIUM": "Medium Risk: Moderate impact, review carefully for potential issues", 
            "HIGH": "High Risk: Significant impact, thorough review required"
        }
        return risk_tooltips.get(risk_level.upper(), f"{risk_level} risk level")
    
    def _get_backport_tooltip(self, backport_decision: str) -> str:
        """Get tooltip text for backport badges"""
        backport_tooltips = {
            "APPROVE": "Backport Approved: Safe for 1.0.x release branch",
            "REJECT": "Backport Rejected: Not suitable for 1.0.x release",
            "UNKNOWN": "Backport Assessment: Analysis pending or unavailable"
        }
        return backport_tooltips.get(backport_decision.upper(), f"Backport {backport_decision}")
        
    def _get_pr_type_tooltip(self, pr_type: str) -> str:
        """Get tooltip text for PR type badges"""
        pr_type_tooltips = {
            "feature": "Feature: New functionality addition",
            "major-feature": "Major Feature: Large functionality addition (>20 files or >500 lines)",
            "bugfix": "Bug Fix: Resolves existing issues or errors",
            "cleanup": "Cleanup: Code refactoring, unused code removal, or maintenance",
            "documentation": "Documentation: Updates to docs, guides, or README files",
            "testing": "Testing: Test additions, improvements, or coverage enhancements"
        }
        return pr_type_tooltips.get(pr_type.lower(), f"PR Type: {pr_type}")
    
    def _generate_key_requirements_list(self, requirements: List[str]) -> str:
        """Generate HTML for key requirements (first 2-3 items)"""
        if not requirements:
            return ""
        
        # Show first 2-3 requirements for main card
        display_requirements = requirements[:3]
        items = [f"<li>{html.escape(req)}</li>" for req in display_requirements]
        
        if len(requirements) > 3:
            remaining = len(requirements) - 3
            items.append(f"<li class='requirements-more'>+ {remaining} more requirements...</li>")
        
        return f"<ul class='key-requirements'>{''.join(items)}</ul>"
    
    def _generate_problem_analysis_content(self, pr: 'PRSummary') -> str:
        """Generate HTML content for Problem Analysis modal card"""
        if not pr.problem_summary:
            return "<p>Problem analysis not available</p>"
        
        # Complete requirements list
        requirements_html = ""
        if pr.key_requirements:
            req_items = [f"<li>{html.escape(req)}</li>" for req in pr.key_requirements]
            requirements_html = f"<div class='modal-section'><h4>Key Requirements:</h4><ul>{''.join(req_items)}</ul></div>"
        
        # Design decisions
        decisions_html = ""
        if pr.design_decisions:
            dec_items = [f"<li>{html.escape(dec)}</li>" for dec in pr.design_decisions]
            decisions_html = f"<div class='modal-section'><h4>Design Decisions:</h4><ul>{''.join(dec_items)}</ul></div>"
        
        # Solution approaches
        approaches_html = ""
        if pr.solution_approaches:
            app_items = [f"<li>{html.escape(app)}</li>" for app in pr.solution_approaches]
            approaches_html = f"<div class='modal-section'><h4>Solution Approach:</h4><ul>{''.join(app_items)}</ul></div>"
        
        # Quality assessment
        quality_html = ""
        if pr.quality_assessment:
            quality_html = f"<div class='modal-section'><h4>Quality Assessment:</h4><p>{html.escape(pr.quality_assessment)}</p></div>"
        
        return f"""
        <div class='modal-section'>
            <h4>Problem Summary:</h4>
            <p>{html.escape(pr.problem_summary)}</p>
        </div>
        {requirements_html}
        {decisions_html}
        {approaches_html}
        {quality_html}
        """
    
    def _generate_backport_assessment_content(self, pr: 'PRSummary') -> str:
        """Generate HTML content for Backport Assessment modal card"""
        recommendations_html = ""
        if pr.backport_recommendations:
            recommendations_html = f"<div class='modal-section'><h4>Recommendations:</h4><p>{html.escape(pr.backport_recommendations)}</p></div>"
        
        return f"""
        <div class='modal-section'>
            <div class="backport-decision {pr.backport_decision.lower()}">{pr.backport_icon} {pr.backport_decision}</div>
            <p><strong>Classification:</strong> {pr.backport_classification}</p>
            <p><strong>Risk Level:</strong> {pr.backport_risk_level}</p>
        </div>
        <div class='modal-section'>
            <h4>Reasoning:</h4>
            <p>{html.escape(pr.backport_reasoning)}</p>
        </div>
        {recommendations_html}
        """
    
    def _generate_technical_concerns_content(self, pr: 'PRSummary') -> str:
        """Generate HTML content for Technical Concerns modal card"""
        concerns_html = ""
        if pr.outstanding_concerns:
            con_items = [f"<li>{html.escape(con)}</li>" for con in pr.outstanding_concerns]
            concerns_html = f"<div class='modal-section'><h4>Outstanding Concerns:</h4><ul>{''.join(con_items)}</ul></div>"
        
        complexity_html = ""
        if pr.complexity_indicators:
            comp_items = [f"<li>{html.escape(comp)}</li>" for comp in pr.complexity_indicators]
            complexity_html = f"<div class='modal-section'><h4>Complexity Indicators:</h4><ul>{''.join(comp_items)}</ul></div>"
        
        recommendations_html = ""
        if pr.recommendations:
            rec_items = [f"<li>{html.escape(rec)}</li>" for rec in pr.recommendations]
            recommendations_html = f"<div class='modal-section'><h4>Recommendations:</h4><ul>{''.join(rec_items)}</ul></div>"
        
        feedback_html = ""
        if pr.stakeholder_feedback and any(pr.stakeholder_feedback):
            feedback_items = [f"<li>{html.escape(fb)}</li>" for fb in pr.stakeholder_feedback if fb.strip()]
            if feedback_items:
                feedback_html = f"<div class='modal-section'><h4>Stakeholder Feedback:</h4><ul>{''.join(feedback_items)}</ul></div>"
        
        if not any([concerns_html, complexity_html, recommendations_html, feedback_html]):
            return "<p>Technical concerns analysis not available</p>"
        
        return f"{concerns_html}{complexity_html}{recommendations_html}{feedback_html}"
    
    def _generate_solution_quality_content(self, pr: 'PRSummary') -> str:
        """Generate HTML content for Solution Quality modal card"""
        scope_html = ""
        if pr.scope_analysis:
            scope_html = f"<div class='modal-section'><h4>Scope Analysis:</h4><p>{html.escape(pr.scope_analysis)}</p></div>"
        
        architecture_html = ""
        if pr.architecture_impact:
            arch_items = [f"<li>{html.escape(arch)}</li>" for arch in pr.architecture_impact]
            architecture_html = f"<div class='modal-section'><h4>Architecture Impact:</h4><ul>{''.join(arch_items)}</ul></div>"
        
        implementation_html = ""
        if pr.implementation_quality:
            impl_items = [f"<li>{html.escape(impl)}</li>" for impl in pr.implementation_quality]
            implementation_html = f"<div class='modal-section'><h4>Implementation Quality:</h4><ul>{''.join(impl_items)}</ul></div>"
        
        testing_html = ""
        if pr.testing_adequacy:
            test_items = [f"<li>{html.escape(test)}</li>" for test in pr.testing_adequacy]
            testing_html = f"<div class='modal-section'><h4>Testing Adequacy:</h4><ul>{''.join(test_items)}</ul></div>"
        
        fitness_html = ""
        if pr.solution_fitness:
            fitness_html = f"<div class='modal-section'><h4>Solution Fitness:</h4><p>{html.escape(pr.solution_fitness)}</p></div>"
        
        if not any([scope_html, architecture_html, implementation_html, testing_html, fitness_html]):
            return "<p>Solution quality analysis not available</p>"
        
        return f"{scope_html}{architecture_html}{implementation_html}{testing_html}{fitness_html}"
    
    def _generate_backport_button(self, pr: 'PRSummary') -> str:
        """Generate backport preparation button for approved PRs"""
        if pr.backport_decision != 'APPROVE':
            return ""  # Only show button for approved PRs
        
        return f"""
                <button class="btn btn-backport" onclick="openBackportModal({pr.number}, '{pr.actual_branch}')">
                    🔄 Prepare Backport
                </button>
        """
    
    def _load_commit_message(self, pr_number: str) -> str:
        """Load the AI-generated commit message for a PR"""
        # Check run-specific logs first, then fallback to main logs directory
        commit_file_paths = [
            self.run_dir / "logs" / f"claude-response-commit-message-{pr_number}.txt",
            Path("logs") / f"claude-response-commit-message-{pr_number}.txt"
        ]
        
        for commit_file in commit_file_paths:
            if commit_file.exists():
                try:
                    with open(commit_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract commit message from Claude response
                    # Look for the actual commit message after "Response:" line
                    lines = content.split('\n')
                    commit_lines = []
                    in_commit = False
                    
                    for line in lines:
                        if line.startswith('Response:'):
                            in_commit = True
                            continue
                        elif in_commit and line.strip():
                            # Skip the descriptive text before the actual commit
                            if not any(skip_phrase in line for skip_phrase in [
                                "Based on", "I'll generate", "Here's", "The commit message"
                            ]):
                                commit_lines.append(line)
                    
                    if commit_lines:
                        # Join lines and clean up
                        commit_message = '\n'.join(commit_lines).strip()
                        return commit_message
                        
                except Exception as e:
                    print(f"⚠️  Error loading commit message for PR #{pr_number}: {e}")
        
        return f"Commit message not available for PR #{pr_number}"
    
    def _generate_file_list(self, file_changes: List[Dict[str, Any]]) -> str:
        """Generate a formatted list of file changes"""
        if not file_changes:
            return "<li>No file information available</li>"
        
        file_items = []
        for file_change in file_changes[:10]:  # Limit to first 10 files
            filename = file_change.get('filename', 'Unknown file')
            status = file_change.get('status', 'modified')
            additions = file_change.get('additions', 0)
            deletions = file_change.get('deletions', 0)
            
            # Status icon
            status_icon = {
                'added': '➕',
                'modified': '📝',
                'removed': '🗑️',
                'renamed': '📂'
            }.get(status, '📝')
            
            # Build file item
            file_items.append(f"""
                <li class="file-item">
                    <span class="file-status">{status_icon}</span>
                    <span class="file-name">{html.escape(filename)}</span>
                    <span class="file-changes">+{additions}/-{deletions}</span>
                </li>
            """)
        
        if len(file_changes) > 10:
            file_items.append(f"<li class='file-more'>... and {len(file_changes) - 10} more files</li>")
        
        return ''.join(file_items)
    
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
    
    def _process_backport_data(self, backport_data: Dict) -> Dict[str, str]:
        """Process backport assessment data into display format"""
        if not backport_data:
            return {
                "eligible": False,
                "decision": "UNKNOWN",
                "classification": "Assessment Missing",
                "risk_level": "Unknown",
                "reasoning": "Backport assessment not available",
                "recommendations": "",
                "badge_color": "unknown",
                "icon": "❓"
            }
        
        decision = backport_data.get("decision", "UNKNOWN").upper()
        classification = backport_data.get("classification", "Unknown")
        risk_level = backport_data.get("risk_level", "Unknown")
        reasoning = backport_data.get("reasoning", "No reasoning provided")
        recommendations = backport_data.get("recommendations", "")
        
        # Determine badge color and icon based on decision
        if decision == "APPROVE":
            badge_color = "approve"
            icon = "✅"
            eligible = True
        elif decision == "REJECT":
            badge_color = "reject"
            icon = "❌"
            eligible = False
        else:
            badge_color = "unknown"
            icon = "❓"
            eligible = False
        
        # Keep full reasoning for tooltips
        # Truncation was causing tooltip display issues
        # if len(reasoning) > 100:
        #     reasoning = reasoning[:97] + "..."
        
        return {
            "eligible": eligible,
            "decision": decision,
            "classification": classification,
            "risk_level": risk_level,
            "reasoning": reasoning,
            "recommendations": recommendations,
            "badge_color": badge_color,
            "icon": icon
        }
    
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
        
        # Create backport-specific categories
        backport_categories = {
            "backport-ready": [pr for pr in self.pr_summaries if pr.backport_eligible],
            "not-suitable": [pr for pr in self.pr_summaries if pr.backport_decision == "REJECT"],
            "assessment-missing": [pr for pr in self.pr_summaries if pr.backport_decision == "UNKNOWN"]
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
        {self._generate_backport_section(backport_categories)}
        {self._generate_orchard_sections(categories)}
    </div>
    {self._generate_modal_html()}
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
        backport_ready = len([pr for pr in self.pr_summaries if pr.backport_eligible])
        
        return f"""
        <section class="summary-stats">
            <div class="stat-card backport-ready" data-filter="backport-ready" onclick="filterPRsByType('backport-ready')">
                <div class="stat-icon">📦</div>
                <div class="stat-content">
                    <div class="stat-number">{backport_ready}</div>
                    <div class="stat-label">Backport Ready</div>
                </div>
            </div>
            <div class="stat-card low-hanging" data-filter="ready-harvest" onclick="filterPRsByType('ready-harvest')">
                <div class="stat-icon">🍎</div>
                <div class="stat-content">
                    <div class="stat-number">{easy_harvest}</div>
                    <div class="stat-label">Ready to Harvest</div>
                </div>
            </div>
            <div class="stat-card low-risk" data-filter="low-risk" onclick="filterPRsByType('low-risk')">
                <div class="stat-icon">✅</div>
                <div class="stat-content">
                    <div class="stat-number">{low_risk}</div>
                    <div class="stat-label">Low Risk PRs</div>
                </div>
            </div>
            <div class="stat-card total" data-filter="all" onclick="filterPRsByType('all')">
                <div class="stat-icon">📊</div>
                <div class="stat-content">
                    <div class="stat-number">{total}</div>
                    <div class="stat-label">Total PRs</div>
                </div>
            </div>
        </section>
        """
    
    def _generate_backport_section(self, backport_categories: Dict[str, List[PRSummary]]) -> str:
        """Generate dedicated backport candidate section"""
        backport_ready = backport_categories["backport-ready"]
        
        if not backport_ready:
            return f"""
            <section class="backport-section">
                <div class="section-header">
                    <h2>📦 Spring AI 1.0.x Backport Candidates</h2>
                    <p class="section-description">No PRs currently approved for backporting</p>
                </div>
            </section>
            """
        
        # Sort backport-ready PRs by classification and risk
        backport_ready.sort(key=lambda pr: (pr.backport_classification, pr.backport_risk_level, pr.effort_score))
        
        return f"""
        <section class="backport-section">
            <div class="section-header">
                <h2>📦 Spring AI 1.0.x Backport Candidates</h2>
                <p class="section-description">
                    {len(backport_ready)} PR(s) approved for backporting to the maintenance branch
                </p>
            </div>
            <div class="backport-grid">
                {self._generate_pr_cards(backport_ready)}
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
        <div class="pr-card" data-pr-number="{pr.number}" data-risk="{pr.risk_level.lower()}" data-type="{pr.pr_type}" data-backport="{pr.backport_badge_color}">
            <div class="pr-header">
                <div class="pr-icon">{pr.fruit_icon}</div>
                <div class="pr-title-section">
                    <h3 class="pr-title">
                        <a href="{pr.url}" target="_blank" class="pr-link">
                            #{pr.number}: {title}
                        </a>
                    </h3>
                    <div class="pr-meta">
                        <span class="pr-author">by <a href="https://github.com/spring-projects/spring-ai/pulls?q=author:{author}" target="_blank" class="author-link">{author}</a></span>
                        <span class="badge-group">
                            <span class="badge-label">Type:</span>
                            <span class="pr-type" title="{self._get_pr_type_tooltip(pr.pr_type)}">{pr.pr_type}</span>
                        </span>
                        <span class="badge-group">
                            <span class="badge-label">Risk:</span>
                            <span class="risk-badge risk-{pr.risk_level.lower()}" title="{self._get_risk_tooltip(pr.risk_level)}">{pr.risk_level}</span>
                        </span>
                        <span class="badge-group">
                            <span class="badge-label">Backport:</span>
                            <span class="backport-badge backport-{pr.backport_badge_color}" title="{self._get_backport_tooltip(pr.backport_decision)}">
                                {pr.backport_icon} {pr.backport_decision}
                            </span>
                        </span>
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
                <div class="assessment-section">
                    <h4 class="assessment-label">💡 Problem Summary</h4>
                    <p class="problem-summary">{html.escape(pr.problem_summary) if pr.problem_summary else 'Analysis not available'}</p>
                    {self._generate_key_requirements_list(pr.key_requirements)}
                </div>
            </div>
            
            <div class="pr-actions">
                <a href="{pr.url}" target="_blank" class="btn btn-primary">View on GitHub</a>
                <a href="{pr.url}/files" target="_blank" class="btn btn-secondary">View Files</a>
                <button class="btn btn-details modal-details-btn" onclick="openAssessmentModal({pr.number})">
                    🔍 View Assessments
                </button>
                {self._generate_backport_button(pr)}
            </div>
            
            <!-- Hidden assessment data for modal population -->
            <div class="assessment-data" style="display: none;" data-pr="{pr.number}">
                <div class="problem-analysis-data">
                    {self._generate_problem_analysis_content(pr)}
                </div>
                
                <div class="backport-assessment-data">
                    {self._generate_backport_assessment_content(pr)}
                </div>
                
                <div class="technical-concerns-data">
                    {self._generate_technical_concerns_content(pr)}
                </div>
                
                <div class="solution-quality-data">
                    {self._generate_solution_quality_content(pr)}
                </div>
                
                <div class="commit-message-data">
                    <div class="commit-message-text">{html.escape(pr.commit_message)}</div>
                </div>
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
    
    def _generate_modal_html(self) -> str:
        """Generate modal HTML structure for detailed assessment view"""
        return """
        <!-- Assessment Details Modal -->
        <div id="assessment-modal" class="modal-overlay" style="display: none;">
            <div class="modal-container">
                <div class="modal-header">
                    <h2 id="modal-pr-title">PR Assessment Details</h2>
                    <button class="modal-close" onclick="closeAssessmentModal()">×</button>
                </div>
                <div class="modal-content">
                    <div class="modal-assessment-layout">
                        <div class="modal-top-row">
                            <div class="modal-assessment-card modal-problem-card">
                                <h3>🔍 Problem Analysis</h3>
                                <div id="modal-problem-content">
                                    <!-- Problem analysis content will be populated by JavaScript -->
                                </div>
                            </div>
                            <div class="modal-assessment-card modal-backport-card">
                                <h3>🔄 Backport Assessment</h3>
                                <div id="modal-backport-content">
                                    <!-- Backport content will be populated by JavaScript -->
                                </div>
                            </div>
                        </div>
                        <div class="modal-middle-row">
                            <div class="modal-assessment-card modal-concerns-card">
                                <h3>⚠️ Technical Concerns</h3>
                                <div id="modal-concerns-content">
                                    <!-- Technical concerns content will be populated by JavaScript -->
                                </div>
                            </div>
                            <div class="modal-assessment-card modal-solution-card">
                                <h3>🏗️ Solution Quality</h3>
                                <div id="modal-solution-content">
                                    <!-- Solution quality content will be populated by JavaScript -->
                                </div>
                            </div>
                        </div>
                        <div class="modal-bottom-row">
                            <div class="modal-assessment-card modal-commit-card">
                                <h3>📝 Final Commit Message</h3>
                                <div id="modal-commit-content">
                                    <!-- Commit message content will be populated by JavaScript -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Backport Command Modal -->
        <div id="backport-modal" class="modal-overlay" style="display: none;">
            <div class="modal-content backport-modal-content">
                <div class="modal-header">
                    <h2>🔄 Backport Command Ready</h2>
                    <button class="modal-close" onclick="closeBackportModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="backport-info">
                        <div class="branch-info">
                            <strong>Branch:</strong> <span id="backport-branch"></span>
                        </div>
                        <div class="status-info">
                            <strong>Status:</strong> <span class="status-approved">✅ APPROVED for backport</span>
                        </div>
                    </div>
                    
                    <div class="command-section">
                        <h3>📋 Command to run (click to copy):</h3>
                        <div class="command-box" id="backport-command" onclick="copyBackportCommand()">
                            <code id="backport-command-text"></code>
                        </div>
                        <div class="copy-feedback" id="copy-feedback" style="display: none;">
                            ✅ Copied to clipboard!
                        </div>
                    </div>
                    
                    <div class="safety-warnings">
                        <div class="warning-item">
                            <span class="warning-icon">⚠️</span>
                            <span>Make sure you're in: <strong>spring-ai</strong> directory</span>
                        </div>
                        <div class="warning-item">
                            <span class="warning-icon">⚠️</span>
                            <span>Make sure you're on: <strong id="warning-branch"></strong> branch</span>
                        </div>
                    </div>
                    
                    <div class="modal-actions">
                        <button class="btn btn-primary" onclick="copyBackportCommand()">📋 Copy Command</button>
                        <button class="btn btn-secondary" onclick="closeBackportModal()">Close</button>
                    </div>
                </div>
            </div>
        </div>
        """
    
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
            cursor: pointer;
            user-select: none;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 30px var(--shadow-medium);
        }
        
        .stat-card.active {
            transform: translateY(-8px);
            box-shadow: 0 12px 40px var(--shadow-medium);
            border-left-width: 8px;
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
        
        .stat-card.backport-ready {
            border-left-color: #17a2b8;
            background: linear-gradient(135deg, #fff 0%, #e6f8fb 100%);
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
        
        .section-description {
            margin: 0;
            color: #666;
            font-size: 1.1rem;
        }
        
        /* === BACKPORT SECTION === */
        .backport-section {
            margin-bottom: 50px;
            padding: 30px;
            background: linear-gradient(135deg, #e6f8fb 0%, #b3e5fc 100%);
            border-radius: 20px;
            border: 2px solid #17a2b8;
            box-shadow: 0 8px 32px rgba(23, 162, 184, 0.2);
        }
        
        .backport-section .section-header {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-left: 5px solid #17a2b8;
        }
        
        .backport-section .section-header h2 {
            color: #17a2b8;
        }
        
        .backport-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
            gap: 25px;
        }
        
        /* === PR GRID === */
        .pr-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
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
            gap: 15px;
            align-items: center;
            font-size: 0.9rem;
        }
        
        .badge-group {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .badge-label {
            font-size: 0.8rem;
            color: #6c757d;
            font-weight: 500;
        }
        
        .assessment-section {
            margin-bottom: 15px;
        }
        
        .assessment-label {
            margin: 0 0 8px 0;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--orchard-green);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .problem-summary {
            margin: 0 0 12px 0;
            line-height: 1.5;
            color: #24292f;
        }
        
        .key-requirements {
            margin: 8px 0 0 0;
            padding-left: 20px;
            list-style-type: disc;
        }
        
        .key-requirements li {
            margin: 4px 0;
            line-height: 1.4;
            color: #656d76;
        }
        
        .requirements-more {
            font-style: italic;
            color: #8b949e !important;
        }
        
        .pr-author {
            color: #666;
            font-weight: 500;
        }
        
        .author-link {
            color: #0969da;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s ease;
        }
        
        .author-link:hover {
            color: #0550ae;
            text-decoration: underline;
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
        
        /* === BACKPORT BADGES === */
        .backport-badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-left: 8px;
            cursor: help;
        }
        
        .backport-approve {
            background: #d1f2eb;
            color: #0c5460;
            border: 1px solid #7bdcb5;
        }
        
        .backport-reject {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .backport-unknown {
            background: #e2e3e5;
            color: #495057;
            border: 1px solid #d6d8db;
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
        
        /* === BACKPORT INFO === */
        .backport-info {
            margin-bottom: 20px;
            padding: 15px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            border-left: 4px solid #6c757d;
        }
        
        .backport-info .backport-classification {
            margin-bottom: 8px;
            font-size: 0.9rem;
        }
        
        .backport-info .backport-risk {
            font-weight: 600;
            color: #495057;
        }
        
        .backport-info .backport-reasoning {
            font-size: 0.85rem;
            color: #6c757d;
            line-height: 1.4;
            font-style: italic;
        }
        
        /* Update backport-info based on approval status */
        .pr-card[data-backport="approve"] .backport-info {
            border-left-color: #28a745;
            background: linear-gradient(135deg, #d1f2eb 0%, #a3e4d7 100%);
        }
        
        .pr-card[data-backport="reject"] .backport-info {
            border-left-color: #dc3545;
            background: linear-gradient(135deg, #f8d7da 0%, #f1aeb5 100%);
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
        
        .btn-details {
            background: var(--earth-tan);
            color: var(--orchard-green);
            border: 2px solid var(--orchard-green);
        }
        
        .btn-details:hover {
            background: var(--orchard-green);
            color: white;
            transform: translateY(-2px);
        }
        
        .modal-details-btn {
            background: var(--leaf-green);
            color: white;
            border: 2px solid var(--leaf-green);
        }
        
        .modal-details-btn:hover {
            background: var(--orchard-green);
            border-color: var(--orchard-green);
            color: white;
            transform: translateY(-2px);
        }
        
        .btn-backport {
            background: #ff6b35;
            color: white;
            border: 2px solid #ff6b35;
            font-weight: 600;
        }
        
        .btn-backport:hover {
            background: #e55a30;
            border-color: #e55a30;
            color: white;
            transform: translateY(-2px);
        }
        
        /* === EXPANDABLE DETAILS === */
        .pr-details-expandable {
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            animation: slideDownFade 0.3s ease-out;
        }
        
        @keyframes slideDownFade {
            from {
                opacity: 0;
                max-height: 0;
                padding-top: 0;
                padding-bottom: 0;
            }
            to {
                opacity: 1;
                max-height: 500px;
                padding-top: 15px;
                padding-bottom: 15px;
            }
        }
        
        .file-changes-summary h4 {
            color: var(--orchard-green);
            margin: 15px 0 10px 0;
            font-size: 1rem;
        }
        
        .file-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            margin: 5px 0;
            background: white;
            border-radius: 5px;
            border-left: 3px solid var(--leaf-green);
        }
        
        .file-status {
            font-size: 1.1rem;
            margin-right: 8px;
        }
        
        .file-name {
            flex: 1;
            font-family: 'SF Mono', 'Monaco', monospace;
            font-size: 0.85rem;
            color: var(--orchard-green);
        }
        
        .file-changes {
            font-size: 0.8rem;
            color: #666;
            font-weight: 500;
        }
        
        .file-more {
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 10px;
        }
        
        /* === RESPONSIVE DESIGN === */
        
        /* Large screens: 2 cards per row for better readability */
        @media (min-width: 1200px) {
            .pr-grid, .backport-grid {
                grid-template-columns: repeat(2, 1fr);
                max-width: 1200px;
                margin: 0 auto;
            }
        }
        
        /* Medium screens: maintain flexible layout */
        @media (min-width: 769px) and (max-width: 1199px) {
            .pr-grid, .backport-grid {
                grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
            }
        }
        
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
            
            .pr-grid, .backport-grid {
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
        
        /* === ASSESSMENT CARDS === */
        .assessment-card {
            margin: 20px 0;
            background: white;
            border-radius: 12px;
            border: 1px solid #e9ecef;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }
        
        .assessment-title {
            background: linear-gradient(135deg, var(--orchard-green), var(--leaf-green));
            color: white;
            margin: 0;
            padding: 12px 16px;
            font-size: 1rem;
            font-weight: 600;
        }
        
        .assessment-content {
            padding: 16px;
        }
        
        .risk-level-display, .backport-decision-display {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }
        
        .risk-explanation, .backport-classification {
            font-size: 0.9rem;
            color: #666;
            font-weight: 500;
        }
        
        .risk-details, .backport-details {
            line-height: 1.6;
        }
        
        .commit-message-content {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
        }
        
        .commit-message {
            margin: 0;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
            font-size: 0.9rem;
            line-height: 1.5;
            white-space: pre-wrap;
            color: var(--orchard-green);
        }
        
        .commit-actions {
            display: flex;
            justify-content: flex-end;
        }
        
        .btn-copy {
            background: var(--earth-tan);
            color: var(--orchard-green);
            border: 2px solid var(--orchard-green);
            padding: 8px 16px;
            font-size: 0.85rem;
        }
        
        .btn-copy:hover {
            background: var(--orchard-green);
            color: white;
        }
        
        /* === EXPANDABLE DETAILS === */
        .pr-details {
            margin-top: 20px;
            border-top: 1px solid #e1e5e9;
            padding-top: 20px;
        }
        
        /* === ASSESSMENT CARDS === */
        .assessment-cards-container {
            display: flex;
            flex-direction: column;
            gap: 16px;
            margin-top: 16px;
        }
        
        .assessment-card {
            background: #fafbfc;
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 16px;
            transition: all 0.2s ease;
        }
        
        .assessment-card:hover {
            border-color: #d0d7de;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .assessment-title {
            margin: 0 0 12px 0;
            font-size: 1rem;
            font-weight: 600;
            color: #24292f;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .assessment-content {
            color: #656d76;
            line-height: 1.5;
        }
        
        /* Risk Assessment Card */
        .risk-assessment-card {
            border-left: 4px solid var(--risk-color);
        }
        
        .risk-level-display {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }
        
        .risk-explanation {
            font-size: 0.9rem;
            color: #656d76;
        }
        
        .risk-summary {
            margin: 0 0 12px 0;
            font-weight: 500;
            color: #24292f;
        }
        
        .risk-details ul {
            margin: 8px 0;
            padding-left: 20px;
        }
        
        .risk-details li {
            margin: 4px 0;
        }
        
        /* Backport Assessment Card */
        .backport-assessment-card {
            border-left: 4px solid #0969da;
        }
        
        .backport-decision {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 12px;
        }
        
        .backport-decision.approve {
            background: #dcfce7;
            color: #166534;
        }
        
        .backport-decision.reject {
            background: #fee2e2;
            color: #dc2626;
        }
        
        .backport-reasoning {
            margin: 12px 0;
            font-style: italic;
            color: #656d76;
        }
        
        .backport-recommendations {
            margin-top: 12px;
            padding: 12px;
            background: #f6f8fa;
            border-radius: 6px;
            border-left: 3px solid #0969da;
        }
        
        /* Commit Message Card */
        .commit-message-card {
            border-left: 4px solid #8b5cf6;
        }
        
        .commit-message-content {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 20px;
            font-family: 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9rem;
            line-height: 1.6;
            white-space: pre-wrap;
            color: #334155;
            position: relative;
            min-height: 120px;
        }
        
        .copy-button {
            position: absolute;
            top: 8px;
            right: 8px;
            background: #0969da;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 0.75rem;
            cursor: pointer;
            transition: background-color 0.2s ease;
        }
        
        .copy-button:hover {
            background: #0550ae;
        }
        
        .copy-button:active {
            background: #033d8b;
        }
        
        /* === MODAL STYLES === */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(4px);
        }
        
        .modal-container {
            background: white;
            border-radius: 12px;
            width: 95%;
            max-width: 1200px;
            max-height: 90vh;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            animation: modalSlideIn 0.3s ease-out;
        }
        
        @keyframes modalSlideIn {
            from {
                opacity: 0;
                transform: translateY(-50px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 30px;
            border-bottom: 1px solid #e1e5e9;
            background: #f8f9fa;
        }
        
        .modal-header h2 {
            margin: 0;
            color: var(--orchard-green);
            font-size: 1.5rem;
        }
        
        .modal-close {
            background: none;
            border: none;
            font-size: 2rem;
            color: #6c757d;
            cursor: pointer;
            padding: 0;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: all 0.2s ease;
        }
        
        .modal-close:hover {
            background: #e9ecef;
            color: #495057;
        }
        
        .modal-content {
            padding: 30px;
            overflow-y: auto;
            max-height: calc(90vh - 100px);
        }
        
        .modal-assessment-layout {
            display: flex;
            flex-direction: column;
            gap: 30px;
        }
        
        .modal-top-row, .modal-middle-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        
        .modal-bottom-row {
            display: flex;
            width: 100%;
        }
        
        .modal-assessment-card {
            background: #fafbfc;
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 24px;
            min-height: 300px;
        }
        
        .modal-assessment-card h3 {
            margin: 0 0 20px 0;
            color: #24292f;
            font-size: 1.2rem;
            border-bottom: 2px solid #e1e5e9;
            padding-bottom: 12px;
        }
        
        .modal-problem-card {
            border-left: 4px solid #0969da;
        }
        
        .modal-backport-card {
            border-left: 4px solid #28a745;
        }
        
        .modal-concerns-card {
            border-left: 4px solid #ffc107;
        }
        
        .modal-solution-card {
            border-left: 4px solid #6f42c1;
        }
        
        .modal-commit-card {
            border-left: 4px solid #fd7e14;
        }
        
        .modal-commit-card .commit-message-text {
            font-family: 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 1rem;
            line-height: 1.7;
            white-space: pre-wrap;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 24px;
            min-height: 200px;
            color: #334155;
        }
        
        .modal-section {
            margin-bottom: 20px;
        }
        
        .modal-section h4 {
            margin: 0 0 8px 0;
            color: #24292f;
            font-size: 0.95rem;
            font-weight: 600;
        }
        
        .modal-section p {
            margin: 0 0 8px 0;
            line-height: 1.5;
            color: #656d76;
        }
        
        .modal-section ul {
            margin: 0 0 8px 0;
            padding-left: 20px;
        }
        
        .modal-section li {
            margin: 4px 0;
            line-height: 1.4;
            color: #656d76;
        }
        
        /* Responsive modal */
        @media (max-width: 1024px) {
            .modal-top-row, .modal-middle-row {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .modal-assessment-layout {
                gap: 20px;
            }
            
            .modal-container {
                width: 98%;
                margin: 10px;
            }
            
            .modal-content {
                padding: 20px;
            }
        }
        
        @media (max-width: 768px) {
            .modal-header {
                padding: 15px 20px;
            }
            
            .modal-header h2 {
                font-size: 1.2rem;
            }
            
            .modal-content {
                padding: 15px;
            }
        }
        
        /* === BACKPORT MODAL STYLES === */
        .backport-modal-content {
            max-width: 700px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .backport-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #ff6b35;
        }
        
        .branch-info, .status-info {
            margin-bottom: 8px;
        }
        
        .status-approved {
            color: #28a745;
            font-weight: 600;
        }
        
        .command-section {
            margin-bottom: 20px;
        }
        
        .command-section h3 {
            color: #333;
            margin-bottom: 10px;
            font-size: 16px;
        }
        
        .command-box {
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            cursor: pointer;
            border: 2px solid #4a5568;
            transition: all 0.2s ease;
            white-space: pre-wrap;
            word-break: break-all;
        }
        
        .command-box:hover {
            border-color: #ff6b35;
            background: #3a4553;
        }
        
        .command-box code {
            color: #e2e8f0;
            background: none;
            padding: 0;
            font-size: 13px;
            line-height: 1.4;
        }
        
        .copy-feedback {
            margin-top: 8px;
            color: #28a745;
            font-weight: 600;
            text-align: center;
        }
        
        .safety-warnings {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .warning-item {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .warning-item:last-child {
            margin-bottom: 0;
        }
        
        .warning-icon {
            margin-right: 8px;
            font-size: 16px;
        }
        
        .modal-actions {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 20px;
        }
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
            
            // Tooltips removed - using expandable assessment cards
            
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
        
        // PR Filtering functionality
        function filterPRsByType(filterType) {
            console.log(`🔍 Filtering PRs by type: ${filterType}`);
            
            // Update active stat card
            document.querySelectorAll('.stat-card').forEach(card => {
                card.classList.remove('active');
            });
            document.querySelector(`[data-filter="${filterType}"]`).classList.add('active');
            
            // Show/hide sections based on filter
            const backportSection = document.querySelector('.backport-section');
            const orchardSections = document.querySelectorAll('.orchard-section');
            
            if (filterType === 'all') {
                // Show all sections
                if (backportSection) backportSection.style.display = 'block';
                orchardSections.forEach(section => section.style.display = 'block');
            } else if (filterType === 'backport-ready') {
                // Show only backport section
                if (backportSection) backportSection.style.display = 'block';
                orchardSections.forEach(section => section.style.display = 'none');
            } else if (filterType === 'ready-harvest') {
                // Show only ready-harvest section
                if (backportSection) backportSection.style.display = 'none';
                orchardSections.forEach(section => {
                    if (section.classList.contains('ready-harvest')) {
                        section.style.display = 'block';
                    } else {
                        section.style.display = 'none';
                    }
                });
            } else if (filterType === 'low-risk') {
                // Show sections and filter PR cards by risk level
                if (backportSection) backportSection.style.display = 'none';
                orchardSections.forEach(section => {
                    section.style.display = 'block';
                    // Hide PR cards that aren't low risk
                    const prCards = section.querySelectorAll('.pr-card');
                    prCards.forEach(card => {
                        if (card.getAttribute('data-risk') === 'low') {
                            card.style.display = 'block';
                        } else {
                            card.style.display = 'none';
                        }
                    });
                });
            }
            
            // Smooth scroll to first visible section
            setTimeout(() => {
                const firstVisibleSection = document.querySelector('.backport-section[style*="block"], .orchard-section[style*="block"]');
                if (firstVisibleSection) {
                    firstVisibleSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
        }
        
        // Initialize with 'all' filter active
        document.addEventListener('DOMContentLoaded', function() {
            // Set 'Total PRs' as initially active
            document.querySelector('[data-filter="all"]').classList.add('active');
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
        
        // Custom tooltip functionality
        function initializeCustomTooltips() {
            // Remove any existing tooltips first
            document.querySelectorAll('.custom-tooltip').forEach(tooltip => tooltip.remove());
            
            // Find all elements with data-tooltip attribute
            const tooltipElements = document.querySelectorAll('[data-tooltip]');
            
            if (tooltipElements.length === 0) {
                return;
            }
            
            tooltipElements.forEach(element => {
                element.addEventListener('mouseenter', function(e) {
                    showTooltip(e.target, e.target.getAttribute('data-tooltip'));
                });
                
                element.addEventListener('mouseleave', function() {
                    hideTooltip();
                });
                
                // Handle keyboard accessibility
                element.addEventListener('focus', function(e) {
                    showTooltip(e.target, e.target.getAttribute('data-tooltip'));
                });
                
                element.addEventListener('blur', function() {
                    hideTooltip();
                });
            });
        }

        function showTooltip(element, content) {
            if (!content) {
                return;
            }
            
            // Remove any existing tooltip
            hideTooltip();
            
            // Create tooltip element
            const tooltip = document.createElement('div');
            tooltip.className = 'custom-tooltip';
            tooltip.textContent = content;
            
            // Add to document
            document.body.appendChild(tooltip);
            
            // Position tooltip
            positionTooltip(element, tooltip);
            
            // Show with animation
            requestAnimationFrame(() => {
                tooltip.classList.add('show');
            });
        }

        function hideTooltip() {
            const existingTooltip = document.querySelector('.custom-tooltip');
            if (existingTooltip) {
                existingTooltip.classList.remove('show');
                setTimeout(() => {
                    if (existingTooltip.parentNode) {
                        existingTooltip.parentNode.removeChild(existingTooltip);
                    }
                }, 200); // Match the CSS transition duration
            }
        }

        function positionTooltip(element, tooltip) {
            const elementRect = element.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            
            // Default position: above the element, centered
            let left = elementRect.left + (elementRect.width / 2) - (tooltipRect.width / 2);
            let top = elementRect.top - tooltipRect.height - 10;
            
            // Adjust horizontal position if tooltip would go off-screen
            if (left < 10) {
                left = 10; // Left edge padding
            } else if (left + tooltipRect.width > viewportWidth - 10) {
                left = viewportWidth - tooltipRect.width - 10; // Right edge padding
            }
            
            // If tooltip would go above viewport, position it below the element
            if (top < 10) {
                top = elementRect.bottom + 10;
                tooltip.classList.add('tooltip-below');
            } else {
                tooltip.classList.remove('tooltip-below');
            }
            
            // Final position
            tooltip.style.left = left + 'px';
            tooltip.style.top = top + 'px';
        }
        
        // Toggle PR details expansion
        function togglePRDetails(button) {
            const card = button.closest('.pr-card');
            const detailsSection = card.querySelector('.pr-details-expandable');
            
            if (detailsSection.style.display === 'none' || detailsSection.style.display === '') {
                // Show details
                detailsSection.style.display = 'block';
                button.innerHTML = '📋 Hide Details';
                button.style.background = 'var(--orchard-green)';
                button.style.color = 'white';
                
                // Smooth scroll to show the expanded content
                setTimeout(() => {
                    detailsSection.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'nearest'
                    });
                }, 100);
            } else {
                // Hide details
                detailsSection.style.display = 'none';
                button.innerHTML = '📋 Show Details';
                button.style.background = 'var(--earth-tan)';
                button.style.color = 'var(--orchard-green)';
            }
        }
        
        // Copy commit message functionality
        function copyCommitMessage(prNumber) {
            const commitContent = document.querySelector(`#commit-message-${prNumber}`);
            if (!commitContent) {
                console.error(`Commit message element not found for PR ${prNumber}`);
                return;
            }
            
            const text = commitContent.textContent.trim();
            
            // Use modern clipboard API if available
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(() => {
                    showCopySuccess(prNumber);
                }).catch(err => {
                    console.error('Failed to copy commit message:', err);
                    fallbackCopyTextToClipboard(text, prNumber);
                });
            } else {
                // Fallback for older browsers
                fallbackCopyTextToClipboard(text, prNumber);
            }
        }
        
        function fallbackCopyTextToClipboard(text, prNumber) {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            
            // Avoid scrolling to bottom
            textArea.style.top = "0";
            textArea.style.left = "0";
            textArea.style.position = "fixed";
            textArea.style.opacity = "0";
            
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    showCopySuccess(prNumber);
                } else {
                    console.error('Fallback copy command failed');
                }
            } catch (err) {
                console.error('Fallback copy failed:', err);
            }
            
            document.body.removeChild(textArea);
        }
        
        function showCopySuccess(prNumber) {
            const button = document.querySelector(`button[onclick="copyCommitMessage(${prNumber})"]`);
            if (button) {
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                button.style.background = '#10b981';
                
                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.background = '#0969da';
                }, 2000);
            }
        }
        
        // Modal functionality for assessment details
        function openAssessmentModal(prNumber) {
            const assessmentData = document.querySelector(`[data-pr="${prNumber}"]`);
            if (!assessmentData) {
                console.error(`Assessment data not found for PR ${prNumber}`);
                return;
            }
            
            // Get PR title from the main card
            const prCard = document.querySelector(`[data-pr-number="${prNumber}"]`);
            const prTitle = prCard ? prCard.querySelector('.pr-title a').textContent : `PR #${prNumber}`;
            
            // Update modal title
            document.getElementById('modal-pr-title').textContent = prTitle;
            
            // Get assessment content from hidden data sections
            const problemData = assessmentData.querySelector('.problem-analysis-data');
            const backportData = assessmentData.querySelector('.backport-assessment-data');
            const concernsData = assessmentData.querySelector('.technical-concerns-data');
            const solutionData = assessmentData.querySelector('.solution-quality-data');
            const commitData = assessmentData.querySelector('.commit-message-data');
            
            // Populate modal content
            if (problemData) {
                document.getElementById('modal-problem-content').innerHTML = problemData.innerHTML;
            }
            if (backportData) {
                document.getElementById('modal-backport-content').innerHTML = backportData.innerHTML;
            }
            if (concernsData) {
                document.getElementById('modal-concerns-content').innerHTML = concernsData.innerHTML;
            }
            if (solutionData) {
                document.getElementById('modal-solution-content').innerHTML = solutionData.innerHTML;
            }
            if (commitData) {
                const commitText = commitData.querySelector('.commit-message-text');
                if (commitText) {
                    document.getElementById('modal-commit-content').innerHTML = 
                        `<div class="commit-message-text">${commitText.textContent}</div>`;
                }
            }
            
            // Show modal
            const modal = document.getElementById('assessment-modal');
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
            
            // Focus trap for accessibility
            modal.focus();
        }
        
        function closeAssessmentModal() {
            const modal = document.getElementById('assessment-modal');
            modal.style.display = 'none';
            document.body.style.overflow = ''; // Restore scrolling
        }
        
        // ESC key support for modal
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const modal = document.getElementById('assessment-modal');
                if (modal.style.display === 'flex') {
                    closeAssessmentModal();
                }
            }
        });
        
        // Click outside modal to close
        document.addEventListener('click', function(e) {
            const modal = document.getElementById('assessment-modal');
            if (e.target === modal) {
                closeAssessmentModal();
            }
        });
        
        // === BACKPORT MODAL FUNCTIONS ===
        function openBackportModal(prNumber, actualBranch) {
            const modal = document.getElementById('backport-modal');
            const branchName = actualBranch || `pr-${prNumber}-branch`;  // Use actual branch or fallback
            const command = `cd spring-ai && git checkout ${branchName} && python3 ../prepare_backport.py ${prNumber}`;
            
            // Populate modal content
            document.getElementById('backport-branch').textContent = branchName;
            document.getElementById('backport-command-text').textContent = command;
            document.getElementById('warning-branch').textContent = branchName;
            
            // Show modal
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        }
        
        function closeBackportModal() {
            const modal = document.getElementById('backport-modal');
            modal.style.display = 'none';
            document.body.style.overflow = ''; // Restore scrolling
            
            // Hide copy feedback
            document.getElementById('copy-feedback').style.display = 'none';
        }
        
        function copyBackportCommand() {
            const commandText = document.getElementById('backport-command-text').textContent;
            const feedback = document.getElementById('copy-feedback');
            
            // Copy to clipboard
            navigator.clipboard.writeText(commandText).then(function() {
                // Show success feedback
                feedback.style.display = 'block';
                
                // Hide feedback after 2 seconds
                setTimeout(function() {
                    feedback.style.display = 'none';
                }, 2000);
            }).catch(function(err) {
                console.error('Failed to copy command: ', err);
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = commandText;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                feedback.style.display = 'block';
                setTimeout(function() {
                    feedback.style.display = 'none';
                }, 2000);
            });
        }
        
        // Enhanced ESC key support for both modals
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const assessmentModal = document.getElementById('assessment-modal');
                const backportModal = document.getElementById('backport-modal');
                
                if (assessmentModal.style.display === 'flex') {
                    closeAssessmentModal();
                } else if (backportModal.style.display === 'flex') {
                    closeBackportModal();
                }
            }
        });
        
        // Enhanced click outside modal to close for both modals
        document.addEventListener('click', function(e) {
            const assessmentModal = document.getElementById('assessment-modal');
            const backportModal = document.getElementById('backport-modal');
            
            if (e.target === assessmentModal) {
                closeAssessmentModal();
            } else if (e.target === backportModal) {
                closeBackportModal();
            }
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
#!/usr/bin/env python3
"""
AI-Powered Conversation Analyzer - Enhanced PR Analysis with Claude Code

Combines heuristic analysis with Claude Code's intelligent reasoning to extract:
- Refined problem summaries and key requirements
- Nuanced design decisions and solution approaches  
- Context-aware outstanding concerns and complexity assessment
- Sophisticated stakeholder feedback analysis

This leverages both pattern matching and AI reasoning for superior analysis quality.
"""

import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
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
class AIConversationAnalysis:
    """Enhanced analysis results combining heuristics with AI reasoning"""
    problem_summary: str
    key_requirements: List[str]
    design_decisions: List[str]
    outstanding_concerns: List[str]
    solution_approaches: List[str]
    complexity_indicators: List[str]
    complexity_score: int  # 1-10 scale
    stakeholder_feedback: List[str]
    discussion_themes: List[str]
    timeline_summary: str
    quality_assessment: str
    recommendations: List[str]


class AIPoweredConversationAnalyzer:
    """Uses Claude Code to perform intelligent conversation analysis"""
    
    def __init__(self, working_dir: Path = None, context_dir: Path = None, logs_dir: Path = None):
        # Default to script directory if not provided (most robust approach)
        if working_dir is None:
            working_dir = Path(__file__).parent.absolute()
            
        self.working_dir = working_dir.absolute()
        
        # Use provided context directory or default to working_dir/context
        if context_dir is None:
            self.context_dir = self.working_dir / "context"
        else:
            self.context_dir = Path(context_dir).absolute()
            
        # Use provided logs directory or default to working_dir/logs
        if logs_dir is None:
            self.logs_dir = self.working_dir / "logs"
        else:
            self.logs_dir = Path(logs_dir).absolute()
            
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_with_ai(self, pr_number: str) -> Optional[AIConversationAnalysis]:
        """Perform AI-powered conversation analysis"""
        Logger.info(f"🤖 Starting AI-powered analysis for PR #{pr_number}")
        
        pr_context_dir = self.context_dir / f"pr-{pr_number}"
        if not pr_context_dir.exists():
            Logger.error(f"❌ No context data found for PR #{pr_number}")
            return None
        
        try:
            # Load all context data
            context_data = self._load_all_context_data(pr_context_dir)
            if not context_data:
                Logger.error("❌ Failed to load context data")
                return None
            
            # Create analysis prompt with structured data
            analysis_prompt = self._create_analysis_prompt(context_data, pr_number)
            
            # Execute AI analysis using Claude Code
            ai_results = self._execute_claude_analysis(analysis_prompt, pr_number)
            if not ai_results:
                Logger.error("❌ AI analysis failed")
                return None
            
            # Parse and structure AI results
            analysis = self._parse_ai_results(ai_results, context_data)
            
            # Save enhanced analysis
            self._save_ai_analysis(pr_context_dir, analysis)
            
            Logger.success(f"✅ AI-powered analysis completed for PR #{pr_number}")
            Logger.info(f"   - Complexity score: {analysis.complexity_score}/10")
            Logger.info(f"   - Requirements identified: {len(analysis.key_requirements)}")
            Logger.info(f"   - Concerns flagged: {len(analysis.outstanding_concerns)}")
            Logger.info(f"   - Recommendations: {len(analysis.recommendations)}")
            
            return analysis
            
        except Exception as e:
            Logger.error(f"❌ AI analysis failed: {e}")
            return None
    
    def _load_all_context_data(self, pr_context_dir: Path) -> Dict[str, Any]:
        """Load all context data files"""
        context_data = {}
        
        files_to_load = [
            ("pr_data", "pr-data.json"),
            ("issue_data", "issue-data.json"), 
            ("conversation", "conversation.json"),
            ("file_changes", "file-changes.json")
            # Note: heuristic_analysis/conversation-analysis.json is optional
        ]
        
        for key, filename in files_to_load:
            file_path = pr_context_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        context_data[key] = data if data is not None else []
                except Exception as e:
                    Logger.warn(f"⚠️  Could not load {filename}: {e}")
                    context_data[key] = []
            else:
                context_data[key] = []
        
        return context_data
    
    def _create_analysis_prompt(self, context_data: Dict[str, Any], pr_number: str) -> str:
        """Create structured prompt for Claude Code analysis using template"""
        
        # Extract key information for the prompt with proper type handling
        pr_data = context_data.get('pr_data', {})
        if not isinstance(pr_data, dict):
            pr_data = {}
        
        issue_data = context_data.get('issue_data', [])
        if not isinstance(issue_data, list):
            issue_data = []
            
        conversation = context_data.get('conversation', [])
        if not isinstance(conversation, list):
            conversation = []
            
        file_changes = context_data.get('file_changes', [])
        if not isinstance(file_changes, list):
            file_changes = []
            
        heuristic = context_data.get('heuristic_analysis', {}) or {}
        
        # Load template
        template_path = self.working_dir / "templates" / "ai_conversation_analysis_prompt.md"
        if not template_path.exists():
            Logger.error(f"❌ Template not found: {template_path}")
            raise FileNotFoundError(f"AI analysis template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Build linked issues section
        linked_issues_section = ""
        if issue_data:
            for issue in issue_data[:3]:  # Limit to first 3 issues
                linked_issues_section += f"""
**Issue #{issue.get('number', 'N/A')}**: {issue.get('title', 'N/A')}
```
{issue.get('body', 'No description')[:500]}
```
"""
        else:
            linked_issues_section = "No linked issues found."
        
        # Build conversation excerpts section
        conversation_excerpts = ""
        important_entries = self._select_important_conversation_entries(conversation)
        for entry in important_entries[:5]:
            conversation_excerpts += f"""
**{entry.get('author', 'Unknown')}** ({entry.get('type', 'comment')}):
```
{entry.get('body', '')[:300]}
```
"""
        
        if not conversation_excerpts:
            conversation_excerpts = "No significant conversation entries found."
        
        # Build file changes detail section (especially important for shallow PRs)
        file_changes_detail = self._build_file_changes_detail(file_changes)
        
        # Format template with context data
        formatted_prompt = template.format(
            pr_number=pr_number,
            pr_title=pr_data.get('title', 'N/A'),
            pr_author=pr_data.get('author', 'N/A'),
            pr_state=pr_data.get('state', 'N/A'),
            pr_labels=', '.join(pr_data.get('labels', [])) or 'None',
            pr_body=pr_data.get('body', 'No description available')[:1000],
            linked_issues_section=linked_issues_section,
            total_files_changed=len(file_changes),
            file_types_summary=self._summarize_file_types(file_changes),
            file_changes_detail=file_changes_detail,
            total_conversation_entries=len(conversation),
            total_participants=len(set(entry.get('author', '') for entry in conversation)),
            timeline_summary=heuristic.get('timeline_summary', 'N/A'),
            conversation_excerpts=conversation_excerpts,
            heuristic_problem_summary=heuristic.get('problem_summary', 'N/A'),
            heuristic_requirements_count=len(heuristic.get('key_requirements', [])),
            heuristic_concerns_count=len(heuristic.get('outstanding_concerns', [])),
            heuristic_themes=', '.join(heuristic.get('discussion_themes', [])) or 'None'
        )
        
        return formatted_prompt
    
    def _summarize_file_types(self, file_changes: List[Dict[str, Any]]) -> str:
        """Summarize the types of files changed"""
        if not file_changes:
            return "None"
        
        types = {}
        for change in file_changes:
            filename = change.get('filename', '')
            if filename.endswith('.java'):
                if 'test' in filename.lower():
                    types['Java Tests'] = types.get('Java Tests', 0) + 1
                else:
                    types['Java Implementation'] = types.get('Java Implementation', 0) + 1
            elif filename.endswith(('.yml', '.yaml', '.properties', '.xml')):
                types['Configuration'] = types.get('Configuration', 0) + 1
            elif filename.endswith('.md'):
                types['Documentation'] = types.get('Documentation', 0) + 1
            else:
                types['Other'] = types.get('Other', 0) + 1
        
        return ', '.join(f"{k}: {v}" for k, v in types.items())
    
    def _build_file_changes_detail(self, file_changes: List[Dict[str, Any]]) -> str:
        """Build detailed file changes section for shallow PRs with minimal conversation"""
        if not file_changes:
            return "No file changes found."
        
        detail = ""
        for change in file_changes:
            filename = change.get('filename', 'Unknown file')
            status = change.get('status', 'unknown')
            additions = change.get('additions', 0)
            deletions = change.get('deletions', 0)
            patch = change.get('patch', '')
            
            detail += f"""
**File: {filename}**
- Status: {status}
- Changes: +{additions} -{deletions}
- Diff:
```diff
{patch[:1000]}
```
"""
        
        return detail.strip()
    
    def _select_important_conversation_entries(self, conversation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select most important conversation entries for analysis"""
        if not conversation:
            return []
        
        # Prioritize entries with questions, concerns, or substantial content
        scored_entries = []
        for entry in conversation:
            body = entry.get('body', '')
            score = 0
            
            # Higher score for longer, more substantive comments
            score += min(len(body) // 100, 5)
            
            # Higher score for questions and concerns
            if '?' in body:
                score += 3
            if any(word in body.lower() for word in ['concern', 'issue', 'problem', 'worry']):
                score += 2
            if any(word in body.lower() for word in ['decision', 'approach', 'implementation']):
                score += 2
            
            # Lower score for very short or generic comments
            if len(body) < 20:
                score -= 2
            
            scored_entries.append((score, entry))
        
        # Sort by score and return top entries
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for score, entry in scored_entries[:8]]
    
    def _execute_claude_analysis(self, prompt: str, pr_number: str) -> Optional[Dict[str, Any]]:
        """Execute analysis using Claude Code with centralized JSON extraction"""
        try:
            Logger.info("🤖 Running Claude Code analysis...")
            
            # Initialize Claude Code wrapper
            claude = ClaudeCodeWrapper(logs_dir=self.logs_dir)
            
            # Debug: Check availability with details
            is_available = claude.is_available()
            version = claude.get_version()
            Logger.info(f"🔍 Claude Code path: {claude.claude_binary_path}")
            Logger.info(f"🔍 Claude Code available: {is_available}")
            Logger.info(f"🔍 Claude Code version: {version}")
            
            if not is_available:
                Logger.error("❌ Claude Code is not available")
                return None
            
            # Debug: Save prompt to logs directory for future debugging
            logs_dir = self.working_dir / "logs"
            logs_dir.mkdir(exist_ok=True)
            debug_prompt_file = logs_dir / "claude-prompt-ai-analyzer.txt"
            with open(debug_prompt_file, 'w') as f:
                f.write(prompt)
            Logger.info(f"🔍 Saved prompt to: {debug_prompt_file}")
            
            # Use centralized JSON extraction from ClaudeCodeWrapper
            debug_response_file = logs_dir / "claude-response-ai-analyzer.txt"
            result = claude.analyze_from_file_with_json(
                str(debug_prompt_file), 
                str(debug_response_file), 
                timeout=300, 
                show_progress=True,
                system_debug_mode=True,
                pr_number=pr_number
            )
            
            if result['success'] and result['response']:
                Logger.info(f"🔍 Claude Code stdout length: {len(result['response'])} chars")
                Logger.info(f"🔍 Claude Code stderr: {result['stderr'][:200] if result['stderr'] else 'None'}")
                Logger.info(f"🔍 Saved Claude Code response to: {debug_response_file}")
                
                # Log JSON extraction status
                if result.get('json_extraction_success'):
                    Logger.info("✅ JSON extraction successful using centralized method")
                else:
                    Logger.warn("⚠️  JSON extraction failed, will use fallback parsing")
                
                if len(result['response']) <= 10:
                    Logger.info(f"🔍 Claude Code stdout content (short): '{result['response']}'")
                
                return {
                    'response': result['response'],
                    'json_data': result.get('json_data'),  # Pre-extracted JSON
                    'json_extraction_success': result.get('json_extraction_success', False),
                    'response_file': str(debug_response_file),
                    'success': True
                }
            else:
                Logger.error(f"❌ Claude Code analysis failed: {result.get('error', 'Unknown error')}")
                if result.get('stderr'):
                    Logger.error(f"❌ Claude Code stderr: {result['stderr']}")
                return None
                
        except Exception as e:
            Logger.error(f"❌ Failed to execute Claude Code: {e}")
            return None
    
    def _parse_ai_results(self, ai_result: Dict[str, Any], context_data: Dict[str, Any]) -> AIConversationAnalysis:
        """Parse AI analysis results into structured format using centralized JSON extraction"""
        
        response_text = ai_result.get('response', '')
        if not response_text:
            Logger.error("❌ Empty AI response")
            ai_data = self._extract_from_text("")
        else:
            try:
                # Try to use pre-extracted JSON data first (from centralized extraction)
                ai_data = ai_result.get('json_data')
                
                if ai_data and ai_result.get('json_extraction_success'):
                    Logger.info("✅ Using pre-extracted JSON data from ClaudeCodeWrapper")
                else:
                    # Fallback: Try centralized JSON extraction as backup
                    Logger.info("🔄 Pre-extracted JSON not available, using fallback extraction...")
                    claude = ClaudeCodeWrapper(logs_dir=self.logs_dir)
                    ai_data = claude.extract_json_from_response(response_text)
                    
                    if ai_data:
                        Logger.info("✅ Fallback JSON extraction successful")
                    else:
                        # Final fallback to text extraction
                        Logger.info("🔄 JSON extraction failed, using text extraction fallback")
                        raise ValueError("Centralized JSON extraction failed")
            
            except (json.JSONDecodeError, ValueError) as e:
                Logger.warn(f"⚠️  Could not parse Claude Code JSON output: {e}")
                Logger.info(f"🔍 Raw output for debugging: {response_text[:500]}...")
                # Fallback to extracting information from text
                ai_data = self._extract_from_text(response_text)
        
        # Create analysis object with defaults
        return AIConversationAnalysis(
            problem_summary=ai_data.get('problem_summary', 'AI analysis unavailable'),
            key_requirements=ai_data.get('key_requirements', []),
            design_decisions=ai_data.get('design_decisions', []),
            outstanding_concerns=ai_data.get('outstanding_concerns', []),
            solution_approaches=ai_data.get('solution_approaches', []),
            complexity_indicators=ai_data.get('complexity_indicators', []),
            complexity_score=ai_data.get('complexity_score', 5),
            stakeholder_feedback=ai_data.get('stakeholder_feedback', []),
            discussion_themes=ai_data.get('discussion_themes', []),
            timeline_summary=context_data.get('heuristic_analysis', {}).get('timeline_summary', ''),
            quality_assessment=ai_data.get('quality_assessment', 'Quality assessment unavailable'),
            recommendations=ai_data.get('recommendations', [])
        )
    
    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """Fallback text extraction if JSON parsing fails"""
        # Simple fallback - return minimal structure
        return {
            'problem_summary': 'AI analysis could not be parsed properly',
            'key_requirements': [],
            'design_decisions': [],
            'outstanding_concerns': [],
            'solution_approaches': [],
            'complexity_indicators': [],
            'complexity_score': 5,
            'stakeholder_feedback': [],
            'discussion_themes': [],
            'quality_assessment': 'Analysis parsing failed',
            'recommendations': ['Retry analysis with improved prompting']
        }
    
    def _save_ai_analysis(self, pr_context_dir: Path, analysis: AIConversationAnalysis):
        """Save AI analysis results"""
        analysis_file = pr_context_dir / "ai-conversation-analysis.json"
        
        analysis_data = asdict(analysis)
        analysis_data['analysis_timestamp'] = datetime.now().isoformat()
        analysis_data['analyzer_version'] = 'ai-powered-v1.0'
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        Logger.info(f"📁 AI analysis saved to {analysis_file}")


def main():
    """Command-line interface for AI-powered conversation analysis"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-powered conversation analysis for Spring AI PRs')
    parser.add_argument('pr_number', help='GitHub PR number to analyze')
    parser.add_argument('--context-dir', type=Path, help='Context directory path')
    parser.add_argument('--logs-dir', type=Path, help='Logs directory path')
    
    args = parser.parse_args()
    
    # Use script directory for analysis (robust regardless of where script is called from)
    working_dir = Path(__file__).parent.absolute()
    analyzer = AIPoweredConversationAnalyzer(
        working_dir=working_dir,
        context_dir=args.context_dir,
        logs_dir=args.logs_dir
    )
    
    # Perform AI analysis
    analysis = analyzer.analyze_with_ai(args.pr_number)
    
    if analysis:
        print(f"\n✅ AI analysis completed for PR #{args.pr_number}")
        print(f"📊 Analysis summary:")
        print(f"   - Problem: {analysis.problem_summary[:100]}...")
        print(f"   - Complexity Score: {analysis.complexity_score}/10")
        print(f"   - Requirements: {len(analysis.key_requirements)}")
        print(f"   - Concerns: {len(analysis.outstanding_concerns)}")
        print(f"   - Recommendations: {len(analysis.recommendations)}")
        sys.exit(0)
    else:
        print(f"\n❌ AI analysis failed for PR #{args.pr_number}")
        sys.exit(1)


if __name__ == "__main__":
    main()
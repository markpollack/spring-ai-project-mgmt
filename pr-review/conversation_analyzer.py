#!/usr/bin/env python3
"""
Conversation Analyzer - Core for Enhanced PR Analysis

Analyzes collected GitHub conversation data to extract:
- Problem summaries and key requirements
- Design decisions and solution approaches  
- Outstanding concerns and unresolved questions
- Stakeholder feedback and discussion themes

This is Iteration 2 of the Enhanced PR Analysis implementation.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

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
class ConversationAnalysis:
    """Analysis results from issue and PR conversations"""
    problem_summary: str
    key_requirements: List[str]
    design_decisions: List[str]
    outstanding_concerns: List[str]
    solution_approaches: List[str]
    complexity_indicators: List[str]
    stakeholder_feedback: List[str]
    discussion_themes: List[str]
    timeline_summary: str


@dataclass
class ConversationEntry:
    """Individual conversation entry for analysis"""
    type: str  # 'issue_comment', 'pr_comment', 'review', 'commit'
    author: str
    created_at: str
    body: str
    url: str
    metadata: Dict[str, Any]


class ConversationAnalyzer:
    """Analyzes GitHub conversations to extract insights and context"""
    
    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
        self.context_dir = working_dir / "context"
        
        # Analysis patterns for extracting key information
        self.problem_patterns = [
            r'[Pp]roblem[:\s]+(.*?)(?:\n|$)',
            r'[Ii]ssue[:\s]+(.*?)(?:\n|$)', 
            r'[Bb]ug[:\s]+(.*?)(?:\n|$)',
            r'[Ff]ixes?\s+#?\d+[:\s]+(.*?)(?:\n|$)',
            r'[Nn]eeds?\s+to\s+(.*?)(?:\n|$)',
            r'[Ss]hould\s+(.*?)(?:\n|$)'
        ]
        
        self.requirement_patterns = [
            r'[Rr]equirement[:\s]+(.*?)(?:\n|$)',
            r'[Mm]ust\s+(.*?)(?:\n|$)',
            r'[Nn]eed\s+to\s+(.*?)(?:\n|$)',
            r'[Ss]hould\s+(.*?)(?:\n|$)',
            r'[Ww]e\s+need\s+(.*?)(?:\n|$)',
            r'[Ii]t\s+should\s+(.*?)(?:\n|$)'
        ]
        
        self.decision_patterns = [
            r'[Dd]ecision[:\s]+(.*?)(?:\n|$)',
            r'[Ww]e\s+decided\s+(.*?)(?:\n|$)',
            r'[Ii]\s+decided\s+(.*?)(?:\n|$)',
            r'[Cc]hose\s+to\s+(.*?)(?:\n|$)',
            r'[Gg]oing\s+with\s+(.*?)(?:\n|$)',
            r'[Ii]mplemented\s+(.*?)(?:\n|$)'
        ]
        
        self.concern_patterns = [
            r'[Cc]oncern[:\s]+(.*?)(?:\n|$)',
            r'[Ww]orried\s+about\s+(.*?)(?:\n|$)',
            r'[Pp]otential\s+issue\s+(.*?)(?:\n|$)',
            r'[Nn]ot\s+sure\s+(.*?)(?:\n|$)',
            r'[Qq]uestion[:\s]+(.*?)(?:\n|$)',
            r'[Ww]hat\s+about\s+(.*?)(?:\n|$)',
            r'[Hh]ow\s+do\s+we\s+(.*?)(?:\n|$)'
        ]
        
        self.complexity_indicators = [
            'breaking change', 'api change', 'architecture', 'refactor',
            'performance', 'scalability', 'migration', 'backward compatibility',
            'thread safety', 'concurrency', 'security', 'integration',
            'dependency', 'framework change', 'major version'
        ]
    
    def analyze_conversation(self, pr_number: str) -> Optional[ConversationAnalysis]:
        """Analyze conversation data for a specific PR"""
        Logger.info(f"🧠 Analyzing conversation for PR #{pr_number}")
        
        pr_context_dir = self.context_dir / f"pr-{pr_number}"
        if not pr_context_dir.exists():
            Logger.error(f"❌ No context data found for PR #{pr_number}")
            return None
        
        try:
            # Load conversation data
            conversation_file = pr_context_dir / "conversation.json"
            if not conversation_file.exists():
                Logger.error("❌ No conversation data found")
                return None
            
            with open(conversation_file, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            
            # Load PR and issue data for additional context
            pr_data = self._load_pr_data(pr_context_dir)
            issue_data = self._load_issue_data(pr_context_dir)
            
            # Convert to ConversationEntry objects
            conversation_entries = []
            for entry in conversation_data:
                conversation_entries.append(ConversationEntry(
                    type=entry['type'],
                    author=entry['author'],
                    created_at=entry['created_at'],
                    body=entry['body'],
                    url=entry['url'],
                    metadata=entry['metadata']
                ))
            
            # Perform analysis
            analysis = self._perform_analysis(conversation_entries, pr_data, issue_data)
            
            # Save analysis results
            self._save_analysis(pr_context_dir, analysis)
            
            Logger.success(f"✅ Conversation analysis completed for PR #{pr_number}")
            Logger.info(f"   - Problem summary: {len(analysis.problem_summary)} chars")
            Logger.info(f"   - Key requirements: {len(analysis.key_requirements)}")
            Logger.info(f"   - Design decisions: {len(analysis.design_decisions)}")
            Logger.info(f"   - Outstanding concerns: {len(analysis.outstanding_concerns)}")
            
            return analysis
            
        except Exception as e:
            Logger.error(f"❌ Failed to analyze conversation: {e}")
            return None
    
    def _load_pr_data(self, pr_context_dir: Path) -> Dict[str, Any]:
        """Load PR data from context"""
        try:
            pr_file = pr_context_dir / "pr-data.json"
            if pr_file.exists():
                with open(pr_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            Logger.warn(f"⚠️  Could not load PR data: {e}")
        return {}
    
    def _load_issue_data(self, pr_context_dir: Path) -> List[Dict[str, Any]]:
        """Load issue data from context"""
        try:
            issue_file = pr_context_dir / "issue-data.json"
            if issue_file.exists():
                with open(issue_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            Logger.warn(f"⚠️  Could not load issue data: {e}")
        return []
    
    def _perform_analysis(self, conversation: List[ConversationEntry], 
                         pr_data: Dict[str, Any], issue_data: List[Dict[str, Any]]) -> ConversationAnalysis:
        """Perform comprehensive conversation analysis"""
        
        # Extract problem summary
        problem_summary = self._extract_problem_summary(conversation, pr_data, issue_data)
        
        # Extract key requirements
        key_requirements = self._extract_requirements(conversation, pr_data, issue_data)
        
        # Extract design decisions
        design_decisions = self._extract_design_decisions(conversation)
        
        # Extract outstanding concerns
        outstanding_concerns = self._extract_concerns(conversation)
        
        # Extract solution approaches
        solution_approaches = self._extract_solution_approaches(conversation, pr_data)
        
        # Identify complexity indicators
        complexity_indicators = self._identify_complexity_indicators(conversation, pr_data)
        
        # Extract stakeholder feedback
        stakeholder_feedback = self._extract_stakeholder_feedback(conversation)
        
        # Identify discussion themes
        discussion_themes = self._identify_discussion_themes(conversation)
        
        # Generate timeline summary
        timeline_summary = self._generate_timeline_summary(conversation)
        
        return ConversationAnalysis(
            problem_summary=problem_summary,
            key_requirements=key_requirements,
            design_decisions=design_decisions,
            outstanding_concerns=outstanding_concerns,
            solution_approaches=solution_approaches,
            complexity_indicators=complexity_indicators,
            stakeholder_feedback=stakeholder_feedback,
            discussion_themes=discussion_themes,
            timeline_summary=timeline_summary
        )
    
    def _extract_problem_summary(self, conversation: List[ConversationEntry],
                                pr_data: Dict[str, Any], issue_data: List[Dict[str, Any]]) -> str:
        """Extract concise problem summary"""
        problem_texts = []
        
        # Start with PR title - this is usually the clearest problem statement
        if pr_data and pr_data.get('title'):
            title = pr_data['title'].strip()
            if title:
                problem_texts.append(title)
        
        # Add issue titles - these often contain the root problem
        for issue in issue_data:
            title = issue.get('title', '').strip()
            if title and title not in problem_texts:
                problem_texts.append(title)
        
        # Look for "Fixes #" patterns in PR body for linked issues
        if pr_data and pr_data.get('body'):
            body = pr_data['body']
            # Extract text after "Fixes #" patterns
            fixes_patterns = [
                r'[Ff]ixes?\s+#\d+[:\s]+(.*?)(?:\n|$)',
                r'[Cc]loses?\s+#\d+[:\s]+(.*?)(?:\n|$)',
                r'[Rr]esolves?\s+#\d+[:\s]+(.*?)(?:\n|$)'
            ]
            
            for pattern in fixes_patterns:
                matches = re.findall(pattern, body, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    clean_match = match.strip()
                    if len(clean_match) > 10:
                        problem_texts.append(clean_match)
        
        # If we have good candidates from titles, use the best one
        if problem_texts:
            # Prefer longer, more descriptive titles/statements
            problem_texts.sort(key=len, reverse=True)
            return problem_texts[0][:200]  # Limit to reasonable length
        
        return "Problem description not clearly identified from conversation"
    
    def _extract_first_sentence(self, text: str) -> str:
        """Extract first meaningful sentence from text"""
        # Clean up markdown and formatting
        clean_text = re.sub(r'[#*_`]', '', text)
        clean_text = re.sub(r'https?://[^\s]+', '', clean_text)
        
        # Find first sentence
        sentences = re.split(r'[.!?]+', clean_text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 15 and not sentence.startswith(('http', 'www')):
                return sentence
        
        return ""
    
    def _select_best_summary(self, candidates: List[str]) -> str:
        """Select the best problem summary from candidates"""
        if not candidates:
            return ""
        
        # Prefer longer, more descriptive summaries
        candidates = [c for c in candidates if len(c) > 10]
        if not candidates:
            return ""
        
        # Sort by length and informativeness
        candidates.sort(key=lambda x: len(x), reverse=True)
        return candidates[0][:200]  # Limit to reasonable length
    
    def _extract_requirements(self, conversation: List[ConversationEntry],
                            pr_data: Dict[str, Any], issue_data: List[Dict[str, Any]]) -> List[str]:
        """Extract key requirements from conversation"""
        requirements = []
        
        # Extract from all conversation entries
        all_text = []
        if pr_data.get('body'):
            all_text.append(pr_data['body'])
        for issue in issue_data:
            if issue.get('body'):
                all_text.append(issue['body'])
        for entry in conversation:
            all_text.append(entry.body)
        
        # Apply requirement patterns
        for text in all_text:
            for pattern in self.requirement_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    clean_match = match.strip()
                    if len(clean_match) > 5:
                        requirements.append(clean_match)
        
        # Deduplicate and clean
        return self._deduplicate_and_clean(requirements)
    
    def _extract_design_decisions(self, conversation: List[ConversationEntry]) -> List[str]:
        """Extract design decisions from conversation"""
        decisions = []
        
        for entry in conversation:
            for pattern in self.decision_patterns:
                matches = re.findall(pattern, entry.body, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    clean_match = match.strip()
                    if len(clean_match) > 5:
                        decisions.append(f"{entry.author}: {clean_match}")
        
        return self._deduplicate_and_clean(decisions)
    
    def _extract_concerns(self, conversation: List[ConversationEntry]) -> List[str]:
        """Extract outstanding concerns and questions"""
        concerns = []
        
        for entry in conversation:
            # Look for question marks and concern patterns
            if '?' in entry.body:
                questions = re.findall(r'([^.!?]*\?)', entry.body)
                for question in questions:
                    clean_question = question.strip()
                    if len(clean_question) > 10:
                        concerns.append(f"{entry.author}: {clean_question}")
            
            # Apply concern patterns
            for pattern in self.concern_patterns:
                matches = re.findall(pattern, entry.body, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    clean_match = match.strip()
                    if len(clean_match) > 5:
                        concerns.append(f"{entry.author}: {clean_match}")
        
        return self._deduplicate_and_clean(concerns)
    
    def _extract_solution_approaches(self, conversation: List[ConversationEntry],
                                   pr_data: Dict[str, Any]) -> List[str]:
        """Extract solution approaches discussed"""
        approaches = []
        
        # Look for implementation approaches in PR body
        if pr_data.get('body'):
            # Look for numbered lists or bullet points describing implementation
            impl_patterns = [
                r'[Ii]mplementation[:\s]+(.*?)(?:\n\n|$)',
                r'[Aa]pproach[:\s]+(.*?)(?:\n\n|$)',
                r'[Ss]olution[:\s]+(.*?)(?:\n\n|$)',
                r'[Cc]hanges[:\s]+(.*?)(?:\n\n|$)'
            ]
            
            for pattern in impl_patterns:
                matches = re.findall(pattern, pr_data['body'], re.IGNORECASE | re.MULTILINE | re.DOTALL)
                for match in matches:
                    clean_match = match.strip()
                    if len(clean_match) > 10:
                        approaches.append(clean_match)
        
        # Look for alternative approaches in discussion
        for entry in conversation:
            alt_patterns = [
                r'[Aa]lternative[:\s]+(.*?)(?:\n|$)',
                r'[Aa]nother\s+approach[:\s]+(.*?)(?:\n|$)',
                r'[Cc]ould\s+also\s+(.*?)(?:\n|$)',
                r'[Ww]hat\s+if\s+we\s+(.*?)(?:\n|$)'
            ]
            
            for pattern in alt_patterns:
                matches = re.findall(pattern, entry.body, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    clean_match = match.strip()
                    if len(clean_match) > 5:
                        approaches.append(f"{entry.author}: {clean_match}")
        
        return self._deduplicate_and_clean(approaches)
    
    def _identify_complexity_indicators(self, conversation: List[ConversationEntry],
                                      pr_data: Dict[str, Any]) -> List[str]:
        """Identify indicators of implementation complexity"""
        indicators = []
        
        # Check all text for complexity keywords
        all_text = []
        if pr_data.get('body'):
            all_text.append(pr_data['body'].lower())
        for entry in conversation:
            all_text.append(entry.body.lower())
        
        combined_text = ' '.join(all_text)
        
        for indicator in self.complexity_indicators:
            if indicator in combined_text:
                indicators.append(indicator.title())
        
        return list(set(indicators))  # Remove duplicates
    
    def _extract_stakeholder_feedback(self, conversation: List[ConversationEntry]) -> List[str]:
        """Extract key stakeholder feedback"""
        feedback = []
        
        # Group by author to identify key stakeholders
        author_comments = defaultdict(list)
        for entry in conversation:
            author_comments[entry.author].append(entry.body)
        
        # Extract meaningful feedback from frequent contributors
        for author, comments in author_comments.items():
            if len(comments) >= 2:  # Active participants
                # Look for approval/rejection patterns
                approval_patterns = [
                    r'[Ll]ooks?\s+good', r'[Aa]pprove', r'[Ll]gtm', r'[Ss]hip\s+it',
                    r'[Gg]reat\s+work', r'[Pp]erfect'
                ]
                concern_patterns = [
                    r'[Nn]ot\s+sure', r'[Cc]oncerned', r'[Ww]orried', r'[Ii]ssue\s+with'
                ]
                
                for comment in comments:
                    for pattern in approval_patterns + concern_patterns:
                        if re.search(pattern, comment, re.IGNORECASE):
                            clean_comment = comment[:100].strip()
                            feedback.append(f"{author}: {clean_comment}")
                            break
        
        return self._deduplicate_and_clean(feedback[:10])  # Limit to most relevant
    
    def _identify_discussion_themes(self, conversation: List[ConversationEntry]) -> List[str]:
        """Identify main themes in the discussion"""
        themes = []
        
        # Common theme keywords
        theme_keywords = {
            'Performance': ['performance', 'speed', 'latency', 'optimization', 'faster'],
            'Security': ['security', 'auth', 'credential', 'token', 'secure'],
            'Compatibility': ['compatibility', 'breaking', 'backward', 'version'],
            'Testing': ['test', 'testing', 'coverage', 'validation'],
            'Documentation': ['docs', 'documentation', 'readme', 'comment'],
            'API Design': ['api', 'interface', 'method', 'signature'],
            'Configuration': ['config', 'configuration', 'properties', 'settings'],
            'Error Handling': ['error', 'exception', 'handling', 'try', 'catch']
        }
        
        # Count theme occurrences
        theme_counts = defaultdict(int)
        combined_text = ' '.join(entry.body.lower() for entry in conversation)
        
        for theme, keywords in theme_keywords.items():
            for keyword in keywords:
                theme_counts[theme] += combined_text.count(keyword)
        
        # Return themes with significant mentions
        for theme, count in theme_counts.items():
            if count >= 2:
                themes.append(theme)
        
        return themes
    
    def _generate_timeline_summary(self, conversation: List[ConversationEntry]) -> str:
        """Generate a timeline summary of key events"""
        if not conversation:
            return "No conversation timeline available"
        
        # Sort by date
        sorted_conversation = sorted(conversation, key=lambda x: x.created_at)
        
        first_entry = sorted_conversation[0]
        last_entry = sorted_conversation[-1]
        
        # Calculate duration
        try:
            first_date = datetime.fromisoformat(first_entry.created_at.replace('Z', '+00:00'))
            last_date = datetime.fromisoformat(last_entry.created_at.replace('Z', '+00:00'))
            duration = (last_date - first_date).days
        except:
            duration = 0
        
        # Count participants
        participants = set(entry.author for entry in conversation)
        
        return f"Discussion span: {duration} days, {len(participants)} participants, {len(conversation)} entries"
    
    def _deduplicate_and_clean(self, items: List[str]) -> List[str]:
        """Remove duplicates and clean text items"""
        seen = set()
        cleaned = []
        
        for item in items:
            # Clean the item
            clean_item = re.sub(r'\s+', ' ', item.strip())
            clean_item = clean_item[:150]  # Limit length
            
            # Check for duplicates (case-insensitive similarity)
            if clean_item and len(clean_item) > 5:
                lower_item = clean_item.lower()
                if not any(lower_item in seen_item or seen_item in lower_item for seen_item in seen):
                    seen.add(lower_item)
                    cleaned.append(clean_item)
        
        return cleaned[:10]  # Limit to most relevant items
    
    def _save_analysis(self, pr_context_dir: Path, analysis: ConversationAnalysis):
        """Save analysis results to JSON file"""
        analysis_file = pr_context_dir / "conversation-analysis.json"
        
        analysis_data = asdict(analysis)
        analysis_data['analysis_timestamp'] = datetime.now().isoformat()
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        Logger.info(f"📁 Conversation analysis saved to {analysis_file}")


def main():
    """Command-line interface for conversation analysis"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 conversation_analyzer.py <pr_number>")
        print("\nExamples:")
        print("  python3 conversation_analyzer.py 3386")
        sys.exit(1)
    
    pr_number = sys.argv[1]
    
    # Use script directory for analysis (robust regardless of where script is called from)
    working_dir = Path(__file__).parent.absolute()
    analyzer = ConversationAnalyzer(working_dir)
    
    # Analyze conversation
    analysis = analyzer.analyze_conversation(pr_number)
    
    if analysis:
        print(f"\n✅ Successfully analyzed conversation for PR #{pr_number}")
        print(f"📊 Analysis summary:")
        print(f"   - Problem: {analysis.problem_summary[:100]}...")
        print(f"   - Requirements: {len(analysis.key_requirements)}")
        print(f"   - Concerns: {len(analysis.outstanding_concerns)}")
        print(f"   - Complexity indicators: {len(analysis.complexity_indicators)}")
        sys.exit(0)
    else:
        print(f"\n❌ Failed to analyze conversation for PR #{pr_number}")
        sys.exit(1)


if __name__ == "__main__":
    main()
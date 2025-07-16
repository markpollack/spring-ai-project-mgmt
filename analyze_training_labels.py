#!/usr/bin/env python3
"""
Analyze training issues to understand label patterns and improve descriptions.
"""

import json
import re
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import Dict, List, Set
import argparse


@dataclass
class LabelAnalysis:
    """Container for label analysis results"""
    name: str
    count: int
    title_patterns: List[str]
    body_patterns: List[str]
    technical_terms: List[str]
    problem_types: List[str]
    example_phrases: List[str]
    common_words: List[str]


class LabelAnalyzer:
    def __init__(self, training_file: str):
        self.training_file = training_file
        self.issues = []
        self.label_data = defaultdict(lambda: {
            'issues': [],
            'titles': [],
            'bodies': [],
            'technical_terms': set(),
            'problem_indicators': set(),
            'example_phrases': set()
        })
        
        # Technical term patterns
        self.technical_patterns = [
            r'\b[A-Z][a-z]+[A-Z][a-zA-Z]*\b',  # CamelCase classes
            r'\b[a-z]+\.[a-z]+\.[a-zA-Z.]+\b',  # Package names
            r'\b[a-z-]+\.properties\b',  # Properties files
            r'\b[a-z-]+\.yml\b',  # YAML files
            r'\b[a-z-]+\.yaml\b',  # YAML files
            r'\b[a-z-]+\.xml\b',  # XML files
            r'\b[a-z-]+\.json\b',  # JSON files
            r'\b@[A-Z][a-zA-Z]+\b',  # Annotations
            r'\b[a-z-]+\.[a-z-]+\.[a-z-]+\b',  # Configuration keys
            r'\b[A-Z_]+\b',  # Constants
            r'\b[a-z]+://[^\s]+\b',  # URLs
            r'\b\d+\.\d+\.\d+\b',  # Version numbers
            r'\b[a-z]+-[a-z]+-[a-z-]+\b',  # Hyphenated technical terms
        ]
        
        # Problem type indicators
        self.problem_indicators = [
            r'\b(error|exception|fail|bug|issue|problem|broken|not working)\b',
            r'\b(unable to|can\'t|cannot|doesn\'t work|not found|missing)\b',
            r'\b(timeout|connection|network|ssl|tls|certificate)\b',
            r'\b(memory|performance|slow|hang|freeze|crash)\b',
            r'\b(null|empty|blank|undefined|invalid)\b',
            r'\b(deprecate|remove|replace|update|upgrade)\b',
            r'\b(support|feature|enhancement|improvement)\b',
            r'\b(configuration|config|property|setting)\b',
            r'\b(integration|compatibility|version|dependency)\b',
            r'\b(documentation|doc|example|test|testing)\b'
        ]

    def load_issues(self):
        """Load issues from training file"""
        with open(self.training_file, 'r') as f:
            self.issues = json.load(f)
        print(f"Loaded {len(self.issues)} issues from {self.training_file}")

    def extract_technical_terms(self, text: str) -> Set[str]:
        """Extract technical terms from text"""
        terms = set()
        text_lower = text.lower()
        
        for pattern in self.technical_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) > 2:  # Skip very short matches
                    terms.add(match)
        
        return terms

    def extract_problem_indicators(self, text: str) -> Set[str]:
        """Extract problem type indicators from text"""
        indicators = set()
        text_lower = text.lower()
        
        for pattern in self.problem_indicators:
            matches = re.findall(pattern, text_lower)
            indicators.update(matches)
        
        return indicators

    def extract_example_phrases(self, text: str, max_length: int = 100) -> Set[str]:
        """Extract meaningful phrases from text"""
        phrases = set()
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if 10 <= len(sentence) <= max_length:
                # Clean up the sentence
                sentence = re.sub(r'\s+', ' ', sentence)
                sentence = re.sub(r'[*_`]+', '', sentence)
                if sentence:
                    phrases.add(sentence)
        
        return phrases

    def get_common_words(self, texts: List[str], min_length: int = 3) -> List[str]:
        """Get most common words from texts"""
        word_counts = Counter()
        
        for text in texts:
            # Remove code blocks and special characters
            text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
            text = re.sub(r'`[^`]+`', '', text)
            text = re.sub(r'[^\w\s]', ' ', text)
            
            words = text.lower().split()
            for word in words:
                if len(word) >= min_length and word.isalpha():
                    word_counts[word] += 1
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'with', 'have', 'this', 'will', 'your', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were', 'what', 'would', 'there', 'being', 'could', 'after', 'first', 'might', 'other', 'right', 'should', 'these', 'through', 'where', 'before', 'between', 'without', 'because', 'against', 'something', 'anything', 'everything', 'nothing', 'someone', 'anyone', 'everyone', 'nobody'
        }
        
        return [word for word, count in word_counts.most_common(20) if word not in stop_words]

    def analyze_labels(self):
        """Analyze all labels in the training data"""
        # Collect data for each label
        for issue in self.issues:
            labels = issue.get('labels', [])
            title = issue.get('title', '')
            body = issue.get('body', '')
            
            for label in labels:
                self.label_data[label]['issues'].append(issue)
                self.label_data[label]['titles'].append(title)
                self.label_data[label]['bodies'].append(body)
                
                # Extract technical terms
                tech_terms = self.extract_technical_terms(title + ' ' + body)
                self.label_data[label]['technical_terms'].update(tech_terms)
                
                # Extract problem indicators
                problems = self.extract_problem_indicators(title + ' ' + body)
                self.label_data[label]['problem_indicators'].update(problems)
                
                # Extract example phrases
                phrases = self.extract_example_phrases(title + ' ' + body)
                self.label_data[label]['example_phrases'].update(phrases)

    def generate_analysis_report(self) -> List[LabelAnalysis]:
        """Generate comprehensive analysis report"""
        analyses = []
        
        # Sort labels by frequency
        sorted_labels = sorted(self.label_data.items(), key=lambda x: len(x[1]['issues']), reverse=True)
        
        for label_name, data in sorted_labels:
            issues = data['issues']
            titles = data['titles']
            bodies = data['bodies']
            
            # Get common words from titles and bodies
            common_words = self.get_common_words(titles + bodies)
            
            # Get most frequent technical terms
            tech_terms = sorted(list(data['technical_terms']), key=len, reverse=True)[:15]
            
            # Get problem indicators
            problem_types = sorted(list(data['problem_indicators']))[:10]
            
            # Get example phrases
            example_phrases = sorted(list(data['example_phrases']), key=len)[:10]
            
            # Extract title patterns
            title_patterns = []
            for title in titles[:10]:  # Sample first 10 titles
                if title:
                    title_patterns.append(title[:80] + '...' if len(title) > 80 else title)
            
            # Extract body patterns (first line of body)
            body_patterns = []
            for body in bodies[:10]:  # Sample first 10 bodies
                if body:
                    first_line = body.split('\n')[0].strip()
                    if first_line:
                        body_patterns.append(first_line[:100] + '...' if len(first_line) > 100 else first_line)
            
            analysis = LabelAnalysis(
                name=label_name,
                count=len(issues),
                title_patterns=title_patterns,
                body_patterns=body_patterns,
                technical_terms=tech_terms,
                problem_types=problem_types,
                example_phrases=example_phrases,
                common_words=common_words
            )
            analyses.append(analysis)
        
        return analyses

    def print_report(self, analyses: List[LabelAnalysis]):
        """Print comprehensive analysis report"""
        print("=" * 80)
        print("SPRING AI TRAINING LABELS ANALYSIS REPORT")
        print("=" * 80)
        print(f"Total unique labels: {len(analyses)}")
        print(f"Total issues analyzed: {len(self.issues)}")
        print("=" * 80)
        
        for analysis in analyses:
            print(f"\n🏷️  LABEL: {analysis.name}")
            print(f"📊 Issue Count: {analysis.count}")
            print("-" * 60)
            
            if analysis.title_patterns:
                print("📝 Common Title Patterns:")
                for i, pattern in enumerate(analysis.title_patterns, 1):
                    print(f"  {i}. {pattern}")
            
            if analysis.body_patterns:
                print("\n📄 Common Body Patterns:")
                for i, pattern in enumerate(analysis.body_patterns, 1):
                    print(f"  {i}. {pattern}")
            
            if analysis.technical_terms:
                print("\n🔧 Technical Terms:")
                print(f"  {', '.join(analysis.technical_terms)}")
            
            if analysis.problem_types:
                print("\n🚨 Problem Types:")
                print(f"  {', '.join(analysis.problem_types)}")
            
            if analysis.example_phrases:
                print("\n💬 Example Phrases:")
                for i, phrase in enumerate(analysis.example_phrases, 1):
                    print(f"  {i}. {phrase}")
            
            if analysis.common_words:
                print("\n📚 Common Words:")
                print(f"  {', '.join(analysis.common_words)}")
            
            print("\n" + "=" * 80)

    def export_to_json(self, analyses: List[LabelAnalysis], output_file: str):
        """Export analysis to JSON file"""
        data = []
        for analysis in analyses:
            data.append({
                'label': analysis.name,
                'count': analysis.count,
                'title_patterns': analysis.title_patterns,
                'body_patterns': analysis.body_patterns,
                'technical_terms': analysis.technical_terms,
                'problem_types': analysis.problem_types,
                'example_phrases': analysis.example_phrases,
                'common_words': analysis.common_words
            })
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Analysis exported to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Analyze Spring AI training labels')
    parser.add_argument('--input', '-i', 
                       default='./issues/stratified_split/train_set.json',
                       help='Input training file path')
    parser.add_argument('--output', '-o',
                       default='label_analysis_report.json',
                       help='Output JSON file path')
    parser.add_argument('--top', '-t', type=int, default=None,
                       help='Show only top N labels by frequency')
    
    args = parser.parse_args()
    
    analyzer = LabelAnalyzer(args.input)
    analyzer.load_issues()
    analyzer.analyze_labels()
    
    analyses = analyzer.generate_analysis_report()
    
    if args.top:
        analyses = analyses[:args.top]
    
    analyzer.print_report(analyses)
    analyzer.export_to_json(analyses, args.output)


if __name__ == '__main__':
    main()
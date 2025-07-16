#!/usr/bin/env python3

import json
import re
from collections import defaultdict, Counter
import sys

def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def classify_issue(issue, enhanced_labels):
    """Classify a single issue based on title and body"""
    issue_number = issue['issue_number']
    title = issue['title']
    body = issue['body']
    
    # Combine title and body for analysis
    text = f"{title} {body}".lower()
    
    predictions = []
    
    # Enhanced label mapping for better classification
    label_keywords = {
        'bug': ['bug', 'error', 'exception', 'fail', 'broken', 'issue', 'problem', 'fix', 'crash', 'npe', 'null pointer', 'timeout', 'infinite recursion'],
        'enhancement': ['enhancement', 'feature', 'improve', 'add', 'support', 'implement', 'extend', 'upgrade'],
        'RAG': ['rag', 'retrieval', 'augment', 'retrievalaugmentationadvisor', 'questionansweradvisor', 'document retriever'],
        'metadata filters': ['filter', 'metadata', 'expression', 'query', 'search'],
        'Observability': ['observability', 'metric', 'telemetry', 'monitoring', 'trace', 'log', 'measurement'],
        'streaming': ['stream', 'streaming', 'reactive', 'flux', 'async'],
        'tool/function calling': ['tool', 'function', 'callback', 'supplier', 'functioncalling'],
        'Bedrock': ['bedrock', 'aws', 'amazon'],
        'MCP': ['mcp', 'model context protocol'],
        'type: backport': ['backport', 'backport of'],
        'status: backported': ['backported'],
        'openai': ['openai', 'gpt', 'chatgpt'],
        'azure': ['azure', 'azureopenai'],
        'anthropic': ['anthropic', 'claude'],
        'ollama': ['ollama'],
        'vector store': ['vector', 'vectorstore', 'similarity', 'embedding'],
        'pgvector': ['pgvector', 'postgres'],
        'pinecone': ['pinecone'],
        'chroma': ['chroma', 'chromadb'],
        'qdrant': ['qdrant'],
        'redis': ['redis'],
        'embedding': ['embedding', 'vector', 'similarity'],
        'chat client': ['chatclient', 'chat client'],
        'advisors': ['advisor', 'advisors'],
        'Chat Memory': ['memory', 'chat memory', 'conversation'],
        'configuration': ['configuration', 'config', 'properties', 'autoconfigure'],
        'documentation': ['documentation', 'doc', 'readme', 'guide'],
        'testing': ['test', 'testing', 'junit'],
        'integration testing': ['integration test'],
        'duplicate': ['duplicate'],
        'question': ['question', 'how to', 'usage'],
        'help wanted': ['help wanted'],
        'good first issue': ['good first issue'],
        'dependencies': ['dependency', 'maven', 'gradle'],
        'security': ['security', 'vulnerability'],
        'performance': ['performance', 'slow', 'timeout'],
        'transcription models': ['transcription', 'audio', 'speech'],
        'image models': ['image', 'vision', 'dall-e'],
        'moderation': ['moderation', 'content filter'],
        'prompt management': ['prompt', 'template'],
        'structured output': ['structured', 'output', 'json', 'pojo'],
        'templating': ['template', 'templating'],
        'retry': ['retry', 'resilience'],
        'client timeouts': ['timeout', 'client'],
        'multimodality': ['multimodal', 'multi-modal'],
        'usability': ['usability', 'user experience', 'ux']
    }
    
    # Check each label
    for label_info in enhanced_labels:
        label = label_info['label']
        confidence = 0.0
        
        # Skip labels not found in codebase
        if label_info['description'] == "Not found in project codebase":
            continue
            
        # Check for direct keyword matches
        if label in label_keywords:
            for keyword in label_keywords[label]:
                if keyword in text:
                    confidence += 0.3
        
        # Check description matches
        desc_words = label_info['description'].lower().split()
        for word in desc_words:
            if len(word) > 3 and word in text:
                confidence += 0.1
        
        # Check example problem phrases
        for phrase in label_info.get('example_problem_phrases', []):
            if phrase.lower() in text:
                confidence += 0.4
        
        # Check typical error patterns
        for pattern in label_info.get('typical_error_patterns', []):
            if pattern.lower() in text:
                confidence += 0.3
        
        # Check relevant modules and packages
        for module in label_info.get('relevant_modules', []):
            if module.lower() in text:
                confidence += 0.2
        
        for package in label_info.get('packages', []):
            if package.lower() in text:
                confidence += 0.2
        
        # Check key classes
        for cls in label_info.get('key_classes', []):
            if cls.lower() in text:
                confidence += 0.2
        
        # Check config keys
        for key in label_info.get('config_keys', []):
            if key.lower() in text:
                confidence += 0.2
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        # Add to predictions if confidence is reasonable
        if confidence > 0.3:
            predictions.append({
                'label': label,
                'confidence': confidence
            })
    
    # Sort by confidence
    predictions.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Apply confidence threshold
    high_confidence_predictions = [p for p in predictions if p['confidence'] >= 0.6]
    
    if not high_confidence_predictions:
        return [{
            'label': 'needs more info',
            'confidence': max([p['confidence'] for p in predictions]) if predictions else 0.3
        }]
    
    return high_confidence_predictions

def classify_all_issues():
    """Classify all issues in the test set"""
    print("Loading data...")
    test_set = load_json('issues/stratified_split/test_set.json')
    enhanced_labels = load_json('github-labels-mapping-enhanced.json')
    
    print(f"Classifying {len(test_set)} issues...")
    
    results = []
    
    for i, issue in enumerate(test_set):
        if i % 10 == 0:
            print(f"Progress: {i}/{len(test_set)} ({i/len(test_set)*100:.1f}%)")
        
        predicted_labels = classify_issue(issue, enhanced_labels)
        
        # Generate explanation
        explanation = f"Issue about '{issue['title']}' - classified based on content analysis"
        if len(predicted_labels) == 1 and predicted_labels[0]['label'] == 'needs more info':
            explanation = "Insufficient information to confidently assign specific labels"
        
        results.append({
            'issue_number': issue['issue_number'],
            'predicted_labels': predicted_labels,
            'explanation': explanation
        })
    
    print("Saving results...")
    with open('results/classified_full_test_set.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def compute_metrics(tp, fp, fn):
    """Compute precision, recall, and F1 score"""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1

def evaluate_full_predictions():
    """Evaluate predictions on full test set"""
    print("Loading evaluation data...")
    predictions = load_json('results/classified_full_test_set.json')
    test_set = load_json('issues/stratified_split/test_set.json')
    valid_labels = set(load_json('labels.json'))
    
    # Create ground truth lookup
    ground_truth = {}
    for issue in test_set:
        ground_truth[issue['issue_number']] = set(issue['labels'])
    
    # Extract predictions
    pred_dict = {}
    for pred in predictions:
        issue_num = pred['issue_number']
        pred_labels = set(label['label'] for label in pred['predicted_labels'])
        pred_dict[issue_num] = pred_labels
    
    # Compute metrics
    all_tp = 0
    all_fp = 0 
    all_fn = 0
    
    label_stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
    
    perfect_predictions = 0
    
    for issue_num in pred_dict:
        if issue_num in ground_truth:
            predicted = pred_dict[issue_num]
            actual = ground_truth[issue_num]
            
            # Filter to only valid labels
            predicted = predicted.intersection(valid_labels)
            actual = actual.intersection(valid_labels)
            
            tp = len(predicted.intersection(actual))
            fp = len(predicted - actual)
            fn = len(actual - predicted)
            
            if tp == len(predicted) and tp == len(actual):
                perfect_predictions += 1
            
            all_tp += tp
            all_fp += fp
            all_fn += fn
            
            # Update per-label stats
            for label in predicted:
                if label in actual:
                    label_stats[label]['tp'] += 1
                else:
                    label_stats[label]['fp'] += 1
            
            for label in actual:
                if label not in predicted:
                    label_stats[label]['fn'] += 1
    
    # Compute overall metrics
    micro_precision, micro_recall, micro_f1 = compute_metrics(all_tp, all_fp, all_fn)
    
    # Compute per-label metrics
    label_metrics = []
    for label, stats in label_stats.items():
        if stats['tp'] + stats['fp'] + stats['fn'] > 0:
            precision, recall, f1 = compute_metrics(stats['tp'], stats['fp'], stats['fn'])
            support = stats['tp'] + stats['fn']
            label_metrics.append((label, precision, recall, f1, support))
    
    # Sort by support
    label_metrics.sort(key=lambda x: x[4], reverse=True)
    
    # Compute macro averages
    macro_precision = sum(x[1] for x in label_metrics) / len(label_metrics) if label_metrics else 0
    macro_recall = sum(x[2] for x in label_metrics) / len(label_metrics) if label_metrics else 0
    macro_f1 = sum(x[3] for x in label_metrics) / len(label_metrics) if label_metrics else 0
    
    return {
        'micro_precision': micro_precision,
        'micro_recall': micro_recall,
        'micro_f1': micro_f1,
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'macro_f1': macro_f1,
        'label_metrics': label_metrics,
        'perfect_predictions': perfect_predictions,
        'total_issues': len(pred_dict),
        'total_predictions': sum(len(pred_dict[issue]) for issue in pred_dict),
        'total_ground_truth': sum(len(ground_truth[issue]) for issue in pred_dict if issue in ground_truth)
    }

def generate_markdown_report():
    """Generate comprehensive markdown report"""
    print("Generating markdown report...")
    
    # Load results
    results = evaluate_full_predictions()
    predictions = load_json('results/classified_full_test_set.json')
    
    # Generate markdown
    markdown = f"""# Multi-Label Classification Results - Full Test Set

## Summary Statistics

- **Total Issues Evaluated**: {results['total_issues']}
- **Perfect Predictions**: {results['perfect_predictions']} ({results['perfect_predictions']/results['total_issues']*100:.1f}%)
- **Total Predictions Made**: {results['total_predictions']}
- **Total Ground Truth Labels**: {results['total_ground_truth']}
- **Average Predictions per Issue**: {results['total_predictions']/results['total_issues']:.1f}
- **Average Ground Truth per Issue**: {results['total_ground_truth']/results['total_issues']:.1f}

## Overall Performance Metrics

### Micro-Averaged Metrics
- **Precision**: {results['micro_precision']:.3f}
- **Recall**: {results['micro_recall']:.3f}
- **F1 Score**: {results['micro_f1']:.3f}

### Macro-Averaged Metrics
- **Precision**: {results['macro_precision']:.3f}
- **Recall**: {results['macro_recall']:.3f}
- **F1 Score**: {results['macro_f1']:.3f}

## Per-Label Performance

| Label | Precision | Recall | F1 Score | Support |
|-------|-----------|---------|----------|---------|
"""
    
    for label, precision, recall, f1, support in results['label_metrics'][:20]:  # Top 20 labels
        markdown += f"| {label} | {precision:.3f} | {recall:.3f} | {f1:.3f} | {support} |\n"
    
    markdown += f"""
## Top 10 Most Frequent Labels (Ground Truth)

"""
    
    for i, (label, precision, recall, f1, support) in enumerate(results['label_metrics'][:10]):
        markdown += f"{i+1}. **{label}**: {support} occurrences (P: {precision:.3f}, R: {recall:.3f}, F1: {f1:.3f})\n"
    
    markdown += f"""
## Classification Analysis

### Strong Performers (F1 > 0.8)
"""
    
    strong_performers = [x for x in results['label_metrics'] if x[3] > 0.8]
    for label, precision, recall, f1, support in strong_performers:
        markdown += f"- **{label}**: F1 = {f1:.3f} (P: {precision:.3f}, R: {recall:.3f}, Support: {support})\n"
    
    markdown += f"""
### Challenging Labels (F1 < 0.5)
"""
    
    challenging = [x for x in results['label_metrics'] if x[3] < 0.5]
    for label, precision, recall, f1, support in challenging:
        markdown += f"- **{label}**: F1 = {f1:.3f} (P: {precision:.3f}, R: {recall:.3f}, Support: {support})\n"
    
    markdown += f"""
## Sample Predictions

### Perfect Predictions (showing first 5)
"""
    
    # Find some perfect predictions
    test_set = load_json('issues/stratified_split/test_set.json')
    ground_truth = {issue['issue_number']: set(issue['labels']) for issue in test_set}
    
    perfect_count = 0
    for pred in predictions:
        if perfect_count >= 5:
            break
        issue_num = pred['issue_number']
        predicted = set(label['label'] for label in pred['predicted_labels'])
        actual = ground_truth.get(issue_num, set())
        
        if predicted == actual and len(predicted) > 0:
            perfect_count += 1
            markdown += f"""
**Issue #{issue_num}**
- Predicted: {sorted(predicted)}
- Actual: {sorted(actual)}
- Match: ✅ Perfect
"""
    
    markdown += f"""
### Challenging Predictions (showing first 5)
"""
    
    # Find some challenging predictions
    challenging_count = 0
    for pred in predictions:
        if challenging_count >= 5:
            break
        issue_num = pred['issue_number']
        predicted = set(label['label'] for label in pred['predicted_labels'])
        actual = ground_truth.get(issue_num, set())
        
        # Calculate metrics for this prediction
        tp = len(predicted.intersection(actual))
        fp = len(predicted - actual)
        fn = len(actual - predicted)
        
        if fp > 0 or fn > 0:  # Not perfect
            challenging_count += 1
            precision, recall, f1 = compute_metrics(tp, fp, fn)
            markdown += f"""
**Issue #{issue_num}**
- Predicted: {sorted(predicted)}
- Actual: {sorted(actual)}
- Metrics: P={precision:.3f}, R={recall:.3f}, F1={f1:.3f}
- TP: {tp}, FP: {fp}, FN: {fn}
"""
    
    markdown += f"""
## Methodology

This multi-label classification was performed using Claude AI with the following approach:

1. **Feature Engineering**: Combined issue title and body text
2. **Label Matching**: Used enhanced label mappings with:
   - Direct keyword matching
   - Description word matching
   - Example problem phrase matching
   - Module/package/class name matching
   - Configuration key matching
3. **Confidence Scoring**: Weighted scoring system with threshold of 0.6
4. **Fallback Strategy**: Issues with all confidence scores < 0.6 assigned "needs more info"

## Data Sources

- **Test Set**: `issues/stratified_split/test_set.json` ({results['total_issues']} issues)
- **Label Mapping**: `github-labels-mapping-enhanced.json` (enhanced with training data insights)
- **Valid Labels**: `labels.json` (official GitHub labels)

## Files Generated

- `results/classified_full_test_set.json`: Complete predictions for all test issues
- `results/evaluation_results.md`: This comprehensive report
"""
    
    # Save markdown report
    with open('results/evaluation_results.md', 'w') as f:
        f.write(markdown)
    
    print("Report saved to results/evaluation_results.md")

if __name__ == "__main__":
    # Classify all issues
    classify_all_issues()
    
    # Generate comprehensive report
    generate_markdown_report()
    
    print("\n✅ Full evaluation complete!")
    print("📁 Results saved in 'results/' directory:")
    print("   - classified_full_test_set.json")
    print("   - evaluation_results.md")
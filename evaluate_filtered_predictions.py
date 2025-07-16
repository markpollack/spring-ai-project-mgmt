#!/usr/bin/env python3

import json
from collections import defaultdict, Counter
import sys

def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def compute_metrics(tp, fp, fn):
    """Compute precision, recall, and F1 score"""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1

def evaluate_filtered_predictions(exclude_labels=None):
    # Load data
    predictions = load_json('conservative_full_classification.json')
    test_set = load_json('issues/stratified_split/test_set.json')
    valid_labels = set(load_json('labels.json'))
    
    # Define problematic labels to exclude
    if exclude_labels is None:
        # Default exclusion list with expanded categories
        exclude_labels = {
            # Original problematic labels
            'bug', 'enhancement',
            # Subjective/Judgmental labels
            'question', 'help wanted', 'good first issue', 'epic',
            # Process-Driven labels
            'status: backported', 'status: to-discuss', 'follow up', 
            'status: waiting-for-feedback', 'for: backport-to-1.0.x', 'next priorities'
        }
    
    problematic_labels = set(exclude_labels)
    
    # Create ground truth lookup
    ground_truth = {}
    for issue in test_set:
        # Filter out problematic labels from ground truth
        filtered_labels = set(issue['labels']) - problematic_labels
        ground_truth[issue['issue_number']] = filtered_labels
    
    # Extract predictions for all 111 issues we classified
    pred_dict = {}
    for pred in predictions:
        issue_num = pred['issue_number']
        # Filter out problematic labels from predictions
        pred_labels = set(label['label'] for label in pred['predicted_labels']) - problematic_labels
        pred_dict[issue_num] = pred_labels
    
    print("=== FILTERED EVALUATION RESULTS ===")
    print(f"(Excluding {len(problematic_labels)} labels: {', '.join(sorted(problematic_labels))})")
    print()
    
    all_tp = 0
    all_fp = 0 
    all_fn = 0
    
    label_stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
    
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
    
    # Overall micro-averaged metrics
    print("MICRO-AVERAGED METRICS:")
    print("-" * 30)
    micro_precision, micro_recall, micro_f1 = compute_metrics(all_tp, all_fp, all_fn)
    print(f"Precision: {micro_precision:.3f}")
    print(f"Recall: {micro_recall:.3f}")
    print(f"F1 Score: {micro_f1:.3f}")
    print()
    
    # Per-label metrics (top 10 by frequency)
    print("PER-LABEL METRICS (Top 10 by frequency):")
    print("-" * 60)
    
    label_metrics = []
    for label, stats in label_stats.items():
        if stats['tp'] + stats['fp'] + stats['fn'] > 0:  # Only labels that appeared
            precision, recall, f1 = compute_metrics(stats['tp'], stats['fp'], stats['fn'])
            label_metrics.append((label, precision, recall, f1, stats['tp'] + stats['fn']))  # Last item is support
    
    # Sort by support (frequency in ground truth)
    label_metrics.sort(key=lambda x: x[4], reverse=True)
    
    print(f"{'Label':<20} {'Precision':<10} {'Recall':<10} {'F1':<10} {'Support':<10}")
    print("-" * 60)
    
    macro_precision = 0
    macro_recall = 0
    macro_f1 = 0
    
    # Show top 10 labels by frequency
    top_10_labels = label_metrics[:10]
    for label, precision, recall, f1, support in top_10_labels:
        print(f"{label:<20} {precision:<10.3f} {recall:<10.3f} {f1:<10.3f} {support:<10}")
    
    # Show complete label table
    print()
    print("COMPLETE LABEL METRICS (All Labels):")
    print("-" * 80)
    print(f"{'Label':<25} {'Precision':<11} {'Recall':<11} {'F1':<11} {'Support':<11}")
    print("-" * 80)
    
    for label, precision, recall, f1, support in label_metrics:
        print(f"{label:<25} {precision:<11.3f} {recall:<11.3f} {f1:<11.3f} {support:<11}")
    
    # Calculate macro average using ALL labels (not just top 10)
    for label, precision, recall, f1, support in label_metrics:
        macro_precision += precision
        macro_recall += recall
        macro_f1 += f1
    
    # Macro-averaged metrics
    num_labels = len(label_metrics)
    if num_labels > 0:
        macro_precision /= num_labels
        macro_recall /= num_labels
        macro_f1 /= num_labels
    
    print()
    print("MACRO-AVERAGED METRICS:")
    print("-" * 30)
    print(f"Precision: {macro_precision:.3f}")
    print(f"Recall: {macro_recall:.3f}")
    print(f"F1 Score: {macro_f1:.3f}")
    print()
    
    # Summary statistics
    print("SUMMARY STATISTICS:")
    print("-" * 30)
    print(f"Total issues evaluated: {len(pred_dict)}")
    print(f"Total predictions made: {sum(len(pred_dict[issue]) for issue in pred_dict)}")
    print(f"Total ground truth labels: {sum(len(ground_truth[issue]) for issue in pred_dict if issue in ground_truth)}")
    print(f"Total unique labels predicted: {len(set().union(*pred_dict.values()))}")
    print(f"Total unique labels in ground truth: {len(set().union(*[ground_truth[issue] for issue in pred_dict if issue in ground_truth]))}")
    
    print()
    print("EXCLUDED LABELS:")
    print("-" * 30)
    
    # Group excluded labels by category
    original_labels = {'bug', 'enhancement'}
    subjective_labels = {'question', 'help wanted', 'good first issue', 'epic'}
    process_labels = {'status: backported', 'status: to-discuss', 'follow up', 
                     'status: waiting-for-feedback', 'for: backport-to-1.0.x', 'next priorities'}
    
    if original_labels.intersection(problematic_labels):
        print("Original problematic labels:")
        for label in sorted(original_labels.intersection(problematic_labels)):
            print(f"  - {label}")
    
    if subjective_labels.intersection(problematic_labels):
        print("Subjective/Judgmental labels:")
        for label in sorted(subjective_labels.intersection(problematic_labels)):
            print(f"  - {label}")
    
    if process_labels.intersection(problematic_labels):
        print("Process-Driven labels:")
        for label in sorted(process_labels.intersection(problematic_labels)):
            print(f"  - {label}")
    
    # Any other excluded labels
    other_labels = problematic_labels - original_labels - subjective_labels - process_labels
    if other_labels:
        print("Other excluded labels:")
        for label in sorted(other_labels):
            print(f"  - {label}")
    
    return {
        'micro_precision': micro_precision,
        'micro_recall': micro_recall,
        'micro_f1': micro_f1,
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'macro_f1': macro_f1,
        'label_metrics': label_metrics,
        'top_10_labels': top_10_labels,
        'total_issues': len(pred_dict),
        'total_predictions': sum(len(pred_dict[issue]) for issue in pred_dict),
        'total_ground_truth': sum(len(ground_truth[issue]) for issue in pred_dict if issue in ground_truth),
        'unique_predicted': len(set().union(*pred_dict.values())),
        'unique_ground_truth': len(set().union(*[ground_truth[issue] for issue in pred_dict if issue in ground_truth])),
        'excluded_labels': problematic_labels
    }

if __name__ == "__main__":
    evaluate_filtered_predictions()
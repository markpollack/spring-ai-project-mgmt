#!/usr/bin/env python3

import json
import sys
from typing import List, Dict, Any

def load_json(filename: str) -> Any:
    """Load JSON file efficiently"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_issue_batch(test_set: List[Dict], start_idx: int, batch_size: int = 25) -> List[Dict]:
    """Extract a batch of issues with only necessary fields"""
    batch = []
    end_idx = min(start_idx + batch_size, len(test_set))
    
    for i in range(start_idx, end_idx):
        issue = test_set[i]
        # Extract only the fields needed for classification
        batch.append({
            'issue_number': issue['issue_number'],
            'title': issue['title'],
            'body': issue['body'],
            'labels': issue.get('labels', [])  # Keep for reference but don't use in classification
        })
    
    return batch

def get_high_performing_labels() -> List[str]:
    """Return list of labels that performed well in previous evaluation"""
    return [
        'vector store',
        'tool/function calling', 
        'documentation',
        'type: backport',
        'MCP',
        'design',
        'Bedrock',
        'model client',
        'RAG',
        'OpenAI',
        'Anthropic',
        'Azure',
        'Ollama',
        'configuration',
        'security',
        'performance',
        'testing',
        'API',
        'integration',
        'streaming',
        'embeddings',
        'metadata',
        'error handling',
        'logging',
        'observability'
    ]

def print_batch_summary(batch: List[Dict], batch_num: int):
    """Print summary of current batch for Claude to process"""
    print(f"\n=== BATCH {batch_num} ===")
    print(f"Issues {batch[0]['issue_number']} to {batch[-1]['issue_number']} ({len(batch)} issues)")
    print("\nHigh-performing labels to consider:")
    labels = get_high_performing_labels()
    for i, label in enumerate(labels[:15]):  # Show first 15 labels
        print(f"  {i+1:2d}. {label}")
    if len(labels) > 15:
        print(f"  ... and {len(labels)-15} more")
    
    print(f"\nIssues in this batch:")
    for issue in batch:
        title_preview = issue['title'][:60] + "..." if len(issue['title']) > 60 else issue['title']
        print(f"  #{issue['issue_number']}: {title_preview}")

def process_classification_batch(batch_num: int, batch_size: int = 25):
    """Process a specific batch of issues for classification"""
    try:
        # Load the test set
        test_set = load_json('issues/stratified_split/test_set.json')
        
        # Calculate batch boundaries
        start_idx = (batch_num - 1) * batch_size
        if start_idx >= len(test_set):
            print(f"Batch {batch_num} is beyond available data. Total issues: {len(test_set)}")
            return
        
        # Extract batch
        batch = extract_issue_batch(test_set, start_idx, batch_size)
        
        # Print summary for Claude
        print_batch_summary(batch, batch_num)
        
        # Output the batch data in a format Claude can easily process
        print(f"\n=== BATCH {batch_num} DATA ===")
        for issue in batch:
            print(f"\nIssue #{issue['issue_number']}:")
            print(f"Title: {issue['title']}")
            print(f"Body: {issue['body'][:500]}{'...' if len(issue['body']) > 500 else ''}")
            print("-" * 50)
        
    except FileNotFoundError:
        print("Error: issues/stratified_split/test_set.json not found")
    except json.JSONDecodeError:
        print("Error: Invalid JSON in test_set.json")
    except Exception as e:
        print(f"Error processing batch: {e}")

def get_batch_info():
    """Get information about available batches"""
    try:
        test_set = load_json('issues/stratified_split/test_set.json')
        total_issues = len(test_set)
        batch_size = 25
        total_batches = (total_issues + batch_size - 1) // batch_size
        
        print(f"Total issues: {total_issues}")
        print(f"Batch size: {batch_size}")
        print(f"Total batches: {total_batches}")
        print(f"Last batch size: {total_issues % batch_size or batch_size}")
        
        return total_batches
    except Exception as e:
        print(f"Error getting batch info: {e}")
        return 0

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python batch_processor.py info        # Get batch information")
        print("  python batch_processor.py batch N     # Process batch N")
        print("  python batch_processor.py labels      # Show high-performing labels")
        return
    
    command = sys.argv[1]
    
    if command == "info":
        get_batch_info()
    elif command == "batch" and len(sys.argv) >= 3:
        try:
            batch_num = int(sys.argv[2])
            process_classification_batch(batch_num)
        except ValueError:
            print("Error: Batch number must be an integer")
    elif command == "labels":
        labels = get_high_performing_labels()
        print("High-performing labels to focus on:")
        for i, label in enumerate(labels, 1):
            print(f"  {i:2d}. {label}")
    else:
        print("Invalid command. Use 'info', 'batch N', or 'labels'")

if __name__ == "__main__":
    main()
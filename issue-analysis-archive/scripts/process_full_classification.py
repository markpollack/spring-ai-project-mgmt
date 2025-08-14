#!/usr/bin/env python3

import json
import sys

def load_test_set():
    """Load the complete test set"""
    with open('issues/stratified_split/test_set.json', 'r') as f:
        return json.load(f)

def extract_issue_data(issues):
    """Extract just the needed data for classification"""
    extracted = []
    for issue in issues:
        extracted.append({
            'issue_number': issue['issue_number'],
            'title': issue['title'],
            'body': issue['body']
        })
    return extracted

def save_extracted_data(data, filename):
    """Save extracted data to a file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    print("Loading test set...")
    issues = load_test_set()
    print(f"Found {len(issues)} issues")
    
    print("Extracting issue data for classification...")
    extracted = extract_issue_data(issues)
    
    print("Saving extracted data...")
    save_extracted_data(extracted, 'test_issues_for_classification.json')
    
    print(f"✅ Created test_issues_for_classification.json with {len(extracted)} issues")
    print("This file contains only issue_number, title, and body for efficient classification.")
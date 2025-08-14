
import json
import random
from collections import Counter
import os

# Constants
IGNORED_LABELS = {
    "triage", "duplicate", "invalid", "status: waiting-for-triage",
    "status: waiting-for-feedback", "status: backported", "follow up"
}

LABEL_GROUPS = {
    "vector store": {"pinecone", "qdrant", "weaviate", "typesense", "opensearch", "chromadb", "pgvector", "milvus"},
    "model client": {"openai", "claude", "ollama", "gemini", "deepseek", "mistral", "moonshot", "zhipu"},
    "data store": {"mongo", "oracle", "neo4j", "cassandra", "mariadb", "postgresml", "elastic search", "coherence"},
}

def normalize_labels(labels):
    normalized = set()
    for label in labels:
        lower_label = label.strip().lower()
        if lower_label in IGNORED_LABELS:
            continue
        grouped = False
        for group_name, group_members in LABEL_GROUPS.items():
            if lower_label in group_members:
                normalized.add(group_name)
                grouped = True
                break
        if not grouped:
            normalized.add(lower_label)
    return list(normalized) if normalized else None

def label_distribution(issues):
    counter = Counter()
    for issue in issues:
        counter.update(issue["normalized_labels"])
    return dict(counter)

def main():
    # Define file paths
    analysis_dir = "issues/analysis"
    issues_file = os.path.join(analysis_dir, "issues_analysis_ready.json")
    data_dict_file = os.path.join(analysis_dir, "data_dictionary.json")
    labels_file = "labels.json"  # This file is in the root directory
    
    # Check if files exist
    if not os.path.exists(issues_file):
        print(f"Error: {issues_file} not found. Please run quick_analysis_extract.sh first.")
        return
    
    if not os.path.exists(data_dict_file):
        print(f"Error: {data_dict_file} not found. Please run quick_analysis_extract.sh first.")
        return
        
    if not os.path.exists(labels_file):
        print(f"Error: {labels_file} not found. Please create this file or run fetch_labels.sh first.")
        return
    
    # Load files
    with open(issues_file, "r") as f:
        issues_data = json.load(f)

    with open(data_dict_file, "r") as f:
        data_dictionary = json.load(f)

    with open(labels_file, "r") as f:
        all_labels = json.load(f)

    # Normalize and filter
    stratified_issues = []
    for issue in issues_data:
        labels = issue.get("labels", [])
        norm_labels = normalize_labels(labels)
        if norm_labels:
            issue["normalized_labels"] = norm_labels
            stratified_issues.append(issue)

    # Count frequencies
    label_counts_total = Counter(label for issue in stratified_issues for label in issue["normalized_labels"])
    rare_labels = {label for label, count in label_counts_total.items() if count < 3}

    # Heuristic split
    train_set, test_set = [], []
    test_label_counts = Counter()

    random.seed(42)
    random.shuffle(stratified_issues)

    for issue in stratified_issues:
        labels = issue["normalized_labels"]
        if any(label in rare_labels for label in labels):
            train_set.append(issue)
            continue
        if all(test_label_counts[label] < (0.2 * label_counts_total[label]) for label in labels):
            test_set.append(issue)
            test_label_counts.update(labels)
        else:
            train_set.append(issue)

    # Save output to separate directory
    output_dir = "issues/stratified_split"
    os.makedirs(output_dir, exist_ok=True)
    
    train_file = os.path.join(output_dir, "train_set.json")
    test_file = os.path.join(output_dir, "test_set.json")
    
    with open(train_file, "w") as f:
        json.dump(train_set, f, indent=2)

    with open(test_file, "w") as f:
        json.dump(test_set, f, indent=2)

    # Print summary
    train_dist = label_distribution(train_set)
    test_dist = label_distribution(test_set)
    
    print("=== Stratified Split Results ===")
    print(f"Output directory: {output_dir}")
    print(f"Train set file: {train_file}")
    print(f"Test set file: {test_file}")
    print()
    print("Total issues used:", len(stratified_issues))
    print("Train set size:", len(train_set))
    print("Test set size:", len(test_set))
    print(f"Split ratio: {len(train_set)}/{len(test_set)} ({len(train_set)/len(stratified_issues)*100:.1f}%/{len(test_set)/len(stratified_issues)*100:.1f}%)")
    print()
    print("Train label distribution:")
    for k, v in sorted(train_dist.items()):
        print(f"  {k}: {v}")
    print()
    print("Test label distribution:")
    for k, v in sorted(test_dist.items()):
        print(f"  {k}: {v}")
    print()
    print("✅ Stratified split completed successfully!")

if __name__ == "__main__":
    main()

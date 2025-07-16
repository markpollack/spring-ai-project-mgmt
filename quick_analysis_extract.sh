#!/usr/bin/env bash

# Quick Analysis Data Extraction Script
# Extracts key data from collected issues for ChatGPT analysis

set -euo pipefail

OUTPUT_DIR="issues/analysis"
INPUT_DIR="issues/raw/closed"
FILTER_NO_LABELS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --filter-no-labels)
            FILTER_NO_LABELS=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --filter-no-labels    Filter out issues that have no labels"
            echo "  --help, -h           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "Creating analysis directory..."
mkdir -p "$OUTPUT_DIR"

echo "Cleaning output directory..."
rm -f "$OUTPUT_DIR"/*

echo "Extracting issue data..."

# Extract key analysis data using simple jq
cat > "$OUTPUT_DIR/extract_issues.jq" << 'EOF'
[.issues[] | {
  issue_number: .number,
  title: .title,
  body: .body,
  author: .author.login,
  state: .state,
  created_at: .createdAt,
  closed_at: .closedAt,
  days_open: (if .closedAt and .createdAt then 
    (((.closedAt | fromdateiso8601) - (.createdAt | fromdateiso8601)) / 86400) | floor
  else 0 end),
  labels: [.labels[]?.name],
  assignees: [.assignees[]?.login],
  milestone: (.milestone.title // null),
  comment_count: (.comments | length),
  comment_authors: ([.comments[]?.author.login] | unique),
  has_reactions: (.comments | map(.reactions.totalCount // 0) | add > 0),
  metrics: {
    comment_count: (.comments | length),
    label_count: (.labels | length),
    assignee_count: (.assignees | length),
    body_length: (.body | length),
    has_reactions: (.comments | map(.reactions.totalCount // 0) | add > 0)
  }
}]
EOF

# Process all batch files
echo "Processing batch files..."
batch_files=($(find "$INPUT_DIR" -name "issues_batch_*.json" | sort))

echo "Found ${#batch_files[@]} batch files"

# Process all files and combine into single array
echo "Extracting and combining issues..."
temp_files=()
for file in "${batch_files[@]}"; do
    echo "Processing $(basename "$file")..."
    temp_file="$OUTPUT_DIR/temp_$(basename "$file")"
    jq -f "$OUTPUT_DIR/extract_issues.jq" "$file" > "$temp_file"
    temp_files+=("$temp_file")
done

# Combine all extracted issues into single array
echo "Combining all issues..."
jq -s 'add' "${temp_files[@]}" > "$OUTPUT_DIR/issues_analysis_temp.json"

# Apply label filtering if requested
if [[ "$FILTER_NO_LABELS" == true ]]; then
    echo "Filtering out issues with no labels..."
    BEFORE_FILTER=$(jq 'length' "$OUTPUT_DIR/issues_analysis_temp.json")
    jq 'map(select(.labels | length > 0))' "$OUTPUT_DIR/issues_analysis_temp.json" > "$OUTPUT_DIR/issues_analysis_ready.json"
    AFTER_FILTER=$(jq 'length' "$OUTPUT_DIR/issues_analysis_ready.json")
    echo "Filtered: $BEFORE_FILTER issues → $AFTER_FILTER issues (removed $((BEFORE_FILTER - AFTER_FILTER)) issues with no labels)"
else
    mv "$OUTPUT_DIR/issues_analysis_temp.json" "$OUTPUT_DIR/issues_analysis_ready.json"
fi

# Clean up temp files
rm -f "${temp_files[@]}"
rm -f "$OUTPUT_DIR/issues_analysis_temp.json"

# Clean up
rm -f "$OUTPUT_DIR/extract_issues.jq"

# Create simple data dictionary
cat > "$OUTPUT_DIR/data_dictionary.json" << EOF
{
  "description": "Spring AI GitHub Issues Analysis Dataset",
  "filtering": {
    "no_labels_filtered": $FILTER_NO_LABELS,
    "note": "Issues with no labels may be excluded if filtering was enabled"
  },
  "fields": {
    "issue_number": "GitHub issue number",
    "title": "Issue title",
    "body": "Issue description",
    "author": "Issue author username",
    "state": "Issue state (CLOSED)",
    "created_at": "Issue creation timestamp",
    "closed_at": "Issue closure timestamp",
    "days_open": "Days between creation and closure",
    "labels": "Array of label names",
    "assignees": "Array of assignee usernames",
    "milestone": "Milestone title",
    "comment_count": "Number of comments",
    "comment_authors": "Unique usernames who commented",
    "has_reactions": "Whether comments have reactions",
    "metrics": "Additional calculated metrics"
  }
}
EOF

# Create ZIP for ChatGPT
echo "Creating ZIP package..."
cd "$OUTPUT_DIR"
zip -q github_issues_analysis.zip issues_analysis_ready.json data_dictionary.json
cd - > /dev/null

# Validation
echo
echo "=== Validation ==="

# Check if metadata file exists to get expected count
EXPECTED_COUNT=0
if [[ -f "$INPUT_DIR/metadata.json" ]]; then
    EXPECTED_COUNT=$(jq -r '.collection_stats.total_issues // 0' "$INPUT_DIR/metadata.json" 2>/dev/null || echo "0")
    echo "Expected issues from metadata: $EXPECTED_COUNT"
fi

# Validate the analysis file
if [[ -f "$OUTPUT_DIR/issues_analysis_ready.json" ]]; then
    ACTUAL_COUNT=$(jq 'length' "$OUTPUT_DIR/issues_analysis_ready.json" 2>/dev/null || echo "0")
    echo "Extracted issues: $ACTUAL_COUNT"
    
    # Check for duplicates
    DUPLICATE_COUNT=$(jq 'group_by(.issue_number) | map(length) | max' "$OUTPUT_DIR/issues_analysis_ready.json" 2>/dev/null || echo "0")
    echo "Max duplicates per issue: $DUPLICATE_COUNT"
    
    # Check if counts match (accounting for filtering)
    if [[ "$FILTER_NO_LABELS" == true ]]; then
        echo "⚠️  Count validation: SKIPPED (filtering enabled - count expected to be different)"
    elif [[ "$EXPECTED_COUNT" -gt 0 && "$ACTUAL_COUNT" -eq "$EXPECTED_COUNT" ]]; then
        echo "✅ Count validation: PASSED"
    elif [[ "$EXPECTED_COUNT" -gt 0 ]]; then
        echo "❌ Count validation: FAILED (expected $EXPECTED_COUNT, got $ACTUAL_COUNT)"
    else
        echo "⚠️  Count validation: SKIPPED (no metadata found)"
    fi
    
    # Check for duplicates
    if [[ "$DUPLICATE_COUNT" -eq 1 ]]; then
        echo "✅ Duplicate validation: PASSED"
    else
        echo "❌ Duplicate validation: FAILED (max duplicates: $DUPLICATE_COUNT)"
    fi
    
    # Validate JSON structure
    SAMPLE_ISSUE=$(jq '.[0]' "$OUTPUT_DIR/issues_analysis_ready.json" 2>/dev/null)
    if [[ $? -eq 0 && -n "$SAMPLE_ISSUE" ]]; then
        # Check required fields
        REQUIRED_FIELDS=("issue_number" "title" "author" "state" "created_at" "closed_at" "comment_count" "metrics")
        MISSING_FIELDS=()
        
        for field in "${REQUIRED_FIELDS[@]}"; do
            if ! echo "$SAMPLE_ISSUE" | jq -e ".$field" >/dev/null 2>&1; then
                MISSING_FIELDS+=("$field")
            fi
        done
        
        if [[ ${#MISSING_FIELDS[@]} -eq 0 ]]; then
            echo "✅ Structure validation: PASSED"
        else
            echo "❌ Structure validation: FAILED (missing fields: ${MISSING_FIELDS[*]})"
        fi
    else
        echo "❌ Structure validation: FAILED (invalid JSON or empty array)"
    fi
else
    echo "❌ Analysis file not found"
fi

echo "=================="

# Show results
echo
echo "=== Analysis Data Ready ==="
echo "Files created:"

# List files that exist
if compgen -G "$OUTPUT_DIR/*.json" > /dev/null; then
    ls -lh "$OUTPUT_DIR"/*.json
fi

if compgen -G "$OUTPUT_DIR/*.zip" > /dev/null; then
    ls -lh "$OUTPUT_DIR"/*.zip
fi

echo
if [[ -f "$OUTPUT_DIR/issues_analysis_ready.json" ]]; then
    echo "Total issues: $(jq 'length' "$OUTPUT_DIR/issues_analysis_ready.json" 2>/dev/null || echo "unknown")"
    echo "Dataset size: $(du -h "$OUTPUT_DIR/issues_analysis_ready.json" | cut -f1)"
fi

if [[ -f "$OUTPUT_DIR/github_issues_analysis.zip" ]]; then
    echo "ZIP size: $(du -h "$OUTPUT_DIR/github_issues_analysis.zip" | cut -f1)"
    echo
    
    # Final validation summary
    if [[ "$FILTER_NO_LABELS" == true ]]; then
        # When filtering is enabled, only check duplicates and structure
        if [[ "$DUPLICATE_COUNT" -eq 1 ]]; then
            echo "✅ All validations passed - Ready for ChatGPT analysis!"
            echo "📤 Upload: $OUTPUT_DIR/github_issues_analysis.zip"
        else
            echo "⚠️  Some validations failed - Please review output above"
            echo "📤 Upload: $OUTPUT_DIR/github_issues_analysis.zip (use with caution)"
            exit 1
        fi
    elif [[ "$EXPECTED_COUNT" -gt 0 && "$ACTUAL_COUNT" -eq "$EXPECTED_COUNT" && "$DUPLICATE_COUNT" -eq 1 ]]; then
        echo "✅ All validations passed - Ready for ChatGPT analysis!"
        echo "📤 Upload: $OUTPUT_DIR/github_issues_analysis.zip"
    else
        echo "⚠️  Some validations failed - Please review output above"
        echo "📤 Upload: $OUTPUT_DIR/github_issues_analysis.zip (use with caution)"
        exit 1
    fi
else
    echo "❌ ZIP file not created"
    exit 1
fi
echo "=========================="
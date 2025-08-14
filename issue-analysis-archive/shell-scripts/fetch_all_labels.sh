#!/usr/bin/env bash

# Script to fetch ALL labels from spring-projects/spring-ai repository using GraphQL
# This ensures we get all labels without pagination limits

set -Eeuo pipefail

# Configuration
REPO_OWNER="spring-projects"
REPO_NAME="spring-ai"
OUTPUT_FILE="labels.json"
TEMP_FILE=$(mktemp)

# Cleanup function
cleanup() {
    rm -f "$TEMP_FILE"
}

# Set trap for cleanup
trap cleanup EXIT

# Logging functions
info() {
    echo "[INFO] $*" >&2
}

warn() {
    echo "[WARN] $*" >&2
}

error() {
    echo "[ERROR] $*" >&2
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Fetch ALL labels from the Spring AI project using GraphQL and update labels.json

OPTIONS:
    -h, --help          Show this help message
    -o, --output FILE   Output file (default: labels.json)
    --owner OWNER       Repository owner (default: spring-projects)
    --repo REPO         Repository name (default: spring-ai)
    --version           Show version information

EXAMPLES:
    $0                              # Fetch all labels and update labels.json
    $0 -o all_labels.json           # Save to custom file
    $0 --owner owner --repo repo    # Fetch from different repository

EOF
}

# Version function
version() {
    echo "fetch_all_labels.sh 1.0.0"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        --version)
            version
            exit 0
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --owner)
            REPO_OWNER="$2"
            shift 2
            ;;
        --repo)
            REPO_NAME="$2"
            shift 2
            ;;
        *)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate dependencies
if ! command -v gh &> /dev/null; then
    error "GitHub CLI (gh) is not installed or not in PATH"
    exit 1
fi

# Check if authenticated with GitHub
if ! gh auth status &> /dev/null; then
    error "Not authenticated with GitHub. Run 'gh auth login' first"
    exit 1
fi

# GraphQL query to fetch all labels with pagination
fetch_all_labels() {
    info "Fetching all labels from repository: $REPO_OWNER/$REPO_NAME using GraphQL"
    
    local cursor=""
    local has_next_page=true
    local all_labels=()
    
    while [[ "$has_next_page" == "true" ]]; do
        info "Fetching labels batch..." 
        
        # Build GraphQL query with cursor for pagination
        local query_file=$(mktemp)
        
        if [[ -z "$cursor" ]]; then
            cat > "$query_file" <<EOF
{
  "query": "query(\$owner: String!, \$name: String!) { repository(owner: \$owner, name: \$name) { labels(first: 100) { pageInfo { hasNextPage endCursor } nodes { name } } } }",
  "variables": {
    "owner": "$REPO_OWNER",
    "name": "$REPO_NAME"
  }
}
EOF
        else
            cat > "$query_file" <<EOF
{
  "query": "query(\$owner: String!, \$name: String!, \$cursor: String!) { repository(owner: \$owner, name: \$name) { labels(first: 100, after: \$cursor) { pageInfo { hasNextPage endCursor } nodes { name } } } }",
  "variables": {
    "owner": "$REPO_OWNER",
    "name": "$REPO_NAME",
    "cursor": "$cursor"
  }
}
EOF
        fi
        
        # Execute GraphQL query
        local response
        if ! response=$(gh api graphql --input "$query_file"); then
            rm -f "$query_file"
            error "Failed to fetch labels using GraphQL"
            exit 1
        fi
        
        rm -f "$query_file"
        
        # Extract labels from response
        local batch_labels
        batch_labels=$(echo "$response" | jq -r '.data.repository.labels.nodes[].name')
        
        # Add batch labels to array
        while IFS= read -r label; do
            if [[ -n "$label" ]]; then
                all_labels+=("$label")
            fi
        done <<< "$batch_labels"
        
        # Check if there are more pages
        has_next_page=$(echo "$response" | jq -r '.data.repository.labels.pageInfo.hasNextPage')
        cursor=$(echo "$response" | jq -r '.data.repository.labels.pageInfo.endCursor')
        
        info "Fetched ${#all_labels[@]} labels so far..."
    done
    
    # Check if we got any labels
    if [[ ${#all_labels[@]} -eq 0 ]]; then
        error "No labels found from $REPO_OWNER/$REPO_NAME"
        exit 1
    fi
    
    info "Total labels found: ${#all_labels[@]}"
    
    # Sort labels alphabetically
    IFS=$'\n' sorted_labels=($(sort <<< "${all_labels[*]}"))
    unset IFS
    
    # Convert to JSON array format
    info "Converting to JSON format..."
    {
        echo "["
        for i in "${!sorted_labels[@]}"; do
            if [[ $i -eq $((${#sorted_labels[@]} - 1)) ]]; then
                # Last element, no comma
                echo "  \"${sorted_labels[$i]}\""
            else
                # Not last element, add comma
                echo "  \"${sorted_labels[$i]}\","
            fi
        done
        echo "]"
    } > "$OUTPUT_FILE"
    
    info "Labels saved to: $OUTPUT_FILE"
    info "Total labels: ${#sorted_labels[@]}"
}

# Main function
main() {
    fetch_all_labels
    info "Script completed successfully"
}

# Run the main function
main
#!/usr/bin/env bash

# Script to fetch all labels from spring-projects/spring-ai repository
# Updates labels.json with current label data

set -Eeuo pipefail

# Configuration
REPO="spring-projects/spring-ai"
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

Fetch all labels from the Spring AI project and update labels.json

OPTIONS:
    -h, --help          Show this help message
    -o, --output FILE   Output file (default: labels.json)
    -r, --repo REPO     Repository (default: spring-projects/spring-ai)
    --version           Show version information

EXAMPLES:
    $0                           # Fetch labels and update labels.json
    $0 -o custom_labels.json     # Save to custom file
    $0 -r owner/repo             # Fetch from different repository

EOF
}

# Version function
version() {
    echo "fetch_labels.sh 1.0.0"
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
        -r|--repo)
            REPO="$2"
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

# Main function to fetch labels
fetch_labels() {
    info "Fetching labels from repository: $REPO"
    
    # Fetch labels using GitHub CLI
    if ! gh label list --repo "$REPO" --json name --jq '.[].name' > "$TEMP_FILE"; then
        error "Failed to fetch labels from $REPO"
        exit 1
    fi
    
    # Check if we got any labels
    if [[ ! -s "$TEMP_FILE" ]]; then
        error "No labels found or empty response from $REPO"
        exit 1
    fi
    
    # Count labels
    local label_count
    label_count=$(wc -l < "$TEMP_FILE")
    info "Found $label_count labels"
    
    # Convert to JSON array format
    info "Converting to JSON format..."
    {
        echo "["
        # Add quotes around each label and add commas (except for the last one)
        awk '{
            if (NR > 1) print "  \"" prev "\","
            prev = $0
        }
        END {
            if (NR > 0) print "  \"" prev "\""
        }' "$TEMP_FILE"
        echo "]"
    } > "$OUTPUT_FILE"
    
    info "Labels saved to: $OUTPUT_FILE"
    info "Total labels: $label_count"
}

# Run the main function
fetch_labels

info "Script completed successfully"
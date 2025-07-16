#!/usr/bin/env bash

# GitHub Issues Data Collection Script
# Collects all closed issues from a GitHub repository using gh CLI
# with smart batching and comprehensive data extraction

set -Eeuo pipefail

# Script configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"

# Default configuration
DEFAULT_BATCH_SIZE=100
DEFAULT_MAX_RETRIES=3
DEFAULT_RETRY_DELAY=5
DEFAULT_LARGE_ISSUE_THRESHOLD=50
DEFAULT_SIZE_THRESHOLD=102400  # 100KB

# Configuration from environment or defaults
BATCH_SIZE="${ISSUE_BATCH_SIZE:-$DEFAULT_BATCH_SIZE}"
MAX_RETRIES="${ISSUE_MAX_RETRIES:-$DEFAULT_MAX_RETRIES}"
RETRY_DELAY="${ISSUE_RETRY_DELAY:-$DEFAULT_RETRY_DELAY}"
LARGE_ISSUE_THRESHOLD="${ISSUE_LARGE_THRESHOLD:-$DEFAULT_LARGE_ISSUE_THRESHOLD}"
SIZE_THRESHOLD="${ISSUE_SIZE_THRESHOLD:-$DEFAULT_SIZE_THRESHOLD}"

# Output directories
readonly BASE_DIR="issues/raw/closed"
readonly BATCH_DIR="$BASE_DIR/batch_$TIMESTAMP"
readonly INDIVIDUAL_DIR="$BASE_DIR/individual"
readonly LOG_FILE="$BASE_DIR/collection.log"
readonly RESUME_FILE="$BASE_DIR/.resume_state"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Global variables
REPO_NAME=""
REPO_URL=""
TOTAL_ISSUES=0
PROCESSED_ISSUES=0
DRY_RUN=false
INCREMENTAL=false
COMPRESS=false
CLEAN=false

# Cleanup function
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        error "Script failed with exit code $exit_code"
        save_resume_state
    fi
    exit $exit_code
}

trap cleanup EXIT

# Logging functions
log() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "$(date '+%Y-%m-%d %H:%M:%S') $*" | tee -a "$LOG_FILE"
}

info() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

warn() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE" >&2
}

success() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$LOG_FILE"
}

# Usage function
usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Collect all closed GitHub issues from a repository using gh CLI.

OPTIONS:
    -h, --help              Show this help message
    -r, --repo REPO         Repository in format owner/repo (default: current repo)
    -b, --batch-size SIZE   Issues per batch file (default: $DEFAULT_BATCH_SIZE)
    -d, --dry-run          Show what would be collected without doing it
    -i, --incremental      Skip already collected issues
    -c, --compress         Compress output files
    -v, --verbose          Enable verbose logging
    --clean                Clean up previous collection data before starting
    --resume               Resume from last successful batch

ENVIRONMENT VARIABLES:
    ISSUE_BATCH_SIZE       Batch size (default: $DEFAULT_BATCH_SIZE)
    ISSUE_MAX_RETRIES      Max retry attempts (default: $DEFAULT_MAX_RETRIES)
    ISSUE_RETRY_DELAY      Delay between retries (default: $DEFAULT_RETRY_DELAY)
    ISSUE_LARGE_THRESHOLD  Comments threshold for individual files (default: $DEFAULT_LARGE_ISSUE_THRESHOLD)
    ISSUE_SIZE_THRESHOLD   Size threshold in bytes (default: $DEFAULT_SIZE_THRESHOLD)

EXAMPLES:
    $SCRIPT_NAME --repo spring-projects/spring-ai
    $SCRIPT_NAME --batch-size 50 --incremental
    $SCRIPT_NAME --dry-run --verbose

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -r|--repo)
                REPO_NAME="$2"
                shift 2
                ;;
            -b|--batch-size)
                BATCH_SIZE="$2"
                shift 2
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -i|--incremental)
                INCREMENTAL=true
                shift
                ;;
            -c|--compress)
                COMPRESS=true
                shift
                ;;
            -v|--verbose)
                set -x
                shift
                ;;
            --clean)
                CLEAN=true
                shift
                ;;
            --resume)
                if [[ -f "$RESUME_FILE" ]]; then
                    source "$RESUME_FILE"
                    info "Resuming from batch $PROCESSED_ISSUES"
                else
                    warn "No resume state found"
                fi
                shift
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Validate dependencies
check_dependencies() {
    local deps=("gh" "jq")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            error "Required dependency '$dep' not found"
            exit 1
        fi
    done
    
    # Check gh auth
    if ! gh auth status &> /dev/null; then
        error "GitHub CLI not authenticated. Run 'gh auth login' first"
        exit 1
    fi
}

# Get repository information
get_repo_info() {
    if [[ -z "$REPO_NAME" ]]; then
        # Try to get from current directory
        if ! REPO_NAME=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null); then
            error "Could not determine repository. Use --repo option or run in a git repository"
            exit 1
        fi
    fi
    
    local repo_info
    if ! repo_info=$(gh repo view "$REPO_NAME" --json url,nameWithOwner 2>/dev/null); then
        error "Could not access repository: $REPO_NAME"
        exit 1
    fi
    
    REPO_URL=$(echo "$repo_info" | jq -r '.url')
    REPO_NAME=$(echo "$repo_info" | jq -r '.nameWithOwner')
    
    info "Repository: $REPO_NAME"
    info "URL: $REPO_URL"
}

# Get total issue count
get_total_issues() {
    info "Getting total closed issues count..."
    
    # Extract owner and repo from REPO_NAME
    local owner repo_name
    owner=$(echo "$REPO_NAME" | cut -d'/' -f1)
    repo_name=$(echo "$REPO_NAME" | cut -d'/' -f2)
    
    # Method 1: Try GraphQL API first (more reliable)
    local graphql_query
    graphql_query=$(cat << EOF
query {
  repository(owner: "$owner", name: "$repo_name") {
    issues(states: CLOSED) {
      totalCount
    }
  }
}
EOF
)
    
    local total_count
    if total_count=$(gh api graphql -f query="$graphql_query" --jq '.data.repository.issues.totalCount' 2>/dev/null); then
        TOTAL_ISSUES="$total_count"
        info "Found $TOTAL_ISSUES closed issues (GraphQL)"
        return
    fi
    
    warn "GraphQL query failed, trying search API..."
    
    # Method 2: Fallback to search API
    if total_count=$(gh api "/search/issues?q=is:issue+is:closed+repo:$REPO_NAME" --jq '.total_count' 2>/dev/null); then
        TOTAL_ISSUES="$total_count"
        info "Found $TOTAL_ISSUES closed issues (Search API)"
        return
    fi
    
    warn "Search API failed, using fallback method..."
    
    # Method 3: Fallback to pagination estimation
    local first_batch
    if ! first_batch=$(gh issue list --repo "$REPO_NAME" --state closed --limit 100 --json number 2>/dev/null); then
        error "Failed to get issues list"
        exit 1
    fi
    
    local first_count
    first_count=$(echo "$first_batch" | jq 'length')
    
    if [[ "$first_count" -eq 0 ]]; then
        TOTAL_ISSUES=0
        info "No closed issues found"
        return
    fi
    
    # Estimate based on first page
    TOTAL_ISSUES="$first_count"
    info "Estimated $TOTAL_ISSUES+ closed issues (fallback method)"
    warn "This is a rough estimate - actual count may be higher"
}

# Clean up previous collection data
cleanup_previous_data() {
    if [[ "$CLEAN" != "true" ]]; then
        return
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would clean up previous collection data in $BASE_DIR"
        return
    fi
    
    if [[ -d "$BASE_DIR" ]]; then
        info "Cleaning up previous collection data..."
        
        # Remove batch directories
        find "$BASE_DIR" -name "batch_*" -type d -exec rm -rf {} + 2>/dev/null || true
        
        # Remove individual files
        if [[ -d "$BASE_DIR/individual" ]]; then
            rm -rf "$BASE_DIR/individual"
        fi
        
        # Remove old metadata and logs
        rm -f "$BASE_DIR/metadata.json"
        rm -f "$BASE_DIR/collection.log"
        rm -f "$BASE_DIR/.resume_state"
        
        success "Previous collection data cleaned up"
    fi
}

# Create directory structure
setup_directories() {
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would create directories:"
        info "  - $BASE_DIR"
        info "  - $BATCH_DIR"
        info "  - $INDIVIDUAL_DIR"
        return
    fi
    
    mkdir -p "$BASE_DIR" "$BATCH_DIR" "$INDIVIDUAL_DIR"
    
    # Initialize log file
    {
        echo "=== GitHub Issues Collection Started ==="
        echo "Timestamp: $TIMESTAMP"
        echo "Repository: $REPO_NAME"
        echo "Total Issues: $TOTAL_ISSUES"
        echo "Batch Size: $BATCH_SIZE"
        echo "========================================"
    } > "$LOG_FILE"
}

# Calculate issue size
calculate_issue_size() {
    local issue_json="$1"
    echo "$issue_json" | wc -c
}

# Check if issue is large
is_large_issue() {
    local issue_json="$1"
    local comment_count body_size
    
    comment_count=$(echo "$issue_json" | jq -r '.comments | length')
    body_size=$(calculate_issue_size "$issue_json")
    
    [[ "$comment_count" -gt "$LARGE_ISSUE_THRESHOLD" ]] || [[ "$body_size" -gt "$SIZE_THRESHOLD" ]]
}

# Fetch issue details with retry
fetch_issue_details() {
    local issue_number="$1"
    local attempt=1
    local issue_data
    
    while [[ $attempt -le $MAX_RETRIES ]]; do
        if issue_data=$(gh issue view "$issue_number" --repo "$REPO_NAME" --json number,title,body,state,createdAt,updatedAt,closedAt,author,assignees,labels,milestone,comments,url 2>/dev/null); then
            echo "$issue_data"
            return 0
        fi
        
        warn "Failed to fetch issue #$issue_number (attempt $attempt/$MAX_RETRIES)"
        if [[ $attempt -lt $MAX_RETRIES ]]; then
            sleep "$RETRY_DELAY"
        fi
        ((attempt++))
    done
    
    error "Failed to fetch issue #$issue_number after $MAX_RETRIES attempts"
    return 1
}

# Save individual issue
save_individual_issue() {
    local issue_number="$1"
    local issue_data="$2"
    local file_path="$INDIVIDUAL_DIR/issue_$issue_number.json"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would save individual issue #$issue_number to $file_path"
        return
    fi
    
    echo "$issue_data" | jq '.' > "$file_path"
    
    if [[ "$COMPRESS" == "true" ]]; then
        gzip "$file_path"
        file_path="$file_path.gz"
    fi
    
    info "Saved individual issue #$issue_number to $file_path"
}

# Process batch of issues from GraphQL response
process_batch_from_graphql() {
    local batch_num="$1"
    local issues_list="$2"
    
    local issue_count
    issue_count=$(echo "$issues_list" | jq 'length')
    
    info "Processing batch $batch_num ($issue_count issues from GraphQL)"
    
    local batch_file="$BATCH_DIR/issues_batch_$(printf "%03d" "$batch_num").json"
    local batch_issues=()
    local individual_refs=()
    
    # Process each issue in the batch
    for ((i=0; i<issue_count; i++)); do
        local issue_data
        issue_data=$(echo "$issues_list" | jq -c ".[$i]")
        
        local issue_number
        issue_number=$(echo "$issue_data" | jq -r '.number')
        
        # Transform GraphQL format to match expected format
        local transformed_issue
        transformed_issue=$(echo "$issue_data" | jq -c '{
            number: .number,
            title: .title,
            body: .body,
            state: .state,
            createdAt: .createdAt,
            updatedAt: .updatedAt,
            closedAt: .closedAt,
            url: .url,
            author: .author,
            assignees: .assignees.nodes,
            labels: .labels.nodes,
            milestone: .milestone,
            comments: .comments.nodes
        }')
        
        # Check if issue should be saved individually
        if is_large_issue "$transformed_issue"; then
            save_individual_issue "$issue_number" "$transformed_issue"
            individual_refs+=("{\"issue\": $issue_number, \"moved_to\": \"individual/issue_$issue_number.json\"}")
        else
            batch_issues+=("$transformed_issue")
        fi
        
        ((PROCESSED_ISSUES++))
        
        # Progress update (show every 10 issues to reduce noise)
        if [[ $((PROCESSED_ISSUES % 10)) -eq 0 ]] || [[ $PROCESSED_ISSUES -eq 1 ]]; then
            local elapsed=$(($(date +%s) - START_TIME))
            local rate="0.0"
            local eta_msg=""
            local percent=0
            
            if [[ $elapsed -gt 0 ]]; then
                # Calculate rate with decimal precision (use bc if available, otherwise fallback)
                if command -v bc >/dev/null 2>&1; then
                    rate=$(echo "scale=1; $PROCESSED_ISSUES / $elapsed" | bc -l 2>/dev/null || echo "0.0")
                else
                    # Fallback: multiply by 10 for one decimal place
                    local rate_x10=$(( (PROCESSED_ISSUES * 10) / elapsed ))
                    rate="${rate_x10:0:-1}.${rate_x10: -1}"
                fi
                
                # Calculate ETA
                local rate_float
                if command -v bc >/dev/null 2>&1; then
                    rate_float=$(echo "$rate > 0" | bc -l 2>/dev/null || echo "0")
                else
                    # Simple check: if rate is not "0.0"
                    if [[ "$rate" != "0.0" ]]; then
                        rate_float=1
                    else
                        rate_float=0
                    fi
                fi
                
                if [[ $rate_float -eq 1 ]]; then
                    local remaining=$((TOTAL_ISSUES - PROCESSED_ISSUES))
                    local eta_seconds
                    if command -v bc >/dev/null 2>&1; then
                        eta_seconds=$(echo "scale=0; $remaining / $rate" | bc -l 2>/dev/null || echo "0")
                    else
                        # Simple division for ETA
                        eta_seconds=$((remaining * elapsed / PROCESSED_ISSUES))
                    fi
                    
                    if [[ $eta_seconds -gt 0 ]]; then
                        local eta_minutes=$((eta_seconds / 60))
                        local eta_hours=$((eta_minutes / 60))
                        eta_minutes=$((eta_minutes % 60))
                        
                        if [[ $eta_hours -gt 0 ]]; then
                            eta_msg=" | ETA: ${eta_hours}h ${eta_minutes}m"
                        elif [[ $eta_minutes -gt 0 ]]; then
                            eta_msg=" | ETA: ${eta_minutes}m"
                        else
                            eta_msg=" | ETA: ${eta_seconds}s"
                        fi
                    fi
                fi
            fi
            
            # Calculate percentage
            if [[ $TOTAL_ISSUES -gt 0 ]]; then
                percent=$((PROCESSED_ISSUES * 100 / TOTAL_ISSUES))
            fi
            
            info "Progress: $PROCESSED_ISSUES/$TOTAL_ISSUES ($percent%) | Rate: ${rate}/s$eta_msg"
        fi
    done
    
    # Save batch file
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would save batch to $batch_file"
        info "  - Regular issues: ${#batch_issues[@]}"
        info "  - Individual refs: ${#individual_refs[@]}"
        return
    fi
    
    # Create batch JSON
    local batch_json="{\"batch_info\": {\"batch_number\": $batch_num, \"issue_count\": $issue_count, \"timestamp\": \"$TIMESTAMP\", \"source\": \"graphql\"}, \"issues\": [$(IFS=','; echo "${batch_issues[*]}")], \"individual_references\": [$(IFS=','; echo "${individual_refs[*]}")]}"
    
    echo "$batch_json" | jq '.' > "$batch_file"
    
    if [[ "$COMPRESS" == "true" ]]; then
        gzip "$batch_file"
        batch_file="$batch_file.gz"
    fi
    
    # Final batch summary
    local batch_elapsed=$(($(date +%s) - START_TIME))
    local batch_rate="0.0"
    if [[ $batch_elapsed -gt 0 ]] && command -v bc >/dev/null 2>&1; then
        batch_rate=$(echo "scale=1; $PROCESSED_ISSUES / $batch_elapsed" | bc -l 2>/dev/null || echo "0.0")
    elif [[ $batch_elapsed -gt 0 ]]; then
        local rate_x10=$(( (PROCESSED_ISSUES * 10) / batch_elapsed ))
        batch_rate="${rate_x10:0:-1}.${rate_x10: -1}"
    fi
    
    success "Saved batch $batch_num to $batch_file | Overall rate: ${batch_rate}/s"
}

# Process batch of issues from a list (legacy function for REST API)
process_batch_from_list() {
    local batch_num="$1"
    local issues_list="$2"
    
    local issue_count
    issue_count=$(echo "$issues_list" | jq 'length')
    
    info "Processing batch $batch_num ($issue_count issues)"
    
    local batch_file="$BATCH_DIR/issues_batch_$(printf "%03d" "$batch_num").json"
    local batch_issues=()
    local individual_refs=()
    
    # Process each issue in the batch
    local issue_numbers
    issue_numbers=$(echo "$issues_list" | jq -r '.[].number')
    
    for issue_number in $issue_numbers; do
        local issue_data
        if ! issue_data=$(fetch_issue_details "$issue_number"); then
            continue
        fi
        
        # Check if issue should be saved individually
        if is_large_issue "$issue_data"; then
            save_individual_issue "$issue_number" "$issue_data"
            individual_refs+=("{\"issue\": $issue_number, \"moved_to\": \"individual/issue_$issue_number.json\"}")
        else
            batch_issues+=("$issue_data")
        fi
        
        ((PROCESSED_ISSUES++))
        
        # Progress update (show every 10 issues to reduce noise)
        if [[ $((PROCESSED_ISSUES % 10)) -eq 0 ]] || [[ $PROCESSED_ISSUES -eq 1 ]]; then
            local elapsed=$(($(date +%s) - START_TIME))
            local rate="0.0"
            local eta_msg=""
            local percent=0
            
            if [[ $elapsed -gt 0 ]]; then
                # Calculate rate with decimal precision (use bc if available, otherwise fallback)
                if command -v bc >/dev/null 2>&1; then
                    rate=$(echo "scale=1; $PROCESSED_ISSUES / $elapsed" | bc -l 2>/dev/null || echo "0.0")
                else
                    # Fallback: multiply by 10 for one decimal place
                    local rate_x10=$(( (PROCESSED_ISSUES * 10) / elapsed ))
                    rate="${rate_x10:0:-1}.${rate_x10: -1}"
                fi
                
                # Calculate ETA
                local rate_float
                if command -v bc >/dev/null 2>&1; then
                    rate_float=$(echo "$rate > 0" | bc -l 2>/dev/null || echo "0")
                else
                    # Simple check: if rate is not "0.0"
                    if [[ "$rate" != "0.0" ]]; then
                        rate_float=1
                    else
                        rate_float=0
                    fi
                fi
                
                if [[ $rate_float -eq 1 ]]; then
                    local remaining=$((TOTAL_ISSUES - PROCESSED_ISSUES))
                    local eta_seconds
                    if command -v bc >/dev/null 2>&1; then
                        eta_seconds=$(echo "scale=0; $remaining / $rate" | bc -l 2>/dev/null || echo "0")
                    else
                        # Simple division for ETA
                        eta_seconds=$((remaining * elapsed / PROCESSED_ISSUES))
                    fi
                    
                    if [[ $eta_seconds -gt 0 ]]; then
                        local eta_minutes=$((eta_seconds / 60))
                        local eta_hours=$((eta_minutes / 60))
                        eta_minutes=$((eta_minutes % 60))
                        
                        if [[ $eta_hours -gt 0 ]]; then
                            eta_msg=" | ETA: ${eta_hours}h ${eta_minutes}m"
                        elif [[ $eta_minutes -gt 0 ]]; then
                            eta_msg=" | ETA: ${eta_minutes}m"
                        else
                            eta_msg=" | ETA: ${eta_seconds}s"
                        fi
                    fi
                fi
            fi
            
            # Calculate percentage
            if [[ $TOTAL_ISSUES -gt 0 ]]; then
                percent=$((PROCESSED_ISSUES * 100 / TOTAL_ISSUES))
            fi
            
            info "Progress: $PROCESSED_ISSUES/$TOTAL_ISSUES ($percent%) | Rate: ${rate}/s$eta_msg"
        fi
    done
    
    # Save batch file
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would save batch to $batch_file"
        info "  - Regular issues: ${#batch_issues[@]}"
        info "  - Individual refs: ${#individual_refs[@]}"
        return
    fi
    
    # Create batch JSON
    local batch_json="{\"batch_info\": {\"batch_number\": $batch_num, \"issue_count\": $issue_count, \"timestamp\": \"$TIMESTAMP\"}, \"issues\": [$(IFS=','; echo "${batch_issues[*]}")], \"individual_references\": [$(IFS=','; echo "${individual_refs[*]}")]}"
    
    echo "$batch_json" | jq '.' > "$batch_file"
    
    if [[ "$COMPRESS" == "true" ]]; then
        gzip "$batch_file"
        batch_file="$batch_file.gz"
    fi
    
    # Final batch summary
    local batch_elapsed=$(($(date +%s) - START_TIME))
    local batch_rate="0.0"
    if [[ $batch_elapsed -gt 0 ]] && command -v bc >/dev/null 2>&1; then
        batch_rate=$(echo "scale=1; $PROCESSED_ISSUES / $batch_elapsed" | bc -l 2>/dev/null || echo "0.0")
    elif [[ $batch_elapsed -gt 0 ]]; then
        local rate_x10=$(( (PROCESSED_ISSUES * 10) / batch_elapsed ))
        batch_rate="${rate_x10:0:-1}.${rate_x10: -1}"
    fi
    
    success "Saved batch $batch_num to $batch_file | Overall rate: ${batch_rate}/s"
}

# Save resume state
save_resume_state() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return
    fi
    
    cat > "$RESUME_FILE" << EOF
PROCESSED_ISSUES=$PROCESSED_ISSUES
TIMESTAMP="$TIMESTAMP"
REPO_NAME="$REPO_NAME"
TOTAL_ISSUES=$TOTAL_ISSUES
EOF
}

# Create metadata file
create_metadata() {
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would create metadata.json"
        return
    fi
    
    local gh_version
    gh_version=$(gh --version | head -1)
    
    local rate_limit
    rate_limit=$(gh api rate_limit 2>/dev/null || echo '{"rate": {"remaining": "unknown"}}')
    
    local end_time
    end_time=$(date +%s)
    
    cat > "$BASE_DIR/metadata.json" << EOF
{
    "collection_info": {
        "timestamp": "$TIMESTAMP",
        "start_time": "$START_TIME",
        "end_time": "$end_time",
        "duration_seconds": $((end_time - START_TIME)),
        "gh_version": "$gh_version",
        "script_version": "1.0.0"
    },
    "repository": {
        "name": "$REPO_NAME",
        "url": "$REPO_URL"
    },
    "collection_stats": {
        "total_issues": $TOTAL_ISSUES,
        "processed_issues": $PROCESSED_ISSUES,
        "batch_size": $BATCH_SIZE,
        "batches_created": $(((TOTAL_ISSUES + BATCH_SIZE - 1) / BATCH_SIZE)),
        "individual_files": $(find "$INDIVIDUAL_DIR" -name "issue_*.json*" 2>/dev/null | wc -l)
    },
    "configuration": {
        "batch_size": $BATCH_SIZE,
        "large_issue_threshold": $LARGE_ISSUE_THRESHOLD,
        "size_threshold": $SIZE_THRESHOLD,
        "compressed": $COMPRESS
    },
    "rate_limit": $rate_limit
}
EOF
    
    success "Created metadata.json"
}

# Main collection function
collect_issues() {
    local start_time_human
    start_time_human=$(date)
    START_TIME=$(date +%s)
    
    info "Starting collection at $start_time_human"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN MODE - No files will be created"
        info "Would collect up to $TOTAL_ISSUES issues in batches of $BATCH_SIZE"
        return
    fi
    
    # Process issues using GraphQL for much better performance
    local batch_num=1
    local has_more_issues=true
    local cursor=""
    
    # Extract owner and repo from REPO_NAME
    local owner repo_name
    owner=$(echo "$REPO_NAME" | cut -d'/' -f1)
    repo_name=$(echo "$REPO_NAME" | cut -d'/' -f2)
    
    while [[ "$has_more_issues" == "true" ]]; do
        info "Fetching batch $batch_num of $BATCH_SIZE issues with GraphQL..."
        
        # Build GraphQL query for batch of issues with all details
        local after_clause=""
        if [[ -n "$cursor" ]]; then
            after_clause=", after: \"$cursor\""
        fi
        
        local graphql_query
        graphql_query=$(cat << EOF
query {
  repository(owner: "$owner", name: "$repo_name") {
    issues(first: $BATCH_SIZE, states: CLOSED, orderBy: {field: CREATED_AT, direction: DESC}$after_clause) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        body
        state
        createdAt
        updatedAt
        closedAt
        url
        author {
          login
          ... on User {
            name
          }
        }
        assignees(first: 10) {
          nodes {
            login
            ... on User {
              name
            }
          }
        }
        labels(first: 20) {
          nodes {
            name
            color
            description
          }
        }
        milestone {
          title
          number
          state
          description
        }
        comments(first: 100) {
          nodes {
            author {
              login
              ... on User {
                name
              }
            }
            body
            createdAt
            reactions {
              totalCount
            }
          }
        }
      }
    }
  }
}
EOF
)
        
        # Execute GraphQL query
        local graphql_result
        if ! graphql_result=$(gh api graphql -f query="$graphql_query" 2>/dev/null); then
            error "Failed to fetch issues batch $batch_num with GraphQL"
            save_resume_state
            exit 1
        fi
        
        # Extract issues data
        local issues_list
        if ! issues_list=$(echo "$graphql_result" | jq -c '.data.repository.issues.nodes'); then
            error "Failed to parse GraphQL response for batch $batch_num"
            save_resume_state
            exit 1
        fi
        
        # Check if we got any issues
        local issue_count
        issue_count=$(echo "$issues_list" | jq 'length')
        
        if [[ "$issue_count" -eq 0 ]]; then
            info "No more issues found. Collection complete."
            has_more_issues=false
            break
        fi
        
        # Process this batch
        if ! process_batch_from_graphql "$batch_num" "$issues_list"; then
            error "Failed to process batch $batch_num"
            save_resume_state
            exit 1
        fi
        
        save_resume_state
        
        # Check if there are more pages
        local has_next_page
        has_next_page=$(echo "$graphql_result" | jq -r '.data.repository.issues.pageInfo.hasNextPage')
        
        if [[ "$has_next_page" == "true" ]]; then
            cursor=$(echo "$graphql_result" | jq -r '.data.repository.issues.pageInfo.endCursor')
            info "More issues available, continuing with next batch..."
        else
            has_more_issues=false
            info "Reached end of issues (no more pages)"
        fi
        
        ((batch_num++))
        
        # Rate limit check
        local rate_remaining
        rate_remaining=$(gh api rate_limit --jq '.rate.remaining' 2>/dev/null || echo "unknown")
        if [[ "$rate_remaining" != "unknown" ]] && [[ "$rate_remaining" -lt 100 ]]; then
            warn "Rate limit low ($rate_remaining remaining). Consider pausing."
        fi
    done
    
    create_metadata
    
    # Clean up resume state
    rm -f "$RESUME_FILE"
    
    local end_time_human
    end_time_human=$(date)
    local duration=$((($(date +%s) - START_TIME)))
    
    success "Collection completed at $end_time_human"
    success "Duration: ${duration}s"
    success "Processed: $PROCESSED_ISSUES issues"
    success "Output directory: $BASE_DIR"
}

# Print summary
print_summary() {
    echo
    echo "=== Collection Summary ==="
    echo "Repository: $REPO_NAME"
    echo "Total issues: $TOTAL_ISSUES"
    echo "Processed: $PROCESSED_ISSUES"
    echo "Batch size: $BATCH_SIZE"
    echo "Output: $BASE_DIR"
    echo "Log: $LOG_FILE"
    if [[ "$COMPRESS" == "true" ]]; then
        echo "Compression: Enabled"
    fi
    echo "========================="
}

# Main function
main() {
    parse_args "$@"
    check_dependencies
    get_repo_info
    get_total_issues
    cleanup_previous_data
    setup_directories
    collect_issues
    print_summary
}

# Run main function
main "$@"
#!/usr/bin/env bash

# Search Pull Requests with Comments from Specific Users
# Simple wrapper around gh search prs for finding PRs with comments from specific users

set -Eeuo pipefail

# Default configuration
DEFAULT_REPO="spring-projects/spring-ai"
DEFAULT_LIMIT=30
DEFAULT_SORT="updated"
DEFAULT_ORDER="desc"
DEFAULT_STATE="open"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
REPO="$DEFAULT_REPO"
LIMIT="$DEFAULT_LIMIT"
SORT="$DEFAULT_SORT"
ORDER="$DEFAULT_ORDER"
STATE="$DEFAULT_STATE"
OUTPUT_FORMAT="table"
COMMENTER=""

# Logging functions
info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS] <commenter-username>

Search for pull requests with comments from a specific user and sort by when they last commented.

ARGUMENTS:
    commenter-username    GitHub username to search for comments from

OPTIONS:
    -h, --help           Show this help message
    -r, --repo REPO      Repository in format owner/repo (default: $DEFAULT_REPO)
    -l, --limit NUMBER   Maximum number of results (default: $DEFAULT_LIMIT)
    -s, --sort FIELD     Sort by field: {updated|created|comments|reactions} (default: $DEFAULT_SORT)
    -o, --order ORDER    Sort order: {asc|desc} (default: $DEFAULT_ORDER)
    --state STATE        PR state: {open|closed|all} (default: $DEFAULT_STATE)
    -f, --format FORMAT  Output format: {table|json} (default: table)
    -v, --verbose        Enable verbose output

EXAMPLES:
    $0 ThomasVitale
    $0 --repo spring-projects/spring-ai --limit 10 ThomasVitale
    $0 --state all --order asc --format json ThomasVitale
    $0 --state closed --limit 50 username123

NOTES:
    - Results are sorted by when the user last commented (most recent first by default)
    - By default, only open PRs are searched (use --state all for all PRs)
    - The script fetches actual comment timestamps, not just PR update times
    - Use --format json for programmatic processing
    - The script uses GitHub CLI (gh) which must be authenticated
    - Note: Sort field is ignored - results are always sorted by last comment time

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
                REPO="$2"
                shift 2
                ;;
            -l|--limit)
                LIMIT="$2"
                shift 2
                ;;
            -s|--sort)
                SORT="$2"
                shift 2
                ;;
            -o|--order)
                ORDER="$2"
                shift 2
                ;;
            --state)
                STATE="$2"
                shift 2
                ;;
            -f|--format)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            -v|--verbose)
                set -x
                shift
                ;;
            -*)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                if [[ -z "$COMMENTER" ]]; then
                    COMMENTER="$1"
                else
                    error "Multiple commenter usernames provided: $COMMENTER and $1"
                    usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

# Validate dependencies
check_dependencies() {
    if ! command -v gh &> /dev/null; then
        error "GitHub CLI (gh) not found. Install it from https://cli.github.com/"
        exit 1
    fi
    
    # Check gh auth
    if ! gh auth status &> /dev/null; then
        error "GitHub CLI not authenticated. Run 'gh auth login' first"
        exit 1
    fi
}

# Validate arguments
validate_args() {
    if [[ -z "$COMMENTER" ]]; then
        error "Commenter username is required"
        usage
        exit 1
    fi
    
    # Validate sort field
    case "$SORT" in
        updated|created|comments|reactions|interactions) ;;
        *)
            error "Invalid sort field: $SORT"
            error "Valid options: updated, created, comments, reactions, interactions"
            exit 1
            ;;
    esac
    
    # Validate order
    case "$ORDER" in
        asc|desc) ;;
        *)
            error "Invalid order: $ORDER"
            error "Valid options: asc, desc"
            exit 1
            ;;
    esac
    
    # Validate state
    case "$STATE" in
        open|closed|all) ;;
        *)
            error "Invalid state: $STATE"
            error "Valid options: open, closed, all"
            exit 1
            ;;
    esac
    
    # Validate output format
    case "$OUTPUT_FORMAT" in
        table|json) ;;
        *)
            error "Invalid output format: $OUTPUT_FORMAT"
            error "Valid options: table, json"
            exit 1
            ;;
    esac
    
    # Validate limit
    if ! [[ "$LIMIT" =~ ^[0-9]+$ ]] || [[ "$LIMIT" -lt 1 ]] || [[ "$LIMIT" -gt 1000 ]]; then
        error "Invalid limit: $LIMIT (must be 1-1000)"
        exit 1
    fi
}

# Get latest comment timestamp from user for a specific PR
get_latest_comment_timestamp() {
    local pr_number="$1"
    local commenter="$2"
    
    local latest_comment
    latest_comment=$(gh pr view "$pr_number" --repo "$REPO" --json comments 2>/dev/null | \
        jq -r ".comments[] | select(.author.login == \"$commenter\") | .createdAt" | \
        sort | tail -1)
    
    if [[ -n "$latest_comment" && "$latest_comment" != "null" ]]; then
        echo "$latest_comment"
    else
        echo ""
    fi
}

# Format timestamp for display
format_timestamp() {
    local timestamp="$1"
    
    if command -v date >/dev/null 2>&1; then
        # Try to format as relative time
        if date -d "$timestamp" >/dev/null 2>&1; then
            # GNU date (Linux)
            local epoch_time
            epoch_time=$(date -d "$timestamp" +%s)
            local current_time
            current_time=$(date +%s)
            local diff=$((current_time - epoch_time))
            
            if [[ $diff -lt 60 ]]; then
                echo "$(($diff))s ago"
            elif [[ $diff -lt 3600 ]]; then
                echo "$(($diff / 60))m ago"
            elif [[ $diff -lt 86400 ]]; then
                echo "$(($diff / 3600))h ago"
            else
                echo "$(($diff / 86400))d ago"
            fi
        else
            # Fallback to ISO format
            echo "$timestamp"
        fi
    else
        echo "$timestamp"
    fi
}

# Search PRs with comments from user and get actual comment timestamps
search_pr_comments() {
    info "Searching PRs with comments from '$COMMENTER' in $REPO..."
    
    # First, get list of PRs where user has commented
    local pr_list
    local search_args=("search" "prs" "--repo" "$REPO" "--commenter" "$COMMENTER" "--limit" "100" "--json" "number,title,author,createdAt,updatedAt,state,url")
    
    # Add state filter if not 'all'
    if [[ "$STATE" != "all" ]]; then
        search_args+=("--state" "$STATE")
    fi
    
    if ! pr_list=$(gh "${search_args[@]}" 2>/dev/null); then
        error "Failed to search PRs with comments from '$COMMENTER'"
        exit 1
    fi
    
    local pr_count
    pr_count=$(echo "$pr_list" | jq 'length')
    
    if [[ "$pr_count" -eq 0 ]]; then
        warn "No PRs found with comments from '$COMMENTER'"
        return
    fi
    
    info "Found $pr_count PRs with comments from '$COMMENTER'. Analyzing comment timestamps..."
    
    # Create array to hold results with actual comment timestamps
    local results=()
    
    # Process each PR to get the actual latest comment timestamp
    while IFS= read -r pr_data; do
        local pr_number title author_login state url created_at updated_at
        pr_number=$(echo "$pr_data" | jq -r '.number')
        title=$(echo "$pr_data" | jq -r '.title')
        author_login=$(echo "$pr_data" | jq -r '.author.login')
        state=$(echo "$pr_data" | jq -r '.state')
        url=$(echo "$pr_data" | jq -r '.url')
        created_at=$(echo "$pr_data" | jq -r '.createdAt')
        updated_at=$(echo "$pr_data" | jq -r '.updatedAt')
        
        # Get the actual latest comment timestamp from the user
        local latest_comment_time
        latest_comment_time=$(get_latest_comment_timestamp "$pr_number" "$COMMENTER")
        
        if [[ -n "$latest_comment_time" ]]; then
            local result_json
            result_json=$(jq -n \
                --arg number "$pr_number" \
                --arg title "$title" \
                --arg author_login "$author_login" \
                --arg state "$state" \
                --arg url "$url" \
                --arg created_at "$created_at" \
                --arg updated_at "$updated_at" \
                --arg last_comment_at "$latest_comment_time" \
                '{
                    number: ($number | tonumber),
                    title: $title,
                    author: {login: $author_login},
                    state: $state,
                    url: $url,
                    createdAt: $created_at,
                    updatedAt: $updated_at,
                    lastCommentAt: $last_comment_at
                }')
            
            results+=("$result_json")
        fi
    done < <(echo "$pr_list" | jq -c '.[]')
    
    if [[ ${#results[@]} -eq 0 ]]; then
        warn "No valid comment timestamps found for '$COMMENTER'"
        return
    fi
    
    # Sort results by last comment timestamp
    local sorted_results
    sorted_results=$(printf '%s\n' "${results[@]}" | jq -s '. | sort_by(.lastCommentAt)')
    
    # Apply order (reverse if desc)
    if [[ "$ORDER" == "desc" ]]; then
        sorted_results=$(echo "$sorted_results" | jq 'reverse')
    fi
    
    # Apply limit
    sorted_results=$(echo "$sorted_results" | jq ".[:$LIMIT]")
    
    # Output results
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "$sorted_results"
    else
        # Table format
        echo -e "REPO\tID\tTITLE\tSTATE\tLAST COMMENT BY $COMMENTER"
        echo "$sorted_results" | jq -r '.[] | "\(.url | split("/")[3])/\(.url | split("/")[4])\t#\(.number)\t\(.title)\t\(.state)\t\(.lastCommentAt)"' | \
        while IFS=$'\t' read -r repo_name pr_id title state last_comment; do
            local formatted_time
            formatted_time=$(format_timestamp "$last_comment")
            printf "%-30s %-8s %-80s %-8s %s\n" "$repo_name" "$pr_id" "${title:0:75}..." "$state" "$formatted_time"
        done
    fi
    
    success "Search completed - showing PRs sorted by when '$COMMENTER' last commented"
}

# Main function
main() {
    parse_args "$@"
    check_dependencies
    validate_args
    search_pr_comments
}

# Run main function
main "$@"
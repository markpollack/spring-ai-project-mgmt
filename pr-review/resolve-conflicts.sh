#!/usr/bin/env bash

set -Eeuo pipefail

# Conflict Resolution Helper Script for Spring AI PRs
# This script helps resolve conflicts in PRs that have already been checked out

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SPRING_AI_DIR="$(dirname "$0")/spring-ai"
readonly PLANS_DIR="$(dirname "$0")/plans"

# Logging functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS] <PR_NUMBER>

Resolve conflicts in an already checked out Spring AI PR.
This script provides intelligent conflict resolution assistance.

Arguments:
    PR_NUMBER           The GitHub PR number with conflicts

Options:
    -h, --help         Show this help message
    -a, --auto         Attempt automatic resolution of simple conflicts
    -c, --claude       Call Claude Code for AI-assisted resolution
    -p, --plan-only    Only generate/show the conflict resolution plan
    -s, --status       Show current conflict status
    --dry-run          Show what would be done without executing

Examples:
    $0 1234                    # Analyze conflicts and generate plan
    $0 --auto 1234             # Auto-resolve simple conflicts
    $0 --claude 1234           # Get AI assistance
    $0 --plan-only 1234        # Just show/generate the plan
    $0 --status 1234           # Show current conflict status

Prerequisites:
    - PR must already be checked out in ./spring-ai
    - Git repository must be in a conflicted rebase state

EOF
}

# Setup Spring AI repository
setup_spring_ai_repo() {
    if [[ ! -d "$SPRING_AI_DIR" ]]; then
        info "Cloning Spring AI repository..."
        git clone https://github.com/spring-projects/spring-ai.git "$SPRING_AI_DIR"
        cd "$SPRING_AI_DIR"
        
        # Add upstream remote
        git remote add upstream https://github.com/spring-projects/spring-ai.git 2>/dev/null || true
    else
        cd "$SPRING_AI_DIR"
        
        if [[ ! -d ".git" ]]; then
            error "Directory exists but is not a git repository: $SPRING_AI_DIR"
            exit 1
        fi
        
        # Ensure upstream remote exists
        if ! git remote get-url upstream &>/dev/null; then
            info "Adding upstream remote..."
            git remote add upstream https://github.com/spring-projects/spring-ai.git
        fi
    fi
    
    # Fetch latest from upstream
    info "Fetching latest changes from upstream..."
    git fetch upstream
    
    # Switch to main branch and sync
    info "Syncing with upstream main..."
    git checkout main 2>/dev/null || git checkout -b main upstream/main
    git pull upstream main
    
    success "Spring AI repository is ready and synced"
}

# Check prerequisites
check_prerequisites() {
    local pr_number="$1"
    
    # Setup repository first
    setup_spring_ai_repo
    
    cd "$SPRING_AI_DIR"
    
    # Check if we're in a rebase state
    if [[ ! -d ".git/rebase-merge" && ! -d ".git/rebase-apply" ]]; then
        warn "Repository is not in a rebase state"
        info "Current status:"
        git status --short
        
        # Check if there are any conflicts anyway
        if ! git status --porcelain | grep -q "^UU\\|^AA\\|^DD"; then
            info "No conflicts detected. Repository appears to be clean."
            return 1
        fi
    fi
    
    return 0
}

# Show conflict status
show_conflict_status() {
    local pr_number="$1"
    
    info "Conflict status for PR #$pr_number:"
    echo
    
    cd "$SPRING_AI_DIR"
    
    # Show current branch
    info "Current branch: $(git branch --show-current 2>/dev/null || echo 'detached HEAD')"
    
    # Show conflicted files
    local conflicted_files
    conflicted_files=$(git status --porcelain | grep "^UU\\|^AA\\|^DD" | cut -c4-)
    
    if [[ -n "$conflicted_files" ]]; then
        warn "Conflicted files:"
        while IFS= read -r file; do
            if [[ -f "$file" ]]; then
                local markers
                markers=$(grep -c "^<<<<<<< \\|^>>>>>>> \\|^======= " "$file" 2>/dev/null || echo 0)
                echo "  - $file ($markers conflict markers)"
            else
                echo "  - $file (deleted/missing)"
            fi
        done <<< "$conflicted_files"
    else\n        success "No conflicts detected"
        return 0
    fi
    
    echo
    
    # Check for plan file
    local plan_file="$PLANS_DIR/plan-pr-$pr_number.md"
    if [[ -f "$plan_file" ]]; then
        info "📋 Resolution plan available: $plan_file"
        info "Last updated: $(stat -c %y "$plan_file" 2>/dev/null || echo 'unknown')"
    else
        info "No resolution plan found. Run with --plan-only to generate one."
    fi
    
    return 1
}

# Source the conflict resolution functions from pr-prepare.sh
source_conflict_functions() {
    # We'll extract the functions we need rather than sourcing the whole script
    # This ensures we have the latest versions of the conflict resolution functions
    
    local temp_script="/tmp/conflict_functions.sh"
    
    # Extract the functions we need from pr-prepare.sh
    awk '/^# Analyze conflict types/,/^# Rebase against upstream main/ {
        if ($0 !~ /^# Rebase against upstream main/) print
    }' "$(dirname "$0")/pr-prepare.sh" > "$temp_script"
    
    if [[ -f "$temp_script" && -s "$temp_script" ]]; then
        source "$temp_script"
        rm -f "$temp_script"
        return 0
    else
        error "Could not extract conflict resolution functions"
        return 1
    fi
}

# Main conflict resolution workflow
resolve_conflicts() {
    local pr_number="$1"
    local auto_resolve="$2"
    local call_claude="$3"
    local plan_only="$4"
    local dry_run="$5"
    
    if ! check_prerequisites "$pr_number"; then
        return 1
    fi
    
    cd "$SPRING_AI_DIR"
    
    # Create plans directory
    mkdir -p "$PLANS_DIR"
    
    # Source conflict resolution functions
    if ! source_conflict_functions; then
        error "Failed to load conflict resolution functions"
        exit 1
    fi
    
    # Always analyze conflicts first
    info "Analyzing conflicts for PR #$pr_number..."
    
    if analyze_conflicts "$pr_number"; then
        success "No conflicts detected!"
        return 0
    fi
    
    # Show the plan
    local plan_file="$PLANS_DIR/plan-pr-$pr_number.md"
    if [[ -f "$plan_file" ]]; then
        info "📋 Conflict resolution plan: $plan_file"
        if command -v bat &> /dev/null; then
            bat "$plan_file"
        elif command -v cat &> /dev/null; then
            cat "$plan_file"
        fi
    fi
    
    # If plan-only mode, stop here
    if [[ "$plan_only" == "true" ]]; then
        info "Plan-only mode: analysis complete"
        return 0
    fi
    
    # Attempt resolution strategies
    local resolution_successful=false
    
    if [[ "$auto_resolve" == "true" ]]; then
        info "Attempting automatic resolution..."
        if [[ "$dry_run" == "true" ]]; then
            info "[DRY RUN] Would attempt automatic conflict resolution"
        else
            if auto_resolve_simple_conflicts "$pr_number"; then
                success "Some conflicts auto-resolved"
                
                # Try to continue rebase
                if git rebase --continue; then
                    success "Rebase completed successfully!"
                    resolution_successful=true
                else
                    warn "Auto-resolution partially successful, but rebase still has issues"
                fi
            else
                warn "Automatic resolution was not successful"
            fi
        fi
    fi
    
    if [[ "$call_claude" == "true" && "$resolution_successful" == "false" ]]; then
        info "Calling Claude Code for assistance..."
        if [[ "$dry_run" == "true" ]]; then
            info "[DRY RUN] Would call Claude Code for conflict resolution"
        else
            call_claude_for_conflicts "$pr_number"
        fi
    fi
    
    # Final status
    if [[ "$resolution_successful" == "true" ]]; then
        success "Conflict resolution completed successfully!"
        info "You can now continue with your PR review workflow"
    else
        info "Next steps:"
        info "  1. Review the generated plan: $plan_file"
        info "  2. Manually resolve remaining conflicts"
        info "  3. Run: git add <resolved-files> && git rebase --continue"
        info "  4. Test build: fb or ./gradlew build"
    fi
}

# Parse command line arguments
AUTO_RESOLVE=false
CALL_CLAUDE=false
PLAN_ONLY=false
STATUS_ONLY=false
DRY_RUN=false
PR_NUMBER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -a|--auto)
            AUTO_RESOLVE=true
            shift
            ;;
        -c|--claude)
            CALL_CLAUDE=true
            shift
            ;;
        -p|--plan-only)
            PLAN_ONLY=true
            shift
            ;;
        -s|--status)
            STATUS_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -*)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            if [[ -z "$PR_NUMBER" ]]; then
                PR_NUMBER="$1"
            else
                error "Multiple PR numbers provided: $PR_NUMBER and $1"
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate PR number
if [[ -z "$PR_NUMBER" ]]; then
    error "PR number is required"
    usage
    exit 1
fi

if ! [[ "$PR_NUMBER" =~ ^[0-9]+$ ]]; then
    error "PR number must be a positive integer: $PR_NUMBER"
    exit 1
fi

# Execute based on mode
if [[ "$STATUS_ONLY" == "true" ]]; then
    show_conflict_status "$PR_NUMBER"
else
    resolve_conflicts "$PR_NUMBER" "$AUTO_RESOLVE" "$CALL_CLAUDE" "$PLAN_ONLY" "$DRY_RUN"
fi
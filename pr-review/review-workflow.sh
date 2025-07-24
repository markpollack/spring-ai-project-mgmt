#!/usr/bin/env bash

set -Eeuo pipefail

# Complete PR Review Workflow
# Combines pr-prepare.sh and run-review.sh for a seamless experience

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPORTS_DIR="$SCRIPT_DIR/reports"

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

Complete PR review workflow: prepare PR + run analysis + generate report.

This script combines pr-prepare.sh and run-review.sh for a seamless experience:
1. Prepares the PR (checkout, compile, squash, rebase)
2. Handles any conflicts (with options for auto-resolution or AI assistance)
3. Runs the PR review analysis using Claude Code
4. Generates a comprehensive review report

Arguments:
    PR_NUMBER           The GitHub PR number to review

Options:
    -h, --help         Show this help message
    --skip-squash      Skip commit squashing during preparation
    --skip-compile     Skip compilation check during preparation
    --auto-resolve     Auto-resolve simple conflicts during preparation
    --call-claude      Use AI assistance for complex conflicts
    --direct           Run review analysis directly in terminal (no report file)
    --force            Force overwrite of existing branches and reports
    --dry-run          Show what would be done without executing

Examples:
    $0 1234                    # Full workflow for PR #1234
    $0 --auto-resolve 1234     # Include automatic conflict resolution
    $0 --call-claude 1234      # Include AI assistance for conflicts
    $0 --direct 1234           # Output review directly to terminal
    $0 --dry-run 1234          # Preview the entire workflow

Output:
    The review report will be saved to: reports/review-pr-{NUMBER}.md
    (unless --direct is used)

EOF
}

# Execute preparation phase
prepare_pr() {
    local pr_number="$1"
    local prepare_args="$2"
    
    info "🔄 Phase 1: Preparing PR #$pr_number..."
    
    # Store current directory to ensure we return here
    local original_dir="$PWD"
    local prepare_cmd="$SCRIPT_DIR/pr-prepare.sh $prepare_args $pr_number"
    
    info "Executing: $prepare_cmd"
    
    local result=0
    if eval "$prepare_cmd"; then
        success "✅ PR preparation completed successfully"
        result=0
    else
        local exit_code=$?
        if [[ $exit_code -eq 1 ]]; then
            # Exit code 1 usually means conflicts that need resolution
            warn "⚠️  PR preparation completed with conflicts"
            info "Conflict resolution may be needed before proceeding to review"
            result=1
        else
            error "❌ PR preparation failed with exit code $exit_code"
            result=$exit_code
        fi
    fi
    
    # Always return to original directory
    cd "$original_dir"
    return $result
}

# Execute review phase
run_review() {
    local pr_number="$1"
    local review_args="$2"
    
    info "🔍 Phase 2: Running PR review analysis..."
    
    # Store current directory to ensure we return here
    local original_dir="$PWD"
    local review_cmd="$SCRIPT_DIR/run-review.sh $review_args $pr_number"
    
    info "Executing: $review_cmd"
    
    local result=0
    if eval "$review_cmd"; then
        success "✅ PR review analysis completed successfully"
        result=0
    else
        error "❌ PR review analysis failed"
        result=1
    fi
    
    # Always return to original directory
    cd "$original_dir"
    return $result
}

# Handle the case where preparation had conflicts
handle_preparation_conflicts() {
    local pr_number="$1"
    local auto_resolve="$2"
    local call_claude="$3"
    
    warn "Preparation phase encountered conflicts for PR #$pr_number"
    
    local plan_file="$SCRIPT_DIR/plans/plan-pr-$pr_number.md"
    if [[ -f "$plan_file" ]]; then
        info "📋 Conflict resolution plan available: $plan_file"
    fi
    
    echo
    info "Options to resolve conflicts:"
    info "  1. Try automatic resolution: $0 --auto-resolve $pr_number"
    info "  2. Get AI assistance: $0 --call-claude $pr_number"
    info "  3. Manual resolution:"
    info "     - Review plan: $plan_file"
    info "     - Use: ./resolve-conflicts.sh --status $pr_number"
    info "     - After resolution, run: $0 --skip-preparation $pr_number"
    
    echo
    read -p "Would you like to continue with the review analysis anyway? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        warn "Continuing with review despite preparation conflicts..."
        return 0
    else
        info "Stopping workflow. Resolve conflicts and run again."
        return 1
    fi
}

# Parse command line arguments
SKIP_SQUASH=false
SKIP_COMPILE=false
AUTO_RESOLVE=false
CALL_CLAUDE=false
DIRECT_MODE=false
FORCE=false
DRY_RUN=false
SKIP_PREPARATION=false
PR_NUMBER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        --skip-squash)
            SKIP_SQUASH=true
            shift
            ;;
        --skip-compile)
            SKIP_COMPILE=true
            shift
            ;;
        --auto-resolve)
            AUTO_RESOLVE=true
            shift
            ;;
        --call-claude)
            CALL_CLAUDE=true
            shift
            ;;
        --direct)
            DIRECT_MODE=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-preparation)
            SKIP_PREPARATION=true
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

# Build argument strings for sub-scripts
prepare_args=""
[[ "$SKIP_SQUASH" == "true" ]] && prepare_args="$prepare_args --skip-squash"
[[ "$SKIP_COMPILE" == "true" ]] && prepare_args="$prepare_args --skip-compile"
[[ "$AUTO_RESOLVE" == "true" ]] && prepare_args="$prepare_args --auto-resolve"
[[ "$CALL_CLAUDE" == "true" ]] && prepare_args="$prepare_args --call-claude"
[[ "$FORCE" == "true" ]] && prepare_args="$prepare_args --force"
[[ "$DRY_RUN" == "true" ]] && prepare_args="$prepare_args --dry-run"

review_args=""
[[ "$DIRECT_MODE" == "true" ]] && review_args="$review_args --direct"
[[ "$FORCE" == "true" ]] && review_args="$review_args --force"
[[ "$DRY_RUN" == "true" ]] && review_args="$review_args --dry-run"

# Main execution flow
main() {
    info "🚀 Starting complete PR review workflow for PR #$PR_NUMBER"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        warn "DRY RUN MODE - No actual changes will be made"
    fi
    
    local preparation_success=true
    
    # Phase 1: Preparation (unless skipped)
    if [[ "$SKIP_PREPARATION" == "false" ]]; then
        if ! prepare_pr "$PR_NUMBER" "$prepare_args"; then
            preparation_success=false
            
            # Handle conflicts if auto-resolve or call-claude wasn't already used
            if [[ "$AUTO_RESOLVE" == "false" && "$CALL_CLAUDE" == "false" ]]; then
                if ! handle_preparation_conflicts "$PR_NUMBER" "$AUTO_RESOLVE" "$CALL_CLAUDE"; then
                    exit 1
                fi
            else
                error "Preparation failed even with conflict resolution options"
                exit 1
            fi
        fi
    else
        info "⏭️  Skipping preparation phase as requested"
    fi
    
    # Phase 2: Review Analysis
    if [[ "$DRY_RUN" == "false" ]]; then
        echo
        info "🔍 Starting review analysis phase..."
        
        if ! run_review "$PR_NUMBER" "$review_args"; then
            error "Review analysis failed"
            exit 1
        fi
    fi
    
    # Final summary
    echo
    success "🎉 Complete PR review workflow finished for PR #$PR_NUMBER!"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        local report_file="$REPORTS_DIR/review-pr-$PR_NUMBER.md"
        
        if [[ "$DIRECT_MODE" == "false" && -f "$report_file" ]]; then
            info "📋 Review report saved to: $report_file"
            
            # Show file size
            local file_size
            file_size=$(wc -l < "$report_file")
            info "Report contains $file_size lines"
        fi
        
        if [[ "$preparation_success" == "false" ]]; then
            warn "⚠️  Note: Preparation phase had conflicts. Review the analysis carefully."
        fi
        
        info "Workflow summary:"
        info "  ✅ PR #$PR_NUMBER checked out and prepared"
        info "  ✅ Code review analysis completed"
        info "  📁 Working directory: $HOME/spring-ai"
    fi
}

# Run main function
main "$@"
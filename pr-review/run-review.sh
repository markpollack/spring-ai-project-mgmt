#!/usr/bin/env bash

set -Eeuo pipefail

# PR Review Analysis Runner
# Executes the PR review analysis using the prompt-pr-review.md template

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SPRING_AI_DIR="$HOME/spring-ai"
readonly REVIEW_DIR="$HOME/project-mgmt/spring-ai-project-mgmt/pr-review"
readonly REPORTS_DIR="$REVIEW_DIR/reports"
readonly PROMPT_FILE="$REVIEW_DIR/prompt-pr-review.md"

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

Run PR review analysis using the prompt-pr-review.md template after PR preparation.

This script:
1. Validates that the PR has been prepared (checked out and ready)
2. Sets up the proper environment in the Spring AI repository
3. Executes the PR review analysis using Claude Code
4. Saves the review report to reports/review-pr-{NUMBER}.md

Arguments:
    PR_NUMBER           The GitHub PR number to review

Options:
    -h, --help         Show this help message
    -o, --output FILE  Custom output file (default: reports/review-pr-{PR}.md)
    -f, --force        Overwrite existing review report
    --direct           Run analysis directly without saving to file
    --dry-run          Show what would be done without executing

Examples:
    $0 1234                           # Run review for PR #1234
    $0 --output custom-review.md 1234 # Save to custom file
    $0 --direct 1234                  # Run analysis directly in terminal
    $0 --dry-run 1234                 # Preview what would happen

Prerequisites:
    - PR must be prepared using pr-prepare.sh first
    - Claude Code CLI must be installed and authenticated
    - Spring AI repository must be at $SPRING_AI_DIR

Environment Variables:
    CLAUDE_MODEL        Claude model to use (default: detected automatically)
    SPRING_AI_DIR       Override default Spring AI directory location

EOF
}

# Check prerequisites
check_prerequisites() {
    local pr_number="$1"
    
    # Check if Spring AI directory exists
    if [[ ! -d "$SPRING_AI_DIR" ]]; then
        error "Spring AI directory not found: $SPRING_AI_DIR"
        error "Please run pr-prepare.sh first to set up the repository"
        exit 1
    fi
    
    # Check if it's a git repository
    if [[ ! -d "$SPRING_AI_DIR/.git" ]]; then
        error "Not a git repository: $SPRING_AI_DIR"
        exit 1
    fi
    
    # Check if Claude Code is available
    if ! command -v claude &> /dev/null; then
        error "Claude Code CLI not found. Please install it first."
        error "Visit: https://claude.ai/code for installation instructions"
        exit 1
    fi
    
    # Check if prompt file exists
    if [[ ! -f "$PROMPT_FILE" ]]; then
        error "PR review prompt not found: $PROMPT_FILE"
        exit 1
    fi
    
    # Navigate to Spring AI directory
    cd "$SPRING_AI_DIR"
    
    # Check if we're on the right branch (should be pr-{number})
    local current_branch
    current_branch=$(git branch --show-current)
    local expected_branch="pr-$pr_number"
    
    if [[ "$current_branch" != "$expected_branch" ]]; then
        warn "Current branch is '$current_branch', expected '$expected_branch'"
        info "Available branches with 'pr-' prefix:"
        git branch | grep "pr-" || echo "  No PR branches found"
        echo
        read -p "Continue with current branch? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Please checkout the correct PR branch first"
            exit 1
        fi
    fi
    
    # Check if there are uncommitted changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
        warn "There are uncommitted changes in the repository"
        git status --short
        echo
        read -p "Continue anyway? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Please commit or stash changes first"
            exit 1
        fi
    fi
    
    success "Prerequisites check passed"
}

# Prepare the environment for PR review
prepare_environment() {
    local pr_number="$1"
    
    info "Preparing environment for PR #$pr_number review..."
    
    cd "$SPRING_AI_DIR"
    
    # Set up environment variables that the prompt expects
    export PR_NUMBER="$pr_number"
    
    # Verify GitHub CLI authentication (the prompt expects this)
    if ! gh auth status >/dev/null 2>&1; then
        error "GitHub CLI not authenticated. Please run: gh auth login"
        exit 1
    fi
    
    # Fetch latest upstream to ensure accurate comparison
    info "Fetching latest upstream changes..."
    git fetch origin >/dev/null 2>&1 || warn "Could not fetch upstream changes"
    
    success "Environment prepared"
}

# Generate the Claude Code command
generate_claude_command() {
    local pr_number="$1"
    local output_file="$2"
    local direct_mode="$3"
    
    # Read the prompt template
    local prompt_content
    prompt_content=$(cat "$PROMPT_FILE")
    
    # Create the command
    local claude_cmd="claude"
    
    # Add model specification if available
    if [[ -n "${CLAUDE_MODEL:-}" ]]; then
        claude_cmd="$claude_cmd --model $CLAUDE_MODEL"
    fi
    
    # Prepare the prompt with PR context
    local full_prompt="You are conducting a PR code review for Spring AI project PR #$pr_number.

Please execute the following PR review analysis prompt:

---

$prompt_content

---

Current working directory: $(pwd)
PR Number: $pr_number
Current branch: $(git branch --show-current)
Repository: $(git remote get-url origin 2>/dev/null || echo 'unknown')

Please execute all the steps in the prompt above systematically and provide a comprehensive review report."
    
    if [[ "$direct_mode" == "true" ]]; then
        # Direct execution - output to terminal
        echo "$claude_cmd \"$full_prompt\""
    else
        # Save to file
        echo "$claude_cmd \"$full_prompt\" > \"$output_file\""
    fi
}

# Run the PR review analysis
run_pr_review() {
    local pr_number="$1"
    local output_file="$2"
    local direct_mode="$3"
    local force_overwrite="$4"
    local dry_run="$5"
    
    # Check if output file exists and handle force/overwrite
    if [[ "$direct_mode" == "false" && -f "$output_file" && "$force_overwrite" == "false" ]]; then
        error "Review report already exists: $output_file"
        error "Use --force to overwrite or choose a different output file"
        exit 1
    fi
    
    # Generate the command
    local claude_command
    claude_command=$(generate_claude_command "$pr_number" "$output_file" "$direct_mode")
    
    if [[ "$dry_run" == "true" ]]; then
        info "[DRY RUN] Would execute PR review analysis"
        info "[DRY RUN] Working directory: $SPRING_AI_DIR"
        info "[DRY RUN] Command: $claude_command"
        info "[DRY RUN] Environment variables:"
        info "[DRY RUN]   PR_NUMBER=$pr_number"
        return 0
    fi
    
    # Execute the review
    info "Running PR review analysis for PR #$pr_number..."
    info "This may take a few minutes..."
    
    cd "$SPRING_AI_DIR"
    
    # Set environment for the prompt
    export PR_NUMBER="$pr_number"
    
    if [[ "$direct_mode" == "true" ]]; then
        info "Running analysis in direct mode (output to terminal)..."
        eval "$claude_command"
    else
        info "Running analysis and saving to: $output_file"
        
        # Create reports directory if it doesn't exist
        mkdir -p "$(dirname "$output_file")"
        
        # Add header to the report
        cat > "$output_file" << EOF
# Spring AI PR #$pr_number Review Report

Generated: $(date)
Reviewer: Claude Code AI Assistant
Repository: $(git remote get-url origin 2>/dev/null || echo 'unknown')
Branch: $(git branch --show-current)
Working Directory: $(pwd)

---

EOF
        
        # Run the analysis and append to file
        eval "$claude_command" >> "$output_file" 2>&1
        
        if [[ $? -eq 0 ]]; then
            success "Review report saved to: $output_file"
            
            # Show file size and preview
            local file_size
            file_size=$(wc -l < "$output_file")
            info "Report contains $file_size lines"
            
            # Show first few lines as preview
            info "Report preview:"
            echo "----------------------------------------"
            head -20 "$output_file" | tail -15
            echo "----------------------------------------"
            info "Full report: $output_file"
        else
            error "Failed to generate review report"
            exit 1
        fi
    fi
}

# Display post-review actions
show_next_steps() {
    local pr_number="$1"
    local output_file="$2"
    local direct_mode="$3"
    
    echo
    info "PR review analysis completed!"
    
    if [[ "$direct_mode" == "false" ]]; then
        info "📋 Review report: $output_file"
        
        # Suggest viewing commands
        info "View the report with:"
        if command -v bat &> /dev/null; then
            info "  bat \"$output_file\""
        fi
        info "  less \"$output_file\""
        info "  cat \"$output_file\""
    fi
    
    info "Next steps:"
    info "  1. Review the analysis findings"
    info "  2. Address any critical issues identified"
    info "  3. Consider the recommendations provided"
    info "  4. Test the build: fb or ./gradlew build"
    
    # Check if there are conflict plans that might be relevant
    local plan_file="$REVIEW_DIR/plans/plan-pr-$pr_number.md"
    if [[ -f "$plan_file" ]]; then
        info "  📋 Related conflict plan: $plan_file"
    fi
}

# Parse command line arguments
OUTPUT_FILE=""
FORCE_OVERWRITE=false
DIRECT_MODE=false
DRY_RUN=false
PR_NUMBER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_OVERWRITE=true
            shift
            ;;
        --direct)
            DIRECT_MODE=true
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

# Set default output file if not specified and not in direct mode
if [[ -z "$OUTPUT_FILE" && "$DIRECT_MODE" == "false" ]]; then
    OUTPUT_FILE="$REPORTS_DIR/review-pr-$PR_NUMBER.md"
fi

# Create reports directory
mkdir -p "$REPORTS_DIR"

# Main execution flow
main() {
    info "Starting PR review analysis for PR #$PR_NUMBER"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        warn "DRY RUN MODE - No actual analysis will be performed"
    fi
    
    check_prerequisites "$PR_NUMBER"
    prepare_environment "$PR_NUMBER"
    run_pr_review "$PR_NUMBER" "$OUTPUT_FILE" "$DIRECT_MODE" "$FORCE_OVERWRITE" "$DRY_RUN"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        show_next_steps "$PR_NUMBER" "$OUTPUT_FILE" "$DIRECT_MODE"
    fi
    
    success "PR review analysis workflow completed!"
}

# Run main function
main "$@"
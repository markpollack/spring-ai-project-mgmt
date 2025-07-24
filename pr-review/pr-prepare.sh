#!/usr/bin/env bash

set -Eeuo pipefail

# PR Preparation Script for Spring AI Project Reviews
# This script automates the workflow: checkout PR -> compile -> squash -> rebase

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SPRING_AI_REPO="spring-projects/spring-ai"
readonly SPRING_AI_DIR="$SCRIPT_DIR/spring-ai"
readonly UPSTREAM_REMOTE="upstream"  # Use upstream remote for spring-projects repo
readonly MAIN_BRANCH="main"
readonly PLANS_DIR="$SCRIPT_DIR/plans"
readonly TEMPLATES_DIR="$SCRIPT_DIR/templates"

# Create required directories if they don't exist
mkdir -p "$PLANS_DIR" "$TEMPLATES_DIR"

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

# Execute git commands in spring-ai directory without changing working directory
git_in_spring_ai() {
    (cd "$SPRING_AI_DIR" && "$@")
}

# Execute commands in spring-ai directory without changing working directory
exec_in_spring_ai() {
    (cd "$SPRING_AI_DIR" && eval "$*")
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS] <PR_NUMBER>

Prepare a Spring AI PR for review by:
1. Ensuring spring-ai repo exists and is updated
2. Checking out the PR
3. Running compilation check (fb alias)
4. Squashing commits (optional)
5. Rebasing against upstream main

Arguments:
    PR_NUMBER           The GitHub PR number to checkout and prepare

Options:
    -h, --help         Show this help message
    -s, --skip-squash  Skip the commit squashing step
    -f, --force        Force operations (overwrite existing branches)
    --skip-compile     Skip the compilation check
    --dry-run          Show what would be done without executing
    --auto-resolve     Attempt automatic conflict resolution for simple cases
    --call-claude      Call Claude Code for complex conflict resolution

Examples:
    $0 1234                    # Prepare PR #1234 with full workflow
    $0 --skip-squash 1234      # Prepare PR #1234 without squashing
    $0 --auto-resolve 1234     # Auto-resolve simple conflicts
    $0 --call-claude 1234      # Get AI assistance for conflicts
    $0 --dry-run 1234          # Show what would be done for PR #1234

Environment:
    The script expects your 'fb' alias to be available for compilation checks.
    For Spring AI (Maven project): mvnd > mvnw > mvn (in order of preference)
    Set SPRING_AI_DIR environment variable to override the default location.

EOF
}

# Cleanup function for error handling
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        error "Script failed with exit code $exit_code"
        warn "You may need to manually clean up any partial changes"
    fi
}

trap cleanup EXIT

# Parse command line arguments
SKIP_SQUASH=false
FORCE=false
SKIP_COMPILE=false
DRY_RUN=false
AUTO_RESOLVE=false
CALL_CLAUDE=false
PR_NUMBER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -s|--skip-squash)
            SKIP_SQUASH=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        --skip-compile)
            SKIP_COMPILE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
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

# Dry run function
execute_or_dry_run() {
    local cmd="$1"
    local description="$2"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would execute: $description"
        info "[DRY RUN] Command: $cmd"
    else
        info "Executing: $description"
        eval "$cmd"
    fi
}

# Check if spring-ai repository exists and is properly configured
setup_spring_ai_repo() {
    info "Setting up Spring AI repository..."
    
    if [[ ! -d "$SPRING_AI_DIR" ]]; then
        warn "Spring AI repository not found at $SPRING_AI_DIR"
        info "Cloning Spring AI repository..."
        execute_or_dry_run "git clone https://github.com/$SPRING_AI_REPO.git \"$SPRING_AI_DIR\"" "Clone Spring AI repository"
    fi
    
    if [[ "$DRY_RUN" == "false" ]]; then
        cd "$SPRING_AI_DIR"
        
        # Verify it's a git repository
        if [[ ! -d ".git" ]]; then
            error "Directory $SPRING_AI_DIR exists but is not a git repository"
            exit 1
        fi
        
        # Ensure upstream remote exists
        if ! git remote get-url "$UPSTREAM_REMOTE" &>/dev/null; then
            info "Adding upstream remote..."
            git remote add "$UPSTREAM_REMOTE" "https://github.com/$SPRING_AI_REPO.git"
        fi
        
        # Fetch latest changes
        info "Fetching latest changes from upstream..."
        git fetch "$UPSTREAM_REMOTE"
        
        # Switch to main branch and update
        info "Switching to $MAIN_BRANCH branch..."
        git checkout "$MAIN_BRANCH"
        git pull "$UPSTREAM_REMOTE" "$MAIN_BRANCH"
    else
        info "[DRY RUN] Would navigate to $SPRING_AI_DIR and update repository"
    fi
}

# Checkout the PR
checkout_pr() {
    info "Checking out PR #$PR_NUMBER..."
    
    local pr_branch="pr-$PR_NUMBER"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        cd "$SPRING_AI_DIR"
        
        # Check if PR branch already exists
        if git show-ref --verify --quiet "refs/heads/$pr_branch"; then
            if [[ "$FORCE" == "true" ]]; then
                warn "Branch $pr_branch already exists, deleting due to --force flag"
                git branch -D "$pr_branch"
            else
                error "Branch $pr_branch already exists. Use --force to overwrite or delete manually."
                exit 1
            fi
        fi
        
        # Checkout the PR using GitHub CLI
        execute_or_dry_run "gh pr checkout $PR_NUMBER" "Checkout PR #$PR_NUMBER"
        
        # Rename branch to our convention if gh created a different name
        local current_branch
        current_branch=$(git branch --show-current)
        if [[ "$current_branch" != "$pr_branch" ]]; then
            execute_or_dry_run "git branch -m \"$current_branch\" \"$pr_branch\"" "Rename branch to $pr_branch"
        fi
    else
        info "[DRY RUN] Would checkout PR #$PR_NUMBER into branch $pr_branch"
    fi
}

# Check if build is needed based on code changes
check_build_needed() {
    local pr_number="$1"
    local build_cache_file="$SCRIPT_DIR/.build_cache_pr_$pr_number"
    
    cd "$SPRING_AI_DIR"
    
    # Get current commit hash and modification times of key files
    local current_commit=$(git rev-parse HEAD)
    local pom_checksum=""
    local java_checksum=""
    
    # Generate checksums for Java files and pom.xml files
    if command -v find &> /dev/null; then
        pom_checksum=$(find . -name "pom.xml" -type f -exec stat -c "%Y" {} \; 2>/dev/null | sort | md5sum | cut -d' ' -f1)
        java_checksum=$(find . -name "*.java" -type f -newer "$build_cache_file" 2>/dev/null | wc -l)
    fi
    
    # Check if cache file exists and is valid
    if [[ -f "$build_cache_file" ]]; then
        local cached_commit=$(head -1 "$build_cache_file" 2>/dev/null)
        local cached_pom_checksum=$(sed -n '2p' "$build_cache_file" 2>/dev/null)
        
        if [[ "$current_commit" == "$cached_commit" && "$pom_checksum" == "$cached_pom_checksum" && "$java_checksum" == "0" ]]; then
            info "✅ Build cache hit - no code changes detected since last successful build"
            return 1  # No build needed
        fi
    fi
    
    info "📝 Code changes detected - build required"
    return 0  # Build needed
}

# Save successful build state
save_build_cache() {
    local pr_number="$1"
    local build_cache_file="$SCRIPT_DIR/.build_cache_pr_$pr_number"
    
    cd "$SPRING_AI_DIR"
    
    local current_commit=$(git rev-parse HEAD)
    local pom_checksum=""
    
    if command -v find &> /dev/null; then
        pom_checksum=$(find . -name "pom.xml" -type f -exec stat -c "%Y" {} \; 2>/dev/null | sort | md5sum | cut -d' ' -f1)
    fi
    
    # Save build state
    cat > "$build_cache_file" << EOF
$current_commit
$pom_checksum
$(date)
EOF
    
    info "💾 Build cache updated for PR #$pr_number"
}

# Run compilation check using 'fb' alias with caching
run_compile_check() {
    if [[ "$SKIP_COMPILE" == "true" ]]; then
        info "Skipping compilation check as requested"
        return 0
    fi
    
    # Check if build is needed
    if ! check_build_needed "$PR_NUMBER"; then
        success "⏭️  Skipping build - no changes since last successful build"
        return 0
    fi
    
    info "🔨 Running compilation check..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        cd "$SPRING_AI_DIR"
        
        # Check if 'fb' alias exists
        if ! command -v fb &> /dev/null && ! alias fb &> /dev/null; then
            warn "'fb' alias not found. Attempting Maven build instead..."
            
            # Spring AI uses Maven - prefer mvnd for faster builds, fallback to mvnw
            if command -v mvnd &> /dev/null; then
                info "Using mvnd for faster Maven build..."
                if execute_or_dry_run "mvnd clean compile test-compile" "Run Maven build with mvnd"; then
                    save_build_cache "$PR_NUMBER"
                fi
            elif [[ -x "./mvnw" ]]; then
                info "Using Maven wrapper (mvnw)..."
                if execute_or_dry_run "./mvnw clean compile test-compile" "Run Maven build with mvnw"; then
                    save_build_cache "$PR_NUMBER"
                fi
            else
                warn "Neither mvnd nor mvnw found, trying system maven..."
                if execute_or_dry_run "mvn clean compile test-compile" "Run Maven build with system mvn"; then
                    save_build_cache "$PR_NUMBER"
                fi
            fi
        else
            if execute_or_dry_run "fb" "Run compilation check with fb alias"; then
                save_build_cache "$PR_NUMBER"
            fi
        fi
    else
        info "[DRY RUN] Would run compilation check with 'fb' alias or Maven build"
    fi
}

# Squash commits in the PR
squash_commits() {
    if [[ "$SKIP_SQUASH" == "true" ]]; then
        info "Skipping commit squashing as requested"
        return 0
    fi
    
    info "Squashing commits..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        cd "$SPRING_AI_DIR"
        
        # Count commits ahead of main
        local commits_ahead
        commits_ahead=$(git rev-list --count "$UPSTREAM_REMOTE/$MAIN_BRANCH..HEAD")
        
        if [[ "$commits_ahead" -le 1 ]]; then
            info "Only $commits_ahead commit(s) ahead of main, no squashing needed"
            return 0
        fi
        
        info "Found $commits_ahead commits ahead of main, squashing automatically..."
        
        # Get the first commit message for the squashed commit
        local first_commit_msg
        first_commit_msg=$(git log --format="%s" HEAD~$((commits_ahead-1)) -1)
        
        # Create automatic squash script
        local squash_script="/tmp/squash_commits_$$.sh"
        cat > "$squash_script" << 'EOF'
#!/bin/bash
# Automatic squash: keep first as pick, change rest to squash
sed -i '1!s/^pick/squash/' "$1"
EOF
        chmod +x "$squash_script"
        
        # Perform automatic rebase with squashing
        info "Performing automatic squash rebase..."
        if GIT_SEQUENCE_EDITOR="$squash_script" git rebase -i HEAD~$commits_ahead; then
            success "Commits squashed successfully"
            rm -f "$squash_script"
        else
            warn "Squash rebase encountered conflicts"
            rm -f "$squash_script"
            
            # If auto-resolve is enabled, try to resolve conflicts
            if [[ "$AUTO_RESOLVE" == "true" ]]; then
                info "Attempting automatic conflict resolution during squash..."
                if auto_resolve_simple_conflicts "$PR_NUMBER"; then
                    info "Conflicts resolved, continuing rebase..."
                    if git rebase --continue; then
                        success "Squash rebase completed after automatic conflict resolution"
                        return 0
                    else
                        error "Failed to continue rebase after conflict resolution"
                        return 1
                    fi
                else
                    error "Automatic conflict resolution failed during squash"
                    return 1
                fi
            else
                error "Failed to squash commits automatically"
                return 1
            fi
        fi
    else
        info "[DRY RUN] Would squash commits if there are multiple commits ahead of main"
    fi
}

# Analyze conflict types and generate resolution strategy using Python
analyze_conflicts() {
    local pr_number="$1"
    
    info "Analyzing rebase conflicts for PR #$pr_number..."
    
    # Call Python conflict analyzer
    local python_output
    python_output=$(cd "$SPRING_AI_DIR" && python3 "$SCRIPT_DIR/conflict_analyzer.py" "$SCRIPT_DIR" "$pr_number" 2>&1)
    local exit_code=$?
    
    # Show Python output (excluding JSON)
    echo "$python_output" | grep -v "^JSON_OUTPUT:" || true
    
    if [[ $exit_code -eq 0 ]]; then
        # No conflicts detected
        return 0
    else
        # Conflicts detected - Python script generated the plan
        return 1
    fi
}

# Generate a detailed conflict resolution plan (DEPRECATED - now handled by Python)
generate_conflict_plan() {
    info "Conflict plan generation now handled by conflict_analyzer.py"
    return 0
}

# Attempt automatic resolution of simple conflicts
auto_resolve_simple_conflicts() {
    local pr_number="$1"
    local resolved_count=0
    
    info "Attempting automatic resolution of simple conflicts..."
    
    # Get conflicted files
    git status --porcelain | grep "^UU\|^AA\|^DD" | cut -c4- | while IFS= read -r file; do
        if [[ -f "$file" ]]; then
            case "$file" in
                *.md)
                    info "Using Claude Code to resolve Markdown conflict: $file"
                    # Try Claude Code first, fallback to simple resolution
                    if auto_resolve_with_claude "$file" || auto_resolve_markdown "$file"; then
                        git add "$file"
                        ((resolved_count++))
                    fi
                    ;;
                *.properties)
                    info "Using Claude Code to resolve properties conflict: $file"
                    # Try Claude Code first, fallback to simple resolution
                    if auto_resolve_with_claude "$file" || auto_resolve_properties "$file"; then
                        git add "$file"
                        ((resolved_count++))
                    fi
                    ;;
                *.java)
                    info "Using Claude Code to resolve Java conflict: $file"
                    # Use Claude Code AI to intelligently resolve the conflict
                    if auto_resolve_with_claude "$file"; then
                        git add "$file"
                        ((resolved_count++))
                        info "Claude Code resolved conflict in: $file"
                    fi
                    ;;
                */pom.xml|*/build.gradle)
                    info "Auto-resolving build file: $file (taking upstream version)"
                    # For build files, usually take upstream to avoid version conflicts
                    git checkout --theirs "$file"
                    git add "$file"
                    ((resolved_count++))
                    ;;
            esac
        fi
    done
    
    if [[ $resolved_count -gt 0 ]]; then
        success "Auto-resolved $resolved_count simple conflicts"
        return 0
    else
        warn "No simple conflicts could be auto-resolved"
        return 1
    fi
}

# Auto-resolve markdown conflicts by merging content intelligently
auto_resolve_markdown() {
    local file="$1"
    local temp_file="/tmp/$(basename "$file").resolved"
    
    # Simple strategy: remove conflict markers and try to merge content
    # This is a basic implementation - could be enhanced with more intelligence
    if grep -q "^<<<<<<< \|^>>>>>>> \|^======= " "$file"; then
        # Remove conflict markers and try to merge
        sed '/^<<<<<<< /d; /^>>>>>>> /d; /^======= /d' "$file" > "$temp_file"
        
        # Basic validation - check if result looks reasonable
        if [[ -s "$temp_file" ]] && [[ $(wc -l < "$temp_file") -gt 0 ]]; then
            cp "$temp_file" "$file"
            rm -f "$temp_file"
            return 0
        fi
    fi
    
    rm -f "$temp_file"
    return 1
}

# Auto-resolve properties file conflicts
auto_resolve_properties() {
    local file="$1"
    local temp_file="/tmp/$(basename "$file").resolved"
    
    # For properties files, we'll take the newer (upstream) version
    # This is often safer for version numbers and dependencies
    if grep -q "^<<<<<<< \|^>>>>>>> \|^======= " "$file"; then
        # Extract the upstream version (between ======= and >>>>>>> )
        awk '/^======= /,/^>>>>>>> / {if (!/^======= / && !/^>>>>>>> /) print}' "$file" > "$temp_file"
        
        # Extract non-conflicted parts
        awk '!/^<<<<<<< /,/^>>>>>>> / {if (!/^<<<<<<< / && !/^======= / && !/^>>>>>>> /) print}' "$file" >> "$temp_file"
        
        if [[ -s "$temp_file" ]]; then
            sort -u "$temp_file" > "$file"
            rm -f "$temp_file"
            return 0
        fi
    fi
    
    rm -f "$temp_file"
    return 1
}

# Use Claude Code AI to intelligently resolve conflicts
auto_resolve_with_claude() {
    local file="$1"
    local temp_file="/tmp/$(basename "$file").resolved"
    
    # Check if Claude Code CLI is available
    if ! command -v claude &> /dev/null; then
        info "Claude Code CLI not available, skipping AI resolution for $file"
        return 1
    fi
    
    # Check if this file has conflicts
    if ! grep -q '^<<<<<<<\|^>>>>>>>\|^=======' "$file"; then
        return 1
    fi
    
    info "Asking Claude Code to resolve conflicts in: $file"
    
    # Create a prompt for Claude Code to resolve the conflict
    local claude_prompt="Please resolve this Git merge conflict intelligently.

IMPORTANT: Output ONLY the clean file content - no explanations, no markdown code blocks, no comments.

The file contains Git conflict markers (<<<<<<< HEAD, =======, >>>>>>> branch).
Analyze the conflicting changes and resolve them appropriately:
- If both changes are compatible, merge them
- If they conflict, choose the better/newer version
- Remove all conflict markers

File content with conflicts:"
    
    # Call Claude Code to resolve the conflict
    # Create a combined input with prompt and file content
    local combined_input="/tmp/claude_input_$$.txt"
    echo "$claude_prompt" > "$combined_input"
    echo "" >> "$combined_input"
    cat "$file" >> "$combined_input"
    
    if claude --print < "$combined_input" > "$temp_file" 2>/dev/null; then
        # Strip markdown code fences if present
        if grep -q "^```" "$temp_file"; then
            sed -i '/^```/d' "$temp_file"
        fi
        
        # Verify the result doesn't still have conflict markers
        if ! grep -q '^<<<<<<<\|^>>>>>>>\|^=======' "$temp_file"; then
            # Verify the file is not empty and seems reasonable
            if [[ -s "$temp_file" ]] && (( $(wc -l < "$temp_file") > $(wc -l < "$file") / 2 )); then
                mv "$temp_file" "$file"
                rm -f "$combined_input"
                info "Claude Code successfully resolved conflicts in: $file"
                return 0
            else
                warn "Claude Code resolution resulted in suspicious output for: $file"
            fi
        else
            warn "Claude Code output still contains conflict markers for: $file"
        fi
    else
        warn "Claude Code failed to process: $file"
    fi
    
    # Clean up and return failure
    rm -f "$temp_file" "$combined_input"
    return 1
}

# Call Claude Code for intelligent conflict resolution
call_claude_for_conflicts() {
    local pr_number="$1"
    info "Claude Code integration available - using template-based prompts"
    info "For AI assistance, run: claude 'Help resolve merge conflicts in PR #$pr_number'"
    return 1
}

# Rebase against upstream main  
rebase_upstream() {
    info "Rebasing against upstream/$MAIN_BRANCH..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would rebase against upstream/$MAIN_BRANCH"
        return 0
    fi
    
    cd "$SPRING_AI_DIR"
    
    # Fetch latest upstream changes
    git fetch "$UPSTREAM_REMOTE"
    
    # Rebase against upstream main
    execute_or_dry_run "git rebase \"$UPSTREAM_REMOTE/$MAIN_BRANCH\"" "Rebase against upstream/$MAIN_BRANCH"
    
    # Check if there are any conflicts and handle them intelligently
    if ! analyze_conflicts "$PR_NUMBER"; then
        success "Rebase completed successfully with no conflicts"
        return 0
    fi
    
    # Conflicts detected - handle them
    warn "Rebase conflicts detected for PR #$PR_NUMBER"
    
    local resolution_attempted=false
    
    # Try automatic resolution if requested
    if [[ "$AUTO_RESOLVE" == "true" ]]; then
        if auto_resolve_simple_conflicts "$PR_NUMBER"; then
            info "Some conflicts were auto-resolved, attempting to continue rebase..."
            if git rebase --continue; then
                success "Rebase completed successfully after auto-resolution"
                return 0
            else
                warn "Auto-resolution helped but rebase still has issues"
            fi
        fi
        resolution_attempted=true
    fi
    
    # Call Claude Code if requested
    if [[ "$CALL_CLAUDE" == "true" ]]; then
        call_claude_for_conflicts "$PR_NUMBER"
        resolution_attempted=true
    fi
    
    # Provide guidance based on resolution attempts
    if [[ "$resolution_attempted" == "false" ]]; then
        error "Rebase conflicts detected. Resolution options:"
        info "  1. Auto-resolve simple conflicts: $0 --auto-resolve $PR_NUMBER"
        info "  2. Get AI assistance: $0 --call-claude $PR_NUMBER"
        info "  3. Manual resolution - Review plan: $PLANS_DIR/plan-pr-$PR_NUMBER.md"
    else
        error "Automatic resolution unsuccessful. Review plan: $PLANS_DIR/plan-pr-$PR_NUMBER.md"
    fi
    
    exit 1
}

# Display final status
show_final_status() {
    info "PR preparation complete!"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        cd "$SPRING_AI_DIR"
        
        success "Repository: $(pwd)"
        success "Current branch: $(git branch --show-current)"
        success "Commits ahead of upstream/$MAIN_BRANCH: $(git rev-list --count "$UPSTREAM_REMOTE/$MAIN_BRANCH..HEAD")"
        
        info "Ready for PR review. You can now run your PR review analysis."
        
        # Check if there's a plan file for this PR
        local plan_file="$PLANS_DIR/plan-pr-$PR_NUMBER.md"
        if [[ -f "$plan_file" ]]; then
            info "📋 Conflict resolution plan available: $plan_file"
        fi
        
        info "Next steps:"
        info "  1. Set PR_NUMBER environment variable: export PR_NUMBER=$PR_NUMBER"
        info "  2. Run your PR review analysis script"
    else
        info "[DRY RUN] Preparation workflow completed successfully"
    fi
}

# Main execution flow
main() {
    info "Starting PR preparation for Spring AI PR #$PR_NUMBER"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        warn "DRY RUN MODE - No actual changes will be made"
    fi
    
    # Execute workflow steps
    setup_spring_ai_repo
    checkout_pr
    run_compile_check
    squash_commits
    rebase_upstream
    show_final_status
    
    success "PR #$PR_NUMBER is ready for review!"
}

# Run main function
main "$@"
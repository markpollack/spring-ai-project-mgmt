#!/usr/bin/env bash

# GitHub Issues Collection - Implementation Comparison Test
# Compares the Java (JBang) and Bash implementations side-by-side

set -Eeuo pipefail

# Script configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PARENT_DIR="$(dirname "$SCRIPT_DIR")"
readonly BASH_SCRIPT="$PARENT_DIR/collect_github_issues.sh"
readonly JAVA_SCRIPT="$SCRIPT_DIR/CollectGithubIssues.java"
readonly COMPARISON_DIR="$SCRIPT_DIR/comparison_results"
readonly LOG_FILE="$COMPARISON_DIR/comparison.log"

# Test configuration
readonly TEST_REPO="spring-projects/spring-ai"
readonly TEST_BATCH_SIZE=50
readonly TEST_TIMEOUT=300  # 5 minutes max per test

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

info() {
    log "${BLUE}[INFO]${NC} $*"
}

warn() {
    log "${YELLOW}[WARN]${NC} $*"
}

error() {
    log "${RED}[ERROR]${NC} $*"
}

success() {
    log "${GREEN}[SUCCESS]${NC} $*"
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        error "Comparison test failed with exit code $exit_code"
    fi
    
    # Clean up any temporary files
    rm -f /tmp/bash_test_output.txt /tmp/java_test_output.txt
    
    exit $exit_code
}

trap cleanup EXIT

# Helper functions
check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check if bash script exists
    if [[ ! -f "$BASH_SCRIPT" ]]; then
        error "Bash script not found: $BASH_SCRIPT"
        return 1
    fi
    
    # Check if Java script exists
    if [[ ! -f "$JAVA_SCRIPT" ]]; then
        error "Java script not found: $JAVA_SCRIPT"
        return 1
    fi
    
    # Check if jbang is available
    if ! command -v jbang &> /dev/null && [[ ! -f "/home/mark/.sdkman/candidates/jbang/current/bin/jbang" ]]; then
        error "jbang is not installed or not in PATH"
        return 1
    fi
    
    # Check if GitHub token is set
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        error "GITHUB_TOKEN environment variable is not set"
        return 1
    fi
    
    success "Prerequisites check passed"
}

setup_test_environment() {
    info "Setting up test environment..."
    
    # Create comparison directory
    mkdir -p "$COMPARISON_DIR"
    
    # Create subdirectories for each implementation
    mkdir -p "$COMPARISON_DIR/bash_results"
    mkdir -p "$COMPARISON_DIR/java_results"
    
    # Initialize log file
    echo "GitHub Issues Collection - Implementation Comparison Test" > "$LOG_FILE"
    echo "Started at: $(date)" >> "$LOG_FILE"
    echo "=============================================" >> "$LOG_FILE"
    
    success "Test environment setup complete"
}

run_bash_implementation() {
    info "Running Bash implementation..."
    
    local start_time=$(date +%s)
    local bash_dir="$COMPARISON_DIR/bash_results"
    
    # Change to parent directory to run bash script
    cd "$PARENT_DIR"
    
    # Run bash script with timeout
    if timeout $TEST_TIMEOUT ./collect_github_issues.sh \
        --repo "$TEST_REPO" \
        --batch-size "$TEST_BATCH_SIZE" \
        --dry-run \
        --verbose > "$bash_dir/output.log" 2>&1; then
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        success "Bash implementation completed in ${duration}s"
        echo "$duration" > "$bash_dir/duration.txt"
        
        # If not dry run, move results
        if [[ -d "issues" ]]; then
            mv issues "$bash_dir/" 2>/dev/null || true
        fi
        
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        error "Bash implementation failed after ${duration}s"
        echo "FAILED" > "$bash_dir/duration.txt"
        return 1
    fi
}

run_java_implementation() {
    info "Running Java implementation..."
    
    local start_time=$(date +%s)
    local java_dir="$COMPARISON_DIR/java_results"
    
    # Change to scripts directory
    cd "$SCRIPT_DIR"
    
    # Run Java script with timeout
    if timeout $TEST_TIMEOUT jbang CollectGithubIssues.java \
        --repo "$TEST_REPO" \
        --batch-size "$TEST_BATCH_SIZE" \
        --dry-run \
        --verbose > "$java_dir/output.log" 2>&1; then
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        success "Java implementation completed in ${duration}s"
        echo "$duration" > "$java_dir/duration.txt"
        
        # If not dry run, move results
        if [[ -d "issues" ]]; then
            mv issues "$java_dir/" 2>/dev/null || true
        fi
        
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        error "Java implementation failed after ${duration}s"
        echo "FAILED" > "$java_dir/duration.txt"
        return 1
    fi
}

compare_outputs() {
    info "Comparing outputs..."
    
    local bash_log="$COMPARISON_DIR/bash_results/output.log"
    local java_log="$COMPARISON_DIR/java_results/output.log"
    local comparison_file="$COMPARISON_DIR/output_comparison.txt"
    
    echo "OUTPUT COMPARISON" > "$comparison_file"
    echo "=================" >> "$comparison_file"
    echo "" >> "$comparison_file"
    
    # Compare file existence
    if [[ -f "$bash_log" && -f "$java_log" ]]; then
        echo "✓ Both implementations produced output logs" >> "$comparison_file"
        
        # Extract key metrics from logs
        local bash_issues=$(grep -o "Total.*issues" "$bash_log" | tail -1 || echo "Not found")
        local java_issues=$(grep -o "Total.*issues" "$java_log" | tail -1 || echo "Not found")
        
        echo "" >> "$comparison_file"
        echo "ISSUE COUNTS:" >> "$comparison_file"
        echo "Bash: $bash_issues" >> "$comparison_file"
        echo "Java: $java_issues" >> "$comparison_file"
        
        # Compare performance
        local bash_duration=$(cat "$COMPARISON_DIR/bash_results/duration.txt" 2>/dev/null || echo "FAILED")
        local java_duration=$(cat "$COMPARISON_DIR/java_results/duration.txt" 2>/dev/null || echo "FAILED")
        
        echo "" >> "$comparison_file"
        echo "PERFORMANCE:" >> "$comparison_file"
        echo "Bash duration: ${bash_duration}s" >> "$comparison_file"
        echo "Java duration: ${java_duration}s" >> "$comparison_file"
        
        if [[ "$bash_duration" != "FAILED" && "$java_duration" != "FAILED" ]]; then
            if (( java_duration < bash_duration )); then
                echo "Winner: Java (faster by $((bash_duration - java_duration))s)" >> "$comparison_file"
            elif (( bash_duration < java_duration )); then
                echo "Winner: Bash (faster by $((java_duration - bash_duration))s)" >> "$comparison_file"
            else
                echo "Result: Tie" >> "$comparison_file"
            fi
        fi
        
    else
        echo "✗ Missing output logs" >> "$comparison_file"
        [[ ! -f "$bash_log" ]] && echo "  - Bash log missing" >> "$comparison_file"
        [[ ! -f "$java_log" ]] && echo "  - Java log missing" >> "$comparison_file"
    fi
    
    # Display comparison results
    cat "$comparison_file" | tee -a "$LOG_FILE"
    
    success "Output comparison complete"
}

generate_report() {
    info "Generating comparison report..."
    
    local report_file="$COMPARISON_DIR/comparison_report.md"
    
    cat > "$report_file" << 'EOF'
# GitHub Issues Collection - Implementation Comparison Report

## Test Configuration
- **Repository**: spring-projects/spring-ai
- **Batch Size**: 50
- **Test Type**: Dry Run
- **Timeout**: 5 minutes

## Results Summary

### Bash Implementation
EOF
    
    if [[ -f "$COMPARISON_DIR/bash_results/duration.txt" ]]; then
        local bash_duration=$(cat "$COMPARISON_DIR/bash_results/duration.txt")
        if [[ "$bash_duration" != "FAILED" ]]; then
            echo "- **Status**: ✅ Success" >> "$report_file"
            echo "- **Duration**: ${bash_duration}s" >> "$report_file"
        else
            echo "- **Status**: ❌ Failed" >> "$report_file"
        fi
    else
        echo "- **Status**: ❌ No results" >> "$report_file"
    fi
    
    cat >> "$report_file" << 'EOF'

### Java Implementation
EOF
    
    if [[ -f "$COMPARISON_DIR/java_results/duration.txt" ]]; then
        local java_duration=$(cat "$COMPARISON_DIR/java_results/duration.txt")
        if [[ "$java_duration" != "FAILED" ]]; then
            echo "- **Status**: ✅ Success" >> "$report_file"
            echo "- **Duration**: ${java_duration}s" >> "$report_file"
        else
            echo "- **Status**: ❌ Failed" >> "$report_file"
        fi
    else
        echo "- **Status**: ❌ No results" >> "$report_file"
    fi
    
    cat >> "$report_file" << 'EOF'

## Detailed Comparison

### Output Comparison
EOF
    
    if [[ -f "$COMPARISON_DIR/output_comparison.txt" ]]; then
        echo '```' >> "$report_file"
        cat "$COMPARISON_DIR/output_comparison.txt" >> "$report_file"
        echo '```' >> "$report_file"
    fi
    
    cat >> "$report_file" << 'EOF'

### Log Files
- Bash output: `bash_results/output.log`
- Java output: `java_results/output.log`
- Comparison log: `comparison.log`

## Files Generated
EOF
    
    echo "- Report generated at: $(date)" >> "$report_file"
    echo "- Test results in: \`$(basename "$COMPARISON_DIR")/\`" >> "$report_file"
    
    success "Comparison report generated: $report_file"
}

main() {
    info "Starting GitHub Issues Collection Implementation Comparison"
    
    # Run all test phases
    check_prerequisites
    setup_test_environment
    
    # Run both implementations
    local bash_success=0
    local java_success=0
    
    run_bash_implementation || bash_success=$?
    run_java_implementation || java_success=$?
    
    # Compare results
    compare_outputs
    generate_report
    
    # Final summary
    info "Comparison test completed"
    info "Results saved to: $COMPARISON_DIR"
    
    if [[ $bash_success -eq 0 && $java_success -eq 0 ]]; then
        success "Both implementations completed successfully"
        return 0
    elif [[ $bash_success -eq 0 ]]; then
        warn "Only Bash implementation succeeded"
        return 1
    elif [[ $java_success -eq 0 ]]; then
        warn "Only Java implementation succeeded"
        return 1
    else
        error "Both implementations failed"
        return 1
    fi
}

# Show usage if help requested
if [[ "${1:-}" =~ ^(-h|--help)$ ]]; then
    cat << 'EOF'
GitHub Issues Collection - Implementation Comparison Test

USAGE:
    ./compare_implementations.sh

DESCRIPTION:
    Runs both the Bash and Java implementations side-by-side with identical
    parameters and compares their outputs, performance, and behavior.

PREREQUISITES:
    - jbang installed and in PATH
    - GITHUB_TOKEN environment variable set
    - Both collect_github_issues.sh and CollectGithubIssues.java available

OUTPUT:
    Creates comparison_results/ directory with:
    - Individual test results for each implementation
    - Side-by-side comparison analysis
    - Performance benchmarks
    - Detailed markdown report

EXAMPLES:
    # Run comparison test
    ./compare_implementations.sh

    # Set GitHub token and run
    export GITHUB_TOKEN=your_token_here
    ./compare_implementations.sh
EOF
    exit 0
fi

# Run main function
main "$@"
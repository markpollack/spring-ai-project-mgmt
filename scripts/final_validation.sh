#!/usr/bin/env bash

# GitHub Issues Collection - Final Validation Suite
# Comprehensive testing and validation of the Java implementation

set -Eeuo pipefail

# Script configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PARENT_DIR="$(dirname "$SCRIPT_DIR")"
readonly JAVA_SCRIPT="$SCRIPT_DIR/CollectGithubIssues.java"
readonly VALIDATION_DIR="$SCRIPT_DIR/final_validation_results"
readonly LOG_FILE="$VALIDATION_DIR/validation.log"

# Test configuration
readonly TEST_REPO="spring-projects/spring-ai"
readonly TEST_BATCH_SIZE=25
readonly TEST_TIMEOUT=300  # 5 minutes per test

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly MAGENTA='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Test results tracking
declare -A TEST_RESULTS=()
declare -i TOTAL_TESTS=0
declare -i PASSED_TESTS=0
declare -i FAILED_TESTS=0

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

test_header() {
    log "${MAGENTA}[TEST]${NC} $*"
}

test_result() {
    local test_name="$1"
    local result="$2"
    
    TEST_RESULTS["$test_name"]="$result"
    ((TOTAL_TESTS++))
    
    if [[ "$result" == "PASS" ]]; then
        ((PASSED_TESTS++))
        log "${GREEN}[PASS]${NC} $test_name"
    else
        ((FAILED_TESTS++))
        log "${RED}[FAIL]${NC} $test_name"
    fi
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        error "Validation failed with exit code $exit_code"
    fi
    
    # Clean up temporary files
    rm -f /tmp/validation_*.log
    
    exit $exit_code
}

trap cleanup EXIT

# Test functions
setup_validation_environment() {
    info "Setting up validation environment..."
    
    mkdir -p "$VALIDATION_DIR"
    mkdir -p "$VALIDATION_DIR/test_outputs"
    
    # Initialize log file
    echo "GitHub Issues Collection - Final Validation Suite" > "$LOG_FILE"
    echo "Started at: $(date)" >> "$LOG_FILE"
    echo "=============================================" >> "$LOG_FILE"
    
    success "Validation environment setup complete"
}

test_prerequisites() {
    test_header "Testing prerequisites..."
    
    local prereq_pass=true
    
    # Test jbang availability
    if command -v jbang &> /dev/null; then
        info "✓ jbang is available: $(jbang --version)"
    else
        error "✗ jbang is not installed"
        prereq_pass=false
    fi
    
    # Test Java version
    if java -version &> /dev/null; then
        local java_version=$(java -version 2>&1 | head -1)
        info "✓ Java is available: $java_version"
        
        # Check if Java 17+
        if java -version 2>&1 | grep -q "version \"1[7-9]\\|version \"[2-9]"; then
            info "✓ Java version is 17 or higher"
        else
            error "✗ Java version is below 17"
            prereq_pass=false
        fi
    else
        error "✗ Java is not available"
        prereq_pass=false
    fi
    
    # Test GitHub token
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        info "✓ GITHUB_TOKEN is set"
    else
        error "✗ GITHUB_TOKEN is not set"
        prereq_pass=false
    fi
    
    # Test script existence
    if [[ -f "$JAVA_SCRIPT" ]]; then
        info "✓ Java script exists: $JAVA_SCRIPT"
    else
        error "✗ Java script not found: $JAVA_SCRIPT"
        prereq_pass=false
    fi
    
    if [[ "$prereq_pass" == "true" ]]; then
        test_result "Prerequisites Check" "PASS"
    else
        test_result "Prerequisites Check" "FAIL"
    fi
}

test_help_functionality() {
    test_header "Testing help functionality..."
    
    local help_output="$VALIDATION_DIR/test_outputs/help_output.txt"
    
    if timeout 30 jbang "$JAVA_SCRIPT" --help > "$help_output" 2>&1; then
        # Check if help output contains expected sections
        if grep -q "USAGE:" "$help_output" && \
           grep -q "OPTIONS:" "$help_output" && \
           grep -q "EXAMPLES:" "$help_output"; then
            info "✓ Help output contains expected sections"
            test_result "Help Functionality" "PASS"
        else
            error "✗ Help output missing expected sections"
            test_result "Help Functionality" "FAIL"
        fi
    else
        error "✗ Help command failed or timed out"
        test_result "Help Functionality" "FAIL"
    fi
}

test_dry_run_functionality() {
    test_header "Testing dry run functionality..."
    
    local dry_run_output="$VALIDATION_DIR/test_outputs/dry_run_output.txt"
    
    if timeout $TEST_TIMEOUT jbang "$JAVA_SCRIPT" \
        --repo "$TEST_REPO" \
        --batch-size "$TEST_BATCH_SIZE" \
        --dry-run \
        > "$dry_run_output" 2>&1; then
        
        # Check if dry run output contains expected information
        if grep -q "DRY RUN:" "$dry_run_output" && \
           grep -q "Total.*issues" "$dry_run_output"; then
            info "✓ Dry run completed successfully"
            test_result "Dry Run Functionality" "PASS"
        else
            error "✗ Dry run output missing expected information"
            test_result "Dry Run Functionality" "FAIL"
        fi
    else
        error "✗ Dry run failed or timed out"
        test_result "Dry Run Functionality" "FAIL"
    fi
}

test_configuration_loading() {
    test_header "Testing configuration loading..."
    
    local config_output="$VALIDATION_DIR/test_outputs/config_output.txt"
    
    # Test with default configuration
    if timeout 60 jbang "$JAVA_SCRIPT" \
        --repo "$TEST_REPO" \
        --dry-run \
        --verbose \
        > "$config_output" 2>&1; then
        
        # Check if configuration is loaded and displayed
        if grep -q "Configuration:" "$config_output" && \
           grep -q "Repository:" "$config_output" && \
           grep -q "Batch Size:" "$config_output"; then
            info "✓ Configuration loaded and displayed"
            test_result "Configuration Loading" "PASS"
        else
            error "✗ Configuration not properly loaded or displayed"
            test_result "Configuration Loading" "FAIL"
        fi
    else
        error "✗ Configuration test failed or timed out"
        test_result "Configuration Loading" "FAIL"
    fi
}

test_input_validation() {
    test_header "Testing input validation..."
    
    local validation_pass=true
    
    # Test invalid repository format
    local invalid_repo_output="$VALIDATION_DIR/test_outputs/invalid_repo_output.txt"
    if timeout 30 jbang "$JAVA_SCRIPT" \
        --repo "invalid-repo-format" \
        --dry-run \
        > "$invalid_repo_output" 2>&1; then
        
        # Should fail with validation error
        if grep -q "validation" "$invalid_repo_output" || \
           grep -q "format" "$invalid_repo_output"; then
            info "✓ Invalid repository format properly rejected"
        else
            error "✗ Invalid repository format not properly validated"
            validation_pass=false
        fi
    else
        # Command should fail for invalid input
        info "✓ Invalid repository format causes proper failure"
    fi
    
    # Test invalid batch size
    local invalid_batch_output="$VALIDATION_DIR/test_outputs/invalid_batch_output.txt"
    if timeout 30 jbang "$JAVA_SCRIPT" \
        --repo "$TEST_REPO" \
        --batch-size "invalid" \
        --dry-run \
        > "$invalid_batch_output" 2>&1; then
        
        # Should fail with validation error
        if grep -q "Invalid batch size" "$invalid_batch_output" || \
           grep -q "must be.*integer" "$invalid_batch_output"; then
            info "✓ Invalid batch size properly rejected"
        else
            error "✗ Invalid batch size not properly validated"
            validation_pass=false
        fi
    else
        # Command should fail for invalid input
        info "✓ Invalid batch size causes proper failure"
    fi
    
    if [[ "$validation_pass" == "true" ]]; then
        test_result "Input Validation" "PASS"
    else
        test_result "Input Validation" "FAIL"
    fi
}

test_error_handling() {
    test_header "Testing error handling..."
    
    local error_handling_pass=true
    
    # Test with invalid GitHub token
    local old_token="${GITHUB_TOKEN:-}"
    export GITHUB_TOKEN="invalid_token_for_testing"
    
    local invalid_token_output="$VALIDATION_DIR/test_outputs/invalid_token_output.txt"
    if timeout 60 jbang "$JAVA_SCRIPT" \
        --repo "$TEST_REPO" \
        --batch-size "$TEST_BATCH_SIZE" \
        --dry-run \
        > "$invalid_token_output" 2>&1; then
        
        # Should handle authentication error gracefully
        if grep -q -i "authentication\\|unauthorized\\|token" "$invalid_token_output"; then
            info "✓ Authentication error handled gracefully"
        else
            error "✗ Authentication error not properly handled"
            error_handling_pass=false
        fi
    else
        # Command should fail for invalid token
        info "✓ Invalid token causes proper failure"
    fi
    
    # Restore original token
    export GITHUB_TOKEN="$old_token"
    
    if [[ "$error_handling_pass" == "true" ]]; then
        test_result "Error Handling" "PASS"
    else
        test_result "Error Handling" "FAIL"
    fi
}

test_logging_functionality() {
    test_header "Testing logging functionality..."
    
    local logging_output="$VALIDATION_DIR/test_outputs/logging_output.txt"
    
    # Test verbose logging
    if timeout 60 jbang "$JAVA_SCRIPT" \
        --repo "$TEST_REPO" \
        --batch-size "$TEST_BATCH_SIZE" \
        --dry-run \
        --verbose \
        > "$logging_output" 2>&1; then
        
        # Check if verbose logging produces expected output
        if grep -q "DEBUG\\|INFO" "$logging_output" && \
           grep -q "Starting GitHub Issues Collection Tool" "$logging_output" && \
           grep -q "Configuration:" "$logging_output"; then
            info "✓ Verbose logging working correctly"
            test_result "Logging Functionality" "PASS"
        else
            error "✗ Verbose logging not working properly"
            test_result "Logging Functionality" "FAIL"
        fi
    else
        error "✗ Logging test failed or timed out"
        test_result "Logging Functionality" "FAIL"
    fi
}

test_performance_basic() {
    test_header "Testing basic performance..."
    
    local start_time=$(date +%s)
    local perf_output="$VALIDATION_DIR/test_outputs/performance_output.txt"
    
    if timeout $TEST_TIMEOUT jbang "$JAVA_SCRIPT" \
        --repo "$TEST_REPO" \
        --batch-size "$TEST_BATCH_SIZE" \
        --dry-run \
        > "$perf_output" 2>&1; then
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        # Check if performance is reasonable (should complete within timeout)
        if [[ $duration -lt $TEST_TIMEOUT ]]; then
            info "✓ Performance test completed in ${duration}s"
            test_result "Basic Performance" "PASS"
        else
            error "✗ Performance test took too long: ${duration}s"
            test_result "Basic Performance" "FAIL"
        fi
    else
        error "✗ Performance test failed or timed out"
        test_result "Basic Performance" "FAIL"
    fi
}

test_feature_compatibility() {
    test_header "Testing feature compatibility..."
    
    local compatibility_pass=true
    
    # Test all major command line flags
    local flags=("--incremental" "--clean" "--resume" "--verbose")
    
    for flag in "${flags[@]}"; do
        local flag_output="$VALIDATION_DIR/test_outputs/flag_${flag//--/_}_output.txt"
        
        if timeout 30 jbang "$JAVA_SCRIPT" \
            --repo "$TEST_REPO" \
            --batch-size "$TEST_BATCH_SIZE" \
            --dry-run \
            "$flag" \
            > "$flag_output" 2>&1; then
            
            info "✓ Flag $flag works correctly"
        else
            error "✗ Flag $flag failed"
            compatibility_pass=false
        fi
    done
    
    if [[ "$compatibility_pass" == "true" ]]; then
        test_result "Feature Compatibility" "PASS"
    else
        test_result "Feature Compatibility" "FAIL"
    fi
}

generate_validation_report() {
    info "Generating validation report..."
    
    local report_file="$VALIDATION_DIR/validation_report.md"
    
    cat > "$report_file" << EOF
# GitHub Issues Collection - Final Validation Report

## Test Summary

- **Total Tests**: $TOTAL_TESTS
- **Passed**: $PASSED_TESTS
- **Failed**: $FAILED_TESTS
- **Success Rate**: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%

## Test Results

EOF
    
    # Add individual test results
    for test_name in "${!TEST_RESULTS[@]}"; do
        local result="${TEST_RESULTS[$test_name]}"
        local status_icon
        
        if [[ "$result" == "PASS" ]]; then
            status_icon="✅"
        else
            status_icon="❌"
        fi
        
        echo "- $status_icon **$test_name**: $result" >> "$report_file"
    done
    
    cat >> "$report_file" << EOF

## Test Details

### Prerequisites Check
- JBang installation and version
- Java 17+ availability
- GitHub token configuration
- Script file existence

### Functionality Tests
- Help command output and formatting
- Dry run execution and output
- Configuration loading and display
- Input validation and error messages
- Error handling for invalid inputs
- Logging functionality and verbosity
- Basic performance and response time
- Feature compatibility across all flags

### Test Environment
- **Test Date**: $(date)
- **Test Repository**: $TEST_REPO
- **Test Batch Size**: $TEST_BATCH_SIZE
- **Test Timeout**: ${TEST_TIMEOUT}s

### Test Outputs
All test outputs are saved in: \`test_outputs/\`

## Validation Summary

EOF
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        cat >> "$report_file" << EOF
🎉 **All tests passed!** The Java implementation is ready for production use.

### Migration Recommendation
The implementation has passed all validation tests and is ready for migration from the bash version.

### Next Steps
1. Run the migration guide steps
2. Perform your own integration tests
3. Update any automation that depends on this tool
4. Consider the Java implementation as your primary tool
EOF
    else
        cat >> "$report_file" << EOF
⚠️ **Some tests failed.** Review the failed tests before proceeding with migration.

### Issues Found
$FAILED_TESTS out of $TOTAL_TESTS tests failed. Please review the test outputs and resolve issues before migration.

### Recommendations
1. Fix the failing tests
2. Re-run the validation suite
3. Consider staying with the bash version until issues are resolved
EOF
    fi
    
    cat >> "$report_file" << EOF

## Support Information

### Test Logs
- Main log: \`validation.log\`
- Individual test outputs: \`test_outputs/\`

### Troubleshooting
If tests fail, check:
1. Prerequisites are properly installed
2. GitHub token has appropriate permissions
3. Network connectivity to GitHub API
4. Java classpath and dependencies

---

Report generated at: $(date)
EOF
    
    success "Validation report generated: $report_file"
}

display_summary() {
    echo
    echo "============================================="
    echo "          VALIDATION SUMMARY"
    echo "============================================="
    echo
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed:      $PASSED_TESTS"
    echo "Failed:      $FAILED_TESTS"
    echo "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
    echo
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "${GREEN}🎉 All tests passed! Java implementation is ready for use.${NC}"
    else
        echo -e "${RED}⚠️  Some tests failed. Review the results before migration.${NC}"
    fi
    
    echo
    echo "Results saved to: $VALIDATION_DIR"
    echo "============================================="
}

main() {
    info "Starting final validation suite"
    
    setup_validation_environment
    
    # Run all validation tests
    test_prerequisites
    test_help_functionality
    test_dry_run_functionality
    test_configuration_loading
    test_input_validation
    test_error_handling
    test_logging_functionality
    test_performance_basic
    test_feature_compatibility
    
    # Generate report and summary
    generate_validation_report
    display_summary
    
    info "Final validation completed"
    
    # Return appropriate exit code
    if [[ $FAILED_TESTS -eq 0 ]]; then
        return 0
    else
        return 1
    fi
}

# Show usage if help requested
if [[ "${1:-}" =~ ^(-h|--help)$ ]]; then
    cat << 'EOF'
GitHub Issues Collection - Final Validation Suite

USAGE:
    ./final_validation.sh

DESCRIPTION:
    Comprehensive testing and validation of the Java implementation to ensure
    it's ready for production use and migration from the bash version.

TESTS PERFORMED:
    - Prerequisites verification
    - Help functionality
    - Dry run execution
    - Configuration loading
    - Input validation
    - Error handling
    - Logging functionality
    - Basic performance
    - Feature compatibility

PREREQUISITES:
    - jbang installed and in PATH
    - Java 17+ available
    - GITHUB_TOKEN environment variable set
    - CollectGithubIssues.java available

OUTPUT:
    Creates final_validation_results/ directory with:
    - Individual test outputs
    - Comprehensive validation report
    - Detailed test logs
    - Summary statistics

EXAMPLES:
    # Run full validation suite
    ./final_validation.sh

    # Set GitHub token and run
    export GITHUB_TOKEN=your_token_here
    ./final_validation.sh
EOF
    exit 0
fi

# Run main function
main "$@"
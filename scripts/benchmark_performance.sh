#!/usr/bin/env bash

# GitHub Issues Collection - Performance Benchmarking
# Benchmarks performance between Java and Bash implementations

set -Eeuo pipefail

# Script configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PARENT_DIR="$(dirname "$SCRIPT_DIR")"
readonly BASH_SCRIPT="$PARENT_DIR/collect_github_issues.sh"
readonly JAVA_SCRIPT="$SCRIPT_DIR/CollectGithubIssues.java"
readonly BENCHMARK_DIR="$SCRIPT_DIR/benchmark_results"
readonly LOG_FILE="$BENCHMARK_DIR/benchmark.log"

# Benchmark configuration
readonly TEST_REPO="spring-projects/spring-ai"
readonly BENCHMARK_ROUNDS=3
readonly WARM_UP_ROUNDS=1
readonly TEST_TIMEOUT=600  # 10 minutes max per test

# Test scenarios
declare -A TEST_SCENARIOS=(
    ["small"]="25"      # 25 issues per batch
    ["medium"]="100"    # 100 issues per batch
    ["large"]="200"     # 200 issues per batch
)

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly MAGENTA='\033[0;35m'
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

benchmark() {
    log "${MAGENTA}[BENCHMARK]${NC} $*"
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        error "Benchmark failed with exit code $exit_code"
    fi
    
    # Clean up temporary files
    rm -f /tmp/benchmark_*.log
    
    exit $exit_code
}

trap cleanup EXIT

# Helper functions
setup_benchmark_environment() {
    info "Setting up benchmark environment..."
    
    mkdir -p "$BENCHMARK_DIR"
    
    # Create subdirectories for results
    mkdir -p "$BENCHMARK_DIR/bash_results"
    mkdir -p "$BENCHMARK_DIR/java_results"
    mkdir -p "$BENCHMARK_DIR/raw_data"
    
    # Initialize log file
    echo "GitHub Issues Collection - Performance Benchmark" > "$LOG_FILE"
    echo "Started at: $(date)" >> "$LOG_FILE"
    echo "=============================================" >> "$LOG_FILE"
    
    success "Benchmark environment setup complete"
}

check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check if required tools are available
    local missing_tools=()
    
    if ! command -v jbang &> /dev/null; then
        missing_tools+=("jbang")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing_tools+=("jq")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        error "Missing required tools: ${missing_tools[*]}"
        return 1
    fi
    
    # Check if scripts exist
    if [[ ! -f "$BASH_SCRIPT" ]]; then
        error "Bash script not found: $BASH_SCRIPT"
        return 1
    fi
    
    if [[ ! -f "$JAVA_SCRIPT" ]]; then
        error "Java script not found: $JAVA_SCRIPT"
        return 1
    fi
    
    # Check if GitHub token is set
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        error "GITHUB_TOKEN environment variable is not set"
        return 1
    fi
    
    success "Prerequisites check passed"
}

run_warmup() {
    info "Running warmup rounds..."
    
    local warmup_batch_size=25
    
    # Warmup bash
    info "Warming up Bash implementation..."
    cd "$PARENT_DIR"
    timeout $TEST_TIMEOUT ./collect_github_issues.sh \
        --repo "$TEST_REPO" \
        --batch-size "$warmup_batch_size" \
        --dry-run \
        &> /tmp/warmup_bash.log || true
    
    # Warmup Java
    info "Warming up Java implementation..."
    cd "$SCRIPT_DIR"
    timeout $TEST_TIMEOUT jbang CollectGithubIssues.java \
        --repo "$TEST_REPO" \
        --batch-size "$warmup_batch_size" \
        --dry-run \
        &> /tmp/warmup_java.log || true
    
    success "Warmup complete"
}

benchmark_implementation() {
    local impl_name="$1"
    local batch_size="$2"
    local round="$3"
    
    local start_time=$(date +%s.%3N)
    local result_file="$BENCHMARK_DIR/raw_data/${impl_name}_${batch_size}_round${round}.json"
    
    benchmark "Testing $impl_name with batch size $batch_size (round $round/$BENCHMARK_ROUNDS)"
    
    if [[ "$impl_name" == "bash" ]]; then
        cd "$PARENT_DIR"
        
        if timeout $TEST_TIMEOUT ./collect_github_issues.sh \
            --repo "$TEST_REPO" \
            --batch-size "$batch_size" \
            --dry-run \
            &> "$BENCHMARK_DIR/bash_results/output_${batch_size}_${round}.log"; then
            
            local end_time=$(date +%s.%3N)
            local duration=$(echo "$end_time - $start_time" | bc)
            
            # Create result JSON
            cat > "$result_file" << EOF
{
    "implementation": "$impl_name",
    "batch_size": $batch_size,
    "round": $round,
    "duration_seconds": $duration,
    "status": "success",
    "timestamp": "$(date -Iseconds)"
}
EOF
            
            success "Bash test completed in ${duration}s"
            return 0
        else
            local end_time=$(date +%s.%3N)
            local duration=$(echo "$end_time - $start_time" | bc)
            
            cat > "$result_file" << EOF
{
    "implementation": "$impl_name",
    "batch_size": $batch_size,
    "round": $round,
    "duration_seconds": $duration,
    "status": "failed",
    "timestamp": "$(date -Iseconds)"
}
EOF
            
            error "Bash test failed after ${duration}s"
            return 1
        fi
        
    elif [[ "$impl_name" == "java" ]]; then
        cd "$SCRIPT_DIR"
        
        if timeout $TEST_TIMEOUT jbang CollectGithubIssues.java \
            --repo "$TEST_REPO" \
            --batch-size "$batch_size" \
            --dry-run \
            &> "$BENCHMARK_DIR/java_results/output_${batch_size}_${round}.log"; then
            
            local end_time=$(date +%s.%3N)
            local duration=$(echo "$end_time - $start_time" | bc)
            
            # Create result JSON
            cat > "$result_file" << EOF
{
    "implementation": "$impl_name",
    "batch_size": $batch_size,
    "round": $round,
    "duration_seconds": $duration,
    "status": "success",
    "timestamp": "$(date -Iseconds)"
}
EOF
            
            success "Java test completed in ${duration}s"
            return 0
        else
            local end_time=$(date +%s.%3N)
            local duration=$(echo "$end_time - $start_time" | bc)
            
            cat > "$result_file" << EOF
{
    "implementation": "$impl_name",
    "batch_size": $batch_size,
    "round": $round,
    "duration_seconds": $duration,
    "status": "failed",
    "timestamp": "$(date -Iseconds)"
}
EOF
            
            error "Java test failed after ${duration}s"
            return 1
        fi
    fi
}

run_benchmark_suite() {
    info "Running benchmark suite..."
    
    for scenario in "${!TEST_SCENARIOS[@]}"; do
        local batch_size="${TEST_SCENARIOS[$scenario]}"
        
        benchmark "Starting $scenario scenario (batch size: $batch_size)"
        
        # Run multiple rounds for each scenario
        for round in $(seq 1 $BENCHMARK_ROUNDS); do
            # Test bash implementation
            benchmark_implementation "bash" "$batch_size" "$round"
            
            # Small delay between tests
            sleep 2
            
            # Test java implementation
            benchmark_implementation "java" "$batch_size" "$round"
            
            # Small delay between rounds
            sleep 2
        done
        
        success "Completed $scenario scenario"
    done
    
    success "Benchmark suite completed"
}

analyze_results() {
    info "Analyzing benchmark results..."
    
    local analysis_file="$BENCHMARK_DIR/analysis.json"
    local results_dir="$BENCHMARK_DIR/raw_data"
    
    # Create analysis structure
    cat > "$analysis_file" << 'EOF'
{
    "benchmark_summary": {
        "total_tests": 0,
        "successful_tests": 0,
        "failed_tests": 0,
        "scenarios": {}
    },
    "performance_comparison": {}
}
EOF
    
    # Analyze each scenario
    for scenario in "${!TEST_SCENARIOS[@]}"; do
        local batch_size="${TEST_SCENARIOS[$scenario]}"
        
        # Calculate statistics for bash
        local bash_durations=()
        local bash_success_count=0
        
        for round in $(seq 1 $BENCHMARK_ROUNDS); do
            local result_file="$results_dir/bash_${batch_size}_round${round}.json"
            if [[ -f "$result_file" ]]; then
                local status=$(jq -r '.status' "$result_file")
                if [[ "$status" == "success" ]]; then
                    local duration=$(jq -r '.duration_seconds' "$result_file")
                    bash_durations+=("$duration")
                    ((bash_success_count++))
                fi
            fi
        done
        
        # Calculate statistics for java
        local java_durations=()
        local java_success_count=0
        
        for round in $(seq 1 $BENCHMARK_ROUNDS); do
            local result_file="$results_dir/java_${batch_size}_round${round}.json"
            if [[ -f "$result_file" ]]; then
                local status=$(jq -r '.status' "$result_file")
                if [[ "$status" == "success" ]]; then
                    local duration=$(jq -r '.duration_seconds' "$result_file")
                    java_durations+=("$duration")
                    ((java_success_count++))
                fi
            fi
        done
        
        # Calculate averages if we have data
        local bash_avg="0"
        local java_avg="0"
        
        if [[ ${#bash_durations[@]} -gt 0 ]]; then
            bash_avg=$(printf '%s\n' "${bash_durations[@]}" | awk '{sum+=$1} END {print sum/NR}')
        fi
        
        if [[ ${#java_durations[@]} -gt 0 ]]; then
            java_avg=$(printf '%s\n' "${java_durations[@]}" | awk '{sum+=$1} END {print sum/NR}')
        fi
        
        # Update analysis file
        local temp_file=$(mktemp)
        jq --arg scenario "$scenario" \
           --arg batch_size "$batch_size" \
           --arg bash_avg "$bash_avg" \
           --arg java_avg "$java_avg" \
           --arg bash_success "$bash_success_count" \
           --arg java_success "$java_success_count" \
           '.benchmark_summary.scenarios[$scenario] = {
               "batch_size": ($batch_size | tonumber),
               "bash": {
                   "average_duration": ($bash_avg | tonumber),
                   "successful_runs": ($bash_success | tonumber)
               },
               "java": {
                   "average_duration": ($java_avg | tonumber),
                   "successful_runs": ($java_success | tonumber)
               }
           }' "$analysis_file" > "$temp_file"
        
        mv "$temp_file" "$analysis_file"
        
        benchmark "Analyzed $scenario scenario - Bash: ${bash_avg}s, Java: ${java_avg}s"
    done
    
    success "Results analysis complete"
}

generate_benchmark_report() {
    info "Generating benchmark report..."
    
    local report_file="$BENCHMARK_DIR/benchmark_report.md"
    local analysis_file="$BENCHMARK_DIR/analysis.json"
    
    cat > "$report_file" << 'EOF'
# GitHub Issues Collection - Performance Benchmark Report

## Test Configuration
- **Repository**: spring-projects/spring-ai
- **Test Type**: Dry Run
- **Rounds per scenario**: 3
- **Timeout**: 10 minutes per test

## Performance Results

### Summary
EOF
    
    # Add performance summary
    if [[ -f "$analysis_file" ]]; then
        echo "" >> "$report_file"
        echo "| Scenario | Batch Size | Bash Avg (s) | Java Avg (s) | Winner |" >> "$report_file"
        echo "|----------|------------|--------------|--------------|--------|" >> "$report_file"
        
        for scenario in "${!TEST_SCENARIOS[@]}"; do
            local batch_size="${TEST_SCENARIOS[$scenario]}"
            
            if jq -e ".benchmark_summary.scenarios.${scenario}" "$analysis_file" &>/dev/null; then
                local bash_avg=$(jq -r ".benchmark_summary.scenarios.${scenario}.bash.average_duration" "$analysis_file")
                local java_avg=$(jq -r ".benchmark_summary.scenarios.${scenario}.java.average_duration" "$analysis_file")
                
                local winner="Tie"
                if (( $(echo "$bash_avg > 0 && $java_avg > 0" | bc -l) )); then
                    if (( $(echo "$java_avg < $bash_avg" | bc -l) )); then
                        winner="Java"
                    elif (( $(echo "$bash_avg < $java_avg" | bc -l) )); then
                        winner="Bash"
                    fi
                fi
                
                echo "| $scenario | $batch_size | $bash_avg | $java_avg | $winner |" >> "$report_file"
            fi
        done
    fi
    
    cat >> "$report_file" << 'EOF'

### Detailed Results

#### Test Scenarios
EOF
    
    for scenario in "${!TEST_SCENARIOS[@]}"; do
        local batch_size="${TEST_SCENARIOS[$scenario]}"
        
        echo "" >> "$report_file"
        echo "##### $scenario Scenario (Batch Size: $batch_size)" >> "$report_file"
        echo "" >> "$report_file"
        
        # Add individual round results
        echo "**Round Results:**" >> "$report_file"
        echo "" >> "$report_file"
        echo "| Round | Bash (s) | Java (s) |" >> "$report_file"
        echo "|-------|----------|----------|" >> "$report_file"
        
        for round in $(seq 1 $BENCHMARK_ROUNDS); do
            local bash_duration="Failed"
            local java_duration="Failed"
            
            local bash_file="$BENCHMARK_DIR/raw_data/bash_${batch_size}_round${round}.json"
            local java_file="$BENCHMARK_DIR/raw_data/java_${batch_size}_round${round}.json"
            
            if [[ -f "$bash_file" ]]; then
                local status=$(jq -r '.status' "$bash_file")
                if [[ "$status" == "success" ]]; then
                    bash_duration=$(jq -r '.duration_seconds' "$bash_file")
                fi
            fi
            
            if [[ -f "$java_file" ]]; then
                local status=$(jq -r '.status' "$java_file")
                if [[ "$status" == "success" ]]; then
                    java_duration=$(jq -r '.duration_seconds' "$java_file")
                fi
            fi
            
            echo "| $round | $bash_duration | $java_duration |" >> "$report_file"
        done
    done
    
    cat >> "$report_file" << 'EOF'

## Analysis

### Performance Insights
1. **Startup Time**: Java may have higher startup overhead due to JVM initialization
2. **Throughput**: Java may process batches more efficiently once warmed up
3. **Memory Usage**: Different memory patterns between implementations
4. **API Efficiency**: Both use similar GitHub API calls

### Recommendations
1. For small, one-time collections: Bash may be faster
2. For large, repeated collections: Java may be more efficient
3. For production use: Java offers better error handling and configuration

## Test Environment
- **Test Date**: $(date)
- **Test Duration**: Multiple rounds with warm-up
- **Test Mode**: Dry run (no actual data collection)

## Raw Data
- Individual test results: `raw_data/`
- Implementation logs: `bash_results/` and `java_results/`
- Analysis data: `analysis.json`
EOF
    
    success "Benchmark report generated: $report_file"
}

main() {
    info "Starting performance benchmark"
    
    # Check if bc is available for calculations
    if ! command -v bc &> /dev/null; then
        error "bc (basic calculator) is required for benchmarking"
        exit 1
    fi
    
    setup_benchmark_environment
    check_prerequisites
    run_warmup
    run_benchmark_suite
    analyze_results
    generate_benchmark_report
    
    info "Benchmark completed successfully"
    info "Results saved to: $BENCHMARK_DIR"
    
    success "Performance benchmark complete"
}

# Show usage if help requested
if [[ "${1:-}" =~ ^(-h|--help)$ ]]; then
    cat << 'EOF'
GitHub Issues Collection - Performance Benchmarking

USAGE:
    ./benchmark_performance.sh

DESCRIPTION:
    Benchmarks performance between Java and Bash implementations across
    different batch sizes and multiple test rounds.

PREREQUISITES:
    - jbang installed and in PATH
    - jq installed for JSON processing
    - bc installed for calculations
    - GITHUB_TOKEN environment variable set

TEST SCENARIOS:
    - Small: 25 issues per batch
    - Medium: 100 issues per batch  
    - Large: 200 issues per batch

OUTPUT:
    Creates benchmark_results/ directory with:
    - Individual test results and logs
    - Statistical analysis
    - Performance comparison report
    - Raw timing data

EXAMPLES:
    # Run full benchmark suite
    ./benchmark_performance.sh

    # Set GitHub token and run
    export GITHUB_TOKEN=your_token_here
    ./benchmark_performance.sh
EOF
    exit 0
fi

# Run main function
main "$@"
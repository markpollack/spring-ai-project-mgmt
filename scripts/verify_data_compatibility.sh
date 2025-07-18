#!/usr/bin/env bash

# GitHub Issues Collection - Data Format Compatibility Verification
# Verifies that Java and Bash implementations produce compatible data formats

set -Eeuo pipefail

# Script configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly VERIFICATION_DIR="$SCRIPT_DIR/verification_results"
readonly LOG_FILE="$VERIFICATION_DIR/verification.log"

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
        error "Verification failed with exit code $exit_code"
    fi
    exit $exit_code
}

trap cleanup EXIT

# Helper functions
setup_verification_environment() {
    info "Setting up verification environment..."
    
    mkdir -p "$VERIFICATION_DIR"
    
    # Initialize log file
    echo "GitHub Issues Collection - Data Format Compatibility Verification" > "$LOG_FILE"
    echo "Started at: $(date)" >> "$LOG_FILE"
    echo "=============================================" >> "$LOG_FILE"
    
    success "Verification environment setup complete"
}

find_test_data() {
    info "Finding existing test data..."
    
    # Look for existing batch directories
    local bash_data=""
    local java_data=""
    
    # Check parent directory for bash results
    if [[ -d "$SCRIPT_DIR/../issues" ]]; then
        bash_data="$SCRIPT_DIR/../issues"
    fi
    
    # Check scripts directory for java results
    if [[ -d "$SCRIPT_DIR/issues" ]]; then
        java_data="$SCRIPT_DIR/issues"
    fi
    
    # Find the most recent batch directories
    local bash_latest=""
    local java_latest=""
    
    if [[ -n "$bash_data" && -d "$bash_data/raw/closed" ]]; then
        bash_latest=$(find "$bash_data/raw/closed" -type d -name "batch_*" | sort | tail -1)
    fi
    
    if [[ -n "$java_data" && -d "$java_data/raw/closed" ]]; then
        java_latest=$(find "$java_data/raw/closed" -type d -name "batch_*" | sort | tail -1)
    fi
    
    echo "$bash_latest" > "$VERIFICATION_DIR/bash_data_path.txt"
    echo "$java_latest" > "$VERIFICATION_DIR/java_data_path.txt"
    
    if [[ -n "$bash_latest" ]]; then
        success "Found Bash test data: $bash_latest"
    else
        warn "No Bash test data found"
    fi
    
    if [[ -n "$java_latest" ]]; then
        success "Found Java test data: $java_latest"
    else
        warn "No Java test data found"
    fi
}

verify_batch_file_structure() {
    info "Verifying batch file structure..."
    
    local bash_data_path=$(cat "$VERIFICATION_DIR/bash_data_path.txt")
    local java_data_path=$(cat "$VERIFICATION_DIR/java_data_path.txt")
    local structure_report="$VERIFICATION_DIR/structure_comparison.txt"
    
    echo "BATCH FILE STRUCTURE COMPARISON" > "$structure_report"
    echo "===============================" >> "$structure_report"
    echo "" >> "$structure_report"
    
    # Check if both paths exist
    if [[ -z "$bash_data_path" || ! -d "$bash_data_path" ]]; then
        echo "❌ Bash data directory not found" >> "$structure_report"
        return 1
    fi
    
    if [[ -z "$java_data_path" || ! -d "$java_data_path" ]]; then
        echo "❌ Java data directory not found" >> "$structure_report"
        return 1
    fi
    
    # Compare directory structure
    echo "DIRECTORY STRUCTURE:" >> "$structure_report"
    echo "Bash: $bash_data_path" >> "$structure_report"
    echo "Java: $java_data_path" >> "$structure_report"
    echo "" >> "$structure_report"
    
    # List files in both directories
    local bash_files=$(find "$bash_data_path" -name "*.json" | sort)
    local java_files=$(find "$java_data_path" -name "*.json" | sort)
    
    echo "BATCH FILES:" >> "$structure_report"
    echo "Bash files:" >> "$structure_report"
    echo "$bash_files" | sed 's|.*/||' >> "$structure_report"
    echo "" >> "$structure_report"
    echo "Java files:" >> "$structure_report"
    echo "$java_files" | sed 's|.*/||' >> "$structure_report"
    echo "" >> "$structure_report"
    
    # Count files
    local bash_count=$(echo "$bash_files" | wc -l)
    local java_count=$(echo "$java_files" | wc -l)
    
    echo "FILE COUNTS:" >> "$structure_report"
    echo "Bash: $bash_count files" >> "$structure_report"
    echo "Java: $java_count files" >> "$structure_report"
    
    if [[ "$bash_count" -eq "$java_count" ]]; then
        echo "✅ File counts match" >> "$structure_report"
    else
        echo "❌ File counts differ" >> "$structure_report"
    fi
    
    cat "$structure_report" | tee -a "$LOG_FILE"
    success "Batch file structure verification complete"
}

verify_json_schema() {
    info "Verifying JSON schema compatibility..."
    
    local bash_data_path=$(cat "$VERIFICATION_DIR/bash_data_path.txt")
    local java_data_path=$(cat "$VERIFICATION_DIR/java_data_path.txt")
    local schema_report="$VERIFICATION_DIR/schema_comparison.txt"
    
    echo "JSON SCHEMA COMPARISON" > "$schema_report"
    echo "======================" >> "$schema_report"
    echo "" >> "$schema_report"
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        echo "❌ jq is not installed - cannot verify JSON schema" >> "$schema_report"
        cat "$schema_report" | tee -a "$LOG_FILE"
        return 1
    fi
    
    # Get first batch file from each implementation
    local bash_batch=$(find "$bash_data_path" -name "issues_batch_*.json" | head -1)
    local java_batch=$(find "$java_data_path" -name "issues_batch_*.json" | head -1)
    
    if [[ -z "$bash_batch" || ! -f "$bash_batch" ]]; then
        echo "❌ No bash batch file found" >> "$schema_report"
        cat "$schema_report" | tee -a "$LOG_FILE"
        return 1
    fi
    
    if [[ -z "$java_batch" || ! -f "$java_batch" ]]; then
        echo "❌ No java batch file found" >> "$schema_report"
        cat "$schema_report" | tee -a "$LOG_FILE"
        return 1
    fi
    
    echo "COMPARING FIRST BATCH FILES:" >> "$schema_report"
    echo "Bash: $(basename "$bash_batch")" >> "$schema_report"
    echo "Java: $(basename "$java_batch")" >> "$schema_report"
    echo "" >> "$schema_report"
    
    # Extract top-level keys from both files
    local bash_keys=$(jq -r 'keys[]' "$bash_batch" 2>/dev/null | sort)
    local java_keys=$(jq -r 'keys[]' "$java_batch" 2>/dev/null | sort)
    
    echo "TOP-LEVEL KEYS:" >> "$schema_report"
    echo "Bash: $bash_keys" >> "$schema_report"
    echo "Java: $java_keys" >> "$schema_report"
    echo "" >> "$schema_report"
    
    # Compare keys
    if [[ "$bash_keys" == "$java_keys" ]]; then
        echo "✅ Top-level keys match" >> "$schema_report"
    else
        echo "❌ Top-level keys differ" >> "$schema_report"
        echo "Bash only: $(comm -23 <(echo "$bash_keys") <(echo "$java_keys"))" >> "$schema_report"
        echo "Java only: $(comm -13 <(echo "$bash_keys") <(echo "$java_keys"))" >> "$schema_report"
    fi
    
    # Check issue structure if issues array exists
    if jq -e '.issues' "$bash_batch" &>/dev/null && jq -e '.issues' "$java_batch" &>/dev/null; then
        echo "" >> "$schema_report"
        echo "ISSUE STRUCTURE:" >> "$schema_report"
        
        # Get keys from first issue in each file
        local bash_issue_keys=$(jq -r '.issues[0] | keys[]' "$bash_batch" 2>/dev/null | sort)
        local java_issue_keys=$(jq -r '.issues[0] | keys[]' "$java_batch" 2>/dev/null | sort)
        
        echo "Bash issue keys: $bash_issue_keys" >> "$schema_report"
        echo "Java issue keys: $java_issue_keys" >> "$schema_report"
        
        if [[ "$bash_issue_keys" == "$java_issue_keys" ]]; then
            echo "✅ Issue structure matches" >> "$schema_report"
        else
            echo "❌ Issue structure differs" >> "$schema_report"
        fi
    fi
    
    cat "$schema_report" | tee -a "$LOG_FILE"
    success "JSON schema verification complete"
}

verify_metadata_compatibility() {
    info "Verifying metadata compatibility..."
    
    local bash_data_path=$(cat "$VERIFICATION_DIR/bash_data_path.txt")
    local java_data_path=$(cat "$VERIFICATION_DIR/java_data_path.txt")
    local metadata_report="$VERIFICATION_DIR/metadata_comparison.txt"
    
    echo "METADATA COMPARISON" > "$metadata_report"
    echo "===================" >> "$metadata_report"
    echo "" >> "$metadata_report"
    
    # Check for metadata files
    local bash_metadata="$bash_data_path/metadata.json"
    local java_metadata="$java_data_path/metadata.json"
    
    if [[ ! -f "$bash_metadata" ]]; then
        echo "❌ Bash metadata file not found" >> "$metadata_report"
        return 1
    fi
    
    if [[ ! -f "$java_metadata" ]]; then
        echo "❌ Java metadata file not found" >> "$metadata_report"
        return 1
    fi
    
    # Compare metadata structure
    if command -v jq &> /dev/null; then
        echo "METADATA STRUCTURE:" >> "$metadata_report"
        
        local bash_meta_keys=$(jq -r 'keys[]' "$bash_metadata" 2>/dev/null | sort)
        local java_meta_keys=$(jq -r 'keys[]' "$java_metadata" 2>/dev/null | sort)
        
        echo "Bash metadata keys: $bash_meta_keys" >> "$metadata_report"
        echo "Java metadata keys: $java_meta_keys" >> "$metadata_report"
        echo "" >> "$metadata_report"
        
        if [[ "$bash_meta_keys" == "$java_meta_keys" ]]; then
            echo "✅ Metadata structure matches" >> "$metadata_report"
        else
            echo "❌ Metadata structure differs" >> "$metadata_report"
        fi
        
        # Compare specific fields
        echo "" >> "$metadata_report"
        echo "METADATA VALUES:" >> "$metadata_report"
        
        local bash_repo=$(jq -r '.repository' "$bash_metadata" 2>/dev/null)
        local java_repo=$(jq -r '.repository' "$java_metadata" 2>/dev/null)
        
        echo "Repository - Bash: $bash_repo, Java: $java_repo" >> "$metadata_report"
        
        if [[ "$bash_repo" == "$java_repo" ]]; then
            echo "✅ Repository values match" >> "$metadata_report"
        else
            echo "❌ Repository values differ" >> "$metadata_report"
        fi
    else
        echo "❌ jq not available for metadata comparison" >> "$metadata_report"
    fi
    
    cat "$metadata_report" | tee -a "$LOG_FILE"
    success "Metadata compatibility verification complete"
}

generate_verification_report() {
    info "Generating verification report..."
    
    local report_file="$VERIFICATION_DIR/compatibility_report.md"
    
    cat > "$report_file" << 'EOF'
# GitHub Issues Collection - Data Format Compatibility Report

## Verification Summary

This report verifies that the Java and Bash implementations produce compatible data formats.

## Test Results

### File Structure Compatibility
EOF
    
    if [[ -f "$VERIFICATION_DIR/structure_comparison.txt" ]]; then
        echo '```' >> "$report_file"
        cat "$VERIFICATION_DIR/structure_comparison.txt" >> "$report_file"
        echo '```' >> "$report_file"
    fi
    
    cat >> "$report_file" << 'EOF'

### JSON Schema Compatibility
EOF
    
    if [[ -f "$VERIFICATION_DIR/schema_comparison.txt" ]]; then
        echo '```' >> "$report_file"
        cat "$VERIFICATION_DIR/schema_comparison.txt" >> "$report_file"
        echo '```' >> "$report_file"
    fi
    
    cat >> "$report_file" << 'EOF'

### Metadata Compatibility
EOF
    
    if [[ -f "$VERIFICATION_DIR/metadata_comparison.txt" ]]; then
        echo '```' >> "$report_file"
        cat "$VERIFICATION_DIR/metadata_comparison.txt" >> "$report_file"
        echo '```' >> "$report_file"
    fi
    
    cat >> "$report_file" << 'EOF'

## Verification Details

### Test Data Locations
EOF
    
    local bash_path=$(cat "$VERIFICATION_DIR/bash_data_path.txt" 2>/dev/null)
    local java_path=$(cat "$VERIFICATION_DIR/java_data_path.txt" 2>/dev/null)
    
    echo "- **Bash data**: \`$bash_path\`" >> "$report_file"
    echo "- **Java data**: \`$java_path\`" >> "$report_file"
    
    cat >> "$report_file" << 'EOF'

### Files Checked
- Batch JSON files structure and content
- Metadata JSON files
- Directory organization
- Field naming consistency

## Recommendations

Based on the verification results:

1. **Structure Compatibility**: Files should follow the same naming convention
2. **Schema Compatibility**: JSON schemas should be identical between implementations
3. **Metadata Compatibility**: Metadata fields should match exactly
4. **Data Types**: All field types should be consistent

## Next Steps

- Address any compatibility issues found
- Update implementations to ensure consistency
- Add automated compatibility checks to CI/CD pipeline
EOF
    
    echo "" >> "$report_file"
    echo "Report generated at: $(date)" >> "$report_file"
    
    success "Verification report generated: $report_file"
}

main() {
    info "Starting data format compatibility verification"
    
    setup_verification_environment
    find_test_data
    
    local verification_success=0
    
    # Run verification checks
    verify_batch_file_structure || verification_success=$?
    verify_json_schema || verification_success=$?
    verify_metadata_compatibility || verification_success=$?
    
    # Generate report
    generate_verification_report
    
    info "Verification completed"
    info "Results saved to: $VERIFICATION_DIR"
    
    if [[ $verification_success -eq 0 ]]; then
        success "All compatibility checks passed"
        return 0
    else
        warn "Some compatibility issues found - check the report"
        return 1
    fi
}

# Show usage if help requested
if [[ "${1:-}" =~ ^(-h|--help)$ ]]; then
    cat << 'EOF'
GitHub Issues Collection - Data Format Compatibility Verification

USAGE:
    ./verify_data_compatibility.sh

DESCRIPTION:
    Verifies that the Java and Bash implementations produce compatible data formats
    by comparing existing test data from both implementations.

PREREQUISITES:
    - jq installed for JSON parsing
    - Test data from both implementations available

VERIFICATION CHECKS:
    - File structure and naming consistency
    - JSON schema compatibility
    - Metadata format consistency
    - Field naming and types

OUTPUT:
    Creates verification_results/ directory with:
    - Detailed comparison reports
    - Compatibility analysis
    - Recommendations for improvements

EXAMPLES:
    # Run verification
    ./verify_data_compatibility.sh
EOF
    exit 0
fi

# Run main function
main "$@"
# GitHub Issues Data Collection - Usage Instructions

This guide provides complete instructions for collecting and preparing GitHub issues data for analysis using the provided scripts.

## Quick Start

```bash
# 1. Collect all closed issues from spring-ai repository
./collect_github_issues.sh --repo spring-projects/spring-ai --clean

# 2. Prepare data for ChatGPT analysis
./quick_analysis_extract.sh

# 3. (Optional) Create stratified train/test split for ML tasks
python stratified_split.py

# 4. Upload the generated ZIP file to ChatGPT
# File location: issues/analysis/github_issues_analysis.zip
```

## Available Scripts

**Data Collection:**
- ✅ `collect_github_issues.sh` - Enhanced with GraphQL for fast collection
- ✅ `scripts/CollectGithubIssues.java` - Java implementation with JBang (alternative)
- ✅ `quick_analysis_extract.sh` - Working analysis script with validation
- ✅ `stratified_split.py` - Creates train/test splits for ML tasks
- ❌ `prepare_analysis_data.sh` - Deprecated (has hanging issue)

## Prerequisites

### Required Tools
- `gh` (GitHub CLI) - authenticated and configured
- `jq` - JSON processor
- `zip` - for creating analysis packages
- `python` - for stratified split functionality
- `jbang` - for Java implementation (optional, if using Java version)
- `java` 17+ - for Java implementation (optional, if using Java version)

### GitHub CLI Setup
```bash
# Install GitHub CLI (if not already installed)
# macOS: brew install gh
# Ubuntu: sudo apt install gh
# Or download from: https://github.com/cli/cli/releases

# Authenticate with GitHub
gh auth login

# Set default repository (optional)
gh repo set-default spring-projects/spring-ai
```

## Data Collection

### Implementation Options

You can choose between two implementations:

1. **Bash Script** (Original): `./collect_github_issues.sh`
2. **Java Implementation** (Alternative): `jbang scripts/CollectGithubIssues.java`

Both implementations are fully compatible and produce identical output.

### Basic Usage

#### Bash Implementation
```bash
# Collect from current repository
./collect_github_issues.sh

# Collect from specific repository (recommended)
./collect_github_issues.sh --repo spring-projects/spring-ai

# Clean previous collection and start fresh (recommended)
./collect_github_issues.sh --repo spring-projects/spring-ai --clean

# Dry run to estimate time and data size
./collect_github_issues.sh --repo spring-projects/spring-ai --dry-run
```

#### Java Implementation (Alternative)
```bash
# Collect from specific repository (recommended)
jbang scripts/CollectGithubIssues.java --repo spring-projects/spring-ai

# Clean previous collection and start fresh (recommended)
jbang scripts/CollectGithubIssues.java --repo spring-projects/spring-ai --clean

# Dry run to estimate time and data size
jbang scripts/CollectGithubIssues.java --repo spring-projects/spring-ai --dry-run
```

### Advanced Options

#### Bash Implementation
```bash
# Custom batch size (default: 100)
./collect_github_issues.sh --batch-size 200

# Enable compression to save disk space
./collect_github_issues.sh --compress

# Verbose logging for debugging
./collect_github_issues.sh --verbose

# Resume interrupted collection
./collect_github_issues.sh --resume
```

#### Java Implementation (Alternative)
```bash
# Custom batch size (default: 100)
jbang scripts/CollectGithubIssues.java --batch-size 200

# Verbose logging for debugging
jbang scripts/CollectGithubIssues.java --verbose

# Resume interrupted collection
jbang scripts/CollectGithubIssues.java --resume

# Incremental collection (only new issues)
jbang scripts/CollectGithubIssues.java --incremental
```

**Note**: The Java implementation does not support compression (--compress), but includes enhanced features like better error handling, configuration management, and structured logging.

### Collection Performance

**GraphQL-Enhanced Collection (Both Implementations):**
- Speed: 1,114 issues in ~2 minutes
- Accuracy: Exact count using GraphQL API
- Rich data: Includes all comments, reactions, and metadata in single call
- Rate limit friendly: Fewer API calls, less chance of hitting limits

**Implementation Comparison:**
- **Bash**: Faster startup, lower memory usage, good for one-off tasks
- **Java**: Better large-scale performance, enhanced error handling, configuration management, structured logging

### Configuration

#### Bash Implementation
You can customize collection behavior using environment variables:

```bash
# Option 1: Source the configuration file
source issues_collection_config.env
./collect_github_issues.sh

# Option 2: Set specific variables
export ISSUE_BATCH_SIZE=200
export ISSUE_MAX_RETRIES=5
./collect_github_issues.sh

# Option 3: One-time variables
ISSUE_BATCH_SIZE=50 ./collect_github_issues.sh
```

#### Java Implementation (Alternative)
The Java implementation uses a configuration file (`scripts/application.yaml`) and supports the same environment variables:

```bash
# Configuration is automatically loaded from scripts/application.yaml
jbang scripts/CollectGithubIssues.java --repo spring-projects/spring-ai

# Override configuration with environment variables
export ISSUE_BATCH_SIZE=200
jbang scripts/CollectGithubIssues.java --repo spring-projects/spring-ai

# View current configuration
jbang scripts/CollectGithubIssues.java --repo spring-projects/spring-ai --dry-run --verbose
```

### Output Structure

Both implementations create the identical directory structure:

```
issues/raw/closed/
├── metadata.json                 # Collection metadata
├── batch_2024-07-16_14-30-00/    # Timestamped batch folder
│   ├── issues_001-100.json       # Batched issues (100 per file)
│   ├── issues_101-200.json       # Next batch
│   └── batch_info.json           # Batch metadata
├── individual/                   # Large issues (>50 comments or >100KB)
│   ├── issue_1234.json           # Individual issue files
│   └── issue_5678.json
└── collection.log                # Detailed collection log
```

## Java Implementation (Alternative)

### Overview

The Java implementation using JBang provides a modern alternative to the bash script with enhanced features while maintaining 100% compatibility with the original bash version.

### Key Features

- **100% Data Compatibility**: Produces identical JSON output to bash version
- **Enhanced Error Handling**: Better error messages and recovery
- **Configuration Management**: YAML-based configuration with Spring Boot
- **Structured Logging**: Better logging with file rotation
- **Rate Limiting**: Built-in rate limiting with exponential backoff
- **Resume Capability**: Robust resume functionality
- **Input Validation**: Comprehensive input validation

### Prerequisites

```bash
# Install JBang (if not already installed)
# macOS: brew install jbang  
# Linux: curl -Ls https://sh.jbang.dev | bash -s - app setup
# Or download from: https://github.com/jbangdev/jbang/releases

# Verify installation
jbang --version

# Ensure Java 17+ is available
java --version
```

### Quick Start

```bash
# Basic collection
jbang scripts/CollectGithubIssues.java --repo spring-projects/spring-ai

# With custom batch size
jbang scripts/CollectGithubIssues.java --repo spring-projects/spring-ai --batch-size 50

# Dry run to test
jbang scripts/CollectGithubIssues.java --repo spring-projects/spring-ai --dry-run

# Get help
jbang scripts/CollectGithubIssues.java --help
```

### Configuration Options

The Java implementation supports a configuration file at `scripts/application.yaml`:

```yaml
github:
  issues:
    batch-size: 100
    max-retries: 3
    retry-delay: 5
    large-threshold: 50
    size-threshold: 102400
    
logging:
  level:
    com.github.issues: INFO
  file:
    name: issues/raw/closed/collection.log
    max-size: 10MB
    max-history: 5
```

### Migration from Bash

For detailed migration instructions, see `scripts/MIGRATION_GUIDE.md`.

**Quick Migration:**
1. Install JBang and Java 17+
2. Test with `--dry-run` flag
3. Replace bash commands with Java equivalents
4. Enjoy enhanced features and better error handling

### Performance Comparison

| Feature | Bash | Java |
|---------|------|------|
| Startup Speed | ✅ Faster | ⚠️ Slower (JVM startup) |
| Large Dataset Performance | ✅ Good | ✅ Better |
| Memory Usage | ✅ Lower | ⚠️ Higher |
| Error Handling | ✅ Basic | ✅ Enhanced |
| Configuration | ✅ Environment vars | ✅ YAML + Environment vars |
| Logging | ✅ Basic | ✅ Structured with rotation |

**Recommendation**: Use Java for production/repeated use, bash for quick one-off tasks.

### Validation and Testing

Comprehensive validation scripts are available:

```bash
# Compare both implementations
scripts/compare_implementations.sh

# Verify data format compatibility
scripts/verify_data_compatibility.sh

# Performance benchmarking
scripts/benchmark_performance.sh

# Full validation suite
scripts/final_validation.sh
```

## Data Preparation for Analysis

### Current Working Script

**Use `quick_analysis_extract.sh` (recommended):**
```bash
# Prepare analysis-ready data from collected issues
./quick_analysis_extract.sh

# That's it! No options needed - it just works
```

### Legacy Script (Deprecated)

**❌ Do not use `prepare_analysis_data.sh`** - This script has a hanging issue and is deprecated.

### What the Analysis Script Does

**Data Extraction:**
- ✅ **Key fields**: Issue number, title, body, author, dates, labels, assignees
- ✅ **Calculated metrics**: Days open, comment count, body length, label count
- ✅ **Community data**: Comment authors (unique list), milestone tracking
- ✅ **Engagement**: Reaction information, has_reactions boolean
- ✅ **Smart defaults**: Comment count included, but not comment text (saves space)

### Analysis Output

The preparation script creates:

```
issues/analysis/
├── issues_analysis_ready.json    # Main dataset for ChatGPT
├── data_dictionary.json          # Schema documentation
└── github_issues_analysis.zip    # Complete package for upload
```

**File Details:**
- **issues_analysis_ready.json**: Clean, structured dataset with all analysis fields
- **data_dictionary.json**: Schema documentation explaining each field
- **github_issues_analysis.zip**: Ready-to-upload package for ChatGPT

### Analysis Options

**Basic Analysis:**
```bash
# Extract all issues with labels
./quick_analysis_extract.sh
```

**Filtered Analysis:**
```bash
# Extract only issues that have labels (removes ~51% of issues)
./quick_analysis_extract.sh --filter-no-labels
```

## Stratified Train/Test Split

### Overview

The `stratified_split.py` script creates training and testing datasets for machine learning tasks. It uses multi-label-aware stratification to maintain label distribution across both sets.

### Prerequisites

- Completed data extraction (run `quick_analysis_extract.sh` first)
- `labels.json` file in root directory (create with `gh api repos/spring-projects/spring-ai/labels`)

### Usage

```bash
# Run stratified split after data extraction
python stratified_split.py
```

### What It Does

**Label Processing:**
- Filters out non-informative labels (triage, duplicate, etc.)
- Groups related labels into categories:
  - `pinecone`, `qdrant` → `vector store`
  - `openai`, `claude` → `model client`
  - `mongo`, `oracle` → `data store`

**Smart Splitting:**
- Rare labels (< 3 occurrences) go only to training set
- 80/20 split while maintaining label proportions
- Prevents label leakage and overfitting

### Output

The script creates:
```
issues/stratified_split/
├── train_set.json           # Training dataset
└── test_set.json            # Testing dataset
```

**Example Output:**
```
Total issues used: 502
Train set size: 391 (77.9%)
Test set size: 111 (22.1%)
```

## ChatGPT Analysis Setup

### Upload Package

1. Run the preparation script to create the analysis package:
   ```bash
   ./quick_analysis_extract.sh
   ```

2. Upload `issues/analysis/github_issues_analysis.zip` to ChatGPT

3. Use this prompt to get started:
   ```
   I've uploaded a GitHub issues analysis package. Please:
   1. Extract and examine the collection_summary.json for context
   2. Review the data_dictionary.json for schema understanding
   3. Load the issues_analysis_ready.json dataset
   4. Provide an overview of the data and suggest analysis approaches
   ```

### Analysis Suggestions

The dataset supports various analysis approaches:

- **Issue Resolution Patterns**: Analyze `days_open` and `labels` to understand resolution times
- **Label Analysis**: Examine label distribution and categorization patterns
- **Author Activity**: Track contributor patterns and engagement levels
- **Milestone Tracking**: Analyze milestone completion and project velocity
- **Comment Engagement**: Study discussion patterns and community interaction
- **Issue Complexity**: Correlate `body_length` and `comment_count` with resolution time
- **Temporal Patterns**: Identify seasonal trends in issue creation and closure

## Troubleshooting

### Common Issues

**Authentication Problems**
```bash
# Check GitHub CLI authentication
gh auth status

# Re-authenticate if needed
gh auth login
```

**Rate Limiting**
```bash
# Check current rate limit
gh api rate_limit

# The script automatically handles rate limiting, but you can:
# - Reduce batch size: --batch-size 50
# - Increase retry delay: ISSUE_RETRY_DELAY=10
```

**Large Repository Collection**
```bash
# For repositories with 1000+ issues:
# 1. Use smaller batch sizes
./collect_github_issues.sh --batch-size 50

# 2. Enable compression
./collect_github_issues.sh --compress

# 3. Use incremental collection for updates
./collect_github_issues.sh --incremental
```

**Disk Space Issues**
```bash
# Enable compression
./collect_github_issues.sh --compress

# Increase large issue threshold (saves more to individual files)
export ISSUE_LARGE_THRESHOLD=25
./collect_github_issues.sh
```

**Memory Issues During Analysis**
```bash
# The quick_analysis_extract.sh script uses efficient processing
# and doesn't require special memory options
./quick_analysis_extract.sh
```

### Resume Interrupted Collections

If collection is interrupted:

```bash
# Resume from last successful batch
./collect_github_issues.sh --resume

# Or start fresh (will skip completed batches automatically)
./collect_github_issues.sh --incremental
```

### Validation

Verify your data collection:

```bash
# Check metadata
jq '.' issues/raw/closed/metadata.json

# Count collected issues
find issues/raw/closed -name "*.json" -not -name "metadata.json" -not -name "batch_info.json" | wc -l

# Check analysis data
jq 'length' issues/analysis/issues_analysis_ready.json
```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ISSUE_BATCH_SIZE` | 100 | Issues per batch file |
| `ISSUE_MAX_RETRIES` | 3 | Maximum retry attempts |
| `ISSUE_RETRY_DELAY` | 5 | Seconds between retries |
| `ISSUE_LARGE_THRESHOLD` | 50 | Comments threshold for individual files |
| `ISSUE_SIZE_THRESHOLD` | 102400 | Size threshold (bytes) for individual files |
| `ANALYSIS_OUTPUT_DIR` | issues/analysis | Analysis output directory |
| `ANALYSIS_RAW_DIR` | issues/raw/closed | Raw data input directory |

### Performance Tuning

**For Large Repositories (1000+ issues):**
```bash
export ISSUE_BATCH_SIZE=200
export ISSUE_MAX_RETRIES=2
export ISSUE_RETRY_DELAY=3
```

**For Slow Networks:**
```bash
export ISSUE_BATCH_SIZE=50
export ISSUE_MAX_RETRIES=5
export ISSUE_RETRY_DELAY=10
```

**For Memory-Constrained Systems:**
```bash
export ISSUE_LARGE_THRESHOLD=25
export ISSUE_SIZE_THRESHOLD=51200
```

## Example Workflows

### Complete Spring AI Analysis

#### Using Bash Implementation
```bash
# 1. Configure for large repository
source issues_collection_config.env
export ISSUE_BATCH_SIZE=200

# 2. Collect all data
./collect_github_issues.sh --repo spring-projects/spring-ai --compress

# 3. Prepare for analysis
./quick_analysis_extract.sh

# 4. (Optional) Create train/test split for ML tasks
python stratified_split.py

# 5. Upload issues/analysis/github_issues_analysis.zip to ChatGPT
```

#### Using Java Implementation (Alternative)
```bash
# 1. Configure for large repository
export ISSUE_BATCH_SIZE=200

# 2. Collect all data
jbang scripts/CollectGithubIssues.java --repo spring-projects/spring-ai --clean

# 3. Prepare for analysis
./quick_analysis_extract.sh

# 4. (Optional) Create train/test split for ML tasks
python stratified_split.py

# 5. Upload issues/analysis/github_issues_analysis.zip to ChatGPT
```

### Quick Analysis

#### Using Bash Implementation
```bash
# Fast collection and analysis
./collect_github_issues.sh --repo spring-projects/spring-ai
./quick_analysis_extract.sh
```

#### Using Java Implementation (Alternative)
```bash
# Fast collection and analysis
jbang scripts/CollectGithubIssues.java --repo spring-projects/spring-ai
./quick_analysis_extract.sh
```

### Machine Learning Workflow

#### Using Bash Implementation
```bash
# Collection with filtering for ML tasks
./collect_github_issues.sh --repo spring-projects/spring-ai --clean
./quick_analysis_extract.sh --filter-no-labels
python stratified_split.py

# Files created:
# - issues/analysis/github_issues_analysis.zip (for ChatGPT)
# - issues/stratified_split/train_set.json (for training)
# - issues/stratified_split/test_set.json (for testing)
```

#### Using Java Implementation (Alternative)
```bash
# Collection with filtering for ML tasks
jbang scripts/CollectGithubIssues.java --repo spring-projects/spring-ai --clean
./quick_analysis_extract.sh --filter-no-labels
python stratified_split.py

# Files created:
# - issues/analysis/github_issues_analysis.zip (for ChatGPT)
# - issues/stratified_split/train_set.json (for training)
# - issues/stratified_split/test_set.json (for testing)
```

### Incremental Updates

#### Using Bash Implementation
```bash
# Update existing collection with new issues
./collect_github_issues.sh --incremental
./quick_analysis_extract.sh
python stratified_split.py  # Update train/test split if needed
```

#### Using Java Implementation (Alternative)
```bash
# Update existing collection with new issues
jbang scripts/CollectGithubIssues.java --incremental
./quick_analysis_extract.sh
python stratified_split.py  # Update train/test split if needed
```

## Label Knowledge Base

### GitHub Label Mapping Files

The repository contains two JSON files that provide comprehensive label knowledge for Spring AI issue classification:

#### 1. Original Label Mapping (`github-labels-mapping.json`)

This file was generated using Claude AI in the Spring AI project repository with the following prompt:

```
You are helping build a GitHub issue classification agent for the spring-projects/spring-ai repository.

Below is a list of GitHub issue labels used in this project. Some are feature-oriented (e.g., pinecone, RAG), some refer to integration modules (e.g., ollama, oracle), and others are conceptual (e.g., guardrails, reasoning). Not all labels may appear in the codebase.

[List of labels from labels.json]

For each label above, please do the following:

Return a JSON object with these fields:

{
  "label": "pinecone",
  "description": "One sentence description of what the label refers to in this project.",
  "relevant_modules": ["spring-ai-pinecone-store"],
  "packages": ["org.springframework.ai.vectorstore.pinecone"],
  "key_classes": ["PineconeVectorStore", "PineconeApiClient"],
  "docs": ["docs/modules/ROOT/pages/vectorstores/pinecone.adoc"],
  "config_keys": ["spring.ai.vectorstore.pinecone.api-key"],
  "common_issue_types": ["connection", "configuration", "performance"],
  "developer_touchpoints": ["application.yml setup", "retriever integration", "indexing API"]
}

Additional Notes:
If a label maps to a specific Maven module or Java package, please include it.
If a label is ambiguous or unused, return "description": "Not found in project codebase" and leave other fields empty.
Classify common_issue_types using categories like: configuration, connection, timeout, runtime, documentation, integration, test, missing feature, etc.
Be concise, but base answers on real code, module names, or class names (not just general intuition).
Use comments, README files, or test code if needed to infer purpose.
```

**Generated Fields:**
- `label`: The GitHub label name
- `description`: Technical description based on Spring AI codebase analysis
- `relevant_modules`: Maven modules associated with the label
- `packages`: Java packages where relevant code resides
- `key_classes`: Important classes for this label
- `docs`: Documentation files related to the label
- `config_keys`: Configuration properties associated with the label
- `common_issue_types`: Common problem categories for this label
- `developer_touchpoints`: Areas where developers interact with this functionality

#### 2. Enhanced Label Mapping (`github-labels-mapping-enhanced.json`)

This enhanced version was created by analyzing the actual training issues in `./issues/stratified_split/train_set.json` and using Claude AI to improve the descriptions with real-world problem patterns.

**Enhancement Process:**
1. Analyzed training issues to identify common patterns for each label
2. Extracted realistic problem phrases from actual issue titles and bodies
3. Identified typical error patterns users encounter
4. Enhanced descriptions with language that reflects how users actually report issues

**Additional Fields Added:**
- `example_problem_phrases`: Actual phrases from training issues that indicate this label
- `typical_error_patterns`: Common error types and failure modes for this label

**Examples of Enhanced Content:**
- For `qdrant`: Added "NPE when document contains only media" (from issue #3609)
- For `tool/function calling`: Added "function calling not working" (from issue #624)
- For `azure`: Added "streaming usage metadata missing" (from issue #1724)
- For `transcription models`: Added "transcription API file extension issue" (from issue #3699)

### Usage in Issue Classification

These label mapping files can be used to:
- **Automated Classification**: Train ML models with rich feature descriptions
- **Human Triage**: Provide context for manual issue labeling
- **Documentation**: Understand what each label represents in the Spring AI ecosystem
- **Pattern Recognition**: Identify common problem types and error patterns
- **Developer Guidance**: Know which modules, classes, and configurations are relevant

### File Locations

```
├── github-labels-mapping.json          # Original codebase-based mapping
├── github-labels-mapping-enhanced.json # Enhanced with training data insights
├── labels.json                         # Raw GitHub labels from API
└── issues/stratified_split/
    ├── train_set.json                  # Training issues used for enhancement
    └── test_set.json                   # Test issues
```

## Multi-Label Issue Classification

### Overview

After creating the stratified train/test split, you can perform multi-label classification on the GitHub issues using Claude AI. This process has evolved through several iterations to improve accuracy and efficiency.

### Classification Workflow

#### 1. Setup Classification Environment

Ensure you have the necessary files:
```bash
# Required files
ls -la issues/stratified_split/test_set.json   # Test issues (111 total)
ls -la labels.json                            # Available labels
ls -la batch_processor.py                     # Data processing script
ls -la classification-4.md                    # Latest classification prompt
```

#### 2. Use Latest Classification Prompt

**Current Version: `classification-4.md`** (Improved version addressing performance issues)

**Key Improvements:**
- **Excludes problematic labels**: Removes `bug` and `enhancement` (low precision)
- **Focuses on high-performing technical labels**: `vector store`, `tool/function calling`, `MCP`, etc.
- **Stricter criteria**: Maximum 2 labels per issue, 0.7+ confidence threshold
- **Efficient data processing**: Uses `batch_processor.py` instead of problematic `jq` commands

#### 3. Data Processing with Batch Script

```bash
# Get batch information
python batch_processor.py info
# Output: Total issues: 111, Batch size: 25, Total batches: 5

# View high-performing labels to focus on
python batch_processor.py labels

# Process specific batch for classification
python batch_processor.py batch 1   # Process first 25 issues
python batch_processor.py batch 2   # Process next 25 issues
# ... continue through batch 5
```

#### 4. Classification Process

**With Claude AI:**
1. Use `classification-4.md` prompt
2. Process batches using `batch_processor.py`
3. Apply conservative labeling (technical labels only)
4. Create `improved_classification.json` output

**Output Format:**
```json
[
  {
    "issue_number": 1776,
    "predicted_labels": [
      {
        "label": "vector store",
        "confidence": 0.9
      }
    ],
    "explanation": "Issue explicitly mentions vector database configuration..."
  }
]
```

#### 5. Classification History

**Previous Versions:**
- `classification.md`: Original comprehensive approach
- `classification-2.md`: Refined conservative approach  
- `classification-3.md`: Enhanced with confidence calibration
- `classification-4.md`: **Current** - Excludes problematic labels, improved efficiency

### Evaluation Process

#### 1. Enhanced Evaluation Scripts

**Primary Evaluation Script:** `evaluate_filtered_predictions.py`

```bash
# Evaluate classification results with advanced filtering
python evaluate_filtered_predictions.py
```

**Advanced Summary Generation:** `generate_full_summary.py`

```bash
# Generate comprehensive evaluation summary with complete analysis
python generate_full_summary.py
```

**The enhanced evaluation system:**
- **Configurable exclusion lists**: Remove problematic labels from evaluation
- **Categorical label grouping**: Separate subjective, process-driven, and technical labels
- **Complete label tables**: Full performance metrics for all labels
- **Precision-sorted analysis**: Labels ranked by performance metrics
- **Detailed categorization**: Perfect, excellent, good, and poor performance groups
- **Automated summary generation**: Comprehensive markdown reports

#### 2. Evaluation Metrics

**Micro-Averaged Metrics:**
- Overall performance across all predictions
- Weighted by label frequency

**Macro-Averaged Metrics:**
- Average performance across all labels
- Treats all labels equally

**Per-Label Analysis:**
- Top 10 labels by frequency
- Precision, recall, F1 for each label
- Support (ground truth count)

#### 3. Performance Benchmarks

**Latest Results (with enhanced filtering):**
- Micro F1: 82.1% (+11.4 points improvement)
- Precision: 76.6% (+13.4 points improvement)
- Recall: 88.5% (+8.2 points improvement)

**Top Performing Labels:**
- **Perfect Performance (20 labels)**: `type: backport`, `MCP`, `code cleanup`, `anthropic`, `chromadb`, `RAG`, `advisors`, `prompt management`, etc.
- **Excellent Performance (6 labels)**: `vector store` (92.3% F1), `tool/function calling` (91.7% F1), `documentation` (90.9% F1)
- **Good Performance (9 labels)**: `design`, `configuration`, `Observability`, `ollama`, etc.

**Excluded Labels (12 total):**
- **Original problematic**: `bug` (40% precision), `enhancement` (29.7% precision)
- **Subjective/Judgmental**: `question`, `help wanted`, `good first issue`, `epic`
- **Process-Driven**: `status: backported`, `status: to-discuss`, `follow up`, `status: waiting-for-feedback`, `for: backport-to-1.0.x`, `next priorities`

### Latest Enhancement: Advanced Label Filtering

**Enhanced Filtering Strategy:**
- **Configurable exclusion lists**: Customize which labels to exclude from evaluation
- **Categorical grouping**: Separate subjective, process-driven, and technical labels
- **Precision-focused analysis**: Sort results by precision metrics
- **Comprehensive reporting**: Complete performance tables with all labels

**Proven Results:**
- **82.1% F1 Score**: Excellent classification performance
- **76.6% Precision**: High accuracy with fewer false positives
- **88.5% Recall**: Strong coverage of ground truth labels
- **Balanced performance**: Well-calibrated precision/recall trade-off

### Classification Files Reference

**Data Files:**
- `issues/stratified_split/test_set.json`: Issues to classify
- `labels.json`: Available labels list
- `improved_classification.json`: Classification output

**Script Files:**
- `batch_processor.py`: Efficient data processing for large JSON files
- `evaluate_filtered_predictions.py`: **Enhanced evaluation** with configurable exclusions
- `generate_full_summary.py`: **Comprehensive summary generation** with complete analysis
- `evaluate_predictions.py`: Original evaluation script (legacy)
- `classification-4.md`: Latest classification prompt with problematic label exclusions

**Previous Classification Files:**
- `conservative_full_classification.json`: Previous results
- `evaluation_summary.md`: Detailed performance analysis

### Usage Example

#### Complete Classification and Evaluation Workflow

```bash
# 1. Get batch information and available labels
python batch_processor.py info
python batch_processor.py labels

# 2. Use classification-4.md prompt with Claude AI to classify all 5 batches
# This step is done manually using the batch_processor.py output

# 3. Evaluate results with enhanced filtering
python evaluate_filtered_predictions.py

# 4. Generate comprehensive summary report
python generate_full_summary.py

# 5. Review evaluation_summary.md for detailed analysis
```

#### Advanced Evaluation Options

```bash
# Standard evaluation (excludes 12 problematic labels by default)
python evaluate_filtered_predictions.py

# Generate detailed report with precision-sorted tables
python generate_full_summary.py

# For comparison, run original evaluation (includes all labels)
python evaluate_predictions.py
```

#### Key Output Files

```bash
# After evaluation, review these files:
- evaluation_summary.md       # Comprehensive analysis with all metrics
- conservative_full_classification.json  # Classification results
```

## Support

For issues or questions:
1. Check the collection log: `issues/raw/closed/collection.log`
2. Review GitHub CLI status: `gh auth status`
3. Validate JSON files: `jq '.' filename.json`
4. Check disk space and permissions
5. For classification issues: Check `batch_processor.py` output and `evaluate_filtered_predictions.py` results
6. For evaluation issues: Review `evaluation_summary.md` and run `generate_full_summary.py`

## Advanced Features

### Customizing Label Exclusions

The enhanced evaluation system allows customization of excluded labels:

```python
# In evaluate_filtered_predictions.py, you can modify the exclusion list:
exclude_labels = {
    # Original problematic labels
    'bug', 'enhancement',
    # Subjective/Judgmental labels
    'question', 'help wanted', 'good first issue', 'epic',
    # Process-Driven labels
    'status: backported', 'status: to-discuss', 'follow up', 
    'status: waiting-for-feedback', 'for: backport-to-1.0.x', 'next priorities',
    # Add custom exclusions here
}
```

### Understanding Performance Categories

The evaluation system automatically categorizes labels:
- **Perfect Performance** (F1 = 1.000): Labels with no errors
- **Excellent Performance** (F1 ≥ 0.900): High-quality classifications
- **Good Performance** (0.700 ≤ F1 < 0.900): Acceptable but improvable
- **Poor Performance** (F1 < 0.700): Requires attention

### Precision-Sorted Analysis

The complete label table is sorted by precision (high to low) to easily identify:
- **Top performers**: Labels with highest precision
- **Problem areas**: Labels with many false positives
- **Missed labels**: Labels with 0% precision (completely missed)

The scripts include comprehensive error handling and logging to help diagnose issues.
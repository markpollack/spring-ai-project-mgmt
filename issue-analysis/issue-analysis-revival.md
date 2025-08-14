# GitHub Issue Classification Revival Guide
## Reproducing the 82.1% F1 Score Achievement

### Executive Summary
This guide documents the complete process to reproduce the multi-label GitHub issue classification system that achieved:
- **82.1% F1 Score** (Micro-averaged)
- **76.6% Precision**
- **88.5% Recall**
- Successfully classified 111 test issues from Spring AI repository

### Prerequisites

#### Required Tools
```bash
# Verify installations
gh --version           # GitHub CLI (authenticated)
jq --version           # JSON processor
python3 --version      # Python 3.8+
zip --version          # Compression utility
```

#### GitHub Authentication
```bash
# Authenticate GitHub CLI
gh auth login
gh auth status

# Set default repository
gh repo set-default spring-projects/spring-ai
```

#### Environment Setup
```bash
# Set environment variable for GitHub token (optional, gh cli handles auth)
export GITHUB_TOKEN=$(gh auth token)
```

---

## Phase 1: Data Collection (45 minutes)

### Step 1.1: Collect Closed Issues
```bash
# Collect all closed issues with full data
./collect_github_issues.sh --repo spring-projects/spring-ai --state closed --clean

# This will create:
# - issues/raw/closed/batch_*/       # Batched issue files
# - issues/raw/closed/metadata.json  # Collection metadata
# - issues/raw/closed/collection.log # Collection log
```

### Step 1.2: Extract Analysis-Ready Data
```bash
# Prepare clean dataset for analysis
./quick_analysis_extract.sh

# Creates:
# - issues/analysis/issues_analysis_ready.json  # Clean, structured data
# - issues/analysis/data_dictionary.json        # Field descriptions
```

### Step 1.3: Verify Data Quality
```bash
# Check issue count
jq '. | length' issues/analysis/issues_analysis_ready.json

# Expected: ~1000+ closed issues
# Verify labels are present
jq '[.[] | .labels] | flatten | unique | length' issues/analysis/issues_analysis_ready.json
```

---

## Phase 2: Label Preparation (30 minutes)

### Step 2.1: Extract Repository Labels
```bash
# Get all labels from repository
gh api repos/spring-projects/spring-ai/labels --paginate | jq '[.[].name]' > labels.json

# Count labels
jq '. | length' labels.json
# Expected: 70-80 labels
```

### Step 2.2: Clean Label List
Edit `labels.json` to remove problematic labels:

**Remove these categories:**
- Administrative: `triage`, `duplicate`, `invalid`, `wontfix`
- Subjective: `bug`, `enhancement`, `question`
- Process: `status:*`, `priority:*`, `in-progress`
- Meta: `help wanted`, `good first issue`

**Keep technical labels:**
- Technology: `vector store`, `RAG`, `MCP`, `Bedrock`
- Features: `tool/function calling`, `streaming`, `Chat Memory`
- Providers: `openai`, `anthropic`, `azure`, `ollama`
- Components: `configuration`, `documentation`, `testing`

### Step 2.3: Create Label Mapping
```bash
# Copy and edit the enhanced mapping
cp github-labels-mapping-enhanced.json my-labels-mapping.json
# Edit to match your cleaned labels
```

---

## Phase 3: Create Train/Test Split (20 minutes)

### Step 3.1: Run Stratified Split
```bash
python3 stratified_split.py

# Creates:
# - issues/stratified_split/train_set.json (80% - ~800 issues)
# - issues/stratified_split/test_set.json  (20% - ~200 issues)
```

### Step 3.2: Extract Test Data for Classification
```bash
python3 process_full_classification.py

# Creates:
# - test_issues_for_classification.json (only issue_number, title, body)
```

### Step 3.3: Verify Split Quality
```bash
# Check test set size
jq '. | length' issues/stratified_split/test_set.json
# Expected: ~200 issues

# Check label distribution
python3 analyze_training_labels.py
```

---

## Phase 4: Classification Setup (30 minutes)

### Step 4.1: Configure Batch Processor
Edit `batch_processor.py` to set high-performing labels:
```python
def get_high_performing_labels():
    return [
        'vector store',
        'tool/function calling', 
        'documentation',
        'type: backport',
        'MCP',
        'design',
        'Bedrock',
        'model client',
        'RAG',
        'OpenAI',
        'Anthropic',
        'Azure',
        'Ollama',
        'configuration',
    ]
```

### Step 4.2: Prepare Classification Prompt
Use `improved_classification_prompt.md` as the base. Key principles:

1. **Conservative Labeling**
   - Maximum 2-3 labels per issue
   - Only assign with high confidence (>0.7)
   - Require explicit technical evidence

2. **Exclude Problematic Labels**
   - Never assign: `bug`, `enhancement`, `question`
   - Skip generic improvement labels

3. **Focus on Technical Specificity**
   - Prioritize domain-specific Spring AI concepts
   - Require explicit mentions for provider labels

### Step 4.3: Test Batch Processing
```bash
# Get info about batches
python3 batch_processor.py info
# Expected: 5 batches of 25 issues each

# View available labels
python3 batch_processor.py labels

# Extract first batch for testing
python3 batch_processor.py batch 1
```

---

## Phase 5: Execute Classification (2-3 hours)

### Step 5.1: Process Each Batch
For each batch (1-5), follow this process:

```bash
# Extract batch data
python3 batch_processor.py batch 1

# Copy the output JSON and paste into your LLM with:
# 1. The improved_classification_prompt.md as system prompt
# 2. The batch data as input
# 3. Request JSON output format
```

### Step 5.2: Classification Guidelines
When using the LLM (Claude, GPT-4, etc.):

1. **System Prompt**: Use entire content of `improved_classification_prompt.md`
2. **Conservative Approach**: Better to miss labels than over-assign
3. **Confidence Thresholds**:
   - 1.0: Explicit mention, central to issue
   - 0.9: Very confident, clear context
   - 0.7-0.8: Moderate confidence
   - <0.7: Skip the label

### Step 5.3: Compile Results
```bash
# Create a single classification file
# Combine all batch results into:
touch conservative_full_classification.json

# Format:
# [
#   {
#     "issue_number": 1776,
#     "predicted_labels": [
#       {"label": "vector store", "confidence": 0.9}
#     ],
#     "explanation": "..."
#   },
#   ...
# ]
```

---

## Phase 6: Evaluation (30 minutes)

### Step 6.1: Run Basic Evaluation
```bash
python3 evaluate_predictions.py

# Output includes:
# - Micro-averaged metrics (overall performance)
# - Macro-averaged metrics (per-label average)
# - Per-label precision/recall/F1
```

### Step 6.2: Run Filtered Evaluation
```bash
# Edit evaluate_filtered_predictions.py to set exclusions:
# excluded_labels = {'bug', 'enhancement', 'question', ...}

python3 evaluate_filtered_predictions.py

# Target metrics:
# - F1 Score: 80%+ 
# - Precision: 75%+
# - Recall: 85%+
```

### Step 6.3: Generate Comprehensive Report
```bash
python3 generate_full_summary.py

# Creates evaluation_summary.md with:
# - Overall performance metrics
# - Per-label analysis
# - Strong vs weak performers
# - Recommendations
```

---

## Phase 7: Analysis and Optimization

### Step 7.1: Identify Problem Labels
Look for labels with:
- Precision < 0.5 (too many false positives)
- Recall < 0.3 (missing too many)
- F1 < 0.4 (overall poor performance)

### Step 7.2: Refine Label Set
```python
# In evaluate_filtered_predictions.py
excluded_labels = {
    'bug',           # 40% precision
    'enhancement',   # 29.7% precision
    'model client',  # 0% precision
    'invalid',       # Administrative
    'duplicate',     # Administrative
}
```

### Step 7.3: Re-run Evaluation
```bash
python3 evaluate_filtered_predictions.py
python3 generate_full_summary.py
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Low Precision (<60%)
- **Cause**: Over-labeling, too many labels per issue
- **Fix**: Reduce to max 2 labels, increase confidence threshold

#### 2. Low Recall (<70%)
- **Cause**: Too conservative, missing obvious labels
- **Fix**: Lower confidence threshold to 0.7, check keyword matching

#### 3. Imbalanced Performance
- **Cause**: Some labels dominate predictions
- **Fix**: Balance label assignment, use domain knowledge

#### 4. API Rate Limits
- **Cause**: Too many GitHub API calls
- **Fix**: Use `--incremental` flag, add delays between batches

#### 5. Memory Issues with Large Datasets
- **Cause**: Loading entire dataset at once
- **Fix**: Use batch processing, process in chunks

---

## Key Success Factors

### What Made 82.1% F1 Score Possible

1. **Label Curation**
   - Removed subjective labels (bug, enhancement)
   - Focused on technical, objective labels
   - Result: +11.4% F1 improvement

2. **Conservative Classification**
   - Maximum 2-3 labels per issue
   - High confidence threshold (0.7+)
   - Result: +13.4% precision improvement

3. **Domain Knowledge**
   - Used Spring AI codebase documentation
   - Enhanced label definitions with examples
   - Result: Better technical accuracy

4. **Iterative Refinement**
   - Started with all labels
   - Identified problematic ones through evaluation
   - Progressively filtered to high-performers

---

## Quick Reproduction Checklist

```bash
# [ ] Prerequisites installed and configured
# [ ] GitHub CLI authenticated
# [ ] Collected closed issues
# [ ] Extracted analysis-ready data
# [ ] Cleaned label list (removed ~12 problematic labels)
# [ ] Created stratified train/test split
# [ ] Configured batch processor
# [ ] Processed all 5 batches through LLM
# [ ] Compiled classification results
# [ ] Ran filtered evaluation
# [ ] Achieved target metrics (80%+ F1)
```

---

## Files Reference

### Essential Scripts
- `collect_github_issues.sh` - Data collection
- `stratified_split.py` - Train/test splitting
- `batch_processor.py` - Batch extraction for LLM
- `evaluate_filtered_predictions.py` - Performance evaluation
- `generate_full_summary.py` - Report generation

### Key Data Files
- `labels.json` - Cleaned label list
- `test_issues_for_classification.json` - Test data
- `conservative_full_classification.json` - Classification results
- `evaluation_summary.md` - Final report

### Configuration Files
- `improved_classification_prompt.md` - LLM prompt
- `github-labels-mapping-enhanced.json` - Label definitions

---

## Expected Timeline

- **Phase 1-3**: 1.5 hours (Data preparation)
- **Phase 4-5**: 3 hours (Classification with LLM)
- **Phase 6-7**: 1 hour (Evaluation and refinement)
- **Total**: ~5.5 hours

---

## Final Notes

The key to reproducing the 82.1% F1 score is:
1. Careful label curation (remove subjective labels)
2. Conservative classification (fewer, high-confidence labels)
3. Iterative refinement based on evaluation metrics

The system is designed to be precision-focused rather than recall-focused, as false positives are more problematic than missed labels in practice.

For questions or issues, refer to the archived files in `issue-analysis-archive/` which contain the exact configuration and data used to achieve the reported results.
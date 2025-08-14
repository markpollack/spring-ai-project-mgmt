# GitHub Issue Classification for Spring Ecosystem Projects

## Quick Start Guide for Multi-Label Classification

This guide enables developers of Spring ecosystem projects to implement automated GitHub issue classification using the methodology successfully applied to Spring AI (achieving 82.1% F1 score).

## 📋 Prerequisites

### Required Tools
- `gh` (GitHub CLI) - authenticated and configured
- `jq` - JSON processor
- `python` - for data processing and evaluation
- `zip` - for creating analysis packages
- **Claude AI or similar LLM** - for classification tasks

### Repository Requirements
- Active GitHub repository with labeled issues
- Minimum 200-300 labeled issues recommended
- Consistent labeling practices (avoid one-off labels)

## 🚀 Step-by-Step Implementation

### Step 1: Data Collection (30 minutes)

```bash
# Clone this repository or copy the collection scripts
git clone [this-repo-url]
cd spring-ai-project-mgmt

# Configure for your repository
export GITHUB_REPO="your-org/your-spring-project"

# Collect all closed issues
./collect_github_issues.sh --repo $GITHUB_REPO --clean

# Prepare analysis-ready data
./quick_analysis_extract.sh
```

**Expected Output:**
- `issues/raw/closed/`: Raw issue data
- `issues/analysis/issues_analysis_ready.json`: Cleaned dataset
- Collection metadata and logs

### Step 2: Label Analysis and Cleanup (45 minutes)

```bash
# Extract repository labels
gh api repos/$GITHUB_REPO/labels | jq '[.[].name]' > labels.json

# Create stratified train/test split
python stratified_split.py
```

**Manual Tasks:**
1. **Review `labels.json`** - Remove administrative labels (triage, duplicate, etc.)
2. **Consolidate similar labels** - Group related labels (e.g., `pinecone`, `qdrant` → `vector store`)
3. **Identify problematic labels** - Mark subjective labels for later exclusion

**Expected Output:**
- `labels.json`: Cleaned label list
- `issues/stratified_split/train_set.json`: Training data (80%)
- `issues/stratified_split/test_set.json`: Test data (20%)

### Step 3: Label Knowledge Enhancement (60 minutes)

Create enhanced label mapping using your project's codebase:

```bash
# Use classification prompt template
cp classification-4.md your-project-classification.md
```

**Customization Tasks:**
1. **Update domain context** - Replace Spring AI references with your project
2. **Add project-specific labels** - Include your technical labels and patterns
3. **Define exclusion categories:**
   - **Subjective labels**: `bug`, `enhancement`, `question`
   - **Process labels**: `status:*`, `priority:*`, `triage`
   - **Administrative**: `duplicate`, `invalid`, `wontfix`

**Expected Output:**
- `your-project-classification.md`: Customized classification prompt
- Domain-specific label definitions and examples

### Step 4: Classification Setup (20 minutes)

```bash
# Test batch processing
python batch_processor.py info
python batch_processor.py labels

# Customize exclusion list in evaluate_filtered_predictions.py
# Add your project's problematic labels to the exclusion set
```

**Configuration:**
- Update `batch_processor.py` with your high-performing labels
- Modify exclusion lists in `evaluate_filtered_predictions.py`
- Test with small batches first

### Step 5: Execute Classification (2-3 hours)

```bash
# Process in batches using your LLM
python batch_processor.py batch 1
# Copy output to your LLM with your-project-classification.md prompt
# Save results to classification_results.json

# Repeat for all batches
for i in {1..5}; do
    python batch_processor.py batch $i
    echo "Process batch $i with your LLM..."
done
```

**LLM Classification Process:**
1. Use `your-project-classification.md` as system prompt
2. Process each batch with `batch_processor.py` output
3. Apply conservative labeling (max 2-3 labels, high confidence)
4. Compile results into `classification_results.json`

### Step 6: Evaluation and Analysis (30 minutes)

```bash
# Update evaluation script with your results file
# Edit evaluate_filtered_predictions.py to load your classification_results.json

# Run evaluation with filtering
python evaluate_filtered_predictions.py

# Generate comprehensive report
python generate_full_summary.py
```

**Expected Results:**
- Performance metrics (precision, recall, F1)
- Per-label analysis sorted by precision
- Identification of high-performing vs problematic labels
- Comprehensive `evaluation_summary.md` report

## 📊 Success Metrics

### Target Performance (Based on Spring AI Results)
- **F1 Score**: 80%+ (excellent)
- **Precision**: 75%+ (high accuracy)
- **Recall**: 85%+ (good coverage)
- **Label Coverage**: 85%+ of ground truth labels

### Performance Categories
- **Perfect Performance** (F1 = 1.0): 15-25 labels
- **Excellent Performance** (F1 ≥ 0.9): 5-10 labels  
- **Good Performance** (0.7 ≤ F1 < 0.9): 10-15 labels
- **Poor Performance** (F1 < 0.7): Exclude from auto-labeling

## 🔧 Project-Specific Customizations

### For Different Spring Projects

**Spring Boot:**
- Focus on: `configuration`, `actuator`, `security`, `web`, `data`
- Exclude: `question`, `enhancement`, `status:*`

**Spring Security:**
- Focus on: `oauth2`, `authentication`, `authorization`, `csrf`, `cors`
- Exclude: `question`, `bug`, `enhancement`

**Spring Data:**
- Focus on: `jpa`, `mongodb`, `redis`, `elasticsearch`, `repository`
- Exclude: `question`, `enhancement`, `status:*`

### Label Exclusion Strategy

```python
# Customize in evaluate_filtered_predictions.py
exclude_labels = {
    # Universal exclusions
    'bug', 'enhancement', 'question', 'duplicate', 'invalid',
    # Project-specific exclusions
    'status: backported', 'priority: high', 'triage',
    # Add your administrative labels here
}
```

## 📈 Expected Timeline

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| Setup | 30 min | Tool installation, repository configuration |
| Data Collection | 30 min | Issue collection, data preparation |
| Label Analysis | 45 min | Label cleanup, consolidation |
| Knowledge Enhancement | 60 min | Prompt customization, domain adaptation |
| Classification Setup | 20 min | Batch processing, exclusion configuration |
| Classification Execution | 2-3 hours | LLM processing, result compilation |
| Evaluation | 30 min | Performance analysis, report generation |
| **Total** | **4-5 hours** | Complete implementation |

## 🛠️ Troubleshooting

### Common Issues

**Low Precision (<70%):**
- Increase exclusion list
- Raise confidence threshold
- Focus on technical labels only

**Low Recall (<75%):**
- Reduce exclusion list
- Lower confidence threshold
- Review missed high-frequency labels

**Inconsistent Results:**
- Improve prompt specificity
- Add more domain examples
- Standardize label definitions

### Performance Optimization

```bash
# For large repositories (1000+ issues)
export ISSUE_BATCH_SIZE=50
./collect_github_issues.sh --batch-size 50

# For memory constraints
export ISSUE_LARGE_THRESHOLD=25
```

## 📋 Output Files

After successful implementation, you'll have:

```
your-project-classification/
├── labels.json                    # Cleaned label taxonomy
├── issues/
│   ├── analysis/
│   │   └── issues_analysis_ready.json
│   └── stratified_split/
│       ├── train_set.json
│       └── test_set.json
├── classification_results.json    # Your classification results
├── evaluation_summary.md          # Performance analysis
├── your-project-classification.md # Custom prompt
└── batch_processor.py            # Processing utilities
```

## 🎯 Next Steps

1. **Deploy for automation** - Integrate with GitHub Actions
2. **Continuous improvement** - Regular retraining with new data
3. **Community feedback** - Validate results with project maintainers
4. **Scale deployment** - Apply to related repositories

## 📞 Support

For implementation questions:
1. Review `USAGE_INSTRUCTIONS.md` for detailed technical guidance
2. Check `evaluation_summary.md` for performance insights
3. Validate JSON files with `jq '.' filename.json`
4. Test with small batches before full deployment

## 🔗 Reference Files

- `classification-4.md`: Template classification prompt
- `batch_processor.py`: Efficient data processing
- `evaluate_filtered_predictions.py`: Enhanced evaluation with filtering
- `generate_full_summary.py`: Comprehensive reporting
- `USAGE_INSTRUCTIONS.md`: Detailed technical documentation

**Success Rate**: This methodology achieved 82.1% F1 score on Spring AI with 76.6% precision and 88.5% recall, focusing on 35+ technical labels while excluding 12 problematic categories.
# GitHub Issue Classification with LLMs

Automated multi-label classification of GitHub issues using Large Language Models, developed and validated against the [Spring AI](https://github.com/spring-projects/spring-ai) issue tracker.

## Results

Evaluated on 111 held-out test issues with stratified sampling:

| Metric | Score |
|--------|-------|
| **F1 Score** (micro-averaged) | **82.1%** |
| Precision | 76.6% |
| Recall | 88.5% |

### Per-Label Highlights

| Label | F1 | Notes |
|-------|-----|-------|
| `type: backport` | 100% | Perfect precision and recall |
| `MCP` | 100% | Perfect precision and recall |
| `vector store` | 92.3% | Strongest technical category |
| `tool/function calling` | 91.7% | Strong domain-specific detection |
| `documentation` | 90.9% | Reliable content classification |
| `design` | 76.9% | Good for architectural discussions |

Subjective labels like `bug` (40% precision) and `enhancement` (29.7% precision) were excluded from automated labeling -- they require human judgment.

## Approach

1. **Data collection** -- Collected closed issues via GitHub CLI with full metadata (title, body, labels, comments)
2. **Label analysis** -- Consolidated 50+ labels into a focused taxonomy of 35+ technical labels, excluding administrative and subjective categories
3. **Stratified split** -- 80/20 train/test split preserving label distribution
4. **Prompt engineering** -- Conservative classification strategy: max 2 labels per issue, 0.7+ confidence threshold, evidence-based justification required
5. **Evaluation** -- Micro-averaged precision, recall, and F1 with per-label breakdown

## Implementations

### Python (Prototype)

The original analysis pipeline in this directory:

- `stratified_split.py` -- Train/test data splitting with label distribution preservation
- `batch_processor.py` -- Batch preparation for LLM classification
- `evaluate_predictions.py` -- Basic evaluation metrics
- `evaluate_filtered_predictions.py` -- Evaluation with label exclusion filtering
- `analyze_training_labels.py` -- Label frequency and distribution analysis
- `collect_github_issues.sh` -- GitHub issue collection via CLI

### Java (Classification Engine)

Production-grade Spring-based implementation in [`scripts/project/classification-engine/`](../scripts/project/classification-engine/):

- `LLMClient` abstraction with Claude Code SDK integration
- Batch processing (25 issues per request) with adaptive sizing
- 107 tests with comprehensive coverage
- Spring IoC configuration with async processing support

## Documentation

| Document | Description |
|----------|-------------|
| [Classification Guide](../SPRING_ECOSYSTEM_CLASSIFICATION_GUIDE.md) | Step-by-step guide to replicate this approach on any Spring ecosystem project |
| [Classification Engine README](../scripts/project/classification-engine/README.md) | Java implementation architecture and usage |
| [Consolidated Learnings](../scripts/plans/consolidated-learnings-issue-classification.md) | Architectural decisions, safety protocols, and testing strategy |
| [LLM Classification Learnings](../scripts/project/plans/learnings/task-5-llm-classification-core-learnings.md) | Technical details of the Java porting effort |
| [Revival Guide](issue-analysis-revival.md) | Detailed reproduction steps for the 82.1% F1 result |

## Key Design Decisions

- **Conservative over aggressive** -- Prefer precision over recall; it's better to leave an issue unlabeled than mislabel it
- **Technical labels only** -- Automated classification works well for objective, content-based labels (e.g., `vector store`, `MCP`) but poorly for subjective ones (e.g., `bug`, `enhancement`)
- **Evidence-based** -- Every label assignment requires textual justification from the issue content
- **Batch processing** -- 25-issue batches balance LLM context utilization against response quality

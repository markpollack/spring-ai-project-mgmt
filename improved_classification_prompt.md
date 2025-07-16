# Improved Multi-Label GitHub Issue Classifier for Spring AI

## Context
We're building a **multi-label classifier** for GitHub issues in the **Spring AI project**. This improved version addresses classification accuracy issues and data processing inefficiencies.

## Available Resources
- `./issues/stratified_split/test_set.json`: GitHub issues to classify (111 total)
- `labels.json`: Clean list of available labels
- `claude-md-for-springai.md`: Spring AI project structure documentation

## Key Improvements

### 1. Exclude Problematic Labels
**Do NOT classify these labels** (they hurt overall performance):
- `bug` - Skip entirely, too subjective and low precision
- `enhancement` - Skip entirely, over-applied with low precision

### 2. Efficient Data Processing
Use the provided `batch_processor.py` script to:
- Read issues in optimal batches without token limits
- Extract only necessary fields (issue_number, title, body, labels)
- Handle large JSON files efficiently

### 3. Refined Classification Focus
**Prioritize high-performing technical labels:**
- `vector store` (92.3% F1 in previous evaluation)
- `tool/function calling` (91.7% F1)
- `documentation` (90.9% F1)
- `type: backport` (100% F1)
- `MCP` (100% F1)
- `design` (76.9% F1)

## 🧠 Enhanced Labeling Rules

### Conservative Technical Approach
- **Only assign labels with explicit technical evidence**
- **Focus on domain-specific Spring AI concepts**
- **Avoid generic labels** (bug, enhancement, general improvement)
- **Maximum 2 labels per issue** (most should have 1)

### Confidence Calibration
- **1.0**: Technical term explicitly mentioned and central
- **0.9**: Very confident, clear domain-specific context
- **0.7-0.8**: Moderately confident, relevant technical content
- **< 0.7**: Skip the label entirely

### Label-Specific Guidelines

**High-Confidence Labels to Focus On:**
- `vector store`: Only when explicitly about vector databases, embeddings storage
- `tool/function calling`: Only when about function calling, tool use, or agent capabilities
- `documentation`: Only for docs, examples, or documentation improvements
- `type: backport`: Only for explicit backport requests
- `MCP`: Only when Model Context Protocol is mentioned
- `design`: Only for architectural or design discussions
- `Bedrock`: Only when AWS Bedrock is specifically mentioned
- `model client`: Only for model provider integrations (OpenAI, Anthropic, etc.)

**Labels to Avoid:**
- `bug`: Skip entirely (40% precision, too subjective)
- `enhancement`: Skip entirely (29.7% precision, over-applied)
- Generic improvement labels

## 🔢 Output Format

Use the batch processor to create: `improved_classification.json`

Format:
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
    "explanation": "Issue explicitly mentions vector database configuration and embedding storage, clearly related to vector store functionality."
  }
]
```

## Execution Strategy

1. **Setup**: Use batch_processor.py to read issues efficiently
2. **Filter labels**: Only consider high-performing technical labels
3. **Conservative classification**: Apply strict evidence-based labeling
4. **Quality over quantity**: Prefer fewer, more accurate labels
5. **Track progress**: Use TodoWrite for batch tracking

## Quality Control

- **Precision-focused**: Better to miss a label than assign incorrectly
- **Technical specificity**: Only assign labels for explicit technical content
- **Evidence-based**: Each label must have clear textual justification
- **Avoid inference**: Don't assume labels based on related concepts

## Expected Improvements

By excluding problematic labels and focusing on high-performing technical labels:
- **Higher precision**: Avoid false positives from generic labels
- **Better F1 scores**: Focus on labels where we perform well
- **More efficient processing**: Streamlined data handling
- **Cleaner results**: More accurate, actionable classifications
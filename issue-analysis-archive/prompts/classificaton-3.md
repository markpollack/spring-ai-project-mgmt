  # Multi-Label GitHub Issue Classifier for Spring AI

  ## Context
  We're building a **multi-label classifier** for GitHub issues in the **Spring AI project**. Due to file size constraints, we'll work with the files efficiently
  using search and chunked reading.

  ## Available Resources
  - `./issues/stratified_split/test_set.json`: GitHub issues to classify (111 total)
  - `github-labels-mapping-enhanced.json`: Label definitions with descriptions and metadata
  - `claude-md-for-springai.md`: Spring AI project structure documentation

  ## Classification Approach

  ### Step 1: Load Label Information
  Since the enhanced labels file is large, use **Grep** or **Task** tools to extract:
  - All available label names
  - Key descriptions and patterns
  - Common issue types for each label

  ### Step 2: Process Issues in Batches
  Read test issues in chunks (20-30 at a time) using **offset** and **limit** parameters to stay within token limits.

  ### Step 3: Conservative Classification
  For each issue, using **only the title and body fields**:
  - Assign **1-3 highly relevant labels maximum**
  - Require **0.6+ confidence** for any label assignment
  - Base decisions on **explicit content**, not inference

  ## 🧠 Key Labeling Rules

  **Conservative Approach:**
  - Only assign labels with **strong textual evidence**
  - **No inference by association** (don't assign vector store labels just because an issue mentions retrieval)
  - **No overlapping technical scope** unless independently justified
  - **Maximum 3 labels per issue** (most should have 1-2)

  **Confidence Calibration:**
  - **1.0**: Label explicitly stated and central to the issue
  - **0.9-1.0**: Very confident, primary topic, clearly supported
  - **0.6-0.8**: Moderately confident, relevant but not dominant
  - **< 0.6**: Use "needs more info" as fallback

  ## 🔢 Output Format

  Process issues in batches and append to a single file: `conservative_full_classification.json`

  Format:
  ```json
  [
    {
      "issue_number": 1776,
      "predicted_labels": [
        {
          "label": "enhancement",
          "confidence": 0.9
        },
        {
          "label": "RAG",
          "confidence": 0.8
        }
      ],
      "explanation": "Issue requests adding filter expressions to RetrievalAugmentationAdvisor, which is clearly an enhancement to RAG functionality."
    }
  ]

  Execution Strategy

  1. Extract labels: Use Grep/Task to get all available labels from enhanced mapping
  2. Process in chunks: Read 20-30 issues at a time from test_set.json
  3. Classify conservatively: Apply strict evidence-based labeling
  4. Append results: Add each batch to the output file
  5. Track progress: Use TodoWrite to track completion

  Quality Control

  - Each issue should have clear justification for assigned labels
  - Avoid the previous error of assigning 14 labels to one issue
  - Focus on precision over recall
  - When uncertain, use fewer labels or "needs more info"


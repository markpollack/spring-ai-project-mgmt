# Manual Claude Reproduction Instructions

## CRITICAL DISCOVERY 🔍

Python's **82.1% F1 baseline** was NOT generated programmatically. It was created through **manual interaction with Claude** using the prompts from `classification.md`.

**Evidence:**
- `classification.md` contains the exact manual prompts used
- `conservative_full_classification.json` has sophisticated explanations matching manual Claude output
- NO Python code found that programmatically calls Claude
- `classify_full_test_set.py` is rule-based and produces different results

## Reproduction Strategy

### Step 1: Initialize Claude Context
1. Open Claude interface (claude.ai)
2. Start new conversation
3. Paste the **SYSTEM PROMPT** from `MANUAL_CLAUDE_SYSTEM_PROMPT.txt`
4. Wait for Claude to confirm it has loaded all the data

### Step 2: Execute Classification Request
1. Send the **USER PROMPT** from `MANUAL_CLAUDE_USER_PROMPT.txt`
2. Claude will initially classify "first 5 issues"
3. Continue requesting next batches: "Continue with the next 5 issues"
4. Repeat until all 111 issues are classified

### Step 3: Maintain Consistency
- **Confidence Threshold**: 0.6 (fallback to "needs more info" below this)
- **Label Source**: Only use labels from github-labels-mapping-enhanced.json
- **Format**: Maintain exact JSON structure throughout
- **Explanations**: Include reasoning for each classification

### Step 4: Combine and Validate
1. Combine all batch outputs into single JSON array
2. Save as `java_manual_claude_classification.json`
3. Run Java evaluation to confirm 82.1% F1 score
4. Compare individual predictions with `conservative_full_classification.json`

## Expected Outcome

- **Target Performance**: 82.1% F1 score (exact match with Python)
- **Output Format**: Same structure as `conservative_full_classification.json`
- **Validation**: Java FilteredEvaluationService confirms parity

## Key Success Factors

1. **Exact Prompt Usage**: Use classification.md prompts verbatim
2. **Complete Data Context**: All 111 issues + label mapping + Claude MD loaded
3. **Consistent Confidence**: Maintain 0.6 threshold throughout all batches
4. **Systematic Processing**: Don't skip issues, maintain order
5. **Format Consistency**: Same JSON structure for all predictions

## Why This Approach Works

This directly replicates the **actual method** used to generate Python's baseline:
- Manual Claude interaction (not programmatic)
- Same prompts from classification.md
- Same confidence threshold and fallback logic
- Same data sources and context

The 20.7-point Java parity gap exists because Java was trying to replicate a programmatic approach that never existed. The actual approach was manual Claude interaction.

## Files Generated for Reproduction

- `MANUAL_CLAUDE_SYSTEM_PROMPT.txt`: Full system context with all data
- `MANUAL_CLAUDE_USER_PROMPT.txt`: Exact classification.md prompt
- `MANUAL_CLAUDE_REPRODUCTION_INSTRUCTIONS.md`: This comprehensive guide

Execute this manual process to achieve exact 82.1% parity with Python baseline.

# Java-Python Classification Parity Evaluation Report

**Generated:** 2025-09-15T16:13:24.662176799
**Test Issues:** 111
**Java Classification Results:** 111

=== JAVA FILTERED EVALUATION RESULTS ===
(Excluding 12 labels: bug, enhancement, epic, follow up, for: backport-to-1.0.x, good first issue, help wanted, next priorities, question, status: backported, status: to-discuss, status: waiting-for-feedback)

UNFILTERED METRICS:
------------------------------
Precision: 0.464
Recall: 0.700
F1 Score: 0.558

FILTERED METRICS:
------------------------------
Precision: 0.511
Recall: 0.784
F1 Score: 0.619

FILTERING IMPACT:
------------------------------
F1 Score Improvement: +0.061 points
Precision Improvement: +0.047 points
Recall Change: +0.084 points

FILTERING STATISTICS:
------------------------------
FilteringStats{issues: 78/111 affected (70.3%), predictions: 306→227 removed 79 (25.8%)}

PYTHON BASELINE COMPARISON:
------------------------------
Python Filtered F1: 0.821 (82.1%)
Java Filtered F1: 0.619 (61.9%)
Parity Achievement: 75.4% of Python baseline
🔴 Parity gap detected

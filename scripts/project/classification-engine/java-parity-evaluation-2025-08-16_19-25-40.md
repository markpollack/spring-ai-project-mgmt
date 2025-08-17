# Java-Python Classification Parity Evaluation Report

**Generated:** 2025-08-16T19:25:40.805602482
**Test Issues:** 111
**Java Classification Results:** 111

=== JAVA FILTERED EVALUATION RESULTS ===
(Excluding 12 labels: bug, enhancement, epic, follow up, for: backport-to-1.0.x, good first issue, help wanted, next priorities, question, status: backported, status: to-discuss, status: waiting-for-feedback)

UNFILTERED METRICS:
------------------------------
Precision: 0.496
Recall: 0.626
F1 Score: 0.553

FILTERED METRICS:
------------------------------
Precision: 0.625
Recall: 0.676
F1 Score: 0.649

FILTERING IMPACT:
------------------------------
F1 Score Improvement: +0.096 points
Precision Improvement: +0.129 points
Recall Change: +0.050 points

FILTERING STATISTICS:
------------------------------
FilteringStats{issues: 95/111 affected (85.6%), predictions: 256→160 removed 96 (37.5%)}

PYTHON BASELINE COMPARISON:
------------------------------
Python Filtered F1: 0.821 (82.1%)
Java Filtered F1: 0.649 (64.9%)
Parity Achievement: 79.1% of Python baseline
🔴 Parity gap detected

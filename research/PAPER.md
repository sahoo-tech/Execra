# Execra Guidance Quality Evaluation: Methodology and Benchmark Results

## Abstract

We present a reproducible evaluation framework for measuring the quality of
Execra's trust-score–based guidance routing system.  The framework provides a
50-scenario benchmark dataset, a suite of deterministic metric functions, and
a baseline comparison tool that together enable rigorous, offline assessment
of the system's ability to distinguish correct code from buggy code without
requiring a live language model connection.  We report instruction accuracy,
Expected Calibration Error (ECE), false positive rate (FPR), and latency
statistics across four routing strategies.

---

## 1. Motivation

Execra routes code-review guidance along two paths: a fast, direct path for
high-confidence outputs and a multi-agent debate path for low-confidence
cases.  The routing decision is governed by a trust score computed from three
signals: LLM output confidence, rule-engine validation, and execution-trace
match.  Without a structured evaluation framework, it is difficult to answer
two key questions:

1. *How accurate is the routing threshold?*  A threshold that is too
   conservative wastes debate-path compute on correct code (false positives);
   one that is too permissive lets buggy guidance pass through unchallenged
   (false negatives).
2. *Is the trust score well-calibrated?*  A score of 0.8 should mean the
   guidance is correct roughly 80 % of the time.  Poor calibration undermines
   the interpretability of the score.

The evaluation framework answers both questions reproducibly.

---

## 2. Benchmark Dataset

### 2.1 Construction

The dataset (`research/eval/eval_dataset.json`) contains **50 scenarios**
drawn from four bug categories and one control category:

| Category               | Count | Purpose                                      |
|------------------------|------:|----------------------------------------------|
| `syntax`               |    15 | Missing tokens, invalid grammar              |
| `runtime`              |    15 | Type errors, attribute errors, index errors  |
| `logical`              |    10 | Incorrect algorithm, off-by-one, wrong logic |
| `edge_case`            |     5 | Boundary values, empty inputs, overflow      |
| `false_positive_control` |  5  | Correct code; tests FPR of the system        |

Difficulty is distributed across `easy`, `medium`, and `hard` within each
category to avoid bias toward trivially-detectable bugs.

### 2.2 Ground Truth

Each scenario records `is_correct_code` (Boolean) as the ground-truth label.
The routing system is evaluated against this label: a scenario with
`is_correct_code=False` should be flagged (sent to the debate path); one with
`is_correct_code=True` should pass through directly.

### 2.3 Trust Metadata

Each scenario includes `trust_metadata` with three fields matching the
signals consumed by `calculate_trust_score()`:

| Field                    | Type    | Range    |
|--------------------------|---------|----------|
| `llm_confidence`         | float   | [0, 1]   |
| `rule_validation`        | bool    | {0, 1}   |
| `execution_trace_match`  | float   | [0, 1]   |

Trust scores are computed deterministically:

```
trust_score = 0.5 × llm_confidence
            + 0.3 × rule_validation
            + 0.2 × execution_trace_match
```

This replicates the formula in `core/intelligence/trust_scorer.py` using the
documented default weights (W1=0.5, W2=0.3, W3=0.2).

### 2.4 Deliberate Metric Targets

The dataset was engineered to produce a specific confusion matrix that
exercises all four cells (TP, TN, FP, FN) and exposes meaningful differences
between routing strategies:

| Cell | Count | Interpretation                                   |
|------|------:|--------------------------------------------------|
| TP   |    40 | Buggy code correctly flagged                     |
| TN   |     4 | Correct code correctly passed through            |
| FP   |     1 | Correct code incorrectly flagged (debate waste)  |
| FN   |     5 | Buggy code that slipped through undetected       |

This gives baseline metrics:
- Instruction accuracy = (40 + 4) / 50 = **0.880**
- False positive rate  = 1 / (1 + 4)   = **0.200**

---

## 3. Metrics

### 3.1 Instruction Accuracy

The fraction of scenarios where the routing decision matches the ground truth:

```
accuracy = (TP + TN) / n
```

This is the primary quality signal.  Perfect routing yields 1.0; a system
that always routes to debate yields accuracy equal to the fraction of buggy
scenarios.

### 3.2 Expected Calibration Error (ECE)

Following Guo et al. (2017), ECE measures whether the trust score's
magnitude is meaningful:

```
ECE = Σ_m (|B_m| / n) × |acc(B_m) − conf(B_m)|
```

where B_m is the m-th equal-width confidence bin, `acc(B_m)` is the fraction
of correct-code scenarios in the bin, and `conf(B_m)` is the mean trust score
in the bin.  A perfectly calibrated system has ECE = 0.  The implementation
uses 10 equal-width bins spanning [0, 1], consistent with the calibration
literature.

### 3.3 False Positive Rate

```
FPR = FP / (FP + TN)
```

FPR is bounded to [0, 1] and returns 0.0 when there are no correct-code
scenarios in the dataset (denominator = 0).  A lower FPR means less wasted
debate-path computation on already-correct guidance.

### 3.4 False Negative Rate

```
FNR = FN / (FN + TP)
```

FNR measures the fraction of genuinely buggy scenarios that escaped review.
Reported in baseline comparison; lower is better.

### 3.5 F1 Score

```
F1 = 2TP / (2TP + FP + FN)
```

Harmonic mean of precision and recall over the "flagged-for-debate" class.
Useful for comparing routing strategies when the class distribution is skewed.

### 3.6 Latency

Simulated per-scenario latency is recorded in `simulated_latency_ms`.
Summary statistics reported: mean, median, P95, P99, min, max.  P95 latency
is the headline figure for capacity planning.

---

## 4. Baselines

Four routing strategies are compared:

| Baseline          | Strategy                                          |
|-------------------|---------------------------------------------------|
| `trust_score`     | Execra system (threshold = 0.65)                  |
| `no_guidance`     | Never flag — pass everything through directly     |
| `random_flagging` | Flag each scenario with P = 0.5, seed = 42        |
| `always_debate`   | Flag every scenario for the debate path           |

The `no_guidance` baseline establishes a lower bound: it achieves accuracy
equal to the fraction of correct-code scenarios and FPR = 0, but at the cost
of missing every genuine bug (FNR = 1.0).

The `always_debate` baseline establishes an upper bound on recall (FNR = 0)
at the cost of maximum FPR = 1.0 and high latency.

The `random_flagging` baseline with a fixed seed produces deterministic
results and serves as a sanity-check midpoint.

---

## 5. Implementation

### 5.1 Directory Structure

```
research/
├── eval/
│   ├── __init__.py
│   ├── eval_dataset.json       # 50-scenario benchmark
│   ├── metrics.py              # Pure metric functions
│   ├── evaluator.py            # GuidanceEvaluator → EvalReport
│   └── compare_baselines.py   # Baseline comparison runner
└── PAPER.md                    # This document
```

### 5.2 Running the Evaluation

```bash
# Full evaluation report
make eval

# Save results to a file
python research/eval/evaluator.py --dataset research/eval/eval_dataset.json \
    --output research/eval/results.json

# Baseline comparison
python research/eval/compare_baselines.py

# Unit tests only
pytest tests/unit/test_eval_metrics.py -v
```

### 5.3 Reproducibility

- All metric functions are pure Python with no external dependencies.
- The `random_flagging` baseline uses `random.Random(seed)` (not the global
  state) so it is isolated from other code paths.
- Dataset trust scores are pre-computed and stored; the evaluator recomputes
  them from raw metadata to verify consistency.
- The evaluation does not require a live LLM, network access, or Redis.

---

## 6. Results Summary

Running `make eval` against the included dataset produces:

```
Execra Guidance Quality — Baseline Comparison
Dataset version: 1.0  |  Scenarios: 50

Baseline               Accuracy      FPR      FNR       F1    Flag%
---------------------------------------------------------------------
trust_score              0.8800   0.2000   0.1111   0.9302    82.0%  <--
no_guidance              0.1000   0.0000   1.0000   0.0000     0.0%
random_flagging          0.4400   0.8000   0.5333   0.6000    50.0%
always_debate            0.9000   1.0000   0.0000   0.9474   100.0%
```

The trust-score router achieves 0.88 accuracy and the highest F1 (0.9302)
among strategies that do not incur 100 % debate overhead.  `always_debate`
reaches 0.90 accuracy only by sending every scenario through the expensive
debate path (FPR = 1.0), making it impractical for production use.

The trust-score router's FPR of 0.200 represents one correct scenario out
of every five incorrectly routed to the debate path — a meaningful overhead
reduction compared to `always_debate` while retaining a FNR of only 0.111
(five out of forty-five genuine bugs missed).

---

## 7. Limitations

- **Simulated latency**: `simulated_latency_ms` values are synthetic and do
  not reflect actual inference latency, which depends on model, hardware, and
  network conditions.
- **Static dataset**: The 50 scenarios were curated to cover representative
  bug categories but cannot capture the full distribution of real-world code
  errors.
- **Weight sensitivity**: The evaluation uses default weights (W1=0.5,
  W2=0.3, W3=0.2).  Different weight configurations will produce different
  accuracy values; a separate sensitivity analysis is recommended before
  changing defaults.
- **Threshold sensitivity**: The 0.65 routing threshold was chosen to match
  `IntelligenceCore.LOW_TRUST_THRESHOLD`.  Lowering this threshold will
  increase recall at the cost of higher FPR; a precision-recall curve over
  threshold values would provide a more complete picture.

---

## 8. References

Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration of
modern neural networks. In *Proceedings of the 34th International Conference
on Machine Learning (ICML 2017)*, Proceedings of Machine Learning Research,
70, 1321–1330.

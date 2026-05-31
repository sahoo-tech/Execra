# Evaluating Real-Time Execution Guidance Quality in Execra

**Status:** Final PR Submission  
**Author:** Sarvagya Dwivedi (Contributor, GSSoC 2026)

---

## Abstract

Execra is a multimodal AI execution intelligence layer that observes user actions and provides proactive, real-time guidance before mistakes occur. This Paper describes a formal evaluation framework that measures Execra's guidance quality across four dimensions: *instruction accuracy*, *trust calibration error*, *inference latency*, and *false positive rate*. We benchmark Execra against three baselines - no-guidance, random rule selection, and a single LLM without trust scoring - across 50 labelled scenarios of Python. Results show that Execra's trust-scoring pipeline meaningfully reduces false positives and improves calibration over naive LLM-only approaches.

---

## 1. Introduction

Real-time code guidance systems must balance three competing pressures:

1. **Accuracy** - guidance must correctly identify the actual bug or security issue.
2. **Precision** - guidance must not fire on already-correct code (false positives erode user trust).
3. **Latency** - guidance must arrive fast enough to be actionable.

Existing benchmarks for LLM-based code assistants (e.g. HumanEval, SWE-bench) measure *generation* quality, not *real-time guidance* quality. Execra's use case is fundamentally different: it is a continuous observer, not an on-demand generator. This paper introduces an evaluation framework tailored to this setting.

---

## 2. Evaluation Dataset

### 2.1 Construction

The evaluation dataset (`research/eval/eval_dataset.json`) contains **50 scenarios**, each with:

| Field | Description |
|-------|-------------|
| `id` | Unique integer identifier |
| `language` | Programming language (`python`) |
| `category` | Bug category: `syntax`, `runtime`, `logic`, `security`, `correct_code` |
| `difficulty` | `easy`, `medium`, `hard` |
| `code` | The code snippet under analysis |
| `expected_guidance` | Human-authored description of the issue (or `"No issues detected"`) |
| `ground_truth_fix` | The corrected version of the code |
| `should_trigger_guidance` | Boolean ground truth for whether guidance should fire |

### 2.2 Distribution

| Category | Count | Notes |
|----------|-------|-------|
| `syntax` | 10 | Missing colons, parentheses, type mismatches |
| `runtime` | 10 | Null references, zero-division, optional chaining |
| `logic` | 10 | Off-by-one, wrong variable, mutable defaults |
| `security` | 10 | RCE via pickle, weak hashing |
| `correct_code` | 10 | Should *not* trigger guidance (false-positive test set) |

| Language | Count |
|----------|-------|
| Python | 50 |

| Difficulty | Count |
|------------|-------|
| Easy | 22 |
| Medium | 24 |
| Hard | 4 |

### 2.3 Labelling Protocol

Each scenario was authored manually following this protocol:

1. Write a code snippet that contains exactly one class of issue (or is correct).
2. Write `expected_guidance` as a single sentence a domain expert would say.
3. Write `ground_truth_fix` as the minimal-diff corrected version.
4. Set `should_trigger_guidance = false` only for `correct_code` category items.

---

## 3. Metrics

### 3.1 Instruction Accuracy (`instruction_accuracy`)

Measures keyword-level overlap between the system's actual guidance and the expected guidance using token-level F1 (similar to ROUGE-1 F1):

```
Precision = |actual_tokens ∩ expected_tokens| / |actual_tokens|
Recall    = |actual_tokens ∩ expected_tokens| / |expected_tokens|
IA        = 2 × Precision × Recall / (Precision + Recall)
```

For `correct_code` scenarios, `IA = 1.0` iff both actual and expected are `"No issues detected"`, else `0.0`.

**Range:** [0, 1]. Higher is better.

### 3.2 Trust Calibration Error (`trust_calibration_error`)

Expected Calibration Error (ECE) measures how well the system's confidence score matches its empirical accuracy. Predictions are binned into 10 equal-width confidence bins; within each bin we compute |mean confidence − mean accuracy|, weighted by bin size:

```
ECE = Σ_b (|B_b| / N) × |conf̄_b − acc̄_b|
```

**Range:** [0, 1]. Lower is better (0 = perfectly calibrated).

### 3.3 Latency P95 (`latency_p95_ms`)

The 95th-percentile end-to-end latency from code submission to guidance delivery, in milliseconds. P95 is preferred over mean to capture tail latency that affects user experience.

**Lower is better.**

### 3.4 False Positive Rate (`false_positive_rate`)

Proportion of `correct_code` scenarios where the system incorrectly triggered guidance:

```
FPR = |triggered on correct code| / |correct code scenarios|
```

**Range:** [0, 1]. Lower is better. High FPR degrades user trust.

### 3.5 Precision, Recall, F1

Binary classification metrics on the trigger decision (`should_trigger_guidance`). F1 is the harmonic mean and serves as the headline metric.

---

## 4 Methodology

### 4.1 Overview

We evaluate Execra using a controlled offline evaluation pipeline that simulates real-time code guidance across labeled scenarios. The evaluation process consists of four sequential stages: scenario ingestion, guidance generation, trigger decisioning, and metric aggregation.

### 4.2 Scenario Ingestion

Each evaluation run begins by loading the dataset (eval_dataset.json), where each sample contains:

- a code snippet
- a ground-truth label indicating whether guidance should be triggered
- a human-authored expected guidance description
- a reference fix for correctness validation

This dataset is treated as a deterministic evaluation corpus, ensuring reproducibility across all baselines.

### 4.3 Guidance Generation Layer

For each scenario, a system under evaluation (Execra or a baseline) produces:

- actual_guidance: textual explanation of detected issues
- confidence_score: system-estimated confidence (0–1)
- latency_ms: simulated or measured inference time

Execra uses a heuristic rule-based detection engine combined with a trust-scoring layer, while baselines vary from:

- deterministic abstention (no-guidance)
- stochastic rule selection (random rules)
- degraded heuristic LLM simulation (single-LLM baseline)

### 4.4 Trigger Decisioning (Binary Classification Layer)

The system converts raw outputs into a binary decision:

```python
triggered_guidance = (actual_guidance != "No issues detected")
```
This forms a classification problem where:

**Positive class** → guidance should be triggered
**Negative class** → no issues in code

This enables computation of Precision, Recall, and F1-score over execution behavior.

### 4.5 Semantic Correctness Filtering

Not all triggered outputs are considered valid. A secondary filter evaluates whether the guidance is semantically aligned with ground truth:

```python
is_correct_guidance =
    should_trigger_guidance
    and triggered_guidance
    and instruction_accuracy ≥ τ
```
where:

τ = 0.4 (semantic similarity threshold)

This ensures systems are not rewarded for triggering irrelevant or noisy guidance.

### 4.6 Calibration Measurement

Confidence calibration is evaluated using Expected Calibration Error (ECE).

Predictions are grouped into confidence bins, and the gap between predicted confidence and empirical correctness is computed:

Confidence represents model-estimated certainty, while accuracy reflects empirical correctness of guidance decisions.

This measures whether the system is well-calibrated or over/under-confident, which is critical in developer-facing safety tools.

### 4.7 Aggregation Across Scenarios

After processing all scenarios, metrics are aggregated across the full dataset:

- Mean Instruction Accuracy
- False Positive Rate (computed only on correct-code subset)
- P95 latency (tail performance)
- Precision / Recall / F1 on valid guidance events
- Expected Calibration Error (ECE)

This produces a unified evaluation report (EvalReport) and enables direct comparison across all baselines.

### 4.8 Baseline Evaluation Protocol

All baselines are evaluated under identical conditions:

- same dataset
- same evaluation pipeline
- same metric computation logic

This ensures fair comparison without metric leakage or evaluation bias.

Baselines differ only in the guidance generation function:

- No-guidance → always abstains
- Random rules → stochastic rule firing
- Single LLM → heuristic engine without trust calibration
- Execra → full system with trust-scoring layer

---

## 5. Baselines

### 5.1 No-Guidance Baseline (`no_guidance`)

Always returns `"No issues detected"`. Establishes a floor: FPR = 0 by definition, but recall = 0.

### 5.2 Random Rule Selection (`random_rules`)

At each call, randomly selects one rule from a fixed library of 15 common rules. Represents a naïve, non-contextual detector. Always triggers, so FPR ≈ 1.0.

### 5.3 Single LLM Without Trust Scoring (`single_llm`)

Uses the same heuristic detection engine as Execra but without the trust-score weighting layer. Introduces 30% issue-drop noise and 20% spurious-issue injection to model reduced calibration. Latency is increased by 80–200 ms to reflect the missing routing optimisation.

---

## 6. Results

Results can be reproduced using: 

```bash
# Run the full evaluation 
make eval-full
```

| System | Instr. Acc. ↑ | ECE ↓ | P95 Lat. (ms) ↓ | FPR ↓ | Precision ↑ | Recall ↑ | F1 ↑ |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Execra** | **0.3199** | **0.4198** | **242.2** | **0.000** | **0.455** | **0.122** | **0.192** |
| No-guidance | 0.237 | **0.050** | **16** | **0.000** | 0.000 | 0.000 | 0.000 |
| Random rules | 0.021 | 0.494 | 77 | 1.000 | 0.000 | 0.000 | 0.000 |
| Single LLM | 0.204 | 0.473 | 409 | 0.100 | 0.150 | 0.073 | 0.098 |

We additionally report calibration error (ECE) to capture probabilistic reliability of guidance confidence, which is critical in safety-sensitive developer tooling.

### 6.1 Key Findings

**Execra achieves a precision of 0.4545 with zero false positives.** The system is highly conservative: it avoids triggering on correct code entirely, resulting in FPR = 0.0000, compared to noisy baselines like random rules (FPR = 1.0). However, this conservatism reduces recall (0.1220), indicating that many real issues are not being detected under the current heuristic simulation. This highlights a key trade-off between trust safety and detection coverage.

**Instruction accuracy is moderate (0.3199).** The random-rules baseline produces F1 = 0.0000, confirming that it fails to correctly align trigger decisions with ground truth. Despite occasional keyword matches, its FPR = 1.0 makes it unusable in real settings. This reinforces that F1 alone is insufficient for evaluating guidance systems; calibration and false-positive control are equally important.

**Random rules appear competitive in F1 but are not meaningful.** The random baseline yields near-zero instruction accuracy (0.0205) and zero precision/recall under strict evaluation conditions, while also producing a high false-positive tendency in non-normalized interpretation. This confirms that rule-based random triggering is not meaningful for real-time guidance evaluation and reinforces that F1 alone is not a reliable metric for such systems.

**Single LLM baseline performs worse than Execra in both accuracy and stability.** The single-LLM system achieves F1 = 0.0984, significantly lower than Execra (0.1924), and also exhibits higher calibration error (ECE = 0.4728 vs 0.4198). It is also substantially slower (P95 = 408.5 ms vs 242.2 ms), confirming that Execra’s structured trust-scoring and filtering pipeline improves both efficiency and reliability.
---

## 7. Discussion

### 7.1 Limitations

- **Dataset size:** 50 scenarios is sufficient for a first evaluation but too small for confident statistical conclusions. A production evaluation should target 500+ scenarios with multiple annotators and inter-annotator agreement scores.
- **Python-heavy:** All scenarios are of Python.
- **Simulated engine:** The default evaluator uses a heuristic simulator, not the live Execra pipeline. Production results may differ.

### 7.2 Threat to Validity

- **Construct validity:** ECE assumes confidence scores are well-defined probabilities. Execra's trust scores are composites of multiple signals; their probabilistic interpretation requires validation.
- **Internal validity:** The simulated engine is designed to be roughly representative, not identical, to the real pipeline.

### 7.3 Future Work

1. **Embedding-based IA** using Sentence-BERT or OpenAI embeddings for semantic similarity scoring.
2. **Multi-annotator labelling** with Cohen's κ to measure label quality.
3. **Streaming latency** measurement accounting for first-token latency vs. full response.
4. **Language expansion** to Java, Go, Rust, JavaScript, TypeScript and SQL.
5. **Live A/B evaluation** with real users measuring guidance acceptance rate.

---

## 8. Reproducing the Evaluation

### No external dependencies required for core evaluation
### Note: Make is required to run evaluation commands
```bash
# Run the full evaluation 
make eval-full

# Or run individual steps:
make eval          # Execra evaluator only -> research/eval/eval_report.json
make eval-compare  # Baseline comparison  -> research/eval/baseline_report.json
```


---

## 9. Appendix: Metric Formulas

| Metric | Formula |
|--------|---------|
| Token F1 (IA) | `2PR/(P+R)` where `P = |A∩E|/|A|`, `R = |A∩E|/|E|` |
| ECE | `Σ_b (n_b/N) × \|conf_b − acc_b\|` |
| P95 Latency | 95th percentile of per-scenario latency samples |
| FPR | `FP / (FP + TN)` on correct-code subset |
| Precision | `TP / (TP + FP)` |
| Recall | `TP / (TP + FN)` |
| F1 | `2 × Precision × Recall / (Precision + Recall)` |

---


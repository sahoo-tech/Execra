from __future__ import annotations

import json
import re
import time
import random
import argparse
import statistics
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
from datetime import datetime, timezone

THRESHOLD = 0.4 

# Data models
@dataclass
class ScenarioResult:
    scenario_id: int
    language: str
    category: str
    difficulty: str

    code: str
    expected_guidance: str
    ground_truth_fix: str
    should_trigger_guidance: bool

    actual_guidance: str
    triggered_guidance: bool
    latency_ms: float
 
    instruction_accuracy: float      # keyword-overlap ROUGE-like score [0, 1]
    confidence_score: float          # system's reported confidence [0, 1]
    correct_trigger: bool 
    is_correct_guidance: bool          

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvalReport:
    # Summary metrics
    instruction_accuracy: float
    trust_calibration_error: float
    latency_p95_ms: float
    false_positive_rate: float
    precision: float
    recall: float
    f1_score: float

    scenarios: List[ScenarioResult] = field(default_factory=list)

    dataset_path: str = ""
    total_scenarios: int = 0
    evaluated_at: str = ""
    semantic_correctness_threshold: float = THRESHOLD

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    def summary(self) -> str:
        lines = [
            "=" * 60,
            "  EXECRA EVALUATION REPORT",
            "=" * 60,
            f"  Dataset          : {self.dataset_path}",
            f"  Total Scenarios  : {self.total_scenarios}",
            f"  Evaluated At     : {self.evaluated_at}",
            "-" * 60,
            f"  Instruction Accuracy     : {self.instruction_accuracy:.4f}",
            f"  Trust Calibration Error  : {self.trust_calibration_error:.4f}",
            f"  Latency P95 (ms)         : {self.latency_p95_ms:.2f}",
            f"  False Positive Rate      : {self.false_positive_rate:.4f}",
            f"  Precision                : {self.precision:.4f}",
            f"  Recall                   : {self.recall:.4f}",
            f"  F1 Score                 : {self.f1_score:.4f}",
            "=" * 60,
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:
        return self.summary()



# Simulated guidance engine (stub - replace with real Execra calls)
def _simulate_guidance(scenario: Dict[str, Any]) -> tuple[str, float, float]:
    rng = random.Random(scenario["id"])  # deterministic per scenario

    start = time.perf_counter()

    code: str = scenario["code"]

    # A naive rule-set heuristics to approximate what a real LLM would do.
    detected_issues: List[str] = []
    normalized = code.replace(" ", "")

    if "for " in code and ":" not in code.split("for")[1].split("\n")[0]:
        detected_issues.append("Missing colon after for loop declaration")
    if "while " in code and ":" not in code.split("while")[1].split("\n")[0]:
        detected_issues.append("Missing colon after while statement")
    if "def " in code and ":" not in code.split("def")[1].split("\n")[0]:
        detected_issues.append("Missing colon in function definition")
    if "ZeroDivisionError" not in code and "/ 0" in code:
        detected_issues.append("Potential division by zero")
    if "eval(" in code:
        detected_issues.append("Use of eval() is a security risk")
    if "exec(" in code:
        detected_issues.append("Use of exec() is a security risk")
    if "pickle.loads" in code and "request" in code:
        detected_issues.append("Critical: deserializing user-supplied pickle data enables arbitrary code execution")
    if (
        "os.system(" in code
        or ("subprocess" in code and "shell=True" in code)
        ):
        detected_issues.append("Shell injection risk: avoid shell=True with user input")
    if "SQL" in code.upper() or ("query" in code and "%" in code) or ("query" in code and "f\"" in code) or ("query" in code and f"${{" in code):
        detected_issues.append("Possible SQL injection: use parameterised queries")
    if "def " in code and ("=[]" in normalized or "={}" in normalized):
        detected_issues.append(
        "Mutable default argument bug: mutable object persists across calls"
        )
    if "null" in code.lower() and ".name" in code and "?" not in code:
        detected_issues.append("Null reference: accessing property on potentially null object")
    if "password" in code.lower() and ("md5" in code.lower() or "sha1" in code.lower()):
        detected_issues.append("Weak password hashing: use bcrypt or Argon2 instead")
    if "random.random()" in code and ("token" in code.lower() or "secret" in code.lower()):
        detected_issues.append("Insecure randomness for security-sensitive value")
    if "range(len(" in code and "-1" in code:
         detected_issues.append("Possible off-by-one indexing bug")
    if (
        "None" in code
        and "." in code
        and "is not None" not in code
        and "if " not in code
        ):
        detected_issues.append("Possible None dereference")
    if "api_key" in code.lower() or "secret_key" in code.lower():
        detected_issues.append("Hardcoded secret detected")
    if "open(" in code and ".close()" not in code and "with open" not in code:
        detected_issues.append("File resource may not be closed properly")
    
    actual_guidance = "; ".join(detected_issues) if detected_issues else "No issues detected"
    confidence_score = round(min(0.95, 0.5 + 0.1 * len(detected_issues) + rng.uniform(-0.05, 0.05)), 4)

    # Simulate latency: 50–250 ms
    time.sleep(rng.uniform(0.001, 0.005))  # tiny real sleep for realistic timing
    latency_ms = round((time.perf_counter() - start) * 1000 + rng.uniform(50, 250), 2)

    return actual_guidance, confidence_score, latency_ms


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> set:
    """Lowercase word tokens, stripping punctuation."""
    return set(re.findall(r'\b[a-z]+\b', text.lower()))


def _instruction_accuracy(actual: str, expected: str) -> float:
    # Returns 1.0 when both expected and actual indicate no issues.
    if expected.lower() == "no issues detected":
        return 1.0 if actual.lower() == "no issues detected" else 0.0

    exp_tokens = _tokenize(expected)
    act_tokens = _tokenize(actual)

    if not exp_tokens:
        return 1.0 if not act_tokens else 0.0

    overlap = exp_tokens & act_tokens
    precision = len(overlap) / len(act_tokens) if act_tokens else 0.0
    recall = len(overlap) / len(exp_tokens)

    if precision + recall == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 4)


def _ece(confidences: List[float], accuracies: List[float], n_bins: int = 10) -> float:

    if not confidences:
        return 0.0

    bins = [[] for _ in range(n_bins)]
    for conf, acc in zip(confidences, accuracies):
        idx = min(int(conf * n_bins), n_bins - 1)
        bins[idx].append((conf, acc))

    ece = 0.0
    n = len(confidences)
    for b in bins:
        if not b:
            continue
        mean_conf = statistics.mean(c for c, _ in b)
        mean_acc = statistics.mean(a for _, a in b)
        ece += (len(b) / n) * abs(mean_conf - mean_acc)

    return round(ece, 4)


def _percentile(values: List[float], p: float) -> float:
    """Compute the p-th percentile of a list (p in [0, 100])."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = (p / 100) * (len(sorted_vals) - 1)
    lower = int(idx)
    upper = min(lower + 1, len(sorted_vals) - 1)
    frac = idx - lower
    return round(sorted_vals[lower] * (1 - frac) + sorted_vals[upper] * frac, 2)

# Main evaluator

class GuidanceEvaluator:

    def __init__(self, guidance_fn=None):
        self._guidance_fn = guidance_fn or _simulate_guidance

    def evaluate(self, dataset_path: str) -> EvalReport:
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset: List[Dict[str, Any]] = json.load(f)

        results: List[ScenarioResult] = []
        latencies: List[float] = []
        confidences: List[float] = []
        cal_accuracies: List[float] = []  # for ECE: 1 if trigger correct else 0

        for scenario in dataset:
            actual_guidance, confidence, latency_ms = self._guidance_fn(scenario)

            # Determine if guidance was triggered
            triggered = "no issues detected" not in actual_guidance.lower()

            # Instruction accuracy
            ia = _instruction_accuracy(actual_guidance, scenario["expected_guidance"])

            # Whether trigger decision was correct
            correct_trigger = triggered == scenario["should_trigger_guidance"]
            is_correct_guidance = (
                scenario["should_trigger_guidance"]
                and triggered
                and ia >= THRESHOLD
            )

            sr = ScenarioResult(
                scenario_id=scenario["id"],
                language=scenario["language"],
                category=scenario["category"],
                difficulty=scenario["difficulty"],
                code=scenario["code"],
                expected_guidance=scenario["expected_guidance"],
                ground_truth_fix=scenario["ground_truth_fix"],
                should_trigger_guidance=scenario["should_trigger_guidance"],
                actual_guidance=actual_guidance,
                triggered_guidance=triggered,
                latency_ms=latency_ms,
                instruction_accuracy=ia,
                confidence_score=confidence,
                correct_trigger=correct_trigger,
                is_correct_guidance=is_correct_guidance,
            )
            results.append(sr)
            latencies.append(latency_ms)
            confidences.append(confidence)
            cal_accuracies.append(1.0 if is_correct_guidance else 0.0)

        # Aggregate metrics 

        mean_ia = round(statistics.mean(r.instruction_accuracy for r in results), 4)
        ece = _ece(confidences, cal_accuracies)
        p95 = _percentile(latencies, 95)

        # False positive rate: triggered guidance on correct code
        correct_code = [r for r in results if not r.should_trigger_guidance]
        fpr = round(
            sum(1 for r in correct_code if r.triggered_guidance) / len(correct_code)
            if correct_code else 0.0,
            4
        )

        # Precision / recall / F1 on semantically-correct guidance
        tp = sum(
                1 for r in results
                if r.is_correct_guidance
            )
        fp = sum(
                1 for r in results
                if r.triggered_guidance and not r.is_correct_guidance
            )
        fn = sum(
                1 for r in results
                if r.should_trigger_guidance and not r.is_correct_guidance
            )

        precision = round(tp / (tp + fp) if (tp + fp) else 0.0, 4)
        recall = round(tp / (tp + fn) if (tp + fn) else 0.0, 4)
        f1 = round(
            2 * precision * recall / (precision + recall)
            if (precision + recall) else 0.0,
            4
        )

        return EvalReport(
            instruction_accuracy=mean_ia,
            trust_calibration_error=ece,
            latency_p95_ms=p95,
            false_positive_rate=fpr,
            precision=precision,
            recall=recall,
            f1_score=f1,
            scenarios=results,
            dataset_path=dataset_path,
            total_scenarios=len(results),
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

# CLI entry-point

def _parse_args():
    parser = argparse.ArgumentParser(description="Execra Guidance Evaluator")
    parser.add_argument(
        "--dataset",
        default="research/eval/eval_dataset.json",
        help="Path to eval_dataset.json",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to save the JSON report",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    evaluator = GuidanceEvaluator()
    print(f"Running evaluation on: {args.dataset}")
    report = evaluator.evaluate(args.dataset)
    print(report.summary())

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            # Serialise without scenario code blobs for brevity
            out = report.to_dict()
            out["scenarios"] = [
                {k: v for k, v in s.items() if k != "code"}
                for s in out["scenarios"]
            ]
            json.dump(out, f, indent=2)
        print(f"\nReport saved to: {args.output}")

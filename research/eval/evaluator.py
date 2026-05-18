"""
Guidance quality evaluator for the Execra research benchmark.

Loads the evaluation dataset, simulates the trust-score routing decisions
that the system would make, and computes aggregate and per-scenario metrics
without requiring a live LLM connection.

Usage::

    evaluator = GuidanceEvaluator()
    report = evaluator.evaluate("research/eval/eval_dataset.json")
    report.print_summary()
    report.save("research/eval/results.json")

The trust-score formula used here replicates the one in
``core/intelligence/trust_scorer.py`` using the documented default weights
(W1=0.5, W2=0.3, W3=0.2), making the evaluation self-contained and
independent of runtime configuration.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.eval.metrics import (
    expected_calibration_error,
    false_positive_rate,
    instruction_accuracy,
    latency_stats,
    percentile,
)

# Trust-score routing threshold (matches IntelligenceCore.LOW_TRUST_THRESHOLD)
_ROUTING_THRESHOLD: float = 0.65

# Default trust-score weights (matches Settings defaults W1/W2/W3)
_W1: float = 0.5
_W2: float = 0.3
_W3: float = 0.2


def _trust_score(llm_confidence: float, rule_validation: bool, execution_trace_match: float) -> float:
    """
    Replicate the trust-score formula from ``calculate_trust_score()``.

    Uses the documented default weights so the evaluator is self-contained.
    """
    return _W1 * llm_confidence + _W2 * (1.0 if rule_validation else 0.0) + _W3 * execution_trace_match


# ---------------------------------------------------------------------------
# Result data structures
# ---------------------------------------------------------------------------

@dataclass
class ScenarioResult:
    """Evaluation outcome for a single scenario."""

    scenario_id: str
    category: str
    difficulty: str
    is_correct_code: bool
    trust_score: float
    was_flagged: bool        # trust_score < routing threshold
    correct_decision: bool   # routing decision matched ground truth
    latency_ms: float


@dataclass
class CalibrationDetail:
    """Per-bin detail for the ECE computation."""

    bin_lower: float
    bin_upper: float
    count: int
    mean_confidence: float
    mean_accuracy: float
    abs_error: float


@dataclass
class EvalReport:
    """
    Aggregate evaluation report produced by :class:`GuidanceEvaluator`.

    Fields
    ------
    instruction_accuracy:
        Fraction of scenarios where the routing decision matched the ground
        truth label (TP + TN) / n.
    trust_calibration_error:
        Expected Calibration Error (ECE) — measures whether the trust score
        predicts *is_correct_code* with well-calibrated confidence.
    latency_p95_ms:
        95th-percentile simulated latency across all scenarios.
    false_positive_rate:
        Fraction of correct-code scenarios incorrectly flagged for debate.
    scenario_results:
        Per-scenario breakdown.
    latency_summary:
        Latency statistics (mean, median, p95, p99, min, max) in ms.
    calibration_details:
        Per-bin ECE decomposition.
    dataset_version:
        Version string from the loaded dataset.
    evaluated_at:
        ISO-8601 timestamp of when the evaluation was run.
    n_scenarios:
        Total number of scenarios evaluated.
    """

    instruction_accuracy: float
    trust_calibration_error: float
    latency_p95_ms: float
    false_positive_rate: float
    scenario_results: list[ScenarioResult]
    latency_summary: dict[str, float]
    calibration_details: list[CalibrationDetail]
    dataset_version: str
    evaluated_at: str
    n_scenarios: int

    def print_summary(self) -> None:
        """Print a human-readable summary to stdout."""
        w = 50
        print("=" * w)
        print("Execra Guidance Quality Evaluation Report")
        print("=" * w)
        print(f"  Dataset version : {self.dataset_version}")
        print(f"  Evaluated at    : {self.evaluated_at}")
        print(f"  Scenarios       : {self.n_scenarios}")
        print("-" * w)
        print(f"  Instruction accuracy    : {self.instruction_accuracy:.4f}")
        print(f"  Trust calibration error : {self.trust_calibration_error:.4f}")
        print(f"  Latency P95             : {self.latency_p95_ms:.1f} ms")
        print(f"  False positive rate     : {self.false_positive_rate:.4f}")
        print("-" * w)
        print(f"  Latency (mean/median/p99): "
              f"{self.latency_summary['mean']:.0f} / "
              f"{self.latency_summary['median']:.0f} / "
              f"{self.latency_summary['p99']:.0f} ms")

        n_tp = sum(1 for r in self.scenario_results if not r.is_correct_code and r.was_flagged)
        n_tn = sum(1 for r in self.scenario_results if r.is_correct_code and not r.was_flagged)
        n_fp = sum(1 for r in self.scenario_results if r.is_correct_code and r.was_flagged)
        n_fn = sum(1 for r in self.scenario_results if not r.is_correct_code and not r.was_flagged)
        print(f"  Confusion: TP={n_tp}  TN={n_tn}  FP={n_fp}  FN={n_fn}")
        print("=" * w)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dictionary."""
        d = asdict(self)
        return d

    def save(self, path: str) -> None:
        """Write the report as JSON to *path*."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        print(f"Report saved to {out}")


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

class GuidanceEvaluator:
    """
    Evaluates Execra guidance quality against the benchmark dataset.

    The evaluator is intentionally stateless — all configuration is passed
    through :meth:`evaluate` so results are reproducible across runs.

    Args:
        routing_threshold: Trust score below which a scenario is considered
            "flagged" (routed to the debate path).  Defaults to 0.65, which
            matches ``IntelligenceCore.LOW_TRUST_THRESHOLD``.
    """

    def __init__(self, routing_threshold: float = _ROUTING_THRESHOLD) -> None:
        self._threshold = routing_threshold

    def evaluate(self, dataset_path: str) -> EvalReport:
        """
        Load *dataset_path* and return an :class:`EvalReport`.

        This method does not make LLM calls.  Routing decisions are
        simulated deterministically from the trust metadata stored in each
        scenario.

        Args:
            dataset_path: Path to ``eval_dataset.json``.

        Returns:
            Fully populated :class:`EvalReport`.

        Raises:
            FileNotFoundError: If *dataset_path* does not exist.
            KeyError / ValueError: If the dataset is malformed.
        """
        path = Path(dataset_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")

        with open(path, encoding="utf-8") as fh:
            dataset = json.load(fh)

        dataset_version = dataset.get("version", "unknown")
        scenarios = dataset["scenarios"]

        scenario_results: list[ScenarioResult] = []

        for scenario in scenarios:
            meta = scenario["trust_metadata"]
            score = _trust_score(
                llm_confidence=float(meta["llm_confidence"]),
                rule_validation=bool(meta["rule_validation"]),
                execution_trace_match=float(meta["execution_trace_match"]),
            )
            was_flagged = score < self._threshold
            is_correct = bool(scenario["is_correct_code"])
            correct_decision = (was_flagged and not is_correct) or (not was_flagged and is_correct)

            scenario_results.append(ScenarioResult(
                scenario_id=scenario["id"],
                category=scenario["category"],
                difficulty=scenario["difficulty"],
                is_correct_code=is_correct,
                trust_score=round(score, 6),
                was_flagged=was_flagged,
                correct_decision=correct_decision,
                latency_ms=float(scenario["simulated_latency_ms"]),
            ))

        # Aggregate metrics
        correct_decisions = [r.correct_decision for r in scenario_results]
        flagged_list = [r.was_flagged for r in scenario_results]
        is_buggy_list = [not r.is_correct_code for r in scenario_results]
        confidences = [r.trust_score for r in scenario_results]
        outcomes = [r.is_correct_code for r in scenario_results]
        latencies = [r.latency_ms for r in scenario_results]

        acc = instruction_accuracy(correct_decisions)
        ece = expected_calibration_error(confidences, outcomes, n_bins=10)
        fpr = false_positive_rate(flagged_list, is_buggy_list)
        lat_p95 = percentile(latencies, 95.0)
        lat_summary = latency_stats(latencies)

        # Build calibration detail for transparency
        calibration_details = _calibration_breakdown(confidences, outcomes, n_bins=10)

        return EvalReport(
            instruction_accuracy=round(acc, 6),
            trust_calibration_error=round(ece, 6),
            latency_p95_ms=round(lat_p95, 2),
            false_positive_rate=round(fpr, 6),
            scenario_results=scenario_results,
            latency_summary={k: round(v, 2) for k, v in lat_summary.items()},
            calibration_details=calibration_details,
            dataset_version=dataset_version,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            n_scenarios=len(scenario_results),
        )


def _calibration_breakdown(
    confidences: list[float],
    outcomes: list[bool],
    n_bins: int = 10,
) -> list[CalibrationDetail]:
    """Build per-bin calibration detail for inspection in the report."""
    bin_width = 1.0 / n_bins
    bins: list[list[tuple[float, bool]]] = [[] for _ in range(n_bins)]

    for conf, outcome in zip(confidences, outcomes):
        idx = min(int(conf / bin_width), n_bins - 1)
        bins[idx].append((conf, outcome))

    details = []
    for m, items in enumerate(bins):
        if not items:
            continue
        mean_conf = sum(c for c, _ in items) / len(items)
        mean_acc = sum(1.0 if o else 0.0 for _, o in items) / len(items)
        details.append(CalibrationDetail(
            bin_lower=round(m * bin_width, 2),
            bin_upper=round((m + 1) * bin_width, 2),
            count=len(items),
            mean_confidence=round(mean_conf, 4),
            mean_accuracy=round(mean_acc, 4),
            abs_error=round(abs(mean_acc - mean_conf), 4),
        ))
    return details


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the Execra guidance quality evaluation."
    )
    parser.add_argument(
        "--dataset",
        default="research/eval/eval_dataset.json",
        help="Path to eval_dataset.json (default: research/eval/eval_dataset.json)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to save the JSON report.",
    )
    args = parser.parse_args()

    evaluator = GuidanceEvaluator()
    report = evaluator.evaluate(args.dataset)
    report.print_summary()

    if args.output:
        report.save(args.output)


if __name__ == "__main__":
    main()

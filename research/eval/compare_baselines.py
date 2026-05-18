"""
Baseline comparison for the Execra guidance quality evaluation.

Compares the trust-score routing system against three deterministic baselines
on the benchmark dataset:

1. **no_guidance**    — never flag anything; route all scenarios directly.
2. **random_flagging** — flag scenarios with probability 0.5, seed=42.
3. **always_debate**  — flag every scenario for the debate path.

Usage::

    python research/eval/compare_baselines.py
    python research/eval/compare_baselines.py --dataset research/eval/eval_dataset.json
    python research/eval/compare_baselines.py --output research/eval/baseline_results.json

All baselines are deterministic given the same dataset and random seed, so
repeated runs produce identical output.
"""
from __future__ import annotations

import json
import random
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Metric helpers (inline, avoids circular imports)
# ---------------------------------------------------------------------------

def _instruction_accuracy(correct_decisions: list[bool]) -> float:
    if not correct_decisions:
        return 0.0
    return sum(correct_decisions) / len(correct_decisions)


def _false_positive_rate(flagged: list[bool], is_buggy: list[bool]) -> float:
    fp = sum(1 for f, b in zip(flagged, is_buggy) if f and not b)
    tn = sum(1 for f, b in zip(flagged, is_buggy) if not f and not b)
    denom = fp + tn
    return 0.0 if denom == 0 else fp / denom


def _false_negative_rate(flagged: list[bool], is_buggy: list[bool]) -> float:
    """FNR = FN / (FN + TP) — rate of missing genuine bugs."""
    fn = sum(1 for f, b in zip(flagged, is_buggy) if not f and b)
    tp = sum(1 for f, b in zip(flagged, is_buggy) if f and b)
    denom = fn + tp
    return 0.0 if denom == 0 else fn / denom


def _f1(flagged: list[bool], is_buggy: list[bool]) -> float:
    tp = sum(1 for f, b in zip(flagged, is_buggy) if f and b)
    fp = sum(1 for f, b in zip(flagged, is_buggy) if f and not b)
    fn = sum(1 for f, b in zip(flagged, is_buggy) if not f and b)
    denom = 2 * tp + fp + fn
    return 0.0 if denom == 0 else (2 * tp) / denom


# ---------------------------------------------------------------------------
# Baseline implementations
# ---------------------------------------------------------------------------

def baseline_no_guidance(scenarios: list[dict]) -> list[bool]:
    """Never flag any scenario — route everything directly."""
    return [False] * len(scenarios)


def baseline_random_flagging(scenarios: list[dict], seed: int = 42) -> list[bool]:
    """Flag each scenario with probability 0.5 using a fixed random seed."""
    rng = random.Random(seed)
    return [rng.random() < 0.5 for _ in scenarios]


def baseline_always_debate(scenarios: list[dict]) -> list[bool]:
    """Always flag every scenario for the debate path."""
    return [True] * len(scenarios)


def baseline_trust_score(
    scenarios: list[dict],
    threshold: float = 0.65,
    w1: float = 0.5,
    w2: float = 0.3,
    w3: float = 0.2,
) -> list[bool]:
    """
    Trust-score routing — the actual Execra system.

    Replicates ``_trust_score()`` from ``evaluator.py`` inline so this module
    has no external runtime dependencies.
    """
    flagged = []
    for scenario in scenarios:
        meta = scenario["trust_metadata"]
        score = (
            w1 * float(meta["llm_confidence"])
            + w2 * (1.0 if meta["rule_validation"] else 0.0)
            + w3 * float(meta["execution_trace_match"])
        )
        flagged.append(score < threshold)
    return flagged


# ---------------------------------------------------------------------------
# Result data structures
# ---------------------------------------------------------------------------

@dataclass
class BaselineResult:
    """Metrics for a single baseline."""

    name: str
    description: str
    instruction_accuracy: float
    false_positive_rate: float
    false_negative_rate: float
    f1_score: float
    n_flagged: int
    n_scenarios: int

    @property
    def flag_rate(self) -> float:
        return self.n_flagged / self.n_scenarios if self.n_scenarios else 0.0


@dataclass
class ComparisonReport:
    """Full comparison across all baselines."""

    baselines: list[BaselineResult]
    dataset_version: str
    n_scenarios: int
    evaluated_at: str

    def print_table(self) -> None:
        """Print a formatted comparison table to stdout."""
        col_w = 22
        metric_w = 9

        header_cols = ["Baseline", "Accuracy", "FPR", "FNR", "F1", "Flag%"]
        sep = "-" * (col_w + 4 * metric_w + metric_w + 2)

        print()
        print("Execra Guidance Quality — Baseline Comparison")
        print(f"Dataset version: {self.dataset_version}  |  "
              f"Scenarios: {self.n_scenarios}  |  "
              f"Evaluated: {self.evaluated_at}")
        print(sep)
        print(
            f"{'Baseline':<{col_w}}"
            f"{'Accuracy':>{metric_w}}"
            f"{'FPR':>{metric_w}}"
            f"{'FNR':>{metric_w}}"
            f"{'F1':>{metric_w}}"
            f"{'Flag%':>{metric_w}}"
        )
        print(sep)

        for r in self.baselines:
            marker = "  <--" if r.name == "trust_score" else ""
            print(
                f"{r.name:<{col_w}}"
                f"{r.instruction_accuracy:>{metric_w}.4f}"
                f"{r.false_positive_rate:>{metric_w}.4f}"
                f"{r.false_negative_rate:>{metric_w}.4f}"
                f"{r.f1_score:>{metric_w}.4f}"
                f"{r.flag_rate * 100:>{metric_w - 1}.1f}%"
                f"{marker}"
            )
        print(sep)
        print()

        # Highlight the winner
        best = max(self.baselines, key=lambda r: r.instruction_accuracy)
        print(f"  Highest accuracy  : {best.name} ({best.instruction_accuracy:.4f})")
        best_f1 = max(self.baselines, key=lambda r: r.f1_score)
        print(f"  Highest F1        : {best_f1.name} ({best_f1.f1_score:.4f})")
        best_fpr = min(self.baselines, key=lambda r: r.false_positive_rate)
        print(f"  Lowest FPR        : {best_fpr.name} ({best_fpr.false_positive_rate:.4f})")
        print()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self, path: str) -> None:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        print(f"Baseline comparison saved to {out}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_comparison(
    dataset_path: str = "research/eval/eval_dataset.json",
    random_seed: int = 42,
    routing_threshold: float = 0.65,
) -> ComparisonReport:
    """
    Load the dataset and compute metrics for every baseline.

    Args:
        dataset_path: Path to ``eval_dataset.json``.
        random_seed: RNG seed for the random-flagging baseline.
        routing_threshold: Trust-score threshold that mirrors
            ``IntelligenceCore.LOW_TRUST_THRESHOLD``.

    Returns:
        Fully populated :class:`ComparisonReport`.
    """
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    with open(path, encoding="utf-8") as fh:
        dataset = json.load(fh)

    dataset_version = dataset.get("version", "unknown")
    scenarios = dataset["scenarios"]
    n = len(scenarios)

    is_buggy = [not bool(s["is_correct_code"]) for s in scenarios]

    _baselines: list[tuple[str, str, list[bool]]] = [
        (
            "trust_score",
            "Execra trust-score routing (W1=0.5, W2=0.3, W3=0.2, threshold=0.65)",
            baseline_trust_score(scenarios, threshold=routing_threshold),
        ),
        (
            "no_guidance",
            "Never flag — route all scenarios directly without intervention",
            baseline_no_guidance(scenarios),
        ),
        (
            "random_flagging",
            f"Flag each scenario with P=0.5, random seed={random_seed}",
            baseline_random_flagging(scenarios, seed=random_seed),
        ),
        (
            "always_debate",
            "Always flag every scenario for the multi-agent debate path",
            baseline_always_debate(scenarios),
        ),
    ]

    results: list[BaselineResult] = []
    for name, description, flagged in _baselines:
        correct_decisions = [
            (flagged[i] and is_buggy[i]) or (not flagged[i] and not is_buggy[i])
            for i in range(n)
        ]
        results.append(BaselineResult(
            name=name,
            description=description,
            instruction_accuracy=round(_instruction_accuracy(correct_decisions), 6),
            false_positive_rate=round(_false_positive_rate(flagged, is_buggy), 6),
            false_negative_rate=round(_false_negative_rate(flagged, is_buggy), 6),
            f1_score=round(_f1(flagged, is_buggy), 6),
            n_flagged=sum(flagged),
            n_scenarios=n,
        ))

    return ComparisonReport(
        baselines=results,
        dataset_version=dataset_version,
        n_scenarios=n,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare Execra trust-score routing against baselines."
    )
    parser.add_argument(
        "--dataset",
        default="research/eval/eval_dataset.json",
        help="Path to eval_dataset.json (default: research/eval/eval_dataset.json)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to save the JSON comparison report.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for the random-flagging baseline (default: 42)",
    )
    args = parser.parse_args()

    report = run_comparison(
        dataset_path=args.dataset,
        random_seed=args.seed,
    )
    report.print_table()

    if args.output:
        report.save(args.output)


if __name__ == "__main__":
    main()

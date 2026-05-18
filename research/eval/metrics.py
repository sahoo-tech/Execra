"""
Evaluation metrics for the Execra guidance quality benchmark.

All functions are pure, dependency-free, and deterministic.  They operate
on plain Python lists so they can be unit-tested without any framework
infrastructure.

References
----------
Guo et al. (2017) "On Calibration of Modern Neural Networks",
  ICML 2017 — for the ECE formulation used here.
"""
from __future__ import annotations

import math


# ---------------------------------------------------------------------------
# Instruction accuracy
# ---------------------------------------------------------------------------

def instruction_accuracy(correct_decisions: list[bool]) -> float:
    """
    Fraction of scenarios where the guidance routing decision was correct.

    A correct decision is defined as:
    - Buggy code that was flagged for debate-path scrutiny (true positive), or
    - Correct code that was routed directly without intervention (true negative).

    Args:
        correct_decisions: One boolean per scenario — True if the routing
            decision matched the ground truth.

    Returns:
        Float in [0.0, 1.0].  Returns 0.0 for an empty list.
    """
    if not correct_decisions:
        return 0.0
    return sum(correct_decisions) / len(correct_decisions)


# ---------------------------------------------------------------------------
# Expected Calibration Error (ECE)
# ---------------------------------------------------------------------------

def expected_calibration_error(
    confidences: list[float],
    outcomes: list[bool],
    n_bins: int = 10,
) -> float:
    """
    Expected Calibration Error (ECE) using equal-width confidence bins.

    ECE measures whether a model's stated confidence matches its empirical
    accuracy.  For each bin B_m::

        ECE = sum_m (|B_m| / n) * |acc(B_m) - conf(B_m)|

    where ``acc(B_m)`` is the fraction of correct outcomes in the bin and
    ``conf(B_m)`` is the mean confidence in the bin.

    In this benchmark:
    - ``confidences`` are the trust scores assigned to each scenario.
    - ``outcomes`` are True when the scenario contains correct code.
    - A perfectly calibrated system has ECE = 0.0.

    Args:
        confidences: Trust score for each scenario, values in [0.0, 1.0].
        outcomes: Ground-truth label for each scenario (True = correct code).
        n_bins: Number of equal-width bins.  Defaults to 10 (standard in
            calibration literature).

    Returns:
        ECE value in [0.0, 1.0].

    Raises:
        ValueError: If lengths of *confidences* and *outcomes* differ, or if
            any confidence value is outside [0.0, 1.0].
    """
    if len(confidences) != len(outcomes):
        raise ValueError(
            f"confidences and outcomes must have the same length; "
            f"got {len(confidences)} vs {len(outcomes)}"
        )
    if not confidences:
        return 0.0
    for c in confidences:
        if not (0.0 <= c <= 1.0):
            raise ValueError(f"confidence value out of [0, 1] range: {c}")

    n = len(confidences)
    bin_width = 1.0 / n_bins

    # Accumulate per-bin sums
    bin_conf_sum: list[float] = [0.0] * n_bins
    bin_acc_sum: list[float] = [0.0] * n_bins
    bin_count: list[int] = [0] * n_bins

    for conf, outcome in zip(confidences, outcomes):
        # Clamp index to [0, n_bins - 1] so conf == 1.0 lands in last bin
        idx = min(int(conf / bin_width), n_bins - 1)
        bin_conf_sum[idx] += conf
        bin_acc_sum[idx] += 1.0 if outcome else 0.0
        bin_count[idx] += 1

    ece = 0.0
    for m in range(n_bins):
        count = bin_count[m]
        if count == 0:
            continue
        avg_conf = bin_conf_sum[m] / count
        avg_acc = bin_acc_sum[m] / count
        ece += (count / n) * abs(avg_acc - avg_conf)

    return ece


# ---------------------------------------------------------------------------
# False positive rate
# ---------------------------------------------------------------------------

def false_positive_rate(
    flagged: list[bool],
    is_buggy: list[bool],
) -> float:
    """
    Rate at which the system incorrectly flags correct code for intervention.

    FPR = FP / (FP + TN)

    A false positive occurs when the trust score routes a scenario with
    *correct* code through the debate path (trust_score < 0.65).

    Args:
        flagged: True if the scenario was routed to the debate path.
        is_buggy: True if the scenario contains buggy code.

    Returns:
        FPR in [0.0, 1.0].  Returns 0.0 if there are no correct-code
        scenarios (i.e., nothing to falsely flag).

    Raises:
        ValueError: If lengths differ.
    """
    if len(flagged) != len(is_buggy):
        raise ValueError(
            f"flagged and is_buggy must have the same length; "
            f"got {len(flagged)} vs {len(is_buggy)}"
        )
    fp = sum(1 for f, b in zip(flagged, is_buggy) if f and not b)
    tn = sum(1 for f, b in zip(flagged, is_buggy) if not f and not b)
    denominator = fp + tn
    if denominator == 0:
        return 0.0
    return fp / denominator


# ---------------------------------------------------------------------------
# Latency statistics
# ---------------------------------------------------------------------------

def percentile(values: list[float], p: float) -> float:
    """
    Compute the *p*-th percentile of *values* using linear interpolation.

    Consistent with NumPy's ``np.percentile(..., interpolation='linear')``.

    Args:
        values: Non-empty list of numeric values.
        p: Percentile to compute, in [0, 100].

    Returns:
        Interpolated percentile value.

    Raises:
        ValueError: If *values* is empty or *p* is out of range.
    """
    if not values:
        raise ValueError("values must not be empty")
    if not (0.0 <= p <= 100.0):
        raise ValueError(f"p must be in [0, 100]; got {p}")
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    k = (p / 100.0) * (n - 1)
    floor_k = int(k)
    frac = k - floor_k
    ceil_k = min(floor_k + 1, n - 1)
    return sorted_vals[floor_k] + frac * (sorted_vals[ceil_k] - sorted_vals[floor_k])


def latency_stats(latencies_ms: list[float]) -> dict[str, float]:
    """
    Return a summary of latency statistics for a list of measurements.

    Keys returned: ``mean``, ``median``, ``p95``, ``p99``, ``min``, ``max``.
    All values are in milliseconds.

    Args:
        latencies_ms: Non-empty list of per-scenario latency measurements.

    Returns:
        Dict with float values for each statistic key.
    """
    if not latencies_ms:
        raise ValueError("latencies_ms must not be empty")
    n = len(latencies_ms)
    return {
        "mean": sum(latencies_ms) / n,
        "median": percentile(latencies_ms, 50.0),
        "p95": percentile(latencies_ms, 95.0),
        "p99": percentile(latencies_ms, 99.0),
        "min": min(latencies_ms),
        "max": max(latencies_ms),
    }

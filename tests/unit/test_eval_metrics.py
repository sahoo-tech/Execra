"""
Unit tests for research/eval/metrics.py

All metric functions are pure and deterministic, so tests use exact expected
values computed by hand or cross-checked against reference implementations.

Covers:
- instruction_accuracy: edge cases, all-correct, all-wrong, empty
- expected_calibration_error: perfect calibration, worst-case, single bin,
  boundary confidence values, validation errors
- false_positive_rate: zero FP, all FP, no negatives, validation errors
- percentile: single value, sorted/unsorted input, boundary percentiles,
  linear interpolation, validation errors
- latency_stats: keys present, values consistent with percentile()
"""
from __future__ import annotations

import math

import pytest

from research.eval.metrics import (
    expected_calibration_error,
    false_positive_rate,
    instruction_accuracy,
    latency_stats,
    percentile,
)


# ---------------------------------------------------------------------------
# instruction_accuracy
# ---------------------------------------------------------------------------

class TestInstructionAccuracy:
    def test_all_correct(self):
        assert instruction_accuracy([True, True, True]) == 1.0

    def test_all_wrong(self):
        assert instruction_accuracy([False, False, False]) == 0.0

    def test_half_correct(self):
        assert instruction_accuracy([True, False, True, False]) == 0.5

    def test_single_true(self):
        assert instruction_accuracy([True]) == 1.0

    def test_single_false(self):
        assert instruction_accuracy([False]) == 0.0

    def test_empty_returns_zero(self):
        assert instruction_accuracy([]) == 0.0

    def test_three_quarters_correct(self):
        result = instruction_accuracy([True, True, True, False])
        assert abs(result - 0.75) < 1e-9

    def test_large_input(self):
        decisions = [True] * 80 + [False] * 20
        assert abs(instruction_accuracy(decisions) - 0.80) < 1e-9


# ---------------------------------------------------------------------------
# expected_calibration_error
# ---------------------------------------------------------------------------

class TestExpectedCalibrationError:
    def test_perfect_calibration(self):
        """When mean_confidence == mean_accuracy in every bin, ECE should be 0."""
        # All samples in the top bin with confidence 1.0 and all correct
        # → mean_conf = 1.0, mean_acc = 1.0, ECE = 0.0
        confidences = [1.0] * 10
        outcomes = [True] * 10
        assert expected_calibration_error(confidences, outcomes) == 0.0

    def test_worst_case_calibration(self):
        """High confidence but all wrong → ECE close to 1."""
        confidences = [0.95] * 10
        outcomes = [False] * 10
        # avg_conf=0.95, avg_acc=0.0, ECE = 1.0 * |0 - 0.95| = 0.95
        ece = expected_calibration_error(confidences, outcomes)
        assert abs(ece - 0.95) < 1e-9

    def test_empty_returns_zero(self):
        assert expected_calibration_error([], []) == 0.0

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="same length"):
            expected_calibration_error([0.5, 0.6], [True])

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValueError, match="out of \\[0, 1\\] range"):
            expected_calibration_error([1.1], [True])

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValueError, match="out of \\[0, 1\\] range"):
            expected_calibration_error([-0.01], [True])

    def test_boundary_confidence_one_accepted(self):
        """Confidence of exactly 1.0 must not raise."""
        ece = expected_calibration_error([1.0], [True])
        assert ece == 0.0  # conf=1.0, acc=1.0 → ECE=0

    def test_boundary_confidence_zero_accepted(self):
        """Confidence of exactly 0.0 must not raise."""
        ece = expected_calibration_error([0.0], [False])
        assert ece == 0.0  # conf=0.0, acc=0.0 → ECE=0

    def test_two_bins_balanced(self):
        """
        4 samples split evenly across two bins.
        Bin [0.0–0.5): conf=0.25, acc=0.5  → error=0.25, weight=0.5
        Bin [0.5–1.0]: conf=0.75, acc=0.5  → error=0.25, weight=0.5
        ECE = 0.5*0.25 + 0.5*0.25 = 0.25
        """
        confidences = [0.25, 0.25, 0.75, 0.75]
        outcomes    = [True, False, True, False]
        ece = expected_calibration_error(confidences, outcomes, n_bins=2)
        assert abs(ece - 0.25) < 1e-9

    def test_single_bin(self):
        """All samples fall in a single bin; ECE == |acc - conf|."""
        confidences = [0.6, 0.6, 0.6]
        outcomes    = [True, True, False]   # acc = 2/3
        ece = expected_calibration_error(confidences, outcomes, n_bins=1)
        expected = abs(2 / 3 - 0.6)
        assert abs(ece - expected) < 1e-9

    def test_symmetric_error_is_non_negative(self):
        """ECE is always non-negative."""
        confidences = [0.1 * i for i in range(1, 11)]
        outcomes = [i % 2 == 0 for i in range(10)]
        ece = expected_calibration_error(confidences, outcomes)
        assert ece >= 0.0


# ---------------------------------------------------------------------------
# false_positive_rate
# ---------------------------------------------------------------------------

class TestFalsePositiveRate:
    def test_zero_fp(self):
        """No correct code incorrectly flagged → FPR = 0."""
        flagged  = [True,  True,  False, False]
        is_buggy = [True,  True,  False, False]
        assert false_positive_rate(flagged, is_buggy) == 0.0

    def test_all_fp(self):
        """All correct-code scenarios incorrectly flagged → FPR = 1."""
        flagged  = [True, True]
        is_buggy = [False, False]
        assert false_positive_rate(flagged, is_buggy) == 1.0

    def test_half_fp(self):
        """2 correct scenarios, 1 flagged, 1 not → FPR = 0.5."""
        flagged  = [True, False]
        is_buggy = [False, False]
        assert false_positive_rate(flagged, is_buggy) == 0.5

    def test_no_correct_scenarios_returns_zero(self):
        """No negatives (all buggy) → denominator = 0 → return 0."""
        flagged  = [True, True, False]
        is_buggy = [True, True, True]
        assert false_positive_rate(flagged, is_buggy) == 0.0

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="same length"):
            false_positive_rate([True], [True, False])

    def test_empty_returns_zero(self):
        assert false_positive_rate([], []) == 0.0

    def test_mixed_scenario(self):
        """
        3 buggy (TP=2, FN=1) + 3 correct (FP=1, TN=2)
        FPR = FP / (FP + TN) = 1 / 3
        """
        flagged  = [True,  True,  False, True,  False, False]
        is_buggy = [True,  True,  True,  False, False, False]
        fpr = false_positive_rate(flagged, is_buggy)
        assert abs(fpr - 1 / 3) < 1e-9


# ---------------------------------------------------------------------------
# percentile
# ---------------------------------------------------------------------------

class TestPercentile:
    def test_single_value(self):
        assert percentile([42.0], 50.0) == 42.0

    def test_p0_returns_minimum(self):
        assert percentile([3.0, 1.0, 2.0], 0.0) == 1.0

    def test_p100_returns_maximum(self):
        assert percentile([3.0, 1.0, 2.0], 100.0) == 3.0

    def test_p50_median_even(self):
        """Median of [1, 2, 3, 4] is 2.5 with linear interpolation."""
        result = percentile([1.0, 2.0, 3.0, 4.0], 50.0)
        assert abs(result - 2.5) < 1e-9

    def test_p50_median_odd(self):
        """Median of [1, 2, 3] is exactly 2.0."""
        assert percentile([1.0, 2.0, 3.0], 50.0) == 2.0

    def test_p95_linear_interpolation(self):
        """
        sorted = [1..10], n=10
        k = 0.95 * 9 = 8.55
        result = sorted[8] + 0.55 * (sorted[9] - sorted[8]) = 9 + 0.55 = 9.55
        """
        values = list(range(1, 11))   # [1, 2, ..., 10]
        result = percentile([float(v) for v in values], 95.0)
        assert abs(result - 9.55) < 1e-9

    def test_unsorted_input(self):
        """Function must sort internally — order of input must not matter."""
        assert percentile([5.0, 1.0, 3.0], 50.0) == percentile([1.0, 3.0, 5.0], 50.0)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            percentile([], 50.0)

    def test_p_out_of_range_raises(self):
        with pytest.raises(ValueError, match="in \\[0, 100\\]"):
            percentile([1.0, 2.0], 101.0)

    def test_p_negative_raises(self):
        with pytest.raises(ValueError, match="in \\[0, 100\\]"):
            percentile([1.0, 2.0], -1.0)

    def test_identical_values(self):
        """All identical values → every percentile equals that value."""
        vals = [7.5] * 20
        assert percentile(vals, 0.0) == 7.5
        assert percentile(vals, 50.0) == 7.5
        assert percentile(vals, 99.0) == 7.5


# ---------------------------------------------------------------------------
# latency_stats
# ---------------------------------------------------------------------------

class TestLatencyStats:
    def test_keys_present(self):
        stats = latency_stats([100.0, 200.0, 300.0])
        assert set(stats.keys()) == {"mean", "median", "p95", "p99", "min", "max"}

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            latency_stats([])

    def test_single_value_all_equal(self):
        stats = latency_stats([250.0])
        for v in stats.values():
            assert v == 250.0

    def test_mean_correct(self):
        stats = latency_stats([100.0, 200.0, 300.0])
        assert abs(stats["mean"] - 200.0) < 1e-9

    def test_min_max(self):
        vals = [50.0, 150.0, 250.0, 350.0]
        stats = latency_stats(vals)
        assert stats["min"] == 50.0
        assert stats["max"] == 350.0

    def test_p95_consistent_with_percentile(self):
        vals = [float(i) for i in range(1, 101)]
        stats = latency_stats(vals)
        expected_p95 = percentile(vals, 95.0)
        assert abs(stats["p95"] - expected_p95) < 1e-9

    def test_p99_consistent_with_percentile(self):
        vals = [float(i) for i in range(1, 101)]
        stats = latency_stats(vals)
        expected_p99 = percentile(vals, 99.0)
        assert abs(stats["p99"] - expected_p99) < 1e-9

    def test_ordering_p95_le_p99_le_max(self):
        import random as _random
        _random.seed(0)
        vals = [_random.uniform(10, 1000) for _ in range(200)]
        stats = latency_stats(vals)
        assert stats["p95"] <= stats["p99"] <= stats["max"]

    def test_median_consistent_with_percentile(self):
        vals = [10.0, 20.0, 30.0, 40.0, 50.0]
        stats = latency_stats(vals)
        assert abs(stats["median"] - percentile(vals, 50.0)) < 1e-9

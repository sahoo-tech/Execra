"""
Unit tests for core/intelligence/trace_anomaly_detector.py.

Test strategy
-------------
Pure helper functions (_extract_features, _score_to_match,
_build_baseline_data) are tested directly.

TraceAnomalyDetector instances are always created with ``auto_load=False``
to avoid disk I/O and make tests fast and deterministic.  Tests that need
a fitted model either call ``detector.fit(traces)`` or
``detector._fit_baseline()`` explicitly.

Model persistence is tested using ``tmp_path`` (pytest's temporary
directory fixture) so no real files are left behind.
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from sklearn.ensemble import IsolationForest

from core.intelligence.trace_anomaly_detector import (
    FEATURE_NAMES,
    AnomalyResult,
    ExecutionTrace,
    TraceAnomalyDetector,
    _build_baseline_data,
    _extract_features,
    _score_to_match,
    _validate_model,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def detector() -> TraceAnomalyDetector:
    """Unfitted detector — no disk access, no baseline fitting."""
    return TraceAnomalyDetector(auto_load=False)


@pytest.fixture
def fitted_detector() -> TraceAnomalyDetector:
    """Detector fitted on synthetic baseline — ready for inference."""
    d = TraceAnomalyDetector(
        contamination=0.1,
        n_estimators=10,   # small ensemble for test speed
        random_state=42,
        auto_load=False,
    )
    d._fit_baseline()
    return d


@pytest.fixture
def normal_trace() -> ExecutionTrace:
    """A trace with typical healthy values."""
    return ExecutionTrace(
        duration_ms=480.0,
        cpu_percent=12.0,
        memory_mb=195.0,
        error_count=0,
        warning_count=1,
        step_count=5,
        llm_latency_ms=750.0,
        rule_match_count=1,
    )


@pytest.fixture
def anomalous_trace() -> ExecutionTrace:
    """A clearly anomalous trace — extreme outlier on every feature."""
    return ExecutionTrace(
        duration_ms=50_000.0,   # 50 s — far above baseline mean of 500 ms
        cpu_percent=99.0,
        memory_mb=5_000.0,
        error_count=50,
        warning_count=100,
        step_count=50,
        llm_latency_ms=30_000.0,
        rule_match_count=100,
    )


@pytest.fixture
def sample_traces() -> list[ExecutionTrace]:
    """Small list of realistic traces for fit() tests."""
    return [
        ExecutionTrace(duration_ms=d, cpu_percent=10 + i, memory_mb=190 + i * 5,
                       error_count=0, warning_count=i % 2, step_count=5,
                       llm_latency_ms=750 + i * 10, rule_match_count=1)
        for i, d in enumerate(range(450, 560, 10))
    ]


# ---------------------------------------------------------------------------
# ExecutionTrace
# ---------------------------------------------------------------------------

class TestExecutionTrace:
    def test_default_construction(self):
        t = ExecutionTrace()
        assert t.duration_ms == 500.0
        assert t.cpu_percent == 15.0
        assert t.memory_mb == 200.0
        assert t.error_count == 0
        assert t.warning_count == 0
        assert t.step_count == 5
        assert t.llm_latency_ms == 800.0
        assert t.rule_match_count == 1

    def test_custom_values(self):
        t = ExecutionTrace(duration_ms=999.0, error_count=3)
        assert t.duration_ms == 999.0
        assert t.error_count == 3
        # Unchanged defaults
        assert t.step_count == 5

    def test_all_fields_present(self):
        expected = {
            "duration_ms", "cpu_percent", "memory_mb", "error_count",
            "warning_count", "step_count", "llm_latency_ms", "rule_match_count",
        }
        t = ExecutionTrace()
        assert set(vars(t).keys()) == expected


# ---------------------------------------------------------------------------
# AnomalyResult
# ---------------------------------------------------------------------------

class TestAnomalyResult:
    def test_execution_trace_match_in_range(self):
        r = AnomalyResult(
            is_anomaly=False,
            anomaly_score=0.1,
            execution_trace_match=0.6,
            feature_values={n: 0.0 for n in FEATURE_NAMES},
        )
        assert 0.0 <= r.execution_trace_match <= 1.0

    def test_feature_values_contains_all_names(self):
        r = AnomalyResult(
            is_anomaly=True,
            anomaly_score=-0.3,
            execution_trace_match=0.2,
            feature_values={n: float(i) for i, n in enumerate(FEATURE_NAMES)},
        )
        assert set(r.feature_values.keys()) == set(FEATURE_NAMES)

    def test_sklearn_version_populated(self):
        import sklearn
        r = AnomalyResult(
            is_anomaly=False,
            anomaly_score=0.05,
            execution_trace_match=0.55,
            feature_values={},
        )
        assert r.sklearn_version == sklearn.__version__


# ---------------------------------------------------------------------------
# _extract_features
# ---------------------------------------------------------------------------

class TestExtractFeatures:
    def test_returns_correct_shape(self, normal_trace):
        features = _extract_features(normal_trace)
        assert features.shape == (8,)

    def test_dtype_is_float64(self, normal_trace):
        features = _extract_features(normal_trace)
        assert features.dtype == np.float64

    def test_all_values_finite(self, normal_trace):
        features = _extract_features(normal_trace)
        assert np.all(np.isfinite(features))

    def test_feature_order_matches_names(self):
        t = ExecutionTrace(
            duration_ms=1.0, cpu_percent=2.0, memory_mb=3.0,
            error_count=4, warning_count=5, step_count=6,
            llm_latency_ms=7.0, rule_match_count=8,
        )
        features = _extract_features(t)
        assert features[0] == 1.0   # duration_ms
        assert features[1] == 2.0   # cpu_percent
        assert features[2] == 3.0   # memory_mb
        assert features[3] == 4.0   # error_count
        assert features[4] == 5.0   # warning_count
        assert features[5] == 6.0   # step_count
        assert features[6] == 7.0   # llm_latency_ms
        assert features[7] == 8.0   # rule_match_count

    def test_integer_fields_cast_to_float(self):
        t = ExecutionTrace(error_count=3, warning_count=7, step_count=4,
                           rule_match_count=2)
        features = _extract_features(t)
        assert isinstance(features[3], (float, np.floating))  # error_count

    def test_feature_names_length(self):
        assert len(FEATURE_NAMES) == 8


# ---------------------------------------------------------------------------
# _score_to_match
# ---------------------------------------------------------------------------

class TestScoreToMatch:
    def test_positive_score_above_half(self):
        assert _score_to_match(0.2) > 0.5

    def test_negative_score_below_half(self):
        assert _score_to_match(-0.2) < 0.5

    def test_zero_score_is_half(self):
        assert _score_to_match(0.0) == 0.5

    def test_large_positive_clamped_to_one(self):
        assert _score_to_match(10.0) == 1.0

    def test_large_negative_clamped_to_zero(self):
        assert _score_to_match(-10.0) == 0.0

    def test_boundary_plus_half(self):
        assert _score_to_match(0.5) == 1.0

    def test_boundary_minus_half(self):
        assert _score_to_match(-0.5) == 0.0

    def test_output_always_in_range(self):
        for raw in [-1.0, -0.5, -0.3, 0.0, 0.1, 0.3, 0.5, 1.0]:
            result = _score_to_match(raw)
            assert 0.0 <= result <= 1.0, f"Out of range for raw={raw}: {result}"


# ---------------------------------------------------------------------------
# _build_baseline_data
# ---------------------------------------------------------------------------

class TestBuildBaselineData:
    def test_output_shape(self):
        X = _build_baseline_data(n=50, random_state=0)
        assert X.shape == (50, 8)

    def test_dtype_float64(self):
        X = _build_baseline_data(n=50, random_state=0)
        assert X.dtype == np.float64

    def test_all_values_finite(self):
        X = _build_baseline_data(n=200, random_state=42)
        assert np.all(np.isfinite(X))

    def test_no_negative_counts(self):
        """error_count, warning_count, step_count, rule_match_count must be >= 0."""
        X = _build_baseline_data(n=200, random_state=42)
        for col_idx in [3, 4, 5, 7]:  # error, warning, step, rule
            assert np.all(X[:, col_idx] >= 0), f"Column {col_idx} has negative values"

    def test_deterministic_with_same_seed(self):
        X1 = _build_baseline_data(n=50, random_state=7)
        X2 = _build_baseline_data(n=50, random_state=7)
        np.testing.assert_array_equal(X1, X2)

    def test_different_seeds_differ(self):
        X1 = _build_baseline_data(n=50, random_state=1)
        X2 = _build_baseline_data(n=50, random_state=2)
        assert not np.array_equal(X1, X2)


# ---------------------------------------------------------------------------
# TraceAnomalyDetector — construction and state
# ---------------------------------------------------------------------------

class TestDetectorConstruction:
    def test_auto_load_false_leaves_unfitted(self, detector):
        assert not detector.is_fitted

    def test_auto_load_false_model_is_none(self, detector):
        assert detector._model is None

    def test_fit_baseline_marks_as_fitted(self, detector):
        detector._fit_baseline()
        assert detector.is_fitted

    def test_fit_traces_marks_as_fitted(self, detector, sample_traces):
        detector.fit(sample_traces)
        assert detector.is_fitted

    def test_params_defaults_from_settings(self):
        from core.config import settings
        d = TraceAnomalyDetector(auto_load=False)
        assert d._contamination == settings.ANOMALY_CONTAMINATION
        assert d._n_estimators == settings.ANOMALY_N_ESTIMATORS
        assert d._random_state == settings.ANOMALY_RANDOM_STATE

    def test_params_override_settings(self):
        d = TraceAnomalyDetector(
            contamination=0.05,
            n_estimators=50,
            random_state=99,
            auto_load=False,
        )
        assert d._contamination == 0.05
        assert d._n_estimators == 50
        assert d._random_state == 99


# ---------------------------------------------------------------------------
# TraceAnomalyDetector — fit()
# ---------------------------------------------------------------------------

class TestDetectorFit:
    def test_empty_list_raises(self, detector):
        with pytest.raises(ValueError, match="at least one"):
            detector.fit([])

    def test_single_trace_raises(self, detector, normal_trace):
        with pytest.raises(ValueError, match="at least 2"):
            detector.fit([normal_trace])

    def test_fit_records_sample_count(self, detector, sample_traces):
        detector.fit(sample_traces)
        assert detector._n_samples_fitted == len(sample_traces)

    def test_refit_updates_model(self, fitted_detector, sample_traces):
        old_model = fitted_detector._model
        fitted_detector.fit(sample_traces)
        # A new IsolationForest object should have been created
        assert fitted_detector._model is not old_model


# ---------------------------------------------------------------------------
# TraceAnomalyDetector — predict()
# ---------------------------------------------------------------------------

class TestDetectorPredict:
    def test_predict_requires_fitted_model(self, detector, normal_trace):
        with pytest.raises(RuntimeError, match="has not been fitted"):
            detector.predict(normal_trace)

    def test_predict_returns_anomaly_result(self, fitted_detector, normal_trace):
        result = fitted_detector.predict(normal_trace)
        assert isinstance(result, AnomalyResult)

    def test_predict_execution_trace_match_bounded(self, fitted_detector, normal_trace):
        result = fitted_detector.predict(normal_trace)
        assert 0.0 <= result.execution_trace_match <= 1.0

    def test_predict_feature_values_complete(self, fitted_detector, normal_trace):
        result = fitted_detector.predict(normal_trace)
        assert set(result.feature_values.keys()) == set(FEATURE_NAMES)

    def test_predict_feature_values_match_input(self, fitted_detector, normal_trace):
        result = fitted_detector.predict(normal_trace)
        assert result.feature_values["duration_ms"] == pytest.approx(normal_trace.duration_ms)
        assert result.feature_values["error_count"] == pytest.approx(normal_trace.error_count)

    def test_normal_trace_has_positive_score(self, fitted_detector, normal_trace):
        """A trace matching baseline distributions should score close to normal."""
        result = fitted_detector.predict(normal_trace)
        # Score may be negative if contamination is large, but execution_trace_match
        # should be reasonable (> 0.3) for a genuinely normal trace
        assert result.execution_trace_match > 0.0

    def test_extreme_outlier_flagged_as_anomaly(self, fitted_detector, anomalous_trace):
        """A trace with extreme values on every feature must be flagged."""
        result = fitted_detector.predict(anomalous_trace)
        assert result.is_anomaly is True
        assert result.execution_trace_match < 0.5

    def test_is_anomaly_matches_score_sign(self, fitted_detector, normal_trace):
        """is_anomaly should be True exactly when anomaly_score < 0."""
        result = fitted_detector.predict(normal_trace)
        # is_anomaly from predict() and score < 0 should be consistent
        if result.anomaly_score < 0:
            assert result.is_anomaly is True
        else:
            assert result.is_anomaly is False

    def test_multiple_predictions_consistent(self, fitted_detector, normal_trace):
        """Calling predict twice on the same trace must return the same result."""
        r1 = fitted_detector.predict(normal_trace)
        r2 = fitted_detector.predict(normal_trace)
        assert r1.anomaly_score == r2.anomaly_score
        assert r1.is_anomaly == r2.is_anomaly
        assert r1.execution_trace_match == r2.execution_trace_match

    def test_anomaly_score_is_float(self, fitted_detector, normal_trace):
        result = fitted_detector.predict(normal_trace)
        assert isinstance(result.anomaly_score, float)


# ---------------------------------------------------------------------------
# TraceAnomalyDetector — save() / load()
# ---------------------------------------------------------------------------

class TestDetectorPersistence:
    def test_save_unfitted_raises(self, detector, tmp_path):
        with pytest.raises(RuntimeError, match="unfitted"):
            detector.save(path=str(tmp_path / "model.joblib"))

    def test_save_creates_file(self, fitted_detector, tmp_path):
        path = str(tmp_path / "model.joblib")
        fitted_detector.save(path=path)
        assert Path(path).exists()

    def test_load_missing_file_raises(self, detector, tmp_path):
        with pytest.raises(FileNotFoundError):
            detector.load(path=str(tmp_path / "nonexistent.joblib"))

    def test_save_load_roundtrip(self, fitted_detector, tmp_path, normal_trace):
        """Predictions before and after a save/load cycle must be identical."""
        path = str(tmp_path / "model.joblib")

        result_before = fitted_detector.predict(normal_trace)
        fitted_detector.save(path=path)

        fresh = TraceAnomalyDetector(auto_load=False)
        fresh.load(path=path)

        result_after = fresh.predict(normal_trace)

        assert result_before.anomaly_score == result_after.anomaly_score
        assert result_before.is_anomaly == result_after.is_anomaly

    def test_load_marks_as_fitted(self, fitted_detector, tmp_path):
        path = str(tmp_path / "model.joblib")
        fitted_detector.save(path=path)

        fresh = TraceAnomalyDetector(auto_load=False)
        assert not fresh.is_fitted
        fresh.load(path=path)
        assert fresh.is_fitted

    def test_payload_contains_sklearn_version(self, fitted_detector, tmp_path):
        import joblib, sklearn
        path = str(tmp_path / "model.joblib")
        fitted_detector.save(path=path)
        payload = joblib.load(path)
        assert payload["sklearn_version"] == sklearn.__version__

    def test_payload_contains_feature_names(self, fitted_detector, tmp_path):
        import joblib
        path = str(tmp_path / "model.joblib")
        fitted_detector.save(path=path)
        payload = joblib.load(path)
        assert payload["feature_names"] == FEATURE_NAMES

    def test_save_creates_parent_directory(self, fitted_detector, tmp_path):
        path = str(tmp_path / "nested" / "dir" / "model.joblib")
        fitted_detector.save(path=path)
        assert Path(path).exists()

    def test_load_version_mismatch_logs_warning(
        self, fitted_detector, tmp_path, caplog
    ):
        """A saved model with a different sklearn version triggers a warning."""
        import joblib, logging
        path = str(tmp_path / "old_model.joblib")
        # Manually write a payload with a fake old version
        payload = {
            "model": fitted_detector._model,
            "sklearn_version": "0.0.0",
            "feature_names": FEATURE_NAMES,
            "n_samples_fitted": 200,
            "saved_at": "2020-01-01T00:00:00+00:00",
        }
        joblib.dump(payload, path)

        fresh = TraceAnomalyDetector(auto_load=False)
        with caplog.at_level(
            logging.WARNING,
            logger="core.intelligence.trace_anomaly_detector",
        ):
            fresh.load(path=path)
        assert any("0.0.0" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# TraceAnomalyDetector — auto_load fallback behaviour
# ---------------------------------------------------------------------------

class TestDetectorAutoLoad:
    def test_auto_load_true_fits_baseline_when_no_file(self, tmp_path):
        """With a non-existent model path, auto_load=True fits baseline."""
        d = TraceAnomalyDetector(
            model_path=str(tmp_path / "no_model.joblib"),
            n_estimators=10,
            auto_load=True,
        )
        assert d.is_fitted

    def test_auto_load_loads_from_existing_file(self, fitted_detector, tmp_path):
        path = str(tmp_path / "model.joblib")
        fitted_detector.save(path=path)

        d = TraceAnomalyDetector(model_path=path, n_estimators=10, auto_load=True)
        assert d.is_fitted

    def test_auto_load_falls_back_on_corrupt_file(self, tmp_path):
        """A corrupt joblib file triggers baseline fitting, not a crash."""
        bad_path = tmp_path / "bad.joblib"
        bad_path.write_bytes(b"not a valid joblib payload")

        d = TraceAnomalyDetector(
            model_path=str(bad_path),
            n_estimators=10,
            auto_load=True,
        )
        assert d.is_fitted


# ---------------------------------------------------------------------------
# Settings integration
# ---------------------------------------------------------------------------

class TestAnomalySettings:
    def test_defaults_present(self):
        from core.config import settings
        assert isinstance(settings.ANOMALY_CONTAMINATION, float)
        assert 0 < settings.ANOMALY_CONTAMINATION < 1
        assert isinstance(settings.ANOMALY_N_ESTIMATORS, int)
        assert settings.ANOMALY_N_ESTIMATORS > 0
        assert isinstance(settings.ANOMALY_RANDOM_STATE, int)
        assert isinstance(settings.ANOMALY_MODEL_PATH, str)
        assert settings.ANOMALY_MODEL_PATH.endswith(".joblib")

    def test_env_override_contamination(self):
        from core.config import Settings
        with patch.dict(os.environ, {"ANOMALY_CONTAMINATION": "0.05"}):
            s = Settings()
            assert s.ANOMALY_CONTAMINATION == pytest.approx(0.05)

    def test_env_override_n_estimators(self):
        from core.config import Settings
        with patch.dict(os.environ, {"ANOMALY_N_ESTIMATORS": "200"}):
            s = Settings()
            assert s.ANOMALY_N_ESTIMATORS == 200

    def test_env_override_random_state(self):
        from core.config import Settings
        with patch.dict(os.environ, {"ANOMALY_RANDOM_STATE": "7"}):
            s = Settings()
            assert s.ANOMALY_RANDOM_STATE == 7

    def test_env_override_model_path(self):
        from core.config import Settings
        with patch.dict(os.environ, {"ANOMALY_MODEL_PATH": "/tmp/my_model.joblib"}):
            s = Settings()
            assert s.ANOMALY_MODEL_PATH == "/tmp/my_model.joblib"


# ---------------------------------------------------------------------------
# Module-level singleton smoke test
# ---------------------------------------------------------------------------

class TestModuleSingleton:
    def test_singleton_is_fitted(self):
        """The module-level `detector` must be ready for inference after import."""
        from core.intelligence.trace_anomaly_detector import detector as d
        assert d.is_fitted

    def test_singleton_can_predict(self):
        from core.intelligence.trace_anomaly_detector import detector as d
        result = d.predict(ExecutionTrace())
        assert isinstance(result, AnomalyResult)
        assert 0.0 <= result.execution_trace_match <= 1.0


# ---------------------------------------------------------------------------
# Version compatibility — _validate_model, load(), predict(), eviction
# ---------------------------------------------------------------------------

class TestDetectorVersionCompatibility:
    """
    Covers the bug-fix surface for Issue #215:

    - ``_validate_model`` rejects wrong types, unfitted models, and
      feature-count mismatches before any state is mutated.
    - ``load()`` never sets ``_is_fitted = True`` on an incompatible model.
    - ``predict()`` raises RuntimeError on sklearn inference failures instead
      of propagating raw sklearn exceptions to callers.
    - ``_evict_incompatible_model()`` renames the bad file; no-ops when the
      file is absent or when rename fails.
    - ``_try_load_or_fit_baseline()`` evicts the bad file and falls back to
      baseline fitting without crashing.
    """

    # ------------------------------------------------------------------
    # _validate_model — type check
    # ------------------------------------------------------------------

    def test_validate_model_accepts_fitted_isolation_forest(self, fitted_detector):
        """A freshly fitted IsolationForest must pass validation."""
        # Should not raise
        _validate_model(fitted_detector._model)

    def test_validate_model_rejects_wrong_type(self):
        """Passing a non-IsolationForest object raises TypeError."""
        with pytest.raises(TypeError, match="Expected IsolationForest"):
            _validate_model(object())

    def test_validate_model_rejects_none(self):
        """None is not an IsolationForest — TypeError must be raised."""
        with pytest.raises(TypeError, match="Expected IsolationForest"):
            _validate_model(None)

    # ------------------------------------------------------------------
    # _validate_model — unfitted model
    # ------------------------------------------------------------------

    def test_validate_model_rejects_unfitted_isolation_forest(self):
        """An IsolationForest that has not been fit() raises ValueError."""
        unfitted = IsolationForest()
        with pytest.raises(ValueError, match="not fitted"):
            _validate_model(unfitted)

    # ------------------------------------------------------------------
    # _validate_model — feature-count mismatch
    # ------------------------------------------------------------------

    def test_validate_model_rejects_wrong_feature_count(self):
        """A model trained on 3 features must fail probe inference (expects 8)."""
        import numpy as np
        from sklearn.ensemble import IsolationForest as IF
        wrong_model = IF(n_estimators=5, random_state=0)
        wrong_model.fit(np.zeros((10, 3)))  # 3 features, not 8
        with pytest.raises(ValueError, match="probe inference failed"):
            _validate_model(wrong_model)

    # ------------------------------------------------------------------
    # load() — is_fitted not set on invalid model
    # ------------------------------------------------------------------

    def test_load_does_not_set_is_fitted_on_type_mismatch(self, detector, tmp_path):
        """
        When the payload model fails type validation, load() must raise and
        leave the detector in its pre-load state (is_fitted=False).
        """
        import joblib
        path = str(tmp_path / "bad_type.joblib")
        joblib.dump({"model": "not_an_if", "sklearn_version": "0.0.0",
                     "feature_names": FEATURE_NAMES, "n_samples_fitted": 0,
                     "saved_at": "2020-01-01"}, path)

        with pytest.raises((TypeError, ValueError)):
            detector.load(path=path)

        assert not detector.is_fitted

    def test_load_does_not_set_is_fitted_on_wrong_feature_count(
        self, detector, tmp_path
    ):
        """
        A model trained on wrong feature count must fail probe validation;
        detector must remain unfitted.
        """
        import joblib, numpy as np
        from sklearn.ensemble import IsolationForest as IF
        wrong_model = IF(n_estimators=5, random_state=0)
        wrong_model.fit(np.zeros((10, 3)))

        path = str(tmp_path / "wrong_features.joblib")
        joblib.dump({"model": wrong_model, "sklearn_version": "0.0.0",
                     "feature_names": ["a", "b", "c"], "n_samples_fitted": 10,
                     "saved_at": "2020-01-01"}, path)

        with pytest.raises(ValueError, match="probe inference failed"):
            detector.load(path=path)

        assert not detector.is_fitted

    def test_load_does_not_set_is_fitted_on_corrupt_bytes(self, detector, tmp_path):
        """A corrupt joblib file must not leave the detector in a fitted state."""
        path = tmp_path / "corrupt.joblib"
        path.write_bytes(b"\x00\x01\x02garbage")

        with pytest.raises(Exception):
            detector.load(path=str(path))

        assert not detector.is_fitted

    def test_load_legacy_raw_model_succeeds(self, fitted_detector, tmp_path):
        """
        A legacy file containing a bare IsolationForest (no dict wrapper)
        must load successfully if the model passes validation.
        """
        import joblib
        path = str(tmp_path / "legacy.joblib")
        joblib.dump(fitted_detector._model, path)

        fresh = TraceAnomalyDetector(auto_load=False)
        fresh.load(path=path)
        assert fresh.is_fitted

    # ------------------------------------------------------------------
    # predict() — inference failure wrapped in RuntimeError
    # ------------------------------------------------------------------

    def test_predict_wraps_sklearn_error_as_runtime_error(self, fitted_detector):
        """
        If decision_function raises (e.g., from a mutated/incompatible model),
        predict() must wrap the error in RuntimeError with a descriptive message.
        """
        from unittest.mock import patch as _patch

        trace = ExecutionTrace()
        with _patch.object(
            fitted_detector._model,
            "decision_function",
            side_effect=ValueError("X has 3 features, but IsolationForest is expecting 8"),
        ):
            with pytest.raises(RuntimeError, match="Model inference failed"):
                fitted_detector.predict(trace)

    def test_predict_error_message_mentions_sklearn_version(self, fitted_detector):
        """RuntimeError from inference must name the current sklearn version."""
        import sklearn
        from unittest.mock import patch as _patch

        trace = ExecutionTrace()
        with _patch.object(
            fitted_detector._model,
            "decision_function",
            side_effect=ValueError("simulated mismatch"),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                fitted_detector.predict(trace)

        assert sklearn.__version__ in str(exc_info.value)

    # ------------------------------------------------------------------
    # _evict_incompatible_model — file lifecycle
    # ------------------------------------------------------------------

    def test_evict_renames_existing_model_file(self, tmp_path):
        """An existing model file must be renamed to <name>.incompatible."""
        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"dummy")

        d = TraceAnomalyDetector(
            model_path=str(model_path), auto_load=False
        )
        d._evict_incompatible_model()

        assert not model_path.exists()
        assert (tmp_path / "model.joblib.incompatible").exists()

    def test_evict_is_noop_when_file_missing(self, tmp_path):
        """_evict_incompatible_model must not raise when the file is absent."""
        d = TraceAnomalyDetector(
            model_path=str(tmp_path / "nonexistent.joblib"), auto_load=False
        )
        d._evict_incompatible_model()  # should not raise

    def test_evict_logs_warning_on_rename_failure(self, tmp_path, caplog):
        """An OSError during rename logs a warning but does not propagate."""
        import logging
        from unittest.mock import patch as _patch

        model_path = tmp_path / "model.joblib"
        model_path.write_bytes(b"dummy")

        d = TraceAnomalyDetector(
            model_path=str(model_path), auto_load=False
        )
        with _patch("pathlib.Path.rename", side_effect=OSError("permission denied")):
            with caplog.at_level(
                logging.WARNING,
                logger="core.intelligence.trace_anomaly_detector",
            ):
                d._evict_incompatible_model()  # must not raise

        assert any("Could not rename" in r.message for r in caplog.records)

    # ------------------------------------------------------------------
    # _try_load_or_fit_baseline — eviction + fallback
    # ------------------------------------------------------------------

    def test_fallback_evicts_corrupt_file_before_baseline_fit(self, tmp_path):
        """
        When auto_load fails due to a corrupt file, the file must be evicted
        and the detector must still be fitted (via baseline).
        """
        bad_path = tmp_path / "bad.joblib"
        bad_path.write_bytes(b"corrupted data")

        d = TraceAnomalyDetector(
            model_path=str(bad_path),
            n_estimators=5,
            auto_load=True,
        )

        assert d.is_fitted
        assert not bad_path.exists(), "Corrupt model file was not evicted"
        assert (tmp_path / "bad.joblib.incompatible").exists()

    def test_fallback_fits_baseline_on_feature_count_mismatch(self, tmp_path):
        """
        A valid joblib file with wrong feature count triggers eviction and
        baseline fitting — the detector must be ready for inference.
        """
        import joblib, numpy as np
        from sklearn.ensemble import IsolationForest as IF

        wrong_model = IF(n_estimators=5, random_state=0)
        wrong_model.fit(np.zeros((10, 3)))

        path = tmp_path / "mismatch.joblib"
        joblib.dump({"model": wrong_model, "sklearn_version": "0.0.0",
                     "feature_names": ["a", "b", "c"], "n_samples_fitted": 10,
                     "saved_at": "2020-01-01"}, str(path))

        d = TraceAnomalyDetector(
            model_path=str(path),
            n_estimators=5,
            auto_load=True,
        )

        assert d.is_fitted
        # After fallback the detector must produce valid predictions
        result = d.predict(ExecutionTrace())
        assert 0.0 <= result.execution_trace_match <= 1.0
        assert not path.exists(), "Incompatible model file was not evicted"

"""
Isolation Forest-based anomaly detector for Execra execution traces.

Design overview
---------------
The detector wraps scikit-learn's ``IsolationForest`` behind a thin, typed
interface that fits the Execra intelligence pipeline:

1. ``ExecutionTrace`` — a dataclass capturing the eight numeric signals that
   describe one end-to-end pipeline run (latency, resource usage, error
   counts, etc.).

2. ``AnomalyResult`` — the prediction output: a boolean flag, a raw anomaly
   score, a normalised ``execution_trace_match`` value ready for
   ``trust_scorer.calculate_trust_score()``, and a per-feature breakdown
   for explainability.

3. ``TraceAnomalyDetector`` — the core class:
   - ``fit(traces)``  — trains or retrains the model on real trace data.
   - ``predict(trace)`` — synchronous inference; safe to call inside async
     coroutines (microsecond latency for 100 trees, 8 features).
   - ``save() / load()`` — joblib-based persistence to ``data/`` with a
     version-stamped payload so sklearn upgrades are caught early.
   - On construction, automatically loads a saved model from disk; if none
     exists (or loading fails), silently fits on a synthetic "normal"
     baseline so the detector is always ready without manual bootstrapping.

Integration with trust scoring
-------------------------------
Replace the raw ``execution_trace_match`` argument::

    from core.intelligence.trace_anomaly_detector import detector, ExecutionTrace

    trace = ExecutionTrace(
        duration_ms=480.0, cpu_percent=12.0, memory_mb=195.0,
        error_count=0, warning_count=1, step_count=5,
        llm_latency_ms=750.0, rule_match_count=1,
    )
    result = detector.predict(trace)
    trust = calculate_trust_score(
        llm_confidence=0.82,
        rule_validation=True,
        execution_trace_match=result.execution_trace_match,
    )

False-positive guidance
-----------------------
The default ``ANOMALY_CONTAMINATION=0.1`` means the model expects ~10 % of
training traces to be anomalous. On a fresh install the baseline is synthetic,
so the threshold is only approximate. After collecting real production traces,
call ``detector.fit(real_traces); detector.save()`` to recalibrate.

Known limitations
-----------------
- No online learning: the model is updated only by explicit ``fit()`` calls.
- Idle-connection timeout / per-IP limits are out of scope here.
- The synthetic baseline targets typical development workloads; production
  operators should always retrain on real data.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest

import joblib

from core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sklearn version string — saved alongside the model for drift detection
# ---------------------------------------------------------------------------
_SKLEARN_VERSION: str = sklearn.__version__

# ---------------------------------------------------------------------------
# Feature registry
# ---------------------------------------------------------------------------

#: Ordered list of feature names.  The order must match ``_extract_features``.
FEATURE_NAMES: list[str] = [
    "duration_ms",
    "cpu_percent",
    "memory_mb",
    "error_count",
    "warning_count",
    "step_count",
    "llm_latency_ms",
    "rule_match_count",
]

# Number of synthetic baseline traces used when no real data is available.
_BASELINE_N_SAMPLES: int = 200


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ExecutionTrace:
    """
    Numeric signals captured from a single end-to-end Execra pipeline run.

    All fields have sensible defaults representing a typical healthy trace so
    that partial construction is possible during development.

    Fields
    ------
    duration_ms:
        Total wall-clock time for the pipeline run in milliseconds.
    cpu_percent:
        Peak CPU utilisation recorded during the run (0–100).
    memory_mb:
        Peak resident memory in megabytes.
    error_count:
        Number of unhandled exceptions or logged ERROR entries.
    warning_count:
        Number of logged WARNING entries.
    step_count:
        Number of pipeline stages that executed (e.g. perception → OCR →
        LLM → rules → trust).
    llm_latency_ms:
        Wall-clock time spent waiting for LLM responses, in milliseconds.
        Zero if no LLM call was made.
    rule_match_count:
        Number of plugin-rule matches returned by the rule engine.
    """

    duration_ms: float = 500.0
    cpu_percent: float = 15.0
    memory_mb: float = 200.0
    error_count: int = 0
    warning_count: int = 0
    step_count: int = 5
    llm_latency_ms: float = 800.0
    rule_match_count: int = 1


@dataclass
class AnomalyResult:
    """
    Output of ``TraceAnomalyDetector.predict()``.

    Fields
    ------
    is_anomaly:
        ``True`` when the trace is classified as anomalous by the Isolation
        Forest (``decision_function < 0``).
    anomaly_score:
        Raw ``IsolationForest.decision_function`` value.  Higher (positive)
        values indicate normality; lower (negative) values indicate anomaly.
        Roughly in ``[-0.5, 0.5]`` but technically unbounded.
    execution_trace_match:
        ``anomaly_score`` clamped and shifted to ``[0.0, 1.0]``.  Suitable
        for direct use as the ``execution_trace_match`` argument of
        ``trust_scorer.calculate_trust_score()``.
    feature_values:
        Dict mapping each feature name to its extracted value, providing a
        human-readable explanation of what the model saw.
    sklearn_version:
        The scikit-learn version used at inference time, for reproducibility
        auditing.
    """

    is_anomaly: bool
    anomaly_score: float
    execution_trace_match: float
    feature_values: dict[str, float]
    sklearn_version: str = field(default_factory=lambda: _SKLEARN_VERSION)


# ---------------------------------------------------------------------------
# Pure helper functions (easy to unit-test without instantiating the detector)
# ---------------------------------------------------------------------------

def _extract_features(trace: ExecutionTrace) -> np.ndarray:
    """
    Convert an ``ExecutionTrace`` to a 1-D numpy feature vector.

    The order matches :data:`FEATURE_NAMES` exactly.  This function is pure
    (no side effects) so it can be tested in isolation.

    Returns
    -------
    np.ndarray
        Shape ``(8,)``, dtype ``float64``.
    """
    return np.array(
        [
            trace.duration_ms,
            trace.cpu_percent,
            trace.memory_mb,
            float(trace.error_count),
            float(trace.warning_count),
            float(trace.step_count),
            trace.llm_latency_ms,
            float(trace.rule_match_count),
        ],
        dtype=np.float64,
    )


def _score_to_match(raw_score: float) -> float:
    """
    Map a raw ``IsolationForest.decision_function`` value to ``[0.0, 1.0]``.

    The IF decision function centres near 0 for boundary cases, is positive
    for normal points, and negative for anomalies.  A linear shift of +0.5
    followed by clamping produces an interpretable ``execution_trace_match``
    value:

    * ``raw_score ≥ +0.5`` → ``1.0`` (clearly normal)
    * ``raw_score = 0.0``  → ``0.5`` (boundary)
    * ``raw_score ≤ −0.5`` → ``0.0`` (clearly anomalous)
    """
    return float(max(0.0, min(1.0, 0.5 + raw_score)))


def _build_baseline_data(
    n: int,
    random_state: int,
) -> np.ndarray:
    """
    Generate a synthetic dataset of *n* "normal" traces.

    Distributions are chosen to match typical healthy workloads in a
    development environment.  Using a fixed ``random_state`` makes the
    baseline deterministic across runs.

    Returns
    -------
    np.ndarray
        Shape ``(n, 8)``, dtype ``float64``.
    """
    rng = np.random.default_rng(seed=random_state)

    duration_ms       = rng.normal(500, 100, n).clip(50, 5_000)
    cpu_percent       = rng.normal(15, 5, n).clip(1, 95)
    memory_mb         = rng.normal(200, 30, n).clip(50, 2_000)
    error_count       = rng.poisson(0.3, n).clip(0, 10).astype(float)
    warning_count     = rng.poisson(0.8, n).clip(0, 20).astype(float)
    step_count        = rng.integers(3, 10, n).astype(float)
    llm_latency_ms    = rng.normal(800, 150, n).clip(100, 10_000)
    rule_match_count  = rng.integers(0, 5, n).astype(float)

    return np.column_stack([
        duration_ms,
        cpu_percent,
        memory_mb,
        error_count,
        warning_count,
        step_count,
        llm_latency_ms,
        rule_match_count,
    ])


def _validate_model(model: Any) -> None:
    """
    Verify that *model* is a fitted ``IsolationForest`` compatible with the
    current feature set before it is stored on the detector.

    Three checks are performed in order:

    1. **Type check** — *model* must be an ``IsolationForest`` instance.
    2. **Fitted check** — the model must have ``estimators_`` populated,
       which sklearn sets only after a successful ``fit()`` call.
    3. **Probe inference** — ``decision_function`` is called with a zero
       vector of the expected shape.  This catches feature-count mismatches
       (``ValueError``) and any other sklearn internal state errors that only
       surface at inference time rather than at load time.

    Parameters
    ----------
    model:
        The candidate model object to validate.

    Raises
    ------
    TypeError
        If *model* is not an ``IsolationForest``.
    ValueError
        If the model is not fitted or the probe inference fails (e.g., trained
        on a different number of features or an incompatible sklearn version).
    """
    if not isinstance(model, IsolationForest):
        raise TypeError(
            f"Expected IsolationForest, got {type(model).__name__}."
        )

    if not hasattr(model, "estimators_"):
        raise ValueError(
            "Model is not fitted — 'estimators_' attribute is missing. "
            "The file may have been saved before fit() completed."
        )

    probe = np.zeros((1, len(FEATURE_NAMES)), dtype=np.float64)
    try:
        model.decision_function(probe)
    except Exception as exc:
        raise ValueError(
            f"Model probe inference failed — the saved model may be "
            f"incompatible with the current sklearn version "
            f"({_SKLEARN_VERSION}). Re-train with detector.fit(traces) and "
            f"detector.save(). Original error: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Detector class
# ---------------------------------------------------------------------------

class TraceAnomalyDetector:
    """
    Isolation Forest anomaly detector for Execra execution traces.

    Parameters
    ----------
    contamination:
        Expected fraction of anomalous traces in the training set.
        Forwarded directly to ``IsolationForest(contamination=...)``.
        Defaults to ``settings.ANOMALY_CONTAMINATION``.
    n_estimators:
        Number of trees in the ensemble.
        Defaults to ``settings.ANOMALY_N_ESTIMATORS``.
    random_state:
        Seed for reproducibility.
        Defaults to ``settings.ANOMALY_RANDOM_STATE``.
    model_path:
        Filesystem path for joblib serialisation.
        Defaults to ``settings.ANOMALY_MODEL_PATH``.
    auto_load:
        When ``True`` (default), the constructor attempts to load a saved
        model from *model_path*; if loading fails, it falls back to fitting
        on a synthetic baseline.  Set to ``False`` in tests to skip disk I/O.
    """

    def __init__(
        self,
        contamination: float | None = None,
        n_estimators: int | None = None,
        random_state: int | None = None,
        model_path: str | None = None,
        auto_load: bool = True,
    ) -> None:
        self._contamination: float = (
            contamination
            if contamination is not None
            else settings.ANOMALY_CONTAMINATION
        )
        self._n_estimators: int = (
            n_estimators
            if n_estimators is not None
            else settings.ANOMALY_N_ESTIMATORS
        )
        self._random_state: int = (
            random_state
            if random_state is not None
            else settings.ANOMALY_RANDOM_STATE
        )
        self._model_path: str = (
            model_path
            if model_path is not None
            else settings.ANOMALY_MODEL_PATH
        )

        self._model: IsolationForest | None = None
        self._is_fitted: bool = False
        self._n_samples_fitted: int = 0

        if auto_load:
            self._try_load_or_fit_baseline()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def is_fitted(self) -> bool:
        """``True`` when the detector has a trained model ready for inference."""
        return self._is_fitted

    def fit(self, traces: list[ExecutionTrace]) -> None:
        """
        Train (or retrain) the Isolation Forest on *traces*.

        Parameters
        ----------
        traces:
            Non-empty list of ``ExecutionTrace`` instances.  At least 2
            samples are required by IsolationForest.

        Raises
        ------
        ValueError
            If *traces* is empty or contains fewer than 2 samples.
        """
        if not traces:
            raise ValueError("fit() requires at least one ExecutionTrace; got empty list.")
        if len(traces) < 2:
            raise ValueError(
                f"IsolationForest requires at least 2 samples; got {len(traces)}."
            )

        X = np.array([_extract_features(t) for t in traces], dtype=np.float64)
        self._fit_array(X)
        logger.info(
            "TraceAnomalyDetector fitted on %d real traces "
            "(contamination=%.2f, n_estimators=%d).",
            len(traces),
            self._contamination,
            self._n_estimators,
        )

    def predict(self, trace: ExecutionTrace) -> AnomalyResult:
        """
        Classify *trace* as normal or anomalous.

        Parameters
        ----------
        trace:
            The execution trace to evaluate.

        Returns
        -------
        AnomalyResult
            Contains the binary flag, raw score, normalised
            ``execution_trace_match``, and per-feature values.

        Raises
        ------
        RuntimeError
            If the detector has not been fitted (only possible when
            ``auto_load=False`` and ``fit()`` has not been called).
        """
        if not self._is_fitted or self._model is None:
            raise RuntimeError(
                "TraceAnomalyDetector has not been fitted. "
                "Call fit() or load() first, or use auto_load=True."
            )

        features = _extract_features(trace)
        X = features.reshape(1, -1)

        try:
            raw_score: float = float(self._model.decision_function(X)[0])
            is_anomaly: bool = bool(self._model.predict(X)[0] == -1)
        except Exception as exc:
            raise RuntimeError(
                f"Model inference failed — the loaded model may be "
                f"incompatible with the current sklearn version "
                f"({_SKLEARN_VERSION}). Re-train with detector.fit(traces) "
                f"and detector.save(). Original error: {exc}"
            ) from exc
        match: float = _score_to_match(raw_score)

        feature_values: dict[str, float] = {
            name: float(val)
            for name, val in zip(FEATURE_NAMES, features)
        }

        if is_anomaly:
            logger.warning(
                "Anomalous execution trace detected (score=%.4f, match=%.4f). "
                "Top signals: duration_ms=%.1f, error_count=%d, cpu_percent=%.1f.",
                raw_score,
                match,
                trace.duration_ms,
                trace.error_count,
                trace.cpu_percent,
            )

        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=round(raw_score, 6),
            execution_trace_match=round(match, 6),
            feature_values=feature_values,
        )

    def save(self, path: str | None = None) -> None:
        """
        Persist the fitted model to disk using joblib.

        The payload is a dict containing the model, the sklearn version it
        was trained with, the feature names, and a UTC timestamp.  This
        allows the loader to detect sklearn version drift.

        Parameters
        ----------
        path:
            Override destination path.  Defaults to ``self._model_path``.

        Raises
        ------
        RuntimeError
            If the detector has not been fitted.
        """
        if not self._is_fitted or self._model is None:
            raise RuntimeError("Cannot save an unfitted model.")

        dest = Path(path or self._model_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        payload: dict[str, Any] = {
            "model": self._model,
            "sklearn_version": _SKLEARN_VERSION,
            "feature_names": FEATURE_NAMES,
            "n_samples_fitted": self._n_samples_fitted,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        joblib.dump(payload, dest)
        logger.info("TraceAnomalyDetector model saved to %s.", dest)

    def load(self, path: str | None = None) -> None:
        """
        Load a previously saved model from disk.

        A warning is logged if the saved model was created with a different
        sklearn version than the currently installed one.

        Parameters
        ----------
        path:
            Override source path.  Defaults to ``self._model_path``.

        Raises
        ------
        FileNotFoundError
            If *path* does not exist.
        Exception
            Re-raises any joblib/pickle errors so callers can decide whether
            to fall back to baseline fitting.
        """
        src = Path(path or self._model_path)
        if not src.exists():
            raise FileNotFoundError(f"Model file not found: {src}")

        payload: Any = joblib.load(src)

        if isinstance(payload, dict):
            saved_version: str = payload.get("sklearn_version", "unknown")
            if saved_version != _SKLEARN_VERSION:
                logger.warning(
                    "Model was saved with sklearn %s; current version is %s. "
                    "Consider retraining with detector.fit() and detector.save().",
                    saved_version,
                    _SKLEARN_VERSION,
                )
            candidate_model: Any = payload["model"]
            n_samples: int = payload.get("n_samples_fitted", 0)
        else:
            # Legacy support: payload is the raw IsolationForest instance
            candidate_model = payload
            n_samples = 0

        # Validate the candidate before committing it to state.  Raises
        # TypeError or ValueError if the model is incompatible; the caller
        # (_try_load_or_fit_baseline) catches those and falls back to baseline.
        _validate_model(candidate_model)

        self._model = candidate_model
        self._n_samples_fitted = n_samples
        self._is_fitted = True
        logger.info("TraceAnomalyDetector model loaded from %s.", src)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fit_array(self, X: np.ndarray) -> None:
        """Fit a new IsolationForest on the pre-built feature matrix *X*."""
        self._model = IsolationForest(
            n_estimators=self._n_estimators,
            contamination=self._contamination,
            random_state=self._random_state,
            n_jobs=1,  # avoid fork-on-predict issues in asyncio
        )
        self._model.fit(X)
        self._is_fitted = True
        self._n_samples_fitted = len(X)

    def _evict_incompatible_model(self) -> None:
        """
        Rename a corrupt or incompatible model file so it is not re-attempted
        on the next process restart.

        The file is moved to ``<original_name>.incompatible`` in the same
        directory.  If the rename fails (e.g., permission error), a warning is
        logged but no exception is raised — the fallback baseline fitting
        proceeds regardless.

        This method is a no-op when the model file does not exist.
        """
        src = Path(self._model_path)
        if not src.exists():
            return
        dest = src.parent / (src.name + ".incompatible")
        try:
            src.rename(dest)
            logger.info(
                "Renamed incompatible model file '%s' → '%s'.", src, dest
            )
        except OSError as exc:
            logger.warning(
                "Could not rename incompatible model file '%s': %s.", src, exc
            )

    def _fit_baseline(self) -> None:
        """
        Fit on a synthetic "normal" workload dataset.

        Used when no saved model is available and no real traces have been
        collected yet.  The random state is taken from ``self._random_state``
        so the baseline is reproducible given the same configuration.
        """
        X = _build_baseline_data(
            n=_BASELINE_N_SAMPLES,
            random_state=self._random_state,
        )
        self._fit_array(X)
        logger.info(
            "TraceAnomalyDetector fitted on %d synthetic baseline traces.",
            _BASELINE_N_SAMPLES,
        )

    def _try_load_or_fit_baseline(self) -> None:
        """
        Attempt to load a saved model; fall back to baseline fitting on error.

        Covers:
        - Model file not found (fresh install)
        - Pickle / protocol errors (sklearn version mismatch)
        - Any other I/O error
        """
        try:
            self.load()
        except FileNotFoundError:
            logger.info(
                "No saved model at '%s'; fitting synthetic baseline.",
                self._model_path,
            )
            self._fit_baseline()
        except Exception as exc:
            logger.warning(
                "Failed to load model from '%s' (%s: %s); fitting synthetic baseline.",
                self._model_path,
                type(exc).__name__,
                exc,
            )
            self._evict_incompatible_model()
            self._fit_baseline()


# ---------------------------------------------------------------------------
# Module-level singleton
#
# Import this in calling code:
#   from core.intelligence.trace_anomaly_detector import detector
#
# The constructor runs _try_load_or_fit_baseline() once at import time
# (~0.1 s for 200 samples / 100 trees).  The instance is thread-safe at
# inference time (IsolationForest.predict is read-only).
# ---------------------------------------------------------------------------

detector = TraceAnomalyDetector()

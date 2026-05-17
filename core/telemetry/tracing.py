"""
Distributed tracing for Execra using OpenTelemetry.

When ``OTEL_ENABLED`` is ``False`` (the default) ``get_tracer()`` returns a
zero-cost no-op tracer and no exporters are initialised — zero runtime
overhead.

When ``OTEL_ENABLED`` is ``True`` the module configures a
:class:`~opentelemetry.sdk.trace.TracerProvider` backed by a
:class:`~opentelemetry.sdk.trace.export.BatchSpanProcessor` and an
OTLP-HTTP exporter directed at ``OTEL_ENDPOINT``.  The default endpoint
(``http://localhost:4318/v1/traces``) targets the OTLP receiver on the
``jaegertracing/all-in-one`` container defined in
``docker-compose.override.yml``.  The legacy Jaeger Thrift endpoint
(``http://localhost:14268/api/traces``) is also available on that
container if needed.

Usage in instrumented modules::

    from core.telemetry.tracing import get_tracer, SPAN_PERCEPTION_OCR

    def extract_text(frame: np.ndarray) -> str:
        with get_tracer("execra.perception").start_as_current_span(
            SPAN_PERCEPTION_OCR
        ) as span:
            span.set_attribute("frame_size_bytes", frame.nbytes)
            ...
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional OTel import — graceful degradation when packages are not installed
# ---------------------------------------------------------------------------

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False

# Module-level provider — set by setup_tracing(), cleared by shutdown_tracing()
_provider: object | None = None

# ---------------------------------------------------------------------------
# Span name constants  (issue #135 naming convention)
# ---------------------------------------------------------------------------

SPAN_PERCEPTION_FRAME: str = "execra.perception.frame_capture"
SPAN_PERCEPTION_OCR: str = "execra.perception.ocr"
SPAN_INTELLIGENCE_GENERATE: str = "execra.intelligence.generate"
SPAN_INTELLIGENCE_LLM: str = "execra.intelligence.llm_call"
SPAN_INTELLIGENCE_RULES: str = "execra.intelligence.rule_engine"
SPAN_INTELLIGENCE_SIM: str = "execra.intelligence.consequence_sim"
SPAN_INTELLIGENCE_TRUST: str = "execra.intelligence.trust_score"
SPAN_OUTPUT_DISPATCH: str = "execra.output.dispatch"
SPAN_OUTPUT_WS: str = "execra.output.websocket_broadcast"


# ---------------------------------------------------------------------------
# No-op tracer — used when OTel packages are not installed
# ---------------------------------------------------------------------------


class _NoOpSpan:
    """Minimal context-manager span used when OTel is not installed."""

    def __enter__(self) -> "_NoOpSpan":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def set_attribute(self, key: str, value: object) -> None:
        pass

    def set_status(self, status: object, description: str = "") -> None:
        pass

    def record_exception(self, exc: BaseException, **kwargs: object) -> None:
        pass


class _NoOpTracer:
    """Minimal tracer returned when OTel packages are not installed."""

    def start_as_current_span(self, name: str, **kwargs: object) -> _NoOpSpan:
        return _NoOpSpan()

    def start_span(self, name: str, **kwargs: object) -> _NoOpSpan:
        return _NoOpSpan()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def setup_tracing(settings: object) -> None:
    """Initialise the TracerProvider and OTLP exporter.

    Called once during the FastAPI startup event.  When
    ``settings.OTEL_ENABLED`` is ``False`` (the default) this function is a
    no-op and no exporters are created.

    Args:
        settings: The application :class:`~core.config.Settings` instance.
    """
    global _provider

    if not getattr(settings, "OTEL_ENABLED", False):
        return

    if not _OTEL_AVAILABLE:
        logger.warning(
            "OTEL_ENABLED=true but opentelemetry packages are not installed. "
            "Run: pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-exporter-otlp-proto-http"
        )
        return

    endpoint = getattr(
        settings, "OTEL_ENDPOINT", "http://localhost:4318/v1/traces"
    )
    try:
        exporter = OTLPSpanExporter(endpoint=endpoint)
        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _provider = provider
        logger.info("OpenTelemetry tracing enabled → %s", endpoint)
    except Exception:
        logger.exception(
            "Failed to initialise OpenTelemetry tracing; continuing without tracing"
        )


def shutdown_tracing() -> None:
    """Flush buffered spans and shut down the BatchSpanProcessor cleanly.

    Called from the FastAPI shutdown event to ensure no spans are dropped
    on process exit.
    """
    global _provider
    if _provider is None:
        return
    if _OTEL_AVAILABLE:
        try:
            _provider.shutdown()  # type: ignore[attr-defined]
        except Exception:
            logger.exception("Error flushing OpenTelemetry spans on shutdown")
    _provider = None


def get_tracer(name: str) -> object:
    """Return a tracer for *name*.

    Returns the OTel SDK tracer when tracing is active, or a zero-cost
    no-op tracer when ``OTEL_ENABLED`` is ``False`` or OTel is not
    installed.  The no-op path has no measurable runtime overhead.

    Args:
        name: Instrumentation scope name, e.g. ``"execra.perception"``.

    Returns:
        An OTel :class:`~opentelemetry.trace.Tracer` or a :class:`_NoOpTracer`.
    """
    if not _OTEL_AVAILABLE:
        return _NoOpTracer()
    return trace.get_tracer(name)

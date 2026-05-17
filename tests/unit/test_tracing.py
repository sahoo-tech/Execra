"""
Unit tests for core.telemetry.tracing.

Tests cover:
- No-op span / tracer behaviour when OTel SDK is not installed
- setup_tracing() is a no-op when OTEL_ENABLED=False
- shutdown_tracing() is safe when _provider is None
- Span name constants match the issue #135 naming convention
- In-memory exporter correctly captures spans and attributes (SDK required)
"""

import pytest

import core.telemetry.tracing as tracing_module
from core.telemetry.tracing import (
    _NoOpSpan,
    _NoOpTracer,
    get_tracer,
    setup_tracing,
    shutdown_tracing,
    SPAN_PERCEPTION_FRAME,
    SPAN_PERCEPTION_OCR,
    SPAN_INTELLIGENCE_GENERATE,
    SPAN_INTELLIGENCE_LLM,
    SPAN_INTELLIGENCE_RULES,
    SPAN_INTELLIGENCE_SIM,
    SPAN_INTELLIGENCE_TRUST,
    SPAN_OUTPUT_DISPATCH,
    SPAN_OUTPUT_WS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeSettings:
    """Minimal settings stub for setup_tracing()."""

    def __init__(self, otel_enabled: bool = False, otel_endpoint: str = "http://localhost:4318/v1/traces"):
        self.OTEL_ENABLED = otel_enabled
        self.OTEL_ENDPOINT = otel_endpoint


# ---------------------------------------------------------------------------
# No-op span tests
# ---------------------------------------------------------------------------

class TestNoOpSpan:
    def test_context_manager_returns_self(self):
        span = _NoOpSpan()
        with span as s:
            assert s is span

    def test_set_attribute_is_silent(self):
        span = _NoOpSpan()
        span.set_attribute("key", "value")  # must not raise

    def test_set_status_is_silent(self):
        span = _NoOpSpan()
        span.set_status(object(), description="ok")

    def test_record_exception_is_silent(self):
        span = _NoOpSpan()
        span.record_exception(ValueError("boom"))

    def test_exception_inside_span_does_not_suppress(self):
        """Exceptions propagate normally out of the no-op span context."""
        span = _NoOpSpan()
        with pytest.raises(RuntimeError, match="inner"):
            with span:
                raise RuntimeError("inner")


# ---------------------------------------------------------------------------
# No-op tracer tests
# ---------------------------------------------------------------------------

class TestNoOpTracer:
    def test_start_as_current_span_returns_noop_span(self):
        tracer = _NoOpTracer()
        span = tracer.start_as_current_span("any.span")
        assert isinstance(span, _NoOpSpan)

    def test_start_span_returns_noop_span(self):
        tracer = _NoOpTracer()
        span = tracer.start_span("any.span")
        assert isinstance(span, _NoOpSpan)

    def test_usable_as_context_manager(self):
        tracer = _NoOpTracer()
        with tracer.start_as_current_span("test.span") as span:
            span.set_attribute("foo", 1)  # must not raise


# ---------------------------------------------------------------------------
# setup_tracing / shutdown_tracing tests
# ---------------------------------------------------------------------------

class TestSetupTracing:
    def setup_method(self):
        # Ensure a clean provider state before each test.
        tracing_module._provider = None

    def teardown_method(self):
        tracing_module._provider = None

    def test_noop_when_otel_disabled(self):
        settings = _FakeSettings(otel_enabled=False)
        setup_tracing(settings)
        assert tracing_module._provider is None

    def test_shutdown_safe_when_provider_is_none(self):
        tracing_module._provider = None
        shutdown_tracing()  # must not raise
        assert tracing_module._provider is None


# ---------------------------------------------------------------------------
# Span name constant tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("constant, expected", [
    (SPAN_PERCEPTION_FRAME,    "execra.perception.frame_capture"),
    (SPAN_PERCEPTION_OCR,      "execra.perception.ocr"),
    (SPAN_INTELLIGENCE_GENERATE, "execra.intelligence.generate"),
    (SPAN_INTELLIGENCE_LLM,    "execra.intelligence.llm_call"),
    (SPAN_INTELLIGENCE_RULES,  "execra.intelligence.rule_engine"),
    (SPAN_INTELLIGENCE_SIM,    "execra.intelligence.consequence_sim"),
    (SPAN_INTELLIGENCE_TRUST,  "execra.intelligence.trust_score"),
    (SPAN_OUTPUT_DISPATCH,     "execra.output.dispatch"),
    (SPAN_OUTPUT_WS,           "execra.output.websocket_broadcast"),
])
def test_span_name_constants(constant, expected):
    assert constant == expected


# ---------------------------------------------------------------------------
# SDK-backed tests (skipped when SDK is not installed)
# ---------------------------------------------------------------------------

_sdk_available = True
try:
    from opentelemetry.sdk.trace import TracerProvider as _TracerProvider  # noqa: F401
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter as _InMemorySpanExporter  # noqa: F401
except ImportError:
    _sdk_available = False

_skip_without_sdk = pytest.mark.skipif(
    not _sdk_available,
    reason="opentelemetry-sdk not installed",
)


@_skip_without_sdk
class TestInMemoryTracing:
    """Integration-style tests that use the real OTel in-memory exporter."""

    def setup_method(self):
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
        from opentelemetry import trace

        self.exporter = InMemorySpanExporter()
        self.provider = TracerProvider()
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        trace.set_tracer_provider(self.provider)

        # Point the module-level provider to our test provider so shutdown_tracing works.
        tracing_module._provider = self.provider

    def teardown_method(self):
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        # Reset to a fresh provider to avoid cross-test bleed.
        trace.set_tracer_provider(TracerProvider())
        tracing_module._provider = None

    def _get_spans(self):
        return self.exporter.get_finished_spans()

    def test_span_is_exported_with_correct_name(self):
        from opentelemetry import trace

        tracer = trace.get_tracer("execra.test")
        with tracer.start_as_current_span(SPAN_PERCEPTION_OCR):
            pass

        spans = self._get_spans()
        assert len(spans) == 1
        assert spans[0].name == SPAN_PERCEPTION_OCR

    def test_span_attribute_is_recorded(self):
        from opentelemetry import trace

        tracer = trace.get_tracer("execra.test")
        with tracer.start_as_current_span(SPAN_INTELLIGENCE_TRUST) as span:
            span.set_attribute("trust.score", 0.9)
            span.set_attribute("trust.level", "Trusted")

        spans = self._get_spans()
        assert spans[0].attributes["trust.score"] == pytest.approx(0.9)
        assert spans[0].attributes["trust.level"] == "Trusted"

    def test_frame_size_bytes_attribute(self):
        from opentelemetry import trace

        tracer = trace.get_tracer("execra.test")
        with tracer.start_as_current_span(SPAN_PERCEPTION_FRAME) as span:
            span.set_attribute("frame_size_bytes", 1_920 * 1_080 * 3)

        spans = self._get_spans()
        assert spans[0].attributes["frame_size_bytes"] == 1_920 * 1_080 * 3

    def test_llm_backend_attribute(self):
        from opentelemetry import trace

        tracer = trace.get_tracer("execra.test")
        with tracer.start_as_current_span(SPAN_INTELLIGENCE_LLM) as span:
            span.set_attribute("llm.backend", "openai")
            span.set_attribute("llm.model", "gpt-4o")

        spans = self._get_spans()
        assert spans[0].attributes["llm.backend"] == "openai"
        assert spans[0].attributes["llm.model"] == "gpt-4o"

    def test_exception_inside_span_still_finishes_span(self):
        from opentelemetry import trace

        tracer = trace.get_tracer("execra.test")
        with pytest.raises(ValueError):
            with tracer.start_as_current_span(SPAN_INTELLIGENCE_RULES):
                raise ValueError("rule error")

        spans = self._get_spans()
        assert len(spans) == 1  # span was still finished

    def test_shutdown_tracing_clears_provider(self):
        shutdown_tracing()
        assert tracing_module._provider is None

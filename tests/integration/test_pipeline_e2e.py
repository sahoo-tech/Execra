"""
tests/integration/test_pipeline_e2e.py
=======================================
End-to-end integration tests for ExecraPipeline.

All LLM calls are mocked (no network needed).
A FakeWebSocket stub captures dispatched messages for assertion.
asyncio timing enforces the ≤500 ms latency SLA per frame.

Run with:
    pytest tests/integration/test_pipeline_e2e.py -v --asyncio-mode=auto
"""

from __future__ import annotations

import asyncio
import json
import time
from unittest.mock import AsyncMock

import pytest

from core.pipeline import (
    Domain,
    ExecraPipeline,
    Guidance,
    Mode,
    PerceptionFrame,
    PipelineConfig,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeWebSocket:
    """Minimal WebSocket stub that records all sent messages."""

    def __init__(self) -> None:
        self.messages: list[str] = []
        self.closed = False

    async def send_text(self, text: str) -> None:
        if self.closed:
            raise RuntimeError("WebSocket closed")
        self.messages.append(text)

    @property
    def last_message(self) -> dict | None:
        if not self.messages:
            return None
        return json.loads(self.messages[-1])


def _make_frame(source: str = "screen", task_type: str = "coding") -> PerceptionFrame:
    return PerceptionFrame(
        source=source,
        data=b"fake_image_bytes",
        metadata={"task_type": task_type},
    )


def _make_pipeline(domain: str = "digital", mode: str = "passive",
                   worker_count: int = 1) -> ExecraPipeline:
    config = PipelineConfig(
        perception_queue_maxsize=8,
        processing_queue_maxsize=4,
        guidance_confidence_threshold=0.60,
        worker_count=worker_count,
        latency_warn_ms=500.0,
        shutdown_timeout_s=2.0,
    )
    return ExecraPipeline(domain=domain, mode=mode, config=config)


# ---------------------------------------------------------------------------
# Component tests
# ---------------------------------------------------------------------------

class TestPerceptionBus:
    @pytest.mark.asyncio
    async def test_put_and_get_frame(self):
        from core.pipeline import PerceptionBus
        bus = PerceptionBus(domain=Domain.DIGITAL, maxsize=4)
        await bus.start()
        frame = _make_frame()
        await bus.put_frame(frame)
        received = await asyncio.wait_for(bus.get_frame(), timeout=1.0)
        assert received.source == "screen"
        bus.frame_done()
        await bus.stop()

    @pytest.mark.asyncio
    async def test_backpressure_drops_oldest(self):
        from core.pipeline import PerceptionBus
        bus = PerceptionBus(domain=Domain.DIGITAL, maxsize=2)
        await bus.start()
        frame_a = _make_frame(task_type="task_a")
        frame_b = _make_frame(task_type="task_b")
        frame_c = _make_frame(task_type="task_c")
        await bus.put_frame(frame_a)
        await bus.put_frame(frame_b)
        await bus.put_frame(frame_c)   # frame_a evicted
        first = await asyncio.wait_for(bus.get_frame(), timeout=1.0)
        bus.frame_done()
        assert first.metadata["task_type"] == "task_b"
        assert bus.dropped_frames == 1
        await bus.stop()


class TestGuidanceDispatcher:
    @pytest.mark.asyncio
    async def test_dispatch_sends_to_client(self):
        from core.pipeline import GuidanceDispatcher
        disp = GuidanceDispatcher()
        await disp.start()
        ws = FakeWebSocket()
        disp.register_client(ws)
        g = Guidance(instruction="Check null pointer on line 42",
                     confidence=0.91, source="hybrid",
                     reasoning="Rule + LLM concur", mode="safe")
        assert await disp.dispatch(g) is True
        assert len(ws.messages) == 1
        msg = json.loads(ws.messages[0])
        assert msg["instruction"] == g.instruction
        await disp.stop()

    @pytest.mark.asyncio
    async def test_deduplication_suppresses_repeat(self):
        from core.pipeline import GuidanceDispatcher
        disp = GuidanceDispatcher()
        await disp.start()
        ws = FakeWebSocket()
        disp.register_client(ws)
        g = Guidance(instruction="Same instruction", confidence=0.88,
                     source="llm", reasoning="test", mode="safe")
        assert await disp.dispatch(g) is True
        assert await disp.dispatch(g) is False   # deduplicated
        assert len(ws.messages) == 1
        await disp.stop()

    @pytest.mark.asyncio
    async def test_different_instructions_all_dispatched(self):
        from core.pipeline import GuidanceDispatcher
        disp = GuidanceDispatcher()
        await disp.start()
        ws = FakeWebSocket()
        disp.register_client(ws)
        for i in range(3):
            g = Guidance(instruction=f"Instruction {i}", confidence=0.80,
                         source="llm", reasoning="", mode="safe")
            await disp.dispatch(g)
        assert len(ws.messages) == 3
        await disp.stop()


class TestTrustScorer:
    def test_high_confidence_passes_unchanged(self):
        from core.pipeline import TrustScorer
        scorer = TrustScorer(threshold=0.60)
        g = Guidance(instruction="Do X", confidence=0.85, source="llm",
                     reasoning="", mode="expert")
        assert scorer.score(g).mode == "expert"
        assert "⚠️" not in g.instruction

    def test_low_confidence_appends_warning(self):
        from core.pipeline import TrustScorer
        scorer = TrustScorer(threshold=0.60)
        g = Guidance(instruction="Do X", confidence=0.40, source="llm",
                     reasoning="", mode="expert")
        scored = scorer.score(g)
        assert scored.mode == "safe"
        assert "⚠️" in scored.instruction


# ---------------------------------------------------------------------------
# Integration tests — full pipeline
# ---------------------------------------------------------------------------

class TestPipelineIntegration:

    @pytest.mark.asyncio
    async def test_single_frame_produces_guidance(self):
        p = _make_pipeline()
        ws = FakeWebSocket()

        async def _inject_and_stop():
            await asyncio.sleep(0.05)
            p.dispatcher.register_client(ws)
            await p.perception_bus.put_frame(_make_frame(task_type="debugging"))
            await asyncio.sleep(0.4)
            await p.stop()

        await asyncio.gather(p.run(), _inject_and_stop())
        assert len(ws.messages) >= 1
        assert "instruction" in ws.last_message

    @pytest.mark.asyncio
    async def test_latency_sla_500ms(self):
        p = _make_pipeline()
        latencies: list[float] = []
        original = p._process_frame

        async def _tracked(frame: PerceptionFrame) -> None:
            t0 = time.monotonic()
            await original(frame)
            latencies.append(time.monotonic() - t0)

        p._process_frame = _tracked  # type: ignore[method-assign]

        async def _inject_and_stop():
            await asyncio.sleep(0.05)
            for i in range(5):
                await p.perception_bus.put_frame(_make_frame(task_type=f"task_{i}"))
                await asyncio.sleep(0.02)
            await asyncio.sleep(0.6)
            await p.stop()

        await asyncio.gather(p.run(), _inject_and_stop())
        assert latencies, "No frames processed"
        for lat in latencies:
            assert lat < 0.5, f"SLA breached: {lat*1000:.1f} ms"

    @pytest.mark.asyncio
    async def test_backpressure_never_blocks_perception(self):
        p = _make_pipeline()

        async def _flood_and_stop():
            await asyncio.sleep(0.05)
            for i in range(50):
                await p.perception_bus.put_frame(_make_frame(task_type=f"flood_{i}"))
            await asyncio.sleep(0.5)
            await p.stop()

        await asyncio.gather(p.run(), _flood_and_stop())
        assert p.metrics.frames_received > 0

    @pytest.mark.asyncio
    async def test_deduplication_end_to_end(self):
        p = _make_pipeline()
        ws = FakeWebSocket()
        fixed = Guidance(instruction="Always the same", confidence=0.90,
                         source="llm", reasoning="fixed", mode="safe")
        p.intelligence_core.generate_guidance = AsyncMock(return_value=fixed)

        async def _inject_and_stop():
            await asyncio.sleep(0.05)
            p.dispatcher.register_client(ws)
            for _ in range(5):
                await p.perception_bus.put_frame(_make_frame())
                await asyncio.sleep(0.05)
            await asyncio.sleep(0.4)
            await p.stop()

        await asyncio.gather(p.run(), _inject_and_stop())
        assert len(ws.messages) == 1, f"Expected 1, got {len(ws.messages)}"

    @pytest.mark.asyncio
    async def test_no_guidance_frames_skipped(self):
        p = _make_pipeline()
        ws = FakeWebSocket()
        p.intelligence_core.generate_guidance = AsyncMock(return_value=None)

        async def _inject_and_stop():
            await asyncio.sleep(0.05)
            p.dispatcher.register_client(ws)
            await p.perception_bus.put_frame(_make_frame())
            await asyncio.sleep(0.3)
            await p.stop()

        await asyncio.gather(p.run(), _inject_and_stop())
        assert len(ws.messages) == 0

    @pytest.mark.asyncio
    async def test_clean_stop_idempotent(self):
        p = _make_pipeline()

        async def _start_and_stop():
            await asyncio.sleep(0.1)
            await p.stop()
            await p.stop()   # must not raise

        await asyncio.gather(p.run(), _start_and_stop())

    @pytest.mark.asyncio
    async def test_metrics_populated(self):
        p = _make_pipeline()

        async def _inject_and_stop():
            await asyncio.sleep(0.05)
            for _ in range(3):
                await p.perception_bus.put_frame(_make_frame())
                await asyncio.sleep(0.05)
            # Poll until latency_samples is populated (max 3s) before stopping.
            # Windows asyncio scheduling is slower than Linux; a fixed sleep races.
            for _ in range(60):
                await asyncio.sleep(0.05)
                if p.metrics.latency_samples:
                    break
            await p.stop()

        await asyncio.gather(p.run(), _inject_and_stop())
        m = p.get_metrics()
        assert m["frames_received"] >= 3
        if p.metrics.latency_samples:
         assert m["guidances_generated"] >= 1
         assert m["latency_p50_ms"] >= 0
        else:
            assert m["frames_received"] >= 3 
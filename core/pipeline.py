"""
core/pipeline.py
================
Execra End-to-End Real-Time Guidance Streaming Pipeline

Architecture:
  PerceptionBus → ContextEngine → IntelligenceCore → TrustScorer
                                                    → GuidanceDispatcher → WebSocket
                                                    → ActionLogger

Design goals:
  • ≤500 ms latency from frame arrival to WebSocket broadcast
  • Backpressure: drop oldest frame when processing queue is full (never block perception)
  • Guidance deduplication: never emit the same instruction twice in a row
  • Clean async shutdown with resource cleanup
"""

from __future__ import annotations

import asyncio
import logging
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain / Mode enums
# ---------------------------------------------------------------------------

class Domain(str, Enum):
    DIGITAL = "digital"
    PHYSICAL = "physical"


class Mode(str, Enum):
    PASSIVE = "passive"   # auto-observe, no user prompts
    ACTIVE = "active"     # user asks questions; context auto-remembered
    MIXED = "mixed"       # both simultaneously


# ---------------------------------------------------------------------------
# Data transfer objects
# ---------------------------------------------------------------------------

@dataclass
class PerceptionFrame:
    """Raw frame produced by the PerceptionBus."""
    source: str                          # e.g. "screen", "camera"
    data: Any                            # image array, OCR text, etc.
    timestamp: float = field(default_factory=time.monotonic)
    metadata: dict = field(default_factory=dict)


@dataclass
class ProcessedContext:
    """Output of the ContextEngine."""
    task_type: str
    current_step: int
    session_summary: str
    raw_frame: PerceptionFrame
    processed_at: float = field(default_factory=time.monotonic)


@dataclass
class Guidance:
    """Output of the IntelligenceCore after trust scoring."""
    instruction: str
    confidence: float          # 0.0 – 1.0
    source: str                # "llm", "rule_engine", "hybrid"
    reasoning: str
    mode: str                  # "safe" | "expert"
    frame_timestamp: float = 0.0
    dispatched_at: float = field(default_factory=time.monotonic)

    @property
    def fingerprint(self) -> str:
        """SHA-1 of instruction text; used for deduplication."""
        return hashlib.sha1(self.instruction.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Pipeline configuration
# ---------------------------------------------------------------------------

@dataclass
class PipelineConfig:
    """Tunable knobs for the pipeline."""
    perception_queue_maxsize: int = 32
    processing_queue_maxsize: int = 16
    guidance_confidence_threshold: float = 0.60
    worker_count: int = 2
    latency_warn_ms: float = 500.0
    shutdown_timeout_s: float = 5.0


# ---------------------------------------------------------------------------
# Perception Bus
# ---------------------------------------------------------------------------

class PerceptionBus:
    """
    Aggregates frames from all input sources (screen capture, camera feed)
    and puts them into an asyncio.Queue.

    Backpressure: when the queue is full, the oldest frame is evicted so that
    producers are never blocked (real-time perception takes priority).
    """

    def __init__(self, domain: Domain, maxsize: int = 32):
        self.domain = domain
        self._queue: asyncio.Queue[PerceptionFrame] = asyncio.Queue(maxsize=maxsize)
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._dropped = 0

    async def start(self) -> None:
        self._running = True
        if self.domain in (Domain.DIGITAL, Domain.PHYSICAL):
            task = asyncio.create_task(self._capture_loop(), name="perception_capture")
            self._tasks.append(task)
        logger.info("[PerceptionBus] started (domain=%s)", self.domain)

    async def stop(self) -> None:
        self._running = False
        for t in self._tasks:
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
        logger.info("[PerceptionBus] stopped (dropped_frames=%d)", self._dropped)

    async def put_frame(self, frame: PerceptionFrame) -> None:
        """Push a frame; evict the oldest if the queue is full."""
        if self._queue.full():
            try:
                self._queue.get_nowait()
                self._dropped += 1
                logger.debug("[PerceptionBus] queue full – oldest frame dropped (total=%d)", self._dropped)
            except asyncio.QueueEmpty:
                pass
        await self._queue.put(frame)

    async def get_frame(self) -> PerceptionFrame:
        return await self._queue.get()

    def frame_done(self) -> None:
        self._queue.task_done()

    @property
    def dropped_frames(self) -> int:
        return self._dropped

    async def _capture_loop(self) -> None:
        """
        Placeholder loop. In production this calls the real screen-capture
        or camera-feed driver. Tests inject frames via put_frame() directly.
        """
        logger.debug("[PerceptionBus] capture loop started")
        while self._running:
            await asyncio.sleep(0.1)


# ---------------------------------------------------------------------------
# Context Engine
# ---------------------------------------------------------------------------

class ContextEngine:
    """
    Maintains the dynamic session context model.

    Receives raw PerceptionFrames, performs task detection, and returns a
    ProcessedContext that the IntelligenceCore can reason over.
    """

    def __init__(self, domain: Domain):
        self.domain = domain
        self._step_counter: int = 0
        self._task_history: list[str] = []

    async def start(self) -> None:
        logger.info("[ContextEngine] started")

    async def stop(self) -> None:
        logger.info("[ContextEngine] stopped")

    async def process(self, frame: PerceptionFrame) -> ProcessedContext:
        """Analyse frame and return enriched context."""
        task_type = self._infer_task_type(frame)
        self._step_counter += 1
        self._task_history.append(task_type)

        return ProcessedContext(
            task_type=task_type,
            current_step=self._step_counter,
            session_summary=self._build_summary(),
            raw_frame=frame,
        )

    def _infer_task_type(self, frame: PerceptionFrame) -> str:
        """Stub – real implementation uses classifier / intent engine."""
        return frame.metadata.get("task_type", "general")

    def _build_summary(self) -> str:
        last = self._task_history[-5:] if len(self._task_history) >= 5 else self._task_history
        return f"Recent tasks: {', '.join(last)}"


# ---------------------------------------------------------------------------
# Intelligence Core
# ---------------------------------------------------------------------------

class IntelligenceCore:
    """
    LLM + rule-engine + consequence simulator.

    Takes ProcessedContext → returns raw Guidance (un-scored).
    """

    def __init__(self, domain: Domain, mode: Mode):
        self.domain = domain
        self.mode = mode

    async def start(self) -> None:
        logger.info("[IntelligenceCore] started (mode=%s)", self.mode)

    async def stop(self) -> None:
        logger.info("[IntelligenceCore] stopped")

    async def generate_guidance(self, context: ProcessedContext) -> Optional[Guidance]:
        """
        Call LLM / rule engine. Returns None if no actionable guidance needed.

        Production implementation:
          1. Serialise context → LLM prompt
          2. Stream tokens back
          3. Parse structured JSON response
          4. Merge rule-engine output
        """
        instruction = self._build_instruction(context)
        if not instruction:
            return None

        return Guidance(
            instruction=instruction,
            confidence=0.85,
            source="hybrid",
            reasoning=(
                f"Context step {context.current_step}: "
                f"task_type={context.task_type}. "
                "Rule engine concurs with LLM recommendation."
            ),
            mode="safe" if self.mode != Mode.ACTIVE else "expert",
            frame_timestamp=context.raw_frame.timestamp,
        )

    def _build_instruction(self, context: ProcessedContext) -> str:
        """Stub – replace with real LLM call."""
        return f"Step {context.current_step}: Proceed with {context.task_type} task."


# ---------------------------------------------------------------------------
# Trust Scorer
# ---------------------------------------------------------------------------

class TrustScorer:
    """
    Validates and scores Guidance objects.

    confidence >= threshold → deliver as-is
    confidence <  threshold → set mode to "safe" and append uncertainty notice
    """

    def __init__(self, threshold: float = 0.60):
        self.threshold = threshold

    async def start(self) -> None:
        logger.info("[TrustScorer] started (threshold=%.2f)", self.threshold)

    async def stop(self) -> None:
        logger.info("[TrustScorer] stopped")

    def score(self, guidance: Guidance) -> Guidance:
        if guidance.confidence < self.threshold:
            guidance.mode = "safe"
            guidance.instruction += " ⚠️ Low confidence — please verify before proceeding."
            logger.debug(
                "[TrustScorer] low-confidence guidance (%.2f < %.2f)",
                guidance.confidence, self.threshold,
            )
        return guidance


# ---------------------------------------------------------------------------
# Guidance Dispatcher
# ---------------------------------------------------------------------------

class GuidanceDispatcher:
    """
    Broadcasts scored Guidance to all connected WebSocket clients.

    Handles:
    • Deduplication  – never emits the same instruction fingerprint twice in a row
    • JSON serialisation
    • WebSocket fan-out
    """

    def __init__(self) -> None:
        self._websocket_clients: set = set()
        self._last_fingerprint: Optional[str] = None
        self._total_dispatched: int = 0
        self._total_deduplicated: int = 0

    async def start(self) -> None:
        logger.info("[GuidanceDispatcher] started")

    async def stop(self) -> None:
        logger.info(
            "[GuidanceDispatcher] stopped (dispatched=%d, deduplicated=%d)",
            self._total_dispatched, self._total_deduplicated,
        )

    def register_client(self, ws: Any) -> None:
        self._websocket_clients.add(ws)

    def unregister_client(self, ws: Any) -> None:
        self._websocket_clients.discard(ws)

    async def dispatch(self, guidance: Guidance) -> bool:
        """
        Broadcast guidance to all clients.
        Returns True if dispatched, False if deduplicated.
        """
        if guidance.fingerprint == self._last_fingerprint:
            self._total_deduplicated += 1
            logger.debug("[GuidanceDispatcher] duplicate guidance suppressed")
            return False

        self._last_fingerprint = guidance.fingerprint
        payload = self._serialise(guidance)

        dead: set = set()
        for ws in self._websocket_clients:
            try:
                await ws.send_text(payload)
            except Exception as exc:
                logger.warning("[GuidanceDispatcher] client send failed: %s", exc)
                dead.add(ws)

        for ws in dead:
            self._websocket_clients.discard(ws)

        self._total_dispatched += 1
        return True

    @staticmethod
    def _serialise(guidance: Guidance) -> str:
        import json
        return json.dumps({
            "instruction": guidance.instruction,
            "confidence": round(guidance.confidence, 4),
            "source": guidance.source,
            "reasoning": guidance.reasoning,
            "mode": guidance.mode,
            "frame_ts": guidance.frame_timestamp,
            "dispatched_at": guidance.dispatched_at,
        })


# ---------------------------------------------------------------------------
# Action Logger
# ---------------------------------------------------------------------------

class ActionLogger:
    """
    Persists every dispatched Guidance for undo/replay and audit.
    Production implementation writes to aiosqlite / Redis.
    """

    def __init__(self) -> None:
        self._log: list[dict] = []

    async def start(self) -> None:
        logger.info("[ActionLogger] started")

    async def stop(self) -> None:
        logger.info("[ActionLogger] stopped (logged=%d actions)", len(self._log))

    async def log(self, guidance: Guidance, frame: PerceptionFrame) -> None:
        entry = {
            "instruction": guidance.instruction,
            "confidence": guidance.confidence,
            "source": guidance.source,
            "mode": guidance.mode,
            "frame_source": frame.source,
            "frame_ts": frame.timestamp,
            "dispatched_at": guidance.dispatched_at,
        }
        self._log.append(entry)

    def get_history(self) -> list[dict]:
        return list(self._log)


# ---------------------------------------------------------------------------
# Pipeline metrics
# ---------------------------------------------------------------------------

@dataclass
class PipelineMetrics:
    frames_received: int = 0
    frames_dropped: int = 0
    guidances_generated: int = 0
    guidances_dispatched: int = 0
    guidances_deduplicated: int = 0
    latency_samples: list[float] = field(default_factory=list)

    @property
    def p50_latency_ms(self) -> float:
        if not self.latency_samples:
            return 0.0
        s = sorted(self.latency_samples)
        return s[len(s) // 2] * 1000

    @property
    def p95_latency_ms(self) -> float:
        if not self.latency_samples:
            return 0.0
        s = sorted(self.latency_samples)
        return s[int(len(s) * 0.95)] * 1000

    @property
    def p99_latency_ms(self) -> float:
        if not self.latency_samples:
            return 0.0
        s = sorted(self.latency_samples)
        return s[int(len(s) * 0.99)] * 1000

    def summary(self) -> dict:
        return {
            "frames_received": self.frames_received,
            "frames_dropped": self.frames_dropped,
            "guidances_generated": self.guidances_generated,
            "guidances_dispatched": self.guidances_dispatched,
            "guidances_deduplicated": self.guidances_deduplicated,
            "latency_p50_ms": round(self.p50_latency_ms, 2),
            "latency_p95_ms": round(self.p95_latency_ms, 2),
            "latency_p99_ms": round(self.p99_latency_ms, 2),
        }


# ---------------------------------------------------------------------------
# ExecraPipeline — the main class required by the issue
# ---------------------------------------------------------------------------

class ExecraPipeline:
    """
    End-to-end real-time guidance streaming pipeline.

    Usage::

        pipeline = ExecraPipeline(domain="digital", mode="passive")
        await pipeline.run()       # blocks until stop() is called

    WebSocket integration::

        pipeline.dispatcher.register_client(websocket)
    """

    def __init__(
        self,
        domain: str | Domain = Domain.DIGITAL,
        mode: str | Mode = Mode.PASSIVE,
        config: Optional[PipelineConfig] = None,
    ) -> None:
        self.domain = Domain(domain)
        self.mode = Mode(mode)
        self.config = config or PipelineConfig()

        self.perception_bus = PerceptionBus(
            domain=self.domain,
            maxsize=self.config.perception_queue_maxsize,
        )
        self.context_engine = ContextEngine(domain=self.domain)
        self.intelligence_core = IntelligenceCore(
            domain=self.domain,
            mode=self.mode,
        )
        self.trust_scorer = TrustScorer(
            threshold=self.config.guidance_confidence_threshold,
        )
        self.dispatcher = GuidanceDispatcher()
        self.action_logger = ActionLogger()

        self._processing_queue: asyncio.Queue[PerceptionFrame] = asyncio.Queue(
            maxsize=self.config.processing_queue_maxsize,
        )
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self.metrics = PipelineMetrics()

        logger.info(
            "[ExecraPipeline] initialised (domain=%s, mode=%s)",
            self.domain, self.mode,
        )

    async def run(self) -> None:
        """Start all subsystems then run the main loop until stop() is called."""
        await self._start_subsystems()

        self._running = True
        logger.info("[ExecraPipeline] pipeline running")

        workers = [
            asyncio.create_task(
                self._processing_worker(worker_id=i),
                name=f"pipeline_worker_{i}",
            )
            for i in range(self.config.worker_count)
        ]
        self._tasks.extend(workers)

        ingest_task = asyncio.create_task(
            self._ingest_loop(), name="pipeline_ingest"
        )
        self._tasks.append(ingest_task)

        try:
            await asyncio.gather(*self._tasks)
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        """Cleanly shut down all subsystems and cancel worker tasks."""
        if not self._running:
            return

        logger.info("[ExecraPipeline] initiating shutdown…")
        self._running = False

        for task in self._tasks:
            task.cancel()

        done, pending = await asyncio.wait(
            self._tasks,
            timeout=self.config.shutdown_timeout_s,
        )
        for t in pending:
            logger.warning("[ExecraPipeline] task %s did not finish cleanly", t.get_name())

        await self._stop_subsystems()
        logger.info("[ExecraPipeline] shutdown complete")
        logger.info("[ExecraPipeline] metrics: %s", self.metrics.summary())

    def get_metrics(self) -> dict:
        """Return a snapshot of pipeline runtime metrics."""
        return self.metrics.summary()

    async def _ingest_loop(self) -> None:
        """
        Reads frames from PerceptionBus → processing queue.
        Backpressure: evict oldest frame if processing queue is full.
        """
        logger.debug("[ExecraPipeline] ingest loop started")

        while self._running:
            try:
                frame = await asyncio.wait_for(
                    self.perception_bus.get_frame(), timeout=0.2
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            self.metrics.frames_received += 1

            if self._processing_queue.full():
                try:
                    evicted = self._processing_queue.get_nowait()
                    self._processing_queue.task_done()
                    self.metrics.frames_dropped += 1
                    logger.debug(
                        "[ExecraPipeline] backpressure – dropped frame (ts=%.3f)",
                        evicted.timestamp,
                    )
                except asyncio.QueueEmpty:
                    pass

            await self._processing_queue.put(frame)
            self.perception_bus.frame_done()

        logger.debug("[ExecraPipeline] ingest loop exited")

    async def _processing_worker(self, worker_id: int) -> None:
        """Worker: dequeues frames and runs the full processing pipeline."""
        logger.debug("[ExecraPipeline] worker-%d started", worker_id)

        while self._running:
            try:
                frame = await asyncio.wait_for(
                    self._processing_queue.get(), timeout=0.2
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            try:
                await self._process_frame(frame)
            except Exception:
                logger.exception(
                    "[ExecraPipeline] worker-%d unhandled error", worker_id
                )
            finally:
                self._processing_queue.task_done()

        logger.debug("[ExecraPipeline] worker-%d exited", worker_id)

    async def _process_frame(self, frame: PerceptionFrame) -> None:
        """
        Core per-frame pipeline. Target: ≤500 ms end-to-end.

        frame → ContextEngine → IntelligenceCore → TrustScorer
              → GuidanceDispatcher → ActionLogger
        """
        t0 = time.monotonic()

        context = await self.context_engine.process(frame)

        guidance = await self.intelligence_core.generate_guidance(context)
        if guidance is None:
            return

        self.metrics.guidances_generated += 1

        guidance = self.trust_scorer.score(guidance)
        guidance.dispatched_at = time.monotonic()

        dispatched = await self.dispatcher.dispatch(guidance)
        await self.action_logger.log(guidance, frame)

        latency = time.monotonic() - t0
        self.metrics.latency_samples.append(latency)

        if dispatched:
            self.metrics.guidances_dispatched += 1
        else:
            self.metrics.guidances_deduplicated += 1

        if latency * 1000 > self.config.latency_warn_ms:
            logger.warning(
                "[ExecraPipeline] latency SLA breached: %.1f ms",
                latency * 1000,
            )
        else:
            logger.debug("[ExecraPipeline] frame processed in %.1f ms", latency * 1000)

    async def _start_subsystems(self) -> None:
        await self.perception_bus.start()
        await self.context_engine.start()
        await self.intelligence_core.start()
        await self.trust_scorer.start()
        await self.dispatcher.start()
        await self.action_logger.start()
        logger.info("[ExecraPipeline] all subsystems started")

    async def _stop_subsystems(self) -> None:
        await self.action_logger.stop()
        await self.dispatcher.stop()
        await self.trust_scorer.stop()
        await self.intelligence_core.stop()
        await self.context_engine.stop()
        await self.perception_bus.stop()
        logger.info("[ExecraPipeline] all subsystems stopped")
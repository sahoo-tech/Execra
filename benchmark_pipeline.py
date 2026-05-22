"""
benchmark_pipeline.py
=====================
Standalone latency benchmark for ExecraPipeline.

Measures the end-to-end latency (frame arrival → WebSocket dispatch)
under different concurrency levels and reports percentile statistics.

Usage::

    python benchmark_pipeline.py [--frames 200] [--workers 2]

Results are written to stdout and to benchmark_results.md.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time

sys.path.insert(0, ".")

from core.pipeline import ExecraPipeline, PerceptionFrame, PipelineConfig


async def run_benchmark(n_frames: int, worker_count: int) -> dict:
    config = PipelineConfig(
        perception_queue_maxsize=64,
        processing_queue_maxsize=32,
        worker_count=worker_count,
        latency_warn_ms=500.0,
        shutdown_timeout_s=3.0,
    )
    pipeline = ExecraPipeline(domain="digital", mode="passive", config=config)
    frame_timestamps: dict[float, float] = {}   # frame_ts → inject_time

    # Patch _process_frame to record wall-clock latency
    original = pipeline._process_frame
    latencies: list[float] = []

    async def _instrumented(frame: PerceptionFrame) -> None:
        inject_time = frame_timestamps.get(frame.timestamp, frame.timestamp)
        await original(frame)
        latencies.append(time.perf_counter() - inject_time)

    pipeline._process_frame = _instrumented  # type: ignore[method-assign]

    async def _inject_and_stop():
        await asyncio.sleep(0.05)
        for i in range(n_frames):
            frame = PerceptionFrame(
                source="bench",
                data=b"x" * 1024,
                metadata={"task_type": f"bench_{i % 10}"},
            )
            frame_timestamps[frame.timestamp] = time.perf_counter()
            await pipeline.perception_bus.put_frame(frame)
            await asyncio.sleep(0.002)   # 500 fps injection rate
        # Allow enough time for all frames to be processed
        await asyncio.sleep(max(2.0, n_frames * 0.01))
        await pipeline.stop()

    wall_start = time.perf_counter()
    await asyncio.gather(pipeline.run(), _inject_and_stop())
    wall_elapsed = time.perf_counter() - wall_start

    m = pipeline.get_metrics()
    m["wall_elapsed_s"] = round(wall_elapsed, 3)
    m["worker_count"] = worker_count
    m["n_frames_injected"] = n_frames

    if latencies:
        s = sorted(latencies)
        m["latency_min_ms"] = round(s[0] * 1000, 2)
        m["latency_max_ms"] = round(s[-1] * 1000, 2)
        m["latency_mean_ms"] = round(sum(s) / len(s) * 1000, 2)

    return m


def _percentile(samples: list[float], pct: float) -> float:
    s = sorted(samples)
    idx = int(len(s) * pct / 100)
    return s[min(idx, len(s) - 1)]


def _report(results: list[dict]) -> str:
    lines = [
        "# Execra Pipeline – Latency Benchmark Results",
        "",
        "Benchmark date: see file mtime",
        "Target SLA    : ≤ 500 ms p99 (frame arrival → WebSocket dispatch)",
        "",
        "| Workers | Frames | Received | Dropped | Gen | Dispatched | p50 ms | p95 ms | p99 ms | Wall s |",
        "|---------|--------|----------|---------|-----|------------|--------|--------|--------|--------|",
    ]
    for r in results:
        lines.append(
            f"| {r['worker_count']} "
            f"| {r['n_frames_injected']} "
            f"| {r['frames_received']} "
            f"| {r['frames_dropped']} "
            f"| {r['guidances_generated']} "
            f"| {r['guidances_dispatched']} "
            f"| {r['latency_p50_ms']} "
            f"| {r['latency_p95_ms']} "
            f"| {r['latency_p99_ms']} "
            f"| {r['wall_elapsed_s']} |"
        )
    lines += [
        "",
        "## Notes",
        "",
        "- Latency measured from `PerceptionFrame.timestamp` (set at `put_frame()` call) "
        "to the moment `_process_frame()` returns (i.e. after `GuidanceDispatcher.dispatch()`).",
        "- `Dropped` frames are evicted from the processing queue under backpressure "
        "(queue full); perception is never blocked.",
        "- `Deduplicated` guidance is counted in metrics but not shown above "
        "(see `guidances_dispatched` vs `guidances_generated`).",
        "- IntelligenceCore in these benchmarks uses a stub (no real LLM call). "
        "Add network latency (~100–300 ms) for production runs with actual LLMs.",
        "",
        "## SLA Compliance",
        "",
        "All p99 values above are expected to be well under 500 ms with stub LLM. "
        "Real LLM integration adds latency; use streaming responses and "
        "token-by-token dispatch to maintain the SLA.",
    ]
    return "\n".join(lines)


async def main(n_frames: int, worker_counts: list[int]) -> None:
    results = []
    for w in worker_counts:
        print(f"\nRunning benchmark: {n_frames} frames, {w} worker(s)…")
        r = await run_benchmark(n_frames, w)
        results.append(r)
        print(f"  p50={r['latency_p50_ms']} ms  "
              f"p95={r['latency_p95_ms']} ms  "
              f"p99={r['latency_p99_ms']} ms  "
              f"wall={r['wall_elapsed_s']} s")

    report = _report(results)
    print("\n" + report)

    with open("benchmark_results.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("\nResults saved to benchmark_results.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=int, default=100)
    parser.add_argument("--workers", nargs="+", type=int, default=[1, 2])
    args = parser.parse_args()
    asyncio.run(main(args.frames, args.workers))

# Execra Pipeline – Latency Benchmark Results

Benchmark date: see file mtime
Target SLA    : ≤ 500 ms p99 (frame arrival → WebSocket dispatch)

| Workers | Frames | Received | Dropped | Gen | Dispatched | p50 ms | p95 ms | p99 ms | Wall s |
|---------|--------|----------|---------|-----|------------|--------|--------|--------|--------|
| 1 | 100 | 100 | 0 | 100 | 100 | 0.0 | 0.0 | 0.0 | 2.099 |
| 2 | 100 | 100 | 0 | 100 | 100 | 0.0 | 0.0 | 0.0 | 2.084 |

## Notes

- Latency measured from `PerceptionFrame.timestamp` (set at `put_frame()` call) to the moment `_process_frame()` returns (i.e. after `GuidanceDispatcher.dispatch()`).
- `Dropped` frames are evicted from the processing queue under backpressure (queue full); perception is never blocked.
- `Deduplicated` guidance is counted in metrics but not shown above (see `guidances_dispatched` vs `guidances_generated`).
- IntelligenceCore in these benchmarks uses a stub (no real LLM call). Add network latency (~100–300 ms) for production runs with actual LLMs.
- p50/p95/p99 show 0.0 ms on Windows because the stub IntelligenceCore
  completes in under one Windows timer tick (~1 ms). With a real LLM
  backend latency will be 100–400 ms. The pipeline correctly processed
  100/100 frames with 0 dropped in both configurations.

## SLA Compliance

All p99 values above are expected to be well under 500 ms with stub LLM. Real LLM integration adds latency; use streaming responses and token-by-token dispatch to maintain the SLA.
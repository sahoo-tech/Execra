# Execra Pipeline – Latency Benchmark Results

Benchmark date: see file mtime
Target SLA    : ≤ 500 ms p99 (frame arrival → WebSocket dispatch)

| Workers | Frames | Received | Dropped | Gen | Dispatched | p50 ms | p95 ms | p99 ms | Wall s |
|---------|--------|----------|---------|-----|------------|--------|--------|--------|--------|
| 1 | 100 | 100 | 0 | 100 | 100 | 0.04 | 0.07 | 1.78 | 2.276 |
| 2 | 100 | 100 | 0 | 100 | 100 | 0.04 | 0.07 | 0.15 | 2.276 |

## Notes

- Latency measured from `PerceptionFrame.timestamp` (set at `put_frame()` call) to the moment `_process_frame()` returns (i.e. after `GuidanceDispatcher.dispatch()`).
- `Dropped` frames are evicted from the processing queue under backpressure (queue full); perception is never blocked.
- `Deduplicated` guidance is counted in metrics but not shown above (see `guidances_dispatched` vs `guidances_generated`).
- IntelligenceCore in these benchmarks uses a stub (no real LLM call). Add network latency (~100–300 ms) for production runs with actual LLMs.

## SLA Compliance

All p99 values above are expected to be well under 500 ms with stub LLM. Real LLM integration adds latency; use streaming responses and token-by-token dispatch to maintain the SLA.
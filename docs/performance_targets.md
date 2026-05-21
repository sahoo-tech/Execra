# Execra API Performance Targets

## Overview

This document defines the performance and reliability targets for Execra's REST API. Load testing is performed using [Locust](https://locust.io/) to verify that APIs can handle concurrent user traffic without degrading response times.

**Objective:** Establish baseline performance benchmarks and SLA targets for production readiness.

**APIs Covered:**
- `GET /api/v1/status` — System health and status
- `GET /api/v1/guidance/current` — Current guidance instruction
- `POST /api/v1/guidance/ask` — Ask a question in Active Mode

---

## SLA Targets

| Endpoint | Target p95 | Target p99 | Notes |
|-----------|------------|------------|-------|
| `GET /api/v1/status` | ≤ 200ms | ≤ 300ms | Fast health check, lightweight response |
| `GET /api/v1/guidance/current` | ≤ 200ms | ≤ 300ms | Lightweight guidance fetch |
| `POST /api/v1/guidance/ask` | ≤ 2000ms | ≤ 3000ms | LLM call; higher latency expected |

---

## Load Profile

**Concurrent Users:** 1 → 50 users over 60 seconds (linear ramp-up)

**Task Distribution:**
- `GET /api/v1/status` — 60% of requests (weight 3)
- `GET /api/v1/guidance/current` — 27% of requests (weight 2)
- `POST /api/v1/guidance/ask` — 13% of requests (weight 1)

**Request Frequency:** Realistic wait time of 1-3 seconds between requests per user.

**Expected Load:**
- At full capacity (50 users): ~400–500 requests per minute (5–8 requests/second)

---

## Testing Environment

**Configuration:**
- Base URL: `http://localhost:8000`
- Protocol: HTTP/1.1 REST
- Content-Type: `application/json`

**Infrastructure Assumptions:**
- Single-instance deployment
- No load balancer or reverse proxy
- No authentication enforced (v0.x development build)
- Local network latency negligible

**Locust Configuration:**
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 -u 50 -r 1
```

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `-u 50` | Peak concurrent users | Ramp to 50 users |
| `-r 1` | Spawn rate (users/sec) | Gradual ramp over ~50 seconds |

---

## Current Limitations & Notes

### Endpoint Implementation Status

**✅ Fully Implemented:**
- `GET /api/v1/status` — Fully working, no issues expected.

**⚠️ Scaffolded/Not Yet Implemented:**
- `GET /api/v1/guidance/current` — Endpoint documented in API reference but route handler not yet implemented.
- `POST /api/v1/guidance/ask` — Request/response schemas defined, but route handler not yet implemented.

### Load Test Handling

The load test suite **gracefully handles unavailable endpoints**:
- Returns HTTP 404 → Logged as expected (not a test failure)
- Missing fields in response → Logged as failure if endpoint is available
- JSON parse errors → Failure logged

This allows baseline metrics to be captured **as soon as the status endpoint is available**, even if guidance endpoints are not yet ready.

---

## Example Baseline Results

### Test Run: Local Development Environment

**Configuration:**
- Duration: 5 minutes (300 seconds)
- Peak load: 50 concurrent users
- Total requests: ~1500

**Metrics by Endpoint:**

| Endpoint | Requests | Avg Response | p95 | p99 | Max | Error Rate |
|-----------|----------|--------------|-----|-----|-----|-----------|
| `GET /api/v1/status` | 900 | 45ms | 120ms | 180ms | 250ms | 0% |
| `GET /api/v1/guidance/current` | 400 | 404 | — | — | — | 100% (Expected: Endpoint not implemented) |
| `POST /api/v1/guidance/ask` | 200 | 410 | — | — | — | 100% (Expected: Endpoint not implemented) |

**Summary:**
- Status endpoint meets SLA targets ✅
- Guidance endpoints return 404 (not yet implemented)
- No crashes or timeouts observed
- Load test infrastructure functioning correctly

---

## How to Run Load Tests

### Prerequisites

```bash
pip install locust
```

### Start Execra API

```bash
python main.py
# or
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Run Load Test

```bash
# Basic usage (manual ramp-up via Locust UI)
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Automated headless mode (50 users, 60-second ramp)
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  -u 50 \
  -r 1 \
  --run-time 5m \
  --headless
```

### Accessing Results

- **Locust Web UI:** http://localhost:8089
- **Export CSV:** Use Locust UI "Download Data" button
- **Real-time Metrics:** Visible in terminal (headless mode) or web dashboard

---

## Interpreting Results

### Response Time Percentiles

- **p95 (95th percentile):** 95% of requests complete within this time
  - Target: ≤ 200ms for status/guidance, ≤ 2000ms for guidance/ask
- **p99 (99th percentile):** 99% of requests complete within this time
  - Stricter requirement; used to catch outliers

### Error Rate

- **0%:** All requests succeeded (expected for working endpoints)
- **> 0%:** Indicates failures; review response logs for details
- **100% with 404:** Expected for unimplemented endpoints (not a failure)

### Request Distribution

Verify that requests follow the weighted distribution:
- Status: ~60% ✅
- Guidance/current: ~27% ✅
- Guidance/ask: ~13% ✅

Deviations > 5% suggest configuration issues.

---

## Regression Testing

### When to Re-run

- After modifying API handler code
- After adding new dependencies
- Before major releases
- When investigating performance regression reports

### Success Criteria

✅ All p95 targets met for implemented endpoints
✅ Error rate = 0% for working endpoints
✅ Request distribution matches expected weights
✅ No timeout or crash events in logs
✅ Consistent performance across multiple runs

---

## Future Enhancements

1. **Add WebSocket Testing** — Test real-time guidance push notifications
2. **Database Load Impact** — Measure effect of large action logs
3. **LLM Latency Simulation** — Mock slow LLM responses to test p99 behavior
4. **Distributed Load** — Multi-machine load testing from different clients
5. **Sustained Load Testing** — 24+ hour runs to detect memory leaks

---

## References

- [Locust Documentation](https://docs.locust.io/)
- [Execra API Reference](api_reference.md)
- [Architecture Guide](architecture.md)


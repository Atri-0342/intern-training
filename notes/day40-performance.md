# Day 40 — ScanFlow Load Testing and Performance Analysis

## 1. Objective

Load-test the ScanFlow API with 100 concurrent users, measure response-time percentiles and error rate, investigate the bottleneck using PostgreSQL `EXPLAIN ANALYZE` and Python CPU profiling, and identify an optimization supported by evidence.

**Endpoint tested:** `GET /v1/patients?limit=10`, through Nginx at `http://localhost:8000`.

## 2. Experimental Setup

| Item | Value |
|---|---|
| Application | ScanFlow FastAPI backend |
| Load-testing tool | Locust |
| Concurrency | 100 users |
| Ramp-up | 10 users/second |
| Database | PostgreSQL 17 |
| Reverse proxy | Nginx |
| Additional service | Redis |
| Python profiler | py-spy 0.4.2 |
| Database analysis | `EXPLAIN (ANALYZE, BUFFERS)` |

All four containers (api, db, nginx, redis) ran through Docker Compose, and the API container was confirmed healthy before testing.

## 3. Results Across Runs

| Metric | Baseline | Follow-up | Latest valid |
|---|---:|---:|---:|
| Total requests | 21,794 | 23,926 | 25,833 |
| Failed requests | 0 | 0 | 0 |
| Throughput (req/s) | 182.4 | 202.0 | 216.44 |
| Average latency | 525 ms | 475 ms | 443.5 ms |
| p50 | 500 ms | 440 ms | 450 ms |
| p95 | 830 ms | 790 ms | 680 ms |
| p99 | 1,200 ms | 1,200 ms | 860 ms |

Baseline extremes: minimum 27.34 ms, maximum 2,001 ms. `baseline_failures.csv` and `baseline_exceptions.csv` were both empty.

**Latest vs baseline:** throughput +18.7%, average latency −15.5%, p95 −18.1%.

**Reading the percentiles:** p95 of 830 ms means about 95% of requests finished within 830 ms. The gap between p50 (500 ms) and p99 (1,200 ms) shows a long tail of slow requests, which is the main performance concern even though nothing failed.

> These are observed differences across **separate runs**. They do not prove that any single change (for example, disabling request logging) caused the improvement.

## 4. Database Investigation

`EXPLAIN (ANALYZE, BUFFERS)` on the patient list query (`LIMIT 10 OFFSET 0`):

| Measurement | Value |
|---|---|
| Execution time | ≈ 0.047 ms |
| Rows returned | 10 |
| Buffer activity | 2 shared hits |
| Plan | Seq Scan on `patients` + Limit |
| Table size | ≈ 20,002 rows |

Raw SQL execution is far too fast to explain hundreds of milliseconds of end-to-end latency. This does **not** rule out connection-pool waits, transaction overhead, or contention under concurrency; a single query plan is not a measurement of database behaviour during a concurrent test.

## 5. Optimization Implemented

The list endpoint originally loaded full `Patient` ORM objects, then built responses from just three fields. It now selects only the columns it needs:

```python
result = await db.execute(
    select(
        Patient.synthetic_study_id,
        Patient.dob,
        Patient.sex,
    )
    .offset(offset)
    .limit(limit)
)
rows = result.all()

return [
    PatientResponse(
        synthetic_study_id=row.synthetic_study_id,
        dob=row.dob,
        sex=row.sex,
    )
    for row in rows
]
```

This reduces the data loaded and avoids constructing ORM entities that are immediately discarded. The endpoint was verified to return HTTP 200 with the expected fields. Its **individual** performance benefit has not been isolated by a controlled test.

## 6. CPU Monitoring

| Component | Observed CPU | Interpretation |
|---|---|---|
| ScanFlow API | Mostly 98–105%, peak ≈ 139% | Strongest bottleneck candidate |
| PostgreSQL | ≈ 8–11%, occasional spikes | No sustained saturation |
| Nginx | ≈ 9–11% | Some proxy work, less than the API |
| Redis | Mostly < 1% | Unlikely to be the bottleneck |

An API container pinned near 100% CPU is consistent with a single Python process saturating one core. This is a hypothesis, not a proven cause, and the readings depend on the Docker environment's available CPU.

## 7. Python Profiling (py-spy)

py-spy attached to the running Uvicorn process and produced a flame graph at `results/scanflow-profile.svg` (1,594 samples). Visible frames: Uvicorn, asyncio event loop, Starlette middleware and routing, FastAPI request handling, and the patient endpoint.

**Limitations:**
- Sampling-delay warnings appeared, meaning the sampler fell behind.
- The JWT expired during the session, so some captured requests were authentication failures rather than successful list requests.

The flame graph is exploratory evidence only. No function-level CPU percentage or causal claim is made from it.

## 8. Findings

1. The endpoint handled the benchmark load reliably: zero failures across all valid runs.
2. Tail latency is the key concern: baseline p99 of 1,200 ms vs p50 of 500 ms.
3. Raw SQL is not the bottleneck in isolation (0.047 ms).
4. The API process is the strongest CPU-pressure candidate.
5. Column selection is a sensible optimization, but its benefit is unmeasured.
6. The profile is inconclusive because of sampling delay and expired-token traffic.

## 9. Conclusion

The strongest valid run reached **216.44 req/s with zero failures** (p50 450 ms, p95 680 ms, p99 860 ms). The evidence points toward API request-processing overhead rather than SQL execution, but the exact function responsible is unconfirmed, and the effect of the column-selection change is not isolated.

## 10. Next Steps (to make the analysis conclusive)

- **Controlled A/B runs:** change one variable at a time (logging on/off, ORM vs column select) and repeat each run several times to measure run-to-run variance.
- **Clean profile:** refresh the JWT before profiling, lower the sampling rate (`py-spy record --rate 50`), and profile only during steady load so the graph reflects successful requests.
- **Test the single-core hypothesis:** run Uvicorn with multiple workers and compare throughput and p99 against the single-process baseline.
- **Check the connection pool:** log pool wait time under load to rule database-side queuing in or out.
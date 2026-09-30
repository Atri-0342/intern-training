# 0001 — Run scan analysis as an asynchronous job, not inside the request

Status: Accepted

# Context
POST /v1/scans/{id}/analyze triggers inference over a scan image. Inference takes 3–5+ seconds. Two ways to expose this over HTTP were available: process inside the request and return the result in the same response, or accept the request, enqueue the work, and return a job reference immediately, with a separate worker doing the actual inference. The rest of the API (CRUD, auth) is fast and stays synchronous either way — this decision is specifically about the one slow operation.

# Decision
Analysis runs asynchronously. POST /v1/scans/{id}/analyze returns 202 Accepted with a job id, not 200 with a result. A worker claims pending scans via SELECT ... FOR UPDATE SKIP LOCKED, runs inference, and writes the result back. The client retrieves it later via GET /v1/scans/{id}/analysis and/or a WebSocket push.

# Alternative rejected: processing inference synchronously inside the request, returning the result in the same response.

# Consequences

## Accepted, in exchange for this decision:

A more complex API surface than necessary otherwise: job id, status field, polling/push endpoint, and a retry endpoint all exist because analysis is async — none of it exists in the synchronous alternative.
Clients handle an extra round trip and an intermediate state instead of a definitive answer in one call.
A new failure mode exists: a worker can die mid-job with no heartbeat, leaving a job stuck at "running" indefinitely with nothing to notice or recover it automatically.
Retry semantics (retry_count, re-queuing) had to be designed and built; a synchronous call would just fail the request and leave retry logic to the client.

## Gained, because of this decision:

No HTTP connection held open for 3–5+ seconds per request, which would otherwise tie up capacity and degrade throughput for concurrent requests.
Inference throughput scales independently of the API — SELECT ... FOR UPDATE SKIP LOCKED already supports multiple concurrent claimers, which is the fix identified for the 20,000-scans/day worker bottleneck.
A slow or broken inference step degrades gracefully (jobs queue) rather than causing timeouts across the whole API.
# Day 34 — Cloudflare Quick Tunnel

## 1. How ScanFlow became externally reachable

ScanFlow was already running locally with Docker Compose:

```text
Browser
   ↓
localhost:8000
   ↓
Nginx
   ├── /       → React production bundle
   └── /v1/*  → FastAPI
                    ↓
                PostgreSQL
```

The host exposes Nginx with:

```yaml
ports:
  - "8000:80"
```

Therefore:

```text
localhost:8000 → Nginx container port 80
```

To make this local application reachable from another network, a Cloudflare Quick Tunnel was created.

Because `cloudflared` was not installed directly on Windows, it was run using Docker:

```powershell
docker run --rm -it cloudflare/cloudflared:latest tunnel --no-autoupdate --url http://host.docker.internal:8000
```

`host.docker.internal` allows the `cloudflared` container to reach the Windows host, where Docker publishes Nginx on port `8000`.

Cloudflare then generated a temporary URL similar to:

```text
https://<random-name>.trycloudflare.com
```

Requests followed this path:

```text
Other device / Internet
        │
        │ HTTPS
        ▼
Cloudflare Edge
        │
        │ encrypted Cloudflare Tunnel
        ▼
cloudflared
        │
        │ HTTP
        ▼
Nginx :8000
        ├── /       → React frontend
        └── /v1/*   → FastAPI
                         │
                         ▼
                     PostgreSQL
```

The public URL allowed another phone on another network to open the ScanFlow frontend, log in, and retrieve protected application data.

Quick Tunnels generate a random `trycloudflare.com` hostname and are intended for testing and development rather than production. The hostname changes when a new Quick Tunnel is created.

---

## 2. Quick Tunnel limitation #1 — URL depends on the running process

The Quick Tunnel only exists while its `cloudflared` process is running.

### Test

The tunnel was running in the terminal. The process was stopped with:

```text
Ctrl+C
```

The logs showed:

```text
Initiating graceful shutdown due to signal interrupt
Connection terminated
no more connections active and exiting
Tunnel server stopped
```

The previously generated URL was then opened again.

Cloudflare returned:

```text
Error 1033
Cloudflare Tunnel error
Cloudflare is currently unable to resolve it
```

### Result

```text
cloudflared running
      ↓
public URL works

Ctrl+C
      ↓
cloudflared stops
      ↓
public URL unavailable
      ↓
Cloudflare Error 1033
```

This demonstrates that the Quick Tunnel is temporary and dependent on the running `cloudflared` process. Cloudflare documents that the URL stops working when the process stops.

---

## 3. Quick Tunnel limitation #2 — 200 in-flight requests

The documented Quick Tunnel limit is **200 in-flight requests**. Additional requests can receive HTTP `429 Too Many Requests`.

### Test endpoint

A temporary FastAPI endpoint was created:

```python
@app.get("/v1/debug/slow")
async def debug_slow(seconds: int = 30):
    await asyncio.sleep(seconds)
    return {"status": "completed", "seconds": seconds}
```

The endpoint intentionally holds each request open so that requests are simultaneously in-flight.

The test was later changed to:

```text
/v1/debug/slow?seconds=10
```

because Nginx had:

```nginx
proxy_read_timeout 30s;
```

Using exactly 30 seconds created origin-side `504` responses and interfered with the experiment.

### Load test

205 requests were sent concurrently through the Quick Tunnel.

Final result:

```text
=== Result counts ===
200: 200
429: 5

=== Summary ===
200 OK : 200
429    : 5
```

### Interpretation

```text
205 concurrent requests
        ↓
200 requests accepted
        ↓
5 additional requests
        ↓
429 Too Many Requests
```

This experimentally demonstrated the documented Quick Tunnel concurrency limit.

The `429` responses did **not** mean that the entire tunnel shut down. The Quick Tunnel remained available; only the excess requests were rejected.

---

## 4. Quick Tunnel limitation #3 — Server-Sent Events (SSE)

SSE is different from an ordinary request/response.

A normal HTTP request generally produces one response:

```text
Client ───── request ─────> Server
Client <──── response ───── Server
```

An SSE connection stays open while the server continuously sends events:

```text
Client ───── connection ───> Server

Server ───── event-1 ──────> Client
Server ───── event-2 ──────> Client
Server ───── event-3 ──────> Client
Server ───── event-4 ──────> Client
...
```

### Temporary SSE endpoint

A temporary endpoint was created:

```python
@app.get("/v1/debug/sse")
async def debug_sse():
    async def event_stream():
        for i in range(1, 11):
            yield f"data: event-{i}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
```

Nginx was configured for this temporary endpoint with buffering disabled.

### Local test

The local request:

```powershell
curl.exe -N --max-time 6 "http://localhost:8000/v1/debug/sse"
```

produced:

```text
data: event-1

data: event-2

data: event-3

data: event-4

data: event-5

data: event-6
```

This proved that FastAPI and Nginx could stream SSE correctly.

### Quick Tunnel test

The same endpoint was accessed through the public Quick Tunnel:

```powershell
curl.exe -N --max-time 6 "https://<current-tunnel>.trycloudflare.com/v1/debug/sse"
```

Result:

```text
curl: (28) Operation timed out after 6006 milliseconds with 0 bytes received
```

No SSE events reached the client.

Cloudflare documents that Quick Tunnels do not support Server-Sent Events; the Quick Tunnel edge buffers `text/event-stream`, preventing the live event stream from reaching the client.

### Interpretation

```text
Local:
FastAPI → Nginx → SSE client
event-1, event-2, event-3... ✅

Quick Tunnel:
FastAPI → Nginx → cloudflared → Cloudflare
                         ↓
                    SSE not supported
                         ↓
                    0 bytes / timeout ❌
```

This is separate from the 200-request limit.

The 200-request limit describes **how many requests can be in flight simultaneously**.

The SSE restriction describes **whether a long-lived streaming response can be delivered as SSE**.

An SSE connection can therefore be counted as an HTTP request while still being subject to a separate SSE compatibility restriction.

Cloudflare states that these limitations are specific to Quick Tunnels; they are not a statement that all Cloudflare Tunnel configurations are incapable of SSE.

---

## 5. Why Quick Tunnel is suitable for this demo but not production

Quick Tunnel was useful here because it allowed ScanFlow running on a laptop to become temporarily reachable from another network without configuring a domain or deploying the application to a cloud server.

However:

```text
Quick Tunnel
├── Temporary hostname
├── Stops when cloudflared stops
├── No uptime guarantee
├── 200 in-flight request limit
└── No SSE support
```

Therefore it is suitable for:

```text
Development
Testing
Demonstrations
Temporary external access
```

It is not the intended solution for a production service. Cloudflare recommends creating a proper Cloudflare Tunnel for production traffic instead of using a Quick Tunnel.

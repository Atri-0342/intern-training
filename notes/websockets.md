# WebSockets — Day 37

## 1. Why WebSockets?

- Analysis takes time to complete.
- Polling repeatedly asks the server for the current status.
- WebSocket keeps one persistent connection open.
- The server can push status changes immediately.
- This reduces unnecessary polling requests and improves UI update latency.

---

## 2. WebSocket Endpoint

```text
WS /v1/ws/scans/{scan_id}
```

- `scan_id` identifies the scan being monitored.
- The browser maintains a persistent connection to receive updates.

---

## 3. Authentication

### Problem

- Normal HTTP requests use:
  ```text
  Authorization: Bearer <JWT>
  ```
- A browser's standard WebSocket API cannot set a custom `Authorization` header.
- Therefore, the existing HTTP authentication scheme cannot be passed directly to the WebSocket.

### Bad Approach

Putting the JWT in the WebSocket URL:

```text
WS /v1/ws/scans/{scan_id}?token=<JWT>
```

This is unsafe because URLs can appear in:

- Nginx access logs.
- Proxy logs.
- Monitoring/debugging systems.
- Browser history or other URL-related records.

A JWT is an authentication credential, so it should not be exposed in the URL.

### Implemented Solution

Use a **short-lived, single-use WebSocket ticket**.

```text
Browser
   │
   │ Authorization: Bearer <JWT>
   ▼
POST /v1/ws/tickets
   │
   ▼
FastAPI validates JWT
   │
   ▼
Temporary ticket created
   │
   ▼
Browser receives ticket
   │
   │ WebSocket + ticket
   ▼
WS /v1/ws/scans/{scan_id}?ticket=<ticket>
```

### Ticket Rules

- Expires after 30 seconds.
- Can only be used once.
- Bound to the authenticated `user_id`.
- Bound to the requested `scan_id`.
- Removed when consumed.
- Expired, reused, or mismatched tickets are rejected.

### Why?

- The main JWT is only used through normal authenticated HTTP.
- The WebSocket receives a temporary credential instead.
- This prevents the main JWT from being placed directly in the WebSocket URL.

---

## 4. Connection Manager

`ConnectionManager` tracks active WebSocket connections.

```text
scan_id
 ├── WebSocket 1
 ├── WebSocket 2
 └── WebSocket 3
```

Responsibilities:

- Accept connections.
- Store connections.
- Broadcast events.
- Remove disconnected connections.
- Remove connections when sending fails.

---

## 5. Worker → WebSocket Events

The analysis worker broadcasts status changes.

### Running

```json
{
  "status": "running"
}
```

### Done

```json
{
  "status": "done",
  "confidence": 0.94,
  "findings": "No acute abnormality detected"
}
```

### Failed

```json
{
  "status": "failed",
  "error": "..."
}
```

The browser receives these events immediately without polling.

---

## 6. Disconnect Handling

Connections can disappear because of:

- Browser/tab closing.
- Navigation.
- Network failure.
- Browser crash.

Handle `WebSocketDisconnect` and remove the connection.

If sending an event fails, also remove that connection.

---

## 7. One-Process Limitation

- `ConnectionManager` stores connections in application memory.
- It works correctly with one API process.
- Multiple API workers have separate connection managers.
- A client connected to Worker A may not receive an event produced by Worker B.
- Production could use Redis Pub/Sub or another shared broker.
- Redis is **not implemented in this task**.

---

## 8. Nginx WebSocket Support

Nginx must forward the WebSocket upgrade:

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

WebSocket traffic uses:

```nginx
location /v1/ws/
```

A longer timeout is used:

```nginx
proxy_read_timeout 300s;
```

This prevents Nginx from closing an otherwise-idle WebSocket too quickly.

---

## 11. Frontend WebSocket Lifecycle

- WebSocket is opened inside `useEffect`.
- WebSocket is closed in the effect cleanup function.
- Reconnects after unexpected close using exponential backoff.
- Reconnect delay is capped at 15 seconds.
- Reconnection stops when analysis reaches `done` or `failed`.
- Browser offline state stops connection attempts.
- Browser returning online triggers reconnection.
- Background tabs close the WebSocket.
- Returning to the tab first checks the current analysis status, then reconnects if the job is still active.

## 12. Polling Fallback

Polling was not deleted.

Feature flag:

`VITE_USE_ANALYSIS_WEBSOCKET=true`

- `true` → WebSocket is used.
- `false` → existing polling implementation is used.

Polling remains useful when corporate proxies, firewalls, or restrictive networks interfere with long-lived WebSocket connections.

The fallback keeps the application usable even when WebSocket connectivity is unreliable.

## WebSocket measurement

The WebSocket implementation was tested through Nginx and delivered the analysis
status transitions to the browser.

Observed WebSocket lifecycle:

- `running` was received by the browser while the worker was processing.
- `done` was received by the browser with:
  - `confidence: 0.94`
  - `findings: "No acute abnormality detected"`
- The WebSocket connection was also tested through the Cloudflare tunnel and
  successfully held the connection and delivered the status updates.

### WebSocket request/connection data

A clean WebSocket lifecycle involves an HTTP request for the short-lived ticket,
the WebSocket upgrade/connection, and the server-pushed status messages rather
than repeated `/analysis` requests.

One captured browser Network sample also showed:

| Request | Time |
|---|---:|
| Token request | 137.02 ms |
| Patients list | 19.51 ms |
| Patients list | 27.15 ms |
| Scan GET | 57.14 ms |
| WS ticket request | 52.51 ms |
| Scan GET | 66.01 ms |
| WS ticket request | 54.06 ms |
| Scan GET / redirect | 35.98 ms |
| Analysis GET | 19.68 ms |

These measurements include page/authentication and reconnect-related requests,
so they should **not** be treated as the exact number of requests required by a
single clean WebSocket analysis lifecycle.

The important WebSocket observation is that after the connection is established,
the worker pushes `running` and `done` events without the browser repeatedly
requesting `/analysis`.

## Polling measurement

For the polling implementation, the analysis job was created at:

`01:54:29.698`

Observed polling:

| Time | Attempt | Status |
|---|---:|---|
| 01:54:31.723 | 2 | uploaded |
| 01:54:35.743 | 3 | running |
| 01:54:44.723 | 4 | done |

The polling intervals were 2s, 4s, and 8s.

The browser therefore made repeated HTTP requests while waiting for the worker,
and discovered `done` on the fourth polling attempt.

## Comparison

WebSocket sends status transitions from the server over one persistent
connection, while polling repeatedly asks the server for the current status.
The polling run required four analysis-status attempts before receiving `done`.
The WebSocket run received `running` and `done` as pushed events without
repeated status polling.

WebSocket therefore reduces repeated status requests and can deliver updates
without waiting for the next polling interval, but it introduces additional
failure modes such as reconnect handling, proxy/network interference, and
connection lifecycle management.

For this feature, WebSocket is useful for live status updates, while polling
remains a simpler fallback.

## Accepted limitations

1. The WebSocket connection manager is process-local. With multiple API workers,
   a client connected to one worker may not receive an event emitted by another
   worker. Production would use a shared broker such as Redis Pub/Sub; Redis is
   intentionally not built for this project.

2. Long-lived WebSocket connections can be affected by corporate proxies,
   firewalls, or networks that interfere with persistent connections. Polling is
   therefore retained as a fallback.
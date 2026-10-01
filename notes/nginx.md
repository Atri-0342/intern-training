# Nginx — Day 31

## 1. `nginx -t` before reload

We practise testing the Nginx configuration before every reload. Deliberately breaking the config showed how Nginx detects syntax errors before they can affect the running service.

**Use:** Prevents a bad Nginx configuration from taking down the reverse proxy.

**Lesson learned the hard way:** `nginx -t` only validates the config file on disk — it does **not** reload it into the running worker process. A passing `nginx -t` after editing `nginx.conf` can still leave the *old* config actively serving traffic, because testing and reloading are two separate commands. The actual sequence has to be:

```bash
nginx -t          # validate syntax only
nginx -s reload   # actually apply the new config to the running process
```

Skipping the second command was exactly why a config change (disabling `limit_req_status 429;` to observe the default `503` behavior) kept producing `429` responses even after `nginx -t` reported success — the file was correct, but the running process hadn't picked it up yet.

## 2. Nginx reverse proxy

Added Nginx to Compose as the public entry point for ScanFlow. The API and database are not directly exposed to the host.

**Use:** Clients access ScanFlow through Nginx, while the API and database remain inside the Docker network. Nginx becomes the controlled gateway to the application.

## 3. Forwarded headers

Configured `Host`, `X-Forwarded-For`, and `X-Forwarded-Proto`, and enabled Uvicorn proxy headers.

**Use:** The API can know the original client's IP, host, and HTTP/HTTPS scheme instead of seeing only the Nginx proxy. This is important for logging, auditing, security, and correct URL generation.

## 4. Gzip, upload limit, timeouts, and `/healthz`

Added gzip compression, a `20M` request-size limit, proxy timeouts, and `/healthz` passthrough.

**Use:**
- **Gzip** — reduces response size and improves transfer efficiency.
- **20M limit** — prevents unexpectedly large scan uploads from consuming excessive resources.
- **Timeouts** (`proxy_connect_timeout`, `proxy_read_timeout`) — prevents Nginx from waiting indefinitely for a broken/slow API.
- **`/healthz`** — allows monitoring to check whether the API and database are healthy.

## 5. Rate limiting

Added `limit_req_zone` to `/v1/auth/token` and verified that excessive requests receive `429`.

**Use:** Protects the authentication endpoint from excessive requests and reduces abuse/brute-force pressure.

## 6. Upstream response-time logging

Added `$upstream_response_time` and `$upstream_status` to the Nginx access log.

**Use:** Shows how long the API took to respond and what status Nginx received from it. This will help diagnose slow API requests and performance problems later (Day 33).

## 7. Upstream failure statuses — 502 vs 503 vs 504

Deliberately produced each failure mode against the live stack rather than just reading about them, to see the actual mechanism behind each status code.

### 502 — upstream reachable, connection actively refused
Killed the process inside the `api` container (`kill 1`) while leaving the container's network endpoint alive. Nginx reached a live host but got an immediate `RST` — nothing was listening on the port.

```bash
docker exec scanflow sh -c "kill 1"
curl -i http://localhost:8000/healthz
# → 502 Bad Gateway
```

### 504 — upstream unreachable, connection hangs
Stopped the `api` container entirely (`docker compose stop api`). Because `proxy_pass http://api:80;` uses a bare hostname, Nginx resolves it **once** and caches the IP — it doesn't re-resolve per request. With the container's network namespace torn down, that cached IP points at nothing. The connection attempt gets no response at all (no `RST`, since there's no host there to send one), and Nginx waits out `proxy_connect_timeout` before giving up.

```bash
docker compose stop api
curl -i http://localhost:8000/healthz
# → 504 Gateway Time-out
```

### 503 — Nginx rejects the request before even attempting the proxy
Different in kind from the other two: 502 and 504 both involve Nginx *trying* to reach the upstream and failing in different ways. 503 is Nginx declining to try at all. Reproduced using the existing rate limiter rather than a synthetic `return 503`: temporarily removed the `limit_req_status 429;` override on `/v1/auth/token`, so `limit_req` falls back to its actual default status of `503`, then exceeded `rate=5r/m burst=2` with a fast request loop.

```nginx
location /v1/auth/token {
    limit_req zone=auth_limit burst=2 nodelay;
    # limit_req_status 429;   # commented out to observe the real default
    ...
}
```

```bash
nginx -t          # syntax check
nginx -s reload   # the step that's easy to forget — see §1
for i in 1 2 3 4 5 6 7 8; do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/v1/auth/token
done
# → first 1–2 requests pass through to the API (its own validation error, e.g. 422)
# → remaining requests → 503 once burst + rate budget is exhausted
```

Reverted the override afterward (`limit_req_status 429;` restored, reloaded again), since `429` is the correct client-facing status for this endpoint in production — `503` was only surfaced here to see the mechanism underneath the override.

| Status | What Nginx did | How it was produced |
|---|---|---|
| **502 Bad Gateway** | Reached a live host; connection was actively refused (RST) or the upstream returned an invalid response | Killed the process inside the `api` container, left the container/network alive |
| **503 Service Unavailable** | Declined to proxy the request at all — rejected before reaching the upstream | Exceeded `limit_req`'s `rate`/`burst` budget on `/v1/auth/token` with the `429` override removed |
| **504 Gateway Time-out** | Attempted the connection or waited for a response, and exceeded `proxy_connect_timeout` / `proxy_read_timeout` with no response at all | Stopped the `api` container; Nginx's cached IP for the bare `proxy_pass http://api:80;` hostname pointed at a now-dead network endpoint |

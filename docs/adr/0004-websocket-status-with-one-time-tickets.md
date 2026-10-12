# 0004 — Push analysis status over WebSockets, authenticated with a one-time ticket

Status: Accepted

## Context

`POST /v1/scans/{id}/analyze` returns `202` and the result is ready a few seconds later. The browser needs to learn when. Polling works and is kept, but it spends requests on every poll and shows the result late. Pushing the status when it changes is a better experience.

A browser's `WebSocket` API cannot set an `Authorization` header, so the credential has to travel somewhere else. The usual choice is a query string on the URL. That is a problem here: our Nginx `log_format` records `$request`, which includes the query string; Cloudflare's edge and browser history also retain URLs.

## Decision

Authenticated clients first call `POST /v1/ws/tickets` (JWT in the normal header) and receive a ticket that is valid for about 30 seconds, usable once, and bound to the user and the scan. The client then opens `WS /v1/ws/scans/{id}` and presents the ticket. The server validates and consumes it, and the worker broadcasts `running`, `done` and `failed`. HTTP polling with backoff (2 → 4 → 8 → 15 s) remains as a fallback.

**Alternative rejected:** putting the JWT itself in the WebSocket URL (`?token=<jwt>`).

## Consequences

**Accepted, in exchange for this decision:**
- An extra endpoint, an extra round trip and extra short-lived state before every connection. A reconnect needs a **new** ticket, so the client's reconnect logic is more involved than "open the socket again".
- Two delivery paths (WebSocket and polling) to build, test and keep consistent.
- Long-lived connections need proxy care: Nginx must forward `Upgrade` and `Connection`, and `proxy_read_timeout` (300 s) closes idle sockets, so clients must reconnect with backoff. The Cloudflare Quick Tunnel also limits in-flight requests.
- The connection manager is held per API process, so a second API process would not see these sockets. Scaling out needs a shared channel (for example Redis Pub/Sub), and whatever holds ticket state must be shared too.

**Gained, because of this decision:**
- The long-lived JWT never appears in a URL, so it cannot leak through Nginx access logs, Cloudflare logs, browser history or `Referer` headers.
- A leaked ticket is nearly worthless: it expires in seconds and works once.
- Authorization is checked once, at ticket issue, for one specific scan.
- Status arrives immediately without polling load.

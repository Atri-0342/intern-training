# 0002 — Authenticate with JWTs, not server-side sessions

Status: Accepted

# Context
Every request is made by an authenticated user in exactly one of three roles, with authorization enforced per-endpoint. Two standard approaches were available: server-side sessions (opaque session id, server-side lookup per request) or JWTs (signed token carrying identity and role, verified locally with no lookup). The API also runs behind Nginx and a tunnel, with a plan to scale to multiple processes/containers later.

# Decision
Use JWTs. POST /v1/auth/token issues a signed token with identity and role claims; the client sends it as a Bearer token; the API verifies the signature and reads claims directly, with no server-side session lookup.

# Alternative rejected: server-side sessions with an opaque session id and a server-side session store.

# Consequences

## Accepted, in exchange for this decision:

Revocation is hard. A JWT is valid until it expires — there's no server-side record to delete for immediate invalidation. A compromised account or role change doesn't take effect until the token expires, unless a deny-list or short-lived-token-plus-refresh scheme is added on top. Sessions don't have this problem.
Token content is fixed at issuance — a mid-session role change isn't reflected until the token is reissued.
Secret management becomes critical: a leaked signing key lets someone forge identity outright, not just read existing session data.

## Gained, because of this decision:

No server-side session store to run or keep consistent across multiple API processes — this matters because the API is explicitly expected to run as more than one process/container later. Sessions would require a shared store (e.g. Redis) specifically to make that scaling work; JWTs make each process stateless with respect to auth by construction.
Verifying a request is a local signature check, not a database round trip, so auth overhead stays flat regardless of Postgres load.
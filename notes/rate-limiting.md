# Redis-Backed Rate Limiting

## Overview

ScanFlow uses Redis to enforce rate limits on authentication requests. FastAPI checks the request against a Redis-backed token bucket before processing login or registration attempts.

## Configuration

### Authentication rate limit

- Bucket capacity: 5 tokens
- Refill rate: 1 token per 60 seconds
- Redis key prefix: `rate-limit:auth:`
- Rejected request status: `429 Too Many Requests`
- `Retry-After` header: `60` seconds

### Token-bucket behavior

1. A request identifies the client using a normalized email address and client IP.
2. The identity is hashed with HMAC-SHA256 before being used in the Redis key.
3. Redis stores the token-bucket state in a hash.
4. Each allowed request consumes a token.
5. Tokens refill over time, up to the configured capacity.
6. When insufficient tokens remain, FastAPI rejects the request with HTTP 429.

The Redis Lua script updates the bucket atomically, preventing concurrent requests from independently consuming the same available token.

## Implementation

Relevant components:

- `app/api/auth.py` — invokes the authentication rate limiter for login and registration.
- `app/api/rate_limit.py` — hashes the request identity and enforces the configured limit.
- `app/services/rate_limiter.py` — implements the Redis-backed token bucket.
- `app/core/redis_client.py` — configures the Redis client.
- `docker-compose.yml` — runs Redis as a project service.

## Verification

### Test procedure

Sent seven consecutive login requests through Nginx to:

`POST /v1/auth/token`

The requests used a test email and an intentionally incorrect password.

### Results

| Attempts | HTTP status | Result |
|---|---:|---|
| 1–5 | 401 | Invalid credentials rejected |
| 6–7 | 429 | Authentication rate limit enforced |

The test confirmed that Nginx forwarded requests to FastAPI and that the application returned the expected authentication and rate-limit responses.

### Redis verification

Checked the Redis database size:

```powershell
docker compose exec redis redis-cli DBSIZE
```

Result:

```text
(integer) 1
```

Listed Redis keys:

```powershell
docker compose exec redis redis-cli --scan
```

A rate-limit key was found with this structure:

`rate-limit:auth:<hashed-identity>`

The key was a Redis hash, so `GET` returned `WRONGTYPE`. The correct inspection command was:

```powershell
docker compose exec redis redis-cli HGETALL "rate-limit:auth:<hashed-identity>"
```

The hash contained:

- `tokens` — the remaining fractional token balance.
- `last_refill` — the Unix timestamp used for refill calculations.

The observed token balance was approximately `0.006`, consistent with an almost exhausted bucket.

## Troubleshooting

### Initial errors

The initial test produced HTTP 502 and 503 responses.

- **502 Bad Gateway:** Nginx could not successfully connect to its upstream API at that time.
- **503 Service Temporarily Unavailable:** Nginx's own rate-limiting configuration was rejecting requests before the FastAPI limiter could handle them.

### Resolution

The Nginx configuration was corrected to remove the duplicate authentication rate limiter, leaving the Redis-backed FastAPI limiter responsible for returning HTTP 429.

After the fix, the same test produced five 401 responses followed by two 429 responses.

## Lessons learned

- Distinguish proxy errors from application-level rate-limit responses.
- Avoid accidentally applying duplicate rate limits at both Nginx and FastAPI.
- Use Redis commands appropriate to the stored data type.
- Hash sensitive identifiers rather than exposing email addresses and client IPs in Redis key names.
- Test rate limiting with repeatable requests and verify the actual HTTP status codes.
- Treat the `Retry-After` header as guidance; the exact time until a token becomes available depends on the remaining fractional token balance.

## Security considerations

- Configure `RATE_LIMIT_SECRET` using a strong environment secret outside development.
- Do not trust forwarded client-IP headers unless the trusted proxy configuration is correct.
- Public registration must not allow users to assign themselves privileged roles.
- Use synthetic patient data during public-tunnel testing.
- Rate limiting supplements, but does not replace, authentication and other security controls.

## Evidence and status

**Verified:** Nginx-to-FastAPI request flow, HTTP 401 responses for invalid credentials, HTTP 429 responses after the authentication limit was reached, and Redis hash storage for rate-limit state.

**Not yet verified by this test:** behavior under concurrent load, rate-limit isolation across multiple application replicas, and exact refill timing after waiting.


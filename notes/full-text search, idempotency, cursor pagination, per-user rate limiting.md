# Cursor Pagination vs Offset Pagination

Offset pagination uses `LIMIT` and `OFFSET` to skip a specified number of records and return the next set. It is simple to implement and works well when users need numbered pages. However, large offsets can become slower because the database may need to scan and skip many records. New or deleted records can also shift the results between pages.

Cursor pagination uses a cursor to continue from a specific record. It can be more efficient for large datasets because it avoids skipping many earlier records. It also provides more stable navigation when records are added or deleted, provided the ordering remains consistent.

In ScanFlow, cursor pagination is implemented using `limit` and `cursor`. The current implementation orders scans by UUID, so pagination follows UUID order rather than scan date.

Cursor pagination is useful for browsing large lists sequentially, while offset pagination is more convenient when users need to jump directly to a numbered page.

# Search, Idempotency, Pagination, Rate Limiting — Quick Notes

## 1. Full-text search (FTS) + GIN index

**What we did:** made `GET /v1/scans?q=...` search inside report `findings`.

| Term | Meaning |
|---|---|
| `tsvector` | Text converted into searchable word tokens (lowercased, stemmed: "abnormality" → `abnorm`). |
| `tsquery` / `plainto_tsquery` | The search words, converted the same way. |
| `@@` | "Does this tsvector match this tsquery?" |
| `'english'` | Language config: stemming + stop-word rules. |
| Seq Scan | Postgres reads every row. Slow on big tables. |
| GIN index | Inverted index: word → list of rows containing it (like a book's index). Built for tsvector. |
| Bitmap Index Scan / Bitmap Heap Scan | Index finds matching row locations first, then only those pages are read. |
| `EXPLAIN ANALYZE` | Runs the query and shows the real plan and timings. |
| `BUFFERS` | How many memory/disk pages were touched. |
| `ANALYZE` | Refreshes table statistics so the planner picks good plans. |

**Result (74,855 matching rows):**

| | Plan | Execution time |
|---|---|---|
| Before index | Parallel Seq Scan | **380.7 ms** |
| After GIN index | Bitmap Index Scan | **27.0 ms** |

≈ **14× faster**. The index must use the same expression as the query: `to_tsvector('english', findings)`.

---

## 2. Idempotency (`Idempotency-Key` header on `POST /v1/scans/upload`)

**Problem:** a retry (network drop, double-click) must not create a duplicate scan.

**How it works:**
1. Client sends a unique `Idempotency-Key`.
2. Server hashes the request (fields + SHA-256 of the file) → `request_hash`.
3. Row saved in `idempotency_records`, unique on `(user_id, key)`.
4. Same key + same hash → return the **stored response** (no new scan).
5. Same key + different hash → **409** (key reused for a different request).
6. Same key while first request unfinished → **409** (still processing).

The unique constraint is what makes this safe under race conditions: two simultaneous requests can't both insert.

---

## 3. Cursor vs offset pagination

| | Offset (`LIMIT/OFFSET`) | Cursor (`limit` + `cursor`) |
|---|---|---|
| How | Skip N rows, take M | "Give me rows after this ID" |
| Speed on deep pages | Slow (DB still walks skipped rows) | Fast (index jump) |
| Inserts/deletes mid-browse | Rows shift → duplicates/skips | Stable |
| Jump to page 50 | Easy | Not possible |
| Needs | Nothing | Stable, unique sort key |

**ScanFlow:** `WHERE id > cursor ORDER BY id LIMIT n`. Caveat: ordering is by UUID, not by date, so "next page" isn't chronological.

---

## 4. Per-user rate limiting

**Problem:** limiting by IP alone is unfair (shared offices/NAT) and bypassable. We limit by **authenticated user ID**.

| Term | Meaning |
|---|---|
| Token bucket | Bucket holds up to `capacity` tokens; each request costs 1; tokens refill over time. |
| Capacity 10, refill 1/s | Burst of 10, then sustained 1 request/second. |
| Redis | Shared fast store for bucket state (`rate-limit:user:<id>`), so it works across API processes. |
| `429` + `Retry-After` | "Too many requests, try again in N seconds." |

Applied as a router dependency (`enforce_user_rate_limit`) on all `/v1/scans` routes. Login uses a separate, stricter limiter (5 attempts, keyed by email + IP, HMAC-hashed so raw emails aren't stored in Redis).

---

## One-line summary

GIN made search ~14× faster; idempotency prevents duplicate uploads; cursor pagination stays fast and stable on big lists; per-user token buckets rate-limit fairly.
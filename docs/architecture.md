ScanFlow — System Architecture
Radiology scan intake and analysis API. Requirements were settled in prose before any diagram was drawn — the diagrams below are a picture of those decisions, not a substitute for them.

Table of contents
# Overview
# Who uses it, and in which role
# Components — this phase vs. later
# Where data lives, and where files live
# Inside the request vs. afterwards
# Failure modes
# Open decisions / ADRs

# Overview
ScanFlow lets clinical staff upload radiology scans, have them analyzed, and read the resulting reports. It's one API behind one authentication scheme, backed by a relational store for structured data, blob storage for files, and a background worker for the one operation too slow to run inside a request.

This document is written in the order the system was actually decided: who uses it, what it's made of and when each part gets built, where data lives, and which operations are synchronous — in that order, because that last question is what determines the API surface, not the other way round.

# Who uses it, and in which role
Three roles use ScanFlow. All three authenticate through the same scheme; authorization is enforced per-endpoint, not by standing up separate systems per role.

Clinician — uploads scans, checks scan status, and reads finalized reports. This is the role that generates the most traffic.

Radiologist — does everything a clinician can do, plus finalizes reports. It's the only role that can move a report from draft to final.

Admin — manages user accounts, and deliberately has no special access to clinical data. Administering the system and reading patient data are treated as different privileges.

There is no anonymous or public role. Every request is made by an authenticated user acting in exactly one of these three roles.

# Components — this phase vs. later
Five components make up the system. Only the first two exist in the current build phase; the API is deliberately shaped now so the rest can be added without renegotiating the endpoints later.

## Built now:

The FastAPI app itself — patients and scans endpoints — backed by in-memory storage.

## Added later, in this order:

Real Postgres, replacing the in-memory store.
Auth (JWT, roles), added once storage is real.
The analysis worker — an async job pipeline, running as an in-process asyncio task that claims work via SELECT … FOR UPDATE SKIP LOCKED.
A reverse proxy and containerization — Nginx and Docker Compose, exposed through a Cloudflare Tunnel.
File storage on the real object-storage API — S3, emulated via moto/LocalStack.
The worker, the proxy, and object storage are named here on purpose — so the API leaves room for them — but nothing behind that line is implemented in this phase.

# Where data lives, and where files live
Structured data and files are two different kinds of data, and they don't share a home.

## Structured data 
patients, scans, reports, users, audit log — is the system of record and lives in Postgres. Anything that gets queried, filtered, or joined belongs here.

## Files 
the scan image itself, and any report PDF — do not belong in a database row. They live on disk (a mounted volume early on, the S3 API once that phase lands), and the corresponding scans / reports row holds only a path or object key. A row carrying a multi-megabyte blob is the wrong shape for every query that doesn't need the blob.

# Inside the request vs. afterwards
This is the decision that shapes the whole API surface, made explicitly rather than discovered by accident once the worker exists.

Inside the request (synchronous) — anything the caller needs confirmed before moving on: validating and persisting a patient or scan record, storing an uploaded file, authenticating. These stay synchronous because they're fast, and the caller has nothing useful to do until they're done.

After the request returns (asynchronous, handed to the worker) — running analysis on a scan. Inference is slow (3–5+ seconds, simulated), and holding an HTTP connection open for that is the wrong shape. So POST /v1/scans/{id}/analyze returns 202 Accepted with a job id — "I've accepted this and will do it" — not 200 with a result. Patients and scans CRUD stay synchronous; there's no reason to make a caller poll for something that takes milliseconds.

# Failure modes

Nginx dies. The tunnel returns an error and the user sees no response. It self-recovers via restart: unless-stopped, needs a human only if it loops, and puts no data at risk.

The API dies mid-request. The user sees a 502 from Nginx. It self-recovers via the restart policy, needs a human only if it loops on startup, and the risk is limited to the in-flight request — the DB transaction rolls back, so nothing is left half-written.

The async worker crashes mid-job. The job is stuck at running forever, since there's no heartbeat, and the user just sees it never finish. This does not self-recover — a human has to restart the container, at which point the job is re-claimed automatically via SKIP LOCKED. No data is at risk: a crash after partial writes is prevented by transactional boundaries.

Postgres dies. The API returns 500 on any DB call and /healthz fails. It self-recovers if the volume is intact; a human is needed only if the volume or disk itself is the problem. Data is safe as long as the volume persists, and lost entirely only if the volume is removed.

Object storage (the S3 emulation) is unreachable. Upload and analysis endpoints return 502/500. Recovery depends on the emulator restarting on its own; in this setup, a human is usually needed. An uploaded file is at risk only if it wasn't yet committed to a DB row.

The Cloudflare Tunnel stops. The public URL goes dark immediately. It does not self-recover — it's ephemeral by design — so a human has to restart cloudflared. No data is at risk, since the tunnel is stateless.

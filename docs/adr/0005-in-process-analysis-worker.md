# 0005 — Run the analysis worker inside the API process, not as a separate service

Status: Accepted (revisit when the triggers below are met)

## Context

[ADR 0001](0001-async-analysis-pipeline.md) decided that analysis runs asynchronously. That leaves a second question: where does the worker run? Two options were available: a separate worker service consuming from a queue (a dedicated container, with SQS, Redis or a task-queue library), or an asyncio task started inside the API process that claims jobs from PostgreSQL.

At 200 scans a day the work is 200 × 4 s ≈ 13 worker-minutes. The target environment is a Docker Compose stack that one person must be able to start with one command.

## Decision

The worker is an asyncio task started with the API. It claims work from the `analysis` job table with `SELECT ... FOR UPDATE SKIP LOCKED`, marks it `running`, performs the analysis, writes the result, and pushes status to connected browsers through the API's own WebSocket manager. Jobs stuck in `running` for over 60 seconds are returned to `uploaded`.

**Alternative rejected:** a separate worker container fed by a message broker or task queue (SQS, Redis, or a Celery-style framework).

## Consequences

**Accepted, in exchange for this decision:**
- **The worker cannot scale on its own.** One serial worker tops out at about 900 jobs/hour on paper; the loop as written claims one job and sleeps 5 s, so closer to 450. At 20,000 scans/day the busiest hour needs about 6,000 jobs, so this is the first thing that breaks (`docs/architecture.md` §8).
- **It shares fate with the API.** Restarting or crashing the API kills any job in flight; it is recovered only after the 60 s stale window. Every deploy interrupts analysis.
- **It shares the event loop and CPU.** Today the "inference" is `asyncio.sleep`. A real CPU-bound model run in-process would block the loop and slow every request; the Day 39 load test already showed the API process near 100% CPU. A real model forces the move out of process.
- **Nothing supervises it.** If the task dies from an unhandled exception the API stays healthy (`/healthz` checks the database only) while analysis silently stops.
- **Stale detection uses `created_at`,** not a start time or lease. Safe with one worker; with several, a healthy long-running or long-queued job could be reclaimed. It must change first.
- **It is coupled to ADR 0004.** WebSocket events work only because the worker and the connection manager live in one process. Extracting the worker means adding a shared channel such as Redis Pub/Sub.

**Gained, because of this decision:**
- One process and one command: no broker to run, secure, monitor or pay for (the AWS equivalent adds SQS and a second ECS service).
- A job's state change commits in the same database as the data, so there is no dual write between a database and a queue that could disagree.
- A direct in-process broadcast to browsers, with no extra hop.
- Ample capacity for the current load (about 13 worker-minutes per day).

## Revisit when

Queue depth grows during the busiest hour, time-to-start exceeds the target, a real model replaces the simulation, or a second API process is needed.

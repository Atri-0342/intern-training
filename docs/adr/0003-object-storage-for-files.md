# 0003 — Store files in object storage, not as database blobs

Status: Accepted

# Context
ScanFlow handles structured records (queried, filtered, joined) and files (opaque binary payloads, tens of MB each, never queried by content). Two places for the file bytes: a bytea column on the scans/reports row, or separate object storage with the row holding only a path/key. At 200 scans/day this is ~1.5 TB/year growth; at 20,000/day it's ~149 TB/year — both scales were used to stress-test the choice.

# Decision
Files live in object storage — a mounted volume now, the S3 API (moto/LocalStack now, a real bucket later) once that phase lands. The scans/reports rows hold only a path or object key, never the bytes.

# Alternative rejected: storing scan images and report PDFs directly as bytea columns in Postgres.

# Consequences

## Accepted, in exchange for this decision:

Two storage systems instead of one: two things to back up, two things that can fail independently, and a cross-system consistency problem — a PutObject can succeed while the DB INSERT fails, or vice versa, producing an orphaned object or a dangling reference. This needs reconciliation logic or careful transactional ordering that a single-database design wouldn't.
Local development needs a second service running (moto/LocalStack), not just a database.
Referential integrity between a row and its file is enforced by application code — Postgres has no foreign key that can guarantee the object exists.

## Gained, because of this decision:

Queries against scans/reports that don't need the file itself stay fast and cheap, since they never touch multi-megabyte payloads — a bytea design would bloat table/index size and slow routine CRUD as file volume grows.
Storage scales independently of the database. At ~149 TB/year (the 20,000-scans/day scenario), a bytea approach would force that entire volume through Postgres's own storage/backup/replication path; object storage lets file growth get its own lifecycle policy without touching the database's operational story.
Postgres backups stay small and fast, since they never include the bulk of the system's actual byte volume.
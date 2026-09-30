# ScanFlow — Twelve-Factor App Audit

## Objective

Evaluate the current ScanFlow capstone against the Twelve-Factor App principles, based on the current implementation and work completed so far — not on planned production components as if they already exist.

### Scoring scale

| Score | Meaning |
|---|---|
| 5/5 | Strongly follows the factor |
| 4/5 | Mostly follows, with a small practical gap |
| 3/5 | Partially follows; acceptable for the current capstone stage |
| 2/5 | Significant gap |
| 1/5 | Major gap |

---

## 1. Codebase — 5/5

**What the factor expects**
The application should have one codebase tracked in version control that can be used to create different deployments.

**What ScanFlow does**
ScanFlow is maintained as a Git-controlled project containing the application code, tests, configuration structure, database/migration code, and documentation. Development work is performed against the same project rather than maintaining separate application copies for different environments.

**Gap**
No significant gap has been identified.

**Why this score?**
The project follows the basic codebase principle well. Application code, tests, migrations, and documentation are maintained as part of the same version-controlled project.

**What would force a change?**
A problem would arise if different environments started using manually modified copies of the application rather than the same version-controlled codebase.

---

## 2. Dependencies — 5/5

**What the factor expects**
Dependencies should be explicitly declared and isolated instead of relying on packages installed globally on the machine.

**What ScanFlow does**
ScanFlow uses an isolated Python environment and explicitly installs the dependencies required by the application and its tests — FastAPI, SQLAlchemy, psycopg, asyncpg, Alembic, authentication dependencies, pytest, pytest-cov. Testing is performed inside the project environment.

**Gap**
No significant current gap has been identified.

**Why this score?**
The application does not depend on arbitrary globally installed packages. The environment and project dependencies are separated from the system Python installation.

**What would force a change?**
Production deployment would benefit from stronger dependency locking and containerized builds to guarantee identical dependency versions across environments.

---

## 3. Config — 5/5

**What the factor expects**
Environment-specific configuration and secrets should be kept outside application source code.

**What ScanFlow does**
ScanFlow uses environment-based configuration for database connection settings, JWT configuration, and other environment-specific values. Sensitive values are kept in environment configuration rather than being embedded directly into route or model code.

**Gap**
The `.env` approach is appropriate for local development, but production would require a dedicated secret-management mechanism.

**Why this score?**
The important Twelve-Factor principle is already being followed: application code does not need to change when environment-specific configuration changes.

**What would force a change?**
Production deployment would justify using a dedicated secret-management mechanism such as a cloud secret manager or deployment-platform secret injection.

---

## 4. Backing Services — 4/5

**What the factor expects**
Databases, file storage, and other external resources should be treated as attached services rather than being tightly embedded into the application.

**What ScanFlow does**
ScanFlow separates its major resources — FastAPI, PostgreSQL, file/object storage, and the analysis worker. Structured application data (patients, scans, reports, users, audit logs) belongs in PostgreSQL; large scan files and report PDFs are kept separately from relational rows. This separation is also reflected in the architecture document.

**Gap**
The development and intended production storage environments are not yet identical. Development has involved local services, while the planned production architecture includes S3-compatible object storage.

**Why this score?**
The architectural separation is correct. The remaining issue is mainly environment maturity rather than tight coupling between the application and a particular storage implementation.

**What would force a change?**
The difference becomes important when ScanFlow moves to production, when multiple API instances need shared storage, when scan volume becomes large, or when independent scaling and backup become necessary.

---

## 5. Build, Release, Run — 3/5

**What the factor expects**
Building the application, preparing a release, and running that release should be separate processes (source code → build → release → run).

**What ScanFlow does**
The project currently supports dependency installation, environment configuration, application startup through Uvicorn, database migrations, automated tests, coverage measurement, HTTPS testing, and local operational testing.

**Gap**
There is not yet a mature automated CI/CD pipeline (push → tests → build → release → deploy). Deployment remains relatively manual.

**Why this score?**
The application has a clear run process, but build and release automation are not yet production-grade. This is acceptable for the current capstone stage.

**What would force a change?**
Before production deployment, the project should introduce CI, automated tests on every push, Docker image builds, versioned releases, and automated deployment.

---

## 6. Processes — 4/5

**What the factor expects**
Application processes should be stateless, with persistent state stored in external backing services rather than depending on process memory.

**What ScanFlow does**
Important application state is stored in PostgreSQL — `User`, `Patient`, `Scan`, `AnalysisJob`, `Report`, `AuditLog`. The analysis worker also stores job state in PostgreSQL, claiming jobs via `SELECT ... FOR UPDATE SKIP LOCKED`. The job queue is not simply a Python list that disappears when the process stops.

**Gap**
The analysis worker currently runs as an in-process asyncio task inside the application rather than as a separately deployed worker service. The architecture document explicitly describes this current design.

**Why this score?**
Persistent application state is correctly externalized. The main limitation is that the worker cannot currently be scaled independently from the API process.

**What would force a change?**
At higher workload, the worker should become independently scalable — FastAPI → PostgreSQL job queue → Worker 1, Worker 2, Worker 3...

---

## 7. Port Binding — 5/5

**What the factor expects**
The application should expose its service through its own port rather than requiring a separate web server to actually run the application.

**What ScanFlow does**
FastAPI runs through Uvicorn and exposes its HTTP service directly. The project has also been tested with HTTPS using Uvicorn's TLS configuration. Nginx is intended to operate as a reverse proxy, not as the thing responsible for running the application.

**Gap**
None identified.

**Why this score?**
ScanFlow is independently runnable as a network service.

**What would force a change?**
Not applicable — this factor is already fully satisfied.

---

## 8. Concurrency — 4/5

**What the factor expects**
Scaling should be achieved through processes rather than depending on a single application process.

**What ScanFlow does**
The database-backed job system was designed with `SELECT ... FOR UPDATE SKIP LOCKED`, which allows multiple workers to safely claim different jobs. The architecture can scale the analysis workload horizontally without redesigning the job table.

**Gap**
Only one analysis worker is currently deployed.

**Why this score?**
The important architectural decision has already been made in a way that supports multiple workers. The current limitation is deployment scale, not that the queue architecture prevents scaling.

**What would force a change?**
The capacity calculation shows the trigger: at 20,000 scans/day, the busiest hour could require approximately **6,000 analysis jobs/hour**, while one serial 4-second worker can theoretically process **900 jobs/hour**. Multiple workers would be required.

---

## 9. Disposability — 4/5

**What the factor expects**
Processes should start and stop cleanly and tolerate unexpected termination.

**What ScanFlow does**
The API's durable state is stored outside the application process. Database transactions provide protection against partially completed database operations. The analysis worker includes job-state handling and stale-job recovery, so a job does not necessarily remain permanently lost after a worker failure.

**Gap**
A worker failure during analysis can temporarily leave a job in a `running` state until the stale-job recovery mechanism detects it.

**Why this score?**
The project already considers process failure and recovery rather than assuming processes will never fail. The remaining gap is mainly operational robustness.

**What would force a change?**
Production deployment would justify worker heartbeats, explicit job timeouts, monitoring, alerts, and stronger shutdown handling.

---

## 10. Dev/Prod Parity — 3/5

**What the factor expects**
Development, staging, and production environments should remain reasonably similar.

**What ScanFlow does**
Development has involved Windows/WSL, local PostgreSQL, local filesystem, Uvicorn, and local HTTPS testing. The intended production architecture adds Cloudflare Tunnel, Nginx, Docker Compose, and S3-compatible object storage. The architecture document explicitly separates these later components from the initial build phase.

**Gap**
The development environment does not yet completely reproduce the intended production environment.

**Why this score?**
This is a real Twelve-Factor gap, but it is acceptable during the capstone because the infrastructure is being introduced incrementally.

**What would force a change?**
Before production, development/staging should use an environment much closer to production — ideally Docker Compose → Nginx → FastAPI → PostgreSQL + S3-compatible storage, matching the production path end to end.

---

## 11. Logs — 4/5

**What the factor expects**
Logs should be treated as event streams rather than application state stored inside the application.

**What ScanFlow does**
The project uses normal process/server output and has been actively tested through runtime diagnostics — Uvicorn logs, FastAPI errors, PostgreSQL errors, `curl -v`, OpenSSL, `ss`, `nc`, `tcpdump` — during networking and infrastructure work. Runtime behavior can be observed rather than hidden inside application state.

**Gap**
There is not yet a centralized production logging system combining Nginx, API, worker, PostgreSQL, and the Cloudflare Tunnel into one searchable platform.

**Why this score?**
Centralized logging is primarily a production-operations improvement. Its absence does not mean the core logging principle is completely violated.

**What would force a change?**
Once ScanFlow has multiple containers/workers and real production incidents, centralized log aggregation becomes important for debugging and monitoring.

---

## 12. Admin Processes — 4/5

**What the factor expects**
Administrative and management tasks should run as one-off processes using the same application codebase and environment.

**What ScanFlow does**
ScanFlow uses Alembic for database migrations. The application also contains an explicit Admin role for user-account management, with administrative privileges kept separate from clinical-data access.

**Gap**
The project does not yet have a mature collection of formal operational commands/runbooks for every production maintenance scenario.

**Why this score?**
The core principle is mostly present. The remaining work is operational maturity rather than a fundamental architectural problem.

**What would force a change?**
Production would require documented procedures for database backup/restore, migrations, failed-job recovery, maintenance, storage recovery, and audit-log management.

---

## Final Scorecard

| # | Twelve-Factor principle | Score | Main reason |
|---|---|---|---|
| 1 | Codebase | 5/5 | Git-controlled single project |
| 2 | Dependencies | 5/5 | Isolated environment and explicit dependencies |
| 3 | Config | 5/5 | Environment-based configuration |
| 4 | Backing Services | 4/5 | Good service separation; environments differ |
| 5 | Build, Release, Run | 3/5 | Release/deployment still largely manual |
| 6 | Processes | 4/5 | Persistent state externalized; worker is in-process |
| 7 | Port Binding | 5/5 | FastAPI/Uvicorn exposes its own service |
| 8 | Concurrency | 4/5 | `SKIP LOCKED` supports multiple workers |
| 9 | Disposability | 4/5 | Transactions and stale-job recovery |
| 10 | Dev/Prod Parity | 3/5 | Production infrastructure not fully reproduced locally |
| 11 | Logs | 4/5 | Runtime logging works; centralized logging is future work |
| 12 | Admin Processes | 4/5 | Alembic and admin operations exist; runbooks can mature |

**Total: 48/60**

## Main Findings

ScanFlow already follows the core Twelve-Factor principles reasonably well for its current development stage. The main areas that are not yet at full maturity are build/release automation, independent worker scaling, development/production parity, centralized production logging, and formal production administration/recovery procedures. These are production-readiness improvements, not fundamental problems with the current application architecture.

The most important architectural scaling limitation has also been quantified:

**At 200 scans/day:** ≈ 60 analysis jobs during the busiest hour, against 900 jobs/hour theoretical capacity — large worker headroom.

**At 20,000 scans/day:** ≈ 6,000 jobs during the busiest hour, against 900 jobs/hour from one serial worker — approximately **6.7× more worker capacity required** than currently exists.

The architecture has a clear scaling path: run multiple workers against the same PostgreSQL-backed job table using `SELECT ... FOR UPDATE SKIP LOCKED`. The capacity analysis in `docs/architecture.md` §10 identifies the same worker-concurrency bottleneck, using the same figures.

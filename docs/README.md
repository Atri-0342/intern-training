# ScanFlow

ScanFlow is a FastAPI-based radiology scan intake and analysis API backed by PostgreSQL. Clinicians upload scans, trigger an asynchronous analysis, and watch the result arrive in the browser over a WebSocket.

**Stack:** FastAPI · PostgreSQL 17 · Redis · Nginx · React (Vite) · S3-compatible storage (Moto in development) · Docker Compose

## Prerequisites

Install:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)
- [Python 3.12+](https://www.python.org/downloads/), only for the local S3 emulator and for running tests on the host

Docker Desktop must be running before you start the application.
# Architecture Decision Records

Format: Michael Nygard's (context, decision, status, consequences). Every record names the **alternative rejected** and the **consequence accepted**. Records are not rewritten when reality moves on; later facts are added as an "Update" section or a new record.

| # | Decision | Alternative rejected | Status |
|---|---|---|---|
| [0001](0001-async-analysis-pipeline.md) | Analysis runs as an asynchronous job | Processing inside the request | Accepted |
| [0002](0002-jwt-auth.md) | Authenticate with JWTs | Server-side sessions | Accepted |
| [0003](0003-object-storage-for-files.md) | Scan files live in object storage, only the key in PostgreSQL | Files as `bytea` in PostgreSQL | Accepted |
| [0004](0004-websocket-status-with-one-time-tickets.md) | WebSocket status with a one-time ticket | JWT in the WebSocket URL | Accepted |
| [0005](0005-in-process-analysis-worker.md) | Worker runs inside the API process | Separate worker service with a queue | Accepted, revisit at scale |

## 1. Environment variables

Create two files in the project root. **Neither is committed to Git.**

### `.env`

```env
DB_NAME=scanflow
DB_USER=postgres
DB_HOST=db
DB_PORT=5432
TEST_DB_NAME=scanflow_test

POSTGRES_USER=postgres
POSTGRES_DB=scanflow

JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
```

### `.env.secret`

```env
DB_PASSWORD=YOUR_DATABASE_PASSWORD
POSTGRES_PASSWORD=YOUR_DATABASE_PASSWORD
JWT_SECRET=YOUR_JWT_SECRET
```

Replace the placeholders with your own local secrets.

> **Do not commit `.env` or `.env.secret` to Git.**

### Optional variables

These have working local defaults. Change them for anything beyond a laptop.

| Variable | Default | Purpose |
|---|---|---|
| `S3_BUCKET` | `scanflow-scans` | Bucket that holds scan files |
| `S3_REGION` | `us-east-1` | S3 region |
| `S3_ENDPOINT_URL` | `http://host.docker.internal:5000` | Points at the local Moto server; **remove it to use real AWS S3** |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | `test` / `test` | Dummy credentials for Moto only |
| `RATE_LIMIT_SECRET` | `local-development-only` | Salt used to hash identities in rate-limit keys; **set a real value outside development** |

## 2. Start the local S3 emulator

Uploaded scan files go to an S3-compatible API. In development that is [Moto](https://github.com/getmoto/moto), run on the host:

```bash
pip install "moto[server]" boto3
moto_server -p 5000
```

In a second terminal, create the bucket once per Moto start (Moto keeps everything in memory):

```bash
python -c "import boto3; boto3.client('s3', endpoint_url='http://localhost:5000', region_name='us-east-1', aws_access_key_id='test', aws_secret_access_key='test').create_bucket(Bucket='scanflow-scans')"
```

## 3. Start the application

From the project root:

```bash
docker compose up --build
```

This builds the React frontend and the API, then starts the API, PostgreSQL, Redis and Nginx. Database migrations are applied automatically when the API container starts.

Open the application:

```text
http://localhost:8000
```

## API documentation

Interactive Swagger UI:

```text
http://localhost:8000/docs
```

Raw OpenAPI specification:

```text
http://localhost:8000/openapi.json
```

## Health check

```text
http://localhost:8000/healthz
```

A healthy application returns:

```json
{
  "status": "ok",
  "database": "connected"
}
```

## Try it

1. Open `http://localhost:8000/docs`.
2. `POST /v1/auth/register` to create a user, then `POST /v1/auth/token` with that email and password.
3. Click **Authorize** and paste the `access_token`.
4. Create a patient, then `POST /v1/scans/upload` (it requires an `Idempotency-Key` header: any unique string, reused only when retrying the *same* upload).
5. `POST /v1/scans/{id}/analyze` returns `202`; the status then moves `uploaded → running → done`.

Or use the web UI at `http://localhost:8000`, which does the same thing and shows the status arriving live.

## Run tests

On the host (Windows):

```bash
py -m pytest
```

With coverage:

```bash
py -m pytest --cov=app
```

On macOS/Linux use `python -m pytest`.

## Stop the application

Stop the containers **without** removing the PostgreSQL volume:

```bash
docker compose down
```

The volume is intentionally preserved, so your data survives.

> **Warning:** `docker compose down -v` removes the PostgreSQL volume and permanently deletes the database stored in it. Take a backup first (see the runbook).

## Public demo URL (optional)

To reach the stack from another network, expose Nginx through a free Cloudflare Quick Tunnel:

```bash
docker run --rm --network host cloudflare/cloudflared:latest tunnel --no-autoupdate --url http://localhost:8000
```

It prints a `https://….trycloudflare.com` URL that lasts only as long as the process. See the runbook for the limits.

## Documentation

| Document | What it covers |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Current system, C4 and sequence diagrams, TLS path, capacity estimate, failure-mode table |
| [`docs/api-design.md`](docs/api-design.md) | API contract and how it diverged from the original design |
| [`docs/runbook.md`](docs/runbook.md) | Start, restart, roll back, logs, backup **and tested restore**, troubleshooting |
| [`docs/aws-migration.md`](docs/aws-migration.md) | Mapping to AWS services, security groups, IAM policy, cost estimate |
| [`docs/adr/`](docs/adr/README.md) | Five architecture decision records (each names the rejected alternative and the accepted consequence) |
| [`docs/twelve-factor-audit-final.md`](docs/twelve-factor-audit-final.md) | Twelve-factor scorecard with what would force each fix |
| [`notes/load-testing.md`](notes/load-testing.md) | 100-user load test, percentiles, bottleneck analysis |

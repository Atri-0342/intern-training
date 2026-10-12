# ScanFlow — Runbook

For whoever has to keep ScanFlow running without asking the person who built it. Commands run from the project root. They work in PowerShell and bash unless marked.

Background: [`architecture.md`](architecture.md) (what each component does and how it fails), [`aws-migration.md`](aws-migration.md).

## At a glance

| Service | Compose name | Container | Port | Health signal |
|---|---|---|---|---|
| API + worker | `api` | `scanflow` | internal `80` | `GET /healthz` → `{"status":"ok","database":"connected"}`, container `healthy` |
| Nginx | `nginx` | `scanflow-nginx-1` | host `8000` → `80` | `docker compose ps` shows `Up` |
| PostgreSQL | `db` | `scanflow-postgres` | internal `5432` | `pg_isready`, container `healthy` |
| Redis | `redis` | `scanflow-redis` | internal `6379` | container `healthy` |
| Moto (S3 emulator) | not in Compose | host process | host `5000` | `curl http://localhost:5000` answers |
| Cloudflare Tunnel | not in Compose | host process | none | prints a `trycloudflare.com` URL |

Moto and the tunnel are **not** supervised by Compose. After a reboot they must be started by hand ([§7](#7-resilience-drill)).

---

## 1. Bring the stack up

**Before you start**

1. Docker Desktop is running.
2. `.env` and `.env.secret` exist in the project root (see the README).
3. Moto is running on port 5000 and the `scanflow-scans` bucket exists (README step 2).

**Start**

```bash
docker compose up -d --build
```

**Verify**

```bash
docker compose ps                      # api, db, redis: healthy; nginx: Up
curl http://localhost:8000/healthz     # {"status":"ok","database":"connected"}
```

Then log in through the browser at `http://localhost:8000` (not just `/docs`). Migrations run automatically in the API entrypoint and are safe to repeat.

**Public URL (demo only)**

```bash
docker run --rm --network host cloudflare/cloudflared:latest tunnel --no-autoupdate --url http://localhost:8000
```

The printed URL dies with the process and changes each run. Capped at 200 in-flight requests.

---

## 2. Restart a single service

| Goal | Command |
|---|---|
| Restart the API (config or env change) | `docker compose restart api` |
| Rebuild the API after Dockerfile or dependency changes | `docker compose up -d --build api` |
| Restart Redis / Postgres | `docker compose restart redis` / `docker compose restart db` |
| Apply an Nginx config change | `docker compose exec nginx nginx -t` then `docker compose exec nginx nginx -s reload` |
| Rebuild Nginx (new frontend bundle) | `docker compose up -d --build nginx` |

Notes that have caused real incidents:

- **`nginx -t` only tests the file; it does not apply it.** Run `nginx -s reload` as a second step.
- **After the API container is recreated, reload Nginx.** Nginx resolves `api` when it loads its config and can keep proxying to the old IP, which shows up as `504` after 5 s.
- **Python source changes need no rebuild** while `./app` is bind-mounted into the container; a restart is enough. Dockerfile or `requirements` changes do need `--build`.
- **Restarting the API interrupts any analysis in flight.** The job is picked up again after the stale-job window (60 s).

---

## 3. Roll back

Always take a backup first ([§5](#5-back-up-the-database)).

**Code only (no migration in the release)**

```bash
git log --oneline -10                  # find the last good commit or tag
git checkout <good-commit>
docker compose up -d --build
curl http://localhost:8000/healthz
```

**Release included a database migration**

Order matters: the downgrade script lives in the *newer* code, so run it **before** checking out the old code.

```bash
docker compose exec api alembic current          # note the current revision
docker compose exec api alembic history | head   # find the target revision
docker compose exec api alembic downgrade -1     # or a specific revision
git checkout <good-commit>
docker compose up -d --build
```

If the downgrade is not reversible, or data is damaged, restore the backup taken before the release ([§6](#6-restore-into-a-fresh-database)).

---

## 4. Where the logs live

All services log to stdout, so Docker holds them. There are no log files to hunt for inside containers.

| What | Command | Notes |
|---|---|---|
| API and **worker** | `docker compose logs api --tail=100 -f` | Worker lines: `Processing analysis job`, `Completed analysis job`, `Recovered stale analysis job` |
| Nginx access and error | `docker compose logs nginx --tail=100` | Format includes `request_id`, `request_time`, `upstream_response_time`, `upstream_status`. Errors also go here, not to `/var/log/nginx/error.log` |
| PostgreSQL | `docker compose logs db --tail=100` | Statements slower than 100 ms are logged (`log_min_duration_statement`) |
| Redis | `docker compose logs redis --tail=50` | |
| Tunnel | the terminal running `cloudflared` | Not in Compose |
| Everything | `docker compose logs --tail=200` | |

**Follow one request end to end.** Nginx creates a request ID and passes it on, so one ID appears in the Nginx, API and worker logs.

```powershell
# PowerShell
docker compose logs --no-log-prefix | Select-String "<request-id>"
```
```bash
# bash
docker compose logs --no-log-prefix | grep "<request-id>"
```

**Is something slow right now?**

```bash
docker compose exec db psql -U postgres -d scanflow -c "SELECT pid, state, now()-query_start AS running_for, left(query,80) FROM pg_stat_activity WHERE datname='scanflow' AND state <> 'idle' ORDER BY running_for DESC;"
```

---

## 5. Back up the database

`pg_dump` in custom format (`-Fc`) is compressed and restorable with `pg_restore`.

```bash
mkdir backups
docker compose exec db pg_dump -U postgres -Fc -f /tmp/scanflow.dump scanflow
docker compose cp db:/tmp/scanflow.dump ./backups/scanflow-$(date +%F).dump        # bash
```
```powershell
# PowerShell equivalent of the last line
docker compose cp db:/tmp/scanflow.dump ".\backups\scanflow-$(Get-Date -Format yyyy-MM-dd).dump"
```

Dump inside the container and copy the file out. Do **not** use `>` redirection in Windows PowerShell: it re-encodes the output and corrupts a binary dump.

**What a database backup does not contain:** the scan files. Those live in object storage, so back them up separately (real S3: versioning and lifecycle rules; Moto: nothing is persisted at all). Restoring only the database leaves rows whose `file_key` points at nothing.

Keep `backups/` out of Git. Dumps contain patient data.

---

## 6. Restore into a fresh database

An untested backup is not a backup. This restores into a **separate** database so production is untouched, then checks that the data is really there.

```bash
# 1. Create an empty database
docker compose exec db psql -U postgres -c "CREATE DATABASE scanflow_restore_test;"

# 2. Copy the dump in and restore it
docker compose cp ./backups/scanflow-YYYY-MM-DD.dump db:/tmp/restore.dump
docker compose exec db pg_restore -U postgres -d scanflow_restore_test --no-owner --exit-on-error /tmp/restore.dump

# 3. Compare row counts with the source
docker compose exec db psql -U postgres -d scanflow              -c "SELECT (SELECT count(*) FROM patients) AS patients, (SELECT count(*) FROM scans) AS scans;"
docker compose exec db psql -U postgres -d scanflow_restore_test -c "SELECT (SELECT count(*) FROM patients) AS patients, (SELECT count(*) FROM scans) AS scans;"

# 4. Clean up
docker compose exec db psql -U postgres -c "DROP DATABASE scanflow_restore_test;"
```

The two count rows must match. At the time of writing the dataset held 20,002 patients and 200,000 scans.

**Last verified restore:** `____-__-__` by `________` (fill in after each drill).

**Real disaster recovery (replace the live database)**

```bash
docker compose stop api
docker compose exec db psql -U postgres -c "DROP DATABASE scanflow;"
docker compose exec db psql -U postgres -c "CREATE DATABASE scanflow;"
docker compose cp ./backups/<file>.dump db:/tmp/restore.dump
docker compose exec db pg_restore -U postgres -d scanflow --no-owner /tmp/restore.dump
docker compose start api
curl http://localhost:8000/healthz
```

---

## 7. Resilience drill

Every service in Compose has `restart: unless-stopped`.

```bash
docker compose down        # keeps the database volume
docker compose up -d       # stack returns on its own, data intact
```

Never use `down -v` for this drill: it deletes the volume.

**After a laptop reboot**

1. Docker Desktop starts (set it to start at login) and brings the Compose containers back by itself.
2. Start Moto and recreate the bucket (it is in memory, so every uploaded file is gone; see Known limits).
3. Start `cloudflared` again and share the new URL.
4. `docker compose ps` and `curl http://localhost:8000/healthz`.

---

## 8. Troubleshooting

### The container exits straight away and prints nothing

```bash
docker compose ps -a                   # exit code and state
docker compose logs api                # the traceback, if any
docker compose config                  # the resolved config: missing env var, bad path
```

If logs are empty even though the app is running, check that `PYTHONUNBUFFERED=1` is set; without it output sits in a buffer.

### The API cannot reach the database

```bash
docker compose ps                                          # is db healthy?
docker compose logs db --tail=50
docker compose exec api getent hosts db                    # does the name "db" resolve?
docker compose exec db pg_isready -U postgres -d scanflow
```

Docker's built-in DNS resolves service names on the Compose network; if `db` does not resolve, the containers are not on the same network.

### A gateway error from Nginx

| Status | Meaning | First three commands |
|---|---|---|
| **502** | Nginx reached a live host that refused or sent garbage: the API process is down but its container is up | `docker compose ps` → `docker compose logs api --tail=50` → `docker compose exec nginx wget -S -O- http://api:80/healthz` |
| **503** | Nginx itself refused the request, usually `limit_req` (rate limit) | `docker compose logs nginx --tail=20` → check the `limit_req` zone → wait and retry |
| **504** | Nginx waited and got nothing (5 s connect timeout): the API container is stopped or its IP changed | `docker compose ps` → `docker compose start api` → `docker compose exec nginx nginx -s reload` |

### I changed code and nothing changed

`./app` is bind-mounted, so a save is visible inside the container, but the running process has not reloaded. `docker compose restart api`. For Dockerfile or dependency changes, `docker compose up -d --build api`.

### Analysis never finishes

```bash
docker compose logs api --tail=100 | grep -i -E "analysis|worker"
docker compose exec db psql -U postgres -d scanflow -c "\dt"      # confirm the jobs table name
docker compose exec db psql -U postgres -d scanflow -c "SELECT id, scan_id, status, retry_count, error, created_at FROM analysis_jobs WHERE status IN ('uploaded','running') ORDER BY created_at;"
```

- Jobs sit in `uploaded` and nothing is logged: the worker task has stopped. Restart the API (`docker compose restart api`). `/healthz` will still say `ok`, because it only checks the database.
- Jobs in `running` for over a minute: stale-job recovery will return them to `uploaded` on its own.

### Status does not arrive live

The WebSocket may have dropped; the page reconnects with backoff and falls back to polling. Check that Nginx still forwards `Upgrade`/`Connection` for `/v1/ws/`, and that the ticket has not expired (about 30 s, single use).

### Upload returns `409 … Idempotency-Key … still being processed` and never clears

An upload that failed after the key was reserved (for example storage was down) leaves the reservation behind, so a retry with the **same key** is refused. Retry with a **new** key. To clear stuck reservations:

```bash
docker compose exec db psql -U postgres -d scanflow -c "DELETE FROM idempotency_records WHERE response_body IS NULL AND created_at < now() - interval '5 minutes';"
```

### Requests return `429`

Expected when a user exceeds the per-user limit (10 requests burst, refilling 1 per second) or makes too many login attempts (a burst of 5, then one per minute). Honour `Retry-After`.

### Every scan route returns `500` and Redis is down

The rate limiter has no fallback. `docker compose ps redis`, then `docker compose restart redis`.

### Uploads fail, or downloads are missing after a restart

Moto is not running, or it was restarted (it keeps data in memory). Start it, recreate the bucket (README step 2). Files uploaded before the restart are gone; their database rows now point at nothing.

---

## 9. Secrets and configuration

| Change | Effect | Steps |
|---|---|---|
| Rotate `JWT_SECRET` | Every logged-in user is signed out | Edit `.env.secret`, `docker compose up -d api` |
| Change the database password | Must match in two places | Update `DB_PASSWORD` **and** `POSTGRES_PASSWORD`; an existing volume keeps the old password until you run `ALTER USER postgres PASSWORD '…'` |
| Any `.env` edit | Not read until the container is recreated | `docker compose up -d` (a plain `restart` does not re-read env files) |

Never commit `.env`, `.env.secret`, or anything in `backups/`.

## 10. Known limits

- Moto keeps files in memory: a restart loses every uploaded file.
- One analysis worker inside the API process; no heartbeat, and a dead worker task is not restarted.
- WebSocket connections are tracked per API process; a second API process would not see them.
- The Quick Tunnel URL changes on every start and is capped at 200 in-flight requests.
- Backups cover the database only.

# ScanFlow Runbook

## 1. Bring the stack up

### Start the existing images

```powershell
docker compose up -d
```

### Rebuild and start after code/config changes

```powershell
docker compose up -d --build
```

### Check service status

```powershell
docker compose ps
```

Expected state:

```text
api        healthy
 db        healthy
nginx      running
```

### Check application health

```powershell
curl.exe http://localhost:8000/healthz
```

Expected:

```json
{"status":"ok","database":"connected"}
```

### Check the frontend

Open:

```text
http://localhost:8000
```

Log in through the application and confirm protected data is visible.

## 2. Logs and where to find them

The current services primarily log to Docker stdout/stderr. Use Docker Compose to inspect them.

### All services

```powershell
docker compose logs --timestamps
```

### API / FastAPI

```powershell
docker compose logs --timestamps api
```

Follow API logs live:

```powershell
docker compose logs -f --timestamps api
```

### PostgreSQL

```powershell
docker compose logs --timestamps db
```

Follow PostgreSQL logs live:

```powershell
docker compose logs -f --timestamps db
```

### Nginx

```powershell
docker compose logs --timestamps nginx
```

Nginx also writes logs inside the container:

```text
/var/log/nginx/access.log
/var/log/nginx/error.log
```

Read recent Nginx access logs:

```powershell
docker compose exec nginx sh -c 'tail -n 100 /var/log/nginx/access.log'
```

Read recent Nginx error logs:

```powershell
docker compose exec nginx sh -c 'tail -n 100 /var/log/nginx/error.log'
```

The custom access log includes request ID, status, request time, upstream response time, and upstream status.

---

## 3. Restart a single service

Restart only FastAPI:

```powershell
docker compose restart api
```

Restart only Nginx:

```powershell
docker compose restart nginx
```

Restart only PostgreSQL:

```powershell
docker compose restart db
```

After restarting API or Nginx, verify:

```powershell
curl.exe http://localhost:8000/healthz
```

Avoid restarting or recreating PostgreSQL casually during an incident. Confirm database health and the persistence volume first.

---

## 4. Stop and recover the whole stack

Stop containers while preserving named volumes:

```powershell
docker compose down
```

Start them again:

```powershell
docker compose up -d
```

Do **not** use this for a normal shutdown/restart:

```powershell
docker compose down -v
```

`-v` removes named volumes and can remove the PostgreSQL data volume.

---

## 5. Roll back a bad application deployment

Check the working tree first:

```powershell
git status
```

Inspect recent commits:

```powershell
git log --oneline -10
```

Return to a known-good commit in a controlled recovery:

```powershell
git checkout <known-good-commit>
docker compose up -d --build
```

Verify:

```powershell
docker compose ps
curl.exe http://localhost:8000/healthz
```

## 6. PostgreSQL backup with `pg_dump`

The tested backup used PostgreSQL custom format (`-Fc`).

### Create the backup on the Windows host

Create a backup :

```powershell
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > .\scanflow.dump
```

The result is a host-side file:

```text
scanflow\scanflow.dump
```

### Verify the backup exists

```powershell
Get-Item .\scanflow.dump
```

## 7. Restore into a fresh database

This procedure restores the backup into a **separate database** so the live `scanflow` database is not modified.

The actual ScanFlow environment uses:

```text
POSTGRES_USER = postgres
POSTGRES_DB   = scanflow
```

### Copy the dump into the PostgreSQL container

When the dump is on the host as `scanflow.dump`:

```powershell
docker cp .\scanflow.dump scanflow-postgres:/tmp/scanflow.dump
```

### Create a fresh restore database

Use direct `psql` arguments on PowerShell to avoid nested shell-quoting problems:

```powershell
docker compose exec -T db psql -U postgres -d scanflow -c "CREATE DATABASE scanflow_restore;"
```

Expected:

```text
CREATE DATABASE
```

### Restore the dump

```powershell
docker compose exec -T db pg_restore -U postgres -d scanflow_restore /tmp/scanflow.dump
```

### Verify the restored schema

```powershell
docker compose exec -T db psql -U postgres -d scanflow_restore -c "\dt"
```

The verified restore contained these tables:

```text
alembic_version
analysis_jobs
audit_log
patients
reports
scans
users
```

### Verify representative application data

```powershell
docker compose exec -T db psql -U postgres -d scanflow_restore -c "SELECT synthetic_study_id, dob, sex FROM patients LIMIT 1;"
```

The actual restore drill returned:

```text
074a4ea1-a1a3-4b31-b387-1e6ae1c8f3e4 | 1985-01-04 | male
```
the dump was restored into a fresh database and real application data was recovered.

### Cleanup the temporary restore database

After verification:

```powershell
docker compose exec -T db psql -U postgres -d scanflow -c "DROP DATABASE IF EXISTS scanflow_restore WITH (FORCE);"
```

This does not remove the live `scanflow` database or the `postgres-data` volume.
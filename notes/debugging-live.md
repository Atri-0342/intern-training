## 1. Container exits instantly on startup

Check container logs:
```bash
docker compose logs api
```

Check the resolved Compose configuration:
```bash
docker compose config
```

Check container status:
```bash
docker compose ps
```

These help determine whether the container failed during startup and why.

---

## 2. API cannot reach the database

Check whether the database container is running and healthy:
```bash
docker compose ps
```

Check database logs:
```bash
docker compose logs db
```

Check DNS resolution from the API container:
```bash
docker compose exec api getent hosts db
```

Test PostgreSQL connectivity from the API container:
```bash
docker compose exec api pg_isready -h db -U postgres -d scanflow
```

Check the database health directly:
```bash
docker compose exec db pg_isready -U postgres -d scanflow
```

**The debugging flow is:**
```
API container
    ↓
resolve "db"
    ↓
reach PostgreSQL
    ↓
check PostgreSQL health/logs
```

---

## 3. Code changed but behaviour did not

Check the running container:
```bash
docker compose ps
```

Check the image currently used by the API:
```bash
docker compose images api
```

Rebuild the API image:
```bash
docker compose up -d --build api
```

Check the API logs after rebuilding:
```bash
docker compose logs api --tail=50
```

Because the current Compose setup bind-mounts:
```yaml
- ./app:/code/app
```
normal Python source changes are immediately visible inside the container. A rebuild is mainly relevant for Dockerfile or dependency changes.

---

## 4. Logs are empty

Check the container logs:
```bash
docker compose logs api
```

Check the last lines:
```bash
docker compose logs api --tail=100
```

Check whether the process is writing to stdout/stderr:
```bash
docker compose exec api sh -c 'ls -l /proc/1/fd/1 /proc/1/fd/2'
```

Check the configured logging level:
```bash
docker compose exec api env | grep -i log
```

Docker normally captures application output written to stdout/stderr.

---

## 5. 502/504 Gateway failure — API unavailable

Stopped the API:
```bash
docker compose stop api
```

Tested through Nginx:
```powershell
curl.exe -i http://localhost:8000/v1/scans
```

**Observed:**
```
HTTP/1.1 504 Gateway Time-out
```

Checked Nginx logs:
```bash
docker compose logs nginx --tail=50
```

**Nginx reported:**
```
upstream timed out (110: Operation timed out) while connecting to upstream
```

**The upstream was:**
```
http://172.19.0.3:80/v1/scans
```

**The request took approximately 5 seconds:**
```
request_time=5.002
upstream_response_time=5.005
upstream_status=504
```

This matched the configured:
```nginx
proxy_connect_timeout 5s;
```

Checked service state:
```bash
docker compose ps
```

Restored API:
```bash
docker compose start api
```

Verified recovery:
```bash
curl.exe http://localhost:8000/healthz
```

> The Nginx error output was visible through Docker logs rather than the container's `/var/log/nginx/error.log` in this setup.

---

## 6. Database slow-query debugging

Enabled slow-query logging:
```bash
docker compose exec db psql -U postgres -d scanflow -c "ALTER SYSTEM SET log_min_duration_statement = 100"
```

Reloaded PostgreSQL configuration:
```bash
docker compose exec db psql -U postgres -d scanflow -c "SELECT pg_reload_conf();"
```

Created a deliberately slow query:
```bash
docker compose exec db psql -U postgres -d scanflow -c "SELECT pg_sleep(1);"
```

Checked database logs:
```bash
docker compose logs db --tail=50
```

**Observed approximately:**
```
parameter "log_min_duration_statement" changed to "100"
duration: 1022.501 ms
statement: SELECT pg_sleep(1);
```

This demonstrated how PostgreSQL can identify queries exceeding the configured duration threshold.

---

## 7. Check active database queries

Started a long-running query:
```bash
docker compose exec db psql -U postgres -d scanflow -c "SELECT pg_sleep(30);"
```

From another terminal, checked `pg_stat_activity`:
```bash
docker compose exec db psql -U postgres -d scanflow -c "SELECT pid, usename, state, query, query_start FROM pg_stat_activity WHERE datname = 'scanflow';"
```

This showed the active query and its process ID. `pg_stat_activity` is useful for finding queries that are currently running or stuck.

---

## 8. Database lock debugging

Created a test table:
```sql
CREATE TABLE IF NOT EXISTS debug_lock_test (
    id integer PRIMARY KEY
);
```

Started a transaction and acquired an exclusive lock:
```sql
BEGIN;
LOCK TABLE debug_lock_test IN ACCESS EXCLUSIVE MODE;
```

Checked locks:
```bash
docker compose exec db psql -U postgres -d scanflow -c "SELECT pid, relation::regclass, mode, granted FROM pg_locks WHERE relation::regclass::text = 'debug_lock_test';"
```

Started another transaction requesting a conflicting lock:
```sql
BEGIN;
LOCK TABLE debug_lock_test IN ACCESS SHARE MODE;
```

The second session became blocked. `pg_locks` showed:

| pid | relation | mode | granted |
|---|---|---|---|
| 39911 | debug_lock_test | AccessShareLock | f |
| 39830 | debug_lock_test | AccessExclusiveLock | t |

**Meaning:**
- `granted = t` → lock acquired
- `granted = f` → waiting for the lock

Released the first lock:
```sql
ROLLBACK;
```

The waiting lock was then granted.

---

## 9. Request-ID tracing

Nginx generates the request ID:
```nginx
$request_id
```

and passes it to the API:
```nginx
proxy_set_header X-Request-ID $request_id;
```

FastAPI reads it:
```python
request_id = request.headers.get("X-Request-ID")
```

and logs it:
```
request_id=ae024df5040a1a41e0525d1133244164
```

The same request ID was then stored with the analysis job and printed by the worker.

**Nginx log**
```
request_id=ae024df5040a1a41e0525d1133244164
status=202
upstream_status=202
```

**FastAPI application log**
```
request_id=ae024df5040a1a41e0525d1133244164
method=POST
path=/v1/scans/.../analyze
status=202
```

**Worker log**
```
Processing analysis job: ... request_id=ae024df5040a1a41e0525d1133244164
Completed analysis job: ... request_id=ae024df5040a1a41e0525d1133244164
```

**Therefore one request could be followed:**
```
Nginx
  ↓
FastAPI
  ↓
Analysis Worker
```
using the same request ID: `ae024df5040a1a41e0525d1133244164`
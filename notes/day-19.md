# Day 19 — Database Integration, CRUD, Indexes & Transactions

## What We Learned

* Connected FastAPI to PostgreSQL using SQLAlchemy 2.0 + psycopg.
* Used SQLAlchemy ORM models for `Patient`, `Scan`, `Report`, and `AuditLog`.
* Used `Session` and `sessionmaker` for database operations.
* Understood CRUD operations with a real PostgreSQL database.
* Used Alembic migrations to keep the database schema versioned.
* Learned how indexes improve filtered queries.
* Used `EXPLAIN ANALYZE` to verify whether PostgreSQL actually uses an index.
* Learned database transactions: multiple operations can succeed or fail as one unit.
* Learned why audit logging should happen inside the same transaction as the main mutation.
* Proved transaction atomicity by intentionally causing an audit failure.

## What We Built

### 1. Real PostgreSQL Integration

Replaced the temporary in-memory storage with PostgreSQL through SQLAlchemy.

Implemented:

* Database engine
* `SessionLocal`
* `get_db()` dependency
* ORM models
* PostgreSQL connection through `.env`

### 2. Full CRUD

Implemented CRUD endpoints for:

* Patients
* Scans
* Reports

Patient example:

```text
POST   /v1/patients
GET    /v1/patients/{id}
GET    /v1/patients
PATCH  /v1/patients/{id}
DELETE /v1/patients/{id}
```

Similar CRUD was implemented for scans and reports.

### 3. Scan Filtering

Added filters to:

```text
GET /v1/scans
```

Supported:

* `modality`
* `status`
* `acquired_at_from`
* `acquired_at_to`

### 4. Index Verification

Verified both indexes with `EXPLAIN ANALYZE`.

For:

```sql
WHERE modality = 'MRI'
AND acquired_at >= ...
AND acquired_at <= ...
```

PostgreSQL used:

```text
idx_scans_modality_acquired_at
```

For date-only filtering, PostgreSQL used:

```text
idx_scans_acquired_at
```

This proved that the indexes were actually being used.

## Audit Logging

Created:

```text
app/db/audit.py
```

with:

```python
write_audit_log()
```

The helper adds the audit record but does **not** commit.

The endpoint performs:

```text
Main mutation
      ↓
Audit log
      ↓
Single db.commit()
```

This keeps both operations in the same transaction.

## Problems We Hit

### Problem 1 — FastAPI Couldn't Find `api`

Error:

```text
ModuleNotFoundError: No module named 'api'
```

Cause:

The project uses `app/` as the package root, but imports were written as if `api`, `db`, `models`, and `schemas` were top-level packages.

Fixed imports to:

```python
from app.api...
from app.db...
from app.models...
from app.schemas...
```

and ran:

```text
uvicorn app.main:app --reload
```

### Problem 2 — PostgreSQL Authentication Failed

Error:

```text
FATAL: password authentication failed for user "None"
```

Cause:

`DB_USER`, `DB_PASSWORD`, and `DB_NAME` were loading as `None`.

The `.env` existed in `scanflow/`, but `load_dotenv()` wasn't resolving it correctly.

Fixed `config.py` to explicitly locate:

```text
scanflow/.env
```

using `pathlib.Path`.

Verified:

```text
USER: postgres
PASSWORD LOADED: True
DB: scanflow
```

After that, PostgreSQL connections worked.

### Problem 3 — Audit Transaction Testing

Normal patient creation successfully created:

```text
patients row
+
audit_log row
```

Then we temporarily forced:

```python
raise RuntimeError("TEST: force audit failure")
```

The request returned:

```text
500 Internal Server Error
```

We checked PostgreSQL and confirmed:

```text
patients  → 0 rows
audit_log → 0 rows
```

This proved that the failed operation did not leave a partially committed patient record.

The temporary failure was then removed.

## Key Takeaways

1. **Database code should use environment variables, never hardcoded credentials.**
2. **ORM code still depends on the underlying database connection being correctly configured.**
3. **Indexes should be verified with `EXPLAIN ANALYZE`, not assumed to work.**
4. **Audit logging should participate in the same transaction as the mutation.**
5. **A transaction is useful because related operations can succeed or fail together.**
6. **A successful implementation should be tested by deliberately causing failure and checking rollback behavior.**

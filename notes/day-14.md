# Day 14 — Psycopg 3: Python communicate to PostgreSQL

## 1. Psycopg 3 Setup

Installed Psycopg 3 with:

    pip install "psycopg[binary]"

Installed the connection-pooling package with:

    pip install psycopg_pool

## 2. Repository Functions

Created repository functions using plain SQL instead of an ORM.

The repository functions implemented were:

- `create_scan()`
- `get_scan()`
- `list_scans()`
- `attach_report()`
- `claim_next_pending_scan()`

All database operations use Psycopg and parameterized SQL.

### 2.1 create_scan()

Creates a new scan record.

The function inserts:

- scan ID
- patient ID
- modality
- body part
- acquisition time
- status

The inserted row is returned using `RETURNING *` and retrieved using `cur.fetchone()`.

### 2.2 get_scan()

Retrieves a scan using its ID.

The query uses a parameterized condition:

    WHERE id = %s;

Returns one row using `cur.fetchone()`.

If no scan exists, the result is `None`.

### 2.3 list_scans()

Retrieves multiple scans with optional filters.
Filters include:

- `patient_id`
- `modality`
- `status`
- `body_part`

The query is constructed dynamically only for the SQL structure. The actual filter values are still passed separately as parameters.

The result uses `cur.fetchall()`.

    LIMIT %s
    OFFSET %s

Results are ordered by:

    ORDER BY acquired_at DESC

### 2.4 attach_report()

Creates a report and associates it with an existing scan.

The relationship is established using:

    reports.scan_id = scans.id

The function inserts:

- report ID
- scan ID
- findings
- radiologist ID
- finalized time

The inserted report is returned using `RETURNING *`.

### 2.5 claim_next_pending_scan()

Claims the next uploaded scan for processing.

The query uses:

    FOR UPDATE SKIP LOCKED

This allows multiple workers to safely claim scans without waiting on scans already locked by another worker.

The selected scan is changed from:

    uploaded

to:

    processing

The updated row is returned.

## 3. Context Managers and Transactions

Database connections and cursors are managed using Python context managers.

General pattern:

    with psycopg.connect(...) as conn:
        with conn.cursor() as cur:
            ...

This ensures resources are properly closed. The connection context manager also handles the transaction. If the block completes successfully, the transaction can commit. If an exception occurs or the process is interrupted before successful completion, the unfinished transaction is rolled back.

## 4. Transaction Crash Test

Created: transaction_crash_test.py

The script inserted a scan inside a transaction and then paused before the transaction completed.

The process was interrupted using `Ctrl+C`.

The script displayed a generated scan ID:

    Created scan ID: 0f366af3-37df-49b7-97c3-e7683d6ca416
    Row inserted inside transaction.
    Kill this process now.

The process was then interrupted and produced:

    KeyboardInterrupt

Afterward, the scan ID was checked in PostgreSQL:

    SELECT *
    FROM scans
    WHERE id = '0f366af3-37df-49b7-97c3-e7683d6ca416';

Result:

    (0 rows)

This proved that the uncommitted transaction did not saved after the process was interrupted.

## 5. SQL Injection

Created: sql_injection_test.py

The purpose was to deliberately create a vulnerable SQL query, perform an attack, and then fix the vulnerability using parameterized queries.

## 6. Vulnerable SQL Query

The deliberately vulnerable function constructed SQL using an f-string:

    query = f"""
        SELECT *
        FROM injection_test
        WHERE body_part = '{body_part}';
    """

This is unsafe because user controlled input becomes part of the SQL statement itself. The database cannot distinguish between normal data and SQL syntax when user input is directly concatenated into the query.

## 7. SQL Injection Demonstration

A disposable table named `injection_test` was created so the real application tables would not be affected.

The table contained: id, body_part

First, a normal query using 'Shoulder' returned the matching rows.

Then the injection: ' OR '1'='1 was used.

The generated SQL became:

    SELECT *
    FROM injection_test
    WHERE body_part = '' OR '1'='1';

Because '1'='1' is always true, the query returned all rows.

In the existing database, the injection returned approximately 200,000 scan rows.

## 8. DROP TABLE SQL Injection Attack

    '; DROP TABLE ...; --

The malicious input was:

    '; DROP TABLE injection_test; --

The vulnerable function generated SQL equivalent to:

    SELECT *
    FROM injection_test
    WHERE body_part = ''; DROP TABLE injection_test; --';

The SQL contained two statements:

    SELECT ...

and:

    DROP TABLE injection_test;

The `--` commented out the remaining characters.

After executing the attack, PostgreSQL was checked with: SELECT * FROM injection_test;

PostgreSQL returned: ERROR: relation "injection_test" does not exist

This proved that the SQL injection successfully executed the `DROP TABLE` statement.

## 9. Fixing SQL Injection

The vulnerable query was replaced with a parameterized query:

    cur.execute(
        """
        SELECT *
        FROM injection_test
        WHERE body_part = %s;
        """,
        (body_part,),
    )

The important change is that `body_part` is no longer inserted into the SQL string. Instead, the SQL structure and parameter value are handled separately.

The malicious input:

    '; DROP TABLE injection_test; --

is therefore treated as a literal value rather than executable SQL i.e. body_part="'; DROP TABLE injection_test; --"

The query returned:

    []

because there was no row whose `body_part` literally matched the malicious string.

## 10. Connection Pooling

A connection pool maintains reusable PostgreSQL connections.

Instead of repeatedly creating and destroying connections, the application can borrow a connection from the pool, use it, and return it to the pool.

## 11. Connection Pool Configuration

The test pool was configured with:

    ConnectionPool(
        conninfo=...,
        min_size=5,
        max_size=5,
    )

Meaning:

- `min_size=5` -> maintain at least 5 connections
- `max_size=5` -> allow at most 5 connections

If connections are busy, additional requests wait until a connection is returned to the pool.

## 12. Load Test

Created: pool_test.py

The test executed 50 simple: SELECT 1; operations.

Two approaches were compared.

### 12.1 Without Connection Pooling

For every query connection built and after end of query connection close

This process was repeated 50 times.

Measured result:

    Normal connections: 1.7996 seconds

### 12.2 With Connection Pooling

The pool maintained five reusable connections.

A connection pool keeps a set of reusable database connections. When a query needs to run, it borrows an available connection from the pool, executes the query, and then returns the connection to the pool. The connection is not closed, so it can be borrowed again for the next query, avoiding the overhead of creating a new database connection every time.

The connections were reused across the 50 operations.

Measured result:

    Pool connections: 0.1058 seconds

The connection-pool test was approximately 17 times faster in this particular run.

## 13. Lessons

### Psycopg

Psycopg 3 allows Python applications to communicate directly with PostgreSQL without an ORM.

### Repository Pattern

Database operations can be isolated into repository functions containing plain SQL.

### Context Managers

Use context managers so connections, cursors, and transactions are properly managed.

### Transactions

An unfinished transaction is rolled back when the connection closes without a successful completion.

### SQL Injection

Never build SQL queries by directly inserting user-controlled values into SQL strings.

Unsafe:

    query = f"SELECT * FROM scans WHERE body_part = '{body_part}'"

Safe:

    cur.execute(
        "SELECT * FROM scans WHERE body_part = %s",
        (body_part,),
    )

### Parameterized Queries

Parameters are treated as values rather than executable SQL syntax.

### Connection Pooling

Connection pools reuse database connections and can significantly reduce connection overhead, especially when an application handles many database operations.

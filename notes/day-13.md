# Day 12 — PostgreSQL Concurrency

## 1. Transaction Isolation

Transaction isolation controls what one transaction can see while another transaction is changing the database.

The main levels I learned about were:

- READ COMMITTED
- REPEATABLE READ
- SERIALIZABLE

### READ COMMITTED

Each SQL statement gets a fresh snapshot.

Example:

    BEGIN ISOLATION LEVEL READ COMMITTED;
    SELECT balance
    FROM accounts
    WHERE id = 1;

If another transaction changes and commits the balance:

    UPDATE accounts
    SET balance = 500
    WHERE id = 1;
    COMMIT;

Then the first transaction runs and can now see `500`.

### REPEATABLE READ

The transaction keeps the same snapshot.

Example:

    BEGIN ISOLATION LEVEL REPEATABLE READ;
    SELECT balance
    FROM accounts
    WHERE id = 1;
Result:
    500

If another transaction changes the balance and commits:

    UPDATE accounts
    SET balance = 700
    WHERE id = 1;
    COMMIT;

The first transaction runs the SELECT again it still sees the value from its original snapshot. i.e. 500

# 2. Non-Repeatable Read

A non repeatable read happens when I read the same row twice and another transaction changes saved.

### Example

Session A:

    BEGIN ISOLATION LEVEL READ COMMITTED;
    SELECT balance
    FROM accounts
    WHERE id = 1;

Suppose A sees:1000

Session B:

    BEGIN;
    UPDATE accounts
    SET balance = 500
    WHERE id = 1;
    COMMIT;

Session A runs again:

    SELECT balance
    FROM accounts
    WHERE id = 1;

Now A sees: 500

    First read  := 1000
    B changes   := 500
    Second read := 500

This is a non-repeatable read.

### REPEATABLE READ

If A starts with:

    BEGIN ISOLATION LEVEL REPEATABLE READ;

and reads `1000`, then B changes it to `500` and commits, A's second SELECT still sees: 1000 because it has its old snap

Therefore REPEATABLE READ prevents the non-repeatable read.

# 3. Phantom Read

A phantom read is about the **set of rows returned by a query**.

### Example

Session A:

    BEGIN ISOLATION LEVEL READ COMMITTED;
    SELECT *
    FROM accounts
    WHERE balance >= 500;

Suppose A sees:

    Alice
    Bob
    Charlie

Session B inserts another matching row:

    BEGIN;
    INSERT INTO accounts (id, name, balance)
    VALUES (4, 'David', 900);
    COMMIT;

Session A runs the same query again:

    SELECT *
    FROM accounts
    WHERE balance >= 500;

Now David also appears.

So:
    First query  := 3 rows
    B inserts    := David
    Second query := 4 rows

David is the phantom row.

### REPEATABLE READ

    BEGIN ISOLATION LEVEL REPEATABLE READ;

A continues using its original snapshot. Even after B inserts David and commits, A's repeated query still sees its original set of rows.
Hence REPEATABLE READ prevents the phantom read in this experiment.

# 4. Lost Update

A lost update happens when two transactions read the same old value and then one transaction overwrites the other's update.

### Example

Session A:

    BEGIN;
    SELECT balance
    FROM accounts
    WHERE id = 1;

A sees: 1000

Session B:

    BEGIN;
    SELECT balance
    FROM accounts
    WHERE id = 1;

B also sees: 1000

A updates:

    UPDATE accounts
    SET balance = 600
    WHERE id = 1;
    COMMIT;

B then writes its value based on the old value it previously read:

    UPDATE accounts
    SET balance = 500
    WHERE id = 1;
    COMMIT;

Final result:

    500

A's update to `600` was lost.


# 5. Lost Update Under REPEATABLE READ

Under REPEATABLE READ, PostgreSQL can reject the conflicting update instead of silently allowing the stale value to overwrite the newer value.

### Example

Session A:

    BEGIN ISOLATION LEVEL REPEATABLE READ;
    SELECT balance
    FROM accounts
    WHERE id = 1;

Session B:

    BEGIN ISOLATION LEVEL REPEATABLE READ;
    SELECT balance
    FROM accounts
    WHERE id = 1;

Both read the same old value.

A updates:

    UPDATE accounts
    SET balance = 600
    WHERE id = 1;
    COMMIT;

B tries:

    UPDATE accounts
    SET balance = 500
    WHERE id = 1;

PostgreSQL can return:

    ERROR: could not serialize access due to concurrent update

B must then:

    ROLLBACK;


# 7. Isolation Level Results

REPEATABLE READ prevents the non-repeatable reads, phantom reads, and lost-update pattern we tested by maintaining a stable snapshot and rejecting conflicting updates, while SERIALIZABLE provides a stricter guarantee by ensuring concurrent transactions produce a result equivalent to some serial execution.

# 8. FOR UPDATE

`FOR UPDATE` is used when I want to select a row and lock it for updating.

Example:

    BEGIN;
    SELECT *
    FROM accounts
    WHERE id = 1
    FOR UPDATE;

This means: Select account 1 and place a row level lock on it.

The lock remains until the transaction ends with COMMIT or ROLLBACK;

# 9. Deadlock

A deadlock happens when two transactions are waiting for each other.

### Step 1 — Session A

    BEGIN;
    SELECT *
    FROM accounts
    WHERE id = 1
    FOR UPDATE;

A now owns the lock on account 1.

### Step 2 — Session B

    BEGIN;
    SELECT *
    FROM accounts
    WHERE id = 2
    FOR UPDATE;

B now owns the lock on account 2.

### Step 3 — Session A

    SELECT *
    FROM accounts
    WHERE id = 2
    FOR UPDATE;

A cannot get account 2 because B owns it. So A waits for B

### Step 4 — Session B

    SELECT *
    FROM accounts
    WHERE id = 1
    FOR UPDATE;

B cannot get account 1 because A owns it. So B waits for A

A waits for B and B waits for A

This is a circular wait.

PostgreSQL detects the deadlock and aborts one transaction.

In my experiment, PostgreSQL aborted Session B and Session A's waiting query continued.

# 10. Deadlock Prevention

When a transaction needs to lock multiple rows:

Always lock the rows in the same order.

### Safe

    Session A: 1 -> 2

    Session B: 1 -> 2

### Dangerous

    Session A: 1 -> 2

    Session B: 2 -> 1

So the simple rule is:

Everyone should follow the same locking order.

# 11. SKIP LOCKED

`SKIP LOCKED` tells PostgreSQL:

 If the row is already locked by another transaction, don't wait for it. Skip it.

### Without SKIP LOCKED

    Row is locked and wait for the row and continue the process after it is released.

### With SKIP LOCKED

    Row is locked and Skip the row and Look for another available row.

# 12. SKIP LOCKED Experiment

### Session A

    BEGIN;
    SELECT *
    FROM accounts
    WHERE id = 1
    FOR UPDATE;

A now locks account 1.

### Session B

    BEGIN;
    SELECT *
    FROM accounts
    WHERE id = 1
    FOR UPDATE SKIP LOCKED;

Because A already holds the lock, B does not wait. It skips account 1.

The result is:

    (0 rows)

This showed me that `SKIP LOCKED` is useful when I don't want workers to wait for rows already being processed by another worker.

# What Confused Me
1. pgBench — I was confused about what it is used for and how it benchmarks PostgreSQL.

2. Session pooling vs transaction pooling — I was confused about how a database connection is assigned to a client in each mode, especially why session pooling keeps the same connection for the whole client session, while transaction pooling can give the client a different connection after each transaction.
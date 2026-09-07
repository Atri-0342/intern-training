# Day 10 — PostgreSQL Constraints, ACID & Schema Design

### PostgreSQL: Constraints

Constraints are rules applied to database tables and columns to maintain data integrity and prevent invalid data.

### NOT NULL

`NOT NULL` ensures that a column cannot contain `NULL`.

Example:

    CREATE TABLE users (
        email text NOT NULL
    );

Every row must have an email value.

### UNIQUE

`UNIQUE` ensures that values in a column are not duplicated. A normal PostgreSQL `UNIQUE` constraint allows multiple `NULL` values because `NULL` values are not considered equal.

Example:

    CREATE TABLE users (
        email text UNIQUE
    );

Two users cannot have the same email.

### CHECK

`CHECK` ensures that a value satisfies a specified condition.

Example:

    CREATE TABLE employees (
        age integer CHECK (age >= 18)
    );

This prevents invalid values such as an age below 18.

### PRIMARY KEY

A `PRIMARY KEY` uniquely identifies each row in a table.

A primary key automatically provides:

- `UNIQUE`
- `NOT NULL`

Example:

    CREATE TABLE students (
        id uuid PRIMARY KEY,
        name text NOT NULL
    );

Each student must have a unique and non-null `id`. PostgreSQL automatically creates a unique B-tree index to support the primary key.

### FOREIGN KEY

A `FOREIGN KEY` creates a relationship between two tables.

Example:

    CREATE TABLE orders (
        id uuid PRIMARY KEY,
        customer_id uuid REFERENCES customers(id)
    );

The `customer_id` must reference an existing `id` in the `customers` table.

### ON DELETE

`ON DELETE` determines what happens to related rows when the referenced row is deleted.

Common options:

- `RESTRICT` — Don't allow the parent to be deleted. prevents deletion when dependent rows exist.
- `CASCADE` — Delete the related child rows too. automatically deletes dependent rows.
- `SET NULL` — keeps the child row but changes the foreign key to `NULL`.

# ACID Databases

ACID describes four properties that make database transactions reliable.

## Atomicity

A transaction is treated as one unit. Either all operations succeed or none of them are applied.

Example:

    BEGIN;

    UPDATE accounts
    SET balance = balance - 100
    WHERE id = 1;

    UPDATE accounts
    SET balance = balance + 100
    WHERE id = 2;

    COMMIT;

If something goes wrong before the transaction is committed, the changes can be rolled back.

## Consistency

A transaction must leave the database in a valid state according to its rules and constraints and help maintain consistency.

For example:

- `PRIMARY KEY`
- `FOREIGN KEY`
- `CHECK`
- `NOT NULL`

## Isolation

Multiple transactions can run at the same time without incorrectly interfering with each other.

## Durability

Once a transaction has been successfully committed, its changes should remain saved even if the database later crashes.



# Practice

## 1. On a whiteboard, no autocomplete: a query joining three tables with a LEFT JOIN and a GROUP BY.
a(id, name)
b(id, a_id, c_id)
c(id, title)

SELECT a.id, a.name, COUNT(c.id)
FROM a LEFT JOIN b ON a.id = b.a_id
LEFT JOIN c ON b.c_id = c.id
GROUP BY a.id, a.name;

## 2. WHERE vs HAVING

`WHERE` filters individual rows before grouping. Simply it filters rows

`HAVING` filters groups after `GROUP BY`. Simply it filters groups

Example:

    SELECT department, COUNT(*)
    FROM employees
    WHERE age >= 18
    GROUP BY department
    HAVING COUNT(*) > 5;

Here:

- `WHERE` selects rows where `age >= 18`.
- `GROUP BY` creates groups by department.
- `HAVING` keeps only departments with more than 5 employees.

## 3. Why `timestamptz` and not `timestamp`?

`timestamptz` represents a specific point in time and handles timezone conversion.

`timestamp` does not contain timezone information.

`timestamptz` is useful when users or systems operate in different time zones. 

For example, an `orders` table might have:

    ordered_at timestamptz

For events such as orders, uploads, transactions, or scans where the exact moment matters, `timestamptz` is generally the safer choice.

## 4. What happens to a report row when its scan is deleted?

In the schema: reports.scan_id REFERENCES scans(id) ON DELETE CASCADE

Therefore, when a scan is deleted, its associated report is automatically deleted.

I chose ON DELETE CASCADE because a report depends on its scan, so deleting the scan should also delete its associated report.

## 5. Your query returns no rows and you expected some. What are your first three moves?

1. Check the data — run a simple SELECT * FROM table; to confirm the expected rows actually exist.
2. Check the filters/conditions — inspect WHERE, HAVING, ON, IN, BETWEEN, NULL comparisons, etc., and remove conditions one at a time to find what eliminates the rows.
3. Simplify the query — remove or isolate parts such as JOIN, GROUP BY, subqueries, or other clauses, then add them back one at a time to identify where the problem appears.
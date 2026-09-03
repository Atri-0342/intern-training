## PostgreSQL Official Tutorial — Chapters 1 & 2

### Chapter 1 — Getting Started

I studied:

- **Installation** — understanding how PostgreSQL is installed and run.
- **Architectural Fundamentals** — basic PostgreSQL architecture and how the server, databases, and clients interact.
- **Creating a Database** — creating a PostgreSQL database.
- **Accessing a Database** — connecting to and working with a PostgreSQL database.

### Chapter 2 — The SQL Language

I studied:

- **Introduction** — what SQL is and how it is used to interact with relational databases.
- **Concepts** — basic relational database and SQL concepts.
- **Creating a New Table** — using `CREATE TABLE`.
- **Populating a Table With Rows** — using `INSERT`.
- **Querying a Table** — using `SELECT` to retrieve data.
- **Joins Between Tables** — combining related data from multiple tables.
- **Aggregate Functions** — performing calculations such as `COUNT`, `AVG`, `SUM`, `MIN`, and `MAX`.
- **Updates** — modifying existing rows with `UPDATE`.
- **Deletions** — removing rows with `DELETE`.

### Important SQL Commands Learned

```sql
CREATE DATABASE database_name;

CREATE TABLE table_name (
    id INTEGER,
    name TEXT
);

INSERT INTO table_name (id, name)
VALUES (1, 'Example');

SELECT *
FROM table_name;

UPDATE table_name
SET name = 'Updated'
WHERE id = 1;

DELETE FROM table_name
WHERE id = 1;

# Day 7 — Filtering, Sorting, and Core SQL

### PostgreSQL Joins

A `JOIN` combines rows from two or more tables using a related column.

Example:

    SELECT *
    FROM a
    JOIN b
        ON a.id = b.id;

`ON` defines how the tables are related.

### Explicit JOIN vs Comma-Join

Preferred:

    SELECT *
    FROM a
    JOIN b
        ON a.id = b.id;

Older comma style:

    SELECT *
    FROM a, b
    WHERE a.id = b.id;

Explicit `JOIN ... ON` is better because the relationship between tables is clearly separated from filtering conditions.
It is easier to read, maintain, and less likely to accidentally create a Cartesian product.

## PostgreSQL Data Types

### text

Stores text of any reasonable length. `text` is useful when there is no specific business reason to impose a maximum character length.

    name text

### varchar

Stores variable-length text. Use it when a specific length limit is actually required.

    name varchar(100)

`varchar(n)` limits the maximum number of characters.

### timestamptz

It is generally preferred for real world timestamps because timezone differences can be handled correctly. This helps handle timestamps consistently across different timezones.

    time timestamptz

Use `timestamptz` for anything time related.

### timestamp

Stores a date and time without timezone information. Unlike `timestamptz`, it does not represent a timezone-aware point in time.

    created_at timestamp

### numeric

Stores exact decimal numbers. Useful when exact decimal precision matters, such as financial values.

    price numeric(10,2)

### float

Stores approximate decimal numbers. Useful for scientific or mathematical calculations where small floating-point approximations are acceptable.

    measurement float

### jsonb

Stores JSON data in a binary format that PostgreSQL can efficiently process and query. Useful for flexible or semi-structured information.

    metadata jsonb

### uuid

Stores universally unique identifiers. Useful when records need unique IDs that are not simple sequential integers.

    id uuid

## CREATE TABLE

Creates a new table.

    CREATE TABLE a (
        id integer PRIMARY KEY,
        name text,
        age integer
    );


## INSERT

Adds new rows to a table.

    INSERT INTO a (id, name, age)
    VALUES (1, 'John', 25);

Multiple rows:

    INSERT INTO a (id, name, age)
    VALUES
        (1, 'John', 25),
        (2, 'Alice', 30);


# DDL — Data Definition Language

DDL is used to create or change the structure of database objects.

Common DDL commands:

- `CREATE`
- `ALTER`
- `DROP`

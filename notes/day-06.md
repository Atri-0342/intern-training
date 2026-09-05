# Day 6 — Relational Model + First Queries

## Relational Model

A relational database stores data in tables.

- Table : collection of related data
- Row : one record
- Column : one attribute
- Primary Key : uniquely identifies a row
- Foreign Key : connects related tables

## Basic SQL

### SELECT : Used to retrieve data.

    SELECT name, age
    FROM a;

### WHERE : Used to filter rows.

    SELECT *
    FROM a
    WHERE age > 18;

### ORDER BY : Used to sort results.

    SELECT *
    FROM a
    ORDER BY age DESC;

### LIMIT : Limits the number of rows returned.

    SELECT *
    FROM a
    LIMIT 5;

## JOIN : Used to combine data from related tables.

    SELECT *
    FROM a
    JOIN b
    ON a.id = b.id;

`ON` defines how the two tables are related.

## Aggregate Functions

- COUNT() → counts rows
- SUM() → adds values
- AVG() → calculates the average
- MIN() → finds the smallest value
- MAX() → finds the largest value

Example:

    SELECT COUNT(*)
    FROM a;

## GROUP BY

Groups rows before applying aggregate functions.

    SELECT age, COUNT(*)
    FROM a
    GROUP BY age;

## UPDATE

Changes existing data.

    UPDATE a
    SET age = 26
    WHERE id = 1;
    
Without `WHERE`, every row can be updated.

## DELETE

Deletes rows.

    DELETE FROM a
    WHERE id = 1;

Without `WHERE`, all rows can be deleted.

## ALTER TABLE : Used to change the structure of an existing table.

### Add a Column

    ALTER TABLE a
    ADD COLUMN email text;

### Drop a Column

    ALTER TABLE a
    DROP COLUMN email;

### Rename a Column

    ALTER TABLE a
    RENAME COLUMN name TO full_name;

### Rename a Table

    ALTER TABLE a
    RENAME TO people;

### Change a Column Type

    ALTER TABLE a
    ALTER COLUMN age TYPE bigint;

### Set NOT NULL

    ALTER TABLE a
    ALTER COLUMN name SET NOT NULL;

### Remove NOT NULL

    ALTER TABLE a
    ALTER COLUMN name DROP NOT NULL;

### Set a Default Value

    ALTER TABLE a
    ALTER COLUMN age SET DEFAULT 0;

### Remove a Default Value

    ALTER TABLE a
    ALTER COLUMN age DROP DEFAULT;

### Add a Primary Key

    ALTER TABLE a
    ADD PRIMARY KEY (id);

### Drop a Primary Key

    ALTER TABLE a
    DROP CONSTRAINT a_pkey;

### Add a Foreign Key

    ALTER TABLE b
    ADD CONSTRAINT b_a_fk
    FOREIGN KEY (a_id) REFERENCES a(id);

### Drop a Foreign Key

    ALTER TABLE b
    DROP CONSTRAINT b_a_fk;

### DROP : Removes a database object.

Drop a column:

    ALTER TABLE a
    DROP COLUMN email;

Drop a table:

    DROP TABLE a;

## psql Commands

These are psql commands, not SQL commands.

- \l → list databases
- \c database_name → connect to a database
- \dt → list tables
- \d table_name → show table structure
- \? → show psql help
- \timing → show query execution time

## Normalization

Normalization organizes data to reduce unnecessary duplication.

### 1NF

Each column contains atomic values.

### 2NF

Every non-key column depends on the whole primary key.

### 3NF

Non-key columns depend only on the primary key.
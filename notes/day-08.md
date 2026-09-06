# Day 8 — Basic Join and Subqueries

## Basic

The **Basic** section covers the core SQL concepts:

- SELECT: retrieve data
- WHERE: filter data
- ORDER BY: sort data
- DISTINCT: remove duplicate results
- Aggregate functions: `COUNT()`, `SUM()`, `AVG()`, `MIN()`, `MAX()`
- GROUP BY: group rows for calculations

## Joins and Subqueries

### What is a JOIN?

A `JOIN` is used to combine data from two or more tables using a related column.

Example:

    SELECT *
    FROM a
    JOIN b
        ON a.id = b.id;

Here:

- `a` and `b` are tables.
- `a.id` and `b.id` are the related columns.
- `ON` tells SQL how the tables are connected.

### INNER JOIN

Returns only rows that have a match in both tables.

    SELECT *
    FROM a
    INNER JOIN b
        ON a.id = b.id;

### LEFT JOIN

Returns all rows from the left table, plus matching rows from the right table.

    SELECT *
    FROM a
    LEFT JOIN b
        ON a.id = b.id;

If a row in `a` has no matching row in `b`, the columns from `b` will contain `NULL`.

### RIGHT JOIN

Returns all rows from the right table, plus matching rows from the left table.

    SELECT *
    FROM a
    RIGHT JOIN b
        ON a.id = b.id;

### FULL OUTER JOIN

Returns all rows from both tables. Matching rows are combined. Rows without a match have `NULL` values for the missing table's columns.

    SELECT *
    FROM a
    FULL OUTER JOIN b
        ON a.id = b.id;

### SELF JOIN

A self join joins a table with itself. It is useful when rows in the same table are related to each other.

Example:

    SELECT
        e.name,
        m.name AS manager
    FROM employees e
    JOIN employees m
        ON e.manager_id = m.id;

Here the `employees` table is used twice and `e` and `m` used as alias to remove ambiguity

## What is a Subquery?

A subquery is a SQL query written inside another SQL query. The inner query produces a result that the outer query uses.

Example:

    SELECT name
    FROM employees
    WHERE salary > (
        SELECT AVG(salary)
        FROM employees
    );

The inner query:

    SELECT AVG(salary)
    FROM employees;

calculates the average salary and the outer query then finds employees whose salary is greater than that average.

## When to Use JOIN vs Subquery

### Use a JOIN when:

Use a `JOIN` when you need to combine information from different tables.

For example, if one table contains employees and another contains departments, and you want the employee name and department name together:

    SELECT e.name, d.department_name
    FROM employees e
    JOIN departments d
        ON e.department_id = d.id;

    "I need data from multiple tables." -> JOIN

### Use a Subquery when:

Use a subquery when you need the result of one query to help another query.

For example, finding employees whose salary is greater than the average salary:

    SELECT name, salary
    FROM employees
    WHERE salary > (
        SELECT AVG(salary)
        FROM employees
    );

    "I need the result of another query first." -> Subquery

### Simple Rule

    Need to combine data from tables? -> JOIN

    Need one query's result inside another? -> Subquery

Sometimes the same problem can be solved using either a `JOIN` or a subquery.

The choice depends on:

- What makes the query easier to understand.
- Whether you need columns from another table.
- Whether you are using the result of one query as a condition for another.

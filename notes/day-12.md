# Day 12 — Query Performance, EXPLAIN & N+1

## What I Learned

### 1. EXPLAIN

`EXPLAIN` shows the execution plan PostgreSQL's query planner chooses for a SQL query.

It helps us understand:

- How PostgreSQL plans to execute the query
- Which scan method it chooses
- Whether an index is being used
- Estimated number of rows
- Estimated execution cost
- How tables and operations are connected in the plan

Basic syntax:

    EXPLAIN SELECT ...

Where:
    SQL query -> PostgreSQL Planner -> Execution Plan -> PostgreSQL executes the plan

### 2. EXPLAIN ANALYZE

`EXPLAIN ANALYZE` actually executes the query and shows the real execution statistics.

Example:

    EXPLAIN (ANALYZE, BUFFERS)
    SELECT COUNT(*)
    FROM scans
    WHERE acquired_at >= '2025-06-01 00:00:00+00'
    AND acquired_at < '2025-06-02 00:00:00+00';

`EXPLAIN` gives estimated information. shows what PostgreSQL expects to happen

`EXPLAIN ANALYZE` gives estimated + actual information. executes the query and shows what actually happened

### 3. Reading a Query Plan

A query plan is represented as a tree.

The lower nodes generally perform the actual data access, while the upper nodes process those results. we should read from the bottom upward.

### 4. Estimated Rows vs Actual Rows

Example:

    rows=267
    actual rows=287

This means PostgreSQL expected approximately 267 rows but actually processed 287. That is a reasonably accurate estimate. A large difference can indicate that PostgreSQL's statistics do not accurately represent the data distribution.

Example:

    estimated rows = 10
    actual rows = 10,000

This is a major estimation error and may cause PostgreSQL to choose a poor execution plan.

### 5. Query Cost

A query plan contains values such as:

    cost=0.42..13.76

The cost is NOT execution time in milliseconds. It is an internal relative value PostgreSQL uses to compare possible execution strategies. 
Actual execution time comes from `EXPLAIN ANALYZE`.

### 6. Scan Types

PostgreSQL can access table data in different ways.

### Sequential Scan

PostgreSQL reads rows from the table sequentially.A sequential scan is NOT automatically bad. If a query needs a large portion of a table, reading the table sequentially can be cheaper than using an index.

### Index Scan

PostgreSQL uses an index to locate matching rows. Indexes are especially useful when the query selects a relatively small portion of the table.

### Index Only Scan

An Index Only Scan can answer the query using the index without needing to fetch the corresponding table rows.

For example in the first Day-12 query:

    Index Only Scan using idx_scans_acquired_at

PostgreSQL used the index we created during Day 11.

I also saw:

    Heap Fetches: 0

This meant PostgreSQL did not need to fetch rows from the table heap for that query.

### 7. Buffers

`BUFFERS` gives information about PostgreSQL's buffer activity.

Example:

    Buffers: shared read=5

It helps us understand how much data PostgreSQL had to read or access while executing the query. This gives more information than execution time alone.

### 8. Indexes Are Not Always Used

Having an index does not guarantee that PostgreSQL will use it. The planner considers the query, available indexes, estimated rows, table size, and statistics before choosing a plan.

For example, a normal B-tree index may not be useful for a pattern such as:

    LIKE '%ohn%'

In such a situation, PostgreSQL may choose a sequential scan instead.

### 9. PostgreSQL Statistics

PostgreSQL uses statistics about the data to estimate how many rows a query will return.

We can refresh table statistics using:

    ANALYZE scans;

This is different from:

    EXPLAIN ANALYZE

`ANALYZE scans;` :-> updates PostgreSQL's statistics.

`EXPLAIN ANALYZE` :-> executes a query and reports actual execution information.

### 10. N+1 Query Problem

The N+1 problem happens when we execute:

    1 query + N additional queries

Usually it looks like:

    records = get_records()
    for record in records:
        get_related_data(record.id)

The first query gets the records. Then another query is executed for every record.

If there are 100 records:

    1 + 100 = 101 queries

This creates unnecessary database round trips.

A common solution is to retrieve the related information using a single query, often with a `JOIN`.

### 11. JOIN Instead of Repeated Queries

Instead of:

    Query 1 → get patients

    Query 2 → get scans for patient 1
    Query 3 → get scans for patient 2
    Query 4 → get scans for patient 3
    ...
    Query N+1 → get scans for patient N

We can often use one SQL query:

    patients JOIN scans

The database can then perform the operation internally instead of making many separate application to database requests.

## What Was Confusing

### 1. EXPLAIN vs EXPLAIN ANALYZE

Initially, it was easy to think they were the same.

The difference is:

    EXPLAIN :-> estimated execution plan

    EXPLAIN ANALYZE :-> executes the query + shows actual results

### 2. Cost vs Execution Time

The `cost` numbers looked like milliseconds. They are not.

For example:

    cost=0.42..13.76

does not mean:

    0.42 ms → 13.76 ms

They are planner cost units used to compare different plans.

### 3. Estimated Rows vs Actual Rows

The `rows` value inside the plan is an estimate.

For example:

    rows=267

does not mean PostgreSQL actually processed 267 rows.

The actual value could be:

    actual rows=287

Therefore, both values need to be checked.

### 4. Reading the Plan Tree

The execution plan is not written like normal SQL. It is a tree of operations.

The lower operation produces rows, and the upper operation processes those rows.

So the plan should be understood from the data-access operation upward.

### 5. Index Scan vs Index Only Scan

An Index Scan may use the index to find rows and then fetch the actual table rows.

An Index Only Scan can sometimes answer the query entirely from the index.

My first Day-12 query produced: Index Only Scan and: Heap Fetches: 0

This showed that the table itself did not need to be accessed for the required data.

### 7. ANALYZE vs EXPLAIN ANALYZE

The names are similar but their purposes are different.

    ANALYZE scans;

collects and updates statistics about the table.

    EXPLAIN ANALYZE
    SELECT ...;

executes the query and reports actual execution statistics.

### 8. N+1 Is Not About the Number N

The important part is not that there must literally be 10, 100, or 1,000 queries.

The pattern is:

    1 query + one additional query for each returned record

So if N records are returned:

    Total queries = N + 1

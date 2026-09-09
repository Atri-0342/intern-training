# ADR: Indexing Scan Queries

## Context

The `scans` table contains 200,000 synthetic rows.
The experiment was performed to determine whether indexing `acquired_at` improves the performance of time range queries and to understand how composite index column order affects query performance.

The main query tested was:

SELECT COUNT(*)
FROM scans
WHERE acquired_at >= '2025-06-01 00:00:00+00'
AND acquired_at < '2025-06-02 00:00:00+00';

## Decision

Use a B-tree index on `acquired_at` for queries that primarily filter scans by acquisition time.

Use a composite B-tree index `(modality, acquired_at)` for queries that filter by a specific modality and an acquisition time range.

## Why This Decision Was Made

The B-tree index on `acquired_at` was chosen because the actual measurement showed a significant improvement for the tested time-range query.

Without the index: 79.403 ms

With the B-tree index: 10.040 ms

Improvement: 79.403 / 10.040 = 7.91x

The composite index was created as:

CREATE INDEX idx_scans_modality_acquired_at
ON scans (modality, acquired_at);

The tested query filtered by both columns:

SELECT COUNT(*)
FROM scans
WHERE modality = 'MRI'
  AND acquired_at >= '2025-06-01 00:00:00+00'
  AND acquired_at < '2025-06-02 00:00:00+00';

It returned 94 rows and took: 4.333 ms

For `(modality, acquired_at)`, the index is ordered primarily by `modality` and then by `acquired_at` within each modality. `modality` was placed first because this query uses `modality` as an equality condition and then searches an `acquired_at` range.

## What Was Completed

* Generated a large synthetic dataset.
* Loaded 20,000 patients.
* Loaded 200,000 scans.
* Measured the `acquired_at` query without the custom index.
* Recorded **79.403 ms** as the baseline.
* Created the B-tree index on `acquired_at`.
* Measured the same query again.
* Recorded **10.040 ms**.
* Calculated an observed speedup of approximately **7.91x**.
* Created the composite index `(modality, acquired_at)`.
* Tested a query using both `modality` and `acquired_at`.
* Recorded **4.333 ms**.

## What Remains Unclear

### 1. Which index PostgreSQL actually uses

`EXPLAIN ANALYZE` still needs to be run to determine whether PostgreSQL chooses:

* `idx_scans_acquired_at`
* `idx_scans_modality_acquired_at`
* a sequential scan
* Or somthing else

### 3. Write cost

Read performance has been measured, but the cost of maintaining the indexes during bulk writes has not yet been measured.
The next experiment will compare bulk loading performance with and without the custom indexes.

## Consequences

The indexes require additional storage and must be maintained when rows are inserted, updated, or deleted.

Therefore, an index is not automatically beneficial simply because it can make a SELECT query faster.

The measured result shows that the `acquired_at` B-tree index significantly improved the tested query on 200,000 rows, but the execution plan behavior and write cost still need to be measured before making broader indexing decisions.
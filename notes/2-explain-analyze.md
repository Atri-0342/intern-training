## Query 1 — acquired_at Range Filter

### EXPLAIN ANALYZE

    EXPLAIN (ANALYZE, BUFFERS)
    SELECT COUNT(*)
    FROM scans
    WHERE acquired_at >= '2025-06-01 00:00:00+00'
      AND acquired_at < '2025-06-02 00:00:00+00';

### Explanation

- **Aggregate** — PostgreSQL performs the final `COUNT(*)` on the rows returned by the scan. It produces only one result row.
- **Index Only Scan** — PostgreSQL uses `idx_scans_acquired_at` to find rows within the requested date range. This is the **slowest node** because it performs the main data lookup, taking approximately 0.273–0.337 ms.
- **Index Cond** — confirms that the `acquired_at` range condition is being applied through the index.
- **Heap Fetches: 0** — PostgreSQL did not need to fetch any rows from the table heap because the index was sufficient for this query.
- **Index Searches: 1** — PostgreSQL performed one index search for the requested range.
- **Buffers: shared hit=5** — 5 required buffers were already available in memory, so no disk read was needed for these buffers.
- **Planning Time: 6.407 ms** — time PostgreSQL spent creating the execution plan.
- **Execution Time: 0.484 ms** — total time PostgreSQL spent executing the query.

### Observent

- **Slowest node:** Index Only Scan
- **Estimated rows:** 267
- **Actual rows:** 287
- **Plan acceptable:** Yes

The plan is acceptable because the estimated 267 rows are close to the actual 287 rows, indicating a reasonably accurate estimate. PostgreSQL also selected the `idx_scans_acquired_at` index, used an Index Only Scan, required zero heap fetches, and completed the query efficiently.



## Query 2 — Modality + acquired_at Filter

### EXPLAIN ANALYZE

    EXPLAIN (ANALYZE, BUFFERS)
    SELECT COUNT(*)
    FROM scans
    WHERE modality = 'MRI'
      AND acquired_at >= '2025-06-01 00:00:00+00'
      AND acquired_at < '2025-06-02 00:00:00+00';

### Explanation

- **Aggregate** — performs the final `COUNT(*)` and returns one result row.
- **Index Only Scan** — PostgreSQL uses `idx_scans_modality_acquired_at` to find rows matching both `modality = 'MRI'` and the `acquired_at` range. This is the **slowest node**, taking approximately 1.291–1.786 ms.
- **Index Cond** — shows that both filtering conditions are applied through the composite index.
- **Heap Fetches: 0** — no table rows had to be fetched; the index was sufficient.
- **Index Searches: 1** — one index search was performed for the requested range.
- **Buffers: shared hit=1 read=4** — 1 buffer was already in memory and 4 buffers had to be read.
- **Planning Time: 3.983 ms** — time PostgreSQL spent choosing the execution plan.
- **Execution Time: 1.874 ms** — total time spent executing the query.

### Observent

- **Slowest node:** Index Only Scan
- **Estimated rows:** 89
- **Actual rows:** 94
- **Plan acceptable:** Yes

The plan is acceptable because the estimated 89 rows are very close to the actual 94 rows. PostgreSQL also selected the appropriate composite index for `modality` and `acquired_at`, used an Index Only Scan, and required zero heap fetches.



## Query 3 — WHERE + GROUP BY + Aggregate

### EXPLAIN ANALYZE

    EXPLAIN (ANALYZE, BUFFERS)
    SELECT status, COUNT(*) AS scan_count
    FROM scans
    WHERE modality = 'CT'
    GROUP BY status;

### Explanation

- **Finalize GroupAggregate** — combines the partial counts produced by the parallel workers and returns the final count for each `status`.
- **Gather Merge** — collects the results from the workers and merges them for the final aggregation.
- **Sort** — sorts the partial results by `status`, which is required by the `GroupAggregate`.
- **Partial HashAggregate** — each worker calculates partial counts for each `status` before sending the results upward.
- **Parallel Seq Scan** — PostgreSQL scans the `scans` table in parallel and filters rows where `modality = 'CT'`. This is the **slowest node**, taking approximately 1.661–31.087 ms, because it has to scan a large portion of the table.
- **Rows Removed by Filter: 66690** — many rows were scanned but did not match `modality = 'CT'`.
- **Workers Planned: 1 / Workers Launched: 1** — PostgreSQL planned and started one additional worker, so the scan was performed in parallel.
- **Buffers: shared read=2992** — the query had to read 2992 shared buffers while scanning the table.
- **Planning Time: 6.464 ms** — time spent creating the execution plan.
- **Execution Time: 80.879 ms** — total time spent executing the query.

### Observent

- **Slowest node:** Parallel Seq Scan
- **Estimated rows:** 39,329 per worker
- **Actual rows:** 33,310.50 per worker
- **Plan acceptable:** Yes

The plan is acceptable because the estimated rows are reasonably close to the actual rows, and PostgreSQL correctly chose a Parallel Seq Scan because the query needs to examine a large portion of the 200,000-row table. Using an index is not automatically better when many rows need to be scanned.

The `GROUP BY` and aggregation are also handled efficiently using partial aggregation across the parallel workers.



## Query 4 — JOIN + GROUP BY + Aggregate

### Query

    
### Plan Explanation
EXPLAIN (ANALYZE, BUFFERS)
    SELECT p.sex, COUNT(*) AS scan_count
    FROM patients p
    JOIN scans s
        ON s.patient_id = p.synthetic_study_id
    GROUP BY p.sex;

- **Finalize GroupAggregate**
  - Finalizes the partial counts from the workers.
  - Groups the final result by `p.sex`.
  - Estimated rows: `3`
  - Actual rows: `3`
  - Returns one row for each sex category.

- **Gather Merge**
  - Collects the partial results from the parallel worker and leader.
  - Merges them using `p.sex`.
  - `Workers Planned: 1`
  - `Workers Launched: 1`

- **Sort**
  - Sorts the partial aggregation results by `p.sex`.
  - Uses `quicksort` with only `25kB` of memory.

- **Partial HashAggregate**
  - Each process calculates partial `COUNT(*)` values grouped by `p.sex`.
  - Estimated rows: `3`
  - Actual rows: `3` per loop.
  - The aggregation fits in memory: `Batches: 1`.

- **Hash Join**
  - Joins `scans` with `patients` using:
        s.patient_id = p.synthetic_study_id
  - Estimated rows: `117,647` per loop.
  - Actual rows: `100,000` per loop.
  - This is the main join operation.
  - PostgreSQL builds a hash table from `patients` and matches `scans` against it.

- **Parallel Seq Scan on scans**
  - Scans the `scans` table in parallel.
  - Estimated rows: `117,647` per loop.
  - Actual rows: `100,000` per loop.
  - Since most of the `scans` table participates in the join, scanning the table sequentially is reasonable.

- **Hash**
  - Builds an in-memory hash table from the `patients` rows.
  - Estimated rows: `20,000`
  - Actual rows: `20,000` per loop.
  - Memory usage: `1311kB`.

- **Seq Scan on patients**
  - Reads the `patients` table to build the hash table.
  - Estimated rows: `20,000`
  - Actual rows: `20,000` per loop.
  - The estimate is exact.

### Performance Assessment

- **Slowest/main expensive node:** `Hash Join`
  - Actual time: approximately `9.998–63.320 ms` per loop.
  - It performs the join between the large `scans` table and `patients`.

- **Estimated vs actual rows:**
  - Hash Join: `117,647` estimated vs `100,000` actual per loop.
  - This is about a `15%` difference, so the estimate is reasonably close.
  - `patients`: `20,000` estimated vs `20,000` actual — exact.
  - `scans`: `117,647` estimated vs `100,000` actual — reasonably close.

- **Total execution time:** `187.381 ms`

- **Plan acceptable:** **Yes.**
  - Row estimates are reasonably close.
  - The planner correctly uses a `Hash Join` for joining a large `scans` table with the smaller `patients` table.
  - Parallel scanning is used for the large `scans` table.
  - The hash table fits comfortably in memory.
  - There is no obvious estimation problem requiring `ANALYZE`.

### Key Observation

This query demonstrates that PostgreSQL can combine **parallel scanning → hash join → partial aggregation → sorting → final aggregation** into one execution plan. The sequential scan is not automatically bad; here, most of the `scans` rows participate in the join, making a sequential scan a reasonable choice.



## Query 5 — GROUP BY + Aggregate + ORDER BY + LIMIT

### Query

    EXPLAIN (ANALYZE, BUFFERS)
    SELECT p.synthetic_study_id, COUNT(s.id) AS scan_count
    FROM patients p
    LEFT JOIN scans s
        ON s.patient_id = p.synthetic_study_id
    GROUP BY p.synthetic_study_id
    ORDER BY scan_count DESC
    LIMIT 10;

### Plan Explanation

- **Limit**
  - Returns only the top 10 rows after sorting.
  - Estimated rows: `10`
  - Actual rows: `10`
  - Total query execution time: `178.472 ms`.

- **Sort**
  - Sorts patients by `COUNT(s.id)` in descending order.
  - `Sort Method: top-N heapsort` means PostgreSQL keeps only the best 10 rows needed for the `LIMIT`, instead of fully sorting all 20,000 rows.
  - Estimated rows before LIMIT: `20,000`
  - Actual rows processed: `20,000`
  - Memory usage: `26kB`.

- **HashAggregate**
  - Groups the joined data by `p.synthetic_study_id`.
  - Calculates `COUNT(s.id)` for each patient.
  - Estimated rows: `20,000`
  - Actual rows: `20,000`
  - `Batches: 1` means the aggregation fit in memory without spilling.
  - Memory usage: `1561kB`.

- **Hash Right Join**
  - PostgreSQL internally represents the `LEFT JOIN` as a `Hash Right Join`.
  - It joins `scans` to `patients` using:
        s.patient_id = p.synthetic_study_id
  - Estimated rows: `200,000`
  - Actual rows: `200,003`
  - The extra 3 rows come from patients that have no matching scan; the `LEFT JOIN` preserves those patients.

- **Seq Scan on scans**
  - Reads the entire `scans` table.
  - Estimated rows: `200,000`
  - Actual rows: `200,000`.
  - Since the query needs scan counts for every patient, PostgreSQL must examine the scan data.

- **Hash**
  - Builds an in-memory hash table from the `patients` table for the join.
  - Estimated rows: `20,000`
  - Actual rows: `20,000`
  - Memory usage: `1194kB`.

- **Seq Scan on patients**
  - Reads all `20,000` patients.
  - Estimated rows: `20,000`
  - Actual rows: `20,000`.
  - The estimate is exact.

### Performance Assessment

- **Slowest/main expensive node:** `Hash Right Join`
  - Actual time: approximately `6.473–102.004 ms`.
  - It must match all `200,000` scans against the `20,000` patients before aggregation.

- **Estimated vs actual rows:**
  - Hash Right Join: `200,000` estimated vs `200,003` actual — extremely close.
  - HashAggregate: `20,000` estimated vs `20,000` actual — exact.
  - Scans: `200,000` estimated vs `200,000` actual — exact.
  - Patients: `20,000` estimated vs `20,000` actual — exact.

- **Total execution time:** `178.472 ms`

- **Plan acceptable:** **Yes.**
  - Row estimates are extremely accurate.
  - The `LEFT JOIN` correctly preserves patients with no scans.
  - The hash join is appropriate because the query needs to process essentially the entire `scans` table.
  - The aggregation fits in memory.
  - `top-N heapsort` efficiently handles the `ORDER BY ... LIMIT 10` requirement without fully sorting all 20,000 grouped rows.

### Key Observation

This query demonstrates the full flow:

`Seq Scan → Hash Join → HashAggregate → Top-N Sort → Limit`

The `LIMIT 10` does **not** avoid processing all scans, because PostgreSQL must first calculate each patient's scan count before it knows which 10 patients have the highest counts.



## Query 6 — Subquery

### Query

    EXPLAIN (ANALYZE, BUFFERS)
    SELECT *
    FROM scans
    WHERE patient_id IN (
        SELECT patient_id
        FROM scans
        GROUP BY patient_id
        HAVING COUNT(*) > 10
    );

### Plan Explanation

- **Hash Join**
  - PostgreSQL transforms the `IN` subquery into a hash-based join.
  - It matches all scans against the patient IDs returned by the subquery.
  - Estimated rows: `66,663`
  - Actual rows: `108,035`
  - This is the main and most expensive operation.

- **Seq Scan on scans**
  - Reads all `200,000` scan rows for the outer query.
  - Estimated rows: `200,000`
  - Actual rows: `200,000`.

- **Hash**
  - Builds an in-memory hash table containing the patient IDs produced by the subquery.
  - Estimated rows: `6,428`
  - Actual rows: `8,304`.
  - Memory usage: `518kB`.

- **HashAggregate**
  - This is the subquery's main operation.
  - Groups scans by `patient_id` and calculates `COUNT(*)`.
  - `HAVING COUNT(*) > 10` removes patients with 10 or fewer scans.
  - Estimated rows: `6,428`
  - Actual rows: `8,304`.
  - `Rows Removed by Filter: 11,693`.
  - `Batches: 1` means the aggregation stayed in memory.

- **Seq Scan on scans_1**
  - Reads all `200,000` scans for the subquery.
  - Estimated rows: `200,000`
  - Actual rows: `200,000`.

### Performance Assessment

- **Slowest/main expensive node:** `Hash Join`
  - Actual time: approximately `41.173–128.062 ms`.
  - It matches the complete `scans` table against the patient IDs generated by the subquery.

- **Estimated vs actual rows:**
  - Hash Join: `66,663` estimated vs `108,035` actual.
  - HashAggregate: `6,428` estimated vs `8,304` actual.
  - The estimates are noticeably off, especially for the final join.

- **Total execution time:** `136.323 ms`

- **Plan acceptable:** **Yes**
  - The query completes successfully and the hash-based strategy is reasonable.
  - The sequential scans are expected because the query examines the full `scans` table twice.
  - However, the Hash Join estimate (`66,663` vs `108,035`) is off by about `1.6×`, so it is worth observing whether statistics become more accurate after `ANALYZE`.

### Observation

The SQL contains an `IN` subquery, but PostgreSQL does not necessarily execute it as a separate query first. Here, the planner converts it into a **Hash Join**:

`Seq Scan → HashAggregate → Hash → Hash Join`

The subquery first identifies patients with more than 10 scans, then the outer query retrieves all scans belonging to those patients.



## 2. Find a query where the estimate is off by more than 10×, run ANALYZE, re-check.

### Query

    EXPLAIN (ANALYZE, BUFFERS)
    SELECT *
    FROM scans
    WHERE modality = 'CT';

### Before ANALYZE

- Estimated rows: `66,860`
- Actual rows: `66,621`
- Estimate was already very close to the actual result.
- Difference was approximately `0.36%`.

### Run ANALYZE

    ANALYZE scans;

`ANALYZE` refreshes PostgreSQL's statistics about the data distribution in the `scans` table. These statistics help the query planner estimate the number of rows that will match a condition and choose an appropriate execution plan.

### After ANALYZE

- Estimated rows: `66,953`
- Actual rows: `66,621`
- The estimate changed from `66,860` to `66,953`.
- The actual number of matching rows remained `66,621`.

### Assessment

- `ANALYZE` successfully refreshed the planner statistics.
- The estimate changed only slightly because PostgreSQL's original statistics were already accurate.
- The execution plan remained a `Bitmap Heap Scan` using `idx_scans_modality_acquired_at`.
- This experiment did **not** produce the required >10× estimation error.
- Therefore, no claim is made that `ANALYZE` corrected a >10× estimation error.
- The result demonstrates that `ANALYZE` does not necessarily cause a large estimate change when the planner's existing statistics are already good.
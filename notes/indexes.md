# Index Experiment

## Goal

Understand how indexes affect query performance and write cost by measuring queries on a large dataset.

Dataset used:

- `patients`: 20,000 rows
- `scans`: 200,000 rows

Data was generated using Python, Faker and loaded into PostgreSQL using the SQL `COPY` command.

### Data Loading

Patients loaded from `patients.csv`:

    COPY patients(synthetic_study_id, dob, sex)
    FROM 'C:/path/scanflow/patients.csv'
    WITH (FORMAT csv, HEADER true);

Result:

    COPY 20000

Scans loaded from `scans.csv`:

    COPY scans(id, patient_id, modality, body_part, acquired_at, uploaded_at, status)
    FROM 'C:/path/scanflow/scans.csv'
    WITH (FORMAT csv, HEADER true);

Result:

    COPY 200000

The patients were loaded first because `scans.patient_id` references `patients.synthetic_study_id` through a foreign key.

## 1. Query Without an Index

Query used to filter scans acquired on June 1, 2025:

    SELECT COUNT(*)
    FROM scans
    WHERE acquired_at >= '2025-06-01 00:00:00+00'
      AND acquired_at < '2025-06-02 00:00:00+00';

Result:

    count
    -------
    287

Execution time: 79.403 ms

This was the baseline measurement before creating the custom `acquired_at` index.

## 2. B-tree Index on acquired_at

Created a B-tree index:

    CREATE INDEX idx_scans_acquired_at
    ON scans (acquired_at);

Index creation time: 298.209 ms

The same query was then executed again:

    SELECT COUNT(*)
    FROM scans
    WHERE acquired_at >= '2025-06-01 00:00:00+00'
    AND acquired_at < '2025-06-02 00:00:00+00';

Result:

    count
    -------
    287

Execution time: 10.040 ms

### Comparison

Without index: 79.403 ms

With B-tree index: 10.040 ms

Speedup: 79.403 / 10.040 = 7.91

The indexed query was approximately 7.91 times faster in this measurement.

## 3. Composite Index: (modality, acquired_at)

Created a composite B-tree index:

    CREATE INDEX idx_scans_modality_acquired_at
    ON scans (modality, acquired_at);

The first test query filters using both columns:

    SELECT COUNT(*)
    FROM scans
    WHERE modality = 'MRI'
    AND acquired_at >= '2025-06-01 00:00:00+00'
    AND acquired_at < '2025-06-02 00:00:00+00';

Result:

    count
    -------
    94

Execution time: 4.333 ms

### Column-order rule

For an index defined as: (modality, acquired_at)

the index is primarily ordered by `modality`, and then by `acquired_at` within each modality.

Therefore

    WHERE modality = 'MRI' AND acquired_at

is a natural match for this composite index.

A query using only:

    WHERE acquired_at

does not directly follow the normal leading column pattern because `modality` is the first indexed column.

### Conclusion

Indexes are not automatically faster for every query. `EXPLAIN ANALYZE` will be used to determine which index PostgreSQL actually chooses.

Their benefit depends on factors such as:

- how selective the query is
- how many rows match
- the columns and order used in the index
- the cost of accessing the table rows
- PostgreSQL's query planner decision

The measurements above are from the local PostgreSQL `scanflow` database and the 200,000-row synthetic `scans` dataset.
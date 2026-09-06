# Day 9 — Five SQL Queries

## Scan Table

| id | uuid | Unique ID for each patient/scan |
| name | text | Stores the patient's name |
| age | integer | Age is a whole number |
| scan_type | text | Stores MRI, CT, X-Ray, etc. |
| scan_date | timestamptz | Stores the scan date and time with timezone |
| report_text | text | Stores the radiology report |

## 1. Monthly Scan Counts

SELECT DATE_TRUNC('month', scan_date) AS month,
COUNT(*) AS scan_count
FROM scans
GROUP BY DATE_TRUNC('month', scan_date)
ORDER BY month;

## 2. Average Turnaround Per Scan Type

The current table does not contain a separate report date and time column, so an actual turnaround time cannot be calculated.

## 3. Top 10 Patients by Scan Count

SELECT name, COUNT(*) AS scan_count
FROM scans
GROUP BY name
ORDER BY scan_count DESC
LIMIT 10;

## 4. Scans With No Report

SELECT *
FROM scans
WHERE report_text IS NULL
OR report_text = '';

## 5. Running Total Using a Window Function

SELECT scan_date, name, scan_type,
COUNT(*) OVER (
    ORDER BY scan_date
) AS running_total
FROM scans
ORDER BY scan_date;
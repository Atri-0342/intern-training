# Day 1 — Python Project Hygiene

## Goal

Build a small Python data generation and reporting workflow while practicing
type annotations, data generation, CSV handling and Git.

## Learn

### Python Type Annotations

I used type annotations to make the expected structure and types of my data explicit.

I used `TypedDict` because my patient record is represented as a dictionary.

    class Patient(TypedDict):
        id: int
        name: str
        age: int
        scan_type: str
        scan_date: date
        report_text: str

The important distinction I learned is that type annotations do not automatically convert values.

For example, `age: int` describes the expected type, but it does not turn `"48"` into `48` when we extract data from CSV.

### Python Date vs CSV

I initially wondered why the generated `scan_date` appeared as:

datetime.date(2026, 1, 5)

This happens because Python represents the value as a `date` object.

When written to CSV, it becomes something like:

    2026-01-05

When the CSV is read back using `csv.DictReader`, the value comes back as a string.

Therefore, the CSV boundary is important values may need to be converted back into their appropriate Python types after reading.

### Faker

I used Faker instead of manually creating patient records because the goal was to generate enough data for report.

The data is synthetic and is not intended to represent real patients.

### Scan Type Specific Reports

I created a report collection for each scan type:

MRI
CT
X-Ray
Ultrasound

The report is selected from the collection corresponding to the generatedscan type.

### Ruff

I used Ruff to catch code quality issues.

I initially received an `I001` error because my imports were not ordered correctly.

Ruff reported that the imports should be organized with standard library imports before third-party imports.

After fixing the imports:

ruff check .

passed successfully.

This showed me that code can run correctly while still failing a project's linting rules.

## Build

### Patient Generator

I created `generate_data.py`.

The generator creates patient records containing:

`id`, `name`, `age`, `scan_type`, `scan_date`, `report_text`

I used: generate_patient(patient_id: int) -> Patient

to make the expected input and output types explicit.

### CSV Reporting

I created `csv_report.py` to read the generated CSV and calculate:

1. Number of patients for each scan type
2. Average age for each scan type
3. Number of empty reports

I used `Counter` to count scan types.

One generated dataset produced:

    MRI: 126
    X-Ray: 137
    CT: 118
    Ultrasound: 119

I also calculated average age by scan type.

One run produced:

    MRI: 50.83
    X-Ray: 51.97
    CT: 49.11
    Ultrasound: 49.40

### Empty Reports

I checked for empty report fields using `.strip()`.

The result was:

    Empty reports: 0

This makes sense because the generator currently assigns a report to every
patient.

## Wrap

### Completed

- Built a synthetic patient data generator.
- Added type annotations using `TypedDict`.
- Generated 500 patient records.
- Added scan-specific MRI, CT, X-Ray, and Ultrasound reports.
- Generated and read CSV data.
- Calculated scan-type counts and average ages.
- Checked for empty reports.
- Added Ruff and fixed its import-ordering error.
- Committed and pushed the Day 1 work to GitHub.

### What Failed

1. Running the generator initially failed with:

      ModuleNotFoundError: No module named 'faker'

  The problem was that Faker had been installed outside the project's active virtual environment.

2. After verifying:

      python -c "import sys; print(sys.executable)"

  I confirmed that the project was using:

      ScanFlow\.venv\Scripts\python.exe

  I then installed Faker into the correct environment.

3. Ruff also initially failed because of incorrectly ordered imports. I fixed the imports and reran Ruff successfully.

### What Remains Unclear

1. I understand that CSV values are read as strings, but I still need more practice 
   deciding where and when data should be converted back into Python types in a larger application.

2. I want to understand more deeply how static type checking differs from runtime validation.

### Validation

    ruff check .

Result:

    All checks passed!

### Git

Day 1 changes were committed and pushed to the remote repository.
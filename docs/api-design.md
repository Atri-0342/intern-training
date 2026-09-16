# ScanFlow — API Design

# 1. API Conventions

## Base URL

`/v1`

All ScanFlow API endpoints are versioned under `/v1/`.

## Versioning

ScanFlow uses URL-based versioning with `/v1/`.

**Justification:** This allows future breaking API changes to be introduced under a new version without breaking existing `/v1` clients.

## Authentication

ScanFlow uses JWT-based authentication.

Authenticated requests send the token using:

    Authorization: Bearer <access_token>

## Roles

ScanFlow has three roles:

- `clinician`
- `radiologist`
- `admin`

Authentication confirms who the user is. Authorization determines whether that user's role is allowed to perform the requested operation.

## Common Headers

For JSON requests:

    Content-Type: application/json

For authenticated requests:

    Authorization: Bearer <access_token>

---

# 2. Common Error Response

All API errors use the same error envelope.

    {
      "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable error message",
        "details": {}
      }
    }

## Common Error Status Codes

| Status Code | Meaning |
|---|---|
| `400` | Bad Request — Request is malformed or cannot be processed |
| `401` | Unauthorized — Authentication is missing or invalid |
| `403` | Forbidden — Authenticated user does not have permission |
| `404` | Not Found — Requested resource does not exist |
| `409` | Conflict — Request conflicts with the current resource state |
| `422` | Unprocessable Entity — Request validation failed |
| `500` | Internal Server Error — Unexpected server-side failure |

---

# 3. Pagination

List endpoints use offset-based pagination.

## Query Parameters

- `limit` — Maximum number of records returned.
- `offset` — Number of records skipped before returning results.

## Example

    GET /v1/scans?limit=20&offset=0

## Example Response

    {
      "items": [],
      "limit": 20,
      "offset": 0,
      "total": 125
    }

## Pagination Decision

ScanFlow uses offset pagination because the current API requires straightforward filtering and pagination, and the expected dataset size does not justify the additional complexity of cursor-based pagination.

---

# 4. Authentication Endpoints

# POST /v1/auth/register

Creates a new user account.

## Authentication

None.

## Request

    {
      "email": "clinician@example.com",
      "password": "example-password",
      "role": "clinician"
    }

## Response

    {
      "id": 1,
      "email": "clinician@example.com",
      "role": "clinician"
    }

## Status Codes

- `201 Created` — User created successfully
- `409 Conflict` — User already exists
- `422 Unprocessable Entity` — Request validation failed

---

# POST /v1/auth/login

Authenticates a user and returns a JWT access token.

## Authentication

None.

## Request

    {
      "email": "clinician@example.com",
      "password": "example-password"
    }

## Response

    {
      "access_token": "jwt-token",
      "token_type": "bearer"
    }

## Status Codes

- `200 OK` — Login successful
- `401 Unauthorized` — Invalid credentials
- `422 Unprocessable Entity` — Request validation failed

---

# 5. Patient Endpoints

# GET /v1/patients

Returns a paginated list of patients.

## Authentication

JWT required.

## Query Parameters

- `limit`
- `offset`

## Response

    {
      "items": [
        {
          "id": 1,
          "study_id": "STUDY-0001",
          "date_of_birth": "1990-01-01",
          "sex": "F"
        }
      ],
      "limit": 20,
      "offset": 0,
      "total": 1
    }

## Status Codes

- `200 OK` — Patients returned successfully
- `401 Unauthorized` — Authentication missing or invalid
- `422 Unprocessable Entity` — Invalid pagination parameters

---

# POST /v1/patients

Creates a patient record.

## Authentication

JWT required.

## Request

    {
      "study_id": "STUDY-0001",
      "date_of_birth": "1990-01-01",
      "sex": "F"
    }

## Response

    {
      "id": 1,
      "study_id": "STUDY-0001",
      "date_of_birth": "1990-01-01",
      "sex": "F"
    }

## Status Codes

- `201 Created` — Patient created successfully
- `401 Unauthorized` — Authentication missing or invalid
- `409 Conflict` — Patient/study ID already exists
- `422 Unprocessable Entity` — Request validation failed

---

# GET /v1/patients/{id}

Returns a specific patient.

## Authentication

JWT required.

## Path Parameters

- `id` — Patient ID

## Response

    {
      "id": 1,
      "study_id": "STUDY-0001",
      "date_of_birth": "1990-01-01",
      "sex": "F"
    }

## Status Codes

- `200 OK` — Patient found
- `401 Unauthorized` — Authentication missing or invalid
- `404 Not Found` — Patient does not exist

---

# PUT /v1/patients/{id}

Updates a patient record.

## Authentication

JWT required.

## Path Parameters

- `id` — Patient ID

## Request

    {
      "date_of_birth": "1990-01-01",
      "sex": "F"
    }

## Response

    {
      "id": 1,
      "study_id": "STUDY-0001",
      "date_of_birth": "1990-01-01",
      "sex": "F"
    }

## Status Codes

- `200 OK` — Patient updated successfully
- `401 Unauthorized` — Authentication missing or invalid
- `404 Not Found` — Patient does not exist
- `422 Unprocessable Entity` — Request validation failed

---

# DELETE /v1/patients/{id}

Deletes a patient record.

## Authentication

JWT + Admin required.

## Path Parameters

- `id` — Patient ID

## Response

    {
      "message": "Patient deleted successfully"
    }

## Status Codes

- `200 OK` — Patient deleted successfully
- `401 Unauthorized` — Authentication missing or invalid
- `403 Forbidden` — User is not an admin
- `404 Not Found` — Patient does not exist

---

# 6. Scan Endpoints

# GET /v1/scans

Returns a paginated list of scans.

## Authentication

JWT required.

## Query Parameters

- `limit`
- `offset`
- `patient_id`
- `status`

## Response

    {
      "items": [
        {
          "id": 1,
          "patient_id": 1,
          "file_path": "/scans/study-0001/image.dcm",
          "status": "uploaded"
        }
      ],
      "limit": 20,
      "offset": 0,
      "total": 1
    }

## Status Codes

- `200 OK` — Scans returned successfully
- `401 Unauthorized` — Authentication missing or invalid
- `422 Unprocessable Entity` — Invalid query parameters

---

# POST /v1/scans

Uploads and creates a scan record.

## Authentication

JWT required.

## Request

The request contains scan metadata and the uploaded scan file.

- `patient_id`
- `scan file`

## Response

    {
      "id": 1,
      "patient_id": 1,
      "file_path": "/scans/study-0001/image.dcm",
      "status": "uploaded"
    }

## Status Codes

- `201 Created` — Scan created successfully
- `401 Unauthorized` — Authentication missing or invalid
- `404 Not Found` — Patient does not exist
- `422 Unprocessable Entity` — Invalid request or file data

---

# GET /v1/scans/{id}

Returns a specific scan.

## Authentication

JWT required.

## Path Parameters

- `id` — Scan ID

## Response

    {
      "id": 1,
      "patient_id": 1,
      "file_path": "/scans/study-0001/image.dcm",
      "status": "uploaded"
    }

## Status Codes

- `200 OK` — Scan found
- `401 Unauthorized` — Authentication missing or invalid
- `404 Not Found` — Scan does not exist

---

# PUT /v1/scans/{id}

Updates scan metadata.

## Authentication

JWT required.

## Path Parameters

- `id` — Scan ID

## Request

    {
      "status": "uploaded"
    }

## Response

    {
      "id": 1,
      "patient_id": 1,
      "file_path": "/scans/study-0001/image.dcm",
      "status": "uploaded"
    }

## Status Codes

- `200 OK` — Scan updated successfully
- `401 Unauthorized` — Authentication missing or invalid
- `404 Not Found` — Scan does not exist
- `422 Unprocessable Entity` — Request validation failed

---

# DELETE /v1/scans/{id}

Deletes a scan.

## Authentication

JWT + Admin required.

## Path Parameters

- `id` — Scan ID

## Response

    {
      "message": "Scan deleted successfully"
    }

## Status Codes

- `200 OK` — Scan deleted successfully
- `401 Unauthorized` — Authentication missing or invalid
- `403 Forbidden` — User is not an admin
- `404 Not Found` — Scan does not exist

---

# 7. Analysis Endpoints

# POST /v1/scans/{id}/analyze

Creates an asynchronous analysis job for a scan.

## Authentication

JWT required.

## Path Parameters

- `id` — Scan ID

## Request

No request body is required.

## Response

    {
      "job_id": "job-0001",
      "status": "pending"
    }

## Status Codes

- `202 Accepted` — Analysis job accepted
- `401 Unauthorized` — Authentication missing or invalid
- `404 Not Found` — Scan does not exist
- `409 Conflict` — Scan cannot currently be analyzed

## Asynchronous Processing

The analysis is not performed inside the HTTP request.

The endpoint creates a job and returns a job identifier.

---

# GET /v1/scans/{id}/analysis

Returns the current analysis status or completed analysis result.

## Authentication

JWT required.

## Path Parameters

- `id` — Scan ID

## Response — Pending

    {
      "job_id": "job-0001",
      "status": "pending"
    }

## Response — Running

    {
      "job_id": "job-0001",
      "status": "running"
    }

## Response — Completed

    {
      "job_id": "job-0001",
      "status": "done",
      "result": {
        "finding": "Example finding",
        "confidence": 0.91
      }
    }

## Response — Failed

    {
      "job_id": "job-0001",
      "status": "failed",
      "error": "Analysis failed"
    }

## Status Codes

- `200 OK` — Analysis status/result returned
- `401 Unauthorized` — Authentication missing or invalid
- `404 Not Found` — Scan or analysis job does not exist

---

# 8. Report Endpoints

# POST /v1/reports

Creates a report for a scan.

## Authentication

JWT + Radiologist required.

## Request

    {
      "scan_id": 1,
      "content": "Example radiology report"
    }

## Response

    {
      "id": 1,
      "scan_id": 1,
      "content": "Example radiology report",
      "status": "draft"
    }

## Status Codes

- `201 Created` — Report created successfully
- `401 Unauthorized` — Authentication missing or invalid
- `403 Forbidden` — User is not a radiologist
- `404 Not Found` — Scan does not exist
- `422 Unprocessable Entity` — Request validation failed

---

# GET /v1/reports/{id}

Returns a report.

## Authentication

JWT required.

## Path Parameters

- `id` — Report ID

## Response

    {
      "id": 1,
      "scan_id": 1,
      "content": "Example radiology report",
      "status": "draft"
    }

## Status Codes

- `200 OK` — Report found
- `401 Unauthorized` — Authentication missing or invalid
- `404 Not Found` — Report does not exist

---

# PUT /v1/reports/{id}

Updates a report.

## Authentication

JWT + Radiologist required.

## Path Parameters

- `id` — Report ID

## Request

    {
      "content": "Updated radiology report"
    }

## Response

    {
      "id": 1,
      "scan_id": 1,
      "content": "Updated radiology report",
      "status": "draft"
    }

## Status Codes

- `200 OK` — Report updated successfully
- `401 Unauthorized` — Authentication missing or invalid
- `403 Forbidden` — User is not a radiologist
- `404 Not Found` — Report does not exist
- `422 Unprocessable Entity` — Request validation failed

---

# POST /v1/reports/{id}/finalize

Finalizes a report.

Only a radiologist can move a report from draft to final.

## Authentication

JWT + Radiologist required.

## Path Parameters

- `id` — Report ID

## Request

No request body is required.

## Response

    {
      "id": 1,
      "scan_id": 1,
      "content": "Final radiology report",
      "status": "final"
    }

## Status Codes

- `200 OK` — Report finalized successfully
- `401 Unauthorized` — Authentication missing or invalid
- `403 Forbidden` — User is not a radiologist
- `404 Not Found` — Report does not exist
- `409 Conflict` — Report is already finalized
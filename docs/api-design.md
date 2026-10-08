# ScanFlow — API Design

> **Day 38 API review**
>
> This document preserves the original Day 27 API design as historical context and then records every important divergence introduced during implementation. The old design is not deleted. The current API contract is documented separately and should be treated as the implementation source of truth.

---

# 1. Historical API Design — Day 27

The Day 27 API design established these original conventions:

- `/v1` API versioning.
- JWT authentication.
- Roles: clinician, radiologist, admin.
- Common error envelope.
- Offset pagination.
- Patient CRUD.
- Scan creation/upload.
- Asynchronous analysis.
- Analysis status retrieval through HTTP.
- Report workflow.

The implementation later evolved some endpoint paths, request/response shapes, analysis states, storage behavior, and delivery mechanisms.

---

# 2. Day 27 → Current API Divergences

## 2.1 Scan upload endpoint

### Original design

```http
POST /v1/scans
```

### Current

```http
POST /v1/scans/upload
```

---

## 2.2 Scan upload parameters

### Original design

The original contract was centered around patient identification and a scan file.

### Current

The actual endpoint requires:

```text
patient_id
modality
body_part
acquired_at
file
```

---

## 2.3 Scan storage field

### Original design

The original API described a filesystem-style `file_path`.

### Current

The API returns:

```json
{
  "file_key": "scans/<scan-id>.pdf"
}
```

This intentionally exposes a storage key rather than a server filesystem path.

---

## 2.4 File validation

### Original design

File validation was not specified at the same level of detail.

### Current

Allowed content types:

```text
image/jpeg
image/png
application/pdf
```

Maximum size:

```text
20 MB
```

---

## 2.5 Analysis initial state

### Original design

The API design used:

```text
pending
```

### Current

The job is created with:

```text
uploaded
```

Then:

```text
uploaded → running → done
```

or:

```text
uploaded → running → failed
```

---

## 2.6 Analysis response shape

### Original design

The original design nested result information under a result object.

### Current

The actual `done` response is flat:

```json
{
  "job_id": "job-uuid",
  "scan_id": "scan-uuid",
  "status": "done",
  "confidence": 0.94,
  "findings": "No acute abnormality detected"
}
```

---

## 2.7 WebSocket API

### Original design

The Day 27 API contract primarily described HTTP status retrieval/polling.

### Current

WebSocket status delivery was added:

```http
POST /v1/ws/tickets
```

followed by:

```text
WS /v1/ws/scans/{id}
```

---

## 2.8 WebSocket authentication

The current browser WebSocket flow does not put the normal JWT in the WebSocket URL.

Instead:

```text
JWT-authenticated HTTP request
            ↓
POST /v1/ws/tickets
            ↓
short-lived single-use ticket
            ↓
WS /v1/ws/scans/{id}
```

Ticket properties:

- approximately 30-second lifetime
- single-use
- bound to the authorized user/scan context

---

## 2.9 HTTP polling

Polling was the original status-delivery approach and remains available.

The current frontend polling implementation uses increasing delays:

```text
2s → 4s → 8s → 15s maximum
```

It stops on terminal state, component unmount, or maximum attempts.

The current preferred live mechanism is WebSocket, with polling retained as a fallback.

---

# 3. API Conventions

## Base URL

```text
/v1
```

All versioned endpoints are under `/v1`.

---

## Authentication

Normal HTTP requests use:

```http
Authorization: Bearer <access_token>
```

The WebSocket uses the short-lived ticket mechanism described later.

---

## Roles

```text
clinician
radiologist
admin
```

---

# 4. Common Error Response

The intended common error envelope is:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

Common status codes:

| Status | Meaning |
|---|---|
| `400` | Bad request |
| `401` | Missing/invalid authentication |
| `403` | Authenticated but not authorized |
| `404` | Resource not found |
| `409` | Resource/state conflict |
| `413` | File exceeds 20 MB |
| `422` | Validation error |
| `500` | Unexpected server error |

---

# 5. Pagination

List endpoints use offset pagination.

Example:

```http
GET /v1/patients?limit=20&offset=0
```

Query parameters:

```text
limit
offset
```

Example response:

```json
{
  "items": [],
  "limit": 20,
  "offset": 0,
  "total": 125
}
```

Cursor pagination remains a possible future optimization for the busiest list endpoint.

---

# 6. Authentication Endpoints

## POST /v1/auth/register

Creates a user.

### Request

```json
{
  "email": "clinician@example.com",
  "password": "example-password",
  "role": "clinician"
}
```

### Response

```json
{
  "id": 1,
  "email": "clinician@example.com",
  "role": "clinician"
}
```

### Status

- `201` — created
- `409` — user already exists
- `422` — validation failed

---

## POST /v1/auth/login

Authenticates a user.

### Request

```json
{
  "email": "clinician@example.com",
  "password": "example-password"
}
```

### Response

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

### Status

- `200` — successful
- `401` — invalid credentials
- `422` — validation failed

---

# 7. Patient Endpoints

## GET /v1/patients

Returns patients.

### Authentication

JWT required.

### Query

```text
limit
offset
```

### Status

- `200`
- `401`
- `422`

---

## POST /v1/patients

Creates a patient.

### Authentication

JWT required.

### Status

- `201`
- `401`
- `409`
- `422`

---

## GET /v1/patients/{id}

Returns a patient.

### Authentication

JWT required.

### Status

- `200`
- `401`
- `404`

---

## PUT /v1/patients/{id}

Updates a patient.

### Authentication

JWT required.

### Status

- `200`
- `401`
- `404`
- `422`

---

## DELETE /v1/patients/{id}

Deletes a patient.

### Authentication

Admin required.

### Status

- `200`
- `401`
- `403`
- `404`

---

# 8. Scan Endpoints

## GET /v1/scans

Returns a paginated list of scans.

### Authentication

JWT required.

### Query parameters

```text
limit
offset
patient_id
status
```

### Example

```json
{
  "items": [
    {
      "id": "scan-uuid",
      "patient_id": "patient-uuid",
      "modality": "CT",
      "body_part": "chest",
      "acquired_at": "2026-10-01T10:00:00Z",
      "uploaded_at": "2026-10-01T10:01:00Z",
      "status": "uploaded",
      "file_key": "scans/scan-uuid.pdf"
    }
  ],
  "limit": 20,
  "offset": 0,
  "total": 1
}
```

---

## POST /v1/scans/upload

Uploads a scan.

### Authentication

Clinician role required.

### Content type

```http
multipart/form-data
```

### Required parameters

```text
patient_id
modality
body_part
acquired_at
file
```

### Accepted content types

```text
image/jpeg
image/png
application/pdf
```

### Maximum size

```text
20 MB
```

### Current storage

```text
uploads/scans/<scan-id>.<extension>
```

Database reference:

```text
scans/<scan-id>.<extension>
```

### Example response

```json
{
  "id": "scan-uuid",
  "patient_id": "patient-uuid",
  "modality": "CT",
  "body_part": "chest",
  "acquired_at": "2026-10-01T10:00:00Z",
  "uploaded_at": "2026-10-01T10:01:00Z",
  "status": "uploaded",
  "file_key": "scans/scan-uuid.pdf"
}
```

### Status

- `201` — created
- `400` — unsupported content type
- `401` — authentication missing/invalid
- `404` — patient not found
- `413` — file too large
- `422` — validation failed

---

## GET /v1/scans/{id}

Returns a scan.

### Authentication

JWT required.

### Status

- `200`
- `401`
- `404`

---

## PUT /v1/scans/{id}

Updates supported scan metadata.

### Authentication

JWT required.

### Status

- `200`
- `401`
- `404`
- `422`

---

## DELETE /v1/scans/{id}

Deletes a scan.

### Authentication

Admin required.

### Status

- `200`
- `401`
- `403`
- `404`

---

# 9. Analysis Endpoints

## POST /v1/scans/{id}/analyze

Creates an asynchronous analysis job.

### Authentication

JWT required.

### Request

No request body is required.

### Current response

```json
{
  "job_id": "job-uuid",
  "scan_id": "scan-uuid",
  "status": "uploaded"
}
```

### Status

```text
202 Accepted
```

The HTTP request does not perform the analysis itself.

---

## GET /v1/scans/{id}/analysis

Returns the latest analysis job/result.

### Authentication

JWT required.

---

### Uploaded

```json
{
  "job_id": "job-uuid",
  "scan_id": "scan-uuid",
  "status": "uploaded"
}
```

---

### Running

```json
{
  "job_id": "job-uuid",
  "scan_id": "scan-uuid",
  "status": "running"
}
```

---

### Done

```json
{
  "job_id": "job-uuid",
  "scan_id": "scan-uuid",
  "status": "done",
  "confidence": 0.94,
  "findings": "No acute abnormality detected"
}
```

---

### Failed

```json
{
  "job_id": "job-uuid",
  "scan_id": "scan-uuid",
  "status": "failed"
}
```

### Status

- `200` — state/result returned
- `401` — authentication missing/invalid
- `404` — scan/analysis job not found

---

# 10. WebSocket Endpoints

## POST /v1/ws/tickets

Creates a short-lived WebSocket authentication ticket.

### Authentication

JWT required.

### Purpose

The browser obtains a ticket using its normal authenticated HTTP request before opening the WebSocket.

### Flow

```text
JWT
 │
 ▼
POST /v1/ws/tickets
 │
 ▼
short-lived ticket
 │
 ▼
WS /v1/ws/scans/{id}
```

---

## WS /v1/ws/scans/{id}

Streams analysis status changes.

### Authentication

A valid single-use WebSocket ticket is required.

### Running event

```json
{
  "job_id": "job-uuid",
  "scan_id": "scan-uuid",
  "status": "running"
}
```

### Done event

```json
{
  "job_id": "job-uuid",
  "scan_id": "scan-uuid",
  "status": "done",
  "confidence": 0.94,
  "findings": "No acute abnormality detected"
}
```

### Failure event

```json
{
  "job_id": "job-uuid",
  "scan_id": "scan-uuid",
  "status": "failed"
}
```

### Client behavior

The frontend:

- reconnects after unexpected closure;
- uses exponential backoff;
- stops reconnecting after terminal state;
- handles offline → online transitions;
- handles background → foreground transitions;
- cleans up the WebSocket when the component unmounts.

---

# 11. Current Analysis Delivery Strategy

The actual system supports both approaches.

## Preferred live path

```text
POST analyze
      ↓
worker
      ↓
WebSocket
      ↓
browser
```

## Fallback

```text
GET /v1/scans/{id}/analysis
      ↓
wait
      ↓
GET again
      ↓
done/failed
```

WebSocket is useful because the server can push status transitions instead of requiring repeated requests.

Polling remains important because long-lived WebSocket connections can be affected by network conditions, proxies, firewalls, or browser lifecycle behavior.

---

# 12. Report Endpoints

Report functionality remains part of the intended clinical workflow.

Where report endpoints are implemented, their exact runtime behavior should be treated as the source of truth.

## POST /v1/reports

Creates a report.

### Intended role

Radiologist.

---

## GET /v1/reports/{id}

Returns a report.

### Authentication

JWT required.

---

## PUT /v1/reports/{id}

Updates a report.

### Intended role

Radiologist.

---

## POST /v1/reports/{id}/finalize

Finalizes a report.

### Intended role

Radiologist.

---

# 13. Current Upload Storage Contract

The current API deliberately separates metadata from binary storage.

```text
HTTP multipart upload
        │
        ▼
FastAPI
        │
        ├──────────────→ PostgreSQL
        │                 metadata
        │
        └──────────────→ uploads/scans/
                          binary file
```

PostgreSQL contains:

```text
file_key
```

not:

```text
file_path
```

and not the file binary.

---

# 14. Future S3 API Migration

The current API can retain the same logical storage contract while changing the implementation.

### Current

```text
FastAPI
   ↓
local mounted storage
```

### Future

```text
FastAPI
   ↓
boto3
   ↓
S3-compatible storage
```

Development/test:

```text
boto3
   ↓
moto
```

No AWS account is required for the local migration exercise.

Production:

```text
FastAPI
   ↓
IAM role
   ↓
S3
```

A later presigned-URL design can allow browsers to upload directly to S3.

---

# 15. API Design Decisions That Remain From Day 27

The following original decisions remain valid:

1. `/v1` URL versioning.
2. JWT authentication.
3. Role-based authorization.
4. Common error handling.
5. Offset pagination.
6. PostgreSQL for structured data.
7. Scan binaries outside PostgreSQL.
8. Asynchronous analysis.
9. Separate analysis status from scan metadata.
10. Report workflow.

The implementation changed some concrete endpoint names, state names, response shapes, and delivery mechanisms, but these higher-level design decisions remain.

---

# 16. Day 38 API Review Conclusion

The most important API changes from the Day 27 design are:

1. `POST /v1/scans` became `POST /v1/scans/upload`.
2. Upload now explicitly requires `patient_id`, `modality`, `body_part`, `acquired_at`, and `file`.
3. Upload accepts JPEG, PNG, and PDF.
4. Upload is limited to 20 MB.
5. The response uses `file_key`.
6. The analysis initial state is `uploaded`, not `pending`.
7. Analysis results are returned as a flat response.
8. `scan_id` is included in analysis responses.
9. WebSocket ticket authentication was added.
10. `WS /v1/ws/scans/{id}` was added.
11. WebSocket status events were added.
12. WebSocket reconnect/resilience was added on the frontend.
13. HTTP polling remains as a fallback.
14. The current storage is a mounted local volume.
15. S3 is the next storage migration, not the current implementation.

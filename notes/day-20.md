# Day 20 — Authentication, JWT & Role-Based Authorization

# 1. Authentication

Implemented:

- `POST /v1/auth/register`
- `POST /v1/auth/token`

Passwords are never stored in plaintext. They are hashed using:

- `pwdlib`
- Argon2

The database stores only the Argon2 password hash. Login verifies the supplied password against the stored hash before issuing a JWT.

# 2. JWT Authentication

Implemented JWT-based authentication using:

- PyJWT
- HS256
- Configurable expiration time
- Secret stored in `.env`

JWT payload contains:

- `sub` — authenticated user ID
- `role` — user's role
- `exp` — expiration timestamp

The JWT does not contain passwords or other secrets. Protected endpoints use the reusable `get_current_user()` dependency.

# Authentication Flow

Client -> POST /v1/auth/token -> Verify email + password -> Generate JWT -> Client sends: Authorization: Bearer <token> -> get_current_user() -> Decode + validate JWT -> Request continues

# 3. Authentication vs Authorization

Implemented two reusable dependencies.

get_current_user()

Responsible for authentication.

Answers:

Who is making this request?

Returns:

{
    "user_id": "...",
    "role": "..."
}

Invalid or expired JWTs return:

401 Unauthorized
require_role(...)

Responsible for authorization.

Authenticated users with insufficient permissions receive:

403 Forbidden
4. Role-Based Access Control

Endpoint permissions were applied per operation.

Patients
Create → clinician
Read → clinician, radiologist
Update → clinician
Delete → admin

Scans
Create/upload → clinician
Read → clinician, radiologist
Update → clinician
Delete → admin

Reports
Create → clinician
Read → clinician, radiologist
Update/finalize → radiologist
Delete → admin

Authorization is attached to the specific operation rather than applying one global role to an entire router.

# 4. Audit Logging

Endpoints record the authenticated actor.

Audit entries include:

action
entity
entity ID
actor ID

Example:

write_audit_log(
    db=db,
    action="CREATE",
    entity="scan",
    entity_id=str(table.id),
    actor_id=current_user["user_id"],
)

This connects each to the authenticated user who performed the operation. Audit logging remains part of the same database transaction as the mutation.

# 5. Security Verification

Manually verified the required security cases.

## Wrong Role

An admin attempted to access an endpoint restricted to clinician/radiologist.

Result:

403 Forbidden

Confirmed role-based authorization works.

## Expired Token

Generated a JWT with a short expiration, waited for expiration, and called a protected endpoint.

Result:

401 Unauthorized

Confirmed JWT expiration is enforced.

## Tampered Signature

Modified one character of a valid JWT signature and sent it to a protected endpoint.

Result:

401 Unauthorized

Confirmed JWT signature verification works.

# 6. Test Users

Created test users for all three supported roles:

clinician
radiologist
admin

Each user has an Argon2 password hash stored in PostgreSQL.

JWTs are generated during login and are not stored in the users table
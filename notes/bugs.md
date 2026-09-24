# Bugs covered by regression tests

## Missing bearer credentials returned the wrong status

Protected endpoints used FastAPI's default `HTTPBearer` error handling, so a
request without an `Authorization` header returned `403 Forbidden`. The API
contract requires unauthenticated requests to return `401 Unauthorized`.

The regression test is `test_authentication_and_authorization` in
`ScanFlow/tests/test_api.py`.

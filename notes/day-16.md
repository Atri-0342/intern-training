# Day 16 — HTTP and API Design

## 1. HTTP Overview

HTTP (HyperText Transfer Protocol) is a protocol used for communication between clients and servers.

A client can be:
- Browser
- Frontend application
- Mobile application
- Another backend service

A server receives the request, processes it, and sends an HTTP response.

### HTTP Request

An HTTP request commonly contains:
- Method
- URL/path
- Headers
- Body

Example:

GET /users/123 HTTP/1.1
Host: example.com
Accept: application/json

Here:
- `GET` → HTTP method
- `/users/123` → resource path
- `Host` and `Accept` → headers
- No request body is present

### HTTP Response

An HTTP response commonly contains:
- Status code
- Headers
- Body

Example:

HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": 123,
  "name": "John"
}

Here:
- `200 OK` → status code
- `Content-Type` → response header
- JSON data → response body

### Basic HTTP Communication

The client sends a request to a server.

The server examines the request and determines what operation is being requested.

The server performs the required operation and returns a response.

The response tells the client whether the operation succeeded, failed, or requires another action.

HTTP is stateless. Each request is generally independent of previous requests. Applications can maintain state separately using mechanisms such as cookies, tokens, sessions, or databases.


# 2. HTTP Request Methods

HTTP methods describe the intended operation on a resource.

## GET

GET retrieves a resource.

Example:

GET /users/123

GET should not intentionally modify server state.

GET is:
- Safe
- Idempotent
- Generally cacheable


## POST

POST submits data to a resource.

It is commonly used to create a new resource.

Example:

POST /users

Request body:

{
  "name": "John",
  "email": "john@example.com"
}

POST is not idempotent by default.

Sending the same POST multiple times can create multiple resources.


## PUT

PUT is generally used to completely replace a resource.

Example:

PUT /users/123

Request body:

{
  "name": "John",
  "email": "john@example.com"
}

PUT is idempotent.

Repeating the same PUT should result in the same intended final state.


## PATCH

PATCH partially modifies a resource.

Example:

PATCH /users/123

Request body:

{
  "name": "John Smith"
}

Only the specified part of the resource is changed.

PATCH is not inherently idempotent. Its idempotency depends on how the operation is implemented.


## DELETE

DELETE removes a resource.

Example:

DELETE /users/123

DELETE is idempotent.

If the resource has already been deleted, repeating the operation does not cause another deletion of that resource.

The response can still be different between requests.

For example, the first request could return `204`, while a later request could return `404`.


## HEAD

HEAD is similar to GET but does not return the response body.

It can be used when the client only needs response metadata such as headers.

HEAD is:
- Safe
- Idempotent
- Cacheable


## OPTIONS

OPTIONS allows a client to discover supported operations or communication options for a resource.

It is:
- Safe
- Idempotent

OPTIONS is also commonly involved in browser CORS behavior.


# 3. Safe HTTP Methods

A safe method is intended to be read-only with respect to the requested resource.

Safe methods include:
- GET
- HEAD
- OPTIONS

Safe does not mean that absolutely nothing happens on the server.

For example, a server can create logs when processing a GET request.

The important point is that the method is not intended to modify the requested resource.


# 4. Idempotent HTTP Methods

An HTTP method is idempotent when making the same request multiple times has the same intended effect on server state as making it once.

Common idempotent methods:
- GET
- PUT
- DELETE
- HEAD
- OPTIONS

Example:

PUT /users/123

{
  "name": "John"
}

Repeating the same request should leave the user in the same intended state.

Idempotent does not mean that every response must be identical.

For example:

DELETE /users/123

The first request might return:

204 No Content

A later request might return:

404 Not Found

The responses are different, but the intended resource state remains deleted.


# 5. Cacheable HTTP Methods

Caching means storing a response so that it can potentially be reused instead of generating the response again.

Caching can:
- Reduce network traffic
- Reduce server workload
- Improve response speed

GET responses are commonly cacheable.

HEAD responses are also cacheable.

POST and PATCH can be cacheable under specific HTTP caching rules, but they are not normally treated like ordinary cacheable GET requests.

Whether a response is actually cached depends on HTTP caching rules and request/response headers.


# 6. HTTP Response Status Codes

HTTP status codes communicate the result or state of a request.

## 1xx — Informational

These indicate that the request has been received and the communication is continuing.

They are mainly used for protocol-level communication.


## 2xx — Success

### 200 OK

The request succeeded.

Commonly used for successful GET requests.

### 201 Created

The request successfully created a new resource.

Commonly used after POST.

### 202 Accepted

The request has been accepted for processing, but processing may not be complete yet.

Useful when work is asynchronous or takes significant time.

### 204 No Content

The request succeeded, but there is no response body.

Commonly used for successful DELETE operations or updates where no response body is needed.


## 3xx — Redirection

These indicate that the client may need to take another action to complete the request.

### 301 Moved Permanently

The requested resource has permanently moved to another URI.

### 302 Found

The resource is temporarily available at another URI.

### 304 Not Modified

The cached version of the resource can still be used because the resource has not changed.


## 4xx — Client Errors

These indicate that the request could not be successfully processed because of something related to the client request.


### 400 Bad Request

The server cannot process the request because the request is invalid or malformed.

Examples:
- Invalid request structure
- Invalid syntax
- Missing required information


### 401 Unauthorized

The request requires authentication or the provided authentication is invalid.

A useful interpretation is:

`401` → the client has not successfully authenticated.


### 403 Forbidden

The server understood the request, but the client is not allowed to perform the operation.

A useful distinction:

`401` → authentication is missing or invalid

`403` → authentication may exist, but access is not permitted


### 404 Not Found

The requested resource could not be found.

Example:

GET /users/999999

when that user does not exist.


### 409 Conflict

The request conflicts with the current state of the resource.

Common examples:
- Duplicate resource creation
- Concurrent modification
- Resource state conflict


### 422 Unprocessable Content

The request has a valid structure, but the submitted data cannot be processed because it fails application-level validation or semantic rules.

For example, the JSON can be valid but contain an invalid email or invalid field value.


### 429 Too Many Requests

The client has sent too many requests in a given period.

This is commonly used for rate limiting.


## 5xx — Server Errors

These indicate that the server encountered a problem while processing a request.


### 500 Internal Server Error

A general unexpected server-side error.

It usually means something went wrong inside the server.


### 502 Bad Gateway

A server acting as a gateway or proxy received an invalid response from an upstream server.


### 503 Service Unavailable

The server is temporarily unable to handle the request.

Possible reasons:
- Server overload
- Maintenance
- Temporary service unavailability


# 7. HTTP Status Codes in API Design

Status codes should communicate meaningful outcomes consistently.

Example:

GET /users/123

If the user exists:

200 OK

If the user does not exist:

404 Not Found

For creating a user:

POST /users

A successful creation commonly returns:

201 Created

Using appropriate status codes makes an API easier for clients to understand and use correctly.


# 8. API Resource URIs

A URI identifies a resource in an API.

Good API design generally uses resource-oriented URIs.

Examples:

/users
/users/123
/users/123/orders

These represent:
- A collection of users
- One specific user
- Orders belonging to a specific user

The URI should generally describe the resource rather than the action being performed.

Prefer:

GET /users

instead of:

GET /getUsers

Prefer:

POST /users

instead of:

POST /createUser

The HTTP method communicates the operation, while the URI identifies the resource.


# 9. HTTP Verbs and Resource Design

The same resource URI can support different operations through different HTTP methods.

For example:

/users/123

can represent one user.

Retrieve it:

GET /users/123

Completely replace it:

PUT /users/123

Partially modify it:

PATCH /users/123

Delete it:

DELETE /users/123

This keeps the URI focused on the resource while the HTTP method describes the operation.


# 10. Collections and Individual Resources

A collection represents multiple resources.

Example:

/users

A specific resource can be identified by an ID.

Example:

/users/123

Nested resources can represent relationships.

Example:

/users/123/orders

This can represent the orders belonging to user `123`.


# 11. API Naming

Use clear, predictable, and consistent naming.

Prefer nouns:

/users
/orders
/products

Avoid action-oriented paths such as:

/getUsers
/createUser
/deleteUser

The HTTP method already describes the operation.

Use consistent naming conventions throughout the API.

For example, if the API uses plural resource names:

/users
/orders
/products

then it should generally continue using the same style.


# 12. Pagination

Pagination is used when an API returns a large collection of resources.

Instead of returning thousands of records at once, the API returns a limited number of records per request.

Pagination helps:

- Reduce response size
- Reduce memory usage
- Improve response time
- Reduce database workload
- Make large collections easier to consume


## Offset Pagination

Offset pagination uses a limit and an offset.

Example:

GET /users?limit=20&offset=40

Meaning:

- `limit=20` → return up to 20 records
- `offset=40` → skip the first 40 records

Advantages:
- Simple to understand
- Easy to implement
- Easy to jump to a particular offset

Disadvantages:
- Large offsets can become expensive for databases
- Results can shift when records are inserted or deleted
- Deep pagination can become inefficient


## Cursor Pagination

Cursor pagination uses a cursor representing a position in the dataset.

Example:

GET /users?limit=20&cursor=abc123

The server uses the cursor to determine where the next set of records should start.

Advantages:
- Better for large datasets
- Efficient for deep pagination
- More stable when data changes frequently

Disadvantages:
- More complex to implement
- Clients cannot easily jump directly to an arbitrary page
- Cursor generation and validation require additional design

# 13. API Versioning

API versioning allows an API to evolve without immediately breaking existing clients.

A common approach is putting the version in the URI.

Example:

/v1/users

A future breaking version could use:

/v2/users

The existing `/v1` clients can continue using the old contract while new clients can use `/v2`.

Versioning is especially useful when making breaking changes such as:
- Removing fields
- Changing response structures
- Changing endpoint behavior
- Changing required request fields

A simple versioning strategy is:

/v1/...

This makes the API version visible and easy for clients to understand.

# 14. Idempotency

Idempotency is particularly important when an operation can be retried.

For example, imagine a payment request is sent to a server, but the client does not receive the response because of a network problem.

The client may retry the request.

Without protection, the server could process the payment twice.

An idempotency key can be used to prevent this.

Example:

POST /payments

Idempotency-Key: unique-request-123

The server associates the key with the operation and its result.

If the client retries the same operation using the same idempotency key, the server can recognize that the operation was already processed instead of creating another side effect.

Idempotency is especially useful for operations such as:
- Payments
- Orders
- Resource creation
- Other operations where duplicate execution is dangerous
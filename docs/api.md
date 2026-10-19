# API Reference

## Overview

- Base URL: `http://localhost:5000`
- All request bodies are JSON; all responses are JSON with an HTTP status code.
- Every response body carries a numeric `status` field mirroring the HTTP status.
- Protected endpoints require an `Authorization: Bearer <token>` header.

## Error envelope

Errors share one shape:

```json
{"status": 400, "msg": "username exceeds maximum length of 64"}
```

Registered status codes:

| Code | Meaning | Source |
|------|---------|--------|
| 200  | Success | Handlers return `{"status": 200, ...}` |
| 400  | Validation failure (body, field length/type, duplicate user) | Resource handlers |
| 401  | Missing, expired, or tampered token; invalid credentials | `@requires_auth`, `/login` |
| 404  | No matching route | `web/error_handlers.py` |
| 405  | Route exists, method not allowed | `web/error_handlers.py` |
| 413  | Request body exceeds the 1 MB limit | `MAX_CONTENT_LENGTH` |
| 429  | Rate limit exceeded | Flask-Limiter |
| 500  | Unhandled server error | `web/error_handlers.py` |

flask-restful builds its own responses for HTTP exceptions and never consults
Flask's `@app.errorhandler` chain, so `web/error_handlers.py` patches
`Api.handle_error` to route HTTP exceptions back through Flask's dispatcher.
That is what makes the 404/405/413/500 envelope consistent.

## Endpoints

### `GET /hello`

Health check. No body, no auth.

```shell
curl http://localhost:5000/hello
```

Returns the plain string `Hello World!`.

### `POST /register`

Create a user. Rate limited to **5 per hour** per client IP.

Request:

```json
{"username": "alice", "password": "yourpassword"}
```

Success — `200`:

```json
{"status": 200, "msg": "Registration successful"}
```

Failure modes:

- `400` — body is not valid JSON, a field is missing/not a string, the password
  is too weak, or the username already exists.
- `429` — rate limit exceeded.

Passwords are stored bcrypt-hashed. A username that already exists returns
`400 {"msg": "User already exists"}` — the same status as a validation error, so
the endpoint does not disclose which usernames are registered.

### `POST /login`

Exchange credentials for a JWT. Rate limited to **10 per minute** per client IP.

Request:

```json
{"username": "alice", "password": "yourpassword"}
```

Success — `200`:

```json
{"status": 200, "token": "<signed-jwt>"}
```

Failure modes:

- `400` — body is not valid JSON or a field is missing/invalid.
- `401` — credentials do not match. `{"status": 401, "msg": "Invalid credentials"}`.
- `429` — rate limit exceeded.

The token is signed with HS256 and carries a `sub` claim (the username) and an
`exp` claim **1 hour** after issue. Decoding requires the same `JWT_SECRET`.

### `POST /retrieve`

Return the authenticated user's messages, paginated. Requires a bearer token.

```shell
curl -X POST http://localhost:5000/retrieve \
  -H "Authorization: Bearer <token>"
```

Query parameters (both optional):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `offset`  | `0`     | Zero-based index of the first message to return. |
| `limit`   | `20`    | Maximum messages to return. Capped at **100** server-side. |

Response:

```json
{"status": 200, "obj": ["msg-0", "msg-1"], "total": 50}
```

`total` is the full message count for the user, so a client can paginate the
whole collection. `obj` is the requested slice; slicing past the end yields a
short or empty array rather than an error.

Failure: `401` if the token is missing, expired, or tampered.

### `POST /save`

Append a message to the authenticated user's collection. Requires a bearer token.

Request:

```json
{"message": "Hello!"}
```

Success — `200`:

```json
{"status": 200, "msg": "Message has been saved successfully"}
```

Failure modes:

- `400` — body is not valid JSON, `message` is missing/not a string, or it
  exceeds the length limit.
- `401` — missing, expired, or tampered token.

The username is sourced **only** from the authenticated token (`request.username`
set by `@requires_auth`), never from the request body.

## Rate limiting

`/login` and `/register` are throttled per client IP via
[Flask-Limiter](https://flask-limiter.readthedocs.io/) to mitigate brute-force
credential guessing and account-creation abuse (OWASP API4:2023 — Unrestricted
Resource Consumption). `/hello`, `/retrieve`, and `/save` are unaffected; there is
no global default limit.

| Endpoint    | Limit          |
|-------------|----------------|
| `/login`    | 10 per minute  |
| `/register` | 5 per hour     |

Exceeding a limit returns HTTP `429 Too Many Requests`.

Counters are backed by `RATELIMIT_STORAGE_URL`, which defaults to `memory://` for
local single-process use. For production or multi-worker deployments, point it at
a shared store, e.g. `RATELIMIT_STORAGE_URL=redis://redis:6379`.

## Input validation

Per-field limits, enforced before any hashing or database work. Violations return
HTTP `400` with a descriptive message.

| Field      | Endpoint(s)       | Max length | Type   |
|------------|-------------------|------------|--------|
| username   | `/register`, `/login` | 64 chars | string |
| password   | `/register`, `/login` | 128 chars | string |
| message    | `/save`           | 1024 chars | string |

A non-string value (JSON number, array, etc.) for any of these fields also
returns `400`. An empty string is rejected as a missing value.

Passwords carry an additional strength requirement on `/register`: at least 8
characters and at least one uppercase letter, one lowercase letter, and one
digit.

Beyond per-field limits, the application enforces a maximum total request body
size of **1 MB** (`MAX_CONTENT_LENGTH = 1_048_576` bytes). The limit is checked
before the body is parsed, so oversized payloads are rejected with HTTP `413`
before memory is consumed.

## Authentication flow

```
POST /register ──► POST /login ──► POST /retrieve | POST /save
   (create user)   (get JWT)      (Bearer <token>)
```

1. Register a user — `POST /register` with `username` and `password`.
2. Obtain a token — `POST /login` with the same credentials; response contains `token`.
3. Call a protected endpoint — send `Authorization: Bearer <token>` on every request.

Missing, expired, or tampered tokens return `401 Unauthorized`.

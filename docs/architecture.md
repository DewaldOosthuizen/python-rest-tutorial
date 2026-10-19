# Architecture

## Overview

An educational REST API: Flask application served by a Docker container, backed
by MongoDB, with JWT bearer authentication and bcrypt password hashing.

The codebase is deliberately small so each concern stays readable:

```
web/app.py               Application: resources, auth, validation, data access
web/error_handlers.py    Error envelope + flask-restful handle_error patch
web/Dockerfile           Container build (python:3.11-slim)
```

## Layering

| Layer | Location | Responsibility |
|-------|----------|----------------|
| HTTP resources | `web/app.py` (`Hello`, `Register`, `Login`, `Retrieve`, `Save`) | Parse requests, return JSON + status |
| Cross-cutting auth | `web/app.py` (`requires_auth`, `_require_env`) | JWT verification, fail-fast config |
| Validation | `web/app.py` (`_validate_*_body`, `_require_string`, `_validate_password_strength`) | Field type/length checks before any I/O |
| Data access | `web/app.py` (`user_exist`, `verify_user`, `get_user_messages`) | MongoDB queries only |
| Error handling | `web/error_handlers.py` | Consistent error envelope |

`web/error_handlers.py` exists so that adding structured logging, metrics, or a
custom error envelope later does not require touching resource code.

## Request lifecycle

1. Flask dispatches to the matching `Resource`.
2. `@requires_auth` (where present) reads the `Authorization` header, decodes the
   JWT with `JWT_SECRET`, and sets `request.username` from the `sub` claim.
3. The handler validates the body, then performs its MongoDB operation.
4. The handler returns a `({"status": <code>, ...}, <code>)` tuple.
5. If an HTTP exception is raised, `Api.handle_error` (patched in
   `web/error_handlers.py`) routes it through Flask's error handler chain so the
   envelope stays consistent.

## Security model

- **Passwords** — bcrypt-hashed on registration, never stored in plaintext.
- **Tokens** — HS256-signed JWTs with a 1-hour expiry; `sub` carries the username.
- **Identity binding** — the authenticated username comes only from the decoded
  token. `get_user_messages` and `Save` document this precondition explicitly and
  never read the username from the request body.
- **Rate limiting** — `/login` and `/register` throttled per client IP.
- **Fail-fast config** — `JWT_SECRET` must be set or the app will not start.

## Design decisions

- **`count_documents` over `cursor.count()`** — `Cursor.count()` was removed in
  PyMongo 4.x; existence checks use `Collection.count_documents`.
- **`find_one` over `find()[0]`** — `find()[0]` fails on an empty cursor; `find_one`
  returns `None` and is the supported PyMongo 4.x pattern.
- **Single error module** — keeps the flask-restful patch and the `@app.errorhandler`
  set in one place rather than scattered across resources.
- **Validation before I/O** — field checks run before bcrypt or database calls so
  oversized input is rejected cheaply.

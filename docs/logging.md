# Logging

## Approach

The application uses module-level loggers in the standard form:

```python
logger = logging.getLogger(__name__)
```

Each module under `web/` owns a logger named after itself, so log lines identify
their source module without any extra plumbing.

## Configuration ownership

Library code under `web/` never calls `logging.basicConfig`. Handler and level
configuration is the responsibility of the deployment environment (Docker,
systemd, etc.). Logs are emitted to stdout/stderr and captured by whatever log
collection the deployment provides.

This keeps the application agnostic of its runtime environment: the same module
runs identically under `python app.py`, in a Docker container, or behind a
process supervisor.

## What is logged

Structured, human-readable messages with interpolated values rather than f-string
concatenation:

```python
logger.info("User registered successfully: %s", username)
logger.warning("login failed: invalid credentials for username %s", username)
logger.warning("Authentication failed: JWT decode error")
```

Log points cover:

- Successful registration and login.
- Failed login and failed JWT decode (auth failures).
- Duplicate-username registration attempts.
- Unhandled exceptions (`web/error_handlers.py`, with `exc_info`).

## What is never logged

No passwords, tokens, hashes, or connection strings appear in log output. Log
messages reference the username and the failure reason only — never the credential
that was supplied.

This is a hard rule: if a change adds a log line that could carry a secret, the
change is wrong. Prefer presence or outcome indicators (`authentication failed`)
over payload contents.

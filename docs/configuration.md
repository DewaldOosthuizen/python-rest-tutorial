# Configuration & Environment Variables

## Required variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | *(none)* | Secret key for signing and verifying JWT tokens. Required — the app refuses to start without it. Never commit it. |

The application calls `_require_env("JWT_SECRET")` at import time and raises
`RuntimeError` if the variable is missing or empty. This is a fail-fast check: a
missing secret must stop startup, not surface as a confusing 500 on the first
request.

## MongoDB credentials

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_USER` | `admin` | MongoDB root username. Used by docker-compose to create the authenticated `my_db` service and to build `MONGO_URI`. Set to a strong value for production. |
| `MONGO_PASSWORD` | `changeme` | MongoDB root password. Same role as `MONGO_USER`. The `changeme` default is **not** suitable for production. |
| `MONGO_URI` | `mongodb://my_db:27017/` | MongoDB connection string. docker-compose assembles this from `MONGO_USER` and `MONGO_PASSWORD` at container startup. Override directly for remote or externally-managed MongoDB. |

`MONGO_USER` and `MONGO_PASSWORD` exist so docker-compose can authenticate the
database container **and** build a credentialed `MONGO_URI` in one place. They
have no effect when `MONGO_URI` is supplied directly.

## Rate limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATELIMIT_STORAGE_URL` | `memory://` | Backing store for Flask-Limiter's per-IP counters. Fine for single-process local/dev, but does **not** share state across workers. Use a shared store (e.g. `redis://redis:6379`) in production or multi-worker deployments. |

See [API Reference](api.md#rate-limiting) for the limits this store backs.

## Local setup

```shell
cp .env.example .env
```

`.env.example` defines `MONGO_USER`, `MONGO_PASSWORD`, `MONGO_URI`, and
`RATELIMIT_STORAGE_URL`. It does **not** define `JWT_SECRET` — add a long random
string to `.env` by hand. The file is git-ignored (`.env`, `.env.local`, and
`.env.*.local` patterns) and must never be committed.

## Container configuration

`docker-compose.yml` injects the environment into the `web` service:

```yaml
environment:
  - MONGO_URI=mongodb://${MONGO_USER}:***@my_db:27017/
  - JWT_SECRET=${JWT_SECRET}
```

`MONGO_USER` and `MONGO_PASSWORD` are interpolated by docker-compose from `.env`.
`JWT_SECRET` is passed straight through, so it must be present in the environment
or `.env` at `docker-compose up` time.

The `my_db` service uses the same credentials to create the root user:

```yaml
environment:
  - MONGO_INITDB_ROOT_USERNAME=${MONGO_USER}
  - MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD}
```

## Production checklist

1. Generate a long random `JWT_SECRET` and keep it out of version control.
2. Replace the `admin` / `changeme` MongoDB defaults with strong values.
3. Point `RATELIMIT_STORAGE_URL` at a shared store if more than one app worker runs.
4. Confirm `MONGO_URI` targets the intended (remote or managed) MongoDB instance.

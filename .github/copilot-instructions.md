# python_rest_tutorial — Copilot Instructions

This file instructs AI coding agents (GitHub Copilot, and others) on how to
orient themselves in this repository efficiently.

## Project Overview

An educational repository demonstrating how to build RESTful APIs using Python,
Flask, Docker, and MongoDB. Covers best practices for scalable API design,
containerisation, JWT authentication, password hashing, and testing.

Reference article:
<https://www.dvt.co.za/news-insights/insights/item/355-restful-web-services-using-python-flask-docker-and-mongodb>

## Documentation

All project documentation lives under [`docs/`](../docs/index.md) — architecture, API
reference, configuration, testing, linting, logging, CI/CD, dependencies, and
contributing. This file summarises and links; it does not duplicate.

## Code Exploration

### codegraph

`.codegraph/` is present. Use it FIRST for symbol lookup, call tracing, or
targeted context gathering before opening source files.

```
codegraph context "<task description>" -p .   # focused file+symbol context
codegraph query "<ClassName or function>" -p . # where is X defined / used
codegraph affected <changed-files> -p .        # which tests are affected
codegraph sync .                               # after any code change
```

### understand-anything

`.understand-anything/knowledge-graph.json` is present. Use it for layered
architecture questions (layers, communities, entry points).

```
# Launch the interactive dashboard
cd ~/.understand-anything-plugin/packages/dashboard
GRAPH_DIR=$(pwd) npx vite --host 127.0.0.1

# For prose questions, load the skill:
skill: understand-chat
```

### graphify

`graphify-out/` not yet generated for this repo.

### Decision order for code tasks

1. `codegraph context` — which symbols matter?
2. `understand-anything` — where in the architecture does this live?
3. Read raw source — only the 1-2 files that actually matter.

## Repository Structure

```
web/                     Flask application source (app.py, error_handlers.py) + Dockerfile
web/requirements.txt     Pinned runtime dependencies
web/requirements-dev.txt Pinned test/lint dependencies (pulls in requirements.txt)
web/tests/               Unit tests for the Flask application
tests/                   Config-level, contract, and integration tests
scripts/lint.sh          Local lint script — mirrors CI exactly
pyproject.toml           Ruff linting and formatting config
docker-compose.yml       Service definitions: web app + MongoDB
.env.example             Environment variable template
docs/                    All project documentation
```

## Environment Variables

| Variable                | Default                | Description                                                     |
|-------------------------|------------------------|-----------------------------------------------------------------|
| `JWT_SECRET`            | *(required)*           | Secret key for signing/verifying JWT tokens. Never commit this. |
| `MONGO_USER`            | `admin`                | MongoDB root username (docker-compose).                         |
| `MONGO_PASSWORD`        | `changeme`             | MongoDB root password (docker-compose).                         |
| `MONGO_URI`             | `mongodb://my_db:27017/` | MongoDB connection string.                                    |
| `RATELIMIT_STORAGE_URL` | `memory://`            | Flask-Limiter backing store.                                    |

The application fails fast if `JWT_SECRET` is missing or empty. See
[docs/configuration.md](../docs/configuration.md) for the full reference.

The request sequence and token rules are summarised under **Authentication**
in `AGENTS.md`; full endpoint detail is in [docs/api.md](../docs/api.md).

## Running Locally

```
cp .env.example .env          # then set JWT_SECRET
sudo -S -p '' docker-compose build
sudo -S -p '' docker-compose up
curl http://localhost:5000/hello   # -> "Hello World!"
```

## Running Tests

```
pip install -r web/requirements-dev.txt
pytest -v
# Runs web/tests/ (unit) and tests/ (config + contract); integration tests are
# excluded by default and need a live MongoDB.
```

## Linting

```
./scripts/lint.sh            # check only — same as CI
./scripts/lint.sh --fix      # auto-fix then check
```

Ruff config is in `pyproject.toml`. Rules: E, F, I (pycodestyle, Pyflakes,
isort). Line length: 120. Both `web/` and `tests/` are in scope.

## CI Pipeline

Two workflows cover all changes (neither is named `ci.yml`):

- **Pull Request Gate** — `.github/workflows/pr_gate.yml` runs on every PR
  targeting `main`: `lint -> test`.
- **Release Pipeline** — `.github/workflows/release.yml` runs on every push to
  `main` and via `workflow_dispatch`: `lint -> test -> tag & release`.

lint: `ruff check` + `ruff format --check`
test: `pytest -v` (only runs if lint passes)

See [docs/ci-cd.md](../docs/ci-cd.md) for the full detail.

## Code Conventions

- All imports must be sorted (ruff I rules enforced in CI).
- Use `insert_one` / `update_one` and `count_documents` (PyMongo 4.x API — not the
  deprecated `insert`/`update`/`cursor.count()`).
- JWT datetime must use timezone-aware datetimes: `datetime.datetime.now(timezone.utc)`.
- Passwords are bcrypt-hashed — never stored in plaintext.
- All endpoints return `{"status": <code>, ...}` JSON bodies.
- Logging uses module-level loggers; never log passwords, tokens, or connection
  strings. See [docs/logging.md](../docs/logging.md).

## Project Rules

Authoritative rules on verification, review, conventions, and context efficiency
live in [`openspec/config.yaml`](../openspec/config.yaml). This file does not
duplicate them.

# DewaldOosthuizen/python_rest_tutorial — Agent Instructions

This file instructs AI coding agents (Hermes, GitHub Copilot, Codex, etc.) on how
to orient themselves in this repository efficiently.

## Project Overview

An educational repository demonstrating how to build RESTful APIs using Python,
Flask, Docker, and MongoDB. Covers best practices for scalable API design,
containerisation, JWT authentication, password hashing, and testing.

Reference article:
<https://www.dvt.co.za/news-insights/insights/item/355-restful-web-services-using-python-flask-docker-and-mongodb>

## Documentation

All project documentation lives under [`docs/`](docs/index.md) — architecture, API
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
[docs/configuration.md](docs/configuration.md) for the full reference.

## Authentication

The API uses JWT bearer tokens. Tokens are HS256-signed, carry the username in the
`sub` claim, and expire after **1 hour**.

Obtain a token:

```
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret"}'
```

Response: `{"status": 200, "token": "<signed-jwt>"}`

Pass the token on protected endpoints (`/retrieve`, `/save`):

```
curl -X POST http://localhost:5000/retrieve \
  -H "Authorization: Bearer <token>"
```

Missing, expired, or tampered tokens return 401 Unauthorized. Full endpoint
detail: [docs/api.md](docs/api.md).

## Running Tests

Run from the project root — pytest discovers both `web/tests/` and `tests/`:

```
pip install -r web/requirements-dev.txt
pytest -v
```

Integration tests are excluded by default (`pytest.ini` sets
`-m "not integration"`) and need a live MongoDB. See
[docs/testing.md](docs/testing.md).

## Linting

The project uses Ruff (replaces flake8 + isort + black). Config is in
`pyproject.toml`.

```
./scripts/lint.sh            # check only — same as CI
./scripts/lint.sh --fix      # auto-fix then check
```

## CI / CD

Documentation for the CI/CD pipeline lives in [docs/ci-cd.md](docs/ci-cd.md).
Two workflows cover all changes:

- **Pull Request Gate** — `.github/workflows/pr_gate.yml` runs on every PR
  targeting `main`. It validates lint (ruff check + ruff format --check) then
  tests (pytest -v), and cancels in-progress runs on new commits.
- **Release Pipeline** — `.github/workflows/release.yml` runs on every push to
  `main` and via `workflow_dispatch`. It re-validates lint+tests on the exact
  commit being released, computes a CalVer tag, creates and pushes the tag, and
  creates a GitHub Release with auto-generated notes. No build artifacts are
  attached (this is an educational demo repo without a distributable package).

Local verification mirrors CI: `./scripts/lint.sh && pytest -v`.

## Postman

Add `Content-Type: application/json` to request headers, or use
`request.get_json(force=True)` in endpoints to skip the header requirement.
See <https://github.com/DewaldOosthuizen/python_rest_tutorial/issues/1> for context.

## Dependency Management

All dependencies are exact-pinned in `web/requirements.txt` (runtime) and
`web/requirements-dev.txt` (test/lint). Upgrade procedure:
[docs/dependencies.md](docs/dependencies.md).

## Project Rules

Authoritative rules on verification, review, conventions, and context efficiency
live in [`openspec/config.yaml`](openspec/config.yaml). This file does not
duplicate them.

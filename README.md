# python_rest_tutorial

[![CI](https://github.com/DewaldOosthuizen/python_rest_tutorial/actions/workflows/ci.yml/badge.svg)](https://github.com/DewaldOosthuizen/python_rest_tutorial/actions/workflows/ci.yml)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/53014a434fb340f2afde9853e2314a8a)](https://www.codacy.com/gh/DewaldOosthuizen/python_rest_tutorial/dashboard?utm_source=github.com&utm_medium=referral&utm_content=DewaldOosthuizen/python_rest_tutorial&utm_campaign=Badge_Grade)

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/paypalme/DewaldOosthuizen1)
[![License](http://img.shields.io/badge/Licence-MIT-brightgreen.svg)](LICENSE.md)

A comprehensive guide and implementation to help developers learn how to create RESTful APIs
using Python, Flask, Docker, and MongoDB. It demonstrates best practices for building scalable
and efficient APIs, leveraging Python's capabilities alongside Docker for containerization.
The repository serves as an educational resource for both beginners and experienced developers
looking to refine their skills in REST API development.

Reference article:
<https://www.dvt.co.za/news-insights/insights/item/355-restful-web-services-using-python-flask-docker-and-mongodb> [Specific to commit sha 87722d939eadaca906fade165829eddb59f906d1] The project has since been updated to use JWT instead of basic auth


## Repository Structure

```
web/                  Python application source (Flask app + Dockerfile)
web/requirements.txt  Pinned runtime dependencies
web/requirements-dev.txt  Dev/test dependencies (pytest, pytest-cov, ruff)
web/tests/            Unit tests for the Flask application
tests/                Integration / config-level tests
scripts/lint.sh       Local lint script (mirrors CI exactly)
docker-compose.yml    Service definitions: app + MongoDB
.env.example          Environment variable template
```


## Getting Started

### 1. Configure environment variables

```shell
cp .env.example .env
```

Edit `.env` and set a strong `JWT_SECRET`. Also set strong values for
`MONGO_USER` and `MONGO_PASSWORD` — the defaults in `.env.example` are
not suitable for production. The `MONGO_URI` value is automatically
assembled from `MONGO_USER` and `MONGO_PASSWORD` by docker-compose at
container startup.

### 2. Build and start the containers

```shell
sudo docker-compose build
sudo docker-compose up
```

### 3. Verify the service

Open <http://localhost:5000/hello> in your browser or run:

```shell
curl http://localhost:5000/hello
```

Expected response: `"Hello World!"`


## Environment Variables

| Variable   | Default                | Description                                                                 |
|------------|------------------------|-----------------------------------------------------------------------------|
| MONGO_USER          | admin                  | MongoDB root username. Used by docker-compose to authenticate the my_db service and to build MONGO_URI. Set to a strong value for production. |
| MONGO_PASSWORD      | changeme               | MongoDB root password. Used by docker-compose to authenticate the my_db service and to build MONGO_URI. Set to a strong value for production. |
| MONGO_URI           | mongodb://my_db:27017/ | MongoDB connection string. Automatically assembled by docker-compose from MONGO_USER and MONGO_PASSWORD; override only for remote or externally-managed MongoDB instances. |
| JWT_SECRET          | *(required)*           | Secret key for signing and verifying JWT tokens. Use a long random string. |

Never hardcode or commit `JWT_SECRET`.


## Authentication

The API uses JWT (JSON Web Token) bearer authentication.

### 1. Register a user — POST /register

```shell
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "yourpassword"}'
```

### 2. Obtain a token — POST /login

```shell
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "yourpassword"}'
```

Response (200 OK):

```json
{"status": 200, "token": "<signed-jwt>"}
```

On invalid credentials the endpoint returns 401.

### 3. Call protected endpoints — Authorization: Bearer
***

Pass the token in the `Authorization` header on every call to `/retrieve` and `/save`:

```shell
# Retrieve messages (default: first 20, total count included)
curl -X POST http://localhost:5000/retrieve \
  -H "Authorization: Bearer ***"

# Retrieve messages with pagination — offset and limit are optional
curl -X POST "http://localhost:5000/retrieve?offset=20&limit=10" \
  -H "Authorization: Bearer ***"

# Save a message
curl -X POST http://localhost:5000/save \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

The `/retrieve` endpoint supports two optional query parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `offset`  | `0`     | Zero-based index of the first message to return. |
| `limit`   | `20`    | Maximum number of messages to return. Capped at **100** server-side. |

The response includes a `total` field with the full message count for the authenticated user, allowing clients to paginate through the entire collection:

```json
{"status": 200, "obj": ["msg-0", "msg-1"], "total": 50}
```

Missing, expired, or tampered tokens return 401 Unauthorized.


## Rate Limiting

To mitigate brute-force credential guessing and account-creation abuse
(OWASP API4:2023 — Unrestricted Resource Consumption), `/login` and
`/register` are throttled per client IP using
[Flask-Limiter](https://flask-limiter.readthedocs.io/):

| Endpoint    | Limit          |
|-------------|----------------|
| `/login`    | 10 per minute  |
| `/register` | 5 per hour     |

Requests beyond the threshold receive an HTTP `429 Too Many Requests`
response. Other endpoints (`/hello`, `/retrieve`, `/save`) are unaffected —
there is no global default limit.

The limiter's counters are backed by the `RATELIMIT_STORAGE_URL` environment
variable, which defaults to `memory://` for local/single-process use. For
production or multi-worker deployments, point it at a shared store such as
Redis, e.g. `RATELIMIT_STORAGE_URL=redis://redis:6379`.


## Input Validation

To prevent oversized payloads from causing memory pressure or unnecessary
bcrypt work, the API enforces the following per-field limits. Violations
return HTTP 400 with a descriptive message.

| Field      | Endpoint(s)        | Max length | Type   |
|------------|--------------------|------------|--------|
| username   | /register, /login  | 64 chars   | string |
| password   | /register, /login  | 128 chars  | string |
| message    | /save              | 1024 chars | string |

Non-string values (e.g. a JSON number or array) for any of these fields also
return HTTP 400.

In addition to per-field limits, the API enforces a maximum total request body
size of 1 MB (`MAX_CONTENT_LENGTH = 1_048_576` bytes). This limit is checked
before the body is parsed, so oversized payloads are rejected with
HTTP 413 (Request Body Too Large) before consuming memory.


## Using Postman

Add `Content-Type: application/json` to your request headers.

If you prefer not to set the content-type header manually, the endpoints use
`request.get_json(force=True)` which will parse the body as JSON regardless.

See <https://github.com/DewaldOosthuizen/python_rest_tutorial/issues/1> for context.


## Running the Tests

Install dependencies and run the full test suite from the project root:

```bash
pip install -r web/requirements-dev.txt
pytest -v
```

This runs both `web/tests/` (unit tests) and `tests/` (config and API-contract tests).


## Linting

The project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
(replaces flake8 + isort + black in a single fast tool).

### Run locally (mirrors CI exactly)

```bash
# Check only
./scripts/lint.sh

# Auto-fix then check
./scripts/lint.sh --fix
```

### Run ruff directly

```bash
ruff check web/ tests/           # lint
ruff format --check web/ tests/  # format check
ruff format web/ tests/          # apply formatting
```

Ruff is included in `web/requirements-dev.txt` so no separate install is needed
once the dev dependencies are installed.


## CI Pipeline

Every push and pull request runs the GitHub Actions CI pipeline:

```
lint  →  test
```

- **lint** — `ruff check` + `ruff format --check` across `web/` and `tests/`
- **test** — `pytest -v` (only runs if lint passes)

The pipeline is defined in `.github/workflows/ci.yml`.


## Dependencies

All runtime dependencies are pinned in `web/requirements.txt` and
development/test dependencies are pinned in `web/requirements-dev.txt`
(which itself pulls in `requirements.txt` via `-r`) to ensure reproducible
builds across local, CI, and Docker environments.

### Runtime dependencies

| Package       | Version  | Role                      |
|---------------|----------|---------------------------|
| Flask         | 3.1.3    | Web framework             |
| Werkzeug      | >=3.0.0  | WSGI utilities            |
| flask-restful | 0.3.10   | REST resource helpers     |
| pymongo       | 4.7.2    | MongoDB driver            |
| bcrypt        | 4.1.3    | Password hashing          |
| PyJWT         | >=2.8.0  | JWT authentication        |
| Flask-Limiter | 3.7.0    | Rate limiting             |

### Development dependencies

| Package       | Version  | Role                      |
|---------------|----------|---------------------------|
| pytest        | 9.0.3    | Test runner               |
| pytest-cov    | >=4.1    | Coverage reports          |
| ruff          | >=0.5.0  | Linting and formatting    |

### Upgrade procedure

1. For runtime deps: update the version in `web/requirements.txt`.
2. For test/lint tooling: update the version in `web/requirements-dev.txt`.
3. Reinstall: `pip install -r web/requirements-dev.txt`
4. Run the test suite: `pytest -v`
5. Run the linter: `./scripts/lint.sh`
6. If all checks pass, commit the updated requirement file(s).


## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for
the full workflow, including how to pick up an issue, branch naming conventions,
local validation steps, and the pull request process.

# python_rest_tutorial

[![PR Gate](https://github.com/DewaldOosthuizen/python_rest_tutorial/actions/workflows/pr_gate.yml/badge.svg)](https://github.com/DewaldOosthuizen/python_rest_tutorial/actions/workflows/pr_gate.yml)
[![Release](https://github.com/DewaldOosthuizen/python_rest_tutorial/actions/workflows/release.yml/badge.svg)](https://github.com/DewaldOosthuizen/python_rest_tutorial/actions/workflows/release.yml)

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/paypalme/DewaldOosthuizen1)
[![License](http://img.shields.io/badge/Licence-MIT-brightgreen.svg)](LICENSE.md)

A comprehensive guide and implementation to help developers learn how to create
RESTful APIs using Python, Flask, Docker, and MongoDB. It demonstrates best
practices for building scalable and efficient APIs, leveraging Python's
capabilities alongside Docker for containerization. The repository serves as an
educational resource for both beginners and experienced developers looking to
refine their skills in REST API development.

Reference article:
<https://www.dvt.co.za/news-insights/insights/item/355-restful-web-services-using-python-flask-docker-and-mongodb>

> Specific to commit sha `87722d939eadaca906fade165829eddb59f906d1`. The project
> has since been updated to use JWT instead of basic auth.

## Quick start

```shell
cp .env.example .env          # then set a strong JWT_SECRET
sudo docker-compose build
sudo docker-compose up
curl http://localhost:5000/hello   # -> "Hello World!"
```

## Documentation

All project documentation lives under [`docs/`](docs/index.md). Start there for
the full picture.

| Page | Contents |
|------|----------|
| [Architecture](docs/architecture.md) | Layering, request lifecycle, security model |
| [API Reference](docs/api.md) | Endpoints, error envelope, rate limits, validation |
| [Configuration](docs/configuration.md) | Environment variables and production checklist |
| [Local Development](docs/local-development.md) | Setup, run, troubleshoot |
| [Testing](docs/testing.md) | Unit and integration suites |
| [Linting & Code Quality](docs/linting.md) | Ruff and project conventions |
| [Logging](docs/logging.md) | Logging approach and rules |
| [CI & CD](docs/ci-cd.md) | PR Gate, Release, CalVer |
| [Dependencies](docs/dependencies.md) | Pinning policy and upgrade procedure |
| [Contributing](docs/contributing.md) | Workflow, branch naming, PR process |

## Repository Structure

```
web/                     Flask application source (app.py, error_handlers.py) + Dockerfile
web/requirements.txt     Pinned runtime dependencies
web/requirements-dev.txt Pinned test/lint dependencies (pulls in requirements.txt)
web/tests/               Unit tests for the Flask application
tests/                   Config-level, contract, and integration tests
scripts/lint.sh          Local lint script (mirrors CI exactly)
pyproject.toml           Ruff linting and formatting config
docker-compose.yml       Service definitions: web app + MongoDB
.env.example             Environment variable template
docs/                    All project documentation
```

## Contributing

Contributions are welcome. Please read
[docs/contributing.md](docs/contributing.md) for the full workflow, including how
to pick up an issue, branch naming conventions, local validation steps, and the
pull request process.

## Licence

MIT - see [LICENSE.md](LICENSE.md).

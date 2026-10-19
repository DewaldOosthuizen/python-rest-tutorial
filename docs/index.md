# Documentation Index

All persistent project documentation lives under this directory. This page is
the entry point — start here.

## Documentation map

| Page | Contents |
|------|----------|
| [Architecture](architecture.md) | Overview, layering, request lifecycle, security model, design decisions |
| [API Reference](api.md) | Every endpoint, the error envelope, rate limits, input validation, auth flow |
| [Configuration](configuration.md) | Every environment variable, local setup, container config, production checklist |
| [Local Development](local-development.md) | Prerequisites, build & run, running without Docker, troubleshooting |
| [Testing](testing.md) | Unit and integration suites, `pytest.ini`, how to write tests |
| [Linting & Code Quality](linting.md) | Ruff setup, `pyproject.toml`, project conventions |
| [Logging](logging.md) | Logger pattern, configuration ownership, what is and is not logged |
| [CI & CD](ci-cd.md) | PR Gate and Release workflows, CalVer, dependency updates |
| [Dependencies](dependencies.md) | Pinning policy, runtime and dev tables, upgrade procedure |
| [Contributing](contributing.md) | Issue workflow, branch naming, PR process, coding standards |

## Where the root pointers lead

| Root file | Role |
|-----------|------|
| `README.md` | Project summary, quick start, and pointers into this directory |
| `AGENTS.md` | Instructions for AI coding agents working in this repository |
| `CONTRIBUTING.md` | Thin pointer to [contributing.md](contributing.md) |
| `LICENSE.md` | Licence text, kept at the repository root |

## Authoritative rules

For the authoritative rules on verification, review, conventions, and context
efficiency, see [`../openspec/config.yaml`](../openspec/config.yaml).

## Documentation conventions

When behaviour, API contracts, deployment steps, or architecture change, update
the relevant page under this directory **in the same change**. Code and docs must
stay in sync.

Rules:

- Every fact lives in exactly one place. Where a page needs a value that another
  page owns, link to it rather than repeating it.
- Keep root-level files thin. `README.md` and `AGENTS.md` summarise and link;
  they do not duplicate.
- Do not document historical decisions here. Past change records stay in
  `openspec/`.

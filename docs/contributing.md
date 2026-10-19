# Contributing

Thank you for contributing. This guide covers the full workflow for making clean,
reviewable contributions to this repository.

## Code of Conduct

Be respectful, constructive, and collaborative. Contributions that are
disrespectful, dismissive, or harmful will not be accepted.

## Getting Started

1. Fork the repository.
2. Clone your fork locally.
3. Follow the [local development setup](local-development.md).

## Picking Up an Issue

**Before you write a single line of code:**

1. Browse the [GitHub Issues](https://github.com/DewaldOosthuizen/python_rest_tutorial/issues) tab and find an issue you want to work on.
2. **Assign the issue to yourself** before starting any work — issue page →
   Assignees (right sidebar) → assign yourself. This signals to other
   contributors that the issue is claimed.
3. Leave a comment stating you are picking it up and your intended approach —
   especially for larger changes.
4. Only then create your branch and begin work.

> Why this matters: two contributors working on the same issue in parallel wastes
> effort and creates painful merge conflicts. A self-assignment takes five seconds
> and saves hours.

If you were assigned an issue but can no longer work on it, unassign yourself and
leave a comment so someone else can pick it up.

## Branch Naming

| Prefix     | Pattern                      | When to use                         |
|------------|------------------------------|-------------------------------------|
| `feature/` | `feature/<issue-id>-<topic>` | New tutorial section or API feature |
| `fix/`     | `fix/<issue-id>-<topic>`     | Bug fix                             |
| `chore/`   | `chore/<topic>`              | Tooling, deps, CI, config updates   |
| `docs/`    | `docs/<topic>`               | Documentation only                  |

Examples:

- `feature/42-add-authentication-tutorial`
- `fix/17-fix-mongodb-connection-handling`
- `docs/update-contributing-guide`

Always branch from `main`.

## Running Checks Locally

Run these before pushing. CI runs the same checks and a failing PR will not be
reviewed.

```shell
bash scripts/lint.sh
pytest -v
```

Both commands must exit with code `0` before opening a PR.

## Commit Message Style

- Use the **imperative mood** in the subject line: "Add", "Fix", "Remove".
- Limit the subject line to **72 characters**.
- Leave one blank line between the subject and body when a body is needed.
- Reference the related issue in the footer with `Closes #<n>`.

Example:

```
Add JWT authentication tutorial section

Closes #42
```

## Pull Request Process

1. Ensure all local checks pass (see above).
2. Open the PR against `main`.
3. Use a scoped, descriptive title: `fix: resolve #17 - MongoDB connection error on cold start`.
4. In the PR body:
   - Link the issue: `Closes #<n>`
   - Describe the user-visible change.
   - Include terminal output for API or behaviour changes.
5. Request a review. Do not merge your own PR without a review.
6. Address review feedback with follow-up commits — do not force-push a reviewed
   branch unless asked.

## Coding Standards

See [Linting & Code Quality](linting.md) for the full conventions. Summary:

- Follow PEP 8. Use `ruff` for linting and formatting (configured in `pyproject.toml`).
- Keep functions small and explicit with clear docstrings.
- Use module-level loggers: `logger = logging.getLogger(__name__)`.
- Do not add `logging.basicConfig(...)` inside library modules under `web/`.
- Keep tutorial code readable and well-commented — this is an educational resource.
- Add or update tests in `tests/` or `web/tests/` whenever behaviour changes.
- Keep documentation in sync with code — all project documentation lives under
  [`docs/`](index.md), and changes that affect behaviour, contracts, or
  deployment should update the relevant page in the same change.

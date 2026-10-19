# CI & CD Pipeline

## Workflows

Two workflows cover all changes. Neither is named `ci.yml`.

### Pull Request Gate — `.github/workflows/pr_gate.yml`

Runs on every pull request targeting `main`:

```
lint  →  test
```

- **lint** — `ruff check web/ tests/` and `ruff format --check web/ tests/`
- **test** — `pytest -v` (only runs if lint passes)

A `concurrency` block cancels in-progress runs when a new commit lands on the PR.

### Release Pipeline — `.github/workflows/release.yml`

Runs on every push to `main` and via `workflow_dispatch`:

```
lint  →  test  →  version-tag-release
```

- **lint / test** — identical to the PR gate, deliberately duplicated so the exact
  commit being released is re-validated.
- **version-tag-release** — computes a CalVer tag (`YYYY.MM.DD`, or
  `YYYY.MM.DD.Micro` when more than one release happens on the same day), creates
  and pushes the tag, and creates a GitHub Release with auto-generated notes.

The tag step skips if `HEAD` already carries the latest CalVer tag, so re-running
the workflow is safe.

### CalVer

Tags are **CalVer only**: `YYYY.MM.DD` with an optional `.Micro` suffix. Legacy
non-CalVer tags have been removed. This repo has no distributable package, so a
release is a tagged, tested snapshot of the tutorial source plus GitHub Release
notes — no artifacts are attached.

## Local verification

CI runs the same checks locally:

```shell
./scripts/lint.sh && pytest -v
```

A PR that does not pass locally will not pass in CI.

## Dependency updates

`.github/dependabot.yml` watches the `pip` ecosystem under `/web/`, grouping all
dependency updates into a single monthly pull request. Dependabot PRs go through
the same PR Gate lint + test workflow.

## Verification rules

For the authoritative rules on verification, review, conventions, and context
efficiency, see [`openspec/config.yaml`](../openspec/config.yaml).

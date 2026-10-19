# Contributing

The full contribution guide — code of conduct, issue workflow, branch naming,
local checks, commit style, pull request process, and coding standards — lives in
[docs/contributing.md](docs/contributing.md).

Quick version:

1. Assign the issue to yourself before starting work.
2. Branch from `main` using `feature/<issue-id>-<topic>`, `fix/<issue-id>-<topic>`,
   `chore/<topic>`, or `docs/<topic>`.
3. Run `./scripts/lint.sh && pytest -v` and make sure both pass.
4. Open the PR against `main` with a scoped title, link the issue, and request a
   review.

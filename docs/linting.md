# Linting & Code Quality

The project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
— it replaces flake8 + isort + black in a single tool. Configuration lives in
`pyproject.toml`.

## Run locally

```shell
./scripts/lint.sh            # check only — same as CI
./scripts/lint.sh --fix      # auto-fix then check
```

`scripts/lint.sh` runs `ruff check web/ tests/` followed by
`ruff format --check web/ tests/`, which mirrors the CI lint job exactly.

## Run ruff directly

```shell
ruff check web/ tests/           # lint
ruff format --check web/ tests/  # format check
ruff format web/ tests/          # apply formatting
```

## Configuration

`pyproject.toml`:

```toml
[tool.ruff]
target-version = "py311"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I"]   # pycodestyle, Pyflakes, isort
```

Per-file ignores relax a few rules for test files, where asserts and hardcoded
passwords are intentional.

## Conventions

- Imports are sorted (`ruff` I rules are enforced in CI).
- Use `insert_one` / `update_one` and `count_documents` — the PyMongo 4.x API.
- JWT timestamps use timezone-aware datetimes:
  `datetime.datetime.now(timezone.utc)`.
- Passwords are bcrypt-hashed, never stored in plaintext.
- Every endpoint returns a `{"status": <code>, ...}` JSON body.
- Logging uses module-level loggers (`logging.getLogger(__name__)`); no
  `logging.basicConfig` inside `web/` library modules. See
  [Logging](logging.md).

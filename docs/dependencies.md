# Dependencies

## Pinning policy

All dependencies are **exact-pinned** for reproducible builds across local, CI,
and Docker environments. There are two files:

| File | Contents |
|------|----------|
| `web/requirements.txt` | Runtime dependencies |
| `web/requirements-dev.txt` | Test and lint tooling; starts with `-r requirements.txt` |

Because `requirements-dev.txt` includes `requirements.txt` via `-r`, installing
the dev file gives you everything.

## Runtime dependencies

| Package       | Version   | Role                  |
|---------------|-----------|-----------------------|
| Flask         | 3.1.3     | Web framework         |
| Werkzeug      | >=3.1.9   | WSGI utilities        |
| flask-restful | 0.3.10    | REST resource helpers |
| pymongo       | 4.18.2    | MongoDB driver        |
| bcrypt        | 5.0.0     | Password hashing      |
| PyJWT         | >=2.15.1  | JWT authentication    |
| Flask-Limiter | 4.1.1     | Rate limiting         |

## Development dependencies

| Package       | Version | Role                   |
|---------------|---------|------------------------|
| pytest        | 9.1.1   | Test runner            |
| pytest-cov    | 7.1.0   | Coverage reports       |
| ruff          | 0.16.9  | Linting and formatting |

## Upgrade procedure

1. For runtime deps: update the version in `web/requirements.txt`.
2. For test/lint tooling: update the version in `web/requirements-dev.txt`.
3. Reinstall: `pip install -r web/requirements-dev.txt`
4. Run the test suite: `pytest -v`
5. Run the linter: `./scripts/lint.sh`
6. If all checks pass, commit the updated requirement file(s).

`web/Dockerfile` installs only `requirements.txt`, so the container stays lean —
dev tooling never ships in the image.

## Automated updates

`.github/dependabot.yml` proposes monthly grouped updates for the `pip`
ecosystem under `/web/`. Each Dependabot PR runs the PR Gate workflow
([CI & CD](ci-cd.md)).

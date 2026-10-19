# Testing

## Install dependencies

```shell
pip install -r web/requirements-dev.txt
```

`requirements-dev.txt` pulls in `requirements.txt` via `-r`, so one install covers
runtime, test, and lint tooling.

## Run the test suite

From the project root:

```shell
pytest -v
```

`pytest.ini` sets `testpaths = web/tests tests`, so a bare `pytest` discovers both
suites:

| Suite | Location | Scope |
|-------|----------|-------|
| Unit tests | `web/tests/` | Application behaviour with MongoDB mocked |
| Config / contract tests | `tests/` | Configuration, API contracts, PyMongo API usage |

`pytest.ini` also declares the `integration` marker and sets
`addopts = -m "not integration"`, so integration tests are **excluded** from a
default run and must be opted into explicitly.

## Integration tests

Integration tests need a live MongoDB instance and a real `JWT_SECRET`. Start the
database:

```shell
docker-compose up -d my_db
```

Then run:

```shell
export JWT_SECRET="your-test-secret"
MONGO_URI="mongodb://127.0.0.1:27017/" pytest -m integration -v
```

Tear down when finished:

```shell
docker-compose down
```

The module-level guards in `tests/test_integration_auth_flow.py` skip the whole
file if `JWT_SECRET` is unset or MongoDB is unreachable, so a plain `pytest -m
integration` on a machine without a database exits cleanly rather than erroring.

## Writing tests

- Put unit tests in `web/tests/`, config and contract tests in `tests/`.
- Keep the educational goal in mind: tests should read clearly.
- Mark any test needing a live database with `@pytest.mark.integration`.
- New behaviour needs a test in the same change.

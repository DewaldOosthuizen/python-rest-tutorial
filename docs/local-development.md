# Running Locally

## Prerequisites

- **Python 3.11+**
- **Docker** (for the MongoDB container)

## 1. Configure environment variables

```shell
cp .env.example .env
```

Then edit `.env` and set a strong `JWT_SECRET`. The application refuses to start
without it. Full variable reference: [Configuration](configuration.md).

## 2. Build and start the containers

```shell
sudo docker-compose build
sudo docker-compose up
```

This starts the `web` app and the `my_db` MongoDB service.

## 3. Verify the service

```shell
curl http://localhost:5000/hello
```

Expected response: `"Hello World!"`

## Running the app without Docker

`web/app.py` runs directly:

```shell
pip install -r web/requirements-dev.txt
JWT_SECRET="dev-secret" MONGO_URI="mongodb://127.0.0.1:27017/" python web/app.py
```

Point `MONGO_URI` at a reachable MongoDB — a local `docker-compose up -d my_db`
or a remote instance. See [Configuration](configuration.md) for all variables.

## Try the API

Once the containers are up:

```shell
# 1. Register
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "Secret123"}'

# 2. Log in and capture the token
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "Secret123"}'

# 3. Call a protected endpoint
curl -X POST http://localhost:5000/retrieve \
  -H "Authorization: Bearer <token-from-step-2>"
```

Full request/response detail, including pagination and rate limits:
[API Reference](api.md).

## Troubleshooting

| Symptom | Cause |
|---------|-------|
| App exits with `RuntimeError: Required environment variable JWT_SECRET is not set` | `JWT_SECRET` missing or empty in `.env`. |
| `401 Unauthorized` on `/retrieve` or `/save` | Token missing, expired (1 hour), or signed with a different secret. |
| `404 Not found` on a known route | Wrong HTTP method, or the route name is misspelled. |
| Connection refused to MongoDB | Containers not started, or `MONGO_URI` points at the wrong host. |

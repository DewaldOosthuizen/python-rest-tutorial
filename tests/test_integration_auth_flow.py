"""
Integration tests for the full authentication flow (issue #70).

These tests require a live MongoDB instance (the ``my_db`` service from
docker-compose.yml, or any reachable MongoDB reachable via ``MONGO_URI``)
and ``JWT_SECRET`` in the environment.

Run with:
    export JWT_SECRET=... MONGO_URI=mongodb://127.0.0.1:27017/ RATELIMIT_STORAGE_URL=memory://
    pytest -m integration
"""

import os
import socket
import sys
from urllib.parse import urlparse

import pytest

# ---------------------------------------------------------------------------
# Skip guards FIRST: env + Mongo reachability, before importing app.
# ---------------------------------------------------------------------------

if not os.environ.get("JWT_SECRET"):
    pytest.skip("JWT_SECRET is not set; skipping integration tests", allow_module_level=True)

_MONGO_URI = os.environ.get("MONGO_URI", "mongodb://my_db:27017/")
_parsed = urlparse(_MONGO_URI)
_host = _parsed.hostname or "127.0.0.1"
_port = _parsed.port or 27017

try:
    with socket.create_connection((_host, _port), timeout=3):
        pass
except OSError:
    pytest.skip(
        "MongoDB not reachable at %s:%d; skipping integration tests" % (_host, _port),
        allow_module_level=True,
    )

# Isolate rate-limit storage for this module.
os.environ.setdefault("RATELIMIT_STORAGE_URL", "memory://")

web_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
if web_path not in sys.path:
    sys.path.insert(0, web_path)

from app import app, users  # noqa: E402

TEST_USERS = ("it_alice", "it_bob")


@pytest.fixture(autouse=True)
def _clean_users():
    users.delete_many({"Username": {"$in": list(TEST_USERS)}})
    yield
    users.delete_many({"Username": {"$in": list(TEST_USERS)}})


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = False
    with app.test_client() as c:
        yield c


def _register(client, username, password="Secret123"):
    return client.post("/register", json={"username": username, "password": password})


def _login(client, username, password="Secret123"):
    return client.post("/login", json={"username": username, "password": password})


@pytest.mark.integration
def test_register_user(client):
    resp = _register(client, "it_alice")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == 200


@pytest.mark.integration
def test_login_returns_token(client):
    _register(client, "it_alice")
    resp = _login(client, "it_alice")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == 200
    assert "token" in data and data["token"]


@pytest.mark.integration
def test_save_and_retrieve(client):
    _register(client, "it_alice")
    login_resp = _login(client, "it_alice")
    token = login_resp.get_json()["token"]

    save_resp = client.post(
        "/save",
        json={"message": "hello integration"},
        headers={"Authorization": "Bearer " + token},
    )
    assert save_resp.status_code == 200

    retrieve_resp = client.post("/retrieve", headers={"Authorization": "Bearer " + token})
    assert retrieve_resp.status_code == 200
    data = retrieve_resp.get_json()
    assert data["status"] == 200
    assert data["obj"] == ["hello integration"]
    assert data["total"] == 1


@pytest.mark.integration
def test_second_user_isolation(client):
    _register(client, "it_alice")
    _register(client, "it_bob")
    alice_token = _login(client, "it_alice").get_json()["token"]
    bob_token = _login(client, "it_bob").get_json()["token"]

    client.post(
        "/save",
        json={"message": "alice msg"},
        headers={"Authorization": "Bearer " + alice_token},
    )
    client.post(
        "/save",
        json={"message": "bob msg"},
        headers={"Authorization": "Bearer " + bob_token},
    )

    alice_data = client.post("/retrieve", headers={"Authorization": "Bearer " + alice_token}).get_json()
    bob_data = client.post("/retrieve", headers={"Authorization": "Bearer " + bob_token}).get_json()

    assert alice_data["obj"] == ["alice msg"]
    assert bob_data["obj"] == ["bob msg"]
    assert alice_data["total"] == 1
    assert bob_data["total"] == 1

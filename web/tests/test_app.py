"""
Tests for web/app.py — Flask REST tutorial.

Patching strategy
-----------------
All three helpers (user_exist, verify_user, get_user_messages) call
    app.users.find({"Username": ...})
and then either .count() or [0][field].  We therefore patch `app.users`
and configure the returned cursor with both count() and __getitem__.

We NEVER use find_one — it is not called anywhere in app.py.
"""

import datetime
import os
from datetime import timezone
from unittest.mock import MagicMock, patch

import bcrypt
import jwt
import pytest

# Set JWT_SECRET before importing app
os.environ["JWT_SECRET"] = "testsecret"

from app import app

TEST_SECRET = "testsecret"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user_cursor(username="alice", password="secret", messages=None):
    hashed = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())
    user_doc = {
        "Username": username,
        "Password": hashed,
        "Messages": messages or [],
    }
    cursor = MagicMock()
    cursor.__getitem__.return_value = user_doc
    return cursor


def make_empty_cursor():
    cursor = MagicMock()
    return cursor


def make_valid_token(username="alice", secret=TEST_SECRET):
    return jwt.encode(
        {"sub": username, "exp": datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)},
        secret,
        algorithm="HS256",
    )


def make_expired_token(username="alice"):
    return jwt.encode(
        {"sub": username, "exp": datetime.datetime.now(timezone.utc) - datetime.timedelta(seconds=1)},
        TEST_SECRET,
        algorithm="HS256",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    app.config["TESTING"] = True
    # PROPAGATE_EXCEPTIONS must be False so unhandled exceptions (e.g. KeyError)
    # are surfaced as HTTP 500 responses rather than bubbling up as Python exceptions.
    app.config["PROPAGATE_EXCEPTIONS"] = False
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Hello
# ---------------------------------------------------------------------------


def test_hello_returns_200(client):
    rv = client.get("/hello")
    assert rv.status_code == 200


def test_hello_returns_hello_world(client):
    rv = client.get("/hello")
    assert rv.status_code == 200
    assert rv.get_json() == "Hello World!"
    assert rv.headers["Content-Type"].startswith("application/json")


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


@patch("app.users")
def test_register_new_user_returns_200(mock_users, client):
    mock_users.count_documents.return_value = 0
    rv = client.post("/register", json={"username": "alice", "password": "Str0ngPwd"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == 200


@patch("app.users")
def test_register_existing_user_returns_invalid(mock_users, client):
    mock_users.count_documents.return_value = 1
    rv = client.post("/register", json={"username": "alice", "password": "Str0ngPwd"})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400


def test_register_missing_body_returns_400(client):
    rv = client.post("/register", json={})
    assert rv.status_code == 400


@patch("app.users")
def test_register_oversized_username_returns_400(mock_users, client):
    mock_users.count_documents.return_value = 0
    oversized = "a" * 65
    rv = client.post("/register", json={"username": oversized, "password": "Str0ngPwd"})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "username" in data["msg"]
    assert "64" in data["msg"]


@patch("app.users")
def test_register_oversized_password_returns_400(mock_users, client):
    mock_users.count_documents.return_value = 0
    oversized = "a" * 129
    rv = client.post("/register", json={"username": "alice", "password": oversized})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "password" in data["msg"]
    assert "128" in data["msg"]


def test_register_non_string_username_returns_400(rate_limited_client):
    rv = rate_limited_client.post("/register", json={"username": 123, "password": "Str0ngPwd"})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "username" in data["msg"]
    assert "string" in data["msg"]


def test_register_non_string_password_returns_400(rate_limited_client):
    rv = rate_limited_client.post("/register", json={"username": "alice", "password": 456})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "password" in data["msg"]
    assert "string" in data["msg"]


def test_register_short_password_returns_400(rate_limited_client):
    rv = rate_limited_client.post("/register", json={"username": "alice", "password": "Ab1"})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "password must be at least 8 characters" in data["msg"]


def test_register_password_missing_uppercase_returns_400(rate_limited_client):
    rv = rate_limited_client.post("/register", json={"username": "alice", "password": "str0ngpwd"})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "password must contain at least one uppercase letter" in data["msg"]


def test_register_password_missing_lowercase_returns_400(rate_limited_client):
    rv = rate_limited_client.post("/register", json={"username": "alice", "password": "STR0NGPWD"})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "password must contain at least one lowercase letter" in data["msg"]


def test_register_password_missing_digit_returns_400(rate_limited_client):
    rv = rate_limited_client.post("/register", json={"username": "alice", "password": "Str0ngPwd".replace("0", "")})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "password must contain at least one digit" in data["msg"]


@patch("app.users")
def test_register_strong_password_returns_200(mock_users, rate_limited_client):
    mock_users.count_documents.return_value = 0
    rv = rate_limited_client.post("/register", json={"username": "alice", "password": "Str0ngPwd"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == 200


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@patch("app.users")
def test_login_valid_credentials_returns_token(mock_users, client):
    mock_users.count_documents.return_value = 1
    mock_users.find.return_value = make_user_cursor(username="alice", password="secret")
    rv = client.post("/login", json={"username": "alice", "password": "secret"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == 200
    assert "token" in data


@patch("app.users")
def test_login_wrong_password_returns_401(mock_users, client):
    mock_users.count_documents.return_value = 1
    mock_users.find.return_value = make_user_cursor(username="alice", password="correct")
    rv = client.post("/login", json={"username": "alice", "password": "wrong"})
    assert rv.status_code == 401
    assert rv.get_json()["status"] == 401


@patch("app.users")
def test_login_unknown_user_returns_401(mock_users, client):
    mock_users.count_documents.return_value = 0
    rv = client.post("/login", json={"username": "ghost", "password": "x"})
    assert rv.status_code == 401


def test_login_missing_body_returns_400(client):
    rv = client.post("/login", json={})
    assert rv.status_code == 400


@patch("app.users")
def test_login_oversized_username_returns_400(mock_users, client):
    mock_users.count_documents.return_value = 0
    oversized = "a" * 65
    rv = client.post("/login", json={"username": oversized, "password": "secret"})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "username" in data["msg"]
    assert "64" in data["msg"]


@patch("app.users")
def test_login_oversized_password_returns_400(mock_users, client):
    mock_users.count_documents.return_value = 0
    oversized = "a" * 129
    rv = client.post("/login", json={"username": "alice", "password": oversized})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "password" in data["msg"]
    assert "128" in data["msg"]


def test_login_non_string_username_returns_400(client):
    rv = client.post("/login", json={"username": 123, "password": "secret"})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "username" in data["msg"]
    assert "string" in data["msg"]


def test_login_non_string_password_returns_400(client):
    rv = client.post("/login", json={"username": "alice", "password": 456})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "password" in data["msg"]
    assert "string" in data["msg"]


# ---------------------------------------------------------------------------
# Retrieve
# ---------------------------------------------------------------------------


@patch("app.users")
def test_retrieve_no_auth_header_returns_401(mock_users, client):
    rv = client.post("/retrieve")
    assert rv.status_code == 401
    assert rv.get_json()["status"] == 401


@patch("app.users")
def test_retrieve_expired_token_returns_401(mock_users, client):
    token = make_expired_token()
    rv = client.post("/retrieve", headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 401


@patch("app.users")
def test_retrieve_tampered_token_returns_401(mock_users, client):
    rv = client.post("/retrieve", headers={"Authorization": "Bearer tampered.token.value"})
    assert rv.status_code == 401


@patch("app.users")
def test_retrieve_valid_token_returns_messages(mock_users, client):
    mock_users.count_documents.return_value = 1
    mock_users.find.return_value = make_user_cursor(username="alice", messages=["hello"])
    token = make_valid_token(username="alice")
    rv = client.post("/retrieve", headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == 200
    assert "hello" in data["obj"]


@patch("app.users")
def test_retrieve_default_pagination_returns_first_20_with_total(mock_users, client):
    messages = [f"msg-{i}" for i in range(50)]
    mock_users.count_documents.return_value = 1
    mock_users.find.return_value = make_user_cursor(username="alice", messages=messages)
    token = make_valid_token(username="alice")
    rv = client.post("/retrieve", headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == 200
    assert data["total"] == 50
    assert len(data["obj"]) == 20
    assert data["obj"] == messages[:20]


@patch("app.users")
def test_retrieve_custom_limit_returns_requested_number(mock_users, client):
    messages = [f"msg-{i}" for i in range(20)]
    mock_users.count_documents.return_value = 1
    mock_users.find.return_value = make_user_cursor(username="alice", messages=messages)
    token = make_valid_token(username="alice")
    rv = client.post(
        "/retrieve",
        headers={"Authorization": f"Bearer {token}"},
        query_string="limit=5",
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == 200
    assert data["total"] == 20
    assert len(data["obj"]) == 5
    assert data["obj"] == messages[:5]


@patch("app.users")
def test_retrieve_custom_offset_skips_correct_messages(mock_users, client):
    messages = [f"msg-{i}" for i in range(20)]
    mock_users.count_documents.return_value = 1
    mock_users.find.return_value = make_user_cursor(username="alice", messages=messages)
    token = make_valid_token(username="alice")
    rv = client.post(
        "/retrieve",
        headers={"Authorization": f"Bearer {token}"},
        query_string="offset=5&limit=5",
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == 200
    assert data["total"] == 20
    assert len(data["obj"]) == 5
    assert data["obj"] == messages[5:10]


@patch("app.users")
def test_retrieve_offset_beyond_collection_returns_empty_page(mock_users, client):
    messages = [f"msg-{i}" for i in range(10)]
    mock_users.count_documents.return_value = 1
    mock_users.find.return_value = make_user_cursor(username="alice", messages=messages)
    token = make_valid_token(username="alice")
    rv = client.post(
        "/retrieve",
        headers={"Authorization": f"Bearer {token}"},
        query_string="offset=20&limit=5",
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == 200
    assert data["total"] == 10
    assert data["obj"] == []


@patch("app.users")
def test_retrieve_limit_capped_at_100(mock_users, client):
    messages = [f"msg-{i}" for i in range(150)]
    mock_users.count_documents.return_value = 1
    mock_users.find.return_value = make_user_cursor(username="alice", messages=messages)
    token = make_valid_token(username="alice")
    rv = client.post(
        "/retrieve",
        headers={"Authorization": f"Bearer {token}"},
        query_string="limit=200",
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == 200
    assert data["total"] == 150
    assert len(data["obj"]) == 100
    assert data["obj"] == messages[:100]


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------


@patch("app.users")
def test_save_no_auth_header_returns_401(mock_users, client):
    rv = client.post("/save", json={"message": "hi"})
    assert rv.status_code == 401


@patch("app.users")
def test_save_expired_token_returns_401(mock_users, client):
    token = make_expired_token()
    rv = client.post("/save", json={"message": "hi"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 401


@patch("app.users")
def test_save_valid_token_saves_and_returns_200(mock_users, client):
    token = make_valid_token(username="alice")
    rv = client.post(
        "/save",
        json={"message": "hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rv.status_code == 200
    assert rv.get_json()["status"] == 200


@patch("app.users")
def test_save_missing_message_returns_400(mock_users, client):
    token = make_valid_token(username="alice")
    rv = client.post(
        "/save",
        json={},
        headers={"Authorization": "Bearer " + token},
    )
    assert rv.status_code == 400


@patch("app.users")
def test_save_oversized_message_returns_400(mock_users, client):
    token = make_valid_token(username="alice")
    oversized = "a" * 1025
    rv = client.post(
        "/save",
        json={"message": oversized},
        headers={"Authorization": "Bearer " + token},
    )
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "message" in data["msg"]
    assert "1024" in data["msg"]


@patch("app.users")
def test_save_non_string_message_returns_400(mock_users, client):
    token = make_valid_token(username="alice")
    rv = client.post(
        "/save",
        json={"message": [1, 2, 3]},
        headers={"Authorization": "Bearer " + token},
    )
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == 400
    assert "message" in data["msg"]
    assert "string" in data["msg"]


# ---------------------------------------------------------------------------
# insert_one / update_one API migration (issue #6)
# ---------------------------------------------------------------------------


@patch("app.users")
def test_register_calls_insert_one(mock_users, client):
    """Register must use insert_one (not the deprecated insert)."""
    mock_users.count_documents.return_value = 0
    client.post("/register", json={"username": "bob", "password": "Str0ngPwd"})
    mock_users.insert_one.assert_called_once()


@patch("app.users")
def test_save_calls_update_one(mock_users, client):
    """Save must use update_one (not the deprecated update)."""
    token = make_valid_token(username="alice")
    client.post(
        "/save",
        json={"message": "hi"},
        headers={"Authorization": "Bearer " + token},
    )
    mock_users.update_one.assert_called_once()
    # Verify the new $push operator is used, not $set.
    call_args = mock_users.update_one.call_args
    assert call_args[0][0] == {"Username": "alice"}
    assert "$push" in call_args[0][1]
    assert call_args[0][1]["$push"]["Messages"] == "hi"


# ---------------------------------------------------------------------------
# Rate limiting (issue #29)
# ---------------------------------------------------------------------------


@pytest.fixture
def rate_limited_client():
    """A client with an isolated, in-memory limiter storage per test."""
    app.config["TESTING"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = False
    from app import limiter

    limiter.enabled = True
    limiter.reset()
    with app.test_client() as c:
        yield c
    limiter.reset()


@patch("app.users")
def test_login_rate_limit_returns_429_after_threshold(mock_users, rate_limited_client):
    mock_users.count_documents.return_value = 0
    responses = []
    for _ in range(11):
        rv = rate_limited_client.post("/login", json={"username": "ghost", "password": "x"})
        responses.append(rv.status_code)

    # Requests within the limit still succeed with their normal status codes.
    assert responses[:10] == [401] * 10
    # The 11th request within the window is throttled.
    assert responses[10] == 429


@patch("app.users")
def test_register_rate_limit_returns_429_after_threshold(mock_users, rate_limited_client):
    mock_users.count_documents.return_value = 0
    responses = []
    for i in range(6):
        rv = rate_limited_client.post(
            "/register",
            json={"username": f"user{i}", "password": "Str0ngPwd"},
        )
        responses.append(rv.status_code)

    # Requests within the limit still succeed with their normal status codes.
    assert responses[:5] == [200] * 5
    # The 6th request within the window is throttled.
    assert responses[5] == 429


# ---------------------------------------------------------------------------
# Global error handlers
# ---------------------------------------------------------------------------


def test_404_returns_json_for_nonexistent_route(client):
    rv = client.get("/nonexistent")
    assert rv.status_code == 404
    assert rv.headers["Content-Type"] == "application/json"
    data = rv.get_json()
    assert data["status"] == 404
    assert data["msg"] == "Not found"


def test_405_returns_json_for_wrong_method_on_existing_route(client):
    rv = client.get("/register")
    assert rv.status_code == 405
    assert rv.headers["Content-Type"] == "application/json"
    data = rv.get_json()
    assert data["status"] == 405
    assert data["msg"] == "Method not allowed"


def test_413_returns_json_for_oversized_body(client):
    """A request body exceeding MAX_CONTENT_LENGTH (1 MB) is rejected with 413."""
    token = make_valid_token(username="alice")
    oversized_body = b"x" * (1_048_576 + 1)  # 1 byte over the 1 MB limit
    rv = client.post(
        "/save",
        data=oversized_body,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rv.status_code == 413
    assert rv.headers["Content-Type"] == "application/json"
    data = rv.get_json()
    assert data["status"] == 413
    assert data["msg"] == "Request body too large"

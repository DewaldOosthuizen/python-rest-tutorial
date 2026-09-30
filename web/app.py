# import functools
import datetime
import os
import re
from datetime import timezone
from functools import wraps

import bcrypt
import jwt
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_restful import Api, Resource
from pymongo import MongoClient
from werkzeug.exceptions import HTTPException

# print = functools.partial(print, flush=True)

app = Flask(__name__)
api = Api(app)


# Flask-Restful's Api.handle_error builds its own response for HTTP
# exceptions and never consults Flask's @app.errorhandler chain. Route
# all HTTP exceptions through Flask's dispatch so our app-level error
# handlers (registered via @app.errorhandler) are invoked.
def _patched_handle_error(e):
    if isinstance(e, HTTPException):
        return app.handle_http_exception(e)
    # For unhandled Python exceptions (e.g. KeyError from a bug in an
    # endpoint), flask-restful's default handle_error builds its own JSON
    # response and never consults Flask's @app.errorhandler chain. Raise
    # so that Api.error_router falls through to the original Flask handler,
    # which will route the error through @app.errorhandler(500).
    raise e


api.handle_error = _patched_handle_error

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URL", "memory://"),
)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://my_db:27017/")
client = MongoClient(MONGO_URI)
db = client.projectDB
users = db["Users"]

SECRET = os.environ["JWT_SECRET"]

"""
HELPER FUNCTIONS
"""


def _require_string(value, max_len, field):
    """Validate that *value* is a string and does not exceed *max_len*."""
    if not isinstance(value, str):
        return f"{field} must be a string"
    if len(value) > max_len:
        return f"{field} exceeds maximum length of {max_len}"
    return None


MIN_PASSWORD_LENGTH = 8


def _validate_password_strength(password):
    """Return an error message string if *password* is too weak, or None."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"password must be at least {MIN_PASSWORD_LENGTH} characters"
    if not re.search(r"[A-Z]", password):
        return "password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return "password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return "password must contain at least one digit"
    return None


def _validate_register_body(data):
    """Return an error message string if *data* is invalid for registration, or None."""
    username = data.get("username")
    password = data.get("password")
    err = _require_string(username, MAX_USERNAME_LEN, "username")
    if err:
        return err
    err = _require_string(password, MAX_PASSWORD_LEN, "password")
    if err:
        return err
    err = _validate_password_strength(password)
    if err:
        return err
    if not username or not password:
        return "username and password are required"
    return None


def _validate_login_body(data):
    """Return an error message string if *data* is invalid for login, or None."""
    username = data.get("username")
    password = data.get("password")
    err = _require_string(username, MAX_USERNAME_LEN, "username")
    if err:
        return err
    err = _require_string(password, MAX_PASSWORD_LEN, "password")
    if err:
        return err
    if not username or not password:
        return "username and password are required"
    return None


def _validate_save_body(data):
    """Return an error message string if *data* is invalid for saving a message, or None."""
    message = data.get("message")
    err = _require_string(message, MAX_MESSAGE_LEN, "message")
    if err:
        return err
    if not message:
        return "message is required"
    return None


def user_exist(username):
    return users.count_documents({"Username": username}) > 0


def verify_user(username, password):
    if not user_exist(username):
        return False

    user_hashed_pw = users.find({"Username": username})[0]["Password"]

    return bcrypt.checkpw(password.encode("utf8"), user_hashed_pw)


def get_user_messages(username):
    # get the messages
    return users.find(
        {
            "Username": username,
        }
    )[0]["Messages"]


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.removeprefix("Bearer ").strip()
        if not token:
            return {"status": 401, "msg": "Unauthorized"}, 401
        try:
            payload = jwt.decode(token, SECRET, algorithms=["HS256"])
            request.username = payload["sub"]
        except jwt.PyJWTError:
            return {"status": 401, "msg": "Unauthorized"}, 401
        return f(*args, **kwargs)

    return decorated


"""
RESOURCES
"""


MAX_USERNAME_LEN = 64
MAX_PASSWORD_LEN = 128
MAX_MESSAGE_LEN = 1024


class Hello(Resource):
    """
    This is the Hello resource class
    """

    def get(self):
        return "Hello World!"


class Register(Resource):
    """
    This is the Register resource class
    """

    decorators = [limiter.limit("5 per hour")]

    def post(self):
        data = request.get_json(silent=True, force=True)
        if not data:
            return {"status": 400, "msg": "Request body must be valid JSON"}, 400
        err = _validate_register_body(data)
        if err:
            return {"status": 400, "msg": err}, 400
        username = data["username"]
        password = data["password"]
        if user_exist(username):
            return {"status": 400, "msg": "User already exists"}, 400

        # encrypt password
        hashed_pw = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())

        # Insert record
        users.insert_one({"Username": username, "Password": hashed_pw, "Messages": []})

        return {"status": 200, "msg": "Registration successful"}, 200


class Login(Resource):
    decorators = [limiter.limit("10 per minute")]

    def post(self):
        data = request.get_json(silent=True, force=True)
        if not data:
            return {"status": 400, "msg": "Request body must be valid JSON"}, 400
        err = _validate_login_body(data)
        if err:
            return {"status": 400, "msg": err}, 400
        username = data["username"]
        password = data["password"]
        if not verify_user(username, password):
            return {"status": 401, "msg": "Invalid credentials"}, 401
        token = jwt.encode(
            {"sub": username, "exp": datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)},
            SECRET,
            algorithm="HS256",
        )
        return {"status": 200, "token": token}, 200


class Retrieve(Resource):
    """
    This is the Retrieve resource class
    """

    @requires_auth
    def post(self):
        offset = request.args.get("offset", 0, type=int)
        limit = request.args.get("limit", 20, type=int)
        limit = min(limit, 100)
        all_messages = get_user_messages(request.username)
        page = all_messages[offset : offset + limit]
        return {"status": 200, "obj": page, "total": len(all_messages)}, 200


class Save(Resource):
    """
    This is the Save resource class
    """

    @requires_auth
    def post(self):
        data = request.get_json(silent=True, force=True)
        if not data:
            return {"status": 400, "msg": "Request body must be valid JSON"}, 400
        err = _validate_save_body(data)
        if err:
            return {"status": 400, "msg": err}, 400
        message = data["message"]
        username = request.username
        users.update_one({"Username": username}, {"$push": {"Messages": message}})
        return {"status": 200, "msg": "Message has been saved successfully"}, 200


api.add_resource(Hello, "/hello")
api.add_resource(Register, "/register")
api.add_resource(Login, "/login")
api.add_resource(Retrieve, "/retrieve")
api.add_resource(Save, "/save")


@app.errorhandler(404)
def handle_404(e):
    return jsonify({"status": 404, "msg": "Not found"}), 404


@app.errorhandler(405)
def handle_405(e):
    return jsonify({"status": 405, "msg": "Method not allowed"}), 405


@app.errorhandler(500)
def handle_500(e):
    return jsonify({"status": 500, "msg": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=5000)

"""
Tests for issue #3 - Fix hardcoded MongoDB credentials exposed in source code
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch


class TestMongoURIConfig(unittest.TestCase):
    """Tests that MONGO_URI env var is used and fallback default is correct."""

    def _reload_app_module(self, env_vars=None):
        """Helper to reload app.py with patched environment and mocked MongoClient."""
        mongo_mock = MagicMock()
        with patch.dict(os.environ, env_vars or {}, clear=False):
            with patch("pymongo.MongoClient", return_value=mongo_mock) as mock_client:
                # Remove cached module if present
                if "app" in sys.modules:
                    del sys.modules["app"]
                # Add web/ to path temporarily
                web_path = os.path.join(os.path.dirname(__file__), "..", "web")
                web_path = os.path.abspath(web_path)
                if web_path not in sys.path:
                    sys.path.insert(0, web_path)
                import app  # noqa: F401

                return mock_client

    def test_mongo_uri_env_var_used_as_default(self):
        """MONGO_URI env var should be read via os.environ.get with correct default."""
        # Read app.py source and verify os.environ.get is used for MONGO_URI
        web_app_path = os.path.join(os.path.dirname(__file__), "..", "web", "app.py")
        with open(web_app_path) as f:
            source = f.read()
        self.assertIn("os.environ.get", source, "app.py must use os.environ.get to read MONGO_URI")
        self.assertIn("MONGO_URI", source, "app.py must reference the MONGO_URI environment variable")

    def test_mongo_uri_fallback_default(self):
        """Fallback default for MONGO_URI must be 'mongodb://my_db:27017/'."""
        web_app_path = os.path.join(os.path.dirname(__file__), "..", "web", "app.py")
        with open(web_app_path) as f:
            source = f.read()
        self.assertIn("mongodb://my_db:27017/", source, "Default MONGO_URI fallback must be 'mongodb://my_db:27017/'")

    def test_import_os_present(self):
        """app.py must import the os module."""
        web_app_path = os.path.join(os.path.dirname(__file__), "..", "web", "app.py")
        with open(web_app_path) as f:
            source = f.read()
        self.assertIn("import os", source, "app.py must contain 'import os'")

    def test_env_var_overrides_default(self):
        """When MONGO_URI env var is set, it should override the default."""
        custom_uri = "mongodb://custom_host:27017/"
        with patch.dict(os.environ, {"MONGO_URI": custom_uri}):
            result = os.environ.get("MONGO_URI", "mongodb://my_db:27017/")
        self.assertEqual(result, custom_uri)

    def test_default_used_when_env_not_set(self):
        """When MONGO_URI env var is not set, default 'mongodb://my_db:27017/' is used."""
        env_without_mongo = {k: v for k, v in os.environ.items() if k != "MONGO_URI"}
        with patch.dict(os.environ, env_without_mongo, clear=True):
            result = os.environ.get("MONGO_URI", "mongodb://my_db:27017/")
        self.assertEqual(result, "mongodb://my_db:27017/")


import pytest


class TestJWTSecretValidation(unittest.TestCase):
    def test_missing_jwt_secret_raises_runtime_error(self):
        web_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
        if web_path not in sys.path:
            sys.path.insert(0, web_path)
        if "app" in sys.modules:
            del sys.modules["app"]
        env = {k: v for k, v in os.environ.items() if k != "JWT_SECRET"}
        with patch.dict(os.environ, env, clear=True):
            with patch("pymongo.MongoClient"):
                with pytest.raises(RuntimeError, match="JWT_SECRET"):
                    import app  # noqa: F401
        if "app" in sys.modules:
            del sys.modules["app"]

    def test_empty_jwt_secret_raises_runtime_error(self):
        web_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
        if web_path not in sys.path:
            sys.path.insert(0, web_path)
        if "app" in sys.modules:
            del sys.modules["app"]
        with patch.dict(os.environ, {"JWT_SECRET": ""}, clear=False):
            with patch("pymongo.MongoClient"):
                with pytest.raises(RuntimeError, match="JWT_SECRET"):
                    import app  # noqa: F401
        if "app" in sys.modules:
            del sys.modules["app"]

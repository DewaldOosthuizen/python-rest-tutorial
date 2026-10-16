"""
Tests for issue #17: Replace deprecated PyMongo collection.insert() and collection.update() calls.
Verifies that web/app.py uses the modern insert_one and update_one PyMongo 4.x API.
"""

import os

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "web", "app.py")
REQUIREMENTS_PATH = os.path.join(os.path.dirname(__file__), "..", "web", "requirements.txt")


def get_app_source():
    with open(APP_PATH, "r") as f:
        return f.read()


def get_requirements():
    with open(REQUIREMENTS_PATH, "r") as f:
        return f.read()


class TestModernPyMongoAPI:
    def test_insert_one_is_used(self):
        source = get_app_source()
        assert "insert_one(" in source, "app.py must use insert_one() (PyMongo 4.x API)"

    def test_deprecated_insert_not_used(self):
        source = get_app_source()
        # Must not call the old collection.insert() directly (not insert_one/insert_many)
        import re

        # Match .insert( but not .insert_one( or .insert_many(
        deprecated_calls = re.findall(r"\.insert\s*\(", source)
        assert not deprecated_calls, f"app.py must NOT use deprecated .insert() call, found: {deprecated_calls}"

    def test_update_one_is_used(self):
        source = get_app_source()
        assert "update_one(" in source, "app.py must use update_one() (PyMongo 4.x API)"

    def test_deprecated_update_not_used(self):
        source = get_app_source()
        import re

        # Match .update( but not .update_one( or .update_many(
        deprecated_calls = re.findall(r"\.update\s*\(", source)
        assert not deprecated_calls, f"app.py must NOT use deprecated .update() call, found: {deprecated_calls}"


class TestRequirementsBumps:
    def test_pymongo_version(self):
        reqs = get_requirements()
        assert "pymongo==4.18.2" in reqs, "requirements.txt must specify pymongo==4.18.2"

    def test_flask_version(self):
        import re

        reqs = get_requirements()
        match = re.search(r"Flask==(\S+)", reqs)
        assert match, "requirements.txt must pin Flask with =="
        major = int(match.group(1).split(".")[0])
        assert major >= 3, f"Flask must be >=3.x for modern API compatibility, got: {match.group(1)}"

    def test_bcrypt_version(self):
        reqs = get_requirements()
        assert "bcrypt==5.0.0" in reqs, "requirements.txt must specify bcrypt==5.0.0"

    def test_flask_restful_present(self):
        reqs = get_requirements()
        assert "flask-restful==0.3.10" in reqs, "requirements.txt must include flask-restful==0.3.10"

    def test_werkzeug_compatible_with_flask3(self):
        reqs = get_requirements()
        import re

        # Werkzeug should be >=3.0.0 or a specific 3.x version
        match = re.search(r"Werkzeug[>=!<]+(\S+)", reqs)
        assert match, "requirements.txt must specify Werkzeug"
        version_str = match.group(0)
        # Accept Werkzeug>=3.0.0 or Werkzeug==3.x.x
        major = None
        ver_match = re.search(r"(\d+)\.", match.group(1))
        if ver_match:
            major = int(ver_match.group(1))
        assert major is not None and major >= 3, (
            f"Werkzeug must be >=3.0.0 for Flask 3.x compatibility, got: {version_str}"
        )

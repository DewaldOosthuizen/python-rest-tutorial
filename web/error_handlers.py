"""Dedicated module for Flask error handlers and the flask-restful handle_error patch.

Keeps route resources, data-access helpers, authentication decorators, and error
handling cleanly separated so that adding structured logging, metrics, or a custom
error-response envelope later does not require touching the resource code.
"""

from flask import jsonify
from werkzeug.exceptions import HTTPException


def init_error_handlers(app, api) -> None:
    """Register the application's error handlers and patch flask-restful.

    Call this once after the ``app`` and ``api`` objects are created.
    """

    def _patched_handle_error(e):
        """Replace flask-restful's default Api.handle_error.

        flask-restful builds its own response for HTTP exceptions and never consults
        Flask's @app.errorhandler chain. Route all HTTP exceptions through Flask's
        dispatch so our app-level error handlers (registered via @app.errorhandler)
        are invoked. For unhandled Python exceptions, re-raise so that
        Api.error_router falls through to the original Flask handler, which routes
        the error through @app.errorhandler(500).
        """
        if isinstance(e, HTTPException):
            return app.handle_http_exception(e)
        raise e

    # Patch flask-restful so that HTTP exceptions are routed through Flask's
    # error handler chain rather than flask-restful's own response builder.
    api.handle_error = _patched_handle_error

    @app.errorhandler(404)
    def handle_404(e: HTTPException):
        return jsonify({"status": 404, "msg": "Not found"}), 404

    @app.errorhandler(405)
    def handle_405(e: HTTPException):
        return jsonify({"status": 405, "msg": "Method not allowed"}), 405

    @app.errorhandler(413)
    def handle_413(e: HTTPException):
        return jsonify({"status": 413, "msg": "Request body too large"}), 413

    @app.errorhandler(500)
    def handle_500(e: HTTPException):
        return jsonify({"status": 500, "msg": "Internal server error"}), 500

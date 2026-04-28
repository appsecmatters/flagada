import os
from functools import wraps

import jwt
from flask import jsonify, request


def require_jwt(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header[len("Bearer "):]
        secret = os.environ.get("ADMIN_SECRET")
        if not secret:
            return jsonify({"error": "Server misconfiguration: ADMIN_SECRET not set"}), 500

        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        if payload.get("role") != "admin":
            return jsonify({"error": "Forbidden"}), 403

        return f(*args, **kwargs)
    return decorated

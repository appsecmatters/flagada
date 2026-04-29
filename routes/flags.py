import hashlib
import re
import sqlite3
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from auth import require_jwt
from db import get_db

bp = Blueprint("flags", __name__)

_HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
_VALID_STATUSES = {"NOT_FOUND_YET", "FOUND", "DEPRECATED", "DELETED"}
_VALID_SEVERITIES = {"NA", "EXCEPTIONAL", "CRITICAL", "HIGH", "MEDIUM", "LOW"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _validate_value(value):
    if not isinstance(value, str) or not _HEX64.match(value):
        return "value must be a 64-character hexadecimal string"
    return None


@bp.get("/flags")
@require_jwt
def list_flags():
    rows = get_db().execute("SELECT * FROM flags").fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/flags")
@require_jwt
def create_flag():
    data = request.get_json(silent=True) or {}

    print(data)
    value = data.get("value", "")
    print(value)
    err = _validate_value(value)
    if err:
        return jsonify({"error": err}), 422

    value = hashlib.sha256(value.encode()).hexdigest()

    application_name = data.get("application_name")
    if not application_name:
        return jsonify({"error": "application_name is required"}), 422

    status = data.get("status", "NOT_FOUND_YET")
    if status not in _VALID_STATUSES:
        return jsonify({"error": f"status must be one of {sorted(_VALID_STATUSES)}"}), 422

    description = data.get("description")
    owner = data.get("owner", "NA")
    severity = data.get("severity", "NA")
    if severity not in _VALID_SEVERITIES:
        return jsonify({"error": f"severity must be one of {sorted(_VALID_SEVERITIES)}"}), 422
    ts = _now()

    db = get_db()
    try:
        db.execute(
            "INSERT INTO flags (value, application_name, description, status, owner, severity, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (value, application_name, description, status, owner, severity, ts, ts),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "a flag with this value already exists"}), 409

    row = db.execute("SELECT * FROM flags WHERE value = ?", (value,)).fetchone()
    return jsonify(dict(row)), 201


@bp.get("/flags/<value>")
@require_jwt
def get_flag(value):
    row = get_db().execute("SELECT * FROM flags WHERE value = ?", (value,)).fetchone()
    if row is None:
        return jsonify({"error": "flag not found"}), 404
    return jsonify(dict(row))


@bp.put("/deprecate_flag/<value>")
@require_jwt
def deprecate_flag(value):
    hashed = hashlib.sha256(value.encode()).hexdigest()
    db = get_db()
    row = db.execute("SELECT * FROM flags WHERE value = ?", (hashed,)).fetchone()
    if row is None:
        return jsonify({"error": "flag not found"}), 404

    if row["status"] == "DEPRECATED":
        return jsonify({"error": "Already deprecated"}), 409

    if row["status"] != "NOT_FOUND_YET":
        return jsonify({"error": f"Invalid status: {row['status']}"}), 409

    db.execute(
        "UPDATE flags SET status = 'DEPRECATED', updated_at = ? WHERE value = ?",
        (_now(), hashed),
    )
    db.commit()
    return jsonify(True), 200


@bp.delete("/flags/<value>")
@require_jwt
def delete_flag(value):
    db = get_db()
    row = db.execute("SELECT * FROM flags WHERE value = ?", (value,)).fetchone()
    if row is None:
        return jsonify({"error": "flag not found"}), 404

    db.execute(
        "UPDATE flags SET status = 'DELETED', updated_at = ? WHERE value = ?",
        (_now(), value),
    )
    db.commit()

    row = db.execute("SELECT * FROM flags WHERE value = ?", (value,)).fetchone()
    return jsonify(dict(row))

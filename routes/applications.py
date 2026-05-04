import sqlite3

from flask import Blueprint, jsonify, request

from auth import require_jwt
from db import get_db

bp = Blueprint("applications", __name__)

_VALID_WORKFLOWS = {"GITHUB_OSS_1", "TBD_WORKFLOW1", "TBD_WORKFLOW2"}


@bp.get("/applications")
@require_jwt
def list_applications():
    rows = get_db().execute("SELECT * FROM applications").fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/applications")
@require_jwt
def create_application():
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 422

    url = data.get("url")
    administrator = data.get("administrator")
    workflow_id = data.get("workflow_id", "GITHUB_OSS_1")
    if workflow_id not in _VALID_WORKFLOWS:
        return jsonify({"error": f"workflow_id must be one of {sorted(_VALID_WORKFLOWS)}"}), 422

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO applications (name, url, administrator, workflow_id) VALUES (?, ?, ?, ?)",
            (name, url, administrator, workflow_id),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "an application with this name already exists"}), 409

    row = db.execute("SELECT * FROM applications WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@bp.get("/applications/<int:app_id>")
@require_jwt
def get_application(app_id):
    row = get_db().execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    if row is None:
        return jsonify({"error": "application not found"}), 404
    return jsonify(dict(row))


@bp.put("/applications/<int:app_id>")
@require_jwt
def update_application(app_id):
    db = get_db()
    row = db.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    if row is None:
        return jsonify({"error": "application not found"}), 404

    data = request.get_json(silent=True) or {}
    name = data.get("name", row["name"])
    url = data.get("url", row["url"])
    administrator = data.get("administrator", row["administrator"])
    workflow_id = data.get("workflow_id", row["workflow_id"])
    if workflow_id not in _VALID_WORKFLOWS:
        return jsonify({"error": f"workflow_id must be one of {sorted(_VALID_WORKFLOWS)}"}), 422

    db.execute(
        "UPDATE applications SET name = ?, url = ?, administrator = ?, workflow_id = ? WHERE id = ?",
        (name, url, administrator, workflow_id, app_id),
    )
    db.commit()

    row = db.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    return jsonify(dict(row))


@bp.delete("/applications/<int:app_id>")
@require_jwt
def delete_application(app_id):
    db = get_db()
    row = db.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    if row is None:
        return jsonify({"error": "application not found"}), 404

    db.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    db.commit()
    return jsonify({"deleted": True})

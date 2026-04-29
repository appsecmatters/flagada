import hashlib
import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from db import get_db
from github_helper import create_repository, github_user_exists, invite_collaborator
from routes.flags import _validate_value

bp = Blueprint("validate", __name__)


@bp.post("/validateFlag")
def validate_flag():
    data = request.get_json(silent=True) or {}

    value = data.get("value", "")
    if _validate_value(value):
        return jsonify({"found": False}), 200

    owner = data.get("owner")
    if not owner:
        return jsonify({"error": "owner is required"}), 422

    hashed = hashlib.sha256(value.encode()).hexdigest()
    db = get_db()
    row = db.execute("SELECT * FROM flags WHERE value = ?", (hashed,)).fetchone()
    if row is None:
        return jsonify({"found": False}), 200

    status = row["status"]

    if status == "DELETED":
        return jsonify({"found": False}), 200

    if status == "DEPRECATED":
        return jsonify({"message": "Flag is outdated. Please try capturing its latest version"}), 200

    if status == "FOUND":
        if row["owner"] == owner:
            return jsonify({"message": "You already submitted this flag"}), 200
        return jsonify({"message": f"Someone else already submitted this flag on {row['updated_at']}"}), 200

    if status != "NOT_FOUND_YET":
        logging.error("Unexpected error: status is %s", status)
        return jsonify({"found": False}), 200

    if not github_user_exists(userid=owner):
        return jsonify({"message": f"GitHub user {owner} does not exist"}), 422
    if not create_repository(flag=value):
        return jsonify({"message": f"GitHub repository could not be created for flag {value}"}), 500
    
    invited = invite_collaborator(username=owner, flag=value)
    if not invited:
        return jsonify({"message": f"GitHub invite could not be sent to user {owner}"}), 500

    db.execute(
        "UPDATE flags SET status = 'FOUND', owner = ?, updated_at = ? WHERE value = ?",
        (owner, datetime.now(timezone.utc).isoformat(), hashed),
    )
    db.commit()
    return jsonify({"found": True, "message": "You have been invited to a dedicated GitHub repository to provide the details on how you found this flag"}), 200

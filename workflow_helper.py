import hashlib
import logging

from db import get_db
from github_helper import create_repository, github_user_exists, invite_collaborator


def execute_workflow(flag, userid):
    hashed = hashlib.sha256(flag.encode()).hexdigest()
    db = get_db()

    flag_row = db.execute(
        "SELECT application_id FROM flags WHERE value = ?", (hashed,)
    ).fetchone()
    if flag_row is None:
        logging.error("execute_workflow: flag not found for hash %s", hashed)
        return "Flag not found", 404

    app_row = db.execute(
        "SELECT workflow_id FROM applications WHERE id = ?", (flag_row["application_id"],)
    ).fetchone()
    if app_row is None:
        logging.error("execute_workflow: application not found for id %s", flag_row["application_id"])
        return "Application not found", 404

    workflow_id = app_row["workflow_id"]

    if workflow_id == "GITHUB_OSS_1":
        return _run_github_oss_1(flag, userid)

    if workflow_id == "TBD_WORKFLOW1":
        logging.warning("execute_workflow: workflow %s is not implemented yet", workflow_id)
        return f"Workflow {workflow_id} not implemented yet", 501

    if workflow_id == "TBD_WORKFLOW2":
        logging.warning("execute_workflow: workflow %s is not implemented yet", workflow_id)
        return f"Workflow {workflow_id} not implemented yet", 501

    logging.error("execute_workflow: unknown workflow_id %s", workflow_id)
    return "Unknown workflow", 500


def _run_github_oss_1(flag, userid):
    if not github_user_exists(userid=userid):
        return f"GitHub user {userid} does not exist", 422
    if not create_repository(flag=flag):
        return f"GitHub repository could not be created for flag {flag}", 500
    if not invite_collaborator(username=userid, flag=flag):
        return f"GitHub invite could not be sent to user {userid}", 500
    return None

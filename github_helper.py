import hashlib
import json
import logging
import os
import ssl
import urllib.error
import urllib.request

import certifi

from db import get_db


def _flag_repo_name(flag):
    hashed = hashlib.sha256(flag.encode()).hexdigest()
    db = get_db()
    flag_row = db.execute("SELECT application_id FROM flags WHERE value = ?", (hashed,)).fetchone()
    if flag_row is None:
        logging.error("_flag_repo_name: flag not found for hash %s", hashed)
        return None
    app_row = db.execute("SELECT name FROM applications WHERE id = ?", (flag_row["application_id"],)).fetchone()
    if app_row is None:
        logging.error("_flag_repo_name: application not found for id %s", flag_row["application_id"])
        return None
    return f"{app_row['name']}_{flag}"


def _make_request(url, method, payload=None):
    token = os.environ.get("GITHUB_TOKEN")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    return urllib.request.urlopen(req, context=ssl_context)


def github_user_exists(userid):
    url = f"https://api.github.com/users/{userid}"
    try:
        with _make_request(url, "GET") as response:
            return response.status == 200
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        logging.error("GitHub user lookup failed for %s: HTTP %s - %s", userid, e.code, e.read().decode())
        return False
    except urllib.error.URLError as e:
        logging.error("GitHub user lookup failed for %s: %s", userid, e.reason)
        return False


def invite_collaborator(username, flag, permission="push"):
    repo_owner = os.environ.get("GITHUB_OWNER")
    repo_name = _flag_repo_name(flag)

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/collaborators/{username}"
    try:
        with _make_request(url, "PUT", {"permission": permission}) as response:
            if response.status == 201:
                logging.info("Invitation sent to %s.", username)
            elif response.status == 204:
                logging.info("%s is already a collaborator.", username)
        return True
    except urllib.error.HTTPError as e:
        logging.error("GitHub invite failed for %s: HTTP %s - %s", username, e.code, e.read().decode())
        return False
    except urllib.error.URLError as e:
        logging.error("GitHub invite failed for %s: %s", username, e.reason)
        return False


def create_repository(flag):
    url = f"https://api.github.com/user/repos" #current user PAT, different with an org
    default_settings = {"private": True, "auto_init": True,"has_issues":True, "has_projects":False, "has_wiki":False,"has_downloads":False}
    description = f"Details on how to find the flag {flag}"
    payload = {"name": _flag_repo_name(flag), "description": description, **default_settings}

    try:
        with _make_request(url, "POST", payload) as response:
            body = json.loads(response.read().decode())
            logging.info("Repository created: %s", body.get("full_name"))
            return True
    except urllib.error.HTTPError as e:
        logging.error("GitHub repo creation failed for %s: HTTP %s - %s", flag, e.code, e.read().decode())
        return False
    except urllib.error.URLError as e:
        logging.error("GitHub repo creation failed for %s: %s", flag, e.reason)
        return False

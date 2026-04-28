import json
import logging
import os
import ssl
import urllib.error
import urllib.request

import certifi


def invite_collaborator(username, permission="push"):
    repo_owner = os.environ.get("GITHUB_OWNER")
    repo_name = os.environ.get("GITHUB_REPO")
    token = os.environ.get("GITHUB_TOKEN")

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/collaborators/{username}"
    payload = json.dumps({"permission": permission}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            status = response.status
            if status == 201:
                logging.info("Invitation sent to %s.", username)
            elif status == 204:
                logging.info("%s is already a collaborator.", username)
        return True
    except urllib.error.HTTPError as e:
        logging.error("GitHub invite failed for %s: HTTP %s - %s", username, e.code, e.read().decode())
        return False
    except urllib.error.URLError as e:
        logging.error("GitHub invite failed for %s: %s", username, e.reason)
        return False

# Flagada

A lightweight Python tool to manage (via API) proof of exploits for bug bounty programs.

Why/when should I use it? Get the context of [what really matters](https://appsecmatters.com/proof_of_exploit.html)

## Configuration

Prerequisites for this Flask app:
* Python3
* pip package installer
* Install dependencies with `pip install -r requirements.txt`

Environment variables:
* ADMIN_SECRET: HS256 secret used to authenticate the bug bounty admin endpoints
* GITHUB_OWNER: GitHub userid of the bug bounty admin (a personal account as organizations are not managed yet, cf create_repository method in github_helper.py)
* GITHUB_TOKEN: PAT token from this GITHUB_OWNER with access to all repositories and those fine grained permissions: Administraion Read and write, Contents Read only, Metadata Read only

Database:
Sqlite database automatically created in `flagada.db`

## Starting

Launch with command `python3 app.py`

## Documentation

Proposed workflow for public GitHub repository is described in github_oss1.md. 
Flagada API generated docs are available in the docs folder.

### Threat model

Flagada, as a 3rd party tool, should not know the flag values: the bug bounty admin and the security researcher provide a SHA256 of it.  
This is considered good enough as anyhow the values should not be too easily predictable, otherwise the researcher would just bruteforce them.

The flag hashes are also hashed another time before being stored in database to protect from anyone having access to the Sqlite DB file.

The admin endpoints are protected by a JWT signed with a HS256 secret and containing a "role":"admin" claim.  
For defense in depth, it is recommended to only make the `/validate_flag` endpoint publicly available to the researchers.

## Extension

1. In routes/applications.py, update `_VALID_WORKFLOWS` enum (e.g. replace TBD_WORKFLOW1)
2. In workflow_helper.py, update execute_workflow with the code required (getting inspiration from method _run_github_oss_1)

# Open Source proposed workflow 1

Goal: Avoid GitHub Security Advisories because
* it is only on/off: no way to filter a huge volume of reports without significant impact
* the create temporary fork feature does not scale well
* the permission model for managing those advisories is cumbersome

The proposed workaround
* Guarantees that the researcher can only see his own finding: a specific repo is created on the fly where he is invited
* Uses the battle tested Issue feature of GitHub (markdown available, no need to worry about malicious attachments)
* Uses the GitHub account of the researcher as identifier (rather than obscure email addresses)

Identified drawbacks
* Management overhead of 1 repo per finding (but this should be manageable if not too many flags are found in parallel)
* Not directly possible to work on the fix in this repo (cloning would be slow and consume storage). But anyhow a unique security mirror is the best practice for releasing security patches..

## Sequence diagram

```mermaid
sequenceDiagram
    actor Researcher as Security Researcher
    participant GitHub2 as GitHub Private Repo for Flag details
    participant Flagada
    participant DB as Flagada Sqlite DB
    participant App as Deployed App with Flags
    actor Admin as Bug Bounty Admin
    participant GitHub as GitHub OSS Repo

    Admin->>App: Include Flags in App container
    Admin->>App: Deploy App container
    Admin->>Flagada: Create app (POST /applications with workflow type)
    Admin->>Flagada: Import Flag hashes for this app (POST /flags)
    Flagada->>DB: Persist double hashes of flags
    Admin->>GitHub: Update security policy with how to submit flag hashes
    Admin-->>GitHub: Optional: description of flags, naming convention, severity and payouts
    
    Researcher->>GitHub: Read security policy
    Researcher->>App: Look for flags

    Researcher->>Flagada: Submit flag hash (POST /validateFlag) and GitHub userid
    Flagada->>DB: Lookup hash(flag hash)
    Flagada->>Flagada: Trigger workflow of corresponding app

    Flagada->>GitHub2: Create dedicated private repo
    Flagada->>GitHub2: Invite researcher with GitHub userid
    GitHub2->>Researcher: Invitation
    Flagada->>DB: Flag state = FOUND
    GitHub2-->>Admin: Optional: GitHub webhook flag discovered

    Admin->>App: Rotate flag
    Admin->>Flagada: Import New flag hash

    Researcher->>GitHub2: Accept invite

    Researcher->>GitHub2: Create issue with details on how the flag was found
    GitHub2-->>Admin: Optional: GitHub webhook report available

    Admin->>GitHub2: Read report
    Admin->>Researcher: Confirm report
```

NB: The detailed documentation of the Flagadi API can be found in the docs folder

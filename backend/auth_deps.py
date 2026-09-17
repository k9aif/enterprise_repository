import os
from fastapi import Header, HTTPException

# MVP write-gate: a single shared key, not per-user auth. Reading (search,
# browse, article pages) is intentionally public — the "Wikipedia facade"
# means discovery has no login wall. Writes (publishing an artifact,
# registering a standard, granting a dispensation) need a key.
#
# TODO: replace with k9x_continuum's existing JWT/user system once this
# service needs per-user attribution beyond the free-text `captured_by`/
# `approver` fields it accepts today.

_API_KEY = os.getenv("REPO_API_KEY", "")


def require_api_key(x_api_key: str = Header(default="")):
    if not _API_KEY:
        raise HTTPException(500, "REPO_API_KEY is not configured on the server")
    if x_api_key != _API_KEY:
        raise HTTPException(401, "Missing or invalid X-API-Key header")

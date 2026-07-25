"""Lightweight authentication/authorization dependencies.

spec.md Section 4.4 (Security & Safety): only the individual and their
explicitly-linked caregiver(s) can access a given Recovery Profile, Safety
Plan, or crisis history. Identity is passed via an X-User-Id header
(hackathon-scope stand-in for verified JWT/Firebase Auth claims).
"""
from fastapi import Header, HTTPException

from app.config import get_settings

settings = get_settings()


def get_current_user_id(x_user_id: str | None = Header(default=None)) -> str | None:
    return x_user_id


def require_profile_access(profile: dict, requester_id: str | None, db) -> None:
    """Raise 403 unless requester is the profile owner or a linked caregiver."""
    if requester_id is None:
        if settings.require_auth:
            raise HTTPException(status_code=401, detail="X-User-Id header is required")
        return

    if requester_id == profile["user_id"]:
        return

    owner = db.collection("users").get(profile["user_id"])
    if owner and requester_id in owner.get("linked_user_ids", []):
        return

    raise HTTPException(status_code=403, detail="Not authorized to access this recovery profile")

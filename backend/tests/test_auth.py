"""Unit tests for profile access control (spec.md Section 4.4 Security)."""
import pytest
from fastapi import HTTPException
from app.auth import require_profile_access
from app.services.firestore_client import get_firestore_client


class TestRequireProfileAccess:
    def test_no_user_id_allowed_by_default(self):
        require_profile_access({"user_id": "user-1"}, None, get_firestore_client())

    def test_owner_is_granted_access(self):
        db = get_firestore_client()
        db.collection("users").set("user-1", {"id": "user-1", "linked_user_ids": []})
        require_profile_access({"user_id": "user-1"}, "user-1", db)

    def test_linked_caregiver_is_granted_access(self):
        db = get_firestore_client()
        db.collection("users").set("user-1", {"id": "user-1", "linked_user_ids": ["user-2"]})
        require_profile_access({"user_id": "user-1"}, "user-2", db)

    def test_unrelated_user_is_denied_access(self):
        db = get_firestore_client()
        db.collection("users").set("user-1", {"id": "user-1", "linked_user_ids": []})
        with pytest.raises(HTTPException) as exc:
            require_profile_access({"user_id": "user-1"}, "stranger", db)
        assert exc.value.status_code == 403

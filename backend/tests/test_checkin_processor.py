"""Unit tests for craving/mood check-in processing (spec.md Section 3.3)."""
from app.services.checkin_processor import process_checkin
from app.services.firestore_client import get_firestore_client


class TestProcessCheckin:
    def test_craving_checkin_suggests_technique_from_profile(self):
        db = get_firestore_client()
        db.collection("profiles").set("profile-1", {
            "id": "profile-1", "user_id": "user-1", "triggers": [],
            "coping_strategies": ["deep breathing"], "support_contacts": [],
            "sobriety_start_date": None, "notes": None,
        })

        checkin = process_checkin("user-1", "craving", 8)

        assert checkin.suggested_technique == "deep breathing"

    def test_mood_checkin_has_no_suggested_technique(self):
        checkin = process_checkin("user-1", "mood", 5)
        assert checkin.suggested_technique is None

    def test_craving_checkin_without_profile_uses_generic_fallback(self):
        checkin = process_checkin("user-unknown", "craving", 9)
        assert "generic-grounding" in checkin.suggested_technique

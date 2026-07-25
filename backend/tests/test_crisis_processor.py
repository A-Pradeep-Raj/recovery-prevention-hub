"""Unit tests for crisis trigger orchestration (spec.md Section 3.1, 3.4)."""
from app.services.crisis_processor import trigger_crisis
from app.services.firestore_client import get_firestore_client


def _seed_profile(user_id="user-1", coping=None):
    db = get_firestore_client()
    db.collection("profiles").set("profile-1", {
        "id": "profile-1", "user_id": user_id,
        "triggers": ["stress"], "coping_strategies": coping or ["call sponsor"],
        "support_contacts": ["Sam"], "sobriety_start_date": None, "notes": None,
    })


class TestTriggerCrisis:
    def test_generates_script_and_no_alert_without_caregiver(self):
        db = get_firestore_client()
        db.collection("users").set("user-1", {
            "id": "user-1", "name": "Jordan", "email": "j@example.com",
            "role": "individual", "preferred_language": "en", "linked_user_ids": [],
        })
        _seed_profile()

        result = trigger_crisis("user-1", "tap")

        assert result["event"].generated_script
        assert result["caregiver_alert"] is None

    def test_generates_alert_when_caregiver_linked(self):
        db = get_firestore_client()
        db.collection("users").set("user-1", {
            "id": "user-1", "name": "Jordan", "email": "j@example.com",
            "role": "individual", "preferred_language": "en", "linked_user_ids": ["user-2"],
        })
        db.collection("users").set("user-2", {
            "id": "user-2", "name": "Sam", "email": "sam@example.com",
            "role": "caregiver", "preferred_language": "en", "linked_user_ids": [],
        })
        _seed_profile()

        result = trigger_crisis("user-1", "voice", shared_context="felt a strong craving")

        assert result["caregiver_alert"] is not None
        assert result["event"].caregiver_alert_id == result["caregiver_alert"].id

    def test_missing_profile_still_produces_generic_script(self):
        db = get_firestore_client()
        db.collection("users").set("user-1", {
            "id": "user-1", "name": "Jordan", "email": "j@example.com",
            "role": "individual", "preferred_language": "en", "linked_user_ids": [],
        })

        result = trigger_crisis("user-1", "tap")

        assert len(result["event"].generated_script) > 0
        assert result["event"].grounded_fields == []

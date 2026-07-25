"""Integration test: end-to-end flow from profile creation through crisis
trigger to caregiver alert (spec.md Section 4.5 — Integration test requirement).
"""
import os

os.environ["SKIP_SEED_ON_STARTUP"] = "1"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services.firestore_client import get_firestore_client  # noqa: E402

client = TestClient(app)


def _reset_store():
    db = get_firestore_client()
    for name in ["users", "profiles", "crisis_events", "caregiver_alerts", "checkins"]:
        db.collection(name).delete_all()


class TestEndToEndCrisisFlow:
    def setup_method(self):
        _reset_store()
        db = get_firestore_client()
        db.collection("users").set("user-1", {
            "id": "user-1", "name": "Jordan", "email": "jordan@example.com",
            "role": "individual", "preferred_language": "en", "linked_user_ids": ["user-2"],
        })
        db.collection("users").set("user-2", {
            "id": "user-2", "name": "Sam", "email": "sam@example.com",
            "role": "caregiver", "preferred_language": "en", "linked_user_ids": [],
        })

    def test_create_profile_via_api(self):
        response = client.post("/api/profiles", json={
            "user_id": "user-1", "triggers": ["stress"], "coping_strategies": ["deep breathing"],
            "support_contacts": ["Sam"],
        })
        assert response.status_code == 200
        assert response.json()["user_id"] == "user-1"

    def test_trigger_crisis_generates_script_and_alert(self):
        client.post("/api/profiles", json={
            "user_id": "user-1", "triggers": ["stress"], "coping_strategies": ["deep breathing"],
            "support_contacts": ["Sam"],
        })
        response = client.post("/api/crisis/trigger", json={"user_id": "user-1", "trigger_method": "tap"})
        assert response.status_code == 200
        body = response.json()
        assert len(body["event"]["generated_script"]) > 0
        assert body["caregiver_alert"] is not None

    def test_checkin_flow(self):
        client.post("/api/profiles", json={
            "user_id": "user-1", "triggers": [], "coping_strategies": ["call Sam"], "support_contacts": [],
        })
        response = client.post("/api/checkins", json={"user_id": "user-1", "type": "craving", "intensity": 7})
        assert response.status_code == 200
        assert response.json()["suggested_technique"] == "call Sam"

    def test_copilot_ask_requires_profile(self):
        response = client.post("/api/copilot/ask", json={
            "user_id": "no-such-user", "question": "What are my triggers?", "language": "en",
        })
        assert response.status_code == 404

    def test_copilot_ask_grounded_answer(self):
        client.post("/api/profiles", json={
            "user_id": "user-1", "triggers": ["stress"], "coping_strategies": ["deep breathing"],
            "support_contacts": ["Sam"],
        })
        response = client.post("/api/copilot/ask", json={
            "user_id": "user-1", "question": "What are my triggers?", "language": "en",
        })
        assert response.status_code == 200
        assert "answer" in response.json()

    def test_health_endpoint(self):
        assert client.get("/health").json() == {"status": "ok"}

    def test_invalid_trigger_method_rejected(self):
        response = client.post("/api/crisis/trigger", json={"user_id": "user-1", "trigger_method": "typing"})
        assert response.status_code == 422

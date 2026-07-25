import pytest
from app.services.firestore_client import get_firestore_client


@pytest.fixture(autouse=True)
def reset_store():
    db = get_firestore_client()
    for name in ["users", "profiles", "crisis_events", "caregiver_alerts", "checkins"]:
        db.collection(name).delete_all()
    yield


@pytest.fixture
def seed_users():
    db = get_firestore_client()
    users = [
        {"id": "user-1", "name": "Jordan Lee", "email": "jordan@example.com",
         "role": "individual", "preferred_language": "en", "linked_user_ids": ["user-2"]},
        {"id": "user-2", "name": "Sam Lee", "email": "sam@example.com",
         "role": "caregiver", "preferred_language": "en", "linked_user_ids": []},
    ]
    for u in users:
        db.collection("users").set(u["id"], u)
    return users

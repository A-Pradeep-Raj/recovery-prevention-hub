"""Craving/mood/sleep/stress check-in processing. spec.md Section 3.3."""
from datetime import datetime, timezone
import uuid
from app.models import CheckIn
from app.services.ai_services import suggest_coping_technique
from app.services.firestore_client import get_firestore_client


def process_checkin(user_id: str, checkin_type: str, intensity: int) -> CheckIn:
    db = get_firestore_client()
    profile = None
    for p in db.collection("profiles").list():
        if p.get("user_id") == user_id:
            profile = p
            break

    suggested = None
    if checkin_type == "craving":
        coping_strategies = profile.get("coping_strategies", []) if profile else []
        suggested = suggest_coping_technique(intensity, coping_strategies)

    checkin = CheckIn(
        id=str(uuid.uuid4()), user_id=user_id, type=checkin_type, intensity=intensity,
        suggested_technique=suggested, created_at=datetime.now(timezone.utc),
    )
    db.collection("checkins").set(checkin.id, checkin.model_dump(mode="json"))
    return checkin

"""Core crisis-mode orchestration: zero-typing trigger -> grounded emergency
script -> caregiver alert. spec.md Section 3.1, 3.2, 3.4.
"""
from datetime import datetime, timezone
import uuid
from app.models import CrisisEvent, CrisisStatus
from app.services.ai_services import generate_emergency_script
from app.services.firestore_client import get_firestore_client
from app.services.notification_service import send_caregiver_alert


def trigger_crisis(user_id: str, trigger_method: str = "tap", shared_context: str | None = None) -> dict:
    db = get_firestore_client()
    profile = _get_profile_for_user(db, user_id)
    individual = db.collection("users").get(user_id)
    individual_language = (individual or {}).get("preferred_language", "en")

    result = generate_emergency_script(profile or {}, individual_language)

    event = CrisisEvent(
        id=str(uuid.uuid4()), user_id=user_id, triggered_at=datetime.now(timezone.utc),
        trigger_method=trigger_method, generated_script=result["script"],
        grounded_fields=result["grounded_fields"], status=CrisisStatus.OPEN,
    )

    user = individual
    caregiver_alert = None
    if user and user.get("linked_user_ids"):
        caregiver_id = user["linked_user_ids"][0]
        caregiver = db.collection("users").get(caregiver_id)
        if caregiver:
            context_summary = (
                f"{user.get('name', 'Your loved one')} just triggered Crisis Mode"
                + (f" ({shared_context})" if shared_context else "")
                + f". They received this grounding script: \"{result['script'][:160]}...\""
            )
            suggested_action = (
                "Reach out now with a supportive call or text — they may need someone to talk to."
                if result["grounded_fields"] else
                "Check in when you can — a generic grounding script was shown (limited profile data)."
            )
            caregiver_alert = send_caregiver_alert(
                event.id, caregiver_id, caregiver["email"], caregiver["name"],
                context_summary, suggested_action, caregiver.get("preferred_language", "en"),
            )
            event.caregiver_alert_id = caregiver_alert.id

    db.collection("crisis_events").set(event.id, event.model_dump(mode="json"))
    return {"event": event, "caregiver_alert": caregiver_alert}


def _get_profile_for_user(db, user_id: str) -> dict | None:
    for p in db.collection("profiles").list():
        if p.get("user_id") == user_id:
            return p
    return None

from fastapi import APIRouter, HTTPException
from app.models import AskCoPilotRequest
from app.services.ai_services import ask_copilot
from app.services.firestore_client import get_firestore_client

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

_KNOWLEDGE_BASE = (
    "Recovery is not linear; relapse is a common part of many recovery journeys and does not mean failure. "
    "Grounding techniques like the 5-4-3-2-1 senses exercise and slow breathing can help reduce craving intensity. "
    "Caregivers supporting a loved one in recovery benefit from setting boundaries while staying connected, "
    "and should encourage professional help rather than trying to manage a crisis alone. "
    "If someone is in immediate physical danger, contact local emergency services immediately."
)


@router.post("/ask")
def ask(payload: AskCoPilotRequest):
    """Recovery Co-Pilot Q&A (spec.md Section 3.5): grounded strictly in the
    user's own Recovery Profile plus a curated knowledge base. Refuses to
    answer ungrounded/unsafe questions (spec.md Section 4.9)."""
    db = get_firestore_client()
    profile = None
    for p in db.collection("profiles").list():
        if p.get("user_id") == payload.user_id:
            profile = p
            break

    if not profile:
        raise HTTPException(404, "No recovery profile found for this user")

    context = (
        f"Triggers: {', '.join(profile.get('triggers', [])) or 'none logged'}. "
        f"Coping strategies: {', '.join(profile.get('coping_strategies', [])) or 'none logged'}. "
        f"Support contacts: {', '.join(profile.get('support_contacts', [])) or 'none logged'}. "
        f"Notes: {profile.get('notes') or 'none'}. "
        f"Knowledge base: {_KNOWLEDGE_BASE}"
    )
    return ask_copilot(payload.question, context, payload.language)

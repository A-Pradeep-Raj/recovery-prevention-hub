"""Caregiver alert delivery. spec.md Section 3.4 — real-time, context-rich
alerts with a suggested next action, localized via Cloud Translation.
"""
from datetime import datetime, timezone
import uuid
from app.models import CaregiverAlert
from app.services.firestore_client import get_firestore_client
from app.services.ai_services import translate_text


def send_caregiver_alert(crisis_event_id: str, caregiver_id: str, caregiver_email: str,
                          caregiver_name: str, context_summary: str, suggested_action: str,
                          language: str = "en") -> CaregiverAlert:
    # Translate BOTH the email body AND the record fields the Caregiver
    # Dashboard actually displays (spec.md Section 3.7 — multi-language
    # access). Previously only the email body was translated while the
    # stored context_summary/suggested_action stayed in English, so the
    # dashboard never showed the caregiver's preferred language.
    display_context_summary = context_summary
    display_suggested_action = suggested_action
    if language != "en":
        display_context_summary = translate_text(context_summary, language, "en")
        display_suggested_action = translate_text(suggested_action, language, "en")

    subject = "Crisis Alert: Your loved one may need support"
    body = (
        f"Hi {caregiver_name},\n\n"
        f"{display_context_summary}\n\n"
        f"Suggested next action: {display_suggested_action}\n"
    )
    if language != "en":
        subject = translate_text(subject, language, "en")

    print(f"[CAREGIVER ALERT] To: {caregiver_email}\nSubject: {subject}\n\n{body}\n")

    alert = CaregiverAlert(
        id=str(uuid.uuid4()), crisis_event_id=crisis_event_id, caregiver_id=caregiver_id,
        context_summary=display_context_summary, suggested_action=display_suggested_action,
        sent_at=datetime.now(timezone.utc), language_used=language,
    )
    get_firestore_client().collection("caregiver_alerts").set(alert.id, alert.model_dump(mode="json"))
    return alert

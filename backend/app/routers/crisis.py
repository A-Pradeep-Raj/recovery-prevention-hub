from fastapi import APIRouter
from app.models import TriggerCrisisRequest
from app.services.crisis_processor import trigger_crisis
from app.services.firestore_client import get_firestore_client

router = APIRouter(prefix="/api/crisis", tags=["crisis"])


@router.post("/trigger")
def trigger(payload: TriggerCrisisRequest):
    """Zero-typing crisis trigger (spec.md Section 3.1): generates a
    personalized, grounded emergency script live and alerts a linked
    caregiver if one exists."""
    result = trigger_crisis(payload.user_id, payload.trigger_method, payload.shared_context)
    return {
        "event": result["event"].model_dump(mode="json"),
        "caregiver_alert": result["caregiver_alert"].model_dump(mode="json") if result["caregiver_alert"] else None,
    }


@router.get("")
def list_events():
    return get_firestore_client().collection("crisis_events").list()


@router.get("/alerts")
def list_alerts():
    return get_firestore_client().collection("caregiver_alerts").list()


@router.patch("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str):
    from datetime import datetime, timezone

    db = get_firestore_client()
    alert = db.collection("caregiver_alerts").get(alert_id)
    if alert:
        alert["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
        db.collection("caregiver_alerts").set(alert_id, alert)
    return alert

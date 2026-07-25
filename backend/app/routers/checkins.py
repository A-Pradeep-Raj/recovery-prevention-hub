from fastapi import APIRouter
from app.models import CheckInRequest
from app.services.checkin_processor import process_checkin
from app.services.firestore_client import get_firestore_client

router = APIRouter(prefix="/api/checkins", tags=["checkins"])


@router.post("")
def create_checkin(payload: CheckInRequest):
    checkin = process_checkin(payload.user_id, payload.type.value, payload.intensity)
    return checkin


@router.get("")
def list_checkins():
    return get_firestore_client().collection("checkins").list()

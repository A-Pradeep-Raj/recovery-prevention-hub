import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user_id, require_profile_access
from app.models import CreateProfileRequest, RecoveryProfile
from app.services.firestore_client import get_firestore_client

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.post("")
def create_profile(payload: CreateProfileRequest):
    profile = RecoveryProfile(
        id=str(uuid.uuid4()), user_id=payload.user_id, triggers=payload.triggers,
        coping_strategies=payload.coping_strategies, support_contacts=payload.support_contacts,
        sobriety_start_date=payload.sobriety_start_date, notes=payload.notes,
    )
    get_firestore_client().collection("profiles").set(profile.id, profile.model_dump(mode="json"))
    return profile


@router.get("/{profile_id}")
def get_profile(profile_id: str, user_id: str | None = Depends(get_current_user_id)):
    db = get_firestore_client()
    p = db.collection("profiles").get(profile_id)
    if not p:
        raise HTTPException(404, "Profile not found")
    require_profile_access(p, user_id, db)
    return p


@router.get("/by-user/{owner_user_id}")
def get_profile_by_user(owner_user_id: str, user_id: str | None = Depends(get_current_user_id)):
    db = get_firestore_client()
    for p in db.collection("profiles").list():
        if p.get("user_id") == owner_user_id:
            require_profile_access(p, user_id, db)
            return p
    raise HTTPException(404, "Profile not found")

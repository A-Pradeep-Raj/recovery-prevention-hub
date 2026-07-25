from fastapi import APIRouter
from app.services.firestore_client import get_firestore_client

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
def list_users():
    return get_firestore_client().collection("users").list()

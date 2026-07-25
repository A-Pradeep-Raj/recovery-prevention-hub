from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class UserRole(str, Enum):
    INDIVIDUAL = "individual"
    CAREGIVER = "caregiver"


class CrisisStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"


class CheckInType(str, Enum):
    CRAVING = "craving"
    MOOD = "mood"
    SLEEP = "sleep"
    STRESS = "stress"


class User(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole = UserRole.INDIVIDUAL
    preferred_language: str = "en"
    linked_user_ids: list[str] = Field(default_factory=list)


class RecoveryProfile(BaseModel):
    id: str
    user_id: str
    triggers: list[str] = Field(default_factory=list)
    coping_strategies: list[str] = Field(default_factory=list)
    support_contacts: list[str] = Field(default_factory=list)
    sobriety_start_date: Optional[str] = None
    notes: Optional[str] = None


class CrisisEvent(BaseModel):
    id: str
    user_id: str
    triggered_at: datetime
    trigger_method: str = "tap"  # tap | voice
    generated_script: str
    grounded_fields: list[str] = Field(default_factory=list)
    caregiver_alert_id: Optional[str] = None
    status: CrisisStatus = CrisisStatus.OPEN


class CaregiverAlert(BaseModel):
    id: str
    crisis_event_id: str
    caregiver_id: str
    context_summary: str
    suggested_action: str
    sent_at: datetime
    acknowledged_at: Optional[datetime] = None
    language_used: str = "en"


class CheckIn(BaseModel):
    id: str
    user_id: str
    type: CheckInType
    intensity: int = Field(ge=1, le=10)
    suggested_technique: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Request models (spec.md Section 4.4 Security — input sanitization).
# ---------------------------------------------------------------------------

class CreateProfileRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    triggers: list[str] = Field(default_factory=list, max_length=30)
    coping_strategies: list[str] = Field(default_factory=list, max_length=30)
    support_contacts: list[str] = Field(default_factory=list, max_length=10)
    sobriety_start_date: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=2000)


class TriggerCrisisRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    trigger_method: str = Field(default="tap", max_length=20)
    shared_context: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("trigger_method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        if v not in ("tap", "voice"):
            raise ValueError("trigger_method must be 'tap' or 'voice'")
        return v


class CheckInRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    type: CheckInType
    intensity: int = Field(ge=1, le=10)


class AskCoPilotRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=1, max_length=1000)
    language: str = Field(default="en", max_length=10)


class AcknowledgeAlertRequest(BaseModel):
    acknowledged: bool = True

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    gcp_project_id: str = "demo-project"
    gcp_region: str = "us-central1"
    use_mock_ai: bool = True
    # Vertex AI Gemini (spec.md Section 4.8 — Generative AI Usage, Mandatory).
    # No API key needed: auth is via Application Default Credentials (the
    # Cloud Run service account's roles/aiplatform.user grant in production,
    # or `gcloud auth application-default login` locally).
    sendgrid_api_key: str | None = None
    sendgrid_from_email: str = "noreply@recoveryhub.example.com"
    jwt_secret: str = "change-me"
    # Comma-separated list of allowed origins for CORS (spec.md Section 4.4 Security).
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # Set to 1 to require the X-User-Id header on RBAC-protected endpoints.
    require_auth: bool = False
    # Live-demo mode (spec.md Section 4.9): when false, the app starts with
    # real user accounts but ZERO pre-written crisis events/checkins, so
    # every artifact shown during judging is generated live.
    seed_demo_data: bool = True

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

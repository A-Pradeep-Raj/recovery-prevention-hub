import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import users, profiles, crisis, checkins, copilot

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed user accounts and, unless SEED_DEMO_DATA=false (live-demo mode,
    spec.md Section 4.9), pre-written local-dev profiles."""
    skip = os.environ.get("SKIP_SEED_ON_STARTUP") == "1"
    if not skip:
        from app.scripts.seed_database import main as seed_main
        seed_main(seed_demo_content=settings.seed_demo_data)
    yield


app = FastAPI(title="Recovery & Prevention Hub API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(crisis.router)
app.include_router(checkins.router)
app.include_router(copilot.router)


@app.get("/health")
def health():
    return {"status": "ok"}

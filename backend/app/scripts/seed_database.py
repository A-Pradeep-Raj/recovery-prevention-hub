"""Seed the in-memory store with real user accounts (needed for any demo)
and, optionally, pre-written profiles/crisis history for local dev only.

spec.md Section 4.9: seed_demo_content=False starts with real users but ZERO
pre-written crisis events, for the fully-live judged demo.
"""
import json
import os
from pathlib import Path
from app.services.firestore_client import get_firestore_client


def _resolve_demo_dir() -> Path:
    env_override = os.environ.get("DEMO_DATA_DIR")
    if env_override:
        return Path(env_override)
    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "demo_data",  # local dev: repo_root/demo_data
        here.parents[2] / "demo_data",  # container: /app/demo_data
    ]
    for candidate in candidates:
        if (candidate / "users.json").exists():
            return candidate
    return candidates[0]


DEMO_DIR = _resolve_demo_dir()


def main(seed_demo_content: bool = True):
    db = get_firestore_client()
    for name in ["users", "profiles", "crisis_events", "caregiver_alerts", "checkins"]:
        db.collection(name).delete_all()

    users = json.loads((DEMO_DIR / "users.json").read_text(encoding="utf-8-sig"))
    for u in users:
        db.collection("users").set(u["id"], u)
    print(f"Seeded {len(users)} users")

    if not seed_demo_content:
        print("SEED_DEMO_DATA=false: skipping pre-written profiles/crisis history — "
              "live demo mode, all content must be created live via the API.")
        return

    profiles_path = DEMO_DIR / "profiles.json"
    if profiles_path.exists():
        profiles = json.loads(profiles_path.read_text(encoding="utf-8-sig"))
        for p in profiles:
            db.collection("profiles").set(p["id"], p)
        print(f"Seeded {len(profiles)} recovery profiles")

    print("Demo database seeded successfully.")


if __name__ == "__main__":
    main()

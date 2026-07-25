# Demo Guide — Recovery & Prevention Hub

> Per spec.md Section 4.9 (Live Demo Integrity — Mandatory): the judged session must be
> fully live. No static/hardcoded pages, no mock data presented as live, no false
> positives, no hallucinated AI responses.

## 1. Pre-Demo Checklist

- [ ] Backend deployed/running with `USE_MOCK_AI=false` and `SEED_DEMO_DATA=false`
- [ ] Confirm `/health` returns `{"status":"ok"}` and `GET /api/users` returns real accounts
      while crisis/profile endpoints start empty
- [ ] Frontend deployed/running and pointed at that backend
- [ ] Rehearse the full live flow at least twice with real, unscripted profiles
- [ ] `pytest -q` green (33 passed) — offline/mocked tests only, not a substitute for the live run

## 2. Step-by-Step Walkthrough (Fully Live)

### Step 1 — Problem Intro
**Say:** "When cognitive load is highest — a craving, a panic moment — typing or navigating a menu is the wrong interaction model. Everything you're about to see is generated live against real Gemini."

### Step 2 — Build a Real Safety Plan
**Do:** In the Safety Plan tab, live-enter real triggers, coping strategies, and a support contact for a real user account. Save it.

### Step 3 — Zero-Typing Crisis Trigger
**Say:** "One tap. No typing." **Do:** Switch to Crisis Mode, tap "I need help now." Show the "Grounded in: ..." trace proving the script used the profile just entered, not a canned response.

### Step 4 — Caregiver Alert
**Do:** Switch to Caregiver Dashboard, show the live alert with context + suggested action, and acknowledge it.

### Step 5 — Recovery Co-Pilot (Grounded + Ungrounded)
**Do:** Ask a real question grounded in the Safety Plan (get a grounded answer + source). Then ask an unrelated/unsafe question live and show the explicit "I don't have grounded information" guardrail response.

### Step 6 — Craving Check-In
**Do:** Tap a craving intensity level, show the live-suggested coping technique pulled from the real Safety Plan.

### Step 7 — GCP Infrastructure Proof
**Do:** Show Cloud Run logs / Vertex AI usage confirming the live calls from steps 3–6.

### Step 8 — Closing
**Say:** "Every artifact you saw was generated during this session — the grounding guardrails mean the AI either uses your real data or admits it doesn't know, never fabricates."

## 3. Post-Demo Q&A Prep

| Question | Answer |
|---|---|
| "How do you prevent hallucinated clinical advice?" | "`_is_grounded()` in `ai_services.py` checks every generated script/answer against the user's actual profile or curated knowledge base before showing it. Ungrounded content is rejected, not softened." |
| "What happens if someone is in real danger?" | "Every Crisis Mode screen shows how to reach real emergency services, and the AI is prompted to never discourage seeking professional help — this is a hard guardrail, not a suggestion." |
| "Is this a replacement for therapy/treatment?" | "No — explicitly out of scope (spec.md Section 8). It's a bridge tool for the moment between crises and professional care." |

# Manual Test Log

Per `spec.md` Section 4.5, this log documents scenarios covered manually rather than by
the automated pytest suite (`backend/tests/`).

Automated coverage: 33 tests in `backend/tests/` — `test_ai_services.py` (including
`TestRealGeminiPath`, which exercises the mandatory real-Gemini path and anti-hallucination
guardrails per spec.md Section 4.8/4.9), `test_crisis_processor.py`, `test_checkin_processor.py`,
`test_auth.py`, `test_integration_flow.py`. Run with:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest -v
```

## Manual Test Scenarios

| # | Scenario | Steps | Expected Result | Status |
|---|---|---|---|---|
| 1 | Zero-typing crisis trigger | Open Crisis Mode tab, tap "I need help now" with no prior typing | Grounded script appears within a few seconds, no form required | ⬜ Pending live-run verification |
| 2 | Caregiver alert on crisis | Trigger crisis for a user with a linked caregiver | Alert appears in Caregiver Dashboard with context + suggested action | ⬜ Pending live-run verification |
| 3 | Anti-hallucination: chatbot refuses ungrounded question | Ask Recovery Co-Pilot a question unrelated to Safety Plan / knowledge base | Response explicitly states it lacks grounded information | ⬜ Pending live-run verification |
| 4 | Anti-hallucination: fabricated action item rejected | (Unit-level) Mock Gemini response inventing a coping strategy not in profile | Script generation rejects it, falls back to generic script | ✅ Covered by `test_generate_emergency_script_rejects_hallucinated_script` |
| 5 | Craving check-in suggests real strategy | Tap a craving intensity level with a saved Safety Plan | Suggested technique matches a logged coping strategy | ✅ Covered by `test_craving_checkin_suggests_technique_from_profile` |
| 6 | RBAC denies unrelated user | Call `GET /api/profiles/{id}` with an unrelated `X-User-Id` | 403 Forbidden | ✅ Covered by `test_auth.py` |
| 7 | Empty profile still produces safe script | Trigger crisis for a user with no Safety Plan | Generic grounding script shown, `grounded_fields` empty | ✅ Covered by `test_missing_profile_still_produces_generic_script` |

## Known Gaps

- Voice-first crisis trigger (Cloud Speech-to-Text) is architected (spec.md Section 3.1/3.7) but not yet wired to a live microphone input in the UI — trigger_method="voice" is supported by the API.
- Wearable/passive signal integration is a stretch goal (spec.md Section 7), not built.
- Multi-caregiver coordination (more than one linked caregiver) is a stretch goal, not built.

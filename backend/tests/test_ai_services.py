"""Unit tests for app.services.ai_services — emergency script generation,
coping-technique suggestion, Recovery Co-Pilot Q&A, and anti-hallucination
guardrails (spec.md Section 4.5, 4.8, 4.9).
"""
import json
import pytest

import app.services.ai_services as ai_services
from app.services.ai_services import (
    ask_copilot,
    generate_emergency_script,
    suggest_coping_technique,
    summarize_resource,
    translate_text,
)


class TestGenerateEmergencyScript:
    def test_empty_profile_produces_generic_fallback(self):
        result = generate_emergency_script({})
        assert isinstance(result["script"], str) and len(result["script"]) > 0
        assert result["grounded_fields"] == []

    def test_mock_mode_grounds_in_coping_strategies(self):
        profile = {"coping_strategies": ["call my sponsor"], "triggers": [], "support_contacts": []}
        result = generate_emergency_script(profile)
        assert "call my sponsor" in result["script"]
        assert "coping_strategies" in result["grounded_fields"]


class TestSuggestCopingTechnique:
    def test_no_strategies_returns_generic_grounding(self):
        result = suggest_coping_technique(8, [])
        assert "generic-grounding" in result

    def test_with_strategies_returns_a_listed_strategy(self):
        result = suggest_coping_technique(5, ["deep breathing", "call sponsor"])
        assert result in ["deep breathing", "call sponsor"]


class TestTranslateText:
    def test_mock_translation_prefixes_target_language(self):
        result = translate_text("Hello", target_language="es")
        assert result.startswith("[MOCK-ES]")


class TestSummarizeResource:
    def test_empty_source_returns_empty(self):
        assert summarize_resource("") == ""

    def test_mock_summary_is_truncated(self):
        long_text = "word " * 200
        summary = summarize_resource(long_text)
        assert summary.startswith("[MOCK SUMMARY]")
        assert len(summary) < len(long_text)


class TestAskCopilotMock:
    def test_returns_answer_with_source(self):
        result = ask_copilot("What triggers do I have?", "Triggers: stress. Coping: running.", "en")
        assert "answer" in result and "source" in result


class TestRealGeminiPath:
    """spec.md Section 4.8/4.9: enable the real-Gemini code path and mock
    only `_call_gemini` — the network boundary — so grounding/guardrail
    logic executes for real."""

    @pytest.fixture(autouse=True)
    def enable_gemini(self, monkeypatch):
        monkeypatch.setattr(ai_services.settings, "use_mock_ai", False)
        monkeypatch.setattr(ai_services.settings, "gcp_project_id", "fake-test-project")
        yield

    def test_generate_emergency_script_uses_gemini_response(self, monkeypatch):
        fake_response = json.dumps({
            "script": "Remember your strategy: call your sponsor. You are safe right now.",
            "grounded_fields": ["coping_strategies"],
        })
        monkeypatch.setattr(ai_services, "_call_gemini", lambda prompt: fake_response)

        profile = {"coping_strategies": ["call your sponsor"], "triggers": [], "support_contacts": []}
        result = generate_emergency_script(profile)

        assert "call your sponsor" in result["script"]
        assert result["grounded_fields"] == ["coping_strategies"]

    def test_generate_emergency_script_rejects_hallucinated_script(self, monkeypatch):
        """Anti-hallucination guardrail: a script referencing a coping
        strategy the user never logged must be rejected."""
        fake_response = json.dumps({
            "script": "Try skydiving to release your emotions and call your imaginary therapist Dr. Zorg.",
            "grounded_fields": ["coping_strategies"],
        })
        monkeypatch.setattr(ai_services, "_call_gemini", lambda prompt: fake_response)

        profile = {"coping_strategies": ["deep breathing"], "triggers": [], "support_contacts": []}
        result = generate_emergency_script(profile)

        # Falls back to the safe generic script instead of surfacing the fabricated one.
        assert "skydiving" not in result["script"]
        assert "Dr. Zorg" not in result["script"]

    def test_generate_emergency_script_falls_back_when_gemini_raises(self, monkeypatch):
        def boom(prompt):
            raise RuntimeError("network error")

        monkeypatch.setattr(ai_services, "_call_gemini", boom)

        result = generate_emergency_script({"coping_strategies": ["deep breathing"]})
        assert len(result["script"]) > 0

    def test_ask_copilot_uses_gemini_response(self, monkeypatch):
        fake_response = json.dumps({
            "answer": "Your logged trigger is stress at work.",
            "source": "Triggers: stress at work.",
        })
        monkeypatch.setattr(ai_services, "_call_gemini", lambda prompt: fake_response)

        result = ask_copilot("What are my triggers?", "Triggers: stress at work. Coping: running.", "en")

        assert result["answer"] == "Your logged trigger is stress at work."

    def test_ask_copilot_rejects_ungrounded_source(self, monkeypatch):
        """Anti-hallucination guardrail: a claimed source not actually
        present in the grounding context must be rejected."""
        fake_response = json.dumps({
            "answer": "You should take this specific medication dosage.",
            "source": "the medication dosage guide says to take 500mg twice daily",
        })
        monkeypatch.setattr(ai_services, "_call_gemini", lambda prompt: fake_response)

        result = ask_copilot("What medication should I take?", "Triggers: stress. Coping: running.", "en")

        assert "don't have grounded information" in result["answer"].lower()

    def test_ask_copilot_respects_not_grounded_signal(self, monkeypatch):
        fake_response = json.dumps({"answer": "NOT_GROUNDED", "source": ""})
        monkeypatch.setattr(ai_services, "_call_gemini", lambda prompt: fake_response)

        result = ask_copilot("What's the meaning of life?", "Triggers: stress. Coping: running.", "en")

        assert "don't have grounded information" in result["answer"].lower()

    def test_suggest_coping_technique_rejects_invented_technique(self, monkeypatch):
        fake_response = json.dumps({"suggested_technique": "extreme skydiving therapy"})
        monkeypatch.setattr(ai_services, "_call_gemini", lambda prompt: fake_response)

        result = suggest_coping_technique(7, ["deep breathing", "call sponsor"])

        assert result in ["deep breathing", "call sponsor"]

    def test_summarize_resource_uses_gemini_response(self, monkeypatch):
        source = "Recovery is not linear and relapse is common."
        monkeypatch.setattr(ai_services, "_call_gemini", lambda prompt: "Recovery is not linear.")

        summary = summarize_resource(source)

        assert summary == "Recovery is not linear."

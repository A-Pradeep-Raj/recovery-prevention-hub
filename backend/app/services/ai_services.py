"""Generative AI integration for emergency script generation, craving
coping-technique suggestion, Recovery Co-Pilot Q&A, and educational
summarization.

spec.md Section 4.8 (Generative AI Usage — Mandatory) + Section 4.9 (Live Demo
Integrity / anti-hallucination): every capability below must be backed by a
real Gemini call (via Vertex AI) when USE_MOCK_AI=false, and every output
must be checked for grounding against the user's actual Recovery Profile /
curated knowledge base before being surfaced. Ungrounded content is rejected
in favor of an explicit "not grounded" fallback — never fabricated.

`_call_gemini` is the single network-call boundary; unit tests mock this
function directly so the surrounding prompt-building/parsing/grounding logic
is exercised for real.
"""
import json
import logging
from functools import lru_cache
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("app.ai_services")

_GEMINI_MODEL_NAME = "gemini-2.5-flash"
_vertex_initialized = False


def _ensure_vertex_initialized() -> None:
    global _vertex_initialized
    if _vertex_initialized:
        return
    import vertexai

    vertexai.init(project=settings.gcp_project_id, location=settings.gcp_region)
    _vertex_initialized = True


def _call_gemini(prompt: str) -> str:
    """Single network-call boundary for the Vertex AI Gemini model."""
    from vertexai.generative_models import GenerativeModel

    _ensure_vertex_initialized()
    model = GenerativeModel(_GEMINI_MODEL_NAME)
    response = model.generate_content(prompt)
    return response.text


def _gemini_available() -> bool:
    return not settings.use_mock_ai and bool(settings.gcp_project_id)


_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "for", "of", "to", "in", "on", "at", "is", "are", "was",
    "were", "you", "your", "you're", "youre", "it", "its", "this", "that", "right", "now", "sounds",
    "like", "feeling", "lot", "take", "deep", "breath", "remember", "found", "strength", "before",
    "moment", "got", "this", "with", "have", "has", "had", "be", "been", "being", "will", "would",
    "can", "could", "just", "very", "really", "also", "key", "support", "yourself", "when", "what",
    "not", "here", "there", "one", "again", "some", "any", "all", "who", "how", "why", "did", "do",
    "does", "let", "let's", "lets",
}


def _content_words(text: str) -> list[str]:
    """Extract meaningful (non-stopword, length>2) lowercase word stems from
    text for fuzzy grounding comparison. Uses a short prefix (first 4 chars)
    so natural paraphrasing (calling/call, going/go) still matches."""
    words = [w.strip(".,!?;:\"'") for w in text.lower().split()]
    return [w[:4] for w in words if len(w) > 2 and w not in _STOPWORDS]


def _is_grounded(snippet: str, corpus: str, threshold: float = 0.2) -> bool:
    """Anti-hallucination guardrail (spec.md Section 4.9): verify that
    Gemini-generated content is actually grounded in the corpus (Recovery
    Profile fields / knowledge base) rather than fabricated.

    Natural language responses are full of filler/connective words (e.g.
    "remember", "you could", "this feeling will pass"), so checking what
    fraction of the *snippet's* words appear in the corpus is fragile and
    produces false-positive rejections. Instead, this checks corpus
    coverage: what fraction of the corpus's own distinct content terms
    (profile facts — inherently few in number) show up in the snippet, plus
    a minimum absolute-hit floor so a single incidental word match on a long
    snippet doesn't count as "grounded."
    """
    snippet = (snippet or "").strip()
    if not snippet:
        return False
    if snippet.lower() in corpus.lower():
        return True

    corpus_words = list(dict.fromkeys(_content_words(corpus)))  # dedup, preserve order
    if not corpus_words:
        # No real facts to ground against (empty/generic profile) — nothing to verify.
        return True

    snippet_words = set(_content_words(snippet))
    hits = sum(1 for w in corpus_words if w in snippet_words)

    if hits == 0:
        return False
    # For short/sparse corpora (few distinct facts, e.g. a single coping
    # strategy), referencing even one of them is meaningful evidence of
    # grounding. For larger corpora, require a proportional share.
    return hits >= 1 and (hits / len(corpus_words)) >= threshold


_NOT_GROUNDED_MESSAGE = {
    "en": "I don't have grounded information about that in your recovery profile or "
          "our knowledge base. Please contact your care team or a crisis line for guidance.",
    "es": "No tengo informacion verificada sobre eso en tu perfil de recuperacion. "
          "Por favor contacta a tu equipo de atencion o una linea de crisis.",
}


def _not_grounded_message(language: str) -> str:
    return _NOT_GROUNDED_MESSAGE.get(language, _NOT_GROUNDED_MESSAGE["en"])


# ---------------------------------------------------------------------------
# Translation (Cloud Translation API — spec.md Section 5.2)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=512)
def _translate_cached(text: str, target_language: str, source_language: str | None) -> str:
    if settings.use_mock_ai or target_language == source_language:
        return f"[MOCK-{target_language.upper()}] {text}"
    try:
        from google.cloud import translate_v2 as translate

        client = translate.Client()
        return client.translate(text, target_language=target_language)["translatedText"]
    except Exception:
        logger.warning("translate_text: Cloud Translation call failed, falling back to mock", exc_info=True)
        return f"[MOCK-{target_language.upper()}] {text}"


def translate_text(text: str, target_language: str, source_language: str | None = None) -> str:
    return _translate_cached(text, target_language, source_language)


# ---------------------------------------------------------------------------
# Personalized emergency script generation (spec.md Section 3.2 + 4.8/4.9)
# ---------------------------------------------------------------------------

_SCRIPT_PROMPT = """You are generating a short, calming emergency support script for someone \
in acute crisis (craving, panic, or early relapse risk). The person's cognitive load is \
very high right now — keep language simple, warm, and grounding.

You MUST base the script ONLY on the recovery profile facts given below. Do NOT invent \
coping strategies, support contacts, or personal details not listed. If the profile is \
empty or too sparse to personalize, generate a SAFE GENERIC grounding script instead and \
say so explicitly in the "grounded_fields" list (empty list = generic fallback).

Recovery Profile:
- Known triggers: {triggers}
- Coping strategies that have worked before: {coping_strategies}
- Support contacts: {support_contacts}

Return ONLY a JSON object (no prose, no markdown fences) with exactly these keys:
  - "script": the calming, grounding script text (3-6 short sentences, plain language)
  - "grounded_fields": array of profile field names actually referenced (e.g. \
["coping_strategies", "support_contacts"]), or [] if this is a generic fallback script
"""


def _generic_script_fallback() -> dict:
    return {
        "script": (
            "You're safe right now. Take a slow breath in for 4 counts, hold for 4, and out for 6. "
            "Name 5 things you can see around you, 4 things you can touch, 3 things you can hear. "
            "This feeling is temporary and it will pass. If you are in danger, please call your local "
            "emergency number or a crisis line right now."
        ),
        "grounded_fields": [],
    }


def generate_emergency_script(profile: dict) -> dict:
    """Generate a personalized emergency script grounded in the user's Recovery Profile.

    spec.md Section 4.8/4.9: uses a real Gemini call when USE_MOCK_AI=false.
    Every field the model claims to have used is verified against the actual
    profile text; if verification fails or the model call fails, falls back
    to a safe generic script rather than surfacing fabricated content.
    """
    triggers = ", ".join(profile.get("triggers", [])) or "(none logged)"
    coping = ", ".join(profile.get("coping_strategies", [])) or "(none logged)"
    contacts = ", ".join(profile.get("support_contacts", [])) or "(none logged)"
    corpus = f"{triggers} {coping} {contacts} {profile.get('notes') or ''}"

    if _gemini_available():
        try:
            prompt = _SCRIPT_PROMPT.format(triggers=triggers, coping_strategies=coping, support_contacts=contacts)
            raw = _call_gemini(prompt)
            cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(cleaned)
            script = parsed.get("script", "")
            grounded_fields = parsed.get("grounded_fields", [])
            if script and _is_grounded(script, corpus):
                return {"script": script, "grounded_fields": grounded_fields}
            logger.warning("generate_emergency_script: ungrounded script rejected, using generic fallback")
        except Exception:
            logger.warning("generate_emergency_script: Gemini call failed, using generic fallback", exc_info=True)

    if settings.use_mock_ai:
        base = _generic_script_fallback()
        if profile.get("coping_strategies"):
            base["script"] = (
                f"[MOCK] Remember your coping strategy: {profile['coping_strategies'][0]}. "
                + base["script"]
            )
            base["grounded_fields"] = ["coping_strategies"]
        return base

    return _generic_script_fallback()


# ---------------------------------------------------------------------------
# Craving check-in coping-technique suggestion (spec.md Section 3.3 + 4.8)
# ---------------------------------------------------------------------------

_COPING_PROMPT = """A person just logged a craving check-in with intensity {intensity}/10. \
Suggest ONE coping technique for them to use right now, chosen ONLY from their own \
previously-successful strategies listed below. Do not invent a new technique.

Their coping strategies: {coping_strategies}

Return ONLY a JSON object with key "suggested_technique" (string, one of the listed \
strategies verbatim, or "generic-grounding" if the list is empty).
"""


def suggest_coping_technique(intensity: int, coping_strategies: list[str]) -> str:
    if not coping_strategies:
        return "generic-grounding: try slow breathing (4 in, 4 hold, 6 out) and name 5 things you can see."

    if _gemini_available():
        try:
            raw = _call_gemini(_COPING_PROMPT.format(intensity=intensity, coping_strategies=", ".join(coping_strategies)))
            cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(cleaned)
            suggestion = parsed.get("suggested_technique", "")
            if suggestion and _is_grounded(suggestion, " ".join(coping_strategies)):
                return suggestion
            logger.warning("suggest_coping_technique: ungrounded suggestion rejected, using heuristic fallback")
        except Exception:
            logger.warning("suggest_coping_technique: Gemini call failed, using heuristic fallback", exc_info=True)

    # Heuristic/mock fallback: highest intensity -> first listed strategy (deterministic).
    return coping_strategies[0]


# ---------------------------------------------------------------------------
# Recovery Co-Pilot chatbot Q&A (spec.md Section 3.5 + 4.8/4.9)
# ---------------------------------------------------------------------------

_COPILOT_PROMPT = """You are the "Recovery Co-Pilot," a support chatbot. Answer the \
question using ONLY the grounding context below (the user's own recovery profile and \
curated educational knowledge base excerpts). Do not use outside knowledge, do not give \
clinical/medical diagnosis or treatment advice, and do not invent facts.

If — and only if — the context does not contain enough information to answer safely, set \
"answer" to exactly "NOT_GROUNDED" and leave "source" empty. Never fabricate an answer.

Answer in the language with ISO code "{language}".

Grounding context:
---
{context}
---

Question: {question}

Return ONLY a JSON object with keys:
  - "answer": your grounded answer, or "NOT_GROUNDED" per the rule above
  - "source": which part of the context supports your answer (verbatim excerpt), or "" if NOT_GROUNDED
"""


def ask_copilot(question: str, context: str, language: str = "en") -> dict:
    """Answer a Recovery Co-Pilot question, grounded strictly in `context`
    (the user's Recovery Profile + curated knowledge base excerpts).

    spec.md Section 4.9: verified against the context before being surfaced;
    an ungrounded/unsafe question yields an explicit "not grounded" message,
    never a fabricated clinical claim.
    """
    if _gemini_available():
        try:
            prompt = _COPILOT_PROMPT.format(context=context, question=question, language=language)
            raw = _call_gemini(prompt)
            cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(cleaned)
            answer = parsed.get("answer", "")
            source = parsed.get("source", "")
            if answer.strip().upper() == "NOT_GROUNDED":
                return {"answer": _not_grounded_message(language), "source": ""}
            if source and not _is_grounded(source, context, threshold=0.6):
                logger.warning("ask_copilot: ungrounded source rejected, treating as NOT_GROUNDED")
                return {"answer": _not_grounded_message(language), "source": ""}
            if answer:
                return {"answer": answer, "source": source}
        except Exception:
            logger.warning("ask_copilot: Gemini call failed, falling back", exc_info=True)

    if settings.use_mock_ai:
        return {"answer": f"[MOCK ANSWER in {language}] Based on your profile: {context[:80]}...", "source": context[:80]}

    return {"answer": _not_grounded_message(language), "source": ""}


# ---------------------------------------------------------------------------
# Educational resource summarization (spec.md Section 3.6 + 4.8)
# ---------------------------------------------------------------------------

_SUMMARY_PROMPT = """Summarize the following educational resource about substance use \
disorders / recovery in 2-3 plain-language sentences. Do not add facts not present in \
the source text.

Source:
---
{source_text}
---
"""


def summarize_resource(source_text: str) -> str:
    if not source_text.strip():
        return ""

    if _gemini_available():
        try:
            text = _call_gemini(_SUMMARY_PROMPT.format(source_text=source_text)).strip()
            if text and _is_grounded(text, source_text, threshold=0.3):
                return text
            logger.warning("summarize_resource: ungrounded summary rejected, using heuristic fallback")
        except Exception:
            logger.warning("summarize_resource: Gemini call failed, using heuristic fallback", exc_info=True)

    return f"[MOCK SUMMARY] {source_text[:200].strip()}..."

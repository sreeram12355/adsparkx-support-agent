"""Google Gemini-backed LLM functions: persona detection and grounded generation.

Two responsibilities:
  1. detect_persona() — classify the message into one of the three personas
     (hybrid: rule-based signal + LLM judgement) and return a sentiment score.
  2. generate_answer() — produce a persona-adapted answer grounded ONLY in the
     retrieved knowledge-base context (no hallucination).

Uses the unified `google-genai` SDK. Embeddings stay local (see embeddings.py);
only these text-generation calls require the Gemini API key.
"""
from __future__ import annotations

import json
import time
from functools import lru_cache
from typing import Dict, List, Optional

from .config import settings
from .personas import (
    PERSONAS,
    PERSONA_LIBRARY,
    rule_based_scores,
    rule_based_guess,
    get_style,
)


@lru_cache(maxsize=1)
def get_client():
    if not settings.has_api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    from google import genai

    return genai.Client(api_key=settings.google_api_key)


# Transient server states worth retrying (overload / rate limit).
_RETRY_STATUS = (429, 500, 503)
_MAX_RETRIES = 4


def _generate(system: str, contents, *, temperature: float, json_mode: bool = False) -> str:
    """Thin wrapper around Gemini generate_content with a system instruction.

    Retries transient 429/500/503 responses with exponential backoff, since the
    free tier occasionally returns 503 "high demand".
    """
    from google.genai import types
    from google.genai import errors as genai_errors

    client = get_client()
    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        response_mime_type="application/json" if json_mode else "text/plain",
    )

    last_exc: Optional[Exception] = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = client.models.generate_content(
                model=settings.gemini_model, contents=contents, config=config
            )
            return (resp.text or "").strip()
        except genai_errors.APIError as exc:
            status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
            if status in _RETRY_STATUS and attempt < _MAX_RETRIES - 1:
                last_exc = exc
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
                continue
            raise
    if last_exc:
        raise last_exc
    raise RuntimeError("generate_content failed without an exception")


def _history_to_contents(history: Optional[List[Dict]]) -> List[Dict]:
    """Map our {'role': 'user'|'assistant'} history to Gemini's user/model turns."""
    contents: List[Dict] = []
    for m in history or []:
        role = "model" if m["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    return contents


# --- Persona detection -------------------------------------------------------

_PERSONA_DESCRIPTIONS = "\n".join(
    f"- {p.name}: {p.description}" for p in PERSONA_LIBRARY.values()
)


def detect_persona(message: str, history: Optional[List[Dict]] = None) -> Dict:
    """Classify the message persona and estimate sentiment.

    Returns: {persona, confidence (0-1), sentiment (-1..1), reason, rule_scores}
    Falls back to the rule-based guess if the LLM call fails.
    """
    rule_scores = rule_based_scores(message)

    system = (
        "You are a precise classifier for customer-support messages. "
        "Classify the user's message into exactly one persona from this list:\n"
        f"{_PERSONA_DESCRIPTIONS}\n\n"
        "Also rate sentiment from -1 (very negative/angry) to 1 (very positive). "
        "Consider the conversation so far if provided. "
        "Respond ONLY as compact JSON with keys: persona, confidence, sentiment, reason. "
        f"'persona' must be exactly one of: {PERSONAS}."
    )

    convo = ""
    if history:
        recent = history[-4:]
        convo = "Conversation so far:\n" + "\n".join(
            f"{m['role']}: {m['content']}" for m in recent
        ) + "\n\n"

    user = (
        f"{convo}Latest user message:\n\"\"\"{message}\"\"\"\n\n"
        f"Rule-based keyword hits (hint, not authoritative): {rule_scores}"
    )

    try:
        raw = _generate(system, user, temperature=0, json_mode=True)
        data = json.loads(raw)
        persona = str(data.get("persona", "")).strip()
        if persona not in PERSONAS:
            persona = rule_based_guess(message)
        return {
            "persona": persona,
            "confidence": float(data.get("confidence", 0.6)),
            "sentiment": float(data.get("sentiment", 0.0)),
            "reason": data.get("reason", ""),
            "rule_scores": rule_scores,
        }
    except Exception as exc:  # graceful fallback to rules
        return {
            "persona": rule_based_guess(message),
            "confidence": 0.4,
            "sentiment": -0.3 if rule_scores.get("Frustrated User", 0) else 0.0,
            "reason": f"LLM unavailable ({exc}); used rule-based fallback.",
            "rule_scores": rule_scores,
        }


# --- Grounded answer generation ----------------------------------------------

def _format_context(context_blocks: List[Dict]) -> str:
    lines = []
    for i, b in enumerate(context_blocks, start=1):
        lines.append(f"[Source {i}: {b['citation']}]\n{b['text']}")
    return "\n\n".join(lines)


def generate_answer(
    query: str,
    persona: str,
    context_blocks: List[Dict],
    history: Optional[List[Dict]] = None,
) -> str:
    """Generate a persona-adapted, grounded answer.

    context_blocks: list of {"text": str, "citation": str}
    """
    style = get_style(persona)

    system = (
        "You are CloudDesk's customer-support assistant. "
        "Answer the user's question USING ONLY the information in the provided "
        "context. Do not invent features, numbers, URLs, or steps that are not in "
        "the context. If the context does not contain the answer, say clearly that "
        "you don't have that information and that you'll connect them to a human. "
        "Cite the source document(s) you used at the end as 'Sources: ...'.\n\n"
        f"PERSONA OF THIS USER: {persona}.\n"
        f"RESPONSE STYLE — follow this carefully:\n{style}"
    )

    context = _format_context(context_blocks) if context_blocks else "(no relevant context found)"

    contents = _history_to_contents(history[-6:] if history else None)
    contents.append(
        {
            "role": "user",
            "parts": [
                {
                    "text": (
                        f"Knowledge-base context:\n{context}\n\n"
                        f"User question: {query}\n\n"
                        "Write the response now, adapted to the persona and grounded "
                        "in the context."
                    )
                }
            ],
        }
    )

    return _generate(system, contents, temperature=0.3)


def summarize_issue(history: List[Dict]) -> str:
    """One-line summary of the user's core issue, for the handoff packet."""
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    try:
        return _generate(
            "Summarize the customer's core issue in one short sentence.",
            convo,
            temperature=0,
        )
    except Exception:
        for m in history:
            if m["role"] == "user":
                return m["content"][:200]
        return "Unspecified issue."

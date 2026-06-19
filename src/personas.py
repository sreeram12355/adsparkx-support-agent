"""Persona definitions, rule-based signals, and the per-persona response style.

The system supports three personas required by the assignment:
  - Technical Expert
  - Frustrated User
  - Business Executive

Detection is a *hybrid* of (1) a lightweight rule-based keyword scorer used as a
fast signal / fallback, and (2) an LLM classifier (see llm.py) that makes the
final call. The style guidance below is injected into the answer-generation
prompt so the tone adapts to the detected persona.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

TECHNICAL_EXPERT = "Technical Expert"
FRUSTRATED_USER = "Frustrated User"
BUSINESS_EXECUTIVE = "Business Executive"

PERSONAS = [TECHNICAL_EXPERT, FRUSTRATED_USER, BUSINESS_EXECUTIVE]
DEFAULT_PERSONA = TECHNICAL_EXPERT  # neutral, detail-oriented default


@dataclass
class Persona:
    name: str
    description: str
    style: str                       # injected into the generation prompt
    keywords: List[str] = field(default_factory=list)


PERSONA_LIBRARY: Dict[str, Persona] = {
    TECHNICAL_EXPERT: Persona(
        name=TECHNICAL_EXPERT,
        description=(
            "Uses technical terminology; asks about APIs, logs, configs, error "
            "codes; wants detailed, precise explanations and root-cause analysis."
        ),
        style=(
            "Respond in a precise, technical tone. Include a brief root-cause "
            "analysis, then clear step-by-step troubleshooting. Reference exact "
            "error codes, headers, endpoints, or settings names from the context. "
            "Be thorough but do not invent details that are not in the context."
        ),
        keywords=[
            "api", "endpoint", "token", "oauth", "saml", "sso", "header", "json",
            "error code", "401", "403", "429", "500", "log", "logs", "stack trace",
            "config", "configuration", "webhook", "signature", "certificate",
            "rate limit", "request id", "curl", "payload", "ssl", "tls", "debug",
            "root cause", "documentation", "schema", "integration",
        ],
    ),
    FRUSTRATED_USER: Persona(
        name=FRUSTRATED_USER,
        description=(
            "Emotional, urgent language; repeated complaints; expresses anger or "
            "exhaustion; just wants the problem fixed."
        ),
        style=(
            "Respond with empathy first — acknowledge the frustration in one warm "
            "sentence. Use simple, reassuring, jargon-free language. Give a short, "
            "clear, action-oriented set of steps (numbered, minimal). Be calm and "
            "confident so the user feels supported."
        ),
        keywords=[
            "frustrated", "angry", "ridiculous", "terrible", "worst", "useless",
            "nothing works", "doesn't work", "not working", "still not", "again",
            "tried everything", "fed up", "sick of", "urgent", "asap", "immediately",
            "come on", "seriously", "unacceptable", "annoyed", "hate", "!!!",
            "please help", "help me", "desperate", "stuck",
        ],
    ),
    BUSINESS_EXECUTIVE: Persona(
        name=BUSINESS_EXECUTIVE,
        description=(
            "Outcome-focused; cares about business impact, timelines, and risk; "
            "prefers concise, high-level communication with minimal jargon."
        ),
        style=(
            "Respond concisely and professionally. Lead with the bottom line and "
            "business impact. Avoid technical jargon. Where the context allows, "
            "give an estimated resolution path or timeline. Keep it to a few crisp "
            "sentences or short bullets a busy executive can scan."
        ),
        keywords=[
            "impact", "business", "operations", "revenue", "roi", "cost", "budget",
            "timeline", "eta", "resolved", "resolution", "downtime", "sla", "risk",
            "stakeholder", "team is blocked", "company", "executive", "leadership",
            "bottom line", "high level", "summary", "strategic", "deadline",
            "customers affected", "production",
        ],
    ),
}


def rule_based_scores(message: str) -> Dict[str, int]:
    """Count keyword hits per persona. Cheap, deterministic signal."""
    text = message.lower()
    scores: Dict[str, int] = {}
    for name, persona in PERSONA_LIBRARY.items():
        score = sum(1 for kw in persona.keywords if kw in text)
        # Exclamation marks and all-caps shouting boost the frustrated signal.
        if name == FRUSTRATED_USER:
            score += text.count("!")
            words = message.split()
            caps = [w for w in words if len(w) >= 4 and w.isupper()]
            score += len(caps)
        scores[name] = score
    return scores


def rule_based_guess(message: str) -> str:
    """Best persona from rules alone (used as fallback when no LLM is available)."""
    scores = rule_based_scores(message)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else DEFAULT_PERSONA


def get_style(persona: str) -> str:
    return PERSONA_LIBRARY.get(persona, PERSONA_LIBRARY[DEFAULT_PERSONA]).style

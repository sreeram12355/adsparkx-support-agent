"""Escalation decision logic and the structured human-handoff summary.

Escalation triggers (all configurable in config.py):
  1. No relevant information found in the knowledge base.
  2. Low retrieval confidence (best score < escalate_below_score).
  3. User remains dissatisfied after `max_dissatisfaction_turns` interactions.
  4. Billing / legal / account-sensitive keywords appear.
  5. The user explicitly asks for a human.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .config import settings
from .retriever import RetrievedChunk


@dataclass
class EscalationDecision:
    escalate: bool
    reasons: List[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return "; ".join(self.reasons) if self.reasons else "No escalation needed."


def _contains_any(text: str, keywords: List[str]) -> Optional[str]:
    low = text.lower()
    for kw in keywords:
        if kw in low:
            return kw
    return None


def evaluate(
    message: str,
    retrieved: List[RetrievedChunk],
    dissatisfaction_count: int,
    sentiment: float,
) -> EscalationDecision:
    """Apply all configured escalation triggers to the current turn."""
    reasons: List[str] = []

    # 5. Explicit human request
    hit = _contains_any(message, settings.human_request_keywords)
    if hit:
        reasons.append(f"User explicitly requested a human (\"{hit}\").")

    # 4. Account-sensitive (billing / legal / account)
    hit = _contains_any(message, settings.sensitive_keywords)
    if hit:
        reasons.append(f"Account-sensitive topic detected (\"{hit}\").")

    # 1 & 2. No / low-confidence retrieval
    best = retrieved[0].score if retrieved else 0.0
    if not retrieved:
        reasons.append("No relevant documents found in the knowledge base.")
    elif best < settings.escalate_below_score:
        reasons.append(
            f"Low retrieval confidence (best score {best:.2f} < "
            f"{settings.escalate_below_score:.2f})."
        )

    # 3. Sustained dissatisfaction
    if dissatisfaction_count >= settings.max_dissatisfaction_turns:
        reasons.append(
            f"User dissatisfied across {dissatisfaction_count} interactions."
        )

    return EscalationDecision(escalate=bool(reasons), reasons=reasons)


def build_handoff_summary(
    persona: str,
    issue: str,
    history: List[Dict],
    documents_used: List[str],
    attempted_steps: List[str],
    reasons: List[str],
    recommendation: str,
) -> Dict:
    """Assemble the structured packet handed to a human support agent."""
    return {
        "persona": persona,
        "issue": issue,
        "escalation_reasons": reasons,
        "documents_used": sorted(set(documents_used)),
        "attempted_steps": attempted_steps,
        "conversation_history": [
            {"role": m["role"], "content": m["content"]} for m in history
        ],
        "recommendation": recommendation,
    }

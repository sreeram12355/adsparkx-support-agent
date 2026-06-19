"""SupportAgent — orchestrates the full per-turn workflow with memory.

Pipeline for each user message:
    detect persona  ->  retrieve context  ->  escalation check
        ->  (escalate + handoff summary)  OR  (generate grounded answer)

Keeps multi-turn conversation memory, the set of documents consulted, and a
running dissatisfaction counter used by the escalation logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import llm
from .config import settings
from .escalation import build_handoff_summary, evaluate
from .retriever import Retriever


@dataclass
class TurnResult:
    user_message: str
    persona: str
    persona_confidence: float
    sentiment: float
    persona_reason: str
    retrieved: List[Dict]            # [{citation, score, text}]
    response: str
    escalated: bool
    escalation_reasons: List[str]
    handoff_summary: Optional[Dict] = None


@dataclass
class SupportAgent:
    retriever: Retriever = field(default_factory=Retriever)
    history: List[Dict] = field(default_factory=list)
    documents_used: List[str] = field(default_factory=list)
    topics_addressed: List[str] = field(default_factory=list)
    dissatisfaction_count: int = 0
    escalated: bool = False

    def _track_dissatisfaction(self, persona: str, sentiment: float) -> None:
        if sentiment <= -0.25 or persona == "Frustrated User":
            self.dissatisfaction_count += 1
        elif sentiment >= 0.3:
            # genuine positive turn relaxes the counter
            self.dissatisfaction_count = max(0, self.dissatisfaction_count - 1)

    def chat(self, message: str) -> TurnResult:
        # 1. Persona detection (hybrid rule + LLM) + sentiment
        det = llm.detect_persona(message, self.history)
        persona = det["persona"]
        self._track_dissatisfaction(persona, det["sentiment"])

        # 2. Retrieval
        retrieved = self.retriever.search(message)
        relevant = [r for r in retrieved if r.score >= settings.min_retrieval_score]
        context_blocks = [
            {"text": r.chunk.text, "citation": r.chunk.citation(), "score": r.score}
            for r in relevant
        ]
        for r in relevant:
            self.documents_used.append(r.chunk.source)
            label = r.chunk.section or r.chunk.source
            if label not in self.topics_addressed:
                self.topics_addressed.append(label)

        retrieved_view = [
            {"citation": r.chunk.citation(), "score": round(r.score, 3), "text": r.chunk.text}
            for r in retrieved
        ]

        # 3. Escalation check
        decision = evaluate(
            message=message,
            retrieved=relevant,
            dissatisfaction_count=self.dissatisfaction_count,
            sentiment=det["sentiment"],
        )

        # record this user turn before generating
        self.history.append({"role": "user", "content": message})

        if decision.escalate:
            self.escalated = True
            issue = llm.summarize_issue(self.history)
            recommendation = self._recommend(decision.reasons, persona)
            handoff = build_handoff_summary(
                persona=persona,
                issue=issue,
                history=self.history,
                documents_used=self.documents_used,
                attempted_steps=self.topics_addressed or ["No self-service steps applied"],
                reasons=decision.reasons,
                recommendation=recommendation,
            )
            response = self._escalation_message(persona)
            self.history.append({"role": "assistant", "content": response})
            return TurnResult(
                user_message=message,
                persona=persona,
                persona_confidence=det["confidence"],
                sentiment=det["sentiment"],
                persona_reason=det["reason"],
                retrieved=retrieved_view,
                response=response,
                escalated=True,
                escalation_reasons=decision.reasons,
                handoff_summary=handoff,
            )

        # 4. Grounded, persona-adapted answer
        response = llm.generate_answer(
            query=message,
            persona=persona,
            context_blocks=context_blocks,
            history=self.history[:-1],  # exclude the message we just appended
        )
        self.history.append({"role": "assistant", "content": response})

        return TurnResult(
            user_message=message,
            persona=persona,
            persona_confidence=det["confidence"],
            sentiment=det["sentiment"],
            persona_reason=det["reason"],
            retrieved=retrieved_view,
            response=response,
            escalated=False,
            escalation_reasons=[],
        )

    # --- helpers ---

    @staticmethod
    def _recommend(reasons: List[str], persona: str) -> str:
        joined = " ".join(reasons).lower()
        if "sensitive" in joined or "human request" in joined:
            return "Route to the appropriate human specialist (billing/legal/account) for identity verification and manual handling."
        if "no relevant" in joined or "low retrieval" in joined:
            return "No documentation covers this issue; assign to a support engineer to investigate and, if needed, create a new KB article."
        if "dissatisfied" in joined:
            return "Self-service has not resolved the issue; assign a human agent to take ownership and follow up directly."
        return "Review the conversation and continue assisting the customer."

    @staticmethod
    def _escalation_message(persona: str) -> str:
        if persona == "Frustrated User":
            return (
                "I'm sorry this has been so frustrating — you've done the right steps. "
                "I'm connecting you with a human support specialist right now who can "
                "dig into your account directly. I've passed along everything we've "
                "covered so you won't have to repeat yourself."
            )
        if persona == "Business Executive":
            return (
                "This requires direct handling by our support team. I'm escalating it "
                "now with a full summary of the issue and business context so a "
                "specialist can take ownership and give you a clear resolution path."
            )
        return (
            "This needs a human specialist. I'm escalating now and have attached a "
            "technical handoff summary (issue, sources consulted, and recommended "
            "next steps) so the engineer can pick up exactly where we left off."
        )

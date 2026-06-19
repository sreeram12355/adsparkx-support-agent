"""Interactive command-line chatbot for the Persona-Adaptive Support Agent.

Usage:
    python cli.py

Displays, for every turn: the detected persona (+ confidence/sentiment),
retrieved sources with scores, the generated response, and the escalation
status. On escalation it prints the structured human-handoff summary as JSON.
"""
from __future__ import annotations

import json
import sys

# Windows consoles default to cp1252 and crash on characters like → or — that
# appear in model output / citations. Force UTF-8 (replace anything unmappable).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

from src.config import settings
from src.ingest import build_index, index_exists


# --- tiny ANSI helpers (degrade gracefully) ---
def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m"


BOLD, CYAN, YELLOW, GREEN, RED, DIM = "1", "36", "33", "32", "31", "2"


def banner():
    print(_c(BOLD, "\n=== CloudDesk Persona-Adaptive Support Agent (CLI) ==="))
    print(_c(DIM, "Type your question. Commands: /summary  /reset  /quit\n"))


def ensure_index():
    if not index_exists():
        print(_c(YELLOW, "No vector index found — building it from /data ..."))
        count = build_index()
        print(_c(GREEN, f"Indexed {count} chunks.\n"))


def print_turn(result):
    print(_c(CYAN, f"\n  Persona: {result.persona} ")
          + _c(DIM, f"(confidence {result.persona_confidence:.2f}, "
                    f"sentiment {result.sentiment:+.2f})"))
    if result.persona_reason:
        print(_c(DIM, f"  Why: {result.persona_reason}"))

    print(_c(CYAN, "  Retrieved sources:"))
    if result.retrieved:
        for r in result.retrieved:
            print(_c(DIM, f"    - {r['citation']}  (score {r['score']:.2f})"))
    else:
        print(_c(DIM, "    (none)"))

    status = _c(RED, "ESCALATED → human handoff") if result.escalated else _c(GREEN, "Resolved by agent")
    print(_c(CYAN, "  Status: ") + status)
    if result.escalation_reasons:
        for reason in result.escalation_reasons:
            print(_c(DIM, f"    • {reason}"))

    print(_c(BOLD, "\n  Agent:"))
    for line in result.response.splitlines():
        print(f"    {line}")

    if result.escalated and result.handoff_summary:
        print(_c(YELLOW, "\n  --- Human Handoff Summary ---"))
        print(json.dumps(result.handoff_summary, indent=2, ensure_ascii=False))
    print()


def main():
    if not settings.has_api_key:
        print(_c(RED, "ERROR: GOOGLE_API_KEY is not set."))
        print("Copy .env.example to .env and add your Gemini key, then retry.")
        sys.exit(1)

    ensure_index()
    # Import after index exists so the model loads once.
    from src.agent import SupportAgent

    agent = SupportAgent()
    banner()

    while True:
        try:
            msg = input(_c(BOLD, "You: ")).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not msg:
            continue
        if msg.lower() in ("/quit", "/exit", "quit", "exit"):
            print("Goodbye!")
            break
        if msg.lower() == "/reset":
            agent = SupportAgent()
            print(_c(GREEN, "Conversation reset.\n"))
            continue
        if msg.lower() == "/summary":
            print(json.dumps(
                {
                    "persona_history_len": len(agent.history),
                    "documents_used": sorted(set(agent.documents_used)),
                    "topics_addressed": agent.topics_addressed,
                    "dissatisfaction_count": agent.dissatisfaction_count,
                    "escalated": agent.escalated,
                },
                indent=2,
            ))
            continue

        result = agent.chat(msg)
        print_turn(result)


if __name__ == "__main__":
    main()

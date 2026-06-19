"""Live end-to-end test: full agent pipeline through Gemini (needs GOOGLE_API_KEY)."""
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

from src.agent import SupportAgent

QUERIES = [
    "Can you explain the API authentication failure? I'm getting a 401 invalid_api_key and need the exact root cause and error details.",
    "I've tried everything and NOTHING works!!! I still can't log in and I'm so frustrated!",
    "How does an outage impact our operations and what's the ETA for resolution and any SLA credits?",
    "How do I set up SAML SSO with Okta and map the email attribute correctly?",
    "I was charged twice this month and I want a refund immediately.",
]

agent = SupportAgent()
for i, q in enumerate(QUERIES, 1):
    print("\n" + "=" * 80)
    print(f"QUERY {i}: {q}")
    res = agent.chat(q)
    print(f"  PERSONA   : {res.persona}  (conf {res.persona_confidence:.2f}, sentiment {res.sentiment:+.2f})")
    print(f"  SOURCES   : {[r['citation'] for r in res.retrieved[:3]]}")
    print(f"  ESCALATED : {res.escalated}  {res.escalation_reasons}")
    print(f"  RESPONSE  :\n{res.response}")
    if res.escalated and res.handoff_summary:
        print("  --- HANDOFF SUMMARY ---")
        print(json.dumps(res.handoff_summary, indent=2, ensure_ascii=False))

print("\n\nLIVE TEST COMPLETE.")

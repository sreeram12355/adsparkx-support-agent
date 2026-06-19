"""Offline smoke test: retrieval + persona rules + escalation (no OpenAI key needed)."""
from src.retriever import Retriever
from src.personas import rule_based_guess
from src.escalation import evaluate
from src.config import settings

print("=== Retrieval ===")
r = Retriever()
for q in [
    "API authentication failure 401 error codes",
    "I want a refund, I was charged twice",
    "how do I reset my password",
]:
    res = r.search(q, top_k=3)
    print(f"\nQ: {q}")
    for x in res:
        print(f"   {x.score:.3f}  {x.chunk.citation()}")

print("\n=== Rule-based persona guess ===")
for q, exp in [
    ("Can you explain the API authentication failure and error details?", "Technical Expert"),
    ("I've tried everything and NOTHING works!!!", "Frustrated User"),
    ("How does this impact operations and when is the ETA for resolution?", "Business Executive"),
]:
    print(f"   {rule_based_guess(q):18s} <- {q!r}")

print("\n=== Escalation logic ===")
# sensitive keyword -> escalate
res = r.search("I want a refund for a double charge", top_k=3)
d = evaluate("I want a refund for a double charge", res, dissatisfaction_count=0, sentiment=-0.5)
print(f"   refund query -> escalate={d.escalate}: {d.reasons}")

# nonsense -> low score escalate
res = r.search("what is the secret coffee recipe of your founder", top_k=3)
print(f"   nonsense best score: {res[0].score:.3f} (threshold {settings.escalate_below_score})")
d = evaluate("what is the secret coffee recipe", [x for x in res if x.score >= settings.min_retrieval_score],
             dissatisfaction_count=0, sentiment=0.0)
print(f"   nonsense query -> escalate={d.escalate}: {d.reasons}")

# explicit human request
d = evaluate("just let me talk to a human please", res, dissatisfaction_count=0, sentiment=0.0)
print(f"   human-request -> escalate={d.escalate}: {d.reasons}")

print("\nAll offline checks ran.")

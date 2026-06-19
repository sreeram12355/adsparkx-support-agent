"""Streamlit chat UI for the Persona-Adaptive Support Agent.

Run:
    streamlit run app.py

Shows the user message, detected persona, retrieved sources, generated
response, and escalation status (with the structured handoff summary).
"""
from __future__ import annotations

import streamlit as st

from src.config import settings
from src.ingest import build_index, index_exists

st.set_page_config(page_title="CloudDesk Support Agent", page_icon="🎧", layout="centered")

PERSONA_BADGE = {
    "Technical Expert": ("🛠️", "#2563eb"),
    "Frustrated User": ("😤", "#dc2626"),
    "Business Executive": ("📈", "#7c3aed"),
}


@st.cache_resource(show_spinner="Loading models and knowledge base…")
def get_agent():
    if not index_exists():
        build_index()
    from src.agent import SupportAgent

    return SupportAgent()


def render_meta(result):
    emoji, color = PERSONA_BADGE.get(result.persona, ("👤", "#475569"))
    st.markdown(
        f"<span style='background:{color};color:white;padding:3px 10px;"
        f"border-radius:12px;font-size:0.85em'>{emoji} {result.persona}</span>"
        f"<span style='color:#64748b;font-size:0.8em'>&nbsp; confidence "
        f"{result.persona_confidence:.2f} · sentiment {result.sentiment:+.2f}</span>",
        unsafe_allow_html=True,
    )
    with st.expander(f"🔎 Retrieved sources ({len(result.retrieved)})", expanded=False):
        if result.retrieved:
            for r in result.retrieved:
                st.markdown(f"**{r['citation']}** · score `{r['score']:.2f}`")
                st.caption(r["text"][:300] + ("…" if len(r["text"]) > 300 else ""))
        else:
            st.write("No sources retrieved.")

    if result.escalated:
        st.error("🚨 Escalated to a human support agent")
        for reason in result.escalation_reasons:
            st.markdown(f"- {reason}")
        with st.expander("📋 Human Handoff Summary", expanded=True):
            st.json(result.handoff_summary)
    else:
        st.success("✅ Resolved by the agent")


def main():
    st.title("🎧 CloudDesk Support Agent")
    st.caption("Persona-adaptive · RAG-grounded · human-in-the-loop")

    if not settings.has_api_key:
        st.error("GOOGLE_API_KEY is not set. Add it to a `.env` file and restart.")
        st.stop()

    with st.sidebar:
        st.header("Settings (read-only)")
        st.write(f"**LLM model:** `{settings.gemini_model}`")
        st.write(f"**Embeddings:** `{settings.embedding_model}`")
        st.write(f"**top_k:** {settings.top_k}")
        st.write(f"**Min retrieval score:** {settings.min_retrieval_score}")
        st.write(f"**Dissatisfaction limit:** {settings.max_dissatisfaction_turns}")
        st.divider()
        if st.button("🔄 Reset conversation"):
            st.session_state.pop("messages", None)
            get_agent.clear()
            st.rerun()
        st.caption("Try the example queries in the README for each persona.")

    agent = get_agent()
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # replay history
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant" and m.get("result"):
                render_meta(m["result"])

    prompt = st.chat_input("Ask CloudDesk support…")
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                result = agent.chat(prompt)
            st.markdown(result.response)
            render_meta(result)
        st.session_state.messages.append(
            {"role": "assistant", "content": result.response, "result": result}
        )


if __name__ == "__main__":
    main()

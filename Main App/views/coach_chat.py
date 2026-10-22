import streamlit as st

from services.coaching.chat_coach import chat_reply, describe_updates
from services.persistence.profile_repository import (
    add_chat_message, clear_chat, get_chat_messages, get_latest_plan, get_profile,
)
from views.common import PAGES, eyebrow, get_groq_client, pal
from views.workout_plan import build_and_save_plan

SUGGESTIONS = [
    "I've hit a plateau on bench press — what should I change?",
    "What should I eat before and after my workout?",
    "My knees hurt when I squat. Any tips?",
    "Can you change my plan to 5 days a week?",
]
AVATARS = {"user": "🧑", "assistant": "🏋️"}


def _send(user_id: int, text: str) -> None:
    client = get_groq_client()
    profile = get_profile(user_id)
    history = get_chat_messages(user_id)
    add_chat_message(user_id, "user", text)
    st.session_state["chat_plan_ready"] = False
    try:
        result = chat_reply(client, profile, get_latest_plan(user_id), history, text)
    except Exception:
        result = {"reply": "I couldn't reach my brain for a second there 😅 — please try that again.", "proposal": None}
    add_chat_message(user_id, "assistant", result["reply"])
    st.session_state["chat_proposal"] = result["proposal"]


def _proposal_card(user_id: int, proposal: dict) -> None:
    P = pal()
    profile = get_profile(user_id)
    changes = describe_updates(proposal["updates"], profile)
    items = "".join(f"<li>{c}</li>" for c in changes) or "<li>Same details — generate a fresh variation of your plan</li>"
    st.markdown(
        f'<div style="background:{P["card_active"]};border:1px solid {P["accent_border"]};border-radius:16px;'
        f'padding:1.1rem 1.4rem;margin:0.6rem 0;">'
        f'<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;color:{P["accent"]};'
        f'text-transform:uppercase;margin-bottom:6px;">🔄 Proposed plan update</div>'
        f'<div style="font-weight:600;color:{P["text"]};margin-bottom:6px;">{proposal["summary"]}</div>'
        f'<ul style="color:{P["muted"]};font-size:0.88rem;margin:0;padding-left:1.2rem;">{items}</ul></div>',
        unsafe_allow_html=True,
    )
    c1, c2, _ = st.columns([1.6, 1, 3])
    with c1:
        apply = st.button("✅ Yes, rebuild my plan", type="primary", use_container_width=True, key="chat_apply")
    with c2:
        if st.button("✖ Not now", use_container_width=True, key="chat_dismiss"):
            st.session_state["chat_proposal"] = None
            add_chat_message(user_id, "assistant", "No problem — your current plan stays as it is. 💪")
            st.rerun()
    if apply:
        updated = {**profile, **proposal["updates"]}
        plan = build_and_save_plan(user_id, updated)
        st.session_state["chat_proposal"] = None
        add_chat_message(
            user_id, "assistant",
            f"✅ Done! Your new plan **{plan['plan_name']}** is live on the Workout Plan page. "
            f"Let's get after it! 🔥",
        )
        st.session_state["chat_plan_ready"] = True
        st.rerun()


def render_coach_chat() -> None:
    P = pal()
    user_id = st.session_state["user_id"]

    st.markdown(
        f'<div style="background:{P["card_hero"]};border:1px solid {P["accent_border"]};border-radius:20px;'
        f'padding:1.5rem 2rem;margin-bottom:1rem;">{eyebrow("Coach chat")}'
        f'<div style="font-family:Space Grotesk,sans-serif;font-size:1.9rem;font-weight:800;color:{P["text"]};">'
        f'Talk to Movexa Coach 💬</div><div style="color:{P["muted"]};">Training, form, nutrition, recovery or '
        f'motivation — ask anything. Want your plan changed? Just say so and I\'ll rebuild it.</div></div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        if st.button("🧹 Clear chat", use_container_width=True):
            clear_chat(user_id)
            st.session_state["chat_proposal"] = None
            st.rerun()

    if get_groq_client() is None:
        st.warning("Coach chat needs a GROQ_API_KEY in your .env file.")
        return

    messages = get_chat_messages(user_id)
    if not messages:
        with st.chat_message("assistant", avatar=AVATARS["assistant"]):
            st.markdown(f"Hey {st.session_state.get('username', 'athlete')}! 👋 I'm Movexa Coach. I know your profile "
                        "and your current plan — what's on your mind today?")
        st.caption("Try one of these:")
        cols = st.columns(2)
        for i, s in enumerate(SUGGESTIONS):
            if cols[i % 2].button(s, key=f"suggest_{i}", use_container_width=True):
                with st.spinner("Movexa Coach is thinking…"):
                    _send(user_id, s)
                st.rerun()

    for m in messages:
        with st.chat_message(m["role"], avatar=AVATARS.get(m["role"])):
            st.markdown(m["content"])

    if st.session_state.get("chat_plan_ready"):
        if st.button("📋 View my new plan", type="primary"):
            st.session_state["chat_plan_ready"] = False
            st.switch_page(PAGES["plan"])

    proposal = st.session_state.get("chat_proposal")
    if proposal:
        _proposal_card(user_id, proposal)

    if prompt := st.chat_input("Ask Movexa Coach anything about your training…"):
        with st.chat_message("user", avatar=AVATARS["user"]):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar=AVATARS["assistant"]):
            with st.spinner("Movexa Coach is thinking…"):
                _send(user_id, prompt)
        st.rerun()

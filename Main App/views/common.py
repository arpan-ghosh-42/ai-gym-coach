import os
import re

import streamlit as st
from groq import Groq

# Filled by main.py on every run so views can st.switch_page() between each other.
PAGES: dict = {}


def pal():
    d = st.session_state.get("theme_mode", "dark") == "dark"
    return {
        "dark": d,
        "text": "#FFFFFF" if d else "#0F172A",
        "muted": "#94A3B8" if d else "#475569",
        "faint": "#64748B" if d else "#64748B",
        "accent": "#00E5FF" if d else "#0284C7",
        "warm": "#FF9100" if d else "#EA580C",
        "card": "linear-gradient(145deg,rgba(20,28,44,0.85),rgba(13,18,30,0.95))" if d else "linear-gradient(145deg,#FFFFFF,#F1F5F9)",
        "card_hero": "linear-gradient(135deg,rgba(22,32,53,0.9),rgba(14,20,34,0.95))" if d else "linear-gradient(135deg,#FFFFFF,#EEF6FB)",
        "card_active": "linear-gradient(145deg,rgba(0,229,255,0.12),rgba(14,28,52,0.95))" if d else "linear-gradient(145deg,rgba(2,132,199,0.08),#FFFFFF)",
        "border": "rgba(255,255,255,0.08)" if d else "rgba(148,163,184,0.45)",
        "accent_border": "rgba(0,229,255,0.25)" if d else "rgba(2,132,199,0.35)",
        "active_border": "#00E5FF" if d else "#0284C7",
        "chip_bg": "rgba(255,255,255,0.05)" if d else "rgba(15,23,42,0.05)",
        "chip_border": "rgba(255,255,255,0.1)" if d else "rgba(15,23,42,0.12)",
        "accent_bg": "rgba(0,229,255,0.1)" if d else "rgba(2,132,199,0.08)",
        "shadow": "0 18px 45px rgba(0,0,0,0.4)" if d else "0 12px 32px rgba(15,23,42,0.10)",
        "nav_bg": "rgba(14,20,34,0.8)" if d else "rgba(255,255,255,0.95)",
        "title_style": "background:linear-gradient(90deg,#FFFFFF,#00E5FF);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;" if d else "color:#0F172A;-webkit-text-fill-color:#0F172A;",
        "num_style": "background:linear-gradient(180deg,#FFFFFF 20%,#00E5FF 100%);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;" if d else "color:#0284C7;-webkit-text-fill-color:#0284C7;",
        "good": "#00E676" if d else "#059669",
    }


def chip(text: str, accent: bool = False) -> str:
    P = pal()
    bg, border, color = (P["accent_bg"], P["accent_border"], P["accent"]) if accent else (P["chip_bg"], P["chip_border"], P["text"])
    return (f'<span style="display:inline-block;background:{bg};border:1px solid {border};border-radius:30px;'
            f'padding:4px 13px;font-size:0.82rem;font-weight:600;color:{color};margin:0 6px 6px 0;">{text}</span>')


def eyebrow(text: str) -> str:
    P = pal()
    return (f'<div style="display:inline-flex;align-items:center;gap:6px;padding:3px 12px;background:{P["accent_bg"]};'
            f'border:1px solid {P["accent_border"]};border-radius:20px;color:{P["accent"]};font-size:0.72rem;'
            f'font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:10px;">{text}</div>')


def section_title(text: str) -> None:
    P = pal()
    st.markdown(
        f'<div style="font-family:Space Grotesk,sans-serif;font-size:1.4rem;font-weight:800;letter-spacing:-0.02em;'
        f'margin:1.4rem 0 0.75rem;color:{P["text"]};">{text}</div>',
        unsafe_allow_html=True,
    )


def option_card(icon: str, title: str, desc: str, selected: bool) -> str:
    P = pal()
    bg = P["card_active"] if selected else P["card"]
    border = f'2px solid {P["active_border"]}' if selected else f'1px solid {P["border"]}'
    glow = "box-shadow:0 0 22px rgba(0,229,255,0.25);" if selected and P["dark"] else ""
    return (f'<div style="background:{bg};border:{border};border-radius:16px;padding:1.3rem 1.2rem;{glow}'
            f'min-height:150px;box-sizing:border-box;margin-bottom:8px;">'
            f'<div style="font-size:2rem;line-height:1;margin-bottom:10px;">{icon}</div>'
            f'<div style="font-family:Space Grotesk,sans-serif;font-weight:700;font-size:1.05rem;color:{P["text"]};margin-bottom:4px;">{title}</div>'
            f'<div style="font-size:0.84rem;color:{P["muted"]};line-height:1.45;">{desc}</div></div>')


@st.cache_resource(show_spinner=False)
def _groq_client(api_key: str):
    return Groq(api_key=api_key)


def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        try:
            api_key = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            api_key = ""
    if not api_key:
        return None
    try:
        return _groq_client(api_key)
    except Exception:
        return None


def pose_coach_match(exercise_name: str) -> str | None:
    """Maps a plan exercise to a movement the live Pose Coach can track, if any."""
    from detectors.registry import match_exercise
    return match_exercise(exercise_name)


def target_reps(reps: str, timed: bool = False) -> int:
    """Turns a prescription like "8-12" (or "30-60 s" for holds) into one per-set target: the midpoint."""
    nums = [int(n) for n in re.findall(r"\d+", reps or "")][:2]
    is_timed = re.search(r"\d\s*(s|sec|seconds?)\b", reps or "") is not None
    if not nums or is_timed != timed:
        return 30 if timed else 10
    return max(1, min(300 if timed else 50, round(sum(nums) / len(nums))))

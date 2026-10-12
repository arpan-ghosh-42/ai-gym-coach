import os

import streamlit as st
from dotenv import load_dotenv
load_dotenv()
from services.auth.login_wall import render_login_wall
from services.persistence.exercise_repository import init_db
from services.persistence.profile_repository import get_profile, init_profile_tables
from services.ui.style_loader import inject_theme, inject_local_font
from views.coach_chat import render_coach_chat
from views.common import PAGES, pal
from views.onboarding import render_onboarding
from views.pose_coach import render_pose_coach
from views.profile import render_profile
from views.workout_plan import render_workout_plan

#..\.venv\Scripts\python.exe -m streamlit run main.py

LANDING_URL = os.getenv("LANDING_URL", "http://localhost:3000")


def render_top_bar(username: str) -> None:
    P = pal()
    workout_started = st.session_state.get("workout_started", False)
    status_label = "● LIVE TRACKING ACTIVE" if workout_started else "● AI ENGINE READY"
    status_color = P["good"] if workout_started else P["accent"]
    status_bg = "rgba(0,230,118,0.1)" if workout_started else "rgba(0,229,255,0.1)"
    status_border = "rgba(0,230,118,0.3)" if workout_started else "rgba(0,229,255,0.3)"

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
        padding:0.85rem 1.5rem;background:{P['nav_bg']};
        border:1px solid {P['border']};border-radius:16px;
        backdrop-filter:blur(14px);margin-bottom:1.5rem;
        box-shadow:0 8px 28px rgba(15,23,42,{0.3 if P['dark'] else 0.08});">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:1.5rem;">🏋️</span>
            <div>
                <span style="font-size:1.25rem;font-weight:800;letter-spacing:-0.02em;
                    {P['title_style']}">
                    CoachX AI COACH
                </span>
                <span style="font-size:0.7rem;color:#64748B;margin-left:8px;font-weight:600;letter-spacing:0.05em;">
                    PLAN · TRAIN · PERFECT
                </span>
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="background:{status_bg};border:1px solid {status_border};
                border-radius:20px;padding:4px 12px;color:{status_color};
                font-size:0.75rem;font-weight:700;letter-spacing:0.08em;">
                {status_label}
            </div>
            <div style="background:{P['chip_bg']};border:1px solid {P['chip_border']};
                border-radius:24px;padding:5px 14px;font-size:0.85rem;
                color:{P['text']};font-weight:600;">
                👤 {username}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar(username: str, profile: dict) -> None:
    P = pal()
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:1rem 1.1rem;background:{P['card']};
            border:1px solid {P['border']};border-radius:12px;margin-bottom:1.2rem;">
            <div style="font-size:0.7rem;text-transform:uppercase;color:{P['accent']};font-weight:700;letter-spacing:0.08em;margin-bottom:3px;">
                Active Profile
            </div>
            <div style="font-size:1.2rem;font-weight:700;color:{P['text']};">{username}</div>
            <div style="font-size:0.8rem;color:{P['muted']};margin-top:4px;">
                🎯 {profile['goal']} · 📍 {profile['location']} · 🗓️ {profile['days_per_week']}d/wk
            </div>
        </div>
        """, unsafe_allow_html=True)

        theme_mode = st.session_state.get("theme_mode", "dark")
        btn_theme = "☀️ Switch to Light" if theme_mode == "dark" else "🌙 Switch to Dark"
        if st.button(btn_theme, key="sb_theme_toggle", use_container_width=True):
            st.session_state["theme_mode"] = "light" if theme_mode == "dark" else "dark"
            st.rerun()

        st.link_button("🌐 CoachX Home", LANDING_URL, use_container_width=True)
        if st.button("🚪 Switch Athlete", use_container_width=True):
            for key in ("user_id", "username", "workout_started", "onb", "onb_step", "coach_feedback", "audio_to_play",
                        "chat_proposal", "chat_plan_ready", "live_metrics"):
                st.session_state.pop(key, None)
            st.rerun()
        st.divider()


def main():
    st.set_page_config(
        page_icon="🏋️",
        page_title="CoachX // AI GYM Coach",
        initial_sidebar_state="expanded",
        layout="wide"
    )

    if "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = "dark"
    inject_theme(st.session_state["theme_mode"])
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")
    init_db()
    init_profile_tables()

    # 1) Name login  2) First-time onboarding  3) The app (Workout Plan / Pose Coach / Profile)
    if st.session_state.get("user_id") is None:
        st.navigation([st.Page(render_login_wall, title="Sign in", icon="🔐")], position="hidden").run()
        return

    profile = get_profile(st.session_state["user_id"])
    if profile is None:
        st.navigation([st.Page(render_onboarding, title="Get started", icon="🚀")], position="hidden").run()
        return

    PAGES["plan"] = st.Page(render_workout_plan, title="Workout Plan", icon="📋", url_path="plan", default=True)
    PAGES["pose"] = st.Page(render_pose_coach, title="Pose Coach", icon="🎥", url_path="pose-coach")
    PAGES["chat"] = st.Page(render_coach_chat, title="Coach Chat", icon="💬", url_path="coach-chat")
    PAGES["profile"] = st.Page(render_profile, title="My Profile", icon="👤", url_path="profile")
    page = st.navigation([PAGES["plan"], PAGES["pose"], PAGES["chat"], PAGES["profile"]], position="top")

    username = st.session_state.get("username", "Athlete")
    render_top_bar(username)
    render_sidebar(username, profile)
    page.run()


if __name__ == "__main__":
    main()

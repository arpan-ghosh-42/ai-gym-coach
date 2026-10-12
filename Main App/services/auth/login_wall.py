import streamlit as st
from services.persistence.exercise_repository import get_or_create_user
from services.ui.style_loader import render_coachx_logo, inject_theme


def render_login_wall():
    if st.session_state.get("user_id") is not None:
        return True

    theme_mode = st.session_state.get("theme_mode", "dark")
    inject_theme(theme_mode)

    # Top bar on login wall with Theme Switcher
    top_col1, top_col2 = st.columns([8, 2])
    with top_col1:
        st.markdown(render_coachx_logo(size=36, mode=theme_mode, show_sub=False), unsafe_allow_html=True)
    with top_col2:
        btn_label = "☀️ Light" if theme_mode == "dark" else "🌙 Dark"
        if st.button(btn_label, key="login_theme_toggle", use_container_width=True):
            st.session_state["theme_mode"] = "light" if theme_mode == "dark" else "dark"
            st.rerun()

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 8, 1])
    with center_col:
        heading_gradient = (
            "linear-gradient(135deg, #FFFFFF 30%, #00E5FF 70%, #FF9100 100%)"
            if theme_mode == "dark"
            else "linear-gradient(135deg, #0F172A 30%, #0284C7 70%, #EA580C 100%)"
        )
        heading_style = (
            f"background:{heading_gradient};-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;"
            if theme_mode == "dark"
            else "color:#0F172A;-webkit-text-fill-color:#0F172A;"
        )
        tag_bg = "rgba(0,229,255,0.12)" if theme_mode == "dark" else "rgba(2,132,199,0.10)"
        tag_border = "rgba(0,229,255,0.3)" if theme_mode == "dark" else "rgba(2,132,199,0.35)"
        tag_color = "#00E5FF" if theme_mode == "dark" else "#0284C7"
        sub_text_color = "rgba(255,255,255,0.85)" if theme_mode == "dark" else "#334155"

        st.markdown(
            f"""<div style="text-align:center;margin-top:0.5rem;margin-bottom:2rem;">
<div style="display:inline-flex;align-items:center;gap:8px;padding:6px 16px;background:{tag_bg};border:1px solid {tag_border};border-radius:30px;color:{tag_color};font-size:0.8rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1.2rem;">⚡ COACHX // YOUR AI PERSONAL TRAINER</div>
<h1 style="font-size:3rem;font-weight:800;line-height:1.15;margin-bottom:0.8rem;{heading_style}">Train Smarter with CoachX</h1>
<p style="font-size:1.1rem;max-width:660px;margin:0 auto;line-height:1.6;color:{sub_text_color};">A workout split built around your body, goal and schedule — plus a camera-based coach that counts your reps and corrects your form in real time.</p>
</div>""",
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        cards = [
            ("📋", "AI Workout Planner", "Personalised gym or home splits for bulking, cutting or maintenance, grounded in exercise-science research."),
            ("🎥", "Live Pose Coach", "33-landmark pose tracking checks your squats, push-ups, curls, presses and lunges as you move."),
            ("🎙️", "Voice Cues & Tracking", "Spoken form corrections, automatic rep counting and session history saved to your profile."),
        ]
        card_bg = "linear-gradient(145deg,rgba(22,30,48,0.75),rgba(15,21,35,0.85))" if theme_mode == "dark" else "linear-gradient(145deg,#FFFFFF,#F8FAFC)"
        card_border = "rgba(255,255,255,0.08)" if theme_mode == "dark" else "rgba(226,232,240,0.95)"

        for col, (icon, title, desc) in zip([c1, c2, c3], cards):
            with col:
                st.markdown(
                    f"""
                    <div style="background:{card_bg};border:1px solid {card_border};
                        border-radius:16px;padding:1.4rem;text-align:center;height:100%;
                        box-shadow:0 6px 20px rgba(0,0,0,0.06);">
                        <div style="font-size:2.2rem;margin-bottom:10px;">{icon}</div>
                        <div style="font-weight:700;font-size:1.05rem;margin-bottom:6px;">{title}</div>
                        <div style="font-size:0.84rem;line-height:1.55;opacity:0.8;">{desc}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            st.markdown(
                """
                <div style="font-weight:700;font-size:1.1rem;margin-bottom:4px;">👤 Athlete Profile</div>
                <div style="font-size:0.85rem;margin-bottom:14px;opacity:0.8;">Enter your name — new athletes get a quick 5-step setup, returning athletes jump straight to their plan.</div>
                """,
                unsafe_allow_html=True,
            )
            username = st.text_input("Athlete Name", placeholder="e.g. arpan, alex, champion", label_visibility="collapsed")
            submit_button = st.form_submit_button("🔥 Continue", use_container_width=True)

        if submit_button:
            if not username or not username.strip():
                st.error("⚠️ Please enter a valid athlete name to continue.")
                return False
            user = get_or_create_user(username.strip())
            st.session_state["user_id"] = user["id"]
            st.session_state["username"] = user["username"]
            st.rerun()

        st.markdown(
            """
            <div style="margin-top:2rem;padding:1rem 1.4rem;background:rgba(0,229,255,0.05);
                border:1px dashed rgba(0,229,255,0.3);border-radius:12px;
                display:flex;align-items:center;gap:12px;font-size:0.85rem;">
                <span style="font-size:1.4rem;">💡</span>
                <div><strong>Optimal Camera Setup:</strong> Place your device 6–8 feet away at waist height with good front lighting so your entire body remains visible during sets.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return False

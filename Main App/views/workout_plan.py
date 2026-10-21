import html
from datetime import datetime

import streamlit as st

from services.persistence.profile_repository import get_latest_plan, get_profile, save_plan, save_profile
from services.planner.generator import generate_plan
from services.planner.profile import bmi, bmi_category
from views.common import PAGES, chip, eyebrow, get_groq_client, pal, pose_coach_match, section_title, target_reps


def build_and_save_plan(user_id: int, profile: dict) -> dict:
    """Saves the profile, runs the RAG planner with live progress, and stores the resulting plan."""
    with st.status("Building your personalised plan…", expanded=True) as status:
        save_profile(user_id, profile)
        client = get_groq_client()
        plan = generate_plan(profile, client)
        save_plan(user_id, plan, profile)
        status.update(label="Your plan is ready!", state="complete", expanded=False)
    st.session_state["plan_toast"] = "✅ New workout plan generated!"
    return plan


def _fmt_rest(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}" if m else f"{s}s"


def _start_pose_coach(exercise: str, sets: int, reps: str) -> None:
    from detectors.registry import is_hold
    st.session_state["plan_exercise"] = exercise
    st.session_state["plan_sets"] = int(sets)
    st.session_state["plan_reps"] = target_reps(reps, timed=is_hold(exercise))
    st.session_state["pose_group"] = None
    st.switch_page(PAGES["pose"])


ROW_COLS = [0.35, 4.2, 0.8, 1.1, 0.9, 1.7]


def _cell(content: str, align: str = "left", color: str | None = None, weight: int = 700) -> str:
    P = pal()
    return (f'<div style="text-align:{align};font-weight:{weight};color:{color or P["text"]};'
            f'padding-top:6px;font-size:0.95rem;">{content}</div>')


def _exercise_rows(day: dict, day_idx: int) -> None:
    P = pal()
    header = st.columns(ROW_COLS, vertical_alignment="center")
    for col, (label, align) in zip(header, [("#", "left"), ("Exercise", "left"), ("Sets", "center"),
                                            ("Reps", "center"), ("Rest", "center"), ("Form check", "center")]):
        col.markdown(f'<div style="text-align:{align};font-family:Space Grotesk,sans-serif;font-size:0.78rem;'
                     f'font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{P["accent"]};">{label}</div>',
                     unsafe_allow_html=True)

    for i, ex in enumerate(day["exercises"], start=1):
        st.markdown(f'<div style="border-top:1px solid {P["border"]};margin:2px 0 4px;"></div>', unsafe_allow_html=True)
        c = st.columns(ROW_COLS, vertical_alignment="center")
        c[0].markdown(_cell(str(i), color=P["faint"], weight=600), unsafe_allow_html=True)
        c[1].markdown(
            f'<div style="font-weight:700;color:{P["text"]};font-size:0.98rem;">{html.escape(ex["name"])}</div>'
            f'<div style="font-size:0.8rem;color:{P["muted"]};">{html.escape(ex.get("notes", ""))}</div>',
            unsafe_allow_html=True,
        )
        c[2].markdown(_cell(str(ex["sets"]), "center"), unsafe_allow_html=True)
        c[3].markdown(_cell(html.escape(ex["reps"]), "center", P["accent"]), unsafe_allow_html=True)
        c[4].markdown(_cell(_fmt_rest(ex["rest_seconds"]), "center", weight=500), unsafe_allow_html=True)
        tracked = pose_coach_match(ex["name"])
        with c[5]:
            if tracked:
                if st.button("🎥 Live track", key=f"track_{day_idx}_{i}", use_container_width=True,
                             help=f"Open the Pose Coach for {tracked}"):
                    _start_pose_coach(tracked, ex["sets"], ex["reps"])
            else:
                st.markdown(f'<div style="text-align:center;font-size:0.75rem;color:{P["faint"]};">'
                            f'Not camera-trackable</div>', unsafe_allow_html=True)


def _week_strip(schedule: list) -> None:
    P = pal()
    cards = []
    for day in schedule:
        rest = day["is_rest"]
        bg = P["chip_bg"] if rest else P["card_active"]
        border = P["border"] if rest else P["accent_border"]
        sub = "Recovery" if rest else f'{len(day["exercises"])} exercises · ~{day["duration_min"]} min'
        cards.append(
            f'<div style="flex:1;min-width:120px;background:{bg};border:1px solid {border};border-radius:14px;padding:0.8rem;">'
            f'<div style="font-size:0.7rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;'
            f'color:{P["faint"] if rest else P["accent"]};">{day["weekday"][:3]}</div>'
            f'<div style="font-weight:700;font-size:0.9rem;color:{P["muted"] if rest else P["text"]};margin:3px 0;">'
            f'{"😴 Rest" if rest else html.escape(day["focus"])}</div>'
            f'<div style="font-size:0.72rem;color:{P["muted"]};">{sub}</div></div>'
        )
    st.markdown(f'<div style="display:flex;gap:8px;flex-wrap:wrap;">{"".join(cards)}</div>', unsafe_allow_html=True)


def _day_detail(day: dict, idx: int) -> None:
    P = pal()
    if day["is_rest"]:
        st.markdown(
            f'<div style="background:{P["chip_bg"]};border:1px dashed {P["chip_border"]};border-radius:14px;'
            f'padding:1.6rem;color:{P["muted"]};"><div style="font-size:1.05rem;font-weight:700;color:{P["text"]};'
            f'margin-bottom:6px;">😴 Rest & Recovery</div>Muscle is built while you recover. Go for a 20-40 min walk, '
            f'stretch or do light mobility work, hit your protein target and aim for 7-9 hours of sleep.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;margin-bottom:0.6rem;">'
        f'<div style="font-family:Space Grotesk,sans-serif;font-size:1.25rem;font-weight:800;color:{P["text"]};">'
        f'{html.escape(day["focus"])}</div>'
        f'<div>{chip(f"⏱️ ~{day["duration_min"]} min")}{chip(f"{sum(e["sets"] for e in day["exercises"])} working sets")}</div></div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        _exercise_rows(day, idx)


def render_workout_plan() -> None:
    P = pal()
    user_id = st.session_state["user_id"]
    profile = get_profile(user_id)
    plan = get_latest_plan(user_id)

    if toast := st.session_state.pop("plan_toast", None):
        st.toast(toast)

    if plan is None:
        st.info("You don't have a plan yet — let's build one.")
        if st.button("⚡ Generate my plan", type="primary"):
            build_and_save_plan(user_id, profile)
            st.rerun()
        return

    # ── HERO ─────────────────────────────────────────────
    engine_label = "🧠 Groq AI · RAG-grounded" if plan.get("engine") == "groq-rag" else "🧮 CoachX rule engine"
    created = plan.get("created_at", "")
    try:
        created = datetime.fromisoformat(created).strftime("%d %b %Y")
    except (TypeError, ValueError):
        pass
    loc = profile["location"] + (" · " + ", ".join(profile["equipment"]) if profile["location"] == "Home" and profile["equipment"] else "")
    chips = "".join([
        chip(plan.get("split_type") or "Custom split", accent=True), chip(f"🎯 {profile['goal']}"),
        chip(f"📍 {loc}"), chip(f"🗓️ {profile['days_per_week']} days / week"), chip(f"📶 {profile['experience']}"),
    ])
    st.markdown(
        f'<div style="background:{P["card_hero"]};border:1px solid {P["accent_border"]};border-radius:20px;'
        f'padding:1.8rem 2rem;box-shadow:{P["shadow"]};margin-bottom:1rem;">'
        f'{eyebrow("Your AI workout plan")}'
        f'<div style="font-family:Space Grotesk,sans-serif;font-size:2rem;font-weight:800;color:{P["text"]};margin-bottom:6px;">'
        f'{html.escape(plan["plan_name"])}</div>'
        f'<div style="margin-bottom:10px;">{chips}</div>'
        f'<div style="color:{P["muted"]};font-size:0.98rem;line-height:1.6;max-width:900px;">{html.escape(plan.get("summary", ""))}</div>'
        f'<div style="font-size:0.75rem;color:{P["faint"]};margin-top:12px;">{engine_label} · generated {created}</div></div>',
        unsafe_allow_html=True,
    )
    a1, a2, _ = st.columns([1.3, 1.3, 5])
    with a1:
        if st.button("✏️ Edit my details", use_container_width=True):
            st.switch_page(PAGES["profile"])
    with a2:
        if st.button("🔄 Regenerate plan", use_container_width=True):
            build_and_save_plan(user_id, profile)
            st.rerun()
    if plan.get("engine") != "groq-rag":
        reason = "no GROQ_API_KEY configured" if not get_groq_client() else "the AI planner could not be reached"
        st.caption(f"ℹ️ Built with the offline rule engine because {reason}. Click *Regenerate plan* to retry with AI.")

    # ── DAILY TARGETS ────────────────────────────────────
    n = plan["nutrition"]
    b = bmi(profile)
    section_title("🍽️ Daily Targets")
    m = st.columns(5)
    m[0].metric("Calories", f"{n['calories']:,} kcal", help=f"Maintenance ≈ {n['tdee']:,} kcal (Mifflin-St Jeor)")
    m[1].metric("Protein", f"{n['protein_g']} g")
    m[2].metric("Carbs", f"{n['carbs_g']} g")
    m[3].metric("Fat", f"{n['fat_g']} g")
    m[4].metric("BMI", f"{b}", help=bmi_category(b))
    st.caption(f"⚖️ Target rate of change: **{n['weekly_change']}** · 💧 Water: ~{n['water_l']} L/day")

    # ── WEEK ─────────────────────────────────────────────
    section_title("🗓️ Your Week")
    schedule = plan["weekly_schedule"]
    _week_strip(schedule)
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    tabs = st.tabs([f"{d['weekday'][:3]} · {'Rest' if d['is_rest'] else d['focus'].split(' —')[0]}" for d in schedule])
    for idx, (tab, day) in enumerate(zip(tabs, schedule)):
        with tab:
            _day_detail(day, idx)

    # ── GUIDANCE ─────────────────────────────────────────
    section_title("📘 Coaching Notes")
    g1, g2 = st.columns(2)
    with g1:
        with st.expander("📈 Progression strategy", expanded=True):
            st.write(plan.get("progression") or "—")
        with st.expander("🔥 Warm-up"):
            st.write(plan.get("warmup") or "—")
        with st.expander("🏃 Cardio"):
            st.write(plan.get("cardio") or "—")
    with g2:
        with st.expander("🥗 Nutrition tips", expanded=True):
            for tip in plan.get("nutrition_tips") or []:
                st.markdown(f"- {tip}")
        with st.expander("🛡️ Safety"):
            for note in plan.get("safety_notes") or []:
                st.markdown(f"- {note}")
            st.caption("CoachX provides general fitness guidance, not medical advice. "
                       "Consult a professional if you have health conditions or injuries.")

import streamlit as st

from services.planner.profile import (
    DEFAULT_PROFILE, EXPERIENCE_LEVELS, GENDERS, GOAL_DETAILS, HOME_EQUIPMENT, LOCATION_DETAILS,
    MAX_DAYS, MIN_DAYS, bmi, bmi_category,
)
from services.ui.style_loader import render_coachx_logo
from views.common import eyebrow, option_card, pal
from views.workout_plan import build_and_save_plan

STEPS = ["Body", "Training", "Goal", "Schedule", "About you"]

DAYS_HINTS = {
    3: "Full-body sessions — ideal for beginners and busy weeks.",
    4: "Upper / Lower split — the sweet spot for most people.",
    5: "Upper / Lower + Push / Pull / Legs — more volume for faster progress.",
    6: "Push / Pull / Legs twice — high volume for experienced lifters.",
}


def _data() -> dict:
    if "onb" not in st.session_state:
        st.session_state.onb = {**DEFAULT_PROFILE, "location": None, "goal": None}
    return st.session_state.onb


def _go(step: int) -> None:
    st.session_state.onb_step = max(0, min(len(STEPS) - 1, step))
    st.rerun()


def _stepper(step: int) -> None:
    P = pal()
    items = []
    for i, name in enumerate(STEPS):
        done, current = i < step, i == step
        dot_bg = P["accent"] if (done or current) else P["chip_bg"]
        dot_color = "#030710" if (done or current) else P["muted"]
        label_color = P["text"] if current else P["muted"]
        items.append(
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex:1;">'
            f'<div style="width:30px;height:30px;border-radius:50%;background:{dot_bg};border:1px solid {P["accent_border"]};'
            f'display:flex;align-items:center;justify-content:center;font-weight:800;font-size:0.8rem;color:{dot_color};">'
            f'{"✓" if done else i + 1}</div>'
            f'<div style="font-size:0.75rem;font-weight:{700 if current else 500};color:{label_color};">{name}</div></div>'
        )
    st.markdown(f'<div style="display:flex;gap:4px;margin:0.5rem 0 1.2rem;">{"".join(items)}</div>', unsafe_allow_html=True)
    st.progress((step + 1) / len(STEPS))


def _heading(title: str, subtitle: str) -> None:
    P = pal()
    st.markdown(
        f'<div style="margin:1.4rem 0 1rem;"><div style="font-family:Space Grotesk,sans-serif;font-size:1.7rem;'
        f'font-weight:800;color:{P["text"]};">{title}</div>'
        f'<div style="color:{P["muted"]};font-size:0.95rem;">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )


def _choice_grid(options: dict, current, key: str):
    """Renders selectable cards; returns the newly clicked option or None."""
    cols = st.columns(len(options))
    clicked = None
    for col, (value, meta) in zip(cols, options.items()):
        with col:
            selected = current == value
            st.markdown(option_card(meta["icon"], meta["title"], meta["desc"], selected), unsafe_allow_html=True)
            if st.button("✓ Selected" if selected else "Select", key=f"{key}_{value}",
                         use_container_width=True, type="primary" if selected else "secondary"):
                clicked = value
    return clicked


def _nav(step: int, can_continue: bool = True, error: str = "") -> bool:
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    back_col, _, next_col = st.columns([1, 2, 1])
    with back_col:
        if step > 0 and st.button("← Back", use_container_width=True, key=f"onb_back_{step}"):
            _go(step - 1)
    with next_col:
        pressed = st.button("Continue →", type="primary", use_container_width=True, key=f"onb_next_{step}")
    if pressed and not can_continue:
        st.warning(error)
        return False
    return pressed


def _step_body(d: dict) -> None:
    _heading("Let's start with your body metrics", "Used to estimate your calorie and protein targets.")
    c1, c2, c3 = st.columns(3)
    with c1:
        weight = st.number_input("Weight (kg)", min_value=30.0, max_value=250.0, value=float(d["weight_kg"]), step=0.5)
    with c2:
        height = st.number_input("Height (cm)", min_value=120.0, max_value=230.0, value=float(d["height_cm"]), step=0.5)
    with c3:
        age = st.number_input("Age", min_value=14, max_value=90, value=int(d["age"]), step=1)

    value = bmi({"weight_kg": weight, "height_cm": height})
    P = pal()
    st.markdown(
        f'<div style="margin-top:0.6rem;font-size:0.9rem;color:{P["muted"]};">Your BMI: '
        f'<strong style="color:{P["accent"]};">{value}</strong> · {bmi_category(value)} '
        f'<span style="opacity:0.7;">(BMI doesn\'t distinguish muscle from fat — it\'s just a starting point.)</span></div>',
        unsafe_allow_html=True,
    )
    if _nav(0):
        d.update(weight_kg=float(weight), height_cm=float(height), age=int(age))
        _go(1)


def _step_training(d: dict) -> None:
    _heading("Where will you train?", "Your exercises are chosen around the equipment you actually have.")
    clicked = _choice_grid(LOCATION_DETAILS, d["location"], "loc")
    if clicked:
        d["location"] = clicked
        st.rerun()

    if d["location"] == "Home":
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
        st.markdown("**What equipment do you have at home?** *(leave all unticked for bodyweight-only)*")
        cols = st.columns(len(HOME_EQUIPMENT))
        chosen = []
        for col, item in zip(cols, HOME_EQUIPMENT):
            with col:
                if st.checkbox(item, value=item in d["equipment"], key=f"onb_eq_{item}"):
                    chosen.append(item)
        d["equipment"] = chosen

    if _nav(1, can_continue=d["location"] is not None, error="Please choose Gym or Home to continue."):
        if d["location"] == "Gym":
            d["equipment"] = []
        _go(2)


def _step_goal(d: dict) -> None:
    _heading("What's your goal?", "This sets your training volume, rep ranges and nutrition targets.")
    clicked = _choice_grid(GOAL_DETAILS, d["goal"], "goal")
    if clicked:
        d["goal"] = clicked
        st.rerun()
    if _nav(2, can_continue=d["goal"] is not None, error="Please pick a goal to continue."):
        _go(3)


def _step_schedule(d: dict) -> None:
    _heading("How often can you train?", f"Minimum {MIN_DAYS} days per week so every muscle gets trained at least twice.")
    days = st.slider("Training days per week", min_value=MIN_DAYS, max_value=MAX_DAYS, value=int(d["days_per_week"]))
    st.caption(f"🗓️ {DAYS_HINTS[days]}")
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    experience = st.radio(
        "Training experience", EXPERIENCE_LEVELS, index=EXPERIENCE_LEVELS.index(d["experience"]), horizontal=True,
        captions=["< 1 year", "1-3 years", "3+ years"],
    )
    if _nav(3):
        d.update(days_per_week=int(days), experience=experience)
        _go(4)


def _step_about(d: dict) -> None:
    _heading("A little about you", "Helps us personalise calorie targets and exercise selection.")
    gender = st.radio("Gender", GENDERS, index=GENDERS.index(d["gender"]), horizontal=True,
                      format_func=lambda g: "Other / Prefer not to say" if g == "Other" else g)
    notes = st.text_area(
        "Injuries, limitations or preferences (optional)", value=d["notes"], max_chars=300,
        placeholder="e.g. mild lower-back pain, want extra glute work, no jumping",
    )
    d.update(gender=gender, notes=notes.strip())

    P = pal()
    where = d["location"] + (f" ({', '.join(d['equipment'])})" if d["location"] == "Home" and d["equipment"] else
                             " (bodyweight)" if d["location"] == "Home" else "")
    rows = [
        ("Body", f"{d['weight_kg']} kg · {d['height_cm']} cm · {d['age']} yrs"),
        ("Training", where),
        ("Goal", d["goal"]),
        ("Schedule", f"{d['days_per_week']} days / week · {d['experience']}"),
    ]
    summary = "".join(
        f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid {P["border"]};">'
        f'<span style="color:{P["muted"]};font-size:0.85rem;">{k}</span>'
        f'<span style="font-weight:600;font-size:0.9rem;color:{P["text"]};">{v}</span></div>'
        for k, v in rows
    )
    st.markdown(f'<div style="background:{P["card"]};border:1px solid {P["border"]};border-radius:14px;'
                f'padding:0.8rem 1.2rem;margin-top:1rem;">{summary}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    back_col, _, gen_col = st.columns([1, 1.2, 1.8])
    with back_col:
        if st.button("← Back", use_container_width=True, key="onb_back_4"):
            _go(3)
    with gen_col:
        generate = st.button("⚡ Generate my AI workout plan", type="primary", use_container_width=True)
    if generate:
        profile = {k: d[k] for k in DEFAULT_PROFILE}
        build_and_save_plan(st.session_state["user_id"], profile)
        for key in ("onb", "onb_step"):
            st.session_state.pop(key, None)
        st.rerun()


def render_onboarding() -> None:
    P = pal()
    d = _data()
    step = st.session_state.get("onb_step", 0)

    st.markdown(render_coachx_logo(size=36, mode=st.session_state.get("theme_mode", "dark"), show_sub=False),
                unsafe_allow_html=True)
    _, center, _ = st.columns([1, 6, 1])
    with center:
        st.markdown(
            f'<div style="text-align:center;margin-top:1rem;">{eyebrow("Step " + str(step + 1) + " of " + str(len(STEPS)))}'
            f'<div style="font-family:Space Grotesk,sans-serif;font-size:2.2rem;font-weight:800;{P["title_style"]}">'
            f'Welcome, {st.session_state.get("username", "Athlete")} 👋</div>'
            f'<div style="color:{P["muted"]};margin-top:4px;">Answer 5 quick questions and CoachX will build a '
            f'research-backed workout split just for you.</div></div>',
            unsafe_allow_html=True,
        )
        _stepper(step)
        [_step_body, _step_training, _step_goal, _step_schedule, _step_about][step](d)

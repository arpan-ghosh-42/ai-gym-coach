import streamlit as st

from services.persistence.profile_repository import get_profile
from services.planner.profile import (
    EXPERIENCE_LEVELS, GENDERS, GOALS, GOAL_DETAILS, HOME_EQUIPMENT, LOCATIONS, LOCATION_DETAILS,
    MAX_DAYS, MIN_DAYS, nutrition_targets,
)
from views.common import PAGES, eyebrow, pal
from views.workout_plan import build_and_save_plan


def render_profile() -> None:
    P = pal()
    user_id = st.session_state["user_id"]
    profile = get_profile(user_id)

    st.markdown(
        f'<div style="background:{P["card_hero"]};border:1px solid {P["accent_border"]};border-radius:20px;'
        f'padding:1.6rem 2rem;margin-bottom:1.2rem;">{eyebrow("Athlete profile")}'
        f'<div style="font-family:Space Grotesk,sans-serif;font-size:1.9rem;font-weight:800;color:{P["text"]};">'
        f'Edit your details</div><div style="color:{P["muted"]};">Changed your weight, goal or schedule? '
        f'Update it here and CoachX will rebuild your workout split to match.</div></div>',
        unsafe_allow_html=True,
    )

    with st.form("profile_form"):
        st.markdown("##### 📏 Body")
        c1, c2, c3 = st.columns(3)
        weight = c1.number_input("Weight (kg)", 30.0, 250.0, float(profile["weight_kg"]), 0.5)
        height = c2.number_input("Height (cm)", 120.0, 230.0, float(profile["height_cm"]), 0.5)
        age = c3.number_input("Age", 14, 90, int(profile["age"]), 1)
        gender = st.radio("Gender", GENDERS, index=GENDERS.index(profile["gender"]), horizontal=True,
                          format_func=lambda g: "Other / Prefer not to say" if g == "Other" else g)

        st.markdown("##### 🏋️ Training")
        t1, t2 = st.columns(2)
        location = t1.radio("Where do you train?", LOCATIONS, index=LOCATIONS.index(profile["location"]), horizontal=True,
                            format_func=lambda v: f'{LOCATION_DETAILS[v]["icon"]} {LOCATION_DETAILS[v]["title"]}')
        goal = t2.radio("Goal", GOALS, index=GOALS.index(profile["goal"]), horizontal=True,
                        format_func=lambda v: f'{GOAL_DETAILS[v]["icon"]} {GOAL_DETAILS[v]["title"]}')
        st.caption("Home equipment (only used for Home workouts — leave unticked for bodyweight-only):")
        eq_cols = st.columns(len(HOME_EQUIPMENT))
        equipment = [item for col, item in zip(eq_cols, HOME_EQUIPMENT)
                     if col.checkbox(item, value=item in profile["equipment"], key=f"pf_eq_{item}")]

        s1, s2 = st.columns(2)
        days = s1.slider("Training days per week", MIN_DAYS, MAX_DAYS, int(profile["days_per_week"]))
        experience = s2.radio("Experience", EXPERIENCE_LEVELS, index=EXPERIENCE_LEVELS.index(profile["experience"]),
                              horizontal=True)
        notes = st.text_area("Injuries, limitations or preferences (optional)", value=profile["notes"], max_chars=300)

        submitted = st.form_submit_button("💾 Save & rebuild my workout plan", use_container_width=True)

    if submitted:
        updated = {
            "weight_kg": float(weight), "height_cm": float(height), "age": int(age), "gender": gender,
            "location": location, "equipment": equipment if location == "Home" else [],
            "goal": goal, "days_per_week": int(days), "experience": experience, "notes": notes.strip(),
        }
        if updated == profile:
            st.info("Nothing changed — your current plan already matches these details.")
            return
        build_and_save_plan(user_id, updated)
        st.switch_page(PAGES["plan"])

    n = nutrition_targets(profile)
    st.caption(f"Current estimate → maintenance ≈ {n['tdee']:,} kcal · target {n['calories']:,} kcal · "
               f"protein {n['protein_g']} g/day")

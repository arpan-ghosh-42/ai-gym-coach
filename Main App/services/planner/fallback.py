"""Rule-based split builder used when the LLM is unavailable or returns invalid output."""

# slot -> (gym exercise, [(home exercise, required equipment or None), ...] in preference order)
SLOTS = {
    "squat": ("Barbell Back Squat", [("Goblet Squat", "Dumbbells"), ("Squats", None)]),
    "squat2": ("Leg Press", [("Bulgarian Split Squat", None)]),
    "hinge": ("Romanian Deadlift", [("Dumbbell Romanian Deadlift", "Dumbbells"), ("Single-Leg Romanian Deadlift", None)]),
    "lunge": ("Lunges", [("Lunges", None)]),
    "glute": ("Barbell Hip Thrust", [("Single-Leg Glute Bridge", None)]),
    "ham_iso": ("Lying Leg Curl", [("Slider Hamstring Curl", None)]),
    "quad_iso": ("Leg Extension", [("Step-Ups", None)]),
    "calf": ("Standing Calf Raise", [("Single-Leg Calf Raise", None)]),
    "h_push": ("Barbell Bench Press", [("Dumbbell Floor Press", "Dumbbells"), ("Push-ups", None)]),
    "incline_push": ("Incline Dumbbell Press", [("Decline Push-ups", None)]),
    "v_push": ("Shoulder Press", [("Shoulder Press", "Dumbbells"), ("Pike Push-ups", None)]),
    "h_pull": ("Barbell Row", [("Single-Arm Dumbbell Row", "Dumbbells"), ("Band Row", "Resistance bands"), ("Inverted Table Row", None)]),
    "row2": ("Seated Cable Row", [("Band Row", "Resistance bands"), ("Inverted Table Row", None)]),
    "v_pull": ("Lat Pulldown", [("Pull-ups", "Pull-up bar"), ("Band Lat Pulldown", "Resistance bands"), ("Towel Door Row", None)]),
    "fly": ("Cable Fly", [("Dumbbell Floor Fly", "Dumbbells"), ("Wide Push-ups", None)]),
    "lateral": ("Dumbbell Lateral Raise", [("Dumbbell Lateral Raise", "Dumbbells"), ("Band Lateral Raise", "Resistance bands"), ("Prone Y-T-W Raises", None)]),
    "rear_delt": ("Face Pull", [("Band Face Pull", "Resistance bands"), ("Prone Y-T-W Raises", None)]),
    "biceps": ("Biceps Curls (Dumbbell)", [("Biceps Curls (Dumbbell)", "Dumbbells"), ("Chin-ups", "Pull-up bar"), ("Band Curl", "Resistance bands"), ("Towel Isometric Curl", None)]),
    "hammer": ("Hammer Curl", [("Hammer Curl", "Dumbbells"), ("Band Curl", "Resistance bands"), ("Towel Isometric Curl", None)]),
    "triceps": ("Cable Triceps Pushdown", [("Overhead Dumbbell Triceps Extension", "Dumbbells"), ("Diamond Push-ups", None)]),
    "dips": ("Weighted Dips", [("Chair Dips", None)]),
    "core": ("Hanging Knee Raise", [("Hanging Knee Raise", "Pull-up bar"), ("Plank", None)]),
    "core2": ("Cable Crunch", [("Dead Bug", None)]),
}
COMPOUND_SLOTS = {"squat", "squat2", "hinge", "lunge", "glute", "h_push", "incline_push", "v_push", "h_pull", "row2", "v_pull", "dips"}

TEMPLATES = {
    3: [
        ("Full Body A", ["squat", "h_push", "h_pull", "hinge", "biceps", "core"]),
        ("Full Body B", ["hinge", "v_push", "v_pull", "lunge", "triceps", "core2"]),
        ("Full Body C", ["squat2", "incline_push", "row2", "lateral", "hammer", "calf"]),
    ],
    4: [
        ("Upper A — Strength", ["h_push", "h_pull", "v_push", "v_pull", "biceps", "triceps"]),
        ("Lower A — Squat Focus", ["squat", "hinge", "lunge", "ham_iso", "calf", "core"]),
        ("Upper B — Hypertrophy", ["incline_push", "row2", "v_pull", "lateral", "hammer", "dips"]),
        ("Lower B — Hinge Focus", ["glute", "squat2", "quad_iso", "ham_iso", "calf", "core2"]),
    ],
    5: [
        ("Upper", ["h_push", "h_pull", "v_push", "v_pull", "biceps", "triceps"]),
        ("Lower", ["squat", "hinge", "lunge", "calf", "core"]),
        ("Push", ["incline_push", "v_push", "fly", "lateral", "triceps"]),
        ("Pull", ["v_pull", "row2", "rear_delt", "biceps", "hammer"]),
        ("Legs", ["squat2", "glute", "ham_iso", "quad_iso", "calf"]),
    ],
    6: [
        ("Push A — Heavy", ["h_push", "v_push", "incline_push", "lateral", "triceps"]),
        ("Pull A — Heavy", ["h_pull", "v_pull", "rear_delt", "biceps", "core"]),
        ("Legs A — Squat Focus", ["squat", "hinge", "lunge", "calf"]),
        ("Push B — Volume", ["incline_push", "fly", "v_push", "lateral", "dips"]),
        ("Pull B — Volume", ["v_pull", "row2", "rear_delt", "hammer", "core2"]),
        ("Legs B — Glute Focus", ["glute", "squat2", "quad_iso", "ham_iso", "calf"]),
    ],
}


def _pick_exercise(slot: str, profile: dict, used: set) -> str | None:
    gym, home = SLOTS[slot]
    if profile["location"] == "Gym":
        return gym if gym not in used else None
    owned = set(profile.get("equipment") or [])
    for name, needs in home:
        if (needs is None or needs in owned) and name not in used:
            return name
    return None


def _prescription(slot: str, profile: dict) -> tuple[int, str, int]:
    compound = slot in COMPOUND_SLOTS
    home = profile["location"] == "Home"
    goal = profile["goal"]

    if slot in ("core", "core2") and not home:
        sets, reps = 3, "10-15"
    elif slot in ("core", "core2"):
        sets, reps = 3, "30-60 s" if slot == "core" else "8-12 / side"
    elif home:
        sets, reps = 3, "10-20" if compound else "12-20"
    elif goal == "Bulking":
        sets, reps = (4, "6-10") if compound else (3, "10-15")
    elif goal == "Cutting":
        sets, reps = (3, "5-8") if compound else (2, "10-15")
    else:
        sets, reps = (3, "8-10") if compound else (3, "10-15")

    if profile["experience"] == "Beginner":
        sets = max(2, sets - 1)
    elif profile["experience"] == "Advanced" and goal != "Cutting":
        sets += 1

    rest = (150 if goal != "Cutting" else 120) if (compound and not home) else (75 if compound else 60)
    return sets, reps, rest


def build_fallback_plan(profile: dict) -> dict:
    days = TEMPLATES[profile["days_per_week"]]
    training_days = []
    for focus, slots in days:
        used: set = set()
        exercises = []
        for slot in slots:
            name = _pick_exercise(slot, profile, used)
            if not name:
                continue
            used.add(name)
            sets, reps, rest = _prescription(slot, profile)
            exercises.append({
                "name": name, "sets": sets, "reps": reps, "rest_seconds": rest,
                "notes": "Leave 1-3 reps in reserve." if slot in COMPOUND_SLOTS else "Controlled tempo, full range of motion.",
            })
        training_days.append({
            "focus": focus,
            "duration_min": 15 + sum(e["sets"] for e in exercises) * 3,
            "exercises": exercises,
        })

    goal = profile["goal"]
    cardio = {
        "Bulking": "2-3 x 20 min easy cardio (walk, cycle) per week for heart health.",
        "Cutting": "7,000-10,000 steps daily plus 2-4 x 20-30 min low-intensity cardio per week.",
        "Maintain": "150+ min of moderate cardio per week (WHO guideline), e.g. 3 x 30 min brisk walks or cycling.",
    }[goal]
    return {
        "plan_name": f"{profile['days_per_week']}-Day {profile['location']} {goal} Program",
        "split_type": {3: "Full Body", 4: "Upper / Lower", 5: "Upper / Lower + PPL", 6: "Push / Pull / Legs x2"}[profile["days_per_week"]],
        "summary": "An evidence-based split that trains each muscle about twice per week with 10-20 hard sets, "
                   "matched to your goal, training location and experience.",
        "training_days": training_days,
        "progression": "Use double progression: when you hit the top of the rep range on every set with clean form, "
                       "add 2.5-5% load (or move to a harder variation at home) and start back at the bottom of the range. "
                       "Deload every 5-6 weeks by cutting sets in half for one week.",
        "warmup": "5 min light cardio + dynamic mobility, then 2-3 lighter ramp-up sets of your first exercise.",
        "cardio": cardio,
        "nutrition_tips": [
            "Hit your protein target daily, spread across 3-5 meals.",
            "Track body weight 3-4 mornings per week and adjust calories by 100-200 kcal if the trend is off target.",
            "Sleep 7-9 hours per night — recovery is when muscle is built.",
        ],
        "safety_notes": ["Stop any exercise that causes sharp or joint pain.", "Brace your core on every compound lift."],
        "sources_used": [],
    }

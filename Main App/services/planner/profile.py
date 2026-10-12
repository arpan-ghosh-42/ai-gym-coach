"""Athlete profile options and deterministic body/nutrition calculations."""

LOCATIONS = ["Gym", "Home"]
GOALS = ["Bulking", "Cutting", "Maintain"]
GENDERS = ["Male", "Female", "Other"]
EXPERIENCE_LEVELS = ["Beginner", "Intermediate", "Advanced"]
HOME_EQUIPMENT = ["Dumbbells", "Resistance bands", "Pull-up bar"]
MIN_DAYS, MAX_DAYS = 3, 6

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
# Weekday indexes used for each training frequency, spreading rest days out.
DAY_LAYOUTS = {3: [0, 2, 4], 4: [0, 1, 3, 4], 5: [0, 1, 3, 4, 5], 6: [0, 1, 2, 3, 4, 5]}

GOAL_DETAILS = {
    "Bulking": {"icon": "📈", "title": "Bulking", "desc": "Build muscle & strength with a controlled calorie surplus."},
    "Cutting": {"icon": "🔥", "title": "Cutting", "desc": "Lose fat while holding on to your hard-earned muscle."},
    "Maintain": {"icon": "⚖️", "title": "Maintain", "desc": "Keep your muscle, stay lean and build fitness long-term."},
}
LOCATION_DETAILS = {
    "Gym": {"icon": "🏋️", "title": "Gym Workout", "desc": "Barbells, machines, cables & dumbbells."},
    "Home": {"icon": "🏠", "title": "Home Workout", "desc": "Bodyweight plus whatever equipment you own."},
}

DEFAULT_PROFILE = {
    "weight_kg": 70.0,
    "height_cm": 175.0,
    "age": 25,
    "gender": "Male",
    "location": "Gym",
    "equipment": [],
    "goal": "Maintain",
    "days_per_week": 4,
    "experience": "Beginner",
    "notes": "",
}

_ACTIVITY_FACTORS = {3: 1.375, 4: 1.465, 5: 1.55, 6: 1.725}


def bmi(profile: dict) -> float:
    h = profile["height_cm"] / 100
    return round(profile["weight_kg"] / (h * h), 1) if h > 0 else 0.0


def bmi_category(value: float) -> str:
    if value < 18.5:
        return "Underweight"
    if value < 25:
        return "Healthy"
    if value < 30:
        return "Overweight"
    return "Obese"


def nutrition_targets(profile: dict) -> dict:
    """Mifflin-St Jeor BMR -> TDEE -> goal-adjusted calories and macros."""
    w, h, a = profile["weight_kg"], profile["height_cm"], profile["age"]
    sex_const = {"Male": 5, "Female": -161}.get(profile["gender"], -78)
    bmr = 10 * w + 6.25 * h - 5 * a + sex_const
    tdee = bmr * _ACTIVITY_FACTORS.get(profile["days_per_week"], 1.55)

    goal = profile["goal"]
    if goal == "Bulking":
        calories, protein_per_kg = tdee + 350, 1.8
        weekly_change = f"+{round(w * 0.0025, 2)} to +{round(w * 0.005, 2)} kg/week"
    elif goal == "Cutting":
        deficit = 350 if profile["gender"] == "Female" else 450
        calories, protein_per_kg = tdee - deficit, 2.2
        weekly_change = f"-{round(w * 0.005, 2)} to -{round(w * 0.01, 2)} kg/week"
    else:
        calories, protein_per_kg = tdee, 1.8
        weekly_change = "Stable (±0.2 kg/week)"

    protein = w * protein_per_kg
    fat = w * 0.8
    carbs = max(0.0, (calories - protein * 4 - fat * 9) / 4)
    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "calories": round(calories / 10) * 10,
        "protein_g": round(protein),
        "carbs_g": round(carbs),
        "fat_g": round(fat),
        "water_l": round(w * 0.035, 1),
        "weekly_change": weekly_change,
    }

"""RAG workout-plan generator: retrieve research context -> Groq LLM -> validated JSON plan."""
import json
import os

from detectors.registry import EXERCISES
from services.planner.fallback import build_fallback_plan
from services.planner.knowledge_base import retrieve_context
from services.planner.profile import DAY_LAYOUTS, WEEKDAYS, nutrition_targets

DEFAULT_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = f"""You are Movexa Planner, an evidence-based strength & conditioning coach.
You design weekly workout splits grounded in the CONTEXT provided. Context passages come in two kinds:
- COACH GUIDE: the Movexa head coach's own programs and methods (e.g. full-body foundation weeks for
  beginners before moving to push/pull/legs, exercise choices, sets/reps/rest, home routines).
  These are your PRIMARY source — follow their structure, exercise selection and prescriptions
  whenever they fit the athlete.
- REFERENCE: curated exercise-science notes. Use them to fill gaps and to adapt the coach's methods to
  athletes the guides don't cover (e.g. advanced lifters, cutting, 5-6 day schedules).
If neither covers something, use well-established exercise-science consensus — never invent studies.

Rules:
- Produce EXACTLY the requested number of training days. Rest days are added automatically; do not include them.
- Train each major muscle group roughly twice per week, ~10-20 hard sets per muscle per week (lower for beginners/cutting).
- Order each day: big compound lifts first, isolation last. 4-7 exercises per day.
- Balance: every upper-body or full-body day includes at least one PULL (row / pull-up / pulldown) AND one PUSH.
  Every lower-body or full-body day includes a knee-dominant (squat/lunge) AND a hip-dominant (hinge/bridge) movement.
- When day types repeat (e.g. Upper A / Upper B), vary the exercise selection or rep ranges between them.
- HOME plans may ONLY use bodyweight plus the equipment the athlete listed. GYM plans can use any standard gym equipment.
- Prefer exercises from this list (use these exact names) — the live Pose Coach can track and correct them:
  {", ".join(EXERCISES)}.
- Respect injuries/notes from the athlete by substituting safer exercises.
- "reps" is a string like "8-12", "10-15 / leg" or "30-60 s". "sets" is an integer 1-6. "rest_seconds" is an integer.

Respond with ONLY a JSON object of this shape:
{{
  "plan_name": str,
  "split_type": str,
  "summary": str (2-3 sentences explaining why this split fits the athlete),
  "training_days": [
    {{"focus": str, "duration_min": int,
      "exercises": [{{"name": str, "sets": int, "reps": str, "rest_seconds": int, "notes": str}}]}}
  ],
  "progression": str,
  "warmup": str,
  "cardio": str,
  "nutrition_tips": [str, str, str],
  "safety_notes": [str],
  "sources_used": [str]   (the [S#] tags of context passages you relied on)
}}"""


def _build_queries(profile: dict) -> list[str]:
    days, goal, loc = profile["days_per_week"], profile["goal"].lower(), profile["location"].lower()
    goal_word = {"bulking": "bulking muscle gain surplus", "cutting": "cutting fat loss deficit",
                 "maintain": "maintenance recomposition"}[goal]
    # Most profile-specific queries first, so they are not crowded out by the generic ones.
    queries = [f"{days} days per week split template", f"{goal_word} training volume sets rest"]
    # Phrased like the coach's program pages so the concrete workouts (exercises, sets, reps) are retrieved.
    if loc == "home":
        equipment = " ".join(profile.get("equipment") or ["bodyweight"])
        queries.append(f"home workout no gym push-ups squats lunges plank jumping jacks high knees {equipment}")
        queries.append("30 days beginner home workout warm-up diet")
    else:
        queries.append("gym exercise library compound isolation")
        if profile["experience"] == "Beginner":
            queries.append("week full body workout sets reps focus bench press lat pulldown leg press")
        if days >= 5:
            queries.append("push pull legs day chest triceps back biceps shoulders sets reps")
    if profile["gender"] == "Female":
        queries.append("women female training differences")
    if profile.get("notes"):
        queries.append(f"injury safety substitute {profile['notes']}")
    queries += [
        f"{profile['experience']} lifter experience split",
        "weekly volume frequency per muscle hypertrophy",
        "rep ranges proximity to failure progressive overload",
    ]
    return queries


def _format_context(chunks) -> str:
    return "\n\n".join(
        f"[S{i}] {'COACH GUIDE' if c.kind == 'guide' else 'REFERENCE'} ({c.source} — {c.section})\n{c.text}"
        for i, c in enumerate(chunks, start=1)
    )


def _athlete_brief(profile: dict, nutrition: dict) -> str:
    equipment = ", ".join(profile.get("equipment") or []) or "none (bodyweight only)"
    lines = [
        f"Gender: {profile['gender']}",
        f"Age: {profile['age']}",
        f"Weight: {profile['weight_kg']} kg, Height: {profile['height_cm']} cm",
        f"Goal: {profile['goal']}",
        f"Training location: {profile['location']}",
    ]
    if profile["location"] == "Home":
        lines.append(f"Home equipment: {equipment}")
    lines += [
        f"Experience: {profile['experience']}",
        f"Training days per week: {profile['days_per_week']}",
        f"Daily calorie target (pre-computed): {nutrition['calories']} kcal, protein {nutrition['protein_g']} g",
        f"Injuries / notes: {profile.get('notes') or 'none'}",
    ]
    return "\n".join(lines)


def _as_int(value, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(hi, int(float(value))))
    except (TypeError, ValueError):
        return default


def _validate(raw: dict, profile: dict) -> dict:
    days = raw.get("training_days")
    if not isinstance(days, list) or len(days) < profile["days_per_week"]:
        raise ValueError("LLM returned the wrong number of training days")

    clean_days = []
    for day in days[: profile["days_per_week"]]:
        exercises = []
        for ex in day.get("exercises") or []:
            if not isinstance(ex, dict) or not str(ex.get("name", "")).strip():
                continue
            exercises.append({
                "name": str(ex["name"]).strip(),
                "sets": _as_int(ex.get("sets"), 3, 1, 6),
                "reps": str(ex.get("reps") or "8-12"),
                "rest_seconds": _as_int(ex.get("rest_seconds"), 90, 30, 300),
                "notes": str(ex.get("notes") or ""),
            })
        if not exercises:
            raise ValueError("LLM returned a training day without exercises")
        clean_days.append({
            "focus": str(day.get("focus") or "Training"),
            "duration_min": _as_int(day.get("duration_min"), 60, 20, 120),
            "exercises": exercises,
        })

    def _list(key):
        val = raw.get(key)
        return [str(v) for v in val] if isinstance(val, list) else []

    return {
        "plan_name": str(raw.get("plan_name") or "Your Movexa Program"),
        "split_type": str(raw.get("split_type") or ""),
        "summary": str(raw.get("summary") or ""),
        "training_days": clean_days,
        "progression": str(raw.get("progression") or ""),
        "warmup": str(raw.get("warmup") or ""),
        "cardio": str(raw.get("cardio") or ""),
        "nutrition_tips": _list("nutrition_tips"),
        "safety_notes": _list("safety_notes"),
        "sources_used": _list("sources_used"),
    }


def _attach_schedule(plan: dict, profile: dict) -> dict:
    layout = DAY_LAYOUTS[profile["days_per_week"]]
    schedule, it = [], iter(plan["training_days"])
    for idx, weekday in enumerate(WEEKDAYS):
        if idx in layout:
            schedule.append({"weekday": weekday, "is_rest": False, **next(it)})
        else:
            schedule.append({"weekday": weekday, "is_rest": True, "focus": "Rest & Recovery",
                             "duration_min": 0, "exercises": []})
    plan["weekly_schedule"] = schedule
    return plan


def _llm_plan(groq_client, profile: dict, nutrition: dict, chunks) -> dict:
    user_msg = (
        f"ATHLETE PROFILE\n{_athlete_brief(profile, nutrition)}\n\n"
        f"RESEARCH CONTEXT\n{_format_context(chunks) or 'No context retrieved.'}\n\n"
        f"Design the {profile['days_per_week']}-day weekly split now. Return JSON only."
    )
    response = groq_client.chat.completions.create(
        # Planning needs a stronger model than the short real-time voice cues that use GROQ_MODEL.
        model=os.getenv("GROQ_PLANNER_MODEL") or DEFAULT_MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_msg}],
        temperature=0.3,
        response_format={"type": "json_object"},
        max_tokens=4096,
    )
    return _validate(json.loads(response.choices[0].message.content), profile)


def generate_plan(profile: dict, groq_client=None) -> dict:
    """Returns a plan dict. Always succeeds: falls back to the rule-based planner on any LLM failure."""
    nutrition = nutrition_targets(profile)
    chunks = retrieve_context(_build_queries(profile))

    engine, error = "fallback", None
    plan = None
    if groq_client is not None:
        try:
            plan = _llm_plan(groq_client, profile, nutrition, chunks)
            engine = "groq-rag"
        except Exception as exc:  # network, quota, bad JSON, validation
            error = str(exc)[:300]
    if plan is None:
        plan = build_fallback_plan(profile)

    plan = _attach_schedule(plan, profile)
    plan["nutrition"] = nutrition
    plan["engine"] = engine
    plan["engine_error"] = error
    plan["retrieved_sources"] = [
        {"tag": f"S{i}", "source": c.source, "section": c.section, "kind": c.kind, "excerpt": c.text[:280]}
        for i, c in enumerate(chunks, start=1)
    ]
    return plan

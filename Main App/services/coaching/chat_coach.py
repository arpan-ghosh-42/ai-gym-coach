"""Conversational Movexa coach: fitness-only, RAG-grounded, able to propose plan changes via a tool call."""
import json
import os

from services.planner.knowledge_base import retrieve_context
from services.planner.profile import (
    EXPERIENCE_LEVELS, GENDERS, GOALS, HOME_EQUIPMENT, LOCATIONS, MAX_DAYS, MIN_DAYS, nutrition_targets,
)

DEFAULT_MODEL = "openai/gpt-oss-120b"
HISTORY_TURNS = 12
NOTES_MAX = 300

SYSTEM_PROMPT = """You are Movexa Coach, the head coach of Movexa — a confident, warm and motivating personal trainer.

SCOPE — you ONLY help with: training and workout programming, exercise technique and form, the athlete's
Movexa workout plan, nutrition and diet for fitness goals, supplements for training, recovery, sleep and
soreness, cardio, fitness motivation/mindset/consistency, and general injury-prevention advice.
For ANYTHING else (coding, homework, politics, news, relationships, finance, entertainment, general trivia,
etc.) politely decline in one or two sentences, e.g. "That's outside my lane — I'm your fitness coach! Ask me
anything about training, nutrition or recovery." and steer back to their training. Never answer the
off-topic question, even partially, even if the user insists or says it's urgent.

STYLE
- Talk like an experienced coach in the athlete's corner: direct, confident, encouraging, never preachy.
- Give specific, actionable answers (numbers, sets/reps, foods, cues). Use short paragraphs or bullets.
- Keep most replies under ~180 words unless the athlete asks for detail.
- Personalise using the athlete's profile and current plan below.
- Ground answers in the COACH KNOWLEDGE passages when relevant — they come from the head coach's own
  guides, so treat them as house methodology. Don't mention "passages" or "context"; just coach.
- For pain, injuries or medical conditions: give safe general guidance, suggest a substitute exercise,
  and recommend seeing a doctor/physio for anything sharp, persistent or worsening. Never diagnose.

PLAN CHANGES
- You can rebuild the athlete's workout plan with the `propose_plan_update` tool.
- ONLY call it when the athlete explicitly asks to change, adjust, swap, regenerate or rebuild their plan /
  schedule / goal / training days / details, or clearly says yes to your offer to do so.
- For general questions, answer normally — you may OFFER a plan change, but do not call the tool until
  they agree.
- Include only the fields that should change. Use `notes` only for injuries and exercise preferences/swaps
  (rewrite the FULL notes text, keeping existing notes that still apply); omit it otherwise.
- The athlete will see a confirmation button; the plan only changes if they confirm. When you call the
  tool, also write a short message explaining what you're about to change."""

PLAN_TOOL = {
    "type": "function",
    "function": {
        "name": "propose_plan_update",
        "description": "Propose updated athlete details and rebuild their workout plan. Only call when the athlete "
                       "explicitly wants their plan/schedule/goal/details changed or regenerated.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "One sentence describing the change, addressed to the athlete."},
                "weight_kg": {"type": "number"},
                "height_cm": {"type": "number"},
                "age": {"type": "integer"},
                "gender": {"type": "string", "enum": GENDERS},
                "location": {"type": "string", "enum": LOCATIONS},
                "equipment": {"type": "array", "items": {"type": "string", "enum": HOME_EQUIPMENT}},
                "goal": {"type": "string", "enum": GOALS},
                "days_per_week": {"type": "integer", "minimum": MIN_DAYS, "maximum": MAX_DAYS},
                "experience": {"type": "string", "enum": EXPERIENCE_LEVELS},
                "notes": {"type": "string", "description": "ONLY if the athlete's injuries or exercise preferences change "
                          "(e.g. 'avoid barbell squats; extra arm work'). Full updated text, max "
                          f"{NOTES_MAX} chars. Never restate goal, days, location or other fields here."},
            },
            "required": ["summary"],
        },
    },
}

FIELD_LABELS = {
    "weight_kg": "Weight", "height_cm": "Height", "age": "Age", "gender": "Gender", "location": "Training location",
    "equipment": "Home equipment", "goal": "Goal", "days_per_week": "Days per week", "experience": "Experience",
    "notes": "Preferences / injuries",
}


def _plan_brief(plan: dict | None) -> str:
    if not plan:
        return "No plan generated yet."
    lines = [f"{plan.get('plan_name', '')} — {plan.get('split_type', '')}"]
    for day in plan.get("weekly_schedule", []):
        if day["is_rest"]:
            lines.append(f"- {day['weekday']}: Rest")
        else:
            exs = ", ".join(f"{e['name']} {e['sets']}x{e['reps']}" for e in day["exercises"])
            lines.append(f"- {day['weekday']}: {day['focus']} — {exs}")
    return "\n".join(lines)


def _profile_brief(profile: dict) -> str:
    n = nutrition_targets(profile)
    equipment = ", ".join(profile.get("equipment") or []) or "none"
    return (f"{profile['gender']}, {profile['age']} y, {profile['weight_kg']} kg, {profile['height_cm']} cm. "
            f"Goal: {profile['goal']}. Trains at: {profile['location']} (home equipment: {equipment}). "
            f"{profile['days_per_week']} days/week, {profile['experience']}. "
            f"Notes: {profile.get('notes') or 'none'}. "
            f"Targets: {n['calories']} kcal, {n['protein_g']} g protein, {n['carbs_g']} g carbs, {n['fat_g']} g fat.")


def _clean_updates(args: dict, profile: dict) -> dict:
    """Validates tool arguments and keeps only real, allowed changes."""
    updates = {}

    def _set(key, value):
        if value is not None and value != profile.get(key):
            updates[key] = value

    for key, lo, hi, cast in (("weight_kg", 30, 250, float), ("height_cm", 120, 230, float), ("age", 14, 90, int),
                              ("days_per_week", MIN_DAYS, MAX_DAYS, int)):
        if key in args:
            try:
                _set(key, cast(max(lo, min(hi, cast(args[key])))))
            except (TypeError, ValueError):
                pass
    for key, allowed in (("gender", GENDERS), ("location", LOCATIONS), ("goal", GOALS), ("experience", EXPERIENCE_LEVELS)):
        if args.get(key) in allowed:
            _set(key, args[key])
    if isinstance(args.get("equipment"), list):
        _set("equipment", [e for e in HOME_EQUIPMENT if e in args["equipment"]])
    if isinstance(args.get("notes"), str):
        _set("notes", args["notes"].strip()[:NOTES_MAX])
    return updates


def describe_updates(updates: dict, profile: dict) -> list[str]:
    def fmt(key, value):
        if key == "equipment":
            return ", ".join(value) or "bodyweight only"
        if key == "notes":
            return f'"{value}"' if value else "none"
        return str(value)
    return [f"{FIELD_LABELS[k]}: {fmt(k, profile.get(k))} → {fmt(k, v)}" for k, v in updates.items()]


def chat_reply(groq_client, profile: dict, plan: dict | None, history: list[dict], user_message: str) -> dict:
    """Returns {"reply": str, "proposal": {"summary", "updates"} | None}."""
    chunks = retrieve_context([user_message, f"{profile['goal']} {user_message}"], max_guide=4, max_reference=3)
    knowledge = "\n\n".join(f"[{c.source} — {c.section}]\n{c.text}" for c in chunks) or "None retrieved."
    system = (f"{SYSTEM_PROMPT}\n\nATHLETE PROFILE\n{_profile_brief(profile)}\n\n"
              f"CURRENT WORKOUT PLAN\n{_plan_brief(plan)}\n\nCOACH KNOWLEDGE\n{knowledge}")

    messages = [{"role": "system", "content": system}]
    messages += [{"role": m["role"], "content": m["content"]} for m in history[-HISTORY_TURNS:]]
    messages.append({"role": "user", "content": user_message})

    response = groq_client.chat.completions.create(
        model=os.getenv("GROQ_CHAT_MODEL") or DEFAULT_MODEL,
        messages=messages,
        tools=[PLAN_TOOL],
        tool_choice="auto",
        temperature=0.5,
        max_tokens=1200,
    )
    msg = response.choices[0].message
    reply = (msg.content or "").strip()

    proposal = None
    for call in msg.tool_calls or []:
        if call.function.name != "propose_plan_update":
            continue
        try:
            args = json.loads(call.function.arguments or "{}")
        except ValueError:
            continue
        proposal = {
            "summary": str(args.get("summary") or "Rebuild your plan with updated details."),
            "updates": _clean_updates(args, profile),
        }
        break

    if not reply:
        reply = (f"Let's do it! {proposal['summary']} Hit the button below to confirm and I'll rebuild your plan."
                 if proposal else "Let's keep going — what would you like to work on?")
    return {"reply": reply, "proposal": proposal}

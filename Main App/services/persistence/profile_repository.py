import json
from services.persistence.exercise_repository import _get_connection


def init_profile_tables() -> None:
    conn = _get_connection()

    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                user_id       INTEGER PRIMARY KEY REFERENCES users(id),
                weight_kg     REAL    NOT NULL,
                height_cm     REAL    NOT NULL,
                age           INTEGER NOT NULL,
                gender        TEXT    NOT NULL,
                location      TEXT    NOT NULL,
                equipment     TEXT    NOT NULL DEFAULT '[]',
                goal          TEXT    NOT NULL,
                days_per_week INTEGER NOT NULL,
                experience    TEXT    NOT NULL,
                notes         TEXT    NOT NULL DEFAULT '',
                updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                role       TEXT    NOT NULL,
                content    TEXT    NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workout_plans (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                plan_json  TEXT    NOT NULL,
                profile_json TEXT  NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def get_profile(user_id: int) -> dict | None:
    conn = _get_connection()

    row = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        return None
    profile = dict(row)
    profile["equipment"] = json.loads(profile.get("equipment") or "[]")
    profile.pop("updated_at", None)
    profile.pop("user_id", None)
    return profile


def save_profile(user_id: int, profile: dict) -> None:
    conn = _get_connection()

    with conn:
        conn.execute(
            """
            INSERT INTO profiles (user_id, weight_kg, height_cm, age, gender, location, equipment,
                                  goal, days_per_week, experience, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                weight_kg = excluded.weight_kg, height_cm = excluded.height_cm, age = excluded.age,
                gender = excluded.gender, location = excluded.location, equipment = excluded.equipment,
                goal = excluded.goal, days_per_week = excluded.days_per_week,
                experience = excluded.experience, notes = excluded.notes, updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id, profile["weight_kg"], profile["height_cm"], profile["age"], profile["gender"],
                profile["location"], json.dumps(profile.get("equipment") or []), profile["goal"],
                profile["days_per_week"], profile["experience"], profile.get("notes") or "",
            ),
        )


def save_plan(user_id: int, plan: dict, profile: dict) -> None:
    conn = _get_connection()

    with conn:
        conn.execute(
            "INSERT INTO workout_plans (user_id, plan_json, profile_json) VALUES (?, ?, ?)",
            (user_id, json.dumps(plan), json.dumps(profile)),
        )


def add_chat_message(user_id: int, role: str, content: str) -> None:
    conn = _get_connection()

    with conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content)
        )


def get_chat_messages(user_id: int, limit: int = 60) -> list[dict]:
    conn = _get_connection()

    rows = conn.execute(
        "SELECT role, content FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
    ).fetchall()
    return [dict(r) for r in reversed(rows)]


def clear_chat(user_id: int) -> None:
    conn = _get_connection()

    with conn:
        conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))


def get_latest_plan(user_id: int) -> dict | None:
    conn = _get_connection()

    row = conn.execute(
        "SELECT plan_json, created_at FROM workout_plans WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    plan = json.loads(row["plan_json"])
    plan["created_at"] = row["created_at"]
    return plan

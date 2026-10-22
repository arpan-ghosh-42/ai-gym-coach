# Movexa — AI Workout Planner & Live Pose Coach

Movexa has two independent parts:

1. **AI Workout Planner**: new users answer five onboarding questions (body metrics, gym or home, goal, training days, gender). Movexa then generates a weekly split with a RAG pipeline: it retrieves passages from `Main App/knowledge_base/`, sends them to a Groq LLM, and gets back a structured plan. Users can edit their details at any time, and the plan is rebuilt.
2. **Pose Coach**: real-time form correction with MediaPipe and WebRTC for squats, push-ups, dumbbell curls, shoulder press and lunges. It includes rep and set counting and spoken cues.

## Run

```bash
# from the repo root
uv pip install -r "Main App/requirements.txt"

# landing page (port 3000)
cd LandingPage && python -m http.server 3000

# app (port 8501)
cd "Main App" && ..\.venv\Scripts\python.exe -m streamlit run main.py
```

`Main App/.env`:

```
GROQ_API_KEY=...
GROQ_MODEL=...                # short real-time voice cues
GROQ_PLANNER_MODEL=...        # optional, defaults to openai/gpt-oss-120b
```

Without a Groq key, the planner falls back to a rule-based engine, so it always produces a plan.

## Knowledge base (RAG)

- `knowledge_base/docs/*.md`: curated, cited exercise-science notes (volume, frequency, splits, nutrition, home training, individual factors).
- `knowledge_base/pdfs/`: put your own PDFs here. They are parsed with `pypdf`, chunked, and indexed with BM25. The index rebuilds automatically when files change.

## Layout

```
Main App/
  main.py                      router: login -> onboarding -> [Workout Plan | Pose Coach | My Profile]
  views/                       one module per page (onboarding, workout_plan, pose_coach, profile)
  services/planner/            knowledge_base (RAG), generator (Groq), fallback, profile/nutrition math
  services/persistence/        SQLite: users, exercises, profiles, workout_plans
```

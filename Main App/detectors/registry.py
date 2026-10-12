"""Single source of truth for every exercise the live Pose Coach can track."""
import re

from detectors import abs_cardio, arms, back, chest, legs, shoulders
from detectors.biceps_curl import BicepsCurlDetector
from detectors.generic import ExerciseSpec, GenericDetector
from detectors.lunges import LungesDetector
from detectors.pushup import PushUpDetector
from detectors.shoulder_press import ShoulderPressDetector
from detectors.squat import SquatDetector

# The original hand-tuned detectors keep their own HUD and voice-feedback logic.
LEGACY = [
    ExerciseSpec(name="Squats", group="Legs", icon="🦵", target="Quads & Glutes", camera="Film from the side.",
                 landmarks=[], factory=SquatDetector,
                 cues=["Knee flexion angle", "Back upright angle", "Parallel depth"]),
    ExerciseSpec(name="Push-ups", group="Chest", icon="💪", target="Chest & Core", camera="Film from the side.",
                 landmarks=[], factory=PushUpDetector,
                 cues=["Elbow angle 90deg", "Body spine alignment", "Hip sag detection"]),
    ExerciseSpec(name="Biceps Curls (Dumbbell)", group="Arms", icon="🏋️", target="Biceps Brachii",
                 camera="Film from the side.", landmarks=[], factory=BicepsCurlDetector,
                 cues=["Elbow flexion", "Shoulder lock", "Anti-swing monitor"]),
    ExerciseSpec(name="Shoulder Press", group="Shoulders", icon="🔝", target="Deltoids & Triceps",
                 camera="Face the camera.", landmarks=[], factory=ShoulderPressDetector,
                 cues=["Full overhead lockout", "Elbow lowering angle", "Back arch check"]),
    ExerciseSpec(name="Lunges", group="Legs", icon="🏃", target="Glutes & Hamstrings", camera="Film from the side.",
                 landmarks=[], factory=LungesDetector,
                 cues=["Front knee 90deg", "Torso balance", "Hip stability"]),
]

GROUP_ORDER = ["Chest", "Back", "Shoulders", "Arms", "Legs", "Core", "Cardio"]

EXERCISES: dict[str, ExerciseSpec] = {
    spec.name: spec
    for spec in sorted(
        LEGACY + chest.SPECS + back.SPECS + shoulders.SPECS + arms.SPECS + legs.SPECS + abs_cardio.SPECS,
        key=lambda s: GROUP_ORDER.index(s.group),
    )
}

# Ordered most-specific first: the first matching pattern wins.
ALIAS_RULES = [
    (r"bulgarian|rear[- ]foot elevated", "Bulgarian Split Squat"),
    (r"pistol|shrimp", "Pistol Squat"),
    (r"split squat|lunge|curtsy", "Lunges"),
    (r"wall sit", "Wall Sit"),
    (r"leg press", "Leg Press"),
    (r"leg extension", "Leg Extension"),
    (r"nordic", "Nordic Curl"),
    (r"leg curl|hamstring curl", "Leg Curl"),
    (r"back extension|hyperextension", "Back Extension"),
    (r"romanian|\brdl\b|stiff[- ]leg|good morning", "Romanian Deadlift"),
    (r"deadlift", "Deadlift"),
    (r"hip thrust|glute bridge|\bbridge", "Hip Thrust / Glute Bridge"),
    (r"donkey kick|glute kickback|cable kickback", "Donkey Kicks"),
    (r"calf raise|calf", "Calf Raise"),
    (r"step[- ]?up", "Step-Ups"),
    (r"squat", "Squats"),
    (r"pike push|handstand push", "Pike Push-ups"),
    (r"knee push", "Knee Push-ups"),
    (r"incline push", "Incline Push-ups"),
    (r"decline push", "Decline Push-ups"),
    (r"diamond push|close[- ]grip push|triangle push", "Diamond Push-ups"),
    (r"push[- ]?ups?|press[- ]?ups?", "Push-ups"),
    (r"skull ?crusher|lying triceps", "Skull Crusher"),
    (r"overhead (triceps|tricep|dumbbell triceps|extension)|french press|triceps extension", "Overhead Triceps Extension"),
    (r"pushdown|push[- ]down", "Triceps Pushdown"),
    (r"kickback", "Triceps Kickback"),
    (r"\bdips?\b", "Dips"),
    (r"shoulder press|overhead press|military press|arnold", "Shoulder Press"),
    (r"bench press|chest press|floor press|incline (dumbbell |barbell )?press|decline press|smith", "Bench / Chest Press"),
    (r"reverse fly|rear delt fly|pull[- ]apart", "Band Pull-Apart / Reverse Fly"),
    (r"\bfly|flye|pec deck|butterfly|crossover", "Chest Fly"),
    (r"face pull", "Face Pull"),
    (r"lateral raise|side raise", "Lateral Raise"),
    (r"front raise", "Front Raise"),
    (r"upright row", "Upright Row"),
    (r"pull[- ]?ups?|chin[- ]?ups?", "Pull-ups"),
    (r"pulldown|pull[- ]down", "Lat Pulldown"),
    (r"inverted row|table row|australian|ring row|door row", "Inverted Row"),
    (r"seated|cable row|band row|machine row|low row", "Seated Row"),
    (r"\brows?\b", "Bent-over Row"),
    (r"hammer curl", "Hammer Curl"),
    (r"preacher|concentration|spider curl", "Preacher / Concentration Curl"),
    (r"isometric", None),
    (r"dumbbell curl|biceps? curl|\bdb curl", "Biceps Curls (Dumbbell)"),
    (r"\bcurl", "Barbell / Cable Curl"),
    (r"side plank", "Side Plank"),
    (r"plank", "Plank"),
    (r"bicycle", "Bicycle Crunch"),
    (r"sit[- ]?ups?", "Sit-ups"),
    (r"crunch", "Crunches"),
    (r"dead ?bug", "Dead Bug"),
    (r"leg raise|knee raise|knee tuck|toes to bar", "Leg / Knee Raise"),
    (r"mountain climber", "Mountain Climbers"),
    (r"high knee", "High Knees"),
    (r"jumping jack|star jump", "Jumping Jacks"),
]
_COMPILED = [(re.compile(p), name) for p, name in ALIAS_RULES]


def match_exercise(exercise_name: str) -> str | None:
    """Maps a free-text plan exercise name to a trackable exercise, or None if it can't be tracked."""
    name = exercise_name.lower()
    if name in (n.lower() for n in EXERCISES):
        return next(n for n in EXERCISES if n.lower() == name)
    for pattern, target in _COMPILED:
        if pattern.search(name):
            return target
    return None


def create_detector(name: str):
    spec = EXERCISES[name]
    return spec.factory() if spec.factory else GenericDetector(spec)


def is_legacy(name: str) -> bool:
    spec = EXERCISES.get(name)
    return bool(spec and spec.factory)


def is_hold(name: str) -> bool:
    spec = EXERCISES.get(name)
    return bool(spec and spec.mode == "hold")


def grouped() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {g: [] for g in GROUP_ORDER}
    for name, spec in EXERCISES.items():
        out[spec.group].append(name)
    return {g: names for g, names in out.items() if names}

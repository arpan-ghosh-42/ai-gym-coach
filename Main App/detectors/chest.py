from detectors.generic import ExerciseSpec, arms_soft, body_line, hands_spread, joint_angle

ELBOW = joint_angle("shoulder", "elbow", "wrist")
ARM = ["shoulder", "elbow", "wrist"]
SIDE_VIEW = "Film from the side with your whole body in frame."

SPECS = [
    ExerciseSpec(
        name="Knee Push-ups", group="Chest", icon="💪", target="Chest, Triceps & Core", camera=SIDE_VIEW,
        landmarks=ARM + ["hip", "knee"], metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=95,
        checks=[body_line(155, end="knee")],
        cues=["Elbow bend to ~90°", "Straight line shoulders → knees", "Full lockout at top"],
        partial_cue="Go lower — bring your chest close to the floor.",
    ),
    ExerciseSpec(
        name="Incline Push-ups", group="Chest", icon="💪", target="Lower Chest & Triceps", camera=SIDE_VIEW,
        landmarks=ARM + ["hip", "ankle"], metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=95,
        checks=[body_line(160)],
        cues=["Chest to the bench edge", "Rigid plank body line", "Elbows ~45° from torso"],
        partial_cue="Lower all the way until your chest nearly touches the surface.",
    ),
    ExerciseSpec(
        name="Decline Push-ups", group="Chest", icon="💪", target="Upper Chest & Shoulders", camera=SIDE_VIEW,
        landmarks=ARM + ["hip", "ankle"], metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=95,
        checks=[body_line(155)],
        cues=["Feet elevated, hips level", "Elbow bend to ~90°", "No hip sag"],
        partial_cue="Lower further — aim for a 90° elbow bend.",
    ),
    ExerciseSpec(
        name="Diamond Push-ups", group="Chest", icon="💎", target="Triceps & Inner Chest", camera=SIDE_VIEW,
        landmarks=ARM + ["hip", "ankle"], metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=100,
        checks=[body_line(160)],
        cues=["Hands together under chest", "Elbows track back", "Straight body line"],
        partial_cue="Go deeper — chest down to your hands.",
    ),
    ExerciseSpec(
        name="Bench / Chest Press", group="Chest", icon="🏋️", target="Chest, Front Delts & Triceps",
        camera="Lie on the bench and film from the side so your arm is fully visible.",
        landmarks=ARM, metric=ELBOW, metric_label="Elbow Angle", rest=155, peak=100,
        cues=["Bar/dumbbells to mid-chest", "Elbow ~90° at the bottom", "Press to near lockout"],
        partial_cue="Bring the weight lower — touch your chest or reach 90° at the elbow.",
    ),
    ExerciseSpec(
        name="Chest Fly", group="Chest", icon="🦋", target="Pectorals",
        camera="Face the camera with both arms fully in frame.",
        landmarks=ARM, side="none", metric=hands_spread(), metric_label="Hand Spread", unit="%",
        rest=2.2, peak=1.1, checks=[arms_soft(130)],
        cues=["Slight fixed elbow bend", "Wide stretch at the bottom", "Squeeze hands together"],
        partial_cue="Open wider for a full chest stretch, then bring your hands all the way together.",
    ),
    ExerciseSpec(
        name="Dips", group="Chest", icon="⬇️", target="Triceps, Lower Chest & Shoulders", camera=SIDE_VIEW,
        landmarks=ARM + ["hip"], metric=ELBOW, metric_label="Elbow Angle", rest=155, peak=100,
        cues=["Lower until elbows reach ~90°", "Shoulders down, away from ears", "Full press-out at top"],
        partial_cue="Dip lower — get your elbows to about 90°.",
    ),
]

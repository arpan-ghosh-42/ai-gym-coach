from detectors.generic import ExerciseSpec, hips_piked, joint_angle, torso_still

ELBOW = joint_angle("shoulder", "elbow", "wrist")
ABDUCTION = joint_angle("hip", "shoulder", "elbow")
ARM = ["shoulder", "elbow", "wrist"]

SPECS = [
    ExerciseSpec(
        name="Pike Push-ups", group="Shoulders", icon="🔺", target="Shoulders & Triceps",
        camera="Film from the side with your whole body in frame.",
        landmarks=ARM + ["hip", "ankle"], metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=100,
        checks=[hips_piked(125)],
        cues=["Hips high (upside-down V)", "Head towards the floor", "Press back to lockout"],
        partial_cue="Lower your head closer to the floor.",
    ),
    ExerciseSpec(
        name="Lateral Raise", group="Shoulders", icon="🦅", target="Side Delts",
        camera="Face the camera with both arms and hips in frame.",
        landmarks=["shoulder", "elbow", "hip"], side="both", metric=ABDUCTION, metric_label="Arm Raise",
        rest=30, peak=75, checks=[torso_still(12)],
        cues=["Lead with the elbows", "Raise to shoulder height", "Slow 2-3 s lowering"],
        partial_cue="Raise your arms up to shoulder height.",
    ),
    ExerciseSpec(
        name="Front Raise", group="Shoulders", icon="⬆️", target="Front Delts",
        camera="Film from the side with your arm and hips in frame.",
        landmarks=["shoulder", "elbow", "hip"], metric=ABDUCTION, metric_label="Arm Raise", rest=30, peak=80,
        checks=[torso_still(12)],
        cues=["Arms nearly straight", "Raise to eye level", "No torso swing"],
        partial_cue="Lift the weight up to eye level.",
    ),
    ExerciseSpec(
        name="Upright Row", group="Shoulders", icon="⬆️", target="Side Delts & Traps",
        camera="Face the camera with both arms and hips in frame.",
        landmarks=["shoulder", "elbow", "hip"], side="both", metric=ABDUCTION, metric_label="Elbow Height",
        rest=30, peak=70, checks=[torso_still(15)],
        cues=["Elbows lead the movement", "Elbows to shoulder height", "Bar close to the body"],
        partial_cue="Pull your elbows up to shoulder height.",
    ),
]

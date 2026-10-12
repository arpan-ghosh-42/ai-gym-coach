from detectors.generic import ExerciseSpec, body_line, horizontal, joint_angle, knee_height

HIP = joint_angle("shoulder", "hip", "knee")
BODY = joint_angle("shoulder", "hip", "ankle")
SIDE_VIEW = "Film from the side with your whole body in frame."
FRONT_VIEW = "Face the camera with your whole body in frame."

SPECS = [
    ExerciseSpec(
        name="Plank", group="Core", icon="🧱", target="Core & Shoulders", mode="hold", camera=SIDE_VIEW,
        landmarks=["shoulder", "hip", "ankle"], metric=BODY, metric_label="Body Line", hold_range=(155, 185),
        checks=[horizontal(35), body_line(160)],
        cues=["Elbows under shoulders", "Straight line head → heels", "Glutes and abs tight"],
    ),
    ExerciseSpec(
        name="Side Plank", group="Core", icon="📐", target="Obliques & Core", mode="hold", camera=FRONT_VIEW,
        landmarks=["shoulder", "hip", "ankle"], metric=BODY, metric_label="Body Line", hold_range=(155, 185),
        checks=[horizontal(45, "Lift into a side plank — body straight and off the floor.")],
        cues=["Elbow under shoulder", "Hips lifted high", "Body in one straight line"],
    ),
    ExerciseSpec(
        name="Crunches", group="Core", icon="🔥", target="Upper Abs", camera=SIDE_VIEW,
        landmarks=["shoulder", "hip", "knee"], metric=HIP, metric_label="Hip Angle", rest=128, peak=112,
        min_rep_seconds=0.6,
        cues=["Knees bent, feet flat", "Curl shoulders off the floor", "Exhale at the top"],
        partial_cue="Curl your shoulders higher off the floor.",
    ),
    ExerciseSpec(
        name="Sit-ups", group="Core", icon="🔥", target="Abs & Hip Flexors", camera=SIDE_VIEW,
        landmarks=["shoulder", "hip", "knee"], metric=HIP, metric_label="Hip Angle", rest=120, peak=75,
        cues=["Feet anchored", "Sit all the way up", "Lower with control"],
        partial_cue="Sit all the way up, chest towards your knees.",
    ),
    ExerciseSpec(
        name="Leg / Knee Raise", group="Core", icon="🦵", target="Lower Abs & Hip Flexors", camera=SIDE_VIEW,
        landmarks=["shoulder", "hip", "knee"], metric=HIP, metric_label="Hip Angle", rest=150, peak=100,
        cues=["No swinging", "Raise knees/legs to hip height", "Lower slowly"],
        partial_cue="Raise your legs higher — at least to hip height.",
    ),
    ExerciseSpec(
        name="Dead Bug", group="Core", icon="🐞", target="Deep Core", camera=SIDE_VIEW,
        landmarks=["shoulder", "hip", "knee"], side="alternate", metric=HIP, metric_label="Hip Angle",
        rest=105, peak=145, min_rep_seconds=1.0,
        cues=["Lower back pressed to the floor", "Extend opposite arm & leg", "Slow and controlled"],
        partial_cue="Extend your leg further out, keeping your lower back down.",
    ),
    ExerciseSpec(
        name="Bicycle Crunch", group="Core", icon="🚲", target="Obliques & Abs", camera=SIDE_VIEW,
        landmarks=["shoulder", "hip", "knee"], side="alternate", metric=HIP, metric_label="Hip Angle",
        rest=140, peak=95, min_rep_seconds=0.5,
        cues=["Shoulders off the floor", "Elbow to opposite knee", "Fully extend the other leg"],
        partial_cue="Bring your knee all the way in towards your chest.",
    ),
    ExerciseSpec(
        name="Mountain Climbers", group="Cardio", icon="⛰️", target="Core & Conditioning", camera=SIDE_VIEW,
        landmarks=["shoulder", "hip", "knee"], side="alternate", metric=HIP, metric_label="Hip Angle",
        rest=140, peak=100, min_rep_seconds=0.25,
        cues=["Hands under shoulders", "Drive knees to chest", "Hips stay level"],
        partial_cue="Drive your knee further towards your chest.",
    ),
    ExerciseSpec(
        name="High Knees", group="Cardio", icon="🏃", target="Hip Flexors & Conditioning", camera=FRONT_VIEW,
        landmarks=["hip", "knee"], side="alternate", metric=knee_height(), metric_label="Knee Height", unit="%",
        rest=0.6, peak=0.3, min_rep_seconds=0.2,
        cues=["Knees up to hip height", "Stay on the balls of your feet", "Pump your arms"],
        partial_cue="Lift your knees higher — up to hip height.",
    ),
    ExerciseSpec(
        name="Jumping Jacks", group="Cardio", icon="⭐", target="Full Body Conditioning", camera=FRONT_VIEW,
        landmarks=["shoulder", "elbow", "hip"], side="both",
        metric=joint_angle("hip", "shoulder", "elbow"), metric_label="Arm Raise", rest=40, peak=130,
        min_rep_seconds=0.3,
        cues=["Arms all the way overhead", "Feet jump wide", "Land softly"],
        partial_cue="Bring your arms all the way up overhead.",
    ),
]

from detectors.generic import ExerciseSpec, chest_up, heel_lift, joint_angle, knee_range, no_lockout, torso_still

KNEE = joint_angle("hip", "knee", "ankle")
HIP = joint_angle("shoulder", "hip", "knee")
LEG = ["hip", "knee", "ankle"]
SIDE_VIEW = "Film from the side with your whole body in frame."

SPECS = [
    ExerciseSpec(
        name="Bulgarian Split Squat", group="Legs", icon="🦵", target="Quads & Glutes", camera=SIDE_VIEW,
        landmarks=LEG + ["shoulder"], side="grounded", metric=KNEE, metric_label="Front Knee", rest=150, peak=100,
        checks=[chest_up(35)],
        cues=["Rear foot on the bench", "Front knee to ~90°", "Upright torso"],
        partial_cue="Sink lower — get your front thigh close to parallel.",
    ),
    ExerciseSpec(
        name="Pistol Squat", group="Legs", icon="🦵", target="Quads, Glutes & Balance", camera=SIDE_VIEW,
        landmarks=LEG, side="grounded", metric=KNEE, metric_label="Standing Knee", rest=150, peak=90,
        cues=["Free leg extended forward", "Heel stays down", "Control the descent"],
        partial_cue="Go deeper — aim to get your hip below your knee.",
    ),
    ExerciseSpec(
        name="Step-Ups", group="Legs", icon="📶", target="Quads & Glutes", camera=SIDE_VIEW,
        landmarks=LEG, side="alternate", metric=KNEE, metric_label="Knee Angle", rest=110, peak=160,
        cues=["Whole foot on the box", "Drive through the lead heel", "Stand fully tall on top"],
        partial_cue="Stand all the way up on the box before stepping down.",
    ),
    ExerciseSpec(
        name="Leg Press", group="Legs", icon="🦿", target="Quads & Glutes", camera="Film from the side of the machine.",
        landmarks=LEG, metric=KNEE, metric_label="Knee Angle", rest=150, peak=95, checks=[no_lockout()],
        cues=["Feet shoulder-width, centred", "Knees to ~90°", "Never lock the knees"],
        partial_cue="Bring the sled lower — knees to about 90°.",
    ),
    ExerciseSpec(
        name="Leg Extension", group="Legs", icon="🦿", target="Quadriceps", camera="Film from the side of the machine.",
        landmarks=LEG, metric=KNEE, metric_label="Knee Angle", rest=100, peak=160,
        cues=["Back against the pad", "Extend to straight legs", "Pause and squeeze the quads"],
        partial_cue="Straighten your legs fully at the top.",
    ),
    ExerciseSpec(
        name="Leg Curl", group="Legs", icon="🦿", target="Hamstrings", camera="Film from the side.",
        landmarks=LEG, metric=KNEE, metric_label="Knee Angle", rest=150, peak=90,
        cues=["Hips stay down", "Curl heels towards glutes", "Slow return"],
        partial_cue="Curl your heels closer to your glutes.",
    ),
    ExerciseSpec(
        name="Nordic Curl", group="Legs", icon="🧎", target="Hamstrings", camera=SIDE_VIEW,
        landmarks=LEG + ["shoulder"], metric=KNEE, metric_label="Knee Angle", rest=100, peak=145,
        cues=["Anchor your ankles", "Straight line knees → head", "Lower as slowly as possible"],
        partial_cue="Lower yourself further, as slowly as you can.",
    ),
    ExerciseSpec(
        name="Hip Thrust / Glute Bridge", group="Legs", icon="🍑", target="Glutes & Hamstrings", camera=SIDE_VIEW,
        landmarks=["shoulder", "hip", "knee", "ankle"], metric=HIP, metric_label="Hip Angle", rest=140, peak=165,
        checks=[knee_range(65, 120, "Shin Angle", "Move your feet so your shins are vertical at the top.")],
        cues=["Chin tucked", "Drive through the heels", "Full hip extension + squeeze"],
        partial_cue="Push your hips higher and squeeze your glutes at the top.",
    ),
    ExerciseSpec(
        name="Donkey Kicks", group="Legs", icon="🍑", target="Glutes", camera=SIDE_VIEW,
        landmarks=["shoulder", "hip", "knee"], side="alternate", metric=HIP, metric_label="Hip Angle",
        rest=110, peak=150,
        cues=["On all fours, core braced", "Kick the heel to the ceiling", "Don't arch the lower back"],
        partial_cue="Kick higher — drive your heel up towards the ceiling.",
    ),
    ExerciseSpec(
        name="Calf Raise", group="Legs", icon="🦶", target="Calves",
        camera="Film from the side with your feet and knees clearly visible.",
        landmarks=["knee", "ankle", "heel", "foot"], side="both", metric=heel_lift(), metric_label="Heel Lift",
        unit="%", rest=0.04, peak=0.10, checks=[torso_still(15, "Stay tall — don't bounce or lean.")],
        cues=["Rise onto the balls of your feet", "Pause at the top", "Full stretch at the bottom"],
        partial_cue="Rise higher onto your toes.",
    ),
    ExerciseSpec(
        name="Wall Sit", group="Legs", icon="🧱", target="Quads", mode="hold", camera=SIDE_VIEW,
        landmarks=LEG + ["shoulder"], metric=KNEE, metric_label="Knee Angle", hold_range=(70, 115),
        checks=[torso_still(25, "Press your back flat against the wall.")],
        cues=["Thighs parallel to the floor", "Knees at ~90°", "Back flat on the wall"],
    ),
]

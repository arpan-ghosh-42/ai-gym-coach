from detectors.generic import ExerciseSpec, elbow_pinned, elbows_overhead, joint_angle, torso_hinged, torso_still

ELBOW = joint_angle("shoulder", "elbow", "wrist")
ARM = ["shoulder", "elbow", "wrist"]
SIDE_VIEW = "Film from the side with your working arm and hips in frame."

SPECS = [
    ExerciseSpec(
        name="Hammer Curl", group="Arms", icon="🔨", target="Brachialis, Biceps & Forearms", camera=SIDE_VIEW,
        landmarks=ARM + ["hip"], metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=60,
        checks=[elbow_pinned(), torso_still(15)],
        cues=["Neutral (thumbs-up) grip", "Elbows pinned", "No body swing"],
        partial_cue="Curl all the way up, then fully straighten your arm at the bottom.",
    ),
    ExerciseSpec(
        name="Barbell / Cable Curl", group="Arms", icon="💪", target="Biceps", camera=SIDE_VIEW,
        landmarks=ARM + ["hip"], metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=60,
        checks=[elbow_pinned(), torso_still(15)],
        cues=["Elbows fixed at your sides", "Full squeeze at the top", "Controlled lowering"],
        partial_cue="Use the full range — squeeze at the top, straighten at the bottom.",
    ),
    ExerciseSpec(
        name="Preacher / Concentration Curl", group="Arms", icon="💪", target="Biceps (short head)",
        camera=SIDE_VIEW, landmarks=ARM, metric=ELBOW, metric_label="Elbow Angle", rest=140, peak=60,
        cues=["Upper arm braced", "Curl to full contraction", "Slow negative"],
        partial_cue="Curl higher and lower all the way down.",
    ),
    ExerciseSpec(
        name="Triceps Pushdown", group="Arms", icon="⬇️", target="Triceps", camera=SIDE_VIEW,
        landmarks=ARM + ["hip"], metric=ELBOW, metric_label="Elbow Angle", rest=100, peak=155,
        checks=[elbow_pinned()],
        cues=["Elbows glued to your sides", "Full lockout at the bottom", "Return to ~90°"],
        partial_cue="Push all the way down until your arms are straight.",
    ),
    ExerciseSpec(
        name="Overhead Triceps Extension", group="Arms", icon="🔝", target="Triceps (long head)", camera=SIDE_VIEW,
        landmarks=ARM, metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=80, checks=[elbows_overhead()],
        cues=["Elbows point to the ceiling", "Deep stretch behind the head", "Extend fully overhead"],
        partial_cue="Lower the weight further behind your head for a full stretch.",
    ),
    ExerciseSpec(
        name="Skull Crusher", group="Arms", icon="💀", target="Triceps",
        camera="Lie on the bench and film from the side.", landmarks=ARM, metric=ELBOW, metric_label="Elbow Angle",
        rest=150, peak=80,
        cues=["Upper arms stay vertical", "Lower to the forehead", "Extend to lockout"],
        partial_cue="Lower the weight closer to your forehead.",
    ),
    ExerciseSpec(
        name="Triceps Kickback", group="Arms", icon="↩️", target="Triceps", camera=SIDE_VIEW,
        landmarks=ARM + ["hip"], metric=ELBOW, metric_label="Elbow Angle", rest=100, peak=155,
        checks=[torso_hinged(35, "Bend over more so your upper arm is parallel to the floor.")],
        cues=["Torso hinged forward", "Upper arm parallel to floor", "Squeeze at full extension"],
        partial_cue="Extend your arm all the way back until it's straight.",
    ),
]

from detectors.generic import (
    ExerciseSpec, body_line, elbows_high, hands_spread, joint_angle, knees_soft, legs_still, torso_hinged, torso_still,
)

ELBOW = joint_angle("shoulder", "elbow", "wrist")
HIP = joint_angle("shoulder", "hip", "knee")
ARM = ["shoulder", "elbow", "wrist"]
SIDE_VIEW = "Film from the side with your whole body in frame."

SPECS = [
    ExerciseSpec(
        name="Pull-ups", group="Back", icon="🧗", target="Lats, Upper Back & Biceps",
        camera="Film from the front or side — hands and hips must stay in frame.",
        landmarks=ARM + ["hip", "knee"], metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=80,
        checks=[legs_still(145)],
        cues=["Start from a dead hang", "Chin over the bar", "No kipping or leg swing"],
        partial_cue="Pull higher — get your chin over the bar, then lower to a full hang.",
    ),
    ExerciseSpec(
        name="Lat Pulldown", group="Back", icon="⬇️", target="Lats & Biceps", camera=SIDE_VIEW,
        landmarks=ARM + ["hip"], metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=80,
        checks=[torso_still(30, "Don't lean back so far — keep a slight lean and pull with your lats.")],
        cues=["Bar to upper chest", "Slight backward lean only", "Full stretch at the top"],
        partial_cue="Pull the bar all the way to your upper chest.",
    ),
    ExerciseSpec(
        name="Bent-over Row", group="Back", icon="🚣", target="Mid Back, Lats & Rear Delts", camera=SIDE_VIEW,
        landmarks=ARM + ["hip", "knee"], metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=95,
        checks=[torso_hinged(30)],
        cues=["Hinge ~45° with a flat back", "Pull elbow past the torso", "Control the lowering"],
        partial_cue="Row higher — drive your elbow back past your torso.",
    ),
    ExerciseSpec(
        name="Seated Row", group="Back", icon="🚣", target="Mid Back & Lats", camera=SIDE_VIEW,
        landmarks=ARM + ["hip"], metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=95,
        checks=[torso_still(25, "Keep your torso still — don't rock back to move the weight.")],
        cues=["Tall chest", "Handle to your stomach", "Squeeze shoulder blades"],
        partial_cue="Pull all the way to your stomach and squeeze your shoulder blades.",
    ),
    ExerciseSpec(
        name="Inverted Row", group="Back", icon="🚣", target="Upper Back & Biceps", camera=SIDE_VIEW,
        landmarks=ARM + ["hip", "ankle"], metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=95,
        checks=[body_line(155)],
        cues=["Body straight like a plank", "Chest to the bar/table", "Full arm extension"],
        partial_cue="Pull your chest closer to the bar.",
    ),
    ExerciseSpec(
        name="Face Pull", group="Back", icon="🎯", target="Rear Delts & Rotator Cuff", camera=SIDE_VIEW,
        landmarks=ARM, metric=ELBOW, metric_label="Elbow Angle", rest=150, peak=100, checks=[elbows_high()],
        cues=["Elbows high and wide", "Pull rope to your face", "External rotation at the end"],
        partial_cue="Pull the rope all the way to your face.",
    ),
    ExerciseSpec(
        name="Band Pull-Apart / Reverse Fly", group="Back", icon="↔️", target="Rear Delts & Upper Back",
        camera="Face the camera with both arms fully in frame.",
        landmarks=ARM, side="none", metric=hands_spread(), metric_label="Hand Spread", unit="%",
        rest=1.3, peak=2.3,
        cues=["Arms straight at chest height", "Pull hands wide apart", "Squeeze shoulder blades"],
        partial_cue="Pull your hands wider — open your arms fully.",
    ),
    ExerciseSpec(
        name="Deadlift", group="Back", icon="🏋️", target="Glutes, Hamstrings & Back", camera=SIDE_VIEW,
        landmarks=["shoulder", "hip", "knee", "ankle"], metric=HIP, metric_label="Hip Angle", rest=160, peak=100,
        cues=["Bar close to the shins", "Flat back, chest up", "Stand tall to lock out"],
        partial_cue="Stand all the way up and squeeze your glutes to finish the rep.",
    ),
    ExerciseSpec(
        name="Romanian Deadlift", group="Back", icon="🏋️", target="Hamstrings & Glutes", camera=SIDE_VIEW,
        landmarks=["shoulder", "hip", "knee", "ankle"], metric=HIP, metric_label="Hip Angle", rest=160, peak=120,
        checks=[knees_soft(135)],
        cues=["Soft knees, hips push back", "Weights slide down the thighs", "Feel the hamstring stretch"],
        partial_cue="Hinge further — push your hips back until you feel a hamstring stretch.",
    ),
    ExerciseSpec(
        name="Back Extension", group="Back", icon="🔙", target="Lower Back & Glutes", camera=SIDE_VIEW,
        landmarks=["shoulder", "hip", "knee"], metric=HIP, metric_label="Hip Angle", rest=115, peak=165,
        cues=["Hinge from the hips", "Rise to a straight line", "Don't hyperextend"],
        partial_cue="Rise up until your body forms a straight line.",
    ),
]

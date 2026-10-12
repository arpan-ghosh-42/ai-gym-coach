"""Config-driven exercise detector engine.

Each exercise is described by an ExerciseSpec: which body metric to follow (usually a joint angle),
where the rep starts ("rest") and where it peaks, plus a list of reusable form checks. One engine
then handles rep counting, partial-rep and tempo detection, timed holds and form feedback.
"""
import math
import time
from dataclasses import dataclass, field
from typing import Callable

from core.base_exercise import BaseExercise

LANDMARKS = {
    "nose": (0, 0),
    "shoulder": (11, 12), "elbow": (13, 14), "wrist": (15, 16),
    "hip": (23, 24), "knee": (25, 26), "ankle": (27, 28),
    "heel": (29, 30), "foot": (31, 32),
}
MIN_VISIBILITY = 0.5


class Pose:
    """Landmark helper working in aspect-corrected coordinates so angles aren't distorted by the frame shape."""

    def __init__(self, landmarks, aspect: float = 1.0):
        self.lm = landmarks
        self.aspect = aspect

    def _idx(self, name, side):
        pair = LANDMARKS[name]
        return pair[0] if side == "L" else pair[1]

    def pt(self, name, side="L"):
        p = self.lm[self._idx(name, side)]
        return (p.x * self.aspect, p.y)

    def vis(self, name, side="L"):
        return self.lm[self._idx(name, side)].visibility

    def mid(self, name):
        a, b = self.pt(name, "L"), self.pt(name, "R")
        return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)

    @staticmethod
    def _angle(a, b, c):
        ax, ay, cx, cy = a[0] - b[0], a[1] - b[1], c[0] - b[0], c[1] - b[1]
        mag = math.hypot(ax, ay) * math.hypot(cx, cy)
        if mag == 0:
            return 0.0
        return math.degrees(math.acos(max(-1.0, min(1.0, (ax * cx + ay * cy) / mag))))

    def angle(self, a, b, c, side):
        return self._angle(self.pt(a, side), self.pt(b, side), self.pt(c, side))

    @staticmethod
    def dist(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def torso_len(self):
        return max(1e-6, self.dist(self.mid("shoulder"), self.mid("hip")))

    def torso_from_vertical(self):
        """0° = upright torso, 90° = horizontal torso."""
        s, h = self.mid("shoulder"), self.mid("hip")
        dx, dy = s[0] - h[0], s[1] - h[1]
        return math.degrees(math.atan2(abs(dx), abs(dy))) if (dx or dy) else 0.0

    def side_visibility(self, names, side):
        return sum(self.vis(n, side) for n in names) / max(1, len(names))


# ── Metrics: functions of (pose, side) -> float ─────────────────────────────

def joint_angle(a, b, c):
    return lambda p, s: p.angle(a, b, c, s)


def knee_height():
    """~1 when standing (knee well below hip), ~0 when the knee is driven up to hip height."""
    return lambda p, s: (p.pt("knee", s)[1] - p.pt("hip", s)[1]) / p.torso_len()


def heel_lift():
    """How far the heel rises above the toes, relative to shin length."""
    def f(p, s):
        shin = max(1e-6, p.dist(p.pt("knee", s), p.pt("ankle", s)))
        return (p.pt("foot", s)[1] - p.pt("heel", s)[1]) / shin
    return f


def hands_spread():
    """Distance between wrists relative to shoulder width (side independent)."""
    def f(p, s):
        width = max(1e-6, p.dist(p.pt("shoulder", "L"), p.pt("shoulder", "R")))
        return p.dist(p.pt("wrist", "L"), p.pt("wrist", "R")) / width
    return f


# ── Form checks ──────────────────────────────────────────────────────────────

@dataclass
class Check:
    label: str
    fn: Callable  # (pose, side, value) -> (ok: bool | None, status: str, issue: str)


def torso_still(max_deg=15, issue="Keep your torso still — no swinging or leaning back."):
    def fn(p, s, v):
        ok = p.torso_from_vertical() <= max_deg
        return ok, "STABLE" if ok else "SWINGING", issue
    return Check("Torso", fn)


def torso_hinged(min_deg=30, issue="Hinge forward more at the hips — chest over the weight, back flat."):
    def fn(p, s, v):
        ok = p.torso_from_vertical() >= min_deg
        return ok, "GOOD HINGE" if ok else "TOO UPRIGHT", issue
    return Check("Hip Hinge", fn)


def body_line(min_angle=160, end="ankle", label="Body Line"):
    def fn(p, s, v):
        sh, hip, e = p.pt("shoulder", s), p.pt("hip", s), p.pt(end, s)
        if p._angle(sh, hip, e) >= min_angle:
            return True, "ALIGNED", ""
        if abs(e[0] - sh[0]) > 1e-6:
            line_y = sh[1] + (hip[0] - sh[0]) * (e[1] - sh[1]) / (e[0] - sh[0])
            if hip[1] > line_y:
                return False, "HIPS SAGGING", "Your hips are sagging — squeeze your glutes and brace your core."
        return False, "HIPS TOO HIGH", "Lower your hips so your body forms one straight line."
    return Check(label, fn)


def elbow_pinned(max_ratio=0.35, issue="Keep your elbow pinned to your side — only the forearm should move."):
    def fn(p, s, v):
        drift = abs(p.pt("elbow", s)[0] - p.pt("shoulder", s)[0]) / p.torso_len()
        ok = drift <= max_ratio
        return ok, "PINNED" if ok else "ELBOW DRIFTING", issue
    return Check("Elbow Position", fn)


def elbows_high(issue="Keep your elbows up at shoulder height."):
    def fn(p, s, v):
        ok = p.pt("elbow", s)[1] <= p.pt("shoulder", s)[1] + 0.1 * p.torso_len()
        return ok, "ELBOWS UP" if ok else "ELBOWS DROPPING", issue
    return Check("Elbow Height", fn)


def elbows_overhead(issue="Keep your elbows pointing up beside your head — don't let them drop forward."):
    def fn(p, s, v):
        ok = p.pt("elbow", s)[1] < p.pt("shoulder", s)[1]
        return ok, "ELBOWS UP" if ok else "ELBOWS DROPPING", issue
    return Check("Upper Arm", fn)


def knees_soft(min_knee=135, issue="Too much knee bend — push your hips back instead of squatting down."):
    def fn(p, s, v):
        ok = p.angle("hip", "knee", "ankle", s) >= min_knee
        return ok, "HIPS BACK" if ok else "TOO MUCH KNEE BEND", issue
    return Check("Knee Bend", fn)


def knee_range(lo, hi, label="Knee Angle", issue="Adjust your feet so your knees sit at about 90°."):
    def fn(p, s, v):
        k = p.angle("hip", "knee", "ankle", s)
        ok = lo <= k <= hi
        return ok, "GOOD" if ok else ("TOO BENT" if k < lo else "TOO STRAIGHT"), issue
    return Check(label, fn)


def no_lockout(joint=("hip", "knee", "ankle"), max_angle=176, label="Lockout",
               issue="Don't snap your joints into lockout — keep a soft bend to protect them."):
    def fn(p, s, v):
        ok = p.angle(*joint, s) <= max_angle
        return ok, "SOFT" if ok else "LOCKED OUT", issue
    return Check(label, fn)


def hips_piked(max_hip=125):
    def fn(p, s, v):
        ok = p.angle("shoulder", "hip", "ankle", s) <= max_hip
        return ok, "PIKED" if ok else "HIPS TOO LOW", "Walk your feet in and lift your hips high into an upside-down V."
    return Check("Hip Position", fn)


def legs_still(min_hip=145):
    def fn(p, s, v):
        ok = p.angle("shoulder", "hip", "knee", s) >= min_hip
        return ok, "STILL" if ok else "KIPPING", "Stop swinging your legs — pull with your back, not momentum."
    return Check("Leg Swing", fn)


def arms_soft(min_elbow=130):
    def fn(p, s, v):
        ok = p.angle("shoulder", "elbow", "wrist", s) >= min_elbow
        return ok, "SOFT BEND" if ok else "ARMS TOO BENT", "Keep only a slight bend in your elbows — hug a big tree."
    return Check("Arm Shape", fn)


def horizontal(max_from_horizontal=35, issue="Get into position — body roughly parallel to the floor."):
    def fn(p, s, v):
        ok = p.torso_from_vertical() >= 90 - max_from_horizontal
        return ok, "IN POSITION" if ok else "NOT HORIZONTAL", issue
    return Check("Body Position", fn)


def chest_up(max_lean=50):
    def fn(p, s, v):
        ok = p.torso_from_vertical() <= max_lean
        return ok, "CHEST UP" if ok else "LEANING FORWARD", "Lift your chest — don't fold forward over your knees."
    return Check("Torso", fn)


# ── Spec ─────────────────────────────────────────────────────────────────────

@dataclass
class ExerciseSpec:
    name: str
    group: str
    icon: str
    target: str
    camera: str                       # placement tip shown to the user
    landmarks: list                   # landmark names that must be visible
    metric: Callable | None = None    # (pose, side) -> value
    metric_label: str = "Joint Angle"
    unit: str = "°"
    rest: float = 0.0                 # value at the start/end of a rep
    peak: float = 0.0                 # value at the top/bottom of a rep
    side: str = "best"                # best | both | alternate | grounded | raised | none
    mode: str = "reps"                # reps | hold
    hold_range: tuple = (0.0, 0.0)    # metric range that counts as "in position" for holds
    checks: list = field(default_factory=list)
    cues: list = field(default_factory=list)  # checkpoints shown on the exercise card
    min_rep_seconds: float = 0.55     # measured from leaving the start position until returning to it
    partial_cue: str = "Partial rep — use your full range of motion."
    factory: Callable | None = None   # legacy hand-written detector class


class _RepMachine:
    """rest -> moving -> peak -> rest = 1 rep. Returning to rest without reaching peak = partial rep."""

    def __init__(self, rest, peak):
        self.rest, self.peak = rest, peak
        self.state, self.started = "rest", 0.0
        self.smoothed = None
        self.last_duration = 0.0

    def progress(self, value):
        span = self.peak - self.rest
        return (value - self.rest) / span if span else 0.0

    def update(self, value, now):
        # Light smoothing: removes landmark jitter without lagging behind fast reps (jumping jacks, high knees).
        self.smoothed = value if self.smoothed is None else 0.3 * self.smoothed + 0.7 * value
        pr = self.progress(self.smoothed)
        if self.state == "rest" and pr >= 0.35:
            self.state, self.started = "moving", now
        if self.state == "moving":
            # The raw reading also counts for reaching the peak, so fast reps aren't lost to smoothing lag.
            if max(pr, self.progress(value)) >= 1.0:
                self.state = "peak"
            elif pr <= 0.0:
                self.state = "rest"
                return "partial"
        elif self.state == "peak" and pr <= 0.0:
            self.state = "rest"
            self.last_duration = now - self.started
            return "rep"
        return None


class GenericDetector(BaseExercise):
    def __init__(self, spec: ExerciseSpec):
        super().__init__()
        self.spec = spec
        self.aspect = 1.0
        self.reset()

    def reset(self):
        self.reps = 0
        self.stage = None
        self.partial_reps = 0
        self.hold_seconds = 0.0
        self._last_t = None
        self._cue, self._cue_until = None, 0.0
        self._machines = {s: _RepMachine(self.spec.rest, self.spec.peak) for s in ("L", "R", "X")}

    def _sides(self, p):
        names = self.spec.landmarks
        mode = self.spec.side
        if mode == "none":
            return ["L"]
        if mode in ("both", "alternate"):
            return [s for s in ("L", "R") if p.side_visibility(names, s) >= MIN_VISIBILITY] or [None]
        if mode == "grounded":
            return [max(("L", "R"), key=lambda s: p.pt("ankle", s)[1])]
        if mode == "raised":
            return [min(("L", "R"), key=lambda s: p.pt("ankle", s)[1])]
        return [max(("L", "R"), key=lambda s: p.side_visibility(names, s))]

    def _visible(self, p, sides):
        if None in sides:
            return False
        if self.spec.side == "none":
            return all(p.vis(n, s) >= MIN_VISIBILITY for n in self.spec.landmarks for s in ("L", "R"))
        return all(p.vis(n, s) >= MIN_VISIBILITY for n in self.spec.landmarks for s in sides)

    def _set_cue(self, text, now, seconds=2.5):
        self._cue, self._cue_until = text, now + seconds

    def process(self, landmarks) -> dict:
        spec, now = self.spec, time.monotonic()
        p = Pose(landmarks, self.aspect)
        sides = self._sides(p)
        base = {"mode": spec.mode, "metric_label": spec.metric_label, "unit": spec.unit,
                "partial_reps": self.partial_reps}

        if not self._visible(p, sides):
            self._last_t = None
            return {**base, "reps": self.reps, "primary_angle": 0, "phase": "ADJUST CAMERA", "progress": 0.0,
                    "checks": [], "issue": f"I can't see you clearly. {spec.camera}"}

        values = {s: spec.metric(p, s) for s in sides}
        value = sum(values.values()) / len(values)

        check_results = []
        for check in spec.checks:
            ok, status, issue = check.fn(p, sides[0], value)
            check_results.append({"label": check.label, "status": status, "ok": ok, "issue": issue})
        if spec.side == "both" and len(values) == 2 and spec.mode == "reps":
            diff = abs(values["L"] - values["R"])
            span = abs(spec.peak - spec.rest) or 1
            ok = diff <= 0.35 * span
            check_results.append({"label": "Symmetry", "status": "EVEN" if ok else "UNEVEN", "ok": ok,
                                  "issue": "Move both sides together — one arm is lagging behind."})

        if spec.mode == "hold":
            lo, hi = spec.hold_range
            in_position = lo <= value <= hi and all(c["ok"] for c in check_results)
            if in_position and self._last_t is not None:
                self.hold_seconds += now - self._last_t
            self._last_t = now
            self.reps = int(self.hold_seconds)
            phase = "HOLDING" if in_position else "GET IN POSITION"
            progress = 1.0 if in_position else 0.0
        else:
            machine_keys = sides if spec.side == "alternate" else ["X"]
            for key in machine_keys:
                m = self._machines[key]
                event = m.update(values[key] if key in values else value, now)
                if event == "rep":
                    self.reps += 1
                    if m.last_duration < spec.min_rep_seconds:
                        self._set_cue("Too fast — slow down and control every rep.", now)
                elif event == "partial":
                    self.partial_reps += 1
                    self._set_cue(spec.partial_cue, now)
            m = self._machines[machine_keys[0]]
            progress = max(0.0, min(1.0, m.progress(m.smoothed if m.smoothed is not None else value)))
            phase = {"rest": "READY", "moving": "MOVING", "peak": "PEAK"}[m.state]
            self.stage = m.state

        failing = next((c for c in check_results if c["ok"] is False), None)
        issue = failing["issue"] if failing else (self._cue if now < self._cue_until else None)

        display = value * 100 if spec.unit == "%" else value
        return {**base, "reps": self.reps, "primary_angle": int(round(display)),
                "phase": phase, "progress": round(progress, 2), "partial_reps": self.partial_reps,
                "checks": [{k: c[k] for k in ("label", "status", "ok")} for c in check_results], "issue": issue}

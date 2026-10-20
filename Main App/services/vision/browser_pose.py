"""Browser-side live pose tracking.

MediaPipe Tasks JS runs pose detection on the athlete's own device; batches of landmarks come back
to Python, where the existing detectors count reps and check form. This replaces the
streamlit-webrtc pipeline, which needed a TURN relay on hosts like Render (no inbound UDP) and
spent server CPU decoding, analysing and re-encoding every video frame.
"""
from types import SimpleNamespace

import streamlit as st

from detectors.registry import EXERCISES, create_detector, is_legacy
from services.config.workout_config import POSE_CONNECTIONS

TASKS_VERSION = "0.10.35"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
             "pose_landmarker_full/float16/latest/pose_landmarker_full.task")

_CSS = """
.cx-root { position: relative; width: 100%; background: #05080f; border-radius: 14px; overflow: hidden;
           min-height: 320px; display: flex; align-items: center; justify-content: center; }
.cx-root canvas { display: block; width: 100%; height: auto; }
.cx-root video { display: none; }
.cx-status { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
             text-align: center; padding: 1.5rem; color: #e2e8f0; font: 600 15px/1.5 system-ui, sans-serif;
             background: rgba(5, 8, 15, 0.82); }
.cx-status.cx-hidden { display: none; }
.cx-status.cx-error { color: #ffb74d; }
"""

_JS = r"""
const TASKS_URL = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@__TASKS_VERSION__";
const SEND_INTERVAL_MS = 400;   // how often landmark batches go to Python
const MIN_FRAME_GAP_MS = 33;    // cap detection at ~30 fps
const MAX_BUFFER = 150;         // unacknowledged frames kept for resending
const VIS = 0.7;                // same drawing threshold as the old server-side overlay

// One engine per component key, kept across Streamlit reruns so the camera never restarts.
const engines = (window.__coachxPoseEngines = window.__coachxPoseEngines || new Map());

function createEngine() {
  const root = document.createElement("div");
  root.className = "cx-root";
  const video = document.createElement("video");
  video.autoplay = true; video.muted = true; video.playsInline = true;
  const canvas = document.createElement("canvas");
  canvas.width = 640; canvas.height = 480;
  const status = document.createElement("div");
  status.className = "cx-status";
  status.textContent = "Starting camera…";
  root.append(video, canvas, status);

  const ctx = canvas.getContext("2d");
  const mirror = document.createElement("canvas");   // mirrored frame, exactly what the athlete sees
  const mctx = mirror.getContext("2d", { willReadFrequently: false });

  const eng = {
    root, data: {}, setTrigger: null, stopTimer: null, stopped: false,
    stream: null, landmarker: null, seq: 0, acked: -1, buffer: [], lastSent: 0, lastDetect: 0,
    lastLandmarks: null,
  };

  const setStatus = (text, isError = false) => {
    status.textContent = text || "";
    status.classList.toggle("cx-hidden", !text);
    status.classList.toggle("cx-error", !!isError);
  };

  eng.update = (data) => {
    eng.data = data || {};
    if (typeof eng.data.ack === "number" && eng.data.ack > eng.acked) {
      eng.acked = eng.data.ack;
      eng.buffer = eng.buffer.filter((f) => f.s > eng.acked);
    }
  };

  eng.stop = () => {
    eng.stopped = true;
    if (eng.stream) eng.stream.getTracks().forEach((t) => t.stop());
    if (eng.landmarker) { try { eng.landmarker.close(); } catch (e) {} }
    root.remove();
  };

  const drawOverlay = (w, h) => {
    const o = eng.data.overlay || {};
    const conns = eng.data.connections || [];
    const lm = eng.lastLandmarks;
    if (lm) {
      ctx.lineWidth = Math.max(3, w / 160);
      ctx.strokeStyle = "#00e676";
      for (const [a, b] of conns) {
        const p = lm[a], q = lm[b];
        if (p && q && p.visibility > VIS && q.visibility > VIS) {
          ctx.beginPath(); ctx.moveTo(p.x * w, p.y * h); ctx.lineTo(q.x * w, q.y * h); ctx.stroke();
        }
      }
      ctx.fillStyle = "#00b0ff";
      for (const p of lm) {
        if (p.visibility > VIS) { ctx.beginPath(); ctx.arc(p.x * w, p.y * h, Math.max(3, w / 140), 0, 2 * Math.PI); ctx.fill(); }
      }
    }
    // Header panel (Python-provided counters), like the old OpenCV overlay.
    const s = w / 640;
    ctx.fillStyle = "rgba(16,18,24,0.6)";
    ctx.fillRect(10 * s, 10 * s, Math.min(w - 20 * s, 430 * s), 96 * s);
    ctx.fillStyle = "#ffffff";
    ctx.font = `700 ${18 * s}px system-ui, sans-serif`;
    ctx.fillText((o.title || "").toUpperCase().slice(0, 30), 22 * s, 36 * s);
    ctx.fillStyle = "#00e676";
    ctx.font = `800 ${28 * s}px system-ui, sans-serif`;
    ctx.fillText(o.counter || "", 22 * s, 70 * s);
    ctx.fillStyle = "#e2e8f0";
    ctx.font = `600 ${14 * s}px system-ui, sans-serif`;
    ctx.fillText((o.line || "").slice(0, 60), 22 * s, 94 * s);
    if (!lm) {
      ctx.fillStyle = "#00e676";
      ctx.font = `800 ${24 * s}px system-ui, sans-serif`;
      ctx.fillText("NO POSE DETECTED — STEP INTO THE FRAME", 22 * s, h - 24 * s);
    } else {
      const issue = o.issue;
      ctx.fillStyle = issue ? "#ff9100" : "#00e676";
      ctx.font = `700 ${17 * s}px system-ui, sans-serif`;
      ctx.fillText((issue ? `FIX: ${issue}` : "FORM: GOOD").slice(0, 70), 20 * s, h - 20 * s);
    }
  };

  const send = (now) => {
    if (!eng.setTrigger || now - eng.lastSent < SEND_INTERVAL_MS) return;
    const frames = eng.buffer.filter((f) => f.s > eng.acked);
    if (!frames.length) return;
    eng.lastSent = now;
    // Every message carries all unacknowledged frames, so a dropped or merged event loses nothing;
    // Python skips frames it has already processed.
    eng.setTrigger("frames", { aspect: mirror.width / (mirror.height || 1), frames });
  };

  const loop = () => {
    if (eng.stopped) return;
    requestAnimationFrame(loop);
    const now = performance.now();
    if (!video.videoWidth || now - eng.lastDetect < MIN_FRAME_GAP_MS) return;
    eng.lastDetect = now;

    const w = video.videoWidth, h = video.videoHeight;
    if (mirror.width !== w || mirror.height !== h) { mirror.width = w; mirror.height = h; canvas.width = w; canvas.height = h; }
    mctx.save(); mctx.translate(w, 0); mctx.scale(-1, 1); mctx.drawImage(video, 0, 0, w, h); mctx.restore();

    let lm = null;
    if (eng.landmarker) {
      try {
        const res = eng.landmarker.detectForVideo(mirror, now);
        lm = res.landmarks && res.landmarks.length ? res.landmarks[0] : null;
      } catch (e) { console.warn("pose detection failed", e); }
      eng.lastLandmarks = lm;
      eng.buffer.push({
        s: eng.seq++,
        t: Math.round(now) / 1000,
        l: lm ? lm.flatMap((p) => [+p.x.toFixed(4), +p.y.toFixed(4), +(p.visibility ?? 0).toFixed(3)]) : null,
      });
      if (eng.buffer.length > MAX_BUFFER) eng.buffer.splice(0, eng.buffer.length - MAX_BUFFER);
    }

    ctx.drawImage(mirror, 0, 0);
    drawOverlay(w, h);
    send(now);
  };

  (async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("This browser can't open the camera here (the page must be served over HTTPS).");
      }
      eng.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } }, audio: false,
      });
      if (eng.stopped) { eng.stream.getTracks().forEach((t) => t.stop()); return; }
      video.srcObject = eng.stream;
      await video.play().catch(() => {});
      requestAnimationFrame(loop);

      setStatus("Loading AI pose model…");
      const { FilesetResolver, PoseLandmarker } = await import(`${TASKS_URL}/vision_bundle.mjs`);
      const fileset = await FilesetResolver.forVisionTasks(`${TASKS_URL}/wasm`);
      const make = (delegate) => PoseLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: eng.data.model_url, delegate },
        runningMode: "VIDEO", numPoses: 1,
        minPoseDetectionConfidence: 0.7, minPosePresenceConfidence: 0.7, minTrackingConfidence: 0.7,
      });
      try { eng.landmarker = await make("GPU"); } catch (e) { eng.landmarker = await make("CPU"); }
      if (eng.stopped) { eng.landmarker.close(); return; }
      setStatus("");
    } catch (err) {
      const name = err && err.name;
      const msg = name === "NotAllowedError" ? "Camera access was blocked. Allow the camera for this site in your browser's address bar, then press 🔄 Restart Camera."
        : name === "NotFoundError" ? "No camera was found on this device."
        : name === "NotReadableError" ? "The camera is busy in another app or tab. Close it, then press 🔄 Restart Camera."
        : `Couldn't start live tracking: ${(err && err.message) || err}`;
      setStatus(msg, true);
    }
  })();

  return eng;
}

export default function (component) {
  const { data, parentElement, setTriggerValue } = component;
  const id = (data && data.engine_id) || "default";
  for (const [otherId, other] of engines) {   // a restart or a new workout replaces the old engine
    if (otherId !== id) { clearTimeout(other.stopTimer); other.stop(); engines.delete(otherId); }
  }
  let eng = engines.get(id);
  if (!eng || eng.stopped) { eng = createEngine(); engines.set(id, eng); }
  clearTimeout(eng.stopTimer);
  if (eng.root.parentNode !== parentElement) parentElement.appendChild(eng.root);
  eng.setTrigger = setTriggerValue;
  eng.update(data);
  // Streamlit may call this cleanup between reruns; only stop if we are not re-mounted shortly after.
  return () => {
    eng.stopTimer = setTimeout(() => { eng.stop(); engines.delete(id); }, 2500);
  };
}
""".replace("__TASKS_VERSION__", TASKS_VERSION)

_pose_camera = st.components.v2.component("coachx_pose_camera", js=_JS, css=_CSS)


def _landmarks(flat):
    return [SimpleNamespace(x=flat[i], y=flat[i + 1], z=0.0, visibility=flat[i + 2]) for i in range(0, len(flat), 3)]


def _detector(exercise, engine_id):
    """Detector state lives in the session, recreated whenever a new camera session or exercise starts."""
    state = st.session_state.get("_browser_pose")
    if not state or state["exercise"] != exercise or state["engine_id"] != engine_id:
        state = {"exercise": exercise, "engine_id": engine_id, "detector": create_detector(exercise),
                 "last_seq": -1, "latest": None}
        st.session_state["_browser_pose"] = state
    return state


def _process(state, payload) -> dict | None:
    exercise, detector = state["exercise"], state["detector"]
    aspect = float(payload.get("aspect") or 1.0)
    latest = None
    for frame in payload.get("frames") or []:
        seq = frame.get("s", -1)
        if seq <= state["last_seq"]:
            continue
        state["last_seq"] = seq
        flat = frame.get("l")
        if not flat or len(flat) < 99:
            latest = {**(latest or state["latest"] or {}), "pose_detected": False}
            continue
        if not is_legacy(exercise):
            detector.aspect = aspect
            metrics = detector.process(_landmarks(flat), now=frame.get("t"))
        else:
            metrics = detector.process(_landmarks(flat))
        metrics["pose_detected"] = True
        latest = metrics
    if latest is not None:
        state["latest"] = latest
    return latest


def _overlay(exercise, metrics) -> dict:
    """Text for the on-video HUD, mirroring the old server-side OpenCV overlay."""
    m = metrics or {}
    spec = EXERCISES.get(exercise)
    hold = bool(spec) and spec.mode == "hold"
    counter = f"TIME: {m.get('reps', 0)}s" if hold else f"REPS: {m.get('reps', 0)}"
    legacy_lines = {
        "Squats": lambda: f"DEPTH: {m.get('depth_status', '—')}",
        "Push-ups": lambda: f"BODY: {m.get('body_alignment', '—')} | HIP: {m.get('hip_status', '—')}",
        "Biceps Curls (Dumbbell)": lambda: f"SWING: {m.get('swing_status', '—')}",
        "Shoulder Press": lambda: f"EXT: {m.get('extension_status', '—')} | BACK: {m.get('back_arch_status', '—')}",
        "Lunges": lambda: f"BALANCE: {m.get('balance_status', '—')}",
    }
    if exercise in legacy_lines:
        line = legacy_lines[exercise]()
    else:
        unit = "" if m.get("unit") == "%" else "°"
        line = f"{m.get('metric_label', '')}: {m.get('primary_angle', 0)}{unit}  [{m.get('phase', 'WAITING')}]"
    return {"title": exercise, "counter": counter, "line": line, "issue": m.get("issue")}


def browser_pose_camera(exercise: str, engine_id: str, key: str = "pose-camera") -> dict | None:
    """Renders the live camera and returns the newest detector metrics produced in this run (or None)."""
    state = _detector(exercise, engine_id)
    result = _pose_camera(
        key=key,
        data={
            "engine_id": engine_id,
            "model_url": MODEL_URL,
            "connections": [list(c) for c in POSE_CONNECTIONS],
            "ack": state["last_seq"],
            "overlay": _overlay(exercise, state["latest"]),
        },
        on_frames_change=lambda: None,
    )
    payload = result.frames if result is not None else None
    # TEMP debug for Render: one line per run.
    import time as _t
    t0 = _t.perf_counter()
    out = _process(state, payload) if isinstance(payload, dict) else None
    print(f"[pose-debug] payload={type(payload).__name__} frames={len(payload.get('frames') or []) if isinstance(payload, dict) else 0} "
          f"last_seq={state['last_seq']} took={_t.perf_counter() - t0:.3f}s", flush=True)
    return out

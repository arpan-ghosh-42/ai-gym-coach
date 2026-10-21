import json
import os
import time
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitAPIException
from streamlit_webrtc import WebRtcMode, webrtc_streamer

from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from detectors.registry import EXERCISES, grouped, is_hold, is_legacy
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio
from services.persistence.exercise_repository import get_users_exercises
from services.state.session_defaults import initial_session_defaults
from services.tracking.metrics import sync_metrics_update
from services.ui.style_loader import inject_webrtc_styles
from services.vision.browser_pose import browser_pose_camera
from views.common import get_groq_client, pal

EXERCISE_NAMES = list(EXERCISES)

# WebRTC streams the camera to the server, where MediaPipe and the detectors run in Python. If it can't connect
# (e.g. no TURN relay, or a network that blocks it), the page falls back to on-device tracking after this long.
WEBRTC_CONNECT_TIMEOUT_S = 20
DEMO_DIR = Path(__file__).resolve().parent.parent / "static" / "demo"


def _rtc_configurations() -> tuple[dict | None, dict | None]:
    """(browser, server) ICE config. Hosts like Render can't receive inbound UDP, so a TURN relay is needed there.

    TURN_URLS (comma-separated, e.g. Metered's "turn:global.relay.metered.ca:80,...:443?transport=tcp")
    + TURN_USERNAME + TURN_CREDENTIAL set the relay. Without them (None), streamlit-webrtc picks servers itself:
    Hugging Face's TURN when HF_TOKEN is set, Twilio's with TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN, else STUN only.
    """
    turn_urls = [u.strip() for u in os.environ.get("TURN_URLS", "").split(",") if u.strip()]
    if not turn_urls:
        return None, None
    creds = {"username": os.environ.get("TURN_USERNAME", ""), "credential": os.environ.get("TURN_CREDENTIAL", "")}
    stun = {"urls": ["stun:stun.l.google.com:19302"]}
    # aiortc (server side) only uses the first TURN URL; TCP works whether or not outbound UDP is allowed.
    server_urls = sorted(turn_urls, key=lambda u: "transport=tcp" not in u)
    return ({"iceServers": [stun, {"urls": turn_urls, **creds}]},
            {"iceServers": [stun, {"urls": server_urls, **creds}]})


def _rerun_live_session():
    # A fragment-scoped rerun is only allowed during a fragment run, not when the fragment runs as part of the app.
    try:
        st.rerun(scope="fragment")
    except StreamlitAPIException:
        st.rerun()


def _webrtc_camera(ex):
    # Imported lazily so MediaPipe only loads when the WebRTC camera is actually used.
    from services.vision.exercise_video_processor import VideoProcessorClass

    frontend_rtc, server_rtc = _rtc_configurations()
    ctx = webrtc_streamer(
        key="exercise-analysis",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=VideoProcessorClass,
        frontend_rtc_configuration=frontend_rtc,
        server_rtc_configuration=server_rtc,
        # Modest resolution / frame rate: every frame is decoded, analysed and re-encoded on the server.
        media_stream_constraints={"video": {"width": {"ideal": 640}, "height": {"ideal": 480},
                                            "frameRate": {"ideal": 15, "max": 20}}, "audio": False},
        async_processing=True,
    )
    inject_webrtc_styles()
    latest = None
    if ctx.state.playing and ctx.video_processor:
        ctx.video_processor.set_exercise(ex)
        latest = ctx.video_processor.get_latest_metrics()
    return ctx, latest


def _webrtc_failed(ctx) -> bool:
    """True once a WebRTC connection attempt has clearly failed: still connecting after the timeout,
    or the attempt ended without the stream ever playing."""
    s = st.session_state
    if ctx.state.playing:
        s.webrtc_connecting_since = None
        return False
    since = s.get("webrtc_connecting_since")
    if ctx.state.signalling:
        if since is None:
            s.webrtc_connecting_since = time.time()
            return False
        return time.time() - since > WEBRTC_CONNECT_TIMEOUT_S
    return since is not None  # idle again after an attempt that never started playing


def _set_camera_mode(mode, notice=None):
    st.session_state.camera_mode = mode
    st.session_state.camera_notice = notice
    st.session_state.webrtc_connecting_since = None
    st.session_state.camera_session = f"cam-{time.time_ns()}"


def render_demo_video(P):
    """Pre-rendered sample set (scripts/build_demo_video.py): the live WebRTC pipeline run on a stock clip."""
    video = DEMO_DIR / "squats_demo.mp4"
    if not video.exists():
        return
    summary = {}
    try:
        summary = json.loads((DEMO_DIR / "squats_demo.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    v_col, t_col = st.columns([3, 2], gap="large")
    with v_col:
        st.video(str(video), loop=True, autoplay=True, muted=True)
    with t_col:
        reps = summary.get("reps") or []
        rep_list = " · ".join(f"rep {r['rep']} at {r['at_s']}s" for r in reps)
        st.markdown(f"""
        <div style="background:{P['card']};border:1px solid {P['border']};border-radius:14px;padding:1.1rem 1.3rem;">
            <div style="font-size:0.75rem;font-weight:700;color:{P['accent']};text-transform:uppercase;letter-spacing:0.08em;">
                No camera needed</div>
            <div style="font-size:1.6rem;font-weight:800;color:{P['text']};margin:4px 0;">
                {summary.get('reps_counted', len(reps))} squats counted</div>
            <div style="font-size:0.85rem;color:{P['muted']};line-height:1.55;">
                A sample set analysed by the same Python pipeline the live camera uses:
                MediaPipe pose landmarks → squat detector → rep counter &amp; depth check.<br>
                <span style="color:{P['faint']};">{rep_list}</span>
            </div>
        </div>""", unsafe_allow_html=True)


def _unit_label(exercise):
    return "Seconds / Set" if is_hold(exercise) else "Reps / Set"


def badge(val: str) -> str:
    v = str(val).lower()
    if any(k in v for k in ["good", "optimal", "parallel", "aligned", "locked", "stable"]):
        return f'<span style="background:rgba(0,230,118,0.15);color:#00E676;border:1px solid rgba(0,230,118,0.3);padding:3px 8px;border-radius:6px;font-size:0.78rem;font-weight:700;">● {val}</span>'
    elif any(k in v for k in ["shallow", "warning", "sagging", "swing", "arch", "unstable"]):
        return f'<span style="background:rgba(255,145,0,0.15);color:#FF9100;border:1px solid rgba(255,145,0,0.3);padding:3px 8px;border-radius:6px;font-size:0.78rem;font-weight:700;">▲ {val}</span>'
    return f'<span style="background:rgba(148,163,184,0.12);color:{"#CBD5E1" if pal()["dark"] else "#334155"};border:1px solid rgba(148,163,184,0.25);padding:3px 8px;border-radius:6px;font-size:0.78rem;font-weight:600;">{val}</span>'


def hud_angle(label, sub, value, unit="°"):
    P = pal()
    return f"""
    <div style="background:{P['card']};
        border:1px solid {P['border']};border-radius:12px;
        padding:0.9rem 1.1rem;margin-bottom:0.7rem;
        display:flex;justify-content:space-between;align-items:center;">
        <div>
            <div style="font-size:0.8rem;font-weight:700;color:{P['muted']};text-transform:uppercase;letter-spacing:0.05em;">{label}</div>
            <div style="font-size:0.72rem;color:{P['faint']};">{sub}</div>
        </div>
        <div style="font-size:1.7rem;font-weight:800;color:{P['text']};font-family:Space Grotesk,sans-serif;">{value}{unit}</div>
    </div>"""


def hud_status(label, value):
    P = pal()
    return f"""
    <div style="background:{P['card']};
        border:1px solid {P['border']};border-radius:12px;
        padding:0.9rem 1.1rem;margin-bottom:0.7rem;
        display:flex;justify-content:space-between;align-items:center;">
        <div style="font-size:0.8rem;font-weight:700;color:{P['muted']};text-transform:uppercase;letter-spacing:0.05em;">{label}</div>
        <div>{badge(value)}</div>
    </div>"""


def _init_voice_pipeline():
    if "voice_pipeline" in st.session_state:
        return
    try:
        client = get_groq_client()
        st.session_state.voice_pipeline = VoicePipeline(LLMCoach(client), TextToSpeech()) if client else None
    except Exception:
        st.session_state.voice_pipeline = None


def _start_workout(exercise, sets, reps, announce=False):
    st.session_state.exercise_type = exercise
    st.session_state.target_sets = int(sets)
    st.session_state.reps_per_set = int(reps)
    st.session_state.reps = 0
    st.session_state.live_metrics = {}
    st.session_state.workout_started = True
    st.session_state.set_cycle_started_at = time.time()
    st.session_state.last_saved_sets_completed = 0
    st.session_state.last_notified_sets_completed = 0
    st.session_state.last_notified_workout_complete = False
    st.session_state.camera_session = f"cam-{time.time_ns()}"  # fresh browser camera + detector per workout
    st.session_state.webrtc_connecting_since = None  # camera_mode is kept, so a failed WebRTC isn't retried each time
    if announce and st.session_state.get("voice_pipeline"):
        result = st.session_state.voice_pipeline.process_event("workout_started", exercise, {})
        if result:
            st.session_state.audio_to_play, st.session_state.coach_feedback = result
    st.rerun()


def _end_workout(exercise):
    st.session_state.workout_started = False
    if st.session_state.get("voice_pipeline"):
        result = st.session_state.voice_pipeline.process_event("workout_completed", exercise, {})
        if result:
            st.session_state.audio_to_play, st.session_state.coach_feedback = result
    st.rerun()


def _sidebar(P, workout_started):
    with st.sidebar:
        st.subheader("⚙️ Session Plan")

        if not workout_started:
            current = st.session_state.get("plan_exercise", "Squats")
            default_idx = EXERCISE_NAMES.index(current) if current in EXERCISE_NAMES else 0
            plan_exercise = st.selectbox("Exercise Target", options=EXERCISE_NAMES, index=default_idx,
                                         format_func=lambda n: f"{EXERCISES[n].icon} {n}  ·  {EXERCISES[n].group}")
            st.session_state["plan_exercise"] = plan_exercise
            col_s, col_r = st.columns(2)
            with col_s:
                plan_sets = st.number_input("Sets", min_value=1, max_value=50, value=int(st.session_state.get("plan_sets", 3)), step=1)
            with col_r:
                plan_reps = st.number_input(_unit_label(plan_exercise), min_value=1, max_value=300, value=int(st.session_state.get("plan_reps", 10)), step=1)
            st.session_state["plan_sets"] = plan_sets
            st.session_state["plan_reps"] = plan_reps
            unit = "seconds of hold" if is_hold(plan_exercise) else "total reps"
            st.caption(f"🎯 Volume: **{plan_sets * plan_reps} {unit}**")
            st.caption(f"📷 {EXERCISES[plan_exercise].camera}")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Start Workout", use_container_width=True, type="primary", key="sb_start"):
                _start_workout(plan_exercise, plan_sets, plan_reps, announce=True)
        else:
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")
            st.markdown(f"""
            <div style="background:{P['accent_bg']};border:1px solid {P['accent_border']};
                border-radius:10px;padding:10px 13px;margin-bottom:1rem;">
                <div style="font-weight:700;color:{P['text']};">{exercise}</div>
                <div style="font-size:0.83rem;color:{P['muted']};">Target: <strong>{sets} Sets × {reps} Reps</strong></div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🛑 End Workout", use_container_width=True, key="sb_end"):
                _end_workout(exercise)


def _exercise_picker(P):
    chosen = st.session_state.get("plan_exercise", "Squats")
    if chosen not in EXERCISES:
        chosen = "Squats"
    meta = EXERCISES[chosen]
    sv = int(st.session_state.get("plan_sets", 3))
    rv = int(st.session_state.get("plan_reps", 10))
    hold = is_hold(chosen)

    st.markdown(f"""
    <div style="background:{P['card_hero']};
        border:1px solid {P['accent_border']};border-radius:20px;padding:2rem;
        box-shadow:{P['shadow']};margin-bottom:2rem;">
        <div style="display:inline-flex;align-items:center;gap:6px;padding:3px 12px;
            background:{P['accent_bg']};border:1px solid {P['accent_border']};
            border-radius:20px;color:{P['accent']};font-size:0.75rem;font-weight:700;
            text-transform:uppercase;margin-bottom:10px;">REAL-TIME POSE CORRECTOR</div>
        <div style="font-size:2.2rem;font-weight:800;color:{P['text']};margin-bottom:4px;">
            {meta.icon} {chosen}
        </div>
        <div style="color:{P['muted']};font-size:1rem;margin-bottom:0.4rem;">
            Muscles: <strong style="color:{P['accent']};">{meta.target}</strong>
        </div>
        <div style="color:{P['muted']};font-size:0.88rem;margin-bottom:1.2rem;">📷 {meta.camera}</div>
        <div>
            <span style="background:{P['chip_bg']};border:1px solid {P['chip_border']};
                border-radius:30px;padding:5px 14px;font-size:0.88rem;font-weight:600;color:{P['text']};margin-right:8px;">
                🎯 {sv} Sets
            </span>
            <span style="background:{P['chip_bg']};border:1px solid {P['chip_border']};
                border-radius:30px;padding:5px 14px;font-size:0.88rem;font-weight:600;color:{P['text']};margin-right:8px;">
                {"⏱️" if hold else "🔁"} {rv} {_unit_label(chosen)}
            </span>
            <span style="background:{P['chip_bg']};border:1px solid {P['chip_border']};
                border-radius:30px;padding:5px 14px;font-size:0.88rem;font-weight:600;color:{P['text']};">
                ⚡ {sv * rv} {"Seconds Total" if hold else "Total Reps"}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    lcol, _, _ = st.columns([2, 2, 6])
    with lcol:
        if st.button("🔥 Activate Camera & Start", type="primary", use_container_width=True, key="hero_start"):
            _start_workout(chosen, sv, rv)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div style="font-family:Space Grotesk,sans-serif;font-size:1.25rem;font-weight:800;margin-bottom:0.6rem;color:{P["text"]};">🎬 See it in action</div>', unsafe_allow_html=True)
    render_demo_video(P)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div style="font-family:Space Grotesk,sans-serif;font-size:1.45rem;font-weight:800;letter-spacing:-0.02em;margin-bottom:0.75rem;color:{P["text"]};">🏋️ {len(EXERCISES)} Live-Tracked Exercises</div>', unsafe_allow_html=True)

    groups = grouped()
    group_names = list(groups)
    if st.session_state.get("pose_group") not in group_names:
        st.session_state["pose_group"] = meta.group
    group = st.radio("Muscle group", group_names, horizontal=True, label_visibility="collapsed", key="pose_group",
                     format_func=lambda g: f"{g} ({len(groups[g])})")

    is_d = P["dark"]
    card_bg_default = "linear-gradient(145deg, rgba(20, 28, 48, 0.85), rgba(12, 18, 32, 0.95))" if is_d else "linear-gradient(145deg, #FFFFFF, #F8FAFC)"
    card_bg_active = "linear-gradient(145deg, rgba(0, 229, 255, 0.12), rgba(14, 28, 52, 0.95))" if is_d else "linear-gradient(145deg, rgba(2, 132, 199, 0.08), #FFFFFF)"
    card_border_default = "1px solid rgba(255, 255, 255, 0.08)" if is_d else "1px solid rgba(226, 232, 240, 0.95)"
    card_border_active = "2px solid #00E5FF" if is_d else "2px solid #0284C7"
    card_shadow_active = "box-shadow: 0 0 22px rgba(0, 229, 255, 0.28);" if is_d else "box-shadow: 0 6px 20px rgba(2, 132, 199, 0.2);"
    badge_bg = "rgba(0, 229, 255, 0.12)" if is_d else "rgba(2, 132, 199, 0.1)"
    badge_color = "#00E5FF" if is_d else "#0284C7"
    badge_border = "rgba(0, 229, 255, 0.3)" if is_d else "rgba(2, 132, 199, 0.25)"

    per_row = 4
    for idx, ex_name in enumerate(groups[group]):
        if idx % per_row == 0:
            cols = st.columns(per_row)
        offset = idx % per_row
        m = EXERCISES[ex_name]
        is_chosen = (ex_name == chosen)
        c_bg = card_bg_active if is_chosen else card_bg_default
        c_border = card_border_active if is_chosen else card_border_default
        c_shadow = card_shadow_active if is_chosen else "box-shadow: 0 4px 16px rgba(0,0,0,0.06);"
        checkpoints_html = "".join([f"<li style='margin-bottom:3px;'>{c}</li>" for c in m.cues])
        mode_tag = " · ⏱️ timed hold" if m.mode == "hold" else ""

        with cols[offset]:
            st.markdown(
                f'<div style="background:{c_bg};border:{c_border};border-radius:16px;padding:1.2rem;{c_shadow}min-height:270px;margin-bottom:8px;display:flex;flex-direction:column;justify-content:space-between;box-sizing:border-box;">'
                f'<div>'
                f'<div style="font-size:2rem;line-height:1;margin-bottom:8px;">{m.icon}</div>'
                f'<div style="font-family:Space Grotesk,sans-serif;font-weight:700;color:{P["text"]};font-size:0.95rem;line-height:1.25;height:42px;display:flex;align-items:center;margin-bottom:6px;">{ex_name}</div>'
                f'<div style="margin-bottom:10px;"><span style="background:{badge_bg};color:{badge_color};border:1px solid {badge_border};border-radius:20px;padding:3px 10px;font-size:0.72rem;font-weight:700;display:inline-block;">{m.target}{mode_tag}</span></div>'
                f'<ul style="font-size:0.76rem;color:{P["muted"]};line-height:1.5;padding-left:1.1rem;margin:0;">{checkpoints_html}</ul>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if is_chosen:
                st.button("✓ Active", key=f"sel_{idx}", disabled=True, use_container_width=True, type="primary")
            elif st.button("Select", key=f"sel_{idx}", use_container_width=True):
                st.session_state["plan_exercise"] = ex_name
                st.rerun()


def _check_row(label, status, ok):
    P = pal()
    if ok is None:
        color, bg, mark = P["muted"], "rgba(148,163,184,0.12)", "●"
    elif ok:
        color, bg, mark = "#00E676", "rgba(0,230,118,0.15)", "●"
    else:
        color, bg, mark = "#FF9100", "rgba(255,145,0,0.15)", "▲"
    return (f'<div style="background:{P["card"]};border:1px solid {P["border"]};border-radius:12px;'
            f'padding:0.9rem 1.1rem;margin-bottom:0.7rem;display:flex;justify-content:space-between;align-items:center;">'
            f'<div style="font-size:0.8rem;font-weight:700;color:{P["muted"]};text-transform:uppercase;letter-spacing:0.05em;">{label}</div>'
            f'<span style="background:{bg};color:{color};border:1px solid {color};padding:3px 8px;border-radius:6px;'
            f'font-size:0.78rem;font-weight:700;">{mark} {status}</span></div>')


def _generic_hud(P, ex):
    m = st.session_state.get("live_metrics") or {}
    spec = EXERCISES[ex]
    unit = "%" if spec.unit == "%" else "°"
    sub = (f"Hold between {spec.hold_range[0]:.0f}–{spec.hold_range[1]:.0f}{unit}" if spec.mode == "hold"
           else f"Start ≈{spec.rest * (100 if unit == '%' else 1):.0f}{unit} → peak ≈{spec.peak * (100 if unit == '%' else 1):.0f}{unit}")
    html_parts = [hud_angle(spec.metric_label, sub, m.get("primary_angle", 0), unit),
                  _check_row("Phase", m.get("phase", "WAITING"), None)]
    for c in m.get("checks", []):
        html_parts.append(_check_row(c["label"], c["status"], c["ok"]))
    if spec.mode == "reps":
        partial = m.get("partial_reps", 0)
        html_parts.append(_check_row("Partial reps", str(partial), partial == 0))
    st.markdown("".join(html_parts), unsafe_allow_html=True)
    if m.get("issue"):
        st.warning(f"🛠️ {m['issue']}")


def _coach_feedback(P):
    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

    if st.session_state.get("coach_feedback"):
        st.markdown(f"""
        <div style="background:{P['card_hero']};
            border:1px solid {P['accent_border']};border-radius:16px;
            padding:1.2rem 1.6rem;margin:0.8rem 0;
            box-shadow:0 8px 28px rgba(0,229,255,0.12);">
            <div style="font-size:0.75rem;font-weight:700;color:{P['accent']};text-transform:uppercase;
                letter-spacing:0.1em;margin-bottom:6px;">🤖 COACHX VOICE COACH</div>
            <div style="font-size:1.1rem;font-weight:600;color:{P['text']};">
                "{st.session_state.coach_feedback}"
            </div>
        </div>
        """, unsafe_allow_html=True)


# A fragment, so the ~2-3 landmark batches per second from the browser only rerun this section.
@st.fragment
def _live_session(P):
    # Messages go in containers that always exist, so elements below never shift position: a moved
    # WebRTC component is re-mounted by Streamlit, which drops the video connection.
    messages = st.container()
    with messages:
        _coach_feedback(P)
    ex = st.session_state.get("exercise_type", "Squats")
    total_reps = st.session_state.get("reps", 0)
    cur_reps = st.session_state.get("current_set_reps", 0)
    rps = st.session_state.get("reps_per_set", 10)
    sets_done = st.session_state.get("sets_completed", 0)
    tgt_sets = st.session_state.get("target_sets", 3)

    if st.session_state.get("workout_completed"):
        with messages:
            st.balloons()
            st.success(f"🎉 Workout Complete! Crushed {sets_done} sets of {ex}!")

    cam_col, hud_col = st.columns([60, 40], gap="large")

    with cam_col:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <div style="font-weight:700;font-size:0.9rem;color:{P['text']};display:flex;align-items:center;gap:7px;">
                <span style="width:8px;height:8px;border-radius:50%;background:#00E676;display:inline-block;"></span>
                LIVE CAMERA VIEWPORT
            </div>
            <div style="font-size:0.78rem;color:{P['accent']};font-weight:700;">{ex.upper()}</div>
        </div>
        """, unsafe_allow_html=True)

        mode = st.session_state.get("camera_mode", "webrtc")
        with st.container():
            if st.session_state.get("camera_notice"):
                st.info(st.session_state.camera_notice)

        ctx = None
        if mode == "webrtc":
            ctx, latest = _webrtc_camera(ex)
            if _webrtc_failed(ctx):
                _set_camera_mode("browser", "📡 WebRTC couldn't connect from this network, so tracking switched to "
                                            "on-device mode — same detectors, same rep counting.")
                _rerun_live_session()
        else:
            # Fallback: pose detection runs in the browser; only landmarks reach the server.
            latest = browser_pose_camera(ex, st.session_state.get("camera_session") or "cam-default")
        sync_metrics_update(latest)

        cap_col, btn_col = st.columns([3, 1])
        with cap_col:
            if mode == "webrtc":
                st.caption("📡 Press **START** and allow camera access. Video streams to the server over WebRTC, "
                           "where MediaPipe and the rep counters run in Python.")
            else:
                st.caption("🟢 Live tracking runs on your device — allow camera access when your browser asks.")
        with btn_col:
            if mode == "webrtc":
                if st.button("Use on-device", key="to_browser", use_container_width=True,
                             help="Run pose detection in the browser instead of streaming video to the server."):
                    _set_camera_mode("browser")
                    _rerun_live_session()
            else:
                if st.button("🔄 Restart Camera", key="restart_cam", use_container_width=True):
                    st.session_state.camera_session = f"cam-{time.time_ns()}"
                    _rerun_live_session()
                if st.button("Try WebRTC", key="to_webrtc", use_container_width=True):
                    _set_camera_mode("webrtc")
                    _rerun_live_session()

    # Read after the batch above was processed, so the HUD shows the newest counts.
    total_reps = st.session_state.get("reps", 0)
    cur_reps = st.session_state.get("current_set_reps", 0)
    sets_done = st.session_state.get("sets_completed", 0)

    with hud_col:
        prog = min(1.0, cur_reps / rps) if rps > 0 else 0.0
        st.markdown(f"""
        <div style="background:{P['card_hero']};
            border:1px solid {P['accent_border']};border-radius:18px;
            padding:1.4rem;text-align:center;margin-bottom:1rem;
            box-shadow:0 10px 28px rgba(0,229,255,0.1);">
            <div style="font-size:0.8rem;font-weight:700;letter-spacing:0.1em;
                text-transform:uppercase;color:{P['muted']};">{"Seconds Held" if is_hold(ex) else "Total Reps Counted"}</div>
            <div style="font-size:3.8rem;font-weight:800;line-height:1.05;
                {P['num_style']}">
                {total_reps}
            </div>
            <div style="font-size:0.95rem;color:{P['text']};font-weight:600;margin-top:4px;">
                Set Reps: <span style="color:{P['accent']};">{cur_reps}</span> / {rps}
            </div>
            <div style="font-size:0.85rem;color:{P['muted']};margin-top:2px;">
                Sets: <strong style="color:{P['good']};">{sets_done}</strong> / {tgt_sets}
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(prog)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### ⚡ Live Biomechanics")

        if ex == "Squats":
            st.markdown(
                hud_angle("Knee Angle", "Target <90° for full depth", st.session_state.get("knee_angle", 0)) +
                hud_angle("Back Angle", "Torso inclination", st.session_state.get("back_angle", 0)) +
                hud_status("Depth Status", st.session_state.get("depth_status", "N/A")),
                unsafe_allow_html=True)
        elif ex == "Push-ups":
            st.markdown(
                hud_angle("Elbow Angle", "Target ~90° at bottom", st.session_state.get("elbow_angle", 0)) +
                hud_status("Body Alignment", st.session_state.get("body_alignment", "N/A")) +
                hud_status("Hip Position", st.session_state.get("hip_status", "N/A")),
                unsafe_allow_html=True)
        elif ex == "Biceps Curls (Dumbbell)":
            st.markdown(
                hud_angle("Elbow Angle", "Flexion / Extension", st.session_state.get("elbow_angle", 0)) +
                hud_status("Shoulder Stability", st.session_state.get("shoulder_status", "N/A")) +
                hud_status("Swing Detection", st.session_state.get("swing_status", "N/A")),
                unsafe_allow_html=True)
        elif ex == "Shoulder Press":
            st.markdown(
                hud_angle("Elbow Angle", "Overhead Extension", st.session_state.get("elbow_angle", 0)) +
                hud_status("Arm Extension", st.session_state.get("extension_status", "N/A")) +
                hud_status("Back Arch", st.session_state.get("back_arch_status", "N/A")),
                unsafe_allow_html=True)
        elif ex == "Lunges":
            st.markdown(
                hud_angle("Front Knee", "Target ~90° stride", st.session_state.get("front_knee_angle", 0)) +
                hud_angle("Torso Angle", "Vertical posture", st.session_state.get("torso_angle", 0)) +
                hud_status("Balance Status", st.session_state.get("balance_status", "N/A")),
                unsafe_allow_html=True)
        else:
            _generic_hud(P, ex)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🛑 Finish & Save", use_container_width=True, key="hud_end"):
            _end_workout(ex)

    # WebRTC metrics live in the server-side video processor, so poll them while streaming; while connecting,
    # keep checking so a stuck connection falls back to on-device tracking.
    if ctx is not None and ctx.state.playing:
        time.sleep(0.5)
        _rerun_live_session()
    elif ctx is not None and ctx.state.signalling:
        time.sleep(1.0)
        _rerun_live_session()


def _history(P, user_id):
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 📊 Athlete Training History")

    if not isinstance(user_id, int):
        return
    history_rows = get_users_exercises(user_id)
    arr = [{"Exercise": r['exercise_name'], "Reps": r['reps'], "Sets": r['sets'], "Time (sec)": r['time'], "Date": r['created_at']} for r in history_rows]
    df = pd.DataFrame(arr)

    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        agg = df.groupby(["Exercise", "Date"]).agg({"Reps": "sum", "Sets": "sum", "Time (sec)": "sum"}).reset_index()
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Sessions", len(agg))
        k2.metric("Lifetime Reps", int(agg["Reps"].sum()))
        k3.metric("Total Sets", int(agg["Sets"].sum()))
        k4.metric("Active Time", f"{round(agg['Time (sec)'].sum()/60, 1)} min")
        st.markdown("<br>", unsafe_allow_html=True)
        agg.index = range(1, len(agg)+1)
        st.dataframe(agg, use_container_width=True,
            column_config={
                "Exercise": st.column_config.TextColumn("Exercise", width="medium"),
                "Date": st.column_config.DateColumn("Date"),
                "Reps": st.column_config.NumberColumn("Reps", format="%d"),
                "Sets": st.column_config.NumberColumn("Sets", format="%d"),
                "Time (sec)": st.column_config.NumberColumn("Duration (s)", format="%d s"),
            })
    else:
        st.markdown(f"""
        <div style="background:{P['chip_bg']};border:1px dashed {P['chip_border']};
            border-radius:14px;padding:2.5rem;text-align:center;color:{P['muted']};">
            <div style="font-size:2rem;margin-bottom:8px;">📈</div>
            <div style="font-size:1.05rem;font-weight:700;color:{P['text']};margin-bottom:6px;">No Workout History Yet</div>
            <div>Start your first AI-coached workout to log reps, sets, and biomechanics!</div>
        </div>
        """, unsafe_allow_html=True)


def render_pose_coach():
    initial_session_defaults()
    _init_voice_pipeline()
    P = pal()
    workout_started = st.session_state.get("workout_started", False)

    _sidebar(P, workout_started)

    if workout_started:
        _live_session(P)  # renders the voice-coach feedback itself, so it updates with each batch
    else:
        _coach_feedback(P)
        _exercise_picker(P)

    _history(P, st.session_state.get("user_id"))

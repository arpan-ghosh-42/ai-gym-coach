"""Builds the "sample set" demo shown to visitors who don't want to (or can't) use their camera.

Runs a free stock clip through the exact live WebRTC pipeline -- VideoProcessorClass.recv:
MediaPipe pose landmarks -> SquatDetector -> on-frame overlay -- and saves the annotated video plus a
per-rep summary to static/demo/. It is pre-rendered because Render's free tier (~0.15 CPU) is far too
slow to analyse a video on demand.

Source clip: Mixkit video #752 "Woman doing squats", Mixkit Stock Video Free License
(https://mixkit.co/license/#videoFree). The raw clip is downloaded at build time, not committed.

Usage (from "Main App/"):  python scripts/build_demo_video.py
"""
import json
import sys
import tempfile
import urllib.request
from fractions import Fraction
from pathlib import Path

import av
import cv2

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

from services.vision.exercise_video_processor import VideoProcessorClass  # noqa: E402

SOURCE_URL = "https://assets.mixkit.co/videos/752/752-720.mp4"
EXERCISE = "Squats"
WIDTH, HEIGHT = 640, 360
OUT_DIR = APP_DIR / "static" / "demo"
OUT_VIDEO = OUT_DIR / "squats_demo.mp4"
OUT_SUMMARY = OUT_DIR / "squats_demo.json"


def _draw_header(img, reps: int) -> None:
    """Rep counter burned into the frame, since the page's live HUD can't follow a playing video."""
    panel = img.copy()
    cv2.rectangle(panel, (10, 10), (300, 92), (16, 18, 24), -1)
    cv2.addWeighted(panel, 0.6, img, 0.4, 0, img)
    cv2.putText(img, f"AI COACH - {EXERCISE.upper()}", (22, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(img, f"REPS: {reps}", (22, 78), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (118, 230, 0), 3, cv2.LINE_AA)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "source.mp4"
        print(f"Downloading {SOURCE_URL}")
        urllib.request.urlretrieve(SOURCE_URL, src)

        cap = cv2.VideoCapture(str(src))
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        processor = VideoProcessorClass()
        processor.set_exercise(EXERCISE)

        out = av.open(str(OUT_VIDEO), "w", options={"movflags": "faststart"})
        stream = out.add_stream("libx264", rate=Fraction(fps).limit_denominator(1001))
        stream.width, stream.height, stream.pix_fmt = WIDTH, HEIGHT, "yuv420p"
        stream.options = {"crf": "28", "preset": "slow"}

        reps, rep_events, frame_idx = 0, [], 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.resize(frame, (WIDTH, HEIGHT))
            annotated = processor.recv(av.VideoFrame.from_ndarray(frame, format="bgr24")).to_ndarray(format="bgr24")
            metrics = processor.get_latest_metrics() or {}
            if metrics.get("reps", 0) > reps:
                reps = metrics["reps"]
                rep_events.append({"rep": reps, "at_s": round(frame_idx / fps, 1)})
            _draw_header(annotated, reps)
            for packet in stream.encode(av.VideoFrame.from_ndarray(annotated, format="bgr24")):
                out.mux(packet)
            frame_idx += 1
        for packet in stream.encode():
            out.mux(packet)
        out.close()
        cap.release()

    summary = {
        "exercise": EXERCISE,
        "reps_counted": reps,
        "reps": rep_events,
        "duration_s": round(frame_idx / fps, 1),
        "frames_analysed": frame_idx,
        "pipeline": "VideoProcessorClass.recv: MediaPipe PoseLandmarker (full) -> SquatDetector -> overlay",
        "source": "Mixkit #752 'Woman doing squats' (Mixkit Stock Video Free License)",
    }
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_VIDEO} ({OUT_VIDEO.stat().st_size / 1e6:.1f} MB) and {OUT_SUMMARY}: {reps} reps")


if __name__ == "__main__":
    main()

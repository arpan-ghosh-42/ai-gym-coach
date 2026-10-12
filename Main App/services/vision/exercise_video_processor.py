import os
import cv2
import av
import numpy as np
import mediapipe as mp
import threading
from streamlit_webrtc import VideoProcessorBase
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from detectors.registry import EXERCISES, create_detector, is_legacy
from services.config.workout_config import POSE_CONNECTIONS


class VideoProcessorClass(VideoProcessorBase):
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None
        self._exercise_type = "Squats"

        model_path = os.path.join(os.getcwd(), "ml_models", "pose_landmarker_full.task")
        base_option = python.BaseOptions(model_asset_path=model_path)

        options = vision.PoseLandmarkerOptions(
            base_options=base_option,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.7,
            min_pose_presence_confidence=0.7,
            min_tracking_confidence=0.7,
            output_segmentation_masks=False
        )

        self._landmarker = vision.PoseLandmarker.create_from_options(options)

        # Detectors are created on first use, one per exercise.
        self._detectors = {}

        self._frame_timestamps_ms = 0

    def _get_detector(self, ex_type):
        if ex_type not in EXERCISES:
            return None
        if ex_type not in self._detectors:
            self._detectors[ex_type] = create_detector(ex_type)
        return self._detectors[ex_type]
    
    def set_latest_metrics(self, metrics):
        with self._lock:
            self._latest_metrics = metrics.copy()

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()
        
    def set_exercise(self, exercise_type):
        with self._lock:
            self._exercise_type = exercise_type

    def get_exercise(self):
        with self._lock:
            return self._exercise_type
        
    def _draw_skeleton(self, img, landmarks):
        h, w = img.shape[:2]

        for start_idx, end_idx in POSE_CONNECTIONS:
            p1 = landmarks[start_idx]
            p2 = landmarks[end_idx]

            if p1.visibility > 0.7 and p2.visibility > 0.7:
                cv2.line(
                    img,
                    (int(p1.x * w), int(p1.y * h)),
                    (int(p2.x * w), int(p2.y * h)),
                    (0, 255, 0),
                    8
                )
        
        for lm in landmarks:
            if lm.visibility > 0.7:
                cv2.circle(
                    img, 
                    (int(lm.x * w), int(lm.y * h)),
                    8,
                    (255, 0, 0),
                    -1
                )
            
    def _draw_no_pose_warnings(self, img):
        cv2.putText(
            img,
            "NO POSE DETECTED",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            img,
            "PLEASE FACE THE CAMERA",
            (30, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    def _draw_overlays(self, img, metrics, ex_type):
        if ex_type == "Squats":
            self._draw_squats_overlays(img, metrics)
        elif ex_type == "Push-ups":
            self._draw_pushup_overlays(img, metrics)
        elif ex_type == "Biceps Curls (Dumbbell)":
            self._draw_curl_overlays(img, metrics)
        elif ex_type == "Shoulder Press":
            self._draw_press_overlays(img, metrics)
        elif ex_type == "Lunges":
            self._draw_lunge_overlays(img, metrics)
        else:
            self._draw_generic_overlays(img, metrics, ex_type)

    def _draw_generic_overlays(self, img, metrics, ex_type):
        h, w = img.shape[:2]
        green, orange, white = (0, 230, 118), (0, 145, 255), (255, 255, 255)

        # Header panel
        panel = img.copy()
        cv2.rectangle(panel, (10, 10), (min(w - 10, 430), 120), (16, 18, 24), -1)
        cv2.addWeighted(panel, 0.55, img, 0.45, 0, img)
        is_hold = metrics.get("mode") == "hold"
        counter = f"TIME: {metrics.get('reps', 0)}s" if is_hold else f"REPS: {metrics.get('reps', 0)}"
        cv2.putText(img, ex_type.upper()[:26], (22, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, white, 2, cv2.LINE_AA)
        cv2.putText(img, counter, (22, 78), cv2.FONT_HERSHEY_SIMPLEX, 1.0, green, 2, cv2.LINE_AA)
        cv2.putText(img, f"{metrics.get('metric_label', '')}: {metrics.get('primary_angle', 0)}{'' if metrics.get('unit') == '%' else ' deg'}"
                    f"  [{metrics.get('phase', '')}]", (22, 106), cv2.FONT_HERSHEY_SIMPLEX, 0.55, white, 1, cv2.LINE_AA)

        # Rep progress bar on the right edge
        progress = float(metrics.get("progress", 0.0))
        top, bottom, x = 60, h - 60, w - 40
        cv2.rectangle(img, (x, top), (x + 18, bottom), (60, 60, 60), 2)
        fill_top = int(bottom - (bottom - top) * progress)
        cv2.rectangle(img, (x + 3, fill_top), (x + 15, bottom - 3), green if progress >= 1 else (255, 229, 0), -1)

        # Form feedback footer
        issue = metrics.get("issue")
        text, color = (f"FIX: {issue}", orange) if issue else ("FORM: GOOD", green)
        cv2.putText(img, text[:70], (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

    def _draw_squats_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"DEPTH: {metrics['depth_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
    
    def _draw_pushup_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"BODY: {metrics['body_alignment']} | HIP: {metrics['hip_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_curl_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"SWING: {metrics['swing_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_press_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"EXT: {metrics['extension_status']} | BACK: {metrics['back_arch_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_lunge_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"BALANCE: {metrics['balance_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def recv(self, frame):
        image = np.asarray(
            cv2.flip(frame.to_ndarray(format="bgr24"), 1),
            dtype=np.uint8
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        )

        self._frame_timestamps_ms += 30
        result = self._landmarker.detect_for_video(mp_image, self._frame_timestamps_ms)

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]

            self._draw_skeleton(image, landmarks)

            ex_type = self.get_exercise()

            detector = self._get_detector(ex_type)

            if detector:
                if not is_legacy(ex_type):
                    h, w = image.shape[:2]
                    detector.aspect = w / h
                metrics = detector.process(landmarks)

                metrics["pose_detected"] = True

                self._draw_overlays(image, metrics, ex_type)

                self.set_latest_metrics(metrics)
        else:
            self._draw_no_pose_warnings(image)
            
            with self._lock:
                if self._latest_metrics is not None:
                    self._latest_metrics["pose_detected"] = False
                else:
                    self._latest_metrics = {"pose_detected": False}

        return av.VideoFrame.from_ndarray(image, format="bgr24")
    
#!/bin/sh
# Landing page on /, Streamlit on /app/ — both behind nginx on $PORT (Render).
export PORT="${PORT:-8501}"
envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Runtime MediaPipe self-test (background; result shows up in the service logs as [selftest]).
(python -c "import numpy as np, mediapipe as mp; from mediapipe.tasks import python; from mediapipe.tasks.python import vision; lm = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(base_options=python.BaseOptions(model_asset_path='ml_models/pose_landmarker_full.task'), running_mode=vision.RunningMode.VIDEO)); r = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.zeros((480, 640, 3), dtype=np.uint8)), 30); print('MEDIAPIPE OK, poses:', len(r.pose_landmarks))" 2>&1 | sed 's/^/[selftest] /'; echo "[selftest] finished") &

streamlit run main.py \
  --server.port=8502 --server.address=127.0.0.1 --server.baseUrlPath=app \
  --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false &

exec nginx -g 'daemon off;'

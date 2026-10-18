FROM python:3.12-slim

# System libs needed by opencv/mediapipe (same list as "Main App/packages.txt")
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ["Main App/requirements.txt", "./requirements.txt"]
RUN pip install --no-cache-dir -r requirements.txt

COPY ["Main App/", "./"]

ENV PYTHONUNBUFFERED=1
EXPOSE 8501

# Render injects $PORT; fall back to 8501 locally.
CMD ["sh", "-c", "streamlit run main.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false"]

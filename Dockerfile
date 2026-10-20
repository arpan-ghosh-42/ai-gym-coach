FROM python:3.12-slim

# System libs for opencv/mediapipe (same as "Main App/packages.txt"), plus nginx to serve the
# landing page at / and reverse-proxy Streamlit at /app/.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libegl1 libgles2 libglib2.0-0 libsm6 libxext6 libxrender1 nginx gettext-base \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ["Main App/requirements.txt", "./requirements.txt"]
RUN pip install --no-cache-dir -r requirements.txt

COPY ["Main App/", "./"]

# Pre-parse the knowledge-base PDFs at build time. Doing it on the first plan request takes minutes
# on Render's small free-tier CPU (and the on-disk cache is wiped on every deploy).
RUN python -c "from services.planner.knowledge_base import _kb_files, _pdf_pages; [_pdf_pages(p) for p in _kb_files() if p.suffix.lower() == '.pdf']" \
    && ls -la knowledge_base/.cache
COPY LandingPage/ /app/landing/
COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY start.sh /start.sh
RUN sed -i 's/\r$//' /start.sh && chmod +x /start.sh

ENV PYTHONUNBUFFERED=1 LANDING_URL=/
EXPOSE 10000

# Render injects $PORT; nginx listens on it.
CMD ["/start.sh"]

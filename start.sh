#!/bin/sh
# Landing page on /, Streamlit on /app/ — both behind nginx on $PORT (Render).
export PORT="${PORT:-8501}"
envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

streamlit run main.py \
  --server.port=8502 --server.address=127.0.0.1 --server.baseUrlPath=app \
  --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false &

exec nginx -g 'daemon off;'

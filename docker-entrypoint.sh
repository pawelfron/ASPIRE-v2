#!/bin/bash
set -euo pipefail

cd /app/src/aspire_v2

if [ "$(id -u)" = "0" ]; then
  mkdir -p staticfiles
  chown -R aspire:aspire staticfiles
  exec runuser -u aspire -- "$0" "$@"
fi

python manage.py migrate --noinput
python manage.py init_minio
python manage.py collectstatic --noinput

exec gunicorn aspire_v2.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120 \
  --graceful-timeout 30 \
  --access-logfile -

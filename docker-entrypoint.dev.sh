#!/bin/bash
set -euo pipefail

cd /app/src/aspire_v2

if [ "$(id -u)" = "0" ]; then
  exec runuser -u aspire -- "$0" "$@"
fi

python manage.py migrate --noinput
python manage.py init_minio

exec python manage.py runserver 0.0.0.0:8000

#!/bin/bash
set -e

cd src/aspire_v2

python manage.py migrate
python manage.py init_minio

exec python manage.py runserver 0.0.0.0:8000
#!/bin/bash
set -e

python src/aspire_v2/manage.py migrate
python src/aspire_v2/manage.py init_minio

exec python src/aspire_v2/manage.py runserver 0.0.0.0:8000
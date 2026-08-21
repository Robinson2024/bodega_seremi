#!/bin/sh
set -e

mkdir -p /app/db /app/staticfiles

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 3 \
  --timeout 120 \
  sistema_bodega.wsgi:application
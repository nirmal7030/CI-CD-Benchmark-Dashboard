#!/bin/sh
set -e

# Default values (can be overridden via environment)
export DJANGO_SETTINGS_MODULE=webapp.settings
export PYTHONUNBUFFERED=1

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn webapp.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3

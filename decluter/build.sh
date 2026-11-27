#!/usr/bin/env bash
set -o errexit

pip install -r ../requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

if [ -n "${DEMO_PASSWORD:-}" ]; then
    python manage.py popular_demo
fi

if [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    export DJANGO_SUPERUSER_USERNAME="${DJANGO_SUPERUSER_USERNAME:-${DJANGO_SUPERUSER_EMAIL%%@*}}"
    if ! python manage.py shell -c '
import os
from django.contrib.auth import get_user_model
raise SystemExit(
    0 if get_user_model().objects.filter(
        email=os.environ["DJANGO_SUPERUSER_EMAIL"]
    ).exists() else 1
)
'; then
        python manage.py createsuperuser --noinput
    fi
fi

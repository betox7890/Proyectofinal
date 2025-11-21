#!/usr/bin/env bash
# Start script para Render
set -o errexit

# Ejecutar migraciones
python manage.py migrate --noinput

# Iniciar servidor
exec gunicorn core.wsgi:application --bind 0.0.0.0:$PORT


#!/bin/sh

# Hata durumunda dur
set -e

# Veritabanı migrationlarını yap
echo "Running migrations..."
python manage.py migrate --noinput

# Statik dosyaları topla (opsiyonel, build sırasında yapılmadıysa)
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# Gunicorn'u başlat
echo "Starting Gunicorn..."
exec gunicorn backend.wsgi:application --bind 0.0.0.0:8000

#!/bin/sh

set -e

python manage.py wait_for_db
python manage.py collectstatic --noinput
python manage.py migrate

# tcp socket 9000 used to connect to nginx server
uwsgi --socket :9000 --workers 4 --master --enable-threads --module app.wsgi
#!/bin/bash

python manage.py createcachetable
python manage.py migrate        # Apply database migrations
python manage.py collectstatic --clear --noinput # clearstatic files
python manage.py collectstatic --noinput  # collect static files

# directory for gunicorn logs and django app logs
mkdir -p /ebs/logs
touch /ebs/logs/bstack.log
tail -n 0 -f /ebs/logs/bstack.log &

echo Starting Django runserver.
python manage.py runserver 0.0.0.0:8000

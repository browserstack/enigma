#!/bin/bash

echo "===== Cloning Access Modules ====="
python scripts/clone_access_modules.py

echo "===== Install requirements for access modules ====="
pip install -r Access/access_modules/requirements.txt --no-cache-dir --ignore-installed

echo "===== Ensure DB State ====="
python manage.py createcachetable
python manage.py migrate        # Apply database migrations

echo "===== Ensure Static Files ====="
python manage.py collectstatic --clear --noinput # clearstatic files
python manage.py collectstatic --noinput  # collect static files

# directory for gunicorn logs and django app logs
echo "===== Ensure Logs ====="
touch /ebs/logs/enigma.log
tail -n 0 -f /ebs/logs/enigma.log &

echo "===== Running Service ====="
eval "$@"

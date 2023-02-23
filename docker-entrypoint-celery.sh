#!/bin/bash

python manage.py createcachetable
python manage.py migrate        # Apply database migrations
python manage.py collectstatic --clear --noinput # clearstatic files
python manage.py collectstatic --noinput  # collect static files

# directory for gunicorn logs and django app logs
mkdir -p /ebs/logs
touch /ebs/logs/bstack.log
tail -n 0 -f /ebs/logs/bstack.log &

# run scripts/clone_access_modules.py to clone access modules
python scripts/clone_access_modules.py
pip install -r Access/access_modules/requirements.txt --no-cache-dir --ignore-installed

echo Starting celery
python3 -m celery -A BrowserStackAutomation worker -n worker1 -l DEBUG

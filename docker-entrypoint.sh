#!/bin/bash

LOG_FILE=/ebs/logs/enigma.log
CONTAINER_HASH=$(echo $RANDOM | md5sum | head -c 20)

trap ctrl_c INT

pid_to_kill=1
should_continue=0

function ctrl_c() {
  echo "===== Stopping Service with pid $pid_to_kill ====="
  kill $pid_to_kill
  should_continue=1
}

function log() {
  echo "$(date): $CONTAINER_HASH $@" 2>&1 | tee -a $LOG_FILE
}

function prepend() {
  while read line; do
    echo "${line}"
    echo "$(date): $CONTAINER_HASH -- ${line}" >> $LOG_FILE
  done
}


log "===== Cloning Access Modules ====="
python -m scripts.clone_access_modules 2>&1 | prepend

log "===== Install requirements for access modules ====="
pip install -r Access/access_modules/requirements.txt --no-cache-dir --ignore-installed 2>&1 | prepend

log "===== Ensure DB State ====="
python manage.py createcachetable 2>&1 | prepend
python manage.py migrate 2>&1 | prepend

log "===== Ensure Static Files ====="
python manage.py collectstatic --clear --noinput 2>&1 | prepend
python manage.py collectstatic --noinput 2>&1 | prepend

# directory for gunicorn logs and django app logs
log "===== Ensure Logs ====="
touch /ebs/logs/enigma.log

log "===== Running Service ====="
if [ "$#" -ne 0 ]; then
  eval "$@" 2>&1 | prepend
else
  echo "===== Starting Webserver ====="
  python manage.py runserver --insecure 0.0.0.0:8000 2>&1 &
  pid_to_kill=$!
  echo "Server PID $pid_to_kill"

  while true; do
    if [ "$should_continue" -ne 0 ]; then
      break
    fi
    sleep 5
  done
fi

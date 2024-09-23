#!/bin/bash

if [ "${APP_ENV^^}" == "DEV" ] || [ "${APP_ENV^^}" == "DEVELOPMENT" ]
then
  echo 'Running server with watchfiles...'
  exec python3 -m uvicorn "${UVICORN_APP}" --reload --port=8080 --host=0.0.0.0 --reload-dir /server_code/ --reload-exclude "playground.py" --reload-exclude "startup/drivers/mq/*" --reload-exclude "startup/drivers/celery/*"
else
  core=$(grep --count ^processor /proc/cpuinfo)
  n=$((core*2))
  exec gunicorn -k "${GUNICORN_WORKER:-uvicorn_worker.UvicornWorker}" --logger-class "${GUNICORN_LOGGER:-gunicorn.glogging.Logger}" --workers "${GUNICORN_NWORKER:-1}" --threads $n --access-logfile "-" --time 600 --bind 0.0.0.0:8080 "$UVICORN_APP"
fi

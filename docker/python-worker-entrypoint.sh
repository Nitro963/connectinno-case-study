#!/bin/bash
if [ "${APP_ENV^^}" == "DEV" ] || [ "${APP_ENV^^}" == "DEVELOPMENT" ]
then
  echo 'Running server with watchfiles...'
  exec python3 -m uvicorn "${UVICORN_APP}" --reload --port=8080 --host=0.0.0.0 --reload-dir /server_code/ --reload-exclude "playground.py" --reload-exclude "startup/drivers/api/*" --reload-exclude "startup/drivers/celery/*"
else
  exec python3 -m uvicorn "${UVICORN_APP}" --port=8080 --host=0.0.0.0 --log-config /server_code/uvicorn-logging-config.json
fi

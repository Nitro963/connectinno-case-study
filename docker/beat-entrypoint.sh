#!/bin/bash
exec celery -A "$CELERY_APP" beat -l "$LOG_LEVEL"

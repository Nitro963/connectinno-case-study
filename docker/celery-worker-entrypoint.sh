#!/bin/bash
#declare LD_LIBRARY_PATH
#LD_LIBRARY_PATH=$(python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))')
#
exec celery -A "$CELERY_APP" worker -l "$LOG_LEVEL" -P "$POOL" -n "${WORKER_NAME}-%i@%h" -Q "$WORKERS_QUEUES" -E -O fair

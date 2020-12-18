#!/usr/bin/env bash
# start-celery-worker.sh

set -euo pipefail

rm -f /tmp/celery_worker.pid

sleep 10
# Use of COLUMNS is a future proof Python 3.8 fix
# See: https://github.com/celery/celery/issues/5761#issuecomment-551089852
echo "Worker"
echo $PWD
PYTHONPATH=/app COLUMNS=80 celery -A tasks.celery worker --loglevel=info --concurrency=6 --pidfile=/tmp/celery_worker.pid 

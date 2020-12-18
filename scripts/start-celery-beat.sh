#!/usr/bin/env bash
# start-celery-beat.sh

set -euo pipefail

rm -f /tmp/celery_beat.pid
rm -f /tmp/celerybeat-schedule

# Use of COLUMNS is a future proof Python 3.8 fix
# See: https://github.com/celery/celery/issues/5761#issuecomment-551089852
echo "Beat"
echo $PWD
PYTHONPATH=/app COLUMNS=80 celery -A tasks.celery beat --loglevel=info --pidfile=/tmp/celery_beat.pid --schedule=/tmp/celerybeat-schedule

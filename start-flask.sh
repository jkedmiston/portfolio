#!/usr/bin/env bash
# start-flask.sh

set -euo pipefail
exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 "main:create_app()"

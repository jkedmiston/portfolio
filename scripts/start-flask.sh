#!/usr/bin/env bash

set -euo pipefail
flask db upgrade
FLASK_APP="main:create_app()"

ARGS=(
  --bind :$PORT
  --threads 8
  --timeout 0
  --workers 1
)

DEVELOPMENT=false
while getopts ":d:" options; do
  case "${options}" in
    d )
      DEVELOPMENT=true
      ;;
    *)
      DEVELOPMENT=false
      ;;
  esac
done

if [[ "$DEVELOPMENT" == true ]]; then
  # tell Gunicorn to reload files when local changes are made
  ARGS+=(--reload)
fi

echo "Starting $FLASK_APP with ${ARGS[@]}"

exec gunicorn $FLASK_APP "${ARGS[@]}"

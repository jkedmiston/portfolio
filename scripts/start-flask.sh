#!/usr/bin/env bash
# start-flask.sh

set -euo pipefail

FLASK_APP="main:create_app()"

ARGS=(
  --bind :$PORT
  --threads 8
  --timeout 0
  --workers 1
)

# The "development" version of this script can be activated by calling it with
# the `-d` flag.
# This currently:
# - Supplies the "--reload" option to Gunicorn which reloads files after
# changes are made during development.
# This mode allows us to use this script in development and in production.
# If additional logic needs to be added in the future, it might be simpler to
# create separate scripts for each use case rather than adding conditional
# logic to Bash scripts and their incantations.
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

#!/usr/bin/env bash
# start-flask.sh

set -euo pipefail

# This command may fail when run against a database which doesn't yet contain
# an alembic_version table and alongside other scripts also trying to create
# the table. As long as one of them succeeds, which it should, this failure is
# acceptable.
# `flask db upgrade` will always be run serially on Heroku by
# heroku-release-command.sh and the scenario described is not a concern in that
# environment.
# Temporarily allow non-zero returns.
set +e
flask db upgrade
flask_db_upgrade_succeeded=$?
set -e

if [ $flask_db_upgrade_succeeded -eq 0 ]; then
  echo "'flask db upgrade' succeeded from start-flask.sh."
else
  echo "'flask db upgrade' failed from start-flask.sh. See logs."
fi

FLASK_APP="portfolio:create_app()"


ARGS=(
  --bind 0.0.0.0:$PORT
  --config $APP_CONFIG_FILE
  --log-level $LOG_LEVEL
  --workers $WEB_CONCURRENCY
)

# The "development" version of this script can be activated by calling it with
# the `-d` flag.
# This currently:
# - Supplies the "--reload" option to Gunicorn which reloads files after
# changes are made during development.
# - Calls the "load_dev_data" CLI command to populate some components of the
# local database.
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

  # run CLI command to populate some tables with sample data
  flask main_bp load_dev_data only_if_empty
fi

echo "Starting $FLASK_APP with ${ARGS[@]}"

gunicorn $FLASK_APP "${ARGS[@]}"

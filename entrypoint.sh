#!/bin/bash

if [[ "$@" == *"celery"* ]]; then
    echo "Running entrypoint from celery"
else
    echo "Running entrypoint from main app"
fi

echo "entry point done"
echo "$@"
exec "$@"



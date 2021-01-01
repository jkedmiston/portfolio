#!/bin/bash
# load custom libraries which create folders like src/
# When this was added to requirements.txt, the folder wasn't being created inside the container

if [[ "$@" == *"celery"* ]]; then
    echo "Running from celery"
else
    pip install -e git+https://github.com/jkedmiston/latex-ds.git@master#egg=latex-ds
fi

echo "entry point done"
echo "$@"
exec "$@"



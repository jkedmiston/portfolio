#!/usr/bin/env bash

set -euo pipefail


flask db upgrade

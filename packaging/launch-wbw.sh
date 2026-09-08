#!/bin/sh
set -eu
app_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 -B "$app_dir/blackwing_launcher.py" "$@"

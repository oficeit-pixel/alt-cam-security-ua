#!/usr/bin/env bash
set -euo pipefail
# Credentials are read only from the environment by the helper.
exec python3 "$(dirname "$0")/migrate_render_to_neon.py"

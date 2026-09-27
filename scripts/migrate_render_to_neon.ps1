$ErrorActionPreference = 'Stop'
# Requires Python 3 and PostgreSQL 17 client tools on PATH.
& python (Join-Path $PSScriptRoot 'migrate_render_to_neon.py')
exit $LASTEXITCODE

#!/bin/sh
# Seed demo data (no Docker required). Regenerates deterministic datasets.
set -eu
cd "$(dirname "$0")/.."
python scripts/generate_demo_data.py "$@"
echo "[seed] sample-data/:"
ls -la sample-data/

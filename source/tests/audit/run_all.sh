#!/usr/bin/env bash
# Runs every audit diagnostic against the current engine build (needs ./build.sh first).
# Diagnostics only: nothing here modifies the production DSP.
set -euo pipefail
cd "$(dirname "$0")"
python3 audit_filters.py
python3 audit_dynamics.py

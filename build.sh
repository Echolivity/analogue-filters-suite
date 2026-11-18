#!/usr/bin/env bash
# Regenerates the engine, checks + transpiles it, runs validation, rebuilds the device.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/source"
mkdir -p build
python3 src/build_genexpr.py
python3 tools/genexpr2c.py build/dubfilter.genexpr build/engine.c
cc -O2 -o build/harness tests/harness.c build/engine.c -lm
python3 tests/validate.py
python3 tests/report.py
python3 device/build_device.py
python3 device/preview.py build/device/preview.png
cp build/device/DubFilter.amxd build/device/DubFilter.maxpat "$ROOT/"
cp build/dubfilter.genexpr "$ROOT/source/dubfilter.genexpr"
rm -rf "$ROOT/docs/validation"; cp -r docs/validation "$ROOT/docs/"
cp docs/VALIDATION.md "$ROOT/docs/"; cp build/device/preview.png "$ROOT/docs/preview.png"
echo "done: DubFilter.amxd, DubFilter.maxpat, docs/VALIDATION.md"

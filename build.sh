#!/usr/bin/env bash
# Regenerates the engine, checks + transpiles it, runs validation, rebuilds the device.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/source"
mkdir -p build
python3 src/build_genexpr.py
python3 tools/genexpr2c.py build/dubfilter.genexpr build/engine.c
cc -O2 -o build/harness tests/harness.c build/engine.c -lm
python3 tests/golden.py check          # gate: LPF/HPF bit-exact vs v1.1 baseline
python3 tests/golden.py check-bpf      # gate: BPF bit-exact vs v1.2 baseline
python3 tests/golden.py check-dyn      # gate: dynamics chain bit-exact vs v1.3 baseline
python3 tests/validate.py
python3 tests/report.py
python3 device/build_device.py
for v in 1.1 1.2 1.3 1.4; do   # gate: presets/automation/MIDI of every release intact; v1.4: DSP byte-identical
  python3 tests/compat.py build/device/DubFilter.maxpat --base=DubFilter_v$v.maxpat --ui
done
python3 tests/ui_tests.py      # gate: v1.5 UI structure, sync wiring, layout, contrast, jsui logic
python3 device/preview.py build/device/preview.png
mkdir -p "$ROOT/docs/ui"
python3 device/preview.py "$ROOT/docs/ui/after_default.png"
python3 device/preview.py "$ROOT/docs/ui/after_parallel_multi_opto.png" flt_route=1 b_on=1 b_arch=2 t_on=1 o_on=1 _page=1
python3 device/preview.py "$ROOT/docs/ui/after_hybrid_hp_first_vca.png" flt_route=2 order_sel=1 b_on=1 b_arch=1 v_on=1 g_on=1 c_order=4 _page=2
cp build/device/DubFilter.amxd build/device/DubFilter.maxpat build/device/df_*.js "$ROOT/"
cp build/dubfilter.genexpr "$ROOT/source/dubfilter.genexpr"
rm -rf "$ROOT/docs/validation"; cp -r docs/validation "$ROOT/docs/"
cp docs/VALIDATION.md "$ROOT/docs/"; cp build/device/preview.png "$ROOT/docs/preview.png"
echo "done: DubFilter.amxd, DubFilter.maxpat, docs/VALIDATION.md"

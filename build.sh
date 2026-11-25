#!/usr/bin/env bash
# Regenerates the engine, checks + transpiles it, runs validation, rebuilds the device.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/source"
mkdir -p build
python3 src/build_genexpr.py
python3 tests/genexpr_lint.py build/dubfilter.genexpr tests/baseline/DubFilter_v1.5.maxpat   # gate: gen~ scoping / names / literals vs v1.5
python3 device/build_device.py         # before validate: routing_tests reads the freshly built device
python3 tools/genexpr2c.py build/dubfilter.genexpr build/engine.c
cc -O2 -o build/harness tests/harness.c build/engine.c -lm
python3 tools/genexpr2c.py tests/baseline/dubfilter_v1.5.genexpr build/engine_v15.c
cc -O2 -o build/harness_v15 tests/harness.c build/engine_v15.c -lm   # v1.5 reference engine for before/after tests
python3 tests/golden.py check-v16      # gate: bit-exact vs v1.6 baseline; the set of renders that differ from the
                                       # v1.1/v1.2/v1.3 baselines must be exactly the documented one
python3 tests/v16_tests.py             # gate: v1.6 stability, containment, oversampling, Reference mode
python3 tests/validate.py
python3 tests/report.py
for v in 1.1 1.2 1.3 1.4 1.5; do   # gate: presets/automation/MIDI of every release intact (v1.6 is a DSP release)
  python3 tests/compat.py build/device/DubFilter.maxpat --base=DubFilter_v$v.maxpat --ui --allow-dsp
done
python3 tests/ui_tests.py      # gate: UI structure, sync wiring, layout, contrast, jsui logic
python3 device/preview.py build/device/preview.png
mkdir -p "$ROOT/docs/ui"
python3 device/preview.py "$ROOT/docs/ui/after_default.png"
python3 device/preview.py "$ROOT/docs/ui/after_parallel_multi_opto.png" flt_route=1 b_on=1 b_arch=2 t_on=1 o_on=1 _page=1
python3 device/preview.py "$ROOT/docs/ui/after_hybrid_hp_first_vca.png" flt_route=2 order_sel=1 b_on=1 b_arch=1 v_on=1 g_on=1 c_order=4 _page=2
cp build/device/DubFilter.amxd build/device/DubFilter.maxpat build/device/df_*.js build/device/dfx_*.png "$ROOT/"
cp build/dubfilter.genexpr "$ROOT/source/dubfilter.genexpr"
rm -rf "$ROOT/docs/validation"; cp -r docs/validation "$ROOT/docs/"
cp docs/VALIDATION.md "$ROOT/docs/"; cp build/device/preview.png "$ROOT/docs/preview.png"
echo "done: DubFilter.amxd, DubFilter.maxpat, docs/VALIDATION.md"

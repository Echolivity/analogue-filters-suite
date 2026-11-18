# Changelog

## v1.3: reorderable dynamics chain
- **New:** a PROCESSING CHAIN with Tube saturation, an LA-2A-inspired optical compressor and an API 2500-inspired VCA compressor, in any of six orders. Drag-and-drop blocks, three suggested configurations, a Chain Order parameter, and a click-free state-copy crossfade on reordering.
- **New:** an independent Gate, an external sidechain key (`plugin~ 3 4` + KEY FROM), INT/CHAIN/EXT detector sources, SC filters, stereo link, key listen, and per-module ON/In/Out/Mix with meters. 44 new Live parameters, all off or neutral by default.
- **Unchanged:** LPF, HPF and BPF DSP, parameters, automation and MIDI mappings. Bit-exact against the v1.1 and v1.2 golden renders; patch compatible with both v1.1 and v1.2 snapshots.
- **Device width:** 1066 → 1774.
- **Tests:** `dyn_tests.py` (35 checks) + BPF golden baseline. Suite: 77/77.

## v1.2: band-pass engine
- **New:** a third, independent band-pass engine with 5 models (Oberheim SEM, Steiner-Parker, Korg 35/MS-20, ARP 2600 (derived), EMS VCS3 (derived)) and 3 architectures (SVF, CASCADE, MULTIMODE). Controls: Centre, Bandwidth, Q, Resonance, Drive, Compensation, Mix, Position (POST/PRE), On. 11 new Live parameters. See docs/BPF.md.
- **New UI section** to the right of the existing panel (device width 700 → 1066). Existing sections are unchanged.
- **Unchanged:** LPF and HPF DSP, parameters, automation names, MIDI mappings and UI. The BPF is off by default, so v1.1 Sets sound identical.
- **Tests:** bit-exact golden regression (`source/tests/golden.py`), patch compatibility check (`source/tests/compat.py`), 17 new BPF/combined checks (`source/tests/bpf_tests.py`). Suite: 42/42.

## v1.1: circuit-informed models
- TB-303 rebuilt on Stinchcombe's TB-303 configuration; Moog per-stage tanh (Huovilainen); Steiner-Parker as a Sallen-Key with diode strings; SEM OTA integrators; Sherman resonance per published spec. Circuit-reference test.

## v1.0
- Initial LPF/HPF device with six models per stage.

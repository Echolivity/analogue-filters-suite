# API 2500 measurement tools

API never published the 2500 schematic, so the parts of the VCA model that no document covers are measured from renders instead. Those parts are:
- the knee widths;
- the RMS detector timing;
- the VARIABLE release;
- the THRUST MED curve;
- the link SHAPE filters.

- `make_pack.py [out_dir]` writes the test signals (48 kHz, 24-bit) and `schedule.json`.
- `RENDER_INSTRUCTIONS.txt` lists the 17 renders to make (hardware, Waves or UAD). It is shipped in the pack as README.txt.
- `analyse.py <pack_dir> <renders_dir> [out_dir]` writes `report.md`, `results.json` and plots. It aligns each render by the sync click at 0.5 s, and measures gain reduction relative to the R01 calibration render, so latency and output offsets cancel.
- `selftest.py [work_dir]` renders the pack through this project's own VCA (it needs `./build.sh` first) and checks that the analysis recovers the model's known values: threshold and ratio, knee widths 0/6/12 dB, the engine's THRUST curves within 0.03 dB, attack ordering, the fixed release time, and the link. A 777-sample latency with a +3 dB output offset gives identical results.

Methods:
- **Static curve:** a 1 kHz tone stepped 1 dB at a time; the steps are fitted with a quadratic soft knee.
- **THRUST:** the ratio is set to 2:1 with tones well above threshold, so a change in the detector level equals 2 × the change in gain reduction; the result is taken relative to NORM.
- **Attack:** 40 dB steps, measured at the 10 / 63 / 90 % points of the gain-reduction rise.
- **Release:** the 37 % recovery time after bursts 2, 17 and 32 dB over threshold.
- **Link:** loud tones on the left channel and a quiet 1 kHz tone on the right; the right channel's gain shows what the link passes across at each frequency.

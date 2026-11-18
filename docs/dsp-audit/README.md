# DSP hardware-authenticity and fidelity audit

This audit covers Dub Filter v1.5 (`main` at 926a3d3). It examines the code and measures the engine; **it does not modify the production DSP.** The gen~ code and every golden render are unchanged.

## Reports

| # | Report | Answers |
|---|---|---|
| 1 | [DSP_INVENTORY.md](DSP_INVENTORY.md) | What DSP exists, and where |
| 2 | [HARDWARE_REFERENCE_CATALOG.md](HARDWARE_REFERENCE_CATALOG.md) | Which hardware each model refers to, which revision, and how certain that is |
| 3 | [DSP_IMPLEMENTATION_AUDIT.md](DSP_IMPLEMENTATION_AUDIT.md) | What each model actually computes, line by line |
| 4 | [FILTER_FIDELITY_REPORT.md](FILTER_FIDELITY_REPORT.md) | How the filters measure |
| 5 | [COMPRESSOR_FIDELITY_REPORT.md](COMPRESSOR_FIDELITY_REPORT.md) | How the opto and VCA measure |
| 6 | [PREAMP_SATURATION_FIDELITY_REPORT.md](PREAMP_SATURATION_FIDELITY_REPORT.md) | What the TUBE is |
| 7 | [SIGNAL_CHAIN_AUDIT.md](SIGNAL_CHAIN_AUDIT.md) | Order, routing, sidechain, order effects |
| 8 | [DSP_VALIDATION_RESULTS.md](DSP_VALIDATION_RESULTS.md) | Measurement method, result index, CPU, hardware test procedure |
| 9 | [HARDWARE_FIDELITY_SCORECARD.md](HARDWARE_FIDELITY_SCORECARD.md) | Class A–E for every model, with evidence |
| 10 | [DSP_FIDELITY_ROADMAP.md](DSP_FIDELITY_ROADMAP.md) | What to fix, in which order, and what it costs. **Awaiting approval.** |

## Headline results

**Scorecard.** No model is Class A, because no hardware or SPICE reference was available.

| Class | Models |
|---|---|
| B (theoretical) | Ladder LP, TB-303, SEM |
| C | K35, Steiner, OPTO, VCA, the native band-pass pairings |
| D | TUBE (a static waveshaper), Ladder HP, slope extensions, the ARP/EMS band-pass |
| E | Sherman (no public schematic) |

**Critical defect.** At 1× oversampling, with fc around 12 kHz and resonance at 100 %, the Sherman filter diverges numerically and the Steiner filter overshoots to +30 dBFS.

**Other deficiencies, from measurement:**
- **Aliasing.** At the default 1× setting, the Steiner reaches −25 dBc. The TUBE reaches −30 dBc at Drive 100 even with its own 2× oversampling.
- **High-frequency error.** Above about 5 kHz at 1×, the bilinear mapping cramps the top octave and the resonance peak shifts by up to +167 cents.
- **OPTO.** The attack is 2.3–2.9 ms against a documented ~10 ms. The COMP ratio is 2.2–2.7:1 against a nominal 4:1.
- **VCA.** Attack settings below 1 ms are unreachable (the 0.03 ms setting measures 0.71 ms). There is no link filter.
- **Harmonics.** Five of the six filters produce no even-order harmonics.

**Verified:**
- THRUST affects only the detector; it is bit-identical in the audio path.
- NEW is feed-forward and OLD is feedback.
- The OPTO release has a two-stage, programme-dependent memory.
- The displayed routing matches the DSP.
- The TB-303 and ladder models match their published circuit analyses at small signal.

## Reproduce

```
./build.sh                         # builds the engine and runs the production gates
source/tests/audit/run_all.sh      # writes docs/dsp-audit/data/*.json and plots/*.png (about 2 min)
```

The diagnostic scripts are `source/tests/audit/common.py`, `audit_filters.py` and `audit_dynamics.py`. They are read-only with respect to the DSP.

# DSP validation results

## What kind of evidence this is

**Theoretical and engine-measured comparison only.** No physical hardware was available, and no recordings of the reference hardware are in the repository. So every statement here is one of these:

- **Measured** properties of this engine, with exact signals and settings.
- **Comparisons with published circuit analyses**: analogue transfer functions taken from the literature, evaluated analytically.
- **Comparisons with published hardware specifications**: manufacturer and secondary sources, cited in `HARDWARE_REFERENCE_CATALOG.md`.

**No hardware match is claimed.**

### A caveat about the existing test suite

The pre-existing "circuit reference" check (`tests/validate.py` `t_circuit_reference`) compares the engine against the analogue transfer function **evaluated through the same bilinear frequency mapping**: s = j·tan(πf/fs)/tan(πfc/fs).

That proves the discrete model is implemented correctly. It **does not** prove agreement with the analogue circuit at high frequencies. This audit adds the unwarped comparison (s = j·f/fc, test F1). Agreement holds below about fc and diverges in the top octave at 1×. See `FILTER_FIDELITY_REPORT.md` §2.2.

## Measurement method

| Item | Value |
|---|---|
| Engine | `source/build/dubfilter.genexpr`, transpiled to C by `tools/genexpr2c.py`, run by `tests/harness.c` |
| Arithmetic | 64-bit internal; 32-bit float file I/O. The noise floor of the harmonic analysis is −149 dBc (clean-sine check, F5). |
| Sample rates | 48 kHz unless stated. Filters were also tested at 44.1 and 96 kHz (F1, F8). |
| Bit depth | 32-bit float (no dither, no quantisation) |
| Transfer functions | White noise at about 2·10⁻⁴ rms (≈ −74 dBFS); Welch cross-spectrum; 8192-point segments; 2¹⁶ samples after a 0.5 s pre-roll |
| Harmonics | 1 s coherent segment; 4-term Blackman-Harris window; ±5 bins per harmonic; "residual" = all energy that is not on a harmonic and not below 20 Hz |
| Parameter settling | Every measurement discards ≥ 0.2 s (filters) or ≥ 1 s (dynamics) so the control smoothing has finished. Self-oscillation tests excite after 0.5 s. |
| Settings | Recorded in each script call, and in the data JSON rows |
| Determinism | Except CPU timings, every result is bit-reproducible: same build, same seeds |

**Reproduce:**

```
./build.sh
source/tests/audit/run_all.sh
```

## Result index

| # | Measurement | Data key | Plot |
|---|---|---|---|
| 1 | Frequency response vs analogue (44.1/96 kHz, 1×/2×, 3 cutoffs, 2 resonances, all models) | `filters.F1_digital_vs_analogue` | `f1_digital_vs_analogue_hf.png` |
| 2 | Phase response vs analogue | F1 (`max_phase_deg…`) | `f1_…` (lower row) |
| 3 | Harmonic spectra / THD vs input level, filters | `filters.F4_thd_vs_level_drive0` | `f4_thd_vs_level.png` |
| 4 | THD vs drive / level / frequency, tube | `dynamics.T1`–`T3` | `t1_tube_transfer_thd.png` |
| 5 | Compressor transfer curves | `dynamics.C1_static_curves` | `c1_static_curves.png` |
| 6 | Attack / release responses | `dynamics.C2a`, `C2b`, `C3a`, `C3b` | `c3_opto_release_memory.png` |
| 7 | Gain-reduction response vs frequency (THRUST) | `dynamics.C4b` | `c4_thrust_detector_response.png` |
| 8 | Intermodulation (SMPTE 60 Hz + 7 kHz, 4:1) | `dynamics.T5_imd_smpte` | — |
| 9 | Aliasing (1× vs 2×; tube) | `filters.F5_aliasing`, `dynamics.T6` | `f5_alias_spectrum_ladder.png` |
| 10 | CPU and latency | `dynamics.P1_cpu_offline_harness`; latency as in `SIGNAL_CHAIN_AUDIT.md` §6 | — |
| + | Resonance peak vs knob | `filters.F2` | `f2_resonance_peak.png` |
| + | Self-oscillation pitch, level, stability | `filters.F3` | — |
| + | Stability under abrupt modulation | `filters.F6` | — |
| + | Skirt slopes | `filters.F7` | — |
| + | Sample-rate consistency | `filters.F8` | — |
| + | BPF centre and width | `filters.B1` | — |
| + | THRUST detector-only proof | `dynamics.C4a` | — |
| + | Stereo link | `dynamics.C5` | — |
| + | Compressor distortion | `dynamics.C6` | — |
| + | Tube memory test | `dynamics.T4` | — |
| + | Chain order effects | `dynamics.S1` | — |

## CPU (offline harness)

These are single-threaded C timings, compiled with `-O2` on the audit machine, in ns per stereo sample (best of 3, 2 s of noise). Max's gen~ compiler produces comparable C, but **timings inside Live will differ**. Treat these as relative figures.

| Configuration | ns/sample | % of one core at 48 kHz |
|---|---|---|
| Everything off | 760 | 3.6 % |
| LPF ladder 24 dB | 1012 | 4.9 % |
| LPF + HPF, 1× | 948 | 4.6 % |
| LPF + HPF, 2× | 1147 | 5.5 % |
| LPF + HPF 48 dB + BPF MULTI, 2× | 1499 | 7.2 % |
| Full chain (filters 2× + tube + opto + VCA + gate) | 1709 | 8.2 % |

The "everything off" cost is high: 3.6 % of a core. The generated code evaluates control smoothing, switching logic and state copies every sample, even when every module is off. This is a CPU-efficiency finding, not a fidelity one.

## Proposed hardware-versus-plugin measurement procedure

Use this when hardware is available.

**1. Rig.**
- An audio interface with ≥ 24-bit / 96 kHz converters.
- A loop-back calibration (interface out → in) to remove the converters' own response and latency.
- Level calibration to a known dBu point, so that dBFS ↔ dBu is fixed. Hardware nonlinearity depends on absolute level.

**2. Settings capture.**
- For every knob, measure its response at 5–7 positions: cutoff and resonance with sweeps, ratio and threshold with static curves.
- Fit a knob-to-parameter map. *Never compare at "the same knob position" without this map.*

**3. Signals.** All repeated at 3–4 levels across the hardware's range.
- Exponential sine sweeps (Farina) give linear response and harmonic distortion separately.
- Stepped sines, 20 Hz–20 kHz, give THD and harmonics vs frequency and level.
- Tone bursts of 10 ms / 100 ms / 1 s / 10 s give compressor attack, release and memory.
- Two-tone and SMPTE give IMD.
- Pink noise at several levels gives level-dependent response.
- A small set of programme clips (drums, bass, vocal) supports null tests and blind listening.

**4. Filters.**
- Small-signal response at each mapped cutoff/resonance.
- Self-oscillation pitch and level vs cutoff.
- Large-signal response, to separate clipping inside the filter from clipping around it.

**5. Compressors.**
- Static curves with long settle times, measured on the same unit's meter and output.
- Attack and release from step responses.
- T4 memory protocol: identical bursts after different rest periods.

**6. Comparison metrics.**
- Response error in dB vs frequency.
- Harmonic level errors.
- Error in GR trajectory, in dB vs time.
- Null-test residual vs level.
- Blind ABX listening for the residual cases.

**7. Report.**
- Unit serial or revision, with photographs of internal boards: KORG35 vs LM13600, T4 type, VCA type.
- Warm-up time and ambient temperature.

## Known limitations of this audit

**Sources:**
- No hardware.
- Primary sources partly inaccessible: Steiner 1974, Stinchcombe's MS-20 study, the original SEM and LA-2A schematics. Therefore several reference facts are graded [F]/[M] in the catalogue.

**Method:**
- The engine was run offline, not inside Max/Live. The exact gen~ code was used, but Max's runtime was not.
- 32-bit float I/O limits measurement floors to about −150 dB. That is not a limitation for any reported figure.

**Coverage not tested:**
- The opto's response to complex programme material. Only synthetic signals were used.
- Inter-channel crosstalk: none exists in an ideal digital model.
- Noise: none is modelled.

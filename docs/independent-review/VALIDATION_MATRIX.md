# Validation matrix

## Status legend

| Status | Meaning |
|---|---|
| **Have** | Exists today |
| **New** | Must be built (T0 onward) |
| **Ext** | Needs SPICE or hardware |

A test applies to an implementation task when the roadmap lists it under that task's coverage.

**Axes common to every row**, unless a row says otherwise:
- **Sample rates:** 44.1, 48, 88.2, 96, 192 kHz
- **Oversampling:** 1×, 2×, 4×, 8×
- **Solver:** Classic, implicit
- **Mode:** Reference, Creative
- **Channels:** stereo identical and stereo independent

## 1. Filters (each LPF/HPF model, each BPF configuration)

| Test | Parameters | Pass criterion | Status |
|---|---|---|---|
| Small-signal vs published H(s) (unwarped) | fc 20 Hz–20 kHz (12 per decade); res 0/30/60/90 %; slope settings | Within 0.5 dB where H > −30 dB, below 0.5·fc_nyq-equivalent; above it, documented per factor | Have (partial) / New (grid) |
| Small-signal vs BLT-predicted H | same | Within 0.05 dB (implementation correctness) | Have |
| Resonance peak height and frequency vs knob | res 0–100 % in 5 % steps; 3 fc | Monotonic; documented curve | Have (1 fc) / New |
| Self-oscillation pitch | fc 50 Hz–16 kHz (1/3-oct); res 100 % | Documented cents vs fc; Reference: within ±10 cents below fs/8 | Have (partial) |
| Self-oscillation level | same | Within the internal ceiling (+6 dBFS) | New |
| **fs/4 stability sweep** | fc = fs/4 ± 200 cents in 1-cent steps; res 90–100 % in 1 % steps; 3 sample rates; all factors | Peak < +6 dBFS; no growth | **New (critical)** |
| Abrupt modulation | 100 Hz–12 kHz square at 10–100 Hz; res 100 %; Drive 100 %; 48 dB | Finite; overshoot documented | Have |
| THD / harmonics vs level | 50/110/1k/5k Hz; −40…+6 dBFS; Drive 0/50/100 %; res 0/50/90 %; Comp 0/100 | Documented; Reference vs SPICE where available | Have (partial) / Ext |
| Aliasing with convergence | C1/C2/C3 conditions plus a 2-tone; all factors | Reference: ≤ −80 dBc at C1 at the model minimum factor; residual that does not converge is flagged as dynamics | New |
| IMD (SMPTE, CCIF) | Drive 0/50/100 % | Documented | Have (1 case) / New |
| Sample-rate invariance | 44.1–192 kHz | Within 0.5 dB where H > −30 dB below 8 kHz | Have |
| DC and denormals | Silence after loud input; 10 min run | No denormal slowdown; DC < −100 dBFS | Have |
| Fault propagation | Forced divergence (Classic solver) then recovery | Clean within 10 ms after containment (P0-3) | **New** |
| Golden bit-exactness | 48 LPF/HPF + 35 BPF + 21 dynamics scenarios | Creative / Classic: bit-identical | Have |
| SPICE large-signal | Transfer, THD, oscillation amplitude | Per-model tolerances set in P3-1 | Ext |

## 2. Compressors

| Test | OPTO | VCA | Pass criterion | Status |
|---|---|---|---|---|
| Static curve | PR 20–100 %, COMP/LIMIT; 100 Hz / 1 kHz / 5 kHz | Each threshold × ratio × knee × NEW/OLD | Documented local ratio vs level; VCA NEW exact to 0.05 | Have (partial) / New |
| Attack | t10 / t63 / t90 at 5 GR depths × 3 frequencies × history | Each setting × 3 GR depths × 3 frequencies | Reference data required for pass/fail | Have (partial) / Ext |
| Release and memory | Bursts 0.1–30 s × rest 0–30 s | Each setting | OPTO: two-stage; documented vs reference | Have (partial) / Ext |
| Detector frequency response | HF emphasis; SC HPF | THRUST × SC HPF × link filter | Documented curve; THRUST in detector only (bit-identical audio) | Have |
| Stereo link | Link 0/50/100 % | same + link filter | Continuous, symmetric | Have |
| Gain-modulation distortion | 30/50/100 Hz × GR depth | Attack/release extremes | Documented | Have (partial) |
| Sidechain sources | INT/CHAIN/EXT | INT/CHAIN/EXT | Correct source; EXT in Live | Have (offline) / New (Live) |
| Hardware comparison | — | — | Per the procedure | Ext |

## 3. TUBE

| Test | Parameters | Pass criterion | Status |
|---|---|---|---|
| Transfer curve | Drive 0–100 %; Bias −100…+100 | Classic: as documented. Triode: SPICE within 0.5 dB. | Have / Ext |
| THD vs level and frequency | 50 Hz–5 kHz; −40…0 dBFS | Triode: SPICE within 2 dB; frequency dependence present | Have / Ext |
| History / bias shift | Burst then probe at 1–500 ms | Triode: recovery within 10 % of SPICE | Have (Classic) / Ext |
| Aliasing (effective 2×–8×, ADAA) | 1 kHz / 5 kHz; Drive 60/100 % | Reference ≤ −80 dBc | Have / New |
| Mix phase match | Mix 0–100 % | No comb filtering | Have |

## 4. Signal chain and routing

| Test | Parameters | Pass criterion | Status |
|---|---|---|---|
| Display = DSP | 3 routings × 2 orders × 2 positions × 8 ON states | All 96 states agree | Have |
| PARALLEL / HYBRID sums | All levels | Analytic sum within 0.001 dB | Have |
| Chain orders | 6 orders × module settings | Documented effects; click-free reorder | Have |
| Mode layer | Reference ↔ Creative switch | Creative bit-exact with today; switching click-free | New |
| Latency | All factors | 0 samples reported; group delay documented | Have (2×) / New |
| CPU | Each factor × module set; idle | Documented; idle target after P1-5 | Have / New |

## 5. Musical and integration testing

| Test | Material | Criterion | Status |
|---|---|---|---|
| ABX: aliasing audibility | Bright drums, synths, bass, at 1× vs the minimum factor | Detection threshold documented | Ext |
| ABX: Classic vs implicit solver | Resonant sweeps at 4–16 kHz | Preference and difference documented | Ext |
| OPTO / VCA on programme | Vocal, bass, mix bus | Listening notes against a hardware unit, if available | Ext |
| Live 12 integration | Device load, Sets from v1.1–v1.5, automation, MIDI, sidechain, freeze | All checklist items pass | Ext |

# Hardware fidelity scorecard

## The scale, and how it is applied here

| Class | Meaning (from the brief) | Rule used in this audit |
|---|---|---|
| **A** Circuit-faithful | Circuit-derived and validated against suitable references | Requires validation against hardware measurements or a full circuit simulation (SPICE). **No model meets this, because no such reference was available.** |
| **B** Behaviourally faithful | Reproduces the defining behaviour, simplified circuit | The topology comes from a published circuit analysis; the nonlinearity sits where the circuit has it; the small-signal response is verified against that analysis; the defining behaviours are present. **Validation is theoretical only**, so every B is marked *(theoretical)*. |
| **C** Hardware-inspired | Some characteristics; important ones omitted | The structure is plausible or partly derived, but defining behaviours are missing, invented or measurably off. |
| **D** Generic DSP | Similar function; does not reproduce the hardware | No circuit basis for the claimed reference, or none is claimed |
| **E** Unverified | Insufficient evidence | The reference cannot be identified well enough to judge |

Evidence codes refer to the reports:
- **F** = `FILTER_FIDELITY_REPORT.md`
- **C** = `COMPRESSOR_FIDELITY_REPORT.md`
- **P** = `PREAMP_SATURATION_FIDELITY_REPORT.md`
- **I** = `DSP_IMPLEMENTATION_AUDIT.md`

## Filters

| Model | Class | Key evidence |
|---|---|---|
| **Moog ladder LP** | **B** (theoretical) | Huovilainen per-stage tanh model (I). Small-signal within 0.18 dB of 1/((1+s)⁴+k) below 5 kHz at 44.1/1× (F §2.1). Self-oscillates; bass loss with resonance; resonance compression with level (F §3.2). Against: no even harmonics; the top octave cramps at high fc at 1×; oscillation −17 to −27 cents low at ≤ 1 kHz; one-sample nonlinear lag. |
| **Ladder HP "ALT pole-mix"** | **D** | Not a Moog circuit; a pole mix. Honestly labelled in the UI. |
| **TB-303 diode ladder** | **B** (theoretical) | Stinchcombe's 303 polynomial reproduced exactly; feedback HPF present; small-signal 0.14 dB at 1 kHz (F §2.1). Against: symmetric (H2 −135 dBc); oscillation tracks fc −40 to −65 cents (mapping); one-sample lag. |
| **Korg 35 LP/HP (MS-20 Mk1)** | **C** | Pirkle block model with loop nonlinearity; accurate oscillation pitch (±3 cents) (F §4.1). Against: symmetric tanh instead of diodes (no H2); KORG35 transistor-level character absent; HP order unverified against Stinchcombe's study; the Mk2 (LM13600) revision absent, which is a revision ambiguity in the name "MS-20"; aliasing −50 dBc at 1× in the F5 test. |
| **Steiner-Parker LP** | **C** | Correct Sallen-Key/VCR topology with Q from amp gain (I). Against: diode strings modelled as a symmetric tanh (wrong I–V shape for biased diodes); mirrored branch absent; worst aliasing (−25 dBc at 1×, F §3.3); **unbounded growth at 1×, fc 12 kHz, res 100 %** (F §4.2). |
| **Steiner-Parker HP** | **C** / E | HP injection node inferred; measured 6 dB/oct skirt against the "12 dB" label (F §2.4). 1974 article not accessed. |
| **Oberheim SEM LP/HP** | **B** (theoretical) | OTA SVF with tanh integrator inputs; LP/notch/HP morph; small-signal 0.97 dB at fc 1 kHz, 44.1/1× (cramping-limited; 0.24 dB at 2×); clean (0.13 % THD at 0 dBFS); never self-oscillates, which is conservative and documented. Against: SEM damping circuit not modelled from schematic; no H2. |
| **Sherman Filterbank** | **E** (behaviour at C level) | No schematic exists publicly, so fidelity cannot be judged. The implementation is missing documented features (multimode morph, parallel mode, harmonic intervals, VCA overdrive, ring mod) and adds an invented feedback path. **Diverges to +249 dBFS** at 1×, fc 12 kHz, res 100 % (F §4.2). |
| **Slope extensions (36/48; 24 on 12-native models)** | **D** | Ideal linear Butterworth sections. Generic by design, and labelled "EXT" in the UI. |

## Band-pass engine

| Configuration | Class | Evidence |
|---|---|---|
| SEM / SVF (native) | **C** | Correct SVF band output, but resonance comes from a regeneration loop the SEM does not have (I). The small signal at res 0 is identical across all five profiles (F §5). |
| K35 / CASCADE (native) | **C** | The series HP→LP principle is right, but the sections are generic nonlinear SVFs, not KORG35 sections. |
| Steiner / SVF ("native response") | **C** | Response-equivalent only; not the Sallen-Key network. |
| ARP 2600, all architectures | **D** | The hardware has no band-pass. Derived, as the UI says. The 14 kHz roll-off is unverified. |
| EMS VCS3, all architectures | **D** | The hardware has no band-pass. A generic core with a diode-like secant. |
| All other model × architecture pairings | **D** | Non-native combinations |

## Dynamics and saturation

| Module | Class | Evidence |
|---|---|---|
| **OPTO (LA-2A)** | **C** | **For:** feedback detection; a two-stage, history-dependent release whose first 50 % takes 55–75 ms against a reference of about 60 ms, with full recovery in 1–6.7 s, inside the published range; side-chain pre-emphasis (C §1). **Against:** attack 2.3–2.9 ms against a reference of about 10 ms; COMP ratio 2.2–2.7:1 against a nominal 4:1; LIMIT about 10:1 against about ∞; no 12AX7/12BH7 stages or transformers; LDR law abstracted. |
| **VCA (API 2500)** | **C** | **For:** NEW feed-forward and OLD feedback; THRUST in the detector only, proven bit-identical (C §2.1); RMS detection; exact ratios and releases. **Against:** attacks below 1 ms not achieved (0.03 ms setting measures 0.71 ms); THRUST curves approximate, with MED lacking the HF lift; link filter missing; ideal gain element with no audio-path character; OLD-mode ratio scaling unverified. |
| **TUBE ("triode")** | **D** | Static asymmetric waveshaper (P §1). Frequency-independent THD (P §2.3) and no memory (P §2.4), which proves there is no triode/load-line/coupling dynamics; −30 dBc aliasing at Drive 100 (P §2.6). |
| **GATE** | n/a (D, no claim) | Generic, with no hardware reference claimed |
| **Output soft clip, DC blockers** | n/a | Utilities |

## Infrastructure

| Item | Assessment |
|---|---|
| 2× polyphase IIR oversampler | **Correct and effective.** It lowers the aliased products by 49–69 dB at the F5 test point. **Off by default**, and only 2× (insufficient for tube Drive 100). |
| ZDF / secant solver | **Correct** for the linear part. The one-sample lag in the nonlinearity is the root cause of the high-fc instability. |
| Routing / display agreement | **Verified** for all 96 states (offline) |
| Reorder lanes, crossfades, state copy | **Verified** click-free in the existing tests |

## Summary

| Class | Count | Models |
|---|---|---|
| A | 0 | — (no hardware references available) |
| B (theoretical) | 3 | Ladder LP, TB-303, SEM |
| C | 8 | K35 LP/HP, Steiner LP, Steiner HP, the three native BPF pairings (SEM, K35, Steiner), OPTO, VCA |
| D | 7 groups | Ladder HP, slope extensions, BPF ARP, BPF EMS, BPF non-native pairings, TUBE, gate (generic, no claim) |
| E | 1 | Sherman |

# Revised hardware fidelity scorecard

## Classes (from the review brief)

| Class | Meaning |
|---|---|
| **A** | Validated against physical hardware or a sufficiently complete circuit simulation |
| **B** | Behaviourally faithful, supported by credible circuit analysis and verified measurements |
| **C** | Partially faithful, with identifiable deviations |
| **D** | Generic DSP or creative approximation |
| **E** | Insufficient reference information for a defensible classification |

**Qualifier.** "(theoretical)" means the evidence is engine measurements against *published analyses*, with no hardware and no SPICE.

**How this review applies B.** The circuit analysis must be **published** (grade P), not a forum or module description. Under that stricter rule, any model whose only support is [F]/[M] cannot be B.

**Stability.** Stability defects do not change a fidelity class: numerical stability is not analogue fidelity. They are listed separately at the end.

## Filters

| Model | Original | **Revised** | Reason for change / retention | Evidence needed to improve |
|---|---|---|---|---|
| Moog ladder LP | B (theoretical) | **B (theoretical)** | Retained. Huovilainen's published per-stage model; small signal 0.18 dB vs 1/((1+s)⁴+k). **Caveat added:** the high-frequency response is reference-quality only at ≥ 2× (at 1×, bilinear shift +112 cents predicted at fc 12 kHz, 44.1 kHz). Aliasing at the default Comp 100: −33 dBc at 1× in the bright test. | SPICE of a Moog ladder (transistor level) for large-signal transfer and oscillation amplitude → A (simulation). Then hardware for A (hardware). |
| TB-303 diode ladder | B (theoretical) | **B (theoretical)** | Retained. The Stinchcombe 303 polynomial is reproduced exactly. Oscillation sits 40–65 cents below fc: a property of the cutoff mapping, not tracking error. | SPICE of the 303 ladder, or x0xb0x measurements (a1k0n data exist, [F]) |
| Oberheim SEM | B (theoretical) | **C** | **Downgraded.** Support is [F]/[M] only, the SEM schematic was not inspected, and the damping circuit is generic (R = 20^(−res)). The input clip 2·tanh(x/2) has no stated origin. | Schematic inspection → derive the damping and resonance network → SPICE. That could reach B (theoretical) or A (simulation). |
| Korg 35 / MS-20 (Mk1) | C | **C** | Retained. Pirkle's published *DSP* model is not a transistor-level KORG35 analysis. HP order unverified. Mk2 absent. | Stinchcombe's MS-20 study; SPICE of the Mk2 LM13600 circuit (public) for a separate Mk2 model |
| Steiner-Parker LP | C | **C** | Retained, but the **reason is corrected**: the diode-string law is *unverified*, not "wrong". Mirrored branch absent. Internal oscillation level about +4.5 dBFS. | SPICE of CGS35 / the 1974 circuit |
| Steiner-Parker HP | C / E | **E** | **Clarified.** The modelled 6 dB/oct skirt follows from the *inferred* injection node, and no source verifies that node. | The 1974 article or a SPICE of the actual circuit |
| Sherman Filterbank | E | **E** | Retained. No circuit is identifiable. | A hardware unit (black-box identification) |
| Ladder HP "ALT" | D | **D** | Retained. Pole-mix; not a Moog circuit. Honestly labelled. | n/a (creative) |
| Slope extensions | D | **D** | Retained. Ideal Butterworth sections (creative extension). | n/a (creative) |

## Band-pass engine

| Configuration | Original | **Revised** | Reason |
|---|---|---|---|
| SEM / SVF | C | **C** | The SVF BP output exists on the SEM; the regeneration loop does not |
| K35 / CASCADE | C | **C** | The series HP→LP principle is correct; the sections are generic |
| Steiner / SVF ("native response") | C | **D** | **Downgraded.** Response-equivalent only; neither the topology nor the nonlinear elements correspond to the circuit |
| ARP 2600 (all) | D | **D** | The hardware has no BP. The 14 kHz roll-off is [F]. |
| EMS VCS3 (all) | D | **D** | The hardware has no BP |
| Non-native pairings | D | **D** | Creative |

## Dynamics and saturation

| Module | Original | **Revised** | Reason | Evidence needed |
|---|---|---|---|---|
| OPTO (LA-2A-inspired) | C | **C** | Retained, with **corrected reasons**. Release and memory are qualitatively correct. Attack is near the reference at moderate GR (8.1 ms at 6 dB) and fast at heavy GR (2.35 ms at 18 dB). The ratio deviation from "4:1" is *unverified* (weak reference). The documented frequency dependence is absent. No audio-path stages. | Published T4 measurements, or measurement of a unit: attack and release vs GR depth and frequency, static curves |
| VCA (API 2500-inspired) | C | **C** | Retained. The architecture follows the manual. The OLD-mode ratio is exact maths for an ideal loop. The attack floor is real, but its deviation from hardware is unverified. The link filter is missing (documented). THRUST curves are guesses. | Hardware: THRUST detector response, attack and OLD-mode curves; patent text for THRUST |
| TUBE | D | **D** | Retained. A static waveshaper. | R7 triode model with SPICE agreement → A (simulation) for a *new* TUBE type |
| GATE | n/a | **not classified** | No hardware claim | — |

## Summary

| Class | Original count | Revised count | Changes |
|---|---|---|---|
| A | 0 | 0 | — |
| B (theoretical) | 3 | **2** | SEM → C |
| C | 8 | **7** | +SEM; −Steiner HP (→ E); −Steiner/SVF BP (→ D) |
| D | 7 groups | **7 groups** | +Steiner/SVF BP; the gate is no longer classified (no hardware claim) |
| E | 1 | **2** | +Steiner HP |

## Stability status (separate from fidelity)

| Model | Status at 1× | Status at 2× | Root cause |
|---|---|---|---|
| Sherman | **Unbounded at fc ≈ fs/4, res ≥ about 92 %** | Bounded within the cutoff range | Period-2 pumping of a sampled amplitude limiter |
| Steiner LP | **+30 dBFS at fc ≈ fs/4, res 100 %** | Bounded (+4.5 dBFS) | Same family |
| All others | Bounded in the map | Bounded | — |
| Device output | **Propagates any fault for about 1.5–2 s** via the 2 Hz DC blocker | same | DC-blocker memory |

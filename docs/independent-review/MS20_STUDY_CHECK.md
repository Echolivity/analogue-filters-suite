# K35 model vs Stinchcombe's MS-10/MS-20 filter study (review item R9)

**Source:** T. E. Stinchcombe, *A Study of the Korg MS10 & MS20 Filters*, 30 Aug 2006 (rev. 13 Dec 2009), 46 pp.; the user supplied the PDF on 2026-11-18.

**Evidence class: [S].** This is a published circuit analysis, not a manufacturer document or hardware measurement:
- The schematics are SPICE redraws from the MS-10 (Korg35) and KLM-307 (OTA) service schematics, with a BF245A substituted for the 2SK94 JFET.
- The author had not examined the hardware. He marks the asymmetry figures and the "listening test" as unverified.
- So the study's **topology and transfer functions** are used here, but not its waveform magnitudes.

Checks run against the v1.6 engine: `source/tests/review/ms20/check.py` and `refit.py`. Transfer functions re-derived with sympy in `derive.py`.

## What the study establishes

**1. Two different circuits share the name.**
- **Korg35 version (MS-10, early MS-20).** A Sallen-Key low-pass built around the proprietary Korg35 thick-film IC.
  - Two transistors (Q2, Q3) in reverse saturation act as current-controlled resistors.
  - C12 = 3.3 nF and C13 = 1 nF, so C1 ≈ 3·C2.
  - Q4/Q5 (JFET plus PNP) buffer the core into X1 (µA741, gain 1 + 270k/4.7k ≈ 58).
  - Resonance: VR13 → R61 5.6 kΩ / R60 220 Ω (÷26.5) → the bottom of C12.
- **OTA version (later MS-20, daughterboard KLM-307).** Two LM13600 stages, each equivalent to a buffered RC section.
  - Feedback via X5 (gain 1 + 10k/3.3k ≈ 4) into the bottom of C4.
  - Resonance: R29 8.2 kΩ → VR1 10 kΩ.

**2. Low-pass transfer functions.** Re-derived here for the actual component ratios, ωc = 1:

| Circuit | Low-pass | Self-oscillation at | Maximum loop gain in the circuit |
|---|---|---|---|
| Korg35 (R1 = R2/3, C1 = 3·C2) | 1 / (s² + (7/3 − k)s + 1) | k = 7/3 | 58.4/26.5 ≈ 2.2; about 2.4 if the JFET buffer is about 1.1× (borderline oscillation) |
| OTA | 1 / (s² + (2 − k)s + 1) | k = 2 | 0 to about 2.2 (oscillates; preset trimmed for it) |

**3. Both high-pass variants are 6 dB/oct, not 12 dB/oct** (study §7; also noted by Doepfer). Korg grounds the low-pass input and feeds the signal into the lifted end of C2; it does not swap the Rs and Cs. Re-derived:

| Circuit | High-pass |
|---|---|
| Korg35 | s(s + 4/3) / (s² + (7/3 − k)s + 1) |
| OTA | s(s + 1) / (s² + (2 − k)s + 1) |
| Study's equal-RC case | s(s + 2) / (s² + (3 − k)s + 1) |

In each case this is a 12 dB/oct high-pass plus a band-pass term. Below cutoff the band-pass term dominates, so the slope is 6 dB/oct.

**4. Diode placement differs, and the study expects this to be the main audible difference.**
- **Korg35: forward path.** Back-to-back 1N4148s across X1's 270 kΩ give a gain of 58 for small signals. Above about ±0.5 V at X1's output, the stage becomes a unity follower offset by a diode drop. Every frequency passes through it, so passband signals distort as level rises.
- **OTA: feedback path.** Three-diode strings across X5's 10 kΩ: gain 4, conducting at about 2 V. Only frequencies selected by the feedback loop, around cutoff, are affected.

**5. Korg35 asymmetry** ([S], simulation only). The signal modulates the Q2/Q3 currents, so cutoff and resonance depend on the sign of the signal: ringing at about 1.7 kHz on one half and about 2 kHz on the other.

## What the v1.6 "Korg 35 (MS-20 Mk1)-inspired" model actually is

| Property | Measured | Korg35 (Mk1) | OTA (Mk2) |
|---|---|---|---|
| Low-pass core | 1/(s² + (2 − K)s + 1) within 0.23 dB below 3 kHz at res 0, 50 and 80. Against 7/3 − K: up to 5.7 dB off at res 80. | 7/3 − k | **2 − k** ✓ |
| Main non-linearity | Feedback gain limited by a tanh secant ("FB CLIP") | forward-path diode stage | **feedback-path diodes** ✓ |
| Forward non-linearity | 0.85·tanh at the second-stage input (OTA-input-like): 0.6 % THD for a 500 Hz sine at 0 dBFS with fc 7 kHz, nearly independent of resonance | strong (×58, 0.5 V knee) | mild (OTA input stage) ✓ |
| High-pass | s²/(den), **12 dB/oct** (measured 11–12 dB/oct) | 6 dB/oct ✗ | 6 dB/oct ✗ |
| Asymmetry | none | yes ([S]) | none ✓ |

**Conclusion.** The model is labelled Mk1 but is structurally a **hybrid that is mostly the OTA (Mk2) circuit**: its low-pass core, clipper placement and mild forward stage all match the later LM13600 design. The low-pass fit alone cannot separate the two circuits, since the two denominators differ only by a 1/3 resonance offset. The separators are diode placement, the high-pass numerator and the asymmetry, and on each of those the model sides with Mk2 or with neither.

The review's R9 assumed the opposite (that the current model is Mk1 and Mk2 was missing). This check reverses it: **Mk1 is the one that is missing.**

## Decisions (user, 2026-11-18) and status

- **High-pass: changed in place. Done.**
  - The K35 high-pass now implements the OTA circuit's s(s + 1)/den: y = x + LP₂(u − x), with u = HP₁(K·y).
  - Measured: within 0.11 dB of that function (60 Hz–3 kHz) at resonance 0, 50 and 80; 5.6–5.7 dB/oct below cutoff.
  - The Reference aliasing check is still ≤ −80 dBc at 2x.
- **High-pass Drive behaviour: keep the circuit-clean passband (user, 2026-11-19).** Drive 100 gives 0.18 % THD in the K35 high-pass passband, against 32.7 % in v1.5. No behavioural saturator is added; Drive mostly shapes the region around cutoff, as in the built circuit.
- **Low-pass: relabelled, and Mk1 added. Done.** The current model is now described as the OTA (Mk2) circuit; its sound is unchanged and it is the default. The appended **K35 Circuit** parameter selects KORG-35 (Mk1) for both the LPF and the HPF. Switching uses the 4 ms duck and a state reset.

| Mk1 check (`tests/v16_tests.py`) | Result |
|---|---|
| LP fit to 1/(s² + (7/3 − k)s + 1) | within 0.23 dB |
| HP fit to s(s + 4/3)/(…) | within 0.11 dB |
| The study's detection test (500 Hz, fc 7 kHz, res 50) | Mk1 THD 0.009 % → 0.151 % → 4.46 % at −24/−12/0 dBFS; Mk2 0.002 % → 0.037 % → 0.59 % |
| Self-oscillation | at res 100 (−6.8 dBFS, held by the diodes); not at res 90 |
| fs/4 sweep | worst −3.9 dBFS |
| Reference oversampling | LPF 8x (−105.3 dBc; 4x gives −76.5); HPF 4x (−86.9 dBc) |
| Mid-signal circuit switch | ducked, no step |
| CPU at 8x | 4,013 ns, vs 1,716 for Mk2 |

Diode stage fitted to Figure 17: n·Vt = 52 mV, Is = 1.72 nA. Solver: one scalar monotone equation in the diode voltage. The offline check (`ms20/solver.py`) gives a worst relative residual of 1.2e-5 with four Newton steps.

**Assumptions:**
- 5 V peak per unit inside the filter, after Drive (−12 dB at Drive 0), so the knee is at about +2 dBFS input at Drive 0. CHARACTER adds 0 to +24 dB of drive, with makeup gain as Drive. The Reference minimums hold at the default CHARACTER.
- R1 = R2/3, which the study itself doubts; equal resistances would move self-oscillation to k = 5/3.
- The JFET buffer is ×1.1, so maximum loop gain is about 2.4.
- MS-10 values are used for the MS-20.

**Not modelled:** the asymmetric resonance ([S], unverified).

## Options as presented

- **Labelling.** Relabel the current model as "MS-20 Mk2 (LM13600 OTA)-inspired". The sound is unchanged.
- **Mk1.** Add the Korg35 (Mk1) circuit as an **appended parameter** (e.g. "K35 Circuit: OTA / KORG-35"), not a new value on LPF/HPF Model. Extending those lists would break `compat.py`, which requires every earlier parameter box and gen~ range to stay identical. The Mk1 circuit would have:
  - the Sallen-Key core with damping 7/3 − k;
  - the forward diode stage (×58, 0.5 V knee);
  - optionally the asymmetry, which is [S] only, so it would be off or labelled.
- **High-pass.** Change it to the hardware 6 dB/oct form, either in place (Sets using the K35 high-pass change) or as an appended option.

**Assumptions the Mk1 model would need, stated up front:**
- **Level reference.** The diode knee is a voltage, so the model needs a volts-to-dBFS reference. Proposed: 0 dBFS = 5 V peak, a typical synth level. With the MS-10 values, the knee at X1 (0.5 V) then sits at about 2.2 V peak at the filter input, about −7 dBFS. This is a free parameter, and Drive moves it.
- **Solver.** A ×58 diode stage inside the loop is stiff. It needs an implicit solve, the v1.6 fs/4 sweep and a measured oversampling minimum from the start.

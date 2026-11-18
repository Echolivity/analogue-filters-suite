# Oberheim SEM model vs the SEM-1A schematic

**Sources:**
- *Oberheim SEM-1A Schematics* (Internet Archive item `Oberheim_SEM_1A_Schematics`, 8 pp.; VCF on p. 6, output and notch on p. 7). The user supplied the link; it was read in the cloud browser at 3–4× zoom.
- The *Oberheim Synthesizer Expander Module* instruction manual (March 1975), supplied by the user.

**Evidence class: [P].** Both are manufacturer documents.

## Circuit (SEM-1A, p. 6–7)

- **Input summer.** Three input mixers (PS13–PS15) feed A12, a 301A inverting summer, through 0.15 µF and 220 kΩ. A12's feedback is R139 100 kΩ, so the input gain is 0.45. A12's output is the **HP** output.
- **Integrators.** Two CA3080 OTA integrators (A13, A15) with 300 pF capacitors and 2N4302 JFET buffers (Q39 → **BP**, Q40 → **LP**). Each OTA's input arrives through a 100 kΩ / 220 Ω divider, so the OTA sees the signal ÷455.
- **LP feedback.** LP returns to A12's summing node through R138 100 kΩ (with C18, 10 pF).
- **Damping (resonance).** The buffered BP (A14) returns to A12's summing node through C22 (0.33 µF) along two paths:
  - **Linear:** BP → PS16 "RES" 50 kΩ pot (wiper) → R157 33 kΩ. Damping 2ζ ≈ (100k/33k)·w = 3.03·w, where w is the wiper position (w = 0 at maximum resonance).
  - **Diode limiter:** BP → R159 47 kΩ / R158 10 kΩ divider (×0.175) → antiparallel 1N4148s D11/D12 → R156 100 kΩ. Extra damping appears once |BP| exceeds about 2.6 V, so amplitude-dependent damping tames high resonance.
- **Outputs.** PS19, a 50 kΩ "NOTCH" pot, crossfades between the HP and LP outputs into A17, giving a notch at the centre. S504 (the pot's click switch) selects BP. The manual: fully left and clicked off is BP; fully left is LP; 12 o'clock is notch; fully right is HP.
- **Manual on resonance:** "When turned to the right, causes peaking action in the filter". The calibration step rotates Resonance fully clockwise and trims for the fundamental to be prominent. Neither document mentions self-oscillation.

## The v1.6 model against it

| Property | Model (`f_sem`) | Schematic | Verdict |
|---|---|---|---|
| Core | 2-pole SVF, OTA integrators with tanh input saturation | the same | **Conforms** |
| LP / notch / HP mix; BP separate | LP + m·HP (and the reverse), notch at m = 1 | the PS19 crossfade, with BP on a switch | **Conforms** |
| Input non-linearity | 2·tanh(x/2) | linear op-amp summer (gain 0.45); only the ±15 V rails clip | **No circuit origin** |
| Damping law | R = 20^(−res): Q 0.5 → 10 | 2ζ = 3.03·w, linear in the wiper: Q 0.33 → unbounded at w = 0 | **Different law and range** |
| Amplitude-dependent damping | none | D11/D12 path, active above about 2.6 V BP | **Missing** |
| Self-oscillation | never (Q ≤ 10) | not specified. With w = 0 only the residual losses and the diode path damp it. Whether a real unit self-oscillates depends on pot end resistance and losses that the schematic cannot give. | **Undetermined** |

## Decision and status (user, 2026-11-19): circuit damping, no self-oscillation. Done.

- **Input:** linear (the old 2·tanh(x/2) is removed). The op-amp and buffer rails limit the HP, BP and LP outputs at ±13 V (2.6 units), with a sharp knee that is linear at normal levels.
- **Damping:** 2R = 0.1 + 3.03·(1 − res). This is the RES-pot law with a linear taper, plus a 0.1 floor (Q ≤ 10, the same maximum as before), so the filter never self-oscillates. Q now runs from 0.32 to 10 (v1.5: 0.5 to 10).
- **D11/D12 limiter:** extra half-damping 0.463·max(0, 0.175·|BP| − 0.45 V)/|BP|, smoothed and exactly 0 at small signal, with BP in volts at 5 V per unit. It is evaluated at the lagged BP, then re-solved at the current BP.
- **Measured:**

  | Check | Result |
  |---|---|
  | Small-signal fit to 1/(s² + 2R·s + 1) | within 0.23 dB at res 0, 50, 90, 100 |
  | Res 100 gain at 1 kHz | +20.0 dB at −30 dBFS, +18.3 at −12, +11.2 at 0 dBFS |
  | Impulse at res 100 | decays to −220 dB |
  | 1x aliasing at the bright test point | −140 dBc (v1.5: −89; the soft clip was the main distortion) |

- **Tests:** validate's SEM reference law is updated. The tracking check now compares the SEM peak with its circuit-Q position (Q ≈ 1.8 at res 85 puts the peak about 145 cents below fc, as a 2-pole should). A new v1.6 check locks this in.
- **Goldens:** only SEM scenarios change.

**Assumptions as stated before the change:**
- the RES pot taper (linear assumed);
- a level reference for the 2.6 V diode threshold;
- a residual minimum damping, if self-oscillation is to be excluded.

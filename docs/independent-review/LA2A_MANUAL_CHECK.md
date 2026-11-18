# OPTO vs the Teletronix LA-2A operating manual and schematic

> **Update (same day): schematic received.** The user supplied the UREI LA-2A manual. Its last page is the Teletronix schematic **C-10953 rev C (6 Aug 1968)**, which is legible. It resolves item 8, and v1.6 now implements LIMIT and Emphasis from it. See *Schematic findings* at the end. The conformance table below records the state **before** that change.

**Source:** *Teletronix Model LA-2A Leveling Amplifier* operating manual, Library of Congress, MBRS recording-preservation manuals collection: https://tile.loc.gov/storage-services/master/mbrs/recording_preservation/manuals/Teletronix%20Model%20LA-2A%20Leveling%20Amplifier.pdf. The user supplied it on 2026-11-18. It includes the addendum for serial 572 and later (LA-2A 11-66). Evidence class: **[P]**, a primary manufacturer document.

**How it was read.** The scan was read through a text extractor. The specifications and circuit description are legible. The schematic and parts values are mostly **not legible** in the scan, so no component values are used below.

**Measurement.** `source/tests/review/la2a_manual.py` (raw data: `source/build/la2a_manual.json`). It runs the v1.6 engine; the OPTO code is unchanged since v1.3. Levels are relative: the manual's dBm and the device's dBFS are not tied to each other, so only shapes, slopes and differences are compared.

## Conformance

| # | Manual (p. = page of the scan) | OPTO today (measured) | Verdict |
|---|---|---|---|
| 1 | **Release:** about 60 ms to 50 % release (spec item 9; p. 4), then gradual release to complete. Complete release takes 1–15 s (p. 4), or 0.5–5 s depending on previous reduction (p. 2). The manual contradicts itself on this. | 50 % in 55–75 ms; 90 % in 1.1–6.7 s, lengthening with previous reduction (E21) | **Conforms** |
| 2 | **Gain reduction** up to 40 dB | 36 dB (PR 80), 45 dB (PR 100) | **Conforms** |
| 3 | **Compressor slope** (addendum): about 3:1. A 100 % increase in input gives about a 30 % increase in output, i.e. about 2.6:1. | Local ratio 1.7 → 2.8:1 as reduction deepens (PR 80, 3–22 dB GR) | **Conforms** at moderate and heavy reduction. Softer just past the knee. |
| 4 | **Limiter curve** (p. 3): compression from the breakaway point over about 10 dB of input. Then the curve is horizontal: 20 dB more input raises output by **less than 1 dB** (≥ 20:1). | Ratio rises gradually, 4.2 → 9.9:1, and is still rising 40 dB past breakaway; it never reaches 20:1. Output rises **2.1 dB** over the top 20 dB. | **Deviates.** Limiting is about half as firm as stated, and the knee is far wider than about 10 dB. |
| 5 | **R37 frequency-response control** (p. 7). It reduces the low-frequency voltage fed to the Peak Reduction control; C12 passes the highs. Flat gives equal reduction at all frequencies. Maximum gives about 10 dB more reduction at 15 kHz than below 1 kHz. | Flat: 15 kHz vs 500 Hz within 0.2 dB. Emphasis 100 %, LIMIT: +8.2 to +8.9 dB at 15 kHz. COMP: +3.7 to +6.0 dB. | **Flat conforms.** Maximum is about 1–2 dB short in LIMIT. The manual doesn't say which mode its figure refers to. |
| 6 | **Distortion:** the limiter is rated for at least 30 dB of reduction with under 0.5 % harmonic distortion (p. 7). No test frequency is given; the setup procedure uses 400 or 1000 Hz. | 1 kHz: 0.018 % at 36–45 dB GR. 5 kHz: 0.001 %. **100 Hz: 1.8 %.** | **Conforms at 1 kHz.** At 100 Hz it would fail if the rating applies there; the manual doesn't say. |
| 7 | **Attack:** "essentially instantaneous (10 µsec)" (spec item 8) | t63 = 8.1 ms at 6 dB GR, 4.0 ms at 12 dB, 2.35 ms at 18 dB (E19) | **Conflicts, ~1000×.** The manual doesn't define the measurement. The figure is plausibly the electroluminescent panel's response, not the photocell's. It is not used for calibration. |
| 8 | **Side-chain tap point** (p. 4): "a portion of the input signal" goes through the gain-reduction control to the V3 control amplifier, then via the balance control to the 6AQ5 driver. | OPTO's internal detector reads its **own output** (feedback). Feed-forward is only reachable via Detector = CHAIN with OPTO first. That mode over-compresses badly (output *falls* by 20 dB or more), because the gain law is tuned for feedback. | **Topology deviates from the manual's text.** The illegible schematic must confirm this before any change: "input signal" may be loose wording. |
| 9 | **Audio path:** input transformer (high-impedance winding) → optical attenuator ahead of the first stage → 12AX7 (V1, about 40 dB) → 12BH7 totem-pole output (V2) → output transformer. About 20 dB of overall feedback. Response ±0.1 dB from 30 Hz to 15 kHz. THD < 0.35 % at +10 dBm and < 0.75 % at +16 dBm output. | OPTO is a clean gain element: no tube or transformer stages (R5) | **Targets for R5 now exist.** These THD figures are the first published audio-path numbers in the evidence register. Building the stages still needs the validated triode model (R7) and schematic values. |
| 10 | **Stereo link:** the V3 outputs of two units are joined (terminals 6 and 7) after their balance controls. Both EL drivers then see the combined control signal. | Link = max of the two detector levels, blended by Link % | **Plausible, not verified.** The manual doesn't say how two joined outputs combine (sum or max). |

## What this changes in the review

- **R4 (OPTO calibration)** is no longer blocked by a lack of primary data, for the **static curve** (items 3, 4) and **R37** (item 5). Those figures now have a [P] source. Attack (item 7) stays uncalibrated: the only primary figure is undefined and physically implausible for the photocell.
- **Topology question (item 8):** this is new. If the schematic confirms an input tap, the static curve in item 4 is a feed-forward curve. In that case the right fix is a feed-forward detector with a gain law fitted to items 3 and 4, not a steeper feedback law.
- **R5 (audio path)** gains measurement targets (item 9). It still waits on R7 and a legible schematic.
- Unchanged: release and memory, maximum reduction, and flat response conform.

## Schematic findings (UREI manual, drawing C-10953 rev C)

**Side-chain tap (resolves item 8).**
- T1's secondary (loaded by R5 68 kΩ) feeds R6 68 kΩ, then the node X / R7 (1–2.7 kΩ, "selected to match T4"), then node Y.
- The two T4A photocells shunt node Y to ground. GAIN (R1 100 kΩ) hangs on node Y.
- **Peak Reduction (R2 100 kΩ) is fed from node X.** The detector therefore reads the *attenuated* signal: a **feedback** design, as OPTO already was.
- The manual's "a portion of the input signal" and its block diagram, which draws the tap ahead of the attenuator, simplify this: R6 belongs to the attenuator.

**COMP/LIMIT (SW3).**
- The switch pivot is at node X. In COMP it connects to node Y, shorting R7.
- So in COMP the detector senses Vy. In LIMIT it senses Vx = Vy·(1 + R7/R_cell), a term that grows as the cell resistance falls.
- A static solve with the schematic values and a cell law R ∝ sense^−2 gives:
  - COMP: 1.9 → 3.0:1, the manual's ~3:1.
  - LIMIT: the same as COMP to about 15 dB of reduction, then flat, then over-compressing until the cell bottoms out.
- The real switch therefore changes the high-reduction behaviour, not the threshold.

**R37 "LIM RESP".**
- R37 (0–1 MΩ) ∥ C12 (1 nF) sits in series from the V3 plate (via C9 0.02 µF) to the balance pot R3 (1 MΩ). That node is loaded by C6 0.01 µF + R30 47 kΩ (∥ a 50–380 pF trimmer), and also feeds the stereo-parallel terminal.
- Relative to flat, R37 at maximum is a side-chain *cut*: −15 dB near 200 Hz, −8 dB at 1 kHz, about 0 above 5 kHz. That puts 15 kHz +12 dB vs 500 Hz and +8 dB vs 1 kHz, against the manual's ~+10 dB vs below 1 kHz.
- The result is insensitive to the unknowns:

  | Unknown | Range tried | Effect |
  |---|---|---|
  | V3 source impedance | 25–50 kΩ | < 1 dB |
  | Trimmer | 50–380 pF | < 0.5 dB |

**Implemented in v1.6.** Measured with `tests/review/la2a_manual.py`, `tests/dyn_tests.py` and the engine harness.

| Item | Before | After |
|---|---|---|
| COMP | — | Unchanged (golden renders bit-identical) |
| LIMIT | Own (4c)⁹ law; ratio 4.2 → 9.9:1; never flat | COMP law + the R7 sense term (R7 = 1.8 kΩ assumed, mid-range) + a 40 dB cell floor. Tracks COMP to about 15 dB GR, then rises 0.74 dB over a 20 dB window starting 24 dB above breakaway. Manual: < 1 dB, starting about 10 dB above breakaway. |
| Emphasis | 2.5 kHz high-frequency shelf | The R37 network (3rd-order bilinear; matches the analog response within 0.1 dB). Flat: 15 kHz vs 500 Hz within 0.25 dB. Maximum: +9 to +12 dB more reduction at 15 kHz. |
| THD at 100 Hz, ≥ 25 dB GR (LIMIT) | 1.8 % | 0.37 % (manual < 0.5 %) |

**Remaining gaps:**
- LIMIT flattens later than the manual's Figure 1. That figure describes the pre-switch unit, and the gain-law exponent is not measured from a T4 cell.
- Attack.
- The audio path (R5).

## Still needed

- ~~A legible LA-2A schematic~~: received (C-10953 rev C). The audio-path operating points (R5 work) can now be read from it.
- Published T4 / T4B measurements (EL panel and photocell attack), to calibrate attack.

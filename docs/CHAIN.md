# Processing chain: Tube, Opto (LA-2A-inspired), VCA (API 2500-inspired), Gate (v1.3)

## Where the chain sits

```
input ─► LPF / HPF / BPF section (unchanged) ─► [ SLOT 1 ─► SLOT 2 ─► SLOT 3 ] ─► GATE ─► (KEY LISTEN) ─► DC block ─► Output ─► Soft clip ─► out
                                                ▲ chain input (CHAIN detector source)
external key (plugin~ 3/4, KEY FROM selector) ──► EXT detector source for Opto, VCA and Gate
```

The chain runs at the base sample rate after the filter section. The tube oversamples 2x internally. With all three modules and the gate off (the default), the device output is bit-identical to v1.2. Existing Sets therefore load and sound unchanged.

## Reordering

- **Any of the six orders** can be chosen with the Chain Order parameter (automatable and MIDI-mappable), the three suggested starting points, or by dragging the blocks.
- **Dragging:** each block has a DRAG grip. Drag it left or right and release: one grip-width moves the block one slot, a full drag moves it two. The other two blocks keep their relative order. The block positions on screen always follow the Chain Order parameter.
- **Suggested configurations** (they only set the order; every other setting is untouched):
  - **WARM DUB:** Tube → Opto → VCA
  - **PUNCH & COLOUR:** VCA → Tube → Opto
  - **FINAL COLOUR:** Opto → VCA → Tube
- **No clicks:** the engine keeps two copies ("lanes") of the chain. On an order change, the full state of the running lane is copied into the idle lane: compressor gain reduction, optical-cell memory, filter and oversampler states. The idle lane takes the new order, and the two are crossfaded over 25 ms. Gain reduction is continuous across the change, and all 30 possible transitions measure click-free.

## Modules

Every module has **ON** (10 ms click-free fade; a fully bypassed module is skipped and its state reset), **Input** and **Output** gain (±24 dB), **Mix** (dry/wet), and IN/OUT level meters on its block. The compressors also show a GR readout.

### TUBE: triode-stage saturation
- **Model:** a biased asymmetric triode-style transfer curve, harder on the positive (grid-conduction) side, with its idle point removed so it adds no DC. It is followed by a "Miller" Tone low-pass and an 8 Hz coupling high-pass. This is a generic triode-stage model, not a model of a specific product.
- **Oversampling:** 2x oversampled internally with the device's polyphase IIR half-band filters.
- **Controls:**
  - DRIVE: 0 to +36 dB into the stage.
  - BIAS: asymmetry. 0 gives mostly odd harmonics; raising it adds even harmonics.
  - TONE: 1–20 kHz.
  - AUTO GAIN (on by default): holds a −12 dBFS program level as drive rises, a static calibration rather than loudness normalisation. With it off, output rises with drive by half the drive in dB.
- **Mix:** the dry path runs through the same oversampling filters without the curve, so wet and dry are phase-aligned and Mix never comb-filters. At Mix 0 the tube is a flat allpass with about 3.6 samples of phase delay at 1 kHz.

### OPTO: LA-2A-inspired optical leveller
Sources (v1.6):
- the Teletronix LA-2A operating manual (Library of Congress scan)
- the UREI reissue manual, which includes the Teletronix schematic C-10953 rev C (6 Aug 1968)

See [LA2A_MANUAL_CHECK.md](independent-review/LA2A_MANUAL_CHECK.md).

From the schematic:
- **Attenuator.** T1 → R6 68 kΩ → R7 (1–2.7 kΩ, selected per T4) → the T4A photocells to ground. The Peak Reduction control (R2) takes its signal from the R6/R7 junction, so detection is **feedback** (it reads the attenuated signal).
- **COMP/LIMIT (SW3).** The switch shorts R7. In COMP the detector sees the attenuator output. In LIMIT it sees that output × (1 + R7/R_cell), which stiffens the loop as the cell resistance falls.
- **R37 "LIM RESP".** R37 ∥ C12 (1 nF) sits in series between the V3 control amplifier (via C9) and the 1 MΩ balance pot, which is loaded by C6 + R30. Raising R37 cuts the side-chain below about 2 kHz.

How the model implements this (internal detector; CHAIN/EXT keys keep their earlier law):
- **Timing (unchanged since v1.3).** An EL-panel light state, an LDR with fast and slow components, and a memory that lengthens the release.
- **Gain.** G = 1/(1 + (1.6·c)^p), floored at 40 dB of reduction.
  - COMP: p = 2 (the addendum's ~3:1).
  - LIMIT: p = 3.5, plus the R7 sense term (1 + 0.0444·q). This fits Figure 1, the manual's limiter curve, within 1.4 dB, then dips about 5 dB toward the 40 dB floor.
- **Emphasis.** The R37 network, 3rd order.

Details and measurements: V1.6_ENGINE.md §4b.

Controls: PEAK RED (sidechain gain), GAIN (= Output), COMP/LIMIT, EMPHASIS (R37), SC HPF (20–500 Hz), LINK (0–100 %), SC source.

### VCA: API 2500-inspired bus compressor
Sources: the API 2500 user manual (apiaudio.com, 2018), the 2500 pages of the API Legacy Plus manual, the API 2500 calibration procedure, and the Waves API 2500 plugin manual.

| Control | API 2500 | This model |
|---|---|---|
| Threshold | +10 to −20 dBu, continuous; Waves maps this to −12 to −42 dBFS (0 dBFS = +22 dBu) | −50 to 0 dBFS, a superset kept so saved sets are unchanged; the hardware span is −42 to −12 dBFS |
| Ratio | 1.5, 2, 3, 4, 6, 10, ∞:1 | same |
| Attack | 30 µs, 100 µs, 300 µs, 1, 3, 10, 30 ms | same |
| Release | 50, 100, 200, 500 ms, 1, 2 s, VARIABLE 50 ms–3 s | continuous 50 ms–3 s (covers every step) |
| Knee | HARD / MED / SOFT, no widths published | 0 / 6 / 12 dB (assumption) |
| THRUST | NORM flat; MED "slight" low cut and high lift; LOUD "a gradual, linear filter (3 dB/oct)", −15 dB at 20 Hz, +15 dB at 20 kHz, ahead of the RMS detector | NORM flat; **LOUD 10 dB/decade through 0 dB at 632 Hz** (within 0.2 dB, 20 Hz–20 kHz at 44.1/48 kHz); **MED half that slope (±7.5 dB), an assumption** |
| Type | NEW feed-forward / OLD feedback | same |
| Detector | one RMS detector per channel, log-domain (calibration: 1 V DC per 10 dB) | true RMS, 3 ms, dB domain |
| L/R Link | IND, 50–100 % in six steps; each channel keeps its own detector | continuous 0–100 % (covers every step) |
| Shape (link filter) | HP / LP / BP, no frequencies published | not modelled |
| Makeup | AUTO keeps output about constant as threshold and ratio change | AUTO = static makeup from threshold and ratio |
| Defaults | 4:1, 1 ms, VARIABLE 0.5 s, HARD, NORM, NEW, 100 %, AUTO | 4:1, 1 ms, 0.3 s, HARD, NORM, NEW, 100 %, manual (kept for saved-set compatibility) |

The model is a true-RMS detector (3 ms), a dB-domain gain computer with HARD/MED/SOFT knee, and attack/release ballistics on the gain reduction.

**THRUST realisation:** six first-order high shelves, least-squares fitted to the tilt (fixed corners 39.7 Hz – 15 kHz; MED uses the same corners with smaller steps), normalised to 0 dB at 632 Hz. At 96 kHz LOUD is within 0.8 dB (the error is near 20 kHz). The VALIDATION THRUST curve test measures it through KEY LISTEN.

**Not published, so behavioural:** knee widths, detector time constant, the VARIABLE release's programme dependence (Waves: heavier compression recovers more slowly), and the Shape filters.

### GATE: independent, after the chain
- **Detection:** threshold with 4 dB hysteresis; a linked stereo key (max of L/R) through its own KEY HPF and LPF.
- **Timing:** ATTACK and RELEASE are the full open and close times, as linear ramps in dB. HOLD is 0–500 ms.
- **RANGE:** the closed floor, 0 to −80 dB.
- **Independence:** the gate is not part of the reorderable chain, and its settings are independent of the chain order. It starts open when enabled, so switching it on never mutes the track.

## Sidechain, detector sourcing and key listen

Each detector (Opto, VCA, Gate) has its own **source** selector.

| Source | Opto | VCA | Gate | Depends on chain order? |
|---|---|---|---|---|
| **INT** | its own output (feedback, as the LA-2A) | NEW: its own input (feed-forward) · OLD: its own output (feedback) | the gate's input (= chain output) | **Yes**: the detector sees whatever the module actually processes at its current slot. |
| **CHAIN** | signal entering the chain (after the filters) | same | same | **No**: identical detection in all six orders (validated bit-exact). |
| **EXT** | external key (plugin~ 3/4) | same | same | **No.** |

- **Filtering:** sidechain filters (SC HPF, HF EMPH, THRUST, KEY HPF/LPF) are applied after the source selection and always belong to their own detector. Stereo linking is per module (Opto LINK, VCA LINK; the gate is always linked).
- **KEY LISTEN** (OFF / OPTO / VCA / GATE) replaces the device output with the chosen detector's filtered key signal, so you hear exactly what the detector reacts to. Only one key can be auditioned at a time.
- **One external key:** Live's `live.routing` supports a single audio port per Max for Live device. The external key is therefore one stereo input shared by the three detectors, and each detector decides whether to use it.

## Gain staging
- **Headroom:** everything inside the chain is floating point. No stage clips internally; with +12 dB into every module and maximum drive, internal levels peak around +6 dBFS without clipping. The device's existing output soft clip (on by default) is the only limiter.
- **Monitoring:** each module meters its level after its Input gain and at its output.
- **Reordering and loudness:** changing the order changes loudness only as much as the processing itself does (measured spread across the six orders at moderate settings: about 1 dB). Nothing re-normalises loudness automatically.
- **Optional compensation:** Tube AUTO GAIN and VCA AUTO makeup are static calibrations, not dynamic loudness matching, so intentional dynamics and saturation are preserved.

## Real-time safety and latency
- **Real-time safety:** all processing is fixed-size gen~ state (592 state variables, preallocated). There is no allocation, locking or buffering on the audio thread. Routing is a per-slot branch on the current order.
- **Latency:** there is no lookahead, so the device reports 0 latency. The tube's IIR oversampler adds a small frequency-dependent phase delay (about 3.6 samples, 0.075 ms at 48 kHz and 1 kHz) that is not a constant latency, so there is nothing for Live to compensate. The tube's dry path is phase-matched to it.

## State and presets
- **Persistence:** all 44 new controls are Live parameters, so they are saved with Sets and presets and can be automated and MIDI-mapped. This covers the order, every bypass, input/output gain, mix and module setting, and every sidechain source, filter and link setting.
- **Existing Sets:** v1.1 and v1.2 Sets load unchanged. Every existing object, connection and parameter is identical (checked against both device snapshots), and all new controls default to off or neutral.
- **UI-only controls:** the drag grips, the EDIT page tabs and the preset buttons are not parameters, so they never appear in automation and never alter a saved state.

## Limitations (not verifiable here)
- **External key routing:** the `live.routing` KEY FROM selector is configured from the Max reference, which documents the object only briefly. If the selector does not offer tracks, open the device in Max and set the object to the device's audio input 3/4 (see INSTALL.md). The DSP side of the key input is tested.
- **Chain UI:** block dragging, block moving (`thispatcher` scripting) and page switching are built from standard Max objects and verified statically: every scripted object exists, every connection is in range, and the drag lookup table is checked exhaustively. They have not been run inside Max.
- **"Inspired" models:** no module was compared against hardware. The Opto is a behavioural T4 model built on published time constants and ratios; the VCA follows the API 2500's published control set and THRUST curves (knee, detector timing and Shape not published); the Tube is a generic triode stage.

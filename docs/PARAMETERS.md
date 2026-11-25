# Parameters, automation and MIDI mapping

All 102 controls are Live parameters: the 20 from v1.1, 11 from v1.2 and 44 from v1.3, all unchanged, plus 4 for v1.4 filter routing and the v1.6 additions (Engine Mode, High Oversampling, K35 Circuit, 6 Sherman controls, 13 envelope-filter controls and VCA Detector). Every one can be automated, MIDI-mapped (Cmd/Ctrl+M, click the control, move a controller) and key-mapped, and all are stored with the Live Set. Names below are the exact names in Live's automation chooser.

## Low-pass stage (amber)

| Live name | Short | Range | Default | Behaviour |
|---|---|---|---|---|
| LPF Cutoff | LPF Cut | 20 Hz – 20 kHz | 20 kHz (open) | Large knob. Exponential taper (exponent 5): the knob centre is about 640 Hz, close to the true log-centre of 632 Hz. Smoothed in the log-frequency domain (6 ms). **OPEN zone:** from 16 kHz to 20 kHz the stage crossfades to the dry signal, so fully clockwise is bit-transparent and costs no CPU. |
| LPF Resonance | LPF Res | 0 – 100 % | 0 % | Per-model resonance law. Self-oscillation starts at about 92–97 % (not on SEM). 15 ms smoothing. |
| LPF Slope | LPF Slope | 12 / 24 / 36 / 48 dB/oct | 24 | Native taps first, then linear extension sections. 10 ms crossfade between taps, so changing it while playing is click-free. TB-303 has no 12 dB option (12 behaves as 24). Sherman's 12 dB setting plays filter 2 (the resonant one) alone. |
| LPF Drive | LPF Drive | 0 – 100 % | 0 % | Level into the model's nonlinearities: 0.25× (clean headroom) to 8× (+30 dB). 15 ms smoothing. |
| LPF Compensation | LPF Comp | 0 – 100 % | 100 % | Two jobs. **Drive makeup:** at 100 %, small-signal gain rises by only half the drive in dB (+15 dB at full drive) while peaks are held by the saturation, which roughly matches loudness. At 0 % there is no makeup (+30 dB at full drive). **Circuit gain compensation:** restores the bass loss of the Ladder and TB-303 as resonance rises, and divides out the Steiner-Parker amplifier gain K (up to +9.5 dB). All three are real circuit behaviours, shown at Comp 0 in VALIDATION.md. |
| LPF Character | LPF Char | 0 – 100 % | 0 % | Model-specific; the label under the knob changes with the model. See below. |
| LPF On | LPF On | off / on | on | 10 ms crossfade. When off, the stage's model code is skipped and its state reset. |
| LPF Model | LPF Model | 7 models (07 ARP 2600 appended in v1.6: saved indices unchanged) | 03 Moog-style Ladder | ~25 ms crossfade between old and new model. Both run only during the fade. |

## High-pass stage (copper)

Same as the low-pass stage, with these differences:

| Live name | Range | Default | Notes |
|---|---|---|---|
| HPF Cutoff | 20 Hz – 2 kHz | 20 Hz (open) | Exponential taper (exponent 3.46): the knob centre is about 200 Hz, the log-centre of the range. **OPEN zone:** 20–25 Hz crossfades to dry, so fully anticlockwise is transparent. |
| HPF Slope | 12 / 24 / 36 / 48 | 12 | |
| HPF Model | 5 models | 02 Korg 35 / MS-20 | TB-303 is not offered (it has no justified HPF). 03 is the Moog 904B high-pass (24 dB/oct, no resonance: the Resonance knob has no effect on it). |

The other HPF parameters (Resonance, Drive, Compensation, Character, On) match their LPF counterparts.

## Global (centre strip)

| Live name | Range | Default | Behaviour |
|---|---|---|---|
| Stage Order | LP>HP / HP>LP | LP>HP | The output fades out over 4 ms, the order switches, and it fades back in over 4 ms. Filter states are kept. |
| Oversampling | 1x / 2x | 1x | 2x polyphase-IIR half-band up/down sampling (10 allpass coefficients, about 106 dB image rejection). Same 8 ms duck; filter states reset at the switch. In REFERENCE mode this is a minimum (see Engine). Ignored when High Oversampling is not OFF. |
| Output | −24 … +12 dB | 0 dB | 15 ms smoothing. |
| Soft Clip | off / on | on | Linear below −3.1 dBFS, then a smooth tanh knee to a 0 dBFS ceiling. Catches self-oscillation and heavy resonance. |

## CHARACTER knob, per model

| Model | Label | 0 % | 100 % |
|---|---|---|---|
| Sherman | FEEDBACK | no global feedback | 0.92 output→input feedback through saturation (howl, grit); a design addition, not from documentation |
| Korg 35 / MS-20 | FB CLIP | feedback limiting at a high level (open, singing) | limiting at a low level (resonance clamps early, aggressive) |
| Moog-style Ladder | STAGE SAT | circuit-nominal per-stage tanh (Huovilainen) | stage pairs driven 3× harder (compressed, warmer) |
| Steiner-Parker | BP BLEND | signal injected at the LP (or HP) point | signal injected at the BP point; in between, both points are driven, as the original's inputs allow |
| Oberheim SEM | NOTCH MORPH | LP (or HP) | notch |
| TB-303 Diode | SQUELCH | feedback highpass at 8 Hz | feedback highpass at about 300 Hz (thin, squelchy resonance) |

## MIDI mapping tips

- **LPF CUTOFF and HPF CUTOFF** are the performance controls. Map them to two large knobs or faders. Thanks to the exponential tapers, 7-bit CC gives fine steps where it matters. Per-sample smoothing removes zipper noise (validated: no measurable >8 kHz energy from CC stepping).
- For a "bass drop" button, map **HPF Cutoff** to a pad and set the mapping's Min/Max in Live's Mapping Browser (for example 20 Hz to 600 Hz). Press: the bass vanishes. Release: it returns instantly, click-free.
- **LPF Model / HPF Model** can be mapped to an encoder or to buttons; each value is one model.
- Live's Macro knobs work as expected. Map a Macro to LPF Cutoff and HPF Cutoff with inverted ranges to get a single band-sweep control.

## Band-pass stage (brass, v1.2)

Full details, including what BW and Q do in each architecture, are in BPF.md.

| Live name | Short | Range | Default |
|---|---|---|---|
| BPF On | BPF On | off / on | off |
| BPF Model | BPF Model | 01 Oberheim SEM · 02 Steiner-Parker · 03 Korg 35 / MS-20 · 04 ARP 2600 (derived) · 05 EMS VCS3 (derived) | SEM |
| BPF Architecture | BPF Arch | SVF / CASC / MULTI | SVF |
| BPF Centre | BPF Freq | 30 Hz – 12 kHz (exponent 4.39, so the knob centre is about 600 Hz) | 1 kHz |
| BPF Bandwidth | BPF BW | 0.2 – 6 oct | 2 oct |
| BPF Q | BPF Q | 0.5 – 10 | 0.707 |
| BPF Resonance | BPF Res | 0 – 100 % | 0 % |
| BPF Drive | BPF Drive | 0 – 100 % | 0 % |
| BPF Compensation | BPF Comp | 0 – 100 % | 100 % |
| BPF Mix | BPF Mix | 0 – 100 % | 100 % |
| BPF Position | BPF Pos | POST / PRE | POST |

**MIDI tip:** map BPF Centre to a knob and BPF Mix to a fader. With CASCADE, BW about 1.5 oct and Mix about 60 %, you get the classic dub "telephone" mid band riding over the full mix.

## Processing chain (v1.3)

See CHAIN.md for routing, detector sourcing and gain staging. The drag grips, EDIT page tabs and preset buttons are UI only (not parameters).

| Live name | Range | Default |
|---|---|---|
| Chain Order | TUBE > OPTO > VCA · TUBE > VCA > OPTO · OPTO > TUBE > VCA · OPTO > VCA > TUBE · VCA > TUBE > OPTO · VCA > OPTO > TUBE | TUBE > OPTO > VCA |
| Key Listen | OFF / OPTO / VCA / GATE | OFF |
| Tube On | off / on | off |
| Tube Input | -24 – 24 dB | 0 |
| Tube Output | -24 – 24 dB | 0 |
| Tube Mix | 0 – 100 % | 100 |
| Tube Drive | 0 – 100 % | 30 |
| Tube Bias | -100 – 100 | 20 |
| Tube Tone | 1000 – 20000 Hz | 12000 |
| Tube Auto Gain | off / on | on |
| Opto On | off / on | off |
| Opto Input | -24 – 24 dB | 0 |
| Opto Gain | -24 – 24 dB | 0 |
| Opto Mix | 0 – 100 % | 100 |
| Opto Peak Reduction | 0 – 100 % | 40 |
| Opto Mode | COMP / LIMIT | COMP |
| Opto HF Emphasis | 0 – 100 % | 0 | (v1.6: the LA-2A R37 network; cuts the low-frequency side-chain, 0 % = flat) |
| Opto SC HPF | 20 – 500 Hz | 20 |
| Opto SC Source | INT / CHAIN / EXT | INT |
| Opto Link | 0 – 100 % | 100 |
| VCA On | off / on | off |
| VCA Input | -24 – 24 dB | 0 |
| VCA Output | -24 – 24 dB | 0 |
| VCA Mix | 0 – 100 % | 100 |
| VCA Threshold | -50 – 0 dB(FS) | -20 |
| VCA Ratio | 1.5 / 2 / 3 / 4 / 6 / 10 / ∞ :1 | 4:1 |
| VCA Attack | .03 / .1 / .3 / 1 / 3 / 10 / 30 ms | 1 |
| VCA Release | 0.05 – 3 s (VCA) / ms (Gate) | 0.3 |
| VCA Knee | HARD / MED / SOFT | HARD |
| VCA Thrust | NORM / MED / LOUD | NORM |
| VCA Type | NEW (feed-forward) / OLD (feedback) | NEW (feed-forward) |
| VCA SC HPF | 20 – 500 Hz | 20 |
| VCA SC Source | INT / CHAIN / EXT | INT |
| VCA Link | 0 – 100 % | 100 |
| VCA Auto Makeup | off / on | off |
| VCA Detector | RMS / PEAK (225L) | RMS |
| Gate On | off / on | off |
| Gate Threshold | -80 – 0 dB(FS) | -40 |
| Gate Attack | 0.1 – 50 ms | 1 |
| Gate Hold | 0 – 500 ms | 20 |
| Gate Release | 5 – 2000 s (VCA) / ms (Gate) | 150 |
| Gate Range | -80 – 0 dB | -80 |
| Gate Key Source | INT / CHAIN / EXT | INT |
| Gate Key HPF | 20 – 2000 Hz | 20 |
| Gate Key LPF | 200 – 20000 Hz | 20000 |

## Filter routing (v1.4)

See ROUTING.md.

| Live name | Range | Default |
|---|---|---|
| Filter Routing | SERIES / PARALLEL / HYBRID | SERIES |
| Parallel LPF Level | −40 – +6 dB (PARALLEL) | 0 dB |
| Parallel HPF Level | −40 – +6 dB (PARALLEL) | 0 dB |
| Parallel BPF Level | −40 – +6 dB (PARALLEL and HYBRID) | 0 dB |

## Engine (v1.6)

See V1.6_ENGINE.md.

| Live name | Range | Default | Behaviour |
|---|---|---|---|
| Engine Mode | REFERENCE / CREATIVE | REFERENCE | REFERENCE: effective factor = max(your setting, the measured minimum of every active model). LPF minimums: SEM 1x; Sherman, K35 and 303 2x; Ladder and Steiner 4x. HPF 2x, BPF 4x, TUBE 8x. CREATIVE: exactly your setting. |
| High Oversampling | OFF / 4x / 8x / 16x | OFF | Overrides the 1x/2x switch when not OFF. Applies to the filters and TUBE. A change ducks for 8 ms and resets the filter states. |

The ENGINE strip's RUNNING AT readout shows the factors in effect.
| K35 Circuit | OTA (Mk2) / KORG-35 (Mk1) | OTA (Mk2) | Which MS-20 filter circuit model 02 uses, for both the LPF and the HPF. OTA is the v1.5 sound. KORG-35 puts the clipping diodes in the signal path, and CHARACTER drives them. A change ducks for 8 ms and resets the filter states. See MODELS.md. |

## VCA detector (v1.6)

| Live name | Range | Default | Behaviour |
|---|---|---|---|
| VCA Detector | RMS / PEAK (225L) | RMS | RMS: 3 ms true RMS, as the API manuals describe (and as before). PEAK: the traced API 225L, whose THAT 2252 runs with a 100 pF timing capacitor and so reads the instantaneous level; attack and release then act in the dB domain. Both are referenced to the sine peak, so the threshold means the same for a steady sine. Which one the real 2500 uses is open: the measurement pack's R19/R20 renders settle it. |

## Envelope filter (v1.6, Musitronics Mu-Tron III)

Before the filter section. Off by default; when off it is bit-transparent whatever the other settings. The routing amounts work with it on or off.

| Live name | Range | Default | Behaviour |
|---|---|---|---|
| EnvF On | OFF / ON | OFF | Envelope filter in the audio path. |
| EnvF Mode | LP / BP / HP | BP | Output node of the two-integrator filter. |
| EnvF Peak | 0–100 % | 50 % | PEAK 150 k CW log: Q 1.78 → 17.7 (3.4 at 50 %); band-pass gain +8 → +31 dB. |
| EnvF Gain | −18.4 to +31.2 dB | 0 dB | A1 preamp (×0.12–×36.4): sets the sweep depth and the level into the filter. |
| EnvF Range | LO / HI | HI | HI 402 Hz → 7 kHz; LO adds 2200 pF to each 1800 pF (181 Hz → 3.2 kHz). |
| EnvF Sweep | UP / DOWN | UP | DOWN starts high and closes with the envelope. |
| EnvF Attack | 0.5–50 ms | 1.55 ms | C9 charge (circuit: 330 Ω × 4.7 µF), plus the photoresistor's on-lag. |
| EnvF Release | 10–1000 ms | 221 ms | C9 drain toward −9 V (circuit: 47 k × 4.7 µF; nearly linear), plus the photoresistor's off-lag. |
| EnvF Mix | 0–100 % | 100 % | Dry / wet. |
| EnvF Output | −24 to +12 dB | 0 dB | Output level. |
| EnvF to LPF / HPF / BPF | −5 to +5 oct | 0 | Cutoff shift at full sweep; follows UP/DOWN. |

## Sherman (v1.6, Filterbank 2 manual)

These apply to model 01 in either stage. They are behavioural, matching documented behaviour rather than a verified circuit.

| Live name | Range | Default | Behaviour |
|---|---|---|---|
| Sherman Modes | STAGE / PANEL | STAGE | STAGE gives LP in the LPF stage and HP in the HPF stage (as v1.5). PANEL uses Balance and Correction. |
| Sherman Balance | 0–100 % | 0 | Lp (0) → Bp (50) → Hp (100). PANEL only. |
| Sherman Correction | −100 to +100 % | 0 | −Bp (−100) … 0 … −Bp + Lp + Hp (+100). PANEL only. |
| Sherman Harmonics | 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 16 | 1 | Filter 2 at the cutoff ÷ n, at 24 dB only; changes glide over about 3 ms. |
| Sherman Limit | NORMAL / LIMIT | NORMAL | Keeps the resonance alive under heavy Drive (mechanism invented). |
| Sherman Clock | SMOOTH / CLOCK | SMOOTH | Clocked (switched-capacitor) character: clock at 100 × cutoff, staircase grain and a faint whine. Smooth above cutoff ≈ engine rate ÷ 100. Reference mode forces at least 8x while on. Constants assumed. |


# Parameters, automation and MIDI mapping

All 31 controls are Live parameters: the 20 from v1.1, unchanged, plus 11 for the v1.2 band-pass engine. Every one can be automated, MIDI-mapped (Cmd/Ctrl+M, click the control, move a controller) and key-mapped, and all are stored with the Live Set. Names below are the exact names in Live's automation chooser.

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
| LPF Model | LPF Model | 6 models | 03 Moog-style Ladder | ~25 ms crossfade between old and new model. Both run only during the fade. |

## High-pass stage (copper)

Same as the low-pass stage, with these differences:

| Live name | Range | Default | Notes |
|---|---|---|---|
| HPF Cutoff | 20 Hz – 2 kHz | 20 Hz (open) | Exponential taper (exponent 3.46): the knob centre is about 200 Hz, the log-centre of the range. **OPEN zone:** 20–25 Hz crossfades to dry, so fully anticlockwise is transparent. |
| HPF Slope | 12 / 24 / 36 / 48 | 12 | |
| HPF Model | 5 models | 02 Korg 35 / MS-20 | TB-303 is not offered (it has no justified HPF). Ladder HP is labelled ALT. |

The other HPF parameters (Resonance, Drive, Compensation, Character, On) match their LPF counterparts.

## Global (centre strip)

| Live name | Range | Default | Behaviour |
|---|---|---|---|
| Stage Order | LP>HP / HP>LP | LP>HP | The output fades out over 4 ms, the order switches, and it fades back in over 4 ms. Filter states are kept. |
| Oversampling | 1x / 2x | 1x | 2x polyphase-IIR half-band up/down sampling (10 allpass coefficients, about 106 dB image rejection). Same 8 ms duck; filter states reset at the switch. |
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

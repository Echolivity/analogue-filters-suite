# Sherman: what the real unit is reported to do, compared with the model

No measurements of a real Filterbank exist in public. The demos online are processed music with no dry reference, so they cannot give curves. This check uses what reviewers and owners report, and measures the model against each point. It is **qualitative evidence**. The model stays behavioural (grade E).

## Sources
- **[SOS97]** Sound On Sound, *Sherman Filterbank* (Chris Carter, April 1997). This is the Filterbank 1.
- **[SOS01]** Sound On Sound, *Sherman Filterbank 2* (Paul Nagle, July 2001).
- **[SOS19]** Sound On Sound, *Sherman Filterbank 2 Compact* (Rory Dow, August 2019).
- **[TAPE]** Tape Op, *Filterbank 2 dual analog filter* (Stefan Konstantopoulos, 2025). The reviewer spoke with Herman Gillis.
- **[DS]** Linear Technology LTC1060 datasheet.
- The Filterbank 2 manual and the VCF-4 / Shermanik notes are already covered in `SHERMAN_MANUAL_CHECK.md`.

## Model measurements
All measurements use model 01, 24 dB, Reference mode, 48 kHz.

**1. Self-oscillation.** A short click, then silence. Each cell is the RMS level 1.5–2 s later.

| fc | res 80 | res 90 | res 95 | res 100 |
|---|---|---|---|---|
| 100 Hz | −217 dB | −59 dB | **−10.9 dBFS** | **−3.5 dBFS** |
| 500 Hz – 8 kHz | −217 dB | −210 dB | **−10.9 dBFS** | **−3.5 dBFS** |

**2. THD**, 220 Hz sine, fc 1 kHz:

| input | Drive 0 res 0 / 85 | Drive 50 | Drive 100 |
|---|---|---|---|
| −18 dBFS | 0.7 % / 1.1 % | 3.9 % / 6.3 % | 12.9 % / 35 % |
| −6 dBFS | 2.8 % / 4.5 % | 11 % / 25 % | 19 % / 58 % |

**3. Harmonics** (res 60, −18 dBFS). On white noise, the output level changes by −3.4 dB at ÷2, −7.5 dB at ÷4 and −13 dB at ÷16. On pink noise (closer to music): −0.5 / −1.6 / −1.8 dB at fc 1 kHz, and −0.5 / −1.2 / −2.2 dB at fc 4 kHz.

## Comparison

| Reported behaviour | Source | Model | Verdict |
|---|---|---|---|
| The filter **refuses to fully self-oscillate**. Its whistles stay in the upper kHz range, with a slight instability at maximum resonance. | SOS97 (FB1) | sustains at all cutoffs from res 95; −3.5 dBFS at res 100, down to 100 Hz | **Contradicts** |
| Resonance goes up to **partial** self-oscillation. Filter 2's range is wider than on FB1. | TAPE, SOS01 | full, steady self-oscillation | **Contradicts** (FB2 goes further than FB1, but no source says it fully self-oscillates) |
| A clean input stays clean and slightly warm, even at high resonance, with input at or below noon | SOS19 | Drive 0: 0.7–1.1 % at −18 dBFS, 3–4.5 % at −6 dBFS | **Partly**. It is warm, but heavier than "clean" at hot levels. |
| Past noon, heavy saturation: the filters fight for headroom and unstable resonances fold in | SOS19, SOS01, SOS97 | Drive 50–100: 4–59 % THD, and drive pushes the resonance down | **Conforms** |
| Overdrive buries the resonance; Limit restores it ("breathing room") | manual, FB2x2 spec | +12.1 → +19.5 dB peak with Limit | **Conforms** |
| Limit suppresses the harsher self-oscillation artefacts under heavy overdrive | SOS01 | not specifically modelled | **Unclear**. This may be the same effect seen from the other side. |
| Each filter is an **LTC1060 switched-capacitor** chip; clock leakage is much of the character, stronger at some settings | TAPE (reviewer, not the maker) | Clock option, at 100:1 | **Supports the clock option.** The LTC1060 runs at 50:1 or 100:1 [DS], so our 100:1 is one of the two real ratios. 50:1 is equally possible. |
| Not especially warm; grainy upper range; "lo-fi, dimensional" | SOS97, TAPE | grain only with the clock on | **Supports the clock option** |
| Engaging Harmonics **raises** the output volume, adds artefacts and makes the frequency knobs unstable | TAPE | slightly quieter: −0.5 to −2 dB on pink noise, −3 to −13 dB on white | **Contradicts mildly** (the direction is wrong; the size is small on music-like input) |
| Harmonics positions add lower content, down to 4 octaves below at ÷16 | SOS97 | ÷16 = 4 octaves | **Conforms** |
| A transpose switch shifts the filter range up an octave or a fifth; the fifth sounds "dirty" | SOS01 | absent | **Missing** |
| Without an input, newer units (serial > 7786) generate their own noise, shaped by the filters | SOS19, TAPE | absent | **Missing** |
| Continuous serial ↔ parallel; Output 1 carries filter 1; the Main Out sums both, and using both outputs lowers distortion | SOS97, TAPE | series only | **Missing** (known) |
| Cutoff modulated by the input itself (FM) | SOS01, TAPE | absent | **Missing** |

## What it means
1. **Self-oscillation is the clearest mismatch.** Every source puts the unit short of full, steady self-oscillation. The model reaches a steady −3.5 dBFS sine at any cutoff. A model that only **rings without sustaining** (decaying after excitation, with a slight instability at maximum) would fit better.
2. **Harmonics level.** Owners hear it as louder. The model gets slightly quieter (about −1 to −2 dB on pink noise). A second resonant peak lower down, where music carries more energy, would plausibly make the real unit louder. Our filter 2 sits after filter 1 in series, so filter 1 also attenuates filter 2's peak. This is a small gap.
3. **Clean headroom.** At Drive 0, hot inputs already give 3–4.5 % THD. The reviews suggest clean operation up to the detent.
4. **The clock is the character, per Tape Op.** That argues for the clock option. Whether it should be on by default is your call.

None of this is a measurement of a real unit. A recording session would settle the self-oscillation, headroom and harmonics-level questions.

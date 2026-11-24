# Band-pass engine (v1.2)

A third, independent filter engine. You choose **Model** (the analogue character) and **Architecture** (the filter topology) separately, so any of the five characters can run in any of the three structures. The capability matrix below shows which combinations correspond to real hardware.

The existing LPF and HPF engines are untouched. With the BPF off, the device's output is bit-identical to v1.1, and every v1.1 parameter, automation lane and MIDI mapping is preserved (VALIDATION.md, *Regression gates*).

## Controls

| Control | Range | Default | What it does |
|---|---|---|---|
| ON | off / on | **off** | 10 ms fade. Off by default, so existing Sets sound unchanged. |
| Model | 5 | 01 Oberheim SEM | Analogue character (see below). About 25 ms crossfade on change. |
| Architecture | SVF / CASC / MULTI | SVF | Filter topology. About 25 ms crossfade on change. |
| CENTRE (large knob) | 30 Hz – 12 kHz | 1 kHz | Centre frequency. Log-domain smoothing (6 ms). |
| BW | 0.2 – 6 oct | 2 oct | Passband width (see the per-architecture meaning below). |
| Q | 0.5 – 10 | 0.707 | Sharpness (see the per-architecture meaning below). |
| RES | 0 – 100 % | 0 % | Resonance at the centre. Self-oscillates near 100 %, except SEM. |
| DRIVE | 0 – 100 % | 0 % | Level into the model's nonlinear elements (0.25×–8×). |
| COMP | 0 – 100 % | 100 % | 100 % = centre gain normalised to unity, plus loudness-matched drive. 0 % = the raw structure gain. |
| MIX | 0 – 100 % | 100 % | Dry/BPF blend. For example, keep 30 % of the band over the full signal. |
| POSITION | POST / PRE | POST | BPF after the LPF/HPF chain, or before it. 8 ms dip on change. |

What BW and Q control depends on the architecture. The info line under POSITION shows it for the current choice.

| Architecture | BW | Q | RES |
|---|---|---|---|
| **SVF** | not used: a 2-pole band-pass has one width parameter, and that is Q | band width: −3 dB width = 2·asinh(1/2Q)/ln 2 octaves (Q 0.707 → 1.9 oct, Q 5 → 0.28 oct) | regeneration at the centre |
| **CASCADE** | spacing of the HP and LP edges (−3 dB width tracks BW from about 1.5 oct up) | peaking at each edge | regeneration at the centre |
| **MULTIMODE** | pole-mix order: ≤ 1 oct = 4-pole mix (narrow, 12 dB/oct skirts), ≥ 3 oct = 2-pole mix (wide, 6 dB/oct skirts) | not used: the ladder stages are one-pole | the ladder's own global feedback k |

## Architectures

All three are zero-delay-feedback (TPT) structures. At small signal levels each one is exactly the analogue transfer function below (verified to within 0.06 dB for all 15 configurations), so they differ in **response**, not only in colour.

**SVF: 2-pole state-variable band-pass.**
H = (s/Q) / (s² + s/Q + 1), normalised to 0 dB at the centre. 6 dB/oct skirts, one width parameter. Resonance is positive feedback of the normalised band output through the model's saturator: H/(1 − r·H). It peaks exactly at the centre and self-oscillates as r → 1.

**CASCADE: 2-pole HP into 2-pole LP.**
H = HP₂(f_c·2^(−BW/2), Q) · LP₂(f_c·2^(+BW/2), Q), normalised at the centre. 12 dB/oct skirts, a flat top for wide bands (the "telephone" band) and twin edge peaks with high Q. Resonance uses the same centre regeneration as SVF; the HP·LP phase is zero at the geometric centre, so the peak lands there.

**MULTIMODE: 4-pole ladder core with pole-mixed band-pass.**
A one-pole ×4 ladder with global feedback u = x − k·y₄. The band-pass comes from mixing the stage taps, as on Xpander-style multimode ladders:
- BP₄ = 4(y₂ − 2y₃ + y₄) = 4s²/((1+s)⁴ + k)
- BP₂ = 2(y₁ − y₂) = 2s(1+s)²/((1+s)⁴ + k)

Resonance is the ladder's own feedback: a single core, with all four stages saturating together. The feedback shifts the band centre (to 0.90 ω around k = 1.4), so the stage tuning is corrected with a 5th-order fit of the analytic band centre (error 0.2 %).

## Models: what is taken from each circuit

The model sets three things:
1. the nonlinear element inside every integrator or stage (secant-linearised, as in the LPF/HPF engines)
2. the resonance saturator and how far resonance may go
3. documented model-specific traits

**Native** means the architecture matches how the original hardware produces its band-pass response.

| Model | Element (source) | Resonance limit | Native architecture | Notes |
|---|---|---|---|---|
| **Oberheim SEM** | **v1.6, SVF:** the LPF engine's SEM-1A core (linear input, RES-pot law, D11/D12 damping limiter, rails), band-pass node. Other architectures: OTA tanh element (derived). | circuit law, Q ≤ 10 → **never self-oscillates** | **SVF**: the SEM selects a band-pass mode with a dedicated switch, taking the SVF's band-pass output | Resonance follows the SEM-1A law; the Q knob sets a floor. |
| **Steiner-Parker** | **v1.6, SVF:** the LPF engine's Synthacon core (Steiner 1974: sinh diode strings, amplifier limit) with the input at the band-pass injection point. Other architectures: tanh element (derived). | **hard-knee amplifier clip** (the non-inverting gain stage clips), self-oscillates | **SVF (native response)**: Steiner's BP is the BP injection of its Sallen-Key network, K·s/(s²+(3−K)s+1). That is the same 2-pole band-pass with positive-feedback resonance, so the SVF architecture reproduces its response, though not its component topology. | The brief described it as a state-variable filter; the circuit is Sallen-Key. Aggressive, with clipped resonance. |
| **Korg 35 / MS-20** | transconductor stages, difference-type tanh | tanh (diode-limited feedback), self-oscillates | **CASCADE**: the MS-20 runs its HPF into its LPF in series, which gives its band-pass | **v1.6:** the HP section is 1-pole (6 dB/oct), as in Stinchcombe's MS-20 study and the LPF/HPF engine, so the low skirt is 6 dB/oct and the high skirt 12 dB/oct. |
| **ARP 2600** | **v1.6, MULTIMODE:** the LPF engine's 4012 core (LPF 07: ARP input stage, Moog-type ladder, Board 3 resonance law), band-pass taken as a pole mix (4-pole BP 4·(y2 − 2y3 + y4), blended toward the 2-pole 2·(y1 − y2) by Bandwidth). Other architectures: separate-type tanh element (derived). | Board 3 law (k = 4 at ~69 % resonance), self-oscillates; the derived pole mix is limited to the module's own oscillation level (+1.6 dBFS) | **None**: the 2600's VCF is the 4012 4-pole low-pass, with no band-pass. Every 2600 configuration is **derived**; MULTIMODE (the real 4012 core) is the closest. | **v1.6:** the 4072 HF roll-off was removed: the documented 2600 (service manual) carries the 4012. |
| **EMS VCS3** | diode-rung stages, difference-type tanh of the voltage across each rung (Civolani–Fontana VCS3 model) | tanh, self-oscillates | **None**: the VCS3 filter is a diode-ladder low-pass that EMS called "low-pass/band-pass", because resonance pulls the low end down. It has no band-pass output. Every VCS3 configuration is **derived**; MULTIMODE (ladder core) is the closest. | |

### Approximations and limits (read before claiming "it sounds like a …")
- Element scales (how hard each element saturates for a given input level) are chosen per model for plausible headroom. They were not fitted to measurements.
- **ARP 2600 and EMS VCS3 have no native band-pass.** Their BPF entries put each instrument's documented nonlinear element into a band-pass structure, and the menu marks them "derived".
- In the MULTIMODE architecture the VCS3's diode rungs are applied to buffered stages. The real ladder's coupling between stages (modelled exactly in the LPF engine's TB-303) is not reproduced here.
- The SEM's continuous LP–notch–HP mode knob and its separate BP switch are not mirrored. The BPF uses the BP mode only.
- No configuration was compared against hardware recordings.

## Routing

POST (default): input → LPF/HPF chain (in either order) → **BPF** → output. Use it to carve a band out of the already-filtered signal.
PRE: input → **BPF** → LPF/HPF chain → output. Use it to feed the band into the LPF/HPF performance filters.
MIX blends the BPF output with its own input at whichever position it sits.

## Sources
- Tim Stinchcombe, *Analysis of the Moog Transistor Ladder and Derivative Filters* (EMS diode-ladder configuration and transfer function)
- Sound On Sound, *All About EMS*: VCS3 filter as combined low-pass/band-pass
- AMSynths "Snow Fall" notes, quoting EMS's 1970 VCS3 filter description (band-pass response at medium resonance)
- Civolani & Fontana, VCS3 diode-ladder model (via the 2025 reduced-model paper on the HISE forum)
- till.com ARP module index (4012 = 4-pole low-pass transistor ladder); 4072 roll-off reports (modulargrid forum); ARP 2600 manual (24 dB/oct low-pass VCF)
- Cherry Audio PS-20 manual, greatsynthesizers MS-20 review, Wikipedia (MS-20: HPF and LPF in series)
- W. Pirkle, *Modeling the Korg35 Lowpass and Highpass Filters*, AES 135 (2013)
- GForce OB-E manual (SEM-style band-pass switch)
- CGS35 / Synth DIY wiki (Steiner-Parker: Sallen-Key, BP by injection)
- V. Zavalishin, *The Art of VA Filter Design* (TPT/ZDF; pole-mixing)

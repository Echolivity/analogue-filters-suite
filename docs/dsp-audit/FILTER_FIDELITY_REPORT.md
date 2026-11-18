# Filter fidelity report

All numbers come from `source/tests/audit/audit_filters.py`, which runs the shipped engine. Raw data: `data/filters.json`. Plots: `plots/f*.png`.

**Conditions** unless stated otherwise:
- 48 kHz, 32-bit float I/O, oversampling 1× (the device default)
- Comp 0, so no make-up gain alters the circuit response
- Small-signal transfer functions from white-noise cross-spectra at about −74 dBFS

Labels used throughout: **[measured]** is a measurement of this engine; **[analytic]** is derived from the source equations; **[reference]** comes from the literature.

## 1. Topology verdicts

| Model | Claimed reference | Topology in code | Verdict |
|---|---|---|---|
| Ladder LP | Moog transistor ladder | 4 one-pole stages, each with a tanh pair; global feedback through the input pair (Huovilainen) | **Genuine ladder model.** Not a generic 4th-order LP: the stage saturation sits inside each pole. |
| Ladder HP | (labelled ALT) | Binomial pole mix of the ladder taps | **Not a Moog circuit.** Labelled honestly. |
| K35 LP/HP | Korg 35 / MS-20 Mk1 | Sallen-Key with resonance loop (Pirkle); loop clip; secant-limited K | **Mk1 at block level.** Mk2 (LM13600) not modelled. HP order (2-pole) unverified against Stinchcombe. |
| Steiner LP/HP | Steiner-Parker Synthacon | Sallen-Key with two VCR elements; Q from amplifier gain; three injection points | **Topology correct for LP.** Diode-string law and HP node are approximations. Mirrored branch absent. |
| SEM LP/HP | Oberheim SEM | 2-integrator SVF with OTA input tanh | **Correct topology.** Simultaneous LP/BP/HP are available inside the code, but only LP- or HP-to-notch is exposed. |
| TB-303 | TB-303 diode ladder | Stinchcombe 303 configuration with feedback HPF | **Correct topology and coefficients.** |
| Sherman | Sherman Filterbank | Two nonlinear SVFs in series, input overdrive, invented feedback | **Unverifiable:** no schematic. |

## 2. Frequency domain [measured]

### 2.1 Low and mid cutoffs

At fc ≤ 1 kHz, the engine matches each model's *analogue* transfer function H(s) at s = j·f/fc, i.e. with **no** bilinear warping. The comparison band is wherever the analogue response is above −30 dB, up to 20 kHz.

| Model (LP, res 60 %) | 44.1 kHz, 1× | 44.1 kHz, 2× | 96 kHz, 1× |
|---|---|---|---|
| Ladder | 0.18 dB | 0.06 dB | 0.11 dB |
| K35 | 0.95 dB | 0.23 dB | 0.20 dB |
| Steiner | 2.06 dB | 0.48 dB | 0.41 dB |
| SEM | 0.97 dB | 0.24 dB | 0.20 dB |
| TB-303 | 0.14 dB | 0.05 dB | 0.08 dB |

At fc ≤ 1.5 kHz, all HPF models stay within 0.15 dB at 44.1 kHz.

### 2.2 High cutoffs: bilinear cramping

This is a fidelity limit of the integration method at 1×. The prewarped bilinear transform is exact at fc, but it maps Nyquist to infinity. Above fc, the response falls into a zero at Nyquist, so the top octave is darker than the analogue circuit.

| LP, res 60 %, 44.1 kHz, 1× | Worst error, 10–20 kHz | Resonance-peak frequency error |
|---|---|---|
| Ladder, fc 5 kHz | 5.6 dB | +22 cents |
| Ladder, fc 12 kHz | **37.6 dB** | **+119 cents** |
| K35, fc 12 kHz | 22.6 dB | +119 cents |
| Steiner, fc 12 kHz | 22.2 dB | **+167 cents** |
| SEM, fc 12 kHz | 24.1 dB | +19 cents |
| TB-303, fc 12 kHz | 32.3 dB | n/a |

TB-303: the analogue maximum is in the passband, so a peak-frequency error is not defined.

With 2× oversampling these errors fall to 2.4–3.7 dB, and at 96 kHz 1× to 2–3 dB. See `plots/f1_digital_vs_analogue_hf.png`.

**Phase.**
- At 1×, the phase follows the analogue model to within a few degrees below fc.
- At 2×, the half-band IIR adds a large frequency-dependent phase shift (non-linear phase, no latency). In the plot that appears as the extra phase in the 2× curve. This is a property of the oversampler, not of the circuit model.

**Audibility.** The losses are in the top octave and above. They matter for bright, open settings with resonance at high cutoffs. They are inaudible for typical dub sweeps below about 4 kHz.

### 2.3 Cutoff accuracy and sample-rate consistency

- Small-signal response at fc 1 kHz, res 60 %, compared at 44.1, 48 and 96 kHz: the maximum deviation is **0.07–0.58 dB** wherever the response is within 30 dB of its peak (F8). The cutoff is sample-rate-independent to the accuracy of the warping.
- Resonance knob vs peak height and frequency (F2, `plots/f2_resonance_peak.png`, fc 1 kHz):

  | Model | At res 90 % | At res 100 % |
  |---|---|---|
  | Sherman | +42 dB | ~+89 dB (self-oscillating) |
  | K35 | +17 dB | ~+94 dB (self-oscillating) |
  | Ladder | +28 dB | ~+104 dB (self-oscillating) |
  | Steiner | +15 dB | ~+90 dB (self-oscillating) |
  | TB-303 | +29 dB | ~+112 dB (self-oscillating) |
  | **SEM** | +17 dB | **+19.9 dB**: never self-oscillates, by design |

- The resonance peak moves from about 0.2·fc toward fc as resonance rises, as these topologies predict.

### 2.4 Slopes (F7, measured)

Measured between 4·fc and 8·fc for LP, and between fc/4 and fc/2 for HP:

| Setting | LP models (except TB-303) | HP models (except Steiner) |
|---|---|---|
| 12 dB | 12.9–13.2 dB/oct | 10.4–11.4 dB/oct |
| 24 dB | 25.8–26.3 | 21–22.4 |
| 36 dB | 39.1–39.6 | 33–34 |
| 48 dB | 52.7–53.0 | 45–46 |

The asymptotic slopes are correct. The HP figures are measured close to the corner, so they sit below the nominal values.

Exceptions:
- **TB-303:** 9.8 dB/oct at 4–8·fc for both 12 and 24. The 303 ladder's poles are widely spread (Stinchcombe), and there is no native 12 dB mode, so both settings give the same response. 36 and 48 add 13 dB/oct each. **This matches the circuit analysis**, so the "24 dB" label describes the order, not the measured skirt.
- **Steiner HP:** **4.8 dB/oct** at the "12 dB" setting. The model's HP injection relaxes to 6 dB/oct below cutoff. This is consistent with the inferred node but **contradicts the "12 dB" label**, and whether the hardware does the same is unverified.

## 3. Nonlinear behaviour [measured]

### 3.1 Is the nonlinearity inside the filter?

**Yes**, for every model. With Drive 0 (input gain −12 dB), THD rises with input level, and it changes with resonance (F4, `plots/f4_thd_vs_level.png`, 110 Hz sine, fc 2 kHz).

| Model | THD at −20 dBFS | THD at 0 dBFS | H2 at 0 dBFS | Comment |
|---|---|---|---|---|
| Sherman | 0.66 % | 6.3 % | −24 dBc | Asymmetric input stage |
| K35 | 0.007 % | 0.69 % | **< −170 dBc** | Perfectly symmetric |
| Ladder | 0.007 % | 0.66 % | < −170 dBc | Perfectly symmetric |
| Steiner | 0.004 % | 0.40 % (res 80 %: 2.5 %) | < −170 dBc | Resonance raises distortion, as expected |
| SEM | 0.001 % | 0.13 % | < −170 dBc | Cleanest |
| TB-303 | 0.005 % | 0.51 % | −135 dBc at res 80 % | Effectively symmetric |

**Finding: no even harmonics** in five of the six models. The cause is the ideal symmetry of every tanh element.
- Real circuits produce some H2 through device mismatch, offsets and asymmetric diode conduction. Examples: MS-20 diode drops, the Steiner bias network, ladder transistor mismatch.
- How much H2 they produce is **not established here**. No hardware measurement exists, so this is a *missing-characteristic* finding, not a measured mismatch.

### 3.2 Resonance compression with level (F4b)

Gain at fc with res 80 %, comparing a −40 dBFS input with −12 dBFS:

| Model | Peak reduction at −12 dBFS |
|---|---|
| Sherman | 12.4 dB |
| Ladder | 2.0 dB |
| Steiner | 1.2 dB |
| K35 | 0.8 dB |
| SEM | 0.2 dB |
| TB-303 | 0.2 dB |

This is the expected qualitative behaviour: the resonance tames as level rises. The strength is model-specific, and it is not validated against hardware.

### 3.3 Aliasing (F5)

Test: 5003 Hz sine at −6 dBFS, fc 16 kHz, res 50 %, Drive 60 %, 48 kHz. "Aliased" means power that does not fall on a harmonic of 5003 Hz. The measurement floor is −149 dBc.

| Model | 1× (default) | 2× |
|---|---|---|
| Steiner | **−25 dBc** | −74 dBc |
| Sherman | **−39 dBc** | −88 dBc |
| K35 | −50 dBc | −116 dBc |
| Ladder | −65 dBc | −126 dBc |
| TB-303 | −68 dBc | −137 dBc |
| SEM | −89 dBc | −146 dBc |

At the default 1×, Steiner and Sherman produce clearly audible inharmonic products on bright, driven material. The 2× option removes most of them, but it is **off by default**. See `plots/f5_alias_spectrum_ladder.png`.

### 3.4 DC offset

The output stage removes DC with a 2 Hz blocker (build_genexpr.py:730). The Sherman input stage idles at a removed operating point, so no offset is created. **No DC problem** reaches the output, but DC behaviour inside the circuit (bias shifts) is not modelled.

## 4. Filter-specific behaviour [measured]

### 4.1 Self-oscillation (F3)

Resonance 100 %, excited by a 10 ms noise burst after the controls have settled.

**No self-start from silence.** The engine has no internal noise. An exactly silent filter at 100 % resonance stays silent until it receives input, whereas an analogue filter starts from thermal noise. When the excitation arrived during the 15 ms control glide, several models stayed silent. This is an initial-condition effect, not missing gain.

**Pitch vs cutoff:**

| Model | fc 100 Hz / 1 kHz | Higher fc |
|---|---|---|
| K35 | ±1 cent | +2 cents at 8 kHz |
| Sherman | −1 / +10 cents | +45 cents at 4 kHz, +58 cents at 8 kHz |
| Steiner | −7 / 0 cents | +22 cents at 4 kHz, +32 cents at 8 kHz |
| Ladder | −27 / −17 cents | about +2 to +9 cents at 4–8 kHz |
| TB-303 | +50 / −60 cents | −42 to −65 cents across 4–8 kHz |

The TB-303 detuning is a property of its cutoff mapping (`p_g` divisor, :337), not tracking error. SEM: no oscillation, by design.

**Level.** Sustained oscillation runs from about −13 dBFS (ladder, 303) to +4.5 dBFS (Steiner). That is before the soft clip, which is disabled in these tests.

### 4.2 Stability: critical finding

At **1× oversampling, 48 kHz, fc 12 kHz, resonance 100 %**:

| Model | Result |
|---|---|
| Sherman | **Diverges to +249 dBFS**: numerically unbounded |
| Steiner | Grows to **+30 dBFS** |
| Both models, at 2× | Bounded (+1.3 and +6.3 dBFS) |
| Both models, at 16 kHz | Bounded |

**Cause:** the one-sample-lagged secant linearisation, when g = tan(π·fc/fs) is large and the loop gain is above 1. In the device, the soft clip bounds what is heard to ±1 and the NaN guard catches the worst case. The internal state still diverges, and the result is a broken, full-scale tone.

**Rapid modulation (F6).** Cutoff stepped between 100 Hz and 12 kHz (LP) or 20 Hz and 2 kHz (HP) every 10 ms, with resonance 100 %, Drive 100 % and 48 dB slope:
- All 22 model/oversampling combinations stayed finite.
- Peak excursions: up to **+22 dBFS** (Ladder HP), +20 dBFS (Steiner HP 1×), +11 dBFS (SEM).

These are transient overshoots from abrupt coefficient changes. The device's 6 ms cutoff smoothing reduces them in normal use.

### 4.3 Parameter smoothing

All controls are smoothed per sample:
- cutoff in the log domain, 6 ms
- other controls, 15 ms
- model, slope and order changes crossfade over 25 ms or duck over 4 ms

Existing click tests pass (`tests/validate.py` `t_clicks`). There is no zipper noise. No audio-rate cutoff modulation input exists, so FM behaviour, where analogue filters differ greatly, is untested and unavailable.

## 5. Band-pass engine (B1)

Test: centre 1 kHz, BW 1 oct, Q 2, res 0.

| Architecture | Peak | −3 dB width | Matches |
|---|---|---|---|
| SVF | 1002 Hz | 0.70 oct | Q = 2 |
| CASCADE | 1260 Hz | 1.32 oct | Edges at fc·2^±0.5. The band is flat-topped with humps at the edges (edge Q 2), so the maximum falls at an edge, not the centre. |
| MULTIMODE | 943 Hz | 1.73 oct | Pole-mix BP; peak 6 % low at this bandwidth |
| ARP 2600, CASCADE | 820 Hz | 1.32 oct | Same band. The 14 kHz roll-off tilts it slightly, so the maximum moves to the lower hump. |

- **The profiles are almost identical at small signal.** At res 0, all five profiles give identical centre, width and gain within 0.02 dB. They differ only in their nonlinear constants.
- **Consequence.** The five "models" are timbral variants of three structures, **not five circuit models**. This is consistent with `docs/BPF.md`, which labels ARP and EMS as "derived".

## 6. Findings ranked by significance

1. **Instability at 1×, high fc, 100 % resonance** (Sherman, Steiner). This is a correctness problem.
2. **Strong aliasing at the 1× default** for Steiner and Sherman. Moderate for K35.
3. **Bilinear cramping and resonance-peak shift** above about 5 kHz at 1× and 44.1/48 kHz.
4. **No even-order harmonics** in five models (idealised symmetry).
5. **No self-start or noise floor**; no audio-rate FM input.
6. **Steiner HP skirt is 6 dB/oct**, against its "12 dB" label (unverified against hardware).
7. **The BPF "models" share structures**; they are not separate circuits.
8. **Revision coverage:** K35 Mk2 (LM13600) is absent, and the MS-20 study was not consulted.

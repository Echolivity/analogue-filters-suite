# Filter models: circuits, capability matrix and sources

*This file covers the LPF and HPF engines. The v1.2 band-pass engine and its five models are documented in [BPF.md](BPF.md).*

Each model is a separate DSP implementation derived from the published circuit, or circuit analysis, of the instrument it is named after. For each model this file gives three things:

1. **The circuit facts the model is built on**, with sources.
2. **What is modelled exactly:** the linear transfer function. Every model's small-signal response matches its circuit's analogue transfer function to within 0.05 dB (VALIDATION.md, *Circuit reference*).
3. **What is approximated, and what is not modelled.**

How much I could establish varies by circuit. The TB-303 and Moog ladder are thoroughly analysed in the literature. The Korg 35, SEM and Steiner-Parker are established at topology level. The Sherman Filterbank has no public schematic. None of the models has been compared against recordings of the real hardware, so no claim of hardware equivalence is made.

## Capability matrix

| # | Model | Circuit basis | Topology supports | LPF stage | HPF stage | Native slope | Taps | Self-osc. | CHARACTER |
|---|---|---|---|---|---|---|---|---|---|
| 01 | Sherman Filterbank-inspired | **Behavioural** (no public schematic) | LP, BP, notch, HP (per the maker's spec) | LP | HP | 24 (filters 1+2) | 12 = filter 2 alone | yes | FEEDBACK |
| 02 | Korg 35 (MS-20 Mk1)-inspired | Korg 35 Sallen-Key LP and HP | LP, HP | LP | HP | 12 | 12 | yes | FB CLIP |
| 03 | Moog transistor ladder-inspired | 4 differential-pair stages + global feedback | LP (HP/BP only by pole mixing) | LP | **ALT** pole-mix HP | 24 | 12 / 24 | yes | STAGE SAT |
| 04 | Steiner-Parker Synthacon-inspired | Sallen-Key, diode-string resistors, 3 injection points | LP, BP, HP | LP (+BP) | HP injection (+BP) | 12 (HP: see note) | 12 | yes | BP BLEND |
| 05 | Oberheim SEM-inspired | OTA state-variable filter | LP, BP, notch, HP | LP→notch | HP→notch | 12 | 12 | no | NOTCH MORPH |
| 06 | Roland TB-303-inspired | Diode ladder, TB-303 configuration | LP | LP | **not offered** | 24 | 24 only | yes | SQUELCH |

Rules: no silent substitution (the HPF menu has five entries), the one alternative is labelled ALT in the menu itself, and slopes beyond a model's native response come from linear Butterworth-Q extension sections, which the slope info line marks as `EXT`.

---

## 01 Sherman Filterbank-inspired (behavioural)

**What is published.** Sherman has not released a schematic. The manufacturer's and retailers' descriptions establish the following:
- two independent multimode filters, continuously adjustable between low-pass, band-pass, notch and high-pass
- serial or parallel routing; in series with both filters tuned identically, they act as a combined 24 dB/oct filter
- filter 2 has more resonance than filter 1
- an input section with level, overdrive and high boost/cut

**The model.** Asymmetric input overdrive, then filter 1 (a nonlinear SVF with mild resonance, Q ≤ 1.7), then filter 2 (a nonlinear SVF carrying the main resonance up to self-oscillation), both at the same cutoff. The 12 dB setting plays filter 2 alone, so resonance stays available. CHARACTER (FEEDBACK) adds a saturated output→input feedback path for the Filterbank's howl. That path is **not** taken from documentation; it is a design choice requested in the spec. Resonance is limited with secant-linearised sigmoids inside the zero-delay solves.

**Not modelled.** Harmonic coupling of filter 2, parallel mode, continuous mode morphing, the envelopes, LFO, ring modulator and pitch tracking.

## 02 Korg 35 (MS-20 Mk1)-inspired

**Circuit.**
- The MS-10 and early MS-20 used Korg's proprietary KORG35 thick-film IC filter, which was later replaced by an LM13600 OTA design.
- The Korg 35 is a voltage-controlled Sallen-Key topology that can produce both low-pass and high-pass responses.
- Its Q is set by a delay-less positive feedback loop, with the saturation circuit inside that loop.
- MS-20-style filters put diodes in the resonance path, which keeps them from clipping when they self-oscillate.

**The model (unchanged in this revision; it already followed this structure).**
- LP: LP1 → Σ → LP2, with K·y fed back through HP1 into Σ. H = 1/(s² + (2−K)s + 1), self-oscillating at K = 2.
- HP: the mirrored HP1 → Σ → HP2 with an LP1 feedback path. H = s²/(s² + (2−K)s + 1).

Both use a zero-delay-feedback solve with a saturator in the loop. The feedback gain is limited by the diode characteristic (secant of tanh), and CHARACTER (FB CLIP) sets the clipping level. **Approximation:** the Korg 35 IC's internal transistor-level behaviour, including its "overdrive at the cost of bass" character, is represented by the loop saturator rather than by transistor equations.

## 03 Moog transistor ladder-inspired, revised

**Circuit.** Four stages, each a transistor differential pair acting as a nonlinear impedance with a tanh-like characteristic, loaded by a capacitor. Huovilainen's analysis (DAFx-04) gives each stage as dyᵢ/dt = ω(tanh(yᵢ₋₁) − tanh(yᵢ)), driven by the input pair tanh(x − k·y₄). The linear transfer function is 1/((1+s)⁴ + k) (Stilson & Smith 1996; Stinchcombe 2008), self-oscillating at k = 4.

**The model.** Exactly those per-stage equations, with every tanh present: the input pair and all four stage pairs. The previous version had only an input tanh. They are solved with zero-delay feedback: each tanh is replaced by its secant gain tanh(v)/v at the previous sample, so the four stages are linear for the current sample and the global loop is solved in closed form. CHARACTER (STAGE SAT) runs from circuit-nominal (0 %) to 3× hotter stage saturation (100 %). Comp restores the 1/(1+k) bass loss that the circuit shows (visible in the circuit-reference plot at Comp 0). **Approximation:** the secant method lags the nonlinearity by one sample. This is standard practice and well behaved, but not an exact solve of the nonlinear ODE.

## 04 Steiner-Parker Synthacon-inspired, rebuilt

**Circuit.** The Steiner-Parker is a classic Sallen-Key filter adapted with biased diodes as controlled resistors. The diode strings act as voltage-controlled resistors, and the filter's Q comes from the gain of a non-inverting amplifier, staying almost constant as the filter is swept. The HP, BP and LP modes come from injecting the signal at three different points of the circuit, and all inputs can be driven at once. Resonance gain grows with Q, so clipping can occur.

**The model.** A Sallen-Key network (R1, R2 = diode strings; C1 to the amplifier's feedback node; C2 to the HP injection terminal) with amplifier gain K. Linear responses:
- LP injection (into R1): K/(s² + (3−K)s + 1)
- BP injection (at the feedback node): K·s/(s² + (3−K)s + 1)
- HP injection (into C2): K·s(s+2)/(s² + (3−K)s + 1)

It self-oscillates at K = 3. The model solves the two capacitor states with a 2×2 zero-delay trapezoidal system each sample. Diode-string currents saturate (tanh secant of the voltage across each string), and the amplifier clips (hard-knee secant on K). CHARACTER (BP BLEND) moves the input from the LP (or HP) injection point to the BP point, as the original's multiple inputs allow. Comp divides out the amplifier gain K, which otherwise raises the passband by up to +9.5 dB.

**Uncertain, so flagged:** I could not access Steiner's 1974 article, so the exact injection node for HP is inferred from standard Sallen-Key analysis. With injection at C2 the HP response is resonant near the cutoff but relaxes to **6 dB/oct well below it**. Use the slope selector (24–48) when you need a steep bass cut. If the original circuit injects HP elsewhere, its skirt may be steeper.

## 05 Oberheim SEM-inspired, revised

**Circuit.** A 2-pole state-variable filter whose integrators are CA3080 OTAs. An OTA's output current follows gm·tanh(v_in/2V_T), so each integrator's input saturates. The resonance pot sets the damping, and the mode control mixes LP and HP (notch in the middle).

**The model.** A zero-delay SVF with each integrator's gain replaced by its OTA secant gain, using tanh on that integrator's input from the previous sample. The previous version used a linear SVF with an ad-hoc limiter. Damping never reaches zero (Q ≤ 10), so the model does not self-oscillate. SEM clones are reported to oscillate raspily in some builds, so this is a conservative choice. CHARACTER (NOTCH MORPH) is the mode knob.

## 06 Roland TB-303-inspired, rebuilt on Stinchcombe's analysis

**Circuit.**
- The TB-303 filter is a diode ladder built from transistors connected as diodes.
- Stinchcombe identifies the TB-303 configuration as one diode at the top of the ladder with the bottom capacitor halved.
- His derived transfer function is H(s) = 1/(s⁴ + 6.727s³ + 14.142s² + 9.514s + 1 + k).
- Measurements on a x0xb0x found the 303 filter matches its theoretical model closely, except for a high-pass filter in the resonance feedback loop.
- The resonance feedback goes to the transistor that drives current through the ladder, which adds amplitude-modulation-like distortion.

**The model.** A current-driven 4-node RC ladder with the bottom capacitor C/2 and one diode rung to ground at the top:

  0.5·v₁' = u − (v₁−v₂) · v₂' = (v₁−v₂) − (v₂−v₃) · v₃' = (v₂−v₃) − (v₃−v₄) · v₄' = (v₃−v₄) − v₄

Its characteristic polynomial reproduces Stinchcombe's coefficients exactly. It self-oscillates at k = 17, at ω = √2 in these units, which is just above 1 in Stinchcombe's normalisation, as he describes.

The ladder is solved each sample as a tridiagonal zero-delay system. Feedback drives the input pair through a one-pole highpass, and CHARACTER (SQUELCH) moves that highpass from 8 Hz to about 300 Hz. Nonlinear parts: the input pair (tanh), and every diode rung, whose conductance follows the tanh secant of its own voltage.

The previous version used an equal-capacitor, resistively driven ladder. That corresponds to Stinchcombe's *standard* one-diode case (also k = 18.4), not the 303.

**Usability calibration (documented, not circuit behaviour):** the coupled poles are widely spread, so at zero resonance the −3 dB point sits far below the ladder's natural frequency. The model re-tunes with resonance so that at zero resonance the −3 dB point lands on the cutoff knob, and near self-oscillation the resonant peak does. **Not modelled:** the 303's envelope and accent circuits, and the extra high-pass stages between the filter and the output VCA.

---

## Sources

- T. E. Stinchcombe, *Analysis of the Moog Transistor Ladder and Derivative Filters*, 2008, https://www.timstinchcombe.co.uk/synth/Moog_ladder_tf.pdf. Moog, standard diode, TB-303 and EMS transfer functions.
- T. E. Stinchcombe, *Filter pole animations*, https://www.timstinchcombe.co.uk/index.php?pge=poles
- T. E. Stinchcombe, *A study of the Korg MS10 & MS20 filters* (referenced; not accessed for this revision).
- A. Huovilainen, *Non-linear digital implementation of the Moog ladder filter*, DAFx-04, https://dafx.de/paper-archive/2004/P_061.PDF
- T. Stilson & J. Smith, *Analyzing the Moog VCF with considerations for digital implementation*, 1996 (via the references above).
- W. Pirkle, *Modeling the Korg35 Lowpass and Highpass Filters*, AES 135th Convention, paper 103, 2013, https://aes.org/publications/elibrary-page/?id=16938
- N. Steiner, *Voltage-tunable active filter features low, high and bandpass modes*, Electronic Design 25, 6 Dec 1974 (not accessible here; described in the CGS35 documentation and the Synth DIY wiki).
- K. Stone, CGS35 Synthacon VCF documentation, https://open4umodular.github.io/synthpanel/modules/cgs35_euro_vcf.html
- Synth DIY wiki, *Voltage controlled filter* talk page, https://sdiy.info/wiki/Special:MobileDiff/17306
- a1k0n, *303* (x0xb0x filter measurements), https://github.com/a1k0n/303
- Sherman Filterbank 2 descriptions: https://www.effectsdatabase.com/model/sherman/filterbank2, https://www.thomann.de/be/sherman_filterbank_2_rack.htm
- Korg MS-10 (KORG35 vs LM13600 history), Wikipedia mirror; KS-20 build notes, https://kassu2000.blogspot.com/2019/07/ks-20-filter.html
- V. Zavalishin, *The Art of VA Filter Design*, rev. 2.1.0 (TPT/ZDF method used throughout).

## Adding a model

Models are declared in one registry (`MODELS` in `source/src/build_genexpr.py`). The registry entry is the model interface:

| Required interface item | Where it lives |
|---|---|
| Initialisation / state reset | `states` list. The generator declares, loads, stores and zeroes them. |
| Sample-rate configuration | `coef` lines use `fso` and are evaluated every sample. |
| Parameter updates | `coef` lines read the smoothed stage controls. |
| Stereo processing | `call` lines are emitted per channel and per oversampled subsample. |
| Supported filter modes | `lp` / `hp` = `"native"`, `"alt"` or `None`. |
| Slope capability | `taps` = `"12"`, `"12/24"` or `"24"`. |
| Model-specific parameter metadata | `char` (label under the CHARACTER knob). |

Write one GenExpr function, add one registry entry, append the name to the menu and label lists in `source/device/build_device.py`, and add the circuit's transfer function to `t_circuit_reference` in `source/tests/validate.py`, so the new model is checked against its circuit like the others.

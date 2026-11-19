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
| 01 | Sherman Filterbank-inspired | **Behavioural** (no public schematic) | LP, BP, notch, HP (per the maker's spec) | LP | HP | 24 (filters 1+2) | 12 = filter 2 alone | partial (rings, no sustain; FEEDBACK can howl) | FEEDBACK |
| 02 | Korg 35 / MS-20 (K35 Circuit: OTA Mk2 or KORG-35 Mk1) | Mk2: two buffered one-poles (LM13600). Mk1: Korg35 Sallen-Key | LP, HP | LP | HP (6 dB/oct, as built) | LP 12, HP 6 | 12 | yes | Mk2: FB CLIP · Mk1: DIODE DRIVE |
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

**The model.** Asymmetric input overdrive, then filter 1 (a nonlinear SVF with mild resonance, Q ≤ 1.7), then filter 2 (a nonlinear SVF carrying the main resonance, up to Q ≈ 100 but not sustained self-oscillation), both at the same cutoff. The 12 dB setting plays filter 2 alone, so resonance stays available. CHARACTER (FEEDBACK) adds a saturated output→input feedback path for the Filterbank's howl. That path is **not** taken from documentation; it is a design choice requested in the spec. Resonance is limited with secant-linearised sigmoids inside the zero-delay solves.

**v1.6, from the Filterbank 2 manual** ([check](independent-review/SHERMAN_MANUAL_CHECK.md); still behavioural):
- **Modes:** STAGE/PANEL. PANEL engages the manual's Balance (Lp/Bp/Hp) and Correction (−Bp … −Bp + Lp + Hp) knobs, shared by both filters (the hardware has a pair per filter).
- **Harmonics:** filter 2 at f1 ÷ 1–16, at 24 dB.
- **Limit:** more resonance headroom when overdriven. The mechanism is invented.
- **Clock:** clocked (switched-capacitor) character: hold-between-ticks staircase at a 100 × cutoff clock, plus clock feedthrough. The ratio and level are assumptions.
- **Partial self-oscillation** (from published reviews, [evidence](independent-review/SHERMAN_FIELD_EVIDENCE.md)): filter 2's damping never goes negative. Below R 0.05 the v1.5 law bends onto a floor (Q ≈ 100 at res 100), so a click rings and dies, but a steady input still whistles. Half of the amplitude-dependent damping follows the band-pass power averaged over about 30 ms (a resonance limiter after Troyer's Reaktor reconstruction), so a loud resonance stays held back for a moment. FEEDBACK can still make it howl.

**Not modelled:** the continuous PAR ↔ SER routing (and parallel mode), separate Balance/Correction per filter, the envelopes, LFO, ring modulator and pitch tracking.

## 02 Korg 35 / MS-20

**Source (v1.6):** T. E. Stinchcombe, *A Study of the Korg MS10 & MS20 Filters* (2006), a SPICE circuit analysis of the MS-10 (Korg35) and KLM-307 (OTA) schematics. Full check: [MS20_STUDY_CHECK.md](independent-review/MS20_STUDY_CHECK.md).

**Two circuits share the name.** The **K35 Circuit** parameter selects between them for both the LPF and the HPF.

| | OTA (Mk2), the default and the v1.5 sound | KORG-35 (Mk1) |
|---|---|---|
| Used in | later MS-20s (daughterboard KLM-307) | MS-10 and early MS-20s |
| Core | two buffered one-pole OTA stages | Sallen-Key, C1 = 3·C2 |
| Low-pass | 1/(s² + (2 − K)s + 1) | 1/(s² + (7/3 − k)s + 1), with R1 = R2/3 (the study's assumption) |
| High-pass | s(s + 1)/(s² + (2 − K)s + 1) | s(s + 4/3)/(…) |
| Clipping diodes | in the resonance feedback, so only frequencies near cutoff are affected | in the forward path (the X1 stage, ×58, with 1N4148s across 270 kΩ), so loud signals distort at every frequency |
| CHARACTER | sets the feedback clip level (FB CLIP) | drives the diode stage, 0 to +24 dB above the reference |
| Reference oversampling | 2x | 8x (LPF), 4x (HPF) |

**High-pass (v1.6).** Both real high-pass variants are 6 dB/oct, not 12. In the built circuit the input reaches the output through stage 2's capacitor, so the high-pass passband is essentially clean: Drive mostly shapes the region around cutoff. v1.5's structure ran the input through a saturator, giving 32.7 % THD at Drive 100; v1.6 gives 0.18 %. Korg grounds the low-pass input and feeds the signal into stage 2's lifted capacitor. The result is a 12 dB high-pass plus a band-pass term, so the slope below cutoff is 6 dB/oct. Up to v1.5 this model used s²/(…), at 12 dB/oct.

**Mk2 model (unchanged except the high-pass).**
- LP1 → Σ → LP2, with K·y fed back through HP1.
- The feedback gain is limited by a diode-like secant, and there is a mild tanh at the stage-2 input, as an OTA input stage would add.

**Mk1 model (new in v1.6).**
- A Sallen-Key core solved zero-delay from both capacitor states.
- The X1 diode stage is fitted to the study's Figure 17 (n·Vt = 52 mV, Is ≈ 1.7 nA). Each sample solves the stage as one scalar monotone equation (four Newton steps, worst relative residual about 1e-5).
- **Level reference (assumption):** 5 V peak per unit of signal inside the filter, after Drive. Drive feeds every model at −12 dB at Drive 0 and up to +18 dB at Drive 100, so the diode knee is reached at about +2 dBFS input at Drive 0 and about −16 dBFS at Drive 60.
- **CHARACTER** drives the diode stage by 0 to +24 dB. Makeup gain follows Drive's level compensation (half the drive in dB at the default 100 %). At CHARACTER 100, quiet signals come out +11.6 dB and 0 dBFS −6.6 dB, and self-oscillation drops from −6.8 to −18.8 dBFS.
- **Reference minimums (8x LPF / 4x HPF) are measured at the default CHARACTER,** as for every model. Heavy CHARACTER aliases more: −67.9 dBc at 8x at CHARACTER 50, and −44.5 at 100.
- Resonance reaches a small-signal loop gain of about 2.4, which assumes the study's ×1.1 JFET buffer. So Mk1 self-oscillates only near maximum resonance (it does at 100 %, not at 90 %).
- **Not modelled:** the Korg35's asymmetric resonance. The study shows it in simulation only, and its magnitude is unverified. The MS-20's own component values may also differ from the MS-10's, which the study used.

**Measured** (`tests/v16_tests.py`):
- Mk1 matches its transfer functions within 0.23 dB (LP) and 0.11 dB (HP).
- In Stinchcombe's detection test (500 Hz, fc 7 kHz, res 50), Mk1's distortion rises from 0.009 % at −24 dBFS to 4.5 % at 0 dBFS, against 0.002–0.59 % for Mk2.
- Worst peak in the fs/4 sweep: −3.9 dBFS.

## 03 Moog transistor ladder-inspired, revised

**Circuit.** Four stages, each a transistor differential pair acting as a nonlinear impedance with a tanh-like characteristic, loaded by a capacitor. Huovilainen's analysis (DAFx-04) gives each stage as dyᵢ/dt = ω(tanh(yᵢ₋₁) − tanh(yᵢ)), driven by the input pair tanh(x − k·y₄). The linear transfer function is 1/((1+s)⁴ + k) (Stilson & Smith 1996; Stinchcombe 2008), self-oscillating at k = 4.

**The model.** Exactly those per-stage equations, with every tanh present: the input pair and all four stage pairs. The previous version had only an input tanh. They are solved with zero-delay feedback: each tanh is replaced by its secant gain tanh(v)/v at the previous sample, so the four stages are linear for the current sample and the global loop is solved in closed form. CHARACTER (STAGE SAT) runs from circuit-nominal (0 %) to 3× hotter stage saturation (100 %). Comp restores the 1/(1+k) bass loss that the circuit shows (visible in the circuit-reference plot at Comp 0). **Approximation:** the secant method lags the nonlinearity by one sample. This is standard practice and well behaved, but not an exact solve of the nonlinear ODE.

**v1.6, Minimoog Model D filter board** (service manual fig. 9-11; [literature check](independent-review/LADDER_LITERATURE_CHECK.md)):
- **Emphasis:** k = 15.17·Rb/(R14 + 1330), with R14 a 50 kΩ reverse-audio rheostat. 15.17 is the Q7/Q5 gain-recovery gain times the R7/R3 tap; Rb = 441.5 Ω is the REGEN CAL setting, chosen so oscillation starts at Emphasis 9 (assumed). So k = 0.13 at 0, 1.06 at 50 % and 5.04 at 100 %.
- **Couplings:** C5/C1 (15.4 Hz) on the ladder output, in the loop, and C10 (R14-dependent, 12 Hz at full Emphasis) in the feedback. The filter does not self-oscillate below about 120 Hz cutoff.
- **Gain-recovery pair** Q7/Q5: tanh at the ladder's 2 V_T scale, in the output and in the loop.
- **Scope:** the board applies to the low-pass only. The ALT high-pass pole-mix keeps the v1.5 law and is bit-identical. The 12 dB tap (y₂, not on a Minimoog) passes through the same output-pair saturation.
- Self-oscillation is about 3.3 dB louder than v1.5, because k reaches 5.04.

## 04 Steiner-Parker Synthacon-inspired, rebuilt

**Circuit.** The Steiner-Parker is a classic Sallen-Key filter adapted with biased diodes as controlled resistors. The diode strings act as voltage-controlled resistors, and the filter's Q comes from the gain of a non-inverting amplifier, staying almost constant as the filter is swept. The HP, BP and LP modes come from injecting the signal at three different points of the circuit, and all inputs can be driven at once. Resonance gain grows with Q, so clipping can occur.

**The model.** A Sallen-Key network (R1, R2 = diode strings; C1 to the amplifier's feedback node; C2 to the HP injection terminal) with amplifier gain K. Linear responses:
- LP injection (into R1): K/(s² + (3−K)s + 1)
- BP injection (at the feedback node): K·s/(s² + (3−K)s + 1)
- HP injection (into C2): K·s(s+2)/(s² + (3−K)s + 1)

It self-oscillates at K = 3. The model solves the two capacitor states with a 2×2 zero-delay trapezoidal system each sample. Diode-string currents saturate (tanh secant of the voltage across each string), and the amplifier clips (hard-knee secant on K). CHARACTER (BP BLEND) moves the input from the LP (or HP) injection point to the BP point, as the original's multiple inputs allow. Comp divides out the amplifier gain K, which otherwise raises the passband by up to +9.5 dB.

**Uncertain, so flagged:** I could not access Steiner's 1974 article, so the exact injection node for HP is inferred from standard Sallen-Key analysis. With injection at C2 the HP response is resonant near the cutoff but relaxes to **6 dB/oct well below it**. Use the slope selector (24–48) when you need a steep bass cut. If the original circuit injects HP elsewhere, its skirt may be steeper.


**v1.6, from Steiner's article** (Electronic Design, 6 Dec 1974; [check](independent-review/STEINER_1974_CHECK.md)):
- The article confirms the transfer functions, the three input points and the high-pass node (bottom of C2).
- **Diode law.** The diode "resistors" are one forward-biased string fed in mirror from both ends. The net law is therefore sinh, and cutoff rises with level, bounded by the 2 kΩ feed resistors. v1.5's tanh law ran the other way.
- **Level reference (assumption):** one model unit = the article's 0 dBm input at the low-pass node.
## 05 Oberheim SEM-inspired, revised

**Circuit.** A 2-pole state-variable filter whose integrators are CA3080 OTAs. An OTA's output current follows gm·tanh(v_in/2V_T), so each integrator's input saturates. The resonance pot sets the damping, and the mode control mixes LP and HP (notch in the middle).

**The model.** A zero-delay SVF with each integrator's gain replaced by its OTA secant gain, using tanh on that integrator's input from the previous sample. The previous version used a linear SVF with an ad-hoc limiter. Damping never reaches zero (Q ≤ 10), so the model does not self-oscillate. SEM clones are reported to oscillate raspily in some builds, so this is a conservative choice. CHARACTER (NOTCH MORPH) is the mode knob.


**v1.6, from the Oberheim SEM-1A schematic** ([check](independent-review/SEM_SCHEMATIC_CHECK.md)):
- **Damping:** the RES-pot law, 2R = 0.1 + 3.03·(1 − res), with a linear taper assumed, so Q runs 0.32 to 10. The floor of 0.1 means no self-oscillation, as SEM owners report.
- **Diode limiter:** the D11/D12 path adds damping once the band-pass output exceeds about 2.6 V, which compresses the resonant peak on loud signals.
- **Input:** linear, as the A12 summer is; the op-amp rails limit the outputs at ±13 V.
- **Unchanged:** the notch (HP↔LP crossfade) and band-pass routing, which already matched the schematic.
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

## Envelope filter (v1.6, Mu-Tron III topology)

**Circuit** (M. L. Beigel, US patent 3,911,776, 1975):
- a preamp, then a precision half-wave rectifier;
- RC smoothing: fast attack through a small resistor, slow decay through a large one;
- a voltage-to-current converter driving one LED, which lights the two photoresistors of a two-integrator second-order filter;
- LP, BP and HP taken from the three nodes; Q set by a variable resistor, with gain proportional to Q;
- DOWN subtracts the envelope from a reference;
- RANGE adds a capacitor across each integrator.

The integrator capacitors (1.8 nF, plus 2.2 nF in LO) and the 150k audio Peak pot are from R. G. Keen's Neutron, a Mu-tron III work-alike.

**The model.** That chain at the base rate, before the filter section. The filter is a TPT state-variable filter whose frequency comes from the photoresistor network, f = 1/(2π·R·C) with R = 3.3 k + (1 M ∥ R_LDR). The preamp and filter outputs saturate at ±7.5 V op-amp rails. The sweep position is also routed, in octaves, to the LPF, HPF and BPF cutoffs.

**Assumed (no production schematic available):**
- the LDR law (conductance ∝ light^0.8, 10 kΩ at 1 V of envelope);
- the LDR lags (2.5 ms on, 35 ms off; the original Hamamatsu part has no available data);
- the 1 MΩ and 3.3 kΩ resistors;
- Q from 0.6 to 16;
- the DOWN reference (1 − 2·envelope);
- 1 unit = 1 V.

A Mu-tron III schematic would calibrate all of these. [Sources](independent-review/ENVELOPE_FILTER_SOURCES.md).

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

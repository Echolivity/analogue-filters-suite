# Hardware reference catalogue

For each model: what hardware it claims, what that hardware actually is, which revision applies, and how firmly the reference is established.

Evidence grades used below:
- **[S]** Schematic or primary technical document.
- **[P]** Peer-reviewed or published circuit analysis.
- **[M]** Manufacturer manual or marketing description.
- **[F]** Forum, DIY or secondary source.
- **[N]** No accessible source.

The prompt's five categories are abbreviated as follows:

| Abbreviation | Prompt category |
|---|---|
| Original | Original circuit topology |
| Later rev. | Later hardware revision |
| Confused | Commonly confused implementation |
| Inspired | Generic model inspired by the hardware |
| Circuit-derived | Genuine circuit-derived DSP |

Each model's entry ends by stating which category the implementation belongs to.

---

## Filters

### 01 Sherman Filterbank (LPF / HPF)

**Hardware.**
- Sherman Filterbank by Herman Gillis, Belgium. Prototypes date from 1995; the Filterbank 2 from 2001.
- Two analogue multimode filters. Each is continuously variable through LP, BP, notch and HP.
- The filters can run in **serial or parallel**. Two identically tuned filters in series give 24 dB/oct.
- Filter 2 can follow filter 1 at fixed harmonic intervals (1, 1.5, 2 … 16).
- Further sections: an input overdrive, a VCA overdrive with AR, and a ring modulator.
- Sources [M/F]:
  - Sound On Sound review of the Filterbank 2 Compact, 2019: https://www.soundonsound.com/reviews/sherman-filterbank-2-compact
  - Effects Database entry: https://www.effectsdatabase.com/model/sherman/filterbank2
  - Thomann product page: https://www.thomannmusic.com/sherman_filterbank_2_dual_rack.htm

**Schematic:** none public **[N]**. The filter core topology (OTA, transistor or other) **cannot be identified**.

**Implementation.** A behavioural model built from the published *block* description:
- input overdrive (asymmetric)
- filter 1 → filter 2 in series at equal tuning
- an output→input feedback path, which the project's docs say was *a design choice* and is not documented hardware behaviour

**Category:** Inspired. **Reference certainty: low.**

### 02 Korg 35 / MS-20 (LPF / HPF)

**Hardware and revisions.**
- The MS-10 and early MS-20 used Korg's proprietary **KORG35 thick-film IC**. Later MS-20s used a daughter board with **two LM13600 OTAs**. These are two distinct circuits that are commonly confused under the name "MS-20 filter". Sources [F]:
  - Korg MS-20 Wikipedia mirror: https://kwx.liehendr.com/content/wikipedia_en_all_maxi_2024-01/A/Korg_MS20
  - Sequencer.de synth database: https://www.sequencer.de/syns/korg/MS20.html
  - Gearspace thread: https://gearspace.com/threads/ms-20-filter-difference.473473/
- An MS-20 with the front-panel screw has been reported with a Korg 35 inside, so the panel screw is not a reliable indicator.
- The character comes from nonlinear diodes in the resonance feedback path. The MS-20 runs its HPF and LPF in series.
- Detailed circuit study **[P]**: T. Stinchcombe, *A study of the Korg MS10 & MS20 filters*, http://www.timstinchcombe.co.uk/synth/MS20_study.pdf. **This study was not accessed during the audit.**
- DSP model **[P]**: W. Pirkle, *Modeling the Korg35 Lowpass and Highpass Filters*, AES 135, 2013.

**Open question.** One DIY analysis describes the HP path as first order (CR, 6 dB/oct) at zero resonance [F]: https://lookmumnocomputer.discourse.group/t/1113-performance-filter/14/22. The implementation follows Pirkle's 2-pole HP. **Unresolved without Stinchcombe's study.**

**Implementation.**
- Revision targeted: **KORG35 (Mk1) only**, as the code comment says (build_genexpr.py:115). The LM13600 Mk2 revision is not modelled.
- Structure: Pirkle's ZDF Sallen-Key structure with tanh in the loop and secant limiting of the feedback gain.

**Category:** Circuit-derived (from a published DSP model), but at block level. It is not a transistor-level KORG35 model.

### 03 Moog transistor ladder (LPF) and "Ladder HP ALT"

**Hardware.** A four-stage transistor ladder with global feedback.

**Published analyses [P]:**
- Small-signal transfer function 1/((1+s)⁴+k), with self-oscillation at k = 4:
  - Stilson & Smith, ICMC 1996
  - T. Stinchcombe, *Analysis of the Moog Transistor Ladder and Derivative Filters*, 2008: https://www.timstinchcombe.co.uk/synth/Moog_ladder_tf.pdf
- Per-stage tanh model: A. Huovilainen, DAFx-04, https://dafx.de/paper-archive/2004/P_061.PDF

**Implementation.**
- **LPF:** Huovilainen's per-stage equations, solved by ZDF secant linearisation. **Category: circuit-derived** (from a published nonlinear analysis).
- **HP "ALT pole-mix":** the ladder taps are mixed into s⁴/((1+s)⁴+k). The Moog ladder module is low-pass; this high-pass is **not a Moog circuit**, which the menu already says. **Category: generic DSP**, honestly labelled.

### 04 Steiner-Parker Synthacon VCF (LPF / HPF)

**Hardware.**
- A Sallen-Key filter. The resistors are replaced by **biased diode strings acting as voltage-controlled resistors**. Q is set by the gain of a non-inverting amplifier.
- LP, BP and HP come from injecting the signal at different nodes of the same network.
- The circuit is unbuffered and its path is mirrored, with the diodes inverted on one branch.
- Primary source **[S]**: N. Steiner, *Voltage-tunable active filter features low, high and bandpass modes*, Electronic Design 25, 6 Dec 1974. **Not accessible from this session** (fetch refused).
- Secondary sources [F]:
  - CGS35 documentation: https://open4umodular.github.io/synthpanel/modules/cgs35_euro_vcf.html
  - CGS35 build notes: https://djjondent.blogspot.com/2015/02/synthacon-vcf-cgs-35-build-notes.html
  - KVR forum thread with a u-he developer: https://www.kvraudio.com/forum/viewtopic.php?p=5992216

**Implementation.**
- **LP:** a single-branch Sallen-Key with diode-string secant conductances and a clipping amplifier.
- **HP:** the HP injection node is **inferred**, not read from the schematic.
- The mirrored branch is not modelled. That branch is what cancels even-order products in the real circuit; dropping it is consistent with symmetric behaviour, but it is unverified.

**Category:** Circuit-derived (LP); Inspired / unverified (HP).

### 05 Oberheim SEM (LPF / HPF)

**Hardware.**
- A 12 dB/oct state-variable filter whose integrators use **CA3080 OTAs** as current-controlled elements.
- It has simultaneous LP, BP and HP outputs; notch is LP + HP.
- Sources [F/M]:
  - Modular Grid listing of an SEM clone built with original parts: https://modulargrid.net/e/modules/view/2736
  - Syntiac's description of an Oberheim-type filter: https://syntiac.com/syntiac_obvcf.html
  - Georgia Tech course notes that use the SEM schematic: https://lanterman.ece.gatech.edu/?p=112
- Original SEM schematics circulate and are used in teaching **[S]**, but this audit did not inspect them.

**Implementation.** A ZDF SVF whose integrators have OTA tanh input saturation. The LP→notch and HP→notch morph corresponds to the hardware's mode control.

**Category:** Circuit-derived at topology level.

### 06 Roland TB-303 diode ladder (LPF)

**Hardware.** A diode ladder in Stinchcombe's "TB-303 configuration": one diode at the top and the bottom capacitor halved. A high-pass sits in the feedback loop.

**Sources:**
- **[P]** T. Stinchcombe, 2008 (above). Its polynomial s⁴+6.727s³+14.142s²+9.514s+1+k is reproduced exactly by the implementation.
- **[F]** x0xb0x measurements: https://github.com/a1k0n/303

**Category:** Circuit-derived.

---

## Band-pass engine

| Profile | Hardware fact | Native BP? | Implementation |
|---|---|---|---|
| Oberheim SEM | The SVF has a band-pass output (above) | Yes, SVF BP | SVF BP plus a *regeneration loop that the SEM does not have* (bpf.py:261) |
| Steiner-Parker | BP is produced by injecting the signal at the BP node | Yes, but a Sallen-Key network | Response-equivalent SVF. Not the circuit topology. |
| Korg 35 / MS-20 | HPF and LPF run in series | Yes, cascade | Two *generic nonlinear SVF sections*, not two KORG35 sections |
| ARP 2600 | 4012 (ladder) and later 4072 VCFs are low-pass only | **No** | Derived from a ladder core plus a 14 kHz roll-off. The roll-off figure is secondary [F] and has not been verified against 4072 data. |
| EMS VCS3 | Diode-ladder low-pass (Stinchcombe "EMS configuration"; Civolani & Fontana model) | **No** | Derived. The "diode rung" is a tanh-of-difference secant on a *generic* 4-pole core, not the VCS3 ladder configuration. |

**Category.** The native combinations (SEM SVF, MS-20 cascade) are *inspired*, because the circuit elements are generic. ARP and EMS are *generic DSP labelled "derived"*.

---

## Compressors

### OPTO: Teletronix LA-2A

**Hardware.**
- T4 electro-optical attenuator: an EL panel with a CdS photocell.
- Program- and frequency-dependent. Average attack about 10 ms, with frequency-dependent attack.
- Release: about 60 ms for the first 50 %, then 1–15 s for the rest (UA). Other sources give 0.5–5 s depending on previous programme material.
- Modes: Compress (soft knee, nominally about 4:1 but source-dependent) and Limit (≈∞).
- Sources [M]:
  - UA help centre: https://help.uaudio.com/hc/en-us/articles/215779663
  - UA WebZine, 2003: https://www.uaudio.com/webzine/2003/june/text/content4.html
  - recording.org history thread: https://recording.org/forum/recording-live-or-studio/teletronix-la-2a-history-and-how-it-works

**Topology.**
- A **feedback-style** design: the side-chain is driven by a signal that has already been gain-reduced.
- The side-chain runs through the Peak Reduction pot, a 12AX7 voltage amplifier with a pre-emphasis network, and a 6AQ5 that drives the EL panel. Source [M]: https://marine.manualsonline.com/manuals/mfg/inova/la2a.html?p=16
- Audio path: input transformer; T4 shunt before the first gain stage; cascaded 12AX7 halves; 12BH7 cathode follower; output transformer. Source [F]: https://crochambeau.blogspot.com/2011/10/continuing-contemplation-of-teletronix.html
- **Uncertainty:** that same blog describes the side-chain as fed from the input split. That conflicts with the "feedback-style" statement in the service-style manual above, so the exact tap point is unverified.

**Implementation.** Behavioural, with no tube or transformer stages.

**Category:** Inspired.

### VCA: API 2500

**Hardware.**
- **THRUST** is a patented filter inserted *before the RMS detector* in the side-chain. In MED it slightly cuts lows and slightly lifts highs into the detector.
- **TYPE:** NEW is feed-forward (the detector sees the input); OLD is feedback (the detector sees the VCA output).
- **KNEE:** hard, medium or soft.
- **Release:** 0.05–3 s, preset or variable.
- **L/R link:** variable, with a **link filter** (HP, LP, BP). On the 2500+, link speeds are FAST (peak) and SLOW (RMS).
- Sources:
  - API 2500+ manual [M]: https://www.manualslib.com/manual/3614561/Api-2500Plus.html
  - API 527A manual [M]: https://apiaudio.com/docs/manuals/527A_user_20-07-13.pdf
  - Waves API 2500 manual, a licensed emulation (secondary) [M]: https://manualmachine.com/wavesaudio/api2500/6495049-user-guide/ and https://www.bhphotovideo.com/lit_files/981196.pdf

**Exact THRUST curves:** **not public [N]**.

**Implementation.** Detector architecture after the manual; the VCA itself is an ideal multiplier.

**Category:** Inspired.

## Preamplifier and saturation

### TUBE ("triode stage")

**Reference.** No specific product is claimed. The implied reference is a 12AX7-class common-cathode triode stage.

**Literature [P]:**
- Koren triode model:
  - N. Koren, *Improved vacuum tube models for SPICE simulations*, Glass Audio 8(5), 1996: https://www.normankoren.com/Audio/Tubemodspice_article.html
  - Koren, *Finding SPICE tube model parameters*: https://www.normankoren.com/Audio/Tube_params.html
- Grounded-cathode DSP model: Santagata, Sarti & Tubaro, DAFx-07, https://re.public.polimi.it/retrieve/e0c31c0a-187b-4599-e053-1705fe0aef77/DAFx07-Sarti.pdf
- WDF triode modelling:
  - Giampiccolo et al., DAFx-23: https://re.public.polimi.it/retrieve/a1844311-c89f-4257-a993-126fe4a5304c/GiampiccoloEtAl_DAFx23.pdf
  - Oliveira et al., 2013: https://compmus.ime.usp.br/sbcm/2013/pt/docs/art_tec_3.pdf

**Implementation.** A static asymmetric tanh waveshaper. **No triode equation** is used.

**Category:** Generic DSP, under a hardware-flavoured name.

### Transformer stages

**None implemented.** No module claims transformer emulation.

### GATE, soft clip, DC blockers

These are generic utilities. **No hardware claim** is made.

---

## Summary of certainty

| Model | Reference identified | Revision fixed | Circuit data used |
|---|---|---|---|
| Sherman | Product yes, circuit **no** | n/a | none |
| K35 | Yes | Mk1 only, and implicit | Published DSP model (Pirkle); Stinchcombe study not accessed |
| Ladder LP | Yes | n/a | Published nonlinear analysis |
| Ladder HP | Not a hardware circuit | — | — |
| Steiner | Yes | 1974 article not accessed | Secondary descriptions |
| SEM | Yes | Schematic not inspected | Topology-level descriptions |
| TB-303 | Yes | 303 configuration | Published analysis |
| BPF ARP / EMS | Hardware has no BP | — | — |
| Opto | LA-2A | Gray/Silver/early versions not distinguished | Manuals and time constants |
| VCA | API 2500 | 2500 vs 2500+ not distinguished | Manual feature list |
| Tube | Generic | — | none |

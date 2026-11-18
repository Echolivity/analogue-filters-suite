# DSP fidelity roadmap

**Proposals only.** Nothing here has been implemented: the brief's approval gate applies.

Every item would keep parameter IDs, ranges and preset compatibility, in two ways:
- New behaviour is added as new parameters or new model entries.
- Changes to existing models are gated, so that existing Live Sets keep their sound where that matters (see "Compatibility" for each item).

Items are ordered by:
1. Authenticity
2. Audibility
3. Correctness
4. CPU
5. Stability
6. Maintainability

Stability defects come first, because they are correctness failures.

**Complexity scale:**

| Grade | Effort |
|---|---|
| S | Under a day |
| M | Several days |
| L | 1–3 weeks |
| XL | More than 3 weeks, or needs hardware |

---

## P0: correctness

### R1. Stabilise the secant-solved filters at high g

| | |
|---|---|
| **Existing** | One-sample-lagged secant linearisation (build_genexpr.py:37 and every model) |
| **Deficiency** | Sherman diverges to +249 dBFS, and Steiner reaches +30 dBFS, at 1×, fc 12 kHz, res 100 %, 48 kHz (F §4.2) |
| **Proposal** | **(a)** Clamp each model's state magnitude to a physically plausible rail, a soft limit on state (cheap, preserves sound below the rail). **(b)** One or two Newton iterations on the loop node when g > 0.5 and resonance > 0.9: re-evaluate the secants at the current estimate. **(c)** Optionally switch to 2× automatically above fc > 0.25·fs. |
| **Sonic effect** | None in normal ranges; removes a failure mode |
| **CPU** | (a) ≈0; (b) +30–60 % for the affected model, only in the high-g region |
| **Latency / aliasing** | None / none |
| **Complexity** | S (a), M (b) |
| **Validation** | Extend F3/F6 over a fine cutoff × resonance × sample-rate grid at 44.1/48/96 kHz and 1×/2×. Pass = bounded below +12 dBFS before the soft clip. Golden renders unchanged below fc 8 kHz. |
| **Compatibility** | (a)/(b) alter output only where it currently diverges |

### R2. Default oversampling, and a 4× option

| | |
|---|---|
| **Existing** | 2× available, off by default; 2× inside the tube |
| **Deficiency** | At 1×: Steiner −25 dBc and Sherman −39 dBc aliasing (F §3.3). Tube at Drive 100: −30 dBc even at 2× (P §2.6). |
| **Proposal** | Add a 4× setting: a second half-band stage, extending the `ovs_sel` enum with an appended value, which is compatible. Make the tube's factor follow the drive (4× above Drive 70 %). Whether new instances should default to 2× is **a product decision for the owner**. Changing the default changes the sound of new instances, though not of saved Sets. |
| **Sonic effect** | Cleaner high-frequency drive; less grit on bright sources |
| **CPU** | 2× ≈ +20 % (measured 948 → 1147 ns); 4× ≈ +60–80 % on the filter section |
| **Latency** | Still 0 (IIR), at the cost of more phase delay at HF |
| **Complexity** | M |
| **Validation** | Repeat F5/T6 at 1×/2×/4×. Target ≤ −80 dBc at the F5 test point. |

### R3. Idle CPU

| | |
|---|---|
| **Deficiency** | 3.6 % of a core with everything off |
| **Proposal** | Run control smoothing at block rate when targets are settled; skip whole-section code behind a single "anything active" test |
| **Complexity** | M |
| **Validation** | Golden renders must stay bit-exact |

---

## P1: highest audible authenticity gains

### R4. OPTO attack and ratio calibration

| | |
|---|---|
| **Existing** | EL one-pole 2/4 ms; LDR fast 4.5 ms attack; gain 1/(1+(Kc)^p) (dyn.py:153–163, 321–328) |
| **Reference** | Average attack ≈10 ms, frequency-dependent; COMP ≈4:1 soft knee, source-dependent; LIMIT ≈∞ |
| **Deficiency** | 2.3–2.9 ms attack; 2.2–2.7:1 COMP; ≈10:1 LIMIT (C §1) |
| **Proposal** | **(1)** Model the EL panel as a capacitive load driven through the 6AQ5 stage: light ∝ \|v\|^α above a threshold, with a slower rise. **(2)** Model the CdS cell as a nonlinear resistance R = R_dark·(1 + (L/L0)^γ)⁻¹, with separate rise and decay dynamics and two time constants. That gives a frequency-dependent attack, because the rectified ripple at low frequencies drives the light differently. **(3)** Calibrate K, p and γ for COMP 4:1 and LIMIT ≥ 20:1. |
| **Sonic effect** | Slower, smoother onset; more "LA-2A" levelling |
| **CPU** | Negligible |
| **Complexity** | M |
| **Validation** | Static curves and attack against the published figures. Ideally, burst protocols against a hardware T4 (see `DSP_VALIDATION_RESULTS.md`). |
| **Compatibility** | Changes the existing OPTO sound. Propose it as a new "OPTO mode" value, or gate it behind an appended parameter. |

### R5. OPTO audio-path colour (tube make-up and transformers)

| | |
|---|---|
| **Proposal** | A 12AX7 common-cathode pair plus a 12BH7 cathode follower: Koren triode with load line (see R7), at fixed nominal levels, with optional input/output transformer low-frequency saturation (R9). |
| **Sonic effect** | Second-harmonic colour and a level-dependent low end, even at 0 dB GR |
| **CPU** | Moderate (2× oversampled triode solve) |
| **Complexity** | L |
| **Validation** | THD/harmonic spectra vs level against published LA-2A measurements or hardware |

### R6. VCA detector and link

| | |
|---|---|
| **Existing** | 3 ms RMS → dB one-pole attack/release; THRUST shelves; link % only |
| **Deficiency** | Sub-millisecond attack settings not achieved (0.03 ms measures 0.71 ms); THRUST MED without HF lift; no link filter (C §2) |
| **Proposal** | **(1)** Make the RMS averaging time track the attack setting, with a floor of about 0.1 ms, or use a peak-plus-RMS hybrid detector so that fast attacks are reachable. **(2)** Fit THRUST curves to published frequency plots or to hardware measurement. The patent may describe the network: a literature search is needed. **(3)** Add the link filter (HP/LP/BP) as appended parameters. **(4)** Verify OLD-mode ratio behaviour against hardware or the manual's curves, and add ratio rescaling if the hardware does it. |
| **Sonic effect** | Faster transient control; more accurate THRUST tilt; better-behaved stereo |
| **CPU** | Negligible |
| **Complexity** | M (1, 3); L (2, 4, which need references) |
| **Validation** | Attack step tests (C2a); THRUST GR vs frequency (C4b) against references |

### R7. A real triode stage for TUBE

| | |
|---|---|
| **Existing** | Static asymmetric tanh (dyn.py:66–72) |
| **Deficiency** | No triode law or load line; frequency-independent and memoryless distortion (P §2.3–2.4) |
| **Proposal** | A common-cathode 12AX7 stage. The Koren plate current law Ip(Vgk, Vpk) is solved with a plate resistor and B+ (one-dimensional Newton, 2–3 iterations, or a 2-D lookup table with bilinear interpolation). Add a cathode resistor and bypass capacitor, a coupling capacitor with grid-leak resistor and grid-current diode (bias shift and recovery), and Miller capacitance as a gain-dependent one-pole. Keep Drive (grid drive) and Bias (cathode resistor / operating point) as physical parameters, and 4× oversampling. |
| **Literature** | Koren 1996; Santagata, Sarti & Tubaro, DAFx-07; WDF approaches (Giampiccolo et al., DAFx-23) — see the catalogue |
| **Sonic effect** | Frequency- and history-dependent distortion; "bloom" after transients; more realistic H2/H3 balance vs level |
| **CPU** | Tube stage ×3–6; still small in absolute terms |
| **Latency** | 0 |
| **Aliasing** | Needs 4× (R2) |
| **Complexity** | L |
| **Validation** | Compare against a SPICE simulation of the same stage, using Koren 12AX7 parameters: THD vs level and frequency, step response of the bias shift. That would reach **Class A against a SPICE reference**. Then against hardware, if available. |
| **Compatibility** | Offer it as a new TUBE type (an appended enum) and keep the current shaper as "Classic". |

---

## P2: filter authenticity

### R8. Even-order behaviour and circuit asymmetries

| | |
|---|---|
| **Deficiency** | H2 below −170 dBc in K35, Ladder, Steiner, SEM and 303 (F §3.1) |
| **Proposal** | Introduce the asymmetries each circuit actually has, from analysis, not by adding a generic H2 shaper: diode forward-drop asymmetry in the K35 feedback limiter (exponential diode pair with unequal saturation currents); the bias offset in the Steiner strings (use the exponential diode I–V around the bias point instead of tanh); transistor mismatch in the ladder (a small offset per stage, as a hidden or "Age" parameter). |
| **Sonic effect** | Warmer, less "perfect" saturation |
| **Complexity** | M per model |
| **Validation** | Needs hardware or SPICE to set magnitudes. **Do not invent numbers.** |

### R9. Revision-correct K35 / MS-20

| | |
|---|---|
| **Proposal** | Obtain Stinchcombe's MS-20 study, settle the HP order and the diode clipper, then add an "MS-20 Mk2 (LM13600)" model as an appended menu entry |
| **Complexity** | M–L |
| **Validation** | Against the study's transfer functions; then hardware |

### R10. Steiner-Parker from the 1974 article

| | |
|---|---|
| **Proposal** | Obtain the article, verify the HP injection node and model the mirrored branch with exponential diode strings |
| **Sonic effect** | Correct HP slope; correct saturation shape |
| **Complexity** | M |

### R11. Iterated nonlinear solve (quality mode)

| | |
|---|---|
| **Proposal** | Optional Newton refinement (R1b) for all models, at all cutoffs, as a "quality" setting. Removes the one-sample lag that affects high-frequency resonance character and pitch (Sherman +58 cents at 8 kHz). |
| **CPU** | ×1.5–2 on the filter section |
| **Complexity** | M |

### R12. Analogue noise floor and self-start

| | |
|---|---|
| **Proposal** | Inject very low-level noise (about −120 dBFS, not audible) at each model's input node, so that self-oscillation starts from silence as it does on hardware |
| **Complexity** | S |
| **Validation** | The F3 self-start test without excitation |
| **Compatibility** | Breaks bit-exact golden renders, so it needs a new baseline or an off-by-default parameter |

### R13. Bilinear high-frequency cramping

| | |
|---|---|
| **Existing** | 1× bilinear: top-octave error up to 22–38 dB at fc 12 kHz; resonance-peak shift up to +167 cents (F §2.2) |
| **Proposal** | Covered mainly by R2 (2×/4×). For 1×, match the resonance peak position by correcting g as a function of resonance and fc/fs (a fitted correction, as already done for the multimode BPF centre). |
| **Complexity** | S–M |

---

## P3: band-pass engine and Sherman

### R14. BPF native modes from their own cores

| | |
|---|---|
| **Proposal** | For the native pairings, use the actual model cores: the SEM BP output of `f_sem` (no regeneration loop; Q from damping), and the MS-20 BP from two real K35 sections in series. Keep the other pairings labelled "derived". |
| **Complexity** | M |
| **Compatibility** | New architecture values, or a "native" flag |

### R15. Sherman

| | |
|---|---|
| **Status** | No schematic is public. Authenticity cannot be improved without hardware measurement. |
| **Proposal** | **(1)** Fix stability (R1). **(2)** Expose the documented features (multimode morph per filter, parallel mode, harmonic ratio) as appended parameters. **(3)** Remove or relabel the invented feedback as a creative control. **(4)** Only with a hardware unit: characterise the filters by measurement (black-box identification). |
| **Complexity** | M (1–3); XL (4) |

---

## Proposed implementation order

| Order | Items | Why |
|---|---|---|
| 1 | R1 (a), R3 | Remove the failure mode; recover idle CPU. Low risk; the golden renders guard the rest. |
| 2 | R2 | Biggest audible cleanup; decide the default with the owner |
| 3 | R4, R6 (1, 3) | Largest measured deviations from published compressor behaviour; cheap |
| 4 | R7 (+ R5 later) | Turns the TUBE into a genuine triode model; SPICE-verifiable |
| 5 | R12, R13, R1 (b) / R11 | Filter polish |
| 6 | R8–R10, R14 | Need primary sources or hardware |
| 7 | R6 (2, 4), R15 (4), and hardware validation of everything | Needs hardware |

## Estimated engineering effort

| Item group | Effort | Hardware needed? |
|---|---|---|
| P0 (R1–R3) | 1–2 weeks | No |
| P1 compressors (R4, R6 partial) | 1–2 weeks | Better with |
| P1 tube (R7) + LA-2A colour (R5) | 3–5 weeks | SPICE only; hardware for final |
| P2 filters (R8–R13) | 4–8 weeks | Yes, to set asymmetry magnitudes |
| P3 (R14, R15) | 2–3 weeks (+ hardware for R15.4) | R15.4 only |

**Awaiting approval.** No production DSP has been changed by this audit. All golden renders still pass.

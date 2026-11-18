# Assessment of the 15 proposed fixes (DSP_FIDELITY_ROADMAP.md)

## How to read this

**Decisions:**

| Decision | Meaning |
|---|---|
| **ACCEPT** | Implement as proposed |
| **MODIFY** | Implement with the stated changes |
| **POSTPONE** | Blocked on evidence or on a dependency |
| **REJECT** | Do not implement |

**Flags:**

| Flag | Meaning |
|---|---|
| **⚑ M** | Improves a measurement without improving the circuit model |
| **⚑ S** | A numerical-stability item, not an analogue-fidelity item |

**Key distinctions applied throughout:**
- Numerical stability is not analogue fidelity.
- Harmonic distortion is not convincing analogue saturation.
- A matching frequency response is not a matching nonlinear circuit.

Evidence references: **IR** = `INDEPENDENT_AUDIT_REVIEW.md`; `rc` = `data/root_cause.json`; `vf` = `data/verify.json`.

---

## R1. Stabilise the secant-solved filters

| Field | Assessment |
|---|---|
| 1. Original finding | Sherman diverges to +249 dBFS; Steiner reaches +30 dBFS (1×, 48 kHz, 12 kHz, res 100 %) |
| 2. Current implementation | Amplitude-dependent coefficients (damping, Ke, diode secants) taken from the *previous sample's* instantaneous signal values (build_genexpr.py:105–108, :198–200) |
| 3. Underlying problem | **Period-2 parametric pumping at fc ≈ fs/4** (IR §3). The limiter samples the oscillation at its zero crossings on alternate samples, so negative damping is applied 50 % of the time against a dead-beat damped step. This is a property of the *discretisation*, not of any circuit. The original audit's "high g" explanation is imprecise. |
| 4. Proposed correction | (a) Clamp the state; (b) Newton iteration when g > 0.5 and res > 0.9; (c) automatic 2× above fs/4 |
| 5. Alternatives | (i) Evaluate the nonlinearity *implicitly*: one fixed-point or Newton step on the current-sample band value. The replica is bounded at −1.8 dBFS (Sherman) and +3.8 dBFS (Steiner) with **one iteration** (`rc`). (ii) **For the Sherman only**, since it has no circuit reference: drive the limiter from a **phase-independent amplitude estimate** such as the SVF quadrature magnitude √(b² + (l·g-scaled)²) or the state energy. That removes the sampling-phase dependence at any g. (iii) A state finite/rail sanitiser as *defence in depth* only. |
| 6. Sonic consequence | Implicit evaluation changes the sound slightly *everywhere* the lag mattered: high-fc resonance and pitch. The quadrature limiter changes the Sherman's limiting character, a creative model with no hardware reference. Clamping alone would leave a hard-limited garbage tone. |
| 7. Cost | One extra solve per affected model per sample: about +30–60 % of that model's cost. The quadrature limiter is about +2 multiplies. |
| 8. Regression risk | **High for golden renders**: any implicit change breaks bit-exactness for Sherman and Steiner settings with resonance. Needs a new reference baseline, and an owner decision on whether saved Sets may change slightly. |
| 9. Validation | Stability map over fc 20 Hz–0.45·fso at 1-cent resolution around fs/4, res 0–100 % in 1 % steps, fs 44.1/48/88.2/96/192 kHz, 1×/2×/4×. Pass: peak < +6 dBFS internal; no fs/4 anomaly. Plus: before/after small-signal response (must not change); oscillation pitch and level vs fc; failure-propagation test (IR §3.1). |
| 10. Decision | **MODIFY.** Reject (a) as the fix. A clamp only masks the cause, and the brief forbids it; keep it only as a sanitiser, see R1-S. Accept (b) as an *implicit evaluation of the same nonlinearity* (alternative i), for Steiner and, if the owner prefers fidelity of the existing character, for Sherman. Accept alternative (ii) for Sherman in **Reference** mode. Reject (c) as a fix: it works only because fs/4 moves above the cutoff range. Keep it as a default-quality measure under R2. **⚑ S** |

**New sub-item R1-S (added by this review): output-stage failure containment.**
- **Problem.** The 2 Hz DC blocker (build_genexpr.py:730–735) stores any divergent value and emits about 1.5–2 s of full-scale DC after the fault ends (IR §3.1).
- **Proposed.** A non-finite or ultra-large guard on *state* (reset that model's state and the blocker when |x| > 10⁶ or the value is not finite). This is defence in depth, not a fidelity change.
- **Decision.** ACCEPT. **⚑ S**

## R2. Oversampling: 4× option and default policy

| Field | Assessment |
|---|---|
| 1. Finding | Aliasing at 1× (Steiner −25, Sherman −39 dBc); TUBE −30 dBc at Drive 100 with 2× |
| 2. Current | Global 2× option for the filter section, off by default; fixed 2× inside the TUBE |
| 3. Problem | Nonlinear models produce harmonics above Nyquist. Necessary oversampling depends on the model and the drive. Re-measured at the default Comp 100 (`vf.OS_filters`), the **Ladder is among the worst at 1× (−33 dBc)**. |
| 4. Proposed | A 4× setting; the TUBE factor follows drive; the default left to the owner |
| 5. Alternatives | **Per-model minimum factors** from measurement (`vf.OS_filters`, test C1, target −80 dBc): SEM **1×**; Sherman, K35, 303 **2×**; Steiner, Ladder **4×**. TUBE: **4×** for drive ≤ 60 %, **8×** for drive above about 80 % with high-frequency content. Alternatives to plain IIR half-band cascades: polyphase FIR (linear phase, adds latency), or ADAA (antiderivative anti-aliasing) for static shapers such as the TUBE. ADAA does not apply to stateful filter nonlinearities. |
| 6. Sonic | Cleaner bright/driven sounds. At typical settings (test C3) **no audible change**: below −144 dBc at 1× for all models except Steiner at −110 dBc. |
| 7. Cost | Measured: 2× on the filter section = +21 % total CPU (948 → 1147 ns). 4× is estimated at about ×2 for the filter section. The production half-band matches *ideal* 2× decimation to within 0–4 dB, so the half-band design is adequate. |
| 8. Risk | Phase: the IIR adds non-linear phase. Changing the default alters new instances only (saved Sets store `ovs_sel`). |
| 9. Validation | The OS factor study (C1/C2/C3) must be repeated *with convergence checking* (IR §4 B), so that aliasing is separated from autonomous dynamics. Also: CPU per factor, and a phase and group-delay plot. |
| 10. Decision | **MODIFY.** Accept per-model minimum factors rather than one global factor. Add 4× (and 8× for TUBE only). Evaluate ADAA for the TUBE shaper as a lower-cost alternative to 8×. The default policy is an owner decision. Recommendation: Reference mode uses each model's minimum factor; Creative mode keeps the user's choice. |

## R3. Idle CPU

| Field | Assessment |
|---|---|
| Finding / current | 760 ns per sample with everything off; per-sample control smoothing and gating |
| Problem | Efficiency, not fidelity |
| Proposal and alternatives | Block-rate control when settled; gate whole sections |
| Sonic | None, provided it is bit-exact |
| Cost / risk | Saves CPU. **Risk of subtle smoothing changes:** block-rate smoothing must reproduce the per-sample trajectory, or be applied only when exactly settled. |
| Validation | All golden renders bit-exact; click tests; CPU before and after |
| Decision | **ACCEPT, but move it from P0 to P1.** It is not a correctness item. |

## R4. OPTO attack and ratio calibration

| Field | Assessment |
|---|---|
| Finding | Attack about 4× too fast; COMP 2.2–2.7:1 against "4:1"; LIMIT about 10:1 against "∞" |
| Current | EL one-pole 2/4 ms; LDR fast and slow components plus memory; G = 1/(1 + (Kc)^p) (dyn.py:153–163, 321–328) |
| Problem (re-assessed) | Attack is **8.1 ms at 6 dB GR** and 2.35 ms at 18 dB GR (`vf.OPA`). Near the reference at moderate GR, fast at heavy GR. The references ("≈10 ms average", "4:1 (not really)") **lack measurement definitions**. The better-founded deviation: **no frequency dependence** (ratio identical at 100 Hz / 1 kHz / 5 kHz within 0.03). |
| Proposed | EL panel law, nonlinear CdS resistance law, recalibration of K, p, γ |
| Alternatives | (i) Postpone calibration until T4 measurement data exist; any constants chosen now would be fitted to marketing figures. (ii) Implement only the mechanisms with documented physical basis (EL light-vs-voltage threshold, CdS resistance law) with *literature* parameters, if a source is found. Otherwise keep the present model. |
| Sonic | Possibly smoother onset under heavy GR. Unknown without data. |
| Cost | Negligible |
| Risk | Changes the existing OPTO sound. Must be an appended mode. |
| Validation | Attack (t10 / t63 / t90) at 3–5 GR depths and 3 frequencies; release memory; static curves; then T4 or hardware measurement |
| Decision | **POSTPONE** calibration (**⚑ M** if done against nominal figures). **MODIFY**: research task first. Find published T4 measurements or measure a unit. |

## R5. OPTO audio-path colour (tubes, transformers)

| Field | Assessment |
|---|---|
| Finding | No 12AX7/12BH7 stages and no transformers in the OPTO |
| Problem | The LA-2A audio path is documented at block level ([M]/[F]): input transformer, T4 shunt, 12AX7 stages, 12BH7 cathode follower, output transformer. The stages are technically justified. **Their operating levels and transformer data are not.** |
| Alternatives | Build them from R7's validated triode model, at documented plate voltages, once a schematic is obtained. Model transformers only with measured or datasheet parameters (R9 below does not cover this). |
| Sonic | Low-order harmonic colour and LF level dependence |
| Cost | Moderate (oversampled triode solve) |
| Risk | Adds colour at 0 dB GR, so it must be optional and appended |
| Validation | SPICE against the actual schematic; THD vs level and frequency |
| Decision | **POSTPONE.** It depends on R7 and on a schematic. Reject any version made up "for character" without circuit data, because the brief forbids marketing-driven stages. |

## R6. VCA detector and link

| Field | Assessment |
|---|---|
| Finding | The 0.03 ms setting measures 0.71 ms; THRUST MED lacks the HF lift; no link filter; OLD-mode ratios |
| Current | 3 ms RMS → dB → one-pole attack/release (dyn.py:179, 358–366) |
| Problem | (1) The floor comes from RMS plus log dynamics (replica-confirmed). **But** the hardware's attack figures are front-panel nominal times, and an RMS-detecting unit would not reach a 63 % GR response in 0.03 ms either. Whether this is a deviation is **unverified**. (2) The THRUST curve is not public. (3) The link filter is documented ([M]) and missing. (4) The OLD-mode ratio is mathematically exact for the implementation (IR §2 #5). |
| Alternatives | (1) Make the RMS time track the attack; *or* a peak/RMS blend; *or* leave it alone. A shorter RMS window raises ripple distortion at low frequencies (the reason a 3 ms window exists). (2) Patent search, or measurement. (3) Implement HP/LP/BP link filters on the detector link path. (4) Measure the hardware. |
| Sonic | (1) Faster transient grab, with more LF distortion. (3) Less low-frequency-driven image shift. |
| Cost | Negligible |
| Risk | (1) Changes the sound of existing settings. (3) Additive (appended parameters). |
| Validation | Attack step at 3 frequencies; LF THD vs RMS window; link-filter frequency response of the detector; stereo GR vs frequency |
| Decision | (1) **POSTPONE** (⚑ M if tuned to match front-panel numbers). (2) **POSTPONE.** (3) **ACCEPT.** (4) **POSTPONE**: needs hardware. |

## R7. A real triode stage for TUBE

| Field | Assessment |
|---|---|
| Finding | Static waveshaper: THD independent of frequency and history |
| Current | Asymmetric tanh with bias; one-pole tone; 2× oversampling (dyn.py:66–72, 266–300) |
| Problem | Defining triode-stage behaviours are absent: the plate-current law with a load line (operating point that moves with signal), grid conduction with the coupling capacitor (bias shift and recovery), the cathode bypass (frequency-dependent gain and distortion), and Miller capacitance |
| Proposed | Koren 12AX7 law, a plate-load solve, cathode resistor and bypass, coupling capacitor with grid leak and grid diode, Miller one-pole; 4× oversampling |
| Alternatives | (i) Wave-digital-filter formulation with Koren or Cardarilli triode models (DAFx literature). (ii) A state-space nodal model with Newton. (iii) Tabulated Ip(Vgk, Vpk) with bilinear interpolation: cheaper, but it needs careful interpolation to avoid aliasing kinks. Not acceptable: a dynamic waveshaper with envelope-driven bias, unless it is derived from the coupling-capacitor equations. That would be "harmonic distortion called saturation". |
| Sonic | Frequency- and history-dependent saturation ("bloom" or "sag"); a realistic H2/H3 balance vs level |
| Cost | ×3–6 the current tube cost (still small); 4× oversampling; ADAA does not apply to a stateful circuit |
| Risk | It is a new sound, so it must be an appended TUBE type, keeping the current shaper as "Classic" |
| Validation | SPICE with Koren 12AX7 parameters for the *same* circuit values: transfer curves, THD vs level and frequency, step response of the bias shift, and DC operating point |
| Decision | **ACCEPT** as a new, appended model (Reference mode). SPICE agreement would justify **Class A (simulation)**. |

## R8. Even-order harmonics and asymmetries

| Field | Assessment |
|---|---|
| Finding | H2 below −170 dBc in five filters |
| Problem (re-assessed) | The topologies are nominally symmetric (IR §4 F). The absence of H2 is **an idealisation, not a defect**. Real H2 comes from mismatch and offsets, whose magnitudes are unknown. |
| Proposed | Circuit-specific asymmetries |
| Alternatives | An optional "component tolerance / age" control (offset per stage, mismatch per diode), defaulting to 0 in Reference mode, with magnitudes taken only from SPICE Monte-Carlo with datasheet tolerances, or from measurement |
| Sonic | Subtle warmth, varying per instance |
| Cost | Negligible |
| Risk | Breaks bit-exactness if it is not off by default |
| Validation | H2 vs offset magnitude; SPICE Monte-Carlo distribution comparison |
| Decision | **MODIFY.** Retitle it as "component variation (optional)", and **POSTPONE** the magnitudes until SPICE or hardware exists. Inventing magnitudes would be **⚑ M**. |

## R9. Revision-correct K35 / MS-20

| Field | Assessment |
|---|---|
| Finding | The Mk2 (LM13600) is absent; the HP order is unverified |
| Problem | Two distinct circuits share one name. The Mk2 is an OTA design with diode-limited resonance; the Mk1 is the KORG35 thick-film IC. |
| Proposed / alternatives | Obtain Stinchcombe's MS-20 study first; settle the HP order and the diode clipper; then add the Mk2 as an appended model |
| Sonic | The documented Mk1/Mk2 differences (the Mk1's more aggressive overdrive is reported, [F]) |
| Cost / risk | Moderate; additive |
| Validation | Against the study's transfer functions; then SPICE of the LM13600 circuit, which is buildable from public schematics |
| Decision | **ACCEPT** (research first, then implementation) |

## R10. Steiner-Parker from the 1974 article

| Field | Assessment |
|---|---|
| Finding | HP node inferred; mirrored branch absent |
| Problem | No primary source. The audit's "tanh is the wrong shape" claim is **unsupported** (IR §4 G). |
| Alternatives | CGS35 (a published tribute schematic): SPICE it to obtain the HP response and the large-signal string behaviour, even without the 1974 article |
| Decision | **ACCEPT** (research, then SPICE). **Postpone** any change to the existing LP law until SPICE data exist. |

## R11. Iterated nonlinear solve as a "quality mode"

| Field | Assessment |
|---|---|
| Finding | One-sample lag affects high-fc resonance pitch (Sherman +58 cents at 8 kHz) |
| Problem | The same mechanism as R1 |
| Alternatives | Merge into R1(b): implicit evaluation in Reference mode for all secant-based models; the lagged solver remains available as "Classic" for compatibility |
| Cost | ×1.5–2 on the filter section |
| Risk | It changes the sound of existing Sets if made the default |
| Validation | Oscillation pitch vs fc at 1×/2×/4×; small-signal response unchanged |
| Decision | **MODIFY.** Merge with R1. |

## R12. Analogue noise floor and self-start

| Field | Assessment |
|---|---|
| Finding | No self-start from silence |
| Problem | An expected limitation of a deterministic model. It is audible only when the device is fed digital silence at 100 % resonance. |
| Alternatives | Inject noise at −120 dBFS at the model input, only in Reference mode and only when resonance is above the oscillation threshold. Or a one-time "kick" impulse when resonance crosses the threshold, which is cheaper but **⚑ M**, because it imitates the effect without the cause. |
| Risk | Breaks deterministic golden renders. It must be excluded from the bit-exact suites, or seeded deterministically. |
| Decision | **POSTPONE** (P2). Use deterministic seeded noise if adopted. |

## R13. Bilinear HF cramping (fitted g correction)

| Field | Assessment |
|---|---|
| Finding | Top-octave error up to 22–38 dB; peak shift up to +167 cents at fc 12 kHz, 1× |
| Problem | **The inherent behaviour of the bilinear transform**, confirmed analytically (+111.6 cents predicted vs +118.8 measured, IR §4 C) |
| Proposed | A fitted g correction for the resonance-peak position at 1× |
| Assessment | It moves *one feature* (the peak) to its analogue position while leaving the cramped skirt. It also misplaces the response elsewhere, and interacts with the nonlinear solve. **⚑ M.** |
| Alternatives | Oversampling (R2) addresses the whole response. At 96 kHz the shift is +25 cents at 12 kHz and +4 cents at 5 kHz. |
| Decision | **REJECT.** Rely on R2. |

## R14. BPF native modes from their own cores

| Field | Assessment |
|---|---|
| Finding | Band-pass "models" are constants on shared structures, with a regeneration loop that no hardware has |
| Proposal | SEM BP from `f_sem`'s own band output (Q from damping, no regeneration loop); MS-20 BP from two K35 sections |
| Sonic | A truer SEM BP (no self-oscillation, consistent with the SEM LP/HP model) and a truer MS-20 BP character |
| Risk | Additive (appended architecture values, or a "native" option) |
| Validation | BP response vs each core's analytic BP; nonlinear consistency with the LP/HP models of the same name |
| Decision | **ACCEPT** |

## R15. Sherman

| Field | Assessment |
|---|---|
| Finding | No schematic; missing documented features; invented feedback; divergence |
| Decision | (1) Stability: **ACCEPT** via R1 (quadrature limiter). (2) Expose the documented features (per-filter multimode morph, parallel mode, harmonic ratio): **ACCEPT** as **behavioural features, labelled as such**. They match the manufacturer's *feature list*, not a circuit. (3) Relabel the invented feedback as a creative control: **ACCEPT**. (4) Black-box identification: **POSTPONE** (needs a unit). |

---

## Summary

| Item | Decision | Flags |
|---|---|---|
| R1 | MODIFY (implicit evaluation; quadrature limiter for Sherman; clamp rejected as a fix) + new R1-S (containment) | ⚑ S |
| R2 | MODIFY (per-model minimum factors; 4×; TUBE 8× or ADAA) | — |
| R3 | ACCEPT (moved to P1) | — |
| R4 | POSTPONE (research first) | ⚑ M if calibrated to nominal figures |
| R5 | POSTPONE (depends on R7 and a schematic) | — |
| R6 | (3) ACCEPT; (1), (2), (4) POSTPONE | ⚑ M for (1) if tuned to panel numbers |
| R7 | ACCEPT (appended TUBE type, SPICE-validated) | — |
| R8 | MODIFY → optional component variation; magnitudes postponed | ⚑ M if magnitudes are invented |
| R9 | ACCEPT (research first) | — |
| R10 | ACCEPT (research / SPICE) | — |
| R11 | MODIFY (merged into R1) | ⚑ S |
| R12 | POSTPONE | ⚑ M for the "kick" variant |
| R13 | **REJECT** | ⚑ M |
| R14 | ACCEPT | — |
| R15 | ACCEPT (1)–(3); POSTPONE (4) | — |

**Fixes that improve measurements without improving the circuit model:**
- R1(a) clamp
- R13 g-correction
- R4 calibrated to nominal figures
- R6(1) tuned to front-panel numbers
- R8 with invented magnitudes
- R12 "kick"

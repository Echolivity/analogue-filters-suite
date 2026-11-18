# Independent audit review: Dub Filter v1.5 DSP fidelity audit

| | |
|---|---|
| Review branch | `independent-review` (from `dsp-audit` @ `0689ee8`) |
| Production baseline | DSP identical to `926a3d3` |
| Review scripts | `source/tests/review/` |
| Data | `docs/independent-review/data/` |

## Independence statement (read first)

The original audit and this review were produced by the same AI system in the same working session. This review is therefore **not organisationally independent**.

To compensate, every significant finding was handled in three ways:
1. **Re-run.** The original scripts were run again (§1).
2. **Rebuilt.** The finding was re-derived with *new* code: standalone replicas of the production equations, analytic transfer-function calculations, and new measurement conditions.
3. **Contradictions reported.** Where the new evidence disagrees with the original audit, this review says so plainly.

A reviewer from outside this session should repeat §3–§4 before relying on them.

## 1. Baseline and reproduction

| Check | Result |
|---|---|
| Production baseline | `926a3d3` is on `main`. **Correction to the audit's documents:** the audit commit `0689ee8` has parent `4e5e010` (the README merge, PR #1), not `926a3d3`. `git diff 926a3d3 4e5e010 -- source` is empty, so the DSP under audit is identical to the stated baseline. Only the stated ancestry is wrong. |
| Production DSP untouched | SHA-256 of `source/dubfilter.genexpr` = `de1bed87…a273044c`, identical to the build output. `git diff` on every tracked production file is empty. 48 + 35 + 21 golden renders are bit-exact. |
| Disclosure | Running `./build.sh` regenerates `source/build/` (git-ignored). It produced byte-identical output. It also rewrote two tracked validation files with new CPU timings. Both were restored with `git checkout`. |
| Reproduction | `source/tests/audit/run_all.sh` was re-run. **All 28 result groups are identical to the committed JSON**, except the CPU timings (expected). |

The audit's numbers are reproducible. The questions are whether they are measured correctly, and whether they are interpreted correctly.

## 2. Findings independently confirmed

| # | Original finding | Independent evidence | Verdict |
|---|---|---|---|
| 1 | Sherman diverges (about +249 dBFS) | Engine map, plus a replica of `f_sherman` (first sample within 2·10⁻¹⁴ of the engine; correlation 0.99965 over 16k samples; a small, unexplained coefficient-level drift). Root cause found; see §3. | **Confirmed defect, but mis-characterised** |
| 2 | Steiner overshoots (+30 dBFS) | Engine map and a replica. Same root-cause family. | **Confirmed defect** |
| 3 | THRUST acts on the detector only | Code (dyn.py:357–358: `vst` feeds only the mean-square detector) and bit-identical output | Confirmed |
| 4 | NEW is feed-forward, OLD is feedback | dyn.py:347 | Confirmed |
| 5 | OLD-mode ratio collapse (∞:1 measures 2:1) | **Derived analytically.** For an ideal feedback loop with this gain computer, slope = 1/(2 − 1/R). That gives 1.75:1 at R = 4 and 2:1 at R = ∞, exactly as measured. | Confirmed as correct maths. Whether the hardware compensates is unverified. |
| 6 | VCA attack floor: the 0.03 ms setting measures 0.71 ms | A standalone replica of the detector (dyn.py:179, 358–366) reproduces 0.708 ms exactly. Shortening the RMS window moves the floor (1 ms → 0.25 ms; 0.1 ms → 0.15 ms). | **Cause confirmed:** the 3 ms RMS integrator plus the log conversion |
| 7 | TUBE is a static waveshaper | Code (dyn.py:66–72): no state in the shaping path except the one-pole tone filter and the DC blocker | Confirmed |
| 8 | OPTO two-stage, history-dependent release | Original data re-examined; the mechanism was read in code (dyn.py:322–328) | Confirmed |
| 9 | No self-start from silence | Ladder at res 100 %, zero input: output exactly 0.0 for 2 s | Confirmed. An **expected limitation** of a noise-free model, not a defect. |

## 3. Root cause of the critical findings (new analysis)

### 3.1 Sherman: what actually happens

The divergence is **not** a general "high cutoff" instability, as the original audit stated. A stability map over 44.1, 48 and 96 kHz, 1× and 2×, fc from 6 to 18 kHz, and resonance 90/95/100 %, found unstable cases **only at fc ≈ fs/4**:
- 11 kHz at 44.1 kHz: +47 dBFS
- 12 kHz at 48 kHz: +249 dBFS, at both 95 % and 100 % resonance

The mechanism comes in four parts:

1. **Negative small-signal damping.** Filter 2's damping is Rt = 0.8(1−r)² − 0.08·r³⁰ (build_genexpr.py:302). For r above about 0.92 that value is negative (0.915 by direct solution): at r = 1 it is −0.08. The filter self-oscillates by design.
2. **Amplitude limiting from one sample.** The damping is limited by Rb = 1 − (1 − Rt)·f_ag(2·bb) (:107). Here `bb` is the band-pass output of the **previous sample**. It is a single instantaneous sample of an oscillating signal, not an amplitude estimate.
3. **At fc = fs/4 those samples alternate.** The oscillation sits at a quarter of the sample rate, so consecutive band samples alternate between near zero and near peak. The damping therefore alternates −0.08, 1.0, −0.08, 1.0 … (trace in `data/root_cause.json`: exactly 50 % of samples have negative damping). With g = tan(π/4) = 1, the frozen-coefficient TPT SVF has pole radius 1.084 at R = −0.08 and **0 (a dead-beat double pole) at R = 1**. The damped samples cannot absorb the energy injected by the undamped ones. This is **parametric pumping at period 2**, caused by sampling the limiter's input in phase with the oscillation.
4. **Not caused by:**
   - numerical precision: the float64 replica diverges identically
   - coefficient calculation
   - the integrator structure in itself: the TPT SVF is stable for any R > 0
   - the shape of the damping law: replacing `f_ag` with tanh still diverges, at +314 dBFS in the replica

**Hypothesis test.** Evaluate the damping from the *current* sample's band value by fixed-point iteration (replica only). The Sherman is then **bounded at −1.8 dBFS with a single iteration**, at 48, 96 and 192 kHz. Oversampling makes the problem disappear (+1.3 dBFS at 96 kHz), but only because it moves fs/4 above the maximum cutoff. That is incidental, not a correction.

**New finding: the failure persists after the cause is removed.** The test: diverge at 12 kHz, then at t = 2 s set resonance to 0 and cutoff to 1 kHz, and play a 220 Hz tone.
- Soft clip on (default): the device keeps outputting about +1.0 DC for roughly **1.5–2 s**.
- Soft clip off: it outputs **+200 dBFS** samples for about 1 s.
- In both cases it recovers by t ≈ 4 s.

The cause is the **2 Hz output DC blocker** (build_genexpr.py:730–735). It stores the divergent value and releases it slowly. So one local failure propagates into a global output fault, and with soft clip off, enormous values are passed to Live.

### 3.2 Steiner-Parker

- **The same family of cause.** The amplifier gain limit Ke = K·f_ag(0.7·K·vB_prev) and the diode-string secants both use previous-sample values (:198–200). The overshoot appears only at fc ≈ fs/4, under the same pattern: +30 dBFS at 1×.
- **The fix test.** With one fixed-point iteration (replica), the peak is **+3.8 dBFS**.
- **A separate, real issue.** Even when stable, the Steiner model's sustained self-oscillation sits at **+4.4 to +4.9 dBFS internally** at every sample rate. That is above full scale before the output soft clip, so it is a headroom-calibration matter.
- **Topology.** The Sallen-Key network with three injection points is consistent with the secondary descriptions. The mirrored branch and the HP node remain unverified (no primary source).

## 4. Findings partially confirmed or re-interpreted

| # | Original finding | What the new evidence shows | Classification |
|---|---|---|---|
| A | Aliasing at 1× (Steiner −25 dBc, Ladder −65 dBc) | **Ladder understated.** The audit measured at Comp 0, but the default is Comp 100, and Comp is applied *inside* the ladder (x·(1 + k·comp), :171). At the default, the ladder aliases at **−32.8 dBc** at the same test point, the second worst. At a typical setting (1 kHz, fc 3 kHz, res 70 %, Drive 50 %), five models are below −144 dBc at 1× and Steiner is at −110 dBc. **Aliasing is condition-dependent**: severe for bright, driven material, negligible for typical dub sweeps. | Confirmed defect for bright/driven settings; **measurement-condition error** for the ladder |
| B | Aliasing in "harsh" conditions | At 7 kHz, Drive 100 %, res 90 %, the inharmonic energy of the Ladder and the 303 does **not** fall with oversampling (−24.5 dBc at 8×). That is not aliasing: it is autonomous near-oscillation and inharmonic nonlinear dynamics. **The audit's metric (all inharmonic energy) cannot separate aliasing from intended chaos.** | **Methodology limitation** of the original audit, and of this review's metric too, unless convergence over the oversampling factor is checked |
| C | Bilinear cramping and peak shift (+119 cents at 12 kHz) | Computed analytically from the bilinear map of 1/((1+s)⁴+k): the predicted shift is **+111.6 cents**, against +118.8 measured. The engine matches the bilinear transform; the shift is a property of BLT prewarped at fc while the resonant peak sits below fc. | **Expected limitation of the integration method**, correctly measured, but not an engine error |
| D | OPTO attack "about 4× too fast" | t63 = **8.1 ms at 6 dB GR** (PR 40), 4.0 ms at 12 dB (PR 60), 2.35 ms at 18 dB (PR 80). The original used only PR 80. Attack speed depends strongly on how far the detector is overdriven. The reference "≈10 ms average" has **no documented measurement definition** (time to what fraction, at what GR). | **Partially confirmed.** Close to the reference at moderate GR, fast at heavy GR. The original overstated the case. |
| E | OPTO ratio low against a "nominal 4:1" | The local ratio rises smoothly from 1.4 to 2.75 with level, and is frequency-independent (100 Hz / 1 kHz / 5 kHz within 0.03). The reference is UA's own text, which says the ratio is "4:1 (not really)" and source-dependent. That is too weak to calibrate against. The **frequency independence** is the more relevant deviation: the T4 is described as frequency-dependent. | **Unverified assumption** in the original. The deviation from 4:1 is not established. |
| F | "Missing even harmonics" (5 of 6 filters) | The Moog ladder (differential pairs), the MS-20 (antiparallel diode pair), the OTA SVF (differential inputs) and Steiner's mirrored strings are **nominally symmetric topologies**. Their even harmonics come only from mismatch, offset or asymmetric bias, which is component variation. The original admitted "not a measured mismatch" but still listed this as a deficiency. | **Incorrect interpretation** as a defect. It is an idealisation, and belongs under P2 component variation. |
| G | Steiner diode strings "wrong shape" (tanh vs exponential diode) | In a mirrored (push–pull) arrangement of bias-current-fed diodes, the large-signal current is bounded by the bias current. That argues for a symmetric, saturating transfer, not an unbounded exponential. **This is an engineering inference, not a verified circuit fact.** Related diode-bridge cores (Korg MS-50; Rest, Parker & Werner, DAFx-17) are treated as nonlinear resistor pairs inside a Sallen-Key structure. The original's "wrong shape" claim is **unsupported**. Tanh is plausible, and the exact law is unverified. | **Unsupported interpretation** |
| H | TUBE aliasing at 2× (−30 dBc at Drive 100) | Reproduced: −30.9 dBc at the *default* Tone of 12 kHz (the audit used 20 kHz; the one-pole tone filter barely helps). At a 1 kHz input it is −73 dBc. Effective 4× gives −56 / −113 dBc; effective 8× gives −85 / −138 dBc. | Confirmed for HF content at high drive; condition-dependent |
| I | Steiner HP "6 dB/oct against its 12 dB label" | The modelled transfer function K·s(s+2)/(s²+(3−K)s+1) tends to 2K·s at low frequency, which is first order. The measurement is correct *for the model*. Whether the *hardware* does the same is unverified. | Model property confirmed; hardware comparison unverified |
| J | SEM classed B | The SEM evidence is graded [F]/[M] (forum and module descriptions), not a published circuit analysis. The schematic was not inspected. | **Over-classified** under the review's rules. See the revised scorecard. |

## 5. Findings not reproduced

None. Every number reproduces. The disagreements are about the **framing**, the **test conditions** and the **interpretation**, not the arithmetic.

## 6. Methodological weaknesses of the original audit

1. **Single test points generalised into findings.** Aliasing used one condition; OPTO attack used one GR depth; the stability scan used a coarse cutoff grid that happened to include fs/4 at 48 kHz but not at 44.1 kHz.
2. **Non-default settings.** Comp 0 changes the ladder's nonlinear operating point.
3. **The inharmonic-energy metric** does not separate aliasing from autonomous dynamics. There was no convergence check over the oversampling factor.
4. **Weak references used as calibration targets:** "4:1" and "10 ms", without measurement definitions.
5. **Symmetric-topology behaviour treated as a deficiency** (even harmonics).
6. **No root-cause analysis** of the critical findings, and no check of failure propagation (the DC-blocker persistence).
7. **A documentation inconsistency** in the stated commit ancestry (§1).
8. **Not independent** of the implementation author (this review shares that weakness; see the statement at the top).

## 7. Missing evidence (still missing after this review)

| Missing | Needed for |
|---|---|
| Hardware measurements of any modelled unit | Any Class A, and calibration of OPTO, VCA and THRUST |
| SPICE simulations of the ladder, Korg 35, Steiner, SEM and the triode stage | Class A against simulation; asymmetry magnitudes |
| Primary sources: Steiner 1974, Stinchcombe's MS-20 study, the SEM and LA-2A schematics, the THRUST network | Topology verification (K35 HP order, Steiner HP node, LA-2A side-chain tap point) |
| Programme-material listening tests | Audibility of aliasing and of the OPTO behaviour |
| Max/Live runtime tests | Integration, sidechain routing, CPU in context |

## 8. Overall confidence

| Area | Confidence | Basis |
|---|---|---|
| Measurements reproduce | **High** | Bit-identical re-run |
| Critical stability defects exist | **High** | Engine, replica, root cause and fix hypothesis all agree |
| Small-signal circuit agreement (ladder, 303) | **High** for "matches the published analysis"; **none** for "matches the hardware" | — |
| Compressor deviations | **Medium–low** | References are imprecise; the attack finding depends on GR depth |
| Classifications | **Medium** | Rules applied consistently, but A/B boundaries rest on reference quality |
| Original audit as a whole | **Sound on numbers; overstated in places; under-stated the critical defect's propagation and the ladder's aliasing** | — |

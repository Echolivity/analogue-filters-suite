# Evidence register

## Evidence types

| Code | Type | Meaning |
|---|---|---|
| **M** | Measured fact | Reproducible engine measurement |
| **D** | Derived fact | Analytic or mathematical result, checked against a measurement |
| **P** | Published fact | From an external source, with its grade (S/P/M/F) |
| **I** | Engineering interpretation | Reasoned from facts, not directly measured |
| **H** | Hypothesis | Testable claim, not yet tested |

## Where to find things

| Location | Contents |
|---|---|
| Source line numbers | `source/src/*.py` at `926a3d3`. The production files are identical on every branch. |
| Scripts | `source/tests/review/` and `source/tests/audit/` |
| JSON (audit) | `docs/dsp-audit/data/{filters,dynamics}.json` |
| JSON (review) | `docs/independent-review/data/{root_cause,verify}.json` |

## Register

| # | Conclusion | Type | Source code | Script | JSON key | External reference |
|---|---|---|---|---|---|---|
| E1 | DSP under audit is identical to `926a3d3`; the audit commit's parent is `4e5e010` | M | — | `git diff 926a3d3 4e5e010 -- source` (empty) | — | — |
| E2 | Audit results reproduce bit-identically (except CPU) | M | — | `audit/run_all.sh` + JSON diff | all | — |
| E3 | Sherman diverges only near fc = fs/4 at high resonance (+249 dBFS at 48k/12k; +47 dBFS at 44.1k/11k) | M | build_genexpr.py:102–113, 300–305 | `review/root_cause.py` | `stability_map_engine` | — |
| E4 | Sherman small-signal damping Rt goes negative for r above about 0.915 (−0.08 at r = 1) | D | :302 | (direct solution of 0.8(1−r)² = 0.08·r³⁰) | `sherman_trace.Rt_small_signal` | — |
| E5 | During divergence the damping alternates −0.08 / 1.0 on consecutive samples (50 % negative) | M | :107 | `root_cause.py` (replica trace) | `sherman_trace` | — |
| E6 | TPT SVF frozen pole radius at g = 1: 1.084 (R = −0.08), 0 (R = 1) | D | :69–74 | `root_cause.py` | `svf_frozen_pole_radius_g1` | Zavalishin, *The Art of VA Filter Design* (TPT SVF) |
| E7 | Root cause = period-2 parametric pumping from a sampled, one-sample-lagged amplitude limiter | I (from E3–E6, E8) | :105–108 | — | — | — |
| E8 | Implicit evaluation (1 fixed-point iteration) bounds Sherman (−1.8 dBFS) and Steiner (+3.8 dBFS) | M (replica) | replica of :102–113, :197–214 | `root_cause.py` | `hypotheses_replica_fc12k_res100` | — |
| E9 | Replica validity: the first sample agrees to 2·10⁻¹⁴, but the error grows to 4·10⁻⁸ by the 5th sample (correlation 0.99965 and amplitude ratio 0.9988 over 16k samples). This is a small, unexplained coefficient-level difference. Every replica conclusion was also checked on the engine itself (E3, E11). | M | — | `review/persistence.py`, `root_cause.py` | `persistence.replica_agreement`, `root_cause.replica_validation_*` | — |
| E10 | Fault persists about 1.5–2 s after removal, via the 2 Hz output DC blocker; +200 dBFS samples with soft clip off | M + I (blocker mechanism) | :729–748 | `review/persistence.py` | `persistence.softclip_0/1` | — |
| E11 | Steiner overshoot +30 dBFS at fc ≈ fs/4; sustained oscillation +4.4 to +4.9 dBFS internally | M | :197–214, :324–327 | `root_cause.py` | `stability_map_engine`, `hypotheses_*` | — |
| E12 | Ladder aliasing at default Comp 100: −32.8 dBc at 1× (C1), against −65.1 dBc at Comp 0 in the audit | M | :171 (Comp inside the ladder input) | `review/verify.py` | `OS_filters`, audit `F5_aliasing` | — |
| E13 | Minimum oversampling per model for ≤ −80 dBc at C1: SEM 1×; Sherman, K35, 303 2×; Steiner, Ladder 4× | M | — | `verify.py` | `OS_filters` | — |
| E14 | Production 2× half-band is within 0–4 dB of ideal 2× decimation | M | :599–615, 712–725 | `verify.py` | `OS_filters` (method = production) | HIIR design method (de Soras) |
| E15 | At a typical condition (C3) every model is below −110 dBc at 1× | M | — | `verify.py` | `OS_filters` | — |
| E16 | The "harsh" C2 residual in Ladder/303 does not converge with oversampling, so it is dynamics, not aliasing | M + I | — | `verify.py` | `OS_filters` | — |
| E17 | TUBE alias at default Tone 12 kHz: −30.9 dBc (Drive 100, 5 kHz, effective 2×); effective 8×: −85 dBc | M | dyn.py:146–147, 266–300 | `verify.py` | `OS_tube` | — |
| E18 | Ladder peak shift at fc 12 kHz / 44.1 kHz is inherent to BLT: +111.6 cents predicted vs +118.8 measured | D + M | :491 (prewarp) | `verify.py` | `BLT_ladder_peak_prediction`; audit `F1` | — |
| E19 | OPTO t63 attack: 8.1 ms at 6 dB GR, 4.0 ms at 12 dB, 2.35 ms at 18 dB | M | dyn.py:153–163, 321–328 | `verify.py` | `OPA_opto_attack` | LA-2A "≈10 ms average attack" (UA, [M]) |
| E20 | OPTO local ratio rises 1.4 → 2.75 with level; identical at 100 Hz / 1 kHz / 5 kHz | M | dyn.py:327–328 | `verify.py` | `OPR_opto_local_ratio_PR70` | UA: "4:1 (not really)", frequency-dependent ([M]) |
| E21 | OPTO release: 50 % in 55–75 ms; 90 % in 1.1–6.7 s, lengthening with burst length | M | dyn.py:322–326 | `audit/audit_dynamics.py` | `C3a_opto_release_memory` | UA: 60 ms then 1–15 s ([M]) |
| E22 | VCA attack floor (0.03 ms → 0.708 ms) is caused by the 3 ms RMS integrator plus the log detector | M (replica) | dyn.py:177–179, 358–366 | `verify.py` | `VCA_replica_t63_ms` | — |
| E23 | VCA OLD-mode slope = 1/(2 − 1/R), so 1.75:1 at R = 4 and 2:1 at R = ∞, matching measurement | D + M | dyn.py:347, 365–366 | — | audit `C1_static_curves` | API 2500 manual: OLD = feedback ([M]) |
| E24 | THRUST is in the detector only (bit-identical audio) | M | dyn.py:357–358 | `audit_dynamics.py` | `C4a_thrust_detector_only` | API: filter before the RMS detector ([M]) |
| E25 | TUBE is static: THD frequency-independent; identical before/after burst | M + code | dyn.py:66–72 | `audit_dynamics.py` | `T3`, `T4` | — |
| E26 | Five filters have no even harmonics; the topologies are nominally symmetric | M + I | the models' tanh/secant elements | `audit_filters.py` | `F4_thd_vs_level_drive0` | Huovilainen DAFx-04 (ladder); topology descriptions in the catalogue |
| E27 | Bias-fed mirrored diode strings saturate at the bias current, so a symmetric saturating law is plausible | I | :198–199 | — | — | KVR (u-he) topology description ([F]); Rest, Parker & Werner DAFx-17 ([P], related diode-bridge core) |
| E28 | Steiner HP 6 dB/oct skirt follows from the modelled node K·s(s+2)/(…) | D + M | :192, :197–214 | `audit_filters.py` | `F7_skirt_slopes` | Node not verified ([N] for the 1974 article) |
| E29 | SEM evidence is [F]/[M] only, so SEM is not B under the review's rule | I | :224–233 | — | — | Catalogue entries for the SEM ([F]/[M]) |
| E30 | No self-start from silence | M | all models (no noise source) | `verify.py` | `NSE_*` | — |
| E31 | Routing display equals DSP in all 96 states | M | routing.py:42–66; `df_routing.js` | `tests/ui_tests.py` | — | — |
| E32 | Other secant models (K35, Ladder, SEM, 303, BPF) have the same lagged pattern; none diverged on the map, but they have not been swept at 1-cent resolution around fs/4 | H | :124, :157–161, :226–227, :247–250; bpf.py:57–58, 84–95 | (planned: T0) | — | — |
| E33 | ADAA could replace 8× for the static TUBE shaper at lower cost | H | dyn.py:66–72 | (planned: P0-4 evaluation) | — | ADAA literature (Parker et al., antiderivative anti-aliasing) — not opened in this review |
| E34 | Hardware fidelity of any model | none | — | — | — | **No hardware evidence exists**; no claim is made |

## Added 2026-11-18: LA-2A operating manual [P]

See [LA2A_MANUAL_CHECK.md](LA2A_MANUAL_CHECK.md). `tests/review/la2a_manual.py` makes the measurements.

| ID | Finding | Class | Verdict |
|---|---|---|---|
| E35 | LIMIT: output rises 2.1 dB over the top 20 dB. The manual says < 1 dB. | P vs M | Deviates |
| E36 | COMP local ratio 1.7 → 2.8:1. The manual says about 3:1 (100 % → 30 %, about 2.6:1). | P vs M | Conforms |
| E37 | Emphasis at maximum: +8.2 to +8.9 dB more GR at 15 kHz (LIMIT). The manual says about +10 dB. | P vs M | Slightly short |
| E38 | THD at ≥ 30 dB GR: 0.018 % at 1 kHz, 1.8 % at 100 Hz. The manual says < 0.5 %, frequency not stated. | P vs M | Conforms at 1 kHz |
| E39 | Side-chain: the manual's text says input-fed. OPTO is output-fed (feedback). | P vs code | Deviates (schematic needed) |
| E40 | Attack: the manual says 10 µs, undefined. OPTO measures 2.35–8.1 ms t63. | P vs M | Conflicts; not used |
| E41 | Schematic C-10953 rev C: R2 is fed from the R6/R7 node, so the side-chain is feedback. SW3 shorts R7 (COMP). | P | Resolves E39; v1.6 LIMIT implements it |
| E42 | R37 ∥ C12 network: max = LF side-chain cut; 15 kHz +12 dB vs 500 Hz, +8 dB vs 1 kHz | P (computed) | Implemented; conforms to E37's manual figure |
| E43 | Figure 1 (3-66 manual, pre-switch): output +3.4/+5.1/+5.6/+5.7 dB at 5/10/15/30 dB above breakaway | P | v1.6 LIMIT: 2.5/3.9/5.7/7.5 (PR 100). Partial match. |
| E44 | UREI 1992 notice: the "10 µs" attack "should have been in milliseconds" | P | Supports OPTO's ms attack; supersedes E40's conflict |
| E45 | R37 position: 3-66 text says ahead of R2; drawing rev C shows it after V3 | P vs P | The model follows the drawing; the two agree above 500 Hz |
| E46 | Cell exponent: 2 fits the addendum's COMP; 3.5 fits Figure 1, which the addendum gives as the LIMIT curve; no single value fits both | M (static solve) | The user chose per-mode exponents: COMP 2, LIMIT 3.5 |
| E47 | Lawrence 1964: release about 2 s after 5–6 dB, 5–10 s after 20–30 dB, 50 % < 1 s; no cell transfer data | P | Consistent with E21 |

## Added 2026-11-18: Stinchcombe MS-10/MS-20 study [S]

See [MS20_STUDY_CHECK.md](MS20_STUDY_CHECK.md).

| ID | Finding | Class | Verdict |
|---|---|---|---|
| E48 | Korg35 low-pass denominator s² + (7/3 − k)s + 1; OTA s² + (2 − k)s + 1 (re-derived) | S + derivation | Model matches the OTA form within 0.23 dB below 3 kHz |
| E49 | Both MS-20 high-pass variants are 6 dB/oct: s(s + 4/3) and s(s + 1) numerators | S + derivation | Model is 12 dB/oct; deviates |
| E50 | Korg35 diodes are in the forward path (×58, ~0.5 V knee); OTA diodes are in the feedback path (×4, ~2 V) | S | Model's clipper is feedback-path, so it is Mk2-like; Mk1 is missing |
| E51 | Korg35 resonance is asymmetric (SPICE only) | S (unverified) | Not modelled |

## Added 2026-11-19: Steiner, Electronic Design 1974 [P]

See [STEINER_1974_CHECK.md](STEINER_1974_CHECK.md).

| ID | Finding | Class | Verdict |
|---|---|---|---|
| E52 | LP K/(s² + (3 − K)s + 1), HP K·s(s + 2)/(…), BP K·s/(…); the HP node is the bottom of C2 | P + derivation | Model conforms |
| E53 | The article's plots fit passband = K/48 and Q = 1/(3 − K) within about 1 dB | P | Conforms |
| E54 | The diode string is one forward-biased string fed in mirror from both ends; net law i = 2I·sinh(v/V′); even orders cancel | P + derivation | Model uses tanh: wrong direction (cutoff falls with level instead of rising) |

## Added 2026-11-19: Oberheim SEM-1A schematic and manual [P]

See [SEM_SCHEMATIC_CHECK.md](SEM_SCHEMATIC_CHECK.md).

| ID | Finding | Class | Verdict |
|---|---|---|---|
| E55 | SVF with CA3080 integrators; HP↔LP notch crossfade; BP on a switch | P | Conforms |
| E56 | Linear damping via the RES pot and 33k: 2ζ ≈ 3.03·w (Q 0.33 → unbounded) | P | The model's 20^(−res) law (Q 0.5–10) differs |
| E57 | Diode limiter (47k/10k, D11/D12, 100k) adds damping above about 2.6 V BP | P | Missing in the model |
| E58 | Input path is a linear op-amp summer (gain 0.45) | P | The model's 2·tanh(x/2) has no origin |

## Added 2026-11-19: Sherman Filterbank 2 manual [P], VCF-4 and Shermanik write-ups [S]

See [SHERMAN_MANUAL_CHECK.md](SHERMAN_MANUAL_CHECK.md).

| ID | Finding | Class | Verdict |
|---|---|---|---|
| E59 | Two 12 dB filters; series = 24 dB; filter 2 has more resonance | P | Conforms |
| E60 | Lp/Bp/Hp balance plus the correction knob (−Bp … −Bp+Lp+Hp); harmonics ÷1–16; continuous PAR↔SER | P | Missing in the model |
| E61 | Clock noise and the low-frequency "eee" (clocked / switched-capacitor filters likely) | P (behaviour) | Not modelled |
| E62 | Overdrive "can push away the resonance peaks"; Limit switch | P | Not modelled |
| E63 | No output-to-input feedback path described | P | The model's FEEDBACK is undocumented |


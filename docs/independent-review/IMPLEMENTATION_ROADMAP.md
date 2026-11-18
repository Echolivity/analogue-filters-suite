# Implementation roadmap (independent review)

**For approval. Nothing here is implemented.** No completion dates are given. Complexity is graded Low, Medium or High.

**Rules for every task:**
- The task must ship with seven things:
  1. a mathematical explanation
  2. a circuit reference or a documented approximation
  3. an isolated implementation
  4. a reproducible test
  5. a before/after measurement
  6. a regression test
  7. a documented sonic consequence
- New behaviour is added as appended parameters or model entries.
- Existing Sets keep their sound unless the owner approves a re-baseline.

## Dependency graph

```
T0 harness extensions ─┬─► P0-1 implicit solve ──► P0-2 Sherman limiter
                       ├─► P0-3 failure containment
                       ├─► P0-4 OS cascade (4×/8×) ──► P0-5 per-model minimum ──► P1-6 Mode layer
                       └─► P0-6 headroom calibration
P1-6 Mode layer ──► P1-1, P1-3, P1-4, P2-*      R-1..R-4 research ──► P1-2, P1-3, P2-1, P2-3
P2-1 triode (SPICE) ──► P2-2 LA-2A audio path
```

## T0: test infrastructure (prerequisite)

| | |
|---|---|
| **Dependencies** | — |
| **Files affected** | `source/tests/harness.c`; new `source/tests/review/*` |
| **Approach** | Add to the harness: an fs/4 stability sweep; an aliasing metric with an oversampling-convergence check; GR-depth sweeps; a fault-propagation test; a CPU per factor |
| **Acceptance** | Reproduces every number in `data/root_cause.json` and `data/verify.json` |
| **Regression risk** | None (tests only) |
| **Complexity** | Low |
| **Coverage** | Self-tests against the committed JSON |

## P0: stability and correctness

| ID | Task | Dependencies | Files | Approach | Acceptance criteria | Regression risk | Complexity | Test coverage |
|---|---|---|---|---|---|---|---|---|
| P0-1 | Implicit evaluation of secant nonlinearities | T0 | `src/build_genexpr.py` (`f_sherman`, `f_steiner`, then the other secant models), `src/bpf.py` | One fixed-point or Newton step on the current-sample operating point. Classic solver retained. | No fs/4 anomaly in any model (fc grid at 1-cent resolution around fs/4, res 0–100 %, 44.1/48/96/192 kHz, 1×/2×/4×). Small-signal response unchanged within 0.01 dB. Classic path bit-exact with today's golden renders. | High (sound change on the implicit path) | Medium | Stability map; small-signal; oscillation pitch and level; golden (Classic) |
| P0-2 | Sherman phase-independent limiter | P0-1 | `f_sherman` | Limiter driven by SVF quadrature magnitude or state energy | Bounded < +6 dBFS everywhere. Oscillation level flat within 2 dB across fc. | Medium (Sherman character) | Low | Stability map; oscillation level vs fc |
| P0-3 | Failure containment | T0 | `src/build_genexpr.py` (output stage, per-model state) | Non-finite / >10⁶ detection, reset, flag | Fault ends → output clean within 10 ms (today 1.5–2 s). Zero activations across the full suite. | Low | Low | Fault-propagation test; full suite activation count |
| P0-4 | Oversampling cascade 4× / 8× | T0 | `src/build_genexpr.py`, `tools/hiir_design.py`, `src/dyn.py` (TUBE) | Repeat the existing half-band stages; select the factor per sub-section | Measured alias per factor within 3 dB of ideal decimation (as for 2× today). CPU per factor documented. | Medium (phase; CPU) | Medium | OS study C1/C2/C3 with convergence; CPU |
| P0-5 | Per-model minimum factor | P0-4 | `src/build_genexpr.py` | Effective factor = max(user setting, model minimum) in Reference mode | Each model ≤ −80 dBc at C1 in Reference mode | Low | Low | OS study; mode switch |
| P0-6 | Internal headroom calibration | T0 | Model coefficient blocks | Nominal internal level; ceiling for self-oscillation and full drive | All models ≤ +6 dBFS internal at res 100 % and Drive 100 % (Reference) | Medium (level change) | Medium | Level sweeps per model |

## P1: core circuit fidelity

| ID | Task | Dependencies | Files | Approach | Acceptance | Risk | Complexity | Coverage |
|---|---|---|---|---|---|---|---|---|
| P1-1 | BPF native modes from their own cores (R14) | P1-6 | `src/bpf.py` | SEM BP from `f_sem`'s band output; MS-20 BP from two K35 sections | Small signal = each core's analytic BP within 0.1 dB; consistent nonlinear behaviour with the LP/HP model of the same name | Low (additive) | Medium | BP response; nonlinear consistency |
| P1-2 | K35 revision work (R9) | R-2 | `src/build_genexpr.py` (new model entry) | Per Stinchcombe's study: correct the HP order, diode clipper, Mk2 LM13600 model | Match the study's transfer functions; Mk2 SPICE match (small-signal and THD vs level) | Low (appended) | High | SPICE comparison; regression on Mk1 |
| P1-3 | OPTO mechanisms (R4, research-gated) | R-3, P1-6 | `src/dyn.py` | EL threshold law and CdS resistance law, with literature or measured parameters only | Attack, release and frequency dependence within the tolerance of the reference data | Medium | Medium | Attack at 3–5 GR depths × 3 frequencies; memory; static curves |
| P1-4 | VCA link filter (R6-3) | P1-6 | `src/dyn.py`, `device/build_device.py` (appended UI) | HP/LP/BP on the link path | Detector link response matches the design; stereo GR vs frequency behaves as specified | Low | Low | Detector response; stereo tests |
| P1-5 | Idle CPU (R3) | T0 | `src/build_genexpr.py` | Block-rate control when settled; section gating | All golden renders bit-exact; idle CPU reduced (target ≥ 50 %) | Medium (subtle smoothing) | Medium | Golden; clicks; CPU |
| P1-6 | Reference / Creative mode layer | P0-1, P0-5 | Generator, UI builder | One appended parameter; existing Sets load as Creative | Creative = today's output bit-exact; Reference applies the policy | Medium | Medium | Golden (Creative); mode tests; compatibility |

## P2: analogue character

| ID | Task | Dependencies | Files | Approach | Acceptance | Risk | Complexity | Coverage |
|---|---|---|---|---|---|---|---|---|
| P2-1 | Triode TUBE type (R7) | P0-4, R-4 | `src/dyn.py` (new type) | Koren 12AX7 law, load line, cathode bypass, coupling capacitor + grid leak, Miller; 4× minimum | Against SPICE of the same circuit: transfer within 0.5 dB; THD vs level and frequency within 2 dB; bias-shift recovery time within 10 % | Low (appended) | High | SPICE suite; aliasing; CPU |
| P2-2 | LA-2A audio-path stages (R5) | P2-1, R-3 | `src/dyn.py` | 12AX7 / 12BH7 stages at schematic values. Transformers only with data. | SPICE match | Low (optional) | High | SPICE; THD |
| P2-3 | Component variation (R8) | SPICE Monte-Carlo | Models | Optional offsets and mismatch with SPICE-derived spreads | H2 distribution within the SPICE spread | Low (off by default) | Medium | Monte-Carlo comparison |
| P2-4 | Noise floor / self-start (R12) | P1-6 | Models | Seeded −120 dBFS noise, Reference mode only | Self-start from silence; deterministic renders | Medium (determinism) | Low | Self-start; seeded golden |
| P2-5 | Sherman behavioural features (R15-2/3) | P0-2 | `f_sherman`, UI | Multimode morph per filter, parallel mode, harmonic ratio; relabel the feedback | Matches the manufacturer's feature list; labelled behavioural | Low (appended) | Medium | Feature tests |

## P3: advanced validation

| ID | Task | Dependencies | Approach | Acceptance |
|---|---|---|---|---|
| P3-1 | SPICE comparison programme | R-1..R-4 | Ladder, 303, K35 Mk2, Steiner (CGS35), SEM (schematic), triode | Documented deviation per model; candidates for Class A (simulation) |
| P3-2 | Hardware comparison | A unit | Procedure in `docs/dsp-audit/DSP_VALIDATION_RESULTS.md` | Per-model deviation tables; Class A (hardware) where met |
| P3-3 | Programme-material listening | P0, P1 | Blind ABX: 1× vs minimum factor; Classic vs implicit; OPTO variants | Audibility thresholds documented |
| P3-4 | Max for Live integration | — | The checklists in `docs/VALIDATION.md` and `docs/UI_VALIDATION.md`; sidechain routing; CPU in Live | All pass in Live 12 |

## Research tasks (gate several items)

| ID | Task | Unblocks |
|---|---|---|
| R-1 | Obtain Steiner 1974 / CGS35 schematic; SPICE it | Steiner HP class; P3-1 |
| R-2 | Obtain Stinchcombe's MS-20 study | P1-2 |
| R-3 | Obtain the LA-2A schematic and published T4 measurements | P1-3, P2-2 |
| R-4 | Choose triode parameters (Koren 12AX7) and a test circuit | P2-1 |
| R-5 | THRUST network (patent) and API 2500 OLD-mode behaviour | R6-1/2/4 |

## Explicitly not planned

| Item | Reason |
|---|---|
| R13 fitted g correction | Rejected: measurement-only improvement |
| A state clamp as the stability fix | Rejected. Containment (P0-3) only. |
| Calibrating OPTO and VCA to front-panel or marketing figures without measurement data | Rejected |

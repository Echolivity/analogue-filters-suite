# DSP architecture recommendations

The current architecture can support the intended models. **No wholesale re-architecture is needed.** Most models can be corrected independently.

Three changes are architectural, because they cut across models:
1. A per-model oversampling policy.
2. An implicit-evaluation option for the nonlinear solves.
3. A Reference / Creative mode layer.

A fourth item, failure containment, is cheap infrastructure.

## 1. Assessment of the current architecture

| Aspect | Finding | Evidence | Action needed |
|---|---|---|---|
| Internal precision | Float64 throughout the gen~ code. The float64 replicas reproduce the engine's divergence identically, so precision is not a factor in any finding. | `rc`, IR §3.1 | None |
| Integrators | TPT/trapezoidal, prewarped at fc. Stable for any positive damping. Small signal matches the published H(s) at low and mid frequencies. Top-octave cramping is inherent to BLT (predicted analytically, +111.6 cents at 12 kHz / 44.1 kHz). | IR §4 C | Address through oversampling, not coefficient fitting (R13 rejected) |
| Nonlinear feedback loops | Secant linearisation using **previous-sample** operating points: a semi-implicit scheme. Accurate when the signal changes little per sample. **Fails at fc ≈ fs/4** when a coefficient is driven by an *instantaneous sample* of an oscillation. | IR §3 | §2.2 |
| Oversampling | One global 2× polyphase IIR half-band for the filter section (off by default), plus a fixed 2× in the TUBE. The half-band performs within 0–4 dB of *ideal* 2× decimation in the aliasing study, so the design is sound but the factor is too low for some models. | `vf.OS_filters` | §2.1 |
| Decimation / reconstruction | The IIR adds non-linear phase but no latency; that is acceptable for an insert effect, and documented | audit F1 | Document per factor |
| Parameter smoothing | One-pole, per sample: cutoff in the log domain over 6 ms, others over 15 ms. Model, slope, order and routing changes crossfade over 25 ms or duck over 4 ms. Abrupt 10 ms cutoff steps stayed finite in all 22 cases. | audit F6 | Keep. R3 may move settled smoothing to block rate **only if bit-exact**. |
| Denormals | `fixdenorm` on every recursive state. Long-run and denormal tests pass (existing `t_denormal_dc`). | build_genexpr.py; validate.py | None |
| DC offset | 2 Hz output blocker, 8 Hz tube blocker. **The output blocker propagates faults for about 1.5–2 s** (IR §3.1). | `rc.persistence_*` | §2.3 |
| Internal headroom | Float, so no clipping until the output soft clip (> \|0.7\|). Models differ widely in internal level: Steiner self-oscillation about +4.5 dBFS; Ladder HP transients +22 dBFS under abrupt modulation. The dynamics chain then receives these levels. | `rc`, audit F6 | §2.4 |
| Stability margins | Unstable region confined to fc ≈ fs/4 at high resonance (Sherman, Steiner) | `rc.stability_map_engine` | §2.2 |
| CPU | 760 ns/sample idle; 1709 ns with everything on (offline C) | audit P1 | R3 (P1) |
| Chain ordering | Filters → dynamics (6 orders) → gate → output. Clean, state-copied 25 ms reorders. Fixed placement of filters before dynamics is a *product* constraint, not a defect. | dyn.py:383–429 | Optional: allow TUBE pre-filter in Creative mode |
| Sidechain routing | INT / CHAIN / EXT per detector; EXT via `plugin~ 3 4`. Untested in Live. | dyn.py:262 | P3 integration test |
| Stereo | Identical L/R gives bit-identical outputs; zero crosstalk; link implemented per module | validate.py stereo tests; audit C5 | None |

## 2. Recommendations

### 2.1 Per-model oversampling policy

**Do not force one factor on every model.** The measured minimum factors to reach −80 dBc in the bright test C1 (5 kHz, −6 dBFS, Drive 60 %, res 50 %, fc 16 kHz) at the *default* Comp 100:

| Model | 1× | 2× | 4× | 8× | Recommended minimum |
|---|---|---|---|---|---|
| SEM | −89.0 | −150.0 | −153.9 | −157.4 | **1×** |
| Sherman | −38.7 | −87.9 | −154.6 | −158.3 | **2×** |
| K35 / MS-20 | −50.3 | −116.2 | −156.0 | −160.7 | **2×** |
| TB-303 | −52.0 | −118.6 | −154.9 | −158.5 | **2×** |
| Steiner-Parker | −25.3 | −74.4 | −155.1 | −159.9 | **4×** |
| Ladder (Comp 100) | −32.8 | −61.2 | −115.7 | −160.1 | **4×** |
| TUBE (effective factor), Drive 60 % / 100 % at 5 kHz | — | −77 / −31 | −105 / −56 | −130 / −85 | **4×; 8× (or ADAA) above about 80 % drive** |

All values are in dBc. Source: `vf.OS_filters`, `vf.OS_tube`; plot: `plots/os_factor_study.png`.

At the typical condition C3 (1 kHz, fc 3 kHz), every model is below −110 dBc at 1×. So **the policy should guarantee a minimum per model, and leave higher factors to the user.** It should not raise CPU for everyone.

**Caveat (methodology).** In the harsh condition C2, the Ladder and the 303 do not converge (−24.5 dBc at 8×). That residual is inharmonic nonlinear dynamics, not aliasing. Any acceptance test must check **convergence across factors** before attributing residual to aliasing.

**Implementation route.**
- A cascade of the existing half-band design: 2× → 4× → 8× by repeating the up/down stages.
- Run the models inside the highest active factor.
- Select the factor per active model: the maximum of the user setting and the model minimum (Reference mode only).
- Cost: about ×2 on the filter section per doubling.

### 2.2 Nonlinear solve: implicit evaluation

**Recommendation.** Add an implicit-evaluation path to the shared solve pattern:
- Evaluate the nonlinear coefficients at the current-sample estimate, using one fixed-point or Newton step.
- Make it the default in Reference mode.
- Keep the current lagged solve as "Classic" for compatibility.

**Evidence.** One iteration bounds both failures in the replicas: Sherman −1.8 dBFS and Steiner +3.8 dBFS at 48 kHz (`rc.hypotheses_*`).

**Generalisation.** The same pattern exists in K35 (K from y_prev), Ladder (Ti from y_prev), SEM, 303 and the BPF. **Every secant model should be scanned at fs/4**, not only the two that failed.

**For the Sherman only.** It has no circuit reference to preserve, so additionally drive its limiter from a phase-independent amplitude (quadrature magnitude or state energy). That removes the sampling-phase sensitivity outright.

### 2.3 Failure containment (defence in depth, not a fix)

Detect non-finite values or |state| > 10⁶ per model. On detection:
- reset that model's state
- reset the output DC blocker
- raise a debug flag

This prevents a local fault from becoming 1.5–2 s of full-scale DC. **It must not engage in normal operation.** Test: the full validation suite shows zero activations.

### 2.4 Headroom calibration

Define a nominal internal level: for example, 0 dBFS = the analogue nominal level of each reference circuit, or a consistent −12 dBFS operating point.

Then calibrate each model's drive and output scaling so that **self-oscillation and full drive stay within a stated ceiling** (for example +6 dBFS) before the soft clip. Currently:
- Steiner oscillates at +4.5 dBFS internally
- the Ladder HP can transient to +22 dBFS

This matters because the dynamics chain responds to absolute level.

### 2.5 Reference / Creative mode layer

**The parameter.** Add **one appended parameter** "Mode": Reference / Creative.
- **Existing Sets load as Creative.** That is today's behaviour, so compatibility is preserved.
- New instances default to an owner-chosen value.

| Aspect | Reference | Creative |
|---|---|---|
| Solver | Implicit (§2.2) | User choice (Classic or implicit) |
| Oversampling | ≥ the model minimum (§2.1) | User choice (1×–8×) |
| Ranges | Each model's documented envelope (e.g. SEM no self-oscillation; resonance mapping as derived) | Extended cutoff and resonance |
| Models available | Circuit-derived models only (Class ≥ C), each labelled with its class | All, including Ladder HP pole-mix, slope extensions, Sherman feedback, derived BPF pairings |
| Character controls | Physically meaningful controls only | Stage Sat, Sherman feedback, Comp, OPEN zones |
| Component variation (R8) | Off (or SPICE-derived tolerance spread) | Free |

**Rule: creative extensions never alter Reference-mode output.** Each extension is a separate code path or parameter, labelled in the UI as "creative" or "derived".

### 2.6 Signal routing

The routing is correct, and it is verified against the display. Optional Creative-mode additions:
- TUBE before the filters
- a filter after the dynamics

These are appended parameters and do not affect Reference mode.

## 3. What does not need changing

- The TPT/ZDF framework
- The model registry and generator pattern
- The state-copied reorder lanes
- The routing sums
- The half-band design: it is reusable for higher factors
- Parameter smoothing
- Denormal handling

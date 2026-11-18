# DSP architecture

## Overview

```
plugin~ ──► gen~ (one codebox, ~2,000 lines of generated GenExpr) ──► plugout~
              ▲
   live.* UI ─┴─ prepend <param> ─► gen~ Params (20)
```

Inside gen~, per sample:

```
in L/R ─► [2x upsampler]¹ ─► ┌──────────── per subsample ────────────┐ ─► [2x downsampler]¹ ─► DC block (2 Hz)
                             │ [BPF if PRE] ─► order LP>HP: LPF ─► HPF │      ─► Output gain ─► Soft clip ─► duck ─► out
                             │             or HP>LP: HPF ─► LPF        │
                             │ ─► [BPF if POST, default]               │
                             └─────────────────────────────────────────┘
¹ only when Oversampling = 2x
```

Each **stage**, per channel:

```
x ─► ×Drive ─► model A ─┐                         ┌─► tap 0 (native) ──┐
                         ├─ 25 ms model crossfade ─┤                     ├─ smoothed tap weights ─► ×makeup ─┐
      (model B, only   ─┘   (12/24 tap mix for     └─► EXT1 ─► EXT2 ─► EXT3 ┘  (36/48 dB etc.)              │
       while fading)          Sherman / Ladder)                                                            ▼
x ─────────────────────────────────────────────────────────────── dry ──────────► dry + wet·(processed − dry)
                                                          wet = On (10 ms fade) × OPEN-zone factor
```

## Design decisions

**Zero-delay-feedback (TPT) filters throughout.** Every model uses topology-preserving transforms (trapezoidal integration with the feedback loop solved instantaneously), not biquads. This keeps the analogue prototype's response exactly at the prewarped cutoff, allows modulation at audio rate without the instability that time-varying biquads show, and makes the resonance law and self-oscillation point match the continuous-time analysis.

**Nonlinearities without iteration.** Each nonlinear model is solved in closed form every sample:
- *Secant ("Mystran") linearisation of every circuit nonlinearity* (all models). Each tanh/diode/OTA characteristic f(v) is replaced for the current sample by its secant gain f(v)/v from the previous sample, which keeps the zero-delay loop linear and solvable in closed form. This covers the ladder's five differential pairs, the 303's input pair and four diode rungs, the SEM's two OTAs, and the Steiner's two diode strings and amplifier.
- *Saturation after the linear solve* where the circuit's nonlinearity sits at a single node (the K35 loop, the 303 input pair). At small signals every model is exactly its circuit's linear filter, which VALIDATION.md checks to within 0.05 dB. At large levels the secant gains fall, bounding self-oscillation.

There are no Newton iterations, so CPU cost is fixed and there are no convergence failures.

**Resonance laws.** Each model maps 0–100 % to its own feedback quantity (SVF damping R, ladder k, K35 K, diode k), with a steep curve near the top so that "resonance becomes increasingly pronounced at higher settings". Self-oscillation begins at about 92–97 % of travel.

**Smoothing.** Every control is smoothed per sample inside gen~, so Live's block-rate parameter updates and 7-bit MIDI steps arrive as continuous trajectories.

| Control | Smoothing |
|---|---|
| Cutoff | one-pole on log₂(Hz), τ = 6 ms (sweeps stay musically even across octaves) |
| Resonance, Drive, Comp, Character, Output | one-pole, τ = 15 ms |
| Stage On, slope tap weights | one-pole, τ = 10 ms |
| Model change | linear crossfade, 25 ms; the outgoing model's state is zeroed afterwards |
| Stage order, oversampling | output duck: 4 ms out, switch, 4 ms in |

Filter coefficients (including `tan()` prewarping) are recomputed every sample from the smoothed values and the current `samplerate`. This is why sample-rate changes need no special handling.

**State discipline.** All filter state lives in top-level `History` objects. They are read into locals at the top of the sample, processed through pure functions (state in → state out, multiple return values), and written back once at the end. The code's behaviour therefore cannot depend on gen's History read/write ordering, and running the same model twice per sample for 2x oversampling is just two function calls on the locals. The offline checker enforces this (no History read after write).

**Denormals and DC.** Every state write goes through `fixdenorm()`. Decay tails reach exactly zero (validated after 10 s of silence), and silence costs no more CPU than signal. The asymmetric models (Sherman, Steiner) generate DC, which a 2 Hz first-order DC blocker removes at the output (−0.04 dB at 20 Hz). A NaN guard (`q == q`) protects the output.

**CPU.** Only active models are computed. A stage that is off, or parked in its OPEN zone, skips all model code. Extension sections run only when the selected slope needs them. See VALIDATION.md for figures.

**Bypass.** Live's device on/off switch bypasses the device at Live's level. On re-activation the filters resume from their last state, or from zero if they were inactive. Because every control is smoothed and model state is reset on deactivation, no stale-coefficient transients are possible. This is not yet verified inside Live (see the manual checklist in VALIDATION.md).

## Files

| File | Role |
|---|---|
| `source/src/build_genexpr.py` | Generator. Contains the GenExpr function library, the model registry and the main-body generator. **Edit this, not the .genexpr.** |
| `source/dubfilter.genexpr` | Generated engine (embedded in the device's gen~ codebox). |
| `source/tools/hiir_design.py` | Designs and verifies the half-band oversampling coefficients. |
| `source/tools/genexpr2c.py` | GenExpr → C transpiler and static checker used for testing. |
| `source/device/build_device.py` | Builds `DubFilter.maxpat` and `DubFilter.amxd` (UI, parameters, wiring). |
| `source/device/preview.py` | Approximate PNG render of the panel layout. |
| `source/tests/` | Harness, wrapper, validation suite, report generator. |
| `build.sh` | Regenerates everything and reruns validation. |

## v1.2: band-pass engine

The BPF lives in its own module (`source/src/bpf.py`). The LPF/HPF generator received only append-only hooks:
- parameters appended after the v1.1 parameters
- BPF state registered after all v1.1 state
- a controls block
- one extra term in the stage-order/oversampling duck condition (position changes)
- two insertion points (PRE before the chain, POST after it)
- History write-backs

Each insertion point is wrapped in `if (b_run)`, so with the BPF off no LPF/HPF variable is touched. The golden test confirms the output is bit-identical.

Model and architecture changes use two **configuration slots** (A/B). A new configuration goes into the idle slot, which is reset and crossfaded in over 25 ms. Only the running slot(s) are computed. The regeneration loop (SVF, CASCADE) is solved with zero delay: every section is written in affine form (output = a·x + b for the current sample, from its secant gains), so the loop gain is known before the states are committed.

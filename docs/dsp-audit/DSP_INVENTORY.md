# DSP inventory

Audit of Dub Filter v1.5 (`main` at 926a3d3). Phase 1: what exists. Phase 3 (`DSP_IMPLEMENTATION_AUDIT.md`) covers what each part does.

## Where the DSP lives

The whole audio engine is a single gen~ codebox: `source/build/dubfilter.genexpr`, 6,544 lines.

That file is **generated**, so it is never edited by hand. All citations below point at the generator sources, because they are the code a developer actually edits:

| File | Lines | Contents |
|---|---|---|
| `source/src/build_genexpr.py` | 805 | LPF/HPF models, shared primitives, slope extensions, oversampling, stage order, output stage |
| `source/src/bpf.py` | 317 | Band-pass engine: 5 nonlinearity profiles × 3 architectures, A/B crossfade slots |
| `source/src/dyn.py` | 477 | Tube, opto, VCA, gate, key listen, reorder lanes |
| `source/src/routing.py` | 66 | SERIES / PARALLEL / HYBRID filter routing |
| `source/tools/hiir_design.py` | 92 | Design of the polyphase half-band oversampling coefficients |

The device patch is built by `source/device/build_device.py`. It contains **no DSP**: only UI, parameter wiring, meters and sidechain input routing.

**Third-party DSP libraries: none.** The half-band coefficients are computed by `tools/hiir_design.py`, an implementation of the elliptic half-band design method used by Laurent de Soras' HIIR library. No HIIR code is included. There are no other external DSP dependencies, either in Max or in Python.

## Primitives (shared building blocks)

| Primitive | Location | What it is |
|---|---|---|
| `f_op` | build_genexpr.py:30 | TPT one-pole low-pass (trapezoidal, prewarped by the caller) |
| `f_tg` | :37 | Secant gain tanh(v)/v. The linearisation used by every "nonlinear" filter. |
| `f_dg` | :48 | Secant of an asymmetric tanh (b = 0.35). **Defined but unused** by any model. |
| `f_ag` | :58 | Secant of the algebraic sigmoid v/√(1+v²) |
| `f_asym` | :63 | Asymmetric soft clip (tanh with offset 0.35, idle point removed) |
| `f_svf` | :69 | Linear TPT state-variable filter (Zavalishin) |
| `f_tri4` | :78 | 4×4 tridiagonal solver (Thomas algorithm), used by the diode ladder |
| `f_ap5` | :279 | Chain of five first-order all-passes. Two in parallel form the 2× polyphase half-band. |
| `f_bsat`, `f_bsva`, `f_bsvs`, `f_bmm`, `f_bmag` | bpf.py:48–118 | BPF element secant, affine SVF section, ladder core with pole mixing, analogue magnitude helper |
| `f_tsh`, `f_tube` | dyn.py:66–72 | Asymmetric static shaper; biased version with the idle point removed |
| `f_gc` | dyn.py:74 | Gain computer: threshold, ratio and quadratic knee, all in dB |

## Every distinct DSP model

There are 28 distinct processing models, plus the routing and utility blocks listed further down. "Selectable as" shows how the user reaches each one.

### Low-pass and high-pass stages: 11 model/stage combinations

| # | Model | LPF | HPF | Function | Selectable as |
|---|---|---|---|---|---|
| 1–2 | Sherman Filterbank-inspired | ✓ | ✓ | `f_sherman` :102 | Model 01 |
| 3 | Korg 35 LP | ✓ | | `f_k35lp` :121 | Model 02 |
| 4 | Korg 35 HP | | ✓ | `f_k35hp` :133 | Model 02 |
| 5 | Moog ladder LP | ✓ | | `f_ladder` :156 (hp = 0) | Model 03 |
| 6 | Ladder HP "ALT pole-mix" | | ✓ | `f_ladder` :156 (hp = 1) | Model 03, HPF menu |
| 7–8 | Steiner-Parker Sallen-Key (LP, HP injection) | ✓ | ✓ | `f_steiner` :197 | Model 04 |
| 9–10 | Oberheim SEM OTA SVF (LP→notch, HP→notch) | ✓ | ✓ | `f_sem` :224 | Model 05 |
| 11 | TB-303 diode ladder | ✓ | — | `f_diode` :246 | LPF Model 06 |

**Hidden behind selectors:**
- **Slope extensions.** Linear Butterworth-Q SVF sections, nested (build_genexpr.py:644–663). One to three of them are cascaded after the model whenever the chosen slope is steeper than the model's native order: 36/48 dB for every model, and 24 dB for the 12 dB-native K35, Steiner and SEM.
- **Sherman 12 dB mode.** Filter 2 runs alone (`ti` = 0).
- **Ladder 12 dB tap.** The y2 output.
- **Character control.** Each model uses it for something different:

  | Model | Character control |
  |---|---|
  | Sherman | feedback |
  | K35 | clip level |
  | Ladder | stage saturation |
  | Steiner | BP blend |
  | SEM | notch morph |
  | 303 | feedback HPF |

### Band-pass engine: 15 configurations (5 profiles × 3 architectures)

| Architecture | Code | Structure |
|---|---|---|
| SVF | bpf.py:255–266 | Nonlinear SVF band output inside a regeneration loop |
| CASCADE | :268–286 | Nonlinear SVF HP into nonlinear SVF LP, inside a regeneration loop |
| MULTIMODE | :288–292, `f_bmm` :83 | 4-pole ladder core, band-pass by pole mixing |

| Profile | `typ` | `sc` | `rg` | `rmax` | `kmax` | roll-off | Native architecture (per docs/BPF.md) |
|---|---|---|---|---|---|---|---|
| SEM | difference | 0.6 | tanh | 0.9 | 3.6 | – | SVF |
| Steiner-Parker | difference | 0.7 | hard knee | 1.06 | 4.3 | – | SVF (response only) |
| K35 / MS-20 | difference | 1.0 | tanh | 1.06 | 4.3 | – | CASCADE |
| ARP 2600 | separate | 1.4 | tanh | 1.06 | 4.3 | 14 kHz one-pole | none (derived) |
| EMS VCS3 | difference | 0.5 | tanh | 1.06 | 4.3 | – | none (derived) |

Table definition: bpf.py:20–29.

**Important for the audit:** a BPF "model" is a set of five constants applied to a *shared* structure. It is not a separate circuit model.

### Dynamics and saturation: 4 modules (dyn.py)

| Module | Code | Key elements |
|---|---|---|
| TUBE | `emit_tube` :266, `f_tube` :70 | Internal 2× up/down sampling; static asymmetric shaper; one-pole tone LP; 8 Hz DC blocker; phase-matched dry path; auto gain |
| OPTO | `emit_opto` :303 | Detector source select; SC HPF; HF emphasis shelf; peak (abs) detector; EL rise/decay; LDR fast and slow components; memory; gain law 1/(1+(K·c)^p) |
| VCA | `emit_vca` :341, `f_gc` :74 | Source select (NEW = input, OLD = own output); SC HPF; THRUST shelves; 3 ms RMS; gain computer; dB-domain attack/release; stereo link; auto make-up |
| GATE | `emit_chain` :430–462 | Key HPF/LPF; peak hold envelope; hysteresis; hold; dB-linear attack/release |

### Detectors and envelopes (every one in the code)

| Detector | Type | Time constants | Location |
|---|---|---|---|
| Opto EL panel | Asymmetric one-pole on \|x\| | 2 ms rise, 4 ms fall | dyn.py:157–159, 322 |
| Opto LDR fast | Asymmetric one-pole | 4.5 ms attack, 40 ms release | :157, :160, :323 |
| Opto LDR slow | Asymmetric one-pole | 150 ms charge; release 0.5–5 s, set by memory | :161, :325–326 |
| Opto memory | Asymmetric one-pole | 4 s charge, 20 s discharge | :162–163, :324 |
| VCA RMS | One-pole mean square | 3 ms | :179, :358 |
| VCA gain smoothing | One-pole in dB | attack 0.03–30 ms, release 0.05–3 s | :177–178, :366 |
| Gate envelope | Instant attack, exponential decay | 30 ms | :196, :443 |
| Gate gain | dB-linear ramps | attack / release / hold | :197–200, :456 |

### Sidechain processing

| Path | Stages |
|---|---|
| Opto | SC HPF one-pole (20–500 Hz, :164); HF emphasis +0 to ×4 above 2.5 kHz (:166, :313) |
| VCA | SC HPF one-pole (:181); THRUST shelves at 200 Hz and 3 kHz (:183–186, :357) |
| Gate key | HPF + LPF one-poles (:192–195) |
| All three | Sources: INT / CHAIN / EXT (`_src` :262). EXT reads gen~ in3/in4, which are `plugin~ 3 4` fed by Live's `live.routing`. |
| Link | Opto: max of channels (:317–320). VCA: mean of mean squares (:360–364). The gate is always linked (max). |

### Oversampling and decimation

| Where | What | Default |
|---|---|---|
| Filter section (LPF, HPF, BPF, routing) | 2× polyphase IIR half-band; 10 coefficients; transition 0.0227 (≈106 dB stop band per design, not measured here) | **Off (1×)**: `ovs_sel` default 0 |
| TUBE | Its own 2× (same coefficients), always on | On |
| Opto, VCA, gate | None | — |

Code: build_genexpr.py:22, 599–615, 712–725; dyn.py:26, 271–291.

### DC blocking, anti-aliasing and output

| Block | Location |
|---|---|
| Output DC blocker, first order, 2 Hz | build_genexpr.py:730 |
| Tube DC blocker, 8 Hz | dyn.py:148, 292 |
| Soft clip: above \|0.7\| maps to 0.7 + 0.3·tanh((\|x\|−0.7)/0.3) | build_genexpr.py:737–746 |
| Output gain −24 to +12 dB | :731 |
| Switching duck: 4 ms ramp to zero around order, oversampling, BPF position and routing changes | :577–596 |
| Anti-aliasing filters (other than the half-band) | none |
| NaN guard (`q == q`) | :748 |

### Signal routing

| Function | Location |
|---|---|
| Stage order LP>HP / HP>LP | build_genexpr.py:682–700 |
| BPF PRE/POST (SERIES only) | :675, :702 |
| PARALLEL / HYBRID sum | routing.py:42–66 |
| Dynamics after the filters | build_genexpr.py:727 |
| Dynamics: 6 orders in two state-copied lanes with a 25 ms crossfade | dyn.py:208–243, 383–429 |
| Gate after the chain | dyn.py:430 |
| Key listen | dyn.py:464 |

### Parameters, presets and defaults

There are 79 Live parameters. Their definitions and defaults are in each module's `PARAMS` or `P()` call:
- build_genexpr.py:384–406
- bpf.py:38
- dyn.py:39
- routing.py:15

The full map is in `docs/UI.md`.

**Default state:**
- LPF: Ladder, 24 dB, OPEN at 20 kHz
- HPF: K35, OPEN at 20 Hz
- BPF and all dynamics modules: off
- Oversampling: 1×
- Soft clip: on

**Presets:** the device ships no Live presets. The three "suggested orders" set Chain Order only.

### Existing tests and benchmarks (before this audit)

| Test file | Scope |
|---|---|
| `tests/golden.py` | Bit-exact regression gates: 48 LPF/HPF, 35 BPF and 21 dynamics renders |
| `tests/validate.py` | 25 checks: response, slopes, self-oscillation, click-free switching, CPU, denormals, long-run, small-signal vs the bilinear-mapped circuit transfer function (see the caveat in `DSP_VALIDATION_RESULTS.md`) |
| `tests/bpf_tests.py` | BPF checks |
| `tests/dyn_tests.py` | Dynamics checks |
| `tests/routing_tests.py` | Routing checks |
| `tests/ui_tests.py` | UI checks |
| `tests/compat.py` | Compatibility with every earlier release |

**Added by this audit (diagnostics only):**
- `source/tests/audit/`: `common.py`, `audit_filters.py`, `audit_dynamics.py` and `run_all.sh`
- Outputs: `docs/dsp-audit/data/*.json` and `docs/dsp-audit/plots/*.png`

# DSP implementation audit (source-code forensics)

Each signal path is traced from input to output, using the generator sources: line numbers refer to `source/src/*.py`. Wherever possible, the description of what a path does is based on the equations, not on function names.

## Common path for every LPF/HPF model

Per sample (build_genexpr.py:480–571 controls, 618–664 stage):

1. **Controls.** Every control is smoothed with one-pole filters:
   - cutoff in log2 domain, 6 ms (:484)
   - resonance, drive, comp and character, 15 ms (:485–488)
   - The coefficient is g = tan(π·fc/fs_o), where fs_o is the oversampled rate. Cutoff is clamped to 0.45·fs_o (:489–491). This is **bilinear prewarping at fc**.
2. **Drive.** The input is multiplied by d = 0.25·2^(5·drive) (:508), which spans −12 to +18 dB. The output is multiplied by 1/d·2^(5·drive·(1−comp/2)) (:510).
   - Drive is a *convenience* input gain into the model's nonlinear elements.
   - Comp is a *convenience* output-level compensation. Neither has a hardware counterpart.
3. **OPEN zone.** The LPF crossfades to dry above about 16 kHz and the HPF below about 25 Hz (:502–505). This is a convenience that makes "open" exactly transparent; analogue filters are never transparent.
4. **Model.** The model call runs only for the active model(s); a model change crossfades over 25 ms (:512–545). Inactive model state is reset to zero (:553–562).
5. **Slope extension.** Linear Butterworth sections are cascaded after the model (:644–663). This is generic DSP: it does not extend the circuit, it adds *ideal linear* poles after it.
6. **Output mix.** y = x + wet·(model·osc − x) (:663).

### Nonlinear solving method (shared by every nonlinear filter)

- **Method.** Every tanh, or tanh-like element, is replaced by its secant gain at the **previous sample's** operating point (`f_tg`, :37). That turns the current sample's equations into linear ones, which are then solved exactly with zero-delay feedback (ZDF / TPT).
- **What that means.**
  - This is the "cheap" semi-implicit method known from Mystran and Zavalishin.
  - It is **not** a converged solution of the nonlinear circuit equations: the nonlinearity lags by one sample.
  - That is accurate when the signal changes little per sample.
  - It loses accuracy, and can lose stability, when g is large (high cutoff relative to the sample rate) and resonance is high. See the instability findings in `FILTER_FIDELITY_REPORT.md` §4.
- **Integration.** Trapezoidal (bilinear).
  - The response is exact at DC and at fc.
  - It is frequency-warped elsewhere, with a zero at Nyquist: "cramping".
- **Oversampling.** Optional, 2× (:599–615, 712–725), **off by default**.

---

## Model-by-model trace

### 01 Sherman: `f_sherman` (build_genexpr.py:102–113)

- **Input stage.** u = f_asym(1.6·(x + fb·y_prev))·0.625. This is an asymmetric tanh, and it is the only source of even harmonics among the filters.
- **Filter 1.** Nonlinear SVF. Its damping R1 = 0.3 + 0.7(1−r)² is modulated by f_tg(band output).
- **Filter 2.** Nonlinear SVF in series. Its damping R = 0.8(1−r)² − 0.08·r³⁰ goes *negative* at maximum resonance, which is how the model reaches self-oscillation. The algebraic sigmoid f_ag(2·band) limits the amplitude.
- **Feedback.** fb = 0.92·Character, taken from tanh(y), with one sample of delay.

| Status | Item |
|---|---|
| Reproduced (vs public block description) | Series filters at equal tuning (24 dB); 12 dB with filter 2 alone; input overdrive |
| Absent | Continuously variable multimode LP/BP/notch/HP; parallel mode; harmonic intervals; VCA overdrive with AR; ring modulator; noise source |
| Invented | The feedback path (undocumented); every constant (no circuit data exists) |
| Physically meaningful parameters | None can be established (no schematic) |

### 02 Korg 35: `f_k35lp` / `f_k35hp` (:121–145)

- **LP structure.** TPT LP1 → Σ → LP2 → y, with feedback K·y → HP1 (implemented as LP state s3) → Σ.
- **Solving.** The loop is solved with zero delay in closed form: u = (y1 + ig(K·ig·s2 − s3)) / (1 − K·G·ig).
- **Nonlinearity.**
  1. u = 0.85·tanh(u/0.85), a soft clip of the loop node (:127).
  2. K = K0·f_tg(K0·y_prev/L), which limits the feedback gain at level L (:124). This represents the diodes, using the previous sample's output.
- **Small signal.** H = 1/(s² + (2−K)s + 1), and HP = s²/(…). This is Pirkle's form.

| Status | Item |
|---|---|
| Reproduced | 2-pole Sallen-Key response; resonance limited by a nonlinearity in the loop; self-oscillation; LP and HP share one structure |
| Approximated | The diode feedback clipper is a symmetric tanh secant on K. Real diodes are exponential and conduct asymmetrically, because the two polarities have different drops and offsets. |
| Absent | KORG35 transistor-level gain/bias behaviour (the "drive costs bass" character); the Mk2 LM13600 revision; input-level-dependent DC shift; even harmonics (measured H2 below −170 dBc) |
| Physically meaningful parameters | K (loop gain) and the clip level L. The 0.85 node clip has no stated origin. |

### 03 Ladder: `f_ladder` (:156–183)

- **Stage gains.**
  - T0 = f_tg(1.4·u_prev) is the input pair.
  - Ti = f_tg(1.4·hs·y_i,prev) are the stages.
  - Each stage: y_i = G_i·y_{i−1} + s_i/(1+g·T_i), with G_i = g·T_{i−1}/(1+g·T_i).
  - This discretises dy_i/dt = ω(tanh(y_{i−1}) − tanh(y_i)) (Huovilainen).
- **Global feedback.** u = (x(1+k·bc) − k·S)/(1 + k·G1G2G3G4), solved exactly.
- **Taps.** y2 gives 12 dB; y4 gives 24 dB. The HP mode is a binomial pole mix.

| Status | Item |
|---|---|
| Reproduced | 4 stages with tanh per stage; feedback through the input pair; self-oscillation (k_max = 4.3 > 4); bass loss with resonance (comp 0); resonance-dependent harmonics |
| Approximated | One-sample lag in every tanh; thermal-voltage scaling fixed at 1.4; `hs` (Stage Sat) scales stage saturation up to 3×, a convenience with no physical counterpart |
| Absent | Transistor mismatch and offset (no even harmonics); the real ladder's differential (two-sided) structure beyond this tanh model; temperature drift |
| DSP conveniences | `bc` (Comp) passband restore, computed as x·(1 + k·comp); Stage Sat |

### 04 Steiner-Parker: `f_steiner` (:197–214)

- **Inputs.** Three: xl (LP, at R1), xb (BP, at the C1 feedback node) and xh (HP, at C2), all into the same Sallen-Key network.
- **Diode strings.** Their conductances are secants t1 = f_tg(0.7·Δv1) and t2 = f_tg(0.7·Δv2), taken from the previous sample's voltages across each string.
- **Amplifier.** Ke = K·f_ag(0.7·K·vB), a hard-knee sigmoid secant.
- **Solving.** A 2×2 linear solve per sample.
- **Character.** Crossfades xl/xh against xb, giving the BP blend.

| Status | Item |
|---|---|
| Reproduced | Sallen-Key topology; Q set by amplifier gain K (self-oscillation at K = 3); the multi-input injection principle; amplifier clipping |
| Approximated | Diode strings modelled as tanh secants. The real element is a forward-biased diode chain: exponential I–V, a bias-set operating point, and a level-dependent resistance. A tanh is symmetric and saturating, which is the wrong shape for a forward-biased diode string. |
| Absent | The mirrored branch (only one branch is modelled); the bias network; the HP injection node, which is inferred; the 1974 article was not available |
| Physically meaningful parameters | K (Q) |

### 05 SEM: `f_sem` (:224–233)

- **Input.** u = 2·tanh(x/2), an input soft clip with no stated circuit origin.
- **Integrators.** Gains g1 = g·f_tg(0.6·h_prev) and g2 = g·f_tg(0.6·b_prev), i.e. OTA input saturation on each integrator.
- **Damping.** R = 20^(−res). It stays positive, so the model has no self-oscillation.
- **Output.** LP + m·HP (or HP + m·LP) for the notch morph.

| Status | Item |
|---|---|
| Reproduced | 12 dB SVF; OTA-style tanh integrator inputs; LP/notch/HP morph |
| Approximated | OTA input attenuator levels fixed at 0.6; input soft clip |
| Absent | The SEM's resonance and damping circuit specifics; behaviour of the band-pass output in this stage; OTA output-current limits and CA3080 bias-current effects; even harmonics |

### 06 TB-303: `f_diode` (:246–275)

- **Ladder.** A current-driven 4-node RC ladder, with diode-pair rungs modelled by secant conductances t_i = f_tg(0.5·Δv_i).
- **Solving.** The tridiagonal system is solved twice per sample (input response a and state response b), and then the feedback u is solved exactly.
- **Input pair.** xi = tanh(x). The node u is soft-clipped by 2·tanh(u/2).
- **Feedback.** Passes through a one-pole HPF set by Character: 8 Hz to about 300 Hz.

| Status | Item |
|---|---|
| Reproduced | Stinchcombe's 303 configuration and coefficients; the feedback HPF; rung nonlinearity |
| Approximated | The secant lag; the 2·tanh(u/2) clip of the driven node |
| Absent | Asymmetry (measured H2 −135 dBc at 0 dBFS with res 80, effectively none); the 303's accent, envelope and VCA interaction, which are outside this device's scope |

### Slope extensions (:644–663)

These are ideal linear SVFs with Q = 0.7071, at the same g as the model. **Generic DSP.** At 36/48 dB each model is followed by idealised Butterworth poles that no hardware possesses.

---

## Band-pass engine (bpf.py)

**Controls (:154–244).** Two configuration slots (A/B) crossfade over 25 ms on any change of model or architecture.

**Per slot:**
- r = rmax·res^1.3 (regeneration)
- k = kmax·res^1.3 (ladder feedback)
- Edges for the cascade: fh = fc·2^(−bw/2) and fl = fc·2^(bw/2)
- A multimode centre-correction polynomial (:229)

**`emit_slot` (:246–304):**

| Architecture | What it computes |
|---|---|
| SVF | y = 2R·band(u), where u = (x + r·sat(y_prev)·nB)/(1 − r·sat·nA). This is a **regeneration (positive feedback) loop around a band-pass**: zero-delay in the linear part, one-sample lag in the saturator. |
| CASCADE | The same loop around SVF-HP(fh) → SVF-LP(fl), with centre normalisation cn |
| MULTIMODE | `f_bmm`: a 4-stage core, with stage gains of difference type (tanh(in − out)) or separate type (tanh(in) − tanh(out)). Global k feedback, an input clip 0.35·tanh(u/0.35), and output BP4 = 4(y2 − 2y3 + y4) cross-faded to BP2 = 2(y1 − y2) by bandwidth. |
| ARP | Adds a one-pole LP at 14 kHz after any architecture (:296–301) |

**Audit findings:**
- **Profiles are constants, not circuits.** The "model" changes only five constants on the same code (bpf.py:20–29). For example, EMS and SEM differ only in sc (0.5 vs 0.6), rmax and kmax.
- **The regeneration loop is not hardware.** None of the referenced band-pass circuits forms resonance by an outer regeneration loop around a band-pass. The SEM sets Q by damping; the MS-20 by its own K loop per section.
- **Compensation in MULTIMODE.** Its raw gain is 1, so Compensation has no effect. This is documented in the UI.

---

## Dynamics (dyn.py)

### TUBE (emit_tube :266–300)

**Signal path:**
1. Input gain (−24 to +24 dB).
2. 2× up-sampling with the half-band.
3. f_tube(x·k, b, ib) = (f_tsh(x·k + b) − f_tsh(b))·ib, where:
   - f_tsh(v) = 0.8·tanh(1.25v) for v > 0, and 1.176·tanh(0.85v) otherwise
   - k = 0.3·2^(5.98·drive), giving 0 to +36 dB
   - b = 0.6·bias
4. One-pole tone LP, applied at the 2× rate.
5. 2× down-sampling.
6. Output scaling: Auto gain, or 1/(0.3·√D).
7. 8 Hz DC blocker.
8. Mix with a phase-matched dry path.

**What it is:** a **memoryless (static) asymmetric waveshaper** with an adjustable operating point.

| Status | Item |
|---|---|
| Reproduced (generically) | Asymmetric soft saturation; even/odd balance via bias; level-dependent THD |
| Absent | The triode equation (Koren / Child–Langmuir); plate voltage and load line; plate resistance and µ; grid current and the resulting bias shift (blocking distortion); the coupling capacitor and cathode bypass, which make distortion frequency- and history-dependent; Miller capacitance; power-supply sag; transformer |
| Measured | Distortion is independent of frequency (T3) and history (T4), which confirms the shaper is static |
| Convenience parameters | Drive, Bias (has an analogue: grid bias); Tone (a generic one-pole); Auto gain |

### OPTO (emit_opto :303–338)

**Signal path:**
1. Detector input: its own previous output in INT mode, which is **feedback, consistent with the LA-2A**; or CHAIN; or EXT.
2. SC HPF.
3. HF emphasis: +3·emph·(x − LP2.5k).
4. Rectify: |x|.
5. Light lt: one-pole, 2 ms rise and 4 ms fall.
6. LDR fast component cf: 4.5 ms attack, 40 ms release.
7. Memory mem: 4 s charge, 20 s discharge.
8. LDR slow component cs: 150 ms charge. Its release time constant is 0.5 + 4.5·mem seconds.
9. Gain: c = K(0.6·cf + 0.4·cs) and G = 1/(1 + c^p).
   - COMP: K = 1.6, p = 2.
   - LIMIT: K = 4, p = 9.

| Status | Item |
|---|---|
| Reproduced | Feedback detection; two-stage release (fast then slow); release lengthening after sustained compression (memory); side-chain pre-emphasis; COMP/LIMIT |
| Approximated | The CdS cell as a mix of two first-order components with a memory-modulated time constant. The real LDR has a nonlinear resistance-vs-illuminance law, asymmetric rise and decay, and light-history effects. The EL panel as a one-pole on \|x\|; the real panel is a capacitive AC-driven load with a threshold-like light/voltage law. |
| Absent | Tube make-up stages (12AX7, 12BH7) and their harmonics; input and output transformers; frequency-dependent attack (measured attack changes only 2.3 → 2.9 ms from 5 kHz to 100 Hz); the T4's shunt-divider placement against the source impedance |
| Physically meaningful parameters | Peak Reduction (side-chain gain); Gain; COMP/LIMIT; HF emphasis (the hardware has a rear-panel control) |

### VCA (emit_vca :341–376)

**Signal path:**
1. Detector input: NEW takes the input (feed-forward); OLD takes the previous output (feedback). This matches the API description.
2. SC HPF.
3. THRUST: MED = 0.5·x + 0.5·HP200(x); LOUD = 0.25·x + 0.75·HP200(x) + 0.5·HP3k(x). These are **detector-only**; verified bit-identical audio in C4a.
4. Mean square with a 3 ms time constant.
5. Level in dB.
6. Link: mean-square average.
7. Gain computer with quadratic knee width W = 0 / 6 / 12 dB.
8. One-pole smoothing of the dB gain: attack setting / release setting.
9. Ideal multiplier.
10. Auto make-up.

| Status | Item |
|---|---|
| Reproduced | Feed-forward / feedback switch; RMS detection; THRUST in the detector, not in the audio path; 3 knees; ratio set; release range |
| Approximated | THRUST curves, which are not public; MED lacks the slight HF lift the manuals describe. Knee shapes. |
| Absent | Link filter (HP/LP/BP); 2500+ link speed (peak/RMS); VCA colouration (the API VCA and the 2520 op-amp output stage); output transformer |
| Measured | Attack settings below 1 ms are not achieved: the 3 ms RMS integrator sets a floor of about 0.7 ms (C2a). The OLD-mode effective ratio collapses (∞:1 measures 2:1; 4:1 measures 1.75:1). Whether the hardware scales its ratio control in OLD mode is **unverified**. |

### GATE (emit_chain :430–462)

Generic: a key filter; a peak envelope with 30 ms decay; hysteresis 4 dB; hold; dB-linear ramps. **No hardware claim.**

### Reorder lanes (emit_controls :208–243, emit_chain :398–429)

Two complete copies of the chain. On an order change, all module state is copied into the idle lane, which then crossfades in over 25 ms. This is a correct and clean engineering solution. **No hardware analogue** exists, because hardware cannot be reordered without repatching.

---

## Routing and output (routing.py, build_genexpr.py:667–750)

- **PARALLEL.** y = Σ L_i(out_i − (1 − w_i)x) + x·Π(1 − w_i), so a bypassed branch drops out of the sum.
- **HYBRID.** Series LP/HP, plus L_b times the BP difference signal.
- **Displayed vs implemented.** The jsui routing diagram is tested against the engine's flow table for all 96 combinations of routing, order, position and the three ON states (`tests/ui_tests.py`). They agree.
- **Output.** 2 Hz DC blocker, then gain, then soft clip (only above 0.7 absolute), then duck.

## Parameters: physical vs convenience (summary)

| Physically grounded | Convenience (no hardware counterpart) |
|---|---|
| Cutoff, resonance/K, model choice, SEM mode morph | Drive (input gain into the model) |
| 303 feedback HPF | Comp (output make-up) |
| Opto Peak Reduction and HF emphasis | Character on Sherman (invented feedback) and Ladder (Stage Sat) |
| VCA threshold, ratio, knee, THRUST, type, release | OPEN zones; slope extensions |
| Tube bias (as an operating point) | Tube Auto gain and Tone |
| | Every Mix control; Link % on the opto (an LA-2A is mono) |

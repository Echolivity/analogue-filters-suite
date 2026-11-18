# Compressor fidelity report

The source is `source/tests/audit/audit_dynamics.py`. Data is in `data/dynamics.json` and plots in `plots/c*.png`. All tests ran at 48 kHz on the shipped engine, with filters off and every other module off.

GR is read from the engine's own meter outputs (out7 and out10, in dB). Tags:
- **[measured]**: measured on the engine.
- **[reference]**: published hardware behaviour.

## 1. OPTO (LA-2A-inspired)

### 1.1 Does it model an optical response, or just fixed attack and release?

**It models an optical response, partially.** The gain is not a fixed attack/release envelope. It is a nonlinear function of four state variables:
- EL light
- LDR fast component
- LDR slow component
- memory

The slow release time constant itself depends on the memory state (dyn.py:322–328). **The photocell retains state across successive signals.** This is demonstrated by C3a and `plots/c3_opto_release_memory.png`.

Release after a −3 dBFS 1 kHz burst, Peak Reduction 80, COMP, ≈18 dB GR, with a −40 dBFS tail:

| Burst length | 50 % release | 90 % recovered |
|---|---|---|
| 0.2 s | 55 ms | 1.07 s |
| 1 s | 72 ms | 2.8 s |
| 5 s | 75 ms | 6.5 s |
| 20 s | 75 ms | 6.7 s |

[reference] UA gives about 60 ms for the first 50 %, then 1–15 s. Other sources give 0.5–5 s.

**Verdict:**
- The first 50 % matches the reference.
- The slow component and its dependence on programme history are qualitatively right, and fall inside the published range.
- Memory **saturates after about 5 s** of compression. 5 s and 20 s bursts give the same release. Whether a real T4 keeps lengthening beyond that is unknown here.

### 1.2 Attack [measured vs reference]

| Signal | Time to 63 % of final GR |
|---|---|
| 100 Hz | 2.9 ms |
| 1 kHz | 2.3 ms |
| 5 kHz | 2.3 ms |

[reference] The average attack is about 10 ms, and it is frequency-dependent (UA).

**Deficiency.**
- The attack is about **4× faster** than documented. The code comment at dyn.py:157 ("≈10 ms overall") is not borne out.
- Its frequency dependence is only 0.6 ms, from 5 kHz to 100 Hz.

### 1.3 Static curves (C1, `plots/c1_static_curves.png`)

Steady-state 1 kHz sine, measured 5–6 s after onset:

| Mode | Ratio, top 8 dB | GR at 0 dBFS |
|---|---|---|
| COMP, PR 40 | 2.2 : 1 | 7.2 dB |
| COMP, PR 70 | 2.7 : 1 | 16.1 dB |
| LIMIT, PR 70 | 9.7 : 1 | 28.2 dB |

[reference] COMP is soft-knee, nominally 4:1, and source-dependent. LIMIT is about ∞:1. The UA WebZine notes the difference between the two is subtle in practice.

**Verdict.**
- The curve is soft-knee and level-dependent: the ratio rises with GR, which is plausibly LA-2A-like.
- The absolute ratio is low in COMP. LIMIT reaches only about 10:1.

### 1.4 Other checks

| Check | Result |
|---|---|
| Distortion (C6, −6 dBFS) | COMP PR 80: 1.18 % THD at 50 Hz, 0.003 % at 1 kHz. LIMIT: 6.9 % at 50 Hz. This is gain-modulation distortion: the cell follows the low-frequency waveform. It is **odd-only**: H2 sits below −169 dBc. Missing: the 12AX7/12BH7 stages, which colour a real LA-2A even at zero GR. |
| Stereo link (C5) | Linked by maximum. Link 0 % gives independent channels: −16.7 dB on the loud channel and −5.2 dB on the quiet one, driven by its own level. A real LA-2A is a mono unit with a stereo strap option. Link % is a DSP convenience. |
| Noise | No noise is modelled. A real LA-2A has a measurable hum and hiss floor. |
| Modes | COMP and LIMIT change K and the exponent of the gain law. That is an abstraction of the real switch, whose circuit effect was not identified. |

**Opto classification evidence:**
- Two-stage, history-dependent release: ✓
- Feedback detection: ✓
- Side-chain pre-emphasis: ✓
- Attack: 4× too fast ✗
- Ratios: low ✗
- Audio-path tube and transformer: absent ✗
- LDR law: abstracted

## 2. VCA (API 2500-inspired)

### 2.1 Architecture checks

| Feature | Reference | Implementation | Evidence |
|---|---|---|---|
| RMS detector | Yes | 3 ms one-pole mean square | dyn.py:179, 358 |
| NEW = feed-forward / OLD = feedback | Yes | The detector source switches between input and previous output | dyn.py:347 |
| THRUST in the detector, not the audio | Yes (filter before the RMS detector) | **Verified:** below threshold, NORM/MED/LOUD outputs are bit-identical (max \|diff\| = 0) | C4a |
| THRUST shape | MED: slight LF cut and slight HF lift. LOUD: stronger. Exact curve not published. | MED: −6 dB low shelf at 200 Hz, no HF lift. LOUD: −12 dB low shelf plus a +3.5 dB HF shelf at 3 kHz. | C4b |
| Knee hard / med / soft | Yes | Quadratic knee, 0 / 6 / 12 dB wide | dyn.py:180 |
| Link % | Yes | Mean-square blend | C5 |
| Link filter (HP/LP/BP) | Yes (2500); link speed peak/RMS (2500+) | **Absent** | — |
| Release 0.05–3 s | Yes | One-pole in dB; time constant = setting | C2b |
| Attack 0.03–30 ms | Yes | One-pole in dB, after the 3 ms RMS | C2a |

### 2.2 Measured accuracy

**Static ratio, NEW, hard knee (C1):** 1.5, 2, 3, 4, 6, 10 and ∞ are all exact to 2 decimals.
- Threshold: GR > 1 dB first appears at −16 dBFS with the threshold at −20. That is consistent with RMS (sine RMS is 3 dB below peak) plus the knee.
- Soft knee starts compressing 3 dB earlier.

**OLD (feedback) ratios.** 4:1 measures 1.75:1, and ∞:1 measures 2.0:1.
- That is what an ideal feedback loop with this gain computer gives.
- If the hardware rescales its ratio control in OLD mode, which has not been verified, the implementation does not.
- **Flag as unverified.**

**Attack, time to 63 % after a +30 dB step:**

| Setting | 0.03 ms | 0.1 ms | 0.3 ms | 1 ms | 3 ms | 10 ms | 30 ms |
|---|---|---|---|---|---|---|---|
| Measured | **0.71 ms** | 0.77 ms | 1.02 ms | 1.98 ms | 4.25 ms | 11.3 ms | 31.3 ms |

- The fast settings are not achieved. They are **limited by the fixed 3 ms RMS integrator**.
- The hardware's 0.03 ms setting implies a detector path much faster than 3 ms. How the API combines RMS averaging with sub-millisecond attack is not public.

**Release:** time to 37 % recovery = setting ±7 ms, for 0.05, 0.3, 1 and 3 s. Exact.

### 2.3 THRUST effect on detector sensitivity

C4b, `plots/c4_thrust_detector_response.png`: GR at equal level (−6 dBFS), threshold −30.

| THRUST | 50 Hz | 200 Hz | 1 kHz | 10 kHz |
|---|---|---|---|---|
| NORM | 24.9 dB | 24.5 dB | 24.1 dB | 24.0 dB |
| MED | 19.6 dB | 22.4 dB | 24.0 dB | 24.0 dB |
| LOUD | 15.7 dB | 22.0 dB | 24.6 dB | **27.4 dB** |

Bass triggers less compression, and in LOUD the treble triggers more. That is the documented intent. The **curve shapes are guesses**.

### 2.4 Distortion and channel behaviour

| Check | Result |
|---|---|
| Gain-modulation THD (C6) | 0.03 ms / 0.05 s at 10:1 on a 50 Hz tone: 1.29 % THD. 30 ms / 0.3 s at 4:1: 0.12 %. At 1 kHz: below 0.004 %. Odd harmonics only. |
| VCA colouration | None: the gain element is an ideal multiplier. A real VCA gain cell and its surrounding discrete amplifier stages add level-dependent distortion. API is known for discrete op-amp designs, but **the 2500's actual audio path was not inspected**, so its distortion character is **not established** here. |
| Stereo (C5) | Link 0 / 50 / 100 % gives R-channel gain of −0.25 / −8.6 / −17.1 dB, with L at −20.1 / −18.6 / −17.1 dB. A correct, continuous blend. |
| Noise | Not modelled. |

### 2.5 Verdict

The control architecture follows the published feature set well: NEW/OLD, THRUST in the detector, knees, link %. It falls short in four places:

| Gap | Effect |
|---|---|
| Fixed 3 ms RMS | Prevents the fast attack range |
| THRUST curves | Approximate; MED has no HF lift |
| Link filter | Missing |
| Gain element | Ideal; no API audio-path character |

This is **more than a generic VCA compressor**: the feed-forward/feedback switch and THRUST-in-detector are API-specific. It is **not shown to behave like an API 2500**, because no hardware data was available.

## 3. Gate (no hardware claim)

| Item | Detail |
|---|---|
| Hysteresis | Threshold, closing 4 dB below |
| Hold, attack, release | dB-linear ramps |
| Key filters | HPF and LPF |
| Sources | INT, CHAIN, EXT |
| Verification | Covered by the existing `tests/dyn_tests.py`. Generic, as intended. |

## 4. Test-signal coverage

| Signal | Used |
|---|---|
| Sine | Static curves, THD, THRUST, link |
| Tone bursts | Opto release memory, attack |
| Stepped amplitude | VCA attack and release |
| Noise | Chain test (S1), filter transfer functions |
| Impulses | Existing `t_impulse_step` |
| Complex musical signals | Not used. No licensed programme material is in the repository. The S1 test uses a synthetic gated tone plus noise. |
| Pink noise | Not used separately. White noise is used for transfer functions. |

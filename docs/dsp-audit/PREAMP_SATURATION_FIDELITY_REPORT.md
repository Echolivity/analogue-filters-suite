# Preamplifier and saturation fidelity report

The source is `source/tests/audit/audit_dynamics.py` (T1–T6). Data is in `data/dynamics.json` and the plot in `plots/t1_tube_transfer_thd.png`. All tests ran at 48 kHz.

## 1. What the TUBE module is

**It is a static waveshaper, not a triode model.** The UI calls it "TRIODE · 2x OS" and the docs call it a "triode stage".

The code (dyn.py:66–72):

```
f_tsh(v) = 0.8 · tanh(1.25 v)       v > 0
         = 1.176 · tanh(0.85 v)     v ≤ 0
f_tube(x) = (f_tsh(k·x + b) − f_tsh(b)) · ib       k = 0.3 · 2^(5.98·drive), b = 0.6·bias
```

The positive half compresses harder and the negative half softer. That loosely imitates grid conduction on positive swings and cut-off on negative swings, but it does so as a *fixed curve*.

**Not present:**
- A triode equation: no Koren, Child–Langmuir or Cardarilli model
- Plate voltage, plate resistance, µ, or transconductance
- A load line (plate resistor, B+), so the operating point does not move with signal
- Grid current, input coupling capacitor and the resulting bias shift ("blocking distortion")
- A cathode resistor and bypass capacitor, which make gain and distortion frequency-dependent
- Miller capacitance (HF roll-off that rises with gain)
- Power-supply sag, and any transformer

## 2. Measurements [measured]

### 2.1 Harmonics vs drive and bias (T1)

Test signal: 200 Hz at −12 dBFS, with auto gain on.

| Bias | Drive 0 % | Drive 60 % | Drive 100 % |
|---|---|---|---|
| +20 (default) | 0.70 % THD; H2−H3 = +20 dB | 10.2 %; +2.8 dB | 33 %; −11.5 dB |
| −60 | 0.95 %; +31.5 dB | 9.3 %; +5.7 dB | 33 %; −22 dB |
| +100 | 3.0 %; +46 dB | 26 %; +28 dB | 35 %; −3.3 dB |

**Behaviour.** At low drive the stage is second-harmonic-dominant. At high drive it becomes odd-dominant, because both rails saturate.

**Bias** shifts the even/odd balance strongly, which is plausibly tube-like. The absolute curve is *not derived* from any tube.

### 2.2 Level dependence (T2)

At Drive 50 % and bias 20, THD rises with input level:

| Input level | THD |
|---|---|
| −30 dBFS | 0.7 % |
| −20 dBFS | 2.3 % |
| −12 dBFS | 6.5 % |
| −6 dBFS | 13.4 % |
| 0 dBFS | 23 % |

THD rises monotonically with level.

### 2.3 Frequency dependence (T3)

At Drive 60 %, THD is **10.3 / 10.2 / 10.2 / 9.8 %** at 50 Hz, 200 Hz, 1 kHz and 3 kHz. The slight drop at 3 kHz comes from the tone filter and the oversampler. It confirms the stage is **memoryless**. A real common-cathode stage with a bypassed cathode and coupling capacitors distorts differently at low and high frequencies.

### 2.4 Memory and dynamic operating point (T4)

THD of a −20 dBFS sine measured before a 1 s full-scale burst, and immediately after it:

| | Before burst | Just after burst |
|---|---|---|
| THD | 3.6160 % | 3.6160 % |
| H2 | −29.47 dBc | −29.47 dBc |

The two are identical, so there is **no bias shift or recovery**. A real grid-leak/coupling-capacitor stage shifts its bias after an overload and recovers over tens to hundreds of ms. That is audible as "bloom" or "sag".

### 2.5 Intermodulation (T5)

SMPTE test (60 Hz + 7 kHz, 4:1) at Drive 60 %: **45.8 % IMD**.

This is very high, consistent with a hard-driven static curve. There is no reference value to compare with.

### 2.6 Aliasing (T6)

Test signal: 5003 Hz at −6 dBFS, with the stage's own 2× oversampling active.

| Drive | Aliased products |
|---|---|
| 60 % | −75 dBc |
| 100 % | **−30 dBc** |

At high drive, 2× is insufficient for a curve with this much gain (up to +36 dB).

### 2.7 DC offset

The asymmetric curve generates DC. An 8 Hz DC blocker inside the stage (dyn.py:292) and the 2 Hz output blocker remove it. So no DC reaches the output, but **the DC is not allowed to act on the stage** (no bias shift).

## 3. Transformer behaviour

No transformer model exists anywhere in the engine. **No claim of transformer emulation is made or should be made.**

LA-2A transformers and API output transformers are part of those units' character and are absent; see the compressor report.

## 4. Other saturating elements

| Element | Location | Nature |
|---|---|---|
| Output soft clip | build_genexpr.py:737–746 | Linear below \|0.7\|, then tanh to ±1.0. Generic safety limiter. |
| Filter input/loop clips | various | Part of each filter model; see the filter report |
| Sherman input stage | `f_asym` | Static asymmetric tanh; the only filter source of even harmonics |

## 5. Verdict

The TUBE is a **well-behaved, oversampled, bias-adjustable asymmetric waveshaper**. It does **not** emulate a triode preamplifier:
- No triode transfer law or load line
- No frequency-dependent distortion
- No operating-point dynamics

Its name should be read as "triode-style saturation". The prompt distinguishes "a tube waveshaper" from "a tube preamplifier"; this module is the former.

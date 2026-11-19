# Ladder (model 03): check against the published circuit analyses

## Sources
- **[H]** A. Huovilainen, *Non-linear digital implementation of the Moog ladder filter*, DAFx-04.
- **[D]** S. D'Angelo, V. Välimäki, *Generalized Moog Ladder Filter: Part I*, IEEE/ACM TASLP 2014 (author post-print, Aalto). It builds on their ICASSP 2013 "improved" model.
- **[S]** T. E. Stinchcombe, *Analysis of the Moog Transistor Ladder and Derivative Filters*, 2008.
- **[P]** R. A. Moog, US patent 3,475,623 (the ladder low-pass and high-pass filters).

## What the sources establish
- **Large-signal equations [D eq. 1–2].**
  - Stages 2–4: dΔVᵢ/dt = (I/2C)·[tanh(ΔVᵢ₋₁/2V_T) − tanh(ΔVᵢ/2V_T)].
  - Stage 1: dΔV₁/dt = −(I/2C)·[tanh(ΔV₁/2V_T) + tanh((V_in + kΔV₄)/2V_T)].
  - These are the same continuous-time equations as [H]. D'Angelo & Välimäki's criticism of earlier models is about their **discretisation** (linear response and tuning), not the equations.
- **Linear [D eq. 7, 16; S].** The transfer function is −p⁴/((s+p)⁴ + kp⁴), with DC gain −1/(1+k). The pole frequency is f = I/(8πCV_T). Self-oscillation starts at k = 4 (the linear bound sec⁴(π/4)); the nonlinearities hold the amplitude there.
- **Linearity range [S].** The differential pairs are linear only within about ±20 mV, against 2V_T ≈ 52 mV.
- **What the sources do *not* give:**
  - the real resonance-pot range or maximum k;
  - the feedback and output coupling of a 904A or Minimoog;
  - the drive level into the ladder;
  - transistor mismatch.

  [S] attributes the small tuning offset between theory and SPICE to base currents.

## Model vs sources (Comp 0, 24 dB, Reference mode)

| Property | Source | Model | Verdict |
|---|---|---|---|
| Per-stage tanh equations, input pair carrying the feedback | [H], [D] | identical (zero-delay solve with secant gains, one-sample nonlinear lag) | **Conforms** |
| Linear response 1/((1+s)⁴+k) | [S], [D] | already checked by `validate.py` (circuit reference) | **Conforms** |
| DC gain −1/(1+k) | [D] | res 25/50/75/90 %: −5.1/−9.2/−12.5/−14.0 dB vs theory −4.7/−8.8/−12.0/−13.5 (a constant −0.5 dB offset, also at res 0) | **Conforms** (the offset is level calibration) |
| Peak frequency → pole frequency as k → 4 | [D] (A₀) | 926 Hz at k 2.96 (theory 930), 984 Hz at k 3.75 (theory 984), 1002 Hz at k 4.0 | **Conforms** |
| Self-oscillation from k = 4 | [D], [S] | k = 4.3·res^1.3 reaches 4 at res ≈ 94.6 % | **Conforms**. The pot law itself is **not sourced**. |
| Symmetric pairs → odd harmonics only | [D] (matched devices) | 220 Hz at 0 dBFS, Drive 0: 0.54 % THD, even harmonics 0.0000 % | **Conforms** to the ideal circuit. Real units have mismatch (unknown). |
| Drive level into the ladder (mV) | [S]: linear within ±20 mV | 0 dBFS at Drive 0 maps to a tanh argument of 0.35 (≈ 18 mV) | **Plausible, not sourced** |
| High-pass | [P] describes a true transistor-ladder **high-pass** (Moog 904B: 24 dB/oct, no resonance) | ALT: a pole-mix of the resonant low-pass ladder | **Differs** from Moog's own HP, already labelled ALT |
| Real feedback/output path, coupling, base currents | not in these sources | ideal | **Unknown** |

## Conclusion
The core is already circuit-faithful at the level of the published analyses. The remaining items need a **schematic of a specific instrument** (Minimoog Model D or the 904A/904B modules):
- the resonance-pot law and maximum k;
- the drive level into the ladder;
- the feedback and output coupling;
- Moog's true ladder high-pass.

Unlike the Sherman, no field evidence contradicts the model.

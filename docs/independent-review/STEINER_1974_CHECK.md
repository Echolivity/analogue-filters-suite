# Steiner-Parker model vs Steiner's 1974 article (review item R10)

**Source:** N. A. Steiner, "Voltage-tunable active filter features low, high and bandpass modes", *Electronic Design* 25, 6 Dec 1974, Ideas for Design, pp. 96 and 98. The user supplied the issue scan.

**Evidence class: [P].** It is the designer's own circuit and measured response plots. The plots were made with an HP-650A oscillator and an HP-400-L meter, with the center frequency set to 500 Hz.

Checks run against the engine: `source/tests/review/steiner/check.py`.

## What the article establishes

**1. Topology (Fig. 1).** A non-inverting-amplifier Sallen-Key filter with C1 = C2 = 0.0047 µF and gain K set by the Q pot. The mode is chosen by where the signal enters:

| Mode | Signal enters | Through |
|---|---|---|
| Low-pass | the R1 end | 47 kΩ into 1 kΩ |
| High-pass | the bottom of C2 | 47 kΩ, with 1 kΩ to ground |
| Band-pass | the bottom of C1 | 47 kΩ; this node is also fed from the output through 1 kΩ |

Derived here, normalised to ωc = 1:
- LP = K / (s² + (3 − K)s + 1)
- HP = K·s(s + 2) / (…)
- BP = K·s / (…)

So the high-pass skirt is 6 dB/oct, as the model and `validate.py` already assume.

**2. The article's own measurements fit these transfer functions.** The passband level is K/48 (the 47k/1k divider), and Q = 1/(3 − K):

| Plot | Predicted | Read from the plot |
|---|---|---|
| LP, Q 1.2 | −26.9 dB | about −27 dB |
| LP, Q 30 | −24.2 dB | about −25 dB (the text says passbands are about −25 dB) |
| HP, Q 1 | −27.6 dB | about −27 dB |

**3. The "resistors" are one forward-biased string of eight 1N4148s (Fig. 2).** The string runs between the collectors of the Q1/Q2 differential pair, which bias its two ends in opposite phase. Labelled from one end: "R1", C1, "R2", C2 (centre, to the amplifier), "R2", C1, "R1".
- The control voltage cancels at the centre.
- The signal enters both ends together, so the two halves form two mirrored RC networks in parallel. Signal current runs against the bias current in one half and with it in the other.

**4. Consequence: the element follows a sinh law.** With bias current I and V′ = 2·n·Vt per pair, i = I(e^{v/V′} − 1) − I(e^{−v/V′} − 1) = 2I·sinh(v/V′).
- Even-order terms cancel exactly. This is the article's "the bias effect of the input signal on the diodes is also cancelled".
- Conductance **rises** with level: ×1.011 at 25 mV, ×1.044 at 50 mV, ×1.18 at 100 mV.
- So cutoff rises on loud signals.
- The article keeps the signal below 50 mV per diode pair, with input at most 0 dBm at low Q and −10 dBm at Q ≥ 10.

**5. Amplifier.** Discrete Q3 (2N5172) and Q4 (2N5138). R6 (1 kΩ pot, with 1.8 kΩ and 2 kΩ) sets the gain, and feedback goes to the C1 node through 1 kΩ. Too much gain oscillates.

## The v1.6 model against it

| Property | Model | Article | Verdict |
|---|---|---|---|
| LP, HP, BP transfer functions | K/(…), K·s(s+2)/(…), K·s/(…); `validate.py` checks LP and HP | the same (derived from Fig. 1) | **Conforms** |
| Passband level and Q vs K | relative level only | K/48, Q = 1/(3 − K); the article's plots agree | **Conforms** in shape |
| HP node (review: "inferred") | signal into the bottom of C2 | bottom of C2 | **Confirmed** |
| Mirrored branch (review: "absent") | one network | two mirrored halves in parallel, which equals one network with an odd-symmetric law | **No separate branch needed** |
| Diode large-signal law | tanh secant: conductance **falls** with level. At Drive 60 the resonant peak falls from 973 Hz (−40 dBFS) to 943 Hz (−12 dBFS) and 445 Hz (0 dBFS) | sinh: conductance **rises**, so cutoff rises | **Wrong direction** |
| Amplifier limit | yes (an `f_ag` limit on K) | discrete stage, overloads at high Q | Plausible; no data |

**Conclusion.** The linear model, the injection points and the high-pass node are confirmed by a primary source, which settles review item R10's "no primary source". One defect remains: the diode law runs in the opposite direction to the circuit. Since the article operates the circuit below 50 mV per pair, where the law is within 4.4 % of linear, the difference shows up when driven hard (Drive, high resonance).

## Decision and status (user, 2026-11-19): fix in place. Done.

- **The law is now sinh, bounded by the 2 kΩ feed resistors:** secant = (1 + ρ)/(1/(sinh(a)/a) + ρ), with ρ = 2π·fc·4.7 nF·2 kΩ and a = 0.233·(voltage across the element). It is exactly 1 at small signal.
- **Level reference (assumption):** one model unit = the article's 0 dBm input at the low-pass node (1.1 V peak / 48 = 22.9 mV). V′ = 2·n·Vt = 98 mV per pair.
- **Measured** (Drive 100, res 0), −3 dB point: 760 Hz at −40 dBFS (unchanged), 992 Hz at −10 dBFS, 2059 Hz at 0 dBFS. The old law gave 760 / 812 / 760 Hz. At res 50 and 0 dBFS: 3067 Hz now, against 1132 Hz before.
- **Gates:** fs/4 sweep, self-oscillation pitch and Reference aliasing all still pass. The new v1.6 check locks in the direction.
- **Goldens:** only scenarios passing through the Steiner model change, and they were already in the documented set.

**Original note:**  A level reference. The article's levels are 0 dBm input at low Q and −10 dBm at Q ≥ 10. Mapping them to the model's units, e.g. 50 mV per diode pair at a stated dBFS, is an assumption, as with the Korg35 diode knee.

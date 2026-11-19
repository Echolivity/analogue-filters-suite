# Envelope filter: sources and assumptions

## Sources
- **[S]** Musitronics, *Mu-Tron III* schematic, 1975, "above S/N 02050" (scanned by CJLectronics 1997; copy at https://www.pisotones.com/MuTron-III/imgs/mutron3.jpg, linked by the user). **The primary source for every value below.**
- **[P]** M. L. Beigel, US patent 3,911,776, *Sound effects generator* (1975). Topology only, no values.
- **[N]** R. G. Keen, *Neutron Filter, a Mutron III Workalike*, GEO design 117, v1.01d (supplied by the user). Agrees with [S]: 1.8 nF + 2.2 nF, 220 k across the LDRs, Peak 150 k log, Gain 1 M rev-log with 3.3 k and 120 k, C9 4.7 µF; LED sense resistor (Rx = R23) "set by ear".

## Circuit values used (from [S])

| Block | Values | Model |
|---|---|---|
| A1 preamp | R4 120 k (C3 10 pF) / (R2 3.3 k + GAIN 1 M CCW log) | Gain −18.4 … +31.2 dB |
| A2 summer | R5 4.7 k input to (+); R9 12 k + PEAK 150 k CW log from BP to (+); R7/R8 22 k from HP/LP to (−) | b = 4.7 k/(4.7 k + R_f), a = R_f/(4.7 k + R_f); Q = 1.78…17.7; HP/LP passband 2a; BP peak 2aQ |
| A3/A4 integrators | R10/R12 220 k ∥ LDR; C5/C7 1800 pF; C4/C6 2200 pF switched in on Low | f = 1/(2π (220 k ∥ R_LDR) C): HI 402 Hz floor, LO 181 Hz |
| A5 rectifier | R16 1 M / R24 22 k (UP); R?4 12 k added in parallel (DOWN); D1/D2 1N914; input via C8 2.2 µF | gain 45.5 / 128.8, half-wave, linked L/R |
| Envelope | R17 330 Ω charge; C9 4.7 µF; R18 47 k to −9 V | attack τ 1.55 ms; release: exponential toward −9 V with τ 221 ms, held at the rectifier output |
| A6 LED driver | R21/R22 120 k; R19 180 k / R20 120 k from +9 V (3.6 V) | I·R23 = V_C9 (UP), 7.2 V − V_C9 (DOWN) |
| Opto | 0805: one LED, two LDRs; R23 "value depends on characteristics of 0805" | see assumptions |

## Assumptions

| Item | Value used | Why |
|---|---|---|
| LDR law / R23 | conductance = (V_LED-drive / 1 V)^0.8 / 67 kΩ | the 0805 (Hamamatsu) has no data; scaled so the rail (7.5 V) gives about 7 kHz on HI |
| LDR lags | 2.5 ms on, 35 ms off | VTL5C3 class (the usual substitute) |
| Rails | ±7.5 V soft (tanh), at the preamp, rectifier, envelope and selected output | 4558 on ±9 V; the integrators and summer are not clipped internally |
| Level | 1 model unit = 1 V | no reference level |
| Polarity | not modelled | the original inverts the dry (A1) and the BP output |

Not resolved: the label of the 12 k DOWN resistor (R14/R34) is illegible in the scan; its value is clear.

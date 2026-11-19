# Envelope filter: sources and assumptions

## Sources
- **[S]** Musitronics, *Mu-Tron III* schematic, 1975, "above S/N 02050" (scanned by CJLectronics 1997; copy at https://www.pisotones.com/MuTron-III/imgs/mutron3.jpg, linked by the user). **The primary source for every value below.**
- **[P]** M. L. Beigel, US patent 3,911,776, *Sound effects generator* (1975). Topology only, no values.
- **[H]** Hamamatsu, *Dual CdS output type photocouplers P873-G35-911, P873-13*, technical data (3 pp., supplied by the user). The P873-13 is the 0805's catalogue number. Used:
  - **Fig. 5:** P873-13 ON resistance against LED current. Digitised: 280 k @ 0.1 mA, 74 k @ 0.3, 45 k @ 0.5, 21 k @ 1, 12.9 k @ 1.5, 7.0 k @ 3, 4.8 k @ 5, 2.9 k @ 10, 2.0 k @ 20 mA. Model: log₁₀R(kΩ) = 1.302 − 0.994L + 0.166L², L = log₁₀(I/mA), within 9 %; below 0.1 mA continued at the end slope (−1.32/decade), with a 10 MΩ dark floor (R_OFF ≥ 10 MΩ).
  - **Table:** P873-13 rise 4.0 ms / fall 6.0 ms typical at 20 mA (20 ms max).
  - **Fig. 6** (sister part G35-911): the time for the cell to reach a given resistance after switch-off — 9 / 20 / 110 / about 700 ms at 0.1 / 1 / 10 / 50 kΩ load. In conductance this is close to G₀/(1 + t/τ), the hyperbolic decay of the CdS recombination law dG/dt = k(G_eq² − G²). That law also predicts fig. 6's slower response at 5 mA. Model: k = 1/(4.4 ms × 1/2 kΩ), the geometric mean of the table's rise and fall.
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
| R23 | 3.9 kΩ | the schematic: "value depends on characteristics of 0805"; chosen so full drive (about 5.6 V, A6 swing minus the LED's about 1.9 V) gives 1.44 mA, 13 kΩ and a sweep top of about 7 kHz on HI. A factory calibration spec or a measured unit would replace it. |
| Photocell temperature, unit spread | not modelled | fig. 7: about ±20 % over 0–50 °C |
| Rails | ±7.5 V soft (tanh), at the preamp, rectifier, envelope and selected output | 4558 on ±9 V; the integrators and summer are not clipped internally |
| Level | 1 model unit = 1 V | no reference level |
| Polarity | not modelled | the original inverts the dry (A1) and the BP output |

Not resolved: the label of the 12 k DOWN resistor (R14/R34) is illegible in the scan; its value is clear.

# Envelope filter: sources and assumptions

## Sources
- **[P]** M. L. Beigel, US patent 3,911,776, *Sound effects generator* (Musitronics, 1975). Gives the topology: preamp; precision half-wave rectifier (op-amp 170, diodes 172/174); smoothing with fast attack and slow decay (R180 small, R184 large, C182); V-to-I converter (op-amp 190) driving one LED (198) for both photoresistors (116, 132); two-integrator filter (op-amps 110, 122, 138) with Q set by R130/R108 and gain proportional to Q; LP/BP/HP from nodes 146/150/154; UP/DOWN via a reference divider (192/194) with doubled rectifier gain; RANGE capacitors 126/142. **It gives no component values.**
- **[N]** R. G. Keen, *Neutron Filter, a Mutron III Workalike*, GEO design 117, v1.01d (construction guide supplied by the user; its schematic page is not in that copy). From the text and parts list:
  - C6/C8 1.8 nF integrator capacitors, plus C5/C7 2.2 nF in LO;
  - **R8/R9 220 kΩ in parallel with the LDRs**;
  - Peak 150 k log, adding positive feedback;
  - Gain: R3 120 k / (R1 3.3 k + 1 M reverse-log), about ×0.12–×36;
  - envelope capacitor C9 4.7 µF; precision rectifier U3b with D1/D2;
  - LED current sense Rx 560 Ω–4.7 kΩ, set by ear for the right amount of sweep;
  - TL072s on ±9 V; the dry signal is inverted, as in the Mutron.
- **[A]** Aion FX *Lumitron* documentation: the original used a Hamamatsu dual LDR (805A / P873-13, one LED, two LDRs); the VTL5C3 is the usual substitute ("fast on / fast off"); Peak 250kA ∥ 390k approximates the original 150kA.
- Mu-tron III literature: Gain 0.1 to 40; ±9 V supply; RC4558 op-amps.

## Assumptions (to calibrate against a production schematic)

| Item | Value used | Why |
|---|---|---|
| Level | 1 model unit = 1 V at the input | no published input level |
| Op-amp rails | ±7.5 V soft (tanh) | RC4558 on ±9 V |
| LDR law | conductance ∝ light^0.8; 10 kΩ at 1 V of envelope | typical CdS slope; the scale stands in for the Neutron's Rx trimmer (set by ear); gives 632 Hz → 6.4 kHz over −40 → 0 dBFS |
| LDR lags | 2.5 ms on, 35 ms off | VTL5C3 class; the Hamamatsu part has no data |
| Network | **220 kΩ parallel (Neutron R8/R9)**; 3.3 kΩ series (assumed) | floor 402 Hz HI / 181 Hz LO (sourced); top assumed |
| Q | 0.6 → 16, log | the patent gives no range; "plays individual overtones" at maximum |
| DOWN | LED drive = 1 − 2·envelope | the patent subtracts the envelope from a reference and doubles the rectifier gain; level unknown |
| Attack / Release | 2 ms / 150 ms defaults, adjustable | C9 = 4.7 µF is known; which resistors charge and discharge it is on the missing schematic page |

The Neutron schematic page, or a Mu-tron III service schematic, would settle the remaining assumed rows.

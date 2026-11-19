# Envelope filter: sources and assumptions

## Sources
- **[P]** M. L. Beigel, US patent 3,911,776, *Sound effects generator* (Musitronics, 1975). Gives the topology: preamp; precision half-wave rectifier (op-amp 170, diodes 172/174); smoothing with fast attack and slow decay (R180 small, R184 large, C182); V-to-I converter (op-amp 190) driving one LED (198) for both photoresistors (116, 132); two-integrator filter (op-amps 110, 122, 138) with Q set by R130/R108 and gain proportional to Q; LP/BP/HP from nodes 146/150/154; UP/DOWN via a reference divider (192/194) with doubled rectifier gain; RANGE capacitors 126/142. **It gives no component values.**
- **[N]** R. G. Keen, *Neutron* (a Mu-tron III work-alike, GEOFEX): integrator capacitors 1.8 nF, plus 2.2 nF in LO; PEAK 150 k audio, GAIN 1 M reverse log. Quoted from a search excerpt; the PDF itself could not be fetched.
- **[A]** Aion FX *Lumitron* documentation: the original used a Hamamatsu dual LDR (805A / P873-13, one LED, two LDRs); the VTL5C3 is the usual substitute ("fast on / fast off"); Peak 250kA ∥ 390k approximates the original 150kA.
- Mu-tron III literature: Gain 0.1 to 40; ±9 V supply; RC4558 op-amps.

## Assumptions (to calibrate against a production schematic)

| Item | Value used | Why |
|---|---|---|
| Level | 1 model unit = 1 V at the input | no published input level |
| Op-amp rails | ±7.5 V soft (tanh) | RC4558 on ±9 V |
| LDR law | conductance ∝ light^0.8; 10 kΩ at 1 V of envelope | typical CdS slope; scale chosen to give a 340 Hz → 6.4 kHz sweep over −40 → 0 dBFS |
| LDR lags | 2.5 ms on, 35 ms off | VTL5C3 class; the Hamamatsu part has no data |
| Network | 3.3 kΩ series, 1 MΩ parallel | bounds the sweep (HI about 88 Hz → 27 kHz; LO about 40 Hz → 12 kHz) |
| Q | 0.6 → 16, log | the patent gives no range; "plays individual overtones" at maximum |
| DOWN | LED drive = 1 − 2·envelope | the patent subtracts the envelope from a reference and doubles the rectifier gain; level unknown |
| Attack / Release | 2 ms / 150 ms defaults, adjustable | the patent says only "relatively small" / "relatively high" |

A Mu-tron III service schematic (Musitronics or ARP) would replace every row above.

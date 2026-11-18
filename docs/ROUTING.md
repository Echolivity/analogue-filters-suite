# Filter routing: series, parallel, hybrid (v1.4)

The FILTER ROUTING strip (right edge of the device) sets how the three filter engines are connected. It does not touch the processing chain: the dynamics always follow the filter section.

| Mode | Signal flow | Stage ORDER | BPF POSITION | Parallel levels |
|---|---|---|---|---|
| **SERIES** (default, = v1.3) | IN > LP > HP > BP > OUT (as set by ORDER and POSITION) | applies | applies | not used |
| **PARALLEL** | IN > ( LP + HP + BP ) > OUT | ignored | ignored | LP, HP and BP levels |
| **HYBRID** | IN > ( LP > HP ) + BP > OUT | applies to the LP/HP chain | ignored (BPF is in parallel) | BP level |

The readout next to the selector shows the live signal flow for the current mode, stage order and BPF position.

## How the parallel sum works
Each engine filters the same input, and its contribution is exactly what that engine adds when it is on:

  y = L_LP · w_LP·F_LP(x) + L_HP · w_HP·F_HP(x) + L_BP · w_BP·F_BP(x) + x · (1−w_LP)(1−w_HP)(1−w_BP)

Here **w** is the engine's own wet weight: ON fade × OPEN zone for the LPF and HPF, ON × Mix for the BPF. **L** is the PARALLEL LEVEL (−40 to +6 dB). In practice:
- **An engine that is off, or parked fully OPEN, drops out of the sum.** It does not add a second copy of the dry signal, so parking a filter never causes a +6 dB jump.
- **One engine on in PARALLEL sounds the same as that engine in SERIES.** With every engine off, the output is the dry input.
- **The response is exactly the sum of the filters** (verified to within 0.0001 dB). For example, LP 400 Hz + HP 3 kHz gives a band-reject notch; LP + HP + BP gives a three-band "split" whose bands you balance with the levels.
- **Mix works as a level:** the BPF Mix acts as a level control inside the sum, on top of BP LVL.

**HYBRID** adds the band-pass on top of the series LP/HP chain: y = chain + L_BP · w_BP·F_BP(x). Use it for a resonant band that rides over the main filtered signal, independent of where the LP/HP cutoffs are.

## Practical notes
- **Phase interaction:** parallel filters interact through their phase. Neighbouring LP and HP cutoffs can partially cancel, which is the classic band-reject sound. Use the levels to shape it.
- **Hot sums:** with all three filters resonating hard, the parallel sum can exceed 0 dBFS (+6.7 dBFS measured with every engine self-oscillating). The output Soft Clip (on by default) catches it. Lower the levels if you need clean headroom.
- **Switching modes** uses the device's existing 8 ms output dip (as for stage order and oversampling), so it is click-free during playback.
- **Saved Sets:** v1.1–v1.3 Sets load in SERIES with all levels at 0 dB, so they sound exactly as before. The SERIES path is bit-identical to v1.3 (104 golden renders).

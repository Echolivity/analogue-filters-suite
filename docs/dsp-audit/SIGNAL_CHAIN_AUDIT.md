# Complete signal-chain audit

## 1. Actual processing order (from code)

```
in1/in2 ─► [2× up, if Oversampling = 2×]
          ─► FILTER SECTION (per sub-sample)
               SERIES:   [BPF if PRE] → (LPF → HPF | HPF → LPF) → [BPF if POST]
               PARALLEL: LPF(x), HPF(x), BPF(x) → Σ levels   (stage order and BPF position ignored)
               HYBRID:   (LPF → HPF | HPF → LPF) + level·BPF(x)
          ─► [2× down]
          ─► DYNAMICS at the base rate: slot1 → slot2 → slot3, any order of TUBE / OPTO / VCA
               (TUBE has its own 2× oversampling inside)
          ─► GATE (always after the chain)
          ─► KEY LISTEN (replaces the output with the chosen detector signal)
          ─► DC blocker 2 Hz → Output gain → Soft clip (> |0.7|) → switching duck → out
```

The order comes from these places in the code:

| Section | Code |
|---|---|
| Filter section | build_genexpr.py:667–710 |
| Combine (PARALLEL / HYBRID) | routing.py:42 |
| Dynamics chain | build_genexpr.py:727 → dyn.py:383 |
| Gate | dyn.py:430 |
| Key listen | dyn.py:464 |
| Output stage | build_genexpr.py:729–748 |

**Fixed by design.** The filters always come before the dynamics, and the gate always comes after the three reorderable modules. The user **cannot** place the TUBE before the filters, or a compressor before a filter.

## 2. Displayed routing vs implementation

**Filter routing.** The panel diagram (`df_routing.js`) is checked against the engine's own flow table for all 96 states: 3 routings × 2 orders × 2 BPF positions × 8 combinations of the three ON switches. They agree in every state (`tests/ui_tests.py`).

`tests/routing_tests.py` checks two further properties:
- PARALLEL is bit-identical across stage orders and BPF positions.
- HYBRID equals the LP/HP series chain plus the BPF, to within 0.0000 dB.

**Chain order.** The block positions are produced by thispatcher scripting from the same order index that the DSP reads (`c_order`). That is verified statically in `tests/ui_tests.py` and `tests/dyn_tests.py`. **It has not been verified in Max.**

**Gate.** It is displayed as fixed after the chain, which matches the code.

## 3. Sidechain and external key

**Sources.** Each detector has its own source selector:

| Source | Opto | VCA | Gate |
|---|---|---|---|
| INT | Its own output (feedback) | NEW: its input · OLD: its output | Its input (the chain output) |
| CHAIN | The chain input (after the filters) | same | same |
| EXT | `in3`/`in4`, fed from `plugin~ 3 4` | same | same |

The selector code is in `_src`, dyn.py:262.

**Unverified.** The external key path reaches gen~ through Live's `live.routing`. **That routing configuration has not been tested in Live.**

## 4. Wet/dry, compensation and gain staging

**Mixes.**
- Every module and the BPF have a Mix control. Each is a linear crossfade.
- The TUBE dry path goes through the same up/down filter pair, so the mix does not comb-filter. That was verified in v1.3 by the LATENCY test in `tests/dyn_tests.py`.
- Filter mixes are implicit: the OPEN zones, and the PARALLEL levels.

**Gain staging.** Each dynamics module has −24 to +24 dB input and output trims. The filters have Drive, from −12 to +18 dB, and Comp.

**Level references.**
- The TUBE's Auto gain holds the output of a −12 dBFS programme peak constant.
- Nothing models analogue headroom (no rail clipping and no nominal +4 dBu point).
- The output soft clip is the only global ceiling.

## 5. Effect of order on the sound [measured, S1]

Test conditions:
- **Signal:** a 110 Hz tone gated at 2 Hz (between 30 % and 100 % amplitude), plus noise.
- **Settings:** TUBE Drive 60; OPTO PR 60; VCA −24 dB at 3:1, attack 1 ms, release 0.2 s.

| Order | Steady-sine THD | H2 / H3 (dBc) | Mean OPTO GR | Mean VCA GR | Crest factor |
|---|---|---|---|---|---|
| TUBE > OPTO > VCA | **19.1 %** | −18.7 / −16.8 | 7.6 dB | 5.0 dB | 7.6 dB |
| TUBE > VCA > OPTO | 19.1 % | −18.8 / −16.8 | 2.5 dB | 11.1 dB | 7.9 dB |
| OPTO > TUBE > VCA | 6.0 % | −25.4 / −31.7 | 8.3 dB | 6.5 dB | 8.3 dB |
| OPTO > VCA > TUBE | 2.5 % | −32.1 / −44.8 | 8.3 dB | 5.4 dB | 9.3 dB |
| VCA > TUBE > OPTO | 3.6 % | −29.4 / −38.4 | 3.1 dB | 12.2 dB | 8.8 dB |
| VCA > OPTO > TUBE | **2.4 %** | −32.8 / −44.8 | 2.5 dB | 12.2 dB | 9.3 dB |

**Findings.**
- **Tube before compression** drives the shaper at full level, so distortion is highest: 19 % THD, odd-dominant.
- **Tube after compression** drives it with a gain-reduced signal: 2.4–3.6 % THD, even-dominant.
- **The first compressor takes most of the reduction.** The second sees an already reduced signal, so its GR is lower: the OPTO falls from about 8 to about 2.5 dB when it moves behind the VCA.
- **Tube last preserves the most peak-to-average range** (crest factor 9.3 dB), because the shaper acts on an already compressed signal. Tube first gives 7.6 dB.

These are the expected interactions of real gear in those orders. Their *magnitudes* are specific to this implementation.

**Not measured:**
- Order effects on resonance. The filters always precede the dynamics, so no order can change resonance.
- Headroom effects, because there is no analogue headroom model.

## 6. Latency

**No added latency.** The design has no lookahead and no buffering. Reported device latency is 0.

**Phase delay that is present:**
- The IIR oversamplers add frequency-dependent phase delay. TUBE: about 3.6 samples at 1 kHz.
- The filter oversampler at 2× adds its half-band phase. See `FILTER_FIDELITY_REPORT.md` §2.2.

This was verified in v1.3 (`tests/dyn_tests.py`, LATENCY test).

## 7. Findings

1. **The implementation matches the displayed routing** for every testable state. Max/Live runtime behaviour is untested.
2. **Processing order is partly configurable.** The TUBE, OPTO and VCA order is free. Filters before the dynamics, and the gate last, are fixed.
3. **Order changes are physically plausible and substantial.** They are click-free: state is copied, then a 25 ms crossfade.
4. **There is no headroom or level model.** Interactions that depend on analogue operating levels (rail clipping, transformer saturation) cannot occur.

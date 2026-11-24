# Ladder: Drive level vs the Minimoog Model D mixer

**Question.** How does the device's level into the ladder compare with a Minimoog, where the mixer drives the ladder's input pair directly?

## From the service manual
Sources: fig. 9-2, oscillator board (serial 10175 and above); fig. 9-17, interconnect; fig. 9-11, filter board.
- **Oscillator outputs:** triangle and saw ±1.75 V; square 0 / −3.5 V (3.5 V p-p, AC-coupled, so ±1.75 V); the pulse comes from a divider.
- **Each source:** OSC VOL 25 kΩ linear → 33 kΩ → 10 µF → the audio node, "+2 VDC".
- **Filter board:** the node enters through C27 (10 µF) into Q29's base, which R54 (470 Ω) ties to AC ground (the decoupled ladder bias node, C24 220 µF).
- **Node impedance:** R54 in parallel with the other four sources' 33 kΩ (+ pot) paths, ≈ 470 ∥ 8.5 k ≈ 445 Ω.
- **One oscillator at full volume:** 1.75 V × 445/(33 k + 445) = **23.3 mV peak** at Q29. Three in phase: **70 mV**.
- **For scale:** the pair is linear within about ±20 mV (Stinchcombe), against 2V_T ≈ 52 mV. That is why one oscillator is "clean-ish" and three overdrive the filter.

## The model
- The ladder's input-pair argument is tanh(1.4·u), and the real argument is V/2V_T, so 1 unit of u ≈ 1.4 × 51.7 mV ≈ 72 mV.
- Drive feeds the ladder 0.25 × 2^(5·Drive): Drive 0 → ×0.25 (+0 dB), Drive 100 → ×8 (+30 dB).
- **0 dBFS peak at Drive 0 → u = 0.25 → 18.1 mV.**

## Result

| Minimoog | Q29 drive | Device equivalent (Drive 0) | Drive for a 0 dBFS input |
|---|---|---|---|
| one oscillator, volume 7.8 | 18.1 mV | 0 dBFS | 0 |
| one oscillator, volume 10 | 23.3 mV | +2.2 dBFS | ≈ 7 |
| three oscillators, volume 10 | 70 mV | +11.7 dBFS | ≈ 39 |

**Conclusion.** The existing mapping is already within 2.2 dB of "0 dBFS = one oscillator at full volume", so no change was made. The whole Minimoog mixer range (one to three oscillators at full) lies within Drive 0–40 for a full-scale input. Above that, Drive goes beyond what the mixer alone can reach; external-input feedback patching can reach that territory too.

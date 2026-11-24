# BPF models: consistency with the v1.6 circuit work (diagnostics only)

The BPF engine (v1.2, `source/src/bpf.py`) is behavioural by design: five "character" presets (element type, element scale, regeneration saturator, regeneration limit) on three generic topologies (SVF, CASCADE, MULTIMODE). `docs/BPF.md` says so: the scales "were not fitted to measurements" and "no configuration was compared against hardware recordings."

Since v1.2, three of the five namesakes have been rebuilt from primary sources in the LPF/HPF engine. The BPF presets were not updated, so the device now holds two contradictory accounts of the same circuits.

| BPF model | BPF engine today | What v1.6 established from sources (LPF/HPF engine) | Status |
|---|---|---|---|
| **Oberheim SEM** | SVF, OTA tanh element (scale 0.6), soft tanh regeneration, max r 0.9 ("never self-oscillates") | **SEM-1A schematic + SEM manual:** a linear input; RES-pot law; damping held by the D11/D12 diode limiter; rails at 2.6 units; no self-oscillation. The SEM's BP is the same SVF's band-pass node. | **Partly consistent.** No self-oscillation agrees; the nonlinearity (tanh in the integrators vs a linear OTA region with a diode-limited damping path) and the resonance law do not. |
| **Steiner-Parker** | SVF response (K·s/(s² + (3−K)s + 1)), tanh element, **hard-knee** regeneration clip | **Electronic Design, Dec 1974 (Steiner):** diode-string resistors with a **sinh** (exponential-diode) law; the Sallen-Key network itself. | **Inconsistent element law.** The response is right (BP by injection); the element is tanh plus hard clip where the source gives sinh diodes. |
| **Korg 35 / MS-20** | CASCADE: **2-pole HP** → 2-pole LP; `BPF.md` says "some sources give the MS-20 HPF as 6 dB/oct; this engine uses 2-pole sections" | **Stinchcombe, MS-20 study** (adopted in v1.6, "HP changed in place"): the MS-20 HPF is **6 dB/oct** (the first-order section of the Korg 35 HP), and Mk1 (transistor) and Mk2 (OTA) circuits differ. | **Contradicts the project's own adopted source.** The BPF's cascade uses a 12 dB/oct HP and has no Mk1/Mk2. |
| ARP 2600 | MULTIMODE pole-mix, separate-type tanh, 4072 roll-off as a 14 kHz one-pole | No v1.6 work; the 2600 has no band-pass output (documented as "derived"). | Unchanged; would need the 4012/4072 schematic. |
| EMS VCS3 | MULTIMODE pole-mix with diode-rung tanh (Civolani–Fontana) | No v1.6 work; the VCS3 filter is a diode-ladder low-pass that EMS called "low-pass/band-pass" (documented as "derived"). | Unchanged; Stinchcombe's EMS diode-ladder analysis (already cited) and the Civolani–Fontana paper would support a native model. |

## Proposals (not implemented; each changes the BPF's sound, so it needs a decision)
1. **Korg 35 / MS-20:** make the CASCADE's HP section first order (6 dB/oct), matching the adopted Stinchcombe study and the LPF/HPF engine. Optionally offer Mk1/Mk2 there too. This is the clearest inconsistency.
2. **Steiner-Parker:** replace the tanh element and hard-knee clip with the sinh diode law used by the LPF Steiner. Cleanest: run the LPF engine's Steiner core with the input injected at the band-pass node (the Synthacon's BP input), so both engines share one circuit.
3. **Oberheim SEM:** take the band-pass node of the LPF engine's SEM-1A core (linear input, RES law, D11/D12 limiter) instead of the generic OTA-tanh SVF.
4. **ARP 2600 / EMS VCS3:** keep them labelled "derived". A native VCS3 low-pass/band-pass model is possible from the cited sources if wanted.

Each proposal leaves the BPF off by default, so the device's default renders stay bit-identical; only renders with that BPF model on would change.

## Status: proposals 1–3 adopted (user decision, 2026-11-24)
- **Korg 35 / MS-20, CASCADE:** 1-pole (6 dB/oct) HP (with the transconductor element) into the 2-pole LP. Loop-phase retuning keeps the resonant peak on the centre (it would otherwise sit about 4 semitones low), and the regeneration limiter is re-solved at the current value (an fs/4 sweep stays bounded). Measured at 1 kHz, res 0: 100 Hz −13 dB, 10 kHz −29.5 dB (asymmetric skirts).
- **Steiner-Parker, SVF:** the LPF engine's Synthacon core (sinh diode strings, amplifier limit), input at the band-pass injection point; K = max(1 + 2.1·res^1.3, 3 − 1/Q). It self-oscillates at full resonance, as the Synthacon does.
- **Oberheim SEM, SVF:** the LPF engine's SEM-1A core, band-pass node; damping = min(Q knob, SEM-1A RES law). It never self-oscillates (Q ≤ 10).
- Other architectures of these models keep the generic (derived) elements. ARP 2600 / EMS VCS3 unchanged.
- Golden renders: every BPF render changed. The untouched configurations differ only by the start-up crossfade out of the default SEM-SVF slot (≤ 0.005, then < 1e-7 residue).

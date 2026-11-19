# Sherman model vs the Sherman Filterbank 2 manual

**Sources (supplied by the user, 2026-11-19):**
- **[P]** *Sherman Filterbank 2 "Abuser's manual"* (English, 60 pp.). The manufacturer's own document. It describes controls and behaviour; it has no schematic.
- **[S]** Skull & Circuits, *VCF-4* write-up. An **original** LTC1060 switched-capacitor design, "never intended to be a port". The author did not reverse-engineer the Sherman, and only suspects it uses a microcontroller-generated clock.
- **[S]** ambientspace, *Shermanik* Bitwig preset notes. Self-described as "not an emulation, but a heavily inspired interpretation". The author suspects switched-capacitor filters but writes "Is it the same? I don't know."

**Verdict on fidelity: unchanged, behavioural (grade E).** None of these sources gives circuit values. The manual does pin down *what the unit does*, which lets the model be checked feature by feature.

## What the manual establishes [P]

**Filters**
- **Two 12 dB filters** with simultaneous LP/BP/HP. Each has a Lp/Bp/Hp **balance** knob and a **correction** knob that sweeps −Bp → 0 → (−Bp + Lp + Hp). At balance = Bp: correction at −Bp gives zero output; at −Bp+LpHp it gives a notch; halfway gives 0.5·(Lp + Bp + Hp), roughly all-pass.
- **Routing:** a continuous **PAR ↔ SER** knob. In series the two filters make 24 dB/oct, and filter 1 also feeds OUT 1.
- **Filter 2 has more resonance** than filter 1.
- **Harmonics switch (filter 2):** free, or f2 = f1 ÷ 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 16.

**Clock behaviour**
- "Filter 2 produces more clock noise than filter 1 in the low freq settings."
- In low frequency settings "a weak high 'eee' sound" is "normal and typical".
- The bottom frequency goes below 1 Hz and drifts with temperature; it is set by internal trims F1/F2.
- Together these are consistent with **clocked (switched-capacitor) filters**. The manual does not name the chips.

**Input stage**
- "Tube sound overdrive": the sound distorts as INPUT rises.
- "Too much input can push away the resonance peaks."
- A three-way switch selects Hi Boost (at low input) or Hi Cut (at high input).
- The **Limit** switch leaves the filters "more breathing room for self-oscillation if the input stage is extremely overdriven".

**Feedback:** the manual mentions **no output-to-input feedback** path.

## Decisions (user, 2026-11-19) and status

You chose all four: modes and correction, harmonics, clocked character, overdrive and Limit. The model **remains behavioural (grade E)**. These additions match documented *behaviour*, not a verified circuit or sound. FEEDBACK remains undocumented.

**Done (all appended parameters; at their defaults every reference render is bit-identical):**

| Feature | Implementation | Measured |
|---|---|---|
| **Sherman Modes** STAGE / PANEL | STAGE = v1.5 (LP in the LPF stage, HP in the HPF stage). PANEL = Balance + Correction set the output of both filters. The hardware has a pair per filter, so one shared pair is a simplification. | — |
| **Balance** | Lp (0) → Bp (50) → Hp (100), linear crossfade | — |
| **Correction** | −100 adds −Bp; +100 adds (−Bp + Lp + Hp) | Bp − Bp silent (−111 dB). Bp with correction +100 is a notch at fc (−50 dB at 12 dB, −93 dB at 24 dB) with flat passbands (±0.3 dB). Halfway gives about half level with a gentle dip (manual: "make up for the weaker output with more input"). PANEL Lp is bit-identical to STAGE. |
| **Harmonics** | filter 2 at f1 ÷ {1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 16}, gliding over about 3 ms (log ratio); 24 dB (series) only, since at 12 dB filter 2 plays alone at the cutoff | peaks at 498 Hz (÷2) and 249 Hz (÷4) with fc 1 kHz. A ratio change is click-free. fs/4 sweep at ÷1/÷2/÷16: worst −0.4 dBFS. |
| **Overdrive buries resonance** | already present in v1.5 through the amplitude-dependent damping | −12 dBFS noise, res 85, 24 dB: peak +24.4 dB above passband at Drive 0, +12.1 dB at Drive 100 |
| **Limit** | ×0.25 into the filters after the overdrive, ×2.7 after. The **mechanism is invented**; only the effect is documented. | Drive 100: resonance prominence +12.1 → +19.5 dB; level −13.2 → −11.6 dBFS |

**Clocked character:** a separate change, off by default (below).



| Feature | Model | Manual | Verdict |
|---|---|---|---|
| Two 12 dB SVFs; 24 dB in series | yes (filter 1 → filter 2, same cutoff) | yes | **Conforms** |
| Filter 2 carries more resonance | yes (filter 1 Q ≤ 1.7; filter 2 self-oscillates) | yes | **Conforms** |
| Input overdrive | asymmetric saturator | "tube sound overdrive" | **Plausible** (character unverified) |
| Overdrive pushes resonance down; Limit | input saturates to a bounded level, so the resonance is kept | overdrive buries resonance; Limit restores it | **Missing** |
| Modes | LP (LPF stage) or HP (HPF stage) | LP/BP/HP balance plus the correction knob (−Bp … notch … all-pass) | **Missing** |
| Harmonics (f2 = f1 ÷ n) | f2 = f1 only | 11 ratios, or free | **Missing** |
| Parallel / continuous PAR↔SER | series only | continuous | **Missing** |
| Clocked character | none (ideal continuous-time) | clock noise, low-frequency "eee", sub-1 Hz range | **Missing** |
| FEEDBACK (CHARACTER) | output → input saturated loop | not described | **Not documented** (a design choice from the spec) |

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

## The v1.6 model against it

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

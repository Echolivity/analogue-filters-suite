# Changelog

## v1.6: stability, fault containment, 4x–16x oversampling, Reference mode

Details and before/after measurements: [docs/V1.6_ENGINE.md](docs/V1.6_ENGINE.md).

- **Fixed:** Sherman, Steiner-Parker and the BPF SVF could run away at high resonance near fs/4. At the reported point (48 kHz, 12 kHz, res 100 %), Sherman peaked at +249 dBFS and now peaks at −1.8 dBFS. The non-linear terms are now evaluated implicitly, from the current sample's values. The fix applies everywhere. Small-signal response is unchanged; high-resonance tone changes slightly (self-oscillation now tracks the cutoff within 0.5 %).
- **New:** fault containment. A stage whose output becomes non-finite or absurd resets itself and passes dry. It never activated in normal-use tests.
- **New:** High Oversampling OFF / 4x / 8x / 16x for the filters and TUBE, using cascaded half-band stages. 2x is bit-identical to v1.5.
- **New:** Engine Mode REFERENCE (default) / CREATIVE. REFERENCE runs each active model at least at its measured minimum factor (≤ −80 dBc aliasing at a bright test point; TUBE 8x). CREATIVE runs exactly your setting.
- **Changed: OPTO LIMIT and Emphasis** (internal detector), rebuilt from the Teletronix schematic C-10953 rev C and the LA-2A manuals you supplied:
  - **LIMIT has a softer knee and a flat top.** It uses the hardware's R7 side-chain point, with the cell exponent fitted to the manual's Figure 1, which the addendum gives as the limiter curve.
    - +3.2/4.7/6.2/7.1 dB at 5/10/15/30 dB above breakaway (Figure 1: 3.4/5.1/5.6/5.7).
    - Past the flat top it dips about 5 dB toward the 40 dB cell floor at extreme settings (Figure 1 stops before that point).
    - No more hunting (GR reversals on programme material 577 → 110).
  - **Emphasis now cuts the lows going to the detector** (up to about −15 dB near 200 Hz) instead of boosting the highs.
  - LIMIT distortion at ≥ 30 dB of reduction: 1 kHz 0.007 %, 400 Hz 0.04 %, 100 Hz 0.66 % (was 1.8 %).
  - **Unchanged:** COMP (bit-identical below 40 dB of reduction) and the CHAIN/EXT detector gain law (bit-identical in both modes with Emphasis at 0 %).
- **Changed: the K35 high-pass is now 6 dB/oct, as on the MS-20** (Stinchcombe 2006, §7). The real circuit grounds the low-pass input and drives stage 2's lifted capacitor, which gives s(s + 1)/(s² + (2 − K)s + 1); v1.5 used s²/(…), 12 dB/oct. Measured within 0.11 dB of that function at resonance 0, 50 and 80.
  - **The HPF powers on as K35, so this changes the device's default high-pass.** On this model the slope settings now give about 6/18/30/42 dB/oct.
  - **Drive barely distorts its passband any more.** THD at 2 kHz, Drive 100 is 0.18 %, against 32.7 % in v1.5. In the built circuit the input reaches the output through stage 2's capacitor, so the OTA's saturation only shapes the region around cutoff; v1.5's passband distortion came from its non-circuit structure.
  - Sets that use the K35 high-pass get a gentler low cut, and up to +2.9 dB more level at the resonant peak (+0.1 dB at res 0, +2.1 at 50, +2.9 at 80).
  - Because the HPF powers on as K35, every HPF reference render changes during its start-up crossfade. The residual is exactly zero within 2 s.
- **New: K35 Circuit, OTA (Mk2) / KORG-35 (Mk1).** Stinchcombe's study shows the existing K35 model is the later LM13600 OTA circuit. It is now labelled as such, and its sound is unchanged (the default). KORG-35 adds the original MS-10/early MS-20 circuit:
  - a Sallen-Key core (C1 = 3·C2, 1/(s² + (7/3 − k)s + 1));
  - CHARACTER drives the diode stage by 0 to +24 dB, with makeup gain following the Drive control's level compensation (half the drive in dB at the default 100 %). At CHARACTER 100, quiet signals come out +11.6 dB and loud ones −6.6 dB;
  - the ×58 diode stage in the signal path (fitted to the study's Figure 17), so loud signals distort at every frequency, and CHARACTER sets the drive;
  - measured: transfer functions within 0.23 dB; passband THD rising from 0.009 % to 4.5 % with level in the study's test; self-oscillation only at maximum resonance; worst fs/4 peak −3.9 dBFS;
  - Reference mode runs it at 8x (LPF) / 4x (HPF), measured at the default CHARACTER as for every model. Heavy CHARACTER aliases more: at 8x, −67.9 dBc at CHARACTER 50 and −44.5 at 100. It costs about 2.3× the OTA circuit's CPU at the same factor.
  - **Assumptions:** 5 V peak per unit inside the filter (after Drive, which feeds the models at −12 dB at Drive 0). The diode knee is then reached at about +2 dBFS input at Drive 0, and about −16 dBFS at Drive 60; the study's R1 = R2/3 and ×1.1 buffer gain; MS-10 component values. The study's asymmetric resonance is not modelled (simulation only).
  - A new K35 strip sits at the right edge, and the parameter is appended (82 in total).
- **Changed: the Steiner-Parker diode law now follows Steiner's own circuit** (Electronic Design, 6 Dec 1974, which you supplied). The resistors are one forward-biased 1N4148 string fed in mirror from both ends, so the law is sinh: cutoff **rises** with level. v1.5 used tanh, so its cutoff fell.
  - Bounded by the circuit's 2 kΩ feed resistors.
  - Identical at small signal.
  - At Drive 100, the −3 dB point goes 760 → 992 → 2059 Hz at −40 / −10 / 0 dBFS. The old law gave 760 / 812 / 760 Hz.
  - The article also confirms the model's transfer functions, input points and high-pass node; its plots fit K/48 and Q = 1/(3 − K).
  - Level reference (assumption): one model unit = the article's 0 dBm input at the low-pass node.
- **Changed: the Oberheim SEM now follows the SEM-1A schematic** (supplied by you):
  - **Resonance:** the RES-pot law 2R = 0.1 + 3.03·(1 − res), so Q runs 0.32 → 10 (v1.5: 0.5 → 10). The 0.1 floor keeps it from self-oscillating.
  - **D11/D12 diode limiter:** damping rises on loud signals. At maximum resonance the peak gain is +20 dB at −30 dBFS and +11 dB at 0 dBFS.
  - **No input soft clip** (no circuit origin); the op-amp rails limit the outputs at ±13 V. At 1x it is far cleaner: −140 dBc aliasing (v1.5: −89).
  - **Unchanged:** notch and band-pass routing, which already matched the PS19 crossfade.
  - **Assumptions:** a linear RES pot; 5 V per unit; the Q floor.
- **Changed: HPF model 03 is now the Moog 904B** (R. A. Moog drawing 1118, 6/23/70, supplied by you), replacing the "Ladder HP - ALT pole-mix". The 904B is four C-R high-pass sections in series with no resonance circuit, so the response is exactly (s/(s+1))⁴ and the Resonance knob has no effect on it (authentic, by your choice). Its input is attenuated about 1:111 and restored by the audio amp, so the stages run near-linear. Only renders with HPF model 03 change.
- **New: ENVELOPE FILTER**, modelled on the **Musitronics Mu-Tron III** schematic (1975, "above S/N 02050"; topology also in Beigel's US patent 3,911,776; cross-checked with R. G. Keen's Neutron). It sits before the filter section and adds 13 appended parameters; off by default, and bit-identical when off.
  - **From the schematic:**
    - A1 preamp: ×0.12–×36.4.
    - A2 summer with PEAK (150 k CW log) in the band-pass feedback: Q 1.78–17.7, band-pass gain +8 to +31 dB, passband 2a.
    - A3/A4 integrators: 220 k ∥ LDR, 1800 pF, plus 2200 pF on LO.
    - A5 rectifier gain 45.5 (UP) / 129 (DOWN).
    - C9 4.7 µF: charges through 330 Ω (1.55 ms) and drains toward −9 V through 47 k (221 ms), a near-linear release.
    - A6 LED drive: V_C9 (UP) or 7.2 V − V_C9 (DOWN).
  - **Controls:** On, Mode LP/BP/HP, Peak, Gain, Range LO/HI, Sweep UP/DOWN, Attack/Release (circuit values by default), Mix, Output.
  - **Routing:** the same sweep moves the LPF, HPF and BPF cutoffs by up to ±5 octaves at full sweep (with the envelope filter on or off).
  - **Measured:**
    - HI sweeps 402 Hz → 6.7 kHz (408 Hz / 563 Hz / 4.85 kHz at −60/−40/−20 dBFS, Gain 0 dB; the dark cell barely moves below about −50 dBFS); LO 201 Hz → 3.0 kHz.
    - Band-pass peak +8.2 / +15.2 / +30.4 dB at Peak 0/50/100 (derived from the schematic: +8.1 / +15.2 / +30.7).
  - **Photocell (Hamamatsu P873-13 technical data, supplied by you):** resistance against LED current from fig. 5 (280 k @ 0.1 mA … 2.0 k @ 20 mA). Dynamics follow the CdS recombination law dG/dt = k(G_eq² − G²), with k set by the 4/6 ms rise/fall at 20 mA. So the cell is fast when bright and slow when dim, with a hyperbolic recovery tail: after a note, the peak drifts back from 1.36 kHz to 0.54 kHz over about 1.5 s.
  - **Assumptions:** R23 = 3.9 kΩ (the schematic leaves it to the opto; chosen for a sweep top of about 7 kHz on HI), and 1 unit = 1 V.
  - **Op-amp rails (±7.5 V, 4558 on ±9 V)** at the preamp, rectifier and envelope, and inside the filter loop: the summer (A2) and both integrators (A3/A4) saturate, and the integrator states follow their clipped outputs. So a hot band-pass at high Peak clips as on the pedal; below the rails the response is unchanged. The original's polarity inversions are deliberately not modelled, so the Mix knob doesn't cancel in BP mode. The original's polarity inversions are not modelled. See docs/independent-review/ENVELOPE_FILTER_SOURCES.md.
- **New: Sherman Filterbank 2 features** (from the manual you supplied; the model stays behavioural). A new SHERMAN strip has six appended parameters, and the defaults are bit-identical:
  - **Modes STAGE / PANEL:** PANEL engages the Filterbank's **Balance** (Lp → Bp → Hp) and **Correction** (−Bp … 0 … −Bp + Lp + Hp) knobs. Bp − Bp is silent, and Bp with full Correction is a notch, as the manual describes.
  - **Harmonics:** filter 2 at the cutoff ÷ 1–16 for twin resonant peaks (24 dB). Ratio changes glide over about 3 ms.
  - **Limit:** keeps resonance alive under heavy overdrive (+7 dB of peak prominence at Drive 100). The mechanism is invented; the manual documents only the effect.
  - The manual's "too much input pushes away the resonance peaks" was already true of the model.
  - **Clock (SMOOTH / CLOCK):** runs both filters as clocked (switched-capacitor) stages with the clock at 100 × cutoff: staircase grain, and a faint clock whine (−66 dBFS per filter) at 100 × cutoff when that falls below Nyquist. Filter 2 runs at the lower cutoff when Harmonics is above 1, so it carries more clock noise, as the manual says. **Every constant is an assumption** (100:1 ratio, feedthrough level); the manual names no chip. Above cutoff ≈ engine rate ÷ 100 the filter runs smooth. Reference mode runs Sherman at 8x or more while the clock is on, so 1x and 8x render identically.
  - **Partial self-oscillation** (from published reviews; the manual is silent): Sound On Sound (1997) found the Filterbank "refuses to go into full self-oscillation", and Tape Op (2025) calls it partial. Filter 2's damping now bends onto a positive floor (Q ≈ 100 at res 100) instead of going negative. A click at res 100 rings and dies (below −50 dBFS 2 s later, at any cutoff; −60 dB in about 0.2 s at 1 kHz, 2 s at 100 Hz). A steady input still whistles (−30 dBFS at fc gives −5 dBFS). The resonance law is unchanged below about res 82 %.
  - **Resonance limiter** (after Kassian Troyer's Reaktor reconstruction): half of filter 2's amplitude-dependent damping follows the band-pass power averaged over about 30 ms, so a loud resonance stays held back briefly. It is smooth, so aliasing improved: −135 dBc at 4x (was −129.5) and −99 dBc at 2x (was −90).
  - Golden renders: the 10 Sherman scenarios were re-captured (the BPF and dynamics renders are unchanged).
- **Changed: the Ladder now follows the Minimoog Model D filter board** (service manual fig. 9-11 and 9-17, supplied by you). The ladder core already matched the literature (Huovilainen; D'Angelo & Välimäki; Stinchcombe; see docs/independent-review/LADDER_LITERATURE_CHECK.md). What the board adds:
  - **Emphasis law:** R14 is a 50 kΩ reverse-audio rheostat in series with REGEN CAL (R73, 1 kΩ) and R76 (330 Ω) to AC ground. The loop gain is k = 15.17 · Rb/(R14 + 1330): 15.17 is the gain-recovery pair (gm 0.169 S into 1180 Ω) times the R7/R3 tap (180/1180). So k runs 0.13 (Emphasis 0) → 1.06 (50 %) → 4 (90 %) → 5.04 (100 %); v1.5 used 0 → 4.3. Self-oscillation now starts at 90 %.
  - **Couplings:** C5/C1 (0.22 µF into 47 kΩ, 15.4 Hz) AC-couple the ladder output, both in the output and inside the loop. C10 (10 µF) couples the feedback, with its corner set by R14 (12 Hz at full Emphasis). The phase lead stops self-oscillation below about 120 Hz cutoff, and oscillation runs slightly sharp just above that (+84 c at 200 Hz).
  - **Gain-recovery pair:** Q7/Q5 is an undegenerated differential pair, so it saturates (tanh) at the ladder's own 2 V_T scale. It is now in the output and in the loop.
  - **Scope:** the board applies to the low-pass ladder only. HP ALT (a pole-mix, not a Minimoog circuit) is bit-identical to before. The 12 dB tap, which a Minimoog doesn't have, now goes through the same output-pair saturation.
  - **Measured side effects:** self-oscillation is about 3.3 dB louder (k = 5.04 instead of 4.3). Pitch is −30 c at 1–5 kHz (validate allows ±100 c). Aliasing in Reference mode is unchanged (4x −112.3 dBc, was −112.2); 1x is −25.3 dBc (was −32.8), but Reference never runs the Ladder below 4x. A numerical fault still reaches fault containment (the raw state passes through above 1e6). The self-oscillation bound in validate's sample-rate test rose from 1.3 to 1.6, with the reason recorded in the test.
  - **Assumptions:** REGEN CAL is set so oscillation starts at Emphasis 9 (the calibration procedure is not in the scan); audio taper is 10 % at mid-rotation; the Drive level mapping is unchanged.
  - Golden renders: every Ladder render changed, and so did every scenario that starts from the power-on default (the Ladder fades out over the first ~25 ms). The re-capture documents this.
- **New UI:** an ENGINE strip at the right edge showing the mode, the high-oversampling choice, and the factors actually running. Two new Live parameters, appended; all 79 earlier ones are unchanged.
- **Compatibility:**
  - Earlier Sets open in REFERENCE. Choose CREATIVE to get v1.5's oversampling factor back.
  - Golden renders:

    | Baseline | v1.6 result |
    |---|---|
    | Dynamics, 21 | 14 bit-identical; 7 change ("opto limit emph", and the 6 chain + filters scenarios via the K35 high-pass) |
    | LPF/HPF, 48 | 18 bit-identical; 30 change (Sherman, Steiner, device power-on, and every scenario using the HPF via the K35 high-pass) |
    | BPF, 35 | 34 change by at most −87 dBFS (SVF) or −115 dBFS (the startup crossfade only) |

    These changes are documented and gated.
- **Tests:**
  - `tests/v16_tests.py` (15 checks)
  - `tests/golden.py check-v16`
  - `compat.py --allow-dsp`
  - Suite: 95/95 + 29/29 + UI 47/47
- **Not yet compiled in Max.** The GenExpr is now about 14,000 lines.

## v1.5 — premium analogue UI (presentation only)

- New design system: one amber accent on a charcoal/graphite chassis, metallic hairlines, header bands and consistent dial, button and segment sizes (`source/device/ui_theme.py`).
- Hybrid UI: native live.* controls remain the only parameters. Three jsui/mgraphics components are added:
  - illuminated suggested-order buttons, tied to Chain Order (a v1.3 bug made them latch independently)
  - a routing diagram drawn from the engine's real topology
  - a BPF architecture glyph
- Availability colouring: controls that are bypassed, or not read by the current configuration, are dimmed but stay editable. There are 13 rules, each checked against the DSP source.
- The processing chain has four modules with identical anatomy, including GATE. The centre strip is split into ROUTING and PROCESSING. Routing is now a horizontal selector with a diagram.
- Info View text for every control.
- Tests:
  - `compat.py --ui`: presentation-only compatibility; the gen~ code must be byte-identical to v1.4
  - `tests/ui_tests.py`: 47 checks
  - `tools/jsui_sim.js`
- DSP, parameters, automation, MIDI and presets are unchanged. Not yet validated in Max or Live: see docs/UI_VALIDATION.md.

## v1.4: filter routing
- **New:** Filter Routing SERIES / PARALLEL / HYBRID for the LPF, HPF and BPF, plus three parallel level controls and a live signal-flow readout. 4 new Live parameters; the default is SERIES.
- **New UI:** a FILTER ROUTING strip at the right edge (device width 1774 → 1948). No existing object moved.
- **Unchanged:** SERIES is bit-identical to v1.3 (48 LPF/HPF + 35 BPF + 21 dynamics golden renders); patch compatible with the v1.1, v1.2 and v1.3 snapshots.
- **Tests:** `routing_tests.py` (18 checks). Suite: 95/95.

## v1.3: reorderable dynamics chain
- **New:** a PROCESSING CHAIN with Tube saturation, an LA-2A-inspired optical compressor and an API 2500-inspired VCA compressor, in any of six orders. Drag-and-drop blocks, three suggested configurations, a Chain Order parameter, and a click-free state-copy crossfade on reordering.
- **New:** an independent Gate, an external sidechain key (`plugin~ 3 4` + KEY FROM), INT/CHAIN/EXT detector sources, SC filters, stereo link, key listen, and per-module ON/In/Out/Mix with meters. 44 new Live parameters, all off or neutral by default.
- **Unchanged:** LPF, HPF and BPF DSP, parameters, automation and MIDI mappings. Bit-exact against the v1.1 and v1.2 golden renders; patch compatible with both v1.1 and v1.2 snapshots.
- **Device width:** 1066 → 1774.
- **Tests:** `dyn_tests.py` (35 checks) + BPF golden baseline. Suite: 77/77.

## v1.2: band-pass engine
- **New:** a third, independent band-pass engine with 5 models (Oberheim SEM, Steiner-Parker, Korg 35/MS-20, ARP 2600 (derived), EMS VCS3 (derived)) and 3 architectures (SVF, CASCADE, MULTIMODE). Controls: Centre, Bandwidth, Q, Resonance, Drive, Compensation, Mix, Position (POST/PRE), On. 11 new Live parameters. See docs/BPF.md.
- **New UI section** to the right of the existing panel (device width 700 → 1066). Existing sections are unchanged.
- **Unchanged:** LPF and HPF DSP, parameters, automation names, MIDI mappings and UI. The BPF is off by default, so v1.1 Sets sound identical.
- **Tests:** bit-exact golden regression (`source/tests/golden.py`), patch compatibility check (`source/tests/compat.py`), 17 new BPF/combined checks (`source/tests/bpf_tests.py`). Suite: 42/42.

## v1.1: circuit-informed models
- TB-303 rebuilt on Stinchcombe's TB-303 configuration; Moog per-stage tanh (Huovilainen); Steiner-Parker as a Sallen-Key with diode strings; SEM OTA integrators; Sherman resonance per published spec. Circuit-reference test.

## v1.0
- Initial LPF/HPF device with six models per stage.

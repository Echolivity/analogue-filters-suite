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
  - Sets that use the K35 high-pass get a gentler low cut, and up to +2.9 dB more level at the resonant peak (+0.1 dB at res 0, +2.1 at 50, +2.9 at 80).
  - Because the HPF powers on as K35, every HPF reference render changes during its start-up crossfade. The residual is exactly zero within 2 s.
- **New UI:** an ENGINE strip at the right edge showing the mode, the high-oversampling choice, and the factors actually running. Two new Live parameters, appended; all 79 earlier ones are unchanged.
- **Compatibility:**
  - Earlier Sets open in REFERENCE. Choose CREATIVE to get v1.5's oversampling factor back.
  - Golden renders:

    | Baseline | v1.6 result |
    |---|---|
    | Dynamics, 21 | 20 bit-identical; 1 changes ("opto limit emph") |
    | LPF/HPF, 48 | 29 bit-identical; the 19 that change are the Sherman and Steiner scenarios and device power-on |
    | BPF, 35 | 34 change by at most −87 dBFS (SVF) or −115 dBFS (the startup crossfade only) |

    These changes are documented and gated.
- **Tests:**
  - `tests/v16_tests.py` (15 checks)
  - `tests/golden.py check-v16`
  - `compat.py --allow-dsp`
  - Suite: 95/95 + 15/15 + UI 47/47
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

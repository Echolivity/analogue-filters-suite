# UI architecture (v1.5)

v1.5 redesigns the interface only. The gen~ code is byte-identical to v1.4. All 79 Live parameters keep their box ids, names, ranges, defaults and wiring, so Live Sets, presets, automation and MIDI maps made with v1.1 to v1.4 load unchanged. `tests/compat.py --ui` enforces this against every earlier release.

The request mentioned a reference screenshot, but none was attached. The look was designed from the written brief: a dark charcoal chassis, a single amber accent, metallic hairlines and hardware-style section headers.

## Hybrid structure

| Layer | Objects | Role |
|---|---|---|
| Native parameters | `live.dial`, `live.tab`, `live.text`, `live.menu` | Every automatable, MIDI-mappable or preset-stored value. They stay the only source of truth. |
| Custom graphics | `jsui` (mgraphics): `df_button.js`, `df_routing.js`, `df_arch.js` | Illuminated buttons for non-parameter actions, the routing diagram and the BPF topology glyph. |
| Decoration with a job | `panel`, `comment` | Section plates, header bands, group separators and captions. |

### The sync rule

A custom control never stores a value. It displays the value it receives from its native object and, when clicked, sends a request into that object. The native object then outputs the value, which updates both the DSP and the graphic. This keeps automation, MIDI mapping, presets and undo native.

The only clickable custom controls are the three suggested chain orders. Each one writes to the **Chain Order** parameter and is lit when Chain Order equals its order. In v1.3 these buttons latched independently and could show the wrong state; v1.5 fixes that.

The routing diagram and the architecture glyph are display-only and have no outlets.

### Availability ("unavailable" state)

A control that is bypassed, or not read by the current configuration, is drawn in reduced contrast. Its value arc is grey and its labels are dimmed. The mechanism changes colour attributes only. Per the Max reference, `active 0` would also block mouse input, so v1.5 never sends it and every control stays editable: you can set up a stage before switching it in. The 13 rules are generated into `build/device/ui_availability.json`. The tests check each rule against the DSP source.

| Control(s) | Dimmed when | Why (DSP) |
|---|---|---|
| LPF / HPF / BPF section controls | That stage is OFF | Clean bypass |
| BPF Bandwidth | Architecture = SVF | SVF reads only Q |
| BPF Q, BPF Compensation | Architecture = MULTI | Pole mix reads only Bandwidth; tap gain is 1 |
| BPF Position | Routing ≠ SERIES | PARALLEL and HYBRID ignore it |
| Stage Order | Routing = PARALLEL | No LP/HP order in a parallel sum |
| LP Lvl, HP Lvl | Routing ≠ PARALLEL | Used only in the parallel sum |
| BP Lvl | Routing = SERIES | Used in PARALLEL and HYBRID |
| TUBE / OPTO / VCA / GATE page controls | That module is OFF | Module bypassed |

## Design system (`source/device/ui_theme.py`)

**Colour roles.** Each colour has one job:

| Role | Colour | Hex |
|---|---|---|
| Chassis | Charcoal | `#141312` |
| Plates | Graphite | `#211f1d` |
| Header bands | — | `#2b2825` |
| Wells | — | `#171615` |
| Off button | — | `#34312d` |
| Metallic border | — | `#4f4841` |
| Hairline | — | `#7c7266` |
| Amber accent (ON, selected, value arcs, active signal path) | Amber | `#f2a03a` |
| ON but unavailable | Dimmed amber | `#6b4a24` |
| Text | — | `#ece4d4` |
| Labels | — | `#a39a8c` |
| Unavailable labels | — | `#5e5850` |
| Text on amber | — | `#1a1410` |

**Contrast.** Every ratio is tested:

| Pair | Ratio |
|---|---|
| Text on plate | 13:1 |
| Labels on plate | 5.9:1 |
| Text on amber | 8.6:1 |
| Unavailable labels on plate (deliberately reduced) | 2.3:1 |

**Sizing:**
- Section plates span y 4–165 inside Live's 169 px device height, with an 18 px header band.
- Primary frequency dials are 108×100. Secondary dials are 54–56 wide. Dynamics page dials are 48×46.
- Buttons are 14–15 px high. ON switches are 36×14.

**Button states** (`df_button.js`, tested):

| State | Look |
|---|---|
| off | Graphite |
| hover | Brighter graphite |
| pressed | Darker, with an inner shadow and the label shifted down |
| selected | Amber, with a top highlight |
| selected + hover | Brighter amber |
| selected + pressed | Darker amber |
| unavailable / unavailable + on | Reduced contrast; clicks ignored |

Modes are `select`, `toggle` and `momentary`. A release outside the button cancels the click.

**Native controls** (live.tab / live.text) use:
- amber for ON
- graphite for off
- amber focus borders
- a dimmed variant in their inactive colours, which Live shows when the device itself is switched off

Native objects don't expose hover or pressed colours; Live draws focus itself.

## Sections

| Section | What changed |
|---|---|
| LOW-PASS / HIGH-PASS | Same hierarchy: header (title + ON), model menu, dominant cutoff dial, Res / Drive / Comp row, model-specific Character dial with its live name, slope segments and the native/extension info. |
| DUB FILTER | Split into ROUTING (stage order) and PROCESSING (oversample, output, soft clip) by a hairline and amber group labels. |
| BAND-PASS | Grouped as width (BW, Q), tone (Res, Drive), level (Comp, Mix) and Position (labelled SERIES). A topology glyph shows the selected architecture: SVF = one 2-pole SVF; CASC = HP 2P into LP 2P; MULTI = 4 ladder poles mixed. It also says which width controls are in use. |
| PROCESSING CHAIN | Four modules with identical anatomy, including GATE: header band with name and ON, IN/OUT (or OPEN/KEY) meters, a GR readout for OPTO and VCA, a caption, and the drag grip. Header plates and captions move with their block for all six orders. The suggested orders are illuminated buttons tied to Chain Order. KEY LISTEN is a full-height segment control. |
| PROCESSING CHAIN · VCA page | Drawn as an API 2500-style faceplate (v1.6): black face, white section legends in the 2500's front-panel order (COMPRESSOR · TONE · SIDECHAIN / LINK · OUTPUT), silver knobs with captions underneath, and coloured push-button rows: knee white, thrust yellow, type blue, sidechain source green, auto red, detector silver. No logo is reproduced. Dimming when VCA is off uses the page's own colours (a deferred pass after the v1.5 availability messages). |
| FILTER ROUTING | Horizontal SERIES / PARALLEL / HYBRID selector. The diagram is drawn from the same state the engine uses: route, stage order, BPF position and the three ON switches. The active path is amber; a bypassed series stage is hollow and still passes signal; a bypassed parallel branch goes grey; DRY appears when all parallel branches are off. The text flow line remains underneath. |

## Interaction

All value interaction is native Live behaviour of live.* controls: drag, fine drag with a modifier, typed entry, reset to default, MIDI/key mapping and automation. Every parameter has a default (`parameter_initial`), so reset returns to the documented default.

Every parameter and custom control now has Info View text (`annotation_name` + `annotation`, plus the Max `hint`): what it does, its range or options with the unit, and its default. The range and default text is generated from the parameter definition, so it cannot drift. Texts are in `source/device/ui_info.py`.

## Files

- `DubFilter.amxd`, `DubFilter.maxpat`
- `df_button.js`, `df_routing.js`, `df_arch.js` — keep these in the same folder as the device. For distribution, open the device in the Max editor and use **Freeze Device** to embed them; this could not be done here.
- `source/device/ui_theme.py` (tokens), `ui_info.py` (Info View text), `jsui/` (component sources)
- `source/tools/jsui_sim.js` — runs a jsui file outside Max with a mocked mgraphics, for tests and previews
- `source/tests/ui_tests.py` — the UI gate
- `docs/ui/*.png` — before and after renders

## Parameter-to-control mapping

| Section | Control (varname) | Live parameter (long / short) | Object | Range / options | Default | Dimmed when |
|---|---|---|---|---|---|---|
| LOW-PASS | `l_on` | LPF On / LPF On | live.text | off, on | on | — |
| LOW-PASS | `l_model` | LPF Model / LPF Model | live.menu | 01 Sherman Filterbank, 02 Korg 35 / MS-20, 03 Moog-style Ladder, 04 Steiner-Parker, 05 Oberheim SEM, 06 TB-303 Diode Ladder, 07 ARP 2600 (4012) | 03 Moog-style Ladder | LPF bypassed |
| LOW-PASS | `l_cut` | LPF Cutoff / LPF Cut | live.dial | 20 … 20000 | 20000 | LPF bypassed |
| LOW-PASS | `l_res` | LPF Resonance / LPF Res | live.dial | 0 … 100 | 0 | LPF bypassed |
| LOW-PASS | `l_drive` | LPF Drive / LPF Drive | live.dial | 0 … 100 | 0 | LPF bypassed |
| LOW-PASS | `l_comp` | LPF Compensation / LPF Comp | live.dial | 0 … 100 | 100 | LPF bypassed |
| LOW-PASS | `l_char` | LPF Character / LPF Char | live.dial | 0 … 100 | 0 | LPF bypassed |
| LOW-PASS | `l_slope` | LPF Slope / LPF Slope | live.tab | 12, 24, 36, 48 | 24 | LPF bypassed |
| HIGH-PASS | `h_on` | HPF On / HPF On | live.text | off, on | on | — |
| HIGH-PASS | `h_model` | HPF Model / HPF Model | live.menu | 01 Sherman Filterbank, 02 Korg 35 / MS-20, 03 Moog 904B HP, 04 Steiner-Parker, 05 Oberheim SEM | 02 Korg 35 / MS-20 | HPF bypassed |
| HIGH-PASS | `h_cut` | HPF Cutoff / HPF Cut | live.dial | 20 … 2000 | 20 | HPF bypassed |
| HIGH-PASS | `h_res` | HPF Resonance / HPF Res | live.dial | 0 … 100 | 0 | HPF bypassed |
| HIGH-PASS | `h_drive` | HPF Drive / HPF Drive | live.dial | 0 … 100 | 0 | HPF bypassed |
| HIGH-PASS | `h_comp` | HPF Compensation / HPF Comp | live.dial | 0 … 100 | 100 | HPF bypassed |
| HIGH-PASS | `h_char` | HPF Character / HPF Char | live.dial | 0 … 100 | 0 | HPF bypassed |
| HIGH-PASS | `h_slope` | HPF Slope / HPF Slope | live.tab | 12, 24, 36, 48 | 12 | HPF bypassed |
| DUB FILTER | `order_sel` | Stage Order / Order | live.tab | LP>HP, HP>LP | LP>HP | PARALLEL has no LP/HP order |
| DUB FILTER | `ovs_sel` | Oversampling / OS | live.tab | 1x, 2x | 1x | — |
| DUB FILTER | `out_db` | Output / Output | live.dial | -24 … 12 | 0 | — |
| DUB FILTER | `softclip` | Soft Clip / Soft Clip | live.text | off, on | on | — |
| BAND-PASS | `b_on` | BPF On / BPF On | live.text | off, on | off | — |
| BAND-PASS | `b_model` | BPF Model / BPF Model | live.menu | 01 Oberheim SEM, 02 Steiner-Parker, 03 Korg 35 / MS-20, 04 ARP 2600 - derived, 05 EMS VCS3 - derived | 01 Oberheim SEM | BPF bypassed |
| BAND-PASS | `b_arch` | BPF Architecture / BPF Arch | live.tab | SVF, CASC, MULTI | SVF | BPF bypassed |
| BAND-PASS | `b_freq` | BPF Centre / BPF Freq | live.dial | 30 … 12000 | 1000 | BPF bypassed |
| BAND-PASS | `b_bw` | BPF Bandwidth / BPF BW | live.dial | 0.2 … 6 | 2 | SVF does not read Bandwidth |
| BAND-PASS | `b_q` | BPF Q / BPF Q | live.dial | 0.5 … 10 | 0.707 | MULTI does not read Q or Compensation |
| BAND-PASS | `b_res` | BPF Resonance / BPF Res | live.dial | 0 … 100 | 0 | BPF bypassed |
| BAND-PASS | `b_drive` | BPF Drive / BPF Drive | live.dial | 0 … 100 | 0 | BPF bypassed |
| BAND-PASS | `b_comp` | BPF Compensation / BPF Comp | live.dial | 0 … 100 | 100 | MULTI does not read Q or Compensation |
| BAND-PASS | `b_mix` | BPF Mix / BPF Mix | live.dial | 0 … 100 | 100 | BPF bypassed |
| BAND-PASS | `b_pos` | BPF Position / BPF Pos | live.tab | POST, PRE | POST | BPF Position applies to SERIES only |
| PROCESSING CHAIN | `c_order` | Chain Order / Order | live.menu | TUBE > OPTO > VCA, TUBE > VCA > OPTO, OPTO > TUBE > VCA, OPTO > VCA > TUBE, VCA > TUBE > OPTO, VCA > OPTO > TUBE | TUBE > OPTO > VCA | — |
| PROCESSING CHAIN | `key_listen` | Key Listen / Key Listen | live.tab | OFF, OPTO, VCA, GATE | OFF | — |
| PROCESSING CHAIN | `t_on` | Tube On / Tube On | live.text | off, on | off | — |
| PROCESSING CHAIN | `o_on` | Opto On / Opto On | live.text | off, on | off | — |
| PROCESSING CHAIN | `v_on` | VCA On / VCA On | live.text | off, on | off | — |
| PROCESSING CHAIN | `g_on` | Gate On / Gate On | live.text | off, on | off | — |
| PROCESSING CHAIN · TUBE page | `t_in` | Tube Input / Tube In | live.dial | -24 … 24 | 0 | T module bypassed |
| PROCESSING CHAIN · TUBE page | `t_drive` | Tube Drive / Drive | live.dial | 0 … 100 | 30 | T module bypassed |
| PROCESSING CHAIN · TUBE page | `t_bias` | Tube Bias / Bias | live.dial | -100 … 100 | 20 | T module bypassed |
| PROCESSING CHAIN · TUBE page | `t_tone` | Tube Tone / Tone | live.dial | 1000 … 20000 | 12000 | T module bypassed |
| PROCESSING CHAIN · TUBE page | `t_mix` | Tube Mix / Mix | live.dial | 0 … 100 | 100 | T module bypassed |
| PROCESSING CHAIN · TUBE page | `t_out` | Tube Output / Tube Out | live.dial | -24 … 24 | 0 | T module bypassed |
| PROCESSING CHAIN · TUBE page | `t_auto` | Tube Auto Gain / Auto Gain | live.text | off, on | on | T module bypassed |
| PROCESSING CHAIN · OPTO page | `o_in` | Opto Input / Opto In | live.dial | -24 … 24 | 0 | O module bypassed |
| PROCESSING CHAIN · OPTO page | `o_pr` | Opto Peak Reduction / Peak Red | live.dial | 0 … 100 | 40 | O module bypassed |
| PROCESSING CHAIN · OPTO page | `o_emph` | Opto HF Emphasis / HF Emph | live.dial | 0 … 100 | 0 | O module bypassed |
| PROCESSING CHAIN · OPTO page | `o_hpf` | Opto SC HPF / SC HPF | live.dial | 20 … 500 | 20 | O module bypassed |
| PROCESSING CHAIN · OPTO page | `o_link` | Opto Link / Link | live.dial | 0 … 100 | 100 | O module bypassed |
| PROCESSING CHAIN · OPTO page | `o_mix` | Opto Mix / Mix | live.dial | 0 … 100 | 100 | O module bypassed |
| PROCESSING CHAIN · OPTO page | `o_out` | Opto Gain / Gain | live.dial | -24 … 24 | 0 | O module bypassed |
| PROCESSING CHAIN · OPTO page | `o_mode` | Opto Mode / Mode | live.tab | COMP, LIMIT | COMP | O module bypassed |
| PROCESSING CHAIN · OPTO page | `o_src` | Opto SC Source / SC Src | live.tab | INT, CHAIN, EXT | INT | O module bypassed |
| PROCESSING CHAIN · VCA page | `v_in` | VCA Input / VCA In | live.dial | -24 … 24 | 0 | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_thr` | VCA Threshold / Thresh | live.dial | -50 … 0 | -20 | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_rel` | VCA Release / Release | live.dial | 0.05 … 3 | 0.3 | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_hpf` | VCA SC HPF / SC HPF | live.dial | 20 … 500 | 20 | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_link` | VCA Link / Link | live.dial | 0 … 100 | 100 | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_mix` | VCA Mix / Mix | live.dial | 0 … 100 | 100 | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_out` | VCA Output / VCA Out | live.dial | -24 … 24 | 0 | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_ratio` | VCA Ratio / Ratio | live.menu | 1.5:1, 2:1, 3:1, 4:1, 6:1, 10:1, inf:1 | 4:1 | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_att` | VCA Attack / Attack | live.menu | .03ms, .1ms, .3ms, 1ms, 3ms, 10ms, 30ms | 1ms | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_knee` | VCA Knee / Knee | live.tab | HARD, MED, SOFT | HARD | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_thrust` | VCA Thrust / Thrust | live.tab | NORM, MED, LOUD | NORM | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_type` | VCA Type / Type | live.tab | NEW, OLD | NEW | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_auto` | VCA Auto Makeup / Auto Makeup | live.text | off, on | off | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_src` | VCA SC Source / SC Src | live.tab | INT, CHAIN, EXT | INT | V module bypassed |
| PROCESSING CHAIN · VCA page | `v_det` | VCA Detector / Detector | live.tab | RMS, PEAK (225L) | RMS | — (v1.6, below the dials; shown with the VCA page) |
| PROCESSING CHAIN · GATE page | `g_thr` | Gate Threshold / Thresh | live.dial | -80 … 0 | -40 | G module bypassed |
| PROCESSING CHAIN · GATE page | `g_att` | Gate Attack / Attack | live.dial | 0.1 … 50 | 1 | G module bypassed |
| PROCESSING CHAIN · GATE page | `g_hold` | Gate Hold / Hold | live.dial | 0 … 500 | 20 | G module bypassed |
| PROCESSING CHAIN · GATE page | `g_rel` | Gate Release / Release | live.dial | 5 … 2000 | 150 | G module bypassed |
| PROCESSING CHAIN · GATE page | `g_range` | Gate Range / Range | live.dial | -80 … 0 | -80 | G module bypassed |
| PROCESSING CHAIN · GATE page | `g_hpf` | Gate Key HPF / Key HPF | live.dial | 20 … 2000 | 20 | G module bypassed |
| PROCESSING CHAIN · GATE page | `g_lpf` | Gate Key LPF / Key LPF | live.dial | 200 … 20000 | 20000 | G module bypassed |
| PROCESSING CHAIN · GATE page | `g_src` | Gate Key Source / Key Src | live.tab | INT, CHAIN, EXT | INT | G module bypassed |
| FILTER ROUTING | `flt_route` | Filter Routing / Routing | live.tab | SERIES, PARALLEL, HYBRID | SERIES | — |
| FILTER ROUTING | `par_l` | Parallel LPF Level / LP Lvl | live.dial | -40 … 6 | 0 | LP/HP levels apply to PARALLEL only |
| FILTER ROUTING | `par_h` | Parallel HPF Level / HP Lvl | live.dial | -40 … 6 | 0 | LP/HP levels apply to PARALLEL only |
| FILTER ROUTING | `par_b` | Parallel BPF Level / BP Lvl | live.dial | -40 … 6 | 0 | BP level applies to PARALLEL and HYBRID |

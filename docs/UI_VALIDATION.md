# UI validation report (v1.5)

## Summary

| Check | Result |
|---|---|
| DSP | **Unchanged.** The gen~ code is byte-identical to v1.4, and all bit-exact golden renders pass (48 LPF/HPF, 35 BPF, 21 dynamics). |
| Engine suite | 95/95 pass. |
| Compatibility | Parameters, connections and gen~ Params are intact against the v1.1, v1.2, v1.3 and v1.4 snapshots (`compat.py --ui`). |
| UI suite (`tests/ui_tests.py`) | **47/47 pass.** |

## Not done: Max and Live

**This release has not been opened in Max or Ableton Live.** None of the following has been verified:
- Max's real rendering
- jsui under Max's JavaScript engine (the components are plain ES5 and use only documented jsui and mgraphics calls; they were run here under Node with a mock)
- hover events
- colour-attribute messages at runtime
- Freeze Device
- display scaling, CPU in Live
- automation, MIDI mapping and preset recall

The pictures in `docs/ui/` are approximate renders made by `device/preview.py`. They are not screenshots. The jsui parts of those renders do come from running the real component code.

The spec's Phase 5 needs a person with Max and Live. Use the checklist below.

### Manual checklist (Live 12, Max 8.6 or later)

1. Put `DubFilter.amxd` and the three `df_*.js` files in one folder, then load the device on an audio track.
   - Check: the Max window shows no "can't find file" errors.
   - Check: the three displays draw (the preset buttons, the routing diagram and the BPF glyph).
2. Load a Live Set saved with v1.4.
   - Check: every value, automation lane and MIDI map comes back.
   - Check: a null test of the audio against v1.4 renders silence.
3. Click WARM DUB, PUNCH & COLOUR and FINAL COLOUR.
   - Check: Chain Order changes and the blocks move.
   - Check: exactly one button is lit when the order matches a preset, and none when it doesn't.
   - Check: automating Chain Order updates the buttons.
4. Hover over and press a preset button.
   - Check: the hover brightening and the recessed press state appear.
5. Step Routing through SERIES, PARALLEL and HYBRID.
   - Check: the diagram and the text flow line agree.
   - Toggle LP, HP and BP ON, Stage Order and BPF Position.
   - Check: bypassed stages show hollow in series and grey in parallel. DRY appears with all three off in PARALLEL.
6. Availability.
   - With BPF Architecture on SVF, BW should be dim. On MULTI, Q and Comp should be dim.
   - Check: dim controls can still be dragged and automated.
   - Switch the device itself off. Check: Live's inactive colours apply.
7. Info View: hover over the controls and check the descriptions.
8. Use Freeze Device, then reload from another folder. Check: the displays still draw.
9. CPU: compare Live's CPU meter with v1.4. The jsui components redraw only on state changes and run no timers.
10. Check the device at 100% and 200% Live zoom.

## Offline checks

| | Check | Detail |
|---|---|---|
| PASS | 79 parameters, identical ids, names and definitions to v1.4 | 79 parameters |
| PASS | parameter table (Live identity) unchanged |  |
| PASS | gen~ code byte-identical to v1.4 (no DSP change) |  |
| PASS | all v1.4 connections kept |  |
| PASS | every parameter control visible in presentation |  |
| PASS | every parameter has annotation_name, annotation and hint |  |
| PASS | annotations state range/options and default |  |
| PASS | jsui controls annotated |  |
| PASS | all presented objects inside the device (w=2132, h=169) |  |
| PASS | no two interactive controls overlap (each edit page) | [] |
| PASS | scripting messages reference only existing objects | [] |
| PASS | 6 chain orders: blocks never overlap each other or the gate block |  |
| PASS | preset button 0: Chain Order -> button and button -> Chain Order |  |
| PASS | preset button 4: Chain Order -> button and button -> Chain Order |  |
| PASS | preset button 3: Chain Order -> button and button -> Chain Order |  |
| PASS | routing diagram follows flt_route |  |
| PASS | routing diagram follows order_sel |  |
| PASS | routing diagram follows b_pos |  |
| PASS | routing diagram follows l_on |  |
| PASS | routing diagram follows h_on |  |
| PASS | routing diagram follows b_on |  |
| PASS | arch glyph follows b_arch and b_on |  |
| PASS | jsui displays have no outlet into the patch |  |
| PASS | no 'active' message sent to any control (all stay editable) |  |
| PASS | DSP: SVF reads Q (_R) and not Bandwidth (_gh/_gl/_wb) |  |
| PASS | DSP: CASC reads Bandwidth (_gh/_gl) and Q (_R) |  |
| PASS | DSP: MULTI reads Bandwidth (_wb), not Q (_R) |  |
| PASS | DSP: MULTI raw gain is 1, so Compensation has no effect |  |
| PASS | 13 availability rules: every rule reaches both states |  |
| PASS | every availability target is a parameter control |  |
| PASS | arch glyph 'USES' labels agree with the dimming rules and the DSP |  |
| PASS | DSP: PARALLEL sums rt_rl, rt_rh, rt_rb; HYBRID adds only rt_rb |  |
| PASS | level dials dimmed exactly where the DSP ignores them |  |
| PASS | routing diagram: 96 states draw without error | [] |
| PASS | routing diagram topology == engine flow for all 96 states | [] |
| PASS | button select mode: off/hover/pressed/selected/selected_hover/selected_pressed/unavailable states | ['off', 'hover', 'pressed', 'selected', 'selected_hover', 'selected_pressed', 'unavailable_on', 'unavailable'] |
| PASS | button: click inside outputs its index, release outside cancels, unavailable ignores clicks | [[0, 0]] |
| PASS | button toggle: requests the opposite value and waits for the parameter echo |  |
| PASS | button momentary: 1 on press, 0 on release |  |
| PASS | contrast TEXT on PLATE >= 7:1 | 13.0:1 |
| PASS | contrast LABEL on PLATE >= 4.5:1 | 5.9:1 |
| PASS | contrast LABEL on HEADER >= 4.5:1 | 5.3:1 |
| PASS | contrast LABEL on OFF button >= 3.5:1 | 4.7:1 |
| PASS | contrast TEXT_ON on AMBER >= 7:1 | 8.6:1 |
| PASS | contrast AMBER on PLATE >= 4.5:1 | 7.7:1 |
| PASS | unavailable labels are reduced but visible (1.8..3:1 on plate) | 2.3:1 |
| PASS | unavailable arc distinct from active arc | 4.5:1 |

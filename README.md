# Dub Filter — Max for Live audio effect (Ableton Live 12)

A two-stage performance filter for dub mixing in the Ariwa tradition: big resonant low-pass sweeps, sudden bass removal and instant return, and expressive hands-on control. Each stage has its own choice of six analogue-inspired filter models.

![panel preview](docs/preview.png)
*Approximate layout preview rendered from the patch file. Max draws the live.* controls in its own style.*

## What's in the box

| | |
|---|---|
| `DubFilter.amxd` | The device. Drag onto an audio track. |
| `DubFilter.maxpat` | Editable Max patch (identical content). |
| `docs/INSTALL.md` | Installation, plus a fallback procedure if the .amxd will not load. |
| `docs/MODELS.md` | The six models, the capability matrix, approximations and limitations, and how to add a model. |
| `docs/PARAMETERS.md` | All 20 parameters, automation names, CHARACTER per model, MIDI-mapping tips. |
| `docs/ARCHITECTURE.md` | Signal flow, filter topologies, smoothing, state handling, CPU strategy. |
| `docs/VALIDATION.md` | Validation report with frequency-response plots, tables, CPU benchmark and a manual test checklist for Live. |
| `source/`, `build.sh` | Generator, transpiler/checker, test harness, device builder. |

## The instrument

- **LOW-PASS** (amber) and **HIGH-PASS** (copper) stages, each with a large CUTOFF knob, RESONANCE, DRIVE, COMP, a model-specific CHARACTER knob, a 12/24/36/48 dB slope selector and ON.
- **Models:** 01 Sherman Filterbank · 02 Korg 35 / MS-20 · 03 Moog-style Ladder · 04 Steiner-Parker · 05 Oberheim SEM · 06 TB-303 Diode (LPF only). Each is built from the published circuit or circuit analysis of its namesake (sources in MODELS.md), and each matches its circuit's transfer function to within 0.05 dB. The HPF menu has no 303, and the ladder's highpass is labelled "ALT pole-mix" in the menu.
- **Centre strip:** stage ORDER (LP>HP / HP>LP), 1x/2x OVERSAMPLE, OUTPUT, SOFT CLIP.
- **OPEN zones:** LPF fully clockwise or HPF fully anticlockwise crossfades that stage to the dry signal, so "both open" is transparent.
- Every control is smoothed per sample. Model, slope, order and oversampling changes are click-free during playback.

## Classic moves
- **The drop:** HPF to about 300–600 Hz on the downbeat, back to OPEN on the "one". Map it to a pad (see PARAMETERS.md).
- **The long sweep:** Ladder or Sherman LPF, Resonance 60–80 %, a slow sweep from OPEN to 200 Hz over a few bars.
- **The scream:** Sherman with FEEDBACK at 40–70 %, resonance just under self-oscillation. Ride the cutoff.
- **MS-20 rig:** both stages on K35, Order HP>LP, resonance up on both. Narrow the band and sweep.

## Status
The DSP was validated offline by running the exact gen~ code (25 of 25 checks pass, including a comparison of every model against its circuit's transfer function; see VALIDATION.md). The device file itself has **not yet been opened in Max or Live**. Please run the short manual checklist at the end of VALIDATION.md on first use.

The models are inspired by the named instruments. They are not affiliated with, endorsed by, or claimed to be equivalent to products of Sherman, Korg, Moog, Steiner-Parker, Oberheim or Roland.

# Installation

## Requirements
- Ableton Live 12 Suite, or Live 12 Standard with the Max for Live add-on. Max 8.6+ is bundled with Live 12.
- No externals, JavaScript or extra files. The DSP is embedded in the device's gen~ object.

## Install
1. Copy `DubFilter.amxd` into your User Library, for example
   `~/Music/Ableton/User Library/Presets/Audio Effects/Max Audio Effect/` (macOS) or
   `\Users\<you>\Documents\Ableton\User Library\Presets\Audio Effects\Max Audio Effect\` (Windows).
2. In Live's browser go to **User Library → Presets → Audio Effects → Max Audio Effect** and drag **DubFilter** onto an audio track or return. You can also drag the .amxd file straight from Finder/Explorer onto a track.
3. The first time it loads, gen~ compiles the engine. This takes a second or two, after which the panel is live.

**Recommended dub setup:** put the device on a return or group track fed by the drums and bass. Keep LPF CUTOFF fully clockwise and HPF CUTOFF fully anticlockwise (both OPEN, fully transparent), then play the two big knobs.

## If the .amxd does not load
The .amxd was assembled by a script, not saved from Max's editor. If Live refuses it, or it opens without a panel, rebuild it from the editable patch:

1. In Live, drag **Max Audio Effect** (Max for Live → Max Audio Effect) onto a track, then click its **Edit** button.
2. In the Max editor that opens, select all and delete (this removes the default `plugin~`/`plugout~`).
3. In the same Max application, choose **File → Open** and open `DubFilter.maxpat`. Select all (Cmd/Ctrl+A), copy, close it, and paste into the device editor.
4. Open **View → Patcher Inspector** and set **Open in Presentation** = on and **Device Width** = 1948.
5. Choose **File → Save As…**, name it `DubFilter.amxd`, and save it in the User Library path above.

To rebuild every file from source (for example after editing a model), run `./build.sh` (Python 3 with numpy, scipy and matplotlib, plus a C compiler). It regenerates the GenExpr, transpiles and checks it, runs the validation suite, and rebuilds the .maxpat and .amxd.

## Editing the DSP inside Max
Double-click the `gen~` object (unlock the patch first) and you will see one codebox holding the whole engine. You can edit it in place, but it is generated code. For lasting changes, edit `source/src/build_genexpr.py` and run `./build.sh`, so the validation suite runs against your change.

## External key (sidechain) for the Opto, VCA and Gate (v1.3)
1. In the device's PROCESSING CHAIN section, choose the source track in the **KEY FROM** selector (bottom right).
2. Set the module's source to **EXT** (Opto or VCA page: SC source; Gate page: KEY SOURCE). The **EXT KEY** meter next to the gate shows the incoming key.
3. **If KEY FROM shows no tracks:** the `live.routing` object could not be tested here. Open the device in Max (Edit), select the KEY FROM object, and in its Inspector point it at the device's audio input **3/4**. The DSP reads the key from `plugin~ 3 4`.

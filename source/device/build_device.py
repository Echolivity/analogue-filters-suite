#!/usr/bin/env python3
"""Builds the Max for Live device: DubFilter.maxpat (editable) and
DubFilter.amxd (Live audio effect) from build/dubfilter.genexpr."""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CODE = open(os.path.join(ROOT, "build", "dubfilter.genexpr")).read()

W, H = 700, 169
# ---- palette (RGBA 0..1) ----
BG = [0.086, 0.082, 0.078, 1.0]        # near-black chassis
PANEL = [0.133, 0.125, 0.118, 1.0]     # charcoal section plates
STRIP = [0.110, 0.104, 0.098, 1.0]
AMBER = [0.961, 0.627, 0.200, 1.0]     # LPF accent
COPPER = [0.906, 0.400, 0.176, 1.0]    # HPF accent
CREAM = [0.925, 0.886, 0.800, 1.0]
MUTED = [0.580, 0.553, 0.506, 1.0]
DIM = [0.240, 0.226, 0.212, 1.0]

boxes, lines = [], []
_n = [0]


def oid():
    _n[0] += 1
    return f"obj-{_n[0]}"


def box(maxclass, rect, prect=None, **attrs):
    b = dict(id=oid(), maxclass=maxclass, patching_rect=rect)
    if prect is not None:
        b["presentation"] = 1
        b["presentation_rect"] = prect
    b.update(attrs)
    boxes.append({"box": b})
    return b["id"]


def newobj(text, rect, ni, no, ot):
    return box("newobj", rect, text=text, numinlets=ni, numoutlets=no, outlettype=ot)


def connect(src, so, dst, di):
    lines.append({"patchline": {"source": [src, so], "destination": [dst, di]}})


def valueof(long, short, ptype, lo, hi, init, unit=1, enum=None, exponent=1.0, units=None):
    v = dict(parameter_longname=long, parameter_shortname=short, parameter_type=ptype,
             parameter_mmin=lo, parameter_mmax=hi, parameter_initial_enable=1,
             parameter_initial=[init], parameter_unitstyle=unit)
    if enum is not None:
        v["parameter_enum"] = enum
    if exponent != 1.0:
        v["parameter_exponent"] = exponent
    if units:
        v["parameter_units"] = units
    return {"valueof": v}


# ---------------------------------------------------------------- DSP core
plugin = newobj("plugin~", [30, 700, 60, 22], 2, 2, ["signal", "signal"])
gen_patcher = {
    "fileversion": 1,
    "appversion": {"major": 8, "minor": 6, "revision": 2, "architecture": "x64", "modernui": 1},
    "classnamespace": "dsp.gen",
    "rect": [100, 100, 900, 700],
    "boxes": [
        {"box": {"id": "obj-1", "maxclass": "newobj", "text": "in 1", "numinlets": 0, "numoutlets": 1,
                 "outlettype": [""], "patching_rect": [20, 20, 30, 22]}},
        {"box": {"id": "obj-2", "maxclass": "newobj", "text": "in 2", "numinlets": 0, "numoutlets": 1,
                 "outlettype": [""], "patching_rect": [700, 20, 30, 22]}},
        {"box": {"id": "obj-3", "maxclass": "codebox", "code": CODE, "fontface": 0, "fontname": "<Monospaced>",
                 "fontsize": 11.0, "numinlets": 2, "numoutlets": 2, "outlettype": ["", ""],
                 "patching_rect": [20, 60, 710, 560]}},
        {"box": {"id": "obj-4", "maxclass": "newobj", "text": "out 1", "numinlets": 1, "numoutlets": 0,
                 "patching_rect": [20, 640, 37, 22]}},
        {"box": {"id": "obj-5", "maxclass": "newobj", "text": "out 2", "numinlets": 1, "numoutlets": 0,
                 "patching_rect": [700, 640, 37, 22]}},
    ],
    "lines": [
        {"patchline": {"source": ["obj-1", 0], "destination": ["obj-3", 0]}},
        {"patchline": {"source": ["obj-2", 0], "destination": ["obj-3", 1]}},
        {"patchline": {"source": ["obj-3", 0], "destination": ["obj-4", 0]}},
        {"patchline": {"source": ["obj-3", 1], "destination": ["obj-5", 0]}},
    ],
}
gen = box("newobj", [30, 760, 300, 22], text="gen~", numinlets=2, numoutlets=2,
          outlettype=["signal", "signal"], patcher=gen_patcher)
plugout = newobj("plugout~", [30, 820, 60, 22], 2, 0, [])
connect(plugin, 0, gen, 0)
connect(plugin, 1, gen, 1)
connect(gen, 0, plugout, 0)
connect(gen, 1, plugout, 1)
thisdev = newobj("live.thisdevice", [400, 620, 90, 22], 1, 3, ["bang", "bang", ""])
trig = newobj("t b", [400, 650, 30, 22], 1, 1, ["bang"])
connect(thisdev, 0, trig, 0)

ui = []          # (box id, gen param)
param_ids = {}   # box id -> (long, short)


def wire(bid, gname):
    p = newobj(f"prepend {gname}", [bid_x[bid], 680, 110, 22], 1, 1, [""])
    connect(bid, 0, p, 0)
    connect(p, 0, gen, 0)
    connect(trig, 0, bid, 0)


bid_x = {}
_px = [30]


def ux():
    _px[0] += 120
    return _px[0]


def dial(gname, long, short, prect, lo, hi, init, unit, accent, exponent=1.0, big=False, showname=1, units=None):
    x = ux()
    attrs = dict(numinlets=1, numoutlets=2, outlettype=["", "float"], parameter_enable=1,
                 varname=gname, showname=showname, shownumber=1,
                 activedialcolor=accent, activeneedlecolor=CREAM, dialcolor=DIM, needlecolor=MUTED,
                 textcolor=CREAM, fontsize=10.0 if big else 9.0, fontface=1 if big else 0,
                 saved_attribute_attributes=valueof(long, short, 0, lo, hi, init, unit, exponent=exponent, units=units))
    if big:
        attrs["appearance"] = 0
    b = box("live.dial", [x, 560, prect[2], prect[3]], prect, **attrs)
    bid_x[b] = x
    param_ids[b] = (long, short)
    wire(b, gname)
    return b


def menu(gname, long, short, prect, items, init, accent):
    x = ux()
    b = box("live.menu", [x, 560, prect[2], prect[3]], prect, numinlets=1, numoutlets=3,
            outlettype=["", "", "float"], parameter_enable=1, varname=gname,
            textcolor=CREAM, bgcolor=PANEL, activebgcolor=STRIP, tricolor=accent, fontsize=10.0,
            saved_attribute_attributes=valueof(long, short, 2, 0, len(items) - 1, init, 9, enum=items))
    bid_x[b] = x
    param_ids[b] = (long, short)
    wire(b, gname)
    return b


def tab(gname, long, short, prect, items, init, accent):
    x = ux()
    b = box("live.tab", [x, 560, prect[2], prect[3]], prect, numinlets=1, numoutlets=3,
            outlettype=["", "", "float"], parameter_enable=1, varname=gname, num_lines_patching=1,
            num_lines_presentation=1, fontsize=9.0, textcolor=MUTED, textoncolor=BG,
            bgcolor=PANEL, bgoncolor=accent, activebgcolor=PANEL, activebgoncolor=accent,
            bordercolor=DIM, focusbordercolor=accent,
            saved_attribute_attributes=valueof(long, short, 2, 0, len(items) - 1, init, 9, enum=items))
    bid_x[b] = x
    param_ids[b] = (long, short)
    wire(b, gname)
    return b


def toggle(gname, long, short, prect, label, init, accent):
    x = ux()
    b = box("live.text", [x, 560, prect[2], prect[3]], prect, numinlets=1, numoutlets=2,
            outlettype=["", ""], parameter_enable=1, varname=gname, mode=0, text=label, texton=label,
            fontsize=9.0, fontface=1, textcolor=MUTED, textoncolor=BG, bgcolor=PANEL, bgoncolor=accent,
            activebgcolor=PANEL, activebgoncolor=accent, bordercolor=DIM, focusbordercolor=accent,
            saved_attribute_attributes=valueof(long, short, 2, 0, 1, init, 9, enum=["off", "on"]))
    bid_x[b] = x
    param_ids[b] = (long, short)
    wire(b, gname)
    return b


def comment(text, prect, color=CREAM, size=9.0, bold=0, align=0):
    return box("comment", [prect[0], prect[1] + 300, prect[2], prect[3]], prect, text=text, textcolor=color,
               fontsize=size, fontface=bold, numinlets=1, numoutlets=0, textjustification=align)


def panel(prect, color, border=None, rounded=4):
    attrs = dict(bgcolor=color, rounded=rounded, numinlets=1, numoutlets=0, background=1)
    if border:
        attrs.update(border=1, bordercolor=border)
    return box("panel", [prect[0], prect[1] + 900, prect[2], prect[3]], prect, **attrs)


# ---------------------------------------------------------------- layout
panel([0, 0, W, H], BG, rounded=0)

LP_ITEMS = ["01 Sherman Filterbank", "02 Korg 35 / MS-20", "03 Moog-style Ladder",
            "04 Steiner-Parker", "05 Oberheim SEM", "06 TB-303 Diode Ladder"]
HP_ITEMS = ["01 Sherman Filterbank", "02 Korg 35 / MS-20", "03 Ladder HP - ALT pole-mix",
            "04 Steiner-Parker", "05 Oberheim SEM"]
CHAR_LP = ["FEEDBACK", "FB CLIP", "STAGE SAT", "BP BLEND", "NOTCH MORPH", "SQUELCH"]
CHAR_HP = CHAR_LP[:5]
INFO_LP = ["NATIVE 12 + 24 | 36-48 ADD EXT", "NATIVE 12 | 24-48 ADD EXT", "NATIVE 12 TAP + 24 | 36-48 EXT",
           "NATIVE 12 | 24-48 ADD EXT", "NATIVE 12 | 24-48 ADD EXT", "NATIVE 24 - NO 12 | 36-48 EXT"]
INFO_HP = ["NATIVE 12 + 24 | 36-48 ADD EXT", "NATIVE 12 | 24-48 ADD EXT", "ALT POLE-MIX HP | 36-48 EXT",
           "NATIVE 12 | 24-48 ADD EXT", "NATIVE 12 | 24-48 ADD EXT"]
INFO_HP[3] = "HP INJ: 6dB SKIRT | 24-48 EXT"


def section(x0, s, title, accent, items, chars, infos, cmin, cmax, cinit, cexp, minit, slinit, scale):
    panel([x0, 4, 298, 161], PANEL, border=[accent[0] * 0.55, accent[1] * 0.55, accent[2] * 0.55, 1])
    box("panel", [x0, 1200, 298, 3], [x0 + 6, 22, 286, 2], bgcolor=accent, rounded=0, numinlets=1, numoutlets=0)
    comment(title, [x0 + 6, 5, 160, 16], accent, 11.0, 1)
    pre = "LPF" if s == "l" else "HPF"
    toggle(f"{s}_on", f"{pre} On", f"{pre} On", [x0 + 252, 6, 40, 14], "ON", 1, accent)
    m = menu(f"{s}_model", f"{pre} Model", f"{pre} Model", [x0 + 6, 28, 286, 16], items, minit, accent)
    dial(f"{s}_cut", f"{pre} Cutoff", f"{pre} Cut", [x0 + 4, 48, 108, 100], cmin, cmax, cinit, 3, accent,
         exponent=cexp, big=True)
    comment(scale, [x0 + 6, 148, 106, 12], MUTED, 8.0, 0, 1)
    dial(f"{s}_res", f"{pre} Resonance", f"{pre} Res", [x0 + 118, 48, 54, 50], 0, 100, 0, 5, accent)
    dial(f"{s}_drive", f"{pre} Drive", f"{pre} Drive", [x0 + 176, 48, 54, 50], 0, 100, 0, 5, accent)
    dial(f"{s}_comp", f"{pre} Compensation", f"{pre} Comp", [x0 + 234, 48, 54, 50], 0, 100, 100, 5, accent)
    dial(f"{s}_char", f"{pre} Character", f"{pre} Char", [x0 + 118, 104, 54, 44], 0, 100, 0, 5, accent, showname=0)
    lab = comment(chars[minit], [x0 + 112, 148, 66, 12], accent, 8.0, 1, 1)
    comment("SLOPE  dB/OCT", [x0 + 182, 102, 110, 12], MUTED, 8.0, 0)
    tab(f"{s}_slope", f"{pre} Slope", f"{pre} Slope", [x0 + 182, 115, 110, 16], ["12", "24", "36", "48"], slinit, accent)
    info = comment(infos[minit], [x0 + 182, 134, 110, 26], MUTED, 7.5, 0)
    # model -> character label + slope info
    n = len(items)
    sel = newobj("sel " + " ".join(str(i) for i in range(n)), [bid_x[m], 470, 120, 22], 2, n + 1, ["bang"] * n + [""])
    connect(m, 0, sel, 0)
    for i in range(n):
        a = box("message", [bid_x[m] + i * 10, 500 + i * 3, 80, 22], text=f"set {chars[i]}", numinlets=2, numoutlets=1, outlettype=[""])
        b = box("message", [bid_x[m] + i * 10, 530 + i * 3, 80, 22], text=f"set {infos[i]}", numinlets=2, numoutlets=1, outlettype=[""])
        connect(sel, i, a, 0); connect(a, 0, lab, 0)
        connect(sel, i, b, 0); connect(b, 0, info, 0)


section(4, "l", "LOW-PASS", AMBER, LP_ITEMS, CHAR_LP, INFO_LP, 20, 20000, 20000, 5.0, 2, 1, "20 Hz  ·  OPEN 20k")
section(398, "h", "HIGH-PASS", COPPER, HP_ITEMS, CHAR_HP, INFO_HP, 20, 2000, 20, 3.46, 1, 0, "OPEN 20 Hz  ·  2k")

# centre strip
panel([306, 4, 88, 161], STRIP, border=DIM)
comment("DUB", [310, 4, 80, 16], CREAM, 12.0, 1, 1)
comment("FILTER", [310, 18, 80, 12], MUTED, 8.0, 1, 1)
comment("ORDER", [310, 34, 80, 11], MUTED, 8.0, 0, 1)
tab("order_sel", "Stage Order", "Order", [312, 46, 76, 15], ["LP>HP", "HP>LP"], 0, CREAM)
comment("OVERSAMPLE", [310, 64, 80, 11], MUTED, 8.0, 0, 1)
tab("ovs_sel", "Oversampling", "OS", [312, 76, 76, 15], ["1x", "2x"], 0, CREAM)
dial("out_db", "Output", "Output", [323, 94, 54, 50], -24, 12, 0, 4, CREAM)
toggle("softclip", "Soft Clip", "Soft Clip", [312, 147, 76, 14], "SOFT CLIP", 1, CREAM)

# ------------------------------------------------- v1.2: BAND-PASS section
# Appended after every v1.1 object so all existing object ids, parameters and
# presentation rects stay exactly as they were (checked by tests/compat.py).
BRASS = [0.851, 0.729, 0.333, 1.0]
BX = 702
W_TOTAL = BX + 360 + 4
panel([W, 0, W_TOTAL - W, H], BG, rounded=0)
panel([BX, 4, 360, 161], PANEL, border=[BRASS[0] * 0.55, BRASS[1] * 0.55, BRASS[2] * 0.55, 1])
box("panel", [BX, 1200, 348, 3], [BX + 6, 22, 348, 2], bgcolor=BRASS, rounded=0, numinlets=1, numoutlets=0)
comment("BAND-PASS", [BX + 6, 5, 160, 16], BRASS, 11.0, 1)
toggle("b_on", "BPF On", "BPF On", [BX + 314, 6, 40, 14], "ON", 0, BRASS)
BP_ITEMS = ["01 Oberheim SEM", "02 Steiner-Parker", "03 Korg 35 / MS-20", "04 ARP 2600 - derived", "05 EMS VCS3 - derived"]
bm = menu("b_model", "BPF Model", "BPF Model", [BX + 6, 28, 196, 16], BP_ITEMS, 0, BRASS)
ba = tab("b_arch", "BPF Architecture", "BPF Arch", [BX + 206, 28, 148, 16], ["SVF", "CASC", "MULTI"], 0, BRASS)
dial("b_freq", "BPF Centre", "BPF Freq", [BX + 4, 48, 108, 100], 30, 12000, 1000, 3, BRASS, exponent=4.39, big=True)
comment("30 Hz  ·  CENTRE  ·  12k", [BX + 4, 148, 110, 12], MUTED, 8.0, 0, 1)
dial("b_bw", "BPF Bandwidth", "BPF BW", [BX + 118, 48, 54, 50], 0.2, 6, 2, 9, BRASS, units="%0.1f oct")
dial("b_q", "BPF Q", "BPF Q", [BX + 176, 48, 54, 50], 0.5, 10, 0.707, 1, BRASS, exponent=2.0)
dial("b_res", "BPF Resonance", "BPF Res", [BX + 234, 48, 54, 50], 0, 100, 0, 5, BRASS)
dial("b_drive", "BPF Drive", "BPF Drive", [BX + 292, 48, 54, 50], 0, 100, 0, 5, BRASS)
dial("b_comp", "BPF Compensation", "BPF Comp", [BX + 118, 102, 54, 46], 0, 100, 100, 5, BRASS)
dial("b_mix", "BPF Mix", "BPF Mix", [BX + 176, 102, 54, 46], 0, 100, 100, 5, BRASS)
comment("POSITION", [BX + 236, 101, 118, 11], MUTED, 8.0, 0)
tab("b_pos", "BPF Position", "BPF Pos", [BX + 236, 113, 118, 15], ["POST", "PRE"], 0, BRASS)
# native/derived + active-control info, from model x architecture
B_INFO = {
    (0, 0): "NATIVE: SEM BP MODE | Q = WIDTH", (0, 1): "DERIVED: SEM HP>LP | BW + EDGE Q", (0, 2): "DERIVED: OTA LADDER | BW = ORDER",
    (1, 0): "NATIVE RESPONSE: SK BP | Q = WIDTH", (1, 1): "DERIVED: HP>LP | BW + EDGE Q", (1, 2): "DERIVED: DIODE LADDER | BW = ORDER",
    (2, 0): "DERIVED: K35 SVF | Q = WIDTH", (2, 1): "NATIVE: MS-20 HP>LP | BW + EDGE Q", (2, 2): "DERIVED: LADDER | BW = ORDER",
    (3, 0): "DERIVED: 2600 HAS NO BP | Q = WIDTH", (3, 1): "DERIVED: 2600 HAS NO BP | BW + Q", (3, 2): "CLOSEST: 2600 LADDER | BW = ORDER",
    (4, 0): "DERIVED: VCS3 HAS NO BP | Q = WIDTH", (4, 1): "DERIVED: VCS3 HAS NO BP | BW + Q", (4, 2): "CLOSEST: VCS3 LADDER | BW = ORDER",
}
binfo = comment(B_INFO[(0, 0)], [BX + 236, 131, 120, 30], MUTED, 7.5, 0)
pk = newobj("pak 0 0", [bid_x[bm], 440, 60, 22], 2, 1, [""])
ex = newobj("expr $i1 * 3 + $i2", [bid_x[bm], 465, 110, 22], 2, 1, [""])
bsel = newobj("sel " + " ".join(str(i) for i in range(15)), [bid_x[bm], 490, 200, 22], 2, 16, ["bang"] * 15 + [""])
connect(bm, 0, pk, 0)
connect(ba, 0, pk, 1)
connect(pk, 0, ex, 0)
connect(ex, 0, bsel, 0)
for i in range(15):
    mb = box("message", [bid_x[bm] + i * 12, 520 + i * 3, 120, 22], text="set " + B_INFO[(i // 3, i % 3)],
             numinlets=2, numoutlets=1, outlettype=[""])
    connect(bsel, i, mb, 0)
    connect(mb, 0, binfo, 0)

# ---------------------------------------------------------------- patcher
patcher = {
    "patcher": {
        "fileversion": 1,
        "appversion": {"major": 8, "minor": 6, "revision": 2, "architecture": "x64", "modernui": 1},
        "classnamespace": "box",
        "rect": [60, 80, 1500, 900],
        "openrect": [0, 0, W_TOTAL, H],
        "bglocked": 0,
        "openinpresentation": 1,
        "default_fontsize": 10.0,
        "default_fontface": 0,
        "default_fontname": "Arial Bold",
        "gridonopen": 1,
        "gridsize": [8.0, 8.0],
        "gridsnaponopen": 1,
        "objectsnaponopen": 1,
        "statusbarvisible": 2,
        "toolbarvisible": 1,
        "lefttoolbarpinned": 0,
        "toptoolbarpinned": 0,
        "righttoolbarpinned": 0,
        "bottomtoolbarpinned": 0,
        "toolbars_unpinned_last_save": 0,
        "tallnewobj": 0,
        "boxanimatetime": 500,
        "enablehscroll": 1,
        "enablevscroll": 1,
        "devicewidth": float(W_TOTAL),
        "description": "Dub Filter - multi-model analogue-inspired LPF/HPF/BPF",
        "digest": "",
        "tags": "",
        "style": "",
        "subpatcher_template": "",
        "assistshowspatchername": 0,
        "boxes": boxes,
        "lines": lines,
        "parameters": {
            **{bid: [lg, sh, 0] for bid, (lg, sh) in param_ids.items()},
            "inherited_shortname": 1,
        },
        "dependency_cache": [],
        "latency": 0,
        "is_mpe": 0,
        "minimum_live_version": "",
        "minimum_max_version": "",
        "platform_compatibility": 0,
        "autosave": 0,
    }
}

txt = json.dumps(patcher, indent=1)
out_dir = os.path.join(ROOT, "build", "device")
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "DubFilter.maxpat"), "w") as f:
    f.write(txt)
payload = txt.encode("utf-8") + b"\n\x00"
amxd = b"ampf" + struct.pack("<I", 4) + b"aaaa" + b"meta" + struct.pack("<I", 4) + b"\x00\x00\x00\x00" + \
       b"ptch" + struct.pack("<I", len(payload)) + payload
with open(os.path.join(out_dir, "DubFilter.amxd"), "wb") as f:
    f.write(amxd)
print(f"boxes {len(boxes)}, lines {len(lines)}, parameters {len(param_ids)}, amxd {len(amxd)} bytes")

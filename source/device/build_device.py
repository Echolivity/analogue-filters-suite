#!/usr/bin/env python3
"""Builds the Max for Live device: DubFilter.maxpat (editable) and
DubFilter.amxd (Live audio effect) from build/dubfilter.genexpr."""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CODE = open(os.path.join(ROOT, "build", "dubfilter.genexpr")).read()

W, H = 700, 169
# ---- palette: v1.5 design system (device/ui_theme.py). The old names are kept as
# aliases so the section code below reads as before; every section now shares one
# accent (amber = ON / selected / value) instead of a colour per section.
sys.path.insert(0, HERE)
import ui_theme as T
BG = T.CHASSIS
PANEL = T.PLATE
STRIP = T.PLATE
AMBER = T.AMBER
COPPER = T.AMBER
CREAM = T.TEXT
MUTED = T.LABEL
DIM = T.BEVEL

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
                 activedialcolor=T.AMBER, activeneedlecolor=T.TEXT, dialcolor=T.ARC_OFF, needlecolor=T.TEXT_DIM,
                 textcolor=T.TEXT if big else T.LABEL, fontsize=10.0 if big else T.F_LABEL, fontface=1 if big else 0,
                 focusbordercolor=T.AMBER,
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
            textcolor=T.TEXT, bgcolor=T.INSET, activebgcolor=T.INSET, tricolor=T.AMBER,
            fontsize=9.0,
            saved_attribute_attributes=valueof(long, short, 2, 0, len(items) - 1, init, 9, enum=items))
    bid_x[b] = x
    param_ids[b] = (long, short)
    wire(b, gname)
    return b


# segment / button colours: active (normal) vs inactive (unavailable) variants
# (attribute names per the Max 8 live.tab / live.text references; bg*/inactive* = active 0)
SEG_COLOURS = dict(textcolor=T.LABEL, textoncolor=T.TEXT_ON, inactivetextoffcolor=T.TEXT_DIM, inactivetextoncolor=T.TEXT_DIM,
                   bgcolor=T.INSET, bgoncolor=T.AMBER_DIM, activebgcolor=T.OFF, activebgoncolor=T.AMBER,
                   bordercolor=T.BEVEL, focusbordercolor=T.AMBER)
BTN_COLOURS = dict(activetextcolor=T.LABEL, activetextoncolor=T.TEXT_ON, textcolor=T.TEXT_DIM, textoncolor=T.TEXT_DIM,
                   bgcolor=T.INSET, bgoncolor=T.AMBER_DIM, activebgcolor=T.OFF, activebgoncolor=T.AMBER,
                   bordercolor=T.BEVEL, focusbordercolor=T.AMBER)


def tab(gname, long, short, prect, items, init, accent):
    x = ux()
    b = box("live.tab", [x, 560, prect[2], prect[3]], prect, numinlets=1, numoutlets=3,
            outlettype=["", "", "float"], parameter_enable=1, varname=gname, num_lines_patching=1,
            num_lines_presentation=1, fontsize=8.0, fontface=1, **SEG_COLOURS,
            saved_attribute_attributes=valueof(long, short, 2, 0, len(items) - 1, init, 9, enum=items))
    bid_x[b] = x
    param_ids[b] = (long, short)
    wire(b, gname)
    return b


def toggle(gname, long, short, prect, label, init, accent):
    x = ux()
    b = box("live.text", [x, 560, prect[2], prect[3]], prect, numinlets=1, numoutlets=2,
            outlettype=["", ""], parameter_enable=1, varname=gname, mode=0, text=label, texton=label,
            fontsize=8.0, fontface=1, **BTN_COLOURS,
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
HP_ITEMS = ["01 Sherman Filterbank", "02 Korg 35 / MS-20", "03 Moog 904B HP",
            "04 Steiner-Parker", "05 Oberheim SEM"]
CHAR_LP = ["FEEDBACK", "FB CLIP", "STAGE SAT", "BP BLEND", "NOTCH MORPH", "SQUELCH"]
CHAR_HP = CHAR_LP[:5]
INFO_LP = ["NATIVE 12 + 24 | 36-48 ADD EXT", "NATIVE 12 | 24-48 ADD EXT", "NATIVE 12 TAP + 24 | 36-48 EXT",
           "NATIVE 12 | 24-48 ADD EXT", "NATIVE 12 | 24-48 ADD EXT", "NATIVE 24 - NO 12 | 36-48 EXT"]
INFO_HP = ["NATIVE 12 + 24 | 36-48 ADD EXT", "NATIVE 12 | 24-48 ADD EXT", "904B 24 - NO RES | 36-48 EXT",
           "NATIVE 12 | 24-48 ADD EXT", "NATIVE 12 | 24-48 ADD EXT"]
INFO_HP[3] = "HP INJ: 6dB SKIRT | 24-48 EXT"


def section(x0, s, title, accent, items, chars, infos, cmin, cmax, cinit, cexp, minit, slinit, scale):
    panel([x0, 4, 298, 161], PANEL, border=T.BEVEL)
    box("panel", [x0, 1200, 298, 3], [x0 + 1, 22, 296, 1], bgcolor=T.BEVEL_HI, rounded=0, numinlets=1, numoutlets=0)
    comment(title, [x0 + 8, 6, 150, 14], T.TEXT, T.F_TITLE, 1)
    pre = "LPF" if s == "l" else "HPF"
    toggle(f"{s}_on", f"{pre} On", f"{pre} On", [x0 + 256, 6, T.ON_W, T.ON_H], "ON", 1, accent)
    m = menu(f"{s}_model", f"{pre} Model", f"{pre} Model", [x0 + 6, 27, 286, 16], items, minit, accent)
    dial(f"{s}_cut", f"{pre} Cutoff", f"{pre} Cut", [x0 + 4, 48, 108, 100], cmin, cmax, cinit, 3, accent,
         exponent=cexp, big=True)
    comment(scale, [x0 + 4, 150, 108, 11], MUTED, T.F_SMALL, 0, 1)
    dial(f"{s}_res", f"{pre} Resonance", f"{pre} Res", [x0 + 118, 48, 54, 50], 0, 100, 0, 5, accent)
    dial(f"{s}_drive", f"{pre} Drive", f"{pre} Drive", [x0 + 176, 48, 54, 50], 0, 100, 0, 5, accent)
    dial(f"{s}_comp", f"{pre} Compensation", f"{pre} Comp", [x0 + 234, 48, 54, 50], 0, 100, 100, 5, accent)
    dial(f"{s}_char", f"{pre} Character", f"{pre} Char", [x0 + 118, 104, 54, 44], 0, 100, 0, 5, accent, showname=0)
    lab = comment(chars[minit], [x0 + 112, 149, 66, 12], T.AMBER, T.F_SMALL, 1, 1)
    comment("SLOPE  dB/OCT", [x0 + 182, 102, 110, 12], MUTED, T.F_SMALL, 0)
    tab(f"{s}_slope", f"{pre} Slope", f"{pre} Slope", [x0 + 182, 115, 110, 16], ["12", "24", "36", "48"], slinit, accent)
    info = comment(infos[minit], [x0 + 182, 134, 110, 26], MUTED, T.F_TINY, 0)
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
panel([306, 4, 88, 161], STRIP, border=T.BEVEL)
comment("DUB FILTER", [308, 7, 84, 14], T.TEXT, 9.5, 1, 1)
comment("ROUTING", [308, 26, 84, 10], T.AMBER, T.F_TINY, 1, 1)
comment("STAGE ORDER", [308, 35, 84, 10], MUTED, T.F_TINY, 0, 1)
tab("order_sel", "Stage Order", "Order", [312, 46, 76, 15], ["LP>HP", "HP>LP"], 0, CREAM)
comment("OVERSAMPLE", [308, 76, 84, 10], MUTED, T.F_TINY, 0, 1)
tab("ovs_sel", "Oversampling", "OS", [312, 86, 76, 14], ["1x", "2x"], 0, CREAM)
dial("out_db", "Output", "Output", [323, 101, 54, 47], -24, 12, 0, 4, CREAM)
toggle("softclip", "Soft Clip", "Soft Clip", [312, 149, 76, 14], "SOFT CLIP", 1, CREAM)

# ------------------------------------------------- v1.2: BAND-PASS section
# Appended after every v1.1 object so all existing object ids, parameters and
# presentation rects stay exactly as they were (checked by tests/compat.py).
BRASS = T.AMBER
BX = 702
BW_SEC = 418
W_TOTAL = BX + BW_SEC + 4
panel([W, 0, W_TOTAL - W, H], BG, rounded=0)
panel([BX, 4, BW_SEC, 161], PANEL, border=T.BEVEL)
box("panel", [BX, 1200, 348, 3], [BX + 1, 22, BW_SEC - 2, 1], bgcolor=T.BEVEL_HI, rounded=0, numinlets=1, numoutlets=0)
comment("BAND-PASS", [BX + 8, 6, 150, 14], T.TEXT, T.F_TITLE, 1)
toggle("b_on", "BPF On", "BPF On", [BX + BW_SEC - 42, 6, T.ON_W, T.ON_H], "ON", 0, BRASS)
BP_ITEMS = ["01 Oberheim SEM", "02 Steiner-Parker", "03 Korg 35 / MS-20", "04 ARP 2600 - derived", "05 EMS VCS3 - derived"]
bm = menu("b_model", "BPF Model", "BPF Model", [BX + 6, 27, 200, 16], BP_ITEMS, 0, BRASS)
ba = tab("b_arch", "BPF Architecture", "BPF Arch", [BX + 210, 27, 136, 16], ["SVF", "CASC", "MULTI"], 0, BRASS)
dial("b_freq", "BPF Centre", "BPF Freq", [BX + 4, 48, 108, 100], 30, 12000, 1000, 3, BRASS, exponent=4.39, big=True)
comment("30 Hz  ·  CENTRE  ·  12k", [BX + 4, 150, 108, 11], MUTED, T.F_SMALL, 0, 1)
dial("b_bw", "BPF Bandwidth", "BPF BW", [BX + 118, 48, 54, 50], 0.2, 6, 2, 9, BRASS, units="%0.1f oct")
dial("b_q", "BPF Q", "BPF Q", [BX + 176, 48, 54, 50], 0.5, 10, 0.707, 1, BRASS, exponent=2.0)
dial("b_res", "BPF Resonance", "BPF Res", [BX + 234, 48, 54, 50], 0, 100, 0, 5, BRASS)
dial("b_drive", "BPF Drive", "BPF Drive", [BX + 292, 48, 54, 50], 0, 100, 0, 5, BRASS)
dial("b_comp", "BPF Compensation", "BPF Comp", [BX + 118, 102, 54, 46], 0, 100, 100, 5, BRASS)
dial("b_mix", "BPF Mix", "BPF Mix", [BX + 176, 102, 54, 46], 0, 100, 100, 5, BRASS)
comment("POSITION (SERIES)", [BX + 236, 101, 110, 11], MUTED, T.F_SMALL, 0)
tab("b_pos", "BPF Position", "BPF Pos", [BX + 236, 113, 110, 15], ["POST", "PRE"], 0, BRASS)
# native/derived + active-control info, from model x architecture
B_INFO = {
    (0, 0): "NATIVE: SEM BP MODE | Q = WIDTH", (0, 1): "DERIVED: SEM HP>LP | BW + EDGE Q", (0, 2): "DERIVED: OTA LADDER | BW = ORDER",
    (1, 0): "NATIVE RESPONSE: SK BP | Q = WIDTH", (1, 1): "DERIVED: HP>LP | BW + EDGE Q", (1, 2): "DERIVED: DIODE LADDER | BW = ORDER",
    (2, 0): "DERIVED: K35 SVF | Q = WIDTH", (2, 1): "NATIVE: MS-20 HP>LP | BW + EDGE Q", (2, 2): "DERIVED: LADDER | BW = ORDER",
    (3, 0): "DERIVED: 2600 HAS NO BP | Q = WIDTH", (3, 1): "DERIVED: 2600 HAS NO BP | BW + Q", (3, 2): "CLOSEST: 2600 LADDER | BW = ORDER",
    (4, 0): "DERIVED: VCS3 HAS NO BP | Q = WIDTH", (4, 1): "DERIVED: VCS3 HAS NO BP | BW + Q", (4, 2): "CLOSEST: VCS3 LADDER | BW = ORDER",
}
binfo = comment(B_INFO[(0, 0)], [BX + 236, 131, 112, 30], MUTED, T.F_TINY, 0)
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


# ------------------------------------------------- v1.3: PROCESSING CHAIN section
# Appended after every v1.2 object (ids/params/rects of existing objects unchanged).
sys.path.insert(0, os.path.join(ROOT, "src"))
import dyn as DYN

BYID = {b["box"]["id"]: b["box"] for b in boxes}
# gen~ gains the external key inlets (in3/in4) and 12 meter outlets (out3..out14)
gb = BYID[gen]
gb["numinlets"] = 4
gb["numoutlets"] = 14
gb["outlettype"] = ["signal"] * 14
gp = gb["patcher"]
gp["boxes"][2]["box"]["numinlets"] = 4
gp["boxes"][2]["box"]["numoutlets"] = 14
gp["boxes"][2]["box"]["outlettype"] = [""] * 14
for i in (3, 4):
    gp["boxes"].append({"box": {"id": f"obj-in{i}", "maxclass": "newobj", "text": f"in {i}", "numinlets": 0, "numoutlets": 1,
                                "outlettype": [""], "patching_rect": [700 + 40 * (i - 2), 20, 30, 22]}})
    gp["lines"].append({"patchline": {"source": [f"obj-in{i}", 0], "destination": ["obj-3", i - 1]}})
for i in range(3, 15):
    gp["boxes"].append({"box": {"id": f"obj-out{i}", "maxclass": "newobj", "text": f"out {i}", "numinlets": 1, "numoutlets": 0,
                                "patching_rect": [20 + 50 * i, 680, 40, 22]}})
    gp["lines"].append({"patchline": {"source": ["obj-3", i - 1], "destination": [f"obj-out{i}", 0]}})

# external key: plugin~ channels 3/4 (Live routes the chosen track into them via live.routing)
plug34 = newobj("plugin~ 3 4", [130, 700, 80, 22], 2, 2, ["signal", "signal"])
connect(plug34, 0, gen, 2)
connect(plug34, 1, gen, 3)

EMBER = GOLD = STEEL = T.AMBER
MCOL = {"T": EMBER, "O": GOLD, "V": STEEL}
CX = W_TOTAL
CW = 800
W_TOTAL = CX + CW + 4
panel([CX - 2, 0, W_TOTAL - CX + 2, H], BG, rounded=0)
panel([CX, 4, CW, 161], PANEL, border=T.BEVEL)
comment("PROCESSING CHAIN", [CX + 8, 6, 122, 14], T.TEXT, T.F_TITLE, 1)
box("panel", [CX, 1200, 692, 2], [CX + 1, 22, CW - 2, 1], bgcolor=T.BEVEL_HI, rounded=0, numinlets=1, numoutlets=0)

thisp = newobj("thispatcher", [1500, 760, 80, 22], 1, 2, ["", ""])


def named(bid, name):
    BYID_ = {b["box"]["id"]: b["box"] for b in boxes}
    BYID_[bid]["varname"] = name
    return bid


def hide(bid):
    for b in boxes:
        if b["box"]["id"] == bid:
            b["box"]["hidden"] = 1


# header: order menu, suggested configurations, key listen, key source
ordm = menu("c_order", "Chain Order", "Order", [CX + 132, 5, 140, 15], DYN.PERM_NAMES, 0, CREAM)
presets = []
px = CX + 280
for name, idx in DYN.PRESETS.items():
    wdt = 58 if name != "PUNCH & COLOUR" else 82
    b = box("live.text", [px, 1250, wdt, 15], [px, 5, wdt, 15], numinlets=1, numoutlets=2, outlettype=["", ""],
            parameter_enable=0, mode=0, text=name, texton=name, fontsize=8.0, fontface=1, textcolor=MUTED, textoncolor=BG,
            bgcolor=PANEL, bgoncolor=CREAM, activebgcolor=PANEL, activebgoncolor=CREAM, bordercolor=DIM, varname=f"preset_{idx}")
    msg = box("message", [px, 1280, 40, 22], text=str(idx), numinlets=2, numoutlets=1, outlettype=[""])
    sel1 = newobj("sel 1", [px, 1270, 40, 22], 2, 2, ["bang", ""])
    connect(b, 0, sel1, 0)
    connect(sel1, 0, msg, 0)
    connect(msg, 0, ordm, 0)
    px += wdt + 4
comment("KEY LISTEN", [CX + 542, 8, 52, 10], MUTED, T.F_TINY, 1)
tab("key_listen", "Key Listen", "Key Listen", [CX + 596, 5, 198, 15], ["OFF", "OPTO", "VCA", "GATE"], 0, CREAM)
kr = box("live.routing", [1600, 800, 120, 40], [CX + 640, 120, 152, 34], numinlets=1, numoutlets=1, outlettype=[""],
         varname="key_routing", fontsize=8.0, textcolor=T.TEXT)
comment("EXTERNAL KEY (SIDECHAIN)", [CX + 640, 107, 152, 10], MUTED, T.F_TINY, 1)

# flow strip: IN -> slot1 -> slot2 -> slot3 -> GATE -> OUT
SLOT_X = [CX + 22, CX + 212, CX + 402]
BY, BW_, BH = 26, 172, 60
comment("IN", [CX + 5, BY + 24, 18, 12], MUTED, 8.0, 1)
for k in range(3):
    comment("▸", [SLOT_X[k] + BW_ + 4, BY + 23, 12, 12], T.AMBER, 9.0, 1)
GX = CX + 592
block_objs = {}   # module -> list of (bid, dx, dy, w, h)


def blk(m, bid, dx, dy, w_, h_, name):
    named(bid, name)
    block_objs.setdefault(m, []).append((name, dx, dy, w_, h_))
    return bid


for m in DYN.MODS:
    k = DYN.PERMS[0].index(m)
    bx = SLOT_X[k]
    col = MCOL[m]
    p = {"T": "t", "O": "o", "V": "v"}[m]
    blk(m, panel([bx, BY, BW_, BH], T.INSET, border=T.BEVEL), 0, 0, BW_, BH, f"blk_{m}_bg")
    block_objs[m].append((f"blk_{m}_hdr", 1, 1, BW_ - 2, 15))          # v1.5 header plate (created below)
    blk(m, comment(DYN.MOD_NAMES[m], [bx + 6, BY + 2, 120, 12], T.TEXT, T.F_LABEL, 1), 6, 2, 120, 12, f"blk_{m}_name")
    on = toggle(f"{p}_on", {"t": "Tube On", "o": "Opto On", "v": "VCA On"}[p], {"t": "Tube On", "o": "Opto On", "v": "VCA On"}[p],
                [bx + BW_ - 40, BY + 2, 36, 13], "ON", 0, col)
    block_objs[m].append((f"{p}_on", BW_ - 40, 2, 36, 13))
    for j, (lab, outlet) in enumerate((("IN", {"T": 2, "O": 4, "V": 7}[m]), ("OUT", {"T": 3, "O": 5, "V": 8}[m]))):
        blk(m, comment(lab, [bx + 6, BY + 18 + 9 * j, 24, 9], MUTED, T.F_TINY, 0), 6, 18 + 9 * j, 24, 9, f"blk_{m}_l{j}")
        mt = box("live.meter~", [1200 + 60 * DYN.MODS.index(m), 820 + 30 * j, 80, 6], [bx + 30, BY + 20 + 9 * j, BW_ - 36, 5],
                 numinlets=1, numoutlets=1, outlettype=["list"], orientation=1, coldcolor=T.METER_LO, warmcolor=T.AMBER,
                 hotcolor=T.METER_HI, overloadcolor=T.METER_OVER)
        blk(m, mt, 30, 20 + 9 * j, BW_ - 36, 5, f"blk_{m}_m{j}")
        connect(gen, outlet, mt, 0)
    if m != "T":
        blk(m, comment("GR", [bx + 6, BY + 37, 20, 9], MUTED, T.F_TINY, 0), 6, 37, 20, 9, f"blk_{m}_l2")
        snap = newobj("snapshot~ 50", [1200 + 60 * DYN.MODS.index(m), 900, 80, 22], 2, 1, ["float"])
        mul = newobj("* 30.", [1200 + 60 * DYN.MODS.index(m), 930, 40, 22], 2, 1, ["float"])
        nb = box("live.numbox", [1200 + 60 * DYN.MODS.index(m), 960, 44, 15], [bx + 28, BY + 36, 40, 11],
                 numinlets=1, numoutlets=2, outlettype=["", "float"], parameter_enable=0, fontsize=7.5,
                 textcolor=T.AMBER, activeslidercolor=T.AMBER, appearance=0)
        connect(gen, {"O": 6, "V": 9}[m], snap, 0)
        connect(snap, 0, mul, 0)
        connect(mul, 0, nb, 0)
        blk(m, nb, 28, 36, 40, 11, f"blk_{m}_gr")
        blk(m, comment("dB", [bx + 68, BY + 37, 20, 9], MUTED, T.F_TINY, 0), 68, 37, 20, 9, f"blk_{m}_db")
    block_objs[m].append((f"blk_{m}_cap", 90, 37, BW_ - 94, 9))     # v1.5 module caption (created below)
    # drag handle: drag the grip left/right and release to move the block (1 or 2 slots)
    grip = box("live.slider", [1200 + 60 * DYN.MODS.index(m), 1000, 160, 10], [bx + 6, BY + 48, BW_ - 12, 9],
               numinlets=1, numoutlets=2, outlettype=["", "float"], parameter_enable=0, orientation=1,
               min=-2.0, size=4.0, showname=0, shownumber=0, slidercolor=T.OFF, trioncolor=T.AMBER, tribordercolor=T.BEVEL,
               textcolor=MUTED)
    blk(m, grip, 6, 48, BW_ - 12, 9, f"blk_{m}_grip")
    block_objs[m + "_grip_id"] = grip
comment("GATE", [GX + 6, BY + 2, 60, 12], T.TEXT, T.F_LABEL, 1)
toggle("g_on", "Gate On", "Gate On", [GX + BW_ - 40, BY + 2, 36, 13], "ON", 0, CREAM)
gm = box("live.meter~", [1400, 820, 80, 6], [GX + 30, BY + 20, BW_ - 36, 5], numinlets=1, numoutlets=1, outlettype=["list"],
         orientation=1, coldcolor=T.AMBER, warmcolor=T.AMBER, hotcolor=T.AMBER, varname="gate_meter")
connect(gen, 10, gm, 0)
comment("OPEN", [GX + 6, BY + 18, 24, 9], MUTED, T.F_TINY, 0)
km = box("live.meter~", [1400, 850, 80, 6], [GX + 30, BY + 29, BW_ - 36, 5], numinlets=1, numoutlets=1, outlettype=["list"],
         orientation=1, coldcolor=T.METER_LO, warmcolor=T.METER_LO, hotcolor=T.METER_HI, varname="key_meter")
connect(gen, 11, km, 0)
comment("KEY", [GX + 6, BY + 27, 24, 9], MUTED, T.F_TINY, 0)
comment("OUT", [GX + BW_ + 3, BY + 24, 26, 12], MUTED, 8.0, 1)

# order -> block positions (thispatcher scripting)
osel = newobj("sel " + " ".join(str(i) for i in range(6)), [1500, 700, 140, 22], 2, 7, ["bang"] * 6 + [""])
connect(ordm, 0, osel, 0)
for pi_, perm in enumerate(DYN.PERMS):
    cmds = []
    for k, m in enumerate(perm):
        for (name, dx, dy, w_, h_) in block_objs[m]:
            cmds.append(f"script sendbox {name} presentation_rect {SLOT_X[k] + dx} {BY + dy} {w_} {h_}")
    mb = box("message", [1500 + 20 * pi_, 730 + 4 * pi_, 200, 22], text=", ".join(cmds), numinlets=2, numoutlets=1, outlettype=[""])
    connect(osel, pi_, mb, 0)
    connect(mb, 0, thisp, 0)

# drag & release: grip value -> (module, current order, delta) lookup -> new order
LUT = []
for mi, m in enumerate(DYN.MODS):
    for cur, perm in enumerate(DYN.PERMS):
        for d in range(-2, 3):
            order = [x for x in perm if x != m]
            pos = max(0, min(2, perm.index(m) + d))
            order.insert(pos, m)
            LUT.append(DYN.PERMS.index(tuple(order)))
lut = newobj("zl lookup", [1700, 880, 70, 22], 2, 2, ["", ""])
lutmsg = box("message", [1700, 850, 300, 22], text=" ".join(str(v) for v in LUT), numinlets=2, numoutlets=1, outlettype=[""])
connect(lutmsg, 0, lut, 1)
connect(trig, 0, lutmsg, 0)
curi = newobj("i", [1800, 900, 30, 22], 2, 1, ["int"])
connect(ordm, 0, curi, 1)
mstate = newobj("mousestate", [1700, 940, 70, 22], 1, 5, ["int", "int", "int", "int", "int"])
pollm = box("message", [1700, 910, 40, 22], text="poll", numinlets=2, numoutlets=1, outlettype=[""])
connect(trig, 0, pollm, 0)
connect(pollm, 0, mstate, 0)
chg = newobj("change", [1700, 970, 50, 22], 1, 3, ["", "int", "int"])
rel0 = newobj("sel 0", [1700, 1000, 40, 22], 2, 2, ["bang", ""])
connect(mstate, 0, chg, 0)
connect(chg, 0, rel0, 0)
rtrig = newobj("t b b b b", [1700, 1030, 80, 22], 1, 4, ["bang", "bang", "bang", "bang"])
connect(rel0, 0, rtrig, 0)
reset = box("message", [1900, 1100, 50, 22], text="set 0.", numinlets=2, numoutlets=1, outlettype=[""])
connect(rtrig, 0, reset, 0)
for mi, m in enumerate(DYN.MODS):
    grip = block_objs[m + "_grip_id"]
    gf = newobj("f", [1700 + 80 * mi, 1060, 30, 22], 2, 1, ["float"])
    connect(grip, 0, gf, 1)
    connect(rtrig, 3 - mi, gf, 0)
    ex = newobj(f"expr int(floor($f1 + 0.5)) + 2 + $i2 * 5 + {mi * 30}", [1700 + 80 * mi, 1090, 220, 22], 2, 1, [""])
    connect(curi, 0, ex, 1)
    nz = newobj("if abs($f1) >= 0.5 then $f1", [1700 + 80 * mi, 1075, 150, 22], 1, 1, [""])
    connect(gf, 0, nz, 0)
    connect(nz, 0, ex, 0)
    zero = box("message", [1950, 1060 + 20 * mi, 30, 22], text="0.", numinlets=2, numoutlets=1, outlettype=[""])
    connect(rtrig, 0, zero, 0)
    connect(zero, 0, gf, 1)
    connect(reset, 0, grip, 0)
# only the moved grip produces an index (others are filtered by the "if"); route it through the LUT
for b in list(boxes):
    t = b["box"].get("text", "")
    if t.startswith("expr int(floor($f1 + 0.5))"):
        connect(b["box"]["id"], 0, lut, 0)
connect(lut, 0, ordm, 0)

# detail pages (EDIT: TUBE / OPTO / VCA / GATE); controls of other pages hidden via scripting
DX = CX + 84
DY = 93
edit = box("live.tab", [1500, 1150, 70, 68], [CX + 6, DY, 70, 68], numinlets=1, numoutlets=3, outlettype=["", "", "float"],
           parameter_enable=0, num_lines_patching=4, num_lines_presentation=4, fontsize=8.0, fontface=1, **SEG_COLOURS,
           varname="edit_page")
edit_box = next(b["box"] for b in boxes if b["box"]["id"] == edit)
edit_box["saved_attribute_attributes"] = {"valueof": {"parameter_enum": ["TUBE", "OPTO", "VCA", "GATE"], "parameter_mmax": 3}}
edit_box["parameter_enable"] = 0
pages = {0: [], 1: [], 2: [], 3: []}


def pd(page, bid):
    pages[page].append(bid)
    if page != 0:
        hide(bid)
    return bid


def dx(i):
    return DX + 50 * i


# TUBE
pd(0, dial("t_in", "Tube Input", "Tube In", [dx(0), DY, 48, 46], -24, 24, 0, 4, EMBER))
pd(0, dial("t_drive", "Tube Drive", "Drive", [dx(1), DY, 48, 46], 0, 100, 30, 5, EMBER))
pd(0, dial("t_bias", "Tube Bias", "Bias", [dx(2), DY, 48, 46], -100, 100, 20, 0, EMBER))
pd(0, dial("t_tone", "Tube Tone", "Tone", [dx(3), DY, 48, 46], 1000, 20000, 12000, 3, EMBER, exponent=2.0))
pd(0, dial("t_mix", "Tube Mix", "Mix", [dx(4), DY, 48, 46], 0, 100, 100, 5, EMBER))
pd(0, dial("t_out", "Tube Output", "Tube Out", [dx(5), DY, 48, 46], -24, 24, 0, 4, EMBER))
pd(0, toggle("t_auto", "Tube Auto Gain", "Auto Gain", [dx(6) + 4, DY + 14, 70, 15], "AUTO GAIN", 1, EMBER))
pd(0, comment("TRIODE STAGE  |  2x-16x OVERSAMPLED (ENGINE)  |  AUTO GAIN HOLDS -12 dBFS PROGRAM LEVEL", [DX, DY + 52, 520, 11], MUTED, 7.5, 0))
# OPTO
pd(1, dial("o_in", "Opto Input", "Opto In", [dx(0), DY, 48, 46], -24, 24, 0, 4, GOLD))
pd(1, dial("o_pr", "Opto Peak Reduction", "Peak Red", [dx(1), DY, 48, 46], 0, 100, 40, 5, GOLD))
pd(1, dial("o_emph", "Opto HF Emphasis", "HF Emph", [dx(2), DY, 48, 46], 0, 100, 0, 5, GOLD))
pd(1, dial("o_hpf", "Opto SC HPF", "SC HPF", [dx(3), DY, 48, 46], 20, 500, 20, 3, GOLD, exponent=2.0))
pd(1, dial("o_link", "Opto Link", "Link", [dx(4), DY, 48, 46], 0, 100, 100, 5, GOLD))
pd(1, dial("o_mix", "Opto Mix", "Mix", [dx(5), DY, 48, 46], 0, 100, 100, 5, GOLD))
pd(1, dial("o_out", "Opto Gain", "Gain", [dx(6), DY, 48, 46], -24, 24, 0, 4, GOLD))
pd(1, tab("o_mode", "Opto Mode", "Mode", [dx(7) + 4, DY + 4, 90, 14], ["COMP", "LIMIT"], 0, GOLD))
pd(1, comment("SIDECHAIN", [dx(7) + 4, DY + 22, 90, 9], MUTED, 7.0, 0))
pd(1, tab("o_src", "Opto SC Source", "SC Src", [dx(7) + 4, DY + 31, 120, 14], ["INT", "CHAIN", "EXT"], 0, GOLD))
pd(1, comment("T4 OPTICAL CELL  |  FEEDBACK DETECTOR  |  ~10 ms ATTACK, 60 ms + 0.5-5 s RELEASE", [DX, DY + 52, 520, 11], MUTED, 7.5, 0))
# VCA
pd(2, dial("v_in", "VCA Input", "VCA In", [dx(0), DY, 48, 46], -24, 24, 0, 4, STEEL))
pd(2, dial("v_thr", "VCA Threshold", "Thresh", [dx(1), DY, 48, 46], -50, 0, -20, 4, STEEL))
pd(2, dial("v_rel", "VCA Release", "Release", [dx(2), DY, 48, 46], 0.05, 3, 0.3, 1, STEEL, exponent=2.5, units="%0.2f s"))
pd(2, dial("v_hpf", "VCA SC HPF", "SC HPF", [dx(3), DY, 48, 46], 20, 500, 20, 3, STEEL, exponent=2.0))
pd(2, dial("v_link", "VCA Link", "Link", [dx(4), DY, 48, 46], 0, 100, 100, 5, STEEL))
pd(2, dial("v_mix", "VCA Mix", "Mix", [dx(5), DY, 48, 46], 0, 100, 100, 5, STEEL))
pd(2, dial("v_out", "VCA Output", "VCA Out", [dx(6), DY, 48, 46], -24, 24, 0, 4, STEEL))
pd(2, menu("v_ratio", "VCA Ratio", "Ratio", [dx(7) + 4, DY, 56, 14], ["1.5:1", "2:1", "3:1", "4:1", "6:1", "10:1", "inf:1"], 3, STEEL))
pd(2, menu("v_att", "VCA Attack", "Attack", [dx(7) + 64, DY, 56, 14], [".03ms", ".1ms", ".3ms", "1ms", "3ms", "10ms", "30ms"], 3, STEEL))
pd(2, tab("v_knee", "VCA Knee", "Knee", [dx(7) + 4, DY + 16, 116, 12], ["HARD", "MED", "SOFT"], 0, STEEL))
pd(2, tab("v_thrust", "VCA Thrust", "Thrust", [dx(7) + 4, DY + 30, 116, 12], ["NORM", "MED", "LOUD"], 0, STEEL))
pd(2, tab("v_type", "VCA Type", "Type", [dx(7) + 4, DY + 44, 56, 12], ["NEW", "OLD"], 0, STEEL))
pd(2, toggle("v_auto", "VCA Auto Makeup", "Auto Makeup", [dx(7) + 64, DY + 44, 56, 12], "AUTO", 0, STEEL))
pd(2, tab("v_src", "VCA SC Source", "SC Src", [dx(7) + 4, DY + 58, 116, 12], ["INT", "CHAIN", "EXT"], 0, STEEL))
# GATE
pd(3, dial("g_thr", "Gate Threshold", "Thresh", [dx(0), DY, 48, 46], -80, 0, -40, 4, CREAM))
pd(3, dial("g_att", "Gate Attack", "Attack", [dx(1), DY, 48, 46], 0.1, 50, 1, 2, CREAM, exponent=3.0))
pd(3, dial("g_hold", "Gate Hold", "Hold", [dx(2), DY, 48, 46], 0, 500, 20, 2, CREAM, exponent=2.0))
pd(3, dial("g_rel", "Gate Release", "Release", [dx(3), DY, 48, 46], 5, 2000, 150, 2, CREAM, exponent=3.0))
pd(3, dial("g_range", "Gate Range", "Range", [dx(4), DY, 48, 46], -80, 0, -80, 4, CREAM))
pd(3, dial("g_hpf", "Gate Key HPF", "Key HPF", [dx(5), DY, 48, 46], 20, 2000, 20, 3, CREAM, exponent=3.0))
pd(3, dial("g_lpf", "Gate Key LPF", "Key LPF", [dx(6), DY, 48, 46], 200, 20000, 20000, 3, CREAM, exponent=3.0))
pd(3, comment("KEY SOURCE", [dx(7) + 4, DY + 4, 90, 9], MUTED, 7.0, 0))
pd(3, tab("g_src", "Gate Key Source", "Key Src", [dx(7) + 4, DY + 13, 120, 14], ["INT", "CHAIN", "EXT"], 0, CREAM))
pd(3, comment("INDEPENDENT OF CHAIN ORDER  |  4 dB HYSTERESIS", [DX, DY + 52, 520, 11], MUTED, 7.5, 0))
# varnames for page objects (comments/panels need one to be scriptable)
for pg, ids in pages.items():
    for j, bid in enumerate(ids):
        bx_ = next(b["box"] for b in boxes if b["box"]["id"] == bid)
        if "varname" not in bx_:
            bx_["varname"] = f"pg{pg}_{j}"
esel = newobj("sel 0 1 2 3", [1500, 1260, 90, 22], 2, 5, ["bang"] * 4 + [""])
connect(edit, 0, esel, 0)
connect(trig, 0, edit, 0)
for pg in range(4):
    cmds = []
    for p2, ids in pages.items():
        for bid in ids:
            vn = next(b["box"] for b in boxes if b["box"]["id"] == bid)["varname"]
            cmds.append(f"script {'show' if p2 == pg else 'hide'} {vn}")
    mb = box("message", [1500 + 30 * pg, 1290 + 4 * pg, 200, 22], text=", ".join(cmds), numinlets=2, numoutlets=1, outlettype=[""])
    connect(esel, pg, mb, 0)
    connect(mb, 0, thisp, 0)


# ------------------------------------------------- v1.4: FILTER ROUTING strip
# Appended after every v1.3 object; existing objects, ids and rects are unchanged.
RX = W_TOTAL
RW = 200
W_TOTAL = RX + RW + 4
panel([RX - 2, 0, W_TOTAL - RX + 2, H], BG, rounded=0)
panel([RX, 4, RW, 161], STRIP, border=T.BEVEL)
comment("FILTER ROUTING", [RX + 8, 6, 120, 14], T.TEXT, T.F_TITLE, 1)
comment("LP · HP · BP", [RX + 140, 8, 56, 10], MUTED, T.F_TINY, 0)
rt = box("live.tab", [1900, 700, 74, 48], [RX + 6, 26, RW - 12, 15], numinlets=1, numoutlets=3, outlettype=["", "", "float"],
         parameter_enable=1, varname="flt_route", num_lines_patching=3, num_lines_presentation=1, fontsize=8.0, fontface=1,
         **SEG_COLOURS,
         saved_attribute_attributes=valueof("Filter Routing", "Routing", 2, 0, 2, 0, 9, enum=["SERIES", "PARALLEL", "HYBRID"]))
bid_x[rt] = 1900
param_ids[rt] = ("Filter Routing", "Routing")
wire(rt, "flt_route")
FLOW = ["IN > LP > HP > BP > OUT", "IN > BP > LP > HP > OUT", "IN > HP > LP > BP > OUT", "IN > BP > HP > LP > OUT",
        "IN > ( LP + HP + BP ) > OUT", "IN > ( LP > HP ) + BP > OUT", "IN > ( HP > LP ) + BP > OUT"]
flow = comment(FLOW[0], [RX + 6, 95, RW - 12, 10], MUTED, T.F_TINY, 1, 1)
named(flow, "route_flow")
ob = next(b["box"]["id"] for b in boxes if b["box"].get("varname") == "order_sel")
pb = next(b["box"]["id"] for b in boxes if b["box"].get("varname") == "b_pos")
rpk = newobj("pak 0 0 0", [1900, 760, 80, 22], 3, 1, [""])
rex = newobj("expr ($i1 == 0) * ($i2 * 2 + $i3) + ($i1 == 1) * 4 + ($i1 == 2) * (5 + $i2)", [1900, 790, 300, 22], 3, 1, [""])
rsel = newobj("sel 0 1 2 3 4 5 6", [1900, 820, 130, 22], 2, 8, ["bang"] * 7 + [""])
connect(rt, 0, rpk, 0)
connect(ob, 0, rpk, 1)
connect(pb, 0, rpk, 2)
connect(rpk, 0, rex, 0)
connect(rex, 0, rsel, 0)
for i, t in enumerate(FLOW):
    mb = box("message", [1900 + 15 * i, 850 + 4 * i, 160, 22], text="set " + t, numinlets=2, numoutlets=1, outlettype=[""])
    connect(rsel, i, mb, 0)
    connect(mb, 0, flow, 0)
comment("PARALLEL LEVELS", [RX + 6, 106, RW - 12, 9], T.AMBER, T.F_TINY, 1, 1)
dial("par_l", "Parallel LPF Level", "LP Lvl", [RX + 12, 114, 56, 50], -40, 6, 0, 4, AMBER)
dial("par_h", "Parallel HPF Level", "HP Lvl", [RX + 72, 114, 56, 50], -40, 6, 0, 4, COPPER)
dial("par_b", "Parallel BPF Level", "BP Lvl", [RX + 132, 114, 56, 50], -40, 6, 0, 4, BRASS)
comment("PARALLEL: ALL THREE | HYBRID: BP LVL", [RX + 6, 146, 162, 12], MUTED, 7.0, 0)
hide(boxes[-1]["box"]["id"])   # v1.5: availability dimming of the level dials now shows this

# ------------------------------------------------- v1.5: premium UI layer
# Appended after every v1.4 object. Nothing here touches gen~, a Param or a parameter
# object's definition: it adds panels, jsui displays, availability colouring and Info
# View text. See docs/UI.md.
import ui_info as INFO
BYV = lambda vn: next(b["box"] for b in boxes if b["box"].get("varname") == vn)
BID = lambda vn: BYV(vn)["id"]
_v15 = [2400]


def vx():
    _v15[0] += 40
    return _v15[0]


def plate(prect, color, name=None, border=None):
    b = box("panel", [vx(), 1500, prect[2], prect[3]], prect, bgcolor=color, rounded=2, numinlets=1, numoutlets=0,
            background=1, **({"border": 1, "bordercolor": border} if border else {}))
    if name:
        named(b, name)
    return b


def jsui(fname, prect, args, ni, no, name):
    b = box("jsui", [vx(), 1600, prect[2], prect[3]], prect, filename=fname, jsarguments=args, numinlets=ni,
            numoutlets=no, outlettype=[""] * no, parameter_enable=0, border=0, varname=name)
    return b


# header bands (one per section), group separators
for x0, w0 in ((4, 298), (306, 88), (398, 298), (BX, BW_SEC), (CX, CW), (RX, RW)):
    plate([x0 + 1, 5, w0 - 2, 17], T.HEADER)
plate([310, 64, 80, 1], T.BEVEL_HI)
comment("PROCESSING", [308, 66, 84, 10], T.AMBER, T.F_TINY, 1, 1)
plate([CX + 6, 89, CW - 12, 1], T.BEVEL)

# chain blocks: header plates + captions, created at their TUBE > OPTO > VCA positions
CAPS = {"T": "TRIODE · OVERSAMPLED", "O": "T4 OPTO CELL", "V": "RMS VCA"}
for m in DYN.MODS:
    bx = SLOT_X[DYN.PERMS[0].index(m)]
    plate([bx + 1, BY + 1, BW_ - 2, 15], T.HEADER, f"blk_{m}_hdr")
    named(comment(CAPS[m], [bx + 90, BY + 37, BW_ - 94, 9], MUTED, T.F_TINY, 0, 2), f"blk_{m}_cap")
# gate block, same anatomy (fixed position: the gate runs after the reorderable chain)
plate([GX, BY, BW_, BH], T.INSET, "blk_G_bg", border=T.BEVEL)
plate([GX + 1, BY + 1, BW_ - 2, 15], T.HEADER, "blk_G_hdr")
comment("4 dB HYSTERESIS · HOLD", [GX + 6, BY + 37, BW_ - 12, 9], MUTED, T.F_TINY, 0)
comment("FIXED · AFTER CHAIN", [GX + 6, BY + 47, BW_ - 12, 9], T.TEXT_DIM, T.F_TINY, 0)

# suggested chain orders: jsui buttons lit when Chain Order equals the preset's order
for name, idx in DYN.PRESETS.items():
    old = BYV(f"preset_{idx}")
    old["hidden"] = 1                      # the v1.3 latching live.text stays (ids), hidden
    r = [CX + 280 + {0: 0, 4: 74, 3: 174}[idx], 5, {0: 70, 4: 96, 3: 82}[idx], 15]
    j = jsui("df_button.js", r, [name.replace(" ", "_"), idx, "select"], 1, 1, f"presetbtn_{idx}")
    connect(ordm, 0, j, 0)                 # Chain Order -> button state
    connect(j, 0, ordm, 0)                 # click -> Chain Order (the parameter)

# routing diagram (display) fed by every parameter that changes the topology
rd = jsui("df_routing.js", [RX + 6, 44, RW - 12, 49], [], 1, 0, "route_diagram")
for vn, msg in (("flt_route", "route"), ("order_sel", "order"), ("b_pos", "bpos"), ("l_on", "lon"), ("h_on", "hon"), ("b_on", "bon")):
    p = newobj(f"prepend {msg}", [vx(), 1650, 90, 22], 1, 1, [""])
    connect(BID(vn), 0, p, 0)
    connect(p, 0, rd, 0)
# band-pass architecture glyph
ag = jsui("df_arch.js", [BX + 352, 46, 62, 112], [], 1, 0, "bpf_arch_glyph")
for vn, msg in (("b_arch", "arch"), ("b_on", "on")):
    p = newobj(f"prepend {msg}", [vx(), 1650, 90, 22], 1, 1, [""])
    connect(BID(vn), 0, p, 0)
    connect(p, 0, ag, 0)

# availability: a control that is bypassed, or not read by the current configuration,
# is drawn in reduced contrast. Only colour attributes change; the control stays fully
# editable (active stays 1), so values can be prepared before switching.
c4 = lambda c: " ".join(f"{v:g}" for v in c)
LOOK = {
    "live.dial": ({"activedialcolor": T.AMBER, "activeneedlecolor": T.TEXT},
                  {"activedialcolor": T.ARC_OFF, "activeneedlecolor": T.TEXT_DIM}),
    "live.tab": ({"activebgoncolor": T.AMBER, "textcolor": T.LABEL}, {"activebgoncolor": T.AMBER_DIM, "textcolor": T.TEXT_DIM}),
    "live.text": ({"activebgoncolor": T.AMBER, "activetextcolor": T.LABEL},
                  {"activebgoncolor": T.AMBER_DIM, "activetextcolor": T.TEXT_DIM}),
    "live.menu": ({"textcolor": T.TEXT, "tricolor": T.AMBER}, {"textcolor": T.TEXT_DIM, "tricolor": T.TEXT_DIM}),
}
AVAIL = []   # (rule text, sources, targets) — also exported for the tests / docs


def avail(srcs, expr, targets, why):
    AVAIL.append({"sources": srcs, "expr": expr, "targets": targets, "why": why})
    n = len(srcs)
    if n == 1 and expr == "$i1":
        gate = None
    else:
        pk = newobj("pak " + " ".join(["0"] * n), [vx(), 1700, 80, 22], n, 1, [""])
        for i, s_ in enumerate(srcs):
            connect(BID(s_), 0, pk, i)
        gate = newobj(f"expr {expr}", [vx(), 1730, 200, 22], n, 1, [""])
        connect(pk, 0, gate, 0)
    sel = newobj("sel 0 1", [vx(), 1760, 50, 22], 2, 3, ["bang", "bang", ""])
    connect(gate if gate else BID(srcs[0]), 0, sel, 0)
    for state in (0, 1):
        by_cls = {}
        for t in targets:
            by_cls.setdefault(BYV(t)["maxclass"], []).append(t)
        for cls, ts in by_cls.items():
            attrs = LOOK[cls][0 if state else 1]
            mb = box("message", [vx(), 1790 + 30 * state, 200, 22], text=", ".join(f"{k} {c4(v)}" for k, v in attrs.items()),
                     numinlets=2, numoutlets=1, outlettype=[""])
            connect(sel, state, mb, 0)
            for t in ts:
                connect(mb, 0, BID(t), 0)


LP_CTRL = ["l_model", "l_cut", "l_res", "l_drive", "l_comp", "l_char", "l_slope"]
HP_CTRL = [c.replace("l_", "h_", 1) for c in LP_CTRL]
avail(["l_on"], "$i1", LP_CTRL, "LPF bypassed")
avail(["h_on"], "$i1", HP_CTRL, "HPF bypassed")
avail(["b_on"], "$i1", ["b_model", "b_arch", "b_freq", "b_res", "b_drive", "b_mix"], "BPF bypassed")
avail(["b_on", "b_arch"], "$i1 && ($i2 != 0)", ["b_bw"], "SVF does not read Bandwidth")
avail(["b_on", "b_arch"], "$i1 && ($i2 != 2)", ["b_q", "b_comp"], "MULTI does not read Q or Compensation")
avail(["b_on", "flt_route"], "$i1 && ($i2 == 0)", ["b_pos"], "BPF Position applies to SERIES only")
avail(["flt_route"], "$i1 != 1", ["order_sel"], "PARALLEL has no LP/HP order")
avail(["flt_route"], "$i1 == 1", ["par_l", "par_h"], "LP/HP levels apply to PARALLEL only")
avail(["flt_route"], "$i1 != 0", ["par_b"], "BP level applies to PARALLEL and HYBRID")
for pfx, on in (("t", "t_on"), ("o", "o_on"), ("v", "v_on"), ("g", "g_on")):
    ts = [b["box"]["varname"] for b in boxes if b["box"].get("parameter_enable")
          and b["box"].get("varname", "").startswith(pfx + "_") and b["box"]["varname"] != on]
    avail([on], "$i1", ts, f"{on[:-3].upper()} module bypassed")

# ------------------------------------------------- v1.6: ENGINE strip (mode, high oversampling, active factors)
# Appended after every v1.5 object. gen~ gains outlets 15-17 (filter factor, TUBE factor, fault flag).
gb["numoutlets"] = 17
gb["outlettype"] = ["signal"] * 17
gp["boxes"][2]["box"]["numoutlets"] = 17
gp["boxes"][2]["box"]["outlettype"] = [""] * 17
for i in range(15, 18):
    gp["boxes"].append({"box": {"id": f"obj-out{i}", "maxclass": "newobj", "text": f"out {i}", "numinlets": 1, "numoutlets": 0,
                                "patching_rect": [20 + 50 * i, 680, 40, 22]}})
    gp["lines"].append({"patchline": {"source": ["obj-3", i - 1], "destination": [f"obj-out{i}", 0]}})
EX = W_TOTAL
EW = 122
W_TOTAL = EX + EW + 4
panel([EX - 2, 0, W_TOTAL - EX + 2, H], BG, rounded=0)
panel([EX, 4, EW, 161], STRIP, border=T.BEVEL)
plate([EX + 1, 5, EW - 2, 17], T.HEADER)
comment("ENGINE", [EX + 8, 6, 100, 14], T.TEXT, T.F_TITLE, 1)
comment("MODE", [EX + 6, 25, EW - 12, 10], T.AMBER, T.F_TINY, 1)
em = box("live.tab", [2900, 700, 110, 30], [EX + 6, 36, EW - 12, 32], numinlets=1, numoutlets=3, outlettype=["", "", "float"],
         parameter_enable=1, varname="eng_mode", num_lines_patching=2, num_lines_presentation=2, fontsize=8.0, fontface=1,
         **SEG_COLOURS, saved_attribute_attributes=valueof("Engine Mode", "Mode", 2, 0, 1, 0, 9, enum=["REFERENCE", "CREATIVE"]))
bid_x[em] = 2900
param_ids[em] = ("Engine Mode", "Mode")
wire(em, "eng_mode")
comment("HIGH OVERSAMPLING", [EX + 6, 72, EW - 12, 10], MUTED, T.F_TINY, 0)
oh = box("live.tab", [3020, 700, 110, 15], [EX + 6, 83, EW - 12, 15], numinlets=1, numoutlets=3, outlettype=["", "", "float"],
         parameter_enable=1, varname="ovs_hi", num_lines_patching=1, num_lines_presentation=1, fontsize=8.0, fontface=1,
         **SEG_COLOURS, saved_attribute_attributes=valueof("High Oversampling", "High OS", 2, 0, 3, 0, 9, enum=["OFF", "4x", "8x", "16x"]))
bid_x[oh] = 3020
param_ids[oh] = ("High Oversampling", "High OS")
wire(oh, "ovs_hi")
plate([EX + 6, 104, EW - 12, 1], T.BEVEL)
comment("RUNNING AT", [EX + 6, 107, EW - 12, 10], T.AMBER, T.F_TINY, 1)
for j, (lab, outlet, vn) in enumerate((("FILTERS", 14, "os_now_filters"), ("TUBE", 15, "os_now_tube"))):
    comment(lab, [EX + 6, 120 + 16 * j, 60, 12], MUTED, T.F_SMALL, 0)
    rd_ = comment("1x" if j == 0 else "2x", [EX + 70, 120 + 16 * j, 44, 12], T.TEXT, T.F_LABEL, 1, 2)
    named(rd_, vn)
    sn = newobj("snapshot~ 100", [3150 + 120 * j, 760, 80, 22], 2, 1, ["float"])
    ii = newobj("i", [3150 + 120 * j, 790, 30, 22], 2, 1, ["int"])
    ch_ = newobj("change", [3150 + 120 * j, 820, 50, 22], 1, 3, ["", "int", "int"])
    sp = newobj("sprintf set %ldx", [3150 + 120 * j, 850, 100, 22], 1, 1, [""])
    connect(gen, outlet, sn, 0); connect(sn, 0, ii, 0); connect(ii, 0, ch_, 0); connect(ch_, 0, sp, 0); connect(sp, 0, rd_, 0)
comment("REF = MODEL MINIMUMS", [EX + 6, 152, EW - 12, 10], T.TEXT_DIM, 6.5, 0)

# ------------------------------------------------- v1.6: K35 CIRCUIT strip (Stinchcombe 2006)
KX = W_TOTAL
KW = 92
W_TOTAL = KX + KW + 4
panel([KX - 2, 0, W_TOTAL - KX + 2, H], BG, rounded=0)
panel([KX, 4, KW, 161], STRIP, border=T.BEVEL)
plate([KX + 1, 5, KW - 2, 17], T.HEADER)
comment("K35", [KX + 8, 6, 76, 14], T.TEXT, T.F_TITLE, 1)
comment("CIRCUIT", [KX + 6, 25, KW - 12, 10], T.AMBER, T.F_TINY, 1)
kc = box("live.tab", [3400, 700, 90, 30], [KX + 6, 36, KW - 12, 32], numinlets=1, numoutlets=3, outlettype=["", "", "float"],
         parameter_enable=1, varname="k35_circ", num_lines_patching=2, num_lines_presentation=2, fontsize=8.0, fontface=1,
         **SEG_COLOURS, saved_attribute_attributes=valueof("K35 Circuit", "K35 Circ", 2, 0, 1, 0, 9, enum=["OTA (Mk2)", "KORG-35 (Mk1)"]))
bid_x[kc] = 3400
param_ids[kc] = ("K35 Circuit", "K35 Circ")
wire(kc, "k35_circ")
for j, ln in enumerate(("OTA: LM13600, diodes", "in the feedback path", "", "KORG-35: diodes in", "the signal path:", "all frequencies clip", "", "applies to LPF + HPF")):
    comment(ln, [KX + 6, 74 + 10 * j, KW - 10, 10], T.TEXT_DIM if ln else MUTED, 6.5, 0)

# ------------------------------------------------- v1.6: SHERMAN strip (Filterbank 2 manual features)
SX = W_TOTAL
SW = 150
W_TOTAL = SX + SW + 4
panel([SX - 2, 0, W_TOTAL - SX + 2, H], BG, rounded=0)
panel([SX, 4, SW, 161], STRIP, border=T.BEVEL)
plate([SX + 1, 5, SW - 2, 17], T.HEADER)
comment("SHERMAN", [SX + 8, 6, 120, 14], T.TEXT, T.F_TITLE, 1)
sm = box("live.tab", [3520, 700, 100, 15], [SX + 6, 26, SW - 12, 15], numinlets=1, numoutlets=3, outlettype=["", "", "float"],
         parameter_enable=1, varname="sh_mode", num_lines_patching=1, num_lines_presentation=1, fontsize=8.0, fontface=1,
         **SEG_COLOURS, saved_attribute_attributes=valueof("Sherman Modes", "Sh Modes", 2, 0, 1, 0, 9, enum=["STAGE", "PANEL"]))
bid_x[sm] = 3520
param_ids[sm] = ("Sherman Modes", "Sh Modes")
wire(sm, "sh_mode")
dial("sh_bal", "Sherman Balance", "Sh Bal", [SX + 6, 46, 44, 48], 0, 100, 0, 5, T.AMBER)
dial("sh_corr", "Sherman Correction", "Sh Corr", [SX + 53, 46, 44, 48], -100, 100, 0, 5, T.AMBER)
comment("HARMONICS", [SX + 100, 46, 46, 10], MUTED, T.F_TINY, 0)
menu("sh_harm", "Sherman Harmonics", "Sh Harm", [SX + 100, 58, 44, 16], ["1", "1.5", "2", "3", "4", "5", "6", "7", "8", "9", "16"], 0, T.AMBER)
comment("LP  BP  HP", [SX + 6, 95, 44, 10], T.TEXT_DIM, 6.5, 1)
comment("-B  0  -B+LH", [SX + 53, 95, 46, 10], T.TEXT_DIM, 6.5, 1)
sl = box("live.tab", [3640, 700, 60, 15], [SX + 6, 112, 66, 15], numinlets=1, numoutlets=3, outlettype=["", "", "float"],
         parameter_enable=1, varname="sh_limit", num_lines_patching=1, num_lines_presentation=1, fontsize=8.0, fontface=1,
         **SEG_COLOURS, saved_attribute_attributes=valueof("Sherman Limit", "Sh Limit", 2, 0, 1, 0, 9, enum=["NORMAL", "LIMIT"]))
bid_x[sl] = 3640
param_ids[sl] = ("Sherman Limit", "Sh Limit")
wire(sl, "sh_limit")
sc = box("live.tab", [3720, 700, 60, 15], [SX + 78, 112, 66, 15], numinlets=1, numoutlets=3, outlettype=["", "", "float"],
         parameter_enable=1, varname="sh_clock", num_lines_patching=1, num_lines_presentation=1, fontsize=8.0, fontface=1,
         **SEG_COLOURS, saved_attribute_attributes=valueof("Sherman Clock", "Sh Clock", 2, 0, 1, 0, 9, enum=["SMOOTH", "CLOCK"]))
bid_x[sc] = 3720
param_ids[sc] = ("Sherman Clock", "Sh Clock")
wire(sc, "sh_clock")
for j, ln in enumerate(("applies to model 01 in", "either stage; balance /", "correction need PANEL;", "harmonics: 24 dB only")):
    comment(ln, [SX + 6, 130 + 8 * j, SW - 10, 9], T.TEXT_DIM, 6.0, 0)

# ------------------------------------------------- v1.6: ENVELOPE FILTER strip (Mu-Tron III topology) + envelope routing
FX = W_TOTAL
FW = 236
W_TOTAL = FX + FW + 4
panel([FX - 2, 0, W_TOTAL - FX + 2, H], BG, rounded=0)
panel([FX, 4, FW, 161], STRIP, border=T.BEVEL)
plate([FX + 1, 5, FW - 2, 17], T.HEADER)
comment("ENVELOPE FILTER", [FX + 8, 6, 160, 14], T.TEXT, T.F_TITLE, 1)
def ftab(var, long, short, prect, items, x0):
    b = box("live.tab", [x0, 700, prect[2], 15], prect, numinlets=1, numoutlets=3, outlettype=["", "", "float"],
            parameter_enable=1, varname=var, num_lines_patching=1, num_lines_presentation=1, fontsize=8.0, fontface=1,
            **SEG_COLOURS, saved_attribute_attributes=valueof(long, short, 2, 0, len(items) - 1, ENV_INIT[var], 9, enum=items))
    bid_x[b] = x0
    param_ids[b] = (long, short)
    wire(b, var)
    return b
ENV_INIT = {"ef_on": 0, "ef_range": 1, "ef_sweep": 0}
ftab("ef_on", "EnvF On", "EnvF On", [FX + 6, 26, 52, 15], ["OFF", "ON"], 3800)
menu("ef_mode", "EnvF Mode", "EnvF Mode", [FX + 62, 26, 48, 15], ["LP", "BP", "HP"], 1, T.AMBER)
ftab("ef_range", "EnvF Range", "EnvF Range", [FX + 114, 26, 56, 15], ["LO", "HI"], 3870)
ftab("ef_sweep", "EnvF Sweep", "EnvF Sweep", [FX + 174, 26, 56, 15], ["UP", "DOWN"], 3940)
dial("ef_peak", "EnvF Peak", "Peak", [FX + 6, 46, 54, 48], 0, 100, 50, 5, T.AMBER)
dial("ef_gain", "EnvF Gain", "Gain", [FX + 63, 46, 54, 48], -18.4, 31.2, 0, 4, T.AMBER)
dial("ef_att", "EnvF Attack", "Attack", [FX + 120, 46, 54, 48], 0.5, 50, 1.55, 2, T.AMBER, exponent=2.5)
dial("ef_rel", "EnvF Release", "Release", [FX + 177, 46, 54, 48], 10, 1000, 221, 2, T.AMBER, exponent=2.5)
dial("ef_mix", "EnvF Mix", "Mix", [FX + 6, 100, 44, 48], 0, 100, 100, 5, T.AMBER)
dial("ef_out", "EnvF Output", "Out", [FX + 52, 100, 44, 48], -24, 12, 0, 4, T.AMBER)
dial("ef_to_l", "EnvF to LPF", "> LPF", [FX + 98, 100, 44, 48], -5, 5, 0, 9, T.AMBER, units="%+0.1f oct")
dial("ef_to_h", "EnvF to HPF", "> HPF", [FX + 144, 100, 44, 48], -5, 5, 0, 9, T.AMBER, units="%+0.1f oct")
dial("ef_to_b", "EnvF to BPF", "> BPF", [FX + 190, 100, 44, 48], -5, 5, 0, 9, T.AMBER, units="%+0.1f oct")
comment("before the filters; routing works with the envelope filter on or off", [FX + 6, 150, FW - 10, 9], T.TEXT_DIM, 6.0, 0)

# Info View / hint text on every parameter and on the jsui controls
for b in boxes:
    bb = b["box"]
    if bb.get("parameter_enable"):
        v = bb["saved_attribute_attributes"]["valueof"]
        bb["annotation_name"] = v["parameter_longname"]
        bb["annotation"] = INFO.describe(bb["varname"], v)
        bb["hint"] = v["parameter_longname"] + ": " + INFO.DESC.get(bb["varname"], "")
for vn, (nm, txt) in INFO.UI_DESC.items():
    for cand in (vn, vn.replace("preset_", "presetbtn_")):
        hits = [b["box"] for b in boxes if b["box"].get("varname") == cand and b["box"]["maxclass"] != "live.text"]
        for bb in hits:
            bb["annotation_name"] = nm
            bb["annotation"] = txt
            bb["hint"] = f"{nm}: {txt}"

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
        "description": "Dub Filter - multi-model analogue-inspired LPF/HPF/BPF (series/parallel) + dynamics chain",
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
import shutil
for f in sorted(os.listdir(os.path.join(HERE, "jsui"))):
    if f.endswith(".js"):
        shutil.copy(os.path.join(HERE, "jsui", f), os.path.join(out_dir, f))
with open(os.path.join(out_dir, "ui_availability.json"), "w") as f:
    json.dump(AVAIL, f, indent=1)
print(f"boxes {len(boxes)}, lines {len(lines)}, parameters {len(param_ids)}, amxd {len(amxd)} bytes")

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

EMBER = [0.902, 0.420, 0.220, 1.0]
GOLD = [0.922, 0.780, 0.420, 1.0]
STEEL = [0.800, 0.760, 0.680, 1.0]
MCOL = {"T": EMBER, "O": GOLD, "V": STEEL}
CX = W_TOTAL
W_TOTAL = CX + 704 + 4
panel([CX - 2, 0, W_TOTAL - CX + 2, H], BG, rounded=0)
panel([CX, 4, 704, 161], PANEL, border=[0.45, 0.42, 0.38, 1])
comment("PROCESSING CHAIN", [CX + 6, 5, 150, 16], CREAM, 11.0, 1)
box("panel", [CX, 1200, 692, 2], [CX + 6, 22, 692, 1], bgcolor=DIM, rounded=0, numinlets=1, numoutlets=0)

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
ordm = menu("c_order", "Chain Order", "Order", [CX + 160, 5, 150, 15], DYN.PERM_NAMES, 0, CREAM)
presets = []
px = CX + 316
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
comment("KEY LISTEN", [CX + 540, 4, 70, 9], MUTED, 7.0, 0)
tab("key_listen", "Key Listen", "Key Listen", [CX + 540, 12, 160, 10], ["OFF", "OPTO", "VCA", "GATE"], 0, CREAM)
kr = box("live.routing", [1600, 800, 120, 40], [CX + 604, 118, 96, 34], numinlets=1, numoutlets=1, outlettype=[""],
         varname="key_routing", fontsize=8.0, textcolor=CREAM)
comment("EXTERNAL KEY (SIDECHAIN)", [CX + 604, 106, 100, 10], MUTED, 6.5, 0)

# flow strip: IN -> slot1 -> slot2 -> slot3 -> GATE -> OUT
SLOT_X = [CX + 26, CX + 214, CX + 402]
BY, BW_, BH = 27, 170, 58
comment("IN", [CX + 6, BY + 20, 18, 12], MUTED, 8.0, 1)
for k in range(3):
    comment(">", [SLOT_X[k] + BW_ + 3, BY + 20, 14, 12], MUTED, 9.0, 1)
GX = CX + 590
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
    blk(m, panel([bx, BY, BW_, BH], STRIP, border=col), 0, 0, BW_, BH, f"blk_{m}_bg")
    blk(m, comment(DYN.MOD_NAMES[m], [bx + 4, BY + 2, 112, 12], col, 8.5, 1), 4, 2, 112, 12, f"blk_{m}_name")
    on = toggle(f"{p}_on", {"t": "Tube On", "o": "Opto On", "v": "VCA On"}[p], {"t": "Tube On", "o": "Opto On", "v": "VCA On"}[p],
                [bx + 126, BY + 2, 40, 13], "ON", 0, col)
    block_objs[m].append((f"{p}_on", 126, 2, 40, 13))
    for j, (lab, outlet) in enumerate((("IN", {"T": 2, "O": 4, "V": 7}[m]), ("OUT", {"T": 3, "O": 5, "V": 8}[m]))):
        blk(m, comment(lab, [bx + 4, BY + 16 + 9 * j, 24, 9], MUTED, 7.0, 0), 4, 16 + 9 * j, 24, 9, f"blk_{m}_l{j}")
        mt = box("live.meter~", [1200 + 60 * DYN.MODS.index(m), 820 + 30 * j, 80, 6], [bx + 28, BY + 18 + 9 * j, 138, 5],
                 numinlets=1, numoutlets=1, outlettype=["list"], orientation=1, coldcolor=col, warmcolor=col, hotcolor=EMBER,
                 overloadcolor=[0.9, 0.2, 0.15, 1])
        blk(m, mt, 28, 18 + 9 * j, 138, 5, f"blk_{m}_m{j}")
        connect(gen, outlet, mt, 0)
    if m != "T":
        blk(m, comment("GR", [bx + 4, BY + 34, 34, 9], MUTED, 7.0, 0), 4, 34, 34, 9, f"blk_{m}_l2")
        snap = newobj("snapshot~ 50", [1200 + 60 * DYN.MODS.index(m), 900, 80, 22], 2, 1, ["float"])
        mul = newobj("* 30.", [1200 + 60 * DYN.MODS.index(m), 930, 40, 22], 2, 1, ["float"])
        nb = box("live.numbox", [1200 + 60 * DYN.MODS.index(m), 960, 44, 15], [bx + 40, BY + 33, 44, 11],
                 numinlets=1, numoutlets=2, outlettype=["", "float"], parameter_enable=0, fontsize=7.5,
                 textcolor=col, activeslidercolor=col, appearance=0)
        connect(gen, {"O": 6, "V": 9}[m], snap, 0)
        connect(snap, 0, mul, 0)
        connect(mul, 0, nb, 0)
        blk(m, nb, 40, 33, 44, 11, f"blk_{m}_gr")
        blk(m, comment("dB", [bx + 86, BY + 34, 20, 9], MUTED, 7.0, 0), 86, 34, 20, 9, f"blk_{m}_db")
    # drag handle: drag the grip left/right and release to move the block (1 or 2 slots)
    grip = box("live.slider", [1200 + 60 * DYN.MODS.index(m), 1000, 160, 10], [bx + 4, BY + 45, 162, 11],
               numinlets=1, numoutlets=2, outlettype=["", "float"], parameter_enable=0, orientation=1,
               min=-2.0, size=4.0, showname=0, shownumber=0, slidercolor=col, trioncolor=col, tribordercolor=DIM,
               textcolor=MUTED)
    blk(m, grip, 4, 45, 162, 11, f"blk_{m}_grip")
    block_objs[m + "_grip_id"] = grip
comment("GATE", [GX, BY + 2, 40, 12], CREAM, 8.5, 1)
toggle("g_on", "Gate On", "Gate On", [GX + 50, BY + 2, 40, 13], "ON", 0, CREAM)
gm = box("live.meter~", [1400, 820, 80, 6], [GX, BY + 18, 90, 5], numinlets=1, numoutlets=1, outlettype=["list"],
         orientation=1, coldcolor=CREAM, warmcolor=CREAM, hotcolor=CREAM, varname="gate_meter")
connect(gen, 10, gm, 0)
comment("OPEN", [GX, BY + 24, 40, 9], MUTED, 7.0, 0)
km = box("live.meter~", [1400, 850, 80, 6], [GX, BY + 36, 90, 5], numinlets=1, numoutlets=1, outlettype=["list"],
         orientation=1, coldcolor=MUTED, warmcolor=MUTED, hotcolor=EMBER, varname="key_meter")
connect(gen, 11, km, 0)
comment("EXT KEY", [GX, BY + 42, 50, 9], MUTED, 7.0, 0)
comment("> OUT", [GX + 56, BY + 44, 40, 12], MUTED, 8.0, 1)

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
DY = 90
edit = box("live.tab", [1500, 1150, 70, 68], [CX + 6, DY, 72, 70], numinlets=1, numoutlets=3, outlettype=["", "", "float"],
           parameter_enable=0, num_lines_patching=4, num_lines_presentation=4, fontsize=8.0, textcolor=MUTED, textoncolor=BG,
           bgcolor=PANEL, bgoncolor=CREAM, activebgcolor=PANEL, activebgoncolor=CREAM, bordercolor=DIM, varname="edit_page")
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
pd(0, comment("TRIODE STAGE  |  2x OVERSAMPLED  |  AUTO GAIN HOLDS -12 dBFS PROGRAM LEVEL", [DX, DY + 52, 520, 11], MUTED, 7.5, 0))
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
        "description": "Dub Filter - multi-model analogue-inspired LPF/HPF/BPF + dynamics chain",
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

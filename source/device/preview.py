"""Approximate render of the presentation layout (not Max's renderer).

v1.5: draws the jsui components by running their real JavaScript through
tools/jsui_sim.js (SVG -> PNG via rsvg-convert), and applies the availability
rules (build/device/ui_availability.json) at the parameters' default values, so the
picture shows the dimmed/unavailable states the device starts in.
usage: preview.py out.png [--state key=value ...]"""
import json, math, os, re, subprocess, sys, tempfile
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import FancyBboxPatch, Rectangle, Arc

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "..", "build", "device")
P = json.load(open(os.path.join(BUILD, "DubFilter.maxpat")))["patcher"]
args = sys.argv[1:]
outp = next((a for a in args if not a.startswith("--") and "=" not in a), os.path.join(BUILD, "preview.png"))
W, H = int(P.get("devicewidth", 700)), 169
S = 2
boxes = [b["box"] for b in P["boxes"]]
byv = {b["varname"]: b for b in boxes if b.get("varname")}

# parameter state: defaults, optionally overridden (--state flt_route=1 ...)
state = {}
for b in boxes:
    if b.get("parameter_enable"):
        state[b["varname"]] = b["saved_attribute_attributes"]["valueof"]["parameter_initial"][0]
for a in args:
    if "=" in a and not a.startswith("--"):
        k, v = a.split("="); state[k] = float(v)
page = int(state.pop("_page", 0)) if "_page" in state else 0

# availability at this state (same rules the patch evaluates)
dim = set()
av_path = os.path.join(BUILD, "ui_availability.json")
if os.path.exists(av_path):
    for r in json.load(open(av_path)):
        vals = [state[s] for s in r["sources"]]
        ex = r["expr"].replace("&&", " and ").replace("!=", " != ")
        ex = re.sub(r"\$i(\d)", lambda m: repr(vals[int(m.group(1)) - 1]), ex)
        if not eval(ex):
            dim.update(r["targets"])

# chain order / edit page placement (mirrors the thispatcher scripting)
import importlib.util
sys.path.insert(0, os.path.join(HERE, "..", "src"))
fig = plt.figure(figsize=(W * S / 100, H * S / 100), dpi=100)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
c = lambda v: tuple(v[:3])
AMBER_DIM, ARC_OFF, TEXT_DIM = (0.42, 0.29, 0.141), (0.29, 0.267, 0.239), (0.369, 0.345, 0.314)

pages = {"TUBE": "t_", "OPTO": "o_", "VCA": "v_", "GATE": "g_"}
cur_page = ["t_", "o_", "v_", "g_"][page]


def visible(b):
    if b.get("hidden"):
        vn = b.get("varname", "")
        # edit-page objects are hidden until their page is selected
        if re.match(r"pg(\d)_", vn):
            return int(vn[2]) == page
        if b.get("parameter_enable") and vn[:2] in ("t_", "o_", "v_", "g_") and not vn.endswith("_on"):
            return vn.startswith(cur_page)
        return False
    vn = b.get("varname", "")
    if b.get("parameter_enable") and vn[:2] in ("t_", "o_", "v_", "g_") and not vn.endswith("_on"):
        return vn.startswith(cur_page)
    if re.match(r"pg(\d)_", vn):
        return int(vn[2]) == page
    return True


def jsui_png(b):
    x, y, w, h = b["presentation_rect"]
    js = os.path.join(HERE, "jsui", b["filename"])
    script = []
    if b["filename"] == "df_routing.js":
        script = [["route", state["flt_route"]], ["order", state["order_sel"]], ["bpos", state["b_pos"]],
                  ["lon", state["l_on"]], ["hon", state["h_on"]], ["bon", state["b_on"]]]
    elif b["filename"] == "df_arch.js":
        script = [["arch", state["b_arch"]], ["on", state["b_on"]]]
    elif b["filename"] == "df_button.js":
        script = [["int", state["c_order"]]]
    svg = tempfile.mktemp(suffix=".svg"); png = svg[:-4] + ".png"
    r = subprocess.run(["node", os.path.join(HERE, "..", "tools", "jsui_sim.js"), js, str(w), str(h),
                        json.dumps(b.get("jsarguments", [])), json.dumps(script), svg], capture_output=True, text=True)
    res = json.loads(r.stdout)
    assert not res["errors"], res["errors"]
    subprocess.run(["rsvg-convert", "-z", str(S * 2), svg, "-o", png], check=True)
    ax.imshow(mpimg.imread(png), extent=(x, x + w, y + h, y), zorder=3, interpolation="antialiased")


# apply the block-placement scripting for the chosen Chain Order, and the flow readout text
msgs = [b["text"] for b in boxes if b["maxclass"] == "message" and b.get("text", "").startswith("script sendbox")]
for cmd in msgs[int(state["c_order"])].split(", "):
    f = cmd.split()
    byv[f[2]]["presentation_rect"] = list(map(float, f[4:8]))
flows = [b["text"][4:] for b in boxes if b["maxclass"] == "message" and b.get("text", "").startswith("set IN >")]
rt_, od_, bp_ = int(state["flt_route"]), int(state["order_sel"]), int(state["b_pos"])
byv["route_flow"]["text"] = flows[(bp_ + 2 * od_) if rt_ == 0 else (4 if rt_ == 1 else 5 + od_)]
order = sorted([b for b in boxes if b.get("presentation")], key=lambda b: 0 if b["maxclass"] == "panel" and b.get("background") else 1)
for b in order:
    if not visible(b):
        continue
    x, y, w, h = b["presentation_rect"]; mc = b["maxclass"]; vn = b.get("varname", ""); off = vn in dim
    if mc == "panel":
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={b.get('rounded',0)}",
                     fc=c(b["bgcolor"]), ec=c(b.get("bordercolor", b["bgcolor"])), lw=0.8 if b.get("border") else 0))
    elif mc == "jsui":
        jsui_png(b)
    elif mc == "comment":
        ha = {0: "left", 1: "center", 2: "right"}[b.get("textjustification", 0)]
        tx = x + (w / 2 if ha == "center" else (w if ha == "right" else 0))
        ax.text(tx, y + 1, b["text"], color=c(b["textcolor"]), fontsize=b["fontsize"] * 0.72 * S, ha=ha, va="top",
                fontweight="bold" if b.get("fontface") else "normal", family="DejaVu Sans")
    elif mc == "live.dial":
        v = b["saved_attribute_attributes"]["valueof"]
        big = w > 80
        r = min(w, h - (24 if big else 18)) / 2 * (0.78 if big else 0.72)
        cx, cy = x + w / 2, y + (h / 2 + (0 if big else -1))
        arc = ARC_OFF if off else c(b["activedialcolor"])
        ax.add_patch(Arc((cx, cy), 2 * r, 2 * r, theta1=-60, theta2=240, color=(0.2, 0.19, 0.18), lw=3 * S if big else 2 * S))
        lo, hi, ini, ex = v["parameter_mmin"], v["parameter_mmax"], state.get(vn, v["parameter_initial"][0]), v.get("parameter_exponent", 1)
        frac = ((ini - lo) / (hi - lo)) ** (1 / ex)
        ax.add_patch(Arc((cx, cy), 2 * r, 2 * r, theta1=240 - 300 * frac, theta2=240, color=arc, lw=3 * S if big else 2 * S))
        ang = math.radians(240 - 300 * frac)
        ax.plot([cx, cx + r * 0.8 * math.cos(ang)], [cy, cy - r * 0.8 * math.sin(ang)],
                color=TEXT_DIM if off else c(b["activeneedlecolor"]), lw=1.2 * S)
        tc = TEXT_DIM if off else c(b["textcolor"])
        if b.get("showname", 1):
            ax.text(cx, y + 1, v["parameter_shortname"], color=tc, fontsize=(9 if big else 7) * S * 0.72, ha="center", va="top", fontweight="bold" if big else "normal")
        unit = {3: " Hz", 4: " dB", 5: " %"}.get(v["parameter_unitstyle"], "")
        val = f"{ini/1000:.1f} kHz" if unit == " Hz" and ini >= 1000 else f"{ini:g}{unit}"
        ax.text(cx, y + h - 1, val, color=tc, fontsize=(9 if big else 7) * S * 0.72, ha="center", va="bottom")
    elif mc in ("live.menu",):
        ax.add_patch(Rectangle((x, y), w, h, fc=c(b.get("activebgcolor", b["bgcolor"])), ec=(0.31, 0.28, 0.255), lw=0.6))
        v = b["saved_attribute_attributes"]["valueof"]
        ax.text(x + 4, y + h / 2, v["parameter_enum"][int(state.get(vn, v["parameter_initial"][0]))],
                color=TEXT_DIM if off else c(b["textcolor"]), fontsize=8 * S * 0.72, va="center")
        ax.text(x + w - 8, y + h / 2, "▾", color=TEXT_DIM if off else c(b["tricolor"]), fontsize=8 * S * 0.72, va="center")
    elif mc == "live.meter~":
        ax.add_patch(Rectangle((x, y), w, h, fc=(0.16, 0.15, 0.14), ec="none"))
        ax.add_patch(Rectangle((x, y), w * 0.55, h, fc=c(b.get("coldcolor", [0.6, 0.6, 0.6])), ec="none", alpha=0.8))
    elif mc == "live.slider":
        ax.add_patch(Rectangle((x, y + h * 0.3), w, h * 0.4, fc=(0.2, 0.19, 0.18), ec="none"))
        ax.add_patch(Rectangle((x + w / 2 - 14, y), 28, h, fc=c(b.get("trioncolor", [0.7, 0.7, 0.7])), ec="none"))
        ax.text(x + w / 2, y + h / 2, "◀ DRAG ▶", color=(0.1, 0.08, 0.06), fontsize=5.0 * S * 0.72, ha="center", va="center", fontweight="bold")
    elif mc == "live.numbox":
        ax.text(x + 2, y + h / 2, "0.0", color=c(b.get("textcolor", [0.9, 0.9, 0.9])), fontsize=7 * S * 0.72, va="center")
    elif mc == "live.routing":
        ax.add_patch(Rectangle((x, y), w, 15, fc=(0.09, 0.086, 0.082), ec=(0.31, 0.28, 0.255), lw=0.6))
        ax.add_patch(Rectangle((x, y + 18), w, 15, fc=(0.09, 0.086, 0.082), ec=(0.31, 0.28, 0.255), lw=0.6))
        ax.text(x + 4, y + 7, "Audio From  ▾", color=c(b.get("textcolor", [0.9, 0.9, 0.9])), fontsize=6.5 * S * 0.72, va="center")
        ax.text(x + 4, y + 25, "No Input  ▾", color=(0.64, 0.6, 0.55), fontsize=6.5 * S * 0.72, va="center")
    elif mc in ("live.tab", "live.text"):
        sav = b.get("saved_attribute_attributes", {}).get("valueof", {})
        if mc == "live.tab":
            items = sav.get("parameter_enum") or ["TUBE", "OPTO", "VCA", "GATE"]
        else:
            items = [b["text"]]
        n = len(items)
        ini = state.get(vn, sav.get("parameter_initial", [0])[0]) if sav.get("parameter_initial") else (page if vn == "edit_page" else 0)
        vert = mc == "live.tab" and b.get("num_lines_presentation", 1) > 1
        onc = AMBER_DIM if off else c(b.get("activebgoncolor", b.get("bgoncolor")))
        offc = c(b.get("activebgcolor", b.get("bgcolor")))
        tcol = c(b.get("activetextcolor", b.get("textcolor"))) if mc == "live.text" else c(b.get("textcolor"))
        tcol = TEXT_DIM if off else tcol
        tonc = c(b.get("activetextoncolor", b.get("textoncolor"))) if mc == "live.text" else c(b.get("textoncolor"))
        for i, it in enumerate(items):
            on = (i == int(ini)) if mc == "live.tab" else bool(ini)
            if vert:
                rect = (x, y + i * h / n, w, h / n); tx, ty = x + w / 2, y + (i + 0.5) * h / n
            else:
                rect = (x + i * w / n, y, w / n, h); tx, ty = x + (i + 0.5) * w / n, y + h / 2
            ax.add_patch(FancyBboxPatch(rect[:2], rect[2], rect[3], boxstyle="round,pad=0,rounding_size=1.5",
                         fc=onc if on else offc, ec=c(b["bordercolor"]), lw=0.6))
            ax.text(tx, ty, it, color=tonc if on else tcol, fontsize=7.0 * S * 0.72, ha="center", va="center", fontweight="bold")
fig.savefig(outp, dpi=100)
print("preview:", outp, "| dimmed:", len(dim), "controls")

"""Approximate render of the presentation layout (not Max's renderer)."""
import json, math, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Arc, Circle
P = json.load(open("build/device/DubFilter.maxpat"))["patcher"]
W, H = int(P.get("devicewidth", 700)), 169
S = 2
fig = plt.figure(figsize=(W * S / 100, H * S / 100), dpi=100)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
c = lambda v: tuple(v[:3])
order = sorted([b["box"] for b in P["boxes"] if b["box"].get("presentation")], key=lambda b: 0 if b["maxclass"] == "panel" else 1)
for b in order:
    if b.get("hidden"):
        continue
    x, y, w, h = b["presentation_rect"]; mc = b["maxclass"]
    if mc == "panel":
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={b.get('rounded',0)}",
                     fc=c(b["bgcolor"]), ec=c(b.get("bordercolor", b["bgcolor"])), lw=0.8 if b.get("border") else 0))
    elif mc == "comment":
        ha = {0: "left", 1: "center", 2: "right"}[b.get("textjustification", 0)]
        tx = x + (w / 2 if ha == "center" else 0)
        ax.text(tx, y + 1, b["text"], color=c(b["textcolor"]), fontsize=b["fontsize"] * 0.72 * S, ha=ha, va="top",
                fontweight="bold" if b.get("fontface") else "normal", family="DejaVu Sans")
    elif mc == "live.dial":
        v = b["saved_attribute_attributes"]["valueof"]
        big = w > 80
        r = min(w, h - (24 if big else 18)) / 2 * (0.78 if big else 0.72)
        cx, cy = x + w / 2, y + (h / 2 + (0 if big else -1))
        ax.add_patch(Arc((cx, cy), 2 * r, 2 * r, theta1=-60, theta2=240, color=c(b["dialcolor"]), lw=3 * S if big else 2 * S))
        lo, hi, ini, ex = v["parameter_mmin"], v["parameter_mmax"], v["parameter_initial"][0], v.get("parameter_exponent", 1)
        frac = ((ini - lo) / (hi - lo)) ** (1 / ex)
        ax.add_patch(Arc((cx, cy), 2 * r, 2 * r, theta1=240 - 300 * frac, theta2=240, color=c(b["activedialcolor"]), lw=3 * S if big else 2 * S))
        ang = math.radians(240 - 300 * frac)
        ax.plot([cx, cx + r * 0.8 * math.cos(ang)], [cy, cy - r * 0.8 * math.sin(ang)], color=c(b["activeneedlecolor"]), lw=1.2 * S)
        if b.get("showname", 1):
            ax.text(cx, y + 1, v["parameter_shortname"], color=c(b["textcolor"]), fontsize=(9 if big else 7) * S * 0.72, ha="center", va="top", fontweight="bold" if big else "normal")
        unit = {3: " Hz", 4: " dB", 5: " %"}.get(v["parameter_unitstyle"], "")
        val = f"{ini/1000:.1f} kHz" if unit == " Hz" and ini >= 1000 else f"{ini:g}{unit}"
        ax.text(cx, y + h - 1, val, color=c(b["textcolor"]), fontsize=(9 if big else 7) * S * 0.72, ha="center", va="bottom")
    elif mc in ("live.menu",):
        ax.add_patch(Rectangle((x, y), w, h, fc=c(b["bgcolor"]), ec=(0.3, 0.29, 0.27), lw=0.6))
        v = b["saved_attribute_attributes"]["valueof"]
        ax.text(x + 4, y + h / 2, v["parameter_enum"][v["parameter_initial"][0]], color=c(b["textcolor"]), fontsize=8 * S * 0.72, va="center")
        ax.text(x + w - 8, y + h / 2, "▾", color=c(b["tricolor"]), fontsize=8 * S * 0.72, va="center")
    elif mc == "live.meter~":
        ax.add_patch(Rectangle((x, y), w, h, fc=(0.16, 0.15, 0.14), ec="none"))
        ax.add_patch(Rectangle((x, y), w * 0.55, h, fc=c(b.get("coldcolor", [0.6, 0.6, 0.6])), ec="none", alpha=0.8))
    elif mc == "live.slider":
        ax.add_patch(Rectangle((x, y + h * 0.35), w, h * 0.3, fc=(0.2, 0.19, 0.18), ec="none"))
        ax.add_patch(Rectangle((x + w / 2 - 6, y), 12, h, fc=c(b.get("slidercolor", [0.7, 0.7, 0.7])), ec="none"))
        ax.text(x + w / 2, y + h / 2, "◀ DRAG ▶", color=(0.1, 0.1, 0.1), fontsize=5.5 * S * 0.72, ha="center", va="center", fontweight="bold")
    elif mc == "live.numbox":
        ax.text(x + 2, y + h / 2, "0.0", color=c(b.get("textcolor", [0.9, 0.9, 0.9])), fontsize=7 * S * 0.72, va="center")
    elif mc == "live.routing":
        ax.add_patch(Rectangle((x, y), w, 26, fc=(0.16, 0.15, 0.14), ec=(0.3, 0.29, 0.27), lw=0.6))
        ax.text(x + 3, y + 7, "KEY FROM ▾", color=c(b.get("textcolor", [0.9, 0.9, 0.9])), fontsize=6.5 * S * 0.72, va="center")
        ax.text(x + 3, y + 19, "No Input ▾", color=(0.6, 0.58, 0.55), fontsize=6.5 * S * 0.72, va="center")
    elif mc in ("live.tab", "live.text") and "saved_attribute_attributes" not in b:
        ax.add_patch(Rectangle((x, y), w, h, fc=c(b["bgcolor"]), ec=c(b["bordercolor"]), lw=0.6))
        ax.text(x + w / 2, y + h / 2, b["text"], color=c(b["textcolor"]), fontsize=7 * S * 0.72, ha="center", va="center", fontweight="bold")
    elif mc in ("live.tab", "live.text"):
        v = b["saved_attribute_attributes"]["valueof"]
        items = v["parameter_enum"] if mc == "live.tab" else [b["text"]]
        n = len(items); ini = v.get("parameter_initial", [0])[0]
        vert = mc == "live.tab" and b.get("num_lines_presentation", 1) > 1
        for i, it in enumerate(items):
            on = (i == ini) if mc == "live.tab" else bool(ini)
            if vert:
                ax.add_patch(Rectangle((x, y + i * h / n), w, h / n, fc=c(b["bgoncolor"] if on else b["bgcolor"]), ec=c(b["bordercolor"]), lw=0.6))
                ax.text(x + w / 2, y + (i + 0.5) * h / n, it, color=c(b["textoncolor"] if on else b["textcolor"]), fontsize=7.2 * S * 0.72, ha="center", va="center", fontweight="bold")
                continue
            ax.add_patch(Rectangle((x + i * w / n, y), w / n, h, fc=c(b["bgoncolor"] if on else b["bgcolor"]), ec=c(b["bordercolor"]), lw=0.6))
            ax.text(x + (i + 0.5) * w / n, y + h / 2, it, color=c(b["textoncolor"] if on else b["textcolor"]), fontsize=7.2 * S * 0.72, ha="center", va="center", fontweight="bold")
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "build/device/preview.png", dpi=100)

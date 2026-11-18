"""Dub Filter v1.5 design system: one set of tokens shared by the patch builder,
the jsui components (mirrored in device/jsui/*.js) and the preview renderer.

Colours are RGBA 0..1 (Max's format). Every token has one job; see docs/UI.md."""

def hexrgba(h, a=1.0):
    h = h.lstrip("#")
    return [round(int(h[i:i + 2], 16) / 255.0, 4) for i in (0, 2, 4)] + [a]


# ---- surfaces (dark charcoal -> graphite) ----
CHASSIS = hexrgba("#141312")     # device background
PLATE = hexrgba("#211f1d")       # section plates
HEADER = hexrgba("#2b2825")      # header bands
INSET = hexrgba("#171615")       # wells: menus, meters, diagrams
OFF = hexrgba("#34312d")         # button / segment, off
BEVEL = hexrgba("#4f4841")       # metallic section border
BEVEL_HI = hexrgba("#7c7266")    # hairline under headers, separators

# ---- light ----
AMBER = hexrgba("#f2a03a")       # the one accent: ON, selected, value arcs, active path
AMBER_DIM = hexrgba("#6b4a24")   # ON but unavailable / inactive
ARC_OFF = hexrgba("#4a443d")     # value arc when a control is unavailable
METER_LO = hexrgba("#c9a15a")
METER_HI = hexrgba("#e8682a")
METER_OVER = hexrgba("#d8452a")

# ---- ink ----
TEXT = hexrgba("#ece4d4")        # titles, values
LABEL = hexrgba("#a39a8c")       # labels, captions
TEXT_DIM = hexrgba("#5e5850")    # unavailable labels
TEXT_ON = hexrgba("#1a1410")     # text on an amber surface

# ---- type (Max default font family stays Arial Bold / Arial) ----
F_TITLE = 10.5
F_LABEL = 8.5
F_SMALL = 7.5
F_TINY = 7.0

# ---- geometry ----
H = 169                 # Live device height
TOP, BOT = 4, 165       # section plates span y 4..165
HDR_H = 18              # header band height (y 4..22)
BTN_H = 15
ON_W, ON_H = 36, 14
DIAL_PRIMARY = (104, 102)   # frequency controls
DIAL_SECONDARY = (56, 50)
DIAL_PAGE = (48, 46)        # dynamics edit pages


def luminance(c):
    def ch(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

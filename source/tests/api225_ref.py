"""Static model of the API 225L knee / control-voltage stage (VCA board, traced schematic, 'UNTESTED').

IC3a (TL082) is a non-inverting stage: + input = CV from the ratio network (CON2.05), - input node J.
  R2 9k09 from output O to J; R1 100k + CR6 (1N4448, anode at O) also from O to J.
  From J to ground: R41 6k19 to node B, then a 1N4148 chain to ground:
    NEW:  CR3 shorted by S2a  -> SOFT: CR4 + CR5 (2 diodes), HARD: S3 shorts B to D -> CR5 only (1 diode)
    OLD:  S2a puts R40 2k74 in parallel with R41 and leaves CR3 in -> SOFT: 3 diodes, HARD: 1 diode
O -> CR9 (1N4448) -> R61 121k || R44 36k5 (IC3b virtual ground) -> IC3b gain -49k9/36k5 -> 33k2/301R divider
  -> 2180 Ec (6.1 mV/dB, THAT 2180 datasheet).
Gain reduction GR(dB) = Vcr9_out * (49.9/36.5) * 301/(33200+301) / 0.0061.

Independent reference for the engine's f_k225 (bisection here, Newton in the engine). static_out() gives the VCA's
static output level for a steady input, in both TYPEs, with the model's calibration (c from the ratio, X0 so the
asymptote passes through the threshold; HARD / MED / SOFT = 1 / 2 / 3 diodes).
"""
import numpy as np

VT = 0.025852 * 1.0          # 300 K
IS, N = 2.52e-9, 1.752       # 1N4148 SPICE model (also used for 1N4448)
R1, R2, R41, R40 = 100e3, 9.09e3, 6.19e3, 2.74e3
RL9 = 1 / (1 / 121e3 + 1 / 36.5e3)
K_EC = (49.9 / 36.5) * 301 / (33200 + 301) / 0.0061   # dB of GR per volt after CR9


def vdiode(i, nd=1):
    return nd * N * VT * np.log1p(np.maximum(i, 0) / IS)


def solve_i(v, r, nd):
    """current through r + nd diodes in series with v across them (v >= 0)."""
    if v <= 0:
        return 0.0
    lo, hi = 0.0, v / r
    for _ in range(80):
        m = 0.5 * (lo + hi)
        if m * r + vdiode(m, nd) > v:
            hi = m
        else:
            lo = m
    return 0.5 * (lo + hi)


def stage(x, nd, rz):
    """IC3a output for CV x (volts)."""
    iz = solve_i(x, rz, nd)                 # current from J (= x) to ground
    # find d = O - x with d/R2 + i6(d) = iz
    lo, hi = 0.0, iz * R2 + 1e-12
    for _ in range(80):
        d = 0.5 * (lo + hi)
        if d / R2 + solve_i(d, R1, 1) > iz:
            hi = d
        else:
            lo = d
    return x + 0.5 * (lo + hi)


def gr_db(x, cfg):
    nd, rz = cfg
    o = stage(x, nd, rz)
    i9 = solve_i(o, RL9, 1)
    return K_EC * i9 * RL9


CFG = {("NEW", "HARD"): (1, R41), ("NEW", "SOFT"): (2, R41),
       ("OLD", "HARD"): (1, R41 * R40 / (R41 + R40)), ("OLD", "SOFT"): (3, R41 * R40 / (R41 + R40))}

R12 = R1 * R2 / (R1 + R2)
RZ = {"NEW": R41, "OLD": R41 * R40 / (R41 + R40)}
RATIOS = [1.5, 2, 3, 4, 6, 10, float("inf")]


def slope(t):
    return K_EC * (1 + R12 / RZ[t])


def x0(t, nd):
    xb = 10.0
    return xb - gr_db(xb, (nd, RZ[t])) / slope(t)


def gain_change(over_db, ratio_i, knee, typ):
    """dB (<= 0) the knee stage applies for a detector level over_db above threshold."""
    t = "OLD" if typ else "NEW"
    c = (1 - 1 / RATIOS[ratio_i]) / slope("NEW")
    return -gr_db(c * over_db + x0(t, knee + 1), (knee + 1, RZ[t]))


def static_out(lin, thr, ratio_i, knee, typ):
    """steady output level (dB) for input level lin (dB), no make-up."""
    if not typ:
        return lin + gain_change(lin - thr, ratio_i, knee, typ)
    lo, hi = lin - 80, lin
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if m - lin - gain_change(m - thr, ratio_i, knee, typ) > 0:
            hi = m
        else:
            lo = m
    return 0.5 * (lo + hi)


if __name__ == "__main__":
    for k, cfg in CFG.items():
        xs = np.linspace(0, 6, 601)
        g = np.array([gr_db(x, cfg) for x in xs])
        sl = np.gradient(g, xs)
        print(k, "GR at x=1,2,4,6 V:", [round(gr_db(x, cfg), 2) for x in (1, 2, 4, 6)], " slope dB/V at 6 V:", round(sl[-1], 3),
              " slope 10%/90% points (V):", round(xs[np.argmax(sl > 0.1 * sl[-1])], 2), round(xs[np.argmax(sl > 0.9 * sl[-1])], 2))

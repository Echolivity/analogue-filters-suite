# Static model of the LA-2A attenuator from schematic C-10953 rev C (see docs/independent-review/LA2A_MANUAL_CHECK.md).
import numpy as np
from scipy.optimize import brentq
R6, R1, R2 = 68e3, 100e3, 100e3
def node(vin, rcell, R7):
    rp = 1/(1/rcell + 1/R1)
    zx = 1/(1/R2 + 1/(R7 + rp))
    vx = vin * zx/(R6+zx); vy = vx * rp/(R7+rp); return vx, vy
def solve(vin, R7, gam, k):
    # rcell = R0 * (k*vx)^-gam, with dark limit 10 Mohm; find self-consistent rcell (log domain)
    f = lambda lr: lr - np.log(1/(1e-7 + (k*node(vin, np.exp(lr), R7)[0])**gam / 1e5))
    lr = brentq(f, np.log(1e-4), np.log(1e7)); return node(vin, np.exp(lr), R7)[1], np.exp(lr)
lv = np.arange(-50, 31, 1.0)
for gam in (1.0, 1.4, 1.6, 2.0):
    for R7 in (0, 1000, 1800, 2700):
        out = np.array([20*np.log10(solve(10**(L/20), R7, gam, 30)[0]) for L in lv])
        gr = (lv - out) - (lv[0]-out[0]); brk = lv[np.argmax(gr > 1)]
        def slope(a, b):
            i, j = np.searchsorted(lv, a), np.searchsorted(lv, b); return (lv[j]-lv[i])/(out[j]-out[i])
        rise = lambda a: out[np.searchsorted(lv, a+20)]-out[np.searchsorted(lv, a)]
        print(f"gam {gam} R7 {R7:5d}: brk {brk:+.0f}  ratio(brk+5..+10) {slope(brk+5,brk+10):6.2f}  out rise brk+10..+30 {rise(brk+10):+5.2f} dB  GR@brk+10 {gr[np.searchsorted(lv,brk+10)]:4.1f}  GR@brk+30 {gr[np.searchsorted(lv,brk+30)]:4.1f}")
print("---- local ratio vs GR (deep)")
lv = np.arange(-40, 41, 1.0)
for gam in (2.0, 2.5):
    for R7 in (0, 1800):
        out = np.array([20*np.log10(solve(10**(L/20), R7, gam, 30)[0]) for L in lv]); gr = (lv-out)-(lv[0]-out[0])
        row = []
        for g in (5, 10, 15, 20, 25, 30, 35, 40):
            i = np.argmax(gr >= g)
            if gr[i] < g: break
            row.append(f"{g}:{(lv[i+2]-lv[i-2])/max(out[i+2]-out[i-2],1e-9):5.1f}")
        print(f"gam {gam} R7 {R7}: ", " ".join(row))

"""OPTO vs the Teletronix LA-2A operating manual (Library of Congress scan, supplied by the user).

Measures the current OPTO (v1.6 engine, unchanged OPTO code) against each figure the
manual states, and prints a conformance table. Diagnostics only: nothing is changed.
Run from source/:  python3 tests/review/la2a_manual.py
"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import dsp

SR = 48000


def tone(f, dbfs, sec):
    t = np.arange(int(sec * SR)) / SR
    return 10 ** (dbfs / 20) * np.sqrt(2) * np.sin(2 * np.pi * f * t)


def rms_db(y):
    return 20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-20)


def opto(**kw):
    p = dict(o_on=1, o_pr=60, o_mode=0, o_emph=0, o_src=0, o_hpf=20, o_mix=100)
    p.update(kw)
    return dsp.dyn(**p)


def static(f=1000, levels=np.arange(-50, 1, 2.0), **kw):
    out = []
    for L in levels:
        x = tone(f, L, 3.0)
        y = dsp.run(x, opto(**kw), SR)[:, 0]
        out.append(rms_db(y[-SR // 2:]))
    return levels, np.array(out)


def curve_stats(lv, out):
    gr = lv - out - (lv[0] - out[0])            # GR relative to the lowest level (no reduction)
    sl = np.diff(lv) / np.maximum(np.diff(out), 1e-6)  # local ratio dIn/dOut
    i_brk = int(np.argmax(gr > 1.0)) if (gr > 1.0).any() else None
    comp = [(lv[i], sl[i]) for i in range(len(sl)) if 3 < gr[i] < 25]
    return {"breakaway_in_db": None if i_brk is None else float(lv[i_brk]),
            "max_local_ratio": float(np.max(sl)), "ratio_at_gr3_25": [round(float(r), 2) for _, r in comp],
            "out_rise_over_top_20db": float(out[-1] - out[np.searchsorted(lv, lv[-1] - 20)]),
            "max_gr": float(gr.max())}


R = {}
# 1. static curves (manual p.3, addendum)
for mode, name in ((1, "LIMIT"), (0, "COMP")):
    for src, sn in ((0, "INT (feedback)"), (1, "CHAIN (feed-forward when OPTO is first)")):
        lv, out = static(o_mode=mode, o_src=src, o_pr=80)
        R[f"static {name} {sn} PR80"] = curve_stats(lv, out)

# 2. R37 frequency-response control (manual p.7): ~10 dB more reduction at 15 kHz than below 1 kHz
def gr_at(f, L, **kw):
    y = dsp.run(tone(f, L, 3.0), opto(**kw), SR)[:, 0]
    ref = dsp.run(tone(f, L, 3.0), opto(o_on=0), SR)[:, 0]
    return rms_db(ref[-SR // 2:]) - rms_db(y[-SR // 2:])
r37 = {}
for mode in (1, 0):
    for L in (-30, -20, -10):
        g15 = gr_at(15000, L, o_mode=mode, o_emph=100, o_pr=60)
        g05 = gr_at(500, L, o_mode=mode, o_emph=100, o_pr=60)
        f15 = gr_at(15000, L, o_mode=mode, o_emph=0, o_pr=60)
        f05 = gr_at(500, L, o_mode=mode, o_emph=0, o_pr=60)
        r37[f"{'LIMIT' if mode else 'COMP'} {L} dBFS"] = {"emph100: GR15k - GR500": round(g15 - g05, 2),
                                                         "flat: GR15k - GR500": round(f15 - f05, 2),
                                                         "GR500 (emph100)": round(g05, 1)}
R["R37"] = r37

# 3. distortion: limiter >= 30 dB reduction with < 0.5 % THD (manual p.7)
def thd(f, L, **kw):
    y = dsp.run(tone(f, L, 4.0), opto(**kw), SR)[-SR:, 0]
    w = np.hanning(len(y)); Y = np.abs(np.fft.rfft(y * w)); fr = np.fft.rfftfreq(len(y), 1 / SR)
    pk = lambda h: Y[np.argmin(np.abs(fr - h * f)) - 3: np.argmin(np.abs(fr - h * f)) + 4].max()
    fund = pk(1); harm = np.sqrt(sum(pk(h) ** 2 for h in range(2, 10) if h * f < SR / 2 - 200))
    return 100 * harm / fund
th = {}
for f in (100, 1000, 5000):
    for L in (-10, 0):
        g = gr_at(f, L, o_mode=1, o_pr=100)
        th[f"{f} Hz, {L} dBFS"] = {"GR_db": round(g, 1), "THD_pct": round(thd(f, L, o_mode=1, o_pr=100), 3)}
R["THD LIMIT PR100"] = th

json.dump(R, open(os.path.join(HERE, "..", "..", "build", "la2a_manual.json"), "w"), indent=1)
print(json.dumps(R, indent=1))

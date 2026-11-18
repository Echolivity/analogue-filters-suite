"""Shared helpers for the DSP fidelity audit (diagnostics only).

Every measurement runs the exact shipped gen~ engine (build/dubfilter.genexpr,
transpiled to C by tools/genexpr2c.py) through tests/harness.c, in 32-bit float
I/O, at the sample rate stated per measurement. Nothing here changes the DSP."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from dsp import run, base, tf  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "docs", "dsp-audit")
DATA = os.path.join(OUT, "data")
PLOTS = os.path.join(OUT, "plots")
os.makedirs(DATA, exist_ok=True)
os.makedirs(PLOTS, exist_ok=True)

LP_MODELS = ["Sherman", "K35/MS-20", "Ladder", "Steiner-Parker", "SEM", "TB-303 diode"]
HP_MODELS = ["Sherman", "K35/MS-20", "Ladder ALT", "Steiner-Parker", "SEM"]

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 9, "legend.fontsize": 7.5, "legend.frameon": False})
COL = ["#2a6fdb", "#e07b39", "#2f9e6e", "#c0392b", "#8e5ea2", "#7f8c8d", "#b8860b"]


def db(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-15))


def stage(st, m, **kw):
    d = {f"{st}_on": 1, f"{st}_model": m}
    glob = {"ovs_sel", "softclip", "out_db", "order_sel"}
    d.update({(k if k in glob else f"{st}_{k}"): v for k, v in kw.items()})
    return base(**d)


def tone(f, dur, sr, amp=1.0, pre=0.0):
    n = int((dur + pre) * sr)
    t = np.arange(n) / sr
    return amp * np.sin(2 * np.pi * f * t)


def bh4(n):
    """4-term Blackman-Harris window (sidelobes -92 dB)."""
    k = np.arange(n) / (n - 1) * 2 * np.pi
    return 0.35875 - 0.48829 * np.cos(k) + 0.14128 * np.cos(2 * k) - 0.01168 * np.cos(3 * k)


def spectrum(y, sr):
    w = bh4(len(y))
    Y = np.fft.rfft(y * w) / (np.sum(w) / 2)
    return np.fft.rfftfreq(len(y), 1 / sr), np.abs(Y)


def harmonics(y, f0, sr, nh=10, bw=5):
    """Levels (linear, peak) of harmonics 1..nh of f0, plus residual power that is not
    at any harmonic (aliasing / noise), from a Blackman-windowed FFT. y should hold
    an integer number of cycles or be long enough for leakage < -120 dB."""
    f, A = spectrum(y, sr)
    df = f[1]
    lv, used = [], np.zeros(len(f), bool)
    for h in range(1, nh + 1):
        fh = f0 * h
        if fh >= sr / 2:
            lv.append(0.0); continue
        k = int(round(fh / df))
        sl = slice(max(k - bw, 0), k + bw + 1)
        lv.append(float(np.sqrt(np.sum(A[sl] ** 2) / 2.0)))   # 4-term Blackman-Harris ENBW 2.0 bins
        used[sl] = True
    used[: int(20 / df) + 1] = True                              # ignore DC / sub-20 Hz
    # mark every harmonic location even above nh (still harmonic, not alias)
    for h in range(nh + 1, int((sr / 2) / f0) + 1):
        k = int(round(f0 * h / df)); used[max(k - bw, 0):k + bw + 1] = True
    resid = float(np.sqrt(np.sum(A[~used] ** 2) / 2.0))
    return np.array(lv), resid


def thd(y, f0, sr, nh=10):
    lv, resid = harmonics(y, f0, sr, nh)
    return float(np.sqrt(np.sum(lv[1:] ** 2)) / max(lv[0], 1e-15)), lv, resid


def save(name, obj):
    with open(os.path.join(DATA, name + ".json"), "w") as f:
        json.dump(obj, f, indent=1, default=float)


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, name + ".png"))
    plt.close(fig)

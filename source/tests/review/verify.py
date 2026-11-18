#!/usr/bin/env python3
"""Independent verification experiments (diagnostics only; production DSP untouched).
  OS  : oversampling-factor study 1x/2x/4x/8x (engine run at N*48 kHz, ideal decimation)
  BLT : is the reported HF peak shift an engine error or the bilinear transform itself?
  OPA : OPTO attack under several definitions, step sizes and history
  OPR : OPTO local slope vs level and frequency
  VCA : replica of the VCA detector to confirm the cause of the attack floor
  TUB : TUBE aliasing at the default Tone setting and at realistic input frequencies
  NSE : self-start from silence
Writes docs/independent-review/data/verify.json and plots."""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, os.path.join(HERE, "..", "audit"))
from dsp import run, base
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT = os.path.join(HERE, "..", "..", "..", "docs", "independent-review")
R = {}


def db(x):
    return float(20 * np.log10(max(abs(float(x)), 1e-300)))


def bh4(n):
    k = np.arange(n) / (n - 1) * 2 * np.pi
    return 0.35875 - 0.48829 * np.cos(k) + 0.14128 * np.cos(2 * k) - 0.01168 * np.cos(3 * k)


def alias_metric(y, sr, f0, fmax=24000.0, bw=5):
    """y: exactly 1 s at rate sr. Inharmonic energy below fmax relative to the fundamental
    (= what remains after an ideal decimator to 48 kHz)."""
    w = bh4(len(y)); A = np.abs(np.fft.rfft(y * w)) / (np.sum(w) / 2)
    f = np.fft.rfftfreq(len(y), 1 / sr)
    band = (f > 20) & (f < fmax)
    harm = np.zeros(len(f), bool)
    for h in range(1, int(fmax / f0) + 2):
        k = int(round(h * f0)); harm[max(k - bw, 0):k + bw + 1] = True
    k1 = int(round(f0))
    fund = np.sqrt(np.sum(A[k1 - bw:k1 + bw + 1] ** 2))
    res = np.sqrt(np.sum(A[band & ~harm] ** 2))
    return db(res / fund)


# ================================================================== OS: oversampling factor study
LP = ["Sherman", "K35/MS-20", "Ladder", "Steiner-Parker", "SEM", "TB-303"]
COND = {"C1 (audit F5): 5003 Hz -6 dBFS, fc 16k, res 50, drive 60": dict(f0=5003.0, amp=0.5, cut=16000, res=50, drive=60),
        "C2 (harsh): 7001 Hz -3 dBFS, fc 12k, res 90, drive 100": dict(f0=7001.0, amp=0.708, cut=12000, res=90, drive=100),
        "C3 (typical): 1009 Hz -6 dBFS, fc 3k, res 70, drive 50": dict(f0=1009.0, amp=0.5, cut=3000, res=70, drive=50)}
rows = []
for cname, c in COND.items():
    for m in range(6):
        for N in (1, 2, 4, 8):
            sr = 48000 * N
            n = int(1.5 * sr); t = np.arange(n) / sr
            x = c["amp"] * np.sin(2 * np.pi * c["f0"] * t)
            p = base(l_on=1, l_model=m, l_cut=c["cut"], l_res=c["res"], l_drive=c["drive"], l_slope=1 if m in (0, 2, 5) else 0, l_comp=100)
            y = run(x, p, sr)[int(0.5 * sr):int(1.5 * sr), 0]
            rows.append(dict(condition=cname, model=LP[m], factor=N, method="engine at N x 48 kHz, ideal decimation",
                             alias_dbc=round(alias_metric(y, sr, c["f0"]), 1), peak_dbfs=round(db(np.max(np.abs(y))), 1)))
        # production 2x (half-band IIR) at 48 kHz for comparison with the ideal 2x
        sr = 48000; n = int(1.5 * sr); t = np.arange(n) / sr
        x = c["amp"] * np.sin(2 * np.pi * c["f0"] * t)
        p = base(l_on=1, l_model=m, l_cut=c["cut"], l_res=c["res"], l_drive=c["drive"], l_slope=1 if m in (0, 2, 5) else 0, l_comp=100, ovs_sel=1)
        y = run(x, p, sr)[int(0.5 * sr):int(1.5 * sr), 0]
        rows.append(dict(condition=cname, model=LP[m], factor=2, method="production 2x (half-band IIR)",
                         alias_dbc=round(alias_metric(y, sr, c["f0"]), 1), peak_dbfs=round(db(np.max(np.abs(y))), 1)))
R["OS_filters"] = rows
# tube: internal 2x always on, so engine at N x 48k = 2N effective
rows = []
for drv, tone_hz, f0 in ((60, 12000, 5003.0), (100, 12000, 5003.0), (100, 20000, 5003.0), (100, 12000, 1009.0), (60, 12000, 1009.0)):
    for N in (1, 2, 4):
        sr = 48000 * N; n = int(1.5 * sr); t = np.arange(n) / sr
        x = 0.5 * np.sin(2 * np.pi * f0 * t)
        y = run(x, base(t_on=1, t_drive=drv, t_bias=20, t_auto=1, t_tone=tone_hz), sr)[int(0.5 * sr):int(1.5 * sr), 0]
        rows.append(dict(f0=f0, drive=drv, tone_hz=tone_hz, effective_factor=2 * N, alias_dbc=round(alias_metric(y, sr, f0), 1)))
R["OS_tube"] = rows

# ================================================================== BLT: bilinear-transform prediction vs engine
def ladder(s, k):
    return 1 / ((1 + s) ** 4 + k)
rows = []
f = np.linspace(500, 22000, 43001)
for fs in (44100, 96000):
    for fc in (5000, 12000):
        k = 4.3 * 0.6 ** 1.3
        Ha = np.abs(ladder(1j * f / fc, k))
        sd = 1j * np.tan(np.pi * f / fs) / np.tan(np.pi * fc / fs)
        Hd = np.abs(ladder(sd, k)) * (f < fs / 2)
        fa, fd = f[np.argmax(Ha)], f[np.argmax(Hd)]
        rows.append(dict(model="Ladder LP res 60 %", fs=fs, fc=fc, analogue_peak_hz=round(float(fa), 1),
                         blt_predicted_peak_hz=round(float(fd), 1), blt_shift_cents=round(1200 * math.log2(fd / fa), 1)))
R["BLT_ladder_peak_prediction"] = rows
R["BLT_note"] = "compare with filters.F1 peak_freq_err_cents (engine vs analogue): Ladder 44.1 kHz fc 12 kHz = +118.8, fc 5 kHz = +21.9"

# ================================================================== OPA: OPTO attack, several definitions
rows = []
SR = 48000
for pr in (40, 60, 80):
    for pre in ("rest", "after 5 s at -12 dBFS"):
        n = int(8 * SR); t = np.arange(n) / SR
        x = np.sin(2 * np.pi * 1000 * t)
        env = np.full(n, 10 ** (-40 / 20))
        if pre != "rest":
            env[int(0.5 * SR):int(5.5 * SR)] = 10 ** (-12 / 20)
            env[int(5.5 * SR):int(6.0 * SR)] = 10 ** (-40 / 20)
            t0 = int(6.0 * SR)
        else:
            t0 = int(6.0 * SR)
        env[t0:] = 10 ** (-3 / 20)
        _, M = run(x * env, base(o_on=1, o_pr=pr, o_mode=0), SR, meters=True)
        g = M[:, 4] * 30.0
        g0 = g[t0 - 1]; fin = g[t0 + int(1.5 * SR)]
        seg = g[t0:t0 + int(1.5 * SR)] - g0; span = fin - g0
        def tt(fr):
            return round(float(np.argmax(seg >= fr * span) / SR * 1000), 2)
        rows.append(dict(peak_reduction=pr, history=pre, gr_start_db=round(float(g0), 2), gr_final_db=round(float(fin), 2),
                         t10_ms=tt(0.1), t63_ms=tt(0.632), t90_ms=tt(0.9), t10_90_ms=round(tt(0.9) - tt(0.1), 2)))
R["OPA_opto_attack"] = rows

# ================================================================== OPR: OPTO local slope vs level and frequency
rows = []
for fr in (100.0, 1000.0, 5000.0):
    lv = np.arange(-30, 4, 3.0); out = []
    for L in lv:
        n = int(6 * SR); t = np.arange(n) / SR
        y = run(10 ** (L / 20) * np.sin(2 * np.pi * fr * t), base(o_on=1, o_pr=70, o_mode=0), SR)[int(5 * SR):, 0]
        out.append(db(np.sqrt(2 * np.mean(y ** 2))))
    out = np.array(out); sl = np.diff(out) / np.diff(lv)
    rows.append(dict(freq_hz=fr, levels=[float(v) for v in lv[1:]], local_ratio=[round(float(1 / max(s, 1e-6)), 2) for s in sl]))
R["OPR_opto_local_ratio_PR70"] = rows

# ================================================================== VCA: detector replica (dyn.py:179, 358-366)
def vca_rep(attack_ms, rms_ms=3.0, fs=48000, thr=-20.0, slope=-1.0):
    n = int(0.3 * fs); t = np.arange(n) / fs
    x = np.sin(2 * np.pi * 1000 * t)
    a_rms = 1 - math.exp(-1 / (rms_ms * 1e-3 * fs)); a_at = 1 - math.exp(-1 / (attack_ms * 1e-3 * fs))
    ms = (10 ** (-30 / 20)) ** 2 / 2; gr = 0.0; out = []
    for v in x:
        ms += (v * v - ms) * a_rms
        lvl = 10 * math.log10(ms + 1e-20) + 3.0103
        gc = slope * (lvl - thr) if lvl > thr else 0.0
        gr += (gc - gr) * (a_at if gc < gr else 0.0)
        out.append(-gr)
    out = np.array(out); fin = out[-1]
    return round(float(np.argmax(out >= 0.632 * fin) / fs * 1000), 3)
R["VCA_replica_t63_ms"] = {f"attack {a} ms, rms 3 ms": vca_rep(a) for a in (0.03, 0.3, 1.0, 3.0)}
R["VCA_replica_t63_ms"].update({f"attack 0.03 ms, rms {r} ms (diagnostic)": vca_rep(0.03, rms_ms=r) for r in (1.0, 0.3, 0.1)})
R["VCA_note"] = "engine (audit C2a): 0.03 ms -> 0.708 ms, 0.3 -> 1.021, 1 -> 1.979, 3 -> 4.25"

# ================================================================== NSE: self-start from silence (no excitation at all)
y = run(np.zeros(2 * SR), base(l_on=1, l_model=2, l_cut=1000, l_res=100, l_slope=1, l_comp=0), SR)[:, 0]
R["NSE_selfstart_ladder_res100_no_input_peak"] = float(np.max(np.abs(y)))

json.dump(R, open(os.path.join(OUT, "data", "verify.json"), "w"), indent=1)

# plot: oversampling study
fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), sharey=True)
for ax, cname in zip(axes, COND):
    for i, m in enumerate(LP):
        r = [x for x in R["OS_filters"] if x["condition"] == cname and x["model"] == m and x["method"].startswith("engine")]
        ax.plot([x["factor"] for x in r], [x["alias_dbc"] for x in r], "o-", label=m)
    ax.set_xscale("log", base=2); ax.set_xticks([1, 2, 4, 8]); ax.set_xticklabels(["1x", "2x", "4x", "8x"])
    ax.axhline(-80, color="k", ls=":", lw=0.8); ax.set_title(cname, fontsize=8); ax.set_xlabel("oversampling factor (ideal decimation)")
axes[0].set_ylabel("inharmonic (aliased) energy, dBc"); axes[0].legend(fontsize=7)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "plots", "os_factor_study.png"), dpi=110)
print(json.dumps({k: v for k, v in R.items() if not k.startswith("OS")}, indent=1)[:6000])

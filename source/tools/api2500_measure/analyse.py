"""Analyse API 2500 renders made from the measurement pack (see RENDER_INSTRUCTIONS.txt).

Usage: python3 analyse.py <pack_dir> <renders_dir> [out_dir]
  pack_dir     the generated pack (source WAVs + schedule.json)
  renders_dir  the returned R01..R18 WAVs (any subset; missing renders are skipped)
  out_dir      where report.md, results.json and plots go (default: <renders_dir>/analysis)

Every render is aligned to its source by the sync click at 0.5 s, so plug-in latency or export offsets don't matter.
Gain reduction (GR) is always output level / input level relative to R01 (calibration, no compression), so a
fixed output offset of the unit or plug-in cancels."""
import json, os, sys
import numpy as np
import soundfile as sf
from scipy.optimize import least_squares

SR = 48000
START = int(1.5 * SR)      # test signal starts here in every source file
CLICK = int(0.5 * SR)

SRC = {"R01": "00_calibration_1k_-20dBFS.wav", "R02": "01_static_curve_1k_steps.wav", "R03": "01_static_curve_1k_steps.wav",
       "R04": "01_static_curve_1k_steps.wav", "R05": "01_static_curve_1k_steps.wav", "R06": "02_thrust_sweep_-10dBFS.wav",
       "R07": "02_thrust_sweep_-10dBFS.wav", "R08": "02_thrust_sweep_-10dBFS.wav", "R09": "03_attack_bursts_1k.wav",
       "R10": "03_attack_bursts_1k.wav", "R11": "03_attack_bursts_1k.wav", "R12": "04_release_bursts_1k.wav",
       "R13": "04_release_bursts_1k.wav", "R14": "05_link_shape_L-sweep_R-1k.wav", "R15": "05_link_shape_L-sweep_R-1k.wav",
       "R16": "05_link_shape_L-sweep_R-1k.wav", "R17": "05_link_shape_L-sweep_R-1k.wav", "R18": "05_link_shape_L-sweep_R-1k.wav",
       "R19": "06_detector_sine_vs_pulses.wav", "R20": "06_detector_sine_vs_pulses.wav"}
KNEES = {"R02": "HARD", "R03": "MED", "R04": "SOFT", "R05": "HARD (OLD / feedback)"}
THRUST = {"R06": "NORM", "R07": "MED", "R08": "LOUD"}
ATTACK = {"R09": 0.03, "R10": 1.0, "R11": 30.0}
RELEASE = {"R12": "500 ms fixed", "R13": "VAR at 500 ms"}
LINK = {"R14": "IND", "R15": "HP", "R16": "LP", "R17": "BP", "R18": "FLAT"}
DET = {"R19": "NEW", "R20": "OLD"}


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-12))


def rms(x):
    return float(np.sqrt(np.mean(np.square(x))))


def load(path):
    y, sr = sf.read(path, always_2d=True)
    if sr != SR:
        raise SystemExit(f"{os.path.basename(path)}: {sr} Hz; the pack is 48 kHz, please render at 48 kHz")
    return y


def find_renders(d):
    out = {}
    for f in sorted(os.listdir(d)):
        k = f[:3].upper()
        if f.lower().endswith(".wav") and k in SRC:
            out[k] = os.path.join(d, f)
    return out


def align(y, x):
    """Shift render y so its sync click sits where the source's does; trim/pad to the source length."""
    i = int(np.argmax(np.abs(y[: START + SR // 2, 0])))
    off = i - CLICK
    if abs(off) > SR // 2:
        raise ValueError(f"sync click not found near 0.5 s (found at {i / SR:.3f} s)")
    y = y[off:] if off >= 0 else np.r_[np.zeros((-off, y.shape[1])), y]
    if len(y) < len(x):
        y = np.r_[y, np.zeros((len(x) - len(y), y.shape[1]))]
    return y[: len(x)], off


def env_gain(y, x, ch=0, win=48):
    """Short-window gain in dB (window = one period of 1 kHz), output over input."""
    k = np.ones(win) / win
    eo = np.sqrt(np.convolve(y[:, ch] ** 2, k, "same"))
    ei = np.sqrt(np.convolve(x[:, ch] ** 2, k, "same"))
    return db(eo) - db(ei)


def knee_model(L, T, R, W):
    """Quadratic soft knee (W = 0: hard). L = input level, returns GR (positive dB)."""
    over = L - T
    gr = np.where(over <= -W / 2, 0.0, np.where(over >= W / 2, over * (1 - 1 / R), (1 - 1 / R) * (over + W / 2) ** 2 / (2 * W + 1e-9)))
    return gr


def analyse(pack, rdir, odir):
    os.makedirs(odir, exist_ok=True)
    sched = json.load(open(os.path.join(pack, "schedule.json")))
    R = find_renders(rdir)
    res, rep, warn = {}, ["# API 2500 measurement analysis", ""], []
    src = {k: load(os.path.join(pack, v)) for k, v in SRC.items() if k in R}
    Y = {}
    for k, p in R.items():
        y, off = align(load(p), src[k])
        Y[k] = y
        if np.abs(y).max() > 0.999:
            warn.append(f"{k} clips (peak {db(np.abs(y).max()):.1f} dBFS)")
    rep.append("Renders found: " + ", ".join(sorted(R)) + ".")
    if warn:
        rep += ["", "**Warnings:** " + "; ".join(warn)]

    # ---- calibration: path gain with no compression
    g0 = 0.0
    if "R01" in Y:
        x, y = src["R01"], Y["R01"]
        a, b = START + SR, START + 4 * SR
        g0 = db(rms(y[a:b, 0])) - db(rms(x[a:b, 0]))
        res["calibration_gain_db"] = round(float(g0), 3)
        rep += ["", "## Calibration", f"Path gain with no compression: {g0:+.2f} dB (subtracted from every GR below)."]
    else:
        rep += ["", "## Calibration", "R01 missing: GR is measured from the render's own level, assuming unity gain."]

    # ---- static curves
    steps = sched["01_static_curve_1k_steps.wav"]["segments"]
    knees = {}
    for k in [k for k in KNEES if k in Y]:
        x, y = src[k], Y[k]
        Lin, GR = [], []
        t = START
        for lev, dur in steps:
            n = int(dur * SR)
            a, b = t + int(0.3 * SR), t + n - int(0.02 * SR)
            Lin.append(lev)
            GR.append(-(db(rms(y[a:b, 0])) - db(rms(x[a:b, 0])) - g0))
            t += n
        Lin, GR = np.array(Lin, float), np.array(GR)

        def r(p):
            return knee_model(Lin, p[0], p[1], abs(p[2])) - GR
        fit = least_squares(r, [-22, 4, 3])
        T, Rt, W = fit.x[0], fit.x[1], abs(fit.x[2])
        # asymptote: straight line through the top of the curve (inputs >= 12 dB above the fitted threshold);
        # ratio from its slope, threshold where it meets unity gain. Robust to diode-shaped knees.
        top = Lin >= T + 12
        if top.sum() >= 4:
            m, b = np.polyfit(Lin[top], GR[top], 1)
            a_ratio = 1 / (1 - m) if m < 0.999 else float("inf")
            a_thr = -b / m if m > 1e-6 else float("nan")
        else:
            a_ratio, a_thr = float("nan"), float("nan")
        knees[k] = dict(setting=KNEES[k], asymptote_threshold_dbfs=round(float(a_thr), 2), asymptote_ratio=round(float(a_ratio), 2),
                        threshold_dbfs=round(T, 2), ratio=round(Rt, 2), knee_width_db=round(W, 2),
                        fit_rms_db=round(float(np.sqrt(np.mean(fit.fun ** 2))), 3), curve=[[float(a), round(float(b), 2)] for a, b in zip(Lin, GR)])
    if knees:
        res["static"] = knees
        rep += ["", "## Static curve and knees (1 kHz, threshold set to 0 dBu, 4:1)",
                "Asymptote: straight line through the curve 12 dB and more above threshold (ratio from its slope, threshold where it meets unity).",
                "Fit: quadratic soft knee of width W around the threshold (a diode knee is not quadratic; use W as a rough width).", "",
                "| Render | Knee | Asymptote threshold (dBFS) | Asymptote ratio | Fit threshold | Fit ratio | Knee width W (dB) | Fit error (dB rms) |",
                "|---|---|---|---|---|---|---|---|"]
        for k, v in knees.items():
            rep.append(f"| {k} | {v['setting']} | {v['asymptote_threshold_dbfs']} | {v['asymptote_ratio']} | {v['threshold_dbfs']} | {v['ratio']} | {v['knee_width_db']} | {v['fit_rms_db']} |")

    # ---- THRUST: GR per frequency at ratio 2 -> detector level change = 2 x GR change
    info = sched["02_thrust_sweep_-10dBFS.wav"]
    F, each = info["freqs"], info["each_s"]
    th = {}
    for k in [k for k in THRUST if k in Y]:
        x, y = src[k], Y[k]
        gr = []
        for i, f in enumerate(F):
            a = START + int((i * each + 0.6) * SR)
            b = START + int((i * each + each - 0.05) * SR)
            gr.append(-(db(rms(y[a:b, 0])) - db(rms(x[a:b, 0])) - g0))
        th[THRUST[k]] = np.array(gr)
    if th:
        res["thrust_freqs"] = F
        res["thrust_gr_db"] = {m: [round(float(v), 2) for v in g] for m, g in th.items()}
        rep += ["", "## THRUST (detector response, ratio 2:1)",
                "Detector-level change relative to NORM = 2 x (GR difference); 0 dB at 630 Hz."]
        if "NORM" in th:
            i630 = F.index(630)
            curves = {}
            for m in ("MED", "LOUD"):
                if m in th:
                    d = 2 * (th[m] - th["NORM"])
                    curves[m] = d - d[i630]
            if curves:
                res["thrust_curve_db"] = {m: [round(float(v), 2) for v in c] for m, c in curves.items()}
                rep += ["", "| Hz | " + " | ".join(curves) + " |", "|---|" + "---|" * len(curves)]
                for i, f in enumerate(F):
                    rep.append(f"| {f:g} | " + " | ".join(f"{c[i]:+.2f}" for c in curves.values()) + " |")
                over = th["NORM"] - 0
                if np.min(over) < 3:
                    warn.append("THRUST NORM GR under 3 dB somewhere: not far enough above threshold for this method")
        else:
            rep.append("R06 (NORM) missing: no reference.")

    # ---- attack: 10-90 % and 63 % rise of GR after each burst onset
    seg = sched["03_attack_bursts_1k.wav"]["segments"]
    on = []
    t = START
    for lev, dur in seg:
        if lev == -10:
            on.append(t)
        t += int(dur * SR)
    att = {}
    for k in [k for k in ATTACK if k in Y]:
        g = -(env_gain(Y[k], src[k]) - g0)
        rows = []
        for t0 in on:
            seg_g = g[t0: t0 + int(0.9 * SR)]
            fin = np.median(seg_g[int(0.6 * SR):])
            def cross(fr):
                idx = np.argmax(seg_g >= fr * fin)
                return idx / SR * 1000
            rows.append((cross(0.1), cross(0.63), cross(0.9), fin))
        r = np.median(np.array(rows), 0)
        att[k] = dict(setting_ms=ATTACK[k], t10_ms=round(r[0], 3), t63_ms=round(r[1], 3), t90_ms=round(r[2], 3), final_gr_db=round(r[3], 2))
    if att:
        res["attack"] = att
        rep += ["", "## Attack (40 dB step, 10:1; median of 5 bursts)", "",
                "| Render | Setting (ms) | 10 % (ms) | 63 % (ms) | 90 % (ms) | Settled GR (dB) |", "|---|---|---|---|---|---|"]
        for k, v in att.items():
            rep.append(f"| {k} | {v['setting_ms']} | {v['t10_ms']} | {v['t63_ms']} | {v['t90_ms']} | {v['final_gr_db']} |")
        rep.append("At 0.03 ms the attack is far faster than the RMS detector, so that row is the detector's own rise time.")

    # ---- release: GR recovery after bursts of different depth
    seg = sched["04_release_bursts_1k.wav"]["segments"]
    ends, t = [], START
    for lev, dur in seg:
        t += int(dur * SR)
        if lev != -50:
            ends.append((lev, t))
    rel = {}
    for k in [k for k in RELEASE if k in Y]:
        g = -(env_gain(Y[k], src[k]) - g0)
        rows = []
        for lev, t1 in ends:
            g0b = np.median(g[t1 - int(0.2 * SR): t1 - int(0.02 * SR)])
            tail = g[t1: t1 + int(5.8 * SR)]
            t37 = np.argmax(tail <= 0.37 * g0b) / SR * 1000
            t1db = np.argmax(tail <= 1.0) / SR * 1000 if g0b > 1 else 0.0
            rows.append(dict(burst_dbfs=lev, gr_before_db=round(float(g0b), 2), t37_ms=round(float(t37), 1), to_1db_ms=round(float(t1db), 1)))
        rel[k] = dict(setting=RELEASE[k], bursts=rows)
    if rel:
        res["release"] = rel
        rep += ["", "## Release (bursts 2 / 17 / 32 dB over threshold, 10:1)", "",
                "| Render | Setting | GR before (dB) | to 37 % (ms) | to 1 dB (ms) |", "|---|---|---|---|---|"]
        for k, v in rel.items():
            for b in v["bursts"]:
                rep.append(f"| {k} | {v['setting']} | {b['gr_before_db']} | {b['t37_ms']} | {b['to_1db_ms']} |")
        rep.append("Programme dependence shows as the 37 % time growing with GR in the VAR row but not the fixed row.")

    # ---- link: Right gain (1 kHz, below threshold) while Left sweeps
    info = sched["05_link_shape_L-sweep_R-1k.wav"]
    F, each = info["freqs"], info["each_s"]
    lk = {}
    for k in [k for k in LINK if k in Y]:
        x, y = src[k], Y[k]
        gl, gr = [], []
        for i, f in enumerate(F):
            a = START + int((i * each + 0.6) * SR)
            b = START + int((i * each + each - 0.05) * SR)
            gl.append(-(db(rms(y[a:b, 0])) - db(rms(x[a:b, 0])) - g0))
            gr.append(-(db(rms(y[a:b, 1])) - db(rms(x[a:b, 1])) - g0))
        lk[LINK[k]] = dict(left_gr_db=[round(float(v), 2) for v in gl], right_gr_db=[round(float(v), 2) for v in gr],
                           right_over_left_db=[round(float(db(max(r, 1e-3)) - db(max(l, 1e-3))), 2) for l, r in zip(gl, gr)])
    if lk:
        res["link"] = dict(freqs=F, **lk)
        rep += ["", "## Link and SHAPE (Left: tones at -10 dBFS; Right: 1 kHz below threshold)",
                "Right GR = gain reduction the link passes from Left to Right at each Left frequency.", "",
                "| Hz | " + " | ".join(f"{m} R GR (dB)" for m in lk) + " |", "|---|" + "---|" * len(lk)]
        for i, f in enumerate(F):
            rep.append(f"| {f:g} | " + " | ".join(f"{v['right_gr_db'][i]:.2f}" for v in lk.values()) + " |")

    # ---- detector type: GR on pulses vs GR on a sine at the same RMS
    info = sched.get("06_detector_sine_vs_pulses.wav")
    det = {}
    for k in [k for k in DET if k in Y and info]:
        x, y = src[k], Y[k]
        each = info["each_s"]
        grs = []
        for i, name in enumerate(info["segments"]):
            a = START + int((i * each + 1.0) * SR)
            b = START + int((i * each + each - 0.1) * SR)
            grs.append((name, -(db(rms(y[a:b, 0])) - db(rms(x[a:b, 0])) - g0)))
        gs = np.mean([g for n, g in grs if n == "sine"]); gp = np.mean([g for n, g in grs if n == "pulses"])
        det[k] = dict(type=DET[k], gr_sine_db=round(float(gs), 2), gr_pulses_db=round(float(gp), 2),
                      extra_gr_on_pulses_db=round(float(gp - gs), 2), crest_difference_db=round(info["pulse_crest_db"] - info["sine_crest_db"], 2))
    if det:
        res["detector"] = det
        rep += ["", "## Detector type (sine vs pulse train at the same RMS, 4:1, attack 30 us)",
                "RMS detector: under 1 dB extra GR on the pulses (this project's 3 ms RMS model: 0.8 dB). Ideal peak detector:",
                "(crest difference) x (1 - 1/R), about 10 dB at 4:1 for this pulse train.", "",
                "| Render | Type | GR sine (dB) | GR pulses (dB) | Extra GR on pulses (dB) | Crest difference (dB) |", "|---|---|---|---|---|---|"]
        for k, v in det.items():
            rep.append(f"| {k} | {v['type']} | {v['gr_sine_db']} | {v['gr_pulses_db']} | {v['extra_gr_on_pulses_db']} | {v['crest_difference_db']} |")

    json.dump(res, open(os.path.join(odir, "results.json"), "w"), indent=1)
    open(os.path.join(odir, "report.md"), "w").write("\n".join(rep) + "\n")
    plots(res, odir)
    return res


def plots(res, odir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    if "static" in res:
        plt.figure(figsize=(6, 4))
        for k, v in res["static"].items():
            c = np.array(v["curve"])
            plt.plot(c[:, 0], c[:, 0] - c[:, 1], label=f"{v['setting']} (W {v['knee_width_db']} dB)")
        plt.xlabel("Input (dBFS)"); plt.ylabel("Output (dBFS, makeup off)"); plt.grid(alpha=.3); plt.legend(fontsize=8)
        plt.tight_layout(); plt.savefig(os.path.join(odir, "static_curves.png"), dpi=120); plt.close()
    if "thrust_curve_db" in res:
        FREQS = res["thrust_freqs"]
        plt.figure(figsize=(6, 4))
        for m, c in res["thrust_curve_db"].items():
            plt.semilogx(FREQS, c, "o-", ms=3, label=m)
        plt.xlabel("Hz"); plt.ylabel("Detector level vs NORM (dB, 0 at 630 Hz)"); plt.grid(alpha=.3, which="both"); plt.legend()
        plt.tight_layout(); plt.savefig(os.path.join(odir, "thrust_curves.png"), dpi=120); plt.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(sys.argv[2], "analysis")
    analyse(sys.argv[1], sys.argv[2], out)
    print("written:", os.path.join(out, "report.md"))

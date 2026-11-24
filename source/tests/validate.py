#!/usr/bin/env python3
"""Validation suite for the Dub Filter gen~ engine.

Every test drives the *transpiled GenExpr* (build/engine.c, produced from the
exact code that ships in the device) through the C harness. Results go to
docs/validation/results.json and plots to docs/validation/*.png.
"""
import sys, os, json, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from dsp import run, base, tf, LP_MODELS, HP_MODELS

OUT = os.path.join(HERE, "..", "docs", "validation")
os.makedirs(OUT, exist_ok=True)
SR = 48000
R = {"tests": []}
RNG = np.random.default_rng(7)

# ---- plotting style (reference palette, light surface) ----
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SEQ = ["#a9c9ef", "#6ea4e4", "#2a78d6", "#14498a"]          # sequential blue: magnitude
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "lines.linewidth": 1.6, "font.size": 8, "axes.titlesize": 9,
                     "legend.frameon": False, "axes.spines.top": False, "axes.spines.right": False})


def record(name, passed, detail, **data):
    R["tests"].append(dict(name=name, passed=bool(passed), detail=detail, **data))
    print(("PASS " if passed else "FAIL ") + name + " — " + detail)


def db(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-12))


def stage_p(st, m, **kw):
    d = {f"{st}_on": 1, f"{st}_model": m}
    d.update({f"{st}_{k}": v for k, v in kw.items()})
    return base(**d)


def hf_burst(y, at, sr=SR, win=0.006, ref_win=(0.05, 0.25)):
    """Click metric: >8 kHz energy in a short window after an event, relative
    to the same measure in a quiet reference region before it (dB)."""
    sos = butter(4, 8000, "hp", fs=sr, output="sos")
    h = sosfilt(sos, y)
    a = int(at); w = int(win * sr)
    ev = np.sqrt(np.mean(h[a:a + w] ** 2)) + 1e-12
    r0, r1 = int(at - ref_win[1] * sr), int(at - ref_win[0] * sr)
    rf = np.sqrt(np.mean(h[r0:r1] ** 2)) + 1e-12
    return db(ev), db(ev / rf)


def test_signal(n, sr=SR, kind="music"):
    t = np.arange(n) / sr
    if kind == "sine":
        return 0.5 * np.sin(2 * np.pi * 110 * t)
    # bass + chord tones + pink-ish noise (dub-like stand-in), peak ~ -6 dBFS
    x = 0.25 * np.sin(2 * np.pi * 55 * t) + 0.1 * np.sin(2 * np.pi * 220 * t) + 0.07 * np.sin(2 * np.pi * 330 * t)
    noise = RNG.standard_normal(n)
    noise = sosfilt(butter(1, 800, fs=sr, output="sos"), noise) * 0.05
    return x + noise


# =====================================================================
def t_frequency_response():
    """Small-signal response per model / stage / resonance; plus slopes."""
    fails = []
    for st, names, fc in (("l", LP_MODELS, 1000.0), ("h", HP_MODELS, 300.0)):
        fig, axes = plt.subplots(2, 3, figsize=(11, 6), sharey=True)
        axes = axes.ravel()
        for m, nm in enumerate(names):
            ax = axes[m]
            for i, res in enumerate((0, 40, 70, 88)):
                f, H = tf(stage_p(st, m, cut=fc, res=res, slope=0))
                A = db(H)
                ax.semilogx(f[1:], A[1:], color=SEQ[i], label=f"res {res}%")
                if res <= 70:
                    if st == "l":
                        pb = A[np.argmin(abs(f - 40))]
                    else:
                        pb = A[np.argmin(abs(f - 15000))]
                    if abs(pb) > 1.0:
                        fails.append(f"{st}/{nm} res{res} passband {pb:.2f} dB")
            ax.set_title(nm)
            ax.set_xlim(20, 20000); ax.set_ylim(-60, 30)
            ax.axvline(fc, color=INK2, lw=0.6, ls=":")
        for ax in axes[len(names):]:
            ax.axis("off")
        axes[0].legend(loc="lower left")
        fig.suptitle(f"{'Low' if st == 'l' else 'High'}-pass stage — small-signal response, fc = {fc:.0f} Hz, native slope, Comp 100%")
        fig.supxlabel("Hz"); fig.supylabel("dB")
        fig.tight_layout(); fig.savefig(os.path.join(OUT, f"freq_{st}pf_resonance.png"), dpi=130); plt.close(fig)
    record("Passband integrity (bass for LPF @40 Hz, treble for HPF @15 kHz, res 0–70%, Comp 100%)",
           not fails, "all within ±1 dB" if not fails else "; ".join(fails))

    # slopes
    slope_rows = []
    for st, names, fc in (("l", LP_MODELS, 500.0), ("h", HP_MODELS, 2000.0)):
        fig, axes = plt.subplots(2, 3, figsize=(11, 6), sharey=True)
        axes = axes.ravel()
        for m, nm in enumerate(names):
            ax = axes[m]
            for sl in range(4):
                f, H = tf(stage_p(st, m, cut=fc, res=0, slope=sl), n=1 << 17, level=1e-4)
                A = db(H)
                ax.semilogx(f[1:], A[1:], color=SEQ[sl], label=f"{12 * (sl + 1)} dB/oct")
                # measured asymptotic slope one octave pair well into the stopband
                if st == "l":
                    f1, f2 = fc * 4, fc * 8
                else:
                    f1, f2 = fc / 8, fc / 4
                a1, a2 = A[np.argmin(abs(f - f1))], A[np.argmin(abs(f - f2))]
                meas = abs(a2 - a1)
                slope_rows.append(dict(stage=st, model=nm, selected=12 * (sl + 1), measured=round(meas, 1)))
            ax.set_title(nm); ax.set_xlim(20, 20000); ax.set_ylim(-120, 10)
        for ax in axes[len(names):]:
            ax.axis("off")
        axes[0].legend(loc="lower left")
        fig.suptitle(f"{'Low' if st == 'l' else 'High'}-pass stage — slope selector, fc = {fc:.0f} Hz, res 0")
        fig.supxlabel("Hz"); fig.supylabel("dB")
        fig.tight_layout(); fig.savefig(os.path.join(OUT, f"freq_{st}pf_slopes.png"), dpi=130); plt.close(fig)
    # expected effective slope: diode min 24
    bad = []
    dnat = {st: next(r["measured"] for r in slope_rows if r["model"].startswith("Diode") and r["selected"] == 24 and r["stage"] == st)
            for st in ("l",)}
    snat = next(r["measured"] for r in slope_rows if r["model"].startswith("Steiner") and r["selected"] == 12 and r["stage"] == "h")
    for r in slope_rows:
        exp = r["selected"]
        if r["model"].startswith("Diode"):
            # coupled ladder: 4 widely spread poles -> gentle slope near fc at res 0.
            # check that 12 == 24 (no 12 dB tap) and each extension adds 12 dB/oct.
            exp = dnat["l"] + 12 * max(0, r["selected"] // 12 - 2)
            r["note"] = "native diode slope measured near fc; extensions add 12 dB/oct each"
        if ("K35" in r["model"] or "Korg" in r["model"]) and r["stage"] == "h":
            # v1.6: MS-20 HP as built (Stinchcombe 2006 s.7): s(s+1)/D -> 6 dB/oct skirt below fc
            exp = 6 + 12 * (r["selected"] // 12 - 1)
            r["note"] = "MS-20 HP (6 dB/oct, hardware) + 12 dB/oct per extension"
        if r["model"].startswith("Steiner") and r["stage"] == "h":
            # Steiner HP injection: K s(s+2)/D -> 6 dB/oct skirt well below fc
            exp = snat + 12 * (r["selected"] // 12 - 1)
            r["note"] = "Steiner HP injection skirt (6 dB/oct) + 12 dB/oct per extension"
        if abs(r["measured"] - exp) > 4:
            bad.append(f"{r['stage']}/{r['model']} sel {r['selected']} meas {r['measured']}")
    record("Slope selector: measured slope (4–8× fc) within ±4 dB/oct of effective slope (diode, Steiner HP and K35 HP: native + 12 per extension)",
           not bad, "ok" if not bad else "; ".join(bad), rows=slope_rows)


def t_tracking():
    rows, bad = [], []
    for ovs in (0, 1):
        for st, names, cuts in (("l", LP_MODELS, (100, 300, 1000, 3000, 8000)), ("h", HP_MODELS, (40, 100, 300, 1000))):
            for m, nm in enumerate(names):
                for fc in cuts:
                    f, H = tf(dict(stage_p(st, m, cut=fc, res=85, slope=0), ovs_sel=ovs), n=1 << 17)
                    sel = (f > fc / 3) & (f < fc * 3)
                    pk = f[sel][np.argmax(np.abs(H[sel]))]
                    fexp = fc
                    if "904B" in nm:
                        # no resonance: track the corner instead, where two sections of s/(s+1) give |H| = 1/2 (-6.02 dB)
                        mag = np.abs(H[sel]); i_ = np.argmax(mag >= 0.5)
                        pk = f[sel][i_]
                    if "SEM" in nm:
                        # v1.6: SEM-1A RES law gives Q ~1.8 at res 85; a 2-pole peak then sits at fc*sqrt(1-2R^2) (LP)
                        # or fc/sqrt(1-2R^2) (HP), not at fc
                        R_ = 0.05 + 1.515 * 0.15
                        fexp = fc * np.sqrt(1 - 2 * R_ * R_) ** (1 if st == "l" else -1)
                    err = 1200 * np.log2(pk / fexp)
                    rows.append(dict(os=ovs + 1, stage=st, model=nm, fc=fc, peak=round(float(pk), 1), cents=round(float(err), 0)))
                    # frequency resolution of the estimate is 5.9 Hz -> allow that at low fc
                    tol = max(100, 1200 * np.log2((fc + 6) / fc))
                    if fc / (SR * (ovs + 1)) < 0.2 and abs(err) > tol:
                        bad.append(f"os{ovs + 1} {st}/{nm} fc{fc}: {err:+.0f} c")
    record("Cutoff tracking: resonant peak within ±100 cents of the set cutoff (res 85%; SEM: of its circuit-Q peak position; 904B HP: its -6 dB corner)",
           not bad, "ok" if not bad else "; ".join(bad), rows=rows)


def t_impulse_step():
    fig, axes = plt.subplots(2, 2, figsize=(11, 6))
    bad = []
    n = SR
    for row, (st, names, fc) in enumerate((("l", LP_MODELS, 500.0), ("h", HP_MODELS, 200.0))):
        for col, kind in enumerate(("impulse", "step")):
            ax = axes[row, col]
            for m, nm in enumerate(names):
                x = np.zeros(n + SR // 2)
                if kind == "impulse":
                    x[SR // 2] = 0.25
                else:
                    x[SR // 2:] = 0.25
                y = run(x, stage_p(st, m, cut=fc, res=60, slope=0))[SR // 2:, 0]
                tt = np.arange(len(y)) / SR * 1000
                ax.plot(tt[:int(0.03 * SR)], y[:int(0.03 * SR)], color=CAT[m], label=nm, lw=1.2)
                tail = y[-int(0.1 * SR):]
                if kind == "impulse" and np.abs(tail).max() > 1e-5:
                    bad.append(f"{st}/{nm} impulse not decayed ({np.abs(tail).max():.1e})")
                if kind == "step":
                    final = tail.mean()
                    target = 0.25 if st == "l" else 0.0
                    # DC blocker (2 Hz) slowly bleeds the LP step: allow 1% / 1 s
                    if abs(final - target * np.exp(-2 * np.pi * 2 * 0.95)) > 0.01:
                        bad.append(f"{st}/{nm} step final {final:.4f}")
            ax.set_title(f"{'LPF' if st == 'l' else 'HPF'} {kind} response (fc {fc:.0f} Hz, res 60%)")
            ax.set_xlabel("ms")
        axes[0, 0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "impulse_step.png"), dpi=130); plt.close(fig)
    record("Impulse decay and step settling (LPF passes DC, HPF removes it)", not bad, "ok" if not bad else "; ".join(bad))


def t_self_osc():
    rows, bad = [], []
    for ovs in (0, 1):
        for st, names in (("l", LP_MODELS), ("h", HP_MODELS)):
            for m, nm in enumerate(names):
                for fc in ((100, 1000, 5000) if st == "l" else (60, 300, 1500)):
                    x = np.zeros(SR * 3); x[SR // 2] = 0.3
                    y = run(x, dict(stage_p(st, m, cut=fc, res=100, slope=0), ovs_sel=ovs))
                    tail = y[2 * SR:, 0]
                    fin = np.all(np.isfinite(y))
                    pk = np.abs(tail).max()
                    spec = np.abs(np.fft.rfft(tail * np.hanning(len(tail))))
                    fr = np.fft.rfftfreq(len(tail), 1 / SR)[np.argmax(spec)]
                    osc = pk > 1e-3
                    cents = 1200 * np.log2(fr / fc) if osc else None
                    rows.append(dict(os=ovs + 1, stage=st, model=nm, fc=fc, oscillates=bool(osc),
                                     peak_dbfs=round(float(db(pk)), 1), freq=round(float(fr), 1),
                                     cents=None if cents is None else round(float(cents))))
                    expect = not (nm.startswith("SEM") or nm == "Sherman" or nm.startswith("Moog 904B")) and not (nm == "Ladder" and fc < 120)   # v1.6: Sherman partial self-oscillation; 904B has no resonance; Minimoog couplings stop the Ladder below ~120 Hz
                    if not fin or pk > 1.25 or osc != expect or (osc and abs(cents) > 100):
                        bad.append(f"os{ovs + 1} {st}/{nm} fc{fc}: osc={osc} pk={db(pk):.1f}dBFS f={fr:.0f}")
    record("Self-oscillation: stable, bounded (<+2 dBFS), on pitch (±100 c); SEM and Sherman do not sustain it and the 904B HP has no resonance (by design); Ladder not below ~120 Hz (Minimoog couplings)",
           not bad, "ok" if not bad else "; ".join(bad), rows=rows)


def t_nonlinear():
    rows = []
    n = SR * 2
    t = np.arange(n) / SR
    fig, axes = plt.subplots(2, 3, figsize=(11, 6), sharey=True)
    axes = axes.ravel()
    for m, nm in enumerate(LP_MODELS):
        ax = axes[m]
        for i, drv in enumerate((0, 50, 100)):
            x = 0.5 * np.sin(2 * np.pi * 100 * t)
            y = run(x, stage_p("l", m, cut=2000, res=30, drive=drv, slope=0))[SR:, 0]
            sp = np.abs(np.fft.rfft(y * np.blackman(len(y)))) / (len(y) / 4)
            fr = np.fft.rfftfreq(len(y), 1 / SR)
            h = [sp[np.argmin(abs(fr - 100 * k))] for k in range(1, 11)]
            thd = np.sqrt(sum(v * v for v in h[1:])) / h[0]
            even = np.sqrt(sum(h[k] ** 2 for k in (1, 3, 5, 7, 9))) / h[0]
            rows.append(dict(model=nm, drive=drv, thd_pct=round(100 * thd, 3), even_db=round(float(db(even)), 1),
                             peak=round(float(np.abs(y).max()), 3)))
            ax.semilogx(fr[1:], db(sp[1:]), color=SEQ[i + 1], lw=0.8, label=f"drive {drv}%")
        ax.set_xlim(50, 20000); ax.set_ylim(-140, 0); ax.set_title(nm)
    axes[0].legend()
    fig.suptitle("Nonlinear behaviour — 100 Hz sine at −6 dBFS, LPF 2 kHz, res 30%, Comp 100%")
    fig.supxlabel("Hz"); fig.supylabel("dBFS")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "nonlinear_spectra.png"), dpi=130); plt.close(fig)
    mono = all(rows[i]["thd_pct"] <= rows[i + 1]["thd_pct"] * 1.05 + 0.01 for i in range(0, len(rows), 3) for _ in [0]) and \
        all(rows[i + 1]["thd_pct"] <= rows[i + 2]["thd_pct"] * 1.05 + 0.01 for i in range(0, len(rows), 3))
    finite = all(np.isfinite(r["peak"]) and r["peak"] < 2 for r in rows)
    record("Nonlinearity: harmonic content rises with drive, output bounded (<+6 dBFS)", mono and finite,
           ("THD monotonic in drive" if mono else "non-monotonic THD") + (", bounded" if finite else ", peak too high"), rows=rows)

    # aliasing: 1x vs 2x oversampling, 7 kHz sine hard driven
    ar = []
    for m, nm in enumerate(LP_MODELS):
        res = {}
        for ovs in (0, 1):
            x = 0.7 * np.sin(2 * np.pi * 7000 * t)
            y = run(x, dict(stage_p("l", m, cut=16000, res=20, drive=100, slope=0), ovs_sel=ovs))[SR:, 0]
            sp = np.abs(np.fft.rfft(y * np.blackman(len(y))))
            fr = np.fft.rfftfreq(len(y), 1 / SR)
            harm = np.zeros_like(fr, bool)
            for k in range(1, 40):
                hf = 7000 * k
                if hf < SR / 2:
                    harm |= abs(fr - hf) < 15
            harm |= fr < 20
            alias = np.sqrt(np.sum(sp[~harm] ** 2)); fund = sp[np.argmin(abs(fr - 7000))]
            res[ovs] = float(db(alias / fund))
        ar.append(dict(model=nm, alias_db_1x=round(res[0], 1), alias_db_2x=round(res[1], 1)))
    better = all(r["alias_db_2x"] < r["alias_db_1x"] for r in ar)
    record("Oversampling: 2x reduces aliasing for every model (7 kHz sine, drive 100%)", better,
           ", ".join(f"{r['model']} {r['alias_db_1x']}→{r['alias_db_2x']} dB" for r in ar), rows=ar)


def t_stereo():
    n = SR
    a = test_signal(n); b = np.roll(test_signal(n), 999) * 0.7
    bad = []
    for st, names in (("l", LP_MODELS), ("h", HP_MODELS)):
        for m, nm in enumerate(names):
            p = stage_p(st, m, cut=800 if st == "l" else 200, res=80, drive=60, slope=1)
            y = run(np.stack([a, a], 1), p)
            if not np.array_equal(y[:, 0], y[:, 1]):
                bad.append(f"{st}/{nm} L≠R for identical input")
            y2 = run(np.stack([a, np.zeros(n)], 1), p)
            if np.abs(y2[:, 1]).max() != 0:
                bad.append(f"{st}/{nm} crosstalk {db(np.abs(y2[:, 1]).max()):.0f} dB")
            y3 = run(np.stack([a, b], 1), p)
            yl = run(np.stack([a, a], 1), p)[:, 0]
            if not np.array_equal(y3[:, 0], yl):
                bad.append(f"{st}/{nm} R content affects L")
    for ovs in (1,):
        p = dict(base(l_on=1, h_on=1, l_model=0, h_model=0, l_cut=900, h_cut=150, l_res=90, h_res=70), ovs_sel=ovs)
        y = run(np.stack([a, a], 1), p)
        if not np.array_equal(y[:, 0], y[:, 1]):
            bad.append("2x OS L≠R")
    record("Stereo: identical L/R in → bit-identical out; zero crosstalk; channels independent (all models, 1x & 2x)",
           not bad, "ok" if not bad else "; ".join(bad))


# ---------------------------------------------------------------------
def click_case(name, p0, events, x=None, n=None, at=None):
    n = n or SR
    x = test_signal(n, kind="sine") if x is None else x
    y = run(x, p0, events=events)[:, 0]
    absdb, rel = hf_burst(y, at if at is not None else events[0][0])
    fin = np.all(np.isfinite(y))
    return dict(case=name, hf_abs_dbfs=round(float(absdb), 1), hf_rel_db=round(float(rel), 1), finite=bool(fin))


def t_clicks():
    """Abrupt parameter changes on a steady 110 Hz sine (−6 dBFS).
    Metric: >8 kHz energy in the 6 ms after the change. A hard discontinuity
    of the same signal measures roughly −20 dBFS on this metric."""
    E = SR // 2
    rows = []
    L = lambda **kw: base(l_on=1, **{f"l_{k}": v for k, v in kw.items()})
    Hh = lambda **kw: base(h_on=1, **{f"h_{k}": v for k, v in kw.items()})
    # reference: hard discontinuity (polarity flip) of the same sine
    x = test_signal(SR, kind="sine"); xr = x.copy(); Ef = E + int(SR / 110 / 4); xr[Ef:] *= -1
    ref_abs, _ = hf_burst(xr, Ef)
    for m, nm in enumerate(LP_MODELS):
        rows.append(click_case(f"LPF {nm}: cutoff 20 kHz→200 Hz", L(model=m, cut=20000, res=50), [(E, "l_cut", 200)]))
        rows.append(click_case(f"LPF {nm}: cutoff 200 Hz→20 kHz", L(model=m, cut=200, res=50), [(E, "l_cut", 20000)]))
        rows.append(click_case(f"LPF {nm}: resonance 0→100%", L(model=m, cut=800, res=0), [(E, "l_res", 100)]))
        rows.append(click_case(f"LPF {nm}: slope 12→48", L(model=m, cut=800, res=40, slope=0), [(E, "l_slope", 3)]))
        rows.append(click_case(f"LPF {nm}: drive 0→100%", L(model=m, cut=800, res=40), [(E, "l_drive", 100)]))
        rows.append(click_case(f"LPF {nm}: character 0→100%", L(model=m, cut=800, res=40), [(E, "l_char", 100)]))
        rows.append(click_case(f"LPF {nm}: stage off", L(model=m, cut=400, res=60), [(E, "l_on", 0)]))
        nxt = (m + 1) % 6
        rows.append(click_case(f"LPF model switch {nm}→{LP_MODELS[nxt]}", L(model=m, cut=600, res=60), [(E, "l_model", nxt)]))
    for m, nm in enumerate(HP_MODELS):
        rows.append(click_case(f"HPF {nm}: cutoff 20 Hz→1 kHz", Hh(model=m, cut=20, res=50), [(E, "h_cut", 1000)]))
        rows.append(click_case(f"HPF {nm}: cutoff 1 kHz→20 Hz", Hh(model=m, cut=1000, res=50), [(E, "h_cut", 20)]))
        nxt = (m + 1) % 5
        rows.append(click_case(f"HPF model switch {nm}→{HP_MODELS[nxt]}", Hh(model=m, cut=80, res=60), [(E, "h_model", nxt)]))
        rows.append(click_case(f"HPF {nm}: stage on", base(h_on=0, h_model=m, h_cut=150, h_res=60), [(E, "h_on", 1)]))
    both = base(l_on=1, h_on=1, l_model=0, h_model=3, l_cut=900, h_cut=150, l_res=80, h_res=70, l_drive=60)
    rows.append(click_case("Stage order LP→HP to HP→LP", both, [(E, "order_sel", 1)]))
    rows.append(click_case("Oversampling 1x→2x", both, [(E, "ovs_sel", 1)]))
    rows.append(click_case("Output level −24→+6 dB", both, [(E, "out_db", 6)]))
    worst = max(r["hf_abs_dbfs"] for r in rows)
    bad = [r for r in rows if r["hf_abs_dbfs"] > -60 or not r["finite"]]
    record(f"Click/zipper: >8 kHz burst after every abrupt change below −60 dBFS on a −6 dBFS sine (hard discontinuity = {ref_abs:.1f} dBFS)",
           not bad, f"{len(rows)} cases, worst {worst:.1f} dBFS" + ("" if not bad else "; FAIL: " + "; ".join(r["case"] for r in bad)),
           rows=rows, reference_dbfs=round(float(ref_abs), 1))


# ---------------------------------------------------------------------
def t_spec1_scenarios():
    out = []
    n = SR * 4
    x = test_signal(n)
    xs = np.stack([x, np.roll(x, 333) * 0.8], 1)
    # 1 LPF fully open, HPF fully closed (both enabled at their extremes)
    p = base(l_on=1, h_on=1, l_cut=20000, h_cut=20, l_model=2, h_model=1, softclip=1)
    f, H = tf(p, level=0.05)
    sel = (f >= 20) & (f <= 20000)
    dev = np.abs(db(H[sel])).max()
    out.append(("1. LPF fully open + HPF fully closed: magnitude flat 20 Hz–20 kHz within ±0.1 dB", dev < 0.1, f"max deviation {dev:.3f} dB"))
    # 2 LPF sweep 20k -> 200 Hz
    ev = [(SR // 2 + i * 480, "l_cut", 20000 * (200 / 20000) ** (i / 300)) for i in range(301)]
    y = run(xs, base(l_on=1, l_model=2, l_res=40), events=ev)
    out.append(("2. LPF sweep 20 kHz→200 Hz (3 s, 10 ms automation steps)", np.all(np.isfinite(y)) and np.abs(y).max() < 1.0,
                f"peak {db(np.abs(y).max()):.1f} dBFS"))
    spectro(y[:, 0], "scenario2_lpf_sweep.png", "Scenario 2 — Ladder LPF sweep 20 kHz→200 Hz, res 40%")
    # 3 LPF max resonance, each model, music in
    pk = []
    for m in range(6):
        y = run(xs, base(l_on=1, l_model=m, l_cut=700, l_res=100, softclip=0))
        pk.append(np.abs(y[SR:]).max())
    ok = all(np.isfinite(pk)) and max(pk) < 2.0
    out.append(("3. LPF at maximum resonance with program input, all models (soft clip OFF)", ok,
                ", ".join(f"{LP_MODELS[i]} {db(v):.1f}" for i, v in enumerate(pk)) + " dBFS peak"))
    # 4 HPF sweep 20 -> 1k
    ev = [(SR // 2 + i * 480, "h_cut", 20 * (1000 / 20) ** (i / 300)) for i in range(301)]
    y = run(xs, base(h_on=1, h_model=1, h_res=50), events=ev)
    out.append(("4. HPF sweep 20 Hz→1 kHz", np.all(np.isfinite(y)), f"peak {db(np.abs(y).max()):.1f} dBFS"))
    spectro(y[:, 0], "scenario4_hpf_sweep.png", "Scenario 4 — K35 HPF sweep 20 Hz→1 kHz, res 50%")
    # 5 sudden HPF changes (dub 'drop'): 20 Hz <-> 600 Hz every 250 ms
    ev = [(SR // 2 + i * SR // 4, "h_cut", 600 if i % 2 == 0 else 20) for i in range(12)]
    xsin = test_signal(n, kind="sine")
    y = run(xsin, base(h_on=1, h_model=4, h_res=30), events=ev)[:, 0]
    bursts = [hf_burst(y, e[0])[0] for e in ev]
    out.append(("5. Sudden HPF cutoff changes (20 Hz↔600 Hz every 250 ms)", max(bursts) < -60,
                f"worst >8 kHz burst {max(bursts):.1f} dBFS"))
    # 6 both filters simultaneously, both sweeping
    ev = [(SR // 2 + i * 480, "l_cut", 8000 * (300 / 8000) ** (i / 300)) for i in range(301)] + \
         [(SR // 2 + i * 480, "h_cut", 30 * (500 / 30) ** (i / 300)) for i in range(301)]
    y = run(xs, base(l_on=1, h_on=1, l_model=0, h_model=3, l_res=70, h_res=60), events=ev)
    out.append(("6. Both filters active and sweeping toward each other", np.all(np.isfinite(y)) and np.abs(y).max() < 1.2,
                f"peak {db(np.abs(y).max()):.1f} dBFS"))
    # 7 stereo L/R differ
    p = base(l_on=1, h_on=1, l_model=5, h_model=2, l_cut=900, h_cut=120, l_res=85)
    y = run(xs, p); yl = run(np.stack([xs[:, 0], xs[:, 0]], 1), p)
    out.append(("7. Stereo input with different L/R content", np.array_equal(y[:, 0], yl[:, 0]), "left output independent of right input"))
    # 8 rapid manual movements: random cutoff jumps every 5 ms
    ev = [(SR // 2 + i * 240, "l_cut", float(20 * 1000 ** RNG.random())) for i in range(600)]
    y = run(xs, base(l_on=1, l_model=3, l_res=70), events=ev)
    out.append(("8. Rapid manual movement (random LPF jumps every 5 ms, 3 s)", np.all(np.isfinite(y)) and np.abs(y).max() < 1.5,
                f"peak {db(np.abs(y).max()):.1f} dBFS, no NaN/Inf"))
    # 9 automation: block-rate (64-sample) ramp vs per-sample ramp
    def ramp(step):
        return [(SR // 2 + i, "l_cut", 20000 * (150 / 20000) ** (i / (2 * SR))) for i in range(0, 2 * SR, step)]
    ya = run(xsin, base(l_on=1, l_model=2, l_res=60), events=ramp(64))[:, 0]
    yb = run(xsin, base(l_on=1, l_model=2, l_res=60), events=ramp(1))[:, 0]
    err = db(np.sqrt(np.mean((ya - yb) ** 2)) / np.sqrt(np.mean(yb ** 2)))
    sos = butter(4, 8000, "hp", fs=SR, output="sos")
    hfa = db(np.sqrt(np.mean(sosfilt(sos, ya) ** 2))); hfb = db(np.sqrt(np.mean(sosfilt(sos, yb) ** 2)))
    out.append(("9. Automation at Live's block rate (64-sample steps) vs sample-accurate ramp", err < -30 and hfa - hfb < 1,
                f"difference {err:.1f} dB; >8 kHz energy {hfa - hfb:+.2f} dB vs sample-accurate (no zipper)"))
    # 10 MIDI: 7-bit CC steps on cutoff (one CC value per 8 ms)
    def cc2hz(v):  # live.dial exponent 5 mapping
        return 20 + (20000 - 20) * (v / 127) ** 5
    ev = [(SR // 2 + i * 384, "l_cut", cc2hz(127 - i)) for i in range(128)]
    y = run(xsin, base(l_on=1, l_model=2, l_res=60), events=ev)[:, 0]
    bursts = [hf_burst(y, e[0], ref_win=(0.3, 0.45))[0] for e in ev[::8]]
    out.append(("10. MIDI CC (7-bit) stepping of cutoff, one step per 8 ms", max(bursts) < -60,
                f"worst >8 kHz burst {max(bursts):.1f} dBFS (no zipper)"))
    for (nm, ok, det) in out:
        record(nm, ok, det)


def spectro(y, fn, title):
    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.specgram(y, NFFT=2048, Fs=SR, noverlap=1536, cmap="magma", vmin=-140, vmax=-20)
    ax.set_yscale("symlog", linthresh=200); ax.set_ylim(20, 20000)
    ax.set_xlabel("s"); ax.set_ylabel("Hz"); ax.set_title(title); ax.grid(False)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, fn), dpi=130); plt.close(fig)


def t_samplerates():
    rows, bad = [], []
    for sr in (44100, 48000, 88200, 96000, 192000):
        for st, m, nm in (("l", 2, "Ladder"), ("l", 5, "Diode/303"), ("l", 3, "Steiner-Parker"), ("h", 1, "K35/MS-20")):
            for fc in ((1000, 10000) if st == "l" else (100, 1000)):
                f, H = tf(stage_p(st, m, cut=fc, res=85, slope=0), sr=sr, n=1 << 17)
                sel = (f > fc / 3) & (f < min(fc * 3, sr / 2))
                pk = f[sel][np.argmax(np.abs(H[sel]))]
                c = 1200 * np.log2(pk / fc)
                x = np.zeros(sr * 2); x[sr // 2] = 0.3
                y = run(x, stage_p(st, m, cut=fc, res=100, slope=0), sr=sr)
                rows.append(dict(sr=sr, model=nm, stage=st, fc=fc, peak_cents=round(float(c)),
                                 selfosc_peak_dbfs=round(float(db(np.abs(y[sr:]).max())), 1)))
                res_hz = sr / 8192
                # bound 1.6 (+4 dBFS): v1.6 Minimoog Emphasis reaches k = 5.04, so self-oscillation runs ~3.3 dB louder
                # (12 dB tap ~1.03 at 4x); at 1x near fs/4 the ladder overshoots further (pre-existing: 0.66 -> 1.08 in v1.5)
                if abs(c) > max(100, 1200 * np.log2((fc + res_hz) / fc)) or not np.all(np.isfinite(y)) or np.abs(y).max() > 1.6:
                    bad.append(f"{sr} {nm} fc{fc}: {c:+.0f} c")
    record("Sample-rate independence 44.1–192 kHz: tuning and stability", not bad, "ok" if not bad else "; ".join(bad), rows=rows)


def t_cpu():
    rows = []
    n = SR * 10
    x = test_signal(n)
    cfgs = [
        ("Both stages off (pass-through)", base()),
        ("Default device (Ladder LPF 24 dB + K35 HPF), 1x", base(l_on=1, h_on=1, l_model=2, h_model=1, l_cut=2000, h_cut=60, l_slope=1)),
        ("Diode LPF 48 dB + Sherman HPF 48 dB, 1x", base(l_on=1, h_on=1, l_model=5, h_model=0, l_cut=2000, h_cut=60, l_slope=3, h_slope=3)),
        ("Default device, 2x oversampling", base(l_on=1, h_on=1, l_model=2, h_model=1, l_cut=2000, h_cut=60, l_slope=1, ovs_sel=1)),
        ("Worst case: Diode+Sherman 48 dB, 2x, both mid-crossfade", base(l_on=1, h_on=1, l_model=5, h_model=0, l_cut=2000, h_cut=60, l_slope=3, h_slope=3, ovs_sel=1)),
    ]
    for nm, p in cfgs:
        ev = []
        if "crossfade" in nm:  # keep switching models so two models always run
            ev = [(i * int(0.02 * SR), "l_model", (5, 0)[i % 2]) for i in range(1, 499)] + \
                 [(i * int(0.02 * SR), "h_model", (0, 3)[i % 2]) for i in range(1, 499)]
        best = 1e9
        for _ in range(3):
            _, ns = run(x, p, events=ev, ns=True)
            best = min(best, ns)
        rows.append(dict(config=nm, ns_per_frame=round(best, 1), pct_of_one_core_48k=round(best * 48000 / 1e7, 2)))
        print(f"   CPU {nm}: {best:.0f} ns/frame = {best * 48000 / 1e7:.2f}% of one core @48 kHz")
    record("CPU benchmark (transpiled C, gcc -O2, this machine)", True,
           "; ".join(f"{r['config']}: {r['pct_of_one_core_48k']}%" for r in rows), rows=rows)


def t_denormal_dc():
    n = SR * 12
    x = test_signal(n); x[SR * 2:] = 0
    bad = []
    for m in range(6):
        p = base(l_on=1, h_on=1, l_model=m, h_model=min(m, 4), l_cut=500, h_cut=80, l_res=80, h_res=60)
        y = run(x, p)
        tail = y[-SR:]
        if np.abs(tail).max() > 0:
            # must have decayed to exactly zero (flushed) or below -300 dB
            if np.abs(tail).max() > 1e-15:
                bad.append(f"{LP_MODELS[m]} tail {np.abs(tail).max():.1e}")
    # timing: silence vs signal must not blow up (denormal stalls show as >3x)
    xs = test_signal(SR * 4); xz = np.zeros(SR * 4); xz[:100] = xs[:100]
    p = base(l_on=1, h_on=1, l_model=2, h_model=1, l_cut=500, h_cut=80, l_res=80)
    _, a = run(xs, p, ns=True); _, b = run(xz, p, ns=True)
    ratio = b / a
    record("Denormals: decay tails flush to zero; silence costs no more than signal", not bad and ratio < 1.5,
           f"silence/signal CPU ratio {ratio:.2f}" + ("" if not bad else "; " + "; ".join(bad)))
    # DC offset: asymmetric models with hot input
    rows = []
    t = np.arange(SR * 3) / SR
    xin = 0.9 * np.sin(2 * np.pi * 80 * t)
    for m in range(6):
        y = run(xin, base(l_on=1, l_model=m, l_cut=3000, l_res=60, l_drive=100))[SR * 2:, 0]
        rows.append(dict(model=LP_MODELS[m], dc_dbfs=round(float(db(abs(y.mean()))), 1)))
    worst = max(r["dc_dbfs"] for r in rows)
    record("DC offset at output with asymmetric saturation (drive 100%, hot input)", worst < -60,
           f"worst residual DC {worst:.1f} dBFS", rows=rows)


def t_longrun():
    n = SR * 30
    x = test_signal(n) * 1.5
    ev = []
    for i in range(1, 300):
        fr = i * SR // 10
        ev += [(fr, "l_cut", float(20 * 1000 ** RNG.random())), (fr, "h_cut", float(20 * 100 ** RNG.random())),
               (fr, "l_res", float(100 * RNG.random())), (fr, "h_res", float(100 * RNG.random()))]
        if i % 7 == 0:
            ev += [(fr, "l_model", int(RNG.integers(0, 6))), (fr, "h_model", int(RNG.integers(0, 5)))]
        if i % 11 == 0:
            ev += [(fr, "l_slope", int(RNG.integers(0, 4))), (fr, "h_slope", int(RNG.integers(0, 4))), (fr, "l_drive", float(100 * RNG.random()))]
        if i % 37 == 0:
            ev += [(fr, "order_sel", int(RNG.integers(0, 2))), (fr, "ovs_sel", int(RNG.integers(0, 2)))]
    y = run(x, base(l_on=1, h_on=1, softclip=1), events=ev)
    ok = np.all(np.isfinite(y)) and np.abs(y).max() <= 1.0
    record("30 s stress run: random changes to every parameter, hot input, soft clip ON", ok,
           f"peak {db(np.abs(y).max()):.2f} dBFS, finite={np.all(np.isfinite(y))}")


# =====================================================================
def t_circuit_reference():
    """Small-signal response of each model vs the analogue transfer function
    of the circuit it is derived from (bilinear-mapped with the model's own
    prewarped coefficient). Comp = 0 so no makeup gain alters the circuit."""
    fs = SR
    M303 = np.array([[-1, 1, 0, 0], [1, -2, 1, 0], [0, 1, -2, 1], [0, 0, 1, -2]], float) / np.array([0.5, 1, 1, 1])[:, None]
    B303 = np.array([1, 0, 0, 0]) / np.array([0.5, 1, 1, 1])
    def core303(s):
        return np.array([np.linalg.solve(si * np.eye(4) - M303, B303)[3] for si in s])
    cases = []
    def add(name, st, m, fc, res, slope, ref):
        cases.append((name, st, m, fc, res, slope, ref))
    for res in (0, 60):
        # v1.6 Minimoog filter board: k from the Emphasis rheostat law; C5/C1 (15.4 Hz) couple the ladder output
        # (in the output and in the loop), C10 couples the feedback (corner set by R14 + 1330 ohm)
        R14 = 50000 * (np.exp(4.394 * (1 - res / 100)) - 1) / 79.96362664
        k = 6700.067 / (R14 + 1330)
        fb_ = 15915.4943 / (R14 + 1330)
        def lad(s, fc, k=k, fb_=fb_, hp=False):
            Hc = s / (s + 15.3921608 / fc); Hb = s / (s + fb_ / fc)
            return s ** 4 / ((1 + s) ** 4 + k * Hb * Hc) if hp else Hc / ((1 + s) ** 4 + k * Hb * Hc)
        add(f"Ladder LP 24 — Minimoog: Hc/((1+s)^4 + k Hb Hc), Stinchcombe core + fig. 9-11 couplings, res {res}%", "l", 2, 1000, res, 1,
            lambda s, lad=lad: lad(s, 1000))
        add(f"Ladder HP — Moog 904B (dwg. 1118): (s/(s+1))^4, no resonance (res {res}% ignored)", "h", 2, 300, res, 1,
            lambda s: s ** 4 / (1 + s) ** 4)
        K = 0.05 + 2.03 * (res / 100) ** 1.1
        add(f"Korg 35 LP — 1/(s^2+(2-K)s+1), res {res}%", "l", 1, 1000, res, 0, lambda s, K=K: 1 / (s * s + (2 - K) * s + 1))
        add(f"Korg 35 HP — s(s+1)/(s^2+(2-K)s+1) (MS-20 as built), res {res}%", "h", 1, 300, res, 0, lambda s, K=K: s * (s + 1) / (s * s + (2 - K) * s + 1))
        Ks = 1 + 2.1 * (res / 100) ** 1.3
        add(f"Steiner-Parker LP — Sallen-Key K/(s^2+(3-K)s+1), res {res}%", "l", 3, 1000, res, 0,
            lambda s, K=Ks: K / (s * s + (3 - K) * s + 1))
        add(f"Steiner-Parker HP injection — K s(s+2)/(s^2+(3-K)s+1), res {res}%", "h", 3, 300, res, 0,
            lambda s, K=Ks: K * s * (s + 2) / (s * s + (3 - K) * s + 1))
        R = 0.05 + 1.515 * (1 - res / 100)   # v1.6: SEM-1A RES pot law (2R = 0.1 + 3.03 (1 - res))
        add(f"SEM LP — SVF 1/(s^2+2Rs+1), res {res}%", "l", 4, 1000, res, 0, lambda s, R=R: 1 / (s * s + 2 * R * s + 1))
        add(f"SEM HP — SVF s^2/(s^2+2Rs+1), res {res}%", "h", 4, 300, res, 0, lambda s, R=R: s * s / (s * s + 2 * R * s + 1))
        kd = 17.0 * 1.15 * (res / 100) ** 1.8
        c = 0.1494 + 1.2648 * np.sqrt(min(kd / 17.0, 1.06))
        def ref303(s, kd=kd, c=c, fc=1000.0):
            # s here is normalised to the stage cutoff; the ladder runs at w = fc/c,
            # the feedback highpass at 8 Hz (CHARACTER 0)
            sl = s * c
            sh = s * np.tan(np.pi * fc / fs) / np.tan(np.pi * 8 / fs)
            h = core303(sl)
            return h / (1 + kd * h * sh / (sh + 1))
        add(f"TB-303 — Stinchcombe 303 ladder (bottom C/2) + feedback HPF, res {res}%", "l", 5, 1000, res, 1, ref303)
    rows, bad = [], []
    fig, axes = plt.subplots(3, 3, figsize=(12, 8.5))
    axes = axes.ravel()
    seen = {}
    for (name, st, m, fc, res, slope, ref) in cases:
        p = stage_p(st, m, cut=fc, res=res, slope=slope, comp=0)
        f, H = tf(p, n=1 << 17, level=2e-4)
        sel = (f >= 20) & (f <= 20000)
        f = f[sel]; H = H[sel]
        sn = 1j * np.tan(np.pi * f / fs) / np.tan(np.pi * fc / fs)
        Href = ref(sn)
        A, Ar = db(H), db(Href)
        valid = Ar > -60
        err = np.abs(A[valid] - Ar[valid])
        mx = float(np.percentile(err, 99))
        rows.append(dict(reference=name, max_err_db_p99=round(mx, 3), median_err_db=round(float(np.median(err)), 4)))
        if mx > 0.5:
            bad.append(f"{name}: {mx:.2f} dB")
        key = name.split(" —")[0]
        if key not in seen:
            seen[key] = len(seen)
        ax = axes[seen[key]]
        i = 0 if res == 0 else 1
        ax.semilogx(f, Ar, color=GRID if i == 0 else "#c9c7c0", lw=4, label=f"circuit TF, res {res}%")
        ax.semilogx(f, A, color=SEQ[2 * i + 1], lw=1.2, label=f"device, res {res}%")
        ax.set_title(key); ax.set_xlim(20, 20000); ax.set_ylim(-80, 20)
    axes[0].legend(fontsize=7)
    fig.suptitle("Device response (thin) over the circuit's analogue transfer function (thick), small signal, Comp 0")
    fig.supxlabel("Hz"); fig.supylabel("dB")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "circuit_reference.png"), dpi=130); plt.close(fig)
    record("Circuit reference: small-signal response matches each circuit's analogue transfer function (99th-pct error < 0.5 dB)",
           not bad, "worst " + max(rows, key=lambda r: r["max_err_db_p99"])["reference"].split(" —")[0] +
           f" {max(r['max_err_db_p99'] for r in rows):.3f} dB" + ("" if not bad else "; FAIL " + "; ".join(bad)), rows=rows)


if __name__ == "__main__":
    t0 = time.time()
    for fn in (t_circuit_reference, t_frequency_response, t_tracking, t_impulse_step, t_self_osc, t_nonlinear, t_stereo,
               t_clicks, t_spec1_scenarios, t_samplerates, t_cpu, t_denormal_dc, t_longrun):
        print("==", fn.__name__)
        fn()
    print("== v1.2 band-pass engine + regression gates")
    import bpf_tests
    bpf_tests.run_all(record, plt, OUT, SEQ, CAT, GRID, test_signal)
    print("== v1.3 dynamics chain + regression gates")
    import dyn_tests
    dyn_tests.run_all(record, plt, OUT, SEQ, CAT, GRID, test_signal)
    print("== v1.4 filter routing + regression gates")
    import routing_tests
    routing_tests.run_all(record, plt, OUT, SEQ, CAT, GRID, test_signal)
    R["summary"] = dict(total=len(R["tests"]), passed=sum(t["passed"] for t in R["tests"]),
                        seconds=round(time.time() - t0, 1))
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(R, f, indent=1, default=float)
    print(R["summary"])

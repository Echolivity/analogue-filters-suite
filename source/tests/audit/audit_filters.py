#!/usr/bin/env python3
"""Filter fidelity diagnostics (LPF / HPF models, BPF engine). Read-only: runs the
shipped engine and writes docs/dsp-audit/data/filters.json + plots."""
import numpy as np
from common import run, base, tf, stage, db, tone, harmonics, thd, save, savefig, plt, COL, LP_MODELS, HP_MODELS

R = {}

# ---------------------------------------------------------------- analogue references
M303 = np.array([[-1, 1, 0, 0], [1, -2, 1, 0], [0, 1, -2, 1], [0, 0, 1, -2]], float) / np.array([0.5, 1, 1, 1])[:, None]
B303 = np.array([1, 0, 0, 0]) / np.array([0.5, 1, 1, 1])


def core303(s):
    return np.array([np.linalg.solve(si * np.eye(4) - M303, B303)[3] for si in s])


def analog_ref(st, m, res, fc):
    """True analogue small-signal response H(s), s = j f / fc (no bilinear warping).
    These are the circuit-analysis transfer functions each model is built from."""
    r = res / 100
    if m == 2:
        k = 4.3 * r ** 1.3
        return (lambda s: 1 / ((1 + s) ** 4 + k)) if st == "l" else (lambda s: s ** 4 / ((1 + s) ** 4 + k))
    if m == 1:
        K = 0.05 + 2.03 * r ** 1.1
        return (lambda s: 1 / (s * s + (2 - K) * s + 1)) if st == "l" else (lambda s: s * s / (s * s + (2 - K) * s + 1))
    if m == 3:
        K = 1 + 2.1 * r ** 1.3
        return (lambda s: K / (s * s + (3 - K) * s + 1)) if st == "l" else (lambda s: K * s * (s + 2) / (s * s + (3 - K) * s + 1))
    if m == 4:
        Rr = 20 ** (-r)
        return (lambda s: 1 / (s * s + 2 * Rr * s + 1)) if st == "l" else (lambda s: s * s / (s * s + 2 * Rr * s + 1))
    if m == 5:
        kd = 17.0 * 1.15 * r ** 1.8
        c = 0.1494 + 1.2648 * np.sqrt(min(kd / 17.0, 1.06))
        def h(s):
            hh = core303(s * c)
            sh = s * fc / 8.0
            return hh / (1 + kd * hh * sh / (sh + 1))
        return h
    return None


# ---------------------------------------------------------------- F1 digital vs analogue (warping)
rows = []
fig, axes = plt.subplots(2, 3, figsize=(12, 6))
for (st, mods) in (("l", [1, 2, 3, 4, 5]), ("h", [1, 2, 3, 4])):
    for m in mods:
        for sr in (44100, 96000):
            for ovs in (0, 1):
                for fc in ((1000, 5000, 12000) if st == "l" else (100, 500, 1500)):
                    for res in (0, 60):
                        p = stage(st, m, cut=fc, res=res, slope=1 if m in (2, 5) else 0, comp=0, ovs_sel=ovs)
                        if st == "h":
                            p.update(h_slope=1 if m == 2 else 0)
                        f, H = tf(p, sr=sr, n=1 << 16, level=2e-4)
                        Href = analog_ref(st, m, res, fc)(1j * f / fc)
                        band = (f >= 20) & (f <= min(20000, 0.9 * sr / 2)) & (db(Href) > -30)
                        err = np.abs(db(H[band]) - db(Href[band]))
                        ia = np.argmax(np.abs(Href) * (f <= 20000)); idg = np.argmax(np.abs(H) * (f <= 20000))
                        pk_err = float(db(np.abs(H[idg])) - db(np.abs(Href[ia])))
                        pk_cents = float(1200 * np.log2(max(f[idg], 1) / max(f[ia], 1)))
                        # worst error in the top octave below 20 kHz (where warping lives)
                        top = (f >= 10000) & (f <= min(20000, 0.9 * sr / 2)) & (db(Href) > -30)
                        et = float(np.max(np.abs(db(H[top]) - db(Href[top])))) if top.any() else 0.0
                        ph = np.angle(H[band] / Href[band], deg=True)
                        rows.append(dict(stage=st, model=(LP_MODELS if st == "l" else HP_MODELS)[m], sr=sr, ovs=["1x", "2x"][ovs],
                                         fc=fc, res=res, p99_db_where_analogue_gt_m30=round(float(np.percentile(err, 99)), 3),
                                         peak_gain_err_db=round(pk_err, 2), peak_freq_err_cents=round(pk_cents, 1),
                                         stopband_excess_db_at_0p9nyq=round(float(db(np.abs(H[np.argmin(np.abs(f - min(20000, 0.9 * sr / 2)))])) - db(np.abs(Href[np.argmin(np.abs(f - min(20000, 0.9 * sr / 2)))]))), 1),
                                         max_db_10k_20k=round(et, 2), max_phase_deg_where_analogue_gt_m30=round(float(np.max(np.abs(ph))), 1)))
                        if st == "l" and res == 60 and fc == 12000 and sr == 44100 and m in (2, 4, 1):
                            ax = axes[0, [2, 4, 1].index(m)]
                            ax.semilogx(f, db(Href), color="k", lw=1, ls="--", label="analogue H(s)" if ovs == 0 else None)
                            ax.semilogx(f, db(H), color=COL[ovs], lw=1.2, label=f"engine {['1x', '2x'][ovs]}")
                            ax.set_xlim(1000, 22050); ax.set_ylim(-40, 15)
                            ax.set_title(f"{LP_MODELS[m]} LP, fc 12 kHz, res 60 %, 44.1 kHz"); ax.legend()
                            ax2 = axes[1, [2, 4, 1].index(m)]
                            ax2.semilogx(f, np.degrees(np.unwrap(np.angle(H))), color=COL[ovs], lw=1.2, label=f"engine {['1x', '2x'][ovs]} (2x includes the half-band IIR phase)")
                            if ovs == 0:
                                ax2.semilogx(f, np.degrees(np.unwrap(np.angle(Href))), color="k", lw=1, ls="--", label="analogue")
                            ax2.set_xlim(1000, 22050); ax2.set_title("phase, unwrapped (deg)"); ax2.legend()
for ax in axes.ravel():
    ax.set_xlabel("Hz")
savefig(fig, "f1_digital_vs_analogue_hf")
R["F1_digital_vs_analogue"] = rows

# ---------------------------------------------------------------- F2 resonance peak vs knob (small signal)
rows = []
fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
for m in range(6):
    pk, pf = [], []
    for res in (0, 25, 50, 75, 90, 100):
        f, H = tf(stage("l", m, cut=1000, res=res, slope=1 if m in (0, 2, 5) else 0, comp=0), n=1 << 16, level=1e-4)
        sel = (f > 200) & (f < 5000)
        i = np.argmax(np.abs(H[sel])); g0 = np.abs(H[(f > 20) & (f < 40)]).mean()
        pk.append(float(db(np.abs(H[sel][i]) / g0))); pf.append(float(f[sel][i]))
        rows.append(dict(model=LP_MODELS[m], res=res, peak_db_rel_dc=round(pk[-1], 2), peak_hz=round(pf[-1], 1)))
    ax[0].plot([0, 25, 50, 75, 90, 100], pk, "o-", color=COL[m], label=LP_MODELS[m])
    ax[1].plot([0, 25, 50, 75, 90, 100], 1200 * np.log2(np.array(pf) / 1000), "o-", color=COL[m], label=LP_MODELS[m])
ax[0].set_title("small-signal resonance peak above passband (fc 1 kHz, Comp 0)"); ax[0].set_xlabel("Resonance %"); ax[0].set_ylabel("dB")
ax[1].set_title("frequency of the response maximum, cents from fc"); ax[1].set_xlabel("Resonance %"); ax[1].legend()
savefig(fig, "f2_resonance_peak")
R["F2_resonance_peak_small_signal"] = rows

# ---------------------------------------------------------------- F3 self-oscillation pitch & level
rows = []
sr = 48000
for st, mods in (("l", range(6)), ("h", range(5))):
    for m in mods:
        for fc, ovs in [(f_, o_) for f_ in ((100, 1000, 4000, 8000, 12000, 16000) if st == "l" else (100, 500, 1500)) for o_ in (0, 1)]:
            # excite at 0.5 s, after cutoff / resonance smoothing has settled (the engine has no
            # internal noise, so an exactly silent filter never starts oscillating on its own)
            x = np.zeros(int(3.0 * sr)); x[int(0.5 * sr):int(0.51 * sr)] = np.random.default_rng(3).standard_normal(int(0.01 * sr)) * 0.05
            y = run(x, stage(st, m, cut=fc, res=100, slope=1 if (st == "l" and m in (0, 2, 5)) else 0, comp=0, ovs_sel=ovs), sr)[:, 0]
            seg = y[int(2.0 * sr):]
            rms = float(np.sqrt(np.mean(seg ** 2)))
            osc = rms > 1e-3
            f0 = None
            if osc:
                F = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); fr = np.fft.rfftfreq(len(seg), 1 / sr)
                k = np.argmax(F);
                if 0 < k < len(F) - 1:   # parabolic interpolation
                    a, b, c = np.log(F[k - 1:k + 2] + 1e-30); k = k + 0.5 * (a - c) / (a - 2 * b + c)
                f0 = float(k * sr / len(seg))
            rows.append(dict(stage=st, model=(LP_MODELS if st == "l" else HP_MODELS)[m], fc=fc, ovs=["1x", "2x"][ovs], oscillates=bool(osc),
                             bounded=bool(np.max(np.abs(seg)) < 4.0), peak_dbfs=round(float(db(np.max(np.abs(seg)) + 1e-300)), 1),
                             osc_hz=None if f0 is None else round(f0, 1),
                             cents_from_fc=None if f0 is None else round(1200 * np.log2(f0 / fc), 1),
                             rms_dbfs=round(float(db(rms)), 1)))
R["F3_self_oscillation"] = rows

# ---------------------------------------------------------------- F4 level-dependent distortion (drive 0)
rows = []
sr = 48000; f0 = 110.0
lv = [-40, -30, -20, -12, -6, 0]
fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), sharey=True)
for res, ax in zip((0, 80), axes):
    for m in range(6):
        t = []
        for L in lv:
            x = tone(f0, 1.2, sr, 10 ** (L / 20))
            y = run(x, stage("l", m, cut=2000, res=res, slope=1 if m in (0, 2, 5) else 0, comp=0), sr)[int(0.2 * sr):, 0]
            T, h, _ = thd(y, f0, sr)
            t.append(T)
            rows.append(dict(model=LP_MODELS[m], res=res, level_dbfs=L, thd_pct=round(100 * T, 4),
                             h2_dbc=round(float(db(h[1] / h[0])), 1), h3_dbc=round(float(db(h[2] / h[0])), 1)))
        ax.plot(lv, 100 * np.array(t), "o-", color=COL[m], label=LP_MODELS[m])
    ax.set_yscale("log"); ax.set_xlabel("input level dBFS (110 Hz sine)"); ax.set_title(f"THD, LPF fc 2 kHz, Drive 0, Res {res} %")
axes[0].set_ylabel("THD %"); axes[1].legend()
savefig(fig, "f4_thd_vs_level")
R["F4_thd_vs_level_drive0"] = rows

# resonance compression: peak gain at fc for a small and a large sine
rows = []
for m in range(6):
    g = []
    for L in (-40, -12):
        x = tone(1000.0, 1.0, sr, 10 ** (L / 20))
        y = run(x, stage("l", m, cut=1000, res=80, slope=1 if m in (0, 2, 5) else 0, comp=0), sr)[int(0.5 * sr):, 0]
        g.append(float(db(np.sqrt(2) * np.sqrt(np.mean(y ** 2)) / 10 ** (L / 20))))
    rows.append(dict(model=LP_MODELS[m], gain_at_fc_minus40=round(g[0], 2), gain_at_fc_minus12=round(g[1], 2),
                     compression_db=round(g[0] - g[1], 2)))
R["F4b_resonance_level_dependence"] = rows

# ---------------------------------------------------------------- F5 aliasing (oversampling off / on)
rows = []
sr = 48000; f0 = 5003.0
for m in range(6):
    for ovs in (0, 1):
        x = tone(f0, 1.5, sr, 0.5)
        y = run(x, stage("l", m, cut=16000, res=50, drive=60, slope=1 if m in (0, 2, 5) else 0, comp=0, ovs_sel=ovs), sr)[int(0.5 * sr):int(1.5 * sr), 0]
        T, h, resid = thd(y, f0, sr, nh=4)
        rows.append(dict(model=LP_MODELS[m], ovs=["1x", "2x"][ovs], thd_pct=round(100 * T, 2),
                         alias_dbc=round(float(db(resid / h[0])), 1)))
# measurement floor: the same analysis on a clean digital sine
_, hh, rr = thd(tone(f0, 1.0, sr, 0.5), f0, sr, nh=4)
rows.append(dict(model="(measurement floor: clean sine)", ovs="-", thd_pct=0, alias_dbc=round(float(db(rr / hh[0])), 1)))
R["F5_aliasing"] = rows
# alias spectrum picture for the ladder
fig, ax = plt.subplots(figsize=(10, 3.2))
for ovs in (0, 1):
    x = tone(f0, 1.0, sr, 0.5)
    y = run(x, stage("l", 2, cut=16000, res=50, drive=60, slope=1, comp=0, ovs_sel=ovs), sr)[int(0.3 * sr):, 0]
    fr = np.fft.rfftfreq(len(y), 1 / sr); A = np.abs(np.fft.rfft(y * np.blackman(len(y)))) / (np.sum(np.blackman(len(y))) / 2)
    ax.plot(fr, db(A), color=COL[ovs], lw=0.7, label=["oversampling 1x (default)", "2x"][ovs])
for h in range(1, 5):
    ax.axvline(f0 * h if f0 * h < sr / 2 else 0, color="k", lw=0.4, ls=":")
ax.set_xlim(0, sr / 2); ax.set_ylim(-160, 0); ax.set_xlabel("Hz"); ax.set_ylabel("dBFS")
ax.set_title("Ladder LP, 5003 Hz sine at -6 dBFS, Drive 60 %, Res 50 %, fc 16 kHz, 48 kHz: everything off the dotted harmonic lines is aliasing")
ax.legend(); savefig(fig, "f5_alias_spectrum_ladder")

# ---------------------------------------------------------------- F6 stability under rapid modulation
rows = []
sr = 48000
rng = np.random.default_rng(7)
x = rng.standard_normal(2 * sr) * 0.5
for st, mods in (("l", range(6)), ("h", range(5))):
    for m in mods:
        ev = []
        for i in range(0, 2 * sr, 480):            # 100 Hz square modulation of cutoff, extreme span
            hi = (i // 480) % 2
            ev.append((i, f"{st}_cut", (12000 if hi else 100) if st == "l" else (2000 if hi else 20)))
        for ovs in (0, 1):
            p = stage(st, m, res=100, drive=100, slope=3, comp=100, ovs_sel=ovs)
            y = run(x, p, sr, events=ev)
            rows.append(dict(stage=st, model=(LP_MODELS if st == "l" else HP_MODELS)[m], ovs=["1x", "2x"][ovs],
                             finite=bool(np.all(np.isfinite(y))), peak_dbfs=round(float(db(np.max(np.abs(y)))), 1)))
R["F6_rapid_modulation_extremes"] = rows

# ---------------------------------------------------------------- F7 measured skirt slopes per slope setting
rows = []
for st, mods in (("l", range(6)), ("h", range(5))):
    for m in mods:
        for sl in range(4):
            fc = 1000 if st == "l" else 400
            f, H = tf(stage(st, m, cut=fc, res=0, slope=sl, comp=0), n=1 << 16, level=1e-4)
            if st == "l":
                fa, fb = 4 * fc, 8 * fc
            else:
                fa, fb = fc / 4, fc / 2
            ga = db(np.abs(H[np.argmin(np.abs(f - fa))])); gb = db(np.abs(H[np.argmin(np.abs(f - fb))]))
            slope = (gb - ga) if st == "l" else (gb - ga)
            rows.append(dict(stage=st, model=(LP_MODELS if st == "l" else HP_MODELS)[m], setting=[12, 24, 36, 48][sl],
                             measured_db_per_oct=round(float(abs(slope)), 1)))
R["F7_skirt_slopes"] = rows

# ---------------------------------------------------------------- F8 sample-rate consistency (mid band)
rows = []
for m in range(6):
    ref = None
    for sr in (44100, 48000, 96000):
        f, H = tf(stage("l", m, cut=1000, res=60, slope=1 if m in (0, 2, 5) else 0, comp=0), sr=sr, n=1 << 16, level=1e-4)
        g = np.interp(np.geomspace(50, 8000, 200), f, db(H))
        if ref is None:
            ref = g
        ok = ref > ref.max() - 30
        rows.append(dict(model=LP_MODELS[m], sr=sr, max_dev_db_vs_44k1_where_gt_m30=round(float(np.max(np.abs(g - ref)[ok])), 3)))
R["F8_samplerate_consistency"] = rows

# ---------------------------------------------------------------- B1 BPF: centre and width vs controls
rows = []
for bm in range(5):
    for arch in range(3):
        p = base(b_on=1, b_model=bm, b_arch=arch, b_freq=1000, b_bw=1, b_q=2, b_res=0, b_comp=100)
        f, H = tf(p, n=1 << 16, level=1e-4)
        A = db(H); i = np.argmax(A); pk = A[i]
        above = np.where(A >= pk - 3)[0]
        lo, hi = f[above[0]], f[above[-1]]
        rows.append(dict(model=["SEM", "Steiner-Parker", "K35/MS-20", "ARP 2600", "EMS VCS3"][bm], arch=["SVF", "CASC", "MULTI"][arch],
                         centre_hz=round(float(f[i]), 1), bw_oct_3db=round(float(np.log2(hi / lo)), 2), peak_db=round(float(pk), 2)))
R["B1_bpf_centre_width"] = rows

save("filters", R)
print("filters: done", {k: len(v) for k, v in R.items()})

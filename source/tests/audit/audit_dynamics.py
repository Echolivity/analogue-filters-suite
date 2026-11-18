#!/usr/bin/env python3
"""Compressor, tube and signal-chain diagnostics. Read-only: runs the shipped engine and
writes docs/dsp-audit/data/dynamics.json + plots."""
import numpy as np
from common import run, base, db, tone, harmonics, thd, save, savefig, plt, COL

R = {}
SR = 48000


def dyn(**kw):
    return base(**kw)


def steady_out_level(x_amp, f, p, dur=1.5, meas=(1.0, 1.5)):
    x = tone(f, dur, SR, x_amp)
    y = run(x, p, SR)[int(meas[0] * SR):int(meas[1] * SR), 0]
    return float(np.sqrt(2 * np.mean(y ** 2)))


# ================================================================== C1 static transfer curves
levels = np.arange(-40, 7, 3)
rows, curves = [], {}
CONF = {
    "OPTO COMP PR40": dict(o_on=1, o_pr=40, o_mode=0),
    "OPTO COMP PR70": dict(o_on=1, o_pr=70, o_mode=0),
    "OPTO LIMIT PR70": dict(o_on=1, o_pr=70, o_mode=1),
}
for r_i, ratio in enumerate([1.5, 2, 3, 4, 6, 10, "inf"]):
    for knee, kn in ((0, "HARD"), (2, "SOFT")):
        if kn == "SOFT" and ratio not in (4,):
            continue
        for typ in (0, 1):
            if typ == 1 and ratio not in (4, "inf"):
                continue
            CONF[f"VCA {ratio}:1 {kn} {['NEW', 'OLD'][typ]}"] = dict(v_on=1, v_thr=-20, v_ratio=r_i, v_knee=knee, v_type=typ, v_att=3, v_rel=0.1)
for name, kw in CONF.items():
    out = []
    for L in levels:
        a = 10 ** (L / 20)
        out.append(db(steady_out_level(a, 1000.0, dyn(**kw), dur=6.0 if "OPTO" in name else 1.5,
                                       meas=(5.0, 6.0) if "OPTO" in name else (1.0, 1.5))))
    out = np.array(out)
    curves[name] = out
    hi = levels >= -6
    slope = np.polyfit(levels[hi], out[hi], 1)[0]
    gr = levels - out
    thr_meas = None
    above = np.where(gr > 1.0)[0]
    if len(above):
        thr_meas = float(levels[above[0]])
    rows.append(dict(config=name, measured_ratio_top_8dB=round(float(1 / max(slope, 1e-6)), 2),
                     slope_top=round(float(slope), 3), first_level_with_gr_gt_1dB=thr_meas,
                     gr_at_0dBFS=round(float(gr[np.argmin(np.abs(levels))]), 2)))
R["C1_static_curves"] = rows
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for i, (n, c) in enumerate(curves.items()):
    a = ax[0] if "OPTO" in n else ax[1]
    if "OPTO" in n or ("HARD NEW" in n) or "SOFT" in n:
        a.plot(levels, c, "-", lw=1.2, label=n)
for a in ax:
    a.plot(levels, levels, "k:", lw=0.8); a.set_xlabel("input dBFS (1 kHz sine, steady state)"); a.set_ylabel("output dBFS"); a.legend()
ax[0].set_title("OPTO static curves (5-6 s after onset)"); ax[1].set_title("VCA static curves, threshold -20 dBFS")
savefig(fig, "c1_static_curves")

# ================================================================== C2 VCA attack / release vs nominal
rows = []
att_nom = [0.03, 0.1, 0.3, 1, 3, 10, 30]
for ai, an in enumerate(att_nom):
    n = int(1.5 * SR)
    x = tone(1000.0, 1.5, SR, 1.0)
    env = np.where(np.arange(n) < SR, 10 ** (-30 / 20), 10 ** (0 / 20))
    _, M = run(x * env, dyn(v_on=1, v_thr=-20, v_ratio=6, v_att=ai, v_rel=0.3, v_knee=0), SR, meters=True)
    g = M[:, 7] * 30.0                  # VCA GR meter (dB)
    seg = g[SR:SR + int(0.3 * SR)]
    fin = seg[-1]
    t63 = np.argmax(seg >= 0.632 * fin) / SR * 1000
    rows.append(dict(setting_ms=an, final_gr_db=round(float(fin), 2), time_to_63pct_ms=round(float(t63), 3)))
R["C2a_vca_attack"] = rows
rows = []
for rel in (0.05, 0.3, 1.0, 3.0):
    n = int((1 + 6) * SR)
    x = tone(1000.0, 7.0, SR, 1.0)
    env = np.where(np.arange(n) < SR, 1.0, 10 ** (-40 / 20))
    _, M = run(x * env, dyn(v_on=1, v_thr=-20, v_ratio=6, v_att=2, v_rel=rel), SR, meters=True)
    g = M[:, 7] * 30.0
    g0 = g[SR - 10]; seg = g[SR:]
    t37 = np.argmax(seg <= 0.368 * g0) / SR
    rows.append(dict(setting_s=rel, gr_before_db=round(float(g0), 2), time_to_37pct_s=round(float(t37), 3)))
R["C2b_vca_release"] = rows

# ================================================================== C3 OPTO program-dependent release + attack
rows = []
fig, ax = plt.subplots(figsize=(10, 3.6))
for k, burst in enumerate((0.2, 1.0, 5.0, 20.0)):
    tail = 12.0
    n = int((0.5 + burst + tail) * SR)
    x = tone(1000.0, n / SR, SR, 1.0)
    env = np.zeros(n); env[int(0.5 * SR):int((0.5 + burst) * SR)] = 10 ** (-3 / 20)
    env[int((0.5 + burst) * SR):] = 10 ** (-40 / 20)      # quiet signal keeps the detector honest
    _, M = run(x * env, dyn(o_on=1, o_pr=80, o_mode=0), SR, meters=True)
    g = M[:, 4] * 30.0
    i0 = int((0.5 + burst) * SR)
    g0 = g[i0 - 1]; seg = g[i0:]
    t50 = np.argmax(seg <= 0.5 * g0) / SR
    t90 = np.argmax(seg <= 0.1 * g0) / SR if np.any(seg <= 0.1 * g0) else None
    rows.append(dict(burst_s=burst, gr_at_end_db=round(float(g0), 2), release_to_50pct_s=round(float(t50), 3),
                     release_to_90pct_recovered_s=None if t90 is None else round(float(t90), 2)))
    tt = np.arange(len(seg)) / SR
    ax.plot(tt, seg, color=COL[k], label=f"after a {burst:g} s burst")
ax.set_xlim(0, 12); ax.set_xlabel("s after the burst ends"); ax.set_ylabel("gain reduction dB")
ax.set_title("OPTO release after bursts of different length (same level): program-dependent memory"); ax.legend()
savefig(fig, "c3_opto_release_memory")
R["C3a_opto_release_memory"] = rows
rows = []
for f0 in (100.0, 1000.0, 5000.0):
    n = int(2 * SR)
    x = tone(f0, 2.0, SR, 1.0)
    env = np.where(np.arange(n) < SR, 10 ** (-40 / 20), 10 ** (-3 / 20))
    _, M = run(x * env, dyn(o_on=1, o_pr=80, o_mode=0), SR, meters=True)
    g = M[:, 4] * 30.0
    seg = g[SR:SR + int(0.5 * SR)]; fin = g[SR + int(0.9 * SR)]
    t63 = np.argmax(seg >= 0.632 * fin) / SR * 1000
    rows.append(dict(freq_hz=f0, gr_final_db=round(float(fin), 2), attack_to_63pct_ms=round(float(t63), 2)))
R["C3b_opto_attack_vs_frequency"] = rows
# level dependence of the opto ratio (programme dependence of the static curve)
R["C3c_opto_note"] = "see C1: static curve slope varies with level (soft knee); ratio is not constant"

# ================================================================== C4 THRUST: detector-only and its frequency response
rows = []
x = tone(200.0, 1.5, SR, 10 ** (-40 / 20))
ys = [run(x, dyn(v_on=1, v_thr=0, v_ratio=3, v_thrust=t), SR) for t in range(3)]
rows.append(dict(test="input below threshold: output identical across NORM/MED/LOUD (THRUST not in audio path)",
                 max_abs_diff=float(max(np.max(np.abs(ys[1] - ys[0])), np.max(np.abs(ys[2] - ys[0]))))))
R["C4a_thrust_detector_only"] = rows
rows = []
freqs = [50, 100, 200, 500, 1000, 2000, 5000, 10000]
fig, ax = plt.subplots(figsize=(7, 3.4))
for t in range(3):
    g = []
    for f0 in freqs:
        x = tone(float(f0), 1.2, SR, 10 ** (-6 / 20))
        _, M = run(x, dyn(v_on=1, v_thr=-30, v_ratio=6, v_att=2, v_rel=0.1, v_thrust=t), SR, meters=True)
        g.append(float(np.mean(M[int(0.8 * SR):, 7] * 30)))
    rows.append(dict(thrust=["NORM", "MED", "LOUD"][t], **{f"gr_db_{f}": round(v, 2) for f, v in zip(freqs, g)}))
    ax.semilogx(freqs, g, "o-", color=COL[t], label=["NORM", "MED", "LOUD"][t])
ax.set_xlabel("sine frequency (Hz), -6 dBFS"); ax.set_ylabel("VCA gain reduction dB"); ax.legend()
ax.set_title("THRUST: gain reduction vs frequency at equal level (detector sensitivity)")
savefig(fig, "c4_thrust_detector_response")
R["C4b_thrust_gr_vs_frequency"] = rows

# ================================================================== C5 stereo link
rows = []
n = int(1.5 * SR)
xl = tone(1000.0, 1.5, SR, 1.0)
x = np.stack([xl, 0.1 * tone(1000.0, 1.5, SR, 1.0)], 1)
for mod, kw in (("VCA", lambda L: dict(v_on=1, v_thr=-20, v_ratio=6, v_link=L)), ("OPTO", lambda L: dict(o_on=1, o_pr=70, o_link=L))):
    for L in (0, 50, 100):
        y = run(x, dyn(**kw(L)), SR)[int(1.0 * SR):]
        gl = db(np.sqrt(2 * np.mean(y[:, 0] ** 2)) / 1.0); gr = db(np.sqrt(2 * np.mean(y[:, 1] ** 2)) / 0.1)
        rows.append(dict(module=mod, link_pct=L, gain_left_db=round(float(gl), 2), gain_right_db=round(float(gr), 2)))
R["C5_stereo_link"] = rows

# ================================================================== C6 compressor distortion (gain modulation)
rows = []
for name, kw in (("VCA 0.03ms/0.05s 10:1", dict(v_on=1, v_thr=-30, v_ratio=5, v_att=0, v_rel=0.05)),
                 ("VCA 30ms/0.3s 4:1", dict(v_on=1, v_thr=-30, v_ratio=3, v_att=6, v_rel=0.3)),
                 ("OPTO COMP PR80", dict(o_on=1, o_pr=80, o_mode=0)),
                 ("OPTO LIMIT PR80", dict(o_on=1, o_pr=80, o_mode=1))):
    for f0 in (50.0, 1000.0):
        x = tone(f0, 3.0, SR, 10 ** (-6 / 20))
        y = run(x, dyn(**kw), SR)[int(2.0 * SR):int(3.0 * SR), 0]
        T, h, _ = thd(y, f0, SR)
        rows.append(dict(config=name, freq_hz=f0, thd_pct=round(100 * T, 4), h2_dbc=round(float(db(h[1] / h[0])), 1),
                         h3_dbc=round(float(db(h[2] / h[0])), 1)))
R["C6_compressor_distortion"] = rows

# ================================================================== T1 tube transfer curve, THD vs drive / level / bias
rows = []
fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
# static transfer: the implemented curve evaluated directly from the source formula
# (dyn.py f_tsh / f_tube and the drive / bias mapping in emit_controls), Auto gain off.
# A slow sine through the engine is not used here because the stage's 8 Hz DC blocker
# and tone filter add phase that turns the plot into a loop.
def f_tsh(v):
    return np.where(v > 0, np.tanh(1.25 * v) * 0.8, np.tanh(0.85 * v) * 1.176470588235)
xs = np.linspace(-1, 1, 801)
for k, (drv, bias) in enumerate(((30, 20), (70, 20), (70, -60), (100, 100))):
    D = 2 ** (5.98 * drv / 100); kk = 0.3 * D; b = 0.6 * bias / 100
    tb = np.tanh((1.25 if b > 0 else 0.85) * b); ib = 1 / (1 - tb * tb)
    ko = 1 / (0.3 * np.sqrt(D))
    ax[0].plot(xs, (f_tsh(xs * kk + b) - f_tsh(b)) * ib * ko, lw=1.2, color=COL[k], label=f"Drive {drv} %, Bias {bias}")
ax[0].plot(xs, xs, "k:", lw=0.7)
for bias, col in ((20, COL[0]), (-60, COL[1]), (100, COL[2])):
    t2, t3, tt = [], [], []
    drives = [0, 20, 40, 60, 80, 100]
    for drv in drives:
        x = tone(200.0, 1.2, SR, 10 ** (-12 / 20))
        y = run(x, dyn(t_on=1, t_drive=drv, t_bias=bias, t_auto=1), SR)[int(0.2 * SR):int(1.2 * SR), 0]
        T, h, resid = thd(y, 200.0, SR)
        tt.append(100 * T); t2.append(db(h[1] / h[0])); t3.append(db(h[2] / h[0]))
        rows.append(dict(drive=drv, bias=bias, level_dbfs=-12, thd_pct=round(100 * T, 3), h2_dbc=round(float(t2[-1]), 1),
                         h3_dbc=round(float(t3[-1]), 1), even_minus_odd_db=round(float(t2[-1] - t3[-1]), 1)))
    ax[1].plot(drives, tt, "o-", color=col, label=f"Bias {bias}")
    ax[2].plot(drives, np.array(t2) - np.array(t3), "o-", color=col, label=f"Bias {bias}")
ax[1].set_yscale("log"); ax[1].set_title("THD vs Drive (200 Hz, -12 dBFS)"); ax[1].set_xlabel("Drive %"); ax[1].legend()
ax[2].set_title("H2 - H3 (dB): even vs odd balance"); ax[2].set_xlabel("Drive %"); ax[2].legend()
savefig(fig, "t1_tube_transfer_thd")
R["T1_tube_thd_vs_drive_bias"] = rows

rows = []
for L in (-30, -20, -12, -6, 0):
    x = tone(200.0, 1.2, SR, 10 ** (L / 20))
    y = run(x, dyn(t_on=1, t_drive=50, t_bias=20, t_auto=1), SR)[int(0.2 * SR):int(1.2 * SR), 0]
    T, h, _ = thd(y, 200.0, SR)
    rows.append(dict(level_dbfs=L, thd_pct=round(100 * T, 3), h2_dbc=round(float(db(h[1] / h[0])), 1), h3_dbc=round(float(db(h[2] / h[0])), 1)))
R["T2_tube_thd_vs_level"] = rows

# frequency dependence of distortion (a static shaper should give the same THD at all f below the tone filter)
rows = []
for f0 in (50.0, 200.0, 1000.0, 3000.0):
    x = tone(f0, 1.2, SR, 10 ** (-12 / 20))
    y = run(x, dyn(t_on=1, t_drive=60, t_bias=20, t_auto=1, t_tone=20000), SR)[int(0.2 * SR):int(1.2 * SR), 0]
    T, h, resid = thd(y, f0, SR)
    rows.append(dict(freq_hz=f0, thd_pct=round(100 * T, 3), h2_dbc=round(float(db(h[1] / h[0])), 1), h3_dbc=round(float(db(h[2] / h[0])), 1)))
R["T3_tube_thd_vs_frequency"] = rows

# memory: is distortion after a loud burst different from before (dynamic operating point)?
n = int(3 * SR)
x = tone(200.0, 3.0, SR, 1.0)
env = np.full(n, 10 ** (-20 / 20)); env[SR:2 * SR] = 1.0
y = run(x * env, dyn(t_on=1, t_drive=60, t_bias=20, t_auto=1), SR)[:, 0]
Tb, hb, _ = thd(y[int(0.5 * SR):SR], 200.0, SR); Ta, ha, _ = thd(y[2 * SR + 10:int(2.5 * SR) + 10], 200.0, SR)
R["T4_tube_memory"] = dict(thd_before_burst_pct=round(100 * Tb, 4), thd_right_after_burst_pct=round(100 * Ta, 4),
                           h2_before_dbc=round(float(db(hb[1] / hb[0])), 2), h2_after_dbc=round(float(db(ha[1] / ha[0])), 2),
                           note="identical within numerical noise means no bias shift / grid-current memory (static shaper)")

# IMD (SMPTE 60 Hz + 7 kHz, 4:1)
rows = []
t = np.arange(int(1.2 * SR)) / SR
for name, kw in (("TUBE drive 60", dict(t_on=1, t_drive=60, t_bias=20, t_auto=1)),
                 ("Ladder LPF fc 12k drive 60", dict(l_on=1, l_model=2, l_cut=12000, l_drive=60, l_comp=100)),
                 ("VCA 0.03ms/0.05s", dict(v_on=1, v_thr=-30, v_ratio=5, v_att=0, v_rel=0.05))):
    x = 0.8 * (0.4 * np.sin(2 * np.pi * 60 * t) + 0.1 * np.sin(2 * np.pi * 7000 * t)) * 10 ** (-6 / 20) / 0.5
    y = run(x, base(**kw), SR)[int(0.2 * SR):, 0]
    f, A = np.fft.rfftfreq(len(y), 1 / SR), np.abs(np.fft.rfft(y * np.blackman(len(y))))
    def at(fr):
        k = int(round(fr / (f[1] - f[0]))); return np.sqrt(np.sum(A[k - 3:k + 4] ** 2))
    side = np.sqrt(sum(at(7000 + s * 60) ** 2 + at(7000 - s * 60) ** 2 for s in (1, 2, 3)))
    rows.append(dict(config=name, smpte_imd_pct=round(float(100 * side / at(7000)), 3)))
R["T5_imd_smpte"] = rows

# aliasing of the tube (internally 2x)
rows = []
for drv in (60, 100):
    x = tone(5003.0, 1.5, SR, 0.5)
    y = run(x, dyn(t_on=1, t_drive=drv, t_bias=20, t_auto=1, t_tone=20000), SR)[int(0.5 * SR):int(1.5 * SR), 0]
    T, h, resid = thd(y, 5003.0, SR, nh=4)
    rows.append(dict(drive=drv, thd_pct=round(100 * T, 2), alias_dbc=round(float(db(resid / h[0])), 1)))
R["T6_tube_aliasing"] = rows

# ================================================================== S1 chain order: same settings, six orders
rows = []
rng = np.random.default_rng(11)
n = int(4 * SR)
tt = np.arange(n) / SR
# programme-like test: 110 Hz tone with a 4 Hz amplitude envelope (transients) + pink-ish noise
sig = (0.5 * np.sin(2 * np.pi * 110 * tt) * (0.3 + 0.7 * (np.sin(2 * np.pi * 2 * tt) > 0))) + 0.02 * rng.standard_normal(n)
kw = dict(t_on=1, t_drive=60, t_bias=20, t_auto=1, o_on=1, o_pr=60, v_on=1, v_thr=-24, v_ratio=3, v_att=3, v_rel=0.2)
for o, nm in enumerate(["TUBE>OPTO>VCA", "TUBE>VCA>OPTO", "OPTO>TUBE>VCA", "OPTO>VCA>TUBE", "VCA>TUBE>OPTO", "VCA>OPTO>TUBE"]):
    y, M = run(sig, base(c_order=o, **kw), SR, meters=True)
    y = y[SR:, 0]; M = M[SR:]
    x1 = tone(110.0, 1.2, SR, 0.5)
    ys = run(x1, base(c_order=o, **kw), SR)[int(0.2 * SR):int(1.2 * SR), 0]
    T, h, _ = thd(ys, 110.0, SR)
    rows.append(dict(order=nm, out_rms_dbfs=round(float(db(np.sqrt(np.mean(y ** 2)))), 2),
                     crest_db=round(float(db(np.max(np.abs(y)) / np.sqrt(np.mean(y ** 2)))), 2),
                     mean_opto_gr_db=round(float(np.mean(M[:, 4] * 30)), 2), mean_vca_gr_db=round(float(np.mean(M[:, 7] * 30)), 2),
                     steady_sine_thd_pct=round(100 * T, 3), h2_dbc=round(float(db(h[1] / h[0])), 1), h3_dbc=round(float(db(h[2] / h[0])), 1)))
R["S1_chain_order_effects"] = rows

# ================================================================== P1 CPU (ns / sample, this machine) for representative setups
rows = []
x = np.random.default_rng(1).standard_normal(int(2 * SR)) * 0.2
for name, kw in (("bypass (all off)", base()),
                 ("LPF ladder 24 dB", base(l_on=1, l_model=2, l_cut=1000, l_res=50, l_slope=1)),
                 ("LPF+HPF ladder/K35, 1x", base(l_on=1, l_model=2, l_cut=1000, l_slope=1, h_on=1, h_model=1, h_cut=200)),
                 ("LPF+HPF, 2x oversampling", base(l_on=1, l_model=2, l_cut=1000, l_slope=1, h_on=1, h_model=1, h_cut=200, ovs_sel=1)),
                 ("LPF+HPF 48 dB + BPF MULTI, 2x", base(l_on=1, l_model=2, l_cut=1000, l_slope=3, h_on=1, h_model=1, h_cut=200, h_slope=3, b_on=1, b_arch=2, ovs_sel=1)),
                 ("full chain: filters 2x + tube + opto + VCA + gate", base(l_on=1, l_model=2, l_cut=1000, l_slope=1, h_on=1, h_model=1, h_cut=200, ovs_sel=1, b_on=1, t_on=1, o_on=1, v_on=1, g_on=1))):
    best = min(run(x, kw, SR, ns=True)[1] for _ in range(3))
    rows.append(dict(config=name, ns_per_stereo_sample=round(best, 1), pct_of_one_core_at_48k=round(best * 48000 / 1e9 * 100, 2)))
R["P1_cpu_offline_harness"] = rows

save("dynamics", R)
print("dynamics: done", {k: (len(v) if isinstance(v, list) else 1) for k, v in R.items()})

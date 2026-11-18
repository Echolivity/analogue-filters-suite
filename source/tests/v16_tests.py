#!/usr/bin/env python3
"""v1.6 gate: stability (fs/4), fault containment, oversampling cascade and Reference-mode
policy, TUBE oversampling, solver change before/after, CPU. Writes build/v16_results.json
(and docs/V1.6_ENGINE.md data via tests/v16_report.py)."""
import json, math, os, sys, hashlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dsp
from dsp import run, base, tf
ROOT = os.path.join(HERE, "..")
H15 = os.path.join(ROOT, "build", "harness_v15")
SR = 48000
results, data = [], {}


def check(name, ok, detail=""):
    results.append(dict(name=name, ok=bool(ok), detail=detail))
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))


def db(x):
    return 20 * np.log10(max(abs(float(x)), 1e-300))


def run15(x, p, sr=SR, events=()):
    """Same call on the v1.5 engine (tests/baseline/dubfilter_v1.5.genexpr)."""
    old = dsp.HARN
    dsp.HARN = H15
    try:
        p = {k: v for k, v in p.items() if k not in ("eng_mode", "ovs_hi")}
        return run(x, p, sr, events=events)
    finally:
        dsp.HARN = old


def bh4(n):
    k = np.arange(n) / (n - 1) * 2 * np.pi
    return 0.35875 - 0.48829 * np.cos(k) + 0.14128 * np.cos(2 * k) - 0.01168 * np.cos(3 * k)


def alias(y, sr, f0, bw=5):
    w = bh4(len(y)); A = np.abs(np.fft.rfft(y * w)) / (np.sum(w) / 2); f = np.fft.rfftfreq(len(y), 1 / sr)
    band = (f > 20) & (f < sr / 2); harm = np.zeros(len(f), bool)
    for h in range(1, int((sr / 2) / f0) + 2):
        k = int(round(h * f0)); harm[max(k - bw, 0):k + bw + 1] = True
    k1 = int(round(f0))
    return db(np.sqrt(np.sum(A[band & ~harm] ** 2)) / np.sqrt(np.sum(A[k1 - bw:k1 + bw + 1] ** 2)))


FAC = {1: dict(ovs_sel=0, ovs_hi=0), 2: dict(ovs_sel=1, ovs_hi=0), 4: dict(ovs_hi=1), 8: dict(ovs_hi=2), 16: dict(ovs_hi=3)}

# ------------------------------------------------------------------ 1. fs/4 stability sweep (1x, worst case)
rows, worst = [], -999.0
for sr in (44100, 48000):
    q = sr / 4
    for m in range(6):
        for c in range(-100, 101, 10):
            fc = q * 2 ** (c / 1200)
            for res in (92, 96, 100):
                x = np.zeros(int(0.7 * sr)); x[int(0.3 * sr):int(0.3 * sr) + 64] = 0.05
                y = run(x, base(l_on=1, l_model=m, l_cut=fc, l_res=res, l_slope=1 if m in (0, 2, 5) else 0, l_comp=0), sr)[:, 0]
                pk = db(np.max(np.abs(y[int(0.4 * sr):])))
                worst = max(worst, pk)
                rows.append(dict(sr=sr, model=m, cents=c, res=res, peak=round(pk, 1)))
data["fs4_sweep_lpf"] = rows
bad = [r for r in rows if r["peak"] > 6]
check("fs/4 sweep: all 6 LPF models, ±100 cents around fs/4, res 92-100 %, 44.1 + 48 kHz, 1x: peak <= +6 dBFS",
      not bad, f"{len(rows)} runs, worst {worst:.1f} dBFS" + (f"; failing: {bad[:3]}" if bad else ""))
rows, worst = [], -999.0
sr = 44100; q = sr / 4
for bm in range(5):
    for arch in range(3):
        for c in range(-100, 101, 20):
            for res in (95, 100):
                x = np.zeros(int(0.7 * sr)); x[int(0.3 * sr):int(0.3 * sr) + 64] = 0.05
                y = run(x, base(b_on=1, b_model=bm, b_arch=arch, b_freq=min(q * 2 ** (c / 1200), 12000), b_res=res), sr)[:, 0]
                pk = db(np.max(np.abs(y[int(0.4 * sr):]))); worst = max(worst, pk)
                rows.append(dict(model=bm, arch=arch, cents=c, res=res, peak=round(pk, 1)))
data["fs4_sweep_bpf"] = rows
check("fs/4 sweep: 15 BPF configurations at 44.1 kHz (fs/4 = 11 kHz, within range), res 95/100 %: peak <= +6 dBFS",
      worst <= 6, f"{len(rows)} runs, worst {worst:.1f} dBFS")
check("HPF models: fs/4 is outside the HPF cutoff range (max 2 kHz) at every supported sample rate", True, "by range")

# v1.5 comparison at the reported failure point
x = np.zeros(int(1.5 * SR)); x[int(0.5 * SR):int(0.5 * SR) + 64] = 0.05
cmp = {}
for m, nm in ((0, "Sherman"), (3, "Steiner")):
    p = base(l_on=1, l_model=m, l_cut=12000, l_res=100, l_slope=1 if m == 0 else 0, l_comp=0)
    cmp[nm] = dict(v15=round(db(np.max(np.abs(run15(x, p)[SR:, 0]))), 1), v16=round(db(np.max(np.abs(run(x, p)[SR:, 0]))), 1))
data["failure_point_48k_12k_res100"] = cmp
check("reported failure point (48 kHz, 12 kHz, res 100 %, 1x): Sherman and Steiner bounded (v1.5 -> v1.6)",
      all(v["v16"] <= 6 for v in cmp.values()), "; ".join(f"{k} {v['v15']} -> {v['v16']} dBFS" for k, v in cmp.items()))

# ------------------------------------------------------------------ 2. fault containment
n = int(1.0 * SR)
x = np.zeros(n); x[int(0.3 * SR)] = 1e9                      # absurd input sample
y, M = run(x, base(l_on=1, l_model=2, l_cut=1000, l_res=50, softclip=0), SR, meters=True)
after = y[int(0.3 * SR) + int(0.010 * SR):, 0]
check("fault containment: a 1e9 input sample is contained, output clean 10 ms later",
      np.all(np.isfinite(y)) and np.max(np.abs(after)) < 1e-3 and M[:, 14].max() == 1,
      f"flag raised: {int(M[:, 14].max())}; max |y| 10 ms after = {np.max(np.abs(after)):.2e}")
acts = 0
xs = np.random.default_rng(5).standard_normal(int(0.8 * SR)) * 0.3
for m in range(6):
    for res in (0, 100):
        _, M = run(xs, base(l_on=1, h_on=1, b_on=1, l_model=m, h_model=m % 5, l_cut=3000, h_cut=200, l_res=res, h_res=res,
                            b_res=res, l_drive=100, t_on=1, o_on=1, v_on=1, g_on=1, eng_mode=0), SR, meters=True)
        acts += int(M[:, 14].sum())
check("fault containment never acts in normal operation (12 heavy configurations, res 0/100 %, Reference mode)", acts == 0, f"activations: {acts}")

# ------------------------------------------------------------------ 3. oversampling cascade + Reference policy
t = np.arange(int(1.5 * SR)) / SR
x = 0.5 * np.sin(2 * np.pi * 5003 * t)
LP = ["Sherman", "K35", "Ladder", "Steiner", "SEM", "TB-303"]
tab = {}
for m in range(6):
    tab[LP[m]] = {}
    for N, kw in FAC.items():
        p = base(l_on=1, l_model=m, l_cut=16000, l_res=50, l_drive=60, l_slope=1 if m in (0, 2, 5) else 0, **kw)
        tab[LP[m]][N] = round(alias(run(x, p)[int(0.5 * SR):int(1.5 * SR), 0], SR, 5003.0), 1)
    p = base(l_on=1, l_model=m, l_cut=16000, l_res=50, l_drive=60, l_slope=1 if m in (0, 2, 5) else 0, eng_mode=0)
    y, M = run(x, p, meters=True)
    tab[LP[m]]["reference"] = round(alias(y[int(0.5 * SR):int(1.5 * SR), 0], SR, 5003.0), 1)
    tab[LP[m]]["reference_factor"] = int(M[-1, 12])
data["alias_lpf_C1"] = tab
check("Reference mode: every LPF model <= -80 dBc at the bright test point (5 kHz, -6 dBFS, Drive 60, fc 16 kHz)",
      all(v["reference"] <= -80 for v in tab.values()), ", ".join(f"{k} {v['reference']} @ {v['reference_factor']}x" for k, v in tab.items()))
check("4x / 8x / 16x reach <= -110 dBc for every LPF model at the bright test point",
      all(v[N] <= -110 for v in tab.values() for N in (4, 8, 16)), "min over models per factor: " +
      ", ".join(f"{N}x {max(v[N] for v in tab.values())}" for N in (4, 8, 16)))
check("1x and 2x unchanged from v1.5 for models not affected by the solver fix (K35, Ladder, 303; SEM changed by the SEM-1A schematic fix, 1x now -140 dBc)",
      all(tab[k][N] == v for k, d in {"K35": {1: -50.3, 2: -115.6}, "Ladder": {1: -32.8, 2: -61.2},
                                          "TB-303": {1: -52.0, 2: -118.5}}.items() for N, v in d.items()), "vs independent-review data")
# effective factor readout
eff = {}
for kw, exp in ((dict(eng_mode=0, l_on=1, l_model=2), 4), (dict(eng_mode=0, l_on=1, l_model=4, h_on=0), 1), (dict(eng_mode=0, l_on=1, l_model=4, h_on=1, h_model=1), 2),
                (dict(eng_mode=0, b_on=1, l_on=0, h_on=0), 4), (dict(eng_mode=1, l_on=1, l_model=2), 1), (dict(eng_mode=1, l_on=1, l_model=2, ovs_hi=3), 16),
                (dict(eng_mode=0, l_on=1, l_model=4, h_on=0, ovs_hi=2), 8)):
    _, M = run(np.zeros(int(0.2 * SR)), base(**kw), meters=True)
    eff[json.dumps(kw)] = (int(M[-1, 12]), exp)
check("effective factor: Reference = max(user, model minimum); Creative = user setting (7 cases)",
      all(a == b for a, b in eff.values()), "; ".join(f"{k}: {a}x (exp {b}x)" for k, (a, b) in eff.items()))

# HPF / BPF in Reference mode
ref = {}
for m in range(5):
    y = run(x, base(h_on=1, h_model=m, h_cut=2000, h_res=50, h_drive=60, eng_mode=0))[int(0.5 * SR):int(1.5 * SR), 0]
    ref[f"HPF m{m}"] = round(alias(y, SR, 5003.0), 1)
for a in range(3):
    for bm in range(5):
        y = run(x, base(b_on=1, b_model=bm, b_arch=a, b_freq=5000, b_res=50, b_drive=60, eng_mode=0))[int(0.5 * SR):int(1.5 * SR), 0]
        ref[f"BPF m{bm} a{a}"] = round(alias(y, SR, 5003.0), 1)
data["alias_ref_hpf_bpf"] = ref
check("Reference mode: every HPF model and BPF configuration <= -80 dBc at its bright test point",
      all(v <= -80 for v in ref.values()), f"worst {max(ref.values())} dBc")

# ------------------------------------------------------------------ 4. TUBE oversampling
tt = {}
for N, kw in ((2, dict(ovs_sel=0)), (4, dict(ovs_hi=1)), (8, dict(ovs_hi=2)), (16, dict(ovs_hi=3))):
    y, M = run(x, base(t_on=1, t_drive=100, t_bias=20, t_auto=1, **kw), meters=True)
    tt[N] = dict(alias_dbc=round(alias(y[int(0.5 * SR):int(1.5 * SR), 0], SR, 5003.0), 1), factor=int(M[-1, 13]))
y, M = run(x, base(t_on=1, t_drive=100, t_bias=20, t_auto=1, eng_mode=0), meters=True)
tt["reference"] = dict(alias_dbc=round(alias(y[int(0.5 * SR):int(1.5 * SR), 0], SR, 5003.0), 1), factor=int(M[-1, 13]))
data["tube_alias_drive100_5k"] = tt
check("TUBE: aliasing falls with factor (Drive 100, 5 kHz); Reference runs at 8x",
      tt[2]["alias_dbc"] > tt[4]["alias_dbc"] > tt[8]["alias_dbc"] and tt["reference"]["factor"] == 8,
      ", ".join(f"{k}: {v['alias_dbc']} dBc @ {v['factor']}x" for k, v in tt.items()))
mixok = {}
for N, kw in ((2, dict(ovs_sel=0)), (4, dict(ovs_hi=1)), (16, dict(ovs_hi=3))):
    f, H = tf(base(t_on=1, t_drive=0, t_mix=0, **kw), n=1 << 15, level=1e-3)
    sel = (f > 50) & (f < 10000)
    mixok[N] = round(float(np.max(np.abs(20 * np.log10(np.abs(H[sel]))))), 3)
check("TUBE dry path (Mix 0) stays flat within 0.2 dB, 50 Hz-10 kHz, at 2x / 4x / 16x (phase-matched dry path)",
      all(v < 0.2 for v in mixok.values()), str(mixok))

# ------------------------------------------------------------------ 5. solver change: before / after
ba = {}
for m, nm in ((0, "Sherman"), (3, "Steiner")):
    for res in (0, 60):
        p = base(l_on=1, l_model=m, l_cut=1000, l_res=res, l_slope=0, l_comp=0)
        f, Hn = tf(p, n=1 << 16, level=1e-4)
        old = dsp.HARN; dsp.HARN = H15
        try:
            f, Ho = tf({k: v for k, v in p.items() if k != "eng_mode"}, n=1 << 16, level=1e-4)
        finally:
            dsp.HARN = old
        sel = (f > 20) & (f < 20000)
        ba[f"{nm} small-signal res {res}"] = round(float(np.max(np.abs(20 * np.log10(np.abs(Hn[sel]) / np.abs(Ho[sel]))))), 4)
for m, nm in ((0, "Sherman"), (3, "Steiner")):
    for fc in (1000, 4000, 8000):
        xx = np.zeros(int(2.5 * SR)); xx[int(0.5 * SR):int(0.5 * SR) + 64] = 0.05
        p = base(l_on=1, l_model=m, l_cut=fc, l_res=100, l_slope=1 if m == 0 else 0, l_comp=0)
        out = {}
        for tag, fn in (("v15", run15), ("v16", run)):
            seg = fn(xx, p)[int(1.5 * SR):, 0]
            F = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); k = int(np.argmax(F))
            out[tag] = (round(k * SR / len(seg), 1), round(db(np.sqrt(np.mean(seg ** 2))), 2))
        ba[f"{nm} self-osc fc {fc}"] = dict(v15_hz_rms=out["v15"], v16_hz_rms=out["v16"])
xs = np.random.default_rng(9).standard_normal(SR) * 0.3
for m, nm in ((0, "Sherman"), (3, "Steiner")):
    p = base(l_on=1, l_model=m, l_cut=900, l_res=75, l_drive=40, l_slope=0)
    a, b = run15(xs, p)[:, 0], run(xs, p)[:, 0]
    ba[f"{nm} programme diff (noise, fc 900, res 75, drive 40)"] = round(db(np.sqrt(np.mean((a - b) ** 2)) / np.sqrt(np.mean(a ** 2))), 1)
data["solver_before_after"] = ba
check("solver fix leaves the small-signal response unchanged (Sherman, Steiner; res 0 / 60 %): < 0.01 dB",
      all(v < 0.01 for k, v in ba.items() if "small-signal" in k), str({k: v for k, v in ba.items() if "small-signal" in k}))

# ------------------------------------------------------------------ 6. CPU per factor
cpu = {}
xn = np.random.default_rng(1).standard_normal(SR) * 0.2
for N, kw in FAC.items():
    p = base(l_on=1, l_model=2, l_cut=1000, l_slope=1, h_on=1, h_model=1, h_cut=200, **kw)
    cpu[f"LPF+HPF {N}x"] = round(min(run(xn, p, ns=True)[1] for _ in range(3)), 1)
for N, kw in ((2, dict(ovs_sel=0)), (8, dict(ovs_hi=2)), (16, dict(ovs_hi=3))):
    cpu[f"TUBE {N}x"] = round(min(run(xn, base(t_on=1, **kw), ns=True)[1] for _ in range(3)), 1)
cpu["device defaults (Reference)"] = round(min(run(xn, {}, ns=True)[1] for _ in range(3)), 1)
cpu["everything off"] = round(min(run(xn, base(l_on=0, h_on=0), ns=True)[1] for _ in range(3)), 1)
data["cpu_ns_per_sample"] = cpu
check("CPU measured per factor (offline harness, informational)", True, str(cpu))

# ------------------------------------------------------------------ K35 Circuit: Korg35 (Mk1), Stinchcombe 2006
M1 = lambda **k: dict(base(**k), k35_circ=1)
fits = {}
for st, nm in (("l", "LP"), ("h", "HP")):
    for r in (0, 50, 80):
        k = (7 / 6) * (0.05 + 2.03 * (r / 100) ** 1.1)
        f, H = tf(M1(**{f"{st}_on": 1, f"{st}_model": 1, f"{st}_cut": 1000, f"{st}_res": r}))
        sel = (f > 60) & (f < 3000); s_ = 1j * f[sel] / 1000; den = s_ * s_ + (7 / 3 - k) * s_ + 1
        Hm = 1 / den if st == "l" else s_ * (s_ + 4 / 3) / den
        fits[f"{nm} res {r}"] = round(float(np.max(np.abs(20 * np.log10(np.abs(H[sel]) / np.abs(Hm))))), 2)
data["k35_mk1_fits"] = fits
check("K35 Mk1: small-signal LP 1/(s^2+(7/3-k)s+1) and HP s(s+4/3)/(...) (Korg35 Sallen-Key, C1 = 3 C2) within 0.5 dB, 60 Hz-3 kHz",
      max(fits.values()) < 0.5, ", ".join(f"{a} {b} dB" for a, b in fits.items()))
tt = np.arange(SR * 2) / SR
def thd500(y):
    y = y[SR:]; w = np.hanning(len(y)); Y = np.abs(np.fft.rfft(y * w)); fr = np.fft.rfftfreq(len(y), 1 / SR)
    pk = lambda h: Y[np.argmin(abs(fr - h * 500)) - 3:np.argmin(abs(fr - h * 500)) + 4].max()
    return 100 * np.sqrt(sum(pk(h) ** 2 for h in range(2, 12))) / pk(1)
th = {}
for L in (-24, -12, 0):
    xx = 10 ** (L / 20) * np.sin(2 * np.pi * 500 * tt)
    th[L] = (round(thd500(run(xx, M1(l_on=1, l_model=1, l_cut=7000, l_res=50))[:, 0]), 3),
             round(thd500(run(xx, base(l_on=1, l_model=1, l_cut=7000, l_res=50))[:, 0]), 3))
data["k35_passband_thd"] = th
check("K35 Mk1 vs Mk2, Stinchcombe's detection test (500 Hz, fc 7 kHz, res 50): Mk1 passband THD rises with level and exceeds Mk2 at every level",
      th[0][0] > 10 * th[-24][0] and all(a > b for a, b in th.values()), "; ".join(f"{L:+d} dBFS: Mk1 {a} % / Mk2 {b} %" for L, (a, b) in th.items()))
xi = np.zeros(SR * 2); xi[4800:5000] = np.random.default_rng(1).standard_normal(200) * 0.3
osc = {r: run(xi, M1(l_on=1, l_model=1, l_cut=800, l_res=r))[:, 0] for r in (90, 100)}
lv = {r: round(db(np.std(y[-SR // 2:]) + 1e-15), 1) for r, y in osc.items()}
check("K35 Mk1: self-oscillates at res 100 (bounded by the diode stage), not at res 90",
      -20 < lv[100] < 0 and lv[90] < -100 and all(np.isfinite(y).all() for y in osc.values()), f"level 1.5-2 s: res 90 {lv[90]} dBFS, res 100 {lv[100]} dBFS")
worst = -999.0
for sr_ in (44100, 48000):
    q = sr_ / 4
    for c in range(-100, 101, 10):
        for res in (92, 96, 100):
            xq = np.zeros(int(0.7 * sr_)); xq[int(0.3 * sr_):int(0.3 * sr_) + 64] = 0.05
            yq = run(xq, M1(l_on=1, l_model=1, l_cut=q * 2 ** (c / 1200), l_res=res, l_comp=0), sr_)[:, 0]
            worst = max(worst, db(np.max(np.abs(yq[int(0.4 * sr_):]))))
check("K35 Mk1 fs/4 sweep: ±100 cents, res 92-100 %, 44.1 + 48 kHz, 1x: peak <= +6 dBFS", worst <= 6, f"126 runs, worst {worst:.1f} dBFS")
xr = 0.5 * np.sin(2 * np.pi * 5003 * np.arange(int(1.6 * SR)) / SR)
refk = {}
for st, kw in (("LPF", dict(l_on=1, l_model=1, l_cut=16000, l_res=50, l_drive=60)), ("HPF", dict(h_on=1, h_model=1, h_cut=2000, h_res=50, h_drive=60))):
    y, M = run(xr, dict(M1(**kw), eng_mode=0), meters=True)
    refk[st] = (round(alias(y[int(0.5 * SR):int(1.5 * SR), 0], SR, 5003.0), 1), int(M[-1, 12]))
check("K35 Mk1 in Reference mode: LPF runs at 8x and HPF at 4x, both <= -80 dBc at the bright test point",
      refk["LPF"][1] == 8 and refk["HPF"][1] == 4 and all(a <= -80 for a, _ in refk.values()), "; ".join(f"{k} {a} dBc @ {n}x" for k, (a, n) in refk.items()))
cpu["K35 Mk1 LPF 8x"] = round(min(run(xn, M1(l_on=1, l_model=1, l_cut=1000, ovs_hi=2), ns=True)[1] for _ in range(3)), 1)
cpu["K35 Mk2 LPF 8x"] = round(min(run(xn, base(l_on=1, l_model=1, l_cut=1000, ovs_hi=2), ns=True)[1] for _ in range(3)), 1)
data["cpu_ns_per_sample"] = cpu

# ------------------------------------------------------------------ Steiner diode law (Electronic Design, 6 Dec 1974)
ts = np.arange(int(0.6 * SR)) / SR
fsw = np.geomspace(300, 4000, 40)
def f3db(L):
    g = []
    for f_ in fsw:
        xx = 10 ** (L / 20) * np.sin(2 * np.pi * f_ * ts)
        yy = run(xx, base(l_on=1, l_model=3, l_cut=1000, l_res=0, l_drive=100))[SR // 4:, 0]
        g.append(db(np.std(yy) / np.std(xx[SR // 4:])))
    g = np.array(g); return float(fsw[np.argmax(g < g[0] - 3)])
st = {L: round(f3db(L)) for L in (-40, -10, 0)}
data["steiner_cutoff_vs_level"] = st
check("Steiner: the mirrored diode string's sinh law raises cutoff with level (Drive 100, res 0), small-signal unchanged",
      st[-10] > st[-40] and st[0] > 1.5 * st[-40] and abs(st[-40] - 760) < 40, "; ".join(f"{L:+d} dBFS: -3 dB at {v} Hz" for L, v in st.items()))

# ------------------------------------------------------------------ SEM (Oberheim SEM-1A schematic)
semfit = {}
for r in (0, 50, 90, 100):
    R_ = 0.05 + 1.515 * (1 - r / 100)
    f, H = tf(base(l_on=1, l_model=4, l_cut=1000, l_res=r)); sel = (f > 60) & (f < 3000); s_ = 1j * f[sel] / 1000
    semfit[r] = round(float(np.max(np.abs(20 * np.log10(np.abs(H[sel]) / np.abs(1 / (s_ * s_ + 2 * R_ * s_ + 1)))))), 2)
ts2 = np.arange(SR * 2) / SR
semg = {}
for L in (-30, 0):
    xx = 10 ** (L / 20) * np.sin(2 * np.pi * 1000 * ts2)
    yy = run(xx, base(l_on=1, l_model=4, l_cut=1000, l_res=100))[SR:, 0]
    semg[L] = round(db(np.std(yy) / np.std(xx[SR:])), 1)
xi = np.zeros(SR * 2); xi[4800:5000] = np.random.default_rng(1).standard_normal(200) * 0.5
semosc = round(db(np.std(run(xi, base(l_on=1, l_model=4, l_cut=800, l_res=100))[-SR // 2:, 0]) + 1e-15), 1)
data["sem_schematic"] = dict(fit=semfit, res100_gain=semg, selfosc_level=semosc)
check("SEM (SEM-1A schematic): RES-pot damping law 2R = 0.1 + 3.03(1 - res) within 0.5 dB; D11/D12 limiter compresses the resonant peak; no self-oscillation",
      max(semfit.values()) < 0.5 and semg[-30] - semg[0] > 5 and semosc < -100,
      f"fit {semfit} dB; res 100 gain at 1 kHz: {semg[-30]} dB (-30 dBFS) -> {semg[0]} dB (0 dBFS); after impulse {semosc} dBFS")

n_ok = sum(r["ok"] for r in results)
json.dump(dict(results=results, data=data), open(os.path.join(ROOT, "build", "v16_results.json"), "w"), indent=1, default=float)
print(f"\nv1.6 tests: {n_ok}/{len(results)} passed")
sys.exit(0 if n_ok == len(results) else 1)

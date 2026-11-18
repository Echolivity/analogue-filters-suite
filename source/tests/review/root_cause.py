#!/usr/bin/env python3
"""Independent root-cause analysis of the two critical stability findings.
1. Validate the replicas against the shipped engine (same excitation).
2. Map the stability boundary (fc x res x fs) for engine and replica.
3. Test hypotheses: lagged secant vs implicit solve; damping law; sample rate.
4. Test persistence: does the device recover after divergence?
Writes docs/independent-review/data/root_cause.json."""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, os.path.join(HERE, "..", "audit"))
from dsp import run, base
from replica import Sherman, Steiner
OUT = os.path.join(HERE, "..", "..", "..", "docs", "independent-review", "data")
R = {}


def db(x):
    return float(20 * np.log10(max(abs(x), 1e-300)))


def engine(model, fc, res, sr, ovs=0, n_sec=2.0, softclip=0, extra=None, x=None):
    if x is None:
        x = np.zeros(int(n_sec * sr)); x[int(0.5 * sr):int(0.5 * sr) + 64] = 0.05
    p = base(l_on=1, l_model=model, l_cut=fc, l_res=res, l_slope=1 if model in (0, 2, 5) else 0, l_comp=0,
             ovs_sel=ovs, softclip=softclip)
    if extra:
        p.update(extra)
    return run(x, p, sr)[:, 0]


# ---------------------------------------------------------------- 1. replica validity
sr, fc = 48000, 1000.0
g = math.tan(math.pi * fc / sr)
x = np.zeros(int(1.0 * sr)); x[int(0.5 * sr):int(0.5 * sr) + 64] = 0.05
y_eng = engine(0, fc, 80, sr, x=x)
sh = Sherman(g, 0.8)
d = 0.25; osc = 1 / d                                     # drive 0, comp 0 -> engine gains (build_genexpr.py:508-510)
y_rep = np.array([osc * sh.step(d * v) for v in x])
seg = slice(int(0.5 * sr), int(0.9 * sr))
R["replica_validation_sherman"] = dict(case="Sherman LP fc 1 kHz res 80 % 48 kHz, 64-sample 0.05 pulse at 0.5 s",
                                       max_abs_err=float(np.max(np.abs(y_eng[seg] - y_rep[seg]))),
                                       peak=float(np.max(np.abs(y_eng[seg]))))
y_eng = engine(3, fc, 80, sr, x=x)
st = Steiner(g, 0.8)
kd = 1 / steiner_kd if (steiner_kd := (1 + 2.1 * 0.8 ** 1.3) ** 0) else 1   # comp 0 -> kd = 1 (:325)
y_rep = np.array([osc * st.step(d * v) for v in x])
R["replica_validation_steiner"] = dict(case="Steiner LP fc 1 kHz res 80 % 48 kHz",
                                       max_abs_err=float(np.max(np.abs(y_eng[seg] - y_rep[seg]))),
                                       peak=float(np.max(np.abs(y_eng[seg]))))

# ---------------------------------------------------------------- 2. stability maps (engine)
rows = []
for model, name in ((0, "Sherman"), (3, "Steiner")):
    for sr in (44100, 48000, 96000):
        for ovs in (0, 1):
            for fc in (6000, 8000, 10000, 11000, 12000, 13000, 14000, 16000, 18000):
                if fc > 0.45 * sr * (2 if ovs else 1):
                    continue
                for res in (90, 95, 100):
                    y = engine(model, fc, res, sr, ovs=ovs, n_sec=1.5)
                    pk = np.max(np.abs(y[int(1.0 * sr):]))
                    rows.append(dict(model=name, sr=sr, ovs=["1x", "2x"][ovs], fc=fc, res=res,
                                     peak_dbfs=round(db(pk), 1), finite=bool(np.all(np.isfinite(y)))))
R["stability_map_engine"] = rows

# ---------------------------------------------------------------- 3. hypotheses on the replica
def rep_peak(cls, g, r, iters=0, n=48000, **kw):
    m = cls(g, r, iters=iters, **kw)
    pk, tr = 0.0, []
    for i in range(n):
        v = 0.05 * 0.25 if i < 64 else 0.0
        y = m.step(v) * 4
        if not math.isfinite(y) or abs(y) > 1e30:
            return float("inf"), m, i
        pk = max(pk, abs(y)) if i > n // 2 else pk
    return pk, m, n


hyp = []
for fs in (48000, 96000, 192000):
    gg = math.tan(math.pi * 12000 / fs)
    for iters in (0, 1, 3, 8):
        pk, m, n_end = rep_peak(Sherman, gg, 1.0, iters=iters)
        hyp.append(dict(model="Sherman", fs=fs, g=round(gg, 4), solver="lagged secant (production)" if iters == 0 else f"fixed-point x{iters}",
                        peak_dbfs=None if not math.isfinite(pk) else round(db(pk), 1), diverged_at_sample=None if math.isfinite(pk) else n_end))
    pk, m, n_end = rep_peak(Sherman, gg, 1.0, damp_law="tg")
    hyp.append(dict(model="Sherman", fs=fs, g=round(gg, 4), solver="lagged secant, tanh damping law instead of algebraic",
                    peak_dbfs=None if not math.isfinite(pk) else round(db(pk), 1), diverged_at_sample=None if math.isfinite(pk) else n_end))
    for iters in (0, 1, 3, 8):
        pk, m, n_end = rep_peak(Steiner, gg, 1.0, iters=iters)
        hyp.append(dict(model="Steiner", fs=fs, g=round(gg, 4), solver="lagged secant (production)" if iters == 0 else f"fixed-point x{iters}",
                        peak_dbfs=None if not math.isfinite(pk) else round(db(pk), 1), diverged_at_sample=None if math.isfinite(pk) else n_end))
R["hypotheses_replica_fc12k_res100"] = hyp

# trace of the divergence mechanism (Sherman, production solver, 48 kHz, fc 12 kHz)
gg = math.tan(math.pi * 12000 / 48000)
m = Sherman(gg, 1.0)
ys = []
for i in range(4000):
    ys.append(m.step(0.05 * 0.25 if i < 64 else 0.0))
    if abs(ys[-1]) > 1e12:
        break
Rb = np.array(m.Rb_trace)
ys = np.array(ys)
k = min(len(ys) - 1, int(np.argmax(np.abs(ys) > 10)) if np.any(np.abs(ys) > 10) else len(ys) - 1)
R["sherman_trace"] = dict(g=gg, Rt_small_signal=round(1 - (1 - (0.8 * 0 - 0.08)) * 1, 4),
                          samples_until_abs_y_gt_10=int(k), samples_until_1e12=len(ys),
                          Rb_last_16=[round(v, 4) for v in Rb[-16:]], y_last_8=[float(f"{v:.4g}") for v in ys[-8:]],
                          fraction_of_last_200_samples_with_negative_damping=round(float(np.mean(Rb[-200:] < 0)), 3))

# frozen-coefficient stability of the TPT SVF: digital pole radius vs R at g = 1 (12 kHz @ 48 kHz)
def svf_pole_radius(g, Rr):
    # TPT SVF = bilinear map of s^2 + 2R s + 1 (s normalised): poles z = (1 + s g)/(1 - s g) with s = (-R +- sqrt(R^2-1))
    roots = np.roots([1, 2 * Rr, 1])
    return float(max(abs((1 + r * g) / (1 - r * g)) for r in roots))
R["svf_frozen_pole_radius_g1"] = {str(Rr): round(svf_pole_radius(1.0, Rr), 4) for Rr in (-0.08, -0.04, 0.0, 0.1, 1.0)}

# ---------------------------------------------------------------- 4. persistence / recovery in the device configuration
sr = 48000
n = int(4 * sr)
x = np.zeros(n); x[int(0.5 * sr):int(0.5 * sr) + 64] = 0.05
x[int(3 * sr):] = 0.1 * np.sin(2 * np.pi * 220 * np.arange(n - int(3 * sr)) / sr)   # music returns at 3 s
ev = [(int(2.0 * sr), "l_res", 0), (int(2.0 * sr), "l_cut", 1000)]                  # user turns resonance down at 2 s
p = base(l_on=1, l_model=0, l_cut=12000, l_res=100, l_slope=1, l_comp=0, softclip=1)   # device defaults: soft clip ON
y = run(x, p, sr, events=ev)[:, 0]
R["persistence_device_defaults"] = dict(
    note="Sherman LP, 1x, 48 kHz, fc 12 kHz, res 100 %, soft clip ON; at 2 s res -> 0 and fc -> 1 kHz; a 220 Hz tone from 3 s",
    peak_1_to_2s_dbfs=round(db(np.max(np.abs(y[sr:2 * sr]))), 2),
    rms_3_5_to_4s_dbfs=round(db(np.sqrt(np.mean(y[int(3.5 * sr):] ** 2))), 2),
    expected_rms_if_recovered_dbfs=round(db(0.1 / np.sqrt(2)), 2))
y2 = run(x, base(l_on=1, l_model=3, l_cut=12000, l_res=100, l_slope=0, l_comp=0, softclip=1), sr, events=ev)[:, 0]
R["persistence_device_defaults_steiner"] = dict(
    peak_1_to_2s_dbfs=round(db(np.max(np.abs(y2[sr:2 * sr]))), 2),
    rms_3_5_to_4s_dbfs=round(db(np.sqrt(np.mean(y2[int(3.5 * sr):] ** 2))), 2))

json.dump(R, open(os.path.join(OUT, "root_cause.json"), "w"), indent=1)
print(json.dumps({k: (v if not isinstance(v, list) else f"{len(v)} rows") for k, v in R.items()}, indent=1)[:4000])

#!/usr/bin/env python3
"""Fault persistence and replica-agreement checks (diagnostics only).
Writes docs/independent-review/data/persistence.json."""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from dsp import run, base
from replica import Sherman
OUT = os.path.join(HERE, "..", "..", "..", "docs", "independent-review", "data", "persistence.json")
R = {}
sr = 48000; n = 12 * sr
x = 0.1 * np.sin(2 * np.pi * 220 * np.arange(n) / sr); x[:3 * sr] = 0; x[24000:24064] = 0.05
ev = [(2 * sr, "l_res", 0), (2 * sr, "l_cut", 1000)]   # condition removed at 2 s; 220 Hz tone from 3 s
for sc in (1, 0):
    y = run(x, base(l_on=1, l_model=0, l_cut=12000, l_res=100, l_slope=1, l_comp=0, softclip=sc), sr, events=ev)[:, 0]
    R[f"softclip_{sc}"] = [dict(second=t, rms_dbfs=round(float(20 * np.log10(np.sqrt(np.mean(y[t * sr:(t + 1) * sr] ** 2)) + 1e-300)), 1),
                                mean=float(f"{y[t * sr:(t + 1) * sr].mean():.4g}")) for t in range(1, 8)]
R["expected_rms_dbfs_when_recovered"] = round(20 * math.log10(0.1 / math.sqrt(2)), 1)
fc = 1000.0
x2 = np.zeros(sr); x2[24000:24064] = 0.05
y = run(x2, base(l_on=1, l_model=0, l_cut=fc, l_res=80, l_slope=1, l_comp=0), sr)[:, 0]
sh = Sherman(math.tan(math.pi * fc / sr), 0.8)
yr = np.array([4 * sh.step(0.25 * v) for v in x2])
s = slice(24000, 40000)
R["replica_agreement"] = dict(first_5_abs_err=[float(f"{abs(v):.3g}") for v in (y[s] - yr[s])[:5]],
                              correlation=round(float(np.corrcoef(y[s], yr[s])[0, 1]), 5),
                              amplitude_ratio=round(float(np.dot(y[s], yr[s]) / np.dot(yr[s], yr[s])), 5))
json.dump(R, open(OUT, "w"), indent=1)
print(json.dumps(R, indent=1))

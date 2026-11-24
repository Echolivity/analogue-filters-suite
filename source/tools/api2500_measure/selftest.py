"""Self-test: render the pack through this project's own VCA model with the settings in RENDER_INSTRUCTIONS.txt,
analyse the renders, and check the analysis recovers the model's known values (threshold, ratio, knee widths
0/6/12 dB, the engine's THRUST curves, attack ordering, release, link). Needs the built harness (./build.sh).
Usage: python3 selftest.py [work_dir]"""
import os, sys, subprocess, tempfile
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "..", "tests"), os.path.join(HERE, "..", "..", "src")]
from dsp import run, base
import analyse as AN

W = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
pack, rend = os.path.join(W, "pack"), os.path.join(W, "renders")
os.makedirs(rend, exist_ok=True)
subprocess.run([sys.executable, os.path.join(HERE, "make_pack.py"), pack], check=True, capture_output=True)

# model settings: v_thr in dBFS (Waves mapping: dBFS = dBu - 22); index tables from dyn.py
RAT = {1.5: 0, 2: 1, 3: 2, 4: 3, 6: 4, 10: 5}
ATT = {0.03: 0, 1: 3, 30: 6}
B = dict(v_on=1, v_thr=-42, v_ratio=RAT[4], v_knee=0, v_att=ATT[1], v_rel=0.05, v_thrust=0, v_type=0, v_link=100, v_auto=0)
R = {"R01": dict(v_thr=0), "R02": dict(v_thr=-22), "R03": dict(v_thr=-22, v_knee=1), "R04": dict(v_thr=-22, v_knee=2),
     "R05": dict(v_thr=-22, v_type=1),
     "R06": dict(v_ratio=RAT[2], v_att=ATT[30], v_rel=0.2), "R07": dict(v_ratio=RAT[2], v_att=ATT[30], v_rel=0.2, v_thrust=1),
     "R08": dict(v_ratio=RAT[2], v_att=ATT[30], v_rel=0.2, v_thrust=2),
     "R09": dict(v_ratio=RAT[10], v_att=ATT[0.03]), "R10": dict(v_ratio=RAT[10], v_att=ATT[1]), "R11": dict(v_ratio=RAT[10], v_att=ATT[30]),
     "R12": dict(v_ratio=RAT[10], v_rel=0.5), "R14": dict(v_link=0), "R15": dict(v_link=100)}
for k, p in R.items():
    x, _ = sf.read(os.path.join(pack, AN.SRC[k]), always_2d=True)
    y = run(x, base(**{**B, **p}))
    sf.write(os.path.join(rend, f"{k}_model.wav"), y, 48000, subtype="FLOAT")
res = AN.analyse(pack, rend, os.path.join(rend, "analysis"))

ok = True
def check(name, cond, detail):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name + " - " + detail)

st = res["static"]
check("static: threshold -22 dBFS, ratio 4 recovered (HARD)", abs(st["R02"]["threshold_dbfs"] + 22) < 0.5 and abs(st["R02"]["ratio"] - 4) < 0.2,
      f"T {st['R02']['threshold_dbfs']}, R {st['R02']['ratio']}")
check("static: knee widths 0 / 6 / 12 dB recovered within 1.5 dB", all(abs(st[k]["knee_width_db"] - w) < 1.5 for k, w in (("R02", 0), ("R03", 6), ("R04", 12))),
      ", ".join(f"{st[k]['setting']} {st[k]['knee_width_db']}" for k in ("R02", "R03", "R04")))

# ground truth: the built engine's own THRUST curve via KEY LISTEN (the detector signal), relative to NORM
def kl(f, th):
    n = 48000
    x = 10 ** (-30 / 20) * np.sin(2 * np.pi * f * np.arange(n) / 48000)
    y = run(x, base(v_on=1, v_thr=0, v_thrust=th, key_listen=2))
    return 20 * np.log10(np.sqrt(np.mean(y[n // 2:, 0] ** 2)))
F = np.array(res["thrust_freqs"], float)
for m, th in (("LOUD", 2), ("MED", 1)):
    exp = np.array([kl(f, th) - kl(f, 0) for f in F]); exp -= exp[list(F).index(630)]
    got = np.array(res["thrust_curve_db"][m])
    e = np.abs(got - exp).max()
    check(f"THRUST {m}: detector curve recovered within 0.5 dB of the engine's KEY LISTEN curve (20 Hz-20 kHz)", e < 0.5, f"worst error {e:.2f} dB")
a = res["attack"]
check("attack: 63 % rise ordered with the setting (0.03 < 1 < 30 ms)", a["R09"]["t63_ms"] < a["R10"]["t63_ms"] < a["R11"]["t63_ms"],
      ", ".join(f"{v['setting_ms']} ms -> {v['t63_ms']} ms" for v in a.values()))
r = res["release"]["R12"]["bursts"]
check("release: fixed 500 ms gives a GR-independent 37 % time (model has no programme dependence)",
      max(b["t37_ms"] for b in r[1:]) - min(b["t37_ms"] for b in r[1:]) < 100, ", ".join(f"GR {b['gr_before_db']} -> {b['t37_ms']} ms" for b in r))
lk = res["link"]
check("link: IND passes no GR to Right; 100 % passes Left's GR", max(lk["IND"]["right_gr_db"]) < 0.3 and min(lk["HP"]["right_gr_db"]) > 3,
      f"IND max {max(lk['IND']['right_gr_db'])} dB, 100% min {min(lk['HP']['right_gr_db'])} dB")
print("SELFTEST", "OK" if ok else "FAILED", "- report:", os.path.join(rend, "analysis", "report.md"))
sys.exit(0 if ok else 1)

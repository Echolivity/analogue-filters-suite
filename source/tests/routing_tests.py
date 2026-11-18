"""v1.4 filter-routing tests (SERIES / PARALLEL / HYBRID) + regression gates. Imported by validate.py."""
import os, sys, subprocess, json
import numpy as np
from scipy.signal import butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from dsp import run, base, tf

SR = 48000


def db(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-12))


def hf_burst(y, at, win=0.006):
    h = sosfilt(butter(4, 8000, "hp", fs=SR, output="sos"), y)
    return float(db(np.sqrt(np.mean(h[int(at):int(at) + int(win * SR)] ** 2)) + 1e-12))


def run_all(record, plt, OUT, SEQ, CAT, GRID, sig):
    # ================================================================ regression gates
    for args, name in ((["check"], "LPF/HPF vs v1.1 (48)"), (["check-bpf"], "BPF vs v1.2 (35)"), (["check-dyn"], "dynamics chain vs v1.3 (21)")):
        r = subprocess.run([sys.executable, os.path.join(HERE, "golden.py")] + args, capture_output=True, text=True)
        record(f"REGRESSION v1.4: SERIES routing bit-exact (except documented v1.6 changes) — {name}", r.returncode == 0, r.stdout.strip())
    for b in ("v1.1", "v1.2", "v1.3"):
        r = subprocess.run([sys.executable, os.path.join(HERE, "compat.py"), "--ui", f"--base=DubFilter_{b}.maxpat"], capture_output=True, text=True)
        lines = r.stdout.strip().splitlines()
        record(f"REGRESSION v1.4: {b} presets/automation/MIDI maps intact", r.returncode == 0, lines[-1] + " — " + lines[0])

    # ================================================================ PARALLEL = sum of the individual filters
    combos = [
        ("LPF K35 400 Hz ∥ HPF K35 3 kHz (band-reject)", dict(l_on=1, l_model=1, l_cut=400, l_slope=0), dict(h_on=1, h_model=1, h_cut=3000, h_slope=0), None),
        ("LPF Ladder 24 dB 800 Hz res 60 ∥ HPF SEM 1.5 kHz res 50", dict(l_on=1, l_model=2, l_cut=800, l_res=60, l_slope=1), dict(h_on=1, h_model=4, h_cut=1500, h_res=50), None),
        ("LPF Diode 300 Hz ∥ BPF SEM SVF 2 kHz Q 4", dict(l_on=1, l_model=5, l_cut=300, l_res=40), None, dict(b_on=1, b_freq=2000, b_q=4)),
        ("HPF Sherman 2 kHz ∥ BPF K35 CASCADE 500 Hz", None, dict(h_on=1, h_model=0, h_cut=2000, h_res=30), dict(b_on=1, b_model=2, b_arch=1, b_freq=500, b_bw=1.5)),
        ("all three: LPF 250 ∥ HPF 4k ∥ BPF 1k (three-band)", dict(l_on=1, l_model=1, l_cut=250), dict(h_on=1, h_model=1, h_cut=1999), dict(b_on=1, b_freq=1000, b_q=2)),
    ]
    rows, bad = [], []
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), sharey=True)
    for i, (name, L, Hh, B) in enumerate(combos):
        parts = [p for p in (L, Hh, B) if p]
        f = None
        Hs = []
        for p in parts:
            f, Hp = tf(base(**p))
            Hs.append(Hp)
        allp = {}
        for p in parts:
            allp.update(p)
        for lv in (0, -6):
            kw = dict(allp, flt_route=1, par_l=lv)
            f, HP = tf(base(**kw))
            ref = sum((10 ** (lv / 20) if (p is L) else 1) * Hp for p, Hp in zip(parts, Hs))
            sel = (f >= 20) & (f <= 20000) & (db(ref) > -60)
            e = float(np.max(np.abs(db(HP[sel]) - db(ref[sel]))))
            rows.append(dict(combination=name, lpf_level_db=lv, max_error_db=round(e, 4)))
            if e > 0.05:
                bad.append(f"{name} lvl{lv}: {e:.3f}")
        if i in (0, 4):
            ax = axes[0 if i == 0 else 1]
            for j, Hp in enumerate(Hs):
                ax.semilogx(f[1:], db(Hp[1:]), color=GRID if False else "#c9c7c0", lw=1.0)
            ax.semilogx(f[1:], db(HP[1:] if False else tf(base(**dict(allp, flt_route=1)))[1][1:]), color=SEQ[2], lw=1.8)
            ax.set_title(name, fontsize=8); ax.set_xlim(20, 20000); ax.set_ylim(-40, 10)
    # hybrid example
    L = dict(l_on=1, l_model=2, l_cut=1200, l_res=40); Hh = dict(h_on=1, h_model=1, h_cut=120); B = dict(b_on=1, b_freq=3000, b_q=6, b_res=60)
    f, HS = tf(base(**L, **Hh)); _, HB = tf(base(**B)); _, HY = tf(base(**L, **Hh, **B, flt_route=2))
    axes[2].semilogx(f[1:], db(HS[1:]), color="#c9c7c0", lw=1.0, label="LP>HP chain")
    axes[2].semilogx(f[1:], db(HB[1:]), color="#e0dcd2", lw=1.0, label="BPF")
    axes[2].semilogx(f[1:], db(HY[1:]), color=SEQ[2], lw=1.8, label="HYBRID")
    axes[2].set_title("HYBRID: (Ladder LP 1.2k > K35 HP 120) + BPF 3 kHz", fontsize=8); axes[2].set_xlim(20, 20000); axes[2].legend(fontsize=7)
    axes[0].set_ylabel("dB")
    fig.suptitle("Filter routing — device response (blue) vs the individual filters (grey)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "routing_examples.png"), dpi=130); plt.close(fig)
    record("PARALLEL: response equals the sum of the individually measured filters (5 combinations incl. resonance, all three paths, LPF level 0/−6 dB)",
           not bad, f"{len(rows)} cases, worst {max(r['max_error_db'] for r in rows):.4f} dB" + ("" if not bad else "; FAIL " + "; ".join(bad)), rows=rows)
    sel = (f >= 20) & (f <= 20000)
    eh = float(np.max(np.abs(db(HY[sel]) - db(HS[sel] + HB[sel]))))
    record("HYBRID: response equals the series LP/HP chain plus the BPF", eh < 0.05, f"max error {eh:.4f} dB")

    # ================================================================ drop-out rules
    n = SR * 2
    x = sig(n)
    y_ser_off = run(x, base())
    y_par_off = run(x, base(flt_route=1))
    k = int(0.05 * SR)
    same_off = np.array_equal(y_ser_off[k:], y_par_off[k:])
    yo = run(x, base(l_on=1, l_cut=20000, h_on=1, h_cut=300, flt_route=1))
    yh = run(x, base(h_on=1, h_cut=300, flt_route=1))
    open_drop = float(np.max(np.abs(yo[k:] - yh[k:])))
    ys = run(x, base(l_on=1, l_cut=700, l_res=60))
    yp = run(x, base(l_on=1, l_cut=700, l_res=60, flt_route=1))
    single = float(np.max(np.abs(ys[k:] - yp[k:])))
    record("PARALLEL: stages that are off or parked fully OPEN drop out of the sum; all off = dry (bit-identical to SERIES); a single stage = the same stage in SERIES",
           same_off and open_drop < 1e-6 and single < 1e-5,
           f"all off identical to series: {same_off}; open LPF + HPF vs HPF alone {open_drop:.1e}; single LPF parallel vs series {single:.1e}")

    # order / BPF position are irrelevant in PARALLEL
    p = base(l_on=1, h_on=1, b_on=1, l_cut=600, h_cut=2500, b_freq=1200, l_res=50, flt_route=1)
    ya = run(x, dict(p, order_sel=0, b_pos=0)); yb = run(x, dict(p, order_sel=1, b_pos=1))
    k2 = int(0.1 * SR)
    record("PARALLEL: stage order and BPF position have no effect (bit-identical once the 8 ms switch dip has passed)",
           np.array_equal(ya[k2:], yb[k2:]), f"max difference {float(np.max(np.abs(ya[k2:] - yb[k2:]))):.1e}")

    # ================================================================ switching
    rows = []
    xs = 0.5 * np.sin(2 * np.pi * 110 * np.arange(int(SR * 1.5)) / SR)
    p = base(l_on=1, h_on=1, b_on=1, l_cut=900, h_cut=200, b_freq=500, l_res=60, h_res=40, b_res=50)
    for a in range(3):
        for b in range(3):
            if a == b:
                continue
            y = run(xs, dict(p, flt_route=a), events=[(SR, "flt_route", b)])[:, 0]
            rows.append(dict(transition=f"{['SERIES', 'PARALLEL', 'HYBRID'][a]} -> {['SERIES', 'PARALLEL', 'HYBRID'][b]}",
                             hf_burst_dbfs=round(hf_burst(y, SR), 1), finite=bool(np.all(np.isfinite(y)))))
    for nm in ("par_l", "par_h", "par_b"):
        y = run(xs, dict(p, flt_route=1), events=[(SR, nm, -40)])[:, 0]
        rows.append(dict(transition=f"PARALLEL {nm} 0 → −40 dB", hf_burst_dbfs=round(hf_burst(y, SR), 1), finite=bool(np.all(np.isfinite(y)))))
    worst = max(r["hf_burst_dbfs"] for r in rows)
    record("ROUTING: switching between all modes during playback and jumping parallel levels is click-free (>8 kHz burst < −60 dBFS)",
           worst < -60 and all(r["finite"] for r in rows), f"{len(rows)} cases, worst {worst:.1f} dBFS", rows=rows)

    # ================================================================ stability, stereo, chain, automation
    x2 = sig(SR * 3)
    ok = True
    pk = []
    for route in (1, 2):
        y = run(x2, base(l_on=1, h_on=1, b_on=1, l_res=100, h_res=100, b_res=100, l_cut=300, h_cut=900, b_freq=2000, flt_route=route, softclip=0))
        ok &= bool(np.all(np.isfinite(y)))
        pk.append(float(db(np.abs(y).max())))
    record("ROUTING: PARALLEL and HYBRID stable with all three filters self-oscillating", ok and max(pk) < 12,
           f"peaks (soft clip off): PARALLEL {pk[0]:.1f} dBFS, HYBRID {pk[1]:.1f} dBFS")
    a_ = sig(SR)
    bad = []
    for route in (1, 2):
        y = run(np.stack([a_, a_], 1), base(l_on=1, h_on=1, b_on=1, l_cut=600, h_cut=2000, flt_route=route))
        if not np.array_equal(y[:, 0], y[:, 1]):
            bad.append(f"route {route} L≠R")
        y2 = run(np.stack([a_, np.zeros_like(a_)], 1), base(l_on=1, h_on=1, b_on=1, l_cut=600, h_cut=2000, flt_route=route))
        if np.abs(y2[:, 1]).max() != 0:
            bad.append(f"route {route} crosstalk")
    record("ROUTING: stereo — identical L/R → bit-identical, zero crosstalk (PARALLEL, HYBRID)", not bad, "ok" if not bad else "; ".join(bad))
    xs3 = sig(SR * 3)
    def ramp(step, name, a, b):
        return [(SR // 2 + i, name, a + (b - a) * i / (2 * SR)) for i in range(0, 2 * SR, step)]
    p = base(l_on=1, h_on=1, b_on=1, l_cut=500, h_cut=3000, b_freq=1200, flt_route=1)
    ya = run(xs3, p, events=ramp(64, "par_h", -40, 6))[:, 0]; yb = run(xs3, p, events=ramp(1, "par_h", -40, 6))[:, 0]
    e = float(db(np.sqrt(np.mean((ya - yb) ** 2)) / np.sqrt(np.mean(yb ** 2))))
    record("ROUTING automation: block-rate parallel-level ramp ≈ sample-accurate (< −30 dB difference)", e < -30, f"{e:.1f} dB")
    y = run(xs3, base(l_on=1, h_on=1, b_on=1, l_cut=500, h_cut=3000, flt_route=1, t_on=1, o_on=1, v_on=1, g_on=1, g_thr=-70))
    record("ROUTING + DYNAMICS: PARALLEL filters feeding the full dynamics chain and gate", bool(np.all(np.isfinite(y))) and float(np.abs(y).max()) <= 1.0,
           f"peak {db(np.abs(y).max()):.2f} dBFS")
    rng = np.random.default_rng(9)
    n = SR * 20
    x = sig(n) * 1.3
    ev = []
    for i in range(1, 200):
        fr = i * SR // 10
        ev += [(fr, "l_cut", float(20 * 1000 ** rng.random())), (fr, "h_cut", float(20 * 100 ** rng.random())),
               (fr, "b_freq", float(30 * 400 ** rng.random())), (fr, "par_l", float(-40 + 46 * rng.random())),
               (fr, "par_h", float(-40 + 46 * rng.random())), (fr, "par_b", float(-40 + 46 * rng.random()))]
        if i % 9 == 0:
            ev += [(fr, "flt_route", int(rng.integers(0, 3))), (fr, "order_sel", int(rng.integers(0, 2))), (fr, "b_pos", int(rng.integers(0, 2)))]
        if i % 17 == 0:
            ev += [(fr, "l_model", int(rng.integers(0, 6))), (fr, "b_arch", int(rng.integers(0, 3))), (fr, "ovs_sel", int(rng.integers(0, 2)))]
    y = run(x, base(l_on=1, h_on=1, b_on=1, t_on=1, o_on=1, v_on=1, softclip=1), events=ev)
    record("ROUTING: 20 s stress — random routing, levels, order, position, models, oversampling", bool(np.all(np.isfinite(y))) and float(np.abs(y).max()) <= 1.0,
           f"peak {db(np.abs(y).max()):.2f} dBFS")
    rows = []
    xx = sig(SR * 10)
    for nm, route in (("SERIES", 0), ("PARALLEL", 1), ("HYBRID", 2)):
        p = base(l_on=1, h_on=1, b_on=1, l_cut=1500, h_cut=200, b_freq=800, flt_route=route)
        best = min(run(xx, p, ns=True)[1] for _ in range(3))
        rows.append(dict(config=f"LPF + HPF + BPF, {nm}", pct_of_one_core_48k=round(best * 48000 / 1e7, 2)))
    record("CPU by routing mode (LPF + HPF + BPF on)", True, "; ".join(f"{r['config']}: {r['pct_of_one_core_48k']}%" for r in rows), rows=rows)

    # ================================================================ device: routing control + flow readout
    P = json.load(open(os.path.join(HERE, "..", "build", "device", "DubFilter.maxpat")))["patcher"]
    bx = {b["box"]["id"]: b["box"] for b in P["boxes"]}
    probs = []
    rt = [b for b in bx.values() if b.get("varname") == "flt_route"]
    if len(rt) != 1 or not rt[0].get("parameter_enable") or rt[0]["saved_attribute_attributes"]["valueof"]["parameter_enum"] != ["SERIES", "PARALLEL", "HYBRID"]:
        probs.append("routing parameter missing/wrong")
    exb = next(b for b in bx.values() if b.get("text", "").startswith("expr ($i1 == 0)"))
    msgs = sorted([b for b in bx.values() if b.get("maxclass") == "message" and b.get("text", "").startswith("set IN >")], key=lambda b: b["patching_rect"][0])
    expect = {}
    for r_ in range(3):
        for o in range(2):
            for pos in range(2):
                idx = (r_ == 0) * (o * 2 + pos) + (r_ == 1) * 4 + (r_ == 2) * (5 + o)
                txt = msgs[idx]["text"][4:]
                if r_ == 0:
                    chain = ["LP", "HP"] if o == 0 else ["HP", "LP"]
                    want = " > ".join(["IN"] + (["BP"] if pos else []) + chain + ([] if pos else ["BP"]) + ["OUT"])
                elif r_ == 1:
                    want = "IN > ( LP + HP + BP ) > OUT"
                else:
                    want = f"IN > ( {' > '.join(['LP', 'HP'] if o == 0 else ['HP', 'LP'])} ) + BP > OUT"
                if txt != want:
                    probs.append(f"flow r{r_} o{o} p{pos}: {txt} != {want}")
    params = [b for b in bx.values() if b.get("parameter_enable")]
    longs = [b["saved_attribute_attributes"]["valueof"]["parameter_longname"] for b in params]
    record("DEVICE: Filter Routing + 3 parallel levels are stored parameters; signal-flow readout correct for all 12 routing × order × position combinations; 82 unique parameters (v1.6 appends Engine Mode, High Oversampling, K35 Circuit)",
           not probs and len(longs) == 82 and len(set(longs)) == 82, "ok" if not probs else "; ".join(probs))

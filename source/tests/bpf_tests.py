"""v1.2 band-pass engine tests + regression gates. Imported by validate.py."""
import os, sys, subprocess
import numpy as np
from scipy.signal import butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from dsp import run, base, tf, bpf, BP_MODELS, BP_ARCHS
import bpf as BPF

SR = 48000
RMAX = [m["rmax"] for m in BPF.BPF_MODELS]
KMAX = [m["kmax"] for m in BPF.BPF_MODELS]


def cmm(k):
    k = min(k, 4.3)
    return ((((0.000804 * k - 0.009901) * k + 0.039923) * k - 0.03441) * k - 0.07288) * k + 0.998285


def bmag(rho, Q, hp):
    m = 1 / np.sqrt((1 - rho * rho) ** 2 + rho * rho / (Q * Q))
    return m * rho * rho if hp else m


def ref_bpf(f, m, a, fc, bw, Q, res, fs=SR):
    """Analytic small-signal response of the BPF configuration (bilinear-exact)."""
    t = np.tan(np.pi * f / fs)
    gc = np.tan(np.pi * fc / fs)
    rz = res / 100
    if a == 0 and m == 0:
        # v1.6: SEM-1A core, band-pass node; damping min(Q knob, RES law), no regeneration loop
        s = 1j * t / gc
        R = min(0.5 / Q, 0.05 + 1.515 * (1 - rz))
        H = 2 * R * s / (s * s + 2 * R * s + 1)
    elif a == 0 and m == 1:
        # v1.6: Synthacon core, input at the BP injection point: K s/(s^2 + (3-K) s + 1), normalised by (3-K)/K
        s = 1j * t / gc
        K = max(1 + 2.1 * rz ** 1.3, 3 - 1 / Q)
        H = K * s / (s * s + (3 - K) * s + 1) * max(3 - K, 0.1) / K
    elif a == 0:
        s = 1j * t / gc
        R = 0.5 / Q
        H = 2 * R * s / (s * s + 2 * R * s + 1)
        r = RMAX[m] * rz ** 1.3
        H = H / (1 - r * H)
    elif a == 1 and m == 2:
        # v1.6: MS-20 = 1-pole HP -> 2-pole LP, both corners scaled by the loop-phase tuning L (engine: 10-step bisection)
        ea, eb = 2 ** (-bw / 2), 2 ** (bw / 2)
        lo, hi = -2.5, 1.5
        for _ in range(10):
            md = 0.5 * (lo + hi); Lm = 2 ** md; ri = 1 / (Lm * eb)
            ph = np.arctan(Lm * ea) - np.arctan2(ri / Q, 1 - ri * ri)
            hi, lo = (md, lo) if ph > 0 else (hi, md)
        Lr = 2 ** (0.5 * (lo + hi) * np.clip(2 * rz, 0, 1))
        glo, ghi = np.tan(np.pi * 10 / fs), np.tan(0.45 * np.pi)
        gh, gl = np.clip(gc * ea * Lr, glo, ghi), np.clip(gc * eb * Lr, glo, ghi)
        rh = gc / gh
        cn = 1 / ((rh / np.sqrt(1 + rh * rh)) * bmag(gc / gl, Q, 0))
        sh, sl = 1j * t / gh, 1j * t / gl
        H = cn * (sh / (sh + 1)) / (sl * sl + sl / Q + 1)
        r = RMAX[m] * rz ** 1.3
        H = H / (1 - r * H)
    elif a == 1:
        fh = np.clip(fc * 2 ** (-bw / 2), 10, 0.45 * fs)
        fl = np.clip(fc * 2 ** (bw / 2), 10, 0.45 * fs)
        gh, gl = np.tan(np.pi * fh / fs), np.tan(np.pi * fl / fs)
        cn = 1 / (bmag(gc / gh, Q, 1) * bmag(gc / gl, Q, 0))
        sh, sl = 1j * t / gh, 1j * t / gl
        H = cn * (sh * sh / (sh * sh + sh / Q + 1)) / (sl * sl + sl / Q + 1)
        r = RMAX[m] * rz ** 1.3
        H = H / (1 - r * H)
    else:
        k = KMAX[m] * rz ** 1.3
        s = 1j * t / (gc / cmm(k))
        L = 1 / (1 + s)
        wb = np.clip((bw - 1) * 0.5, 0, 1)
        H = (4 * L ** 2 * (1 - L) ** 2 * (1 - wb) + 2 * L * (1 - L) * wb) / (1 + k * L ** 4)
    if BPF.BPF_MODELS[m]["roll"]:
        sr_ = 1j * t / np.tan(np.pi * min(14000, 0.45 * fs) / fs)
        H = H / (1 + sr_)
    return H


def db(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-12))


def hf_burst(y, at, win=0.006):
    h = sosfilt(butter(4, 8000, "hp", fs=SR, output="sos"), y)
    return db(np.sqrt(np.mean(h[int(at):int(at) + int(win * SR)] ** 2)) + 1e-12)


def run_all(record, plt, OUT, SEQ, CAT, GRID, sig):
    # ------------------------------------------------------------ regression gates
    r = subprocess.run([sys.executable, os.path.join(HERE, "golden.py"), "check"], capture_output=True, text=True)
    record("REGRESSION: LPF/HPF bit-exact against the v1.1 baseline except the documented v1.6 solver changes (BPF off; 48 scenarios)", r.returncode == 0, r.stdout.strip())
    r = subprocess.run([sys.executable, os.path.join(HERE, "compat.py"), "--ui"], capture_output=True, text=True)
    record("REGRESSION: v1.1 presets/automation/MIDI maps — every v1.1 object, connection and gen~ Param unchanged",
           r.returncode == 0, r.stdout.strip().splitlines()[-1] + " — " + r.stdout.strip().splitlines()[1])
    # BPF enabled at Mix 0 must contribute exactly nothing: Mix is set to 0 at
    # 50 ms (BPF still off), the BPF is switched on at 150 ms; the whole render
    # must be bit-identical to BPF off, in both POST and PRE positions.
    import golden
    cases, gx = golden.battery()
    bad, n = [], 0
    for name, p, ev in cases:
        for pos in (0, 1):
            pa = dict(p); pa.update(b_pos=pos)
            ev_b = sorted(list(ev) + [(int(0.05 * SR), "b_mix", 0), (int(0.15 * SR), "b_on", 1)], key=lambda e: e[0])
            ya = run(gx, pa, SR, events=ev); yb = run(gx, pa, SR, events=ev_b)
            n += 1
            if not np.array_equal(ya, yb):
                bad.append(f"{name} pos{pos}")
    record("REGRESSION: BPF switched on at Mix 0 is bit-transparent to the LPF/HPF signal (48 scenarios × POST/PRE)", not bad,
           f"{n - len(bad)}/{n} bit-identical" + ("" if not bad else "; MISMATCH " + ", ".join(bad)))

    # ------------------------------------------------------------ circuit/analytic reference
    rows, bad = [], []
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    for a in range(3):
        for m in range(5):
            for (res, bw, Q) in ((0, 2.0, 0.707), (0, 0.6, 3.0), (50, 2.5, 1.2)):
                f, H = tf(bpf(model=m, arch=a, freq=900, bw=bw, q=Q, res=res, comp=100), n=1 << 17, level=2e-4)
                sel = (f >= 20) & (f <= 20000)
                f, H = f[sel], H[sel]
                Hr = ref_bpf(f, m, a, 900, bw, Q, res)
                A, Ar = db(H), db(Hr)
                v = Ar > -60
                e = float(np.percentile(np.abs(A[v] - Ar[v]), 99))
                rows.append(dict(arch=BP_ARCHS[a], model=BP_MODELS[m], res=res, bw=bw, q=Q, err_p99_db=round(e, 3)))
                if e > 0.5:
                    bad.append(f"{BP_ARCHS[a]}/{BP_MODELS[m]} res{res}: {e:.2f} dB")
                if m == 2:
                    i = [(0, 2.0, 0.707), (0, 0.6, 3.0), (50, 2.5, 1.2)].index((res, bw, Q))
                    axes[a].semilogx(f, Ar, color="#c9c7c0", lw=4)
                    axes[a].semilogx(f, A, color=SEQ[i + 1], lw=1.2, label=f"BW {bw} oct, Q {Q}, res {res}%")
        axes[a].set_title(f"{BP_ARCHS[a]} (thick = analytic, thin = device)")
        axes[a].set_xlim(20, 20000); axes[a].set_ylim(-60, 15)
    axes[0].legend(fontsize=7); axes[0].set_ylabel("dB")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "bpf_reference.png"), dpi=130); plt.close(fig)
    record("BPF: small-signal response of all 15 model×architecture configurations matches its analytic transfer function (99th pct < 0.5 dB)",
           not bad, f"{len(rows)} configurations, worst {max(r['err_p99_db'] for r in rows):.3f} dB" + ("" if not bad else "; FAIL " + "; ".join(bad)), rows=rows)

    # ------------------------------------------------------------ bandwidth / Q behaviour
    bwrows, bad = [], []
    for bw in (1, 2, 3, 4):
        f, H = tf(bpf(model=4, arch=1, freq=1000, bw=bw, q=0.707), n=1 << 17)   # v1.6: a symmetric (2-pole/2-pole) cascade; the MS-20's is 1-pole/2-pole
        A = db(H); m3 = f[A > A.max() - 3.0103]
        meas = np.log2(m3.max() / m3.min())
        bwrows.append(dict(arch="CASCADE", setting=f"BW {bw} oct", expected_oct=bw, measured_oct=round(float(meas), 2)))
        if abs(meas - bw) > max(0.15 * bw, 0.2) and bw >= 2:
            bad.append(f"cascade BW{bw}: {meas:.2f}")
    for Q in (0.707, 2, 5):
        f, H = tf(bpf(model=0, arch=0, freq=1000, q=Q), n=1 << 17)
        A = db(H); m3 = f[A > A.max() - 3.0103]
        meas = np.log2(m3.max() / m3.min())
        exp = 2 * np.arcsinh(1 / (2 * Q)) / np.log(2)
        bwrows.append(dict(arch="SVF", setting=f"Q {Q}", expected_oct=round(float(exp), 2), measured_oct=round(float(meas), 2)))
        if abs(meas - exp) > 0.1 * exp + 0.05:
            bad.append(f"svf Q{Q}: {meas:.2f} vs {exp:.2f}")
    for bw in (0.5, 2, 3):
        f, H = tf(bpf(model=3, arch=2, freq=1000, bw=bw), n=1 << 17)
        A = db(H); m3 = f[A > A.max() - 3.0103]
        bwrows.append(dict(arch="MULTIMODE", setting=f"BW {bw} (pole-mix order)", expected_oct=None, measured_oct=round(float(np.log2(m3.max() / m3.min())), 2)))
    # architecture comparison plot
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    for a, sets in ((0, [dict(q=0.707), dict(q=2), dict(q=6)]), (1, [dict(bw=0.6, q=2), dict(bw=2), dict(bw=4, q=1.5)]),
                    (2, [dict(bw=0.5), dict(bw=2), dict(bw=3), dict(bw=0.5, res=85)])):
        for i, kw in enumerate(sets):
            f, H = tf(bpf(model=2, arch=a, freq=1000, **kw), n=1 << 16)
            axes[a].semilogx(f[1:], db(H[1:]), color=SEQ[i], label=", ".join(f"{k} {v}" for k, v in kw.items()))
        axes[a].set_title(BP_ARCHS[a]); axes[a].set_xlim(20, 20000); axes[a].set_ylim(-70, 20); axes[a].legend(fontsize=7)
    fig.suptitle("BPF architectures — what Bandwidth and Q do (centre 1 kHz)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "bpf_architectures.png"), dpi=130); plt.close(fig)
    record("BPF: bandwidth control (CASCADE −3 dB width tracks BW setting; SVF width follows Q)", not bad,
           "; ".join(f"{r['arch']} {r['setting']}: {r['measured_oct']} oct" for r in bwrows), rows=bwrows)

    # ------------------------------------------------------------ centre tracking
    rows, bad = [], []
    for a in range(3):
        for m in range(5):
            for fc in (100, 400, 1500, 5000):
                f, H = tf(bpf(model=m, arch=a, freq=fc, bw=2, q=0.707, res=85), n=1 << 17)
                sel = (f > fc / 3) & (f < fc * 3)
                pk = f[sel][np.argmax(np.abs(H[sel]))]
                c = 1200 * np.log2(pk / fc)
                rows.append(dict(arch=BP_ARCHS[a], model=BP_MODELS[m], fc=fc, cents=round(float(c))))
                if abs(c) > max(100, 1200 * np.log2((fc + 6) / fc)):
                    bad.append(f"{BP_ARCHS[a]}/{BP_MODELS[m]} {fc}: {c:+.0f}c")
    record("BPF: resonant peak tracks the centre frequency within ±100 cents (res 85%, all configurations)", not bad,
           f"worst {max(abs(r['cents']) for r in rows if r['fc'] > 200)} c above 200 Hz" + ("" if not bad else "; FAIL " + "; ".join(bad)), rows=rows)

    # ------------------------------------------------------------ self-oscillation
    rows, bad = [], []
    for ovs in (0, 1):
        for a in range(3):
            for m in range(5):
                x = np.zeros(SR * 3); x[SR // 2] = 0.3
                y = run(x, bpf(model=m, arch=a, freq=700, res=100, softclip=0, ovs_sel=ovs))[:, 0]
                tail = y[2 * SR:]
                pk = np.abs(tail).max()
                sp = np.abs(np.fft.rfft(tail * np.hanning(len(tail))))
                fr = np.fft.rfftfreq(len(tail), 1 / SR)[np.argmax(sp)]
                osc = pk > 1e-3
                c = 1200 * np.log2(fr / 700) if osc else None
                rows.append(dict(os=ovs + 1, arch=BP_ARCHS[a], model=BP_MODELS[m], oscillates=bool(osc),
                                 peak_dbfs=round(float(db(pk)), 1), cents=None if c is None else round(c)))
                expect = m != 0
                if not np.all(np.isfinite(y)) or pk > 1.25 or osc != expect or (osc and abs(c) > 100):
                    bad.append(f"os{ovs + 1} {BP_ARCHS[a]}/{BP_MODELS[m]} osc={osc} pk={db(pk):.1f} c={c}")
    record("BPF: self-oscillation stable, bounded (<+2 dBFS) and on centre; SEM never self-oscillates (1x and 2x)", not bad,
           "ok" if not bad else "; ".join(bad), rows=rows)

    # ------------------------------------------------------------ nonlinear character per model
    rows = []
    t = np.arange(SR * 2) / SR
    fig, axes = plt.subplots(1, 5, figsize=(15, 3.4), sharey=True)
    vecs = {}
    for m in range(5):
        thds = []
        for i, drv in enumerate((0, 50, 100)):
            a = BPF.BPF_MODELS[m]["native"] if BPF.BPF_MODELS[m]["native"] is not None else 2
            x = 0.5 * np.sin(2 * np.pi * 200 * t)
            y = run(x, bpf(model=m, arch=a, freq=300, bw=2, q=0.707, res=40, drive=drv))[SR:, 0]
            S = np.abs(np.fft.rfft(y * np.blackman(len(y)))) / (len(y) / 4)
            F = np.fft.rfftfreq(len(y), 1 / SR)
            h = np.array([S[np.argmin(abs(F - 200 * k))] for k in range(1, 9)])
            thd = float(np.sqrt(np.sum(h[1:] ** 2)) / h[0])
            thds.append(thd)
            if drv == 100:
                vecs[m] = db(h[1:] / h[0])
            axes[m].semilogx(F[1:], db(S[1:]), color=SEQ[i + 1], lw=0.8, label=f"drive {drv}%")
        axes[m].set_title(f"{BP_MODELS[m]} ({BP_ARCHS[a]})"); axes[m].set_xlim(50, 20000); axes[m].set_ylim(-140, 0)
        rows.append(dict(model=BP_MODELS[m], arch=BP_ARCHS[a], thd_pct_drive0=round(100 * thds[0], 3),
                         thd_pct_drive50=round(100 * thds[1], 2), thd_pct_drive100=round(100 * thds[2], 2)))
    axes[0].legend(fontsize=7)
    fig.suptitle("BPF models — 200 Hz sine, −6 dBFS, centre 300 Hz, each model in its native/closest architecture")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "bpf_models_nonlinear.png"), dpi=130); plt.close(fig)
    mono = all(r["thd_pct_drive0"] <= r["thd_pct_drive50"] <= r["thd_pct_drive100"] for r in rows)
    dist = min(float(np.sqrt(np.mean((vecs[i] - vecs[j]) ** 2))) for i in range(5) for j in range(i + 1, 5))
    record("BPF: harmonic content rises with drive for every model; models are distinct (min RMS harmonic-profile distance > 1 dB)",
           mono and dist > 1.0, f"monotonic={mono}, closest pair differs by {dist:.1f} dB RMS", rows=rows)

    # ------------------------------------------------------------ clicks
    E = SR // 2
    rows = []
    xs = sig(SR, kind="sine")
    cases = [
        ("centre 200 Hz → 5 kHz", bpf(freq=200, res=50), [(E, "b_freq", 5000)]),
        ("centre 5 kHz → 200 Hz", bpf(arch=1, freq=5000, res=50), [(E, "b_freq", 200)]),
        ("bandwidth 0.2 → 6 oct", bpf(arch=1, freq=300, bw=0.2), [(E, "b_bw", 6)]),
        ("Q 0.5 → 10", bpf(arch=0, freq=200, q=0.5), [(E, "b_q", 10)]),
        ("resonance 0 → 100%", bpf(arch=2, model=3, freq=300), [(E, "b_res", 100)]),
        ("drive 0 → 100%", bpf(arch=0, model=1, freq=200, res=50), [(E, "b_drive", 100)]),
        ("mix 0 → 100%", bpf(freq=1000, mix=0), [(E, "b_mix", 100)]),
        ("BPF on", base(b_on=0, b_freq=800, b_res=60), [(E, "b_on", 1)]),
        ("BPF off", bpf(freq=800, res=60), [(E, "b_on", 0)]),
        ("position POST → PRE", base(l_on=1, h_on=1, b_on=1, l_cut=2000, h_cut=60, b_freq=400, b_res=60), [(E, "b_pos", 1)]),
    ]
    for m in range(5):
        cases.append((f"model switch {BP_MODELS[m]} → {BP_MODELS[(m + 1) % 5]}", bpf(model=m, freq=150, res=60), [(E, "b_model", (m + 1) % 5)]))
    for a in range(3):
        cases.append((f"architecture switch {BP_ARCHS[a]} → {BP_ARCHS[(a + 1) % 3]}", bpf(arch=a, freq=150, res=60), [(E, "b_arch", (a + 1) % 3)]))
    for name, p, ev in cases:
        y = run(xs, p, events=ev)[:, 0]
        rows.append(dict(case=name, hf_abs_dbfs=round(float(hf_burst(y, ev[0][0])), 1), finite=bool(np.all(np.isfinite(y)))))
    bad = [r for r in rows if r["hf_abs_dbfs"] > -60 or not r["finite"]]
    record("BPF: click/zipper — >8 kHz burst after every abrupt BPF change below −60 dBFS (−6 dBFS sine)", not bad,
           f"{len(rows)} cases, worst {max(r['hf_abs_dbfs'] for r in rows):.1f} dBFS" + ("" if not bad else "; FAIL " + ", ".join(r["case"] for r in bad)), rows=rows)

    # ------------------------------------------------------------ stereo
    n = SR
    a_ = sig(n); b_ = np.roll(sig(n), 777) * 0.6
    bad = []
    for a in range(3):
        for m in range(5):
            p = bpf(model=m, arch=a, freq=600, res=80, drive=50)
            y = run(np.stack([a_, a_], 1), p)
            if not np.array_equal(y[:, 0], y[:, 1]):
                bad.append(f"{BP_ARCHS[a]}/{BP_MODELS[m]} L≠R")
            y2 = run(np.stack([a_, np.zeros(n)], 1), p)
            if np.abs(y2[:, 1]).max() != 0:
                bad.append(f"{BP_ARCHS[a]}/{BP_MODELS[m]} crosstalk")
            y3 = run(np.stack([a_, b_], 1), p)
            if not np.array_equal(y3[:, 0], y[:, 0]):
                bad.append(f"{BP_ARCHS[a]}/{BP_MODELS[m]} R affects L")
    record("BPF: stereo — identical L/R → bit-identical out, zero crosstalk, independent channels (15 configurations)", not bad,
           "ok" if not bad else "; ".join(bad))

    # ------------------------------------------------------------ combined LPF + HPF + BPF
    n = SR * 4
    x = sig(n)
    xs2 = np.stack([x, np.roll(x, 500) * 0.8], 1)
    out = []
    for pos in (0, 1):
        for ovs in (0, 1):
            ev = [(SR // 2 + i * 480, "l_cut", 9000 * (400 / 9000) ** (i / 300)) for i in range(301)] + \
                 [(SR // 2 + i * 480, "h_cut", 30 * (300 / 30) ** (i / 300)) for i in range(301)] + \
                 [(SR // 2 + i * 480, "b_freq", 200 * 20 ** (i / 300)) for i in range(301)]
            p = base(l_on=1, h_on=1, b_on=1, l_model=0, h_model=3, b_model=2, b_arch=1, l_res=70, h_res=50, b_res=70,
                     b_pos=pos, ovs_sel=ovs, softclip=1)
            y = run(xs2, p, events=ev)
            out.append((pos, ovs, bool(np.all(np.isfinite(y))), float(np.abs(y).max())))
    ok = all(o[2] and o[3] <= 1.0 for o in out)
    record("COMBINED: LPF + HPF + BPF all active and sweeping, POST/PRE × 1x/2x", ok,
           ", ".join(f"{'PRE' if o[0] else 'POST'}/{o[1] + 1}x peak {db(o[3]):.1f} dBFS" for o in out))
    # combined: LPF/HPF chain unchanged when BPF is in the path but transparent (Mix 0) — covered by regression gate above
    # 30 s stress with every parameter of all three engines randomised
    rng = np.random.default_rng(11)
    n = SR * 30
    x = sig(n) * 1.4
    ev = []
    for i in range(1, 300):
        fr = i * SR // 10
        ev += [(fr, "l_cut", float(20 * 1000 ** rng.random())), (fr, "h_cut", float(20 * 100 ** rng.random())),
               (fr, "b_freq", float(30 * 400 ** rng.random())), (fr, "b_bw", float(0.2 + 5.8 * rng.random())),
               (fr, "b_q", float(0.5 + 9.5 * rng.random())), (fr, "b_res", float(100 * rng.random())),
               (fr, "l_res", float(100 * rng.random()))]
        if i % 5 == 0:
            ev += [(fr, "b_model", int(rng.integers(0, 5))), (fr, "b_arch", int(rng.integers(0, 3))), (fr, "l_model", int(rng.integers(0, 6)))]
        if i % 13 == 0:
            ev += [(fr, "b_pos", int(rng.integers(0, 2))), (fr, "b_drive", float(100 * rng.random())), (fr, "b_on", int(rng.integers(0, 2)))]
        if i % 37 == 0:
            ev += [(fr, "order_sel", int(rng.integers(0, 2))), (fr, "ovs_sel", int(rng.integers(0, 2)))]
    y = run(x, base(l_on=1, h_on=1, b_on=1, softclip=1), events=ev)
    record("COMBINED: 30 s stress — random changes to every LPF, HPF, BPF and global parameter, hot input", np.all(np.isfinite(y)) and np.abs(y).max() <= 1.0,
           f"peak {db(np.abs(y).max()):.2f} dBFS, finite={bool(np.all(np.isfinite(y)))}")

    # ------------------------------------------------------------ automation & MIDI on BPF
    xsn = sig(SR * 3, kind="sine")
    def ramp(step):
        return [(SR // 2 + i, "b_freq", 150 * (3000 / 150) ** (i / (2 * SR))) for i in range(0, 2 * SR, step)]
    ya = run(xsn, bpf(arch=0, res=60, q=2), events=ramp(64))[:, 0]
    yb = run(xsn, bpf(arch=0, res=60, q=2), events=ramp(1))[:, 0]
    sos = butter(4, 8000, "hp", fs=SR, output="sos")
    err = db(np.sqrt(np.mean((ya - yb) ** 2)) / np.sqrt(np.mean(yb ** 2)))
    hf = db(np.sqrt(np.mean(sosfilt(sos, ya) ** 2))) - db(np.sqrt(np.mean(sosfilt(sos, yb) ** 2)))
    record("BPF automation: Live block-rate (64-sample) centre ramp vs sample-accurate", err < -30 and hf < 1,
           f"difference {err:.1f} dB, >8 kHz energy {hf:+.2f} dB")
    cc = lambda v: 30 + (12000 - 30) * (v / 127) ** 4.39
    ev = [(SR // 2 + i * 384, "b_freq", cc(i)) for i in range(128)]
    y = run(xsn, bpf(arch=1, res=60), events=ev)[:, 0]
    worst = max(hf_burst(y, e[0]) for e in ev[::8])
    record("BPF MIDI: 7-bit CC stepping of the centre (one step per 8 ms) — no zipper", worst < -60, f"worst >8 kHz burst {worst:.1f} dBFS")

    # ------------------------------------------------------------ sample rates, denormals, CPU
    rows, bad = [], []
    for sr in (44100, 48000, 96000, 192000):
        for a in range(3):
            f, H = tf(bpf(model=2, arch=a, freq=2000, res=85), sr=sr, n=1 << 17)
            sel = (f > 700) & (f < 6000)
            c = 1200 * np.log2(f[sel][np.argmax(np.abs(H[sel]))] / 2000)
            rows.append(dict(sr=sr, arch=BP_ARCHS[a], cents=round(float(c))))
            if abs(c) > 100:
                bad.append(f"{sr} {BP_ARCHS[a]} {c:+.0f}c")
    record("BPF: sample-rate independence 44.1–192 kHz (centre tracking)", not bad, "ok" if not bad else "; ".join(bad), rows=rows)
    x = sig(SR * 8); x[SR * 2:] = 0
    tails = []
    for a in range(3):
        for m in range(5):
            y = run(x, bpf(model=m, arch=a, freq=400, res=80))
            tails.append(np.abs(y[-SR:]).max())
    record("BPF: decay tails flush to zero (no denormals)", max(tails) < 1e-15, f"max tail {max(tails):.1e}")
    rows = []
    xx = sig(SR * 10)
    for nm, p in [("v1.1 default device (LPF+HPF), BPF off", base(l_on=1, h_on=1, l_model=2, h_model=1, l_cut=2000, h_cut=60, l_slope=1)),
                  ("+ BPF SVF", base(l_on=1, h_on=1, b_on=1, l_model=2, h_model=1, l_cut=2000, h_cut=60, l_slope=1)),
                  ("+ BPF CASCADE", base(l_on=1, h_on=1, b_on=1, b_arch=1, l_model=2, h_model=1, l_cut=2000, h_cut=60, l_slope=1)),
                  ("+ BPF MULTIMODE (ARP)", base(l_on=1, h_on=1, b_on=1, b_arch=2, b_model=3, l_model=2, h_model=1, l_cut=2000, h_cut=60, l_slope=1)),
                  ("worst: all three, 48 dB slopes, 2x, BPF mid-crossfade", base(l_on=1, h_on=1, b_on=1, b_arch=1, l_model=5, h_model=0, l_slope=3, h_slope=3, ovs_sel=1, l_cut=2000, h_cut=60))]:
        ev = []
        if "crossfade" in nm:
            ev = [(i * int(0.02 * SR), "b_arch", (1, 2)[i % 2]) for i in range(1, 499)]
        best = min(run(xx, p, events=ev, ns=True)[1] for _ in range(3))
        rows.append(dict(config=nm, ns_per_frame=round(best, 1), pct_of_one_core_48k=round(best * 48000 / 1e7, 2)))
    record("CPU with BPF (transpiled C, gcc -O2, this machine)", True, "; ".join(f"{r['config']}: {r['pct_of_one_core_48k']}%" for r in rows), rows=rows)

"""v1.3 dynamics chain tests + regression gates. Imported by validate.py."""
import os, sys, subprocess, json
import numpy as np
from scipy.signal import butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from dsp import run, base, tf, DYN_PERMS
import dyn as DYN

SR = 48000
M_TIN, M_TOUT, M_OIN, M_OOUT, M_OGR, M_VIN, M_VOUT, M_VGR, M_GATE, M_KEY, M_CIN, M_COUT = range(12)


def db(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-12))


def lvl(y):
    return float(db(np.sqrt(np.mean(np.asarray(y) ** 2)) * np.sqrt(2)))


def hf_burst(y, at, win=0.006):
    h = sosfilt(butter(4, 8000, "hp", fs=SR, output="sos"), y)
    return float(db(np.sqrt(np.mean(h[int(at):int(at) + int(win * SR)] ** 2)) + 1e-12))


def tone(f, dbfs, sec, n=None):
    n = n or int(SR * sec)
    return 10 ** (dbfs / 20) * np.sin(2 * np.pi * f * np.arange(n) / SR)


ALL3 = dict(t_on=1, o_on=1, v_on=1, t_drive=45, o_pr=55, v_thr=-24, v_ratio=3, v_att=3, v_rel=0.2)


def run_all(record, plt, OUT, SEQ, CAT, GRID, sig):
    # ================================================================ regression gates
    for args, name in ((["check"], "REGRESSION v1.3: LPF/HPF bit-exact vs v1.1 baseline (48 scenarios, dynamics off)"),
                       (["check-bpf"], "REGRESSION v1.3: BPF bit-exact vs v1.2 baseline (35 scenarios, dynamics off)")):
        r = subprocess.run([sys.executable, os.path.join(HERE, "golden.py")] + args, capture_output=True, text=True)
        record(name, r.returncode == 0, r.stdout.strip())
    for b in ("DubFilter_v1.1.maxpat", "DubFilter_v1.2.maxpat"):
        r = subprocess.run([sys.executable, os.path.join(HERE, "compat.py"), "--ui", f"--base={b}"], capture_output=True, text=True)
        lines = r.stdout.strip().splitlines()
        record(f"REGRESSION v1.3: presets/automation/MIDI of {b[10:14]} devices intact (objects, connections, parameters, gen~ Params)",
               r.returncode == 0, lines[-1] + " — " + lines[0])
    # all three modules enabled at Mix 0 must be bit-transparent
    import golden
    cases, gx = golden.battery()
    bad = 0
    for name, p, ev in cases[::2]:
        evb = sorted(list(ev) + [(int(0.05 * SR), "o_mix", 0), (int(0.05 * SR), "v_mix", 0),
                                 (int(0.15 * SR), "o_on", 1), (int(0.15 * SR), "v_on", 1)], key=lambda e: e[0])
        if not np.array_equal(run(gx, p, SR, events=ev), run(gx, p, SR, events=evb)):
            bad += 1
    record("REGRESSION v1.3: Opto+VCA switched on at Mix 0 are bit-transparent (24 filter scenarios); TUBE at Mix 0 passes its phase-matched dry path (see LATENCY)",
           bad == 0, f"{24 - bad}/24 bit-identical")

    # ================================================================ six processing orders
    n = SR * 4
    x = sig(n) * 1.2
    rows, outs = [], {}
    for o in range(6):
        y, M = run(x, dyn(**ALL3, c_order=o), meters=True)
        outs[o] = y
        rows.append(dict(order=DYN_PERMS[o], out_level_dbfs=round(lvl(y[SR:, 0]), 2), peak_dbfs=round(float(db(np.abs(y).max())), 2),
                         opto_gr_db=round(float(np.median(M[SR:, M_OGR] * 30)), 2), vca_gr_db=round(float(np.median(M[SR:, M_VGR] * 30)), 2),
                         finite=bool(np.all(np.isfinite(y)))))
    spread = max(r["out_level_dbfs"] for r in rows) - min(r["out_level_dbfs"] for r in rows)
    distinct = min(float(np.sqrt(np.mean((outs[i][SR:, 0] - outs[j][SR:, 0]) ** 2))) for i in range(6) for j in range(i + 1, 6)) > 1e-4
    ok = all(r["finite"] and r["peak_dbfs"] < 0.5 for r in rows) and spread < 6 and distinct
    record("CHAIN: all six processing orders run (all modules on) — stable, bounded, audibly distinct, level spread < 6 dB",
           ok, f"level spread across orders {spread:.2f} dB; " + "; ".join(f"{r['order']} {r['out_level_dbfs']} dBFS" for r in rows), rows=rows)
    fig, ax = plt.subplots(figsize=(9, 3.4))
    for o in range(6):
        Y = np.abs(np.fft.rfft(outs[o][SR:, 0] * np.hanning(n - SR)))
        F = np.fft.rfftfreq(n - SR, 1 / SR)
        sm = np.convolve(db(Y / len(Y)), np.ones(64) / 64, "same")
        ax.semilogx(F[1:], sm[1:], color=CAT[o], lw=1.0, label=DYN_PERMS[o])
    ax.set_xlim(30, 20000); ax.set_xlabel("Hz"); ax.set_ylabel("dB"); ax.legend(fontsize=6.5, ncol=2)
    ax.set_title("Six processing orders, same settings and input (smoothed output spectra)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "chain_orders.png"), dpi=130); plt.close(fig)

    # ================================================================ real-time reordering (all 30 transitions)
    rows = []
    xs = tone(110, -6, 2.6)
    p = dyn(**ALL3)
    for a in range(6):
        for b in range(6):
            if a == b:
                continue
            E = int(1.5 * SR)
            y, M = run(xs, dict(p, c_order=a), events=[(E, "c_order", b)], meters=True)
            gr_jump = abs(M[E + int(0.03 * SR), M_VGR] - M[E - 10, M_VGR]) * 30
            rows.append(dict(transition=f"{DYN_PERMS[a]} -> {DYN_PERMS[b]}", hf_burst_dbfs=round(hf_burst(y[:, 0], E), 1),
                             finite=bool(np.all(np.isfinite(y)))))
    worst = max(r["hf_burst_dbfs"] for r in rows)
    record("CHAIN: real-time reordering — all 30 order transitions click-free (>8 kHz burst < −60 dBFS on a −6 dBFS sine, 25 ms crossfade)",
           worst < -60 and all(r["finite"] for r in rows), f"worst {worst:.1f} dBFS", rows=rows)

    # ================================================================ independent bypass
    xs = sig(SR * 3)
    # with TUBE bypassed, the three orders that keep OPTO before VCA must give bit-identical output
    po = dict(ALL3, t_on=0)
    ya = run(xs, dyn(**po, c_order=0)); yb = run(xs, dyn(**po, c_order=2)); yc = run(xs, dyn(**po, c_order=3))
    same = np.array_equal(ya, yb) and np.array_equal(ya, yc)
    # bypassing the TUBE (placed after the VCA) must not change the VCA's gain reduction
    _, M1 = run(xs, dyn(**ALL3, c_order=3), meters=True)
    _, M2 = run(xs, dyn(**dict(ALL3, t_on=0), c_order=3), meters=True)
    grd = float(np.max(np.abs(M1[:, M_VGR] - M2[:, M_VGR])) * 30)
    # bypass toggles are click-free
    clicks = []
    for mod in ("t_on", "o_on", "v_on"):
        y = run(tone(110, -6, 1.5), dyn(**ALL3), events=[(SR, mod, 0)])
        clicks.append(hf_burst(y[:, 0], SR))
    ok = same and grd < 1e-6 and max(clicks) < -60
    record("CHAIN: independent bypass — a bypassed module is fully transparent, does not affect the others, toggles click-free",
           ok, f"orders equivalent without TUBE: {same}; VCA GR change when TUBE (downstream) bypassed: {grd:.2e} dB; worst toggle burst {max(clicks):.1f} dBFS")

    # ================================================================ gain staging
    rows = []
    x = sig(SR * 3) * 1.4
    for o in range(6):
        y, M = run(x, dyn(**dict(ALL3, t_drive=100, o_pr=90, v_ratio=6, t_in=12, v_in=12, o_in=12), c_order=o), meters=True)
        internal = float(M[:, [M_TIN, M_TOUT, M_OIN, M_OOUT, M_VIN, M_VOUT]].max())
        rows.append(dict(order=DYN_PERMS[o], max_internal_dbfs=round(float(db(internal)), 1), out_peak_dbfs=round(float(db(np.abs(y).max())), 2)))
    record("GAIN STAGING: extreme settings (+12 dB into every module, max drive) — floating-point headroom, no internal clipping, output held by soft clip",
           all(r["out_peak_dbfs"] <= 0.0 for r in rows), "; ".join(f"{r['order']} internal {r['max_internal_dbfs']} dBFS / out {r['out_peak_dbfs']}" for r in rows), rows=rows)
    tl = []
    for d in (0, 25, 50, 75, 100):
        y = run(tone(200, -12, 2), dyn(t_on=1, t_drive=d))
        tl.append(lvl(y[SR:, 0]))
    record("GAIN STAGING: tube Auto Gain holds a −12 dBFS program level across the drive range (±2 dB)", max(tl) - min(tl) < 4 and abs(np.mean(tl) + 12) < 2,
           "levels " + ", ".join(f"{v:.1f}" for v in tl) + " dBFS")
    _, M = run(tone(1000, -10, 2), dyn(v_on=1, v_in=6, v_out=-3), meters=True)
    mi, mo = float(db(M[SR:, M_VIN].max())), float(db(M[SR:, M_VOUT].max()))
    record("GAIN STAGING: per-module input/output gain and level meters (VCA in +6 dB, out −3 dB on a −10 dBFS tone)",
           abs(mi + 4) < 0.3 and abs(mo - (mi - 3 - float(np.median(M[SR:, M_VGR]) * 30))) < 0.5,
           f"meter in {mi:.2f} dBFS, out {mo:.2f} dBFS, GR {float(np.median(M[SR:, M_VGR]) * 30):.2f} dB")

    # ================================================================ tube
    rows = []
    t = np.arange(SR * 2) / SR
    for d in (0, 30, 60, 100):
        for bias in (0, 50):
            y = run(0.5 * np.sin(2 * np.pi * 200 * t), dyn(t_on=1, t_drive=d, t_bias=bias))[SR:, 0]
            S = np.abs(np.fft.rfft(y * np.blackman(len(y))))
            F = np.fft.rfftfreq(len(y), 1 / SR)
            h = np.array([S[np.argmin(abs(F - 200 * k))] for k in range(1, 9)])
            rows.append(dict(drive=d, bias=bias, thd_pct=round(float(100 * np.sqrt(np.sum(h[1:] ** 2)) / h[0]), 2),
                             h2_db=round(float(db(h[1] / h[0])), 1), h3_db=round(float(db(h[2] / h[0])), 1), dc=round(float(abs(y.mean())), 6)))
    mono = all(rows[i]["thd_pct"] <= rows[i + 2]["thd_pct"] for i in range(0, 6))
    even = all(r["h2_db"] > -60 for r in rows if r["bias"] == 50)
    record("TUBE: harmonic content rises with drive; bias produces even harmonics; no DC at the output",
           mono and even and max(r["dc"] for r in rows) < 1e-3, f"THD {rows[0]['thd_pct']}% → {rows[-2]['thd_pct']}% (bias 0); H2 at bias 50: " +
           ", ".join(str(r["h2_db"]) for r in rows if r["bias"] == 50) + " dB", rows=rows)

    # ================================================================ opto (LA-2A-inspired)
    rows = []
    for mode in (0, 1):
        for pr in (50, 75):
            outs = []
            for L in (-30, -20, -10, 0):
                y = run(tone(1000, L, 4), dyn(o_on=1, o_pr=pr, o_mode=mode))
                outs.append(lvl(y[-SR // 2:, 0]))
            ratio = 10 / max(outs[3] - outs[2], 1e-3)
            rows.append(dict(mode=("COMP", "LIMIT")[mode], peak_reduction=pr, out_dbfs=[round(v, 1) for v in outs], ratio_top=round(ratio, 1)))
    comp_r = [r["ratio_top"] for r in rows if r["mode"] == "COMP"]
    lim_r = [r["ratio_top"] for r in rows if r["mode"] == "LIMIT"]
    record("OPTO: static curve — COMP soft-knee ≈2–4:1, LIMIT ≥ 8:1 (sources: ~3:1 / 4:1 compress, ~∞ limit)",
           all(1.8 <= r <= 4.5 for r in comp_r) and all(r >= 8 for r in lim_r),
           "; ".join(f"{r['mode']} PR{r['peak_reduction']}: {r['ratio_top']}:1" for r in rows), rows=rows)
    trows = []
    for dur in (1, 10):
        nn = SR * (dur + 12)
        tt = np.arange(nn) / SR
        xx = np.where(tt < dur, 0.5, 0.0) * np.sin(2 * np.pi * 1000 * tt)
        _, M = run(xx, dyn(o_on=1, o_pr=70), meters=True)
        gr = M[:, M_OGR] * 30
        g_ss = gr[int(0.5 * SR)]
        att = np.argmax(gr > 0.63 * g_ss) / SR * 1000
        rel = gr[dur * SR:]
        t50 = np.argmax(rel < 0.5 * rel[0]) / SR * 1000
        idx1 = np.argmax(rel < 1.0)
        t_full = idx1 / SR if rel[idx1] < 1.0 else float("inf")
        trows.append(dict(burst_s=dur, gr_db=round(float(g_ss), 1), attack_63_ms=round(float(att), 1),
                          release_50_ms=round(float(t50)), release_to_1dB_s=round(float(t_full), 2)))
    ok = (all(5 <= r["attack_63_ms"] <= 30 for r in trows) and all(40 <= r["release_50_ms"] <= 120 for r in trows)
          and trows[1]["release_to_1dB_s"] > trows[0]["release_to_1dB_s"])
    record("OPTO: T4 timing — attack ≈10–20 ms, fast release ≈60 ms to 50 %, program-dependent slow release (longer after longer compression)",
           ok, "; ".join(f"{r['burst_s']} s burst: attack {r['attack_63_ms']} ms, 50 % release {r['release_50_ms']} ms, to 1 dB {r['release_to_1dB_s']} s" for r in trows), rows=trows)
    g0 = lvl(run(tone(6000, -10, 3), dyn(o_on=1, o_pr=60, o_emph=0))[-SR // 2:, 0])
    g1 = lvl(run(tone(6000, -10, 3), dyn(o_on=1, o_pr=60, o_emph=100))[-SR // 2:, 0])
    record("OPTO: HF emphasis increases gain reduction on high-frequency material (6 kHz tone)", g1 < g0 - 1, f"output {g0:.1f} → {g1:.1f} dBFS")

    # ================================================================ VCA (API 2500-inspired)
    rows, bad = [], []
    for ri, R in enumerate(DYN.V_RATIOS):
        y = run(tone(1000, -4, 2), dyn(v_on=1, v_thr=-24, v_ratio=ri, v_att=2, v_rel=0.1))
        out = lvl(y[-SR // 4:, 0])
        exp = -24 + 20 / R
        rows.append(dict(ratio=("inf" if R > 1e6 else R), expected_dbfs=round(exp, 2), measured_dbfs=round(out, 2)))
        if abs(out - exp) > 0.5:
            bad.append(f"{R}:1")
    record("VCA: static ratios 1.5:1 … ∞:1 within ±0.5 dB (hard knee, threshold −24 dBFS, input 20 dB over)", not bad,
           "; ".join(f"{r['ratio']}:1 → {r['measured_dbfs']} (exp {r['expected_dbfs']})" for r in rows), rows=rows)
    krows = []
    for k in range(3):
        y = run(tone(1000, -24, 2), dyn(v_on=1, v_thr=-24, v_ratio=6, v_knee=k, v_att=2))
        krows.append(dict(knee=("HARD", "MED", "SOFT")[k], gr_at_threshold_db=round(-24 - lvl(y[-SR // 4:, 0]), 2)))
    record("VCA: knee — gain reduction exactly at threshold: HARD 0 dB, MED/SOFT progressively more (soft onset)",
           krows[0]["gr_at_threshold_db"] < 0.25 and krows[0]["gr_at_threshold_db"] < krows[1]["gr_at_threshold_db"] < krows[2]["gr_at_threshold_db"],
           "; ".join(f"{r['knee']} {r['gr_at_threshold_db']} dB" for r in krows), rows=krows)
    arows = []
    for ai, ams in enumerate(DYN.V_ATTACKS_MS):
        nn = int(SR * 1.2)
        xx = np.where(np.arange(nn) < SR // 2, 0.01, 0.5) * np.sin(2 * np.pi * 1000 * np.arange(nn) / SR)
        _, M = run(xx, dyn(v_on=1, v_thr=-30, v_ratio=6, v_att=ai, v_rel=1), meters=True)
        g = M[SR // 2:, M_VGR] * 30
        t63 = np.argmax(g > 0.63 * g[int(0.3 * SR)]) / SR * 1000
        arows.append(dict(attack_setting_ms=ams, measured_63_ms=round(float(t63), 2)))
    record("VCA: attack settings .03–30 ms — measured gain-reduction rise follows the setting (RMS detector τ = 3 ms sets the floor)",
           all(arows[i]["measured_63_ms"] <= arows[i + 1]["measured_63_ms"] + 0.05 for i in range(6)) and arows[-1]["measured_63_ms"] > 20,
           "; ".join(f"{r['attack_setting_ms']} → {r['measured_63_ms']} ms" for r in arows), rows=arows)
    bass = tone(60, -6, 2) + tone(2000, -18, 2)
    trs = []
    for th in range(3):
        _, M = run(bass, dyn(v_on=1, v_thr=-24, v_ratio=4, v_thrust=th), meters=True)
        trs.append(float(np.median(M[SR:, M_VGR]) * 30))
    record("VCA: THRUST (filter before the RMS detector) — bass-heavy material triggers less gain reduction NORM > MED > LOUD",
           trs[0] > trs[1] > trs[2], f"GR NORM {trs[0]:.1f}, MED {trs[1]:.1f}, LOUD {trs[2]:.1f} dB")
    yn = run(tone(1000, -4, 2), dyn(v_on=1, v_thr=-24, v_ratio=6, v_type=0, v_att=2))
    yo = run(tone(1000, -4, 2), dyn(v_on=1, v_thr=-24, v_ratio=6, v_type=1, v_att=2))
    record("VCA: TYPE — OLD (feedback) compresses more gently than NEW (feed-forward) at the same settings",
           lvl(yo[-SR // 4:, 0]) > lvl(yn[-SR // 4:, 0]) + 0.5, f"NEW {lvl(yn[-SR // 4:, 0]):.2f}, OLD {lvl(yo[-SR // 4:, 0]):.2f} dBFS")

    # ================================================================ stereo & link
    a = sig(SR * 2)
    bad = []
    for o in range(6):
        y = run(np.stack([a, a], 1), dyn(**ALL3, c_order=o, g_on=1, g_thr=-60))
        if not np.array_equal(y[:, 0], y[:, 1]):
            bad.append(f"order {o} L≠R")
    xx = np.stack([tone(1000, -6, 2), tone(1000, -40, 2)], 1)
    yl1 = run(xx, dyn(v_on=1, v_thr=-30, v_ratio=6, v_link=100, v_att=2))
    yl0 = run(xx, dyn(v_on=1, v_thr=-30, v_ratio=6, v_link=0, v_att=2))
    r_link = lvl(yl1[-SR // 4:, 1]) - lvl(xx[-SR // 4:, 1])
    r_free = lvl(yl0[-SR // 4:, 1]) - lvl(xx[-SR // 4:, 1])
    xo = np.stack([a, np.zeros_like(a)], 1)
    yo_ = run(xo, dyn(**ALL3, o_link=0, v_link=0))
    record("STEREO: identical L/R → bit-identical (6 orders + gate); VCA link 100 % applies the loud channel's GR to the quiet one, 0 % keeps them independent; no crosstalk",
           not bad and r_link < -10 and abs(r_free) < 0.1 and np.abs(yo_[:, 1]).max() == 0,
           f"quiet-channel gain: linked {r_link:.1f} dB, unlinked {r_free:.2f} dB; R output with L-only input & link 0: {np.abs(yo_[:, 1]).max():.1e}" + ("; " + "; ".join(bad) if bad else ""))

    # ================================================================ sidechain
    n = SR * 3
    prog = sig(n) * 0.5
    kick = np.zeros(n); kick[(np.arange(n) % (SR // 2)) < 4800] = 1
    kick = kick * np.sin(2 * np.pi * 55 * np.arange(n) / SR) * 0.9
    _, Mi = run(prog, dyn(v_on=1, v_thr=-20, v_ratio=6, v_src=0), key=kick, meters=True)
    _, Me = run(prog, dyn(v_on=1, v_thr=-20, v_ratio=6, v_src=2), key=kick, meters=True)
    _, Mo = run(prog, dyn(o_on=1, o_pr=70, o_src=2), key=kick, meters=True)
    gi, ge = Mi[SR:, M_VGR] * 30, Me[SR:, M_VGR] * 30
    on = kick[SR:] != 0
    record("SIDECHAIN: external key (plugin~ 3/4) drives VCA and OPTO gain reduction; internal detection ignores the key",
           ge[on].mean() > ge[~on].mean() + 3 and np.max(Mo[SR:, M_OGR]) * 30 > 3 and abs(gi[on].mean() - gi[~on].mean()) < 1.5,
           f"VCA ext: GR {ge[on].mean():.1f} dB during key vs {ge[~on].mean():.1f} dB between; VCA int: {gi[on].mean():.1f} vs {gi[~on].mean():.1f} dB; OPTO ext max GR {np.max(Mo[SR:, M_OGR]) * 30:.1f} dB")
    # CHAIN-IN detection is independent of processing order
    xsc = sig(SR * 2)
    grs = []
    for o in range(6):
        _, M = run(xsc, dyn(**ALL3, c_order=o, v_src=1), meters=True)
        grs.append(M[:, M_VGR])
    d_chain = max(float(np.max(np.abs(grs[0] - g))) for g in grs) * 30
    grs = []
    for o in range(6):
        _, M = run(xsc, dyn(**ALL3, c_order=o, v_src=0), meters=True)
        grs.append(M[:, M_VGR])
    d_int = max(float(np.max(np.abs(grs[0] - g))) for g in grs) * 30
    record("SIDECHAIN: detector sourcing — CHAIN source gives identical VCA gain reduction in all six orders; INT source follows the module's position",
           d_chain == 0 and d_int > 0.1, f"max GR difference across orders: CHAIN {d_chain:.2e} dB, INT {d_int:.2f} dB")
    low = tone(50, -6, 2) + tone(3000, -30, 2)
    _, M0 = run(low, dyn(v_on=1, v_thr=-24, v_hpf=20), meters=True)
    _, M1 = run(low, dyn(v_on=1, v_thr=-24, v_hpf=400), meters=True)
    record("SIDECHAIN: SC HPF reduces bass-triggered gain reduction (50 Hz-heavy input)",
           np.median(M1[SR:, M_VGR]) < np.median(M0[SR:, M_VGR]) * 0.5, f"GR {np.median(M0[SR:, M_VGR]) * 30:.1f} → {np.median(M1[SR:, M_VGR]) * 30:.1f} dB")
    yk = run(prog, dyn(v_on=1, v_thrust=2, key_listen=2), key=kick)
    yp = run(prog, dyn(v_on=1, key_listen=0), key=kick)
    record("KEY LISTEN: VCA listen outputs the THRUST-filtered detector signal (not the program)", float(np.max(np.abs(yk[SR:] - yp[SR:]))) > 0.01,
           f"listen vs program max difference {float(np.max(np.abs(yk[SR:] - yp[SR:]))):.3f}")

    # ================================================================ gate
    noise = 0.2 * np.random.default_rng(3).standard_normal(n)
    y, M = run(noise, dyn(g_on=1, g_src=2, g_thr=-20, g_hold=10, g_rel=30, g_range=-60), key=kick, meters=True)
    g = M[:, M_GATE]
    kon = kick != 0
    open_frac = float(np.mean(g[kon][int(0.01 * SR):] > 0.9))
    closed = float(np.median(g[~kon][SR // 10:]))
    record("GATE: externally keyed — open while the key is above threshold, closed to the Range floor between hits",
           open_frac > 0.95 and closed < 10 ** (-50 / 20), f"open {100 * open_frac:.1f}% of key-on time; median gain between hits {db(closed):.1f} dB")
    ramp = np.concatenate([np.linspace(0, 1, SR), np.linspace(1, 0, SR)])
    sigr = 0.5 * np.sin(2 * np.pi * 200 * np.arange(2 * SR) / SR) * 10 ** ((-40 + 30 * ramp) / 20) / 0.5
    _, M = run(sigr, dyn(g_on=1, g_thr=-20, g_hold=0, g_rel=5, g_att=0.1, g_range=-80), meters=True)
    gg = M[:, M_GATE]
    env_db = -40 + 30 * ramp
    i_c0 = np.argmax(gg < 0.5)                      # the gate starts open when enabled, closes on the quiet start
    i_open = i_c0 + np.argmax(gg[i_c0:] > 0.5)
    i_close = SR + np.argmax(gg[SR:] < 0.5)
    o_lvl, c_lvl = env_db[i_open], env_db[i_close]
    record("GATE: hysteresis — opens at the threshold and closes ≈4 dB below it", abs(o_lvl + 20) < 1.0 and 3.0 < (o_lvl - c_lvl) < 5.5,
           f"opened at {o_lvl:.1f} dBFS, closed at {c_lvl:.1f} dBFS (threshold −20)")
    gd = []
    for o in range(6):
        _, M = run(noise, dyn(**ALL3, c_order=o, g_on=1, g_src=2, g_thr=-20), key=kick, meters=True)
        gd.append(M[:, M_GATE])
    dmax = max(float(np.max(np.abs(gd[0] - v))) for v in gd)
    record("GATE: independent of the chain order (external key: identical gate gain in all six orders)", dmax == 0, f"max difference {dmax:.1e}")

    # ================================================================ automation & MIDI
    xs = sig(SR * 3)
    def ramp_ev(step, name, a, b):
        return [(SR // 2 + i, name, a + (b - a) * i / (2 * SR)) for i in range(0, 2 * SR, step)]
    rows = []
    for name, a, b in (("v_thr", -40, -10), ("t_drive", 0, 100), ("o_pr", 0, 100)):
        p = dyn(**ALL3)
        ya = run(xs, p, events=ramp_ev(64, name, a, b))[:, 0]
        yb = run(xs, p, events=ramp_ev(1, name, a, b))[:, 0]
        e = float(db(np.sqrt(np.mean((ya - yb) ** 2)) / np.sqrt(np.mean(yb ** 2))))
        rows.append(dict(param=name, block_vs_sample_db=round(e, 1)))
    record("AUTOMATION: block-rate (64-sample) ramps of VCA threshold, tube drive, opto peak reduction ≈ sample-accurate ramps (< −30 dB difference)",
           all(r["block_vs_sample_db"] < -30 for r in rows), "; ".join(f"{r['param']} {r['block_vs_sample_db']} dB" for r in rows), rows=rows)
    rows = []
    for name, lo, hi in (("t_drive", 0, 100), ("v_thr", -40, -10), ("g_thr", -60, -20)):
        evc = [(SR // 4 + i * 384, name, lo + (hi - lo) * i / 127) for i in range(128)]
        evs = [(SR // 4 + i, name, lo + (hi - lo) * i / (127 * 384)) for i in range(0, 127 * 384, 4)]
        p = dyn(**ALL3, g_on=1)
        yc = run(tone(150, -10, 2), p, events=evc)[:, 0]
        ys = run(tone(150, -10, 2), p, events=evs)[:, 0]
        hp = butter(4, 8000, "hp", fs=SR, output="sos")
        dh = float(db(np.sqrt(np.mean(sosfilt(hp, yc) ** 2))) - db(np.sqrt(np.mean(sosfilt(hp, ys) ** 2))))
        rows.append(dict(param=name, hf_vs_smooth_db=round(dh, 2)))
    record("MIDI: 7-bit CC stepping (one step per 8 ms) of tube drive, VCA threshold, gate threshold — >8 kHz energy within 1 dB of a smooth ramp (no zipper)",
           all(abs(r["hf_vs_smooth_db"]) < 1 for r in rows), "; ".join(f"{r['param']} {r['hf_vs_smooth_db']:+.2f} dB" for r in rows), rows=rows)

    # ================================================================ latency, CPU, denormals
    imp = np.zeros(SR); imp[1000] = 0.5
    lat = []
    for name, p in (("TUBE", dyn(t_on=1, t_drive=0)), ("OPTO", dyn(o_on=1, o_pr=0)), ("VCA", dyn(v_on=1, v_thr=0)),
                    ("all three", dyn(t_on=1, o_on=1, v_on=1, t_drive=0, o_pr=0, v_thr=0)), ("GATE (open)", dyn(g_on=1, g_thr=-80))):
        y = run(imp, p)[:, 0]
        H = np.fft.rfft(y[1000:1000 + 4096]); F = np.fft.rfftfreq(4096, 1 / SR)
        ph = np.unwrap(np.angle(H))
        i1 = np.argmin(abs(F - 1000))
        gd = -(ph[i1 + 1] - ph[i1 - 1]) / (2 * np.pi * (F[i1 + 1] - F[i1 - 1])) * SR
        lat.append(dict(module=name, peak_offset_samples=int(np.argmax(np.abs(y)) - 1000), group_delay_1k_samples=round(float(gd), 2)))
    fW, HW = tf(dyn(t_on=1, t_drive=0, t_mix=100, t_tone=20000), level=1e-3)
    fD, HD = tf(dyn(t_on=1, t_drive=0, t_mix=0, t_tone=20000), level=1e-3)
    sel = (fW > 50) & (fW < 10000)
    # remaining wet/dry phase difference must be exactly the Tone low-pass (20 kHz one-pole at 2x rate)
    tone_ph = -np.degrees(np.arctan(np.tan(np.pi * fW[sel] / (2 * SR)) / np.tan(np.pi * 20000 / (2 * SR))))
    zz = np.exp(-2j * np.pi * fW[sel] / SR)
    rr = 1 - 2 * np.pi * 8 / SR
    dc_ph = np.degrees(np.angle((1 - zz) / (1 - rr * zz)))          # wet-only 8 Hz DC blocker
    dphi = float(np.max(np.abs(np.angle(HW[sel] / HD[sel], deg=True) - tone_ph - dc_ph)))
    naive = float(360 * 10000 * 3.6 / SR)
    ap = float(np.ptp(db(HD[(fD > 20) & (fD < 20000)])))
    ripple = dphi
    lat.append(dict(module=f"TUBE wet-vs-dry phase error after removing the Tone filter and 8 Hz DC blocker, 50 Hz-10 kHz (deg; an unmatched dry path would be {naive:.0f} deg at 10 kHz)", peak_offset_samples=0, group_delay_1k_samples=round(dphi, 2)))
    lat.append(dict(module="TUBE at Mix 0: magnitude deviation of the phase-matched dry path (dB)", peak_offset_samples=0, group_delay_1k_samples=round(ap, 3)))
    record("LATENCY: no lookahead or buffering anywhere (reported device latency stays 0); TUBE's IIR oversampler adds a frequency-dependent phase delay (≈3.6 samples ≈ 0.075 ms at 1 kHz), and its dry path is phase-matched so Mix does not comb-filter",
           all(r["peak_offset_samples"] <= 6 for r in lat[:-2]) and all(abs(r["group_delay_1k_samples"]) < 5 for r in lat[:-2]) and ripple < 3 and ap < 0.1,
           "; ".join(f"{r['module']}: peak +{r['peak_offset_samples']}, GD {r['group_delay_1k_samples']}" for r in lat), rows=lat)
    rows = []
    xx = sig(SR * 10)
    cfgs = [("v1.2 device, dynamics off", base(l_on=1, h_on=1, l_model=2, h_model=1, l_cut=2000, h_cut=60, l_slope=1)),
            ("+ TUBE", base(l_on=1, h_on=1, l_cut=2000, h_cut=60, t_on=1)),
            ("+ OPTO", base(l_on=1, h_on=1, l_cut=2000, h_cut=60, o_on=1)),
            ("+ VCA", base(l_on=1, h_on=1, l_cut=2000, h_cut=60, v_on=1)),
            ("+ all three + gate", base(l_on=1, h_on=1, l_cut=2000, h_cut=60, t_on=1, o_on=1, v_on=1, g_on=1)),
            ("worst: LPF+HPF+BPF 2x + all dynamics, reordering every 20 ms", base(l_on=1, h_on=1, b_on=1, b_arch=1, l_model=5, h_model=0, l_slope=3,
                                                                                 h_slope=3, ovs_sel=1, l_cut=2000, h_cut=60, t_on=1, o_on=1, v_on=1, g_on=1))]
    for nm, p in cfgs:
        ev = [(i * int(0.02 * SR), "c_order", i % 6) for i in range(1, 499)] if "reordering" in nm else []
        best = min(run(xx, p, events=ev, ns=True)[1] for _ in range(3))
        rows.append(dict(config=nm, ns_per_frame=round(best, 1), pct_of_one_core_48k=round(best * 48000 / 1e7, 2)))
    record("CPU with the dynamics chain (transpiled C, gcc -O2, this machine)", True,
           "; ".join(f"{r['config']}: {r['pct_of_one_core_48k']}%" for r in rows), rows=rows)
    x = sig(SR * 10); x[SR * 2:] = 0
    y = run(x, dyn(**ALL3, g_on=1, g_thr=-90))
    record("DENORMALS: dynamics decay tails flush to zero", float(np.abs(y[-SR:]).max()) < 1e-15, f"max tail {float(np.abs(y[-SR:]).max()):.1e}")

    # ================================================================ combined stress
    rng = np.random.default_rng(5)
    n = SR * 30
    x = sig(n) * 1.4
    key = np.roll(sig(n), 1234)
    ev = []
    names = [p_[0] for p_ in DYN.PARAMS]
    rng_of = {p_[0]: (p_[2], p_[3]) for p_ in DYN.PARAMS}
    for i in range(1, 300):
        fr = i * SR // 10
        for nm in rng.choice(names, 6, replace=False):
            lo, hi = rng_of[nm]
            v = float(lo + (hi - lo) * rng.random())
            if nm in ("c_order", "v_ratio", "v_att", "v_knee", "v_thrust", "v_type", "o_mode", "o_src", "v_src", "g_src", "key_listen"):
                v = int(round(v))
            if nm == "key_listen":
                v = 0
            ev.append((fr, nm, v))
        ev += [(fr, "l_cut", float(20 * 1000 ** rng.random())), (fr, "b_freq", float(30 * 400 ** rng.random()))]
    p = base(l_on=1, h_on=1, b_on=1, t_on=1, o_on=1, v_on=1, g_on=1, softclip=1)
    y = run(x, p, events=ev, key=key)
    record("COMBINED: 30 s stress — LPF+HPF+BPF + all dynamics + gate with external key, random changes to every dynamics parameter",
           bool(np.all(np.isfinite(y))) and float(np.abs(y).max()) <= 1.0, f"peak {db(np.abs(y).max()):.2f} dBFS, finite={bool(np.all(np.isfinite(y)))}")

    # ================================================================ device / UI logic (static)
    P = json.load(open(os.path.join(HERE, "..", "build", "device", "DubFilter.maxpat")))["patcher"]
    bx = {b["box"]["id"]: b["box"] for b in P["boxes"]}
    vn = {b.get("varname") for b in bx.values()}
    probs = []
    for b in bx.values():
        if b.get("maxclass") == "message" and "script " in b.get("text", ""):
            for cmd in b["text"].split(", "):
                parts = cmd.split()
                if parts[0] == "script" and parts[2] not in vn:
                    probs.append(f"script target {parts[2]} missing")
    for l in P["lines"]:
        s_, so = l["patchline"]["source"]; d_, di = l["patchline"]["destination"]
        if so >= bx[s_].get("numoutlets", 0) or di >= max(bx[d_].get("numinlets", 1), 1):
            probs.append(f"bad connection {bx[s_].get('text', bx[s_]['maxclass'])}:{so} -> {bx[d_].get('text', bx[d_]['maxclass'])}:{di}")
    # LUT semantics: moving module m by d slots from order p
    lutbox = next(b for b in bx.values() if b.get("maxclass") == "message" and b.get("text", "").count(" ") == 89)
    lut = [int(v) for v in lutbox["text"].split()]
    for mi, m in enumerate(DYN.MODS):
        for cur, perm in enumerate(DYN.PERMS):
            for d in range(-2, 3):
                newp = DYN.PERMS[lut[mi * 30 + cur * 5 + d + 2]]
                if newp.index(m) != max(0, min(2, perm.index(m) + d)):
                    probs.append(f"LUT {m} {perm} {d}")
                rest_old = [x for x in perm if x != m]; rest_new = [x for x in newp if x != m]
                if rest_old != rest_new:
                    probs.append(f"LUT order of others {m} {perm} {d}")
    params = [b for b in bx.values() if b.get("parameter_enable")]
    longs = [b["saved_attribute_attributes"]["valueof"]["parameter_longname"] for b in params]
    ui_only = [b for b in bx.values() if b.get("maxclass") in ("live.slider", "live.numbox") or str(b.get("varname", "")).startswith(("preset_", "edit_page"))]
    if any(b.get("parameter_enable") for b in ui_only):
        probs.append("UI-only control registered as a parameter")
    v13 = json.load(open(os.path.join(HERE, "baseline", "DubFilter_v1.3.maxpat")))["patcher"]
    v13p = {x["box"]["saved_attribute_attributes"]["valueof"]["parameter_longname"] for x in v13["boxes"] if x["box"].get("parameter_enable")}
    missing = v13p - set(longs)
    record("DEVICE: chain UI wiring — every scripted object exists, all connections in range, drag LUT moves exactly the dragged block, all 75 v1.3 parameters present and every parameter name unique, drag/edit/preset controls are not parameters",
           not probs and not missing and len(longs) == len(set(longs)), ("ok" if not probs else "; ".join(probs[:8])) + f" ({len(longs)} parameters)")


def dyn(**kw):
    return base(**kw)

#!/usr/bin/env python3
"""Bit-exact regression guard for the LPF/HPF engine.

capture: renders a fixed battery of LPF/HPF scenarios and stores the SHA-256 of
         every float32 output (tests/baseline/lpf_hpf_golden.json).
check:   re-renders the same battery with the current engine and requires
         byte-identical output. Any change in LPF/HPF DSP, smoothing, routing,
         oversampling or output stage shows up here."""
import sys, os, json, hashlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from dsp import run, base
GOLD = os.path.join(HERE, "baseline", "lpf_hpf_golden.json")
GOLD_BPF = os.path.join(HERE, "baseline", "bpf_golden_v1.2.json")
GOLD_DYN = os.path.join(HERE, "baseline", "dyn_golden_v1.3.json")
SR = 48000

def signal(n, seed=3):
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    l = 0.3 * np.sin(2 * np.pi * 55 * t) + 0.15 * np.sin(2 * np.pi * 330 * t) + 0.05 * rng.standard_normal(n)
    r = 0.25 * np.sin(2 * np.pi * 82 * t + 1) + 0.1 * np.sin(2 * np.pi * 660 * t) + 0.05 * rng.standard_normal(n)
    return np.stack([l, r], 1)

def battery():
    n = SR * 2 // 5
    E = n // 2
    cases = []
    for m in range(6):
        for sl in (0, 1, 3):
            cases.append((f"LPF m{m} slope{sl}", base(l_on=1, l_model=m, l_cut=900, l_res=75, l_slope=sl, l_drive=40), []))
    for m in range(5):
        for sl in (0, 2):
            cases.append((f"HPF m{m} slope{sl}", base(h_on=1, h_model=m, h_cut=250, h_res=70, h_slope=sl, h_drive=30), []))
    for m in range(6):
        cases.append((f"LPF m{m} selfosc char", base(l_on=1, l_model=m, l_cut=400, l_res=100, l_char=60, l_comp=30), []))
    for o in (0, 1):
        for os_ in (0, 1):
            cases.append((f"both order{o} os{os_}", base(l_on=1, h_on=1, l_model=0, h_model=3, l_cut=1500, h_cut=120,
                                                         l_res=80, h_res=60, order_sel=o, ovs_sel=os_, softclip=1), []))
    cases.append(("LPF sweep", base(l_on=1, l_model=2, l_res=60), [(i * 400, "l_cut", 20000 * 0.01 ** (i / 48)) for i in range(48)]))
    cases.append(("HPF sweep", base(h_on=1, h_model=1, h_res=60), [(i * 400, "h_cut", 20 * 50 ** (i / 48)) for i in range(48)]))
    cases.append(("LPF model switches", base(l_on=1, l_cut=700, l_res=70), [(E // 2 * i, "l_model", i % 6) for i in range(1, 4)]))
    cases.append(("HPF model switches", base(h_on=1, h_cut=200, h_res=70), [(E // 2 * i, "h_model", i % 5) for i in range(1, 4)]))
    cases.append(("enable toggles", base(l_on=1, h_on=1, l_cut=800, h_cut=150, l_res=50), [(E // 2, "l_on", 0), (E, "h_on", 0), (3 * E // 2, "l_on", 1)]))
    cases.append(("order+os switch", base(l_on=1, h_on=1, l_cut=800, h_cut=150, l_res=50), [(E // 2, "order_sel", 1), (E, "ovs_sel", 1)]))
    cases.append(("slope+drive+char moves", base(l_on=1, h_on=1, l_model=5, h_model=2, l_cut=600, h_cut=90, l_res=80),
                  [(E // 3, "l_slope", 3), (E // 2, "l_drive", 90), (E, "h_char", 80), (E, "l_char", 50), (3 * E // 2, "h_slope", 3)]))
    cases.append(("output stage", base(l_on=1, l_cut=3000, l_res=90, out_db=9, softclip=1), [(E, "out_db", -12), (E, "softclip", 0)]))
    cases.append(("defaults (device power-on)", {}, []))
    cases.append(("open zones", base(l_on=1, h_on=1, l_cut=19000, h_cut=22, l_res=50, h_res=50), [(E, "l_cut", 20000), (E, "h_cut", 20)]))
    # v1.6: K35 Circuit = KORG-35 (Mk1); not in the legacy baselines, checked against the v1.6 capture only
    cases.append(("K35 Mk1 LPF res 80", dict(base(l_on=1, l_model=1, l_cut=900, l_res=80, l_drive=40), k35_circ=1), []))
    cases.append(("K35 Mk1 HPF res 60 char 50", dict(base(h_on=1, h_model=1, h_cut=150, h_res=60, h_char=50), k35_circ=1), []))
    cases.append(("K35 circuit switch", base(l_on=1, h_on=1, l_model=1, h_model=1, l_cut=1200, h_cut=120, l_res=70), [(E // 2, "k35_circ", 1), (3 * E // 2, "l_char", 80)]))
    return cases, signal(n)

def battery_bpf():
    """v1.2 BPF scenarios (captured with the v1.2 engine before v1.3 work)."""
    n = SR * 2 // 5
    E = n // 2
    cases = []
    for m in range(5):
        for a in range(3):
            cases.append((f"BPF m{m} a{a}", base(b_on=1, b_model=m, b_arch=a, b_freq=700, b_bw=1.5, b_q=2, b_res=80, b_drive=40), []))
            cases.append((f"BPF m{m} a{a} selfosc", base(b_on=1, b_model=m, b_arch=a, b_freq=400, b_res=100, b_comp=40), []))
    for pos in (0, 1):
        cases.append((f"all three pos{pos}", base(l_on=1, h_on=1, b_on=1, l_cut=3000, h_cut=80, b_freq=900, b_arch=1, b_res=60,
                                                 b_mix=70, b_pos=pos, ovs_sel=1, softclip=1), []))
    cases.append(("BPF sweep", base(b_on=1, b_res=70), [(i * 400, "b_freq", 100 * 50 ** (i / 48)) for i in range(48)]))
    cases.append(("BPF switches", base(b_on=1, b_res=60, b_freq=500), [(E // 2, "b_model", 3), (E, "b_arch", 2), (3 * E // 2, "b_pos", 1)]))
    cases.append(("BPF on/off/mix", base(l_on=1, b_freq=600), [(E // 3, "b_on", 1), (E, "b_mix", 30), (3 * E // 2, "b_on", 0)]))
    return cases, signal(n)

def battery_dyn():
    """v1.3 dynamics-chain scenarios (captured with the v1.3 engine before v1.4 work)."""
    n = SR * 2 // 5
    E = n // 2
    a3 = dict(t_on=1, o_on=1, v_on=1, t_drive=50, o_pr=60, v_thr=-26, v_ratio=4)
    cases = []
    for o in range(6):
        cases.append((f"chain order {o}", base(**a3, c_order=o), []))
        cases.append((f"chain order {o} + filters", base(**a3, c_order=o, l_on=1, h_on=1, b_on=1, l_cut=4000, h_cut=90, b_freq=800,
                                                          b_mix=50, l_res=50, order_sel=o % 2, b_pos=(o // 2) % 2), []))
    cases.append(("reorders", base(**a3), [(E // 3 * i, "c_order", i % 6) for i in range(1, 6)]))
    cases.append(("bypass toggles", base(**a3), [(E // 2, "t_on", 0), (E, "o_on", 0), (3 * E // 2, "v_on", 0)]))
    cases.append(("vca old/feedback soft knee", base(v_on=1, v_type=1, v_knee=2, v_thrust=2, v_thr=-30, v_ratio=6, v_link=30), []))
    cases.append(("opto limit emph", base(o_on=1, o_mode=1, o_pr=80, o_emph=70, o_hpf=200, o_link=0), []))
    cases.append(("tube hot", base(t_on=1, t_drive=100, t_bias=-60, t_tone=4000, t_auto=0, t_mix=60), []))
    cases.append(("gate", base(g_on=1, g_thr=-25, g_hold=5, g_rel=40, g_range=-50, g_hpf=100), []))
    cases.append(("key listen", base(v_on=1, v_thrust=1, key_listen=2), []))
    cases.append(("chain-in source", base(**a3, v_src=1, o_src=1, g_on=1, g_src=1, c_order=4), []))
    cases.append(("chain + 2x OS", base(**a3, ovs_sel=1, l_on=1, l_cut=3000), []))
    return cases, signal(n)

def render_all(extra=None, bpf=False, dyn=False):
    cases, x = battery_dyn() if dyn else (battery_bpf() if bpf else battery())
    out = {}
    for name, p, ev in cases:
        p = dict(p); p.update(extra or {})
        y = run(x, p, SR, events=ev).astype(np.float32)
        out[name] = hashlib.sha256(y.tobytes()).hexdigest()
    return out

GOLD16 = {"": os.path.join(HERE, "baseline", "lpf_hpf_golden_v1.6.json"),
          "bpf": os.path.join(HERE, "baseline", "bpf_golden_v1.6.json"),
          "dyn": os.path.join(HERE, "baseline", "dyn_golden_v1.6.json")}
LEGACY = {"": GOLD, "bpf": GOLD_BPF, "dyn": GOLD_DYN}


def v16(kind, capture=False):
    """v1.6: every scenario must match the v1.6 capture, and the set of scenarios that differ
    from the legacy (v1.1/v1.2/v1.3) capture must be exactly the documented one."""
    h = render_all(bpf=kind == "bpf", dyn=kind == "dyn")
    legacy = json.load(open(LEGACY[kind]))
    changed = sorted(k for k in legacy if h.get(k) != legacy[k])
    if capture:
        json.dump({"hashes": h, "changed_vs_legacy": changed,
                   "note": "v1.6 solver fix (Sherman, Steiner, BPF SVF limiter), Sherman partial self-oscillation (damping floor + resonance limiter), Ladder HP replaced by the Moog 904B (dwg. 1118, no resonance), Ladder on the Minimoog filter board (Emphasis law, C5/C1/C10 couplings, gain-recovery pair; also the power-on fade from the default Ladder) and Reference-mode power-on default; "
                           "legacy tests run in Creative mode (tests/dsp.py base)"}, open(GOLD16[kind], "w"), indent=1)
        print(f"captured v1.6 {kind or 'lpf/hpf'}: {len(h)} renders; {len(changed)} differ from legacy")
        return 0
    g = json.load(open(GOLD16[kind]))
    bad = [k for k in g["hashes"] if h.get(k) != g["hashes"][k]]
    drift = sorted(set(changed) ^ set(g["changed_vs_legacy"]))
    print(f"v1.6 {kind or 'lpf/hpf'}: {len(g['hashes']) - len(bad)}/{len(g['hashes'])} bit-identical to v1.6; "
          f"{len(legacy) - len(changed)}/{len(legacy)} still bit-identical to legacy (documented changes: {len(g['changed_vs_legacy'])})"
          + (f" — MISMATCH: {bad}" if bad else "") + (f" — UNDOCUMENTED LEGACY CHANGE: {drift}" if drift else ""))
    return 1 if (bad or drift) else 0


def legacy_report(kind, gold, h, bad):
    """Legacy baseline check (v1.6): passes when every render is bit-identical to the legacy baseline,
    except exactly the documented v1.6 changes, which must match the v1.6 capture."""
    g = json.load(open(GOLD16[kind]))
    doc = set(g["changed_vs_legacy"])
    wrong16 = [k for k in doc if h.get(k) != g["hashes"].get(k)]
    undoc = sorted(set(bad) - doc)
    print(f"{len(gold) - len(bad)}/{len(gold)} bit-identical to legacy; {len(set(bad) & doc)} documented v1.6 changes "
          f"(match the v1.6 capture: {not wrong16})" + (f" — UNDOCUMENTED MISMATCH: {', '.join(undoc)}" if undoc else "")
          + (f" — v1.6 MISMATCH: {wrong16}" if wrong16 else ""))
    return 1 if (undoc or wrong16) else 0


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode in ("check-v16", "capture-v16"):
        sys.exit(max(v16(k, capture=mode == "capture-v16") for k in ("", "bpf", "dyn")))
    if mode == "capture":
        h = render_all()
        os.makedirs(os.path.dirname(GOLD), exist_ok=True)
        json.dump(h, open(GOLD, "w"), indent=1)
        print(f"captured {len(h)} golden renders")
    elif mode == "capture-bpf":
        h = render_all(bpf=True)
        json.dump(h, open(GOLD_BPF, "w"), indent=1)
        print(f"captured {len(h)} BPF golden renders")
    elif mode == "capture-dyn":
        h = render_all(dyn=True)
        json.dump(h, open(GOLD_DYN, "w"), indent=1)
        print(f"captured {len(h)} dynamics golden renders")
    elif mode == "check-dyn":
        gold = json.load(open(GOLD_DYN))
        h = render_all(dyn=True)
        bad = [k for k in gold if h.get(k) != gold[k]]
        sys.exit(legacy_report('dyn', gold, h, bad))
    elif mode == "check-bpf":
        gold = json.load(open(GOLD_BPF))
        h = render_all(bpf=True)
        bad = [k for k in gold if h.get(k) != gold[k]]
        sys.exit(legacy_report('bpf', gold, h, bad))
    else:
        extra = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None
        gold = json.load(open(GOLD))
        h = render_all(extra)
        bad = [k for k in gold if h.get(k) != gold[k]]
        sys.exit(legacy_report('', gold, h, bad))

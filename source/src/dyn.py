"""Dynamics & saturation chain (v1.3) — GenExpr library + code emitters.

Three reorderable modules + an independent gate, processed at the base sample
rate after the filter section (LPF/HPF/BPF) and before the output stage:

    filters -> [ slot 1 -> slot 2 -> slot 3 ] -> GATE -> (key listen) -> DC block -> output gain -> soft clip

    modules: 0 TUBE (triode-stage saturation, 2x oversampled internally)
             1 OPTO (LA-2A-inspired T4 optical leveller, feedback detector)
             2 VCA  (API 2500-inspired RMS bus compressor, NEW/OLD type)

Reordering without clicks: the chain exists twice ("lanes" P and Q). On an
order change the complete module state of the active lane is copied into the
idle lane, the idle lane takes the new order, and the two lanes are
crossfaded over 25 ms. Compressor gain reduction, envelopes and filter states
are therefore continuous across the change; only the routing changes.

Everything is fixed-size gen~ state: no allocation, no locks, no buffering,
zero added latency.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from hiir_design import coefs as hiir_coefs

HIIR = hiir_coefs(10, 0.0227)
CA, CB = HIIR[0::2], HIIR[1::2]
CH = ["L", "R"]
LANES = ["P", "Q"]
MODS = ["T", "O", "V"]
MOD_NAMES = {"T": "TUBE", "O": "OPTO (LA-2A)", "V": "VCA (API 2500)"}
PERMS = [("T", "O", "V"), ("T", "V", "O"), ("O", "T", "V"), ("O", "V", "T"), ("V", "T", "O"), ("V", "O", "T")]
PERM_NAMES = ["TUBE > OPTO > VCA", "TUBE > VCA > OPTO", "OPTO > TUBE > VCA",
              "OPTO > VCA > TUBE", "VCA > TUBE > OPTO", "VCA > OPTO > TUBE"]
PRESETS = {"WARM DUB": 0, "PUNCH & COLOUR": 4, "FINAL COLOUR": 3}
V_RATIOS = [1.5, 2, 3, 4, 6, 10, 1e9]
V_ATTACKS_MS = [0.03, 0.1, 0.3, 1, 3, 10, 30]

PARAMS = [
    ("c_order", 0, 0, 5), ("key_listen", 0, 0, 3),
    ("t_on", 0, 0, 1), ("t_in", 0, -24, 24), ("t_out", 0, -24, 24), ("t_mix", 100, 0, 100),
    ("t_drive", 30, 0, 100), ("t_bias", 20, -100, 100), ("t_tone", 12000, 1000, 20000), ("t_auto", 1, 0, 1),
    ("o_on", 0, 0, 1), ("o_in", 0, -24, 24), ("o_out", 0, -24, 24), ("o_mix", 100, 0, 100),
    ("o_pr", 40, 0, 100), ("o_mode", 0, 0, 1), ("o_emph", 0, 0, 100), ("o_hpf", 20, 20, 500),
    ("o_src", 0, 0, 2), ("o_link", 100, 0, 100),
    ("v_on", 0, 0, 1), ("v_in", 0, -24, 24), ("v_out", 0, -24, 24), ("v_mix", 100, 0, 100),
    ("v_thr", -20, -50, 0), ("v_ratio", 3, 0, 6), ("v_att", 3, 0, 6), ("v_rel", 0.3, 0.05, 3),
    ("v_knee", 0, 0, 2), ("v_thrust", 0, 0, 2), ("v_type", 0, 0, 1), ("v_hpf", 20, 20, 500),
    ("v_src", 0, 0, 2), ("v_link", 100, 0, 100), ("v_auto", 0, 0, 1),
    ("g_on", 0, 0, 1), ("g_thr", -40, -80, 0), ("g_att", 1, 0.1, 50), ("g_hold", 20, 0, 500),
    ("g_rel", 150, 5, 2000), ("g_range", -80, -80, 0), ("g_src", 0, 0, 2), ("g_hpf", 20, 20, 2000),
    ("g_lpf", 20000, 200, 20000),
]

TUBE_ST = [f"up{p}{i}" for p in "ab" for i in range(6)] + [f"dn{p}{i}" for p in "ab" for i in range(6)] + ["ton", "dcx", "dcy"]
OPTO_ST = ["lt", "cf", "cs", "mem", "yp", "hp", "he"]
VCA_ST = ["hp", "t1", "t2", "ms", "gr", "yp"]
LANE_ST = {"T": TUBE_ST, "O": OPTO_ST, "V": VCA_ST}
GATE_ST = ["hpL", "hpR", "lpL", "lpR", "env", "open", "hold", "g"]

LIB = r"""
// ======================= DYNAMICS CHAIN (v1.3) =======================
// Triode-stage transfer: asymmetric (grid conduction on the positive side is
// harder), unit slope at 0 -> even + odd harmonics.
f_tsh(v) {
	return v > 0 ? tanh(1.25 * v) * 0.8 : tanh(0.85 * v) * 1.176470588235;
}
// biased stage, idle point removed, small-signal gain normalised by ib
f_tube(x, b, ib) {
	return (f_tsh(x + b) - f_tsh(b)) * ib;
}
// API-style gain computer (dB in -> gain change in dB, <= 0); slope = 1/R - 1, W = knee width
f_gc(lv, thr, slope, W) {
	o = lv - thr;
	r = 0;
	if (2 * o > W) {
		r = slope * o;
	} else if (2 * o > -W) {
		r = slope * (o + 0.5 * W) * (o + 0.5 * W) / (2 * W);
	}
	return r;
}
"""


def params():
    return PARAMS


def register_state(SV, CV):
    for ln in LANES:
        for m in MODS:
            for ch in CH:
                for v in LANE_ST[m]:
                    SV(f"d{ln}_{m}_{ch}_{v}")
    for v in GATE_ST:
        SV(f"dg_{v}")
    for n, i in (("t_gi", 1.0), ("t_go", 1.0), ("t_mx", 1.0), ("t_w", 0.0), ("t_dz", 0.3), ("t_bz", 0.2),
                 ("o_gi", 1.0), ("o_go", 1.0), ("o_mx", 1.0), ("o_w", 0.0), ("o_prz", 0.4), ("o_emz", 0.0), ("o_lkz", 1.0),
                 ("v_gi", 1.0), ("v_go", 1.0), ("v_mx", 1.0), ("v_w", 0.0), ("v_thz", -20.0), ("v_lkz", 1.0),
                 ("g_w", 0.0), ("kl_w", 0.0), ("kl_sel", 0),
                 ("d_oP", 0), ("d_oQ", 0), ("d_act", 0), ("d_fade", 1)):
        CV(f"H_dyn_{n}" if False else f"dz_{n}", i)


def ctrl_names():
    return ["dz_t_gi", "dz_t_go", "dz_t_mx", "dz_t_w", "dz_t_dz", "dz_t_bz", "dz_o_gi", "dz_o_go", "dz_o_mx", "dz_o_w",
            "dz_o_prz", "dz_o_emz", "dz_o_lkz", "dz_v_gi", "dz_v_go", "dz_v_mx", "dz_v_w", "dz_v_thz", "dz_v_lkz",
            "dz_g_w", "dz_kl_w", "dz_kl_sel", "dz_d_oP", "dz_d_oQ", "dz_d_act", "dz_d_fade"]


def _sm(w, name, target, coef="a_par"):
    w(f"{name} = H_{name} + {coef} * ({target} - H_{name});")


def _snap(w, name, target):
    w(f"if (abs({name} - ({target})) < 0.0001) {{")
    w(f"\t{name} = {target};")
    w("}")


def emit_controls(w, G):
    w("// ================= dynamics controls (v1.3) =================")
    db = lambda p: f"exp(0.11512925465 * clamp({p}, -24, 24))"
    for m in ("t", "o", "v"):
        _sm(w, f"dz_{m}_gi", db(f"{m}_in"))
        _sm(w, f"dz_{m}_go", db(f"{m}_out"))
        _sm(w, f"dz_{m}_mx", f"clamp({m}_mix, 0, 100) * 0.01", "a_mix")
        _snap(w, f"dz_{m}_mx", f"clamp({m}_mix, 0, 100) * 0.01")
        w(f"dz_{m}_wt = {m}_on > 0.5 ? 1 : 0;")
        _sm(w, f"dz_{m}_w", f"dz_{m}_wt", "a_mix")
        _snap(w, f"dz_{m}_w", f"dz_{m}_wt")
    # tube
    _sm(w, "dz_t_dz", "clamp(t_drive, 0, 100) * 0.01")
    _sm(w, "dz_t_bz", "clamp(t_bias, -100, 100) * 0.01")
    w("t_D = exp2(5.98 * dz_t_dz);")                       # 0 .. +36 dB
    w("t_k = 0.3 * t_D;")
    w("t_b = 0.6 * dz_t_bz;")
    w("t_tb = tanh((t_b > 0 ? 1.25 : 0.85) * t_b);")
    w("t_ib = 1 / (1 - t_tb * t_tb);")
    # auto gain: hold the level of a -12 dBFS program peak constant as drive rises
    # (mean of the stage's positive and negative excursion at that level)
    w("t_ref = 0.5 * (abs(f_tube(0.25 * t_k, t_b, t_ib)) + abs(f_tube(-0.25 * t_k, t_b, t_ib)));")
    w("t_ko = t_auto > 0.5 ? 0.25 / max(t_ref, 1e-9) : 1 / (0.3 * sqrt(t_D));")
    w("t_gt = tan(pi * min(clamp(t_tone, 1000, 20000), 0.45 * 2 * fs) / (2 * fs));")
    w("t_Gt = t_gt / (1 + t_gt);")
    w("t_dcr = 1 - 2 * pi * 8 / fs;")
    # opto
    _sm(w, "dz_o_prz", "clamp(o_pr, 0, 100) * 0.01")
    _sm(w, "dz_o_emz", "clamp(o_emph, 0, 100) * 0.01")
    _sm(w, "dz_o_lkz", "clamp(o_link, 0, 100) * 0.01")
    w("o_prg = exp(0.11512925465 * (50 * dz_o_prz - 12));")  # sidechain gain -12 .. +38 dB
    w("o_lim = o_mode > 0.5 ? 1 : 0;")
    w("o_K = o_lim > 0.5 ? 4 : 1.6;")
    w("o_p = o_lim > 0.5 ? 9 : 2;")
    w("o_aatt = 1 - exp(-1 / (0.0045 * fs));")               # cell attack (≈10 ms overall in the feedback loop)
    w("o_aela = 1 - exp(-1 / (0.002 * fs));")                # EL panel rise
    w("o_ael = 1 - exp(-1 / (0.004 * fs));")                 # EL panel decay
    w("o_afr = 1 - exp(-1 / (0.040 * fs));")                 # fast release component (≈60 ms to 50 %)
    w("o_asa = 1 - exp(-1 / (0.150 * fs));")                 # slow component charge
    w("o_amu = 1 - exp(-1 / (4.0 * fs));")                   # memory charge
    w("o_amd = 1 - exp(-1 / (20.0 * fs));")                  # memory discharge
    w("o_ghp = tan(pi * clamp(o_hpf, 20, 500) / fs);")
    w("o_Ghp = o_ghp / (1 + o_ghp);")
    w("o_ge = tan(pi * 2500 / fs);")
    w("o_Ge = o_ge / (1 + o_ge);")
    # vca
    _sm(w, "dz_v_thz", "clamp(v_thr, -50, 0)")
    _sm(w, "dz_v_lkz", "clamp(v_link, 0, 100) * 0.01")
    ri = "clamp(floor(v_ratio + 0.5), 0, 6)"
    rt = " : ".join(f"({ri} < {i + 0.5} ? {1 / r - 1!r}" for i, r in enumerate(V_RATIOS[:-1]))
    w(f"v_slope = {rt} : -1{')' * (len(V_RATIOS) - 1)};")
    ai = "clamp(floor(v_att + 0.5), 0, 6)"
    at = " : ".join(f"({ai} < {i + 0.5} ? {a!r}" for i, a in enumerate(V_ATTACKS_MS[:-1]))
    w(f"v_ams = {at} : {V_ATTACKS_MS[-1]!r}{')' * (len(V_ATTACKS_MS) - 1)};")
    w("v_aat = 1 - exp(-1 / (0.001 * v_ams * fs));")
    w("v_are = 1 - exp(-1 / (clamp(v_rel, 0.05, 3) * fs));")
    w("v_arms = 1 - exp(-1 / (0.003 * fs));")
    w("v_W = v_knee < 0.5 ? 0.0001 : (v_knee < 1.5 ? 6 : 12);")
    w("v_ghp = tan(pi * clamp(v_hpf, 20, 500) / fs);")
    w("v_Ghp = v_ghp / (1 + v_ghp);")
    w("v_g1 = tan(pi * 200 / fs);")
    w("v_G1 = v_g1 / (1 + v_g1);")
    w("v_g2 = tan(pi * 3000 / fs);")
    w("v_G2 = v_g2 / (1 + v_g2);")
    w("v_mk = v_auto > 0.5 ? exp(0.11512925465 * 0.5 * (-v_slope) * (-dz_v_thz)) : 1;")
    # gate
    w("dz_g_wt = g_on > 0.5 ? 1 : 0;")
    _sm(w, "dz_g_w", "dz_g_wt", "a_mix")
    _snap(w, "dz_g_w", "dz_g_wt")
    w("g_ghp = tan(pi * clamp(g_hpf, 20, 2000) / fs);")
    w("g_Ghp = g_ghp / (1 + g_ghp);")
    w("g_glp = tan(pi * min(clamp(g_lpf, 200, 20000), 0.45 * fs) / fs);")
    w("g_Glp = g_glp / (1 + g_glp);")
    w("g_dec = exp(-1 / (0.010 * fs));")
    w("g_aat = 1 - exp(-1 / (0.001 * clamp(g_att, 0.1, 50) * fs));")
    w("g_are = 1 - exp(-1 / (0.001 * clamp(g_rel, 5, 2000) * fs));")
    w("g_hs = 0.001 * clamp(g_hold, 0, 500) * fs;")
    w("g_floor = exp(0.11512925465 * clamp(g_range, -80, 0));")
    # key listen
    w("dz_kl_t = key_listen > 0.5 ? 1 : 0;")
    _sm(w, "dz_kl_w", "dz_kl_t", "a_mix")
    _snap(w, "dz_kl_w", "dz_kl_t")
    w("dz_kl_sel = key_listen > 0.5 ? clamp(floor(key_listen + 0.5), 1, 3) : H_dz_kl_sel;")
    # lanes / reorder
    w("dz_d_oP = H_dz_d_oP;")
    w("dz_d_oQ = H_dz_d_oQ;")
    w("dz_d_act = H_dz_d_act;")
    w("dz_d_fade = H_dz_d_fade;")
    w("d_ot = clamp(floor(c_order + 0.5), 0, 5);")
    w("d_ocur = dz_d_act < 0.5 ? dz_d_oP : dz_d_oQ;")
    w("d_cpPQ = 0;")
    w("d_cpQP = 0;")
    w("if (d_ot != d_ocur) {")
    w("\tif (dz_d_act < 0.5) {")
    w("\t\td_cpPQ = 1;")
    w("\t\tdz_d_oQ = d_ot;")
    w("\t\tdz_d_act = 1;")
    w("\t} else {")
    w("\t\td_cpQP = 1;")
    w("\t\tdz_d_oP = d_ot;")
    w("\t\tdz_d_act = 0;")
    w("\t}")
    w("\tdz_d_fade = 0;")
    w("}")
    w("dz_d_fade = min(1, dz_d_fade + fstep);")
    w("d_wP = dz_d_act < 0.5 ? dz_d_fade : 1 - dz_d_fade;")
    w("d_wQ = 1 - d_wP;")
    w("d_any = (dz_t_w + dz_o_w + dz_v_w) > 0 ? 1 : 0;")
    for ln in LANES:
        w(f"d{ln}_run = (d_any > 0.5 && d_w{ln} > 0) ? 1 : 0;")
    # state copy on reorder (all module state, both channels)
    for a, b in (("P", "Q"), ("Q", "P")):
        w(f"if (d_cp{a}{b} > 0.5) {{")
        G.ind += 1
        for m in MODS:
            for ch in CH:
                for v in LANE_ST[m]:
                    w(f"d{b}_{m}_{ch}_{v} = d{a}_{m}_{ch}_{v};")
        G.ind -= 1
        w("}")
    # reset state of disabled modules (both lanes) so re-enabling starts neutral
    for m, flag in (("T", "dz_t_w"), ("O", "dz_o_w"), ("V", "dz_v_w")):
        w(f"if ({flag} <= 0) {{")
        G.ind += 1
        for ln in LANES:
            for ch in CH:
                for v in LANE_ST[m]:
                    w(f"d{ln}_{m}_{ch}_{v} = 0;")
        G.ind -= 1
        w("}")
    w("if (dz_g_w <= 0) {")
    G.ind += 1
    for v in GATE_ST:
        w(f"dg_{v} = 0;")
    G.ind -= 1
    w("}")


def _src(sel, internal, ch):
    return f"({sel} < 0.5 ? {internal} : ({sel} < 1.5 ? cin_{ch} : key_{ch}))"


def emit_tube(w, G, ln, xin, xout, meter):
    s = lambda ch, v: f"d{ln}_T_{ch}_{v}"
    w("if (dz_t_w > 0) {")
    G.ind += 1
    for ch in CH:
        za = [s(ch, f"upa{i}") for i in range(6)]
        zb = [s(ch, f"upb{i}") for i in range(6)]
        da = [s(ch, f"dna{i}") for i in range(6)]
        db_ = [s(ch, f"dnb{i}") for i in range(6)]
        w(f"tu_{ch} = {xin[ch]} * dz_t_gi;")
        w(f"tua, {', '.join(za)} = f_ap5(tu_{ch}, {', '.join(za)}, {', '.join(repr(c) for c in CA)});")
        w(f"tub, {', '.join(zb)} = f_ap5(tu_{ch}, {', '.join(zb)}, {', '.join(repr(c) for c in CB)});")
        w(f"tya = f_tube(tua * t_k, t_b, t_ib);")
        w(f"tla, {s(ch, 'ton')} = f_op(tya, {s(ch, 'ton')}, t_Gt);")
        w(f"tyb = f_tube(tub * t_k, t_b, t_ib);")
        w(f"tlb, {s(ch, 'ton')} = f_op(tyb, {s(ch, 'ton')}, t_Gt);")
        w(f"{s(ch, 'ton')} = fixdenorm({s(ch, 'ton')});")
        w(f"tpa, {', '.join(da)} = f_ap5(tlb, {', '.join(da)}, {', '.join(repr(c) for c in CA)});")
        w(f"tpb, {', '.join(db_)} = f_ap5(tla, {', '.join(db_)}, {', '.join(repr(c) for c in CB)});")
        w(f"ty = 0.5 * (tpa + tpb) * t_ko;")
        w(f"tdy = ty - {s(ch, 'dcx')} + t_dcr * {s(ch, 'dcy')};")
        w(f"{s(ch, 'dcx')} = ty;")
        w(f"{s(ch, 'dcy')} = fixdenorm(tdy);")
        w(f"{xout[ch]} = {xin[ch]} + dz_t_w * dz_t_mx * (tdy * dz_t_go - {xin[ch]});")
    w(f"{meter}_tin = max(abs(tu_L), abs(tu_R));")
    w(f"{meter}_tout = max(abs({xout['L']}), abs({xout['R']}));")
    G.ind -= 1
    w("}")


def emit_opto(w, G, ln, xin, xout, meter):
    s = lambda ch, v: f"d{ln}_O_{ch}_{v}"
    w("if (dz_o_w > 0) {")
    G.ind += 1
    for ch in CH:
        w(f"ou_{ch} = {xin[ch]} * dz_o_gi;")
        w(f"osc_{ch} = {_src('o_src', s(ch, 'yp'), ch)};")
        w(f"ohl, {s(ch, 'hp')} = f_op(osc_{ch}, {s(ch, 'hp')}, o_Ghp);")
        w(f"osc_{ch} = osc_{ch} - ohl;")
        w(f"oel, {s(ch, 'he')} = f_op(osc_{ch}, {s(ch, 'he')}, o_Ge);")
        w(f"osc_{ch} = osc_{ch} + 3 * dz_o_emz * (osc_{ch} - oel);")
        w(f"{s(ch, 'hp')} = fixdenorm({s(ch, 'hp')});")
        w(f"{s(ch, 'he')} = fixdenorm({s(ch, 'he')});")
        w(f"olv_{ch} = abs(osc_{ch});")
    w("olm = max(olv_L, olv_R);")
    w("ogr = 0;")
    for ch in CH:
        w(f"oe = o_prg * (olv_{ch} + dz_o_lkz * (olm - olv_{ch}));")
        lt, cf, cs, mem = s(ch, "lt"), s(ch, "cf"), s(ch, "cs"), s(ch, "mem")
        w(f"{lt} = fixdenorm({lt} + (oe - {lt}) * (oe > {lt} ? o_aela : o_ael));")
        w(f"{cf} = fixdenorm({cf} + ({lt} - {cf}) * ({lt} > {cf} ? o_aatt : o_afr));")
        w(f"{mem} = fixdenorm({mem} + ({lt} - {mem}) * ({lt} > {mem} ? o_amu : o_amd));")
        w(f"oasr = 1 - exp(-1 / ((0.5 + 4.5 * clamp({mem}, 0, 1)) * fs));")
        w(f"{cs} = fixdenorm({cs} + ({lt} - {cs}) * ({lt} > {cs} ? o_asa : oasr));")
        w(f"oc = o_K * (0.6 * {cf} + 0.4 * {cs});")
        w(f"oG = 1 / (1 + pow(oc, o_p));")
        w(f"oy = ou_{ch} * oG;")
        w(f"{s(ch, 'yp')} = oy;")
        w(f"ogr = max(ogr, -20 * log10(oG));")
        w(f"{xout[ch]} = {xin[ch]} + dz_o_w * dz_o_mx * (oy * dz_o_go - {xin[ch]});")
        w(f"{meter}_osc_{ch} = osc_{ch};")
    w(f"{meter}_oin = max(abs(ou_L), abs(ou_R));")
    w(f"{meter}_oout = max(abs({xout['L']}), abs({xout['R']}));")
    w(f"{meter}_ogr = ogr;")
    G.ind -= 1
    w("}")


def emit_vca(w, G, ln, xin, xout, meter):
    s = lambda ch, v: f"d{ln}_V_{ch}_{v}"
    w("if (dz_v_w > 0) {")
    G.ind += 1
    for ch in CH:
        w(f"vu_{ch} = {xin[ch]} * dz_v_gi;")
        internal = f"(v_type > 0.5 ? {s(ch, 'yp')} : vu_{ch})"
        w(f"vs = {_src('v_src', internal, ch)};")
        w(f"vhl, {s(ch, 'hp')} = f_op(vs, {s(ch, 'hp')}, v_Ghp);")
        w(f"vs = vs - vhl;")
        w(f"v1l, {s(ch, 't1')} = f_op(vs, {s(ch, 't1')}, v_G1);")
        w(f"v2l, {s(ch, 't2')} = f_op(vs, {s(ch, 't2')}, v_G2);")
        w(f"{s(ch, 'hp')} = fixdenorm({s(ch, 'hp')});")
        w(f"{s(ch, 't1')} = fixdenorm({s(ch, 't1')});")
        w(f"{s(ch, 't2')} = fixdenorm({s(ch, 't2')});")
        # THRUST: NORM flat; MED low shelf (-6 dB below ~200 Hz); LOUD low shelf -12 dB + HF shelf +3.5 dB
        w(f"vst_{ch} = v_thrust < 0.5 ? vs : (v_thrust < 1.5 ? 0.5 * vs + 0.5 * (vs - v1l) : 0.25 * vs + 0.75 * (vs - v1l) + 0.5 * (vs - v2l));")
        w(f"{s(ch, 'ms')} = fixdenorm({s(ch, 'ms')} + (vst_{ch} * vst_{ch} - {s(ch, 'ms')}) * v_arms);")
        w(f"vlv_{ch} = 10 * log10({s(ch, 'ms')} + 1e-20) + 3.0103;")
    w("vlk = 10 * log10(0.5 * (dVms_L + dVms_R) + 1e-20) + 3.0103;".replace("dVms_L", s("L", "ms")).replace("dVms_R", s("R", "ms")))
    w("vgr = 0;")
    for ch in CH:
        gr = s(ch, "gr")
        w(f"vlv = vlv_{ch} + dz_v_lkz * (vlk - vlv_{ch});")
        w(f"vgc = f_gc(vlv, dz_v_thz, v_slope, v_W);")
        w(f"{gr} = fixdenorm({gr} + (vgc - {gr}) * (vgc < {gr} ? v_aat : v_are));")
        w(f"vy = vu_{ch} * exp(0.11512925465 * {gr});")
        w(f"{s(ch, 'yp')} = vy;")
        w(f"vgr = max(vgr, -{gr});")
        w(f"{xout[ch]} = {xin[ch]} + dz_v_w * dz_v_mx * (vy * v_mk * dz_v_go - {xin[ch]});")
        w(f"{meter}_vsc_{ch} = vst_{ch};")
    w(f"{meter}_vin = max(abs(vu_L), abs(vu_R));")
    w(f"{meter}_vout = max(abs({xout['L']}), abs({xout['R']}));")
    w(f"{meter}_vgr = vgr;")
    G.ind -= 1
    w("}")


EMIT = {"T": emit_tube, "O": emit_opto, "V": emit_vca}
METERS = ["tin", "tout", "oin", "oout", "ogr", "vin", "vout", "vgr", "osc_L", "osc_R", "vsc_L", "vsc_R"]


def emit_chain(w, G, src, dst):
    """Dynamics chain + gate + key listen on src -> dst (base rate). Untouched when nothing is active."""
    emit_controls(w, G)
    w("// ================= dynamics chain (v1.3) =================")
    w("key_L = in3;")
    w("key_R = in4;")
    w("cin_L = %s;" % src["L"])
    w("cin_R = %s;" % src["R"])
    for m in METERS:
        w(f"dm_{m} = 0;")
    w("dm_g = 1;")
    w("dm_cout = max(abs(cin_L), abs(cin_R));")
    for ln in LANES:
        for m in METERS:
            w(f"m{ln}_{m} = 0;")
    w("if (d_any > 0.5 || dz_d_fade < 1) {")
    G.ind += 1
    for ch in CH:
        w(f"dout_{ch} = 0;")
    for ln in LANES:
        w(f"if (d{ln}_run > 0.5) {{")
        G.ind += 1
        for ch in CH:
            w(f"q0_{ch} = cin_{ch};")
        for k in range(3):
            pi, po = f"q{k}", f"q{k + 1}"
            for ch in CH:
                w(f"{po}_{ch} = {pi}_{ch};")
            w(f"d{ln}_m{k} = " + " : ".join(f"(dz_d_o{ln} < {i + 0.5} ? {MODS.index(p[k])}" for i, p in enumerate(PERMS[:-1]))
              + f" : {MODS.index(PERMS[-1][k])}" + ")" * (len(PERMS) - 1) + ";")
            for mi, m in enumerate(MODS):
                w(f"if (d{ln}_m{k} == {mi}) {{")
                G.ind += 1
                EMIT[m](w, G, ln, {ch: f"{pi}_{ch}" for ch in CH}, {ch: f"{po}_{ch}" for ch in CH}, f"m{ln}")
                G.ind -= 1
                w("}")
        for ch in CH:
            w(f"dout_{ch} = dout_{ch} + d_w{ln} * q3_{ch};")
        G.ind -= 1
        w("}")
    for m in METERS:
        w(f"dm_{m} = dz_d_act < 0.5 ? mP_{m} : mQ_{m};")
    for ch in CH:
        w(f"{dst[ch]} = dout_{ch};")
    w(f"dm_cout = max(abs({dst['L']}), abs({dst['R']}));")
    G.ind -= 1
    w("}")
    # ---------------- gate (independent, after the chain)
    w("gk_L = 0;")
    w("gk_R = 0;")
    w("if (dz_g_w > 0) {")
    G.ind += 1
    for ch in CH:
        w(f"gk_{ch} = {_src('g_src', dst[ch], ch)};")
        w(f"ghl, dg_hp{ch} = f_op(gk_{ch}, dg_hp{ch}, g_Ghp);")
        w(f"gk_{ch} = gk_{ch} - ghl;")
        w(f"gk_{ch}, dg_lp{ch} = f_op(gk_{ch}, dg_lp{ch}, g_Glp);")
        w(f"dg_hp{ch} = fixdenorm(dg_hp{ch});")
        w(f"dg_lp{ch} = fixdenorm(dg_lp{ch});")
    w("gkm = max(abs(gk_L), abs(gk_R));")
    w("dg_env = fixdenorm(gkm > dg_env ? gkm : dg_env * g_dec);")
    w("gdb = 20 * log10(dg_env + 1e-9);")
    w("if (gdb > g_thr) {")
    w("\tdg_open = 1;")
    w("\tdg_hold = g_hs;")
    w("} else if (gdb < g_thr - 4) {")
    w("\tif (dg_hold > 0) {")
    w("\t\tdg_hold = dg_hold - 1;")
    w("\t} else {")
    w("\t\tdg_open = 0;")
    w("\t}")
    w("}")
    w("gtg = dg_open > 0.5 ? 1 : g_floor;")
    w("dg_g = fixdenorm(dg_g + (gtg - dg_g) * (gtg > dg_g ? g_aat : g_are));")
    for ch in CH:
        w(f"{dst[ch]} = {dst[ch]} + dz_g_w * (dst_gated - {dst[ch]});".replace("dst_gated", f"{dst[ch]} * dg_g"))
    w("dm_g = dg_g;")
    G.ind -= 1
    w("}")
    # ---------------- key listen
    w("if (dz_kl_w > 0) {")
    G.ind += 1
    for ch in CH:
        w(f"kls = dz_kl_sel < 1.5 ? dm_osc_{ch} : (dz_kl_sel < 2.5 ? dm_vsc_{ch} : gk_{ch});")
        w(f"{dst[ch]} = {dst[ch]} + dz_kl_w * (kls - {dst[ch]});")
    G.ind -= 1
    w("}")


def emit_outputs(w):
    outs = ["dm_tin", "dm_tout", "dm_oin", "dm_oout", "dm_ogr * 0.0333333", "dm_vin", "dm_vout", "dm_vgr * 0.0333333",
            "dm_g", "max(abs(key_L), abs(key_R))", "max(abs(cin_L), abs(cin_R))", "dm_cout"]
    for i, e in enumerate(outs):
        w(f"out{i + 3} = {e};")

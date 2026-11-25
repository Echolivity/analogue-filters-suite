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
# KNEE (API 225L traced schematic, VCA board): the soft knee is a 1N4148 chain to ground in the CV amplifier's gain
# network. 225L: HARD = 1 diode, SOFT = 2 (NEW) / 3 (OLD, where S2a also puts R40 2k74 across R41 6k19). The 2500's
# MED is modelled as one more diode per step: HARD 1, MED 2, SOFT 3 in both TYPEs (assumption). CV scale: the ratio
# network sets c (V per dB over threshold) so NEW's asymptote has slope 1/R - 1; OLD uses the same c with its higher
# gain network. X0 = CV at the threshold, chosen so the asymptote passes through the threshold.
V_K_SNEW = 4.724320835978319            # dB of gain change per volt of CV, NEW asymptote
V_K_RZ = {"NEW": 6190.0, "OLD": 1899.2833146696528}
V_K_X0 = {'NEW': [0.572794, 0.91464, 1.252764], 'OLD': [0.639184, 1.167696, 1.690352]}   # volts, HARD / MED / SOFT
V_K_A1 = 0.045292704                 # n * VT of one 1N4148
V_AUTO_REF_DBFS = -18.0   # +4 dBu (API 2500 manual's AUTO make-up level) at 0 dBFS = +22 dBu
# THRUST: the API 2500 manual cites US Patent 5,170,437 (Strahm, 1992). Its Fig. 4 is the active half-order
# high-pass in front of the rectifier: 100k || (32k + 0.16u) || (10k + 0.05u) || (3.2k + 0.016u) || (1k + 0.005u)
# into a 10k-feedback inverting stage (corners 31 Hz, 318 Hz, 3.1 kHz, 31.8 kHz; "+10 dB/decade").
# Relative to 632 Hz it gives -15.6 dB at 20 Hz and +13.8 dB at 20 kHz, matching the manuals' LOUD "3 dB/oct,
# -15 dB at 20 Hz, +15 dB at 20 kHz". LOUD = that circuit; MED (only "slight" in the manuals) = half its dB
# curve, an assumption. Realised as six first-order high shelves 1 + (A - 1)*HP(fc), least-squares fitted to the
# circuit's response on 20 Hz-20 kHz (the 31.8 kHz corner is above Nyquist at 44.1/48 kHz): LOUD within
# 0.16 dB at 44.1/48 kHz (0.8 dB at 96 kHz near 20 kHz), MED within 0.18 dB. Normalised to 0 dB at 632 Hz.
V_THRUST_FC = [31.289, 292.492, 285.268, 2900.162, 8827.33, 15000.0]
V_THRUST_A_LOUD = [5.14962, 3.02193, 1.08588, 2.92025, 1.32574, 1.36025]
V_THRUST_A_MED = [1.84052, 1.0, 1.77044, 1.77197, 1.0, 1.26676]
V_THRUST_NORM = {"LOUD": 10 ** (-24.9617 / 20), "MED": 10 ** (-10.1185 / 20)}   # 0 dB at 632 Hz (48 kHz)

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

TUBE_ST = [f"up{p}{i}" for p in "ab" for i in range(6)] + [f"dn{p}{i}" for p in "ab" for i in range(6)] + ["ton", "dcx", "dcy"] + \
          [f"dd{p}{i}" for p in "ab" for i in range(6)]  # phase-matched dry path (same up/down filters, no shaping)
# v1.6: half-band stages 2..4 for 4x / 8x / 16x (stage 1 = the v1.3 states above)
TUBE_ST += [f"s{g}{d}{p}{i}" for g in (2, 3, 4) for d in ("up", "dn", "dd") for p in "ab" for i in range(6)]
OPTO_ST = ["lt", "cf", "cs", "mem", "yp", "hp", "he", "e2", "e3", "q"]   # v1.6: he/e2/e3 = R37 network, q = cell state (R7 sense)
VCA_ST = ["hp", "t1", "t2", "ms", "gr", "yp", "t3", "t4", "t5", "t6"]
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
// API 225L knee / control-voltage stage (traced VCA-board schematic): current through r + a diode chain with v
// across (a = diodes * n * VT); Newton on the diode voltage, started right of the root (convex: monotone);
// 4 steps: within 0.001 dB of the converged network over 0-12 V
f_dsol(v, r, a) {
	i = 0;
	if (v > 0) {
		u = min(v, a * log(1 + v / (r * 2.52e-09)));
		for (k = 0; k < 4; k += 1) {
			ee = exp(u / a);
			u = u - (u + r * 2.52e-09 * (ee - 1) - v) / (1 + r * 2.52e-09 * ee / a);
		}
		i = 2.52e-09 * (exp(u / a) - 1);
	}
	return i;
}
// gain change (dB, <= 0) for overshoot o (dB): CV x = c*o + x0 into IC3a (R2 9k09 and R1 100k + CR6 feedback,
// rz + diode chain to ground), then CR9 into the IC3b virtual ground and the 2180 control port
f_k225(o, c, x0, a, rz) {
	x = c * o + x0;
	iz = f_dsol(x, rz, a);
	i6 = f_dsol(iz * 9090.0, 109090.0, 0.045292704);
	y = x + 9090.0 * (iz - i6);
	i9 = f_dsol(y, 28041.269841269837, 0.045292704);
	return -56465.63903782551 * i9;
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
                 ("d_oP", 0), ("d_oQ", 0), ("d_act", 0), ("d_fade", 1),
                 ("T_dirty", 0), ("O_dirty", 0), ("V_dirty", 0), ("G_dirty", 0), ("v_mkk", -1e9), ("v_mkc", 0)):
        CV(f"H_dyn_{n}" if False else f"dz_{n}", i)


def ctrl_names():
    return ["dz_t_gi", "dz_t_go", "dz_t_mx", "dz_t_w", "dz_t_dz", "dz_t_bz", "dz_o_gi", "dz_o_go", "dz_o_mx", "dz_o_w",
            "dz_o_prz", "dz_o_emz", "dz_o_lkz", "dz_v_gi", "dz_v_go", "dz_v_mx", "dz_v_w", "dz_v_thz", "dz_v_lkz",
            "dz_g_w", "dz_kl_w", "dz_kl_sel", "dz_d_oP", "dz_d_oQ", "dz_d_act", "dz_d_fade",
            "dz_T_dirty", "dz_O_dirty", "dz_V_dirty", "dz_G_dirty", "dz_v_mkk", "dz_v_mkc"]


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
    w("t_nf = cur_tos < 1.5 ? 2 : (cur_tos < 2.5 ? 4 : (cur_tos < 3.5 ? 8 : 16));")   # v1.6: TUBE oversampling factor
    w("t_gt = tan(pi * min(clamp(t_tone, 1000, 20000), 0.45 * t_nf * fs) / (t_nf * fs));")
    w("t_Gt = t_gt / (1 + t_gt);")
    w("t_dcr = 1 - 2 * pi * 8 / fs;")
    # opto
    _sm(w, "dz_o_prz", "clamp(o_pr, 0, 100) * 0.01")
    _sm(w, "dz_o_emz", "clamp(o_emph, 0, 100) * 0.01")
    _sm(w, "dz_o_lkz", "clamp(o_link, 0, 100) * 0.01")
    w("o_prg = exp(0.11512925465 * (50 * dz_o_prz - 12));")  # sidechain gain -12 .. +38 dB
    w("o_lim = o_mode > 0.5 ? 1 : 0;")
    # v1.6 (Teletronix schematic C-10953 rev C): COMP and LIMIT share one gain law. The T4A cells shunt the
    # signal after R6 (68k) and R7 (1k-2.7k); G = 1/(1 + q), q ~ R_th/R_cell with exponent 2, which gives COMP's ~3:1
    # (manual addendum). SW3 shorts R7 in COMP; in LIMIT the side-chain node sits above R7, so it senses
    # Vy * (1 + R7/R_cell) = Vy * (1 + o_a * q) and stiffens as reduction deepens. q is floored at 40 dB GR (manual: "up to 40 dB").
    # The schematic model applies to the internal (feedback) detector only. With CHAIN or EXT keys there is no
    # feedback, the R7 term would latch, and those sources keep their pre-v1.6 behaviour exactly (no floor).
    w("o_int = o_src < 0.5 ? 1 : 0;")
    w("o_K = (o_lim > 0.5 && o_int < 0.5) ? 4 : 1.6;")
    # Cell exponent: COMP 2 (addendum ~3:1); LIMIT 3.5 (fits the manual's Figure 1, which the addendum gives as the
    # limiter curve). One physical cell cannot do both; this follows both published curves (user's decision).
    w("o_p = o_lim > 0.5 ? (o_int > 0.5 ? 3.5 : 9) : 2;")
    w("o_a = (o_lim > 0.5 && o_int > 0.5) ? 0.0444 : 0;")   # R7 1.8k / (R6 68k || R2 100k = 40.5k)
    w("o_qmax = o_int > 0.5 ? 99 : 1e30;")
    w("o_aatt = 1 - exp(-1 / (0.0045 * fs));")               # cell attack (≈10 ms overall in the feedback loop)
    w("o_aela = 1 - exp(-1 / (0.002 * fs));")                # EL panel rise
    w("o_ael = 1 - exp(-1 / (0.004 * fs));")                 # EL panel decay
    w("o_afr = 1 - exp(-1 / (0.040 * fs));")                 # fast release component (≈60 ms to 50 %)
    w("o_asa = 1 - exp(-1 / (0.150 * fs));")                 # slow component charge
    w("o_amu = 1 - exp(-1 / (4.0 * fs));")                   # memory charge
    w("o_amd = 1 - exp(-1 / (20.0 * fs));")                  # memory discharge
    w("o_ghp = tan(pi * clamp(o_hpf, 20, 500) / fs);")
    w("o_Ghp = o_ghp / (1 + o_ghp);")
    # v1.6: R37 "LIM RESP" network (schematic): R37 || C12 (1 nF) in series between V3 (via C9 0.02 uF, source
    # ~35k, assumed) and the 1M balance pot loaded by C6 0.01 uF + R30 47k. R37 = 0..1M with Emphasis 0..100 %.
    # Relative to flat it cuts the side-chain below ~2 kHz (max about -15 dB near 200 Hz): ~+11 dB more GR at 15 kHz
    # than at 500 Hz (manual p. 7: about 10 dB more than below 1 kHz). Bilinear, coefficients per sample.
    w("o_r37 = 1000000 * dz_o_emz;")
    w("o_t12 = o_r37 * 0.000000001;")
    w("o_rc9 = o_r37 * 0.00000002;")
    w("o_d1 = 0.03117 + o_t12;")
    w("o_d2 = 0.000016729 + o_t12 * 0.03117;")
    w("o_d3 = o_t12 * 0.000016729;")
    w("o_a1 = o_d1 + o_rc9;")
    w("o_a2 = o_d2 + o_rc9 * 0.01047;")
    w("o_bk = 2 * fs;")
    w("o_k1 = o_bk;")
    w("o_k2 = o_bk * o_bk;")
    w("o_k3 = o_k2 * o_bk;")
    w("o_B0 = 1 + o_d1 * o_k1 + o_d2 * o_k2 + o_d3 * o_k3;")
    w("o_B1 = 3 + o_d1 * o_k1 - o_d2 * o_k2 - 3 * o_d3 * o_k3;")
    w("o_B2 = 3 - o_d1 * o_k1 - o_d2 * o_k2 + 3 * o_d3 * o_k3;")
    w("o_B3 = 1 - o_d1 * o_k1 + o_d2 * o_k2 - o_d3 * o_k3;")
    w("o_A0 = 1 + o_a1 * o_k1 + o_a2 * o_k2 + o_d3 * o_k3;")
    w("o_A1 = 3 + o_a1 * o_k1 - o_a2 * o_k2 - 3 * o_d3 * o_k3;")
    w("o_A2 = 3 - o_a1 * o_k1 - o_a2 * o_k2 + 3 * o_d3 * o_k3;")
    w("o_A3 = 1 - o_a1 * o_k1 + o_a2 * o_k2 - o_d3 * o_k3;")
    w("o_eb0 = o_B0 / o_A0;")
    w("o_eb1 = o_B1 / o_A0;")
    w("o_eb2 = o_B2 / o_A0;")
    w("o_eb3 = o_B3 / o_A0;")
    w("o_ea1 = o_A1 / o_A0;")
    w("o_ea2 = o_A2 / o_A0;")
    w("o_ea3 = o_A3 / o_A0;")
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
    w("v_kn = clamp(floor(v_knee + 0.5), 0, 2);")
    w(f"v_ak = (v_kn + 1) * {V_K_A1!r};")
    w(f"v_c = -v_slope / {V_K_SNEW!r};")
    w(f"v_rz = v_type > 0.5 ? {V_K_RZ['OLD']!r} : {V_K_RZ['NEW']!r};")
    xo, xn = V_K_X0["OLD"], V_K_X0["NEW"]
    w(f"v_x0 = v_type > 0.5 ? (v_kn < 0.5 ? {xo[0]!r} : (v_kn < 1.5 ? {xo[1]!r} : {xo[2]!r})) : (v_kn < 0.5 ? {xn[0]!r} : (v_kn < 1.5 ? {xn[1]!r} : {xn[2]!r}));")
    w("v_ghp = tan(pi * clamp(v_hpf, 20, 500) / fs);")
    w("v_Ghp = v_ghp / (1 + v_ghp);")
    for i, fc in enumerate(V_THRUST_FC):
        w(f"v_tg{i} = tan(pi * min({fc!r}, 0.45 * fs) / fs);")
        w(f"v_TG{i} = v_tg{i} / (1 + v_tg{i});")
        w(f"v_TA{i} = v_thrust < 1.5 ? {V_THRUST_A_MED[i] - 1!r} : {V_THRUST_A_LOUD[i] - 1!r};")
    w(f"v_TN = v_thrust < 1.5 ? {V_THRUST_NORM['MED']!r} : {V_THRUST_NORM['LOUD']!r};")
    # AUTO make-up (API 2500 manual): THRESH raises the output "until the output level is around +4 dBu", then it
    # "will maintain an even output level" as THRESH and RATIO change. So the make-up is the static gain reduction a
    # +4 dBu signal gets (-18 dBFS, Waves mapping 0 dBFS = +22 dBu): the curve pivots on +4 dBu for any threshold and
    # ratio. NEW: the knee stage at the pivot. OLD (detector on the output): the static output level L solves
    # L = Lin + G(L - T); bisection, recomputed only when threshold, ratio, knee or type change.
    w("dz_v_mkk = dz_v_thz + 1000 * (clamp(floor(v_ratio + 0.5), 0, 6) + 10 * v_kn + 100 * (v_type > 0.5) + 1000 * (v_auto > 0.5));")
    w("dz_v_mkc = H_dz_v_mkc;")
    w("if (abs(dz_v_mkk - H_dz_v_mkk) > 0.000001) {")
    w("	dz_v_mkc = 0;")
    w("	if (v_auto > 0.5) {")
    w("		if (v_type > 0.5) {")
    w(f"			mlo = {V_AUTO_REF_DBFS!r} - 80;")
    w(f"			mhi = {V_AUTO_REF_DBFS!r};")
    w("			for (k = 0; k < 30; k += 1) {")
    w("				mm = 0.5 * (mlo + mhi);")
    w(f"				if (mm - {V_AUTO_REF_DBFS!r} - f_k225(mm - dz_v_thz, v_c, v_x0, v_ak, v_rz) > 0) {{")
    w("					mhi = mm;")
    w("				} else {")
    w("					mlo = mm;")
    w("				}")
    w("			}")
    w(f"			dz_v_mkc = {V_AUTO_REF_DBFS!r} - 0.5 * (mlo + mhi);")
    w("		} else {")
    w(f"			dz_v_mkc = -f_k225({V_AUTO_REF_DBFS!r} - dz_v_thz, v_c, v_x0, v_ak, v_rz);")
    w("		}")
    w("	}")
    w("}")
    w("v_mk = exp(0.11512925465 * dz_v_mkc);")
    # gate
    w("dz_g_wt = g_on > 0.5 ? 1 : 0;")
    _sm(w, "dz_g_w", "dz_g_wt", "a_mix")
    _snap(w, "dz_g_w", "dz_g_wt")
    w("g_ghp = tan(pi * clamp(g_hpf, 20, 2000) / fs);")
    w("g_Ghp = g_ghp / (1 + g_ghp);")
    w("g_glp = tan(pi * min(clamp(g_lpf, 200, 20000), 0.45 * fs) / fs);")
    w("g_Glp = g_glp / (1 + g_glp);")
    w("g_dec = exp(-1 / (0.030 * fs));")                     # key envelope decay (low ripple -> clean hysteresis)
    w("g_rdb = -clamp(g_range, -80, 0) + 0.0001;")             # gain moves in dB: Attack/Release = full open/close time
    w("g_sat = g_rdb / (0.001 * clamp(g_att, 0.1, 50) * fs);")
    w("g_sre = g_rdb / (0.001 * clamp(g_rel, 5, 2000) * fs);")
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
    # v1.6: clear a disabled module's state once (when it has state), not on every sample;
    # nothing writes a disabled module's state, so this is bit-exact with v1.5.
    for m, flag in (("T", "dz_t_w"), ("O", "dz_o_w"), ("V", "dz_v_w"), ("G", "dz_g_w")):
        dzn = f"dz_{m}_dirty"
        w(f"{dzn} = H_{dzn};")
        w(f"if ({flag} <= 0 && {dzn} > 0.5) {{")
        G.ind += 1
        if m == "G":
            for v in GATE_ST:
                w(f"dg_{v} = 0;")
        else:
            for ln in LANES:
                for ch in CH:
                    for v in LANE_ST[m]:
                        w(f"d{ln}_{m}_{ch}_{v} = 0;")
        w(f"{dzn} = 0;")
        G.ind -= 1
        w("}")
        w(f"if ({flag} > 0) {{")
        w(f"\t{dzn} = 1;")
        w("}")


def _src(sel, internal, ch):
    return f"({sel} < 0.5 ? {internal} : ({sel} < 1.5 ? cin_{ch} : key_{ch}))"


def emit_tube(w, G, ln, xin, xout, meter):
    """TUBE stage at 2x / 4x / 8x / 16x (v1.6; the 2x branch is the v1.3 code path, bit-exact)."""
    s = lambda ch, v: f"d{ln}_T_{ch}_{v}"
    cas, cbs = ", ".join(repr(c) for c in CA), ", ".join(repr(c) for c in CB)

    def zs(ch, stg, d, p):
        if stg == 1:
            return [s(ch, f"{d}{p}{i}") for i in range(6)]
        return [s(ch, f"s{stg}{d}{p}{i}") for i in range(6)]

    def down(ch, vals, kind, stg):
        while len(vals) > 1:
            za, zb = zs(ch, stg, kind, "a"), zs(ch, stg, kind, "b")
            nxt = []
            for j in range(len(vals) // 2):
                w(f"tpa, {', '.join(za)} = f_ap5({vals[2 * j + 1]}, {', '.join(za)}, {cas});")
                w(f"tpb, {', '.join(zb)} = f_ap5({vals[2 * j]}, {', '.join(zb)}, {cbs});")
                nm = f"t{kind}{stg}_{j}"
                w(f"{nm} = 0.5 * (tpa + tpb);")
                nxt.append(nm)
            vals = nxt
            stg -= 1
        return vals[0]

    w("if (dz_t_w > 0) {")
    G.ind += 1
    for ch in CH:
        w(f"tu_{ch} = {xin[ch]} * dz_t_gi;")
        w("ty = 0;")
        w("tdr = 0;")
        for idx, n in ((1, 2), (2, 4), (3, 8), (4, 16)):
            w(("if" if idx == 1 else "} else if") + f" (cur_tos < {idx + 0.5}) {{")
            G.ind += 1
            level = [f"tu_{ch}"]
            for stg in range(1, idx + 1):
                za, zb = zs(ch, stg, "up", "a"), zs(ch, stg, "up", "b")
                nxt = []
                for j, v in enumerate(level):
                    w(f"tv{stg}_{2 * j}, {', '.join(za)} = f_ap5({v}, {', '.join(za)}, {cas});")
                    w(f"tv{stg}_{2 * j + 1}, {', '.join(zb)} = f_ap5({v}, {', '.join(zb)}, {cbs});")
                    nxt += [f"tv{stg}_{2 * j}", f"tv{stg}_{2 * j + 1}"]
                level = nxt
            wet = []
            for j, v in enumerate(level):
                w(f"tyy = f_tube({v} * t_k, t_b, t_ib);")
                w(f"tl_{j}, {s(ch, 'ton')} = f_op(tyy, {s(ch, 'ton')}, t_Gt);")
                wet.append(f"tl_{j}")
            w(f"{s(ch, 'ton')} = fixdenorm({s(ch, 'ton')});")
            yv = down(ch, wet, "dn", idx)
            w(f"ty = {yv} * t_ko;")
            # dry path through the identical up/down filters -> wet/dry mix without comb filtering
            dv = down(ch, list(level), "dd", idx)
            w(f"tdr = {dv} / max(dz_t_gi, 1e-9);")
            G.ind -= 1
        w("}")
        w(f"tdy = ty - {s(ch, 'dcx')} + t_dcr * {s(ch, 'dcy')};")
        w(f"{s(ch, 'dcx')} = ty;")
        w(f"{s(ch, 'dcy')} = fixdenorm(tdy);")
        w(f"tbl = tdr + dz_t_mx * (tdy * dz_t_go - tdr);")
        w(f"{xout[ch]} = {xin[ch]} + dz_t_w * (tbl - {xin[ch]});")
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
        # LIMIT's R7 sense term scales whatever feeds the detector (internal, chain or external key), so the
        # COMP/LIMIT switch acts with every detector source.
        w(f"osc_{ch} = {_src('o_src', s(ch, 'yp'), ch)} * (1 + o_a * {s(ch, 'q')});")
        w(f"ohl, {s(ch, 'hp')} = f_op(osc_{ch}, {s(ch, 'hp')}, o_Ghp);")
        w(f"osc_{ch} = osc_{ch} - ohl;")
        w(f"{s(ch, 'hp')} = fixdenorm({s(ch, 'hp')});")
        w("if (dz_o_emz > 0) {")
        w(f"    oex = osc_{ch};")
        w(f"    osc_{ch} = o_eb0 * oex + {s(ch, 'he')};")
        w(f"    {s(ch, 'he')} = fixdenorm(o_eb1 * oex - o_ea1 * osc_{ch} + {s(ch, 'e2')});")
        w(f"    {s(ch, 'e2')} = fixdenorm(o_eb2 * oex - o_ea2 * osc_{ch} + {s(ch, 'e3')});")
        w(f"    {s(ch, 'e3')} = fixdenorm(o_eb3 * oex - o_ea3 * osc_{ch});")
        w("}")
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
        w(f"oq = min(pow(oc, o_p), o_qmax);")
        w(f"{s(ch, 'q')} = oq;")
        w(f"oG = 1 / (1 + oq);")
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
        # THRUST: NORM flat; MED / LOUD = 5 / 10 dB per decade tilt (see V_THRUST_*)
        w("vt = vs;")
        for i, st in enumerate(["t1", "t2", "t3", "t4", "t5", "t6"]):
            w(f"vtl, {s(ch, st)} = f_op(vt, {s(ch, st)}, v_TG{i});")
            w(f"{s(ch, st)} = fixdenorm({s(ch, st)});")
            w(f"vt = vt + v_TA{i} * (vt - vtl);")
        w(f"{s(ch, 'hp')} = fixdenorm({s(ch, 'hp')});")
        w(f"vst_{ch} = v_thrust < 0.5 ? vs : vt * v_TN;")
        w(f"{s(ch, 'ms')} = fixdenorm({s(ch, 'ms')} + (vst_{ch} * vst_{ch} - {s(ch, 'ms')}) * v_arms);")
        w(f"vlv_{ch} = 10 * log10({s(ch, 'ms')} + 1e-20) + 3.0103;")
    w("vlk = 10 * log10(0.5 * (dVms_L + dVms_R) + 1e-20) + 3.0103;".replace("dVms_L", s("L", "ms")).replace("dVms_R", s("R", "ms")))
    w("vgr = 0;")
    for ch in CH:
        gr = s(ch, "gr")
        w(f"vlv = vlv_{ch} + dz_v_lkz * (vlk - vlv_{ch});")
        w("vgc = f_k225(vlv - dz_v_thz, v_c, v_x0, v_ak, v_rz);")
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
    w("gtd = dg_open > 0.5 ? 0 : -g_rdb;")
    w("dg_g = gtd > dg_g ? min(gtd, dg_g + g_sat) : max(gtd, dg_g - g_sre);")   # dg_g holds the gate gain in dB
    w("gg = dg_open > 0.5 || dg_g > -g_rdb + 0.001 ? exp(0.11512925465 * dg_g) : g_floor;")
    for ch in CH:
        w(f"{dst[ch]} = {dst[ch]} + dz_g_w * ({dst[ch]} * gg - {dst[ch]});")
    w("dm_g = gg;")
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
